"""
用户层剩余5个Agent

tcm_wellness: 中医养生指导
motivation_support: 动机激励
habit_tracker: 习惯追踪
community_guide: 社区引导（四同道者）
content_recommender: 内容推荐
"""
from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..base import BaseAssistantAgent

logger = logging.getLogger(__name__)

DISCLAIMER = "\n\n---\n以上为健康科普信息，不构成医疗建议。如有具体健康问题，请咨询专业医疗人员。"


# ═══════════════════════════════════════════════════════════
# tcm_wellness — 中医养生
# ═══════════════════════════════════════════════════════════

class TcmWellnessAgent(BaseAssistantAgent):
    """中医养生指导 — 科普级"""

    @property
    def name(self) -> str:
        return "tcm_wellness"

    @property
    def domain(self) -> str:
        return "tcm"

    BOUNDARY_KEYWORDS = ["开方", "中药方", "处方", "汤剂", "煎药", "针灸治疗",
                         "拔罐治疗", "刮痧治疗", "中医诊断"]

    def _get_rag(self):
        try:
            from core.rag.pipeline import RAGPipeline
            return RAGPipeline()
        except ImportError:
            return None

    def _get_llm(self):
        try:
            from core.llm_client import get_llm_client
            return get_llm_client()
        except ImportError:
            return None

    async def run(self, message: str, **kwargs) -> Dict[str, Any]:
        if not await self.safety_check(message):
            return self._format_response(content="安全拦截", safety_intercepted=True)

        boundary = next((kw for kw in self.BOUNDARY_KEYWORDS if kw in message), None)

        # RAG
        knowledge = []
        rag = self._get_rag()
        if rag:
            try:
                results = rag.search(message, top_k=5) if hasattr(rag, 'search') else []
                knowledge = [{"content": str(r), "source": getattr(r, 'source', '')} for r in (results or [])]
            except Exception:
                pass

        # LLM
        llm = self._get_llm()
        system = """你是行健平台的中医养生顾问。专长：
- 体质辨识科普（九种体质的日常调养）
- 四季养生（春养肝、夏养心、秋养肺、冬养肾）
- 食疗药膳基础知识
- 经络穴位保健（自我按摩指导）
- 情志养生（七情调摄）
你不开中药方，不做中医诊断，不替代中医师。"""

        if llm:
            ctx = "\n".join([k["content"][:300] for k in knowledge[:3]]) if knowledge else ""
            note = f"\n注意：涉及「{boundary}」，请引导就医。" if boundary else ""
            prompt = f"{system}{note}\n{f'参考:{ctx}' if ctx else ''}\n用户: {message}"
            try:
                resp = await llm.achat(prompt) if hasattr(llm, 'achat') else llm.chat(prompt)
                text = resp if isinstance(resp, str) else getattr(resp, 'content', str(resp))
                if "不构成" not in text:
                    text += DISCLAIMER
                return self._format_response(content=text, boundary_warning=boundary, confidence=0.7)
            except Exception:
                pass

        return self._format_response(
            content=f"中医养生建议暂不可用。{DISCLAIMER}",
            confidence=0.3,
        )


# ═══════════════════════════════════════════════════════════
# motivation_support — 动机激励
# ═══════════════════════════════════════════════════════════

class MotivationSupportAgent(BaseAssistantAgent):
    """动机激励 — 基于TTM阶段的激励策略"""

    @property
    def name(self) -> str:
        return "motivation_support"

    @property
    def domain(self) -> str:
        return "motivation"

    # TTM阶段×激励策略
    STAGE_MOTIVATION = {
        "S0": {"style": "gentle_awareness", "focus": "引发好奇心，不施压",
               "techniques": ["提供新信息", "分享他人故事", "提问引导反思"]},
        "S1": {"style": "exploratory", "focus": "帮助权衡利弊",
               "techniques": ["动机访谈", "价值观澄清", "自我效能探索"]},
        "S2": {"style": "planning_support", "focus": "具体化行动计划",
               "techniques": ["SMART目标设定", "障碍预演", "资源盘点"]},
        "S3": {"style": "active_coaching", "focus": "强化行动信心",
               "techniques": ["小步成功", "及时肯定", "同伴榜样"]},
        "S4": {"style": "maintenance_affirm", "focus": "巩固身份认同",
               "techniques": ["复发预防", "自我奖励", "价值回顾"]},
        "S5": {"style": "celebration", "focus": "庆祝与传承",
               "techniques": ["成就回顾", "分享经验", "新目标展望"]},
    }

    def _get_llm(self):
        try:
            from core.llm_client import get_llm_client
            return get_llm_client()
        except ImportError:
            return None

    async def run(self, message: str, **kwargs) -> Dict[str, Any]:
        if not await self.safety_check(message):
            return self._format_response(content="安全拦截", safety_intercepted=True)

        profile = kwargs.get("user_profile", {})
        stage = profile.get("ttm_stage", "S0")
        config = self.STAGE_MOTIVATION.get(stage, self.STAGE_MOTIVATION["S0"])

        llm = self._get_llm()
        if llm:
            prompt = f"""作为动机激励伙伴，用户处于{stage}阶段。
激励风格: {config['style']}
焦点: {config['focus']}
可用技术: {', '.join(config['techniques'])}

用户说: {message}

请用温暖、不施压的语气回应，运用合适的激励技术。"""
            try:
                resp = await llm.achat(prompt) if hasattr(llm, 'achat') else llm.chat(prompt)
                text = resp if isinstance(resp, str) else getattr(resp, 'content', str(resp))
                return self._format_response(content=text, stage=stage, style=config["style"], confidence=0.7)
            except Exception:
                pass

        # 兜底
        return self._format_response(
            content=f"你的每一步都有价值。当前建议: {config['focus']}",
            stage=stage, style=config["style"], confidence=0.4,
        )


# ═══════════════════════════════════════════════════════════
# habit_tracker — 习惯追踪
# ═══════════════════════════════════════════════════════════

class HabitTrackerAgent(BaseAssistantAgent):
    """习惯追踪 — 打卡记录 + 趋势分析"""

    @property
    def name(self) -> str:
        return "habit_tracker"

    @property
    def domain(self) -> str:
        return "habit"

    async def run(self, message: str, **kwargs) -> Dict[str, Any]:
        if not await self.safety_check(message):
            return self._format_response(content="安全拦截", safety_intercepted=True)

        user_id = kwargs.get("user_id")
        db = kwargs.get("db")

        # 意图检测
        if any(w in message for w in ["打卡", "记录", "完成了", "做了", "吃了", "跑了", "睡了"]):
            return await self._record_habit(message, user_id, db)
        elif any(w in message for w in ["统计", "趋势", "多少天", "连续", "总结", "回顾"]):
            return await self._show_summary(user_id, db)
        else:
            return self._format_response(
                content="你可以告诉我你完成了什么习惯（比如「今天跑步30分钟」），或者问我「这周统计」查看进度。",
                confidence=0.6,
            )

    async def _record_habit(self, message: str, user_id, db) -> dict:
        # 提取习惯内容
        habit_text = message.strip()
        if db and user_id:
            try:
                from sqlalchemy import text as sa_text
                await db.execute(
                    sa_text("""
                        INSERT INTO habit_logs (user_id, content, logged_at)
                        VALUES (:uid, :content, NOW())
                    """),
                    {"uid": user_id, "content": habit_text[:200]}
                )
                await db.commit()
            except Exception as e:
                logger.warning(f"习惯记录失败: {e}")

        return self._format_response(
            content=f"已记录！坚持就是进步。继续加油！",
            action="habit_recorded",
            habit_content=habit_text[:200],
            confidence=0.8,
        )

    async def _show_summary(self, user_id, db) -> dict:
        if not db or not user_id:
            return self._format_response(content="暂无记录数据。", confidence=0.5)
        try:
            from sqlalchemy import text as sa_text
            row = await db.execute(
                sa_text("""
                    SELECT COUNT(*) as total,
                           COUNT(DISTINCT DATE(logged_at)) as days
                    FROM habit_logs
                    WHERE user_id = :uid AND logged_at > NOW() - INTERVAL '30 days'
                """),
                {"uid": user_id}
            )
            result = row.mappings().first()
            total = result["total"] if result else 0
            days = result["days"] if result else 0
            return self._format_response(
                content=f"最近30天：共记录{total}次，活跃{days}天。每一次记录都是进步！",
                stats={"total": total, "active_days": days, "period": "30d"},
                confidence=0.8,
            )
        except Exception as e:
            return self._format_response(content="统计暂不可用。", confidence=0.3)


# ═══════════════════════════════════════════════════════════
# community_guide — 社区引导（四同道者）
# ═══════════════════════════════════════════════════════════

class CommunityGuideAgent(BaseAssistantAgent):
    """社区引导 — 四同道者匹配 + 互动引导"""

    @property
    def name(self) -> str:
        return "community_guide"

    @property
    def domain(self) -> str:
        return "community"

    async def run(self, message: str, **kwargs) -> Dict[str, Any]:
        if not await self.safety_check(message):
            return self._format_response(content="安全拦截", safety_intercepted=True)

        user_id = kwargs.get("user_id")
        db = kwargs.get("db")

        if any(w in message for w in ["同道者", "伙伴", "同伴", "结对", "匹配"]):
            return await self._find_peers(user_id, db)
        elif any(w in message for w in ["社区", "活动", "挑战", "打卡圈"]):
            return await self._show_activities(user_id, db)
        else:
            return self._format_response(
                content=(
                    "在行健社区，你可以找到和你目标相似的同道者一起成长。\n\n"
                    "你可以问我：「帮我找同道者」或「有什么社区活动」"
                ),
                confidence=0.6,
            )

    async def _find_peers(self, user_id, db) -> dict:
        if not db or not user_id:
            return self._format_response(content="同道者匹配需要登录。", confidence=0.5)
        try:
            from sqlalchemy import text as sa_text
            row = await db.execute(
                sa_text("""
                    SELECT COUNT(*) as peer_count
                    FROM companion_relations
                    WHERE user_id = :uid OR companion_id = :uid
                """),
                {"uid": user_id}
            )
            count = row.scalar() or 0
            if count > 0:
                return self._format_response(
                    content=f"你已有{count}位同道者。查看「同道者」页面了解更多互动机会！",
                    peer_count=count,
                    confidence=0.8,
                )
            return self._format_response(
                content="暂未匹配到同道者。完成更多评估后，系统会为你推荐目标相似的伙伴。",
                action="peer_matching_pending",
                confidence=0.6,
            )
        except Exception:
            return self._format_response(content="同道者查询暂不可用。", confidence=0.3)

    async def _show_activities(self, user_id, db) -> dict:
        if not db:
            return self._format_response(content="活动信息暂不可用。", confidence=0.3)
        try:
            from sqlalchemy import text as sa_text
            rows = await db.execute(
                sa_text("SELECT title, start_date FROM challenges WHERE is_active = true ORDER BY start_date LIMIT 5")
            )
            activities = [dict(r) for r in rows.mappings().all()]
            if activities:
                text = "当前社区活动:\n\n" + "\n".join(
                    f"· {a['title']}" for a in activities
                )
                return self._format_response(content=text, activities=activities, confidence=0.8)
            return self._format_response(content="暂无进行中的社区活动，敬请期待！", confidence=0.6)
        except Exception:
            return self._format_response(content="活动查询暂不可用。", confidence=0.3)


# ═══════════════════════════════════════════════════════════
# content_recommender — 内容推荐
# ═══════════════════════════════════════════════════════════

class ContentRecommenderAgent(BaseAssistantAgent):
    """内容推荐 — 基于阶段+兴趣的个性化推荐"""

    @property
    def name(self) -> str:
        return "content_recommender"

    @property
    def domain(self) -> str:
        return "content"

    STAGE_CONTENT = {
        "S0": ["慢性病基础知识", "健康生活方式入门", "成功案例分享"],
        "S1": ["行为改变的科学", "小步行动指南", "动机探索练习"],
        "S2": ["目标设定工具", "习惯养成方法", "营养运动基础"],
        "S3": ["实操技巧视频", "同伴经验分享", "阶段性挑战"],
        "S4": ["维持策略", "复发预防", "深度专题文章"],
        "S5": ["进阶健康知识", "教练成长路径", "社区贡献指南"],
    }

    async def run(self, message: str, **kwargs) -> Dict[str, Any]:
        if not await self.safety_check(message):
            return self._format_response(content="安全拦截", safety_intercepted=True)

        profile = kwargs.get("user_profile", {})
        stage = profile.get("ttm_stage", "S0")
        db = kwargs.get("db")

        # 基于阶段的推荐
        stage_recs = self.STAGE_CONTENT.get(stage, self.STAGE_CONTENT["S0"])

        # 从知识库补充
        db_recs = await self._fetch_content(stage, db)

        if db_recs:
            return self._format_response(
                content=f"为你推荐:\n\n" + "\n".join(f"· {r['title']}" for r in db_recs[:5]),
                recommendations=db_recs[:5],
                stage=stage,
                confidence=0.8,
            )

        return self._format_response(
            content=f"根据你的阶段，推荐学习:\n\n" + "\n".join(f"· {r}" for r in stage_recs),
            recommendations=stage_recs,
            stage=stage,
            confidence=0.6,
        )

    async def _fetch_content(self, stage, db) -> list:
        if not db:
            return []
        try:
            from sqlalchemy import text as sa_text
            rows = await db.execute(
                sa_text("""
                    SELECT id, title, category FROM knowledge_documents
                    WHERE is_published = true
                    ORDER BY created_at DESC LIMIT 10
                """)
            )
            return [dict(r) for r in rows.mappings().all()]
        except Exception:
            return []
