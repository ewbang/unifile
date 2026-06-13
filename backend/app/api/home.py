"""首页公开访问 API — 游客无需登录"""
import os
import fnmatch
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.models import StorageSource
from app.schemas.schemas import FileListResponse, FileItem
from app.services.factory import create_adapter

router = APIRouter(prefix="/home", tags=["首页公开访问"])


async def _get_public_storages(db: AsyncSession):
    """获取所有公开显示的存储源"""
    result = await db.execute(
        select(StorageSource)
        .where(StorageSource.is_public == True, StorageSource.enabled == True)
        .order_by(StorageSource.sort_order, StorageSource.id)
    )
    return result.scalars().all()


def _check_path_protected(path: str, protected_paths: list) -> dict | None:
    """
    检查路径是否受密码保护，使用Glob表达式匹配
    
    规则说明:
    - / : 根路径需要密码访问
    - /music/* : music文件夹需要密码，子文件夹不加密
    - /music/** : music文件夹及其所有子文件夹都需要密码
    - /ewb-pan/a* : 匹配 /ewb-pan/ 下以 a 开头的目录
    
    匹配逻辑:
    1. 规则按顺序匹配，第一个匹配的规则生效
    2. /** 匹配目录及其所有子目录和文件
    3. /* 只匹配目录本身（一级）
    4. / 只匹配根目录
    5. 其他通配符模式使用 fnmatch 匹配
    6. 子目录继承父目录的保护规则
    """
    if not protected_paths:
        return None
    
    # 标准化路径
    normalized_path = path.rstrip("/") or "/"
    
    # 检查当前路径及其所有父目录
    check_paths = [normalized_path]
    # 添加所有父目录路径
    parts = normalized_path.split("/")
    for i in range(len(parts) - 1, 0, -1):
        parent = "/".join(parts[:i])
        if parent:
            check_paths.append(parent)
    
    # 对每个路径检查规则
    for check_path in check_paths:
        for rule in protected_paths:
            pattern = rule.get("pattern", "").rstrip("/") or "/"
            
            # 规则1: / 只匹配根目录
            if pattern == "/":
                if check_path == "/":
                    return rule
                continue
            
            # 规则2: /music/** 匹配目录及其所有子目录
            if pattern.endswith("/**"):
                base_pattern = pattern[:-3]  # 去掉 /**
                # 匹配目录本身
                if check_path == base_pattern:
                    return rule
                # 匹配子目录和文件
                if fnmatch.fnmatch(check_path, pattern):
                    return rule
                # 也支持直接路径前缀匹配
                if check_path.startswith(base_pattern + "/"):
                    return rule
                continue
            
            # 规则3: /ewb-pan/a* 或 /music/* 等包含通配符的模式
            # 检查模式是否包含通配符字符
            if any(c in pattern for c in ['*', '?', '[']):
                # 获取父目录和匹配模式
                # 例如 /ewb-pan/a* -> 父目录 /ewb-pan, 模式 a*
                parts = pattern.rsplit('/', 1)
                if len(parts) == 2:
                    parent_dir = parts[0] or '/'
                    glob_pattern = parts[1]
                    
                    # 检查当前路径是否是父目录的子目录
                    if check_path.startswith(parent_dir + "/"):
                        # 获取相对路径部分
                        relative_path = check_path[len(parent_dir) + 1:]
                        # 检查相对路径的第一层是否匹配
                        first_part = relative_path.split('/')[0]
                        if fnmatch.fnmatch(first_part, glob_pattern):
                            return rule
                else:
                    # 没有父目录，直接匹配
                    if fnmatch.fnmatch(check_path, pattern):
                        return rule
                continue
            
            # 规则4: 精确匹配
            if check_path == pattern:
                return rule
    
    return None


def _check_file_need_password(file_path: str, file_is_dir: bool, protected_paths: list) -> bool:
    """检查文件/目录是否需要密码"""
    if not protected_paths:
        return False
    
    # 对于文件，检查其所在目录是否需要密码
    if not file_is_dir:
        # 获取文件所在目录
        parent_dir = "/".join(file_path.rstrip("/").split("/")[:-1]) or "/"
        return _check_path_protected(parent_dir, protected_paths) is not None
    
    # 对于目录，直接检查是否需要密码
    return _check_path_protected(file_path, protected_paths) is not None


@router.get("/storages")
async def list_public_storages(db: AsyncSession = Depends(get_db)):
    """获取所有公开显示的存储源（无需登录）"""
    storages = await _get_public_storages(db)
    result = []
    for s in storages:
        config = s.config or {}
        # 获取挂载路径（prefix字段）
        mount_path = config.get("prefix", "")
        result.append({
            "id": s.id,
            "name": s.name,
            "storage_type": s.storage_type,
            "icon": s.icon,
            "color": s.color,
            "description": s.description,
            "has_protected_paths": bool(s.protected_paths),
            "mount_path": mount_path,
        })
    return result


@router.get("/{storage_id}/list")
async def public_list_files(
    storage_id: int,
    path: str = Query("/", description="目录路径"),
    password: str = Query(None, description="目录密码（如果需要）"),
    db: AsyncSession = Depends(get_db),
):
    """公开访问文件列表（无需登录，但可能需要密码）"""
    # 获取存储源
    result = await db.execute(
        select(StorageSource).where(
            StorageSource.id == storage_id,
            StorageSource.is_public == True,
            StorageSource.enabled == True,
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="存储源不存在或未公开")

    # 检查路径是否受保护
    protected_config = _check_path_protected(path, source.protected_paths or [])
    if protected_config:
        # 需要密码验证
        if not password or password != protected_config.get("password"):
            raise HTTPException(
                status_code=401,
                detail={
                    "need_password": True,
                    "message": "此目录需要密码访问",
                    "path": path,
                },
            )

    # 获取文件列表
    config = dict(source.config)
    config["_storage_id"] = source.id
    adapter = create_adapter(source.storage_type, config)
    
    try:
        files = await adapter.list_files(path)
        # Sort: dirs first, then by name
        files.sort(key=lambda f: (not f.is_dir, f.name.lower()))
        
        # 为每个文件添加是否需要密码的信息
        protected_paths = source.protected_paths or []
        result_files = []
        for f in files:
            f_dict = f.model_dump()
            f_dict["need_password"] = _check_file_need_password(f.path, f.is_dir, protected_paths)
            result_files.append(f_dict)
        
        return {
            "files": result_files,
            "path": path,
            "storage_id": storage_id,
            "storage_name": source.name,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")


@router.get("/{storage_id}/download")
async def public_download_file(
    storage_id: int,
    path: str = Query(..., description="文件路径"),
    password: str = Query(None, description="目录密码（如果需要）"),
    db: AsyncSession = Depends(get_db),
):
    """公开下载文件（无需登录，但可能需要密码）"""
    # 获取存储源
    result = await db.execute(
        select(StorageSource).where(
            StorageSource.id == storage_id,
            StorageSource.is_public == True,
            StorageSource.enabled == True,
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="存储源不存在或未公开")

    # 检查文件所在目录是否受保护
    parent_dir = "/".join(path.rstrip("/").split("/")[:-1]) or "/"
    protected_config = _check_path_protected(parent_dir, source.protected_paths or [])
    if protected_config:
        if not password or password != protected_config.get("password"):
            raise HTTPException(status_code=401, detail="此目录需要密码访问")

    # 获取下载链接
    config = dict(source.config)
    config["_storage_id"] = source.id
    adapter = create_adapter(source.storage_type, config)

    # 本地存储直接返回文件
    if source.storage_type == "local":
        real_path = adapter._real_path(path)
        if not os.path.isfile(real_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        return FileResponse(real_path, filename=os.path.basename(real_path))

    # 云存储返回签名URL
    try:
        url = await adapter.get_download_url(path)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取下载链接失败: {str(e)}")


@router.post("/{storage_id}/verify-password")
async def verify_path_password(
    storage_id: int,
    path: str = Query(..., description="目录路径"),
    password: str = Query(..., description="密码"),
    db: AsyncSession = Depends(get_db),
):
    """验证目录密码"""
    result = await db.execute(
        select(StorageSource).where(
            StorageSource.id == storage_id,
            StorageSource.is_public == True,
            StorageSource.enabled == True,
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="存储源不存在或未公开")

    protected_config = _check_path_protected(path, source.protected_paths or [])
    if not protected_config:
        return {"success": True, "message": "此目录无需密码"}

    if password == protected_config.get("password"):
        return {"success": True, "message": "密码正确"}
    else:
        raise HTTPException(status_code=401, detail="密码错误")