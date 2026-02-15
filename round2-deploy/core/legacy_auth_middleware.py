# -*- coding: utf-8 -*-
"""
旧版端点鉴权中间件 (FIX-14)

拦截 /api/assessment/* (非 /api/v1/) 等旧版端点,
强制检查 Authorization header
"""
import re
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

LEGACY_PROTECTED = [
    re.compile(r"^/api/assessment/"),
]


class LegacyAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        is_legacy = any(p.match(path) for p in LEGACY_PROTECTED)
        if not is_legacy:
            return await call_next(request)

        auth = request.headers.get("authorization", "")
        if not auth.startswith("Bearer ") or len(auth) < 20:
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized", "detail": "此端点需要认证"}
            )

        return await call_next(request)
