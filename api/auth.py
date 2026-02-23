"""
JWT Auth module - v3 compatible bridge.
Uses core.models.User + provides v3-style auth functions (jose JWT).
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
from sqlalchemy.orm import Session

from core.models import User  # noqa: F401 - re-export core User
from core.database import get_db  # noqa: F401

# ==============================================
# Config
# ==============================================

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "bhp-v3-dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


# ==============================================
# Password utils
# ==============================================

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ==============================================
# Token utils
# ==============================================

class TokenPayload(BaseModel):
    user_id: int
    role: str = "user"
    exp: float = 0
    token_type: str = "access"


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


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
            detail=f"Token invalid: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ==============================================
# FastAPI Dependencies
# ==============================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing auth token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    if payload.token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Use access_token (not refresh_token)",
        )
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if not credentials:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def require_role(*roles: str):
    async def _check(user: User = Depends(get_current_user)) -> User:
        user_role = (user.role.value if hasattr(user.role, "value") else str(user.role)).lower()
        if user_role not in {r.lower() for r in roles}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {', '.join(roles)}, current: {user_role}",
            )
        return user
    return _check


# ==============================================
# Pydantic Schemas
# ==============================================

class RegisterRequest(BaseModel):
    phone: str = Field(..., min_length=11, max_length=11, pattern=r"^1\d{10}$")
    password: str = Field(..., min_length=6, max_length=32)
    nickname: str = Field("", max_length=64)


class LoginRequest(BaseModel):
    phone: str = Field(..., min_length=11, max_length=11)
    password: str = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    refresh_token: str


_ROLE_LEVELS = {
    "observer": 1, "grower": 2, "sharer": 3, "coach": 4,
    "promoter": 5, "supervisor": 5, "master": 6, "admin": 99,
}


class UserProfile(BaseModel):
    id: int
    phone: str = ""
    nickname: str = ""
    role: str = ""
    role_level: int = 1
    is_active: bool = True
    created_at: datetime | None = None

    class Config:
        from_attributes = True

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Handle core.models.User → UserProfile mapping."""
        if hasattr(obj, "__table__"):
            role_val = obj.role.value if hasattr(obj.role, "value") else str(obj.role or "")
            return cls(
                id=obj.id,
                phone=obj.phone or "",
                nickname=getattr(obj, "full_name", None) or "",
                role=role_val,
                role_level=_ROLE_LEVELS.get(role_val.lower(), 1),
                is_active=obj.is_active if obj.is_active is not None else True,
                created_at=getattr(obj, "created_at", None),
            )
        return super().model_validate(obj, **kwargs)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=32)
