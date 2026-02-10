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
    Token 黑名单 — Redis 实现

    使用 Redis SET + TTL 存储已撤销的 token 哈希，
    跨 worker 共享，token 过期后自动清理。
    Redis 不可用时降级为内存 set（单 worker 有效）。
    """

    _PREFIX = "bhp:token_blacklist:"

    def __init__(self):
        self._fallback: set = set()
        self._redis = None
        self._redis_checked = False

    def _get_redis(self):
        """延迟初始化 Redis 客户端（db=2，与 scheduler lock db=1 隔离）"""
        if self._redis_checked:
            return self._redis
        self._redis_checked = True
        try:
            import redis
            host = os.environ.get("REDIS_HOST", "localhost")
            port = int(os.environ.get("REDIS_PORT", "6379"))
            password = os.environ.get("REDIS_PASSWORD", "")
            self._redis = redis.Redis(
                host=host, port=port, password=password or None,
                db=int(os.environ.get("REDIS_BLACKLIST_DB", "2")),
                decode_responses=True, socket_timeout=2,
            )
            self._redis.ping()
            logger.info(f"[TokenBlacklist] Redis 已连接 {host}:{port} db=2")
        except Exception as e:
            self._redis = None
            logger.warning(f"[TokenBlacklist] Redis 不可用，降级为内存模式: {e}")
        return self._redis

    @staticmethod
    def _hash(token: str) -> str:
        import hashlib
        return hashlib.sha256(token.encode()).hexdigest()

    def revoke(self, token: str):
        """撤销 token — 存入 Redis（TTL = token 剩余有效期）"""
        payload = decode_token(token)
        if not payload:
            return
        token_hash = self._hash(token)
        # 计算剩余 TTL（秒），至少 60s 兜底
        exp = payload.get("exp", 0)
        ttl = max(int(exp - datetime.utcnow().timestamp()), 60)

        r = self._get_redis()
        if r is not None:
            try:
                r.setex(f"{self._PREFIX}{token_hash}", ttl, "1")
                logger.info(f"Token 已撤销 (Redis, TTL={ttl}s): {token_hash[:16]}...")
                return
            except Exception as e:
                logger.warning(f"[TokenBlacklist] Redis write 失败，降级内存: {e}")
        # fallback
        self._fallback.add(token_hash)
        logger.info(f"Token 已撤销 (内存降级): {token_hash[:16]}...")

    def is_revoked(self, token: str) -> bool:
        """检查 token 是否已撤销"""
        token_hash = self._hash(token)
        r = self._get_redis()
        if r is not None:
            try:
                return r.exists(f"{self._PREFIX}{token_hash}") > 0
            except Exception:
                pass
        return token_hash in self._fallback


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

# v18 统一角色层级（与前端 roles.ts 同步）
ROLE_LEVELS = {
    "observer": 1,      # 行为健康观察员
    "grower": 2,        # 成长者
    "sharer": 3,        # 分享者
    "coach": 4,         # 健康教练
    "promoter": 5,      # 行为健康促进师
    "supervisor": 5,    # 督导专家（与促进师同级）
    "master": 6,        # 行为健康促进大师
    "admin": 99,        # 系统管理员
    "system": 100,      # 系统账号
    # 旧角色映射（向后兼容）
    "patient": 2,       # 映射到 grower
    "provider": 4,      # 映射到 coach
}


def check_permission(user_role: str, required_role: str) -> bool:
    """
    检查用户权限

    Args:
        user_role: 用户角色
        required_role: 需要的角色

    Returns:
        是否有权限（用户等级 >= 所需等级）
    """
    user_level = ROLE_LEVELS.get(user_role.lower(), 0)
    required_level = ROLE_LEVELS.get(required_role.lower(), 0)

    return user_level >= required_level


def get_role_level(role: str) -> int:
    """获取角色权限等级"""
    return ROLE_LEVELS.get(role.lower(), 0)


def normalize_role(role: str) -> str:
    """
    标准化角色名称
    将旧角色名称转换为新标准名称
    """
    role_migration = {
        "patient": "grower",
        "患者": "grower",
        "自我管理": "grower",
        "self_manager": "grower",
        "provider": "coach",
        "医疗提供者": "coach",
    }
    lower_role = role.lower().strip()
    return role_migration.get(lower_role, lower_role)


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
    "get_role_level",
    "normalize_role",
    "ROLE_LEVELS",
    "token_blacklist",
    "TokenBlacklist",
]
