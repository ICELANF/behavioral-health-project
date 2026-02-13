"""
数据库连接与会话管理 (v3 增强版：支持异步与同步双模)
Database Connection and Session Management
"""
import os
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from contextlib import contextmanager, asynccontextmanager
from loguru import logger
from dotenv import load_dotenv

# 导入 Base 
from core.models import Base

# 加载环境变量
load_dotenv()

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/behavioral_health.db")

# ============================================
# 引擎创建 (同步 & 异步)
# ============================================

# 同步引擎创建
SYNC_URL = DATABASE_URL.replace("+asyncpg", "") if "+asyncpg" in DATABASE_URL else DATABASE_URL

if SYNC_URL.startswith("sqlite"):
    engine = create_engine(
        SYNC_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    engine = create_engine(
        SYNC_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False
    )

# 异步引擎创建 (graceful: asyncpg may not be installed)
ASYNC_URL = DATABASE_URL if "+asyncpg" in DATABASE_URL else DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

async_engine = None
try:
    if "sqlite" in ASYNC_URL:
        async_engine = create_async_engine(ASYNC_URL.replace("sqlite:", "sqlite+aiosqlite:", 1))
    else:
        async_engine = create_async_engine(
            ASYNC_URL,
            pool_pre_ping=True,
            echo=False
        )
except Exception as e:
    logger.warning(f"异步引擎创建失败 (asyncpg 未安装?), 仅使用同步引擎: {e}")

# ============================================
# 会话类定义
# ============================================

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

if async_engine is not None:
    AsyncSessionLocal = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
else:
    AsyncSessionLocal = None

# ============================================
# 数据库初始化 (核心修复：包含扩展和表结构)
# ============================================

async def init_db_async(drop_existing: bool = False):
    """
    异步初始化数据库：安装扩展并创建表
    解决 pgvector 类型识别和 NotNull 约束问题
    """
    try:
        async with async_engine.begin() as conn:
            # 1. 如果是 PostgreSQL，确保安装 vector 扩展
            if async_engine.dialect.name == "postgresql":
                logger.info("正在检查/安装 pgvector 扩展...")
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

            # 2. 如果需要，删除旧表
            if drop_existing:
                logger.warning("正在删除现有表结构...")
                await conn.run_sync(Base.metadata.drop_all)

            # 3. 创建所有表
            logger.info("正在同步模型到物理表结构...")
            await conn.run_sync(Base.metadata.create_all)
            
        logger.success("数据库异步初始化完成 (含扩展加载)")
        return True
    except Exception as e:
        logger.error(f"数据库异步初始化失败: {e}")
        return False

def init_database(drop_existing: bool = False):
    """同步初始化入口 (兼容旧代码)"""
    try:
        if drop_existing:
            Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        return True
    except Exception as e:
        logger.error(f"同步初始化失败: {e}")
        return False

# ============================================
# 会话管理
# ============================================

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

@asynccontextmanager
async def get_async_db_session():
    async with AsyncSessionLocal() as session:
        yield session

@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================
# 事务与检查
# ============================================

@contextmanager
def db_transaction():
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

def check_database_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.success("数据库连接正常")
        return True
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return False

__all__ = [
    "engine", "async_engine", "SessionLocal", "AsyncSessionLocal",
    "Base", "get_db", "get_async_db", "get_db_session", 
    "get_async_db_session", "db_transaction", "init_database",
    "init_db_async", "check_database_connection",
]