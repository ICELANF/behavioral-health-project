"""
新手引导Agent (TrustGuide) — 用户层入口

职责:
  1. 首次交互引导（平台介绍、功能导航）
  2. 初始信任评估（trust_score冷启动）
  3. 自主模式探测（agency_mode初始化）
  4. 引导完成首次评估

对接:
  - core/trust_score_engine → 信任分计算
  - core/agency_engine → 自主模式引擎
  - assessment系统 → 引导首次评估
"""
from __future__ import annotations
import logging
from typing import Any, Dict, Optional

from ..base import BaseAssistantAgent

logger = logging.getLogger(__name__)

ONBOARDING_STAGES = {
    "welcome": {
        "order": 0,
        "message": (
            "你好！欢迎来到行健平台。\n\n"
            "我是你的健康成长伙伴，会一直陪伴你的健康之旅。"
            "在开始之前，我想简单了解一下你，这样我能更好地帮助你。\n\n"
            "准备好了吗？"
        ),
        "next": "motivation",
    },
    "motivation": {
        "order": 1,
        "prompt": "是什么让你来到这里？（比如：想改善睡眠、管理慢性病、调整饮食习惯等）",
        "extracts": ["health_goal", "motivation_level"],
        "next": "baseline",
    },
    "baseline": {
        "order": 2,
        "prompt": "你觉得自己目前的健康状况怎么样？（1-10分，10分是非常好）",
        "extracts": ["self_rated_health"],
        "next": "agency_probe",
    },
    "agency_probe": {
        "order": 3,
        "prompt": (
            "当你决定做出一个健康改变时，你通常会：\n"
            "A. 自己研究制定计划\n"
            "B. 希望有人给我具体指导\n"
            "C. 想有人陪我一起做\n"
            "D. 需要先弄清楚为什么要改变"
        ),
        "extracts": ["agency_mode_hint"],
        "next": "assessment_invite",
    },
    "assessment_invite": {
        "order": 4,
        "prompt": (
            "了解你了！为了给你更精准的建议，"
            "我们有一份简短的健康行为评估（约5分钟），"
            "完成后你会获得个性化的成长路线图。\n\n"
            "想现在开始吗？"
        ),
        "next": "complete",
    },
    "complete": {
        "order": 5,
        "message": (
            "太好了！你已经迈出了第一步。\n\n"
            "接下来你可以随时问我健康问题，"
            "或者开始你的首次评估。加油！"
        ),
        "next": None,
    },
}

AGENCY_MAP = {
    "A": "self_directed",
    "B": "guided",
    "C": "collaborative",
    "D": "contemplative",
}


class Agent(BaseAssistantAgent):
    """新手引导 — TrustGuide"""

    @property
    def name(self) -> str:
        return "onboarding_guide"

    @property
    def domain(self) -> str:
        return "onboarding"

    async def run(self, message: str, **kwargs) -> Dict[str, Any]:
        user_id = kwargs.get("user_id")
        session_context = kwargs.get("session_context", {})
        db = kwargs.get("db")

        # 确定当前引导阶段
        current_stage = session_context.get("onboarding_stage", "welcome")

        if current_stage == "welcome":
            return self._stage_welcome()

        elif current_stage == "motivation":
            return await self._stage_motivation(message, user_id, db)

        elif current_stage == "baseline":
            return await self._stage_baseline(message, user_id, db)

        elif current_stage == "agency_probe":
            return await self._stage_agency_probe(message, user_id, db)

        elif current_stage == "assessment_invite":
            return self._stage_assessment_invite(message)

        elif current_stage == "complete":
            return self._stage_complete()

        else:
            return self._stage_welcome()

    def _stage_welcome(self) -> dict:
        config = ONBOARDING_STAGES["welcome"]
        return self._format_response(
            content=config["message"],
            onboarding_stage="welcome",
            next_stage="motivation",
            progress=0.0,
        )

    async def _stage_motivation(self, message: str, user_id, db) -> dict:
        # 提取健康目标
        health_goal = message.strip()

        # 初始化trust_score
        await self._init_trust_score(user_id, "motivation_shared", db)

        config = ONBOARDING_STAGES["motivation"]
        return self._format_response(
            content=f"「{health_goal[:30]}」—— 很好的目标！\n\n{ONBOARDING_STAGES['baseline']['prompt']}",
            onboarding_stage="motivation",
            next_stage="baseline",
            extracted={"health_goal": health_goal},
            progress=0.25,
        )

    async def _stage_baseline(self, message: str, user_id, db) -> dict:
        # 提取自评分数
        import re
        score_match = re.search(r'(\d+)', message)
        health_score = int(score_match.group(1)) if score_match else 5
        health_score = max(1, min(10, health_score))

        await self._update_profile(user_id, {"self_rated_health": health_score}, db)

        return self._format_response(
            content=f"收到，{health_score}分。\n\n{ONBOARDING_STAGES['agency_probe']['prompt']}",
            onboarding_stage="baseline",
            next_stage="agency_probe",
            extracted={"self_rated_health": health_score},
            progress=0.5,
        )

    async def _stage_agency_probe(self, message: str, user_id, db) -> dict:
        # 解析自主模式
        msg_upper = message.strip().upper()
        agency = None
        for key, mode in AGENCY_MAP.items():
            if key in msg_upper:
                agency = mode
                break
        if not agency:
            agency = "collaborative"  # 默认

        # 写入agency_mode
        await self._init_agency_mode(user_id, agency, db)
        await self._init_trust_score(user_id, "agency_revealed", db)

        mode_names = {
            "self_directed": "自主探索型",
            "guided": "引导跟随型",
            "collaborative": "协作陪伴型",
            "contemplative": "深思熟虑型",
        }

        return self._format_response(
            content=(
                f"了解了，你是「{mode_names.get(agency, agency)}」风格。\n\n"
                f"{ONBOARDING_STAGES['assessment_invite']['prompt']}"
            ),
            onboarding_stage="agency_probe",
            next_stage="assessment_invite",
            extracted={"agency_mode": agency},
            progress=0.75,
        )

    def _stage_assessment_invite(self, message: str) -> dict:
        positive = any(w in message for w in ["好", "是", "开始", "可以", "行", "来", "走"])
        if positive:
            return self._format_response(
                content=ONBOARDING_STAGES["complete"]["message"],
                onboarding_stage="assessment_invite",
                next_stage="complete",
                action="start_assessment",
                progress=1.0,
            )
        return self._format_response(
            content="没关系，你随时可以开始评估。现在有什么想问我的吗？",
            onboarding_stage="assessment_invite",
            next_stage="complete",
            progress=0.9,
        )

    def _stage_complete(self) -> dict:
        return self._format_response(
            content="有什么健康问题随时问我！",
            onboarding_stage="complete",
            onboarding_finished=True,
            progress=1.0,
        )

    # ── 引擎对接 ──

    async def _init_trust_score(self, user_id, event: str, db):
        if not user_id or not db:
            return
        try:
            from core.trust_score_engine import TrustScoreEngine
            engine = TrustScoreEngine()
            engine.record_event(user_id, event)
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"trust_score初始化失败: {e}")

    async def _init_agency_mode(self, user_id, mode: str, db):
        if not user_id or not db:
            return
        try:
            from core.agency_engine import AgencyEngine
            engine = AgencyEngine()
            engine.set_initial_mode(user_id, mode)
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"agency_mode初始化失败: {e}")

    async def _update_profile(self, user_id, data: dict, db):
        if not user_id or not db:
            return
        try:
            from sqlalchemy import text as sa_text
            for key, value in data.items():
                await db.execute(
                    sa_text(f"UPDATE users SET {key} = :val WHERE id = :uid"),
                    {"val": value, "uid": user_id}
                )
        except Exception as e:
            logger.warning(f"profile更新失败: {e}")
