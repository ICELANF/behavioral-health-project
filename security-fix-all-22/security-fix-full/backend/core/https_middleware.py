"""
HTTPS 强制重定向中间件 (FIX-16)

生产环境:
- HTTP 请求 301 重定向到 HTTPS
- 添加 HSTS header
- 信任反向代理的 X-Forwarded-Proto header
"""
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """生产环境强制 HTTPS"""

    async def dispatch(self, request: Request, call_next):
        env = os.getenv("ENVIRONMENT", "production")

        # 开发/测试环境跳过
        if env in ("development", "test"):
            return await call_next(request)

        # 检查协议 (支持反向代理)
        proto = request.headers.get("x-forwarded-proto", request.url.scheme)

        # 健康检查放行 (负载均衡器内部检查)
        if request.url.path in ("/", "/health"):
            return await call_next(request)

        # HTTP → HTTPS 重定向
        if proto == "http":
            url = request.url.replace(scheme="https")
            return RedirectResponse(url=str(url), status_code=301)

        # HTTPS 请求: 添加 HSTS
        response: Response = await call_next(request)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        return response
