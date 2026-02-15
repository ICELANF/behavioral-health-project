# -*- coding: utf-8 -*-
"""
CSRF 审计中间件 (FIX-18)

确认纯 JWT Bearer 认证, 无 cookie 认证泄露
"""
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from loguru import logger


class CSRFAuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        env = os.getenv("ENVIRONMENT", "production")
        if env == "production":
            set_cookie = response.headers.get("set-cookie", "")
            if any(kw in set_cookie.lower() for kw in ["session", "token", "auth", "jwt"]):
                logger.warning(
                    f"[CSRF-AUDIT] 疑似认证 cookie: path={request.url.path}"
                )
                del response.headers["set-cookie"]

        return response
