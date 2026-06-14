"""阿里云 OSS 适配器"""
import oss2
from datetime import datetime
from app.services.base import BaseStorageAdapter
from app.schemas.schemas import FileItem


class AliyunOSSAdapter(BaseStorageAdapter):
    """
    config fields:
        access_key_id, access_key_secret, bucket_name, endpoint, 
        custom_domain (optional), prefix (optional)
    """

    def _get_client(self):
        auth = oss2.Auth(self.config["access_key_id"], self.config["access_key_secret"])
        return oss2.Bucket(auth, self.config["endpoint"], self.config["bucket_name"])

    def _get_prefix(self, path: str) -> str:
        p = self.normalize_path(path).lstrip("/")
        prefix = self.config.get("prefix", "").strip("/")
        if prefix:
            if p and p != "/":
                return f"{prefix}/{p}/"
            return f"{prefix}/"
        if p and p != "/":
            return f"{p}/"
        return ""

    async def list_files(self, path: str = "/") -> list[FileItem]:
        bucket = self._get_client()
        prefix = self._get_prefix(path)
        files = []
        seen_dirs = set()

        for obj in oss2.ObjectIterator(bucket, prefix=prefix, delimiter="/"):
            if obj.is_prefix():  # 目录
                dir_name = obj.key[len(prefix):].rstrip("/")
                if dir_name and dir_name not in seen_dirs:
                    seen_dirs.add(dir_name)
                    full_path = self.join_path(path, dir_name)
                    files.append(FileItem(name=dir_name, path=full_path, is_dir=True))
            else:  # 文件
                name = obj.key[len(prefix):]
                if not name:
                    continue
                full_path = self.join_path(path, name)
                domain = self.config.get("custom_domain", "").rstrip("/")
                url = f"https://{domain}/{obj.key}" if domain else None
                files.append(FileItem(
                    name=name,
                    path=full_path,
                    is_dir=False,
                    size=obj.size,
                    last_modified=datetime.fromtimestamp(obj.last_modified).strftime("%Y-%m-%d %H:%M:%S") if obj.last_modified else None,
                    storage_type="aliyun",
                    url=url,
                ))
        return files

    async def get_file_info(self, path: str) -> FileItem:
        bucket = self._get_client()
        key = self._to_key(path)
        head = bucket.head_object(key)
        domain = self.config.get("custom_domain", "").rstrip("/")
        url = f"https://{domain}/{key}" if domain else None
        return FileItem(
            name=path.split("/")[-1],
            path=path,
            is_dir=False,
            size=head.content_length,
            last_modified=datetime.fromtimestamp(head.last_modified).strftime("%Y-%m-%d %H:%M:%S") if head.last_modified else None,
            storage_type="aliyun",
            url=url,
        )

    async def get_download_url(self, path: str, expires: int = 3600) -> str:
        bucket = self._get_client()
        key = self._to_key(path)
        if self.config.get("custom_domain"):
            domain = self.config["custom_domain"].rstrip("/")
            return f"https://{domain}/{key}"
        return bucket.sign_url("GET", key, expires)

    async def upload_file(self, local_path: str, remote_path: str) -> FileItem:
        bucket = self._get_client()
        key = self._to_key(remote_path)
        with open(local_path, "rb") as f:
            bucket.put_object(key, f)
        return await self.get_file_info(remote_path)

    async def delete_file(self, path: str) -> bool:
        bucket = self._get_client()
        bucket.delete_object(self._to_key(path))
        return True

    async def delete_folder(self, path: str) -> bool:
        bucket = self._get_client()
        prefix = self._to_key(path).rstrip("/") + "/"
        for obj in oss2.ObjectIterator(bucket, prefix=prefix):
            bucket.delete_object(obj.key)
        return True

    async def create_folder(self, path: str) -> bool:
        bucket = self._get_client()
        key = self._to_key(path).rstrip("/") + "/"
        bucket.put_object(key, b"")
        return True

    async def move_file(self, src_path: str, dest_path: str) -> bool:
        bucket = self._get_client()
        src_key = self._to_key(src_path)
        dest_key = self._to_key(dest_path)
        # 检查是否是目录（以/结尾或存在子对象）
        if src_key.endswith('/'):
            # 目录：递归移动所有子对象
            for obj in oss2.ObjectIterator(bucket, prefix=src_key):
                if obj.key == src_key:
                    continue
                new_key = dest_key + obj.key[len(src_key):]
                bucket.copy_object(self.config["bucket_name"], obj.key, new_key)
                bucket.delete_object(obj.key)
            return True
        # 检查是否是目录（没有后缀名的key可能是目录）
        try:
            bucket.head_object(src_key)
            # 是文件，直接移动
            bucket.copy_object(self.config["bucket_name"], src_key, dest_key)
            bucket.delete_object(src_key)
        except oss2.exceptions.NoSuchKey:
            # 可能是目录（无key但有prefix下的子对象）
            prefix = src_key.rstrip('/') + '/'
            has_children = False
            for obj in oss2.ObjectIterator(bucket, prefix=prefix, max_keys=1):
                has_children = True
                break
            if has_children:
                for obj in oss2.ObjectIterator(bucket, prefix=prefix):
                    new_key = dest_key.rstrip('/') + '/' + obj.key[len(prefix):]
                    bucket.copy_object(self.config["bucket_name"], obj.key, new_key)
                    bucket.delete_object(obj.key)
            else:
                raise
        return True

    async def copy_file(self, src_path: str, dest_path: str) -> bool:
        bucket = self._get_client()
        src_key = self._to_key(src_path)
        dest_key = self._to_key(dest_path)
        # 检查是否是目录
        try:
            bucket.head_object(src_key)
            # 是文件，直接复制
            bucket.copy_object(self.config["bucket_name"], src_key, dest_key)
        except oss2.exceptions.NoSuchKey:
            # 可能是目录
            prefix = src_key.rstrip('/') + '/'
            has_children = False
            for obj in oss2.ObjectIterator(bucket, prefix=prefix, max_keys=1):
                has_children = True
                break
            if has_children:
                for obj in oss2.ObjectIterator(bucket, prefix=prefix):
                    new_key = dest_key.rstrip('/') + '/' + obj.key[len(prefix):]
                    bucket.copy_object(self.config["bucket_name"], obj.key, new_key)
            else:
                raise
        return True

    async def get_file_size(self, path: str) -> int:
        bucket = self._get_client()
        head = bucket.head_object(self._to_key(path))
        return head.content_length

    async def test_connection(self) -> dict:
        try:
            bucket = self._get_client()
            # Try listing with limit 1
            list(oss2.ObjectIterator(bucket, max_keys=1))
            return {"success": True, "message": "连接成功"}
        except Exception as e:
            return {"success": False, "message": f"连接失败: {str(e)}"}

    async def get_upload_url(self, remote_path: str, expires: int = 3600) -> dict:
        bucket = self._get_client()
        key = self._to_key(remote_path)
        url = bucket.sign_url('PUT', key, expires)
        return {"url": url, "method": "PUT", "headers": {}}

    def _to_key(self, path: str) -> str:
        """将路径转为 OSS object key"""
        p = self.normalize_path(path).lstrip("/")
        prefix = self.config.get("prefix", "").strip("/")
        if prefix:
            return f"{prefix}/{p}" if p else prefix
        return p
