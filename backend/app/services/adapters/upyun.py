"""又拍云 USS 适配器"""
import httpx
import hashlib
import base64
import time
from datetime import datetime
from app.services.base import BaseStorageAdapter
from app.schemas.schemas import FileItem


class UpyunUSSAdapter(BaseStorageAdapter):
    """
    config fields:
        operator_name, operator_password, bucket_name,
        domain (optional), prefix (optional)
    """

    BASE_URL = "https://v0.api.upyun.com"

    def _auth_header(self) -> dict:
        operator = self.config["operator_name"]
        password = self.config["operator_password"]
        auth_str = f"{operator}:{password}"
        b64 = base64.b64encode(auth_str.encode()).decode()
        return {"Authorization": f"Basic {b64}"}

    def _to_path(self, remote_path: str) -> str:
        p = self.normalize_path(remote_path)
        prefix = self.config.get("prefix", "").strip("/")
        if prefix:
            return f"/{prefix}{p}" if p != "/" else f"/{prefix}"
        return p

    async def list_files(self, path: str = "/") -> list[FileItem]:
        url_path = self._to_path(path)
        bucket = self.config["bucket_name"]
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/{bucket}{url_path}",
                headers=self._auth_header(),
                params={"accept": "json"},
            )
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()
        files = []
        for item in data.get("files", []):
            name = item["name"]
            is_dir = item.get("type") == "F"
            full_path = self.join_path(path, name)
            if is_dir:
                files.append(FileItem(name=name, path=full_path, is_dir=True))
            else:
                domain = self.config.get("domain", "").rstrip("/")
                url = f"https://{domain}{self._to_path(full_path)}" if domain else None
                files.append(FileItem(
                    name=name, path=full_path, is_dir=False,
                    size=int(item.get("size", 0)),
                    last_modified=datetime.fromtimestamp(int(item.get("time", 0))).strftime("%Y-%m-%d %H:%M:%S") if item.get("time") else None,
                    storage_type="upyun", url=url,
                ))
        return files

    async def get_file_info(self, path: str) -> FileItem:
        url_path = self._to_path(path)
        bucket = self.config["bucket_name"]
        async with httpx.AsyncClient() as client:
            resp = await client.head(
                f"{self.BASE_URL}/{bucket}{url_path}",
                headers=self._auth_header(),
            )
        resp.raise_for_status()
        domain = self.config.get("domain", "").rstrip("/")
        url = f"https://{domain}{url_path}" if domain else None
        return FileItem(
            name=path.split("/")[-1], path=path, is_dir=False,
            size=int(resp.headers.get("x-upyun-file-size", 0)),
            last_modified=resp.headers.get("x-upyun-file-date", ""),
            storage_type="upyun", url=url,
        )

    async def get_download_url(self, path: str, expires: int = 3600) -> str:
        url_path = self._to_path(path)
        domain = self.config.get("domain", "").rstrip("/")
        if domain:
            return f"https://{domain}{url_path}"
        bucket = self.config["bucket_name"]
        return f"{self.BASE_URL}/{bucket}{url_path}"

    async def upload_file(self, local_path: str, remote_path: str) -> FileItem:
        url_path = self._to_path(remote_path)
        bucket = self.config["bucket_name"]
        with open(local_path, "rb") as f:
            data = f.read()
        headers = {**self._auth_header(), "Content-Length": str(len(data))}
        async with httpx.AsyncClient() as client:
            resp = await client.put(
                f"{self.BASE_URL}/{bucket}{url_path}",
                headers=headers, content=data,
            )
        resp.raise_for_status()
        return await self.get_file_info(remote_path)

    async def delete_file(self, path: str) -> bool:
        url_path = self._to_path(path)
        bucket = self.config["bucket_name"]
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{self.BASE_URL}/{bucket}{url_path}",
                headers=self._auth_header(),
            )
        return resp.status_code in (200, 204)

    async def delete_folder(self, path: str) -> bool:
        # Recursively delete
        files = await self.list_files(path)
        for f in files:
            if f.is_dir:
                await self.delete_folder(f.path)
            else:
                await self.delete_file(f.path)
        url_path = self._to_path(path)
        bucket = self.config["bucket_name"]
        async with httpx.AsyncClient() as client:
            await client.delete(f"{self.BASE_URL}/{bucket}{url_path}", headers=self._auth_header())
        return True

    async def create_folder(self, path: str) -> bool:
        url_path = self._to_path(path)
        bucket = self.config["bucket_name"]
        headers = {**self._auth_header(), "folder": "true", "Content-Length": "0"}
        async with httpx.AsyncClient() as client:
            resp = await client.put(
                f"{self.BASE_URL}/{bucket}{url_path}",
                headers=headers,
            )
        return resp.status_code in (200, 201)

    async def move_file(self, src_path: str, dest_path: str) -> bool:
        # Upload + delete (USS has no native move)
        bucket = self.config["bucket_name"]
        src_url_path = self._to_path(src_path)
        dest_url_path = self._to_path(dest_path)
        headers = {**self._auth_header(), "x-upyun-move-source": f"/{bucket}{src_url_path}"}
        async with httpx.AsyncClient() as client:
            resp = await client.put(
                f"{self.BASE_URL}/{bucket}{dest_url_path}",
                headers=headers, content=b"",
            )
        return resp.status_code in (200, 201)

    async def copy_file(self, src_path: str, dest_path: str) -> bool:
        bucket = self.config["bucket_name"]
        src_url_path = self._to_path(src_path)
        dest_url_path = self._to_path(dest_path)
        headers = {**self._auth_header(), "x-upyun-copy-source": f"/{bucket}{src_url_path}"}
        async with httpx.AsyncClient() as client:
            resp = await client.put(
                f"{self.BASE_URL}/{bucket}{dest_url_path}",
                headers=headers, content=b"",
            )
        return resp.status_code in (200, 201)

    async def get_file_size(self, path: str) -> int:
        info = await self.get_file_info(path)
        return info.size or 0

    async def test_connection(self) -> dict:
        try:
            bucket = self.config["bucket_name"]
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.BASE_URL}/{bucket}/",
                    headers=self._auth_header(),
                )
            if resp.status_code == 200:
                return {"success": True, "message": "连接成功"}
            return {"success": False, "message": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as e:
            return {"success": False, "message": f"连接失败: {str(e)}"}
