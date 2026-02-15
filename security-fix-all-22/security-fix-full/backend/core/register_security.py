"""
安全组件一键注册 (FIX-12~18)

在 main.py 中调用:
    from core.register_security import register_all_security
    register_all_security(app)
"""
import os
from loguru import logger


def register_all_security(app):
    """注册全部安全中间件 (按优先级从低到高, 实际执行从高到低)"""
    env = os.getenv("ENVIRONMENT", "production")
    registered = []

    # 1. CSRF 审计 (最外层, 最后执行)
    try:
        from core.csrf_audit_middleware import CSRFAuditMiddleware
        app.add_middleware(CSRFAuditMiddleware)
        registered.append("CSRFAudit")
    except ImportError:
        pass

    # 2. 旧版端点鉴权
    try:
        from core.legacy_auth_middleware import LegacyAuthMiddleware
        app.add_middleware(LegacyAuthMiddleware)
        registered.append("LegacyAuth")
    except ImportError:
        pass

    # 3. 全局限流
    try:
        from core.rate_limit_middleware import GlobalRateLimitMiddleware
        app.add_middleware(GlobalRateLimitMiddleware)
        registered.append("GlobalRateLimit")
    except ImportError:
        pass

    # 4. 安全响应头
    try:
        from core.security_middleware import SecurityHeadersMiddleware
        app.add_middleware(SecurityHeadersMiddleware)
        registered.append("SecurityHeaders")
    except ImportError:
        pass

    # 5. HTTPS 重定向 (最内层, 最先执行)
    if env == "production":
        try:
            from core.https_middleware import HTTPSRedirectMiddleware
            app.add_middleware(HTTPSRedirectMiddleware)
            registered.append("HTTPSRedirect")
        except ImportError:
            pass

    logger.info(f"[Security] 已注册 {len(registered)} 个安全中间件: {', '.join(registered)}")
