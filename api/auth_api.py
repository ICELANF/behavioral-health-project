"""
认证API端点
Authentication API Endpoints

端点：
- POST /auth/register: 用户注册
- POST /auth/login: 用户登录
- POST /auth/refresh: 刷新token
- POST /auth/logout: 登出
- GET /auth/me: 获取当前用户信息
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from core.database import get_db
from core.models import User, UserRole, UserSession, UserActivityLog
from core.auth import (
    hash_password, authenticate_user, create_user_tokens,
    verify_token, verify_token_with_blacklist
)
from loguru import logger

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])
security = HTTPBearer()

# 登录限流：每个IP每分钟最多10次登录尝试
_login_attempts: dict = {}  # ip -> [timestamp, ...]

def _check_login_rate(client_ip: str, max_attempts: int = 10, window: int = 60):
    """检查登录频率限制"""
    import time
    now = time.time()
    window_start = now - window
    if client_ip in _login_attempts:
        _login_attempts[client_ip] = [t for t in _login_attempts[client_ip] if t > window_start]
    else:
        _login_attempts[client_ip] = []
    if len(_login_attempts[client_ip]) >= max_attempts:
        raise HTTPException(
            status_code=429,
            detail="登录尝试过于频繁，请稍后再试"
        )
    _login_attempts[client_ip].append(now)

# 角色名称规范化映射（旧角色 → 新角色）
ROLE_MIGRATION_MAP = {
    "patient": "grower",      # 患者 → 成长者
    "provider": "coach",      # 医疗提供者 → 健康教练
}


def normalize_role(role: str) -> str:
    """规范化角色名称，将旧角色映射到新角色"""
    role_value = role.value if hasattr(role, 'value') else str(role)
    return ROLE_MIGRATION_MAP.get(role_value.lower(), role_value.lower())


# ============================================
# Pydantic 模型
# ============================================

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None


class LoginRequest(BaseModel):
    username: str  # 可以是用户名或邮箱
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime


# ============================================
# 依赖注入：获取当前用户
# ============================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    从token获取当前用户

    用于API路由的依赖注入
    """
    token = credentials.credentials

    # 验证token（含黑名单检查）
    payload = verify_token_with_blacklist(token, "access")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的token",
        )

    # 查询用户
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )

    return user


# ============================================
# API端点
# ============================================

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    用户注册

    创建新用户并返回认证token
    """
    # 检查用户名是否存在
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 检查邮箱是否存在
    existing_email = db.query(User).filter(User.email == request.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )

    # 密码强度验证
    if len(request.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度不能少于6位"
        )

    # 创建新用户（默认角色为观察员）
    new_user = User(
        username=request.username,
        email=request.email,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        phone=request.phone,
        role=UserRole.OBSERVER,  # 默认为观察员角色（L0）
        is_active=True,
        is_verified=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"新用户注册: {request.username} (ID: {new_user.id})")

    # 生成token
    tokens = create_user_tokens(
        user_id=new_user.id,
        username=new_user.username,
        role=new_user.role.value
    )

    # 规范化角色名称
    normalized_role = normalize_role(new_user.role)
    return TokenResponse(
        **tokens,
        user={
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "role": normalized_role,
            "full_name": new_user.full_name,
            "intervention_stage": getattr(new_user, 'intervention_stage', None)
        }
    )


@router.post("/login", response_model=TokenResponse)
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    用户登录

    使用用户名/邮箱和密码登录（OAuth2 Password Flow）
    """
    try:
        # 登录频率限制
        client_ip = request.client.host if request.client else "unknown"
        _check_login_rate(client_ip)

        logger.info(f"[LOGIN] Received login request - username: {form_data.username}")

        # 查询用户（支持用户名或邮箱登录）
        def get_user(identifier: str):
            user = db.query(User).filter(
                (User.username == identifier) | (User.email == identifier)
            ).first()
            logger.info(f"[LOGIN] Database query - found user: {user.username if user else 'None'}")
            return user

        # 认证用户
        logger.info(f"[LOGIN] Starting authentication...")
        user = authenticate_user(form_data.username, form_data.password, get_user)
        logger.info(f"[LOGIN] Authentication result: {'SUCCESS - ' + user.username if user else 'FAILED'}")

        if not user:
            logger.warning(f"[LOGIN] Authentication failed - invalid credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()

        # 记录登录活动
        try:
            activity = UserActivityLog(
                user_id=user.id,
                activity_type="login",
                detail={"ip": client_ip, "username": user.username},
                created_at=datetime.utcnow(),
            )
            db.add(activity)
        except Exception:
            pass  # 活动日志不影响登录流程

        db.commit()

        logger.info(f"[LOGIN] User logged in successfully: {user.username} (ID: {user.id})")

        # 生成token
        logger.info(f"[LOGIN] Generating tokens...")
        tokens = create_user_tokens(
            user_id=user.id,
            username=user.username,
            role=user.role.value
        )

        logger.info(f"[LOGIN] Tokens generated successfully")
        # 规范化角色名称（兼容旧数据）
        normalized_role = normalize_role(user.role)
        return TokenResponse(
            **tokens,
            user={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": normalized_role,
                "full_name": user.full_name,
                "intervention_stage": getattr(user, 'intervention_stage', None)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[LOGIN] Unexpected error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录过程发生错误"
        )


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前用户信息

    需要认证
    """
    # 规范化角色名称（兼容旧数据）
    normalized_role = normalize_role(current_user.role)
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": normalized_role,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "intervention_stage": getattr(current_user, 'intervention_stage', None)
    }


@router.post("/refresh")
def refresh_token(
    refresh_token: str = None,
    db: Session = Depends(get_db)
):
    """
    刷新访问令牌

    使用 refresh_token 获取新的 access_token
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少 refresh_token"
        )

    payload = verify_token(refresh_token, "refresh")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的刷新令牌"
        )

    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用"
        )

    tokens = create_user_tokens(
        user_id=user.id,
        username=user.username,
        role=user.role.value
    )

    normalized_role = normalize_role(user.role)
    return TokenResponse(
        **tokens,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": normalized_role,
            "full_name": user.full_name,
        }
    )


@router.put("/password")
async def change_password(
    old_password: str = None,
    new_password: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改密码
    """
    if not old_password or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请提供旧密码和新密码"
        )

    from core.auth import verify_password
    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )

    if len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码长度不能少于6位"
        )

    current_user.password_hash = hash_password(new_password)
    db.commit()

    logger.info(f"用户修改密码: {current_user.username}")
    return {"message": "密码修改成功"}


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
):
    """
    用户登出

    将token加入黑名单
    """
    from core.auth import token_blacklist
    token_blacklist.revoke(credentials.credentials)
    logger.info(f"用户登出: {current_user.username} (ID: {current_user.id})")
    return {"message": "登出成功"}


# 导出router
__all__ = ["router", "get_current_user"]
