# -*- coding: utf-8 -*-
"""
master_agent.py - 中枢 Master Agent 入口 (Facade)

行健行为教练多Agent系统的核心控制器入口。
本模块作为 MasterAgent 的统一外观层，提供:
  - 9步编排流程的日志化封装
  - 异常处理与降级保护
  - 向后兼容的 API 接口

从 master_agent_v0 导入全部内容，保持向后兼容。
"""

import logging
from typing import Dict, Any, Optional, List, Tuple

from core.master_agent_v0 import *  # noqa: F401,F403
from core.master_agent_v0 import (
    MasterAgent as _MasterAgentBase,
    MasterAgentResponse,
    UserInput,
    PipelineOrchestrator,
    AgentAnalysisResult,
    IntegratedAnalysis,
    ActionPlan,
    DailyBriefing,
    DeviceData,
)

logger = logging.getLogger(__name__)


class MasterAgent(_MasterAgentBase):
    """MasterAgent Facade — 带日志与异常保护的中枢代理入口。

    在 master_agent_v0.MasterAgent 基础上增加:
      - 每个核心方法的 try/except 保护
      - 结构化日志记录 (进入/退出/异常)
      - 统一错误响应构建
    """

    def process(self, user_input: UserInput) -> MasterAgentResponse:
        """Step 1-9: 处理用户输入的完整编排流程"""
        try:
            logger.info("MasterAgent.process 开始: user_id=%s, type=%s",
                        getattr(user_input, 'user_id', 'unknown'),
                        getattr(user_input, 'request_type', 'unknown'))
            result = super().process(user_input)
            logger.info("MasterAgent.process 完成: user_id=%s",
                        getattr(user_input, 'user_id', 'unknown'))
            return result
        except Exception as e:
            logger.error("MasterAgent.process 异常: %s", e, exc_info=True)
            raise

    def chat(self, user_id: str, message: str, efficacy_score: float = 50.0) -> str:
        """快捷对话接口 — 文本消息 → 教练回复"""
        try:
            logger.info("MasterAgent.chat 开始: user_id=%s, msg_len=%d",
                        user_id, len(message))
            result = super().chat(user_id, message, efficacy_score)
            logger.info("MasterAgent.chat 完成: user_id=%s, reply_len=%d",
                        user_id, len(result))
            return result
        except Exception as e:
            logger.error("MasterAgent.chat 异常: user_id=%s, error=%s",
                         user_id, e, exc_info=True)
            raise

    def process_json(self, input_json: Dict[str, Any]) -> Dict[str, Any]:
        """JSON 输入处理入口"""
        try:
            logger.info("MasterAgent.process_json 开始")
            return super().process_json(input_json)
        except Exception as e:
            logger.error("MasterAgent.process_json 异常: %s", e)
            raise

    def process_with_pipeline(self, input_json: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """带 Pipeline 上下文的 JSON 处理"""
        try:
            logger.info("MasterAgent.process_with_pipeline 开始")
            return super().process_with_pipeline(input_json)
        except Exception as e:
            logger.error("MasterAgent.process_with_pipeline 异常: %s", e)
            raise

    def route_agents(self, message: str, profile: Dict[str, Any],
                     device_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Step 4: Agent 路由决策"""
        try:
            logger.info("MasterAgent.route_agents 开始: msg_len=%d", len(message))
            return super().route_agents(message, profile, device_data)
        except Exception as e:
            logger.error("MasterAgent.route_agents 异常: %s", e)
            raise

    def coordinate(self, agent_results: List[AgentAnalysisResult]) -> IntegratedAnalysis:
        """Step 6: 多 Agent 结果协调整合"""
        try:
            logger.info("MasterAgent.coordinate 开始: %d个Agent结果",
                        len(agent_results))
            return super().coordinate(agent_results)
        except Exception as e:
            logger.error("MasterAgent.coordinate 异常: %s", e)
            raise

    def create_action_plan(self, analysis: Any, profile: Dict[str, Any],
                           stage: str = "contemplation") -> ActionPlan:
        """Step 7: 生成个性化行为干预计划"""
        try:
            logger.info("MasterAgent.create_action_plan 开始: stage=%s", stage)
            return super().create_action_plan(analysis, profile, stage)
        except Exception as e:
            logger.error("MasterAgent.create_action_plan 异常: %s", e)
            raise

    def generate_daily_briefing(self, user_id: str,
                                profile: Optional[Dict] = None,
                                plan: Optional[ActionPlan] = None) -> DailyBriefing:
        """Step 9: 生成每日简报与任务"""
        try:
            logger.info("MasterAgent.generate_daily_briefing 开始: user=%s", user_id)
            return super().generate_daily_briefing(user_id, profile, plan)
        except Exception as e:
            logger.error("MasterAgent.generate_daily_briefing 异常: %s", e)
            raise

    def sync_device_data(self, user_id: str, device_data: DeviceData) -> MasterAgentResponse:
        """设备数据同步处理"""
        try:
            logger.info("MasterAgent.sync_device_data 开始: user=%s", user_id)
            return super().sync_device_data(user_id, device_data)
        except Exception as e:
            logger.error("MasterAgent.sync_device_data 异常: %s", e)
            raise

    def get_pipeline_orchestrator(self) -> PipelineOrchestrator:
        """获取 Pipeline 编排器实例"""
        logger.info("MasterAgent.get_pipeline_orchestrator 调用")
        return super().get_pipeline_orchestrator()
