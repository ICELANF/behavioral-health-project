"""
3个整合型Agent
来源: §9.1.2 — 跨领域综合干预
"""
from __future__ import annotations
from .base import BaseAgent, AgentDomain, AgentInput, AgentResult, RiskLevel


class BehaviorRxAgent(BaseAgent):
    """行为处方师Agent — 跨全领域综合干预输出"""
    domain = AgentDomain.BEHAVIOR_RX
    display_name = "行为处方师"
    keywords = ["行为处方", "习惯", "戒烟", "依从性", "打卡", "任务"]
    priority = 2
    base_weight = 0.9

    def process(self, inp: AgentInput) -> AgentResult:
        stage = inp.profile.get("current_stage", "S0")
        spi = inp.profile.get("spi_score", 50)
        recs, tasks = [], []

        if stage in ("S0", "S1"):
            recs.append("以觉察为主, 安排观察型微任务(无执行压力)")
            tasks.append({"type": "awareness_task", "description": "记录一次饮食时间",
                          "difficulty": "minimal"})
        elif stage in ("S2", "S3"):
            recs.append("引入1-2个行为处方, 强调'试一试'而非'必须做'")
            tasks.append({"type": "trial_rx", "description": "餐前一杯水",
                          "difficulty": "easy"})
        elif stage in ("S4", "S5", "S6"):
            recs.append("完整行为处方执行, 追踪依从性, 自主调整")
            tasks.append({"type": "full_rx", "difficulty": "moderate"})

        result = AgentResult(
            agent_domain=self.domain.value,
            confidence=0.8,
            risk_level=RiskLevel.LOW,
            recommendations=recs, tasks=tasks,
            metadata={"stage": stage, "spi": spi},
        )
        return self._enhance_with_llm(result, inp)


class WeightAgent(BaseAgent):
    """体重管理师Agent — 多系统联动(饮食+运动+代谢+睡眠+心理)"""
    domain = AgentDomain.WEIGHT
    display_name = "体重管理师"
    keywords = ["体重", "减重", "BMI", "脂肪", "腰围", "减肥"]
    priority = 2
    base_weight = 0.85

    def process(self, inp: AgentInput) -> AgentResult:
        findings, recs = [], []
        bmi = inp.profile.get("bmi")
        if bmi and bmi >= 28:
            findings.append(f"BMI={bmi}, 属于肥胖范围")
            recs.append("多系统联动: 营养控碳 + 运动增肌减脂 + 睡眠优化 + 压力管理")
        elif bmi and bmi >= 24:
            findings.append(f"BMI={bmi}, 属于超重范围")
            recs.append("优先营养调整, 配合适度运动")
        result = AgentResult(
            agent_domain=self.domain.value,
            confidence=0.75 if findings else 0.5,
            risk_level=RiskLevel.MODERATE if (bmi and bmi >= 28) else RiskLevel.LOW,
            findings=findings, recommendations=recs,
        )
        return self._enhance_with_llm(result, inp)


class CardiacRehabAgent(BaseAgent):
    """心脏康复师Agent — 全方位康复方案"""
    domain = AgentDomain.CARDIAC_REHAB
    display_name = "心脏康复师"
    keywords = ["心脏", "心血管", "冠心病", "康复", "心梗", "支架"]
    priority = 1
    base_weight = 0.85

    def process(self, inp: AgentInput) -> AgentResult:
        findings, recs = [], []
        diagnoses = inp.profile.get("diagnoses", [])
        has_cardiac = any("心" in d or "冠" in d for d in diagnoses)
        if has_cardiac:
            findings.append("心血管病史, 启动心脏康复路径")
            recs.append("分阶段心脏康复: 评估→低强度→渐进→维护")
            recs.append("运动处方须在安全心率区间(HRmax×50-70%)")
        result = AgentResult(
            agent_domain=self.domain.value,
            confidence=0.8 if has_cardiac else 0.3,
            risk_level=RiskLevel.MODERATE if has_cardiac else RiskLevel.LOW,
            findings=findings, recommendations=recs,
        )
        return self._enhance_with_llm(result, inp)


# ── 注册到 AGENT_CLASS_REGISTRY ──
from .base import AGENT_CLASS_REGISTRY

AGENT_CLASS_REGISTRY.update({
    "behavior_rx": BehaviorRxAgent,
    "weight": WeightAgent,
    "cardiac_rehab": CardiacRehabAgent,
})
