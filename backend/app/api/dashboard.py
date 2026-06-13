"""控制台统计 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import StorageSource, ShareLink, User, FileOperationLog

router = APIRouter(prefix="/dashboard", tags=["控制台"])


@router.get("/stats")
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """控制台统计数据"""
    storage_count = (await db.execute(select(func.count(StorageSource.id)))).scalar() or 0
    storage_enabled = (await db.execute(select(func.count(StorageSource.id)).where(StorageSource.enabled == True))).scalar() or 0
    share_count = (await db.execute(select(func.count(ShareLink.id)))).scalar() or 0
    share_active = (await db.execute(select(func.count(ShareLink.id)).where(ShareLink.enabled == True))).scalar() or 0
    user_count = (await db.execute(select(func.count(User.id)))).scalar() or 0
    log_count = (await db.execute(select(func.count(FileOperationLog.id)))).scalar() or 0

    # 最近操作
    recent_q = await db.execute(
        select(FileOperationLog)
        .order_by(FileOperationLog.created_at.desc())
        .limit(5)
    )
    recent_logs = []
    for log in recent_q.scalars().all():
        recent_logs.append({
            "id": log.id,
            "username": log.username or "-",
            "operation": log.operation,
            "file_name": log.file_name or log.file_path.split("/")[-1],
            "created_at": str(log.created_at) if log.created_at else None,
        })

    return {
        "storage_count": storage_count,
        "storage_enabled": storage_enabled,
        "share_count": share_count,
        "share_active": share_active,
        "user_count": user_count,
        "log_count": log_count,
        "recent_logs": recent_logs,
    }
