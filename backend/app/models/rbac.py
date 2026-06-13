"""RBAC 权限模型"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

# 角色-菜单 关联表
role_menu_table = Table(
    "role_menus",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("menu_id", Integer, ForeignKey("menus.id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, comment="角色名称")
    code = Column(String(50), unique=True, nullable=False, comment="角色编码")
    description = Column(String(200), default="")
    is_system = Column(Boolean, default=False, comment="系统内置角色不可删除")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    menus = relationship("Menu", secondary=role_menu_table, back_populates="roles", lazy="selectin")


class Menu(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_id = Column(Integer, default=0, comment="父菜单ID,0=顶级")
    name = Column(String(50), nullable=False, comment="菜单/按钮名称")
    menu_type = Column(String(10), nullable=False, comment="menu=菜单, button=按钮")
    permission_code = Column(String(100), unique=True, nullable=False, comment="权限标识")
    path = Column(String(200), default="", comment="菜单路由路径")
    icon = Column(String(50), default="", comment="菜单图标")
    sort_order = Column(Integer, default=0)
    visible = Column(Boolean, default=True, comment="是否在菜单中显示")
    created_at = Column(DateTime, server_default=func.now())

    roles = relationship("Role", secondary=role_menu_table, back_populates="menus", lazy="selectin")
