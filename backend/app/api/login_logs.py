"""登录日志 API"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete as sql_delete
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import LoginLog

router = APIRouter(prefix="/login-logs", tags=["登录日志"])


def _check_admin(current_user: dict):
    from fastapi import HTTPException
    if current_user.get("role_code") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")


@router.get("/")
async def list_login_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    username: str = Query(None),
    status: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取登录日志"""
    _check_admin(current_user)
    q = select(LoginLog)
    count_q = select(func.count(LoginLog.id))
    if username:
        q = q.where(LoginLog.username.contains(username))
        count_q = count_q.where(LoginLog.username.contains(username))
    if status:
        q = q.where(LoginLog.status == status)
        count_q = count_q.where(LoginLog.status == status)
    total = (await db.execute(count_q)).scalar() or 0
    q = q.order_by(LoginLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    logs = result.scalars().all()
    items = []
    for log in logs:
        items.append({
            "id": log.id,
            "username": log.username,
            "ip_address": log.ip_address or "-",
            "user_agent": log.user_agent or "-",
            "status": log.status,
            "message": log.message or "",
            "created_at": str(log.created_at) if log.created_at else None,
        })
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/stats")
async def login_log_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """登录日志统计"""
    _check_admin(current_user)
    total = (await db.execute(select(func.count(LoginLog.id)))).scalar() or 0
    success = (await db.execute(select(func.count(LoginLog.id)).where(LoginLog.status == "success"))).scalar() or 0
    failed = (await db.execute(select(func.count(LoginLog.id)).where(LoginLog.status == "failed"))).scalar() or 0
    return {"total": total, "success": success, "failed": failed}


@router.delete("/clear")
async def clear_login_logs(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """清空登录日志"""
    _check_admin(current_user)
    await db.execute(sql_delete(LoginLog))
    return {"success": True, "message": "登录日志已清空"}
