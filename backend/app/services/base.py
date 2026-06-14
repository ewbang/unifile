from abc import ABC, abstractmethod
from typing import Optional
import os
from app.schemas.schemas import FileItem


class BaseStorageAdapter(ABC):
    """存储适配器抽象基类 — 所有存储类型必须实现这些方法"""

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    async def list_files(self, path: str = "/") -> list[FileItem]:
        """列出指定路径下的文件和目录"""
        pass

    @abstractmethod
    async def get_file_info(self, path: str) -> FileItem:
        """获取单个文件信息"""
        pass

    @abstractmethod
    async def get_download_url(self, path: str, expires: int = 3600) -> str:
        """获取文件下载URL"""
        pass

    @abstractmethod
    async def upload_file(self, local_path: str, remote_path: str) -> FileItem:
        """上传文件"""
        pass

    @abstractmethod
    async def delete_file(self, path: str) -> bool:
        """删除文件"""
        pass

    @abstractmethod
    async def delete_folder(self, path: str) -> bool:
        """删除文件夹"""
        pass

    @abstractmethod
    async def create_folder(self, path: str) -> bool:
        """创建文件夹"""
        pass

    @abstractmethod
    async def move_file(self, src_path: str, dest_path: str) -> bool:
        """移动/重命名文件"""
        pass

    @abstractmethod
    async def copy_file(self, src_path: str, dest_path: str) -> bool:
        """复制文件"""
        pass

    @abstractmethod
    async def get_file_size(self, path: str) -> int:
        """获取文件大小(bytes)"""
        pass

    @abstractmethod
    async def test_connection(self) -> dict:
        """测试连接是否正常，返回 {success: bool, message: str}"""
        pass

    async def get_upload_url(self, remote_path: str, expires: int = 3600) -> Optional[dict]:
        """获取预签名上传URL，用于前端直传
        返回: {url, method, headers} 或 None (不支持直传)
        """
        return None

    @staticmethod
    def normalize_path(path: str) -> str:
        """标准化路径：确保以/开头，不以/结尾(除非是根路径)"""
        if not path:
            path = "/"
        if not path.startswith("/"):
            path = "/" + path
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")
        return path

    @staticmethod
    def join_path(*parts: str) -> str:
        """拼接路径"""
        result = "/".join(p.strip("/") for p in parts if p.strip("/"))
        return "/" + result if result else "/"
