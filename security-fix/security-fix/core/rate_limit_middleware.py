"""
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
