"""UniFile — 统一文件管理平台 (module entry point)"""
import sys
from pathlib import Path

# Add the backend directory to Python path to ensure 'app' can be imported
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Import and run the main application
from app.main import app
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
