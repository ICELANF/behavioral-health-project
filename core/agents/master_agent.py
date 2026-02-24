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
import logging
import time
from typing import Any

from .base import AgentInput, AgentResult, PolicyDecision

logger = logging.getLogger(__name__)

# V007 PolicyEngine (延迟导入, 降级安全)
try:
    from core.policy_engine import PolicyEngine, Event, UserContext, ExecutionPlan
    _HAS_POLICY_ENGINE = True
except ImportError:
    _HAS_POLICY_ENGINE = False

from .specialist_agents import (
    CrisisAgent, SleepAgent, GlucoseAgent, StressAgent,
    NutritionAgent, ExerciseAgent, MentalHealthAgent,
    TCMWellnessAgent, MotivationAgent,
)
from .integrative_agents import BehaviorRxAgent, WeightAgent, CardiacRehabAgent
from .vision_agent import VisionGuideAgent
from .router import AgentRouter
from .coordinator import MultiAgentCoordinator
from .policy_gate import RuntimePolicyGate


class MasterAgent:
    """
    中枢控制器, 串联9步处理流程
    """

    def __init__(self, db_session=None):
        # 尝试从 DB 模板加载 Agent (增量叠加, 硬编码降级)
        agents_from_db = None
        if db_session:
            try:
                from core.agent_template_service import build_agents_from_templates
                agents_from_db = build_agents_from_templates(db_session)
            except Exception as e:
                logger.warning("从模板加载 Agent 失败, 使用硬编码: %s", e)

        if agents_from_db:
            self._agents: dict[str, Any] = agents_from_db
            logger.info("MasterAgent 使用 DB 模板初始化 (%d 个 Agent)", len(self._agents))
        else:
            # ── 原有硬编码, 一字不改 ──
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
                "vision": VisionGuideAgent(),
            }

        self.router = AgentRouter(self._agents)
        self.coordinator = MultiAgentCoordinator()
        self.policy_gate = RuntimePolicyGate()

        # V007 PolicyEngine 初始化 (可选, 降级安全)
        self._policy_engine = None
        self._db_session = db_session
        if db_session and _HAS_POLICY_ENGINE:
            try:
                self._policy_engine = PolicyEngine(db_session=db_session)
                self._policy_engine.rule_registry.initialize()
                logger.info("V007 PolicyEngine 初始化成功")
            except Exception as e:
                logger.warning("V007 PolicyEngine 初始化失败 (non-blocking): %s", e)

    def process(self,
                user_id: int,
                message: str,
                profile: dict = None,
                device_data: dict = None,
                context: dict = None,
                tenant_ctx: dict = None) -> dict:
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

        # Step 2.5: SafetyPipeline L1 — 输入过滤
        safety_meta = {}
        input_category = "normal"
        try:
            from core.safety.pipeline import get_safety_pipeline
            safety = get_safety_pipeline()
            input_result = safety.process_input(message)
            input_category = input_result.category
            safety_meta["input_filter"] = {
                "safe": input_result.safe,
                "category": input_result.category,
                "severity": input_result.severity,
            }

            # 危机检测 → 直接走 CrisisAgent
            if input_result.category == "crisis" and input_result.severity == "critical":
                crisis_agent = self._agents.get("crisis")
                if crisis_agent:
                    crisis_result = crisis_agent.process(agent_input)
                    elapsed_ms = int((time.time() - t0) * 1000)
                    return {
                        "response": safety.get_crisis_response(),
                        "tasks": [],
                        "risk_level": "critical",
                        "agents_used": ["crisis"],
                        "gate_decision": "escalate_coach",
                        "gate_reason": "safety_crisis_detected",
                        "coordination": {},
                        "insights": [],
                        "processing_time_ms": elapsed_ms,
                        "llm_enhanced": False,
                        "safety": safety_meta,
                    }

            # 输入被阻断 → 返回拒绝消息
            if not input_result.safe:
                elapsed_ms = int((time.time() - t0) * 1000)
                return {
                    "response": "抱歉, 您的消息包含不适当的内容, 无法处理。如需帮助请联系客服。",
                    "tasks": [],
                    "risk_level": "high",
                    "agents_used": [],
                    "gate_decision": "deny",
                    "gate_reason": "safety_input_blocked",
                    "coordination": {},
                    "insights": [],
                    "processing_time_ms": elapsed_ms,
                    "llm_enhanced": False,
                    "safety": safety_meta,
                }
        except Exception as e:
            logger.warning("SafetyPipeline L1 failed (non-blocking): %s", e)

        # Step 4: 路由 — 优先 PolicyEngine, 降级到 AgentRouter
        policy_trace_id = None
        policy_meta = {}
        if self._policy_engine:
            try:
                event = Event(
                    type='user_message',
                    content=message,
                    domain_keywords=list(context.get('domains', [])),
                    metadata={'session_id': context.get('session_id')},
                )
                policy_ctx = UserContext(
                    user_id=user_id,
                    tenant_id=(tenant_ctx or {}).get('tenant_id'),
                    current_stage=profile.get('current_stage', 'S0'),
                    risk_level=context.get('risk_level', 'normal'),
                    domain=context.get('primary_domain', ''),
                    preferred_model=context.get('preferred_model', 'deepseek-chat'),
                )
                plan = self._policy_engine.evaluate(event, policy_ctx)
                if plan.primary_agent != 'BLOCKED':
                    target_domains = [plan.primary_agent] + plan.secondary_agents
                    policy_trace_id = plan.trace_id
                    policy_meta = plan.metadata or {}
                    logger.info("PolicyEngine 决策: primary=%s, model=%s",
                                plan.primary_agent, plan.model)
                else:
                    target_domains = self.router.route(agent_input, tenant_ctx=tenant_ctx)
            except Exception as e:
                logger.warning("PolicyEngine evaluate 失败, 降级到 AgentRouter: %s", e)
                target_domains = self.router.route(agent_input, tenant_ctx=tenant_ctx)
        else:
            target_domains = self.router.route(agent_input, tenant_ctx=tenant_ctx)

        # Step 4.5: InsightGenerator (简化: 提取关键数据洞察)
        insights = self._generate_insights(profile, device_data)

        # Step 5: 调用目标Agent
        agent_results: list[AgentResult] = []
        for domain in target_domains:
            agent = self._agents.get(domain)
            if agent:
                result = agent.process(agent_input)
                agent_results.append(result)

        # Step 6: 多Agent协调 (租户上下文: 专家冲突规则覆盖)
        coordination = self.coordinator.coordinate(agent_results, tenant_ctx=tenant_ctx)

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

        # Step 7.5: SafetyPipeline L3 — 生成约束 (注入安全 system prompt)
        try:
            from core.safety.pipeline import get_safety_pipeline
            safety = get_safety_pipeline()
            # 传入 input_category 以调整约束强度
            guarded = safety.guard_generation(
                system_prompt="",
                input_category=input_category,
                agent_domain=target_domains[0] if target_domains else "",
                user_message=message,
            )
            safety_meta["generation_guard"] = {
                "constraints": guarded.constraints,
                "is_crisis": guarded.is_crisis,
            }
        except Exception as e:
            logger.warning("SafetyPipeline L3 failed (non-blocking): %s", e)

        # Step 8: 合成回复 (先尝试 LLM, 失败回退模板)
        synthesis_result = self._synthesize_response(
            stage=profile.get("current_stage", "S0"),
            recommendations=final_recs,
            insights=insights,
            gate=gate_result,
            user_message=message,
            agent_results=agent_results,
        )

        # Step 8.5: SafetyPipeline L4 — 输出过滤
        try:
            from core.safety.pipeline import get_safety_pipeline
            safety = get_safety_pipeline()
            output_result = safety.filter_output(
                synthesis_result["response"],
                input_category=input_category,
            )
            synthesis_result["response"] = output_result.text
            safety_meta["output_filter"] = {
                "grade": output_result.grade,
                "annotations": output_result.annotations,
                "disclaimer_added": output_result.disclaimer_added,
            }
        except Exception as e:
            logger.warning("SafetyPipeline L4 failed (non-blocking): %s", e)

        # Step 9: (外部完成) 写回Profile + 生成任务
        elapsed_ms = int((time.time() - t0) * 1000)

        # LLM 可观测字段
        llm_enhanced_agents = [
            r.agent_domain for r in agent_results if r.llm_enhanced
        ]
        agent_llm_latency = sum(r.llm_latency_ms for r in agent_results)
        total_llm_latency = agent_llm_latency + synthesis_result.get("latency_ms", 0)

        return {
            "response": synthesis_result["response"],
            "tasks": final_tasks,
            "risk_level": coordination.get("risk_level", "low"),
            "agents_used": target_domains,
            "gate_decision": gate_result.decision.value,
            "gate_reason": gate_result.reason,
            "coordination": coordination,
            "insights": insights,
            "processing_time_ms": elapsed_ms,
            "llm_enhanced": bool(llm_enhanced_agents) or synthesis_result.get("llm_used", False),
            "llm_enhanced_agents": llm_enhanced_agents,
            "llm_synthesis_used": synthesis_result.get("llm_used", False),
            "llm_total_latency_ms": total_llm_latency,
            "safety": safety_meta,
            "policy_trace_id": policy_trace_id,
            "policy_metadata": policy_meta,
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
                             insights: list[str], gate,
                             user_message: str = "",
                             agent_results: list = None) -> dict:
        """
        合成教练风格的回复。
        先尝试 LLM 合成 → 失败回退模板。
        Returns: {"response": str, "llm_used": bool, "latency_ms": int}
        """
        # 尝试 LLM 合成 (通过 UnifiedLLMClient: 云优先 → 本地降级)
        if user_message and agent_results:
            try:
                from core.llm_client import get_llm_client
                from .prompts import SYNTHESIS_SYSTEM_PROMPT, build_synthesis_prompt

                client = get_llm_client()
                if client.is_available():
                    agent_summaries = []
                    for r in agent_results:
                        agent_summaries.append({
                            "domain": r.agent_domain,
                            "recommendations": r.recommendations,
                        })
                    user_prompt = build_synthesis_prompt(
                        user_message=user_message,
                        stage=stage,
                        gate_decision=gate.decision.value,
                        insights=insights,
                        agent_summaries=agent_summaries,
                    )
                    resp = client.chat(SYNTHESIS_SYSTEM_PROMPT, user_prompt,
                                       timeout=45.0)
                    if resp.success and resp.content:
                        return {
                            "response": resp.content,
                            "llm_used": True,
                            "latency_ms": resp.latency_ms,
                            "llm_model": resp.model,
                            "llm_provider": resp.provider,
                        }
            except Exception as e:
                logger.warning("LLM synthesis failed, falling back to template: %s", e)

        # 模板回退
        return {
            "response": self._template_synthesize(stage, recommendations, insights),
            "llm_used": False,
            "latency_ms": 0,
        }

    def _template_synthesize(self, stage: str, recommendations: list[str],
                             insights: list[str]) -> str:
        """原始模板合成 (降级方案)"""
        if stage in ("S0", "S1"):
            opener = "我理解你现在的状态。"
        elif stage in ("S2", "S3"):
            opener = "看起来你已经在思考改变了，"
        else:
            opener = "继续保持！"

        parts = [opener]
        if insights:
            parts.append("根据你的数据: " + "; ".join(insights[:3]) + "。")
        if recommendations:
            parts.append("建议: " + recommendations[0])
            if len(recommendations) > 1:
                parts.append(f"另外还有{len(recommendations) - 1}条建议可以参考。")

        return " ".join(parts)
