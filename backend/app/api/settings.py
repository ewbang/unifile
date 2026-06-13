"""站点设置 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import SiteSettings

router = APIRouter(prefix="/settings", tags=["站点设置"])

# 默认配置项
DEFAULT_SETTINGS = {
    "site_name": "UniFile",
    "site_description": "统一文件管理系统",
    "site_logo": "",
    "site_favicon": "",
    "icp_number": "",
    "footer_text": "",
    "public_url": "",
    "allow_register": "true",
    "default_theme": "light",
}


class SettingsUpdate(BaseModel):
    settings: dict[str, Optional[str]]


@router.get("/")
async def get_settings(db: AsyncSession = Depends(get_db)):
    """获取所有站点设置（公开接口）"""
    result = await db.execute(select(SiteSettings))
    rows = result.scalars().all()
    settings = {row.key: row.value for row in rows}
    # 合并默认值
    for key, default in DEFAULT_SETTINGS.items():
        if key not in settings:
            settings[key] = default
    return settings


@router.put("/")
async def update_settings(
    req: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """更新站点设置（需要登录）"""
    for key, value in req.settings.items():
        result = await db.execute(select(SiteSettings).where(SiteSettings.key == key))
        row = result.scalar_one_or_none()
        if row:
            row.value = value
        else:
            row = SiteSettings(key=key, value=value)
            db.add(row)
    await db.flush()
    return {"success": True, "message": "设置已保存"}


@router.get("/public")
async def get_public_settings(db: AsyncSession = Depends(get_db)):
    """获取公开设置（无需登录，用于页面展示）"""
    public_keys = ["site_name", "site_description", "site_logo", "site_favicon", "icp_number", "footer_text"]
    result = await db.execute(select(SiteSettings).where(SiteSettings.key.in_(public_keys)))
    rows = result.scalars().all()
    settings = {row.key: row.value for row in rows}
    for key in public_keys:
        if key not in settings:
            settings[key] = DEFAULT_SETTINGS.get(key, "")
    return settings
