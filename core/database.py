"""
数据库连接与会话管理
Database Connection and Session Management
"""
import os
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from loguru import logger
from dotenv import load_dotenv

from core.models import Base

# 加载环境变量
load_dotenv()

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/behavioral_health.db")

# 创建引擎
if DATABASE_URL.startswith("sqlite"):
    # SQLite配置
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # 设置为True可查看SQL语句
    )

    # SQLite外键支持
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

else:
    # PostgreSQL或其他数据库配置
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # 连接前测试
        pool_size=10,        # 连接池大小
        max_overflow=20,     # 最大溢出连接数
        echo=False
    )

# 创建SessionLocal类
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ============================================
# 数据库初始化
# ============================================

def init_database(drop_existing: bool = False):
    """
    初始化数据库

    Args:
        drop_existing: 是否删除现有表
    """
    try:
        if drop_existing:
            logger.warning("删除所有现有表...")
            Base.metadata.drop_all(bind=engine)

        logger.info("创建数据库表...")
        Base.metadata.create_all(bind=engine)

        logger.success("数据库初始化完成")
        return True

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False


def check_database_connection():
    """检查数据库连接"""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.success("数据库连接正常")
        return True
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return False


def get_database_info():
    """获取数据库信息"""
    info = {
        "url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL,
        "dialect": engine.dialect.name,
        "driver": engine.driver,
        "pool_size": engine.pool.size() if hasattr(engine.pool, 'size') else None,
    }
    return info


# ============================================
# 会话管理
# ============================================

def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话（用于FastAPI依赖注入）

    使用方式:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            users = db.query(User).all()
            return users
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """
    获取数据库会话（上下文管理器）

    使用方式:
        with get_db_session() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_db_session() -> Session:
    """
    创建数据库会话（手动管理）

    使用方式:
        db = create_db_session()
        try:
            user = db.query(User).first()
        finally:
            db.close()
    """
    return SessionLocal()


# ============================================
# 事务管理
# ============================================

@contextmanager
def db_transaction():
    """
    数据库事务上下文管理器

    使用方式:
        with db_transaction() as db:
            user = User(username="test")
            db.add(user)
            # 自动提交，出错自动回滚
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"事务回滚: {e}")
        raise
    finally:
        db.close()


# ============================================
# 数据库维护
# ============================================

def clear_all_data():
    """清空所有表数据（保留表结构）"""
    try:
        with db_transaction() as db:
            from core.models import (
                User, Assessment, TriggerRecord,
                Intervention, UserSession, HealthData
            )

            # 按依赖顺序删除
            db.query(Intervention).delete()
            db.query(TriggerRecord).delete()
            db.query(Assessment).delete()
            db.query(HealthData).delete()
            db.query(UserSession).delete()
            db.query(User).delete()

        logger.success("所有数据已清空")
        return True
    except Exception as e:
        logger.error(f"清空数据失败: {e}")
        return False


def get_table_counts():
    """获取各表记录数"""
    try:
        with get_db_session() as db:
            from core.models import (
                User, Assessment, TriggerRecord,
                Intervention, UserSession, HealthData
            )

            counts = {
                "users": db.query(User).count(),
                "assessments": db.query(Assessment).count(),
                "trigger_records": db.query(TriggerRecord).count(),
                "interventions": db.query(Intervention).count(),
                "user_sessions": db.query(UserSession).count(),
                "health_data": db.query(HealthData).count(),
            }
            return counts
    except Exception as e:
        logger.error(f"获取表记录数失败: {e}")
        return {}


# ============================================
# 导出
# ============================================

__all__ = [
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "get_db_session",
    "create_db_session",
    "db_transaction",
    "init_database",
    "check_database_connection",
    "get_database_info",
    "clear_all_data",
    "get_table_counts",
]
