"""
MasterAgent — 九步处理流程编排
来源: §8 MasterAgent 九步处理流程

Step 1-2: 用户输入 → Orchestrator接收请求
Step 3:   更新 UserMasterProfile
Step 4:   AgentRouter 判别问题类型与风险优先级
Step 4.5: InsightGenerator 生成数据洞察
Step 5:   调用 1-2个专业Agent
Step 6:   MultiAgentCoordinator 统一上下文 + 整合各Agent结果
Step 7:   InterventionPlanner 生成个性化行为干预路径
Step 8:   ResponseSynthesizer 统一教练风格 + 输出给用户
Step 9:   写回 UserMasterProfile + 生成今日任务/追踪点
"""
from __future__ import annotations
import time
from typing import Any

from .base import AgentInput, AgentResult, PolicyDecision
from .specialist_agents import (
    CrisisAgent, SleepAgent, GlucoseAgent, StressAgent,
    NutritionAgent, ExerciseAgent, MentalHealthAgent,
    TCMWellnessAgent, MotivationAgent,
)
from .integrative_agents import BehaviorRxAgent, WeightAgent, CardiacRehabAgent
from .router import AgentRouter
from .coordinator import MultiAgentCoordinator
from .policy_gate import RuntimePolicyGate


class MasterAgent:
    """
    中枢控制器, 串联9步处理流程
    """

    def __init__(self):
        # 初始化所有Agent
        self._agents: dict[str, Any] = {
            "crisis": CrisisAgent(),
            "sleep": SleepAgent(),
            "glucose": GlucoseAgent(),
            "stress": StressAgent(),
            "nutrition": NutritionAgent(),
            "exercise": ExerciseAgent(),
            "mental": MentalHealthAgent(),
            "tcm": TCMWellnessAgent(),
            "motivation": MotivationAgent(),
            "behavior_rx": BehaviorRxAgent(),
            "weight": WeightAgent(),
            "cardiac_rehab": CardiacRehabAgent(),
        }
        self.router = AgentRouter(self._agents)
        self.coordinator = MultiAgentCoordinator()
        self.policy_gate = RuntimePolicyGate()

    def process(self,
                user_id: int,
                message: str,
                profile: dict = None,
                device_data: dict = None,
                context: dict = None) -> dict:
        """
        主处理入口 — 9步流水线

        Returns:
            {
                "response": str,           # 给用户的回复
                "tasks": list[dict],       # 今日任务
                "risk_level": str,         # 综合风险等级
                "agents_used": list[str],  # 激活的Agent
                "gate_decision": str,      # 策略闸门决策
                "coordination": dict,      # 协调详情
                "processing_time_ms": int,
            }
        """
        t0 = time.time()
        profile = profile or {}
        device_data = device_data or {}
        context = context or {}

        # Step 1-2: 构建AgentInput
        agent_input = AgentInput(
            user_id=user_id,
            message=message,
            intent=context.get("intent", ""),
            profile=profile,
            device_data=device_data,
            context=context,
        )

        # Step 3: (外部完成) 更新 UserMasterProfile — 此处仅读取

        # Step 4: 路由
        target_domains = self.router.route(agent_input)

        # Step 4.5: InsightGenerator (简化: 提取关键数据洞察)
        insights = self._generate_insights(profile, device_data)

        # Step 5: 调用目标Agent
        agent_results: list[AgentResult] = []
        for domain in target_domains:
            agent = self._agents.get(domain)
            if agent:
                result = agent.process(agent_input)
                agent_results.append(result)

        # Step 6: 多Agent协调
        coordination = self.coordinator.coordinate(agent_results)

        # Step 7: 策略闸门 + 干预规划
        gate_result = self.policy_gate.evaluate(
            current_stage=profile.get("current_stage", "S0"),
            stability=profile.get("stability", "stable"),
            intervention_strength=self._assess_strength(coordination),
            dropout_risk=profile.get("dropout_risk", False),
            relapse_risk=profile.get("relapse_risk", False),
            risk_level=coordination.get("risk_level", "low"),
        )

        # 根据闸门决策过滤tasks和recommendations
        final_tasks = coordination.get("tasks", [])
        final_recs = coordination.get("recommendations", [])

        if gate_result.decision == PolicyDecision.DELAY:
            final_tasks = []
            final_recs = ["当前状态不稳定, 暂不下发新任务, 先稳定情绪"]
        elif gate_result.decision == PolicyDecision.ALLOW_SOFT_SUPPORT:
            final_tasks = [t for t in final_tasks
                           if t.get("difficulty") in ("minimal", "easy", None)]
            final_recs = [r for r in final_recs if "挑战" not in r and "必须" not in r]

        # Step 8: 合成回复
        response = self._synthesize_response(
            stage=profile.get("current_stage", "S0"),
            recommendations=final_recs,
            insights=insights,
            gate=gate_result,
        )

        # Step 9: (外部完成) 写回Profile + 生成任务
        elapsed_ms = int((time.time() - t0) * 1000)

        return {
            "response": response,
            "tasks": final_tasks,
            "risk_level": coordination.get("risk_level", "low"),
            "agents_used": target_domains,
            "gate_decision": gate_result.decision.value,
            "gate_reason": gate_result.reason,
            "coordination": coordination,
            "insights": insights,
            "processing_time_ms": elapsed_ms,
        }

    # ── 内部方法 ──

    def _generate_insights(self, profile: dict, device: dict) -> list[str]:
        insights = []
        cgm = device.get("cgm_value")
        if cgm and cgm > 10:
            insights.append(f"血糖偏高({cgm}mmol/L)")
        hrv = device.get("hrv_sdnn")
        if hrv and hrv < 30:
            insights.append(f"HRV偏低(SDNN={hrv}ms), 压力较大")
        sleep = device.get("sleep_hours")
        if sleep and sleep < 6:
            insights.append(f"睡眠不足({sleep}h)")
        steps = device.get("steps")
        if steps and steps < 5000:
            insights.append(f"活动量不足({steps}步)")
        return insights

    def _assess_strength(self, coordination: dict) -> str:
        tasks = coordination.get("tasks", [])
        if any(t.get("difficulty") in ("hard", "challenging") for t in tasks):
            return "challenge"
        if any(t.get("difficulty") in ("moderate",) for t in tasks):
            return "normal"
        return "soft"

    def _synthesize_response(self, stage: str, recommendations: list[str],
                             insights: list[str], gate) -> str:
        """根据阶段 + 闸门决策合成教练风格的回复"""
        # 交互模式 (§5.4)
        if stage in ("S0", "S1"):
            tone = "共情模式"
            opener = "我理解你现在的状态。"
        elif stage in ("S2", "S3"):
            tone = "引导模式"
            opener = "看起来你已经在思考改变了，"
        else:
            tone = "执行模式"
            opener = "继续保持！"

        parts = [opener]
        if insights:
            parts.append("根据你的数据: " + "; ".join(insights[:3]) + "。")
        if recommendations:
            parts.append("建议: " + recommendations[0])
            if len(recommendations) > 1:
                parts.append(f"另外还有{len(recommendations) - 1}条建议可以参考。")

        return " ".join(parts)
