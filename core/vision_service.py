# -*- coding: utf-8 -*-
"""
VisionGuard 视力行为保护 — 核心服务

包含:
- 5 ORM 模型 (VisionExamRecord, VisionBehaviorLog, VisionBehaviorGoal, VisionGuardianBinding, VisionProfile)
- 行为评分引擎 (五维加权: 户外35/屏幕30/眼操10/叶黄素10/睡眠15)
- 风险评估: 结合检查数据 + 行为评分
- TTM 阶段感知即时反馈
- 监护人辅助函数
- 目标自动调整 (按 TTM 阶段)
- 周报生成
- 处方触发 (连续3天评分下降 → coach_push_queue, 遵守 AI→审核→推送铁律)
"""
from __future__ import annotations

import enum
import logging
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float, ForeignKey,
    Index, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Session, relationship
from sqlalchemy import text as sa_text

from core.models import Base, User

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════
# 枚举
# ══════════════════════════════════════════

class VisionRiskLevel(str, enum.Enum):
    NORMAL = "normal"
    WATCH = "watch"
    ALERT = "alert"
    URGENT = "urgent"


class VisionInputSource(str, enum.Enum):
    MANUAL = "manual"
    DEVICE_SYNC = "device_sync"
    GUARDIAN_INPUT = "guardian_input"
    COACH_INPUT = "coach_input"
    AI_INFERRED = "ai_inferred"


# ══════════════════════════════════════════
# ORM 模型
# ══════════════════════════════════════════

class VisionExamRecord(Base):
    """视力检查记录"""
    __tablename__ = "vision_exam_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exam_date = Column(Date, nullable=False)
    left_eye_sph = Column(Float, nullable=True)
    right_eye_sph = Column(Float, nullable=True)
    left_eye_cyl = Column(Float, nullable=True)
    right_eye_cyl = Column(Float, nullable=True)
    left_eye_axial_len = Column(Float, nullable=True)
    right_eye_axial_len = Column(Float, nullable=True)
    left_eye_va = Column(Float, nullable=True)
    right_eye_va = Column(Float, nullable=True)
    exam_type = Column(String(30), server_default="routine", nullable=False)
    examiner_name = Column(String(100), nullable=True)
    institution = Column(String(200), nullable=True)
    risk_level = Column(String(20), server_default="normal", nullable=False)
    notes = Column(Text, nullable=True)
    raw_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)
    updated_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)

    __table_args__ = (
        Index("idx_vision_exam_user_date", "user_id", "exam_date"),
        Index("idx_vision_exam_risk", "risk_level"),
    )


class VisionBehaviorLog(Base):
    """视力行为日志 — 每日一条 (UPSERT by user_id + log_date)"""
    __tablename__ = "vision_behavior_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    log_date = Column(Date, nullable=False)
    outdoor_minutes = Column(Integer, server_default="0", nullable=False)
    screen_sessions = Column(Integer, server_default="0", nullable=False)
    screen_total_minutes = Column(Integer, server_default="0", nullable=False)
    eye_exercise_done = Column(Boolean, server_default=sa_text("false"), nullable=False)
    lutein_intake_mg = Column(Float, server_default="0.0", nullable=False)
    sleep_minutes = Column(Integer, server_default="0", nullable=False)
    behavior_score = Column(Float, nullable=True)
    input_source = Column(String(20), server_default="manual", nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)
    updated_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "log_date", name="uq_vision_log_user_date"),
        Index("idx_vision_log_user_date", "user_id", "log_date"),
        Index("idx_vision_log_score", "behavior_score"),
    )


class VisionBehaviorGoal(Base):
    """视力行为目标 — 每用户一条"""
    __tablename__ = "vision_behavior_goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    outdoor_target_min = Column(Integer, server_default="120", nullable=False)
    screen_session_limit = Column(Integer, server_default="6", nullable=False)
    screen_daily_limit = Column(Integer, server_default="120", nullable=False)
    lutein_target_mg = Column(Float, server_default="10.0", nullable=False)
    sleep_target_min = Column(Integer, server_default="480", nullable=False)
    ttm_stage = Column(String(4), nullable=True)
    auto_adjust = Column(Boolean, server_default=sa_text("true"), nullable=False)
    created_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)
    updated_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)


class VisionGuardianBinding(Base):
    """监护人绑定关系 (C6: 替代 PARENT 角色, 任何角色可做监护人)"""
    __tablename__ = "vision_guardian_bindings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    guardian_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    relationship = Column(String(20), server_default="parent", nullable=False)
    notify_risk_threshold = Column(String(20), server_default="watch", nullable=False)
    can_input_behavior = Column(Boolean, server_default=sa_text("true"), nullable=False)
    is_active = Column(Boolean, server_default=sa_text("true"), nullable=False)
    created_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)
    deactivated_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("student_user_id", "guardian_user_id", name="uq_vision_guardian_pair"),
        Index("idx_vision_guardian_student", "student_user_id"),
        Index("idx_vision_guardian_guardian", "guardian_user_id"),
    )


class VisionProfile(Base):
    """视力专属扩展档案"""
    __tablename__ = "vision_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    is_vision_student = Column(Boolean, server_default=sa_text("true"), nullable=False)
    myopia_onset_age = Column(Integer, nullable=True)
    current_risk_level = Column(String(20), server_default="normal", nullable=False)
    ttm_vision_stage = Column(String(4), server_default="S0", nullable=False)
    last_exam_date = Column(Date, nullable=True)
    expert_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    enrolled_at = Column(DateTime, server_default=sa_text("now()"), nullable=False)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_vision_profile_user", "user_id"),
        Index("idx_vision_profile_risk", "current_risk_level"),
    )


# ══════════════════════════════════════════
# 辅助函数
# ══════════════════════════════════════════

def get_user_age(user: User) -> Optional[int]:
    """C7: 从 date_of_birth 计算年龄 (ZIP 用 user.age, 平台无此字段)"""
    dob = getattr(user, "date_of_birth", None)
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def get_or_create_goal(db: Session, user_id: int) -> VisionBehaviorGoal:
    """获取或创建用户的视力行为目标"""
    goal = db.query(VisionBehaviorGoal).filter(VisionBehaviorGoal.user_id == user_id).first()
    if not goal:
        goal = VisionBehaviorGoal(user_id=user_id)
        db.add(goal)
        db.flush()
    return goal


def get_or_create_profile(db: Session, user_id: int) -> VisionProfile:
    """获取或创建用户视力档案"""
    profile = db.query(VisionProfile).filter(VisionProfile.user_id == user_id).first()
    if not profile:
        profile = VisionProfile(user_id=user_id)
        db.add(profile)
        db.flush()
    return profile


# ══════════════════════════════════════════
# 评分引擎
# ══════════════════════════════════════════

# 五维权重
_W_OUTDOOR = 35
_W_SCREEN = 30
_W_EYE_EX = 10
_W_LUTEIN = 10
_W_SLEEP = 15


def calc_behavior_score(log: VisionBehaviorLog, goal: VisionBehaviorGoal) -> float:
    """
    五维加权评分 (0-100):
      户外(35) + 屏幕(30) + 眼操(10) + 叶黄素(10) + 睡眠(15)
    """
    # 1. 户外: 达标=满分, 线性衰减
    outdoor_target = goal.outdoor_target_min or 120
    outdoor_ratio = min((log.outdoor_minutes or 0) / outdoor_target, 1.0)
    s_outdoor = outdoor_ratio * _W_OUTDOOR

    # 2. 屏幕: 越少越好, 超标扣分
    screen_limit = goal.screen_daily_limit or 120
    screen_actual = log.screen_total_minutes or 0
    if screen_actual <= screen_limit:
        s_screen = _W_SCREEN
    else:
        over_ratio = min((screen_actual - screen_limit) / screen_limit, 1.0)
        s_screen = _W_SCREEN * (1 - over_ratio)

    # 3. 眼保健操: 做了=满分
    s_eye_ex = _W_EYE_EX if log.eye_exercise_done else 0

    # 4. 叶黄素: 达标=满分
    lutein_target = goal.lutein_target_mg or 10.0
    lutein_ratio = min((log.lutein_intake_mg or 0) / lutein_target, 1.0) if lutein_target > 0 else 1.0
    s_lutein = lutein_ratio * _W_LUTEIN

    # 5. 睡眠: 达标=满分
    sleep_target = goal.sleep_target_min or 480
    sleep_ratio = min((log.sleep_minutes or 0) / sleep_target, 1.0) if sleep_target > 0 else 1.0
    s_sleep = sleep_ratio * _W_SLEEP

    return round(s_outdoor + s_screen + s_eye_ex + s_lutein + s_sleep, 1)


# ══════════════════════════════════════════
# 风险评估
# ══════════════════════════════════════════

_RISK_LEVELS_ORDER = {
    VisionRiskLevel.NORMAL: 0,
    VisionRiskLevel.WATCH: 1,
    VisionRiskLevel.ALERT: 2,
    VisionRiskLevel.URGENT: 3,
}


def assess_vision_risk(db: Session, user_id: int) -> VisionRiskLevel:
    """
    综合风险评估 = max(检查数据风险, 行为评分风险)
    """
    risk = VisionRiskLevel.NORMAL

    # 1. 最近检查记录的风险
    latest_exam = (
        db.query(VisionExamRecord)
        .filter(VisionExamRecord.user_id == user_id)
        .order_by(VisionExamRecord.exam_date.desc())
        .first()
    )
    if latest_exam:
        # 球镜 < -6.0 → URGENT, < -3.0 → ALERT, < -0.5 → WATCH
        worst_sph = min(
            latest_exam.left_eye_sph or 0,
            latest_exam.right_eye_sph or 0,
        )
        if worst_sph < -6.0:
            risk = VisionRiskLevel.URGENT
        elif worst_sph < -3.0:
            risk = VisionRiskLevel.ALERT
        elif worst_sph < -0.5:
            risk = VisionRiskLevel.WATCH

        # 眼轴 > 26mm → 至少 ALERT
        worst_axial = max(
            latest_exam.left_eye_axial_len or 0,
            latest_exam.right_eye_axial_len or 0,
        )
        if worst_axial > 26.0:
            axial_risk = VisionRiskLevel.ALERT
            if _RISK_LEVELS_ORDER.get(axial_risk, 0) > _RISK_LEVELS_ORDER.get(risk, 0):
                risk = axial_risk

    # 2. 近7天行为评分 < 40 → 至少 WATCH, < 25 → ALERT
    recent_logs = (
        db.query(VisionBehaviorLog)
        .filter(
            VisionBehaviorLog.user_id == user_id,
            VisionBehaviorLog.log_date >= date.today() - timedelta(days=7),
        )
        .all()
    )
    if recent_logs:
        avg_score = sum((l.behavior_score or 0) for l in recent_logs) / len(recent_logs)
        if avg_score < 25:
            behavior_risk = VisionRiskLevel.ALERT
        elif avg_score < 40:
            behavior_risk = VisionRiskLevel.WATCH
        else:
            behavior_risk = VisionRiskLevel.NORMAL

        if _RISK_LEVELS_ORDER.get(behavior_risk, 0) > _RISK_LEVELS_ORDER.get(risk, 0):
            risk = behavior_risk

    return risk


# ══════════════════════════════════════════
# 即时反馈 (TTM 阶段感知)
# ══════════════════════════════════════════

_TTM_MESSAGES = {
    "S0": {  # 前意向
        "high": "今天做得不错！每一步都算数，坚持下去会看到变化的。",
        "mid": "有进步的空间，不过没关系，慢慢来就好。",
        "low": "今天的数据偏低，试试先从一件小事开始，比如出门走10分钟？",
    },
    "S1": {  # 意向
        "high": "太棒了！你已经开始行动了，保持这个势头！",
        "mid": "还不错，离目标越来越近了。今天试试减少一次看屏幕？",
        "low": "今天有点懈怠也没关系，明天是新的开始。",
    },
    "S2": {  # 准备
        "high": "你的坚持在发挥作用！视力保护就是这样一点点积累的。",
        "mid": "继续保持，可以关注一下户外时间是否达标。",
        "low": "今天分数有些低，回顾一下哪个维度还能改进？",
    },
    "S3": {  # 行动
        "high": "出色！你已经养成了很好的习惯，继续挑战自己！",
        "mid": "稳定进步中。试试把眼保健操加入日常？",
        "low": "偶尔的波动很正常，重要的是整体趋势向上。",
    },
    "S4": {  # 维持
        "high": "了不起的自律！你是视力保护的榜样。",
        "mid": "持续达标，非常稳定。看看能不能帮助同伴一起进步？",
        "low": "最近分数有些下降，是否生活节奏有变化？适当调整即可。",
    },
}


def build_instant_message(
    log: VisionBehaviorLog,
    score: float,
    goal: VisionBehaviorGoal,
    ttm_stage: Optional[str] = None,
) -> dict:
    """
    构建打卡即时反馈:
    - 总分 + 各维度完成度
    - TTM 阶段感知文案
    - 差距提示
    """
    stage = ttm_stage or "S0"
    stage_msgs = _TTM_MESSAGES.get(stage, _TTM_MESSAGES["S0"])

    if score >= 75:
        msg = stage_msgs["high"]
    elif score >= 45:
        msg = stage_msgs["mid"]
    else:
        msg = stage_msgs["low"]

    # 各维度完成度
    outdoor_pct = min(100, round((log.outdoor_minutes or 0) / max(goal.outdoor_target_min or 120, 1) * 100))
    screen_pct = min(100, round(max(0, 1 - (log.screen_total_minutes or 0) / max(goal.screen_daily_limit or 120, 1)) * 100))
    sleep_pct = min(100, round((log.sleep_minutes or 0) / max(goal.sleep_target_min or 480, 1) * 100))

    # 差距提示
    gaps = []
    if outdoor_pct < 60:
        remaining = (goal.outdoor_target_min or 120) - (log.outdoor_minutes or 0)
        gaps.append(f"户外还差 {max(0, remaining)} 分钟")
    if (log.screen_total_minutes or 0) > (goal.screen_daily_limit or 120):
        over = (log.screen_total_minutes or 0) - (goal.screen_daily_limit or 120)
        gaps.append(f"屏幕超标 {over} 分钟")
    if not log.eye_exercise_done:
        gaps.append("今天还没做眼保健操")

    return {
        "score": score,
        "message": msg,
        "ttm_stage": stage,
        "dimensions": {
            "outdoor_pct": outdoor_pct,
            "screen_pct": screen_pct,
            "eye_exercise": log.eye_exercise_done,
            "lutein_pct": min(100, round((log.lutein_intake_mg or 0) / max(goal.lutein_target_mg or 10, 0.1) * 100)),
            "sleep_pct": sleep_pct,
        },
        "gaps": gaps,
    }


# ══════════════════════════════════════════
# 监护人辅助
# ══════════════════════════════════════════

def get_guardian_students(db: Session, guardian_user_id: int) -> list[dict]:
    """查询监护人下的所有学生"""
    bindings = (
        db.query(VisionGuardianBinding)
        .filter(
            VisionGuardianBinding.guardian_user_id == guardian_user_id,
            VisionGuardianBinding.is_active == True,
        )
        .all()
    )
    results = []
    for b in bindings:
        student = db.query(User).filter(User.id == b.student_user_id).first()
        if not student:
            continue
        profile = db.query(VisionProfile).filter(VisionProfile.user_id == student.id).first()
        results.append({
            "binding_id": b.id,
            "student_id": student.id,
            "student_name": student.username,
            "relationship": b.relationship,
            "risk_level": profile.current_risk_level if profile else "normal",
            "ttm_stage": profile.ttm_vision_stage if profile else "S0",
        })
    return results


def get_student_guardians(db: Session, student_user_id: int) -> list[dict]:
    """查询学生的所有监护人"""
    bindings = (
        db.query(VisionGuardianBinding)
        .filter(
            VisionGuardianBinding.student_user_id == student_user_id,
            VisionGuardianBinding.is_active == True,
        )
        .all()
    )
    results = []
    for b in bindings:
        guardian = db.query(User).filter(User.id == b.guardian_user_id).first()
        if not guardian:
            continue
        results.append({
            "binding_id": b.id,
            "guardian_id": guardian.id,
            "guardian_name": guardian.username,
            "relationship": b.relationship,
            "can_input_behavior": b.can_input_behavior,
        })
    return results


# ══════════════════════════════════════════
# 目标自动调整 (按 TTM 阶段)
# ══════════════════════════════════════════

_STAGE_GOALS = {
    # S0-S1: 宽松目标 (降低门槛, 鼓励开始)
    "S0": {"outdoor_target_min": 60, "screen_daily_limit": 180, "sleep_target_min": 420, "lutein_target_mg": 5.0},
    "S1": {"outdoor_target_min": 80, "screen_daily_limit": 160, "sleep_target_min": 440, "lutein_target_mg": 6.0},
    # S2-S3: 适中目标
    "S2": {"outdoor_target_min": 100, "screen_daily_limit": 140, "sleep_target_min": 460, "lutein_target_mg": 8.0},
    "S3": {"outdoor_target_min": 110, "screen_daily_limit": 130, "sleep_target_min": 470, "lutein_target_mg": 9.0},
    # S4+: 标准目标
    "S4": {"outdoor_target_min": 120, "screen_daily_limit": 120, "sleep_target_min": 480, "lutein_target_mg": 10.0},
}


def adjust_goals_for_stage(db: Session, user_id: int, ttm_stage: str) -> VisionBehaviorGoal:
    """根据 TTM 阶段自动调整目标"""
    goal = get_or_create_goal(db, user_id)
    if not goal.auto_adjust:
        return goal

    stage_defaults = _STAGE_GOALS.get(ttm_stage, _STAGE_GOALS["S4"])
    for k, v in stage_defaults.items():
        setattr(goal, k, v)
    goal.ttm_stage = ttm_stage
    goal.updated_at = datetime.utcnow()
    db.flush()
    return goal


# ══════════════════════════════════════════
# 周报生成
# ══════════════════════════════════════════

def generate_weekly_report(db: Session, student_id: int, guardian_id: Optional[int] = None) -> dict:
    """生成过去7天的视力行为周报"""
    end_date = date.today()
    start_date = end_date - timedelta(days=7)

    logs = (
        db.query(VisionBehaviorLog)
        .filter(
            VisionBehaviorLog.user_id == student_id,
            VisionBehaviorLog.log_date >= start_date,
            VisionBehaviorLog.log_date < end_date,
        )
        .order_by(VisionBehaviorLog.log_date)
        .all()
    )

    if not logs:
        return {
            "student_id": student_id,
            "period": f"{start_date} ~ {end_date}",
            "days_logged": 0,
            "message": "本周暂无打卡记录",
        }

    scores = [l.behavior_score or 0 for l in logs]
    avg_score = round(sum(scores) / len(scores), 1)
    outdoor_avg = round(sum(l.outdoor_minutes or 0 for l in logs) / len(logs))
    screen_avg = round(sum(l.screen_total_minutes or 0 for l in logs) / len(logs))
    eye_ex_days = sum(1 for l in logs if l.eye_exercise_done)

    # 趋势判断
    if len(scores) >= 3:
        first_half = sum(scores[:len(scores)//2]) / (len(scores)//2)
        second_half = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
        if second_half > first_half + 5:
            trend = "improving"
        elif second_half < first_half - 5:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"

    profile = db.query(VisionProfile).filter(VisionProfile.user_id == student_id).first()

    return {
        "student_id": student_id,
        "guardian_id": guardian_id,
        "period": f"{start_date} ~ {end_date}",
        "days_logged": len(logs),
        "avg_score": avg_score,
        "outdoor_avg_min": outdoor_avg,
        "screen_avg_min": screen_avg,
        "eye_exercise_days": eye_ex_days,
        "trend": trend,
        "risk_level": profile.current_risk_level if profile else "normal",
        "daily_scores": [{"date": str(l.log_date), "score": l.behavior_score or 0} for l in logs],
    }


# ══════════════════════════════════════════
# 处方触发 (铁律: AI→教练审核→推送)
# ══════════════════════════════════════════

def check_rx_trigger(db: Session, user_id: int) -> bool:
    """
    连续3天评分下降 → 创建 coach_push_queue 条目 (遵守铁律)
    返回 True 表示已触发
    """
    logs = (
        db.query(VisionBehaviorLog)
        .filter(
            VisionBehaviorLog.user_id == user_id,
            VisionBehaviorLog.log_date >= date.today() - timedelta(days=4),
        )
        .order_by(VisionBehaviorLog.log_date.desc())
        .limit(4)
        .all()
    )

    if len(logs) < 3:
        return False

    # 检查连续下降: 最近3天每天都比前一天低
    scores = [(l.log_date, l.behavior_score or 0) for l in logs]
    scores.sort(key=lambda x: x[0])  # 按日期升序

    declining = True
    for i in range(1, min(4, len(scores))):
        if scores[i][1] >= scores[i - 1][1]:
            declining = False
            break

    if not declining:
        return False

    # 查找用户的教练 (从 profile 或 User)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    coach_id = None
    try:
        profile_data = user.profile if isinstance(user.profile, dict) else {}
        coach_id = profile_data.get("coach_id")
    except Exception:
        pass

    if not coach_id:
        logger.info(f"[VisionRx] user {user_id} 评分连续下降但无教练, 跳过")
        return False

    # 去重: 7天内已有 pending 的 vision_rx 条目则跳过
    try:
        existing = db.execute(sa_text("""
            SELECT 1 FROM coach_push_queue
            WHERE student_id = :uid AND source_type = 'vision_rx'
              AND status = 'pending'
              AND created_at > CURRENT_DATE - INTERVAL '7 days'
            LIMIT 1
        """), {"uid": user_id}).first()
        if existing:
            return False
    except Exception:
        pass

    # 创建推送队列条目 (铁律: AI建议 → 教练审核 → 推送)
    latest_score = scores[-1][1]
    try:
        db.execute(sa_text("""
            INSERT INTO coach_push_queue
              (coach_id, student_id, source_type, title, content,
               priority, status, created_at)
            VALUES (:cid, :uid, 'vision_rx',
              '视力行为评分连续下降预警',
              :content, 'high', 'pending', NOW())
        """), {
            "cid": coach_id,
            "uid": user_id,
            "content": f"学生近3天视力行为评分持续下降(最新 {latest_score:.0f} 分)，"
                       f"建议关注其用眼习惯并制定干预方案。",
        })
        db.commit()
        logger.info(f"[VisionRx] 已为 user {user_id} 创建视力处方队列条目 (coach={coach_id})")
        return True
    except Exception as e:
        logger.warning(f"[VisionRx] 创建队列条目失败: {e}")
        db.rollback()
        return False


# ══════════════════════════════════════════
# 批量计算评分 (供 Scheduler 使用)
# ══════════════════════════════════════════

def batch_calc_daily_scores(db: Session) -> int:
    """为所有今天有打卡但未计算评分的日志计算评分"""
    today = date.today()
    logs = (
        db.query(VisionBehaviorLog)
        .filter(
            VisionBehaviorLog.log_date == today,
            VisionBehaviorLog.behavior_score == None,
        )
        .all()
    )
    count = 0
    for log in logs:
        goal = get_or_create_goal(db, log.user_id)
        log.behavior_score = calc_behavior_score(log, goal)
        count += 1
    if count:
        db.commit()
    return count


def batch_update_risk_levels(db: Session) -> int:
    """更新所有视力学生的风险等级"""
    profiles = db.query(VisionProfile).filter(VisionProfile.is_vision_student == True).all()
    count = 0
    for p in profiles:
        new_risk = assess_vision_risk(db, p.user_id)
        if p.current_risk_level != new_risk.value:
            p.current_risk_level = new_risk.value
            count += 1
    if count:
        db.commit()
    return count
