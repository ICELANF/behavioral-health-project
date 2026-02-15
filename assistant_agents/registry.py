"""
Assistant Agent 注册表

每个Agent必须在此注册才能被路由发现。
从 agents/ 目录加载具体实现。
"""
from typing import Dict, Any

REGISTRY: Dict[str, Any] = {
    "health_assistant": {"domain": "general", "desc": "健康知识科普助手"},
    "nutrition_guide": {"domain": "nutrition", "desc": "营养知识引导"},
    "exercise_guide": {"domain": "exercise", "desc": "运动知识引导"},
    "sleep_guide": {"domain": "sleep", "desc": "睡眠知识引导"},
    "emotion_support": {"domain": "mental", "desc": "情绪支持（非诊断）"},
    "tcm_wellness": {"domain": "tcm", "desc": "中医养生知识"},
    "motivation_support": {"domain": "mental", "desc": "动机激发支持"},
    "crisis_responder": {"domain": "safety", "desc": "危机响应（转介）"},
    "habit_tracker": {"domain": "general", "desc": "习惯追踪助手"},
    "community_guide": {"domain": "social", "desc": "社区引导助手"},
    "onboarding_guide": {"domain": "general", "desc": "新手引导 (TrustGuide)"},
    "content_recommender": {"domain": "general", "desc": "内容推荐助手"},
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
