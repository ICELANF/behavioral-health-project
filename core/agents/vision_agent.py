# -*- coding: utf-8 -*-
"""
VisionGuideAgent — 视力保护引导 Agent

意图处理 (5 种):
  - behavior_checkin: 打卡反馈 + 差距提示 + 连续天数
  - goal_inquiry: 五维目标展示 + 今日完成度
  - guardian_summary: 监护人版摘要
  - resistance_handling: TTM 阶段感知阻抗应对
  - expert_consultation: 风险等级分流 (URGENT→24h / ALERT→1-2工作日 / 其他→自助)

VisionRxGenerator: 三格式处方 (student / guardian / coach)
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from .base import (
    BaseAgent, AgentDomain, AgentInput, AgentResult,
    RiskLevel,
)

logger = logging.getLogger(__name__)


class VisionGuideAgent(BaseAgent):
    """视力保护引导 Agent"""

    domain = AgentDomain.VISION
    display_name = "视力保护引导"
    keywords = [
        "视力", "近视", "眼睛", "屏幕", "户外", "眼保健操",
        "叶黄素", "散光", "远视", "眼轴", "度数", "配镜", "OK镜",
        "眼镜", "视力检查", "视力保护", "护眼", "蓝光", "用眼",
    ]
    data_fields = ["vision"]
    priority = 3
    base_weight = 0.8
    evidence_tier = "T2"

    # 意图关键词映射
    _INTENT_CHECKIN = ["打卡", "记录", "今天做了", "完成了"]
    _INTENT_GOAL = ["目标", "标准", "应该", "多少"]
    _INTENT_GUARDIAN = ["孩子", "报告", "监护", "家长"]
    _INTENT_RESIST = ["不想", "做不到", "太难", "没用", "坚持不了"]
    _INTENT_EXPERT = ["医生", "检查", "就诊", "专家", "配镜"]

    def _detect_intent(self, message: str) -> str:
        """意图识别"""
        msg = message.lower()
        if any(kw in msg for kw in self._INTENT_RESIST):
            return "resistance_handling"
        if any(kw in msg for kw in self._INTENT_EXPERT):
            return "expert_consultation"
        if any(kw in msg for kw in self._INTENT_GUARDIAN):
            return "guardian_summary"
        if any(kw in msg for kw in self._INTENT_GOAL):
            return "goal_inquiry"
        if any(kw in msg for kw in self._INTENT_CHECKIN):
            return "behavior_checkin"
        return "general_vision"

    def process(self, inp: AgentInput) -> AgentResult:
        """主处理入口"""
        intent = self._detect_intent(inp.message)
        handler = getattr(self, f"_handle_{intent}", self._handle_general_vision)
        return handler(inp)

    def _handle_behavior_checkin(self, inp: AgentInput) -> AgentResult:
        """打卡反馈"""
        findings = ["检测到视力行为打卡意图"]
        recs = [
            "请通过视力打卡页面记录今天的用眼行为",
            "记录包括: 户外时间、屏幕使用、眼保健操、叶黄素、睡眠",
        ]
        # 如有设备数据中的视力信息
        vision_data = inp.device_data.get("vision", {})
        if vision_data:
            score = vision_data.get("behavior_score")
            if score is not None:
                if score >= 75:
                    recs.insert(0, f"今天评分 {score:.0f} 分，做得很棒！")
                elif score >= 45:
                    recs.insert(0, f"今天评分 {score:.0f} 分，继续加油！")
                else:
                    recs.insert(0, f"今天评分 {score:.0f} 分，试试增加户外活动时间")

        return AgentResult(
            agent_domain=self.domain.value,
            confidence=0.85,
            risk_level=RiskLevel.LOW,
            findings=findings,
            recommendations=recs,
            metadata={"intent": "behavior_checkin"},
        )

    def _handle_goal_inquiry(self, inp: AgentInput) -> AgentResult:
        """五维目标展示"""
        recs = [
            "视力保护五维目标参考:",
            "1. 户外活动: 每天至少 120 分钟",
            "2. 屏幕使用: 每天不超过 120 分钟，单次不超过 20 分钟",
            "3. 眼保健操: 每天至少做一次",
            "4. 叶黄素: 每天摄入 10mg (深色蔬菜、蛋黄等)",
            "5. 睡眠: 每天至少 8 小时",
        ]
        return AgentResult(
            agent_domain=self.domain.value,
            confidence=0.9,
            risk_level=RiskLevel.LOW,
            findings=["用户咨询视力行为目标"],
            recommendations=recs,
            metadata={"intent": "goal_inquiry"},
        )

    def _handle_guardian_summary(self, inp: AgentInput) -> AgentResult:
        """监护人版摘要"""
        recs = [
            "您可以在「孩子视力报告」页面查看详细数据",
            "包括: 每日行为评分趋势、各维度完成度、风险等级",
            "如有异常，系统会自动通知您",
        ]
        return AgentResult(
            agent_domain=self.domain.value,
            confidence=0.85,
            risk_level=RiskLevel.LOW,
            findings=["监护人咨询孩子视力情况"],
            recommendations=recs,
            metadata={"intent": "guardian_summary"},
        )

    def _handle_resistance_handling(self, inp: AgentInput) -> AgentResult:
        """TTM 阶段感知的阻抗应对 (共情→最小行动→自主权)"""
        findings = ["检测到行为阻抗信号"]
        recs = [
            "理解你的感受，改变确实不容易。",
            "不需要一下子做到完美，试试一个最小的改变:",
            "比如今天出门走 10 分钟，或者每看屏幕 20 分钟就远眺 20 秒。",
            "你可以选择自己觉得最容易的一步开始，决定权在你手中。",
        ]
        return AgentResult(
            agent_domain=self.domain.value,
            confidence=0.9,
            risk_level=RiskLevel.LOW,
            findings=findings,
            recommendations=recs,
            metadata={"intent": "resistance_handling", "approach": "empathy_minimal_action"},
        )

    def _handle_expert_consultation(self, inp: AgentInput) -> AgentResult:
        """根据风险等级分流"""
        vision_data = inp.device_data.get("vision", {})
        risk = vision_data.get("risk_level", "normal")

        if risk == "urgent":
            recs = [
                "根据您的数据，建议尽快预约眼科专家检查",
                "系统已通知您的教练，将在 24 小时内跟进",
            ]
            risk_level = RiskLevel.HIGH
        elif risk == "alert":
            recs = [
                "建议在 1-2 个工作日内预约眼科检查",
                "您的教练会协助安排专家咨询",
            ]
            risk_level = RiskLevel.MODERATE
        else:
            recs = [
                "目前数据在正常范围内",
                "建议每半年进行一次常规视力检查",
                "如需专业咨询，可在「视力档案」页面申请",
            ]
            risk_level = RiskLevel.LOW

        return AgentResult(
            agent_domain=self.domain.value,
            confidence=0.85,
            risk_level=risk_level,
            findings=[f"视力专家咨询请求 (当前风险: {risk})"],
            recommendations=recs,
            metadata={"intent": "expert_consultation", "risk_level": risk},
        )

    def _handle_general_vision(self, inp: AgentInput) -> AgentResult:
        """通用视力话题"""
        recs = [
            "保护视力的核心原则: 多户外、少屏幕、好习惯",
            "坚持每日打卡记录，系统会根据你的数据给出个性化建议",
        ]
        return AgentResult(
            agent_domain=self.domain.value,
            confidence=0.75,
            risk_level=RiskLevel.LOW,
            findings=["一般性视力话题咨询"],
            recommendations=recs,
            metadata={"intent": "general_vision"},
        )


# ══════════════════════════════════════════
# VisionRxGenerator: 三格式处方
# ══════════════════════════════════════════

class VisionRxGenerator:
    """
    生成视力行为干预处方 (三种格式, 均需教练审核后推送)
    """

    @staticmethod
    def generate_student_rx(score: float, gaps: list[str], ttm_stage: str = "S0") -> dict:
        """学生版处方: 简洁、正向、可操作"""
        actions = []
        if "户外" in str(gaps):
            actions.append("每天增加 15 分钟户外活动 (课间走走也算!)")
        if "屏幕" in str(gaps):
            actions.append("设置屏幕使用提醒，每 20 分钟休息一次")
        if "眼保健操" in str(gaps):
            actions.append("跟着视频做一次眼保健操 (只需 5 分钟)")
        if not actions:
            actions.append("继续保持好习惯，挑战连续 7 天满分！")

        return {
            "format": "student",
            "title": "你的视力保护小任务",
            "score": score,
            "actions": actions,
            "encouragement": "每个小改变都在保护你的眼睛 💪",
        }

    @staticmethod
    def generate_guardian_rx(student_name: str, score: float, risk_level: str, gaps: list[str]) -> dict:
        """监护人版处方: 数据导向、行动建议"""
        suggestions = []
        if risk_level in ("alert", "urgent"):
            suggestions.append("建议尽快预约眼科检查")
        if "户外" in str(gaps):
            suggestions.append("周末安排户外亲子活动")
        if "屏幕" in str(gaps):
            suggestions.append("共同约定屏幕使用规则")
        if "睡眠" in str(gaps):
            suggestions.append("关注孩子的就寝时间")

        return {
            "format": "guardian",
            "title": f"{student_name} 的视力保护报告",
            "score": score,
            "risk_level": risk_level,
            "suggestions": suggestions,
        }

    @staticmethod
    def generate_coach_rx(user_id: int, score: float, risk_level: str, trend: str, gaps: list[str]) -> dict:
        """教练版处方: 专业分析、干预策略"""
        strategies = []
        if trend == "declining":
            strategies.append("评分持续下降，建议主动沟通了解原因")
        if risk_level == "urgent":
            strategies.append("高风险: 需安排专家转介")
        if risk_level == "alert":
            strategies.append("中高风险: 加强行为干预频次")
        if "户外" in str(gaps):
            strategies.append("户外时间不足，建议制定户外活动方案")
        if "屏幕" in str(gaps):
            strategies.append("屏幕使用超标，建议 20-20-20 规则干预")

        return {
            "format": "coach",
            "user_id": user_id,
            "score": score,
            "risk_level": risk_level,
            "trend": trend,
            "strategies": strategies,
        }
