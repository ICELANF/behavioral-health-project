"""
V4.0 Governance API — 治理体系统一端点

包含:
  双轨晋级 (MEU-10): /v1/governance/dual-track/*
  防刷策略 (MEU-11): /v1/governance/anti-cheat/*
  责任追踪 (MEU-12): /v1/governance/responsibility/*
  治理仪表盘 (MEU-13): /v1/governance/dashboard
  约束退出 (MEU-19): /v1/governance/violations/*
  服务权益 (MEU-17): /v1/governance/service-rights

共 ~25 endpoints
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import User, GovernanceViolation, ROLE_LEVEL, ROLE_LEVEL_STR, ROLE_DISPLAY
from api.dependencies import get_current_user, require_admin, require_coach_or_admin

router = APIRouter(prefix="/api/v1/governance", tags=["governance"])


# ══════════════════════════════════════════════════════════
# Dual-Track Promotion (MEU-10)
# ══════════════════════════════════════════════════════════

@router.get("/dual-track/status")
def get_dual_track_status(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取双轨晋级状态 (4种状态)"""
    target_id = user_id if user_id else current_user.id
    from core.dual_track_engine import PROMOTION_THRESHOLDS
    user = db.query(User).filter(User.id == target_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    current_level = ROLE_DISPLAY.get(user.role, "L0")
    level_map = {"L0": "L0_TO_L1", "L1": "L1_TO_L2", "L2": "L2_TO_L3",
                 "L3": "L3_TO_L4", "L4": "L4_TO_L5"}
    promo_key = level_map.get(current_level)
    threshold = PROMOTION_THRESHOLDS.get(promo_key) if promo_key else None
    return {
        "user_id": target_id,
        "current_level": current_level,
        "promotion_key": promo_key,
        "state": "max_level" if not promo_key else "pending_check",
        "target_level": threshold.to_level.value if threshold else None,
        "ceremony_name": threshold.growth.ceremony_name if threshold else None,
        "ceremony_emoji": threshold.growth.ceremony_emoji if threshold else None,
    }


@router.get("/dual-track/gap-analysis")
def get_gap_analysis(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取晋级差距分析报告"""
    target_id = user_id if user_id else current_user.id
    from core.dual_track_engine import PROMOTION_THRESHOLDS
    user = db.query(User).filter(User.id == target_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    current_level = ROLE_DISPLAY.get(user.role, "L0")
    level_map = {"L0": "L0_TO_L1", "L1": "L1_TO_L2", "L2": "L2_TO_L3",
                 "L3": "L3_TO_L4", "L4": "L4_TO_L5"}
    promo_key = level_map.get(current_level)
    threshold = PROMOTION_THRESHOLDS.get(promo_key) if promo_key else None
    if not threshold:
        return {"user_id": target_id, "current_level": current_level, "gaps": [], "message": "已达最高等级"}
    return {
        "user_id": target_id,
        "current_level": current_level,
        "target_level": threshold.to_level.value,
        "points_required": {"growth": threshold.points.growth, "contribution": threshold.points.contribution, "influence": threshold.points.influence},
        "growth_requirements": {
            "capability": threshold.growth.capability_requirements,
            "exam": threshold.growth.exam_requirements,
            "behavior": threshold.growth.behavior_requirements,
            "ethics": threshold.growth.ethics_requirements,
            "min_period_months": threshold.growth.min_period_months,
            "peer_total_required": threshold.growth.peer_req.total_required,
        },
    }


@router.get("/dual-track/thresholds")
def get_promotion_thresholds(current_user: User = Depends(get_current_user)):
    """获取各级别晋级门槛"""
    from core.dual_track_engine import PROMOTION_THRESHOLDS
    levels = []
    for key, threshold in PROMOTION_THRESHOLDS.items():
        levels.append({
            "promotion_key": key,
            "from_level": threshold.from_level.value,
            "to_level": threshold.to_level.value,
            "ceremony_name": threshold.growth.ceremony_name,
            "ceremony_emoji": threshold.growth.ceremony_emoji,
            "points_thresholds": {
                "growth": threshold.points.growth,
                "contribution": threshold.points.contribution,
                "influence": threshold.points.influence,
            },
            "companions_required": threshold.growth.peer_req.total_required,
            "min_period_months": threshold.growth.min_period_months,
        })
    return {"levels": levels}


# ══════════════════════════════════════════════════════════
# Anti-Cheat (MEU-11)
# ══════════════════════════════════════════════════════════

@router.get("/anti-cheat/check")
def check_point_validity(
    action: str,
    base_points: int = 10,
    quality: str = "normal",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """检查积分获取是否合规 (综合6策略)"""
    from core.anti_cheat_engine import AntiCheatEngine
    engine = AntiCheatEngine(db)
    return engine.validate_point_award(current_user.id, action, base_points, quality)


@router.get("/anti-cheat/daily-caps")
def get_daily_caps(current_user: User = Depends(get_current_user)):
    """获取各行为的每日积分上限"""
    from core.anti_cheat_engine import DAILY_CAPS
    return {"daily_caps": DAILY_CAPS}


@router.get("/anti-cheat/events")
def get_anti_cheat_events(
    user_id: Optional[int] = None,
    limit: int = 20,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """获取防刷事件记录 (管理员)"""
    from core.anti_cheat_engine import AntiCheatEngine
    engine = AntiCheatEngine(db)
    target_id = user_id if user_id else current_user.id
    return engine.get_user_events(target_id, limit)


@router.get("/anti-cheat/anomaly-scan")
def scan_anomalies(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """对指定用户执行异常扫描 (管理员)"""
    from core.anti_cheat_engine import AntiCheatEngine
    engine = AntiCheatEngine(db)
    return engine.detect_anomaly(user_id)


# ══════════════════════════════════════════════════════════
# Responsibility Tracking (MEU-12)
# ══════════════════════════════════════════════════════════

@router.get("/responsibility/my-metrics")
def get_my_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的责任指标状态"""
    from core.responsibility_tracker import ResponsibilityTracker
    tracker = ResponsibilityTracker()
    return tracker.get_user_metrics(current_user.id)


@router.get("/responsibility/user-metrics/{user_id}")
def get_user_metrics(
    user_id: int,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    """获取指定用户的责任指标 (教练/管理员)"""
    from core.responsibility_tracker import ResponsibilityTracker
    tracker = ResponsibilityTracker()
    return tracker.get_user_metrics(user_id)


class MetricRecordRequest(BaseModel):
    user_id: int
    metric_code: str
    value: float


@router.post("/responsibility/record")
def record_metric(
    req: MetricRecordRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """记录责任指标数据 (管理员/系统)"""
    from core.responsibility_tracker import ResponsibilityTracker
    tracker = ResponsibilityTracker()
    result = tracker.record_metric(req.user_id, req.metric_code, req.value)
    db.commit()
    return result


@router.get("/responsibility/definitions")
def get_metric_definitions(current_user: User = Depends(get_current_user)):
    """获取所有责任指标定义 (按角色分组)"""
    from core.responsibility_tracker import ResponsibilityTracker, METRIC_DEFINITIONS
    return ResponsibilityTracker(None).get_all_definitions()


# ══════════════════════════════════════════════════════════
# Governance Dashboard (MEU-13)
# ══════════════════════════════════════════════════════════

@router.get("/dashboard")
def get_governance_dashboard(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """治理健康仪表盘 (管理员)"""
    from core.responsibility_tracker import ResponsibilityTracker
    tracker = ResponsibilityTracker()
    health = tracker.get_all_registry_stats()

    # Add governance violations summary
    from sqlalchemy import func
    thirty_days_ago = date.today() - timedelta(days=30)
    violations = db.query(
        GovernanceViolation.severity,
        func.count(GovernanceViolation.id),
    ).filter(
        GovernanceViolation.created_at >= thirty_days_ago.isoformat(),
    ).group_by(GovernanceViolation.severity).all()
    violation_counts = {s: c for s, c in violations}

    # User role distribution
    role_counts = db.query(
        User.role, func.count(User.id),
    ).group_by(User.role).all()
    roles = {r.value if hasattr(r, 'value') else r: c for r, c in role_counts}

    return {
        "responsibility_health": health,
        "violations_30d": {
            "light": violation_counts.get("light", 0),
            "moderate": violation_counts.get("moderate", 0),
            "severe": violation_counts.get("severe", 0),
            "ethics": violation_counts.get("ethics", 0),
        },
        "role_distribution": roles,
    }


# ══════════════════════════════════════════════════════════
# Constraint & Exit (MEU-19)
# ══════════════════════════════════════════════════════════

class ViolationRequest(BaseModel):
    user_id: int
    violation_type: str
    severity: str = "light"
    description: Optional[str] = None
    point_penalty: int = 0
    action_taken: Optional[str] = None


@router.post("/violations/record")
def record_violation(
    req: ViolationRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """记录治理违规 (管理员)"""
    # Check 3-month protection period
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # Protection period check (new promotion within 3 months)
    existing = db.query(GovernanceViolation).filter(
        GovernanceViolation.user_id == req.user_id,
        GovernanceViolation.protection_until != None,
        GovernanceViolation.protection_until >= date.today(),
    ).first()

    protection_active = False
    if req.severity == "light":
        # Check for first-time protection
        past_violations = db.query(GovernanceViolation).filter(
            GovernanceViolation.user_id == req.user_id,
        ).count()
        if past_violations == 0:
            protection_active = True

    violation = GovernanceViolation(
        user_id=req.user_id,
        violation_type=req.violation_type,
        severity=req.severity,
        description=req.description,
        point_penalty=0 if protection_active else req.point_penalty,
        action_taken="protection_period_exempt" if protection_active else req.action_taken,
    )
    db.add(violation)
    db.commit()

    return {
        "id": violation.id,
        "severity": violation.severity,
        "point_penalty": violation.point_penalty,
        "protection_active": protection_active,
        "message": "新晋级3月保护期, 首次免罚" if protection_active else None,
    }


@router.get("/violations/user/{user_id}")
def get_user_violations(
    user_id: int,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    """获取用户违规记录"""
    violations = db.query(GovernanceViolation).filter(
        GovernanceViolation.user_id == user_id,
    ).order_by(GovernanceViolation.created_at.desc()).limit(50).all()

    return [
        {
            "id": v.id,
            "type": v.violation_type,
            "severity": v.severity,
            "description": v.description,
            "point_penalty": v.point_penalty,
            "action_taken": v.action_taken,
            "resolved": v.resolved,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in violations
    ]


@router.put("/violations/{violation_id}/resolve")
def resolve_violation(
    violation_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """解决违规记录"""
    violation = db.query(GovernanceViolation).filter(
        GovernanceViolation.id == violation_id,
    ).first()
    if not violation:
        raise HTTPException(status_code=404, detail="违规记录不存在")

    from datetime import datetime
    violation.resolved = True
    violation.resolved_by = current_user.id
    violation.resolved_at = datetime.utcnow()
    db.commit()
    return {"id": violation_id, "resolved": True}


# ══════════════════════════════════════════════════════════
# Service Rights Matrix (MEU-17)
# ══════════════════════════════════════════════════════════

# Service rights matrix from Sheet ⑤
SERVICE_RIGHTS = {
    "browse_public": {"min_level": 0, "label": "T1公开科普/案例故事"},
    "browse_knowledge": {"min_level": 1, "label": "公开知识库检索"},
    "learning_t2": {"min_level": 2, "label": "T2健康内容学习"},
    "learning_t3": {"min_level": 3, "label": "T3成长内容"},
    "learning_t4": {"min_level": 5, "label": "T4管理/专业内容"},
    "assessment_trial": {"min_level": 1, "label": "体验版HF-20(限1次)", "trial": True},
    "assessment_full": {"min_level": 2, "label": "完整行为评估"},
    "ai_trial": {"min_level": 1, "label": "AI体验对话(限3轮)", "trial": True},
    "ai_full": {"min_level": 2, "label": "12个专业Agent完整对话"},
    "ai_crisis": {"min_level": 2, "label": "危机干预Agent"},
    "ai_expert": {"min_level": 4, "label": "4个专家Agent(BehaviorRx)"},
    "ai_custom_create": {"min_level": 5, "label": "自定义Agent创建"},
    "ai_marketplace": {"min_level": 5, "label": "Agent市场发布/安装"},
    "ai_composition": {"min_level": 6, "label": "多Agent组合编排"},
    "health_data": {"min_level": 2, "label": "设备绑定+7类数据录入"},
    "micro_action": {"min_level": 2, "label": "每日微行动+打卡"},
    "challenge": {"min_level": 2, "label": "挑战参加"},
    "program": {"min_level": 2, "label": "监测方案报名"},
    "behavior_rx": {"min_level": 4, "label": "行为处方(为学员)"},
    "incentive": {"min_level": 2, "label": "签到/徽章/里程碑"},
    "content_submit": {"min_level": 3, "label": "内容投稿"},
    "content_publish": {"min_level": 4, "label": "内容发布管理"},
    "rag_ingest": {"min_level": 4, "label": "知识灌注(RAG)"},
    "coach_workbench": {"min_level": 4, "label": "教练工作台"},
    "expert_studio": {"min_level": 5, "label": "白标工作室"},
    "supervision": {"min_level": 5, "label": "督导中心"},
    "admin_panel": {"min_level": 99, "label": "管理面板"},
}


@router.get("/service-rights")
def get_service_rights(
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的服务权益列表"""
    role = current_user.role.value if hasattr(current_user.role, 'value') else current_user.role
    user_level = ROLE_LEVEL_STR.get(role, 1)

    rights = []
    for key, right in SERVICE_RIGHTS.items():
        min_level = right["min_level"]
        accessible = user_level >= min_level
        rights.append({
            "feature": key,
            "label": right["label"],
            "accessible": accessible,
            "min_level": min_level,
            "trial": right.get("trial", False),
            "unlock_hint": f"升级到L{min_level}解锁" if not accessible else None,
        })

    accessible_count = sum(1 for r in rights if r["accessible"])
    return {
        "user_level": user_level,
        "role": role,
        "total_features": len(rights),
        "accessible": accessible_count,
        "locked": len(rights) - accessible_count,
        "rights": rights,
    }


@router.get("/service-rights/check/{feature}")
def check_service_right(
    feature: str,
    current_user: User = Depends(get_current_user),
):
    """检查当前用户是否有权访问某功能"""
    right = SERVICE_RIGHTS.get(feature)
    if not right:
        raise HTTPException(status_code=404, detail=f"未知功能: {feature}")

    role = current_user.role.value if hasattr(current_user.role, 'value') else current_user.role
    user_level = ROLE_LEVEL_STR.get(role, 1)
    accessible = user_level >= right["min_level"]

    return {
        "feature": feature,
        "accessible": accessible,
        "user_level": user_level,
        "required_level": right["min_level"],
        "trial": right.get("trial", False),
    }


# ══════════════════════════════════════════════════════════
# Four-Companion Tracking (MEU-15)
# ══════════════════════════════════════════════════════════

@router.get("/companions/overview")
def get_companion_overview(
    user_id: Optional[int] = None,
    target_level: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取四同道者追踪概览"""
    target_id = user_id if user_id else current_user.id
    from core.companion_tracker import CompanionTracker
    tracker = CompanionTracker(db)
    return tracker.get_companion_overview(target_id, target_level)


@router.get("/companions/prereq-check")
def check_companion_prereq(
    target_level: int,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """检查晋级同道者前置条件"""
    target_id = user_id if user_id else current_user.id
    from core.companion_tracker import CompanionTracker
    tracker = CompanionTracker(db)
    return tracker.check_promotion_companion_prereq(target_id, target_level)


@router.get("/companions/quality-requirements")
def get_quality_requirements(current_user: User = Depends(get_current_user)):
    """获取各级别的同道者质量要求"""
    from core.companion_tracker import COMPANION_QUALITY_REQS
    levels = []
    for target_level, reqs in COMPANION_QUALITY_REQS.items():
        levels.append({
            "target_level": target_level,
            "required_count": reqs["count"],
            "quality_rules": reqs["quality_rules"],
        })
    return {"levels": levels}


# ══════════════════════════════════════════════════════════
# Observer Tiered Access (MEU-16)
# ══════════════════════════════════════════════════════════

# Observer access tiers (free-browse → registered → trial → converted)
OBSERVER_TIERS = {
    "free_browse": {
        "label": "免费浏览",
        "features": ["browse_public"],
        "limits": {},
    },
    "registered": {
        "label": "已注册观察员",
        "features": ["browse_public", "browse_knowledge", "assessment_trial", "ai_trial"],
        "limits": {
            "assessment_trial": 1,  # 限1次
            "ai_trial": 3,          # 限3轮
        },
    },
}


@router.get("/observer/tier")
def get_observer_tier(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取观察员的访问层级"""
    role = current_user.role.value if hasattr(current_user.role, 'value') else current_user.role
    if role != "observer":
        user_level = ROLE_LEVEL_STR.get(role, 1)
        return {
            "user_id": current_user.id,
            "tier": "full_access",
            "role": role,
            "user_level": user_level,
            "message": "非观察员，拥有完整访问权限",
        }

    # Check if observer has completed registration profile
    has_profile = bool(current_user.email and current_user.username)
    tier = "registered" if has_profile else "free_browse"
    tier_info = OBSERVER_TIERS[tier]

    # Check trial usage
    trial_usage = {}
    from core.models import JourneyState
    journey = db.query(JourneyState).filter(
        JourneyState.user_id == current_user.id,
    ).first()

    trial_usage["assessment_used"] = 0
    trial_usage["ai_dialog_used"] = journey.observer_dialog_count if journey else 0

    return {
        "user_id": current_user.id,
        "tier": tier,
        "tier_label": tier_info["label"],
        "features": tier_info["features"],
        "limits": tier_info["limits"],
        "trial_usage": trial_usage,
        "can_trial_assessment": trial_usage["assessment_used"] < tier_info["limits"].get("assessment_trial", 0) if tier == "registered" else False,
        "can_trial_ai": trial_usage["ai_dialog_used"] < tier_info["limits"].get("ai_trial", 0) if tier == "registered" else False,
    }


@router.post("/observer/use-trial")
def use_observer_trial(
    trial_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """消耗观察员体验次数 (assessment_trial / ai_trial)"""
    role = current_user.role.value if hasattr(current_user.role, 'value') else current_user.role
    if role != "observer":
        raise HTTPException(status_code=400, detail="非观察员无需体验次数")

    if trial_type not in ("assessment_trial", "ai_trial"):
        raise HTTPException(status_code=400, detail="无效的体验类型")

    from core.models import JourneyState
    journey = db.query(JourneyState).filter(
        JourneyState.user_id == current_user.id,
    ).first()
    if not journey:
        journey = JourneyState(user_id=current_user.id)
        db.add(journey)
        db.flush()

    limit = OBSERVER_TIERS["registered"]["limits"].get(trial_type, 0)

    if trial_type == "ai_trial":
        current_count = journey.observer_dialog_count or 0
        if current_count >= limit:
            raise HTTPException(status_code=429, detail=f"AI体验对话已用完({limit}轮)")
        journey.observer_dialog_count = current_count + 1
        db.commit()
        return {"trial_type": trial_type, "used": current_count + 1, "limit": limit}
    else:
        # assessment_trial tracked via assessment records
        db.commit()
        return {"trial_type": trial_type, "used": 1, "limit": limit}


# ══════════════════════════════════════════════════════════
# Agent Double-Layer Separation (MEU-18)
# ══════════════════════════════════════════════════════════

# User layer: 12 health assistants (all users L1+)
USER_LAYER_AGENTS = [
    "metabolic", "sleep", "emotion", "motivation", "coaching",
    "nutrition", "exercise", "tcm", "crisis",
    "behavior_rx", "weight", "cardiac_rehab",
]

# Coach layer: professional agents (L3+ only)
COACH_LAYER_AGENTS = [
    "metabolic", "sleep", "emotion", "motivation", "coaching",
    "nutrition", "exercise", "tcm", "crisis",
    "behavior_rx", "weight", "cardiac_rehab",
    # Expert-specific agents (dynamic from templates)
]

# Expert-only agents (L5+ only)
EXPERT_LAYER_FEATURES = [
    "agent_custom_create", "agent_marketplace", "agent_composition",
]


@router.get("/agent-layer")
def get_agent_layer(
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的Agent访问层级"""
    role = current_user.role.value if hasattr(current_user.role, 'value') else current_user.role
    user_level = ROLE_LEVEL_STR.get(role, 1)

    if user_level >= 5:  # promoter/master
        layer = "expert"
        agents = COACH_LAYER_AGENTS
        extra_features = EXPERT_LAYER_FEATURES
    elif user_level >= 4:  # coach
        layer = "coach"
        agents = COACH_LAYER_AGENTS
        extra_features = []
    elif user_level >= 2:  # grower/sharer
        layer = "user"
        agents = USER_LAYER_AGENTS
        extra_features = []
    elif user_level == 1:  # observer
        layer = "observer"
        agents = []  # No direct agent access (only trial via /observer/use-trial)
        extra_features = []
    else:
        layer = "none"
        agents = []
        extra_features = []

    return {
        "user_id": current_user.id,
        "role": role,
        "user_level": user_level,
        "layer": layer,
        "available_agents": agents,
        "extra_features": extra_features,
        "can_create_agent": user_level >= 5,
        "can_publish_marketplace": user_level >= 5,
        "can_compose_agents": user_level >= 6,
    }


@router.get("/agent-layer/check/{agent_id}")
def check_agent_access(
    agent_id: str,
    current_user: User = Depends(get_current_user),
):
    """检查当前用户是否可以访问指定Agent"""
    role = current_user.role.value if hasattr(current_user.role, 'value') else current_user.role
    user_level = ROLE_LEVEL_STR.get(role, 1)

    # Crisis agent always accessible for L2+
    if agent_id == "crisis" and user_level >= 2:
        return {"agent_id": agent_id, "accessible": True, "reason": "crisis_always_allowed"}

    # Observer: no direct agent access
    if user_level <= 1:
        return {"agent_id": agent_id, "accessible": False, "reason": "observer_no_agent_access"}

    # User layer (L2-L3): only user-layer agents
    if user_level <= 3:
        accessible = agent_id in USER_LAYER_AGENTS
        return {
            "agent_id": agent_id,
            "accessible": accessible,
            "reason": "user_layer" if accessible else "requires_coach_level",
        }

    # Coach+ layer: all agents
    return {"agent_id": agent_id, "accessible": True, "reason": "coach_or_above"}


# ══════════════════════════════════════════════════════════
# Self-Audit Avoidance Engine (MEU-20)
# ══════════════════════════════════════════════════════════

class SelfAuditCheckRequest(BaseModel):
    content_creator_id: int
    reviewer_id: int
    content_type: str = "general"
    risk_level: str = "low"


@router.post("/self-audit/check")
def check_self_audit(
    req: SelfAuditCheckRequest,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    """
    自审回避检查: creator_id == reviewer_id → 按风险级别处理。
    高风险 → 必须换人审核;
    中风险 → 允许但标记;
    低风险 → 允许并附免责声明。
    """
    is_self_audit = req.content_creator_id == req.reviewer_id

    if not is_self_audit:
        return {
            "self_audit": False,
            "allowed": True,
            "action": "proceed",
            "message": "非自审情况, 正常流程",
        }

    # Self-audit detected
    if req.risk_level in ("critical", "high"):
        return {
            "self_audit": True,
            "allowed": False,
            "action": "require_different_reviewer",
            "message": "高风险内容不允许自审, 请指派其他审核人",
            "risk_level": req.risk_level,
        }
    elif req.risk_level == "moderate":
        return {
            "self_audit": True,
            "allowed": True,
            "action": "allow_with_flag",
            "message": "中等风险内容自审已标记, 建议安排二次复核",
            "risk_level": req.risk_level,
            "requires_secondary_review": True,
        }
    else:
        return {
            "self_audit": True,
            "allowed": True,
            "action": "allow_with_disclaimer",
            "message": "低风险内容自审允许, 已附免责声明",
            "risk_level": req.risk_level,
            "disclaimer": "本内容由创作者自行审核, 平台不承担额外审核责任",
        }


@router.get("/self-audit/suggest-reviewer/{content_creator_id}")
def suggest_reviewer(
    content_creator_id: int,
    content_type: str = "general",
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    """为自审回避推荐替代审核人"""
    creator = db.query(User).filter(User.id == content_creator_id).first()
    if not creator:
        raise HTTPException(status_code=404, detail="创作者不存在")

    creator_role = creator.role.value if hasattr(creator.role, 'value') else creator.role
    creator_level = ROLE_LEVEL_STR.get(creator_role, 1)

    # Find users with same or higher level, excluding the creator
    from sqlalchemy import or_
    candidates = db.query(User).filter(
        User.id != content_creator_id,
        User.is_active == True,
        or_(
            User.role == "admin",
            User.role == "master",
            User.role == "promoter",
            User.role == "supervisor",
            User.role == "coach",
        ),
    ).limit(10).all()

    suggestions = []
    for c in candidates:
        c_role = c.role.value if hasattr(c.role, 'value') else c.role
        c_level = ROLE_LEVEL_STR.get(c_role, 1)
        if c_level >= creator_level:
            suggestions.append({
                "user_id": c.id,
                "username": c.username,
                "role": c_role,
                "level": c_level,
            })

    return {
        "content_creator_id": content_creator_id,
        "creator_role": creator_role,
        "suggested_reviewers": suggestions[:5],
        "total_available": len(suggestions),
    }


# ══════════════════════════════════════════════════════════
# CR-15: Governance Health-Check (审计修复)
# ══════════════════════════════════════════════════════════

from core.governance_health_check import GovernanceHealthCheckService


@router.get("/health-check", summary="治理健康度检查")
def governance_health_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """运行 6 维度治理健康度检查，返回综合报告"""
    service = GovernanceHealthCheckService(db)
    report = service.run_full_check()
    return {"status": "ok", "report": report}


@router.get("/health-check/history", summary="治理健康度历史")
def governance_health_check_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """查询治理健康度检查历史记录"""
    from core.models import ResponsibilityMetric
    metrics = db.query(ResponsibilityMetric).filter(
        ResponsibilityMetric.metric_type == "governance_health_check",
    ).order_by(
        ResponsibilityMetric.checked_at.desc()
    ).limit(limit).all()
    return {"count": len(metrics), "history": [
        {
            "id": m.id,
            "status": m.status,
            "score": m.value,
            "checked_at": m.checked_at.isoformat() if m.checked_at else None,
        }
        for m in metrics
    ]}
