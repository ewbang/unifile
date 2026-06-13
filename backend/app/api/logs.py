"""操作日志 API"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import FileOperationLog

router = APIRouter(prefix="/logs", tags=["操作日志"])


def _check_admin(current_user: dict):
    from fastapi import HTTPException
    if current_user.get("role_code") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")


@router.get("/")
async def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    operation: str = Query(None),
    keyword: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取操作日志"""
    _check_admin(current_user)
    q = select(FileOperationLog)
    count_q = select(func.count(FileOperationLog.id))
    if operation:
        q = q.where(FileOperationLog.operation == operation)
        count_q = count_q.where(FileOperationLog.operation == operation)
    if keyword:
        q = q.where(FileOperationLog.file_name.contains(keyword))
        count_q = count_q.where(FileOperationLog.file_name.contains(keyword))
    # 总数
    total = (await db.execute(count_q)).scalar() or 0
    # 分页
    q = q.order_by(FileOperationLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    logs = result.scalars().all()
    items = []
    for log in logs:
        items.append({
            "id": log.id,
            "username": log.username or "-",
            "storage_name": log.storage_name or "-",
            "operation": log.operation,
            "file_name": log.file_name or log.file_path.split("/")[-1],
            "file_path": log.file_path,
            "file_size": log.file_size,
            "ip_address": log.ip_address or "-",
            "created_at": str(log.created_at) if log.created_at else None,
        })
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/stats")
async def log_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """日志统计"""
    _check_admin(current_user)
    total = (await db.execute(select(func.count(FileOperationLog.id)))).scalar() or 0
    downloads = (await db.execute(select(func.count(FileOperationLog.id)).where(FileOperationLog.operation == "download"))).scalar() or 0
    uploads = (await db.execute(select(func.count(FileOperationLog.id)).where(FileOperationLog.operation == "upload"))).scalar() or 0
    deletes = (await db.execute(select(func.count(FileOperationLog.id)).where(FileOperationLog.operation == "delete"))).scalar() or 0
    return {"total": total, "downloads": downloads, "uploads": uploads, "deletes": deletes}


@router.delete("/clear")
async def clear_logs(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """清空所有操作日志"""
    _check_admin(current_user)
    from sqlalchemy import delete as sql_delete
    await db.execute(sql_delete(FileOperationLog))
    return {"success": True, "message": "日志已清空"}
