"""
危机响应Agent — 用户层最高优先级

职责:
  1. 检测自伤/自杀/紧急医疗意图
  2. 立即提供安全资源
  3. 触发教练层告警 + 推送
  4. 记录危机事件用于后续跟进

触发条件 (Sheet⑮ 安全管线):
  - 关键词匹配 (自杀/自残/伤害/急救)
  - 情绪风暴检测 (连续负面情绪升级)
  - 被其他Agent转介
"""
from __future__ import annotations
import logging
import re
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..base import BaseAssistantAgent

logger = logging.getLogger(__name__)

# ── 危机分级 ──

CRISIS_LEVELS = {
    "critical": {
        "keywords": ["自杀", "自残", "结束生命", "不想活了", "去死", "割腕", "跳楼", "上吊", "吞药"],
        "action": "immediate_escalation",
        "response_template": "critical",
    },
    "emergency": {
        "keywords": ["胸痛", "呼吸困难", "大量出血", "意识不清", "昏迷", "抽搐", "中毒", "过敏休克"],
        "action": "emergency_referral",
        "response_template": "medical_emergency",
    },
    "high": {
        "keywords": ["伤害自己", "活着没意思", "好累不想动", "崩溃了", "受不了了", "没人在乎",
                     "很痛苦", "绝望", "撑不下去"],
        "action": "coach_alert",
        "response_template": "emotional_crisis",
    },
    "moderate": {
        "keywords": ["焦虑发作", "恐慌", "失控", "停不下来", "强迫", "幻听", "幻觉"],
        "action": "coach_notify",
        "response_template": "psychological_distress",
    },
}

HOTLINES = {
    "crisis": "全国24小时心理援助热线: 400-161-9995",
    "emergency": "急救电话: 120",
    "youth": "希望24热线: 400-161-9995",
    "domestic": "全国妇女维权热线: 12338",
}


class Agent(BaseAssistantAgent):
    """危机响应 — 安全第一，永远优先于其他Agent"""

    @property
    def name(self) -> str:
        return "crisis_responder"

    @property
    def domain(self) -> str:
        return "safety"

    @property
    def priority(self) -> int:
        return 0  # 最高优先级

    async def run(self, message: str, **kwargs) -> Dict[str, Any]:
        user_id = kwargs.get("user_id")
        db = kwargs.get("db")

        # 1. 多级危机检测
        crisis = self._detect_crisis(message)

        if not crisis:
            return self._format_response(
                content=None,
                crisis_detected=False,
                action="pass_through",
            )

        level = crisis["level"]
        action = crisis["action"]

        # 2. 生成安全响应
        response_text = self._build_crisis_response(level, message)

        # 3. 触发告警链
        alerts_sent = await self._trigger_alerts(level, user_id, message, db)

        # 4. 记录危机事件
        await self._log_crisis_event(user_id, level, message, db)

        return self._format_response(
            content=response_text,
            crisis_detected=True,
            crisis_level=level,
            action=action,
            alerts_sent=alerts_sent,
            hotlines=self._get_relevant_hotlines(level),
            override_other_agents=True,
        )

    def _detect_crisis(self, message: str) -> Optional[dict]:
        """多级危机检测"""
        msg_lower = message.lower()

        for level, config in CRISIS_LEVELS.items():
            for kw in config["keywords"]:
                if kw in msg_lower:
                    return {
                        "level": level,
                        "keyword": kw,
                        "action": config["action"],
                        "template": config["response_template"],
                    }

        # 情绪升级模式检测
        negative_count = sum(1 for word in
            ["难过", "害怕", "无助", "孤独", "疲惫", "厌倦", "愤怒", "沮丧"]
            if word in msg_lower)
        if negative_count >= 3:
            return {
                "level": "high",
                "keyword": f"emotional_escalation({negative_count})",
                "action": "coach_alert",
                "template": "emotional_crisis",
            }

        return None

    def _build_crisis_response(self, level: str, message: str) -> str:
        """构建安全响应 — 温暖、专业、不加重焦虑"""

        if level == "critical":
            return (
                "我听到了你说的话，我很关心你现在的状况。\n\n"
                "你现在的感受很重要，你愿意告诉我更多吗？\n\n"
                "同时，我想让你知道，专业的帮助就在身边：\n"
                f"📞 {HOTLINES['crisis']}\n"
                f"📞 {HOTLINES['emergency']}\n\n"
                "电话那头有人在等着帮助你。如果你现在不方便打电话，"
                "你的健康教练也已经收到通知，会尽快联系你。\n\n"
                "你并不孤单。"
            )

        elif level == "emergency":
            return (
                "这听起来可能是紧急医疗情况。\n\n"
                f"请立即拨打 {HOTLINES['emergency']}\n\n"
                "在等待救援时：\n"
                "· 保持冷静，找安全的地方坐下\n"
                "· 如果身边有人，请让他们陪伴你\n"
                "· 不要独自驾车或做剧烈运动\n\n"
                "你的健康教练已经收到通知。"
            )

        elif level == "high":
            return (
                "我感受到你现在很不容易，谢谢你愿意说出来。\n\n"
                "你的感受是真实的，也是可以被理解的。"
                "在困难的时候愿意表达，本身就是一种力量。\n\n"
                "如果你想和专业的人聊聊，随时可以拨打：\n"
                f"📞 {HOTLINES['crisis']}\n\n"
                "你的健康教练也会很快了解到你的情况，"
                "为你提供更具体的支持。\n\n"
                "现在，有什么我能帮你的吗？"
            )

        else:  # moderate
            return (
                "听起来你正在经历一些困扰。\n\n"
                "这些感受虽然不舒服，但它们是身体在告诉你需要关注自己。"
                "我们可以一起想想怎么让你感觉好一些。\n\n"
                "如果这些感受影响了你的日常生活，"
                "建议和你的健康教练或专业心理咨询师谈谈。\n\n"
                f"随时可用的支持热线: {HOTLINES['crisis']}"
            )

    async def _trigger_alerts(
        self, level: str, user_id: Optional[str], message: str, db=None
    ) -> List[str]:
        """触发告警链"""
        alerts = []

        if not db or not user_id:
            return ["no_db_connection"]

        try:
            from sqlalchemy import text as sa_text

            # 写入推送队列
            if level in ("critical", "emergency", "high"):
                await db.execute(
                    sa_text("""
                        INSERT INTO coach_schema.coach_push_queue
                            (user_id, push_type, priority, payload, created_at)
                        VALUES
                            (:user_id, 'crisis_alert', :priority,
                             :payload, NOW())
                    """),
                    {
                        "user_id": user_id,
                        "priority": {"critical": 0, "emergency": 0, "high": 1}.get(level, 2),
                        "payload": f'{{"level":"{level}","excerpt":"{message[:100]}"}}',
                    }
                )
                alerts.append("coach_push_queue")

            # critical/emergency额外写入review_items
            if level in ("critical", "emergency"):
                await db.execute(
                    sa_text("""
                        INSERT INTO coach_schema.coach_review_items
                            (user_id, review_type, priority, status, content, created_at)
                        VALUES
                            (:user_id, 'crisis', 0, 'pending',
                             :content, NOW())
                    """),
                    {
                        "user_id": user_id,
                        "content": f"危机响应触发 [{level}]: {message[:200]}",
                    }
                )
                alerts.append("coach_review_items")

            await db.commit()

        except Exception as e:
            logger.error(f"危机告警写入失败: {e}")
            alerts.append(f"error:{e}")

        return alerts

    async def _log_crisis_event(
        self, user_id: Optional[str], level: str, message: str, db=None
    ):
        """记录危机事件"""
        if not db:
            return
        try:
            from sqlalchemy import text as sa_text
            await db.execute(
                sa_text("""
                    INSERT INTO cross_layer_audit_log
                        (id, actor_id, actor_role, action, layer_from, layer_to,
                         resource_type, result, metadata, timestamp)
                    VALUES
                        (gen_random_uuid(), :user_id, 'system', 'crisis_detection',
                         'assistant', 'professional', 'crisis_event', 'allowed',
                         :metadata, NOW())
                """),
                {
                    "user_id": user_id or "0",
                    "metadata": f'{{"level":"{level}","length":{len(message)}}}',
                }
            )
        except Exception as e:
            logger.error(f"危机日志写入失败: {e}")

    def _get_relevant_hotlines(self, level: str) -> dict:
        if level in ("critical",):
            return {"crisis": HOTLINES["crisis"], "emergency": HOTLINES["emergency"]}
        elif level == "emergency":
            return {"emergency": HOTLINES["emergency"]}
        return {"crisis": HOTLINES["crisis"]}
