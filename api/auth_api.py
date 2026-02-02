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
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from core.database import get_db
from core.models import User, UserRole, UserSession
from core.auth import (
    hash_password, authenticate_user, create_user_tokens, verify_token
)
from loguru import logger

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])
security = HTTPBearer()


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

    # 验证token
    payload = verify_token(token, "access")
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

    # 创建新用户
    new_user = User(
        username=request.username,
        email=request.email,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        phone=request.phone,
        role=UserRole.PATIENT,  # 默认为患者角色
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

    return TokenResponse(
        **tokens,
        user={
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "role": new_user.role.value
        }
    )


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    用户登录

    使用用户名/邮箱和密码登录（OAuth2 Password Flow）
    """
    try:
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
        return TokenResponse(
            **tokens,
            user={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "full_name": user.full_name
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


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前用户信息

    需要认证
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role.value,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    用户登出

    实际实现可以将token加入黑名单
    """
    logger.info(f"用户登出: {current_user.username} (ID: {current_user.id})")

    return {"message": "登出成功"}


# 导出router
__all__ = ["router", "get_current_user"]
