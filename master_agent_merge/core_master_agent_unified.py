# -*- coding: utf-8 -*-
"""
master_agent_unified.py — 统一 MasterAgent (v0+v6 合并)

合并策略:
  BASE = v6 (core/agents/master_agent.py)
    - 12领域Agent + 模板驱动 + 硬编码降级
    - SafetyPipeline L1/L3/L4 全层级集成
    - V007 PolicyEngine → AgentRouter 双路径路由
    - LLM合成 → 模板合成 降级链
    - 租户路由上下文 (tenant_ctx)

  ADDITIONS from v0 (core/master_agent_v0.py):
    - chat() 快捷对话接口
    - process_json() / process_with_pipeline() JSON入口
    - generate_daily_briefing() 每日简报
    - create_action_plan() 行为干预计划
    - sync_device_data() / submit_assessment() / report_task_completion()
    - route_agents() / coordinate() 显式调用入口

  FACADE from core/master_agent.py:
    - try/except 保护 + 结构化日志

消除双单例:
  Before: _master_agent(v0) + _agent_master(v6)
  After:  _master_agent = UnifiedMasterAgent (单例)

向后兼容:
  - from core.master_agent import MasterAgent → UnifiedMasterAgent
  - from core.master_agent_v0 import MasterAgent → 保留但标记 deprecated
  - from core.agents.master_agent import MasterAgent → 保留原 v6
"""
from __future__ import annotations
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# =====================================================================
# v0 类型导入 (向后兼容, 延迟加载)
# =====================================================================

def _import_v0_types():
    """延迟导入 v0 数据类型, 缺失时返回占位"""
    try:
        from core.master_agent_v0 import (
            UserInput, MasterAgentResponse, PipelineOrchestrator,
            AgentAnalysisResult, IntegratedAnalysis, ActionPlan,
            DailyBriefing, DeviceData, InputType,
        )
        return {
            "UserInput": UserInput,
            "MasterAgentResponse": MasterAgentResponse,
            "PipelineOrchestrator": PipelineOrchestrator,
            "AgentAnalysisResult": AgentAnalysisResult,
            "IntegratedAnalysis": IntegratedAnalysis,
            "ActionPlan": ActionPlan,
            "DailyBriefing": DailyBriefing,
            "DeviceData": DeviceData,
            "InputType": InputType,
        }
    except ImportError as e:
        logger.warning("v0 types import failed (v0 compat disabled): %s", e)
        return {}

_v0_types: dict | None = None

def _v0(name: str):
    """获取 v0 类型 (惰性初始化)"""
    global _v0_types
    if _v0_types is None:
        _v0_types = _import_v0_types()
    cls = _v0_types.get(name)
    if cls is None:
        raise ImportError(f"v0 type '{name}' not available — install core.master_agent_v0")
    return cls


# =====================================================================
# v6 核心导入
# =====================================================================

from core.agents.master_agent import MasterAgent as _V6MasterAgent


# =====================================================================
# 统一 MasterAgent
# =====================================================================

class UnifiedMasterAgent(_V6MasterAgent):
    """
    统一 MasterAgent — v6核心架构 + v0兼容API + facade日志保护

    继承 v6 的:
      - __init__(db_session) — 12 Agent + 模板驱动 + PolicyEngine
      - process(user_id, message, profile, device_data, context, tenant_ctx) → dict

    新增 v0 兼容 API:
      - chat(user_id, message, efficacy_score) → str
      - process_json(input_json) → dict
      - process_with_pipeline(input_json) → (dict, dict)
      - generate_daily_briefing(user_id, profile, plan) → DailyBriefing
      - create_action_plan(analysis, profile, stage) → ActionPlan
      - sync_device_data(user_id, device_data) → dict
      - submit_assessment(user_id, assessment_data) → dict
      - report_task_completion(user_id, task_id, completion_data) → dict
      - route_agents(message, profile, device_data) → dict
      - coordinate(agent_results) → dict
      - get_pipeline_orchestrator() → PipelineOrchestrator
    """

    def __init__(self, db_session=None, config_path: str = "config.yaml"):
        super().__init__(db_session=db_session)
        self._config_path = config_path
        self._v0_instance = None  # 惰性 v0 实例 (仅需要 v0 独有功能时)
        logger.info("UnifiedMasterAgent 初始化完成 (v6核心 + v0兼容)")

    # =================================================================
    # v6 核心覆写 — 增加日志保护 (原 facade 功能)
    # =================================================================

    def process(self, user_id=None, message: str = "",
                profile: dict = None, device_data: dict = None,
                context: dict = None, tenant_ctx: dict = None,
                # v0 兼容: 接受 UserInput 对象
                user_input=None) -> dict:
        """
        主处理入口 — 9步流水线

        支持两种调用方式:
          1. v6 风格: process(user_id=1, message="...", profile={...})
          2. v0 风格: process(user_input=UserInput(...))
        """
        # v0 兼容: 如果传入 UserInput 对象, 解构到 v6 参数
        if user_input is not None:
            user_id = getattr(user_input, "user_id", user_id)
            message = getattr(user_input, "content", "") or getattr(user_input, "message", "")
            device_data = self._convert_v0_device_data(user_input)
            context = getattr(user_input, "context", {})
            context["efficacy_score"] = getattr(user_input, "efficacy_score", 50.0)
            context["session_id"] = getattr(user_input, "session_id", "")
            context["input_type"] = getattr(user_input, "input_type", None)
            if hasattr(user_input, "input_type"):
                it = user_input.input_type
                context["input_type_value"] = it.value if hasattr(it, "value") else str(it)

        try:
            logger.info("MasterAgent.process: user_id=%s, msg_len=%d",
                        user_id, len(message or ""))
            result = super().process(
                user_id=user_id, message=message,
                profile=profile, device_data=device_data,
                context=context, tenant_ctx=tenant_ctx,
            )
            logger.info("MasterAgent.process 完成: user_id=%s, %dms",
                        user_id, result.get("processing_time_ms", 0))
            return result
        except Exception as e:
            logger.error("MasterAgent.process 异常: user_id=%s, %s",
                         user_id, e, exc_info=True)
            raise

    # =================================================================
    # v0 兼容 API — 快捷方法
    # =================================================================

    def chat(self, user_id, message: str, efficacy_score: float = 50.0) -> str:
        """
        快捷对话接口 — 文本 → 教练回复字符串

        v0 兼容: 返回 str (不是 dict)
        """
        try:
            logger.info("MasterAgent.chat: user_id=%s, msg_len=%d",
                        user_id, len(message))
            result = self.process(
                user_id=user_id,
                message=message,
                context={"efficacy_score": efficacy_score},
            )
            response = result.get("response", "")
            logger.info("MasterAgent.chat 完成: reply_len=%d", len(response))
            return response
        except Exception as e:
            logger.error("MasterAgent.chat 异常: %s", e, exc_info=True)
            return "抱歉，系统处理遇到问题，请稍后重试。"

    def process_json(self, input_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        JSON 输入处理入口

        自动从 JSON 提取 user_id, message 等字段, 调用 process()
        """
        try:
            logger.info("MasterAgent.process_json")
            user_id = input_json.get("user_id", "")
            message = (input_json.get("content", "")
                       or input_json.get("message", "")
                       or input_json.get("query", "")
                       or input_json.get("text", ""))
            profile = input_json.get("profile", {})
            device_data = input_json.get("device_data", {})
            context = input_json.get("context", {})

            # 合并顶层字段到 context
            for key in ("efficacy_score", "session_id", "input_type"):
                if key in input_json:
                    context[key] = input_json[key]

            return self.process(
                user_id=user_id, message=message,
                profile=profile, device_data=device_data,
                context=context,
            )
        except Exception as e:
            logger.error("MasterAgent.process_json 异常: %s", e)
            raise

    def process_with_pipeline(self, input_json: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        带 Pipeline 上下文的 JSON 处理

        Returns: (response_dict, pipeline_summary)
        """
        try:
            logger.info("MasterAgent.process_with_pipeline")
            result = self.process_json(input_json)
            # 构建 pipeline summary
            summary = {
                "steps_completed": 9,
                "processing_time_ms": result.get("processing_time_ms", 0),
                "agents_used": result.get("agents_used", []),
                "gate_decision": result.get("gate_decision", ""),
                "llm_enhanced": result.get("llm_enhanced", False),
                "safety": result.get("safety", {}),
            }
            return result, summary
        except Exception as e:
            logger.error("MasterAgent.process_with_pipeline 异常: %s", e)
            raise

    def route_agents(self, message: str = "", profile: Dict[str, Any] = None,
                     device_data: Optional[Dict] = None,
                     tenant_ctx: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Step 4: Agent 路由决策 (显式调用入口)

        Returns:
            {"agents": ["glucose", "sleep"], "primary": "glucose"}
        """
        try:
            logger.info("MasterAgent.route_agents: msg_len=%d", len(message or ""))
            from core.agents.base import AgentInput
            inp = AgentInput(
                user_id=0, message=message or "",
                intent="", profile=profile or {},
                device_data=device_data or {},
                context={},
            )
            domains = self.router.route(inp, tenant_ctx=tenant_ctx)
            return {
                "agents": domains,
                "primary": domains[0] if domains else "behavior_rx",
                "secondary": domains[1:] if len(domains) > 1 else [],
            }
        except Exception as e:
            logger.error("MasterAgent.route_agents 异常: %s", e)
            raise

    def coordinate(self, agent_results) -> Dict[str, Any]:
        """
        Step 6: 多 Agent 结果协调整合

        接受 v6 AgentResult 列表 或 v0 AgentAnalysisResult 列表
        """
        try:
            logger.info("MasterAgent.coordinate: %d 个Agent结果", len(agent_results))
            return self.coordinator.coordinate(agent_results)
        except Exception as e:
            logger.error("MasterAgent.coordinate 异常: %s", e)
            raise

    def sync_device_data(self, user_id, device_data=None) -> Dict[str, Any]:
        """设备数据同步处理"""
        try:
            logger.info("MasterAgent.sync_device_data: user=%s", user_id)
            dd = {}
            if device_data is not None:
                dd = self._convert_v0_device_data_obj(device_data)
            return self.process(
                user_id=user_id, message="[设备数据同步]",
                device_data=dd,
                context={"input_type": "device"},
            )
        except Exception as e:
            logger.error("MasterAgent.sync_device_data 异常: %s", e)
            raise

    def submit_assessment(self, user_id, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """提交评估数据"""
        try:
            logger.info("MasterAgent.submit_assessment: user=%s", user_id)
            return self.process(
                user_id=user_id, message="[评估提交]",
                context={"input_type": "assessment", "assessment_data": assessment_data},
            )
        except Exception as e:
            logger.error("MasterAgent.submit_assessment 异常: %s", e)
            raise

    def report_task_completion(self, user_id, task_id: str,
                              completion_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """上报任务完成"""
        try:
            logger.info("MasterAgent.report_task_completion: user=%s, task=%s",
                        user_id, task_id)
            return self.process(
                user_id=user_id, message=f"[任务完成: {task_id}]",
                context={
                    "input_type": "task_report",
                    "task_id": task_id,
                    "completion_data": completion_data or {},
                },
            )
        except Exception as e:
            logger.error("MasterAgent.report_task_completion 异常: %s", e)
            raise

    # =================================================================
    # v0 高级功能 — 委托到 v0 实例 (惰性加载)
    # =================================================================

    @property
    def _v0(self):
        """惰性加载 v0 MasterAgent (仅用于 v0 独有功能)"""
        if self._v0_instance is None:
            try:
                from core.master_agent_v0 import MasterAgent as V0Agent
                self._v0_instance = V0Agent(config_path=self._config_path)
                logger.info("v0 MasterAgent 惰性加载成功 (用于高级功能)")
            except Exception as e:
                logger.error("v0 MasterAgent 加载失败: %s", e)
                raise
        return self._v0_instance

    def create_action_plan(self, analysis=None, profile: Dict[str, Any] = None,
                           stage: str = "contemplation"):
        """
        Step 7: 生成个性化行为干预计划

        委托到 v0 引擎 (包含完整的干预策略库)
        """
        try:
            logger.info("MasterAgent.create_action_plan: stage=%s", stage)
            return self._v0.create_action_plan(analysis, profile or {}, stage)
        except Exception as e:
            logger.error("MasterAgent.create_action_plan 异常: %s", e)
            # 降级: 返回简化计划
            return self._fallback_action_plan(stage)

    def generate_daily_briefing(self, user_id, profile=None, plan=None):
        """
        Step 9: 生成每日简报与任务

        委托到 v0 引擎 (包含完整的每日推送逻辑)
        """
        try:
            logger.info("MasterAgent.generate_daily_briefing: user=%s", user_id)
            return self._v0.generate_daily_briefing(user_id, profile, plan)
        except Exception as e:
            logger.error("MasterAgent.generate_daily_briefing 异常: %s", e)
            # 降级: 返回基础简报
            return self._fallback_daily_briefing(user_id)

    def get_pipeline_orchestrator(self):
        """获取 PipelineOrchestrator 实例"""
        try:
            logger.info("MasterAgent.get_pipeline_orchestrator")
            return self._v0.get_pipeline_orchestrator()
        except Exception as e:
            logger.error("PipelineOrchestrator 获取失败: %s", e)
            raise

    def generate_phased_plan(self, user_id, profile=None, weeks: int = 12):
        """生成分阶段计划 (v0 独有)"""
        try:
            return self._v0.generate_phased_plan(user_id, profile, weeks)
        except Exception as e:
            logger.error("generate_phased_plan 异常: %s", e)
            raise

    def get_daily_push_content(self, user_id) -> Dict[str, Any]:
        """获取每日推送内容 (v0 独有)"""
        try:
            return self._v0.get_daily_push_content(user_id)
        except Exception as e:
            logger.error("get_daily_push_content 异常: %s", e)
            return {"message": "今天也要加油哦！", "tasks": []}

    def get_daily_push_message(self, user_id) -> str:
        """获取每日推送消息文本 (v0 独有)"""
        try:
            return self._v0.get_daily_push_message(user_id)
        except Exception as e:
            logger.error("get_daily_push_message 异常: %s", e)
            return "新的一天，继续保持健康习惯！"

    # =================================================================
    # 内部工具方法
    # =================================================================

    def _convert_v0_device_data(self, user_input) -> dict:
        """从 v0 UserInput 提取设备数据为 v6 dict"""
        dd = getattr(user_input, "device_data", None)
        if dd is None:
            return {}
        return self._convert_v0_device_data_obj(dd)

    def _convert_v0_device_data_obj(self, dd) -> dict:
        """将 v0 DeviceData 对象转为 v6 dict"""
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

    def _fallback_action_plan(self, stage: str):
        """降级行为干预计划"""
        return {
            "stage": stage,
            "goals": ["保持健康习惯"],
            "actions": [
                {"type": "observation", "description": "记录今日饮食和运动", "difficulty": "easy"}
            ],
            "duration_weeks": 4,
            "fallback": True,
        }

    def _fallback_daily_briefing(self, user_id):
        """降级每日简报"""
        return {
            "user_id": user_id,
            "greeting": "新的一天开始了！",
            "tasks": [
                {"task": "完成今日打卡", "priority": "normal"}
            ],
            "coach_message": "保持良好的生活习惯，每天进步一点点。",
            "fallback": True,
        }


# =====================================================================
# 公开 API — 单例管理
# =====================================================================

_unified_agent: UnifiedMasterAgent | None = None


def get_master_agent(db_session=None) -> UnifiedMasterAgent:
    """
    获取统一 MasterAgent 单例

    替代原有的:
      - get_master_agent() → v0 facade
      - get_agent_master() → v6

    现在统一为一个入口:
      agent = get_master_agent(db_session)
      agent.process(...)       # v6 核心流程
      agent.chat(...)          # v0 快捷接口
      agent.route_agents(...)  # 显式路由
    """
    global _unified_agent
    if _unified_agent is None:
        _unified_agent = UnifiedMasterAgent(db_session=db_session)
    return _unified_agent


# 向后兼容别名
def get_agent_master(db_session=None) -> UnifiedMasterAgent:
    """v6 别名 → 统一入口 (deprecated)"""
    logger.warning("get_agent_master() deprecated, use get_master_agent()")
    return get_master_agent(db_session)


# 导出供 facade 使用
MasterAgent = UnifiedMasterAgent
