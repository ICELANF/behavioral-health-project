"""
Professional Agent 注册表

每个Agent必须在此注册才能被路由发现。
从 agents/ 目录加载具体实现。
"""
from typing import Dict, Any

REGISTRY: Dict[str, Any] = {
    "behavior_coach": {"domain": "behavior", "desc": "行为教练（上游前置）", "rx_enabled": True},
    "metabolic_expert": {"domain": "endocrine", "desc": "代谢内分泌专家", "rx_enabled": True},
    "cardiac_rehab": {"domain": "cardio", "desc": "心血管康复专家", "rx_enabled": True},
    "adherence_monitor": {"domain": "adherence", "desc": "就医依从性（横切）", "rx_enabled": True},
    "nutrition_expert": {"domain": "nutrition", "desc": "营养处方专家", "rx_enabled": True},
    "exercise_expert": {"domain": "exercise", "desc": "运动处方专家", "rx_enabled": True},
    "sleep_expert": {"domain": "sleep", "desc": "睡眠干预专家", "rx_enabled": True},
    "tcm_expert": {"domain": "tcm", "desc": "中医辨证专家", "rx_enabled": True},
    "mental_expert": {"domain": "mental", "desc": "心理干预专家", "rx_enabled": True},
    "chronic_manager": {"domain": "chronic", "desc": "慢病管理专家", "rx_enabled": True},
    "rehab_expert": {"domain": "rehab", "desc": "康复管理专家", "rx_enabled": True},
    "health_educator": {"domain": "education", "desc": "健康教育专家", "rx_enabled": True},
    "assessment_engine": {"domain": "assessment", "desc": "评估引擎Agent"},
    "rx_composer": {"domain": "rx", "desc": "处方编排Agent", "rx_enabled": True},
    "supervisor_reviewer": {"domain": "governance", "desc": "督导审核Agent"},
    "quality_auditor": {"domain": "governance", "desc": "质量审计Agent"},
}


def get_agent(name: str):
    """按名称获取Agent实例"""
    if name not in REGISTRY:
        raise ValueError(f"未注册的Agent: {name}")

    # 延迟导入避免循环
    import importlib
    module = importlib.import_module(f".agents.{name}", package=__package__)
    agent_class = getattr(module, "Agent", None)
    if agent_class is None:
        raise ImportError(f"agents/{name}.py 缺少 Agent 类")
    return agent_class()


def list_agents() -> list:
    """列出所有已注册Agent"""
    return [
        {"name": k, **v}
        for k, v in REGISTRY.items()
    ]
