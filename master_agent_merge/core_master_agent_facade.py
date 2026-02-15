# -*- coding: utf-8 -*-
"""
master_agent.py — 中枢 Master Agent 入口 (Facade)

行健行为教练多Agent系统的统一外观层。

V4.0 重构:
  Before: 从 master_agent_v0 导入, 仅添加日志
  After:  从 master_agent_unified 导入, 合并 v0+v6

统一入口:
  from core.master_agent import MasterAgent
  from core.master_agent import get_master_agent
"""

# =====================================================================
# 统一导入 (v0+v6 合并版)
# =====================================================================

from core.master_agent_unified import (  # noqa: F401
    UnifiedMasterAgent as MasterAgent,
    get_master_agent,
    get_agent_master,    # deprecated 别名
)

# =====================================================================
# v0 类型向后兼容导出 (供历史代码 import)
# =====================================================================

try:
    from core.master_agent_v0 import (  # noqa: F401
        UserInput,
        MasterAgentResponse,
        PipelineOrchestrator,
        AgentAnalysisResult,
        IntegratedAnalysis,
        ActionPlan,
        DailyBriefing,
        DeviceData,
    )
except ImportError:
    pass  # v0 不可用时静默跳过

__all__ = [
    "MasterAgent",
    "get_master_agent",
    "get_agent_master",
]
