"""
数据库会话管理 — 桥接模块
Re-exports from core.database for v3 router compatibility.
"""
from core.database import engine, SessionLocal, get_db, Base  # noqa: F401


def init_db():
    """创建所有表 (开发用, 生产用 Alembic)"""
    Base.metadata.create_all(bind=engine)
