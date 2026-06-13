"""七牛云 Kodo 适配器"""
from qiniu import Auth, BucketManager, put_file, build_delete_marker_op
from datetime import datetime
from app.services.base import BaseStorageAdapter
from app.schemas.schemas import FileItem


class QiniuKodoAdapter(BaseStorageAdapter):
    """
    config fields:
        access_key, secret_key, bucket_name,
        custom_domain (optional), prefix (optional)
    """

    def _get_auth(self):
        return Auth(self.config["access_key"], self.config["secret_key"])

    def _get_bucket_manager(self):
        auth = self._get_auth()
        return BucketManager(auth)

    def _to_key(self, path: str) -> str:
        p = self.normalize_path(path).lstrip("/")
        prefix = self.config.get("prefix", "").strip("/")
        return f"{prefix}/{p}" if prefix else p

    def _get_prefix(self, path: str) -> str:
        p = self.normalize_path(path).lstrip("/")
        prefix = self.config.get("prefix", "").strip("/")
        if prefix:
            return f"{prefix}/{p}/" if p and p != "/" else f"{prefix}/"
        return f"{p}/" if p and p != "/" else ""

    async def list_files(self, path: str = "/") -> list[FileItem]:
        bm = self._get_bucket_manager()
        prefix = self._get_prefix(path)
        bucket = self.config["bucket_name"]
        files = []
        marker = None

        while True:
            ret, eof, info = bm.list(bucket, prefix=prefix, delimiter="/", marker=marker, limit=1000)
            if info.status_code != 200:
                break
            # Directories
            for cp in (ret.get("commonPrefixes", [])):
                dir_name = cp[len(prefix):].rstrip("/")
                if dir_name:
                    files.append(FileItem(name=dir_name, path=self.join_path(path, dir_name), is_dir=True))
            # Files
            for item in (ret.get("items", [])):
                name = item["key"][len(prefix):]
                if not name:
                    continue
                domain = self.config.get("custom_domain", "").rstrip("/")
                url = f"https://{domain}/{item['key']}" if domain else None
                files.append(FileItem(
                    name=name, path=self.join_path(path, name), is_dir=False,
                    size=item.get("fsize", 0),
                    last_modified=datetime.fromtimestamp(item.get("putTime", 0) / 1e7).strftime("%Y-%m-%d %H:%M:%S") if item.get("putTime") else None,
                    storage_type="qiniu", url=url,
                ))
            if eof:
                break
            marker = ret.get("marker")
        return files

    async def get_file_info(self, path: str) -> FileItem:
        bm = self._get_bucket_manager()
        key = self._to_key(path)
        ret, info = bm.stat(self.config["bucket_name"], key)
        if info.status_code != 200:
            raise Exception(f"文件不存在: {path}")
        domain = self.config.get("custom_domain", "").rstrip("/")
        url = f"https://{domain}/{key}" if domain else None
        return FileItem(
            name=path.split("/")[-1], path=path, is_dir=False,
            size=ret.get("fsize", 0),
            last_modified=datetime.fromtimestamp(ret.get("putTime", 0) / 1e7).strftime("%Y-%m-%d %H:%M:%S"),
            storage_type="qiniu", url=url,
        )

    async def get_download_url(self, path: str, expires: int = 3600) -> str:
        auth = self._get_auth()
        key = self._to_key(path)
        domain = self.config.get("custom_domain", "").rstrip("/")
        if domain:
            base_url = f"https://{domain}/{key}"
            return auth.private_download_url(base_url, expires=expires)
        # Fallback: use default domain
        return auth.private_download_url(f"https://{self.config['bucket_name']}.qiniudn.com/{key}", expires=expires)

    async def upload_file(self, local_path: str, remote_path: str) -> FileItem:
        auth = self._get_auth()
        token = auth.upload_token(self.config["bucket_name"])
        key = self._to_key(remote_path)
        ret, info = put_file(token, key, local_path)
        if info.status_code != 200:
            raise Exception(f"上传失败: {info.text_body}")
        return await self.get_file_info(remote_path)

    async def delete_file(self, path: str) -> bool:
        bm = self._get_bucket_manager()
        ret, info = bm.delete(self.config["bucket_name"], self._to_key(path))
        return info.status_code in (200, 612)  # 612 = no such key (already deleted)

    async def delete_folder(self, path: str) -> bool:
        files = await self.list_files(path)
        bm = self._get_bucket_manager()
        bucket = self.config["bucket_name"]
        ops = []
        for f in files:
            if f.is_dir:
                await self.delete_folder(f.path)
            else:
                ops.append(build_delete_marker_op(self._to_key(f.path)))
        if ops:
            ret, info = bm.batch(ops)
        return True

    async def create_folder(self, path: str) -> bool:
        auth = self._get_auth()
        token = auth.upload_token(self.config["bucket_name"])
        key = self._to_key(path).rstrip("/") + "/"
        # Qiniu doesn't have real folders, create a 0-byte marker
        ret, info = put_file(token, key, local_file=None, data=b"")
        return info.status_code in (200, 614)  # 614 = file exists

    async def move_file(self, src_path: str, dest_path: str) -> bool:
        bm = self._get_bucket_manager()
        ret, info = bm.move(
            self.config["bucket_name"], self._to_key(src_path),
            self.config["bucket_name"], self._to_key(dest_path),
        )
        return info.status_code == 200

    async def copy_file(self, src_path: str, dest_path: str) -> bool:
        bm = self._get_bucket_manager()
        ret, info = bm.copy(
            self.config["bucket_name"], self._to_key(src_path),
            self.config["bucket_name"], self._to_key(dest_path),
        )
        return info.status_code == 200

    async def get_file_size(self, path: str) -> int:
        bm = self._get_bucket_manager()
        ret, info = bm.stat(self.config["bucket_name"], self._to_key(path))
        return ret.get("fsize", 0) if info.status_code == 200 else 0

    async def test_connection(self) -> dict:
        try:
            bm = self._get_bucket_manager()
            ret, eof, info = bm.list(self.config["bucket_name"], limit=1)
            if info.status_code == 200:
                return {"success": True, "message": "连接成功"}
            return {"success": False, "message": f"HTTP {info.status_code}"}
        except Exception as e:
            return {"success": False, "message": f"连接失败: {str(e)}"}
