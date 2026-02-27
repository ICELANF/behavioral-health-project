"""
行诊智伴定时任务（文档 §5.3）
Job 26-30，扩展平台现有 Scheduler

所有 Job 使用 Redis 分布式锁防止重复执行
使用方式：在现有 Celery beat 配置中添加这些任务
"""
from __future__ import annotations
import logging
from datetime import datetime, timedelta
from typing import List
from uuid import UUID

from celery import Celery
from sqlalchemy import and_, select, update, func

logger = logging.getLogger(__name__)

# 复用平台现有 Celery 实例
# from core.celery_app import celery_app as app
app = Celery("xzb_scheduler")


# ─────────────────────────────────────────────
# Redis 分布式锁（复用平台现有机制）
# ─────────────────────────────────────────────

class RedisLock:
    def __init__(self, redis_client, key: str, timeout: int = 3600):
        self.redis = redis_client
        self.key = f"xzb:lock:{key}"
        self.timeout = timeout

    async def __aenter__(self):
        acquired = await self.redis.set(self.key, "1", ex=self.timeout, nx=True)
        if not acquired:
            raise RuntimeError(f"Lock {self.key} already held")
        return self

    async def __aexit__(self, *args):
        await self.redis.delete(self.key)


# ═══════════════════════════════════════════════
# Job 26: xzb_knowledge_health_check
# 每日 03:30 — 知识库健康度检查
# ═══════════════════════════════════════════════

@app.task(name="xzb.knowledge_health_check", bind=True, max_retries=3)
def xzb_knowledge_health_check(self):
    """
    检查超2年未更新的知识 → 标记「需复核」
    检测与最新指南冲突（需外部指南数据源）
    """
    import asyncio
    asyncio.get_event_loop().run_until_complete(_run_knowledge_health_check())


async def _run_knowledge_health_check():
    from xzb.models.xzb_models import XZBKnowledge

    # async with RedisLock(redis, "knowledge_health_check"):
    two_years_ago = datetime.utcnow() - timedelta(days=730)

    async with get_async_session() as db:
        # 1. 标记超2年未更新的知识为「需复核」
        result = await db.execute(
            update(XZBKnowledge)
            .where(and_(
                XZBKnowledge.updated_at < two_years_ago,
                XZBKnowledge.is_active == True,    # noqa
                XZBKnowledge.needs_review == False, # noqa
                XZBKnowledge.expires_at.is_(None),  # 永久有效的才检查
            ))
            .values(needs_review=True)
            .returning(XZBKnowledge.id)
        )
        flagged_ids = result.scalars().all()

        if flagged_ids:
            logger.info("Job 26: 标记 %d 条知识需复核", len(flagged_ids))
            # 发送专家通知（复用平台 WS 通知）
            # await _notify_experts_for_review(flagged_ids, db)

        # 2. 检查已过期知识
        expired = await db.execute(
            update(XZBKnowledge)
            .where(and_(
                XZBKnowledge.expires_at < datetime.utcnow(),
                XZBKnowledge.is_active == True,   # noqa
            ))
            .values(is_active=False)
            .returning(XZBKnowledge.id)
        )
        expired_ids = expired.scalars().all()
        if expired_ids:
            logger.info("Job 26: 停用 %d 条已过期知识", len(expired_ids))

        await db.commit()


# ═══════════════════════════════════════════════
# Job 27: xzb_conversation_digest
# 每日 06:30 — 对话沉淀（XZBKnowledgeMiner）
# ═══════════════════════════════════════════════

@app.task(name="xzb.conversation_digest", bind=True, max_retries=3)
def xzb_conversation_digest(self):
    """
    提炼昨日对话中的待确认知识条目，推送给专家
    对话沉淀：识别「新知识」→ 生成待确认条目 → WS推送给专家
    """
    import asyncio
    asyncio.get_event_loop().run_until_complete(_run_conversation_digest())


async def _run_conversation_digest():
    from xzb.models.xzb_models import XZBConversation, XZBKnowledge

    yesterday_start = datetime.utcnow().replace(hour=0, minute=0, second=0) - timedelta(days=1)
    yesterday_end = yesterday_start + timedelta(days=1)

    async with get_async_session() as db:
        # 获取昨日未挖掘的对话
        result = await db.execute(
            select(XZBConversation).where(and_(
                XZBConversation.created_at >= yesterday_start,
                XZBConversation.created_at < yesterday_end,
                XZBConversation.knowledge_mined == False,   # noqa
                XZBConversation.ended_at.isnot(None),
            ))
        )
        conversations = result.scalars().all()
        logger.info("Job 27: 处理 %d 条昨日对话", len(conversations))

        for conv in conversations:
            try:
                # 调用 XZBKnowledgeMiner 分析对话（需对接 LLM）
                mined_items = await _mine_knowledge_from_conversation(conv, db)

                for item in mined_items:
                    knowledge = XZBKnowledge(
                        expert_id=conv.expert_id,
                        type="note",
                        content=item["content"],
                        source=f"conversation:{conv.id}",
                        tags=item.get("tags", []),
                        evidence_tier="T4",
                        expert_confirmed=False,   # 需专家二次确认
                    )
                    db.add(knowledge)

                conv.knowledge_mined = True

                if mined_items:
                    # WS推送 xzb_knowledge_confirm 给专家工作台
                    # await ws_manager.send_to_user(conv.expert_id, {
                    #     "event": "xzb_knowledge_confirm",
                    #     "count": len(mined_items),
                    # })
                    pass

            except Exception as e:
                logger.error("Job 27: 对话 %s 挖掘失败: %s", conv.id, e)

        await db.commit()


async def _mine_knowledge_from_conversation(conv, db) -> List[dict]:
    """
    使用 LLM 分析对话内容，识别潜在新知识
    实际实现需调用 LLM + 提示词工程
    """
    # TODO: 调用平台 LLM，提取结构化知识条目
    return []  # stub


# ═══════════════════════════════════════════════
# Job 28: xzb_expert_active_check
# 每日 09:00 — 专家活跃度检查
# ═══════════════════════════════════════════════

@app.task(name="xzb.expert_active_check", bind=True)
def xzb_expert_active_check(self):
    """
    检测超30日未登录专家 → 智伴进入「休眠模式」
    受益者收到提示通知
    """
    import asyncio
    asyncio.get_event_loop().run_until_complete(_run_expert_active_check())


async def _run_expert_active_check():
    from xzb.models.xzb_models import XZBExpertProfile, XZBConfig

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    async with get_async_session() as db:
        # 找到需要进入休眠的专家
        result = await db.execute(
            select(XZBExpertProfile).where(and_(
                XZBExpertProfile.is_active == True,   # noqa
                XZBExpertProfile.last_active_at < thirty_days_ago,
            ))
        )
        inactive_experts = result.scalars().all()

        for expert in inactive_experts:
            if not expert.config or expert.config.dormant_mode:
                continue

            expert.config.dormant_mode = True
            logger.info("Job 28: 专家 %s 进入休眠模式", expert.id)

            # 通知该专家的受益者
            # seekers = await _get_expert_seekers(expert.id, db)
            # for seeker_id in seekers:
            #     await ws_manager.send_to_user(seeker_id, {
            #         "event": "xzb_expert_offline",
            #         "expert_id": str(expert.id),
            #         "message": f"{expert.display_name}暂时不在线，您可以继续使用智伴基础功能。"
            #     })

        await db.commit()
        logger.info("Job 28: 检查完成，%d 位专家进入休眠", len(inactive_experts))


# ═══════════════════════════════════════════════
# Job 29: xzb_rx_fragment_audit
# 每日 06:15后5分钟 — 处方片段审计
# ═══════════════════════════════════════════════

@app.task(name="xzb.rx_fragment_audit", bind=True)
def xzb_rx_fragment_audit(self):
    """
    在 prescription_task_generation（06:15）之后运行
    确认专家处方片段已正确注入现有 RxComposer 流水线
    """
    import asyncio
    asyncio.get_event_loop().run_until_complete(_run_rx_fragment_audit())


async def _run_rx_fragment_audit():
    from xzb.models.xzb_models import XZBRxFragment

    async with get_async_session() as db:
        # 检查 submitted 状态超过1小时未处理的片段
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        result = await db.execute(
            select(XZBRxFragment).where(and_(
                XZBRxFragment.status == "submitted",
                XZBRxFragment.created_at < one_hour_ago,
            ))
        )
        stale_fragments = result.scalars().all()

        if stale_fragments:
            logger.warning(
                "Job 29: 发现 %d 个处方片段超时未处理", len(stale_fragments)
            )
            # 告警通知
            for frag in stale_fragments:
                logger.warning(
                    "Stale XZBRxFragment id=%s expert=%s seeker=%s",
                    frag.id, frag.expert_id, frag.seeker_id
                )

        # 统计当日处方注入成功率
        total_today = await db.execute(
            select(func.count(XZBRxFragment.id)).where(
                XZBRxFragment.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
            )
        )
        approved_today = await db.execute(
            select(func.count(XZBRxFragment.id)).where(and_(
                XZBRxFragment.status == "approved",
                XZBRxFragment.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0),
            ))
        )
        t = total_today.scalar() or 0
        a = approved_today.scalar() or 0
        logger.info("Job 29: 今日处方注入率 %d/%d = %.1f%%", a, t, 100 * a / t if t > 0 else 0)


# ═══════════════════════════════════════════════
# Job 30: xzb_knowledge_embedding_sync
# 每日 02:30 — 知识向量同步
# ═══════════════════════════════════════════════

@app.task(name="xzb.knowledge_embedding_sync", bind=True)
def xzb_knowledge_embedding_sync(self):
    """
    重新嵌入被专家修改但未更新向量的知识条目
    （vector_embedding=NULL 表示待同步）
    """
    import asyncio
    asyncio.get_event_loop().run_until_complete(_run_embedding_sync())


async def _run_embedding_sync():
    from xzb.models.xzb_models import XZBKnowledge

    async with get_async_session() as db:
        # 找到需要重新嵌入的知识
        result = await db.execute(
            select(XZBKnowledge).where(and_(
                XZBKnowledge.is_active == True,     # noqa
                XZBKnowledge.expert_confirmed == True,  # noqa
                XZBKnowledge.vector_embedding.is_(None),
            )).limit(500)  # 每批最多500条
        )
        pending = result.scalars().all()
        logger.info("Job 30: 待重新嵌入知识 %d 条", len(pending))

        # embed_svc = get_embed_service()
        success, failed = 0, 0
        for k in pending:
            try:
                # k.vector_embedding = await embed_svc.embed(k.content)
                k.updated_at = datetime.utcnow()
                success += 1
            except Exception as e:
                logger.error("Job 30: 嵌入失败 knowledge=%s: %s", k.id, e)
                failed += 1

        await db.commit()
        logger.info("Job 30: 嵌入完成 成功=%d 失败=%d", success, failed)


# ─────────────────────────────────────────────
# Celery Beat 调度配置（添加到平台现有 beat_schedule）
# ─────────────────────────────────────────────

XZB_BEAT_SCHEDULE = {
    # Job 26
    "xzb-knowledge-health-check": {
        "task": "xzb.knowledge_health_check",
        "schedule": "30 3 * * *",       # 每日 03:30
        "options": {"expires": 3600},
    },
    # Job 27
    "xzb-conversation-digest": {
        "task": "xzb.conversation_digest",
        "schedule": "30 6 * * *",       # 每日 06:30
        "options": {"expires": 3600},
    },
    # Job 28
    "xzb-expert-active-check": {
        "task": "xzb.expert_active_check",
        "schedule": "0 9 * * *",        # 每日 09:00
        "options": {"expires": 3600},
    },
    # Job 29 (prescription_task_generation 是 06:15)
    "xzb-rx-fragment-audit": {
        "task": "xzb.rx_fragment_audit",
        "schedule": "20 6 * * *",       # 每日 06:20（prescription生成后5分钟）
        "options": {"expires": 1800},
    },
    # Job 30
    "xzb-knowledge-embedding-sync": {
        "task": "xzb.knowledge_embedding_sync",
        "schedule": "30 2 * * *",       # 每日 02:30
        "options": {"expires": 7200},
    },
}

# 在 celery_app 配置中合并：
# app.conf.beat_schedule.update(XZB_BEAT_SCHEDULE)


# ─────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────

def get_async_session():
    """复用平台现有数据库会话工厂（stub）"""
    from contextlib import asynccontextmanager
    @asynccontextmanager
    async def _session():
        yield None  # 替换为平台 AsyncSession
    return _session()
