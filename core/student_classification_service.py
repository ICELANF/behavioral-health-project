# -*- coding: utf-8 -*-
"""
学员多维分类服务
Student Multi-Dimensional Classification Service

无状态服务，接收批量学员数据，返回4维分类标签 + 复合优先级分数。
8次批量SQL查询(非N+1)，支持331+学员规模。

维度:
- 行为 behavior: precontemplation/contemplation/preparation/action/maintenance/relapse/growth/advocacy/unassessed
- 需求 needs: metabolic/emotional/nutrition/exercise/adherence/general
- 风险 risk: crisis/high/moderate/low/normal
- 活跃度 activity: highly_active/active/moderate/inactive/dormant
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, text as sa_text
from loguru import logger

from core.models import (
    User, BehavioralProfile, Assessment, JourneyState,
    DeviceAlert, UserLearningStats, DailyTask, MicroActionTask,
)


# ── 分类结果 ──

@dataclass
class StudentClassification:
    behavior: str = "unassessed"
    needs: str = "general"
    risk: str = "normal"
    activity: str = "dormant"
    priority_score: float = 0.0
    priority_bucket: str = "routine"
    risk_flags: list = field(default_factory=list)
    needs_detail: list = field(default_factory=list)


# ── 行为阶段映射: current_stage → behavior label ──

_STAGE_TO_BEHAVIOR = {
    "S0": "precontemplation",
    "S1": "contemplation",
    "S2": "preparation",
    "S3": "action",
    "S4": "maintenance",
    "S5": "relapse",
    "S6": "growth",
}

# ── bpt6_type → needs 映射 ──

_BPT6_TO_NEEDS = {
    "action": "exercise",
    "knowledge": "general",
    "emotion": "emotional",
    "relation": "adherence",
    "environment": "nutrition",
    "mixed": "general",
}

# ── 薄弱能力 → 需求详情映射 ──

_CAPACITY_WEAK_NEEDS = {
    "A2_资源": "资源不足",
    "T_时间": "时间管理",
    "M_动机": "动机不足",
    "C_信心": "信心不足",
    "A1_认知": "健康认知",
    "P_计划": "计划能力",
    "I_自我效能": "自我效能",
    "S_社会支持": "社会支持",
}

# ── 风险等级顺序 ──

_RISK_ORDER = {"crisis": 4, "high": 3, "moderate": 2, "low": 1, "normal": 0}
_RISK_LEVEL_MAP = {"R4": "crisis", "R3": "high", "R2": "moderate", "R1": "low", "R0": "normal"}

# ── 优先级评分权重 ──

_BEHAVIOR_SCORES = {
    "relapse": 100, "precontemplation": 80, "contemplation": 60,
    "preparation": 40, "action": 20, "maintenance": 10,
    "growth": 5, "advocacy": 0, "unassessed": 50,
}

_RISK_SCORES = {"crisis": 100, "high": 80, "moderate": 50, "low": 20, "normal": 0}

_ACTIVITY_SCORES = {
    "dormant": 100, "inactive": 70, "moderate": 40, "active": 10, "highly_active": 0,
}

_NEEDS_URGENCY = {
    "emotional": 80, "metabolic": 60, "adherence": 50,
    "nutrition": 30, "exercise": 20, "general": 0,
}


def classify_students_batch(db: Session, user_ids: list[int]) -> dict[int, StudentClassification]:
    """
    批量分类 — 8次SQL查询(非N+1)

    Returns: { user_id: StudentClassification }
    """
    if not user_ids:
        return {}

    result: dict[int, StudentClassification] = {uid: StudentClassification() for uid in user_ids}

    try:
        # ── 1. BehavioralProfiles ──
        profiles = _fetch_profiles(db, user_ids)

        # ── 2. Latest Assessments ──
        assessments = _fetch_latest_assessments(db, user_ids)

        # ── 3. Device alerts (7 days, unacknowledged) ──
        alert_counts = _fetch_alert_counts(db, user_ids)

        # ── 4. UserLearningStats ──
        learning_stats = _fetch_learning_stats(db, user_ids)

        # ── 5. Users (last_login_at) ──
        user_logins = _fetch_user_logins(db, user_ids)

        # ── 6. DailyTask completion (7 days) ──
        task_completion = _fetch_task_completion(db, user_ids)

        # ── 7. MicroAction completion (7 days) ──
        micro_completion = _fetch_micro_completion(db, user_ids)

        # ── Classify each student ──
        for uid in user_ids:
            cls = result[uid]
            bp = profiles.get(uid)
            assess = assessments.get(uid)
            alerts = alert_counts.get(uid, 0)
            stats = learning_stats.get(uid)
            login_dt = user_logins.get(uid)
            task_done = task_completion.get(uid, 0)
            micro_done = micro_completion.get(uid, 0)

            # -- Behavior dimension --
            cls.behavior = _classify_behavior(bp)

            # -- Needs dimension --
            cls.needs, cls.needs_detail = _classify_needs(bp)

            # -- Risk dimension --
            cls.risk, cls.risk_flags = _classify_risk(assess, bp, alerts)

            # -- Activity dimension --
            cls.activity = _classify_activity(
                login_dt, stats, task_done + micro_done,
            )

            # -- Priority score --
            cls.priority_score = _compute_priority(cls)
            cls.priority_bucket = _priority_bucket(cls.priority_score)

    except Exception as e:
        logger.error(f"classify_students_batch error: {e}")
        # Return defaults for all

    return result


# ============================================================
# Data fetchers (batch SQL)
# ============================================================

def _fetch_profiles(db: Session, ids: list[int]) -> dict[int, BehavioralProfile]:
    rows = db.query(BehavioralProfile).filter(
        BehavioralProfile.user_id.in_(ids)
    ).all()
    return {r.user_id: r for r in rows}


def _fetch_latest_assessments(db: Session, ids: list[int]) -> dict[int, Assessment]:
    """Get the most recent assessment per user via subquery."""
    from sqlalchemy import desc
    # Get all assessments for these users, ordered by date
    rows = db.query(Assessment).filter(
        Assessment.user_id.in_(ids)
    ).order_by(Assessment.user_id, desc(Assessment.created_at)).all()

    latest: dict[int, Assessment] = {}
    for r in rows:
        if r.user_id not in latest:
            latest[r.user_id] = r
    return latest


def _fetch_alert_counts(db: Session, ids: list[int]) -> dict[int, int]:
    """Count unresolved device alerts in the last 7 days."""
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    try:
        rows = db.query(
            DeviceAlert.user_id,
            func.count(DeviceAlert.id),
        ).filter(
            DeviceAlert.user_id.in_(ids),
            DeviceAlert.created_at >= seven_days_ago,
            DeviceAlert.resolved == False,
        ).group_by(DeviceAlert.user_id).all()
        return {r[0]: r[1] for r in rows}
    except Exception:
        return {}


def _fetch_learning_stats(db: Session, ids: list[int]) -> dict[int, UserLearningStats]:
    rows = db.query(UserLearningStats).filter(
        UserLearningStats.user_id.in_(ids)
    ).all()
    return {r.user_id: r for r in rows}


def _fetch_user_logins(db: Session, ids: list[int]) -> dict[int, Optional[datetime]]:
    rows = db.query(User.id, User.last_login_at).filter(User.id.in_(ids)).all()
    return {r[0]: r[1] for r in rows}


def _fetch_task_completion(db: Session, ids: list[int]) -> dict[int, int]:
    """Count completed daily tasks in the last 7 days."""
    seven_days_ago = (datetime.utcnow() - timedelta(days=7)).date()
    try:
        rows = db.query(
            DailyTask.user_id,
            func.count(DailyTask.id),
        ).filter(
            DailyTask.user_id.in_(ids),
            DailyTask.task_date >= seven_days_ago,
            DailyTask.done == True,
        ).group_by(DailyTask.user_id).all()
        return {r[0]: r[1] for r in rows}
    except Exception:
        return {}


def _fetch_micro_completion(db: Session, ids: list[int]) -> dict[int, int]:
    """Count completed micro-action tasks in the last 7 days."""
    seven_days_ago = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    try:
        rows = db.query(
            MicroActionTask.user_id,
            func.count(MicroActionTask.id),
        ).filter(
            MicroActionTask.user_id.in_(ids),
            MicroActionTask.scheduled_date >= seven_days_ago,
            MicroActionTask.status == "completed",
        ).group_by(MicroActionTask.user_id).all()
        return {r[0]: r[1] for r in rows}
    except Exception:
        return {}


# ============================================================
# Dimension classifiers
# ============================================================

def _classify_behavior(bp: Optional[BehavioralProfile]) -> str:
    if not bp or not bp.current_stage:
        return "unassessed"

    stage = bp.current_stage.value if hasattr(bp.current_stage, 'value') else str(bp.current_stage)
    behavior = _STAGE_TO_BEHAVIOR.get(stage, "unassessed")

    # agency_mode=active + S4+ → advocacy
    if bp.agency_mode == "active" and stage in ("S4", "S5", "S6"):
        behavior = "advocacy"

    return behavior


def _classify_needs(bp: Optional[BehavioralProfile]) -> tuple[str, list[str]]:
    if not bp:
        return "general", []

    needs_detail = []

    # From bpt6_type
    needs = _BPT6_TO_NEEDS.get(bp.bpt6_type or "", "general")

    # capacity_weak supplements
    weak_list = bp.capacity_weak or []
    for w in weak_list:
        label = _CAPACITY_WEAK_NEEDS.get(w, w)
        needs_detail.append(label)

    # Primary domains add detail
    domains = bp.primary_domains or []
    domain_labels = {
        "nutrition": "饮食控制", "exercise": "运动管理",
        "sleep": "睡眠改善", "emotion": "情绪调节",
        "stress": "压力管理", "glucose": "血糖管理",
        "weight": "体重管理", "cardiac": "心脏康复",
    }
    for d in domains[:3]:
        label = domain_labels.get(d, d)
        if label not in needs_detail:
            needs_detail.append(label)

    # Override: if emotional in domains, set needs to emotional
    if "emotion" in domains:
        needs = "emotional"
    elif "glucose" in domains or "nutrition" in domains:
        needs = "metabolic" if "glucose" in domains else "nutrition"

    return needs, needs_detail[:5]


def _classify_risk(
    assess: Optional[Assessment],
    bp: Optional[BehavioralProfile],
    alert_count: int,
) -> tuple[str, list[str]]:
    risk_flags = []

    # Base risk from assessment
    risk = "normal"
    if assess and assess.risk_level:
        rl = assess.risk_level.value if hasattr(assess.risk_level, 'value') else str(assess.risk_level)
        risk = _RISK_LEVEL_MAP.get(rl, "normal")

    # Unresolved device alerts → escalate one level
    if alert_count > 0:
        risk_flags.append(f"设备告警({alert_count}条)")
        current_order = _RISK_ORDER.get(risk, 0)
        if current_order < 4:
            escalated = {v: k for k, v in _RISK_ORDER.items()}.get(current_order + 1, risk)
            risk = escalated

    # BehavioralProfile risk_flags → at least moderate
    if bp and bp.risk_flags:
        flag_labels = {
            "dropout_risk": "流失风险", "relapse_risk": "回退风险",
            "crisis_risk": "危机风险", "noncompliance": "依从性差",
        }
        for f in bp.risk_flags:
            risk_flags.append(flag_labels.get(f, f))
        if _RISK_ORDER.get(risk, 0) < _RISK_ORDER["moderate"]:
            risk = "moderate"

    return risk, risk_flags


def _classify_activity(
    last_login: Optional[datetime],
    stats: Optional[UserLearningStats],
    completed_tasks_7d: int,
) -> str:
    now = datetime.utcnow()

    if not last_login:
        return "dormant"

    days_since_login = (now - last_login).days
    streak = stats.current_streak if stats else 0

    if days_since_login <= 7 and (days_since_login <= 2 or completed_tasks_7d >= 5) and streak >= 3:
        return "highly_active"
    if days_since_login <= 7 and (completed_tasks_7d >= 2 or streak >= 1):
        return "active"
    if days_since_login <= 14:
        return "moderate"
    if days_since_login <= 30:
        return "inactive"
    return "dormant"


# ============================================================
# Priority scoring
# ============================================================

def _compute_priority(cls: StudentClassification) -> float:
    b = _BEHAVIOR_SCORES.get(cls.behavior, 50)
    r = _RISK_SCORES.get(cls.risk, 0)
    a = _ACTIVITY_SCORES.get(cls.activity, 50)
    n = _NEEDS_URGENCY.get(cls.needs, 0)
    return round(b * 0.25 + r * 0.35 + a * 0.25 + n * 0.15, 1)


def _priority_bucket(score: float) -> str:
    if score >= 70:
        return "urgent"
    if score >= 45:
        return "important"
    if score >= 20:
        return "normal"
    return "routine"


# ============================================================
# Summary builder (for API response)
# ============================================================

def build_classification_summary(
    classifications: dict[int, StudentClassification],
) -> dict:
    """Build aggregate summary counts for all dimensions."""
    summary: dict[str, dict[str, int]] = {
        "by_behavior": {},
        "by_needs": {},
        "by_risk": {},
        "by_activity": {},
        "by_priority": {},
    }

    for cls in classifications.values():
        summary["by_behavior"][cls.behavior] = summary["by_behavior"].get(cls.behavior, 0) + 1
        summary["by_needs"][cls.needs] = summary["by_needs"].get(cls.needs, 0) + 1
        summary["by_risk"][cls.risk] = summary["by_risk"].get(cls.risk, 0) + 1
        summary["by_activity"][cls.activity] = summary["by_activity"].get(cls.activity, 0) + 1
        summary["by_priority"][cls.priority_bucket] = summary["by_priority"].get(cls.priority_bucket, 0) + 1

    return summary


def classification_to_dict(cls: StudentClassification) -> dict:
    """Serialize a StudentClassification to dict for API response."""
    return {
        "behavior": cls.behavior,
        "needs": cls.needs,
        "risk": cls.risk,
        "activity": cls.activity,
        "priority_score": cls.priority_score,
        "priority_bucket": cls.priority_bucket,
        "risk_flags": cls.risk_flags,
        "needs_detail": cls.needs_detail,
    }
