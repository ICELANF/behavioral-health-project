"""
Phase 3 — base.py 补丁说明

在 core/agents/base.py 中需要追加:

1. AgentDomain 新增 3 个:

    class AgentDomain(str, Enum):
        ...
        # Phase 3 新增
        HEALTH_ASSISTANT = "health_assistant"
        HABIT_TRACKER = "habit_tracker"
        ONBOARDING_GUIDE = "onboarding_guide"

2. AGENT_BASE_WEIGHTS 新增:

    AGENT_BASE_WEIGHTS.update({
        "health_assistant": 0.65,
        "habit_tracker": 0.6,
        "onboarding_guide": 0.7,
    })

3. DOMAIN_CORRELATIONS 新增:

    DOMAIN_CORRELATIONS.update({
        "health_assistant": ["nutrition", "tcm", "exercise", "sleep"],
        "habit_tracker": ["behavior_rx", "motivation"],
        "onboarding_guide": ["trust_guide", "motivation", "health_assistant"],
    })

实施方式: str_replace 工具执行以下 3 处修改
"""

# ── 以下为 str_replace 操作的精确参数 ──

# 操作 1: AgentDomain 追加
PATCH_1_OLD = '''    XZB_EXPERT = "xzb_expert"'''
PATCH_1_NEW = '''    XZB_EXPERT = "xzb_expert"
    # Phase 3 新增: 用户层 Agent
    HEALTH_ASSISTANT = "health_assistant"
    HABIT_TRACKER = "habit_tracker"
    ONBOARDING_GUIDE = "onboarding_guide"'''

# 操作 2: AGENT_BASE_WEIGHTS 追加
PATCH_2_OLD = '''    "xzb_expert": 0.95,
}'''
PATCH_2_NEW = '''    "xzb_expert": 0.95,
    # Phase 3 新增
    "health_assistant": 0.65,
    "habit_tracker": 0.6,
    "onboarding_guide": 0.7,
}'''

# 操作 3: DOMAIN_CORRELATIONS 追加
PATCH_3_OLD = '''    "vision":       ["sleep", "exercise", "behavior_rx", "nutrition"],
}'''
PATCH_3_NEW = '''    "vision":       ["sleep", "exercise", "behavior_rx", "nutrition"],
    # Phase 3 新增
    "health_assistant": ["nutrition", "tcm", "exercise", "sleep"],
    "habit_tracker":    ["behavior_rx", "motivation"],
    "onboarding_guide": ["trust_guide", "motivation", "health_assistant"],
}'''
