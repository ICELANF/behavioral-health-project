"""
旧版端点鉴权中间件 (FIX-14)

拦截 /api/assessment/* (非 /api/v1/) 等旧版端点,
强制检查 Authorization header, 未认证返回 401
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import re

# 需要鉴权的旧版路径模式
LEGACY_PROTECTED = [
    re.compile(r"^/api/assessment/history/"),
    re.compile(r"^/api/assessment/recent/"),
    re.compile(r"^/api/assessment/submit$"),
    re.compile(r"^/api/assessment/user/"),
    re.compile(r"^/api/assessment/[^/]+$"),  # /api/assessment/{id}
]

# 白名单 (不需要鉴权)
LEGACY_PUBLIC = [
    # 目前没有公开的旧版端点
]


class LegacyAuthMiddleware(BaseHTTPMiddleware):
    """拦截旧版 API 端点, 强制检查 Bearer Token"""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 仅检查旧版路径
        is_legacy = any(p.match(path) for p in LEGACY_PROTECTED)
        if not is_legacy:
            return await call_next(request)

        # 检查白名单
        is_public = any(p.match(path) for p in LEGACY_PUBLIC)
        if is_public:
            return await call_next(request)

        # 检查 Authorization header
        auth = request.headers.get("authorization", "")
        if not auth.startswith("Bearer ") or len(auth) < 20:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "message": "请先登录",
                    "detail": "此端点需要认证, 请提供有效的 Bearer Token",
                }
            )

        # Token 格式合法, 交给下游验证具体有效性
        return await call_next(request)
