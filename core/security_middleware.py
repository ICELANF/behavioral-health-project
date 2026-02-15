"""
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
