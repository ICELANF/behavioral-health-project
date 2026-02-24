"""
XZBCacheManager — Redis 缓存策略
复用平台 dify-redis:6379

缓存键规范:
  xzb:expert:{id}:profile      24h  专家画像快照
  xzb:config:{id}              1h   智伴配置
  xzb:session:{conv_id}:ctx    30min 对话上下文
  xzb:knowledge:{expert}:hot   6h   热门知识条目(前20)
  xzb:rx_draft:{rx_id}         4h   待审核处方草案
  xzb:expert:{id}:online       5min 专家在线状态
"""
from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID

logger = logging.getLogger(__name__)

TTL_EXPERT_PROFILE = 86400    # 24h
TTL_CONFIG         = 3600     # 1h
TTL_SESSION_CTX    = 1800     # 30min
TTL_HOT_KNOWLEDGE  = 21600    # 6h
TTL_RX_DRAFT       = 14400    # 4h
TTL_ONLINE_STATUS  = 300      # 5min


class XZBCacheManager:
    """行智诊疗缓存管理器 (同步 Redis, 与平台 core/redis_lock.py 风格一致)"""

    def __init__(self, redis_client=None):
        self.redis = redis_client

    def _available(self) -> bool:
        return self.redis is not None

    # ── 专家画像缓存 ───────────────────────────────

    def get_expert_profile(self, expert_id: UUID) -> Optional[Dict]:
        if not self._available():
            return None
        try:
            data = self.redis.get(f"xzb:expert:{expert_id}:profile")
            return json.loads(data) if data else None
        except Exception:
            return None

    def set_expert_profile(self, expert_id: UUID, profile: Dict):
        if not self._available():
            return
        try:
            self.redis.setex(
                f"xzb:expert:{expert_id}:profile",
                TTL_EXPERT_PROFILE,
                json.dumps(profile, ensure_ascii=False, default=str),
            )
        except Exception as e:
            logger.warning("XZB cache set_expert_profile failed: %s", e)

    def invalidate_expert_profile(self, expert_id: UUID):
        if self._available():
            self.redis.delete(f"xzb:expert:{expert_id}:profile")

    # ── 智伴配置缓存 ───────────────────────────────

    def get_config(self, config_id: UUID) -> Optional[Dict]:
        if not self._available():
            return None
        try:
            data = self.redis.get(f"xzb:config:{config_id}")
            return json.loads(data) if data else None
        except Exception:
            return None

    def set_config(self, config_id: UUID, config: Dict):
        if not self._available():
            return
        try:
            self.redis.setex(
                f"xzb:config:{config_id}", TTL_CONFIG,
                json.dumps(config, ensure_ascii=False, default=str),
            )
        except Exception as e:
            logger.warning("XZB cache set_config failed: %s", e)

    def invalidate_config(self, config_id: UUID):
        if self._available():
            self.redis.delete(f"xzb:config:{config_id}")

    # ── 专家在线状态 ───────────────────────────────

    def set_expert_online(self, expert_id: UUID):
        if self._available():
            self.redis.setex(f"xzb:expert:{expert_id}:online", TTL_ONLINE_STATUS, "1")

    def is_expert_online(self, expert_id: UUID) -> bool:
        if not self._available():
            return False
        return bool(self.redis.exists(f"xzb:expert:{expert_id}:online"))

    def set_expert_offline(self, expert_id: UUID):
        if self._available():
            self.redis.delete(f"xzb:expert:{expert_id}:online")

    # ── Cache-aside ──────────────────────────────

    def get_or_load(self, key: str, ttl: int, loader: Callable) -> Optional[Any]:
        if self._available():
            try:
                data = self.redis.get(key)
                if data:
                    return json.loads(data)
            except Exception:
                pass
        result = loader()
        if result and self._available():
            try:
                self.redis.setex(key, ttl, json.dumps(result, ensure_ascii=False, default=str))
            except Exception:
                pass
        return result
