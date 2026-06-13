"""数据库备份管理 API"""
import os
import shutil
import sqlite3
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings

router = APIRouter(prefix="/backups", tags=["备份管理"])

# 备份目录
BACKUP_DIR = os.path.expanduser("~/.unifile/backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

# 数据库路径
DB_PATH = os.path.expanduser("~/.unifile/db/unifile.db")


def _check_admin(current_user: dict):
    """检查管理员权限"""
    if current_user.get("role_code") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")


def _get_backup_list():
    """获取备份文件列表"""
    backups = []
    if os.path.exists(BACKUP_DIR):
        for filename in sorted(os.listdir(BACKUP_DIR), reverse=True):
            if filename.endswith('.db'):
                filepath = os.path.join(BACKUP_DIR, filename)
                stat = os.stat(filepath)
                backups.append({
                    "filename": filename,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%dT%H:%M:%S"),
                })
    return backups


def _format_size(size: int) -> str:
    """格式化文件大小"""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.1f} GB"


@router.get("/")
async def list_backups(
    page: int = 1,
    page_size: int = 4,
    current_user: dict = Depends(get_current_user)
):
    """获取备份列表"""
    _check_admin(current_user)
    all_backups = _get_backup_list()
    total = len(all_backups)
    
    # 分页
    start = (page - 1) * page_size
    end = start + page_size
    backups = all_backups[start:end]
    
    for b in backups:
        b["size_text"] = _format_size(b["size"])
    return {"backups": backups, "total": total, "page": page, "page_size": page_size}


@router.post("/create")
async def create_backup(current_user: dict = Depends(get_current_user)):
    """创建备份"""
    _check_admin(current_user)
    
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail="数据库文件不存在")
    
    # 生成备份文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"unifile_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    try:
        # 使用 SQLite 的 backup 命令来安全备份
        source_conn = sqlite3.connect(DB_PATH)
        dest_conn = sqlite3.connect(backup_path)
        source_conn.backup(dest_conn)
        source_conn.close()
        dest_conn.close()
        
        stat = os.stat(backup_path)
        return {
            "success": True,
            "message": "备份创建成功",
            "backup": {
                "filename": backup_filename,
                "size": stat.st_size,
                "size_text": _format_size(stat.st_size),
                "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%dT%H:%M:%S"),
            }
        }
    except Exception as e:
        # 清理失败的备份文件
        if os.path.exists(backup_path):
            os.remove(backup_path)
        raise HTTPException(status_code=500, detail=f"备份失败: {str(e)}")


@router.post("/restore/{filename}")
async def restore_backup(filename: str, current_user: dict = Depends(get_current_user)):
    """从备份还原"""
    _check_admin(current_user)
    
    backup_path = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="备份文件不存在")
    
    # 验证文件名格式
    if not filename.endswith('.db') or '..' in filename or '/' in filename:
        raise HTTPException(status_code=400, detail="无效的备份文件名")
    
    try:
        # 备份当前数据库（以防还原失败）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pre_restore_backup = os.path.join(BACKUP_DIR, f"pre_restore_{timestamp}.db")
        shutil.copy2(DB_PATH, pre_restore_backup)
        
        # 还原数据库
        shutil.copy2(backup_path, DB_PATH)
        
        return {
            "success": True,
            "message": f"还原成功！已自动备份还原前的数据库: pre_restore_{timestamp}.db",
            "pre_restore_backup": f"pre_restore_{timestamp}.db"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"还原失败: {str(e)}")


@router.get("/download/{filename}")
async def download_backup(filename: str, current_user: dict = Depends(get_current_user)):
    """下载备份文件"""
    _check_admin(current_user)
    
    backup_path = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="备份文件不存在")
    
    # 验证文件名格式
    if not filename.endswith('.db') or '..' in filename or '/' in filename:
        raise HTTPException(status_code=400, detail="无效的备份文件名")
    
    return FileResponse(
        backup_path,
        filename=filename,
        media_type="application/octet-stream"
    )


@router.delete("/{filename}")
async def delete_backup(filename: str, current_user: dict = Depends(get_current_user)):
    """删除备份"""
    _check_admin(current_user)
    
    backup_path = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="备份文件不存在")
    
    # 验证文件名格式
    if not filename.endswith('.db') or '..' in filename or '/' in filename:
        raise HTTPException(status_code=400, detail="无效的备份文件名")
    
    try:
        os.remove(backup_path)
        return {"success": True, "message": "备份已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.post("/upload")
async def upload_backup(
    file: UploadFile = FastAPIFile(...),
    current_user: dict = Depends(get_current_user)
):
    """上传备份文件"""
    _check_admin(current_user)
    
    # 验证文件类型
    if not file.filename.endswith('.db'):
        raise HTTPException(status_code=400, detail="只支持 .db 文件")
    
    # 验证文件名
    safe_filename = os.path.basename(file.filename)
    if '..' in safe_filename or '/' in safe_filename:
        raise HTTPException(status_code=400, detail="无效的文件名")
    
    # 检查是否已存在同名文件
    backup_path = os.path.join(BACKUP_DIR, safe_filename)
    if os.path.exists(backup_path):
        # 添加时间戳避免覆盖
        name, ext = os.path.splitext(safe_filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{name}_{timestamp}{ext}"
        backup_path = os.path.join(BACKUP_DIR, safe_filename)
    
    try:
        # 保存上传的文件
        with open(backup_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 验证是否为有效的 SQLite 数据库
        try:
            conn = sqlite3.connect(backup_path)
            conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            conn.close()
        except Exception:
            os.remove(backup_path)
            raise HTTPException(status_code=400, detail="无效的 SQLite 数据库文件")
        
        stat = os.stat(backup_path)
        return {
            "success": True,
            "message": "备份上传成功",
            "backup": {
                "filename": safe_filename,
                "size": stat.st_size,
                "size_text": _format_size(stat.st_size),
                "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%dT%H:%M:%S"),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(backup_path):
            os.remove(backup_path)
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/db-info")
async def get_db_info(current_user: dict = Depends(get_current_user)):
    """获取数据库信息"""
    _check_admin(current_user)
    
    if not os.path.exists(DB_PATH):
        return {"exists": False}
    
    stat = os.stat(DB_PATH)
    
    # 获取数据库表信息
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        # 获取每个表的记录数
        table_counts = {}
        for table in tables:
            try:
                cursor = conn.execute(f"SELECT COUNT(*) FROM [{table}]")
                table_counts[table] = cursor.fetchone()[0]
            except:
                table_counts[table] = -1
        
        conn.close()
    except Exception:
        tables = []
        table_counts = {}
    
    return {
        "exists": True,
        "path": DB_PATH,
        "size": stat.st_size,
        "size_text": _format_size(stat.st_size),
        "modified_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%dT%H:%M:%S"),
        "tables": tables,
        "table_counts": table_counts,
    }