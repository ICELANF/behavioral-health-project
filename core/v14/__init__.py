"""
行为健康数字平台 - v14 扩展模块
v14 Extension Module

[v14-NEW] 包含以下新功能：
1. config - 功能开关配置
2. rhythm_engine - 节律引擎
3. agents - Agent增强（Explain/Resistance/Safety）
4. trigger_router - Trigger事件路由

使用方式：
    from core.v14 import (
        feature_flags,
        is_feature_enabled,
        get_rhythm_engine,
        get_agent_enhancer,
        get_trigger_router
    )

版本演进：
- v10: 基础平台 + BAPS评估
- v11: Dify深度集成 + Ollama回退 + 患者H5 + TriggerEngine基础版
- v14: 融合版 = v11 + 事件路由 + 节律模型 + Agent增强 + 安全兜底
"""

# 功能开关
from core.v14.config import (
    feature_flags,
    is_feature_enabled,
    require_feature,
    get_version_info,
    get_active_features,
    check_dependencies,
    print_feature_status
)

# 节律引擎
from core.v14.rhythm_engine import (
    RhythmPhase,
    RhythmDomain,
    RhythmSignal,
    RhythmPolicy,
    RhythmEngine,
    get_rhythm_engine
)

# Agent增强
from core.v14.agents import (
    AgentAction,
    ResistanceType,
    AgentOutput,
    SafetyAgent,
    ResistanceAgent,
    ExplainAgent,
    AgentEnhancer,
    get_agent_enhancer
)

# Trigger事件路由
from core.v14.trigger_router import (
    TriggerEventType,
    TriggerLevel,
    EngineAction,
    TriggerEvent,
    TriggerRoute,
    TriggerRouter,
    get_trigger_router
)

__all__ = [
    # config
    'feature_flags',
    'is_feature_enabled',
    'require_feature',
    'get_version_info',
    'get_active_features',
    'check_dependencies',
    'print_feature_status',
    
    # rhythm
    'RhythmPhase',
    'RhythmDomain',
    'RhythmSignal',
    'RhythmPolicy',
    'RhythmEngine',
    'get_rhythm_engine',
    
    # agents
    'AgentAction',
    'ResistanceType',
    'AgentOutput',
    'SafetyAgent',
    'ResistanceAgent',
    'ExplainAgent',
    'AgentEnhancer',
    'get_agent_enhancer',
    
    # trigger_router
    'TriggerEventType',
    'TriggerLevel',
    'EngineAction',
    'TriggerEvent',
    'TriggerRoute',
    'TriggerRouter',
    'get_trigger_router',
]

__version__ = "14.0.0"
