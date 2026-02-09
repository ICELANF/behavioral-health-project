# -*- coding: utf-8 -*-
"""
挑战/打卡活动服务

核心业务逻辑:
- 模板 CRUD（从JSON配置导入、手动创建）
- 双专家审核发布流程
- 用户报名与进度跟踪
- 每日推送生成
- 问卷回答收集
"""
import json
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import and_

from core.models import (
    ChallengeTemplate, ChallengeDayPush, ChallengeEnrollment,
    ChallengeSurveyResponse, ChallengePushLog,
    ChallengeStatus, EnrollmentStatus, User, UserRole,
)


# ============================================
# 角色权限常量
# ============================================

# 可创建挑战的最低角色等级
MIN_CREATE_LEVEL = 4  # coach (L3, 1-indexed=4)

# 可审核挑战的最低角色等级
MIN_REVIEW_LEVEL = 5  # promoter/supervisor (L4, 1-indexed=5)

# 引用 models.py 权威定义
from core.models import ROLE_LEVEL


def _user_level(user: User) -> int:
    return ROLE_LEVEL.get(user.role, 1)


# ============================================
# 模板管理
# ============================================

def import_from_config(db: Session, config_key: str, user: User) -> ChallengeTemplate:
    """从 configs/challenges/{config_key}.json 导入挑战模板"""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "configs", "challenges", f"{config_key}.json"
    )
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Check if already imported
    existing = db.query(ChallengeTemplate).filter_by(config_key=config_key).first()
    if existing:
        raise ValueError(f"Challenge config '{config_key}' already imported as template #{existing.id}")

    # Create template
    template = ChallengeTemplate(
        title=config["title"],
        description=config.get("description", ""),
        category=config.get("category", "general"),
        duration_days=config["duration_days"],
        config_key=config_key,
        daily_push_times=config.get("daily_push_times"),
        day_topics=config.get("day_topics"),
        created_by=user.id,
        status=ChallengeStatus.DRAFT,
    )
    db.add(template)
    db.flush()  # get template.id

    # Create day pushes
    for push_data in config.get("pushes", []):
        push = ChallengeDayPush(
            challenge_id=template.id,
            day_number=push_data["day"],
            push_time=push_data["push_time"],
            sort_order=push_data.get("sort_order", 0),
            is_core=push_data.get("is_core", True),
            tag=push_data.get("tag", "core"),
            management_content=push_data.get("management_content"),
            behavior_guidance=push_data.get("behavior_guidance"),
            survey=push_data.get("survey"),
        )
        db.add(push)

    db.commit()
    db.refresh(template)
    return template


def create_template(db: Session, user: User, data: Dict[str, Any]) -> ChallengeTemplate:
    """手动创建挑战模板"""
    if _user_level(user) < MIN_CREATE_LEVEL:
        raise PermissionError("需要教练(L3)及以上权限才能创建挑战")

    template = ChallengeTemplate(
        title=data["title"],
        description=data.get("description", ""),
        category=data.get("category", "general"),
        duration_days=data["duration_days"],
        daily_push_times=data.get("daily_push_times", ["9:00", "11:30", "17:30"]),
        day_topics=data.get("day_topics"),
        cover_image=data.get("cover_image"),
        created_by=user.id,
        status=ChallengeStatus.DRAFT,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def update_template(db: Session, template_id: int, user: User, data: Dict[str, Any]) -> ChallengeTemplate:
    """更新挑战模板（仅草稿状态可编辑）"""
    template = db.query(ChallengeTemplate).get(template_id)
    if not template:
        raise ValueError("挑战模板不存在")
    if template.status not in (ChallengeStatus.DRAFT, ChallengeStatus.REVIEW_PARTIAL):
        raise ValueError("只有草稿或待审核状态可以编辑")
    if template.created_by != user.id and _user_level(user) < 99:
        raise PermissionError("只有创建者或管理员可以编辑")

    for field in ("title", "description", "category", "duration_days", "daily_push_times", "day_topics", "cover_image"):
        if field in data:
            setattr(template, field, data[field])

    db.commit()
    db.refresh(template)
    return template


def list_templates(db: Session, status: Optional[str] = None, category: Optional[str] = None) -> List[ChallengeTemplate]:
    """列出挑战模板"""
    query = db.query(ChallengeTemplate)
    if status:
        query = query.filter(ChallengeTemplate.status == status)
    if category:
        query = query.filter(ChallengeTemplate.category == category)
    return query.order_by(ChallengeTemplate.created_at.desc()).all()


# ============================================
# 推送内容管理
# ============================================

def add_day_push(db: Session, template_id: int, data: Dict[str, Any]) -> ChallengeDayPush:
    """添加每日推送内容"""
    push = ChallengeDayPush(
        challenge_id=template_id,
        day_number=data["day_number"],
        push_time=data.get("push_time", "9:00"),
        sort_order=data.get("sort_order", 0),
        is_core=data.get("is_core", True),
        tag=data.get("tag", "core"),
        management_content=data.get("management_content"),
        behavior_guidance=data.get("behavior_guidance"),
        survey=data.get("survey"),
    )
    db.add(push)
    db.commit()
    db.refresh(push)
    return push


def update_day_push(db: Session, push_id: int, data: Dict[str, Any]) -> ChallengeDayPush:
    """更新推送内容"""
    push = db.query(ChallengeDayPush).get(push_id)
    if not push:
        raise ValueError("推送内容不存在")

    for field in ("day_number", "push_time", "sort_order", "is_core", "tag",
                  "management_content", "behavior_guidance", "survey"):
        if field in data:
            setattr(push, field, data[field])

    db.commit()
    db.refresh(push)
    return push


def delete_day_push(db: Session, push_id: int):
    """删除推送内容"""
    push = db.query(ChallengeDayPush).get(push_id)
    if push:
        db.delete(push)
        db.commit()


def get_day_pushes(db: Session, template_id: int, day_number: Optional[int] = None) -> List[ChallengeDayPush]:
    """获取挑战的推送内容"""
    query = db.query(ChallengeDayPush).filter_by(challenge_id=template_id)
    if day_number is not None:
        query = query.filter_by(day_number=day_number)
    return query.order_by(ChallengeDayPush.day_number, ChallengeDayPush.sort_order).all()


# ============================================
# 双专家审核流程
# ============================================

def submit_for_review(db: Session, template_id: int, user: User) -> ChallengeTemplate:
    """提交审核"""
    template = db.query(ChallengeTemplate).get(template_id)
    if not template:
        raise ValueError("挑战模板不存在")
    if template.status != ChallengeStatus.DRAFT:
        raise ValueError("只有草稿状态可以提交审核")
    if template.created_by != user.id and _user_level(user) < 99:
        raise PermissionError("只有创建者或管理员可以提交审核")

    # Check has pushes
    push_count = db.query(ChallengeDayPush).filter_by(challenge_id=template_id).count()
    if push_count == 0:
        raise ValueError("至少需要添加一条推送内容")

    template.status = ChallengeStatus.PENDING_REVIEW
    db.commit()
    db.refresh(template)
    return template


def review_challenge(db: Session, template_id: int, reviewer: User,
                     approved: bool, note: Optional[str] = None) -> ChallengeTemplate:
    """专家审核挑战"""
    if _user_level(reviewer) < MIN_REVIEW_LEVEL:
        raise PermissionError("需要促进师(L4)及以上权限才能审核")

    template = db.query(ChallengeTemplate).get(template_id)
    if not template:
        raise ValueError("挑战模板不存在")
    if template.status not in (ChallengeStatus.PENDING_REVIEW, ChallengeStatus.REVIEW_PARTIAL):
        raise ValueError("当前状态不允许审核")
    if template.created_by == reviewer.id:
        raise ValueError("创建者不能审核自己的挑战")

    now = datetime.utcnow()
    status_val = "approved" if approved else "rejected"

    # Assign to reviewer slot
    if template.reviewer1_id is None or template.reviewer1_id == reviewer.id:
        template.reviewer1_id = reviewer.id
        template.reviewer1_status = status_val
        template.reviewer1_note = note
        template.reviewer1_at = now
    elif template.reviewer2_id is None or template.reviewer2_id == reviewer.id:
        if template.reviewer1_id == reviewer.id:
            raise ValueError("同一专家不能审核两次")
        template.reviewer2_id = reviewer.id
        template.reviewer2_status = status_val
        template.reviewer2_note = note
        template.reviewer2_at = now
    else:
        raise ValueError("已有两位专家审核")

    # Determine overall status
    r1 = template.reviewer1_status
    r2 = template.reviewer2_status

    if r1 == "rejected" or r2 == "rejected":
        # Any rejection → back to draft
        template.status = ChallengeStatus.DRAFT
    elif r1 == "approved" and r2 == "approved":
        # Both approved → published
        template.status = ChallengeStatus.PUBLISHED
        template.published_at = now
    elif r1 and not r2:
        template.status = ChallengeStatus.REVIEW_PARTIAL
    # else keep current status

    db.commit()
    db.refresh(template)
    return template


# ============================================
# 用户报名与进度
# ============================================

def enroll(db: Session, user: User, challenge_id: int, coach_id: Optional[int] = None) -> ChallengeEnrollment:
    """用户报名挑战"""
    template = db.query(ChallengeTemplate).get(challenge_id)
    if not template:
        raise ValueError("挑战不存在")
    if template.status != ChallengeStatus.PUBLISHED:
        raise ValueError("该挑战尚未发布")

    # Check duplicate
    existing = db.query(ChallengeEnrollment).filter(
        and_(
            ChallengeEnrollment.user_id == user.id,
            ChallengeEnrollment.challenge_id == challenge_id,
            ChallengeEnrollment.status.in_([EnrollmentStatus.ENROLLED, EnrollmentStatus.ACTIVE])
        )
    ).first()
    if existing:
        raise ValueError("已报名该挑战")

    enrollment = ChallengeEnrollment(
        user_id=user.id,
        challenge_id=challenge_id,
        coach_id=coach_id,
        status=EnrollmentStatus.ENROLLED,
    )
    db.add(enrollment)

    # Update enrollment count
    template.enrollment_count = (template.enrollment_count or 0) + 1

    db.commit()
    db.refresh(enrollment)
    return enrollment


def start_challenge(db: Session, enrollment_id: int) -> ChallengeEnrollment:
    """开始挑战（从报名变为进行中）"""
    enrollment = db.query(ChallengeEnrollment).get(enrollment_id)
    if not enrollment:
        raise ValueError("报名记录不存在")
    if enrollment.status != EnrollmentStatus.ENROLLED:
        raise ValueError("只有已报名状态可以开始")

    enrollment.status = EnrollmentStatus.ACTIVE
    enrollment.started_at = datetime.utcnow()
    enrollment.current_day = 0

    # Generate push logs for day 0
    _generate_push_logs(db, enrollment, 0)

    db.commit()
    db.refresh(enrollment)
    return enrollment


def advance_day(db: Session, enrollment_id: int) -> ChallengeEnrollment:
    """推进到下一天"""
    enrollment = db.query(ChallengeEnrollment).get(enrollment_id)
    if not enrollment:
        raise ValueError("报名记录不存在")
    if enrollment.status != EnrollmentStatus.ACTIVE:
        raise ValueError("只有进行中的挑战可以推进")

    template = db.query(ChallengeTemplate).get(enrollment.challenge_id)
    next_day = enrollment.current_day + 1

    if next_day > template.duration_days:
        # Completed
        enrollment.status = EnrollmentStatus.COMPLETED
        enrollment.completed_at = datetime.utcnow()
    else:
        enrollment.current_day = next_day
        enrollment.streak_days += 1
        _generate_push_logs(db, enrollment, next_day)

    db.commit()
    db.refresh(enrollment)
    return enrollment


def _generate_push_logs(db: Session, enrollment: ChallengeEnrollment, day_number: int):
    """为指定天生成推送日志，若有教练则创建审批队列条目"""
    from core import coach_push_queue_service as queue_svc

    pushes = db.query(ChallengeDayPush).filter(
        and_(
            ChallengeDayPush.challenge_id == enrollment.challenge_id,
            ChallengeDayPush.day_number == day_number,
        )
    ).all()

    # 获取挑战标题
    template = db.query(ChallengeTemplate).get(enrollment.challenge_id)
    challenge_title = template.title if template else "挑战"

    now = datetime.utcnow()
    for push in pushes:
        existing = db.query(ChallengePushLog).filter(
            and_(
                ChallengePushLog.enrollment_id == enrollment.id,
                ChallengePushLog.push_id == push.id,
            )
        ).first()
        if not existing:
            log = ChallengePushLog(
                enrollment_id=enrollment.id,
                push_id=push.id,
                status="sent",
                sent_at=now,
            )
            db.add(log)

            # 若有教练，创建 CoachPushQueue 条目
            if enrollment.coach_id:
                content_parts = []
                if push.management_content:
                    content_parts.append(push.management_content)
                if push.behavior_guidance:
                    content_parts.append(push.behavior_guidance)
                queue_svc.create_queue_item(
                    db,
                    coach_id=enrollment.coach_id,
                    student_id=enrollment.user_id,
                    source_type="challenge",
                    source_id=str(push.id),
                    title=f"{challenge_title} · 第{day_number}天 · {push.push_time}",
                    content="\n".join(content_parts) if content_parts else None,
                    content_extra={"push_id": push.id, "day_number": day_number, "push_time": push.push_time},
                    priority="normal",
                )


def get_today_pushes(db: Session, enrollment_id: int) -> List[Dict[str, Any]]:
    """获取今日推送内容（含阅读状态）"""
    enrollment = db.query(ChallengeEnrollment).get(enrollment_id)
    if not enrollment:
        return []

    pushes = db.query(ChallengeDayPush).filter(
        and_(
            ChallengeDayPush.challenge_id == enrollment.challenge_id,
            ChallengeDayPush.day_number == enrollment.current_day,
        )
    ).order_by(ChallengeDayPush.sort_order).all()

    result = []
    for push in pushes:
        log = db.query(ChallengePushLog).filter(
            and_(
                ChallengePushLog.enrollment_id == enrollment_id,
                ChallengePushLog.push_id == push.id,
            )
        ).first()

        # Check if survey already answered
        survey_response = db.query(ChallengeSurveyResponse).filter(
            and_(
                ChallengeSurveyResponse.enrollment_id == enrollment_id,
                ChallengeSurveyResponse.push_id == push.id,
            )
        ).first()

        result.append({
            "push_id": push.id,
            "day_number": push.day_number,
            "push_time": push.push_time,
            "is_core": push.is_core,
            "tag": push.tag,
            "management_content": push.management_content,
            "behavior_guidance": push.behavior_guidance,
            "survey": push.survey,
            "status": log.status if log else "pending",
            "read_at": log.read_at.isoformat() if log and log.read_at else None,
            "survey_completed": survey_response is not None,
            "survey_response": survey_response.responses if survey_response else None,
        })

    return result


def mark_push_read(db: Session, enrollment_id: int, push_id: int):
    """标记推送为已读"""
    log = db.query(ChallengePushLog).filter(
        and_(
            ChallengePushLog.enrollment_id == enrollment_id,
            ChallengePushLog.push_id == push_id,
        )
    ).first()
    if log and not log.read_at:
        log.status = "read"
        log.read_at = datetime.utcnow()

        # Update enrollment completed_pushes
        enrollment = db.query(ChallengeEnrollment).get(enrollment_id)
        if enrollment:
            enrollment.completed_pushes = (enrollment.completed_pushes or 0) + 1

        db.commit()


# ============================================
# 问卷回答
# ============================================

def submit_survey(db: Session, user: User, enrollment_id: int, push_id: int,
                  responses: Dict[str, Any]) -> ChallengeSurveyResponse:
    """提交问卷回答"""
    enrollment = db.query(ChallengeEnrollment).get(enrollment_id)
    if not enrollment:
        raise ValueError("报名记录不存在")
    if enrollment.user_id != user.id:
        raise PermissionError("不能替他人回答问卷")

    # Check push exists and has survey
    push = db.query(ChallengeDayPush).get(push_id)
    if not push:
        raise ValueError("推送内容不存在")
    if not push.survey:
        raise ValueError("该推送没有问卷")

    # Check duplicate
    existing = db.query(ChallengeSurveyResponse).filter(
        and_(
            ChallengeSurveyResponse.enrollment_id == enrollment_id,
            ChallengeSurveyResponse.push_id == push_id,
        )
    ).first()
    if existing:
        # Update existing response
        existing.responses = responses
        existing.submitted_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    response = ChallengeSurveyResponse(
        enrollment_id=enrollment_id,
        push_id=push_id,
        user_id=user.id,
        responses=responses,
    )
    db.add(response)

    # Update enrollment completed_surveys
    enrollment.completed_surveys = (enrollment.completed_surveys or 0) + 1

    db.commit()
    db.refresh(response)
    return response


def get_enrollment_progress(db: Session, enrollment_id: int) -> Dict[str, Any]:
    """获取报名进度详情"""
    enrollment = db.query(ChallengeEnrollment).get(enrollment_id)
    if not enrollment:
        return {}

    template = db.query(ChallengeTemplate).get(enrollment.challenge_id)

    total_pushes = db.query(ChallengeDayPush).filter_by(challenge_id=enrollment.challenge_id).count()
    total_surveys = db.query(ChallengeDayPush).filter(
        and_(
            ChallengeDayPush.challenge_id == enrollment.challenge_id,
            ChallengeDayPush.survey.isnot(None),
        )
    ).count()

    return {
        "enrollment_id": enrollment.id,
        "challenge_id": enrollment.challenge_id,
        "challenge_title": template.title if template else "",
        "duration_days": template.duration_days if template else 0,
        "current_day": enrollment.current_day,
        "status": enrollment.status.value if hasattr(enrollment.status, 'value') else enrollment.status,
        "started_at": enrollment.started_at.isoformat() if enrollment.started_at else None,
        "completed_at": enrollment.completed_at.isoformat() if enrollment.completed_at else None,
        "streak_days": enrollment.streak_days,
        "total_pushes": total_pushes,
        "completed_pushes": enrollment.completed_pushes or 0,
        "total_surveys": total_surveys,
        "completed_surveys": enrollment.completed_surveys or 0,
        "push_progress_pct": round((enrollment.completed_pushes or 0) / max(total_pushes, 1) * 100),
        "day_progress_pct": round(enrollment.current_day / max(template.duration_days, 1) * 100) if template else 0,
    }


def coach_assign_challenge(db: Session, coach: User, student_id: int, challenge_id: int) -> ChallengeEnrollment:
    """教练为学员报名挑战"""
    if _user_level(coach) < MIN_CREATE_LEVEL:
        raise PermissionError("需要教练(L3)及以上权限")

    student = db.query(User).get(student_id)
    if not student:
        raise ValueError("学员不存在")

    return enroll(db, student, challenge_id, coach_id=coach.id)
