"""
MasterAgent — 唯一版本 (手术后)

合并来源:
  ✓ V6 core/agents/master_agent.py   → 9步流水线 (process)
  ✓ Unified master_agent_unified.py  → 快捷方法 (chat/process_json/route_agents...)
  ✓ V0 master_agent_v0.py           → 高级功能委托 (action_plan/daily_briefing)

变更:
  - __init__ 不再硬编码 Agent, 全部从 Registry 获取
  - AgentRouter(registry) 替代 AgentRouter(dict)
  - V0 高级功能委托到独立模块 (core.intervention / core.assessment)
  - 保留所有公开 API 签名, 向后兼容
"""
from __future__ import annotations
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from .base import AgentInput, AgentResult, PolicyDecision
from .registry import AgentRegistry
from .router import AgentRouter
from .coordinator import MultiAgentCoordinator
from .policy_gate import RuntimePolicyGate

logger = logging.getLogger(__name__)

# PolicyEngine (延迟导入, 降级安全)
try:
    from core.policy_engine import PolicyEngine, Event, UserContext, ExecutionPlan
    _HAS_POLICY_ENGINE = True
except ImportError:
    _HAS_POLICY_ENGINE = False


class MasterAgent:
    """
    中枢控制器 — 唯一版本

    初始化:
        registry = create_registry(db_session)
        agent = MasterAgent(registry=registry, db_session=db)

    核心 API:
        process()                → 9步流水线 (V6 架构)
        chat()                   → 快捷对话 (Unified)
        process_json()           → JSON 入口 (Unified)
        create_action_plan()     → 干预计划 (V0→独立模块)
        generate_daily_briefing()→ 每日简报 (V0→独立模块)
    """

    def __init__(self, registry: AgentRegistry = None, db_session=None,
                 # 向后兼容: 无 registry 时走硬编码
                 **kwargs):
        self._registry = registry
        self._db_session = db_session

        if registry:
            # ✅ 手术后路径: 从 Registry 获取
            self._agents = registry.list_agents()
            self.router = AgentRouter(registry)
        else:
            # ⚠️ 向后兼容: 硬编码 (过渡期, 2周后删除)
            logger.warning("MasterAgent 无 registry, 使用硬编码降级路径")
            self._agents = self._build_hardcoded_agents(db_session)
            from .router import AgentRouter as _LegacyRouter
            # Legacy router 需要 registry-like wrapper, 直接用旧路径
            self.router = self._build_legacy_router()

        self.coordinator = MultiAgentCoordinator()
        self.policy_gate = RuntimePolicyGate()

        # PolicyEngine (可选)
        self._policy_engine = None
        if db_session and _HAS_POLICY_ENGINE:
            try:
                self._policy_engine = PolicyEngine(db_session=db_session)
                self._policy_engine.rule_registry.initialize()
                logger.info("PolicyEngine 初始化成功")
            except Exception as e:
                logger.warning("PolicyEngine 初始化失败 (non-blocking): %s", e)

    # ═══════════════════════════════════════════════
    # 核心: 9步流水线 (来自 V6)
    # ═══════════════════════════════════════════════

    def process(self, user_id=None, message: str = "",
                profile: dict = None, device_data: dict = None,
                context: dict = None, tenant_ctx: dict = None,
                user_input=None) -> dict:
        """
        主处理入口 — 9步流水线

        支持两种调用:
          v6: process(user_id=1, message="...", profile={...})
          v0: process(user_input=UserInput(...))
        """
        # V0 兼容: UserInput 对象解构
        if user_input is not None:
            user_id, message, device_data, context = self._unpack_v0_input(
                user_input, user_id, message, device_data, context,
            )

        t0 = time.time()
        profile = profile or {}
        device_data = device_data or {}
        context = context or {}

        logger.info("MasterAgent.process: user_id=%s, msg_len=%d",
                     user_id, len(message or ""))

        # Step 1-2: 构建 AgentInput
        agent_input = AgentInput(
            user_id=user_id, message=message,
            intent=context.get("intent", ""),
            profile=profile, device_data=device_data,
            context=context,
        )

        # Step 2.5: SafetyPipeline L1 — 输入过滤
        safety_meta = {}
        input_category = "normal"
        crisis_shortcut = self._safety_l1(message, agent_input, t0, safety_meta)
        if crisis_shortcut:
            return crisis_shortcut
        input_category = safety_meta.get("input_filter", {}).get("category", "normal")

        # 输入被阻断
        if safety_meta.get("input_filter", {}).get("safe") is False:
            return self._blocked_response(t0, safety_meta)

        # Step 4: 路由 — PolicyEngine 优先, 降级 AgentRouter
        target_domains, policy_trace_id, policy_meta = self._route(
            message, agent_input, profile, context, tenant_ctx,
        )

        # Step 4.5: InsightGenerator
        insights = self._generate_insights(profile, device_data)

        # Step 5: 调用目标 Agent
        agent_results: list[AgentResult] = []
        for domain in target_domains:
            agent = self._agents.get(domain)
            if agent:
                result = agent.process(agent_input)
                agent_results.append(result)

        # Step 6: 多 Agent 协调
        coordination = self.coordinator.coordinate(agent_results, tenant_ctx=tenant_ctx)

        # Step 7: 策略闸门
        gate_result = self.policy_gate.evaluate(
            current_stage=profile.get("current_stage", "S0"),
            stability=profile.get("stability", "stable"),
            intervention_strength=self._assess_strength(coordination),
            dropout_risk=profile.get("dropout_risk", False),
            relapse_risk=profile.get("relapse_risk", False),
            risk_level=coordination.get("risk_level", "low"),
        )

        final_tasks, final_recs = self._apply_gate(gate_result, coordination)

        # Step 7.5: SafetyPipeline L3 — 生成约束
        self._safety_l3(input_category, target_domains, message, safety_meta)

        # Step 8: 合成回复
        synthesis_result = self._synthesize_response(
            stage=profile.get("current_stage", "S0"),
            recommendations=final_recs,
            insights=insights,
            gate=gate_result,
            user_message=message,
            agent_results=agent_results,
        )

        # Step 8.5: SafetyPipeline L4 — 输出过滤
        self._safety_l4(synthesis_result, input_category, safety_meta)

        # Step 9: 组装返回
        elapsed_ms = int((time.time() - t0) * 1000)
        llm_enhanced_agents = [r.agent_domain for r in agent_results if r.llm_enhanced]
        agent_llm_latency = sum(r.llm_latency_ms for r in agent_results)
        total_llm_latency = agent_llm_latency + synthesis_result.get("latency_ms", 0)

        logger.info("MasterAgent.process 完成: user_id=%s, %dms", user_id, elapsed_ms)

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

    # ═══════════════════════════════════════════════
    # 快捷 API (来自 Unified)
    # ═══════════════════════════════════════════════

    def chat(self, user_id, message: str, efficacy_score: float = 50.0) -> str:
        """快捷对话 — 文本 → 教练回复字符串"""
        try:
            result = self.process(
                user_id=user_id, message=message,
                context={"efficacy_score": efficacy_score},
            )
            return result.get("response", "")
        except Exception as e:
            logger.error("MasterAgent.chat 异常: %s", e, exc_info=True)
            return "抱歉，系统处理遇到问题，请稍后重试。"

    def process_json(self, input_json: Dict[str, Any]) -> Dict[str, Any]:
        """JSON 输入处理入口"""
        user_id = input_json.get("user_id", "")
        message = (input_json.get("content", "") or input_json.get("message", "")
                   or input_json.get("query", "") or input_json.get("text", ""))
        profile = input_json.get("profile", {})
        device_data = input_json.get("device_data", {})
        context = input_json.get("context", {})
        for key in ("efficacy_score", "session_id", "input_type"):
            if key in input_json:
                context[key] = input_json[key]
        return self.process(user_id=user_id, message=message,
                            profile=profile, device_data=device_data, context=context)

    def process_with_pipeline(self, input_json: Dict[str, Any]) -> Tuple[Dict, Dict]:
        """带 Pipeline 摘要的 JSON 处理"""
        result = self.process_json(input_json)
        summary = {
            "steps_completed": 9,
            "processing_time_ms": result.get("processing_time_ms", 0),
            "agents_used": result.get("agents_used", []),
            "gate_decision": result.get("gate_decision", ""),
            "llm_enhanced": result.get("llm_enhanced", False),
            "safety": result.get("safety", {}),
        }
        return result, summary

    def route_agents(self, message: str = "", profile: Dict = None,
                     device_data: Optional[Dict] = None,
                     tenant_ctx: Optional[Dict] = None) -> Dict[str, Any]:
        """Step 4: Agent 路由决策 (显式入口)"""
        inp = AgentInput(user_id=0, message=message or "", intent="",
                         profile=profile or {}, device_data=device_data or {}, context={})
        domains = self.router.route(inp, tenant_ctx=tenant_ctx)
        return {
            "agents": domains,
            "primary": domains[0] if domains else "behavior_rx",
            "secondary": domains[1:] if len(domains) > 1 else [],
        }

    def coordinate(self, agent_results) -> Dict[str, Any]:
        """Step 6: 多 Agent 结果协调"""
        return self.coordinator.coordinate(agent_results)

    def sync_device_data(self, user_id, device_data=None) -> Dict[str, Any]:
        dd = self._convert_device_data_obj(device_data) if device_data else {}
        return self.process(user_id=user_id, message="[设备数据同步]",
                            device_data=dd, context={"input_type": "device"})

    def submit_assessment(self, user_id, assessment_data: Dict) -> Dict[str, Any]:
        return self.process(user_id=user_id, message="[评估提交]",
                            context={"input_type": "assessment",
                                     "assessment_data": assessment_data})

    def report_task_completion(self, user_id, task_id: str,
                               completion_data: Dict = None) -> Dict[str, Any]:
        return self.process(
            user_id=user_id, message=f"[任务完成: {task_id}]",
            context={"input_type": "task_report", "task_id": task_id,
                     "completion_data": completion_data or {}},
        )

    # ═══════════════════════════════════════════════
    # 高级功能 (来自 V0, 委托到独立模块)
    # ═══════════════════════════════════════════════

    def create_action_plan(self, analysis=None, profile: Dict = None,
                           stage: str = "contemplation"):
        """生成个性化行为干预计划"""
        try:
            from core.intervention.action_plan import create_action_plan
            return create_action_plan(analysis, profile or {}, stage)
        except ImportError:
            logger.warning("core.intervention 不可用, 尝试 v0 降级")
        # 降级: 尝试 v0
        try:
            return self._v0_delegate("create_action_plan", analysis, profile or {}, stage)
        except Exception:
            return self._fallback_action_plan(stage)

    def generate_daily_briefing(self, user_id, profile=None, plan=None):
        """生成每日简报与任务"""
        try:
            from core.intervention.daily_briefing import generate_daily_briefing
            return generate_daily_briefing(user_id, profile, plan)
        except ImportError:
            logger.warning("core.intervention 不可用, 尝试 v0 降级")
        try:
            return self._v0_delegate("generate_daily_briefing", user_id, profile, plan)
        except Exception:
            return self._fallback_daily_briefing(user_id)

    def generate_phased_plan(self, user_id, profile=None, weeks: int = 12):
        return self._v0_delegate("generate_phased_plan", user_id, profile, weeks)

    def get_daily_push_content(self, user_id) -> Dict[str, Any]:
        try:
            return self._v0_delegate("get_daily_push_content", user_id)
        except Exception:
            return {"message": "今天也要加油哦！", "tasks": []}

    def get_daily_push_message(self, user_id) -> str:
        try:
            return self._v0_delegate("get_daily_push_message", user_id)
        except Exception:
            return "新的一天，继续保持健康习惯！"

    def get_pipeline_orchestrator(self):
        try:
            from core.agents.pipeline import PipelineOrchestrator
            return PipelineOrchestrator()
        except ImportError:
            return self._v0_delegate("get_pipeline_orchestrator")

    # ═══════════════════════════════════════════════
    # 内部方法: 9步流水线子步骤
    # ═══════════════════════════════════════════════

    def _safety_l1(self, message, agent_input, t0, safety_meta):
        """SafetyPipeline L1 — 输入过滤, 危机截断"""
        try:
            from core.safety.pipeline import get_safety_pipeline
            safety = get_safety_pipeline()
            input_result = safety.process_input(message)
            safety_meta["input_filter"] = {
                "safe": input_result.safe,
                "category": input_result.category,
                "severity": input_result.severity,
            }
            if input_result.category == "crisis" and input_result.severity == "critical":
                crisis_agent = self._agents.get("crisis")
                if crisis_agent:
                    crisis_agent.process(agent_input)
                return {
                    "response": safety.get_crisis_response(),
                    "tasks": [], "risk_level": "critical",
                    "agents_used": ["crisis"],
                    "gate_decision": "escalate_coach",
                    "gate_reason": "safety_crisis_detected",
                    "coordination": {}, "insights": [],
                    "processing_time_ms": int((time.time() - t0) * 1000),
                    "llm_enhanced": False, "safety": safety_meta,
                    "policy_trace_id": None, "policy_metadata": {},
                }
            if not input_result.safe:
                return None  # 交给 caller 处理 blocked
        except Exception as e:
            logger.warning("SafetyPipeline L1 failed (non-blocking): %s", e)
        return None

    def _blocked_response(self, t0, safety_meta):
        return {
            "response": "抱歉, 您的消息包含不适当的内容, 无法处理。如需帮助请联系客服。",
            "tasks": [], "risk_level": "high", "agents_used": [],
            "gate_decision": "deny", "gate_reason": "safety_input_blocked",
            "coordination": {}, "insights": [],
            "processing_time_ms": int((time.time() - t0) * 1000),
            "llm_enhanced": False, "safety": safety_meta,
            "policy_trace_id": None, "policy_metadata": {},
        }

    def _route(self, message, agent_input, profile, context, tenant_ctx):
        """Step 4: 路由 — PolicyEngine 优先, 降级到 AgentRouter"""
        policy_trace_id = None
        policy_meta = {}

        if self._policy_engine:
            try:
                event = Event(
                    type='user_message', content=message,
                    domain_keywords=list(context.get('domains', [])),
                    metadata={'session_id': context.get('session_id')},
                )
                policy_ctx = UserContext(
                    user_id=agent_input.user_id,
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
                    return target_domains, policy_trace_id, policy_meta
            except Exception as e:
                logger.warning("PolicyEngine 降级到 AgentRouter: %s", e)

        target_domains = self.router.route(agent_input, tenant_ctx=tenant_ctx)
        return target_domains, policy_trace_id, policy_meta

    def _safety_l3(self, input_category, target_domains, message, safety_meta):
        try:
            from core.safety.pipeline import get_safety_pipeline
            safety = get_safety_pipeline()
            guarded = safety.guard_generation(
                system_prompt="", input_category=input_category,
                agent_domain=target_domains[0] if target_domains else "",
                user_message=message,
            )
            safety_meta["generation_guard"] = {
                "constraints": guarded.constraints,
                "is_crisis": guarded.is_crisis,
            }
        except Exception as e:
            logger.warning("SafetyPipeline L3 failed: %s", e)

    def _safety_l4(self, synthesis_result, input_category, safety_meta):
        try:
            from core.safety.pipeline import get_safety_pipeline
            safety = get_safety_pipeline()
            output_result = safety.filter_output(
                synthesis_result["response"], input_category=input_category,
            )
            synthesis_result["response"] = output_result.text
            safety_meta["output_filter"] = {
                "grade": output_result.grade,
                "annotations": output_result.annotations,
                "disclaimer_added": output_result.disclaimer_added,
            }
        except Exception as e:
            logger.warning("SafetyPipeline L4 failed: %s", e)

    def _apply_gate(self, gate_result, coordination):
        final_tasks = coordination.get("tasks", [])
        final_recs = coordination.get("recommendations", [])
        if gate_result.decision == PolicyDecision.DELAY:
            final_tasks = []
            final_recs = ["当前状态不稳定, 暂不下发新任务, 先稳定情绪"]
        elif gate_result.decision == PolicyDecision.ALLOW_SOFT_SUPPORT:
            final_tasks = [t for t in final_tasks
                           if t.get("difficulty") in ("minimal", "easy", None)]
            final_recs = [r for r in final_recs if "挑战" not in r and "必须" not in r]
        return final_tasks, final_recs

    # ═══════════════════════════════════════════════
    # 内部方法: 合成 + 工具
    # ═══════════════════════════════════════════════

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

    def _synthesize_response(self, stage, recommendations, insights, gate,
                              user_message="", agent_results=None) -> dict:
        """合成教练风格回复: LLM 优先 → 模板降级"""
        if user_message and agent_results:
            try:
                from core.llm_client import get_llm_client
                from .prompts import SYNTHESIS_SYSTEM_PROMPT, build_synthesis_prompt
                client = get_llm_client()
                if client.is_available():
                    agent_summaries = [{"domain": r.agent_domain,
                                        "recommendations": r.recommendations}
                                       for r in agent_results]
                    user_prompt = build_synthesis_prompt(
                        user_message=user_message, stage=stage,
                        gate_decision=gate.decision.value,
                        insights=insights, agent_summaries=agent_summaries,
                    )
                    resp = client.chat(SYNTHESIS_SYSTEM_PROMPT, user_prompt, timeout=45.0)
                    if resp.success and resp.content:
                        return {"response": resp.content, "llm_used": True,
                                "latency_ms": resp.latency_ms,
                                "llm_model": resp.model, "llm_provider": resp.provider}
            except Exception as e:
                logger.warning("LLM synthesis failed, template fallback: %s", e)

        return {"response": self._template_synthesize(stage, recommendations, insights),
                "llm_used": False, "latency_ms": 0}

    def _template_synthesize(self, stage, recommendations, insights) -> str:
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

    # ═══════════════════════════════════════════════
    # V0 兼容工具
    # ═══════════════════════════════════════════════

    def _unpack_v0_input(self, user_input, user_id, message, device_data, context):
        """从 V0 UserInput 对象解构参数"""
        user_id = getattr(user_input, "user_id", user_id)
        message = getattr(user_input, "content", "") or getattr(user_input, "message", "")
        device_data = self._convert_device_data_obj(
            getattr(user_input, "device_data", None)
        )
        context = context or {}
        context["efficacy_score"] = getattr(user_input, "efficacy_score", 50.0)
        context["session_id"] = getattr(user_input, "session_id", "")
        it = getattr(user_input, "input_type", None)
        if it:
            context["input_type"] = it
            context["input_type_value"] = it.value if hasattr(it, "value") else str(it)
        return user_id, message, device_data, context

    def _convert_device_data_obj(self, dd) -> dict:
        if dd is None:
            return {}
        if isinstance(dd, dict):
            return dd
        result = {}
        if hasattr(dd, "cgm") and dd.cgm:
            result["cgm_value"] = getattr(dd.cgm, "current_glucose", None)
            result["cgm_trend"] = getattr(dd.cgm, "trend", None)
            result["tir"] = getattr(dd.cgm, "time_in_range_percent", None)
        if hasattr(dd, "hrv") and dd.hrv:
            result["hrv_sdnn"] = getattr(dd.hrv, "sdnn", None)
            result["hrv_rmssd"] = getattr(dd.hrv, "rmssd", None)
        if hasattr(dd, "sleep") and dd.sleep:
            result["sleep_hours"] = getattr(dd.sleep, "duration_hours", None)
            result["sleep_quality"] = getattr(dd.sleep, "quality_score", None)
        if hasattr(dd, "activity") and dd.activity:
            result["steps"] = getattr(dd.activity, "steps", None)
        return result

    def _v0_delegate(self, method_name, *args, **kwargs):
        """惰性加载 V0 实例, 调用其方法"""
        if not hasattr(self, "_v0_instance"):
            self._v0_instance = None
        if self._v0_instance is None:
            from core.master_agent_v0 import MasterAgent as V0Agent
            self._v0_instance = V0Agent()
            logger.info("V0 MasterAgent 惰性加载 (用于 %s)", method_name)
        return getattr(self._v0_instance, method_name)(*args, **kwargs)

    def _fallback_action_plan(self, stage):
        return {"stage": stage, "goals": ["保持健康习惯"],
                "actions": [{"type": "observation",
                             "description": "记录今日饮食和运动",
                             "difficulty": "easy"}],
                "duration_weeks": 4, "fallback": True}

    def _fallback_daily_briefing(self, user_id):
        return {"user_id": user_id, "greeting": "新的一天开始了！",
                "tasks": [{"task": "完成今日打卡", "priority": "normal"}],
                "coach_message": "保持良好的生活习惯，每天进步一点点。",
                "fallback": True}

    # ═══════════════════════════════════════════════
    # 向后兼容: 硬编码降级 (过渡期)
    # ═══════════════════════════════════════════════

    def _build_hardcoded_agents(self, db_session=None):
        """过渡期: 无 registry 时的硬编码 Agent (2周后删除)"""
        from .specialist_agents import (
            CrisisAgent, SleepAgent, GlucoseAgent, StressAgent,
            NutritionAgent, ExerciseAgent, MentalHealthAgent,
            TCMWellnessAgent, MotivationAgent,
        )
        from .integrative_agents import BehaviorRxAgent, WeightAgent, CardiacRehabAgent
        agents = {
            "crisis": CrisisAgent(), "sleep": SleepAgent(),
            "glucose": GlucoseAgent(), "stress": StressAgent(),
            "nutrition": NutritionAgent(), "exercise": ExerciseAgent(),
            "mental": MentalHealthAgent(), "tcm": TCMWellnessAgent(),
            "motivation": MotivationAgent(), "behavior_rx": BehaviorRxAgent(),
            "weight": WeightAgent(), "cardiac_rehab": CardiacRehabAgent(),
        }
        try:
            from .vision_agent import VisionGuideAgent
            agents["vision"] = VisionGuideAgent()
        except ImportError:
            pass
        try:
            from .xzb_expert_agent import XZBExpertAgent
            agents["xzb_expert"] = XZBExpertAgent()
        except ImportError:
            pass
        return agents

    def _build_legacy_router(self):
        """过渡期: 伪造 registry 给旧 router"""
        # 创建临时 registry 仅用于 router
        from .registry import AgentRegistry
        from .agent_meta import AgentMeta
        temp_reg = AgentRegistry()
        for domain, agent in self._agents.items():
            temp_reg.register(agent, AgentMeta(
                domain=domain,
                display_name=getattr(agent, "display_name", domain),
                priority=getattr(agent, "priority", 5),
            ))
        # 不冻结: 过渡期允许 behavior_rx 补丁
        return AgentRouter(temp_reg)


# ═══════════════════════════════════════════════
# 公开 API — 单例管理
# ═══════════════════════════════════════════════

_master_agent: MasterAgent | None = None


def get_master_agent(db_session=None, registry: AgentRegistry = None) -> MasterAgent:
    """
    获取 MasterAgent 单例

    替代:
      - get_master_agent()   (v0 facade)
      - get_agent_master()   (v6)
    """
    global _master_agent
    if _master_agent is None:
        _master_agent = MasterAgent(registry=registry, db_session=db_session)
    return _master_agent


def get_agent_master(db_session=None) -> MasterAgent:
    """v6 别名 (deprecated)"""
    logger.warning("get_agent_master() deprecated → use get_master_agent()")
    return get_master_agent(db_session)
