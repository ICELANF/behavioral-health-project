"""
Feature Flag Service — deterministic hash assignment with in-memory cache.
"""
import hashlib
import time
from typing import Optional

from loguru import logger

# In-memory cache: key → {data, expires_at}
_cache: dict = {}
_CACHE_TTL = 60  # seconds


class FeatureFlagService:
    """Evaluate feature flags and A/B experiment variants."""

    def __init__(self, db_session=None):
        self._db = db_session

    async def _load_flag(self, flag_key: str) -> Optional[dict]:
        """Load flag from cache or DB."""
        now = time.time()
        cached = _cache.get(flag_key)
        if cached and cached["expires_at"] > now:
            return cached["data"]

        if not self._db:
            return None

        try:
            from sqlalchemy import text
            result = await self._db.execute(
                text("SELECT key, enabled, rollout_pct, variants, targeting_rules FROM feature_flags WHERE key = :k"),
                {"k": flag_key},
            )
            row = result.mappings().first()
            if row:
                data = dict(row)
                _cache[flag_key] = {"data": data, "expires_at": now + _CACHE_TTL}
                return data
        except Exception as e:
            logger.debug(f"Feature flag load error: {e}")
        return None

    async def is_enabled(self, flag_key: str, user_id: Optional[int] = None) -> bool:
        """Check if a feature flag is enabled for a user."""
        flag = await self._load_flag(flag_key)
        if not flag or not flag.get("enabled"):
            return False

        rollout = flag.get("rollout_pct", 0)
        if rollout >= 100:
            return True
        if rollout <= 0:
            return False

        if user_id is None:
            return rollout >= 50  # default for anonymous

        # Deterministic hash
        h = hashlib.md5(f"{user_id}:{flag_key}".encode()).hexdigest()
        bucket = int(h[:8], 16) % 100
        return bucket < rollout

    async def get_variant(self, experiment_key: str, user_id: int) -> str:
        """Get deterministic A/B variant for a user. Returns 'control' as default."""
        flag = await self._load_flag(experiment_key)
        if not flag or not flag.get("enabled"):
            return "control"

        variants = flag.get("variants") or ["control"]
        if isinstance(variants, str):
            import json
            try:
                variants = json.loads(variants)
            except Exception:
                variants = ["control"]

        if not variants:
            return "control"

        # Deterministic assignment
        h = hashlib.md5(f"{user_id}:{experiment_key}".encode()).hexdigest()
        idx = int(h[:8], 16) % len(variants)
        return variants[idx]

    @staticmethod
    def clear_cache():
        """Clear all cached flags."""
        _cache.clear()
