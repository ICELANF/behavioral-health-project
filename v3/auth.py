"""
JWT 鉴权模块 — 用户模型 + 密码 + Token
放置: api/auth.py

安全设计:
  - 密码: bcrypt 散列, 永不存明文
  - Token: JWT HS256, 含 user_id + role, 可配置过期
  - 刷新: access_token 2h + refresh_token 7d
  - 角色: user / bhp_coach / bhp_promoter / bhp_master / admin
"""
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from v3.database import Base, get_db


# ══════════════════════════════════════════════
# 配置
# ══════════════════════════════════════════════

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "bhp-v3-dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


# ══════════════════════════════════════════════
# 用户模型 (SQLAlchemy ORM)
# ══════════════════════════════════════════════

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    nickname = Column(String(64), default="")
    avatar_url = Column(String(256), default="")
    role = Column(String(32), default="user", index=True)     # user/bhp_coach/bhp_promoter/bhp_master/admin
    is_active = Column(Boolean, default=True)
    # v3.1 扩展字段
    health_competency_level = Column(String(4), default="Lv0")
    current_stage = Column(String(4), default="S0")
    growth_level = Column(String(4), default="G0")
    # 时间
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime, nullable=True)


# ══════════════════════════════════════════════
# 密码工具
# ══════════════════════════════════════════════

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ══════════════════════════════════════════════
# Token 工具
# ══════════════════════════════════════════════

class TokenPayload(BaseModel):
    user_id: int
    role: str = "user"
    exp: float = 0
    token_type: str = "access"   # access / refresh


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int              # access_token 秒数


def create_access_token(user_id: int, role: str = "user") -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int, role: str = "user") -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_token_pair(user_id: int, role: str = "user") -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user_id, role),
        refresh_token=create_refresh_token(user_id, role),
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def decode_token(token: str) -> TokenPayload:
    """解码并验证 JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenPayload(
            user_id=int(payload["sub"]),
            role=payload.get("role", "user"),
            exp=payload.get("exp", 0),
            token_type=payload.get("type", "access"),
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token 无效: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ══════════════════════════════════════════════
# FastAPI 依赖注入
# ══════════════════════════════════════════════

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    核心鉴权依赖: 从 Bearer Token 提取当前用户

    用法:
        @router.get("/me")
        def get_me(user: User = Depends(get_current_user)):
            return user
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)

    if payload.token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请使用 access_token (非 refresh_token)",
        )

    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已停用")

    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """可选鉴权: 有 Token 就解析, 没有返回 None"""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def require_role(*roles: str):
    """
    角色权限装饰器工厂

    用法:
        @router.get("/admin/stats")
        def admin_stats(user: User = Depends(require_role("admin", "bhp_master"))):
            ...
    """
    async def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要角色: {', '.join(roles)}, 当前: {user.role}",
            )
        return user
    return _check


# ══════════════════════════════════════════════
# 请求/响应 Schema
# ══════════════════════════════════════════════

class RegisterRequest(BaseModel):
    phone: str = Field(..., min_length=11, max_length=11, pattern=r"^1\d{10}$")
    password: str = Field(..., min_length=6, max_length=32)
    nickname: str = Field("", max_length=64)


class LoginRequest(BaseModel):
    phone: str = Field(..., min_length=11, max_length=11)
    password: str = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    refresh_token: str


class UserProfile(BaseModel):
    id: int
    phone: str
    nickname: str
    role: str
    current_stage: str
    growth_level: str
    health_competency_level: str
    is_active: bool
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=32)
