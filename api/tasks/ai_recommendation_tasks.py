# -*- coding: utf-8 -*-
"""
P2: AI 每日内容推荐 Celery 任务
beat schedule: 每天 08:00 运行一次，为活跃学员生成个性化内容推荐并写入推送队列（待教练审核）。

流程：
  1. 查询活跃学员（近7天有微行动记录或近30天有评估）
  2. 读取学员行为画像（stage + domains）
  3. 向量召回（Qdrant）或关键词匹配内容库（降级）
  4. 生成推荐理由（Ollama）
  5. 写入 coach_push_queue (source_type='ai_recommendation', status='pending')
  6. 跳过近3天已有 ai_recommendation 记录的学员（防重推）
"""
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ── 量表阶段 → 适合内容标签映射 ──
_STAGE_CONTENT_TAGS = {
    "S0": ["觉察", "科普", "认知改变"],
    "S1": ["动机激活", "成功案例", "改变收益"],
    "S2": ["目标设定", "计划制定", "行动工具"],
    "S3": ["习惯建立", "障碍应对", "每日打卡"],
    "S4": ["维持策略", "进阶挑战", "里程碑"],
    "S5": ["巩固强化", "同伴分享", "数据复盘"],
    "S6": ["融入生活", "传播分享", "教练成长"],
}

_DOMAIN_KEYWORDS = {
    "nutrition":  ["饮食", "营养", "食谱", "血糖", "饮食日记"],
    "exercise":   ["运动", "步数", "锻炼", "有氧", "力量训练"],
    "sleep":      ["睡眠", "休息", "睡前", "昼夜节律"],
    "emotion":    ["情绪", "压力", "焦虑", "冥想", "正念"],
    "behavior":   ["习惯", "微行动", "行为改变", "打卡"],
    "medication": ["用药", "依从性", "服药提醒"],
}


def _get_content_keywords(stage: str, domains: list) -> list:
    tags = _STAGE_CONTENT_TAGS.get(stage, ["健康", "行为改变"])
    for d in (domains or []):
        tags += _DOMAIN_KEYWORDS.get(d, [])
    return list(dict.fromkeys(tags))[:8]  # 去重，最多8个


def _match_content_by_keywords(db, keywords: list, limit: int = 3) -> list:
    """关键词匹配内容库（Qdrant 不可用时的降级方案）"""
    try:
        from sqlalchemy import text
        if not keywords:
            return []
        # 使用 ILIKE 逐个关键词搜索
        kw = keywords[0]  # 取第一个关键词做 SQL 匹配
        rows = db.execute(text("""
            SELECT id, title, content_type, summary
            FROM content_items
            WHERE status = 'published'
              AND (title ILIKE :kw OR summary ILIKE :kw)
            ORDER BY created_at DESC
            LIMIT :limit
        """), {"kw": f"%{kw}%", "limit": limit}).fetchall()
        return [{"id": r[0], "title": r[1], "type": r[2], "summary": r[3] or ""} for r in rows]
    except Exception as e:
        logger.warning(f"[ai_rec] 关键词匹配失败: {e}")
        return []


def _qdrant_vector_search(keywords: list, limit: int = 3) -> list:
    """Qdrant 向量召回（可选，失败时降级到关键词匹配）"""
    try:
        from qdrant_client import QdrantClient
        import os
        client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
            timeout=5.0,
        )
        # 使用关键词联合文本做查询向量（需要 embed 服务可用）
        try:
            import httpx
            ollama_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
            embed_model = os.getenv("OLLAMA_EMBED_MODEL", "mxbai-embed-large:latest")
            query_text = " ".join(keywords[:4])
            resp = httpx.post(
                f"{ollama_url}/api/embed",
                json={"model": embed_model, "input": query_text},
                timeout=10.0,
            )
            if resp.status_code == 200:
                vector = resp.json().get("embeddings", [[]])[0]
                if len(vector) == 1024:
                    results = client.search(
                        collection_name="bhp_knowledge",
                        query_vector=vector,
                        limit=limit,
                        score_threshold=0.6,
                    )
                    return [
                        {
                            "id": r.id,
                            "title": r.payload.get("title", ""),
                            "type": r.payload.get("content_type", "article"),
                            "summary": r.payload.get("content", "")[:100],
                            "score": r.score,
                        }
                        for r in results
                    ]
        except Exception as e:
            logger.debug(f"[ai_rec] Qdrant embed失败: {e}")
    except Exception as e:
        logger.debug(f"[ai_rec] Qdrant不可用: {e}")
    return []


def _generate_push_reason(student_name: str, content_title: str, stage: str) -> str:
    """Ollama 生成推荐理由（30字以内，降级使用模板）"""
    try:
        from core.agents.ollama_client import get_ollama_client
        client = get_ollama_client()
        if client.is_available():
            resp = client.chat(
                system="用30字以内说明为什么向学员推荐此内容，直接输出推荐理由，不需要任何前缀。",
                user=f"学员阶段：{stage}，推荐内容：《{content_title}》",
            )
            if resp.success and resp.content and len(resp.content) < 60:
                return resp.content.strip()
    except Exception:
        pass
    _STAGE_REASON = {
        "S0": "适合当前觉察阶段，帮助建立改变意愿",
        "S1": "激活改变动力，与您当前阶段高度匹配",
        "S2": "实用行动指南，助您从准备走向执行",
        "S3": "支持习惯建立，适合行动期学员",
        "S4": "维持阶段专属内容，防止行为反弹",
        "S5": "巩固强化期精选，帮助深化改变",
        "S6": "高阶内容，助力融入可持续健康生活",
    }
    return _STAGE_REASON.get(stage, "AI为您精选，与当前健康目标高度相关")


def run_ai_content_recommendation():
    """
    每日内容推荐主逻辑（可被 Celery task 调用，也可独立运行）。
    返回: {"processed": N, "skipped": N, "created": N}
    """
    from core.database import SessionLocal
    db = SessionLocal()
    processed = skipped = created = 0
    try:
        from sqlalchemy import text

        # 1. 查询活跃学员（coach_student_bindings 中存在绑定关系）
        rows = db.execute(text("""
            SELECT DISTINCT csb.student_id, csb.coach_id,
                            u.full_name, u.username
            FROM coach_schema.coach_student_bindings csb
            JOIN users u ON u.id = csb.student_id
            WHERE csb.status = 'active'
            LIMIT 200
        """)).fetchall()

        for row in rows:
            student_id, coach_id = row[0], row[1]
            student_name = row[2] or row[3] or f"学员{student_id}"
            processed += 1

            # 2. 跳过近3天已有推荐的学员
            recent = db.execute(text("""
                SELECT COUNT(*)
                FROM coach_schema.coach_push_queue
                WHERE student_id = :sid
                  AND source_type = 'ai_recommendation'
                  AND created_at > NOW() - INTERVAL '3 days'
            """), {"sid": student_id}).scalar()
            if recent and recent > 0:
                skipped += 1
                continue

            # 3. 读取行为画像
            stage = "S1"
            domains = []
            try:
                from core.models import BehavioralProfile
                profile = db.query(BehavioralProfile).filter(
                    BehavioralProfile.user_id == student_id
                ).first()
                if profile:
                    stage = profile.current_stage or "S1"
                    domains = (profile.dominant_domains
                               if isinstance(profile.dominant_domains, list)
                               else ([profile.dominant_domains] if profile.dominant_domains else []))
            except Exception:
                pass

            # 4. 内容召回（Qdrant 优先，降级关键词匹配）
            keywords = _get_content_keywords(stage, domains)
            contents = _qdrant_vector_search(keywords, limit=2)
            if not contents:
                contents = _match_content_by_keywords(db, keywords, limit=2)
            if not contents:
                skipped += 1
                continue

            # 5. 为每条推荐生成推送队列条目
            for c in contents[:2]:
                reason = _generate_push_reason(student_name, c.get("title", ""), stage)
                title = c.get("title", "推荐内容")
                push_content = f"为您推荐：《{title}》\n推荐理由：{reason}"
                try:
                    db.execute(text("""
                        INSERT INTO coach_schema.coach_push_queue
                            (coach_id, student_id, source_type, source_id,
                             title, content, content_extra,
                             priority, status, created_at)
                        VALUES
                            (:coach_id, :sid, 'ai_recommendation', :source_id,
                             :title, :content, :extra,
                             'low', 'pending', NOW())
                    """), {
                        "coach_id": coach_id,
                        "sid": student_id,
                        "source_id": str(c.get("id", "")),
                        "title": f"AI推荐：{title[:50]}",
                        "content": push_content,
                        "extra": json.dumps({
                            "content_id": c.get("id"),
                            "content_type": c.get("type"),
                            "stage": stage,
                            "keywords": keywords[:4],
                            "recommendation_reason": reason,
                        }, ensure_ascii=False),
                    })
                    created += 1
                except Exception as e:
                    logger.warning(f"[ai_rec] 推送队列写入失败 student={student_id}: {e}")

        db.commit()
        logger.info(f"[ai_rec] 每日推荐完成: processed={processed} skipped={skipped} created={created}")

    except Exception as e:
        logger.error(f"[ai_rec] 每日推荐任务失败: {e}")
        db.rollback()
    finally:
        db.close()

    return {"processed": processed, "skipped": skipped, "created": created}


# ── Celery Task 包装 ──
try:
    from api.worker import celery_app

    @celery_app.task(name="api.tasks.ai_recommendation_tasks.daily_ai_content_recommendation",
                     bind=True, max_retries=2)
    def daily_ai_content_recommendation(self):
        """每日 AI 内容推荐 Celery 任务（beat: 每天 08:00）"""
        try:
            result = run_ai_content_recommendation()
            logger.info(f"[ai_rec] Celery task 完成: {result}")
            return result
        except Exception as exc:
            logger.error(f"[ai_rec] Celery task 失败: {exc}")
            raise self.retry(exc=exc, countdown=600)

except ImportError:
    # 非 Celery 环境（直接运行时）跳过 task 注册
    pass
