"""
生产级中间件集合
Production Middleware Collection

包含：
- CORS 白名单
- 安全响应头
- 速率限制
- 请求/响应日志
- Sentry 集成
"""
import os
import time
import uuid
from typing import List
from datetime import datetime

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
from dotenv import load_dotenv

load_dotenv()


# ============================================
# CORS 白名单配置
# ============================================

def get_cors_origins() -> List[str]:
    """
    从环境变量获取 CORS 允许的域名列表

    环境变量: CORS_ORIGINS (逗号分隔)
    默认值: 本地开发端口
    """
    env_origins = os.getenv("CORS_ORIGINS", "")
    if env_origins:
        return [o.strip() for o in env_origins.split(",") if o.strip()]

    # 开发环境默认值
    return [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:8080",
        "http://localhost:5180",
        "http://127.0.0.1:5180",
    ]


def setup_cors(app: FastAPI):
    """配置 CORS 中间件"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-User-ID", "X-Source-UI", "X-Role"],
        max_age=600,
    )


# ============================================
# 安全响应头中间件
# ============================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """添加安全响应头"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # 生产环境启用 HSTS
        if os.getenv("ENABLE_HSTS", "false").lower() == "true":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


# ============================================
# 请求日志中间件
# ============================================

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """结构化请求/响应日志"""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        start_time = time.time()

        # 注入 request_id
        request.state.request_id = request_id

        try:
            response = await call_next(request)
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"req_id={request_id} method={request.method} path={request.url.path} "
                f"duration={duration:.3f}s error={type(e).__name__}: {e}"
            )
            raise

        duration = time.time() - start_time

        # 跳过健康检查的日志
        if request.url.path not in ("/health", "/metrics"):
            logger.info(
                f"req_id={request_id} method={request.method} path={request.url.path} "
                f"status={response.status_code} duration={duration:.3f}s"
            )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.3f}s"

        return response


# ============================================
# 速率限制中间件
# ============================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    基于内存的速率限制

    生产环境应替换为 Redis 后端
    """

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.rpm = requests_per_minute
        self._buckets: dict = {}  # ip -> [(timestamp, count)]

    async def dispatch(self, request: Request, call_next):
        # 跳过健康检查
        if request.url.path in ("/health", "/metrics"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60

        # 清理过期记录
        if client_ip in self._buckets:
            self._buckets[client_ip] = [
                t for t in self._buckets[client_ip] if t > window_start
            ]
        else:
            self._buckets[client_ip] = []

        # 检查限制
        if len(self._buckets[client_ip]) >= self.rpm:
            return Response(
                content='{"detail": "Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": "60"}
            )

        self._buckets[client_ip].append(now)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.rpm)
        response.headers["X-RateLimit-Remaining"] = str(
            self.rpm - len(self._buckets[client_ip])
        )
        return response


# ============================================
# Sentry 集成
# ============================================

def setup_sentry(app: FastAPI):
    """
    初始化 Sentry 错误追踪

    环境变量: SENTRY_DSN
    """
    dsn = os.getenv("SENTRY_DSN", "")
    if not dsn:
        logger.info("[Sentry] SENTRY_DSN 未设置，跳过初始化")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=dsn,
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
            environment=os.getenv("DEPLOY_ENV", "development"),
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                StarletteIntegration(transaction_style="endpoint"),
            ],
        )
        logger.info("[Sentry] 错误追踪已启用")
    except ImportError:
        logger.warning("[Sentry] sentry-sdk 未安装，跳过初始化")
    except Exception as e:
        logger.error(f"[Sentry] 初始化失败: {e}")


# ============================================
# 统一初始化
# ============================================

def setup_production_middleware(app: FastAPI):
    """
    一键配置所有生产级中间件

    调用顺序影响执行顺序（后添加的先执行）
    """
    # Structured logging (configure first so all subsequent logs use it)
    from core.logging_config import setup_logging
    setup_logging()

    # Sentry（最先初始化，捕获所有错误）
    setup_sentry(app)

    # CORS
    setup_cors(app)

    # 安全头
    app.add_middleware(SecurityHeadersMiddleware)

    # 请求日志
    app.add_middleware(RequestLoggingMiddleware)

    # 速率限制
    rpm = int(os.getenv("RATE_LIMIT_RPM", "120"))
    app.add_middleware(RateLimitMiddleware, requests_per_minute=rpm)

    # Prometheus metrics (after middleware so /metrics route is not wrapped incorrectly)
    from core.metrics import setup_prometheus
    setup_prometheus(app)

    logger.info("[Middleware] 生产级中间件已全部启用")
