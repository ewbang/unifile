"""腾讯云 COS 适配器"""
from qcloud_cos import CosConfig, CosS3Client
from datetime import datetime
from app.services.base import BaseStorageAdapter
from app.schemas.schemas import FileItem


class TencentCOSAdapter(BaseStorageAdapter):
    """
    config fields:
        secret_id, secret_key, bucket_name, region,
        custom_domain (optional), prefix (optional)
    """

    def _get_client(self):
        conf = CosConfig(
            Region=self.config["region"],
            SecretId=self.config["secret_id"],
            SecretKey=self.config["secret_key"],
        )
        return CosS3Client(conf)

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

        resp = client.list_objects(Bucket=bucket, Prefix=prefix, Delimiter="/", MaxKeys=1000)
        # Common prefixes (directories)
        for cp in resp.get("CommonPrefixes", []):
            dir_name = cp["Prefix"][len(prefix):].rstrip("/")
            if dir_name and dir_name not in seen_dirs:
                seen_dirs.add(dir_name)
                files.append(FileItem(name=dir_name, path=self.join_path(path, dir_name), is_dir=True))
        # Files
        for obj in resp.get("Contents", []):
            name = obj["Key"][len(prefix):]
            if not name:
                continue
            domain = self.config.get("custom_domain", "").rstrip("/")
            url = f"https://{domain}/{obj['Key']}" if domain else None
            files.append(FileItem(
                name=name, path=self.join_path(path, name), is_dir=False,
                size=int(obj.get("Size", 0)),
                last_modified=obj.get("LastModified", "")[:19].replace("T", " "),
                storage_type="tencent", url=url,
            ))
        return files

    async def get_file_info(self, path: str) -> FileItem:
        client = self._get_client()
        key = self._to_key(path)
        resp = client.head_object(Bucket=self.config["bucket_name"], Key=key)
        domain = self.config.get("custom_domain", "").rstrip("/")
        url = f"https://{domain}/{key}" if domain else None
        # 解析 Last-Modified: "Fri, 12 Jun 2026 03:10:17 GMT" -> "2026-06-12 03:10:17"
        raw_date = resp.get("Last-Modified", "")
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
            size=int(resp.get("Content-Length", 0)),
            last_modified=last_modified,
            storage_type="tencent", url=url,
        )

    async def get_download_url(self, path: str, expires: int = 3600) -> str:
        client = self._get_client()
        key = self._to_key(path)
        if self.config.get("custom_domain"):
            domain = self.config["custom_domain"].rstrip("/")
            return f"https://{domain}/{key}"
        url = client.get_presigned_url(
            Bucket=self.config["bucket_name"], Key=key,
            Method="GET", Expired=expires,
        )
        return url

    async def upload_file(self, local_path: str, remote_path: str) -> FileItem:
        client = self._get_client()
        key = self._to_key(remote_path)
        client.upload_file(
            Bucket=self.config["bucket_name"],
            Key=key,
            LocalFilePath=local_path,
        )
        return await self.get_file_info(remote_path)

    async def delete_file(self, path: str) -> bool:
        client = self._get_client()
        client.delete_object(Bucket=self.config["bucket_name"], Key=self._to_key(path))
        return True

    async def delete_folder(self, path: str) -> bool:
        client = self._get_client()
        prefix = self._to_key(path).rstrip("/") + "/"
        bucket = self.config["bucket_name"]
        resp = client.list_objects(Bucket=bucket, Prefix=prefix, MaxKeys=1000)
        for obj in resp.get("Contents", []):
            client.delete_object(Bucket=bucket, Key=obj["Key"])
        return True

    async def create_folder(self, path: str) -> bool:
        client = self._get_client()
        key = self._to_key(path).rstrip("/") + "/"
        client.put_object(Bucket=self.config["bucket_name"], Key=key, Body=b"")
        return True

    async def move_file(self, src_path: str, dest_path: str) -> bool:
        await self.copy_file(src_path, dest_path)
        await self.delete_file(src_path)
        return True

    async def copy_file(self, src_path: str, dest_path: str) -> bool:
        client = self._get_client()
        bucket = self.config["bucket_name"]
        client.copy(Bucket=bucket, Key=self._to_key(dest_path),
                    CopySource={"Bucket": bucket, "Key": self._to_key(src_path), "Region": self.config["region"]})
        return True

    async def get_file_size(self, path: str) -> int:
        client = self._get_client()
        resp = client.head_object(Bucket=self.config["bucket_name"], Key=self._to_key(path))
        return int(resp.get("Content-Length", 0))

    async def test_connection(self) -> dict:
        try:
            client = self._get_client()
            client.list_objects(Bucket=self.config["bucket_name"], MaxKeys=1)
            return {"success": True, "message": "连接成功"}
        except Exception as e:
            return {"success": False, "message": f"连接失败: {str(e)}"}

    async def get_upload_url(self, remote_path: str, expires: int = 3600) -> dict:
        client = self._get_client()
        key = self._to_key(remote_path)
        url = client.get_presigned_url(
            Bucket=self.config["bucket_name"], Key=key,
            Method="PUT", Expired=expires,
        )
        return {"url": url, "method": "PUT", "headers": {}}
