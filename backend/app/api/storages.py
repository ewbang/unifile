"""存储源管理 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import StorageSource
from app.schemas.schemas import StorageSourceCreate, StorageSourceUpdate, StorageSourceResponse
from app.services.factory import STORAGE_TYPE_FIELDS, create_adapter
from app.schemas.schemas import StorageTypeInfo

router = APIRouter(prefix="/storages", tags=["存储源管理"])


@router.get("/types", response_model=list[StorageTypeInfo])
async def get_storage_types():
    """获取所有支持的存储类型及其配置字段"""
    return [StorageTypeInfo(**v) for v in STORAGE_TYPE_FIELDS.values()]


@router.get("/", response_model=list[StorageSourceResponse])
async def list_storages(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(StorageSource).order_by(StorageSource.sort_order, StorageSource.id))
    sources = result.scalars().all()
    # Hide sensitive fields in response
    items = []
    for s in sources:
        item = StorageSourceResponse.model_validate(s)
        # Mask secrets
        safe_config = {}
        fields_def = STORAGE_TYPE_FIELDS.get(s.storage_type, {}).get("fields", [])
        secret_keys = {f["key"] for f in fields_def if f.get("secret")}
        for k, v in item.config.items():
            safe_config[k] = "******" if k in secret_keys else v
        item.config = safe_config
        items.append(item)
    return items


@router.get("/{storage_id}", response_model=StorageSourceResponse)
async def get_storage(
    storage_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(StorageSource).where(StorageSource.id == storage_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="存储源不存在")
    return StorageSourceResponse.model_validate(source)


@router.post("/", response_model=StorageSourceResponse)
async def create_storage(
    req: StorageSourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    source = StorageSource(
        name=req.name,
        storage_type=req.storage_type,
        config=req.config,
        icon=req.icon,
        color=req.color,
        sort_order=req.sort_order,
        description=req.description,
        is_public=req.is_public,
    )
    db.add(source)
    await db.flush()
    await db.refresh(source)
    return StorageSourceResponse.model_validate(source)


@router.put("/{storage_id}", response_model=StorageSourceResponse)
async def update_storage(
    storage_id: int,
    req: StorageSourceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(StorageSource).where(StorageSource.id == storage_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="存储源不存在")
    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "config" and value:
            # Merge config — preserve existing keys not in update
            merged = {**(source.config or {}), **value}
            # Remove keys that are explicitly set to empty string (clear field)
            source.config = {k: v for k, v in merged.items() if v != ""}
        else:
            setattr(source, key, value)
    db.add(source)
    await db.flush()
    await db.refresh(source)
    return StorageSourceResponse.model_validate(source)


@router.delete("/{storage_id}")
async def delete_storage(
    storage_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(StorageSource).where(StorageSource.id == storage_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="存储源不存在")
    await db.delete(source)
    return {"success": True, "message": "已删除"}


@router.post("/{storage_id}/test")
async def test_storage_connection(
    storage_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(StorageSource).where(StorageSource.id == storage_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="存储源不存在")
    try:
        adapter = create_adapter(source.storage_type, source.config)
        return await adapter.test_connection()
    except ImportError as e:
        return {"success": False, "message": str(e)}
    except Exception as e:
        return {"success": False, "message": f"错误: {str(e)}"}


@router.put("/{storage_id}/toggle")
async def toggle_storage(
    storage_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(StorageSource).where(StorageSource.id == storage_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="存储源不存在")
    source.enabled = not source.enabled
    db.add(source)
    return {"success": True, "enabled": source.enabled}
