"""UniFile — 统一文件管理平台"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from app.core.config import settings
from app.core.database import init_db, async_session
from app.core.security import get_password_hash
from app.models.models import User
from app.models.rbac import Role, Menu  # noqa: F401
from app.api import auth, storages, files, shares, settings as settings_api, users, logs, roles, menus, dashboard, login_logs, home, backups


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init database + seed admin user
    await init_db()
    async with async_session() as db:
        result = await db.execute(select(User).where(User.username == "admin"))
        if not result.scalar_one_or_none():
            admin = User(username="admin", password_hash=get_password_hash("admin123"), role_id=1)
            db.add(admin)
            await db.commit()
            print("✅ 默认管理员已创建: admin / admin123")
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动完成")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api")
app.include_router(storages.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(shares.router, prefix="/api")
app.include_router(settings_api.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(roles.router, prefix="/api")
app.include_router(menus.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(login_logs.router, prefix="/api")
app.include_router(home.router, prefix="/api")
app.include_router(backups.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "name": settings.APP_NAME, "version": settings.APP_VERSION}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
