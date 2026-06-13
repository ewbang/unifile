import uuid
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    role_id = Column(Integer, default=2, comment="角色ID: 1=管理员 2=普通用户 3=游客")
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class StorageSource(Base):
    __tablename__ = "storage_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="存储源名称")
    storage_type = Column(String(20), nullable=False, comment="存储类型: aliyun/huawei/tencent/baidu/upyun/qiniu/volcengine/local")
    enabled = Column(Boolean, default=True, comment="是否启用")

    # Connection config (JSON - different fields per storage type)
    config = Column(JSON, nullable=False, default=dict, comment="存储连接配置")

    # Display
    icon = Column(String(50), default="folder")
    color = Column(String(20), default="#409EFF")
    sort_order = Column(Integer, default=0)
    description = Column(Text, default="")

    # Access control
    is_public = Column(Boolean, default=False, comment="是否公开访问(无需登录)")
    protected_paths = Column(JSON, default=list, comment="受保护的目录路径列表，每个元素包含path和password")

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class FileOperationLog(Base):
    __tablename__ = "file_operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True, comment="操作用户,null=匿名")
    username = Column(String(50), default="", comment="用户名快照")
    storage_id = Column(Integer, nullable=True)
    storage_name = Column(String(100), default="", comment="存储源名快照")
    operation = Column(String(20), nullable=False)  # upload/download/delete/move/copy/mkdir/share
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), default="")
    file_size = Column(Integer, default=0)
    ip_address = Column(String(50), default="")
    created_at = Column(DateTime, server_default=func.now())


class LoginLog(Base):
    """登录日志"""
    __tablename__ = "login_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, comment="登录用户名")
    ip_address = Column(String(50), default="", comment="登录IP")
    user_agent = Column(String(500), default="", comment="浏览器UA")
    status = Column(String(10), nullable=False, comment="success/failed")
    message = Column(String(200), default="", comment="失败原因")
    created_at = Column(DateTime, server_default=func.now())


class ShareLink(Base):
    __tablename__ = "share_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    share_code = Column(String(32), unique=True, nullable=False, index=True, default=lambda: uuid.uuid4().hex[:12])
    user_id = Column(Integer, nullable=False, comment="创建者")
    storage_id = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False, comment="单文件路径或多文件JSON数组")
    is_dir = Column(Boolean, default=False)
    is_multi = Column(Boolean, default=False, comment="是否多文件分享")
    file_name = Column(String(255), default="")

    # Permissions
    allow_download = Column(Boolean, default=True)
    allow_preview = Column(Boolean, default=True)
    password = Column(String(50), nullable=True, comment="访问密码,空=无需密码")

    # Limits
    max_views = Column(Integer, nullable=True, comment="最大访问次数,null=不限")
    view_count = Column(Integer, default=0)
    expire_at = Column(DateTime, nullable=True, comment="过期时间,null=永不过期")

    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class SiteSettings(Base):
    __tablename__ = "site_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
