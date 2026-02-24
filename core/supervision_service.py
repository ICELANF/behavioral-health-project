"""
supervision_service.py — 督导会议管理服务

提供 CoachSupervisionRecord CRUD + 状态机 + 统计。
同步 SQLAlchemy (与 learning_service / program_service 一致)。
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from core.models import CoachSupervisionRecord, User, UserRole, ROLE_LEVEL

import logging

logger = logging.getLogger(__name__)

# 督导类型
VALID_SESSION_TYPES = [
    "individual",          # 个人督导
    "group",               # 团体督导
    "case_review",         # 案例研讨
    "live_observation",    # 现场观摩
    "emergency",           # 紧急干预复盘
]

# 状态机: from → allowed targets
_STATUS_TRANSITIONS = {
    "scheduled": ["in_progress", "cancelled"],
    "in_progress": ["completed", "cancelled"],
    "completed": [],       # 终态
    "cancelled": [],       # 终态
}

# 允许创建督导的最低角色等级
MIN_SUPERVISOR_LEVEL = ROLE_LEVEL.get(UserRole.PROMOTER, 5)


class SupervisionService:
    """督导会议管理服务 (同步 SQLAlchemy)"""

    def create_session(
        self,
        db: Session,
        supervisor: User,
        coach_id: int,
        session_type: str,
        scheduled_at: Optional[datetime] = None,
        template_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> CoachSupervisionRecord:
        """创建督导会议"""
        # 权限检查
        sup_level = ROLE_LEVEL.get(supervisor.role, 0)
        if sup_level < MIN_SUPERVISOR_LEVEL:
            raise PermissionError("需要促进师(L4)及以上权限才能创建督导会议")

        # 类型校验
        if session_type not in VALID_SESSION_TYPES:
            raise ValueError(f"无效的督导类型: {session_type}，允许: {VALID_SESSION_TYPES}")

        # 被督导教练存在性检查
        coach = db.query(User).filter(User.id == coach_id, User.is_active == True).first()
        if not coach:
            raise ValueError(f"教练 {coach_id} 不存在或已停用")

        record = CoachSupervisionRecord(
            supervisor_id=supervisor.id,
            coach_id=coach_id,
            session_type=session_type,
            scheduled_at=scheduled_at,
            status="scheduled",
            template_id=template_id,
            session_notes=notes,
        )
        db.add(record)
        db.flush()
        logger.info(f"[Supervision] 创建督导: #{record.id} supervisor={supervisor.id} coach={coach_id} type={session_type}")
        return record

    def update_session(
        self,
        db: Session,
        record_id: int,
        supervisor: User,
        *,
        session_notes: Optional[str] = None,
        action_items: Optional[list] = None,
        quality_rating: Optional[float] = None,
        compliance_met: Optional[bool] = None,
        scheduled_at: Optional[datetime] = None,
    ) -> CoachSupervisionRecord:
        """更新督导记录"""
        record = self._get_owned_record(db, record_id, supervisor)

        if session_notes is not None:
            record.session_notes = session_notes
        if action_items is not None:
            record.action_items = action_items
        if quality_rating is not None:
            if not (0.0 <= quality_rating <= 5.0):
                raise ValueError("quality_rating 必须在 0.0-5.0 之间")
            record.quality_rating = quality_rating
        if compliance_met is not None:
            record.compliance_met = compliance_met
        if scheduled_at is not None:
            record.scheduled_at = scheduled_at

        db.flush()
        return record

    def transition_status(
        self,
        db: Session,
        record_id: int,
        supervisor: User,
        target_status: str,
    ) -> CoachSupervisionRecord:
        """状态转换"""
        record = self._get_owned_record(db, record_id, supervisor)
        allowed = _STATUS_TRANSITIONS.get(record.status, [])
        if target_status not in allowed:
            raise ValueError(
                f"不能从 {record.status} 转为 {target_status}，允许: {allowed}"
            )
        record.status = target_status
        if target_status == "completed":
            record.completed_at = datetime.utcnow()
        db.flush()
        logger.info(f"[Supervision] #{record_id} 状态变更 → {target_status}")
        return record

    def get_session(self, db: Session, record_id: int) -> Optional[CoachSupervisionRecord]:
        """获取单条记录"""
        return db.query(CoachSupervisionRecord).filter(
            CoachSupervisionRecord.id == record_id
        ).first()

    def list_sessions(
        self,
        db: Session,
        supervisor_id: Optional[int] = None,
        coach_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[CoachSupervisionRecord], int]:
        """列表查询 (支持按 supervisor / coach / status 过滤)"""
        q = db.query(CoachSupervisionRecord)
        if supervisor_id is not None:
            q = q.filter(CoachSupervisionRecord.supervisor_id == supervisor_id)
        if coach_id is not None:
            q = q.filter(CoachSupervisionRecord.coach_id == coach_id)
        if status:
            q = q.filter(CoachSupervisionRecord.status == status)
        total = q.count()
        records = q.order_by(desc(CoachSupervisionRecord.created_at)).offset(offset).limit(limit).all()
        return records, total

    def get_stats(self, db: Session, supervisor_id: int) -> dict:
        """督导者统计"""
        base = db.query(CoachSupervisionRecord).filter(
            CoachSupervisionRecord.supervisor_id == supervisor_id
        )
        total = base.count()
        completed = base.filter(CoachSupervisionRecord.status == "completed").count()
        scheduled = base.filter(CoachSupervisionRecord.status == "scheduled").count()

        # 平均评分
        avg_rating = db.query(func.avg(CoachSupervisionRecord.quality_rating)).filter(
            CoachSupervisionRecord.supervisor_id == supervisor_id,
            CoachSupervisionRecord.quality_rating.isnot(None),
        ).scalar()

        # 被督导教练数
        coach_count = db.query(func.count(func.distinct(CoachSupervisionRecord.coach_id))).filter(
            CoachSupervisionRecord.supervisor_id == supervisor_id,
        ).scalar() or 0

        # 本月完成数
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_completed = base.filter(
            CoachSupervisionRecord.status == "completed",
            CoachSupervisionRecord.completed_at >= month_start,
        ).count()

        return {
            "total_sessions": total,
            "completed": completed,
            "scheduled": scheduled,
            "avg_quality_rating": round(float(avg_rating), 2) if avg_rating else None,
            "coach_count": coach_count,
            "monthly_completed": monthly_completed,
        }

    def _get_owned_record(
        self, db: Session, record_id: int, supervisor: User
    ) -> CoachSupervisionRecord:
        """获取并检查所有权"""
        record = db.query(CoachSupervisionRecord).filter(
            CoachSupervisionRecord.id == record_id
        ).first()
        if not record:
            raise ValueError(f"督导记录 {record_id} 不存在")
        # admin 可操作所有记录
        if supervisor.role.value == "admin":
            return record
        if record.supervisor_id != supervisor.id:
            raise PermissionError("只能操作自己创建的督导记录")
        return record


def _record_to_dict(r: CoachSupervisionRecord, db: Session) -> dict:
    """序列化督导记录"""
    # 获取 supervisor 和 coach 的名字
    supervisor = db.query(User.full_name, User.username).filter(User.id == r.supervisor_id).first()
    coach = db.query(User.full_name, User.username).filter(User.id == r.coach_id).first()

    return {
        "id": r.id,
        "supervisor_id": r.supervisor_id,
        "supervisor_name": (supervisor.full_name or supervisor.username) if supervisor else "",
        "coach_id": r.coach_id,
        "coach_name": (coach.full_name or coach.username) if coach else "",
        "session_type": r.session_type,
        "scheduled_at": r.scheduled_at.isoformat() if r.scheduled_at else None,
        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        "status": r.status,
        "template_id": r.template_id,
        "session_notes": r.session_notes,
        "action_items": r.action_items or [],
        "quality_rating": r.quality_rating,
        "compliance_met": r.compliance_met,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }
