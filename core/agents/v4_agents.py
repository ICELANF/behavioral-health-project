"""
V4.0 Three Core Agents (TABLE 5 四合一精简):

1. JourneyCompanion (旅程伴行Agent)
   = ProactiveCompanion + BehaviorReview + AdherenceTracker
   全程S0-S5陪伴, agency三态交互, trust_score感知

2. GrowthReflection (成长复盘Agent)
   = GrowthArchive + SelfAwareness
   周/月成长叙事, 模式觉察, 身份微触碰

3. CoachCopilot (教练副驾驶Agent)
   = CoachAssistant + CoachTraining
   嵌入BFR/M-Action, 学员周报自动生成, 预警异常
"""
from __future__ import annotations

import logging
from datetime import datetime

from .base import (
    BaseAgent, AgentInput, AgentResult, AgentDomain, RiskLevel,
    AGENT_CLASS_REGISTRY,
)

logger = logging.getLogger(__name__)

# ── Stage-Awareness Helpers ─────────────────────
_STAGE_ORDER = [
    "s0_authorization", "s1_awareness", "s2_trial",
    "s3_pathway", "s4_internalization", "s5_graduation",
]

_STAGE_GUIDANCE = {
    "s0_authorization": {
        "focus": "建立安全感与信任",
        "tone": "温和、接纳、不判断",
        "key_actions": ["倾听用户故事", "确认用户感受", "不急于给建议"],
    },
    "s1_awareness": {
        "focus": "帮助用户看见现状",
        "tone": "好奇、探索、陪伴",
        "key_actions": ["引导数据观察", "提问而非告知", "鼓励自我发现"],
    },
    "s2_trial": {
        "focus": "支持行为尝试",
        "tone": "鼓励、耐心、小步慢走",
        "key_actions": ["设定微小目标", "庆祝每次尝试", "normalizing失败"],
    },
    "s3_pathway": {
        "focus": "巩固行为路径",
        "tone": "协作、赋能、逐步放手",
        "key_actions": ["回顾成功模式", "建立行为链", "培养内在动力"],
    },
    "s4_internalization": {
        "focus": "内化为身份认同",
        "tone": "反思、深层、身份层对话",
        "key_actions": ["探索价值观连接", "身份叙事", "减少外部依赖"],
    },
    "s5_graduation": {
        "focus": "庆祝成长、传递价值",
        "tone": "尊重、平等、引导传承",
        "key_actions": ["成长叙事总结", "鼓励帮助他人", "持续精进"],
    },
}


class JourneyCompanionAgent(BaseAgent):
    """
    旅程伴行Agent — 全程S0-S5陪伴
    融合: ProactiveCompanion + BehaviorReview + AdherenceTracker
    """
    domain = AgentDomain.COACHING
    display_name = "旅程伴行"
    keywords = [
        "旅程", "陪伴", "阶段", "进展", "困难", "坚持不下去",
        "我在哪", "目前", "接下来", "回顾", "总结",
        "依从", "打卡", "连续", "中断", "放弃",
    ]
    data_fields = []  # Cross-domain: uses profile + journey state
    priority = 1
    base_weight = 0.90
    enable_llm = True

    def process(self, inp: AgentInput) -> AgentResult:
        findings, recs, tasks = [], [], []

        stage = inp.profile.get("current_stage", "s0_authorization")
        agency_mode = inp.context.get("agency_mode", "passive")

        guidance = _STAGE_GUIDANCE.get(stage, _STAGE_GUIDANCE["s0_authorization"])

        # Stage-based findings
        try:
            stage_idx = _STAGE_ORDER.index(stage)
        except ValueError:
            stage_idx = 0

        findings.append(f"当前阶段: {stage} ({guidance['focus']})")
        findings.append(f"交互模式: {agency_mode}")

        # Stage-specific recommendations
        for action in guidance["key_actions"]:
            recs.append(action)

        # Adherence check from profile
        adherence = inp.profile.get("adherence_rate", 0)
        if isinstance(adherence, (int, float)) and adherence < 0.5:
            findings.append(f"依从率较低({adherence:.0%}), 需要关注")
            recs.append("回顾最近的行为中断, 探索背后的原因")
            tasks.append({"type": "adherence_review", "duration": 1, "unit": "session"})

        # Agency-aware interaction style
        if agency_mode == "passive":
            recs.insert(0, "以照料者角色主动提供引导和支持")
        elif agency_mode == "transitional":
            recs.insert(0, "以同行者角色协作探索")
        elif agency_mode == "active":
            recs.insert(0, "以镜子角色倾听和反映")

        # Check for interruption/regression signals
        msg_lower = inp.message.lower()
        if any(kw in msg_lower for kw in ["放弃", "坚持不下去", "不想做了", "没用"]):
            findings.append("检测到放弃倾向信号")
            recs.append("先接纳用户的感受, 不急于劝说")
            recs.append("探索'这次和上次有什么不同'")

        # Stage progression suggestion
        if stage_idx >= 3:
            tasks.append({"type": "growth_review", "duration": 7, "unit": "day"})
            recs.append("可以回顾本阶段的成长记录")

        confidence = 0.85 if findings else 0.6
        risk = RiskLevel.MODERATE if (
            adherence and isinstance(adherence, (int, float)) and adherence < 0.3
        ) else RiskLevel.LOW

        result = AgentResult(
            agent_domain="journey_companion",
            confidence=confidence,
            risk_level=risk,
            findings=findings,
            recommendations=recs,
            tasks=tasks,
            metadata={
                "stage": stage,
                "agency_mode": agency_mode,
                "stage_guidance": guidance,
            },
        )
        return self._enhance_with_llm(result, inp)


class GrowthReflectionAgent(BaseAgent):
    """
    成长复盘Agent — 周/月成长叙事 + 模式觉察
    融合: GrowthArchive + SelfAwareness
    """
    domain = AgentDomain.COACHING
    display_name = "成长复盘"
    keywords = [
        "成长", "复盘", "反思", "觉察", "模式", "发现",
        "变化", "进步", "回顾", "日记", "记录",
        "我注意到", "我意识到", "我发现", "规律",
    ]
    data_fields = []
    priority = 3
    base_weight = 0.80
    enable_llm = True

    def process(self, inp: AgentInput) -> AgentResult:
        findings, recs, tasks = [], [], []
        agency_mode = inp.context.get("agency_mode", "passive")

        # Analyze text for reflection depth
        from core.agency_engine import AgencyEngine
        text_analysis = AgencyEngine._compute_s4_from_text(None, inp.message)

        if text_analysis >= 0.8:
            findings.append("觉察深度: 身份层反思 — 非常深入")
            recs.append("你的反思已经触及身份层面, 可以进一步探索'我想成为什么样的人'")
        elif text_analysis >= 0.5:
            findings.append("觉察深度: 模式觉察 — 正在发现规律")
            recs.append("你正在发现行为模式, 可以试着记录'每次这个模式出现时, 我的感受是什么'")
        elif text_analysis >= 0.2:
            findings.append("觉察深度: 表面觉察 — 开始留意")
            recs.append("开始觉察是很好的第一步, 可以试着写下今天让你印象最深的一个瞬间")
        else:
            findings.append("觉察深度: 初始阶段")
            recs.append("可以从'今天有什么让你感到意外的事?'开始练习觉察")

        # Agency-mode specific reflection prompts
        if agency_mode == "passive":
            recs.append("引导式反思: '这周让你最开心/最困扰的一件事是什么?'")
            tasks.append({"type": "guided_reflection", "duration": 1, "unit": "session"})
        elif agency_mode == "transitional":
            recs.append("探索式反思: '你注意到自己有什么新的行为模式了吗?'")
            tasks.append({"type": "pattern_journal", "duration": 7, "unit": "day"})
        elif agency_mode == "active":
            recs.append("深层反思: '这个发现如何改变了你对自己的看法?'")
            tasks.append({"type": "identity_reflection", "duration": 1, "unit": "session"})

        # Weekly/monthly narrative suggestion
        recs.append("建议每周写一次成长小结, 记录'我看到了什么+我做了什么+我想成为什么'")

        result = AgentResult(
            agent_domain="growth_reflection",
            confidence=0.75,
            risk_level=RiskLevel.LOW,
            findings=findings,
            recommendations=recs,
            tasks=tasks,
            metadata={
                "reflection_depth": text_analysis,
                "agency_mode": agency_mode,
            },
        )
        return self._enhance_with_llm(result, inp)


class CoachCopilotAgent(BaseAgent):
    """
    教练副驾驶Agent — 嵌入BFR/M-Action, 学员报告, 预警
    融合: CoachAssistant + CoachTraining
    """
    domain = AgentDomain.COACHING
    display_name = "教练副驾驶"
    keywords = [
        "教练", "学员", "报告", "周报", "预警", "异常",
        "处方", "干预", "微行动", "建议", "指导",
        "BFR", "行为", "案例", "督导",
    ]
    data_fields = ["cgm", "sleep", "hrv", "steps"]
    priority = 2
    base_weight = 0.85
    enable_llm = True

    def process(self, inp: AgentInput) -> AgentResult:
        findings, recs, tasks = [], [], []

        # Coach-specific: analyze student data
        device = inp.device_data or {}

        # Alert checks
        alerts = []
        cgm = device.get("cgm_value") or device.get("glucose")
        if cgm and isinstance(cgm, (int, float)):
            if cgm > 11.1:
                alerts.append(f"血糖异常偏高: {cgm} mmol/L")
            elif cgm < 3.9:
                alerts.append(f"血糖异常偏低: {cgm} mmol/L")

        sleep = device.get("sleep_hours")
        if sleep and isinstance(sleep, (int, float)) and sleep < 5:
            alerts.append(f"睡眠严重不足: {sleep}小时")

        hrv = device.get("hrv_sdnn")
        if hrv and isinstance(hrv, (int, float)) and hrv < 20:
            alerts.append(f"HRV异常偏低: {hrv}ms (压力/疲劳信号)")

        if alerts:
            findings.append(f"发现{len(alerts)}项异常预警:")
            findings.extend(alerts)
            recs.append("建议尽快与学员沟通, 了解近期情况")
            recs.append("考虑调整当前微行动处方的强度")

        # Student status summary
        stage = inp.profile.get("current_stage", "未知")
        adherence = inp.profile.get("adherence_rate", 0)
        findings.append(f"学员阶段: {stage}")
        findings.append(f"依从率: {adherence:.0%}" if isinstance(adherence, (int, float)) else "依从率: 未知")

        # Coach action recommendations
        if isinstance(adherence, (int, float)):
            if adherence < 0.3:
                recs.append("依从率极低, 建议: 1) 简化微行动 2) 电话/视频跟进 3) 探索阻碍因素")
                tasks.append({"type": "student_followup", "duration": 1, "unit": "day"})
            elif adherence < 0.6:
                recs.append("依从率偏低, 建议: 回顾行为处方难度是否匹配学员当前阶段")
                tasks.append({"type": "rx_review", "duration": 3, "unit": "day"})

        # Weekly report generation prompt
        recs.append("可以为该学员生成本周学习报告 (含数据趋势+行为分析+建议)")

        # BFR (Behavior Function Review) integration
        if any(kw in inp.message for kw in ["BFR", "功能分析", "行为功能"]):
            recs.append("BFR分析框架: 触发事件→行为反应→短期结果→长期后果")
            tasks.append({"type": "bfr_session", "duration": 1, "unit": "session"})

        risk = RiskLevel.HIGH if alerts else RiskLevel.LOW
        confidence = 0.9 if alerts else 0.7

        result = AgentResult(
            agent_domain="coach_copilot",
            confidence=confidence,
            risk_level=risk,
            findings=findings,
            recommendations=recs,
            tasks=tasks,
            metadata={
                "alerts": alerts,
                "student_stage": stage,
            },
        )
        return self._enhance_with_llm(result, inp)


class LifeDesignerAgent(BaseAgent):
    """
    生命设计Agent — 身份链训练 + LifeOS设计
    融合: CapabilityTrainer + IdentityEvolution
    Covers L5-L6: 身份层 + 精神层
    """
    domain = AgentDomain.COACHING
    display_name = "生命设计师"
    keywords = [
        "人生", "生命", "身份", "价值观", "使命", "意义",
        "未来", "目标", "梦想", "成为", "我是谁",
        "生命设计", "LifeOS", "脚本", "叙事",
    ]
    data_fields = []
    priority = 4
    base_weight = 0.75
    enable_llm = True

    def process(self, inp: AgentInput) -> AgentResult:
        findings, recs, tasks = [], [], []
        agency_mode = inp.context.get("agency_mode", "passive")
        stage = inp.profile.get("current_stage", "s0_authorization")

        # Only fully activate for advanced stages
        try:
            stage_idx = _STAGE_ORDER.index(stage)
        except ValueError:
            stage_idx = 0

        if stage_idx < 3:
            findings.append(f"当前阶段({stage})尚在行为层面, 身份工作将在后期展开")
            recs.append("当前聚焦于行为改变基础, 身份探索将自然浮现")
            result = AgentResult(
                agent_domain="life_designer",
                confidence=0.4,
                risk_level=RiskLevel.LOW,
                findings=findings, recommendations=recs,
            )
            return self._enhance_with_llm(result, inp)

        # Advanced stage identity work
        findings.append(f"阶段{stage}已进入身份层面工作范围")

        if "身份" in inp.message or "我是谁" in inp.message:
            recs.append("身份链练习: '我曾经是___, 我正在成为___, 我选择成为___'")
            tasks.append({"type": "identity_chain", "duration": 1, "unit": "session"})

        if "未来" in inp.message or "目标" in inp.message or "梦想" in inp.message:
            recs.append("LifeOS设计: 为未来3年制定一个生命操作系统蓝图")
            tasks.append({"type": "lifeos_design", "duration": 7, "unit": "day"})

        if "意义" in inp.message or "使命" in inp.message:
            recs.append("生命叙事重建: 重新编写你的生命故事, 将困难重框为成长的养料")
            tasks.append({"type": "narrative_rewrite", "duration": 1, "unit": "session"})

        # Default deep reflections
        if not recs:
            recs.append("从'你希望在生命中留下什么痕迹?'开始探索")

        if agency_mode == "active":
            recs.append("你的觉察力已经很强。可以开始做身份层面的深度工作了")
        elif agency_mode == "transitional":
            recs.append("你正在从行为改变走向身份转变。让我们慢慢探索")

        result = AgentResult(
            agent_domain="life_designer",
            confidence=0.7 if stage_idx >= 4 else 0.5,
            risk_level=RiskLevel.LOW,
            findings=findings,
            recommendations=recs,
            tasks=tasks,
            metadata={"stage": stage, "agency_mode": agency_mode},
        )
        return self._enhance_with_llm(result, inp)


# ── Register V4 Agents ─────────────────────────
AGENT_CLASS_REGISTRY.update({
    "journey_companion": JourneyCompanionAgent,
    "growth_reflection": GrowthReflectionAgent,
    "coach_copilot": CoachCopilotAgent,
    "life_designer": LifeDesignerAgent,
})
