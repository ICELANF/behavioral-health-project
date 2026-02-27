"""
鉴权路由
路径前缀: /api/v3/auth
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.database import get_db
from api.schemas import APIResponse
from api.auth import (
    User, hash_password, verify_password,
    create_token_pair, decode_token,
    get_current_user, require_role,
    RegisterRequest, LoginRequest, RefreshRequest,
    UserProfile, ChangePasswordRequest, TokenPair,
)

router = APIRouter(prefix="/api/v3/auth", tags=["鉴权"])


@router.post("/register", response_model=APIResponse, summary="用户注册")
def register(
    req: RegisterRequest,
    upgrade: Optional[str] = Query(None, description="注册后自动升级角色: grower"),
    source: Optional[str] = Query(None, description="注册来源: chat_trial"),
    db: Session = Depends(get_db),
):
    """
    手机号 + 密码注册

    密码: bcrypt 散列存储, 最少 6 位
    - `upgrade=grower`: 注册后自动升级为成长者 (L1)
    - `source=chat_trial`: 标记来源为 AI 健康向导体验
    """
    existing = db.query(User).filter(User.phone == req.phone).first()
    if existing:
        raise HTTPException(status_code=409, detail="手机号已注册")

    from core.models import UserRole
    initial_role = UserRole.OBSERVER
    role_level = 1
    if upgrade and upgrade.lower() == "grower":
        initial_role = UserRole.GROWER
        role_level = 2

    user = User(
        phone=req.phone,
        username=f"u_{req.phone[-6:]}",
        email=f"{req.phone}@bhp.local",
        password_hash=hash_password(req.password),
        full_name=req.nickname or f"用户{req.phone[-4:]}",
        role=initial_role,
    )
    # 标记转化来源
    if source:
        try:
            user.conversion_source = source
        except Exception:
            pass  # 字段不存在时静默跳过
    db.add(user)
    db.commit()
    db.refresh(user)

    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    tokens = create_token_pair(user.id, role_str)
    return APIResponse(data={
        "user": {**UserProfile.model_validate(user).model_dump(), "role_level": role_level},
        "tokens": tokens.model_dump(),
    })


@router.post("/login", response_model=APIResponse, summary="登录")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """
    手机号 + 密码登录 → 返回 access_token + refresh_token
    """
    user = db.query(User).filter(User.phone == req.phone).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="手机号或密码错误")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已停用")

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    tokens = create_token_pair(user.id, role_str)
    return APIResponse(data={
        "user": UserProfile.model_validate(user).model_dump(),
        "tokens": tokens.model_dump(),
    })


@router.post("/refresh", response_model=APIResponse, summary="刷新 Token")
def refresh_token(req: RefreshRequest, db: Session = Depends(get_db)):
    """
    用 refresh_token 换取新的 token 对

    refresh_token 有效期 7 天, access_token 2 小时
    """
    payload = decode_token(req.refresh_token)
    if payload.token_type != "refresh":
        raise HTTPException(status_code=400, detail="请提供 refresh_token")

    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已停用")

    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    tokens = create_token_pair(user.id, role_str)
    return APIResponse(data=tokens.model_dump())


@router.get("/me", response_model=APIResponse, summary="获取当前用户信息")
def get_me(user: User = Depends(get_current_user)):
    return APIResponse(data=UserProfile.model_validate(user).model_dump())


@router.put("/password", response_model=APIResponse, summary="修改密码")
def change_password(
    req: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(req.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")

    user.password_hash = hash_password(req.new_password)
    db.commit()
    return APIResponse(message="密码已修改")


@router.put("/profile", response_model=APIResponse, summary="更新个人信息")
def update_profile(
    nickname: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if nickname is not None:
        user.full_name = nickname
    db.commit()
    return APIResponse(data=UserProfile.model_validate(user).model_dump())


# ── Admin 专用 ──

@router.get("/users", response_model=APIResponse, summary="用户列表 (Admin)")
def list_users(
    page: int = 1,
    page_size: int = 20,
    role: str | None = None,
    _admin: User = Depends(require_role("admin", "bhp_master")),
    db: Session = Depends(get_db),
):
    """管理员查看用户列表"""
    q = db.query(User)
    if role:
        q = q.filter(User.role == role)

    total = q.count()
    users = q.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return APIResponse(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "users": [UserProfile.model_validate(u).model_dump() for u in users],
    })


@router.put("/users/{user_id}/role", response_model=APIResponse, summary="修改用户角色 (Admin)")
def update_role(
    user_id: int,
    new_role: str,
    _admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """仅 admin 可修改角色"""
    new_role = new_role.strip().upper()
    valid_roles = {"USER", "COACH", "MASTER", "ADMIN", "OBSERVER"}
    if new_role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"无效角色, 可选: {valid_roles}")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.role = new_role
    db.commit()
    return APIResponse(message=f"用户 {user_id} 角色已改为 {new_role}")
