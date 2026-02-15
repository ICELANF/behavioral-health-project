# -*- coding: utf-8 -*-
"""
HTTPS 强制重定向中间件 (FIX-16)

生产环境: HTTP→301→HTTPS, 添加 HSTS
信任反向代理 X-Forwarded-Proto
"""
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        env = os.getenv("ENVIRONMENT", "production")
        if env in ("development", "test"):
            return await call_next(request)

        proto = request.headers.get("x-forwarded-proto", request.url.scheme)

        # 健康检查放行
        if request.url.path in ("/", "/health"):
            return await call_next(request)

        if proto == "http":
            url = request.url.replace(scheme="https")
            return RedirectResponse(url=str(url), status_code=301)

        response: Response = await call_next(request)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        return response
