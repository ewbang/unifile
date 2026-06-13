"""RBAC 角色管理 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.rbac import Role, Menu, role_menu_table

router = APIRouter(prefix="/roles", tags=["角色管理"])


def _check_admin(current_user: dict):
    if current_user.get("role_code") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")


def _role_response(role: Role) -> dict:
    return {
        "id": role.id,
        "name": role.name,
        "code": role.code,
        "description": role.description,
        "is_system": role.is_system,
        "sort_order": role.sort_order,
        "menu_ids": [m.id for m in role.menus],
        "created_at": str(role.created_at) if role.created_at else None,
    }


class RoleCreate(BaseModel):
    name: str
    code: str
    description: str = ""
    sort_order: int = 0
    menu_ids: list[int] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    menu_ids: Optional[list[int]] = None


@router.get("/")
async def list_roles(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    _check_admin(current_user)
    result = await db.execute(select(Role).order_by(Role.sort_order))
    roles = result.scalars().all()
    return [_role_response(r) for r in roles]


@router.post("/")
async def create_role(req: RoleCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    _check_admin(current_user)
    dup = await db.execute(select(Role).where((Role.name == req.name) | (Role.code == req.code)))
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="角色名或编码已存在")
    role = Role(name=req.name, code=req.code, description=req.description, sort_order=req.sort_order)
    if req.menu_ids:
        menus = (await db.execute(select(Menu).where(Menu.id.in_(req.menu_ids)))).scalars().all()
        role.menus = list(menus)
    db.add(role)
    await db.flush()
    await db.refresh(role)
    return _role_response(role)


@router.put("/{role_id}")
async def update_role(role_id: int, req: RoleUpdate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    _check_admin(current_user)
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    if req.name is not None:
        role.name = req.name
    if req.description is not None:
        role.description = req.description
    if req.sort_order is not None:
        role.sort_order = req.sort_order
    if req.menu_ids is not None:
        menus = (await db.execute(select(Menu).where(Menu.id.in_(req.menu_ids)))).scalars().all()
        role.menus = list(menus)
    db.add(role)
    await db.flush()
    await db.refresh(role)
    return _role_response(role)


@router.delete("/{role_id}")
async def delete_role(role_id: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    _check_admin(current_user)
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    if role.is_system:
        raise HTTPException(status_code=400, detail="系统内置角色不可删除")
    await db.delete(role)
    return {"success": True, "message": "已删除"}


@router.get("/menus")
async def list_menus_for_role(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """获取完整菜单树（供角色分配用）"""
    result = await db.execute(select(Menu).order_by(Menu.sort_order))
    menus = result.scalars().all()
    return [{"id": m.id, "parent_id": m.parent_id, "name": m.name, "menu_type": m.menu_type, "permission_code": m.permission_code} for m in menus]
