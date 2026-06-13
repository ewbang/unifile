from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import select
from app.core.config import settings

DATABASE_URL = f"sqlite+aiosqlite:///{settings.DB_PATH}"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    # 导入所有模型确保表被创建
    from app.models.models import User, StorageSource, FileOperationLog, ShareLink, SiteSettings
    from app.models.rbac import Role, Menu, role_menu_table

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 种子数据
    async with async_session() as db:
        await _seed_roles_and_menus(db)
        await _ensure_admin_user(db)
        await db.commit()


async def _seed_roles_and_menus(db: AsyncSession):
    """初始化默认角色和菜单"""
    from app.models.rbac import Role, Menu
    # 检查是否已有数据
    result = await db.execute(select(Role).limit(1))
    if result.scalar_one_or_none():
        return  # 已初始化

    # 创建菜单
    menus_data = [
        # 顶级菜单
        {"id": 1, "parent_id": 0, "name": "控制台", "menu_type": "menu", "permission_code": "dashboard", "path": "/admin/dashboard", "icon": "Odometer", "sort_order": 1},
        {"id": 2, "parent_id": 0, "name": "存储管理", "menu_type": "menu", "permission_code": "storage", "path": "/admin/storages", "icon": "Box", "sort_order": 2},
        {"id": 3, "parent_id": 0, "name": "分享管理", "menu_type": "menu", "permission_code": "share_manage", "path": "/admin/shares", "icon": "Share", "sort_order": 3},
        {"id": 4, "parent_id": 0, "name": "站点设置", "menu_type": "menu", "permission_code": "settings", "path": "/admin/settings", "icon": "Setting", "sort_order": 4},
        {"id": 5, "parent_id": 0, "name": "用户管理", "menu_type": "menu", "permission_code": "user_manage", "path": "/admin/users", "icon": "User", "sort_order": 5},
        {"id": 6, "parent_id": 0, "name": "角色管理", "menu_type": "menu", "permission_code": "role_manage", "path": "/admin/roles", "icon": "UserFilled", "sort_order": 6},
        {"id": 7, "parent_id": 0, "name": "菜单管理", "menu_type": "menu", "permission_code": "menu_manage", "path": "/admin/menus", "icon": "Menu", "sort_order": 7},
        {"id": 8, "parent_id": 0, "name": "操作日志", "menu_type": "menu", "permission_code": "logs", "path": "/admin/logs", "icon": "Document", "sort_order": 8},
        {"id": 9, "parent_id": 0, "name": "登录日志", "menu_type": "menu", "permission_code": "login_logs", "path": "/admin/login-logs", "icon": "Monitor", "sort_order": 9},
        {"id": 10, "parent_id": 0, "name": "备份管理", "menu_type": "menu", "permission_code": "backup_manage", "path": "/admin/backups", "icon": "FolderChecked", "sort_order": 10},
        # 文件操作按钮权限
        {"id": 101, "parent_id": 2, "name": "新建文件夹", "menu_type": "button", "permission_code": "file.mkdir", "sort_order": 1},
        {"id": 102, "parent_id": 2, "name": "上传文件", "menu_type": "button", "permission_code": "file.upload", "sort_order": 2},
        {"id": 103, "parent_id": 2, "name": "预览文件", "menu_type": "button", "permission_code": "file.preview", "sort_order": 3},
        {"id": 104, "parent_id": 2, "name": "下载文件", "menu_type": "button", "permission_code": "file.download", "sort_order": 4},
        {"id": 105, "parent_id": 2, "name": "复制下载链接", "menu_type": "button", "permission_code": "file.copy_link", "sort_order": 5},
        {"id": 106, "parent_id": 2, "name": "重命名", "menu_type": "button", "permission_code": "file.rename", "sort_order": 6},
        {"id": 107, "parent_id": 2, "name": "复制文件", "menu_type": "button", "permission_code": "file.copy", "sort_order": 7},
        {"id": 108, "parent_id": 2, "name": "移动文件", "menu_type": "button", "permission_code": "file.move", "sort_order": 8},
        {"id": 109, "parent_id": 2, "name": "删除文件", "menu_type": "button", "permission_code": "file.delete", "sort_order": 9},
        {"id": 110, "parent_id": 2, "name": "获取直链", "menu_type": "button", "permission_code": "file.direct_link", "sort_order": 10},
        {"id": 111, "parent_id": 2, "name": "创建分享链接", "menu_type": "button", "permission_code": "file.create_share", "sort_order": 11},
        # 存储管理按钮权限
        {"id": 112, "parent_id": 2, "name": "添加存储源", "menu_type": "button", "permission_code": "storage.create", "sort_order": 12},
        {"id": 113, "parent_id": 2, "name": "编辑存储源", "menu_type": "button", "permission_code": "storage.edit", "sort_order": 13},
        {"id": 114, "parent_id": 2, "name": "删除存储源", "menu_type": "button", "permission_code": "storage.delete", "sort_order": 14},
        {"id": 115, "parent_id": 2, "name": "启停存储源", "menu_type": "button", "permission_code": "storage.toggle", "sort_order": 15},
        {"id": 116, "parent_id": 2, "name": "测试连接", "menu_type": "button", "permission_code": "storage.test", "sort_order": 16},
    ]
    for m in menus_data:
        db.add(Menu(**m))
    await db.flush()

    # 创建角色
    # 管理员 - 拥有全部菜单
    all_menus = (await db.execute(select(Menu))).scalars().all()
    admin_role = Role(id=1, name="管理员", code="admin", description="系统管理员，拥有全部权限", is_system=True, sort_order=1)
    admin_role.menus = list(all_menus)
    db.add(admin_role)

    # 普通用户 - 拥有文件操作相关菜单，不含系统管理
    normal_user = Role(id=2, name="普通用户", code="user", description="普通用户，可浏览和操作文件", is_system=True, sort_order=2)
    normal_menus = [m for m in all_menus if m.permission_code.startswith("file.") or m.permission_code.startswith("storage.") or m.permission_code in ("dashboard", "storage", "share_manage")]
    normal_user.menus = normal_menus
    db.add(normal_user)

    # 游客 - 只能浏览和下载
    guest_role = Role(id=3, name="游客", code="guest", description="游客用户，仅可浏览和下载", is_system=True, sort_order=3)
    guest_menus = [m for m in all_menus if m.permission_code in ("dashboard", "storage", "file.preview", "file.download", "file.copy_link")]
    guest_role.menus = guest_menus
    db.add(guest_role)

    await db.flush()


async def _ensure_admin_user(db: AsyncSession):
    """确保admin用户存在且角色为管理员"""
    from app.models.models import User
    result = await db.execute(select(User).where(User.username == "admin"))
    admin = result.scalar_one_or_none()
    if admin:
        admin.role_id = 1  # 确保是管理员角色
        db.add(admin)
    else:
        from app.core.security import get_password_hash
        admin = User(username="admin", password_hash=get_password_hash("admin123"), role_id=1)
        db.add(admin)
