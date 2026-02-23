"""
Admin User Management API
管理后台用户管理接口

Endpoints:
- GET    /api/v1/admin/users              - List users (paginated, filterable)
- GET    /api/v1/admin/users/{user_id}    - Get user details
- GET    /api/v1/admin/users/{user_id}/role-profile - User role profile (aggregated)
- POST   /api/v1/admin/users              - Create user (admin only)
- PUT    /api/v1/admin/users/{user_id}    - Update user info
- PUT    /api/v1/admin/users/{user_id}/status - Toggle active/inactive
- DELETE /api/v1/admin/users/{user_id}    - Soft delete (deactivate)
- GET    /api/v1/admin/stats              - Dashboard statistics
- GET    /api/v1/admin/coaches            - Coach list with load info
- GET    /api/v1/admin/distribution/pending  - Unassigned growers
- POST   /api/v1/admin/distribution/assign   - Assign grower to coach
- GET    /api/v1/admin/distribution/transfers - Transfer approval list
- POST   /api/v1/admin/distribution/transfers/{id}/approve
- POST   /api/v1/admin/distribution/transfers/{id}/reject
"""
from datetime import datetime, date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from loguru import logger

from core.database import get_db
from core.models import (
    User, UserRole, Assessment, ROLE_LEVEL,
    UserLearningStats, DailyTask, UserStreak, ExamResult,
    KnowledgeDocument, KnowledgeContribution, CompanionRelation,
    PointTransaction, AssessmentAssignment,
)
from core.auth import hash_password
from api.dependencies import get_current_user, require_admin, require_coach_or_admin

router = APIRouter(prefix="/api/v1/admin", tags=["Admin - User Management"])


# ============================================
# Pydantic Schemas
# ============================================

class CreateUserRequest(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    role: str = "grower"
    email: Optional[str] = None
    phone: Optional[str] = None


class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class UpdateStatusRequest(BaseModel):
    is_active: bool


class AssignRequest(BaseModel):
    grower_id: int
    coach_id: int


# ============================================
# User CRUD
# ============================================

@router.get("/users")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    risk: Optional[str] = Query(None, description="风险等级过滤(学员)"),
    activity: Optional[str] = Query(None, description="活跃度过滤(学员)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """用户列表 - 支持分页、搜索、角色/状态/风险/活跃度过滤"""
    from core.student_classification_service import (
        classify_students_batch, classification_to_dict,
    )

    query = db.query(User)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                User.username.ilike(pattern),
                User.full_name.ilike(pattern),
                User.email.ilike(pattern),
            )
        )

    if role:
        try:
            query = query.filter(User.role == UserRole(role))
        except ValueError:
            pass

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    _student_roles = [UserRole.OBSERVER, UserRole.GROWER, UserRole.SHARER]
    need_classification = bool(risk or activity)

    if need_classification:
        # Classification filters require in-memory post-filtering on student-role users
        query = query.filter(User.role.in_(_student_roles))
        all_users = query.order_by(User.created_at.desc()).all()

        student_ids = [u.id for u in all_users]
        classifications = classify_students_batch(db, student_ids) if student_ids else {}

        if risk:
            vals = set(risk.split(","))
            all_users = [u for u in all_users if classifications.get(u.id) and classifications[u.id].risk in vals]
        if activity:
            vals = set(activity.split(","))
            all_users = [u for u in all_users if classifications.get(u.id) and classifications[u.id].activity in vals]

        total = len(all_users)
        start = (page - 1) * page_size
        users = all_users[start:start + page_size]
    else:
        # Normal path: DB-level pagination (no full-table load)
        total = query.count()
        users = query.order_by(User.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        # Classify student-role users in this page only
        student_ids = [u.id for u in users if u.role in _student_roles]
        classifications = classify_students_batch(db, student_ids) if student_ids else {}

    return {
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "full_name": u.full_name,
                "role": u.role.value if u.role else "grower",
                "email": u.email,
                "phone": getattr(u, 'phone', None),
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_login_at": u.last_login_at.isoformat() if getattr(u, 'last_login_at', None) else None,
                "classification": classification_to_dict(classifications[u.id]) if u.id in classifications else None,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/users/{user_id}/role-profile")
def get_user_role_profile(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """用户角色画像聚合端点 — 按角色等级条件填充数据"""
    from api.paths_api import _compute_user_level, _LEVEL_THRESHOLDS, _LEVEL_META, _COMPANION_REQS
    from core.learning_service import get_or_create_stats, _count_companions

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    role_val = user.role.value if user.role else "observer"
    role_level = ROLE_LEVEL.get(user.role, 1) - 1  # convert 1-indexed to L0-L5

    # === basic ===
    basic = {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": role_val,
        "role_label": {
            "admin": "管理员", "supervisor": "督导", "promoter": "促进师",
            "master": "大师", "coach": "教练", "sharer": "分享者",
            "grower": "成长者", "observer": "观察员",
        }.get(role_val, role_val),
        "role_level": role_level,
        "avatar_url": getattr(user, 'avatar_url', None),
        "email": user.email,
        "phone": getattr(user, 'phone', None),
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login_at": user.last_login_at.isoformat() if getattr(user, 'last_login_at', None) else None,
    }

    # === points & level_progress ===
    stats = get_or_create_stats(db, user.id)
    computed_level = _compute_user_level(stats)
    next_level = min(computed_level + 1, 5)
    is_max = computed_level >= 5

    points = {
        "growth": stats.growth_points or 0,
        "contribution": stats.contribution_points or 0,
        "influence": stats.influence_points or 0,
    }

    next_req = _LEVEL_THRESHOLDS.get(next_level) if not is_max else None
    cur_meta = _LEVEL_META.get(computed_level, _LEVEL_META[0])
    nxt_meta = _LEVEL_META.get(next_level, _LEVEL_META[0]) if not is_max else None

    comp_req = _COMPANION_REQS.get(next_level)
    comp_graduated = 0
    comp_required = 0
    comp_target = None
    if comp_req and not is_max:
        comp_required, comp_target, comp_target_role = comp_req
        comp_graduated = _count_companions(db, user.id, comp_target_role)

    level_progress = {
        "current_level": computed_level,
        "current_name": cur_meta["name"],
        "next_level": next_level if not is_max else None,
        "next_name": nxt_meta["name"] if nxt_meta else None,
        "requirements": {
            "growth": {"current": points["growth"], "required": next_req["min_growth"] if next_req else 0},
            "contribution": {"current": points["contribution"], "required": next_req["min_contribution"] if next_req else 0},
            "influence": {"current": points["influence"], "required": next_req["min_influence"] if next_req else 0},
        } if not is_max else None,
        "companions": {
            "graduated": comp_graduated,
            "required": comp_required,
            "target": comp_target,
        } if comp_required > 0 else None,
    }

    # === grower_data (role_level >= 1, i.e. grower+) ===
    grower_data = None
    if role_level >= 1:
        streak = db.query(UserStreak).filter(UserStreak.user_id == user.id).first()
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        today_tasks = db.query(DailyTask).filter(
            DailyTask.user_id == user.id,
            DailyTask.task_date == today,
        ).all()
        today_total = len(today_tasks)
        today_done = sum(1 for t in today_tasks if t.done)

        week_tasks = db.query(DailyTask).filter(
            DailyTask.user_id == user.id,
            DailyTask.task_date >= week_start,
            DailyTask.task_date <= today,
        ).all()
        week_total = len(week_tasks)
        week_done = sum(1 for t in week_tasks if t.done)
        weekly_rate = round(week_done / week_total * 100, 1) if week_total > 0 else 0.0

        exam_total = db.query(func.count(ExamResult.id)).filter(ExamResult.user_id == user.id).scalar() or 0
        exam_passed = db.query(func.count(ExamResult.id)).filter(
            ExamResult.user_id == user.id, ExamResult.status == "passed"
        ).scalar() or 0

        grower_data = {
            "current_streak": streak.current_streak if streak else (stats.current_streak or 0),
            "longest_streak": streak.longest_streak if streak else (stats.longest_streak or 0),
            "total_learning_minutes": stats.total_minutes or 0,
            "daily_tasks_today": {"total": today_total, "done": today_done},
            "weekly_completion_rate": weekly_rate,
            "exams": {"total": exam_total, "passed": exam_passed},
        }

    # === sharer_data (role_level >= 2, i.e. sharer+) ===
    sharer_data = None
    if role_level >= 2:
        contribs = db.query(KnowledgeContribution).filter(
            KnowledgeContribution.contributor_id == user.id
        ).all()
        contrib_total = len(contribs)
        contrib_pending = sum(1 for c in contribs if c.status == "pending")
        contrib_approved = sum(1 for c in contribs if c.status == "approved")
        contrib_rejected = sum(1 for c in contribs if c.status == "rejected")

        contribution_list = []
        for c in contribs[:10]:
            doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == c.document_id).first()
            contribution_list.append({
                "id": c.id,
                "title": doc.title if doc else "(已删除)",
                "status": c.status,
                "evidence_tier": doc.evidence_tier if doc else None,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            })

        mentees = db.query(CompanionRelation).filter(
            CompanionRelation.mentor_id == user.id
        ).all()
        mentee_list = []
        for m in mentees:
            mentee_user = db.query(User).filter(User.id == m.mentee_id).first()
            mentee_list.append({
                "mentee_id": m.mentee_id,
                "mentee_name": (mentee_user.full_name or mentee_user.username) if mentee_user else "未知",
                "mentee_role": mentee_user.role.value if mentee_user and mentee_user.role else "observer",
                "status": m.status or "active",
                "quality_score": m.quality_score,
                "started_at": m.started_at.isoformat() if m.started_at else None,
            })

        influence_txns = db.query(PointTransaction).filter(
            PointTransaction.user_id == user.id,
            PointTransaction.point_type == "influence",
        ).all()
        inf_total = sum(t.amount for t in influence_txns)
        inf_likes = sum(t.amount for t in influence_txns if t.action == "like")
        inf_saves = sum(t.amount for t in influence_txns if t.action == "save")
        inf_official = inf_total - inf_likes - inf_saves

        sharer_data = {
            "contributions": {
                "total": contrib_total,
                "pending": contrib_pending,
                "published": contrib_approved,
                "rejected": contrib_rejected,
            },
            "contribution_list": contribution_list,
            "mentees": mentee_list,
            "influence": {
                "total": points["influence"],
                "likes": inf_likes,
                "saves": inf_saves,
                "official": max(0, inf_official),
            },
        }

    # === coach_data (role_level >= 3, i.e. coach+) ===
    coach_data = None
    if role_level >= 3:
        student_count = db.query(func.count(func.distinct(AssessmentAssignment.student_id))).filter(
            AssessmentAssignment.coach_id == user.id
        ).scalar() or 0
        case_count = db.query(func.count(AssessmentAssignment.id)).filter(
            AssessmentAssignment.coach_id == user.id
        ).scalar() or 0

        coach_data = {
            "student_count": student_count,
            "case_count": case_count,
        }

    return {
        "basic": basic,
        "points": points,
        "level_progress": level_progress,
        "grower_data": grower_data,
        "sharer_data": sharer_data,
        "coach_data": coach_data,
    }


@router.get("/users/{user_id}")
def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """用户详情"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role.value if user.role else "grower",
        "email": user.email,
        "phone": getattr(user, 'phone', None),
        "is_active": user.is_active,
        "is_verified": getattr(user, 'is_verified', False),
        "profile": user.profile,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(
    request: CreateUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """创建新用户"""
    if db.query(User).filter(User.username == request.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if request.email and db.query(User).filter(User.email == request.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="密码长度不能少于6位")

    try:
        role_enum = UserRole(request.role)
    except ValueError:
        role_enum = UserRole.GROWER

    new_user = User(
        username=request.username,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        role=role_enum,
        email=request.email or f"{request.username}@placeholder.com",
        is_active=True,
        is_verified=True,
    )
    if hasattr(new_user, 'phone') and request.phone:
        new_user.phone = request.phone

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"管理员 {current_user.username} 创建用户: {request.username}")
    return {"id": new_user.id, "username": new_user.username, "role": new_user.role.value}


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    request: UpdateUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """更新用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if request.full_name is not None:
        user.full_name = request.full_name
    if request.role is not None:
        try:
            user.role = UserRole(request.role)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的角色: {request.role}")
    if request.email is not None:
        if db.query(User).filter(User.email == request.email, User.id != user_id).first():
            raise HTTPException(status_code=400, detail="邮箱已被注册")
        user.email = request.email
    if request.phone is not None and hasattr(user, 'phone'):
        user.phone = request.phone

    db.commit()
    logger.info(f"管理员 {current_user.username} 更新用户 {user.username}")
    return {"message": "用户已更新", "id": user_id}


@router.put("/users/{user_id}/status")
def update_status(
    user_id: int,
    request: UpdateStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """启用/停用用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == current_user.id and not request.is_active:
        raise HTTPException(status_code=400, detail="不能停用自己的账号")

    user.is_active = request.is_active
    db.commit()
    action = "启用" if request.is_active else "停用"
    logger.info(f"管理员 {current_user.username} {action}用户 {user.username}")
    return {"message": f"用户已{action}", "id": user_id, "is_active": request.is_active}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """删除用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己的账号")

    username = user.username
    db.delete(user)
    db.commit()
    logger.info(f"管理员 {current_user.username} 删除用户 {username}")
    return {"message": "用户已删除"}


# ============================================
# Statistics
# ============================================

@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """用户统计"""
    total = db.query(func.count(User.id)).scalar() or 0
    active_count = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0

    role_counts = {}
    for role in UserRole:
        count = db.query(func.count(User.id)).filter(User.role == role).scalar() or 0
        role_counts[f"{role.value}_count"] = count

    return {"total": total, "active_count": active_count, **role_counts}


# ============================================
# Distribution Management
# ============================================

@router.get("/coaches")
def list_coaches(
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """教练/成员列表(含负载)"""
    if role:
        try:
            target_roles = [UserRole(role)]
        except ValueError:
            target_roles = [UserRole.COACH, UserRole.SUPERVISOR]
    else:
        target_roles = [
            UserRole.OBSERVER, UserRole.GROWER, UserRole.SHARER,
            UserRole.COACH, UserRole.SUPERVISOR, UserRole.PROMOTER,
        ]

    members = db.query(User).filter(
        User.role.in_(target_roles),
        User.is_active == True,
    ).order_by(User.created_at.desc()).limit(50).all()

    all_growers = db.query(User).filter(
        User.role == UserRole.GROWER, User.is_active == True
    ).all()

    role_level_map = {
        UserRole.OBSERVER: 0, UserRole.GROWER: 1, UserRole.SHARER: 2,
        UserRole.COACH: 3, UserRole.PROMOTER: 4, UserRole.SUPERVISOR: 4,
        UserRole.MASTER: 5, UserRole.ADMIN: 99,
    }

    result = []
    for m in members:
        assigned = [g for g in all_growers if (g.profile or {}).get('coach_id') == m.id]
        profile = m.profile or {}
        lv = role_level_map.get(m.role, 0)
        result.append({
            "id": m.id,
            "name": m.full_name or m.username,
            "full_name": m.full_name or m.username,
            "username": m.username,
            "role": m.role.value if m.role else "observer",
            "level": lv,
            "currentLoad": len(assigned),
            "maxLoad": profile.get("max_load", 20),
            "student_count": len(assigned),
            "case_count": profile.get("case_count", 0),
            "domains": profile.get("specializations", []),
            "avatar": getattr(m, "avatar_url", None) or "",
        })

    return {"items": result, "coaches": result, "total": len(result)}


@router.get("/distribution/pending")
def list_pending(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """待分配成长者"""
    growers = db.query(User).filter(
        User.role == UserRole.GROWER, User.is_active == True
    ).all()

    pending = []
    for g in growers:
        profile = g.profile or {}
        if profile.get("coach_id"):
            continue

        risk = "低"
        last_a = db.query(Assessment).filter(
            Assessment.user_id == g.id
        ).order_by(Assessment.created_at.desc()).first()
        if last_a and last_a.risk_level:
            risk_map = {"R0": "低", "R1": "低", "R2": "中", "R3": "高", "R4": "高"}
            risk = risk_map.get(last_a.risk_level.value, "低")

        pending.append({
            "id": g.id,
            "name": g.full_name or g.username,
            "risk": risk,
            "domain": profile.get("primary_condition", "综合"),
            "assignedCoach": None,
        })

    return {"pending": pending, "total": len(pending)}


@router.post("/distribution/assign")
def assign_grower(
    request: AssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """分配成长者给教练"""
    grower = db.query(User).filter(User.id == request.grower_id, User.role == UserRole.GROWER).first()
    if not grower:
        raise HTTPException(status_code=404, detail="成长者不存在")

    coach = db.query(User).filter(
        User.id == request.coach_id,
        User.role.in_([UserRole.COACH, UserRole.SUPERVISOR]),
    ).first()
    if not coach:
        raise HTTPException(status_code=404, detail="教练不存在")

    profile = grower.profile or {}
    profile["coach_id"] = coach.id
    profile["coach_name"] = coach.full_name or coach.username
    profile["assigned_at"] = datetime.utcnow().isoformat()
    grower.profile = profile

    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(grower, "profile")
    db.commit()

    logger.info(f"分配 {grower.username} -> {coach.username}")
    return {"message": f"{grower.full_name or grower.username} 已分配给 {coach.full_name or coach.username}"}


@router.get("/distribution/transfers")
def list_transfers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """待审批转移"""
    growers = db.query(User).filter(
        User.role == UserRole.GROWER, User.is_active == True
    ).all()

    transfers = []
    for g in growers:
        transfer = (g.profile or {}).get("transfer_request")
        if transfer and transfer.get("status") == "pending":
            transfers.append({
                "id": g.id,
                "patientName": g.full_name or g.username,
                "fromCoach": transfer.get("from_coach_name", "未知"),
                "toCoach": transfer.get("to_coach_name", "未知"),
                "reason": transfer.get("reason", ""),
            })

    return {"transfers": transfers, "total": len(transfers)}


@router.post("/distribution/transfers/{grower_id}/approve")
def approve_transfer(
    grower_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """批准转移"""
    grower = db.query(User).filter(User.id == grower_id).first()
    if not grower:
        raise HTTPException(status_code=404, detail="用户不存在")

    profile = grower.profile or {}
    transfer = profile.get("transfer_request")
    if not transfer or transfer.get("status") != "pending":
        raise HTTPException(status_code=400, detail="没有待处理的转移请求")

    profile["coach_id"] = transfer.get("to_coach_id")
    profile["coach_name"] = transfer.get("to_coach_name")
    profile["assigned_at"] = datetime.utcnow().isoformat()
    transfer["status"] = "approved"
    transfer["approved_by"] = current_user.username
    profile["transfer_request"] = transfer
    grower.profile = profile

    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(grower, "profile")
    db.commit()
    return {"message": "转移已批准"}


@router.post("/distribution/transfers/{grower_id}/reject")
def reject_transfer(
    grower_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """拒绝转移"""
    grower = db.query(User).filter(User.id == grower_id).first()
    if not grower:
        raise HTTPException(status_code=404, detail="用户不存在")

    profile = grower.profile or {}
    transfer = profile.get("transfer_request")
    if not transfer or transfer.get("status") != "pending":
        raise HTTPException(status_code=400, detail="没有待处理的转移请求")

    transfer["status"] = "rejected"
    transfer["rejected_by"] = current_user.username
    profile["transfer_request"] = transfer
    grower.profile = profile

    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(grower, "profile")
    db.commit()
    return {"message": "转移已拒绝"}
