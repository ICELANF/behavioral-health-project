"""
分布式速率限制器 (FIX-03)
支持 Redis 后端, 回退到内存
"""
import os
import time
from typing import Optional
from loguru import logger

# Redis 连接 (可选)
_redis = None

def _get_redis():
    global _redis
    if _redis is not None:
        return _redis
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            import redis
            _redis = redis.from_url(redis_url, decode_responses=True)
            _redis.ping()
            logger.info("Rate limiter: Redis 连接成功")
            return _redis
        except Exception as e:
            logger.warning(f"Rate limiter: Redis 不可用 ({e}), 回退到内存")
            _redis = False
    else:
        _redis = False
    return None


# 内存回退 (单进程)
_memory_store: dict = {}


def check_rate_limit(
    key: str,
    max_attempts: int = 10,
    window_seconds: int = 60,
    prefix: str = "rl:"
) -> tuple[bool, int]:
    """
    检查速率限制

    Returns: (allowed: bool, remaining: int)
    """
    full_key = f"{prefix}{key}"
    r = _get_redis()

    if r:
        # Redis 滑动窗口
        pipe = r.pipeline()
        now = time.time()
        window_start = now - window_seconds

        pipe.zremrangebyscore(full_key, 0, window_start)
        pipe.zadd(full_key, {str(now): now})
        pipe.zcard(full_key)
        pipe.expire(full_key, window_seconds + 10)
        results = pipe.execute()

        current_count = results[2]
        remaining = max(0, max_attempts - current_count)

        if current_count > max_attempts:
            return False, 0
        return True, remaining
    else:
        # 内存回退
        now = time.time()
        window_start = now - window_seconds

        if full_key in _memory_store:
            _memory_store[full_key] = [t for t in _memory_store[full_key] if t > window_start]
        else:
            _memory_store[full_key] = []

        current_count = len(_memory_store[full_key])
        if current_count >= max_attempts:
            return False, 0

        _memory_store[full_key].append(now)
        return True, max_attempts - current_count - 1


def rate_limit_or_429(key: str, max_attempts: int, window: int, msg: str = "请求过于频繁"):
    """检查限流, 超限则抛出 429"""
    from fastapi import HTTPException
    allowed, remaining = check_rate_limit(key, max_attempts, window)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=msg,
            headers={"Retry-After": str(window)}
        )
    return remaining
