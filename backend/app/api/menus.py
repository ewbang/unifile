"""菜单管理 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.rbac import Menu

router = APIRouter(prefix="/menus", tags=["菜单管理"])


def _check_admin(current_user: dict):
    if current_user.get("role_code") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")


def _menu_response(menu: Menu) -> dict:
    return {
        "id": menu.id,
        "parent_id": menu.parent_id,
        "name": menu.name,
        "menu_type": menu.menu_type,
        "permission_code": menu.permission_code,
        "path": menu.path,
        "icon": menu.icon,
        "sort_order": menu.sort_order,
        "visible": menu.visible,
    }


class MenuCreate(BaseModel):
    parent_id: int = 0
    name: str
    menu_type: str = "menu"  # menu or button
    permission_code: str
    path: str = ""
    icon: str = ""
    sort_order: int = 0
    visible: bool = True


class MenuUpdate(BaseModel):
    parent_id: Optional[int] = None
    name: Optional[str] = None
    menu_type: Optional[str] = None
    permission_code: Optional[str] = None
    path: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    visible: Optional[bool] = None


@router.get("/")
async def list_menus(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    _check_admin(current_user)
    result = await db.execute(select(Menu).order_by(Menu.sort_order))
    menus = result.scalars().all()
    return [_menu_response(m) for m in menus]


@router.post("/")
async def create_menu(req: MenuCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    _check_admin(current_user)
    dup = await db.execute(select(Menu).where(Menu.permission_code == req.permission_code))
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="权限标识已存在")
    menu = Menu(**req.model_dump())
    db.add(menu)
    await db.flush()
    await db.refresh(menu)
    return _menu_response(menu)


@router.put("/{menu_id}")
async def update_menu(menu_id: int, req: MenuUpdate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    _check_admin(current_user)
    result = await db.execute(select(Menu).where(Menu.id == menu_id))
    menu = result.scalar_one_or_none()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    for key, val in req.model_dump(exclude_unset=True).items():
        setattr(menu, key, val)
    db.add(menu)
    await db.flush()
    await db.refresh(menu)
    return _menu_response(menu)


@router.delete("/{menu_id}")
async def delete_menu(menu_id: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    _check_admin(current_user)
    result = await db.execute(select(Menu).where(Menu.id == menu_id))
    menu = result.scalar_one_or_none()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    await db.delete(menu)
    return {"success": True, "message": "已删除"}
