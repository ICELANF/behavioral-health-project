"""
中医骨科康复 — API路由注册

将5个新Agent注册到现有路由体系:
  - /v1/assistant/agents 用户层列表 → 追加 #29 #30
  - /v1/agent/agents 教练层列表 → 追加 #31 #32 #33
  - 网关授权矩阵扩展 (19→24端点)

注: 本文件需集成到现有 app/routes/ 中
"""
from __future__ import annotations

from typing import Any

# ──────────────────────────────────────────────
# Agent 注册表扩展
# ──────────────────────────────────────────────

TCM_ORTHO_AGENT_REGISTRY = {
    # 用户层 (+2)
    "pain_relief_guide": {
        "id": 29,
        "name": "pain_relief_guide",
        "display_name": "疼痛自评引导",
        "layer": "用户",
        "domain": "tcm_ortho",
        "description": "疼痛自评引导+中医骨科科普+功法推荐+日常防护建议",
        "icon": "💆",
        "module": "app.agents.tcm_ortho_agents",
        "class_name": "PainReliefGuide",
        "review_required": False,
        "dependencies": ["RAGPipeline", "LLM", "PainScaleEngine"],
        "safety_rules": "禁止诊断/开方; 红旗症状→转介; 边界词→引导就医",
    },
    "rehab_exercise_guide": {
        "id": 30,
        "name": "rehab_exercise_guide",
        "display_name": "康复运动指导",
        "layer": "用户",
        "domain": "rehab_move",
        "description": "康复运动视频/图文指导+八段锦/太极/易筋经功法套路+打卡追踪",
        "icon": "🧘",
        "module": "app.agents.tcm_ortho_agents",
        "class_name": "RehabExerciseGuide",
        "review_required": False,
        "dependencies": ["RAGPipeline", "LLM", "DB(habit_logs)"],
        "safety_rules": "运动中疼痛加剧→停止; 术后期→医嘱优先",
    },
    # 教练层 (+3)
    "tcm_ortho_expert": {
        "id": 31,
        "name": "tcm_ortho_expert",
        "display_name": "中医骨伤科专家",
        "layer": "教练",
        "domain": "tcm_ortho_pro",
        "description": "中医骨伤科辨证分析+经络穴位处方+推拿手法方案+中药外用方",
        "icon": "🏥",
        "module": "app.agents.tcm_ortho_expert_agents",
        "class_name": "TCMOrthoExpert",
        "review_required": True,
        "dependencies": ["LLM", "TCMOrthoKB", "PainAssessEngine"],
        "safety_rules": "骨折/脱位→影像先行; 神经损伤→转诊; 孕妇禁用穴位",
    },
    "pain_management_expert": {
        "id": 32,
        "name": "pain_management_expert",
        "display_name": "疼痛管理专家",
        "layer": "教练",
        "domain": "pain_mgmt",
        "description": "多维疼痛评估(NRS/VAS/PCS/PSEQ)+中西结合镇痛+慢性疼痛管理路径",
        "icon": "🎯",
        "module": "app.agents.tcm_ortho_expert_agents",
        "class_name": "PainManagementExpert",
        "review_required": True,
        "dependencies": ["LLM", "PainAssessEngine", "BehaviorRx"],
        "safety_rules": "VAS≥8→即时转诊; 阿片类依赖→警报; 感觉异常→神内",
    },
    "ortho_rehab_planner": {
        "id": 33,
        "name": "ortho_rehab_planner",
        "display_name": "骨科康复规划师",
        "layer": "教练",
        "domain": "ortho_rehab",
        "description": "骨科康复方案编制(1-12周分期)+运动处方与功法融合+康复进度评估",
        "icon": "📋",
        "module": "app.agents.tcm_ortho_expert_agents",
        "class_name": "OrthoRehabPlanner",
        "review_required": True,
        "dependencies": ["LLM", "StageEngine", "RehabProtocolKB"],
        "safety_rules": "康复停滞/恶化→升级; 术后早期→严格医嘱约束",
    },
}


# ──────────────────────────────────────────────
# 网关授权矩阵扩展
# ──────────────────────────────────────────────

GATEWAY_EXTENSIONS = {
    # 新增5个Agent专用端点
    "/v1/assistant/pain-relief/{user_id}/assess": {
        "method": "POST",
        "function": "用户疼痛自评提交",
        "auth": {"Admin": True, "Coach(绑定)": True, "Coach(未绑定)": False,
                 "Grower": True, "Observer": False},
        "masking": "L2(脱敏输出)",
    },
    "/v1/assistant/rehab-exercise/{user_id}/checkin": {
        "method": "POST",
        "function": "康复运动打卡",
        "auth": {"Admin": True, "Coach(绑定)": True, "Coach(未绑定)": False,
                 "Grower": True, "Observer": False},
        "masking": "L3(聚合)",
    },
    "/v1/gateway/patient/{id}/pain-history": {
        "method": "GET",
        "function": "疼痛评估历史",
        "auth": {"Admin": True, "Coach(绑定)": True, "Coach(未绑定)": False,
                 "Grower": False, "Observer": False},
        "masking": "L2(脱敏)",
    },
    "/v1/gateway/patient/{id}/rehab-plan": {
        "method": "GET",
        "function": "康复方案详情",
        "auth": {"Admin": True, "Coach(绑定)": True, "Coach(未绑定)": False,
                 "Grower": False, "Observer": False},
        "masking": "L1(完整)",
    },
    "/v1/gateway/patient/{id}/syndrome-records": {
        "method": "GET",
        "function": "中医辨证记录",
        "auth": {"Admin": True, "Coach(绑定)": True, "Coach(未绑定)": False,
                 "Grower": False, "Observer": False},
        "masking": "L1(完整)",
    },
}


def get_user_layer_agents() -> list[dict]:
    """返回用户层Agent列表 (12→14)"""
    return [
        v for v in TCM_ORTHO_AGENT_REGISTRY.values()
        if v["layer"] == "用户"
    ]


def get_coach_layer_agents() -> list[dict]:
    """返回教练层Agent列表 (16→19)"""
    return [
        v for v in TCM_ORTHO_AGENT_REGISTRY.values()
        if v["layer"] == "教练"
    ]


def get_all_new_agents() -> dict[str, dict]:
    """返回所有新增Agent注册信息"""
    return TCM_ORTHO_AGENT_REGISTRY


def get_gateway_extensions() -> dict[str, dict]:
    """返回网关授权矩阵扩展"""
    return GATEWAY_EXTENSIONS
