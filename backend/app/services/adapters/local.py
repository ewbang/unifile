"""本地文件系统适配器"""
import os
import shutil
import aiofiles
from datetime import datetime
from app.services.base import BaseStorageAdapter
from app.schemas.schemas import FileItem


class LocalStorageAdapter(BaseStorageAdapter):
    """
    config fields:
        root_path  — 本地文件系统根目录
    """

    @property
    def root(self) -> str:
        root = self.config.get("root_path", "/tmp/unifile-local")
        os.makedirs(root, exist_ok=True)
        return os.path.abspath(root)

    def _real_path(self, path: str) -> str:
        """将虚拟路径映射到真实路径，并检查越界"""
        p = self.normalize_path(path)
        real = os.path.normpath(os.path.join(self.root, p.lstrip("/")))
        # Security: prevent path traversal
        if not real.startswith(self.root):
            raise ValueError("非法路径")
        return real

    async def list_files(self, path: str = "/") -> list[FileItem]:
        real_path = self._real_path(path)
        if not os.path.isdir(real_path):
            return []
        files = []
        for name in sorted(os.listdir(real_path)):
            full = os.path.join(real_path, name)
            is_dir = os.path.isdir(full)
            stat = os.stat(full)
            files.append(FileItem(
                name=name,
                path=self.join_path(path, name),
                is_dir=is_dir,
                size=stat.st_size if not is_dir else None,
                last_modified=datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                storage_type="local",
                url=None,
            ))
        return files

    async def get_file_info(self, path: str) -> FileItem:
        real_path = self._real_path(path)
        if not os.path.exists(real_path):
            raise FileNotFoundError(f"文件不存在: {path}")
        stat = os.stat(real_path)
        name = os.path.basename(real_path)
        return FileItem(
            name=name, path=path, is_dir=os.path.isdir(real_path),
            size=stat.st_size,
            last_modified=datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            storage_type="local",
        )

    async def get_download_url(self, path: str, expires: int = 3600) -> str:
        # For local files, return a special URL the backend can serve
        return f"/api/files/{self.config.get('_storage_id', 0)}/serve?path={path}"

    async def upload_file(self, local_path: str, remote_path: str) -> FileItem:
        real_path = self._real_path(remote_path)
        os.makedirs(os.path.dirname(real_path), exist_ok=True)
        shutil.copy2(local_path, real_path)
        return await self.get_file_info(remote_path)

    async def delete_file(self, path: str) -> bool:
        real_path = self._real_path(path)
        if os.path.isfile(real_path):
            os.remove(real_path)
            return True
        return False

    async def delete_folder(self, path: str) -> bool:
        real_path = self._real_path(path)
        if os.path.isdir(real_path):
            shutil.rmtree(real_path)
            return True
        return False

    async def create_folder(self, path: str) -> bool:
        real_path = self._real_path(path)
        os.makedirs(real_path, exist_ok=True)
        return True

    async def move_file(self, src_path: str, dest_path: str) -> bool:
        src = self._real_path(src_path)
        dest = self._real_path(dest_path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.move(src, dest)
        return True

    async def copy_file(self, src_path: str, dest_path: str) -> bool:
        src = self._real_path(src_path)
        dest = self._real_path(dest_path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if os.path.isdir(src):
            shutil.copytree(src, dest)
        else:
            shutil.copy2(src, dest)
        return True

    async def get_file_size(self, path: str) -> int:
        real_path = self._real_path(path)
        return os.path.getsize(real_path) if os.path.isfile(real_path) else 0

    async def test_connection(self) -> dict:
        try:
            root = self.root
            if os.path.isdir(root):
                return {"success": True, "message": f"目录可访问: {root}"}
            return {"success": False, "message": f"目录不存在: {root}"}
        except Exception as e:
            return {"success": False, "message": f"错误: {str(e)}"}
