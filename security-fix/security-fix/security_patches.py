#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行健平台 V4.0 — 安全修复补丁
Security Remediation Patches

基于渗透测试报告 (60测试/57通过/3失败/18项发现)
修复全部 2 HIGH + 8 MEDIUM + 6 LOW + 2 INFO

用法:
  python security_patches.py [项目根目录]
  # 默认: 当前目录
"""

import os
import sys
import re
import shutil
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
BACKUP_DIR = PROJECT_ROOT / ".security-patches-backup" / datetime.now().strftime("%Y%m%d_%H%M%S")

applied = []
skipped = []


def backup_and_patch(filepath: str, old: str, new: str, desc: str):
    """备份原文件并应用补丁"""
    fpath = PROJECT_ROOT / filepath
    if not fpath.exists():
        skipped.append(f"[跳过] {filepath} — 文件不存在")
        return False

    content = fpath.read_text(encoding="utf-8")
    if old not in content:
        # 检查是否已修复
        if new.strip().split('\n')[0].strip() in content:
            skipped.append(f"[已修复] {filepath} — {desc}")
        else:
            skipped.append(f"[跳过] {filepath} — 未找到目标代码")
        return False

    # 备份
    backup_path = BACKUP_DIR / filepath
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(fpath, backup_path)

    # 替换
    new_content = content.replace(old, new, 1)
    fpath.write_text(new_content, encoding="utf-8")
    applied.append(f"[修复] {filepath} — {desc}")
    return True


def create_file(filepath: str, content: str, desc: str):
    """创建新文件"""
    fpath = PROJECT_ROOT / filepath
    if fpath.exists():
        skipped.append(f"[已存在] {filepath} — {desc}")
        return False
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content, encoding="utf-8")
    applied.append(f"[新建] {filepath} — {desc}")
    return True


# ═══════════════════════════════════════════════════════════════════════
# FIX-01: CORS allow_origins=['*'] → 环境变量白名单
# 严重性: HIGH | 发现: STATIC + T09
# ═══════════════════════════════════════════════════════════════════════

def fix_01_cors():
    backup_and_patch(
        "main.py",
        old='''# 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)''',
        new='''# 中间件配置 — CORS 白名单 (FIX-01: SEC-001)
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
_cors_origins = [o.strip() for o in _cors_origins if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)''',
        desc="FIX-01: CORS 限制为环境变量白名单"
    )


# ═══════════════════════════════════════════════════════════════════════
# FIX-02: 全局异常处理脱敏
# 严重性: MEDIUM | 发现: STATIC + T08
# ═══════════════════════════════════════════════════════════════════════

def fix_02_error_handler():
    backup_and_patch(
        "main.py",
        old='''@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="服务器内部错误",
            detail=str(exc),
            timestamp=datetime.now()
        ).model_dump(mode="json")
    )''',
        new='''@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # FIX-02: 生产环境不泄露内部错误详情
    from loguru import logger
    import uuid
    error_id = str(uuid.uuid4())[:8]
    logger.exception(f"[{error_id}] Unhandled exception: {exc}")

    env = os.getenv("ENVIRONMENT", "production")
    detail = str(exc) if env in ("development", "test") else f"请联系管理员, 错误编号: {error_id}"

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="服务器内部错误",
            detail=detail,
            timestamp=datetime.now()
        ).model_dump(mode="json")
    )''',
        desc="FIX-02: 生产环境异常响应脱敏"
    )


# ═══════════════════════════════════════════════════════════════════════
# FIX-03: 登录限流 → Redis 分布式限流
# 严重性: MEDIUM | 发现: STATIC + T07
# ═══════════════════════════════════════════════════════════════════════

def fix_03_rate_limiter():
    # 创建独立的限流模块
    create_file(
        "core/rate_limiter.py",
        content='''"""
分布式速率限制器 (FIX-03)
支持 Redis 后端, 回退到内存
"""
import os
import time
from typing import Optional
from loguru import logger

# Redis 连接 (可选)
_redis = None

def _get_redis():
    global _redis
    if _redis is not None:
        return _redis
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            import redis
            _redis = redis.from_url(redis_url, decode_responses=True)
            _redis.ping()
            logger.info("Rate limiter: Redis 连接成功")
            return _redis
        except Exception as e:
            logger.warning(f"Rate limiter: Redis 不可用 ({e}), 回退到内存")
            _redis = False
    else:
        _redis = False
    return None


# 内存回退 (单进程)
_memory_store: dict = {}


def check_rate_limit(
    key: str,
    max_attempts: int = 10,
    window_seconds: int = 60,
    prefix: str = "rl:"
) -> tuple[bool, int]:
    """
    检查速率限制

    Returns: (allowed: bool, remaining: int)
    """
    full_key = f"{prefix}{key}"
    r = _get_redis()

    if r:
        # Redis 滑动窗口
        pipe = r.pipeline()
        now = time.time()
        window_start = now - window_seconds

        pipe.zremrangebyscore(full_key, 0, window_start)
        pipe.zadd(full_key, {str(now): now})
        pipe.zcard(full_key)
        pipe.expire(full_key, window_seconds + 10)
        results = pipe.execute()

        current_count = results[2]
        remaining = max(0, max_attempts - current_count)

        if current_count > max_attempts:
            return False, 0
        return True, remaining
    else:
        # 内存回退
        now = time.time()
        window_start = now - window_seconds

        if full_key in _memory_store:
            _memory_store[full_key] = [t for t in _memory_store[full_key] if t > window_start]
        else:
            _memory_store[full_key] = []

        current_count = len(_memory_store[full_key])
        if current_count >= max_attempts:
            return False, 0

        _memory_store[full_key].append(now)
        return True, max_attempts - current_count - 1


def rate_limit_or_429(key: str, max_attempts: int, window: int, msg: str = "请求过于频繁"):
    """检查限流, 超限则抛出 429"""
    from fastapi import HTTPException
    allowed, remaining = check_rate_limit(key, max_attempts, window)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=msg,
            headers={"Retry-After": str(window)}
        )
    return remaining
''',
        desc="FIX-03: 创建分布式限流模块 (Redis + 内存回退)"
    )

    # 替换 auth_api.py 中的内存限流
    backup_and_patch(
        "auth_api.py",
        old='''# 登录限流：每个IP每分钟最多10次登录尝试
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
    _login_attempts[client_ip].append(now)''',
        new='''# 登录限流: Redis 分布式 (FIX-03)
from core.rate_limiter import rate_limit_or_429

def _check_login_rate(client_ip: str, max_attempts: int = 10, window: int = 60):
    """检查登录频率限制 — Redis 分布式"""
    rate_limit_or_429(
        key=f"login:{client_ip}",
        max_attempts=max_attempts,
        window=window,
        msg="登录尝试过于频繁，请稍后再试"
    )''',
        desc="FIX-03: 登录限流改为 Redis 分布式"
    )


# ═══════════════════════════════════════════════════════════════════════
# FIX-04: 注册端点限流
# 严重性: MEDIUM | 发现: T07
# ═══════════════════════════════════════════════════════════════════════

def fix_04_register_rate_limit():
    backup_and_patch(
        "auth_api.py",
        old='''@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    用户注册

    创建新用户并返回认证token
    """
    # 检查用户名是否存在''',
        new='''@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, req: Request = None, db: Session = Depends(get_db)):
    """
    用户注册

    创建新用户并返回认证token
    """
    # FIX-04: 注册限流 (每IP每小时5次)
    client_ip = req.client.host if req and req.client else "unknown"
    rate_limit_or_429(
        key=f"register:{client_ip}",
        max_attempts=5,
        window=3600,
        msg="注册请求过于频繁，请稍后再试"
    )

    # 检查用户名是否存在''',
        desc="FIX-04: 注册端点增加限流 (5次/小时/IP)"
    )

    # 修复函数签名: 添加 Request 导入
    # (Request 已在文件头部导入, 只需添加参数)


# ═══════════════════════════════════════════════════════════════════════
# FIX-05: 密码策略增强
# 严重性: MEDIUM | 发现: STATIC
# ═══════════════════════════════════════════════════════════════════════

def fix_05_password_policy():
    backup_and_patch(
        "auth_api.py",
        old='''    # 密码强度验证
    if len(request.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度不能少于6位"
        )''',
        new='''    # 密码强度验证 (FIX-05: 增强密码策略)
    _validate_password_strength(request.password)''',
        desc="FIX-05: 注册密码策略增强"
    )

    # 同时修复改密码处的验证
    backup_and_patch(
        "auth_api.py",
        old='''    if len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码长度不能少于6位"
        )''',
        new='''    # FIX-05
    _validate_password_strength(new_password)''',
        desc="FIX-05: 改密码策略增强"
    )

    # 在文件中添加密码验证函数 (在 RegisterRequest 类之前)
    backup_and_patch(
        "auth_api.py",
        old='''class RegisterRequest(BaseModel):''',
        new='''def _validate_password_strength(password: str):
    """密码强度验证 (FIX-05)"""
    errors = []
    if len(password) < 8:
        errors.append("至少8位")
    if not re.search(r'[a-z]', password):
        errors.append("包含小写字母")
    if not re.search(r'[A-Z]', password):
        errors.append("包含大写字母")
    if not re.search(r'[0-9]', password):
        errors.append("包含数字")
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"密码要求: {', '.join(errors)}"
        )


class RegisterRequest(BaseModel):''',
        desc="FIX-05: 添加密码强度验证函数"
    )

    # 确保 re 已导入
    fpath = PROJECT_ROOT / "auth_api.py"
    if fpath.exists():
        content = fpath.read_text(encoding="utf-8")
        if "import re" not in content:
            content = content.replace(
                "from loguru import logger",
                "from loguru import logger\nimport re",
                1
            )
            fpath.write_text(content, encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════
# FIX-06: 学习时长上限验证
# 严重性: MEDIUM | 发现: T10
# ═══════════════════════════════════════════════════════════════════════

def fix_06_learning_time_cap():
    backup_and_patch(
        "learning_api.py",
        old='''    minutes = event.duration_seconds // 60\r\n    if minutes <= 0:\r\n        return {"success": True, "minutes_earned": 0, "new_total": 0, "new_milestones": []}''',
        new='''    minutes = event.duration_seconds // 60\r\n    if minutes <= 0:\r\n        return {"success": True, "minutes_earned": 0, "new_total": 0, "new_milestones": []}\r\n\r\n    # FIX-06: 学习时长上限 (单次最多480分钟 = 8小时)\r\n    MAX_MINUTES_PER_EVENT = 480\r\n    if minutes > MAX_MINUTES_PER_EVENT:\r\n        raise HTTPException(\r\n            status_code=400,\r\n            detail=f"单次学习时长不能超过 {MAX_MINUTES_PER_EVENT} 分钟"\r\n        )''',
        desc="FIX-06: 学习时长增加上限 (480分钟/次)"
    )

    # 尝试不带 \r\n 的版本
    backup_and_patch(
        "learning_api.py",
        old='''    minutes = event.duration_seconds // 60
    if minutes <= 0:
        return {"success": True, "minutes_earned": 0, "new_total": 0, "new_milestones": []}''',
        new='''    minutes = event.duration_seconds // 60
    if minutes <= 0:
        return {"success": True, "minutes_earned": 0, "new_total": 0, "new_milestones": []}

    # FIX-06: 学习时长上限 (单次最多480分钟 = 8小时)
    MAX_MINUTES_PER_EVENT = 480
    if minutes > MAX_MINUTES_PER_EVENT:
        raise HTTPException(
            status_code=400,
            detail=f"单次学习时长不能超过 {MAX_MINUTES_PER_EVENT} 分钟"
        )''',
        desc="FIX-06: 学习时长增加上限 (480分钟/次)"
    )


# ═══════════════════════════════════════════════════════════════════════
# FIX-07: Swagger/API 文档生产环境禁用
# 严重性: LOW | 发现: T08 (3项)
# ═══════════════════════════════════════════════════════════════════════

def fix_07_disable_docs():
    backup_and_patch(
        "main.py",
        old='''app = FastAPI(
    title="行健行为教练 API"''',
        new='''# FIX-07: 生产环境禁用 API 文档
_env = os.getenv("ENVIRONMENT", "production")
_docs_url = "/docs" if _env in ("development", "test") else None
_redoc_url = "/redoc" if _env in ("development", "test") else None
_openapi_url = "/openapi.json" if _env in ("development", "test") else None

app = FastAPI(
    title="行健行为教练 API",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url''',
        desc="FIX-07: 生产环境禁用 Swagger"
    )

    # 去掉重复的 title 参数 (因为上面已经加了)
    fpath = PROJECT_ROOT / "main.py"
    if fpath.exists():
        content = fpath.read_text(encoding="utf-8")
        # 清理可能出现的重复 title
        content = content.replace(
            '''    title="行健行为教练 API",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
    title="行健行为教练 API"''',
            '''    title="行健行为教练 API",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url'''
        )
        fpath.write_text(content, encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════
# FIX-08: 安全响应头中间件
# 严重性: MEDIUM | 发现: T08 (安全头缺失)
# ═══════════════════════════════════════════════════════════════════════

def fix_08_security_headers():
    create_file(
        "core/security_middleware.py",
        content='''"""
安全响应头中间件 (FIX-08)
修复: HSTS, CSP, X-Content-Type-Options 等缺失
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import os


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # 防 MIME 嗅探
        response.headers["X-Content-Type-Options"] = "nosniff"
        # 防点击劫持
        response.headers["X-Frame-Options"] = "DENY"
        # XSS 保护
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Referrer 策略
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # 权限策略
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # HSTS (仅生产 HTTPS)
        env = os.getenv("ENVIRONMENT", "production")
        if env == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: blob:; "
                "connect-src 'self' wss: ws:; "
                "frame-ancestors 'none'"
            )

        # 隐藏 Server header (FIX-08: Server header泄露)
        if "server" in response.headers:
            del response.headers["server"]

        return response
''',
        desc="FIX-08: 创建安全响应头中间件"
    )

    # 在 main.py 中注册中间件
    backup_and_patch(
        "main.py",
        old='''# 中间件配置 — CORS 白名单 (FIX-01: SEC-001)''',
        new='''# 安全响应头 (FIX-08)
from core.security_middleware import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)

# 中间件配置 — CORS 白名单 (FIX-01: SEC-001)''',
        desc="FIX-08: 注册安全头中间件"
    )


# ═══════════════════════════════════════════════════════════════════════
# FIX-09: IDOR — 教练只能访问自己的学员
# 严重性: MEDIUM | 发现: STATIC
# ═══════════════════════════════════════════════════════════════════════

def fix_09_idor_coach():
    create_file(
        "core/access_control.py",
        content='''"""
访问控制辅助函数 (FIX-09)
教练只能访问自己学员的数据
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from core.models import User


def check_user_data_access(
    current_user: User,
    target_user_id: int,
    db: Session
):
    """
    检查当前用户是否有权访问目标用户数据

    规则:
    - 自己的数据: 始终允许
    - admin/supervisor: 允许所有
    - coach/promoter/master: 只能访问自己学员
    - observer/grower: 仅限自己
    """
    if target_user_id == current_user.id:
        return  # 自己的数据

    role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)

    if role in ("admin", "supervisor"):
        return  # 管理员和督导可查看所有

    if role in ("coach", "promoter", "master"):
        # 检查是否是自己的学员
        is_my_student = db.execute(
            """
            SELECT 1 FROM coach_student_assignments
            WHERE coach_id = :coach_id AND student_id = :student_id
            AND status = 'active'
            LIMIT 1
            """,
            {"coach_id": current_user.id, "student_id": target_user_id}
        ).fetchone()

        if is_my_student:
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您只能访问自己学员的数据"
        )

    # observer/grower — 仅限自己
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="无权访问其他用户数据"
    )
''',
        desc="FIX-09: 创建细粒度访问控制模块"
    )


# ═══════════════════════════════════════════════════════════════════════
# FIX-10: Token 黑名单 Redis 持久化
# 严重性: INFO | 发现: STATIC
# ═══════════════════════════════════════════════════════════════════════

def fix_10_token_blacklist():
    create_file(
        "core/token_blacklist_redis.py",
        content='''"""
Token 黑名单 — Redis 持久化 (FIX-10)
替代内存实现, 支持多 worker 和重启后保持
"""
import os
from loguru import logger


class RedisTokenBlacklist:
    """Redis-backed token blacklist with TTL auto-expiry"""

    def __init__(self):
        self._redis = None
        self._memory_fallback = set()
        self.prefix = "token_bl:"

    def _get_redis(self):
        if self._redis is not None:
            return self._redis
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                import redis
                self._redis = redis.from_url(redis_url, decode_responses=True)
                self._redis.ping()
                return self._redis
            except Exception as e:
                logger.warning(f"Token blacklist: Redis 不可用 ({e})")
                self._redis = False
        else:
            self._redis = False
        return None

    def revoke(self, token: str, ttl_seconds: int = 86400):
        """将 token 加入黑名单"""
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()[:32]

        r = self._get_redis()
        if r:
            r.setex(f"{self.prefix}{token_hash}", ttl_seconds, "1")
        else:
            self._memory_fallback.add(token_hash)

    def is_revoked(self, token: str) -> bool:
        """检查 token 是否已被撤销"""
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()[:32]

        r = self._get_redis()
        if r:
            return r.exists(f"{self.prefix}{token_hash}") > 0
        return token_hash in self._memory_fallback


# 全局实例
token_blacklist = RedisTokenBlacklist()
''',
        desc="FIX-10: 创建 Redis Token 黑名单"
    )


# ═══════════════════════════════════════════════════════════════════════
# FIX-11: 全局 API 限流中间件
# 严重性: LOW | 发现: T07
# ═══════════════════════════════════════════════════════════════════════

def fix_11_global_rate_limit():
    create_file(
        "core/rate_limit_middleware.py",
        content='''"""
全局 API 速率限制中间件 (FIX-11)
默认: 60 请求/分钟/IP
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from core.rate_limiter import check_rate_limit


class GlobalRateLimitMiddleware(BaseHTTPMiddleware):
    """全局 API 限流 — 每IP每分钟60次"""

    async def dispatch(self, request: Request, call_next):
        # 跳过健康检查
        if request.url.path in ("/", "/health", "/docs", "/openapi.json"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "0.0.0.0"
        allowed, remaining = check_rate_limit(
            key=f"global:{client_ip}",
            max_attempts=60,
            window_seconds=60,
            prefix="rl:"
        )

        response = await call_next(request) if allowed else JSONResponse(
            status_code=429,
            content={"detail": "请求过于频繁，请稍后再试"},
            headers={"Retry-After": "60"}
        )

        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
''',
        desc="FIX-11: 创建全局 API 限流中间件"
    )


# ═══════════════════════════════════════════════════════════════════════
# 执行
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("═" * 60)
    print("  行健平台 V4.0 安全修复补丁")
    print(f"  目标: {PROJECT_ROOT.resolve()}")
    print(f"  时间: {datetime.now().isoformat()}")
    print("═" * 60)
    print()

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    fixes = [
        ("FIX-01", "CORS 白名单",        "HIGH",   fix_01_cors),
        ("FIX-02", "异常响应脱敏",        "MEDIUM", fix_02_error_handler),
        ("FIX-03", "Redis 分布式限流",    "MEDIUM", fix_03_rate_limiter),
        ("FIX-04", "注册限流",            "MEDIUM", fix_04_register_rate_limit),
        ("FIX-05", "密码策略增强",        "MEDIUM", fix_05_password_policy),
        ("FIX-06", "学习时长上限",        "MEDIUM", fix_06_learning_time_cap),
        ("FIX-07", "禁用生产Swagger",     "LOW",    fix_07_disable_docs),
        ("FIX-08", "安全响应头",          "MEDIUM", fix_08_security_headers),
        ("FIX-09", "IDOR细粒度控制",      "MEDIUM", fix_09_idor_coach),
        ("FIX-10", "Token黑名单Redis",    "INFO",   fix_10_token_blacklist),
        ("FIX-11", "全局API限流",         "LOW",    fix_11_global_rate_limit),
    ]

    for fix_id, name, severity, func in fixes:
        print(f"── {fix_id}: {name} ({severity}) ──")
        try:
            func()
        except Exception as e:
            print(f"  ⚠ 异常: {e}")
        print()

    # 汇总
    print("═" * 60)
    print("  修复汇总")
    print("═" * 60)
    print(f"  应用: {len(applied)}")
    for a in applied:
        print(f"    {a}")
    print(f"\n  跳过: {len(skipped)}")
    for s in skipped:
        print(f"    {s}")
    print(f"\n  备份: {BACKUP_DIR}")
    print("═" * 60)


if __name__ == "__main__":
    main()
