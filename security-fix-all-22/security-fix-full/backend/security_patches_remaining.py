#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行健平台 V4.0 — 安全修复补丁 (完整版: 22/22)
═══════════════════════════════════════════════════════

前一版 security_patches.py 覆盖了 15/22 项 (FIX-01 ~ FIX-11)
本脚本补全剩余 7 项:
  FIX-12: rxApi Token Key 不一致 (CRITICAL) — 前端补丁
  FIX-13: JWT Token 明文存数据库 (HIGH) — 模型+迁移
  FIX-14: 旧版 /api/assessment/* 缺鉴权 (MEDIUM) — 中间件
  FIX-15: 登录日志明文用户名 (LOW) — 脱敏
  FIX-16: HTTPS 重定向中间件 (HIGH) — main.py
  FIX-17: 用户 public_id UUID (LOW) — 模型+迁移
  FIX-18: CSRF 确认 (INFO) — 审计中间件

用法:
  python security_patches_full.py [后端项目根目录]
"""

import os
import sys
import re
import shutil
from datetime import datetime
from pathlib import Path
from textwrap import dedent

PROJECT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
BACKUP = PROJECT / ".security-patches-backup" / datetime.now().strftime("%Y%m%d_%H%M%S")

applied, skipped = [], []


def _backup_patch(fp: str, old: str, new: str, desc: str):
    p = PROJECT / fp
    if not p.exists():
        skipped.append(f"[跳过] {fp} — 不存在")
        return False
    c = p.read_text("utf-8")
    if old not in c:
        if new.strip().split('\n')[0].strip() in c:
            skipped.append(f"[已修] {fp} — {desc}")
        else:
            skipped.append(f"[跳过] {fp} — 目标代码未匹配")
        return False
    bk = BACKUP / fp
    bk.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, bk)
    p.write_text(c.replace(old, new, 1), "utf-8")
    applied.append(f"[修复] {fp} — {desc}")
    return True


def _create(fp: str, content: str, desc: str):
    p = PROJECT / fp
    if p.exists():
        skipped.append(f"[已存在] {fp}")
        return False
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(dedent(content).lstrip(), "utf-8")
    applied.append(f"[新建] {fp} — {desc}")
    return True


# ═══════════════════════════════════════════════════════════════════════
# FIX-12: rxApi Token Key 不一致 (CRITICAL → SEC-003)
#   rxApi.ts 用 localStorage.getItem('access_token')
#   http.ts  用 const TOKEN_KEY = 'bos_access_token'
#   登录后 token 存 bos_access_token → rxApi 读 access_token = null
#   → 行为处方请求全部裸跑
# ═══════════════════════════════════════════════════════════════════════

def fix_12_rxapi_token():
    """前端修复: rxApi 改用共享 getToken()"""
    # 搜索多个可能路径
    candidates = [
        "src/modules/rx/api/rxApi.ts",
        "frontend/src/modules/rx/api/rxApi.ts",
    ]
    for fp in candidates:
        _backup_patch(
            fp,
            "  const token = localStorage.getItem('access_token')",
            "  const token = localStorage.getItem('bos_access_token')  // FIX-12: 对齐 TOKEN_KEY",
            "FIX-12: rxApi Token Key 对齐 bos_access_token"
        )

    # 更佳方案: 导入共享 getToken (需手动验证 import 路径)
    _create(
        "docs/FIX-12_MANUAL.md",
        """
        # FIX-12: rxApi Token Key 对齐 (CRITICAL)

        ## 问题
        `modules/rx/api/rxApi.ts` 第51行使用 `localStorage.getItem('access_token')`
        而全局 `api/http.ts` 使用 `const TOKEN_KEY = 'bos_access_token'`

        ## 最小修复 (已自动应用)
        ```diff
        - const token = localStorage.getItem('access_token')
        + const token = localStorage.getItem('bos_access_token')
        ```

        ## 推荐修复 (手动)
        将 rxApi 的独立 axios 实例替换为导入共享 http:
        ```typescript
        // rxApi.ts 顶部
        import { getToken } from '@/api/http'

        // 拦截器中
        http.interceptors.request.use((config) => {
          const token = getToken()  // 统一来源
          if (token) config.headers.Authorization = `Bearer ${token}`
          return config
        })
        ```

        ## 验证
        1. 登录后访问行为处方页面
        2. 检查 Network → rx/strategies 请求的 Authorization header
        3. 应显示 `Bearer <token>`, 不应为空
        """,
        "FIX-12: 手动修复指南"
    )


# ═══════════════════════════════════════════════════════════════════════
# FIX-13: JWT Token 明文存数据库 (HIGH → SEC-007)
#   UserSession.token = Column(String(500)) 明文存储
#   数据库泄露 → 所有活跃 token 暴露 → 冒充任意用户
# ═══════════════════════════════════════════════════════════════════════

def fix_13_token_hash():
    """存储 token hash 而非明文"""
    _create(
        "core/token_storage.py",
        '''
        """
        Token 安全存储 (FIX-13)
        存储 SHA-256 哈希而非明文, 数据库泄露不暴露有效 token
        """
        import hashlib
        from sqlalchemy.orm import Session


        def hash_token(token: str) -> str:
            """SHA-256 哈希 token"""
            return hashlib.sha256(token.encode("utf-8")).hexdigest()


        def store_session_token(
            db: Session,
            session_model,
            session_id: str,
            user_id: int,
            access_token: str,
            refresh_token: str,
            ip_address: str = None,
            user_agent: str = None,
            expires_at=None,
        ):
            """
            创建会话记录 — 仅存储 token 哈希

            用法:
                from core.token_storage import store_session_token
                store_session_token(db, UserSession, sid, uid, at, rt, ...)
            """
            session = session_model(
                session_id=session_id,
                user_id=user_id,
                token=hash_token(access_token),       # 哈希存储
                refresh_token=hash_token(refresh_token),  # 哈希存储
                ip_address=ip_address,
                user_agent=user_agent,
                is_active=True,
                expires_at=expires_at,
            )
            db.add(session)
            db.commit()
            return session


        def verify_session_token(
            db: Session,
            session_model,
            token: str,
        ) -> bool:
            """验证 token 是否有活跃会话"""
            token_hash = hash_token(token)
            session = db.query(session_model).filter(
                session_model.token == token_hash,
                session_model.is_active == True,
            ).first()
            return session is not None
        ''',
        "FIX-13: Token 安全存储模块 (hash)"
    )

    # Alembic 迁移
    _create(
        "alembic/versions/fix13_token_hash_column.py",
        '''
        """FIX-13: Rename token columns to indicate hash storage

        Revision ID: fix13_001
        """
        from alembic import op
        import sqlalchemy as sa

        revision = "fix13_001"
        down_revision = None  # 手动设置为当前最新 revision
        branch_labels = None
        depends_on = None


        def upgrade():
            # 添加注释标记为 hash, 不改列名 (避免破坏现有代码)
            # 数据迁移: 将现有明文 token 替换为哈希
            op.execute("""
                UPDATE user_sessions
                SET token = encode(digest(token, 'sha256'), 'hex'),
                    refresh_token = encode(digest(refresh_token, 'sha256'), 'hex')
                WHERE token IS NOT NULL
                  AND length(token) > 64
            """)

            # 添加注释
            op.execute("COMMENT ON COLUMN user_sessions.token IS 'SHA-256 hash of JWT token'")
            op.execute("COMMENT ON COLUMN user_sessions.refresh_token IS 'SHA-256 hash of refresh token'")


        def downgrade():
            # 不可逆: 哈希无法还原为明文
            op.execute("COMMENT ON COLUMN user_sessions.token IS 'JWT token (was hashed in fix13)'")
        ''',
        "FIX-13: Alembic 迁移 — token 哈希化"
    )


# ═══════════════════════════════════════════════════════════════════════
# FIX-14: 旧版 /api/assessment/* 缺鉴权 (MEDIUM → SEC-009)
#   5个旧版端点 /api/assessment/* 不在 /api/v1/ 前缀下
#   可能未接入 get_current_user 鉴权链
# ═══════════════════════════════════════════════════════════════════════

def fix_14_legacy_auth():
    """中间件拦截旧版端点, 强制鉴权"""
    _create(
        "core/legacy_auth_middleware.py",
        '''
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
        ''',
        "FIX-14: 旧版端点鉴权中间件"
    )


# ═══════════════════════════════════════════════════════════════════════
# FIX-15: 登录日志明文用户名 (LOW → SEC-015)
#   logger.info("[LOGIN] ... username: admin") 明文记录
# ═══════════════════════════════════════════════════════════════════════

def fix_15_log_sanitize():
    """日志脱敏辅助函数 + 补丁"""
    _create(
        "core/log_sanitizer.py",
        '''
        """
        日志脱敏工具 (FIX-15)
        """
        import re


        def mask_username(username: str) -> str:
            """用户名脱敏: admin → ad***n, ab → a*"""
            if not username:
                return "***"
            if len(username) <= 2:
                return username[0] + "*"
            return username[:2] + "***" + username[-1]


        def mask_email(email: str) -> str:
            """邮箱脱敏: user@example.com → us***r@e***.com"""
            if not email or "@" not in email:
                return "***"
            local, domain = email.rsplit("@", 1)
            return mask_username(local) + "@" + mask_username(domain)


        def mask_ip(ip: str) -> str:
            """IP脱敏: 192.168.1.100 → 192.168.*.100"""
            if not ip:
                return "***"
            parts = ip.split(".")
            if len(parts) == 4:
                return f"{parts[0]}.{parts[1]}.***.{parts[3]}"
            return ip[:4] + "***"


        def sanitize_log(msg: str) -> str:
            """通用日志脱敏: 替换已知敏感模式"""
            # password= 后面的值
            msg = re.sub(r"(password[=:]\\s*)(\\S+)", r"\\1***", msg, flags=re.I)
            # token= 后面的值
            msg = re.sub(r"(token[=:]\\s*)(\\S{10})\\S+", r"\\1\\2...", msg, flags=re.I)
            return msg
        ''',
        "FIX-15: 日志脱敏工具"
    )

    # 补丁 auth_api.py: 替换明文 username 日志
    _backup_patch(
        "auth_api.py",
        'logger.info(f"[LOGIN] Received login request - username: {form_data.username}")',
        'logger.info(f"[LOGIN] Received login request - username: {form_data.username[:2]}***")',
        "FIX-15: 登录日志用户名脱敏 (1/4)"
    )
    _backup_patch(
        "auth_api.py",
        'logger.info(f"[LOGIN] Database query - found user: {user.username if user else \'None\'}")',
        'logger.info(f"[LOGIN] Database query - found user: {user.username[:2]+\"***\" if user else \"None\"}")',
        "FIX-15: 登录日志用户名脱敏 (2/4)"
    )
    _backup_patch(
        "auth_api.py",
        "logger.info(f\"[LOGIN] Authentication result: {'SUCCESS - ' + user.username if user else 'FAILED'}\")",
        "logger.info(f\"[LOGIN] Authentication result: {'SUCCESS' if user else 'FAILED'}\")",
        "FIX-15: 登录日志用户名脱敏 (3/4)"
    )
    _backup_patch(
        "auth_api.py",
        'logger.info(f"[LOGIN] User logged in successfully: {user.username} (ID: {user.id})")',
        'logger.info(f"[LOGIN] User logged in successfully: ID={user.id}")',
        "FIX-15: 登录日志用户名脱敏 (4/4)"
    )


# ═══════════════════════════════════════════════════════════════════════
# FIX-16: HTTPS 重定向中间件 (HIGH)
#   PHI 健康数据必须加密传输
# ═══════════════════════════════════════════════════════════════════════

def fix_16_https_redirect():
    """生产环境 HTTPS 重定向 + HSTS"""
    _create(
        "core/https_middleware.py",
        '''
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
        ''',
        "FIX-16: HTTPS 重定向中间件"
    )


# ═══════════════════════════════════════════════════════════════════════
# FIX-17: 用户 public_id UUID (LOW → SEC-014)
#   自增 ID 可遍历, 对外暴露 UUID
# ═══════════════════════════════════════════════════════════════════════

def fix_17_uuid_public_id():
    """用户模型添加 public_id, 迁移脚本"""
    _create(
        "alembic/versions/fix17_user_public_id.py",
        '''
        """FIX-17: Add UUID public_id to users table

        对外暴露 public_id 替代自增 id, 防止 ID 枚举

        Revision ID: fix17_001
        """
        from alembic import op
        import sqlalchemy as sa
        from sqlalchemy.dialects.postgresql import UUID

        revision = "fix17_001"
        down_revision = None  # 手动设置
        branch_labels = None
        depends_on = None


        def upgrade():
            # 添加 public_id 列
            op.add_column("users", sa.Column(
                "public_id",
                UUID(as_uuid=True),
                server_default=sa.text("gen_random_uuid()"),
                nullable=True,
            ))

            # 为现有用户生成 UUID
            op.execute("UPDATE users SET public_id = gen_random_uuid() WHERE public_id IS NULL")

            # 设置 NOT NULL + 唯一索引
            op.alter_column("users", "public_id", nullable=False)
            op.create_unique_constraint("uq_users_public_id", "users", ["public_id"])
            op.create_index("ix_users_public_id", "users", ["public_id"])


        def downgrade():
            op.drop_index("ix_users_public_id")
            op.drop_constraint("uq_users_public_id", "users")
            op.drop_column("users", "public_id")
        ''',
        "FIX-17: Alembic 迁移 — 用户 public_id UUID"
    )

    _create(
        "core/public_id.py",
        '''
        """
        Public ID 工具 (FIX-17)

        对外接口使用 UUID public_id, 内部使用整数 id
        """
        from uuid import UUID
        from sqlalchemy.orm import Session
        from fastapi import HTTPException, status


        def resolve_public_id(db: Session, model, public_id: str) -> int:
            """
            将 public_id (UUID) 解析为内部 integer id

            用法:
                user_id = resolve_public_id(db, User, request_path_param)
            """
            try:
                uid = UUID(public_id)
            except (ValueError, AttributeError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无效的用户标识符"
                )

            record = db.query(model).filter(model.public_id == uid).first()
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            return record.id
        ''',
        "FIX-17: Public ID 解析工具"
    )


# ═══════════════════════════════════════════════════════════════════════
# FIX-18: CSRF 确认 (INFO)
#   纯 JWT Bearer 架构不需要传统 CSRF, 但需确认无 cookie 认证
# ═══════════════════════════════════════════════════════════════════════

def fix_18_csrf_audit():
    """CSRF 审计中间件: 确保无 cookie 认证泄露"""
    _create(
        "core/csrf_audit_middleware.py",
        '''
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
        ''',
        "FIX-18: CSRF 审计中间件"
    )


# ═══════════════════════════════════════════════════════════════════════
# 注册中间件到 main.py
# ═══════════════════════════════════════════════════════════════════════

def register_middlewares():
    """将新中间件注册到 main.py"""
    _create(
        "core/register_security.py",
        '''
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
        ''',
        "注册所有安全中间件的入口"
    )


# ═══════════════════════════════════════════════════════════════════════
# 验证清单
# ═══════════════════════════════════════════════════════════════════════

def create_verification():
    """生成修复验证清单"""
    _create(
        "docs/SECURITY_VERIFICATION.md",
        '''
        # 行健平台 V4.0 — 安全修复验证清单 (22/22)

        ## 验证命令

        ```bash
        # 1. 运行渗透测试脚本
        python pentest_bhp.py --base http://localhost:8000/api/v1

        # 2. 检查新模块存在
        ls core/rate_limiter.py \\
           core/security_middleware.py \\
           core/access_control.py \\
           core/token_blacklist_redis.py \\
           core/rate_limit_middleware.py \\
           core/token_storage.py \\
           core/legacy_auth_middleware.py \\
           core/log_sanitizer.py \\
           core/https_middleware.py \\
           core/public_id.py \\
           core/csrf_audit_middleware.py \\
           core/register_security.py

        # 3. 数据库迁移
        alembic upgrade head
        ```

        ## 逐项验证

        ### P0 — 立即修复 (1-3天)

        | # | ID | 严重性 | 修复 | 验证方法 |
        |---|-----|--------|------|---------|
        | 19 | FIX-12 | CRIT | rxApi Token Key | 登录→行为处方页→检查Network请求Authorization不为空 |
        | 1 | FIX-01 | HIGH | CORS白名单 | `curl -H "Origin: https://evil.com" -I api/auth/me` 无 ACAO=evil |
        | 2 | FIX-16 | HIGH | HTTPS重定向 | `curl -I http://app.xingjian.com` → 301 Location: https://... |

        ### P1 — 高优 (1周)

        | # | ID | 严重性 | 修复 | 验证方法 |
        |---|-----|--------|------|---------|
        | 20 | FIX-13 | HIGH | Token哈希存储 | `SELECT token FROM user_sessions` 全部64字符hex |
        | 3 | FIX-02 | MED | 异常脱敏 | 触发500→响应无堆栈, 只有 error_id |
        | 6 | FIX-09 | MED | IDOR细粒度 | 教练A访问教练B的学员→403 |
        | 21 | FIX-14 | MED | 旧版鉴权 | `curl /api/assessment/history/1` 无Token→401 |

        ### P2 — 中优 (2-4周)

        | # | ID | 严重性 | 修复 | 验证方法 |
        |---|-----|--------|------|---------|
        | 4 | FIX-03 | MED | Redis限流 | 11次快速登录→429, 重启服务→计数不清零 |
        | 5 | FIX-05 | MED | 密码策略 | 注册 "123456"→400, "Abc12345"→成功 |
        | 7 | FIX-04 | MED | 注册限流 | 6次快速注册→429 |
        | 9 | FIX-08 | MED | 安全头 | `curl -I /` → X-Frame-Options, CSP 存在 |
        | 10 | FIX-06 | MED | 时长上限 | POST 999999分钟→400 |

        ### P3 — 改进 (1-3月)

        | # | ID | 严重性 | 修复 | 验证方法 |
        |---|-----|--------|------|---------|
        | 11 | FIX-17 | LOW | UUID public_id | API响应用户标识为UUID格式 |
        | 12 | FIX-11 | LOW | 全局限流 | 61次/分钟→429 |
        | 13-15 | FIX-07 | LOW | Swagger禁用 | 生产 /docs→404 |
        | 16 | FIX-08 | LOW | Server头隐藏 | 响应无 `server: uvicorn` |
        | 22 | FIX-15 | LOW | 日志脱敏 | 日志文件中用户名显示 `ad***n` |
        | 17 | FIX-10 | INFO | Token黑名单 | logout→Redis中有 token_bl:xxx 键 |
        | 18 | FIX-18 | INFO | CSRF审计 | API响应无 Set-Cookie with session/token |

        ## main.py 集成代码

        ```python
        # 在 CORS 中间件注册之后添加:
        from core.register_security import register_all_security
        register_all_security(app)
        ```
        ''',
        "安全修复验证清单"
    )


# ═══════════════════════════════════════════════════════════════════════
# 执行
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("═" * 60)
    print("  行健平台 V4.0 安全修复补丁 (剩余 7/22)")
    print(f"  目标: {PROJECT.resolve()}")
    print(f"  时间: {datetime.now().isoformat()}")
    print("═" * 60)
    print()

    BACKUP.mkdir(parents=True, exist_ok=True)

    fixes = [
        ("FIX-12", "rxApi Token Key 对齐",    "CRITICAL", fix_12_rxapi_token),
        ("FIX-13", "Token 哈希存储",           "HIGH",     fix_13_token_hash),
        ("FIX-14", "旧版端点鉴权",             "MEDIUM",   fix_14_legacy_auth),
        ("FIX-15", "登录日志脱敏",             "LOW",      fix_15_log_sanitize),
        ("FIX-16", "HTTPS 重定向",             "HIGH",     fix_16_https_redirect),
        ("FIX-17", "用户 UUID public_id",      "LOW",      fix_17_uuid_public_id),
        ("FIX-18", "CSRF 审计",                "INFO",     fix_18_csrf_audit),
        ("——",     "中间件注册入口",            "——",       register_middlewares),
        ("——",     "验证清单",                  "——",       create_verification),
    ]

    for fid, name, sev, func in fixes:
        print(f"── {fid}: {name} ({sev}) ──")
        try:
            func()
        except Exception as e:
            print(f"  ⚠ 异常: {e}")
        print()

    print("═" * 60)
    print("  修复汇总")
    print("═" * 60)
    print(f"  应用: {len(applied)}")
    for a in applied:
        print(f"    {a}")
    print(f"\n  跳过: {len(skipped)}")
    for s in skipped:
        print(f"    {s}")
    print(f"\n  备份: {BACKUP}")
    print("═" * 60)


if __name__ == "__main__":
    main()
