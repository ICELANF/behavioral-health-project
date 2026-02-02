"""
API依赖项
API Dependencies

提供API端点的通用依赖项，如认证、授权等
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from loguru import logger

from core.database import get_db
from core.models import User
from core.auth import verify_token

# OAuth2密码模式
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前认证用户

    从JWT token中解析用户信息并验证

    Args:
        token: JWT access token
        db: 数据库会话

    Returns:
        User: 当前用户对象

    Raises:
        HTTPException: 认证失败
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 验证Token
        payload = verify_token(token)
        if payload is None:
            raise credentials_exception

        # 获取用户ID
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception

        # 从数据库获取用户
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise credentials_exception

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户已被禁用"
            )

        return user

    except JWTError:
        raise credentials_exception
    except Exception as e:
        logger.error(f"获取当前用户失败: {str(e)}")
        raise credentials_exception


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    要求管理员权限

    Args:
        current_user: 当前用户

    Returns:
        User: 管理员用户

    Raises:
        HTTPException: 非管理员用户
    """
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


def require_coach_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    要求教练或管理员权限

    Args:
        current_user: 当前用户

    Returns:
        User: 教练或管理员用户

    Raises:
        HTTPException: 非教练/管理员用户
    """
    if current_user.role.value not in ["coach", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要教练或管理员权限"
        )
    return current_user
