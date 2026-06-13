"""用户管理 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_user, get_password_hash, verify_password
from app.models.models import User
from app.models.rbac import Role

router = APIRouter(prefix="/users", tags=["用户管理"])


def _check_admin(current_user: dict):
    if current_user.get("role_code") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")


async def _user_response(user: User, db: AsyncSession) -> dict:
    role_result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = role_result.scalar_one_or_none()
    return {
        "id": user.id,
        "username": user.username,
        "role_id": user.role_id,
        "role_name": role.name if role else "未知",
        "role_code": role.code if role else "guest",
        "enabled": user.enabled,
        "created_at": str(user.created_at) if user.created_at else None,
    }


class UserCreate(BaseModel):
    username: str
    password: str
    role_id: int = 2


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role_id: Optional[int] = None
    enabled: Optional[bool] = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


@router.get("/")
async def list_users(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    _check_admin(current_user)
    result = await db.execute(select(User).order_by(User.id))
    users = result.scalars().all()
    return [await _user_response(u, db) for u in users]


@router.post("/")
async def create_user(req: UserCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    _check_admin(current_user)
    dup = await db.execute(select(User).where(User.username == req.username))
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")
    # 验证角色存在
    role = (await db.execute(select(Role).where(Role.id == req.role_id))).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=400, detail="角色不存在")
    user = User(username=req.username, password_hash=get_password_hash(req.password), role_id=req.role_id)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return await _user_response(user, db)


@router.put("/{user_id}")
async def update_user(user_id: int, req: UserUpdate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    _check_admin(current_user)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if req.username is not None:
        dup = await db.execute(select(User).where(User.username == req.username, User.id != user_id))
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="用户名已存在")
        user.username = req.username
    if req.password is not None:
        user.password_hash = get_password_hash(req.password)
    if req.role_id is not None:
        role = (await db.execute(select(Role).where(Role.id == req.role_id))).scalar_one_or_none()
        if not role:
            raise HTTPException(status_code=400, detail="角色不存在")
        user.role_id = req.role_id
    if req.enabled is not None:
        user.enabled = req.enabled
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return await _user_response(user, db)


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    _check_admin(current_user)
    if user_id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="不能删除自己")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    await db.delete(user)
    return {"success": True, "message": "已删除"}


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == current_user["user_id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return await _user_response(user, db)


@router.put("/me/password")
async def change_my_password(req: PasswordChange, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(User).where(User.id == current_user["user_id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if not verify_password(req.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    user.password_hash = get_password_hash(req.new_password)
    db.add(user)
    return {"success": True, "message": "密码已修改"}
