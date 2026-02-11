"""
v3 数据库会话管理 — 桥接模块
复用 core.database 的引擎和会话，保持自己的 Base 供 v3 模型注册。
"""
from sqlalchemy.orm import declarative_base

from core.database import engine, SessionLocal, get_db  # noqa: F401

Base = declarative_base()


def init_db():
    """创建 v3 模型表 (开发用, 生产用 Alembic)"""
    Base.metadata.create_all(bind=engine)
