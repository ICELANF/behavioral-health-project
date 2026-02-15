"""
CSRF 审计中间件 (FIX-18)

JWT Bearer 架构无需传统 CSRF token, 但需确保:
1. 服务端不通过 Set-Cookie 泄露认证信息
2. 不使用 session cookie 做认证
3. 记录异常的 cookie-based 认证尝试
"""
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from loguru import logger


class CSRFAuditMiddleware(BaseHTTPMiddleware):
    """审计 cookie 使用, 确保纯 Bearer 认证"""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # 生产环境: 确保 API 响应不设置认证 cookie
        env = os.getenv("ENVIRONMENT", "production")
        if env == "production":
            set_cookie = response.headers.get("set-cookie", "")
            if any(kw in set_cookie.lower() for kw in
                   ["session", "token", "auth", "jwt"]):
                logger.warning(
                    f"[CSRF-AUDIT] API 响应包含疑似认证 cookie: "
                    f"path={request.url.path} cookie={set_cookie[:80]}"
                )
                # 移除可疑 cookie (安全优先)
                del response.headers["set-cookie"]

        return response
