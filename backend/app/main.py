"""UniFile — 统一文件管理平台"""
import os
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from app.core.config import settings
from app.core.database import init_db, async_session
from app.core.security import get_password_hash, get_current_user
from app.models.models import User
from app.models.rbac import Role, Menu  # noqa: F401
from app.api import auth, storages, files, shares, settings as settings_api, users, logs, roles, menus, dashboard, login_logs, home, backups

# 上传目录
UPLOAD_DIR = os.path.expanduser("~/.unifile/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


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

# 静态文件服务（上传的图片等）
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

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


@app.post("/api/settings/upload-image")
async def upload_site_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """上传站点图片（Logo/Favicon）"""
    allowed = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".ico", ".svg"}
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed:
        raise HTTPException(400, f"不支持的图片格式，仅允许: {', '.join(allowed)}")
    filename = f"site_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    return {"url": f"/uploads/{filename}"}


@app.get("/api/health")
async def health():
    return {"status": "ok", "name": settings.APP_NAME, "version": settings.APP_VERSION}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
