"""百度云 BOS 适配器"""
from baidubce.services.bos.bos_client import BosClient
from baidubce.bce_client_configuration import BceClientConfiguration
from baidubce.auth.bce_credentials import BceCredentials
from datetime import datetime
from app.services.base import BaseStorageAdapter
from app.schemas.schemas import FileItem


class BaiduBOSAdapter(BaseStorageAdapter):
    """
    config fields:
        access_key_id, access_key_secret, bucket_name, endpoint,
        custom_domain (optional), prefix (optional)
    """

    def _get_client(self):
        config = BceClientConfiguration(
            credentials=BceCredentials(self.config["access_key_id"], self.config["access_key_secret"]),
            endpoint=self.config["endpoint"],
        )
        return BosClient(config)

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

        resp = client.list_objects(bucket, prefix=prefix, delimiter="/", max_keys=1000)
        for cp in (resp.common_prefixes or []):
            dir_name = cp.prefix[len(prefix):].rstrip("/")
            if dir_name and dir_name not in seen_dirs:
                seen_dirs.add(dir_name)
                files.append(FileItem(name=dir_name, path=self.join_path(path, dir_name), is_dir=True))
        for obj in (resp.contents or []):
            name = obj.key[len(prefix):]
            if not name:
                continue
            domain = self.config.get("custom_domain", "").rstrip("/")
            url = f"https://{domain}/{obj.key}" if domain else None
            files.append(FileItem(
                name=name, path=self.join_path(path, name), is_dir=False,
                size=obj.size,
                last_modified=str(obj.last_modified)[:19] if obj.last_modified else None,
                storage_type="baidu", url=url,
            ))
        return files

    async def get_file_info(self, path: str) -> FileItem:
        client = self._get_client()
        key = self._to_key(path)
        meta = client.get_object_meta_data(self.config["bucket_name"], key)
        domain = self.config.get("custom_domain", "").rstrip("/")
        url = f"https://{domain}/{key}" if domain else None
        return FileItem(
            name=path.split("/")[-1], path=path, is_dir=False,
            size=int(meta.metadata.content_length),
            storage_type="baidu", url=url,
        )

    async def get_download_url(self, path: str, expires: int = 3600) -> str:
        client = self._get_client()
        key = self._to_key(path)
        if self.config.get("custom_domain"):
            domain = self.config["custom_domain"].rstrip("/")
            return f"https://{domain}/{key}"
        from baidubce.utils import SampleUtils
        url = client.generate_pre_signed_url(self.config["bucket_name"], key, expiration=expires)
        return url

    async def upload_file(self, local_path: str, remote_path: str) -> FileItem:
        client = self._get_client()
        key = self._to_key(remote_path)
        client.put_object_from_file(self.config["bucket_name"], key, local_path)
        return await self.get_file_info(remote_path)

    async def delete_file(self, path: str) -> bool:
        client = self._get_client()
        client.delete_object(self.config["bucket_name"], self._to_key(path))
        return True

    async def delete_folder(self, path: str) -> bool:
        client = self._get_client()
        prefix = self._to_key(path).rstrip("/") + "/"
        bucket = self.config["bucket_name"]
        resp = client.list_objects(bucket, prefix=prefix, max_keys=1000)
        for obj in (resp.contents or []):
            client.delete_object(bucket, obj.key)
        return True

    async def create_folder(self, path: str) -> bool:
        client = self._get_client()
        key = self._to_key(path).rstrip("/") + "/"
        client.put_object(self.config["bucket_name"], key, "")
        return True

    async def move_file(self, src_path: str, dest_path: str) -> bool:
        await self.copy_file(src_path, dest_path)
        await self.delete_file(src_path)
        return True

    async def copy_file(self, src_path: str, dest_path: str) -> bool:
        client = self._get_client()
        bucket = self.config["bucket_name"]
        client.copy_object(bucket, self._to_key(src_path), bucket, self._to_key(dest_path))
        return True

    async def get_file_size(self, path: str) -> int:
        client = self._get_client()
        meta = client.get_object_meta_data(self.config["bucket_name"], self._to_key(path))
        return int(meta.metadata.content_length)

    async def test_connection(self) -> dict:
        try:
            client = self._get_client()
            client.list_objects(self.config["bucket_name"], max_keys=1)
            return {"success": True, "message": "连接成功"}
        except Exception as e:
            return {"success": False, "message": f"连接失败: {str(e)}"}
