"""
9个专科Agent
来源: §9.1.1 + §9.2 + §11
"""
from __future__ import annotations
from .base import (
    BaseAgent, AgentDomain, AgentInput, AgentResult,
    RiskLevel, AGENT_BASE_WEIGHTS,
)


class CrisisAgent(BaseAgent):
    """危机干预Agent — 优先级0(最高), 检测自杀/自残等危急信号"""
    domain = AgentDomain.CRISIS
    display_name = "危机干预"
    keywords = ["自杀", "自残", "不想活", "结束生命", "活着没意思",
                "去死", "跳楼", "割腕", "安眠药", "遗书"]
    priority = 0
    base_weight = 1.0
    enable_llm = False  # 危机干预必须确定性，不走 LLM

    CRITICAL_KW = ["自杀", "自残", "不想活", "结束生命", "去死", "跳楼", "割腕", "遗书"]
    WARNING_KW = ["活着没意思", "太痛苦了", "撑不下去", "崩溃", "绝望"]

    def process(self, inp: AgentInput) -> AgentResult:
        msg = inp.message
        # 危急关键词
        for kw in self.CRITICAL_KW:
            if kw in msg:
                return AgentResult(
                    agent_domain=self.domain.value,
                    confidence=1.0,
                    risk_level=RiskLevel.CRITICAL,
                    findings=[f"检测到危急关键词: {kw}"],
                    recommendations=["立即升级至人工专业支持"],
                    metadata={"risk_level": "critical", "keyword": kw,
                              "action": "escalate_immediately"},
                )
        # 警告关键词
        for kw in self.WARNING_KW:
            if kw in msg:
                return AgentResult(
                    agent_domain=self.domain.value,
                    confidence=0.9,
                    risk_level=RiskLevel.HIGH,
                    findings=[f"检测到警告关键词: {kw}"],
                    recommendations=["提供共情支持", "评估是否需要升级"],
                    metadata={"risk_level": "warning", "keyword": kw,
                              "action": "soft_support_then_assess"},
                )
        return AgentResult(agent_domain=self.domain.value, confidence=0.95,
                           risk_level=RiskLevel.LOW,
                           metadata={"risk_level": "safe"})


class SleepAgent(BaseAgent):
    """睡眠专家Agent"""
    domain = AgentDomain.SLEEP
    display_name = "睡眠专家"
    keywords = ["睡眠", "失眠", "早醒", "熬夜", "睡不着", "嗜睡", "打鼾", "午睡"]
    data_fields = ["sleep"]
    priority = 2
    base_weight = 0.85

    def process(self, inp: AgentInput) -> AgentResult:
        findings, recs, tasks = [], [], []
        sleep = inp.device_data.get("sleep_hours")
        if sleep is not None:
            if sleep < 6:
                findings.append(f"睡眠不足: {sleep}小时 (建议≥7h)")
                recs.append("制定睡前90分钟断屏计划")
                tasks.append({"type": "sleep_hygiene", "duration": 7, "unit": "day"})
            elif sleep > 9:
                findings.append(f"睡眠过长: {sleep}小时，可能与情绪低落相关")
                recs.append("排查抑郁倾向, 建议规律起床时间")
        if any(kw in inp.message for kw in ["失眠", "睡不着"]):
            recs.append("认知行为疗法(CBT-I): 睡眠限制+刺激控制")
            tasks.append({"type": "sleep_diary", "duration": 14, "unit": "day"})
        result = AgentResult(
            agent_domain=self.domain.value,
            confidence=0.8 if findings else 0.5,
            risk_level=RiskLevel.MODERATE if findings else RiskLevel.LOW,
            findings=findings, recommendations=recs, tasks=tasks,
        )
        return self._enhance_with_llm(result, inp)


class GlucoseAgent(BaseAgent):
    """血糖管理Agent"""
    domain = AgentDomain.GLUCOSE
    display_name = "血糖管理"
    keywords = ["血糖", "糖尿病", "胰岛素", "低血糖", "高血糖", "糖化", "控糖"]
    data_fields = ["cgm"]
    priority = 1
    base_weight = 0.9

    def process(self, inp: AgentInput) -> AgentResult:
        findings, recs, tasks = [], [], []
        cgm = inp.device_data.get("cgm_value")
        if cgm is not None:
            if cgm > 10.0:
                findings.append(f"血糖偏高: {cgm} mmol/L")
                recs.append("餐后30分钟轻度活动, 下一餐减少精制碳水")
                tasks.append({"type": "post_meal_walk", "duration": 15, "unit": "min"})
            elif cgm < 3.9:
                findings.append(f"低血糖警告: {cgm} mmol/L")
                recs.append("立即补充15g速效碳水, 15分钟后复测")
        result = AgentResult(
            agent_domain=self.domain.value,
            confidence=0.85 if findings else 0.5,
            risk_level=RiskLevel.HIGH if cgm and cgm < 3.9 else RiskLevel.LOW,
            findings=findings, recommendations=recs, tasks=tasks,
        )
        return self._enhance_with_llm(result, inp)


class StressAgent(BaseAgent):
    """压力管理Agent"""
    domain = AgentDomain.STRESS
    display_name = "压力管理"
    keywords = ["压力", "焦虑", "紧张", "烦躁", "崩溃", "喘不过气"]
    data_fields = ["hrv"]
    priority = 2
    base_weight = 0.85

    def process(self, inp: AgentInput) -> AgentResult:
        findings, recs, tasks = [], [], []
        hrv_sdnn = inp.device_data.get("hrv_sdnn")
        if hrv_sdnn is not None and hrv_sdnn < 30:
            findings.append(f"HRV偏低(SDNN={hrv_sdnn}ms), 提示交感神经过度激活")
            recs.append("4-7-8呼吸法 + 5分钟正念冥想")
            tasks.append({"type": "breathing_exercise", "times_per_day": 3})
        if any(kw in inp.message for kw in ["压力", "焦虑", "紧张"]):
            recs.append("识别压力源, 建立压力应对清单")
        result = AgentResult(
            agent_domain=self.domain.value,
            confidence=0.8 if findings else 0.5,
            risk_level=RiskLevel.MODERATE if findings else RiskLevel.LOW,
            findings=findings, recommendations=recs, tasks=tasks,
        )
        return self._enhance_with_llm(result, inp)


class NutritionAgent(BaseAgent):
    """营养指导Agent"""
    domain = AgentDomain.NUTRITION
    display_name = "营养指导"
    keywords = ["饮食", "营养", "减肥", "热量", "碳水", "蛋白质", "吃什么",
                "食谱", "代餐", "节食"]
    priority = 3
    base_weight = 0.8

    def process(self, inp: AgentInput) -> AgentResult:
        findings, recs = [], []
        stage = inp.profile.get("current_stage", "S0")
        if stage in ("S0", "S1"):
            recs.append("从饮食记录开始, 不做限制, 先建立觉察")
        elif stage in ("S2", "S3"):
            recs.append("控碳先行: 主食减1/3, 蔬菜先吃, 蛋白质加量")
        else:
            recs.append("精细化营养方案: 根据CGM数据个性化调整")
        result = AgentResult(
            agent_domain=self.domain.value,
            confidence=0.7,
            risk_level=RiskLevel.LOW,
            findings=findings, recommendations=recs,
        )
        return self._enhance_with_llm(result, inp)


class ExerciseAgent(BaseAgent):
    """运动指导Agent"""
    domain = AgentDomain.EXERCISE
    display_name = "运动指导"
    keywords = ["运动", "健身", "步数", "跑步", "散步", "力量训练", "瑜伽"]
    data_fields = ["activity"]
    priority = 3
    base_weight = 0.8

    def process(self, inp: AgentInput) -> AgentResult:
        findings, recs, tasks = [], [], []
        steps = inp.device_data.get("steps")
        if steps is not None and steps < 5000:
            findings.append(f"日步数不足: {steps}步 (建议≥7000)")
            recs.append("每小时起身活动5分钟, 累积增加步数")
            tasks.append({"type": "hourly_walk", "duration": 5, "unit": "min"})
        result = AgentResult(
            agent_domain=self.domain.value,
            confidence=0.7 if findings else 0.5,
            risk_level=RiskLevel.LOW,
            findings=findings, recommendations=recs, tasks=tasks,
        )
        return self._enhance_with_llm(result, inp)


class MentalHealthAgent(BaseAgent):
    """心理咨询Agent"""
    domain = AgentDomain.MENTAL
    display_name = "心理咨询"
    keywords = ["情绪", "抑郁", "心情", "难过", "伤心", "郁闷", "无助"]
    priority = 2
    base_weight = 0.85

    def process(self, inp: AgentInput) -> AgentResult:
        findings, recs = [], []
        if any(kw in inp.message for kw in ["抑郁", "无助", "绝望"]):
            findings.append("检测到抑郁相关表达")
            recs.append("建议PHQ-9筛查 + 寻求专业心理支持")
        elif any(kw in inp.message for kw in ["情绪", "心情", "郁闷"]):
            recs.append("ABC情绪日记: 事件-信念-情绪, 每日记录")
        result = AgentResult(
            agent_domain=self.domain.value,
            confidence=0.75 if findings else 0.5,
            risk_level=RiskLevel.MODERATE if findings else RiskLevel.LOW,
            findings=findings, recommendations=recs,
        )
        return self._enhance_with_llm(result, inp)


class TCMWellnessAgent(BaseAgent):
    """中医养生Agent"""
    domain = AgentDomain.TCM
    display_name = "中医养生"
    keywords = ["中医", "体质", "穴位", "气血", "经络", "养生", "上火", "湿气"]
    priority = 4
    base_weight = 0.75

    def process(self, inp: AgentInput) -> AgentResult:
        recs = ["结合体质辨识, 提供个性化中医养生建议"]
        result = AgentResult(
            agent_domain=self.domain.value,
            confidence=0.6,
            risk_level=RiskLevel.LOW,
            recommendations=recs,
        )
        return self._enhance_with_llm(result, inp)


class MotivationAgent(BaseAgent):
    """动机管理Agent"""
    domain = AgentDomain.MOTIVATION
    display_name = "动机管理"
    keywords = ["动力", "坚持", "放弃", "没意义", "为什么", "值不值"]
    priority = 3
    base_weight = 0.8

    def process(self, inp: AgentInput) -> AgentResult:
        findings, recs = [], []
        stage = inp.profile.get("current_stage", "S0")
        if stage in ("S0", "S1"):
            recs.append("探索改变的个人意义, 不施压")
        elif stage in ("S2", "S3"):
            recs.append("动机访谈: 探索矛盾, '改变对你意味着什么?'")
        elif stage in ("S4", "S5", "S6"):
            recs.append("身份强化: '你已经是一个注重健康的人了'")
        result = AgentResult(
            agent_domain=self.domain.value,
            confidence=0.7,
            risk_level=RiskLevel.LOW,
            findings=findings, recommendations=recs,
        )
        return self._enhance_with_llm(result, inp)


# ── 注册到 AGENT_CLASS_REGISTRY ──
from .base import AGENT_CLASS_REGISTRY

AGENT_CLASS_REGISTRY.update({
    "crisis": CrisisAgent,
    "sleep": SleepAgent,
    "glucose": GlucoseAgent,
    "stress": StressAgent,
    "nutrition": NutritionAgent,
    "exercise": ExerciseAgent,
    "mental": MentalHealthAgent,
    "tcm": TCMWellnessAgent,
    "motivation": MotivationAgent,
})
