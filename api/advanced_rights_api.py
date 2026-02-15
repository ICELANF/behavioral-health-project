"""
V4.0 Advanced Service Rights API — L4/L5高级权益 (MEU-31)

L4 Promoter/Supervisor:
  - Agent creation & marketplace publish
  - Advanced analytics access
  - Supervision tools
  - Student group management

L5 Master:
  - Agent composition (multi-agent orchestration)
  - Platform-level configuration
  - Expert community leadership
  - Standards & curriculum design

Endpoints:
  GET  /my-rights           我的高级权益
  GET  /rights-catalog      权益目录
  GET  /agent-capabilities  Agent能力矩阵
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from core.models import User, ROLE_LEVEL_STR

router = APIRouter(prefix="/api/v1/advanced-rights", tags=["advanced-rights"])


# ── Rights Definitions ──────────────────────────

L4_RIGHTS = {
    "agent_management": {
        "label": "Agent管理",
        "features": [
            "create_agent",         # 创建自定义Agent
            "publish_marketplace",  # 发布到Agent市场
            "manage_templates",     # 管理Agent模板
            "view_agent_metrics",   # 查看Agent效果数据
        ],
    },
    "advanced_analytics": {
        "label": "高级分析",
        "features": [
            "student_deep_analytics", # 学员深度分析
            "cohort_analysis",        # 群体分析
            "behavior_pattern_report",# 行为模式报告
            "outcome_tracking",       # 干预效果追踪
        ],
    },
    "supervision_tools": {
        "label": "督导工具",
        "features": [
            "supervision_sessions",   # 督导会议管理
            "case_review_board",      # 案例评审看板
            "intern_coach_management",# 实习教练管理
            "quality_assessment",     # 质量评估
        ],
    },
    "student_group": {
        "label": "学员组管理",
        "features": [
            "caseload_management",    # 学员组管理
            "priority_sorting",       # 优先级排序
            "workload_monitoring",    # 工作量监控
            "batch_intervention",     # 批量干预
        ],
    },
}

L5_RIGHTS = {
    "agent_composition": {
        "label": "Agent编排",
        "features": [
            "compose_multi_agent",    # 多Agent编排
            "orchestration_design",   # 编排流程设计
            "cross_domain_fusion",    # 跨域Agent融合
            "composition_testing",    # 编排测试沙箱
        ],
    },
    "platform_config": {
        "label": "平台配置",
        "features": [
            "policy_rules_management",# 策略规则管理
            "safety_config",          # 安全配置
            "system_parameters",      # 系统参数调整
            "content_governance",     # 内容治理规则
        ],
    },
    "expert_community": {
        "label": "专家社区",
        "features": [
            "community_leadership",   # 社区领导
            "expert_mentoring",       # 专家指导
            "knowledge_curation",     # 知识策展
            "standard_setting",       # 标准制定
        ],
    },
    "curriculum_design": {
        "label": "课程设计",
        "features": [
            "curriculum_authoring",   # 课程编写
            "assessment_design",      # 评估设计
            "certification_programs", # 认证项目
            "training_materials",     # 培训材料
        ],
    },
}

# Agent capability matrix by role level
AGENT_CAPABILITY_MATRIX = {
    "observer": {
        "can_use": [],
        "can_create": False,
        "can_publish": False,
        "can_compose": False,
        "trial_agents": ["crisis"],
    },
    "grower": {
        "can_use": [
            "metabolic", "sleep", "emotion", "motivation", "coaching",
            "nutrition", "exercise", "tcm", "crisis",
            "behavior_rx", "weight", "cardiac_rehab",
            "journey_companion", "growth_reflection",
        ],
        "can_create": False,
        "can_publish": False,
        "can_compose": False,
    },
    "sharer": {
        "can_use": [
            "metabolic", "sleep", "emotion", "motivation", "coaching",
            "nutrition", "exercise", "tcm", "crisis",
            "behavior_rx", "weight", "cardiac_rehab",
            "journey_companion", "growth_reflection",
        ],
        "can_create": False,
        "can_publish": False,
        "can_compose": False,
    },
    "coach": {
        "can_use": [
            "metabolic", "sleep", "emotion", "motivation", "coaching",
            "nutrition", "exercise", "tcm", "crisis",
            "behavior_rx", "weight", "cardiac_rehab",
            "journey_companion", "growth_reflection", "coach_copilot",
        ],
        "can_create": False,
        "can_publish": False,
        "can_compose": False,
    },
    "promoter": {
        "can_use": "all",
        "can_create": True,
        "can_publish": True,
        "can_compose": False,
    },
    "master": {
        "can_use": "all",
        "can_create": True,
        "can_publish": True,
        "can_compose": True,
    },
}


@router.get("/my-rights")
def get_my_rights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的高级权益"""
    role = current_user.role.value if hasattr(current_user.role, 'value') else current_user.role
    level = ROLE_LEVEL_STR.get(role, 1)

    rights = {}
    if level >= 5:  # L4 promoter/supervisor
        rights.update(L4_RIGHTS)
    if level >= 6:  # L5 master
        rights.update(L5_RIGHTS)

    # Admin gets everything
    if level >= 99:
        rights.update(L4_RIGHTS)
        rights.update(L5_RIGHTS)

    agent_caps = AGENT_CAPABILITY_MATRIX.get(role, AGENT_CAPABILITY_MATRIX.get("grower", {}))

    return {
        "user_id": current_user.id,
        "role": role,
        "level": level,
        "rights": rights,
        "total_features": sum(len(r["features"]) for r in rights.values()),
        "agent_capabilities": agent_caps,
    }


@router.get("/rights-catalog")
def get_rights_catalog(
    current_user: User = Depends(get_current_user),
):
    """获取完整权益目录"""
    return {
        "L4_rights": L4_RIGHTS,
        "L5_rights": L5_RIGHTS,
        "l4_total_features": sum(len(r["features"]) for r in L4_RIGHTS.values()),
        "l5_total_features": sum(len(r["features"]) for r in L5_RIGHTS.values()),
    }


@router.get("/agent-capabilities")
def get_agent_capabilities(
    current_user: User = Depends(get_current_user),
):
    """获取Agent能力矩阵 (所有角色)"""
    return AGENT_CAPABILITY_MATRIX
