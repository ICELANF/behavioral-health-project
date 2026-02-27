"""
⚠️ DEPRECATED — 转发 stub (2周后删除)

原: core.master_agent_unified → UnifiedMasterAgent
现: core.agents.master_agent → MasterAgent (唯一版本)

所有 import 应迁移到:
    from core.agents.master_agent import MasterAgent, get_master_agent
"""
import warnings
import logging

logger = logging.getLogger(__name__)
warnings.warn(
    "core.master_agent_unified 已弃用, 请使用 core.agents.master_agent",
    DeprecationWarning,
    stacklevel=2,
)

# ── 转发 ──
from core.agents.master_agent import (  # noqa: F401, E402
    MasterAgent as UnifiedMasterAgent,
    MasterAgent,
    get_master_agent,
    get_agent_master,
)

logger.warning("core.master_agent_unified: 转发到 core.agents.master_agent (deprecated)")
