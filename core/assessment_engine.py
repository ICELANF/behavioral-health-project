"""
L2 评估分流引擎
Assessment and Routing Engine

行为健康平台的"系统大脑"，负责：
1. Trigger 识别
2. 风险评估
3. Agent 路由决策
4. 干预包匹配
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger

from core.trigger_engine import get_trigger_engine, Trigger, TriggerSeverity
from core.multimodal_client import get_multimodal_client
from core.models import RiskLevel


# ============================================
# 风险评估结果
# ============================================


class AgentType(Enum):
    """Agent 类型"""
    CRISIS = "CrisisAgent"
    GLUCOSE = "GlucoseAgent"
    METABOLIC = "MetabolicAgent"
    SLEEP = "SleepAgent"
    STRESS = "StressAgent"
    MENTAL_HEALTH = "MentalHealthAgent"
    MOTIVATION = "MotivationAgent"
    NUTRITION = "NutritionAgent"
    EXERCISE = "ExerciseAgent"
    COACHING = "CoachingAgent"
    TCM = "TCMAgent"


@dataclass
class RiskAssessment:
    """风险评估结果"""
    risk_level: RiskLevel
    risk_score: float  # 0-100
    contributing_triggers: List[Trigger]
    severity_distribution: Dict[str, int]  # {critical: 1, high: 2, ...}
    primary_concern: str  # 主要关注点
    urgency: str  # immediate/high/moderate/low
    reasoning: str  # 评估理由

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_level": self.risk_level.value,
            "risk_score": self.risk_score,
            "contributing_triggers": [t.to_dict() for t in self.contributing_triggers],
            "severity_distribution": self.severity_distribution,
            "primary_concern": self.primary_concern,
            "urgency": self.urgency,
            "reasoning": self.reasoning
        }


@dataclass
class RoutingDecision:
    """路由决策结果"""
    primary_agent: AgentType
    secondary_agents: List[AgentType]
    priority: int  # 1-4
    response_time: str  # 建议响应时间
    routing_reasoning: str  # 路由理由
    recommended_actions: List[str]  # 推荐行动

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_agent": self.primary_agent.value,
            "secondary_agents": [a.value for a in self.secondary_agents],
            "priority": self.priority,
            "response_time": self.response_time,
            "routing_reasoning": self.routing_reasoning,
            "recommended_actions": self.recommended_actions
        }


@dataclass
class AssessmentResult:
    """完整评估结果"""
    user_id: int
    assessment_id: str
    triggers: List[Trigger]
    risk_assessment: RiskAssessment
    routing_decision: RoutingDecision
    timestamp: str
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "assessment_id": self.assessment_id,
            "triggers": [t.to_dict() for t in self.triggers],
            "risk_assessment": self.risk_assessment.to_dict(),
            "routing_decision": self.routing_decision.to_dict(),
            "timestamp": self.timestamp,
            "context": self.context
        }


# ============================================
# L2 评估引擎
# ============================================

class AssessmentEngine:
    """
    L2 评估分流引擎

    四大模块：
    1. Trigger 识别器
    2. 风险评估器
    3. 路由决策器
    4. 干预匹配器
    """

    def __init__(self):
        self.trigger_engine = get_trigger_engine()
        self.multimodal_client = get_multimodal_client()
        logger.info("L2 评估引擎初始化完成")

    # ============================================
    # 主入口：完整评估流程
    # ============================================

    async def assess(
        self,
        user_id: int,
        text_content: Optional[str] = None,
        hrv_values: Optional[List[float]] = None,
        glucose_values: Optional[List[float]] = None,
        user_profile: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> AssessmentResult:
        """
        执行完整评估流程

        Args:
            user_id: 用户ID
            text_content: 用户消息
            hrv_values: HRV数据
            glucose_values: 血糖数据
            user_profile: 用户画像
            context: 上下文信息

        Returns:
            完整评估结果
        """
        from datetime import datetime
        import uuid

        assessment_id = f"ASS-{uuid.uuid4().hex[:8]}"
        logger.info(f"开始评估 {assessment_id} for 用户 {user_id}")

        # 步骤1: Trigger 识别
        triggers = await self.trigger_engine.recognize_triggers(
            user_id=user_id,
            text_content=text_content,
            hrv_values=hrv_values,
            glucose_values=glucose_values,
            user_profile=user_profile
        )
        logger.info(f"识别到 {len(triggers)} 个 Triggers")

        # 步骤2: 风险评估
        risk_assessment = self.assess_risk(triggers, user_profile)
        logger.info(f"风险等级: {risk_assessment.risk_level.value}")

        # 步骤3: 路由决策
        routing_decision = self.route_agents(
            triggers, risk_assessment, user_profile
        )
        logger.info(f"主Agent: {routing_decision.primary_agent.value}")

        # 构建结果
        result = AssessmentResult(
            user_id=user_id,
            assessment_id=assessment_id,
            triggers=triggers,
            risk_assessment=risk_assessment,
            routing_decision=routing_decision,
            timestamp=datetime.now().isoformat(),
            context=context or {}
        )

        logger.info(f"评估完成 {assessment_id}")
        return result

    # ============================================
    # 模块2: 风险评估
    # ============================================

    def assess_risk(
        self,
        triggers: List[Trigger],
        user_profile: Optional[Dict] = None
    ) -> RiskAssessment:
        """
        风险评估

        基于 Triggers 的数量、严重程度、组合模式进行风险评分
        """
        if not triggers:
            return RiskAssessment(
                risk_level=RiskLevel.R0,
                risk_score=0,
                contributing_triggers=[],
                severity_distribution={},
                primary_concern="无风险",
                urgency="low",
                reasoning="未检测到风险信号"
            )

        # 统计严重程度分布
        severity_count = {
            "critical": 0,
            "high": 0,
            "moderate": 0,
            "low": 0
        }

        for trigger in triggers:
            severity_count[trigger.severity.value] += 1

        # 计算风险分数 (0-100)
        risk_score = 0.0
        risk_score += severity_count["critical"] * 40  # 危急级别权重最高
        risk_score += severity_count["high"] * 20
        risk_score += severity_count["moderate"] * 10
        risk_score += severity_count["low"] * 5

        # 聚类加成：多个相关 Trigger 同时出现增加风险
        if self._check_cluster_pattern(triggers, "metabolic_syndrome"):
            risk_score += 15
        if self._check_cluster_pattern(triggers, "burnout"):
            risk_score += 15
        if self._check_cluster_pattern(triggers, "depression"):
            risk_score += 20

        # 限制在0-100范围
        risk_score = min(risk_score, 100)

        # 确定风险等级
        if severity_count["critical"] > 0:
            risk_level = RiskLevel.R4
            urgency = "immediate"
        elif severity_count["high"] >= 2 or risk_score >= 60:
            risk_level = RiskLevel.R3
            urgency = "high"
        elif severity_count["high"] >= 1 or risk_score >= 30:
            risk_level = RiskLevel.R2
            urgency = "moderate"
        elif severity_count["moderate"] >= 1:
            risk_level = RiskLevel.R1
            urgency = "low"
        else:
            risk_level = RiskLevel.R0
            urgency = "low"

        # 确定主要关注点
        if severity_count["critical"] > 0:
            critical_triggers = [t for t in triggers if t.severity.value == "critical"]
            primary_concern = critical_triggers[0].name
        elif severity_count["high"] > 0:
            high_triggers = [t for t in triggers if t.severity.value == "high"]
            primary_concern = high_triggers[0].name
        else:
            primary_concern = triggers[0].name

        # 生成评估理由
        reasoning = self._generate_risk_reasoning(
            severity_count, risk_score, triggers
        )

        return RiskAssessment(
            risk_level=risk_level,
            risk_score=risk_score,
            contributing_triggers=triggers,
            severity_distribution=severity_count,
            primary_concern=primary_concern,
            urgency=urgency,
            reasoning=reasoning
        )

    # ============================================
    # 模块3: 路由决策
    # ============================================

    def route_agents(
        self,
        triggers: List[Trigger],
        risk_assessment: RiskAssessment,
        user_profile: Optional[Dict] = None
    ) -> RoutingDecision:
        """
        Agent 路由决策

        基于 Triggers 和风险等级，决定调用哪些 Agent
        """
        if not triggers:
            # 无 Trigger，默认路由到 CoachingAgent
            return RoutingDecision(
                primary_agent=AgentType.COACHING,
                secondary_agents=[],
                priority=4,
                response_time="48小时内",
                routing_reasoning="常规咨询",
                recommended_actions=["提供一般性健康建议"]
            )

        # 初始化
        agent_scores: Dict[AgentType, float] = {agent: 0.0 for agent in AgentType}

        # 遍历 Triggers，累加 Agent 分数
        for trigger in triggers:
            # 获取路由的 Agents
            routed_agents = self._get_routed_agents_for_trigger(trigger.tag_id)

            # 根据严重程度赋予权重
            if trigger.severity.value == "critical":
                weight = 10.0
            elif trigger.severity.value == "high":
                weight = 5.0
            elif trigger.severity.value == "moderate":
                weight = 2.0
            else:
                weight = 1.0

            for agent_name in routed_agents:
                try:
                    agent_type = AgentType(agent_name)
                    agent_scores[agent_type] += weight
                except ValueError:
                    continue

        # 排序选出 Top Agents
        sorted_agents = sorted(
            agent_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # 选择主Agent和次要Agents
        primary_agent = sorted_agents[0][0] if sorted_agents[0][1] > 0 else AgentType.COACHING
        secondary_agents = [
            agent for agent, score in sorted_agents[1:4] if score > 0
        ]

        # 确定优先级和响应时间
        if risk_assessment.risk_level == RiskLevel.R4:
            priority = 1
            response_time = "立即"
        elif risk_assessment.risk_level == RiskLevel.R3:
            priority = 1
            response_time = "1小时内"
        elif risk_assessment.risk_level == RiskLevel.R2:
            priority = 2
            response_time = "24小时内"
        else:
            priority = 3
            response_time = "48小时内"

        # 生成路由理由
        routing_reasoning = self._generate_routing_reasoning(
            triggers, primary_agent, risk_assessment
        )

        # 推荐行动
        recommended_actions = self._generate_recommended_actions(
            triggers, primary_agent
        )

        return RoutingDecision(
            primary_agent=primary_agent,
            secondary_agents=secondary_agents,
            priority=priority,
            response_time=response_time,
            routing_reasoning=routing_reasoning,
            recommended_actions=recommended_actions
        )

    # ============================================
    # 辅助方法
    # ============================================

    def _check_cluster_pattern(
        self,
        triggers: List[Trigger],
        cluster_type: str
    ) -> bool:
        """检查是否匹配聚类模式"""
        trigger_ids = {t.tag_id for t in triggers}

        # 代谢综合征聚类
        if cluster_type == "metabolic_syndrome":
            required = {"high_glucose", "glucose_spike", "sedentary", "high_gi_meal"}
            return len(trigger_ids & required) >= 2

        # 职业倦怠聚类
        elif cluster_type == "burnout":
            required = {"stress_overload", "poor_sleep", "low_motivation", "work_stress"}
            return len(trigger_ids & required) >= 2

        # 抑郁风险聚类
        elif cluster_type == "depression":
            required = {"depression_sign", "negative_sentiment", "low_motivation", "sedentary"}
            return len(trigger_ids & required) >= 2

        return False

    def _get_routed_agents_for_trigger(self, trigger_id: str) -> List[str]:
        """获取 Trigger 对应的路由 Agents"""
        # 从 Trigger 定义中获取
        trigger_def = self.trigger_engine.get_trigger_definition(trigger_id)
        if trigger_def and "routed_agents" in trigger_def:
            return trigger_def["routed_agents"]

        # 默认映射
        mapping = {
            "high_glucose": ["GlucoseAgent", "MetabolicAgent"],
            "low_glucose": ["CrisisAgent", "GlucoseAgent"],
            "glucose_spike": ["GlucoseAgent", "NutritionAgent"],
            "low_hrv": ["StressAgent", "SleepAgent"],
            "high_stress_hrv": ["StressAgent", "MentalHealthAgent"],
            "high_anxiety": ["MentalHealthAgent", "StressAgent"],
            "depression_sign": ["MentalHealthAgent", "CrisisAgent"],
            "stress_overload": ["StressAgent", "MentalHealthAgent"],
            "crisis_keyword": ["CrisisAgent"],
            "task_failure": ["CoachingAgent", "MotivationAgent"],
            "low_adherence": ["CoachingAgent", "MotivationAgent"],
            "poor_sleep": ["SleepAgent"],
            "work_stress": ["StressAgent", "CoachingAgent"],
            "low_motivation": ["MotivationAgent", "CoachingAgent"],
            "negative_sentiment": ["MentalHealthAgent", "MotivationAgent"],
            "sedentary": ["ExerciseAgent"],
            "high_gi_meal": ["NutritionAgent", "GlucoseAgent"],
        }
        return mapping.get(trigger_id, ["CoachingAgent"])

    def _generate_risk_reasoning(
        self,
        severity_count: Dict[str, int],
        risk_score: float,
        triggers: List[Trigger]
    ) -> str:
        """生成风险评估理由"""
        parts = []

        if severity_count["critical"] > 0:
            parts.append(f"检测到 {severity_count['critical']} 个危急级别信号")

        if severity_count["high"] > 0:
            parts.append(f"{severity_count['high']} 个高风险信号")

        if severity_count["moderate"] > 0:
            parts.append(f"{severity_count['moderate']} 个中等风险信号")

        parts.append(f"综合风险分数 {risk_score:.1f}/100")

        return "，".join(parts)

    def _generate_routing_reasoning(
        self,
        triggers: List[Trigger],
        primary_agent: AgentType,
        risk_assessment: RiskAssessment
    ) -> str:
        """生成路由理由"""
        return f"基于 {risk_assessment.primary_concern} 主要问题，路由到 {primary_agent.value} 进行专业评估"

    def _generate_recommended_actions(
        self,
        triggers: List[Trigger],
        primary_agent: AgentType
    ) -> List[str]:
        """生成推荐行动"""
        actions = []

        # 基于主Agent生成行动
        if primary_agent == AgentType.CRISIS:
            actions.append("立即联系用户")
            actions.append("启动危机干预协议")
        elif primary_agent == AgentType.GLUCOSE:
            actions.append("查看血糖趋势图")
            actions.append("评估饮食和运动记录")
        elif primary_agent == AgentType.MENTAL_HEALTH:
            actions.append("进行心理评估")
            actions.append("提供情绪支持")
        elif primary_agent == AgentType.STRESS:
            actions.append("压力源评估")
            actions.append("压力管理技巧")
        else:
            actions.append("了解用户需求")
            actions.append("制定个性化方案")

        return actions


# ============================================
# 全局单例
# ============================================

_assessment_engine: Optional[AssessmentEngine] = None


def get_assessment_engine() -> AssessmentEngine:
    """获取评估引擎单例"""
    global _assessment_engine
    if _assessment_engine is None:
        _assessment_engine = AssessmentEngine()
    return _assessment_engine
