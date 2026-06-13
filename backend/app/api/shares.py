"""分享链接 API"""
import json
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import ShareLink, StorageSource, FileOperationLog
from app.schemas.schemas import ShareCreate, ShareUpdate, ShareResponse, FileItem
from app.services.factory import create_adapter

router = APIRouter(prefix="/shares", tags=["分享管理"])


@router.post("/", response_model=ShareResponse)
async def create_share(
    req: ShareCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    # Verify storage exists
    result = await db.execute(select(StorageSource).where(StorageSource.id == req.storage_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="存储源不存在")

    expire_at = None
    if req.expire_hours and req.expire_hours > 0:
        expire_at = datetime.utcnow() + timedelta(hours=req.expire_hours)

    share = ShareLink(
        user_id=current_user["user_id"],
        storage_id=req.storage_id,
        file_path=req.file_path,
        is_dir=req.is_dir,
        is_multi=req.is_multi,
        file_name=req.file_name,
        allow_download=req.allow_download,
        allow_preview=req.allow_preview,
        password=req.password,
        max_views=req.max_views,
        expire_at=expire_at,
    )
    db.add(share)
    await db.flush()
    await db.refresh(share)

    # Log share creation
    ip_address = ""
    if request:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()
        else:
            ip_address = request.client.host if request.client else ""
    log = FileOperationLog(
        user_id=current_user["user_id"],
        username=current_user.get("username", ""),
        storage_id=source.id,
        storage_name=source.name,
        operation="share",
        file_path=req.file_path,
        file_name=req.file_name,
        ip_address=ip_address,
    )
    db.add(log)

    resp = ShareResponse.model_validate(share)
    resp.share_url = f"/s/{share.share_code}"
    resp.storage_name = source.name
    return resp


@router.get("/")
async def list_shares(
    storage_id: int = Query(None),
    storage_name: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    q = select(ShareLink).where(ShareLink.user_id == current_user["user_id"])
    count_q = select(func.count(ShareLink.id)).where(ShareLink.user_id == current_user["user_id"])
    if storage_id:
        q = q.where(ShareLink.storage_id == storage_id)
        count_q = count_q.where(ShareLink.storage_id == storage_id)
    # 按存储源名称筛选
    if storage_name:
        # 先查询匹配的存储源ID
        storage_result = await db.execute(
            select(StorageSource.id).where(StorageSource.name == storage_name)
        )
        matching_storage_ids = [row[0] for row in storage_result.fetchall()]
        if matching_storage_ids:
            q = q.where(ShareLink.storage_id.in_(matching_storage_ids))
            count_q = count_q.where(ShareLink.storage_id.in_(matching_storage_ids))
        else:
            # 没有匹配的存储源，返回空结果
            return {"items": [], "total": 0, "page": page, "page_size": page_size}
    # 总数
    total = (await db.execute(count_q)).scalar() or 0
    # 分页
    q = q.order_by(ShareLink.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    shares = result.scalars().all()

    # Batch load storage names
    storage_ids = list(set(s.storage_id for s in shares))
    storage_map = {}
    if storage_ids:
        sr = await db.execute(select(StorageSource).where(StorageSource.id.in_(storage_ids)))
        for s in sr.scalars().all():
            storage_map[s.id] = s.name

    items = []
    for s in shares:
        resp = ShareResponse.model_validate(s)
        resp.share_url = f"/s/{s.share_code}"
        resp.storage_name = storage_map.get(s.storage_id, "")
        items.append(resp)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.put("/{share_id}", response_model=ShareResponse)
async def update_share(
    share_id: int,
    req: ShareUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(ShareLink).where(ShareLink.id == share_id, ShareLink.user_id == current_user["user_id"])
    )
    share = result.scalar_one_or_none()
    if not share:
        raise HTTPException(status_code=404, detail="分享不存在")
    if req.allow_download is not None:
        share.allow_download = req.allow_download
    if req.allow_preview is not None:
        share.allow_preview = req.allow_preview
    share.password = req.password
    if req.max_views is not None:
        share.max_views = req.max_views or None
    if req.expire_hours is not None:
        share.expire_at = datetime.utcnow() + timedelta(hours=req.expire_hours) if req.expire_hours > 0 else None
    db.add(share)
    await db.flush()
    await db.refresh(share)
    resp = ShareResponse.model_validate(share)
    resp.share_url = f"/s/{share.share_code}"
    return resp


@router.delete("/{share_id}")
async def delete_share(
    share_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(ShareLink).where(ShareLink.id == share_id, ShareLink.user_id == current_user["user_id"])
    )
    share = result.scalar_one_or_none()
    if not share:
        raise HTTPException(status_code=404, detail="分享不存在")
    await db.delete(share)
    return {"success": True, "message": "已删除"}


@router.put("/{share_id}/toggle")
async def toggle_share(
    share_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(ShareLink).where(ShareLink.id == share_id, ShareLink.user_id == current_user["user_id"])
    )
    share = result.scalar_one_or_none()
    if not share:
        raise HTTPException(status_code=404, detail="分享不存在")
    share.enabled = not share.enabled
    db.add(share)
    return {"success": True, "enabled": share.enabled}


@router.post("/batch-delete")
async def batch_delete_shares(
    share_ids: list[int],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """批量删除分享链接"""
    result = await db.execute(
        select(ShareLink).where(
            ShareLink.id.in_(share_ids),
            ShareLink.user_id == current_user["user_id"],
        )
    )
    shares = result.scalars().all()
    deleted = 0
    for s in shares:
        await db.delete(s)
        deleted += 1
    return {"success": True, "deleted": deleted}


@router.get("/access/{share_code}")
async def access_share(
    share_code: str,
    password: str = Query(None),
    subpath: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """公开访问分享链接（无需登录）"""
    result = await db.execute(select(ShareLink).where(ShareLink.share_code == share_code))
    share = result.scalar_one_or_none()
    if not share:
        raise HTTPException(status_code=404, detail="分享链接不存在或已失效")
    if not share.enabled:
        raise HTTPException(status_code=403, detail="分享已关闭")
    if share.expire_at:
        from datetime import timezone
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        if share.expire_at < now_utc:
            raise HTTPException(status_code=403, detail="分享已过期")
    if share.max_views and share.view_count >= share.max_views:
        raise HTTPException(status_code=403, detail="访问次数已达上限")
    if share.password and not password:
        return {
            "type": "need_password",
            "share": {"file_name": share.file_name, "is_dir": share.is_dir, "is_multi": share.is_multi},
            "message": "此分享需要密码访问",
        }
    if share.password and share.password != password:
        raise HTTPException(status_code=401, detail="密码错误")

    # 只有首次访问才增加计数（无subpath时）
    if not subpath:
        share.view_count += 1
        db.add(share)

    # Get storage source
    result2 = await db.execute(select(StorageSource).where(StorageSource.id == share.storage_id))
    source = result2.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="存储源不存在")

    config = dict(source.config)
    config["_storage_id"] = source.id
    adapter = create_adapter(source.storage_type, config)

    # 生成分享下载URL
    def share_download_url(file_path: str) -> str:
        return f"/api/shares/access/{share_code}/download?file_path={file_path}"

    # 辅助函数：列出目录文件并生成下载URL
    async def list_dir_with_urls(dir_path: str):
        files = await adapter.list_files(dir_path)
        file_list = []
        for f in files:
            d = f.model_dump()
            if not f.is_dir:
                if source.storage_type == "local":
                    d["url"] = share_download_url(f.path)
                elif f.url:
                    d["url"] = f.url
                else:
                    try:
                        d["url"] = await adapter.get_download_url(f.path)
                    except Exception:
                        pass
            file_list.append(d)
        return file_list

    # Multi-file share
    if share.is_multi:
        shared_paths = json.loads(share.file_path)
        # 支持子目录导航
        if subpath:
            actual_path = subpath
            file_list = await list_dir_with_urls(actual_path)
            return {
                "type": "multi",
                "share": ShareResponse.model_validate(share).model_dump(),
                "files": file_list,
                "subpath": subpath,
            }
        # 无subpath：展示共享路径本身（文件夹显示为可进入的条目）
        all_files = []
        for p in shared_paths:
            name = p.rstrip('/').split('/')[-1] if p != '/' else '/'
            try:
                items = await adapter.list_files(p)
                if items is not None:
                    # 是目录，创建目录条目（不展开内容）
                    all_files.append(FileItem(name=name, path=p, is_dir=True))
                else:
                    fi = await adapter.get_file_info(p)
                    all_files.append(fi)
            except Exception:
                try:
                    fi = await adapter.get_file_info(p)
                    all_files.append(fi)
                except Exception:
                    pass
        file_list = []
        for f in all_files:
            d = f.model_dump()
            if not f.is_dir:
                if source.storage_type == "local":
                    d["url"] = share_download_url(f.path)
                elif f.url:
                    d["url"] = f.url
                else:
                    try:
                        d["url"] = await adapter.get_download_url(f.path)
                    except Exception:
                        pass
            file_list.append(d)
        return {
            "type": "multi",
            "share": ShareResponse.model_validate(share).model_dump(),
            "files": file_list,
            "subpath": subpath or "",
        }

    if share.is_dir:
        # 拼接实际路径
        if subpath:
            actual_path = share.file_path.rstrip("/") + "/" + subpath.lstrip("/")
        else:
            actual_path = share.file_path
        file_list = await list_dir_with_urls(actual_path)
        return {
            "type": "dir",
            "share": ShareResponse.model_validate(share).model_dump(),
            "files": file_list,
            "subpath": subpath or "",
        }
    else:
        fi = await adapter.get_file_info(share.file_path)
        d = fi.model_dump()
        if source.storage_type == "local":
            d["url"] = share_download_url(share.file_path)
        elif fi.url:
            d["url"] = fi.url
        else:
            try:
                d["url"] = await adapter.get_download_url(share.file_path)
            except Exception:
                pass
        return {
            "type": "file",
            "share": ShareResponse.model_validate(share).model_dump(),
            "files": [d],
        }


@router.get("/access/{share_code}/download")
async def download_share_file(
    share_code: str,
    file_path: str = Query(...),
    password: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """公开下载分享文件（无需登录）"""
    result = await db.execute(select(ShareLink).where(ShareLink.share_code == share_code))
    share = result.scalar_one_or_none()
    if not share:
        raise HTTPException(status_code=404, detail="分享链接不存在或已失效")
    if not share.enabled:
        raise HTTPException(status_code=403, detail="分享已关闭")
    if share.expire_at:
        from datetime import timezone
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        if share.expire_at < now_utc:
            raise HTTPException(status_code=403, detail="分享已过期")
    if share.password and share.password != password:
        raise HTTPException(status_code=401, detail="密码错误")
    if not share.allow_download:
        raise HTTPException(status_code=403, detail="此分享不允许下载")

    # Get storage source
    result2 = await db.execute(select(StorageSource).where(StorageSource.id == share.storage_id))
    source = result2.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="存储源不存在")

    # Local storage: serve file directly
    if source.storage_type == "local":
        from app.services.factory import create_adapter
        config = dict(source.config)
        config["_storage_id"] = source.id
        adapter = create_adapter("local", config)
        real_path = adapter._real_path(file_path)
        if not os.path.isfile(real_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        return FileResponse(real_path, filename=os.path.basename(real_path))

    # Cloud storage: redirect to signed URL
    config = dict(source.config)
    config["_storage_id"] = source.id
    from app.services.factory import create_adapter
    adapter = create_adapter(source.storage_type, config)
    try:
        url = await adapter.get_download_url(file_path)
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取下载链接失败: {str(e)}")
