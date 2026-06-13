"""认证 API"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, get_current_user
from app.models.models import User
from app.models.rbac import Role, Menu
from app.models.models import LoginLog

router = APIRouter(prefix="/auth", tags=["认证"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(req: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    ip = request.client.host if request.client else ""
    ua = request.headers.get("user-agent", "")[:500]
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        # 记录失败日志
        db.add(LoginLog(username=req.username, ip_address=ip, user_agent=ua, status="failed", message="用户名或密码错误"))
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not user.enabled:
        db.add(LoginLog(username=req.username, ip_address=ip, user_agent=ua, status="failed", message="账号已被停用"))
        await db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被停用")
    # 获取角色信息
    role_result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = role_result.scalar_one_or_none()
    role_code = role.code if role else "guest"
    token = create_access_token({"sub": str(user.id), "username": user.username, "role_id": user.role_id, "role_code": role_code})
    # 记录成功日志
    db.add(LoginLog(username=req.username, ip_address=ip, user_agent=ua, status="success"))
    await db.commit()
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == current_user["user_id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    # 获取角色
    role_result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = role_result.scalar_one_or_none()
    role_name = role.name if role else "未知"
    role_code = role.code if role else "guest"
    return {
        "id": user.id,
        "username": user.username,
        "role_id": user.role_id,
        "role_name": role_name,
        "role_code": role_code,
        "enabled": user.enabled,
        "created_at": str(user.created_at) if user.created_at else None,
    }


@router.get("/permissions")
async def get_permissions(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取当前用户的权限列表和菜单"""
    # 管理员拥有全部权限
    if current_user.get("role_code") == "admin":
        result = await db.execute(select(Menu))
        menus = result.scalars().all()
        menu_list = [
            {"id": m.id, "parent_id": m.parent_id, "name": m.name, "menu_type": m.menu_type,
             "permission_code": m.permission_code, "path": m.path, "icon": m.icon, "sort_order": m.sort_order}
            for m in menus
        ]
        return {"role_code": "admin", "permissions": [m.permission_code for m in menus], "menus": menu_list}
    # 普通用户：根据角色获取权限
    user_result = await db.execute(select(User).where(User.id == current_user["user_id"]))
    user = user_result.scalar_one_or_none()
    if not user:
        return {"role_code": "guest", "permissions": [], "menus": []}
    role_result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = role_result.scalar_one_or_none()
    if not role:
        return {"role_code": "guest", "permissions": [], "menus": []}
    perm_codes = [m.permission_code for m in role.menus]
    menu_list = [
        {"id": m.id, "parent_id": m.parent_id, "name": m.name, "menu_type": m.menu_type,
         "permission_code": m.permission_code, "path": m.path, "icon": m.icon, "sort_order": m.sort_order}
        for m in role.menus
    ]
    return {"role_code": role.code, "permissions": perm_codes, "menus": menu_list}
