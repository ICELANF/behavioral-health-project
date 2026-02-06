"""
Admin User Management API
管理后台用户管理接口

Endpoints:
- GET    /api/v1/admin/users              - List users (paginated, filterable)
- GET    /api/v1/admin/users/{user_id}    - Get user details
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
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from loguru import logger

from core.database import get_db
from core.models import User, UserRole, Assessment
from core.auth import hash_password
from api.dependencies import get_current_user, require_admin

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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """用户列表 - 支持分页、搜索、角色和状态过滤"""
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

    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

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
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """教练列表(含负载)"""
    coaches = db.query(User).filter(
        User.role.in_([UserRole.COACH, UserRole.SUPERVISOR]),
        User.is_active == True,
    ).all()

    all_growers = db.query(User).filter(
        User.role == UserRole.GROWER, User.is_active == True
    ).all()

    result = []
    for coach in coaches:
        assigned = [g for g in all_growers if (g.profile or {}).get('coach_id') == coach.id]
        profile = coach.profile or {}
        result.append({
            "id": coach.id,
            "name": coach.full_name or coach.username,
            "username": coach.username,
            "role": coach.role.value,
            "level": profile.get("level", "L2 中级"),
            "currentLoad": len(assigned),
            "maxLoad": profile.get("max_load", 20),
            "domains": profile.get("specializations", []),
            "color": "#722ed1" if coach.role == UserRole.SUPERVISOR else "#1890ff",
        })

    return {"coaches": result}


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
