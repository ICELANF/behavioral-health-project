# -*- coding: utf-8 -*-
"""
安全中间件一键注册 (Round 2)

在 main.py 中调用:
    from core.register_security import register_round2_security
    register_round2_security(app)
"""
import os
from loguru import logger


def register_round2_security(app):
    """注册 Round 2 安全中间件"""
    registered = []
    env = os.getenv("ENVIRONMENT", "production")

    # CSRF 审计
    try:
        from core.csrf_audit_middleware import CSRFAuditMiddleware
        app.add_middleware(CSRFAuditMiddleware)
        registered.append("CSRFAudit")
    except ImportError:
        pass

    # 旧版端点鉴权
    try:
        from core.legacy_auth_middleware import LegacyAuthMiddleware
        app.add_middleware(LegacyAuthMiddleware)
        registered.append("LegacyAuth")
    except ImportError:
        pass

    # HTTPS 重定向 (仅生产)
    if env == "production":
        try:
            from core.https_middleware import HTTPSRedirectMiddleware
            app.add_middleware(HTTPSRedirectMiddleware)
            registered.append("HTTPSRedirect")
        except ImportError:
            pass

    logger.info(f"[Security R2] 注册 {len(registered)} 个中间件: {', '.join(registered)}")
