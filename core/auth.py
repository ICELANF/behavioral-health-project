"""
认证与授权模块
Authentication and Authorization Module

功能：
- 密码哈希与验证
- JWT Token生成与验证
- 用户认证
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from loguru import logger

# 加载环境变量
load_dotenv()

# JWT配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
if not SECRET_KEY:
    logger.warning(
        "[Auth] JWT_SECRET_KEY 未设置！生产环境必须设置此变量。"
        "当前使用临时密钥（仅限开发）。"
    )
    import hashlib
    SECRET_KEY = hashlib.sha256(b"dev-only-behavioral-health-2026").hexdigest()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================
# 密码哈希
# ============================================

def hash_password(password: str) -> str:
    """
    密码哈希

    Args:
        password: 明文密码

    Returns:
        哈希后的密码
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============================================
# JWT Token
# ============================================

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌

    Args:
        data: 要编码的数据（通常包含user_id, username等）
        expires_delta: 过期时间增量

    Returns:
        JWT token字符串
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict) -> str:
    """
    创建刷新令牌

    Args:
        data: 要编码的数据

    Returns:
        JWT refresh token字符串
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict]:
    """
    解码JWT token

    Args:
        token: JWT token字符串

    Returns:
        解码后的数据字典，如果失败返回None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"Token解码失败: {e}")
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[Dict]:
    """
    验证token并检查类型

    Args:
        token: JWT token
        token_type: token类型（access或refresh）

    Returns:
        payload或None
    """
    payload = decode_token(token)

    if payload is None:
        return None

    # 检查token类型
    if payload.get("type") != token_type:
        logger.warning(f"Token类型不匹配: 期望{token_type}, 实际{payload.get('type')}")
        return None

    return payload


# ============================================
# 用户认证
# ============================================

def authenticate_user(username: str, password: str, get_user_func) -> Optional[Dict]:
    """
    认证用户

    Args:
        username: 用户名或邮箱
        password: 密码
        get_user_func: 获取用户的函数（通过username/email查询）

    Returns:
        用户信息字典或None
    """
    user = get_user_func(username)

    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    if not user.is_active:
        logger.warning(f"用户{username}已被禁用")
        return None

    return user


def create_user_tokens(user_id: int, username: str, role: str) -> Dict[str, str]:
    """
    为用户创建访问令牌和刷新令牌

    Args:
        user_id: 用户ID
        username: 用户名
        role: 用户角色

    Returns:
        包含access_token和refresh_token的字典
    """
    token_data = {
        "user_id": user_id,
        "username": username,
        "role": role
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


# ============================================
# Token 撤销（黑名单机制）
# ============================================

class TokenBlacklist:
    """
    Token 黑名单

    内存实现，生产环境应替换为 Redis
    """

    def __init__(self):
        self._blacklist: set = set()

    def revoke(self, token: str):
        """撤销 token"""
        payload = decode_token(token)
        if payload:
            # 用 jti 或整个 token 的哈希
            import hashlib
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            self._blacklist.add(token_hash)
            logger.info(f"Token 已撤销: {token_hash[:16]}...")

    def is_revoked(self, token: str) -> bool:
        """检查 token 是否已撤销"""
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return token_hash in self._blacklist


# 全局黑名单实例
token_blacklist = TokenBlacklist()


def verify_token_with_blacklist(token: str, token_type: str = "access") -> Optional[Dict]:
    """验证 token（含黑名单检查）"""
    if token_blacklist.is_revoked(token):
        logger.warning("Token 已被撤销")
        return None
    return verify_token(token, token_type)


# ============================================
# 权限检查
# ============================================

def check_permission(user_role: str, required_role: str) -> bool:
    """
    检查用户权限

    Args:
        user_role: 用户角色
        required_role: 需要的角色

    Returns:
        是否有权限
    """
    # 角色层级
    role_hierarchy = {
        "admin": 3,
        "coach": 2,
        "patient": 1,
        "system": 0
    }

    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 0)

    return user_level >= required_level


# ============================================
# 导出
# ============================================

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_token",
    "verify_token_with_blacklist",
    "authenticate_user",
    "create_user_tokens",
    "check_permission",
    "token_blacklist",
    "TokenBlacklist",
]
