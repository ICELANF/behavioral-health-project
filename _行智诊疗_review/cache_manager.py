"""
行诊智伴 Redis 缓存策略（文档 §5.2）
复用平台现有 dify-redis:6379

缓存键规范：
  xzb:expert:{id}:profile      24h  专家画像快照
  xzb:config:{id}              1h   智伴配置
  xzb:session:{conv_id}:ctx    30min 对话上下文
  xzb:knowledge:{expert}:hot   6h   热门知识条目(usage_count前20)
  xzb:rx_draft:{rx_id}         4h   待审核处方草案
  xzb:expert:{id}:online       5min 专家在线状态（sliding window）
"""
from __future__ import annotations
import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

logger = logging.getLogger(__name__)

# TTL 常量（秒）
TTL_EXPERT_PROFILE = 86400    # 24h
TTL_CONFIG         = 3600     # 1h
TTL_SESSION_CTX    = 1800     # 30min
TTL_HOT_KNOWLEDGE  = 21600    # 6h
TTL_RX_DRAFT       = 14400    # 4h
TTL_ONLINE_STATUS  = 300      # 5min


class XZBCacheManager:
    """
    行诊智伴缓存管理器
    包装平台现有 Redis 客户端，提供类型安全的缓存接口
    """

    def __init__(self, redis_client):
        self.redis = redis_client

    # ── 专家画像缓存 ───────────────────────────────

    async def get_expert_profile(self, expert_id: UUID) -> Optional[Dict]:
        key = f"xzb:expert:{expert_id}:profile"
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set_expert_profile(self, expert_id: UUID, profile: Dict):
        key = f"xzb:expert:{expert_id}:profile"
        await self.redis.setex(key, TTL_EXPERT_PROFILE, json.dumps(profile, ensure_ascii=False))

    async def invalidate_expert_profile(self, expert_id: UUID):
        await self.redis.delete(f"xzb:expert:{expert_id}:profile")

    # ── 智伴配置缓存 ───────────────────────────────

    async def get_config(self, config_id: UUID) -> Optional[Dict]:
        key = f"xzb:config:{config_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set_config(self, config_id: UUID, config: Dict):
        key = f"xzb:config:{config_id}"
        await self.redis.setex(key, TTL_CONFIG, json.dumps(config, ensure_ascii=False))

    async def invalidate_config(self, config_id: UUID):
        """专家修改配置后主动失效"""
        await self.redis.delete(f"xzb:config:{config_id}")

    # ── 对话上下文缓存（短期记忆）─────────────────

    async def get_session_context(self, conversation_id: UUID) -> Optional[Dict]:
        key = f"xzb:session:{conversation_id}:ctx"
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set_session_context(self, conversation_id: UUID, ctx: Dict):
        key = f"xzb:session:{conversation_id}:ctx"
        await self.redis.setex(key, TTL_SESSION_CTX, json.dumps(ctx, ensure_ascii=False))

    async def update_session_context(self, conversation_id: UUID, updates: Dict):
        """增量更新对话上下文，并重置 TTL"""
        existing = await self.get_session_context(conversation_id) or {}
        existing.update(updates)
        await self.set_session_context(conversation_id, existing)

    async def clear_session_context(self, conversation_id: UUID):
        await self.redis.delete(f"xzb:session:{conversation_id}:ctx")

    # ── 热门知识缓存 ───────────────────────────────

    async def get_hot_knowledge(self, expert_id: UUID) -> Optional[List[Dict]]:
        key = f"xzb:knowledge:{expert_id}:hot"
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set_hot_knowledge(self, expert_id: UUID, knowledge_list: List[Dict]):
        """缓存 usage_count 前20的知识条目"""
        key = f"xzb:knowledge:{expert_id}:hot"
        await self.redis.setex(
            key, TTL_HOT_KNOWLEDGE,
            json.dumps(knowledge_list[:20], ensure_ascii=False)
        )

    async def invalidate_hot_knowledge(self, expert_id: UUID):
        await self.redis.delete(f"xzb:knowledge:{expert_id}:hot")

    # ── 处方草案缓存 ───────────────────────────────

    async def get_rx_draft(self, rx_id: UUID) -> Optional[Dict]:
        key = f"xzb:rx_draft:{rx_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set_rx_draft(self, rx_id: UUID, draft: Dict):
        key = f"xzb:rx_draft:{rx_id}"
        await self.redis.setex(key, TTL_RX_DRAFT, json.dumps(draft, ensure_ascii=False))

    async def clear_rx_draft(self, rx_id: UUID):
        """处方审核通过/拒绝后主动清除"""
        await self.redis.delete(f"xzb:rx_draft:{rx_id}")

    # ── 专家在线状态（Sliding Window）──────────────

    async def set_expert_online(self, expert_id: UUID):
        """
        设置专家在线状态，TTL=5min
        每次活动时调用，实现 sliding window
        """
        key = f"xzb:expert:{expert_id}:online"
        await self.redis.setex(key, TTL_ONLINE_STATUS, "1")

    async def is_expert_online(self, expert_id: UUID) -> bool:
        key = f"xzb:expert:{expert_id}:online"
        return bool(await self.redis.exists(key))

    async def set_expert_offline(self, expert_id: UUID):
        await self.redis.delete(f"xzb:expert:{expert_id}:online")

    # ── 批量操作 ───────────────────────────────────

    async def get_or_load_expert_profile(
        self,
        expert_id: UUID,
        loader_fn,
    ) -> Optional[Dict]:
        """缓存穿透保护：缓存未命中时调用 loader_fn 从 DB 加载"""
        cached = await self.get_expert_profile(expert_id)
        if cached is not None:
            return cached

        profile = await loader_fn(expert_id)
        if profile:
            await self.set_expert_profile(expert_id, profile)
        return profile

    async def warm_expert_cache(self, expert_id: UUID, db):
        """
        专家首次登录或定时任务调用，预热缓存
        """
        from xzb.models.xzb_models import XZBExpertProfile, XZBKnowledge
        from sqlalchemy import select, and_

        # 预热专家画像
        result = await db.execute(
            select(XZBExpertProfile).where(XZBExpertProfile.id == expert_id)
        )
        expert = result.scalar_one_or_none()
        if expert:
            profile_dict = {
                "id": str(expert.id),
                "display_name": expert.display_name,
                "specialty": expert.specialty,
                "tcm_weight": expert.tcm_weight,
                "domain_tags": expert.domain_tags,
                "style_profile": expert.style_profile,
            }
            await self.set_expert_profile(expert_id, profile_dict)

        # 预热热门知识
        hot_result = await db.execute(
            select(XZBKnowledge).where(and_(
                XZBKnowledge.expert_id == expert_id,
                XZBKnowledge.is_active == True,   # noqa
                XZBKnowledge.expert_confirmed == True,  # noqa
            ))
            .order_by(XZBKnowledge.usage_count.desc())
            .limit(20)
        )
        hot_items = hot_result.scalars().all()
        knowledge_list = [
            {"id": str(k.id), "content": k.content[:500],
             "type": k.type, "evidence_tier": k.evidence_tier,
             "tags": k.tags, "usage_count": k.usage_count}
            for k in hot_items
        ]
        await self.set_hot_knowledge(expert_id, knowledge_list)

        logger.info("Cache warmed for expert %s (%d hot knowledge items)", expert_id, len(knowledge_list))
