"""同步 Session + Redis 分布式锁 — Celery Worker 专用"""
import os, logging
from contextlib import contextmanager
logger = logging.getLogger(__name__)

_engine = None; _SessionLocal = None

def _init_engine():
    global _engine, _SessionLocal
    if _engine is not None: return
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    a = os.getenv("DATABASE_URL","")
    s = os.getenv("SYNC_DATABASE_URL","")
    if s: url = s
    elif "+asyncpg" in a: url = a.replace("postgresql+asyncpg","postgresql")
    elif a.startswith("postgresql://"): url = a
    else: url = "postgresql://bhp_user:bhp_password@db:5432/bhp_db"
    _engine = create_engine(url, pool_size=5, max_overflow=10, pool_pre_ping=True, pool_recycle=1800)
    _SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)
    logger.info("Celery sync DB: %s", url.split("@")[-1])

def get_sync_url():
    a = os.getenv("DATABASE_URL",""); s = os.getenv("SYNC_DATABASE_URL","")
    if s: return s
    if "+asyncpg" in a: return a.replace("postgresql+asyncpg","postgresql")
    if a.startswith("postgresql://"): return a
    return "postgresql://bhp_user:bhp_password@db:5432/bhp_db"

@contextmanager
def get_sync_session():
    _init_engine()
    session = _SessionLocal()
    try: yield session; session.commit()
    except: session.rollback(); raise
    finally: session.close()

_redis_client = None
def _get_redis():
    global _redis_client
    if _redis_client is None:
        import redis as r
        _redis_client = r.Redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"), decode_responses=True)
    return _redis_client

@contextmanager
def task_lock(name, ttl=60):
    r = _get_redis(); key = f"bhp:lock:{name}"
    acq = r.set(key, "1", nx=True, ex=ttl)
    try: yield bool(acq)
    finally:
        if acq:
            try: r.delete(key)
            except: pass
