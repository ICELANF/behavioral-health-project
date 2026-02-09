# -*- coding: utf-8 -*-
"""
Redis 分布式锁 — 用于 APScheduler 多实例互斥

降级策略: Redis不可用时直接执行(无锁)
"""

import os
import time
import functools
from loguru import logger

_redis_client = None
_redis_available = False


def _get_redis():
    """延迟初始化 Redis 客户端"""
    global _redis_client, _redis_available

    if _redis_client is not None:
        return _redis_client if _redis_available else None

    try:
        import redis
        host = os.environ.get("REDIS_HOST", "localhost")
        port = int(os.environ.get("REDIS_PORT", "6379"))
        password = os.environ.get("REDIS_PASSWORD", "")
        db = int(os.environ.get("REDIS_LOCK_DB", "1"))

        _redis_client = redis.Redis(
            host=host, port=port, password=password or None,
            db=db, decode_responses=True, socket_timeout=2,
        )
        _redis_client.ping()
        _redis_available = True
        logger.info(f"[RedisLock] 已连接 Redis {host}:{port} db={db}")
        return _redis_client
    except Exception as e:
        _redis_client = True  # sentinel: tried
        _redis_available = False
        logger.warning(f"[RedisLock] Redis不可用，降级为无锁模式: {e}")
        return None


def with_redis_lock(lock_name: str, ttl: int = 300):
    """
    装饰器: 通过 Redis SETNX 实现互斥锁

    Args:
        lock_name: 锁名称 (全局唯一)
        ttl: 锁超时秒数 (防止死锁, 默认300s)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            r = _get_redis()

            if r is None:
                # Redis 不可用，降级直接执行
                return func(*args, **kwargs)

            key = f"bhp:lock:{lock_name}"
            acquired = False
            try:
                acquired = r.set(key, str(time.time()), nx=True, ex=ttl)
                if not acquired:
                    logger.debug(f"[RedisLock] 锁 {lock_name} 已被占用，跳过执行")
                    return None
                logger.debug(f"[RedisLock] 获取锁 {lock_name} (TTL={ttl}s)")
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"[RedisLock] 锁操作异常({lock_name}): {e}")
                # 锁异常时降级执行
                return func(*args, **kwargs)
            finally:
                if acquired:
                    try:
                        r.delete(key)
                        logger.debug(f"[RedisLock] 释放锁 {lock_name}")
                    except Exception:
                        pass  # TTL 兜底
        return wrapper
    return decorator
