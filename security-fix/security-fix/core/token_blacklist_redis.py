"""
Token 黑名单 — Redis 持久化 (FIX-10)
替代内存实现, 支持多 worker 和重启后保持
"""
import os
from loguru import logger


class RedisTokenBlacklist:
    """Redis-backed token blacklist with TTL auto-expiry"""

    def __init__(self):
        self._redis = None
        self._memory_fallback = set()
        self.prefix = "token_bl:"

    def _get_redis(self):
        if self._redis is not None:
            return self._redis
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                import redis
                self._redis = redis.from_url(redis_url, decode_responses=True)
                self._redis.ping()
                return self._redis
            except Exception as e:
                logger.warning(f"Token blacklist: Redis 不可用 ({e})")
                self._redis = False
        else:
            self._redis = False
        return None

    def revoke(self, token: str, ttl_seconds: int = 86400):
        """将 token 加入黑名单"""
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()[:32]

        r = self._get_redis()
        if r:
            r.setex(f"{self.prefix}{token_hash}", ttl_seconds, "1")
        else:
            self._memory_fallback.add(token_hash)

    def is_revoked(self, token: str) -> bool:
        """检查 token 是否已被撤销"""
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()[:32]

        r = self._get_redis()
        if r:
            return r.exists(f"{self.prefix}{token_hash}") > 0
        return token_hash in self._memory_fallback


# 全局实例
token_blacklist = RedisTokenBlacklist()
