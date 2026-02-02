"""
行为健康数字平台 - v14 功能开关配置
Feature Flags Configuration

版本演进：
- v10: 基础平台 + BAPS评估
- v11: Dify深度集成 + Ollama回退 + 患者H5 + TriggerEngine基础版
- v14: 融合版 = v11 + 事件路由 + 节律模型 + Agent增强 + 安全兜底

使用方式：
    from core.v14.config import feature_flags, is_feature_enabled
    
    if is_feature_enabled("ENABLE_RHYTHM_MODEL"):
        from core.v14.rhythm_engine import get_rhythm_engine
        rhythm = get_rhythm_engine()

[v14-NEW] 全新模块
"""
import os
from dataclasses import dataclass
from typing import Dict, Any, List
from loguru import logger


@dataclass
class V14FeatureFlags:
    """v14功能开关配置"""
    
    # ============================================
    # v11原有功能（默认启用，保持向后兼容）
    # ============================================
    ENABLE_DIFY_INTEGRATION: bool = True       # Dify集成
    ENABLE_OLLAMA_FALLBACK: bool = True        # Ollama回退
    ENABLE_CGM_SIMULATOR: bool = True          # CGM模拟器
    ENABLE_PATIENT_PORTAL: bool = True         # 患者门户
    ENABLE_TRIGGER_ENGINE: bool = True         # 基础Trigger引擎(v11)
    ENABLE_AGENT_ORCHESTRATOR: bool = True     # Agent编排器(v11)
    
    # ============================================
    # [v14-NEW] Trigger事件系统增强
    # ============================================
    ENABLE_TRIGGER_EVENT_ROUTING: bool = False    # 事件路由系统
    ENABLE_TRIGGER_TASK_EVENTS: bool = False      # 任务触发事件
    ENABLE_TRIGGER_USAGE_EVENTS: bool = False     # 使用行为触发
    ENABLE_TRIGGER_EMOTION_EVENTS: bool = False   # 情绪触发
    
    # ============================================
    # [v14-NEW] 节律模型
    # ============================================
    ENABLE_RHYTHM_MODEL: bool = False             # 节律检测引擎
    RHYTHM_FREEZE_ON_COLLAPSE: bool = True        # 崩溃风险时冻结干预
    RHYTHM_ONLY_DOWNGRADE: bool = True            # 节律只能降级（伦理约束）
    
    # ============================================
    # [v14-NEW] Agent框架增强
    # ============================================
    ENABLE_V14_AGENTS: bool = False               # v14增强Agent总开关
    ENABLE_EXPLAIN_AGENT: bool = False            # 行为解释Agent
    ENABLE_RESISTANCE_AGENT: bool = False         # 阻抗识别Agent
    ENABLE_SAFETY_AGENT: bool = True              # 安全兜底Agent（始终启用）
    
    # ============================================
    # [v14-NEW] 专家规则配置
    # ============================================
    ENABLE_EXPERT_RULE_CONFIG: bool = False       # 专家规则配置
    EXPERT_SANDBOX_REQUIRED: bool = True          # 沙箱测试必须
    EXPERT_AUDIT_ENABLED: bool = True             # 审计日志
    
    # ============================================
    # [v14-NEW] 质量审计模块
    # ============================================
    ENABLE_QUALITY_AUDIT: bool = False            # 质量审计总开关
    QUALITY_AUDIT_ASYNC: bool = True              # 异步审计（默认）
    QUALITY_JUDGE_MODEL: str = "qwen2.5:14b"      # 评判模型
    QUALITY_JUDGE_BACKEND: str = "ollama"         # 评判后端 (ollama/dify)
    
    # ============================================
    # [v14-NEW] 披露控制模块
    # ============================================
    ENABLE_DISCLOSURE_CONTROL: bool = False       # 披露控制总开关
    ENABLE_BLACKLIST_FILTER: bool = True          # 禁词过滤（默认启用）
    ENABLE_DUAL_SIGNATURE: bool = True            # 双重签名（默认启用）
    ENABLE_AI_REWRITER: bool = True               # AI重写器（默认启用）
    DISCLOSURE_AUTO_APPROVE_LOW_RISK: bool = True # 低风险自动批准
    
    # ============================================
    # 调试选项
    # ============================================
    V14_DEBUG_MODE: bool = False
    V14_LOG_LEVEL: str = "INFO"
    
    def __post_init__(self):
        """从环境变量加载配置（覆盖默认值）"""
        for field_name in self.__dataclass_fields__:
            env_key = f"BH_V14_{field_name}"
            env_value = os.getenv(env_key)
            if env_value is not None:
                field_type = self.__dataclass_fields__[field_name].type
                if field_type == bool:
                    setattr(self, field_name, env_value.lower() in ('true', '1', 'yes'))
                else:
                    setattr(self, field_name, env_value)


# 全局单例
feature_flags = V14FeatureFlags()


def is_feature_enabled(flag_name: str) -> bool:
    """检查功能是否启用"""
    return getattr(feature_flags, flag_name, False)


def require_feature(flag_name: str):
    """功能开关装饰器 - 未启用时跳过执行"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not is_feature_enabled(flag_name):
                logger.debug(f"功能未启用: {flag_name}, 调用被跳过")
                return None
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator


def get_active_features() -> Dict[str, bool]:
    """获取所有已启用的功能"""
    return {
        name: value 
        for name, value in feature_flags.__dict__.items()
        if isinstance(value, bool) and value
    }


def get_version_info() -> Dict[str, Any]:
    """获取版本信息"""
    v14_features = [
        "ENABLE_TRIGGER_EVENT_ROUTING",
        "ENABLE_RHYTHM_MODEL",
        "ENABLE_V14_AGENTS",
        "ENABLE_EXPLAIN_AGENT",
        "ENABLE_RESISTANCE_AGENT"
    ]
    
    v14_enabled = any(is_feature_enabled(f) for f in v14_features)
    
    return {
        "version": "v14" if v14_enabled else "v11",
        "base_version": "v11",
        "v11_features": {
            "dify_integration": feature_flags.ENABLE_DIFY_INTEGRATION,
            "ollama_fallback": feature_flags.ENABLE_OLLAMA_FALLBACK,
            "trigger_engine": feature_flags.ENABLE_TRIGGER_ENGINE,
            "patient_portal": feature_flags.ENABLE_PATIENT_PORTAL,
            "agent_orchestrator": feature_flags.ENABLE_AGENT_ORCHESTRATOR,
        },
        "v14_features": {
            "trigger_event_routing": feature_flags.ENABLE_TRIGGER_EVENT_ROUTING,
            "rhythm_model": feature_flags.ENABLE_RHYTHM_MODEL,
            "v14_agents": feature_flags.ENABLE_V14_AGENTS,
            "explain_agent": feature_flags.ENABLE_EXPLAIN_AGENT,
            "resistance_agent": feature_flags.ENABLE_RESISTANCE_AGENT,
            "safety_agent": feature_flags.ENABLE_SAFETY_AGENT,
        }
    }


def check_dependencies() -> List[str]:
    """检查功能依赖关系"""
    issues = []
    
    # 节律模型需要Trigger系统
    if feature_flags.ENABLE_RHYTHM_MODEL and not feature_flags.ENABLE_TRIGGER_ENGINE:
        issues.append("ENABLE_RHYTHM_MODEL 需要 ENABLE_TRIGGER_ENGINE")
    
    # 事件路由需要Trigger系统
    if feature_flags.ENABLE_TRIGGER_EVENT_ROUTING and not feature_flags.ENABLE_TRIGGER_ENGINE:
        issues.append("ENABLE_TRIGGER_EVENT_ROUTING 需要 ENABLE_TRIGGER_ENGINE")
    
    # v14 Agent需要Agent编排器
    if feature_flags.ENABLE_V14_AGENTS and not feature_flags.ENABLE_AGENT_ORCHESTRATOR:
        issues.append("ENABLE_V14_AGENTS 需要 ENABLE_AGENT_ORCHESTRATOR")
    
    # 解释Agent需要v14 Agent总开关
    if feature_flags.ENABLE_EXPLAIN_AGENT and not feature_flags.ENABLE_V14_AGENTS:
        issues.append("ENABLE_EXPLAIN_AGENT 需要 ENABLE_V14_AGENTS")
    
    # 阻抗Agent需要v14 Agent总开关
    if feature_flags.ENABLE_RESISTANCE_AGENT and not feature_flags.ENABLE_V14_AGENTS:
        issues.append("ENABLE_RESISTANCE_AGENT 需要 ENABLE_V14_AGENTS")
    
    return issues


def print_feature_status():
    """打印功能状态（调试用）"""
    info = get_version_info()
    print(f"\n{'='*50}")
    print(f"  行为健康平台 - 版本: {info['version']}")
    print(f"{'='*50}")
    print("\nv11功能:")
    for k, v in info['v11_features'].items():
        print(f"  {'✅' if v else '❌'} {k}")
    print("\nv14新增功能:")
    for k, v in info['v14_features'].items():
        print(f"  {'✅' if v else '❌'} {k}")
    
    issues = check_dependencies()
    if issues:
        print("\n⚠️ 依赖问题:")
        for issue in issues:
            print(f"  - {issue}")
    print()
