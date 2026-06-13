from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


# ---- Auth ----
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserInfo(BaseModel):
    id: int
    username: str
    role_id: int = 2
    role_code: str = "user"


# ---- Storage Source ----
class StorageSourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    storage_type: str = Field(..., pattern="^(aliyun|huawei|tencent|baidu|upyun|qiniu|volcengine|local)$")
    config: dict = {}
    icon: str = "folder"
    color: str = "#409EFF"
    sort_order: int = 0
    description: str = ""
    is_public: bool = False
    protected_paths: list = []

class StorageSourceUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[dict] = None
    enabled: Optional[bool] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    protected_paths: Optional[list] = None

class StorageSourceResponse(BaseModel):
    id: int
    name: str
    storage_type: str
    enabled: bool
    config: dict
    icon: str
    color: str
    sort_order: int
    description: str
    is_public: bool
    protected_paths: list = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---- File ----
class FileItem(BaseModel):
    name: str
    path: str
    is_dir: bool
    size: Optional[int] = None
    last_modified: Optional[str] = None
    storage_type: Optional[str] = None
    url: Optional[str] = None  # Download/preview URL
    need_password: bool = False  # 是否需要密码访问

class FileListResponse(BaseModel):
    files: list[FileItem]
    path: str
    storage_id: int

class FileOperationResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


# ---- Share ----
class ShareCreate(BaseModel):
    storage_id: int
    file_path: str
    is_dir: bool = False
    is_multi: bool = False
    file_name: str = ""
    allow_download: bool = True
    allow_preview: bool = True
    password: Optional[str] = None
    max_views: Optional[int] = None
    expire_hours: Optional[int] = None  # 过期小时数

class ShareUpdate(BaseModel):
    allow_download: Optional[bool] = None
    allow_preview: Optional[bool] = None
    password: Optional[str] = None
    max_views: Optional[int] = None
    expire_hours: Optional[int] = None

class ShareResponse(BaseModel):
    id: int
    share_code: str
    storage_id: int
    file_path: str
    is_dir: bool
    is_multi: bool = False
    file_name: str
    allow_download: bool
    allow_preview: bool
    password: Optional[str] = None
    max_views: Optional[int] = None
    view_count: int
    expire_at: Optional[datetime] = None
    enabled: bool
    created_at: Optional[datetime] = None
    share_url: Optional[str] = None  # 完整分享链接
    storage_name: Optional[str] = None  # 存储源名称

    class Config:
        from_attributes = True

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        # 确保 datetime 字段输出 ISO 格式
        for field in ('expire_at', 'created_at'):
            val = data.get(field)
            if val is not None and not isinstance(val, str):
                data[field] = val.strftime('%Y-%m-%dT%H:%M:%S')
        return data


# ---- Storage Type Info ----
class StorageTypeInfo(BaseModel):
    type: str
    name: str
    fields: list[dict]  # Config fields for this storage type
