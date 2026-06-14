"""华为云 OBS 适配器"""
from obs import ObsClient
from datetime import datetime
from app.services.base import BaseStorageAdapter
from app.schemas.schemas import FileItem


class HuaweiOBSAdapter(BaseStorageAdapter):
    """
    config fields:
        access_key_id, access_key_secret, bucket_name, endpoint,
        custom_domain (optional), prefix (optional)
    """

    def _get_client(self):
        return ObsClient(
            access_key_id=self.config["access_key_id"],
            access_key_secret=self.config["access_key_secret"],
            server=self.config["endpoint"],
        )

    def _get_prefix(self, path: str) -> str:
        p = self.normalize_path(path).lstrip("/")
        prefix = self.config.get("prefix", "").strip("/")
        if prefix:
            return f"{prefix}/{p}/" if p and p != "/" else f"{prefix}/"
        return f"{p}/" if p and p != "/" else ""

    def _to_key(self, path: str) -> str:
        p = self.normalize_path(path).lstrip("/")
        prefix = self.config.get("prefix", "").strip("/")
        return f"{prefix}/{p}" if prefix else p

    async def list_files(self, path: str = "/") -> list[FileItem]:
        client = self._get_client()
        prefix = self._get_prefix(path)
        bucket = self.config["bucket_name"]
        files = []
        seen_dirs = set()

        resp = client.listObjects(bucket, prefix=prefix, delimiter="/", max_keys=1000)
        if resp.status < 300:
            # Directories (common prefixes)
            for cp in (resp.body.commonPrefixes or []):
                dir_name = cp.prefix[len(prefix):].rstrip("/")
                if dir_name and dir_name not in seen_dirs:
                    seen_dirs.add(dir_name)
                    files.append(FileItem(name=dir_name, path=self.join_path(path, dir_name), is_dir=True))
            # Files
            for obj in (resp.body.contents or []):
                name = obj.key[len(prefix):]
                if not name:
                    continue
                domain = self.config.get("custom_domain", "").rstrip("/")
                url = f"https://{domain}/{obj.key}" if domain else None
                files.append(FileItem(
                    name=name, path=self.join_path(path, name), is_dir=False,
                    size=obj.size,
                    last_modified=obj.lastModified[:19].replace("T", " ") if obj.lastModified else None,
                    storage_type="huawei", url=url,
                ))
        client.close()
        return files

    async def get_file_info(self, path: str) -> FileItem:
        client = self._get_client()
        key = self._to_key(path)
        resp = client.getObjectMetadata(self.config["bucket_name"], key)
        client.close()
        domain = self.config.get("custom_domain", "").rstrip("/")
        url = f"https://{domain}/{key}" if domain else None
        # 解析 Last-Modified
        raw_date = resp.header.get("last-modified", "")
        last_modified = ""
        if raw_date:
            try:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(raw_date)
                last_modified = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                last_modified = raw_date[:19].replace("T", " ")
        return FileItem(
            name=path.split("/")[-1], path=path, is_dir=False,
            size=int(resp.header.get("content-length", 0)),
            last_modified=last_modified,
            storage_type="huawei", url=url,
        )

    async def get_download_url(self, path: str, expires: int = 3600) -> str:
        client = self._get_client()
        key = self._to_key(path)
        if self.config.get("custom_domain"):
            domain = self.config["custom_domain"].rstrip("/")
            client.close()
            return f"https://{domain}/{key}"
        resp = client.createSignedUrl(self.config["bucket_name"], key, expires=expires)
        client.close()
        return resp.signedUrl

    async def upload_file(self, local_path: str, remote_path: str) -> FileItem:
        client = self._get_client()
        key = self._to_key(remote_path)
        client.putFile(self.config["bucket_name"], key, local_path)
        client.close()
        return await self.get_file_info(remote_path)

    async def delete_file(self, path: str) -> bool:
        client = self._get_client()
        client.deleteObject(self.config["bucket_name"], self._to_key(path))
        client.close()
        return True

    async def delete_folder(self, path: str) -> bool:
        client = self._get_client()
        prefix = self._to_key(path).rstrip("/") + "/"
        bucket = self.config["bucket_name"]
        resp = client.listObjects(bucket, prefix=prefix, max_keys=1000)
        if resp.status < 300:
            for obj in (resp.body.contents or []):
                client.deleteObject(bucket, obj.key)
        client.close()
        return True

    async def create_folder(self, path: str) -> bool:
        client = self._get_client()
        key = self._to_key(path).rstrip("/") + "/"
        client.putObject(self.config["bucket_name"], key, content="")
        client.close()
        return True

    async def move_file(self, src_path: str, dest_path: str) -> bool:
        await self.copy_file(src_path, dest_path)
        await self.delete_file(src_path)
        return True

    async def copy_file(self, src_path: str, dest_path: str) -> bool:
        client = self._get_client()
        bucket = self.config["bucket_name"]
        client.copyObject(bucket, self._to_key(src_path), bucket, self._to_key(dest_path))
        client.close()
        return True

    async def get_file_size(self, path: str) -> int:
        client = self._get_client()
        resp = client.getObjectMetadata(self.config["bucket_name"], self._to_key(path))
        client.close()
        return int(resp.header.get("content-length", 0))

    async def test_connection(self) -> dict:
        try:
            client = self._get_client()
            resp = client.listObjects(self.config["bucket_name"], max_keys=1)
            client.close()
            if resp.status < 300:
                return {"success": True, "message": "连接成功"}
            return {"success": False, "message": f"HTTP {resp.status}"}
        except Exception as e:
            return {"success": False, "message": f"连接失败: {str(e)}"}

    async def get_upload_url(self, remote_path: str, expires: int = 3600) -> dict:
        client = self._get_client()
        key = self._to_key(remote_path)
        resp = client.createSignedUrl(self.config["bucket_name"], key, expires=expires, method="PUT")
        client.close()
        return {"url": resp.signedUrl, "method": "PUT", "headers": {}}
