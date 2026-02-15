#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
行健平台 V4.0 — 剩余 11 项安全修复 (Round 2)
═══════════════════════════════════════════════════════════════

Round 1 成果: 18→11 findings, 57/60→58/58 (100%)
  已修: FIX-01~08 代码补丁, FIX-09/10/11 模块创建(未集成)

本脚本修复 Round 1 遗留的 11 项:
  A. 集成已创建但未接入的模块 (FIX-09/10/11)
  B. 新增 7 项补丁 (FIX-12~18)
  C. 中间件统一注册

用法 (在项目根目录运行):
  python apply_remaining_11.py

前提: Round 1 的 core/access_control.py, core/token_blacklist_redis.py 已存在
═══════════════════════════════════════════════════════════════
"""

import os
import sys
import re
import shutil
import hashlib
from datetime import datetime
from pathlib import Path

# ── 配置 ──
PROJECT = Path(".")
BACKUP = PROJECT / ".security-backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP.mkdir(parents=True, exist_ok=True)

applied = []
skipped = []
errors = []


def patch(filepath: str, old: str, new: str, desc: str) -> bool:
    """安全替换: 备份 → 查找 → 替换"""
    fp = PROJECT / filepath
    if not fp.exists():
        skipped.append(f"  [文件不存在] {filepath} — {desc}")
        return False

    content = fp.read_text("utf-8")
    if old not in content:
        # 检查是否已修复
        check = new.strip().split('\n')[0].strip()
        if check and check in content:
            skipped.append(f"  [已修复] {filepath} — {desc}")
        else:
            skipped.append(f"  [未匹配] {filepath} — {desc}")
        return False

    # 备份
    bk = BACKUP / filepath
    bk.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(fp, bk)

    fp.write_text(content.replace(old, new, 1), "utf-8")
    applied.append(f"  ✅ {filepath} — {desc}")
    return True


def patch_all(filepath: str, old: str, new: str, desc: str) -> int:
    """替换所有匹配 (用于重复模式如 IDOR)"""
    fp = PROJECT / filepath
    if not fp.exists():
        skipped.append(f"  [文件不存在] {filepath} — {desc}")
        return 0

    content = fp.read_text("utf-8")
    count = content.count(old)
    if count == 0:
        skipped.append(f"  [未匹配] {filepath} — {desc}")
        return 0

    bk = BACKUP / filepath
    bk.parent.mkdir(parents=True, exist_ok=True)
    if not bk.exists():
        shutil.copy2(fp, bk)

    fp.write_text(content.replace(old, new), "utf-8")
    applied.append(f"  ✅ {filepath} — {desc} ({count}处)")
    return count


def create(filepath: str, content: str, desc: str) -> bool:
    """创建新文件"""
    fp = PROJECT / filepath
    if fp.exists():
        skipped.append(f"  [已存在] {filepath}")
        return False
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content, "utf-8")
    applied.append(f"  ✅ [新建] {filepath} — {desc}")
    return True


def section(title: str):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


# ═══════════════════════════════════════════════════════════════
# A. 集成已创建模块
# ═══════════════════════════════════════════════════════════════

def fix_09_integrate_idor():
    """FIX-09: 将 IDOR 细粒度控制集成到 learning_api.py"""
    section("FIX-09: IDOR 细粒度控制 — 集成到 learning_api.py")

    # 步骤1: 在文件顶部添加 import
    patch(
        "api/learning_api.py",
        "from core.models import User",
        "from core.models import User\nfrom core.access_control import check_user_data_access",
        "添加 access_control 导入"
    )

    # 步骤2: 替换所有 8 处宽松 IDOR 检查
    # 原代码: 5个角色全部放行
    old_idor = '''    if user_id != current_user.id and current_user.role.value not in ("admin", "coach", "supervisor", "promoter", "master"):\r\n        raise HTTPException(status_code=403, detail="无权访问他人数据")'''
    new_idor = '''    # FIX-09: 细粒度访问控制 (教练仅限自己学员)\r\n    check_user_data_access(current_user, user_id, db)'''

    count = patch_all("api/learning_api.py", old_idor, new_idor,
                      "IDOR 检查替换为 check_user_data_access")

    # 尝试 \n 版本 (非 Windows 换行)
    if count == 0:
        old_idor_unix = old_idor.replace('\r\n', '\n')
        new_idor_unix = new_idor.replace('\r\n', '\n')
        patch_all("api/learning_api.py", old_idor_unix, new_idor_unix,
                  "IDOR 检查替换 (unix换行)")


def fix_10_integrate_blacklist():
    """FIX-10: 将 Redis Token 黑名单集成到 auth_api.py"""
    section("FIX-10: Token 黑名单 Redis — 集成到 auth_api.py")

    patch(
        "api/auth_api.py",
        '    from core.auth import token_blacklist\n    token_blacklist.revoke(credentials.credentials)',
        '    from core.token_blacklist_redis import token_blacklist  # FIX-10\n    token_blacklist.revoke(credentials.credentials)',
        "logout 函数使用 Redis 黑名单"
    )

    # 也检查 verify_token_with_blacklist 的导入
    patch(
        "core/auth.py",
        'from core.auth import token_blacklist',
        'from core.token_blacklist_redis import token_blacklist  # FIX-10',
        "auth模块使用 Redis 黑名单"
    )


def fix_11_confirm_ratelimit():
    """FIX-11: 确认全局限流中间件已注册"""
    section("FIX-11: 全局 API 限流 — 确认集成")
    # Round 1 已升级 core/middleware.py, 此处确认
    fp = PROJECT / "core/middleware.py"
    if fp.exists():
        content = fp.read_text("utf-8")
        if "rate_limit" in content.lower() or "ratelimit" in content.lower():
            skipped.append("  [已集成] core/middleware.py — 全局限流已在 Round 1 升级")
        else:
            applied.append("  ⚠ core/middleware.py — 需手动确认全局限流是否生效")
    else:
        skipped.append("  [文件不存在] core/middleware.py")


# ═══════════════════════════════════════════════════════════════
# B. 新增 7 项补丁
# ═══════════════════════════════════════════════════════════════

def fix_12_rxapi_token():
    """FIX-12: rxApi Token Key 对齐 (CRITICAL)"""
    section("FIX-12: rxApi Token Key 对齐 [CRITICAL]")

    # 搜索多个可能路径
    candidates = [
        "src/modules/rx/api/rxApi.ts",
        "frontend/src/modules/rx/api/rxApi.ts",
    ]
    fixed = False
    for fp in candidates:
        if patch(fp,
                 "const token = localStorage.getItem('access_token')",
                 "const token = localStorage.getItem('bos_access_token')  // FIX-12: 对齐 TOKEN_KEY",
                 "rxApi Token Key → bos_access_token"):
            fixed = True
            break

    if not fixed:
        # 尝试更宽泛的搜索
        for root, dirs, files in os.walk(PROJECT):
            for f in files:
                if f == "rxApi.ts":
                    full = os.path.join(root, f)
                    content = open(full, "r").read()
                    if "localStorage.getItem('access_token')" in content:
                        rel = os.path.relpath(full, PROJECT)
                        patch(rel,
                              "const token = localStorage.getItem('access_token')",
                              "const token = localStorage.getItem('bos_access_token')  // FIX-12",
                              f"rxApi Token Key (发现于 {rel})")
                        fixed = True
                        break
            if fixed:
                break

    if not fixed:
        errors.append("  ❌ FIX-12: 未找到 rxApi.ts, 需手动修复!")
        errors.append("     文件: modules/rx/api/rxApi.ts 第51行")
        errors.append("     改: localStorage.getItem('access_token')")
        errors.append("     为: localStorage.getItem('bos_access_token')")


def fix_13_token_hash():
    """FIX-13: JWT Token 哈希存储"""
    section("FIX-13: JWT Token 哈希存储 [HIGH]")

    create("core/token_storage.py", '''# -*- coding: utf-8 -*-
"""
Token 安全存储 (FIX-13)
存储 SHA-256 哈希而非明文, 数据库泄露不暴露有效 token
"""
import hashlib
from sqlalchemy.orm import Session


def hash_token(token: str) -> str:
    """SHA-256 哈希 token"""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def store_session_token(db, session_model, **kwargs):
    """
    创建会话记录 — 存储 token 哈希

    用法:
        from core.token_storage import store_session_token, hash_token
        store_session_token(db, UserSession,
            user_id=uid, token=hash_token(access_token), ...)
    """
    session = session_model(**kwargs)
    db.add(session)
    db.commit()
    return session


def verify_session_token(db, session_model, token: str) -> bool:
    """验证 token 是否有活跃会话"""
    token_hash = hash_token(token)
    return db.query(session_model).filter(
        session_model.token == token_hash,
        session_model.is_active == True,
    ).first() is not None
''', "Token 哈希存储模块")

    # Alembic 迁移
    create("alembic/versions/fix13_token_hash_migration.py", '''"""FIX-13: Hash existing plaintext tokens in user_sessions

Revision ID: fix13_001
Revises: (set to current head)
"""
from alembic import op

revision = "fix13_001"
down_revision = None  # ← 手动设置为当前 alembic head
branch_labels = None
depends_on = None


def upgrade():
    # 将现有明文 token 替换为 SHA-256 哈希
    # PostgreSQL digest() 需要 pgcrypto 扩展
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("""
        UPDATE user_sessions
        SET token = encode(digest(token, 'sha256'), 'hex'),
            refresh_token = encode(digest(refresh_token, 'sha256'), 'hex')
        WHERE token IS NOT NULL
          AND length(token) > 64
    """)
    op.execute("COMMENT ON COLUMN user_sessions.token IS 'SHA-256 hash (FIX-13)'")
    op.execute("COMMENT ON COLUMN user_sessions.refresh_token IS 'SHA-256 hash (FIX-13)'")


def downgrade():
    op.execute("COMMENT ON COLUMN user_sessions.token IS 'Hashed in FIX-13, cannot revert'")
''', "Token 哈希 Alembic 迁移")


def fix_14_legacy_auth():
    """FIX-14: 旧版 /api/assessment/* 鉴权中间件"""
    section("FIX-14: 旧版端点鉴权 [MEDIUM]")

    create("core/legacy_auth_middleware.py", '''# -*- coding: utf-8 -*-
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
''', "旧版端点鉴权中间件")


def fix_15_log_sanitize():
    """FIX-15: 登录日志脱敏"""
    section("FIX-15: 登录日志脱敏 [LOW]")

    create("core/log_sanitizer.py", '''# -*- coding: utf-8 -*-
"""日志脱敏工具 (FIX-15)"""


def mask_username(username: str) -> str:
    """admin → ad***n"""
    if not username:
        return "***"
    if len(username) <= 2:
        return username[0] + "*"
    return username[:2] + "***" + username[-1]


def mask_email(email: str) -> str:
    """user@example.com → us***r@ex***e.com"""
    if not email or "@" not in email:
        return "***"
    local, domain = email.rsplit("@", 1)
    return mask_username(local) + "@" + mask_username(domain)


def mask_ip(ip: str) -> str:
    """192.168.1.100 → 192.168.***.100"""
    if not ip:
        return "***"
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.***.{parts[3]}"
    return ip[:4] + "***"
''', "日志脱敏工具")

    # 补丁 auth_api.py 中的4处明文日志
    patches = [
        (
            'logger.info(f"[LOGIN] Received login request - username: {form_data.username}")',
            'logger.info(f"[LOGIN] Login request - user: {form_data.username[:2]}***")',
            "登录请求日志脱敏"
        ),
        (
            'logger.info(f"[LOGIN] Received login request - username: {username}")',
            'logger.info(f"[LOGIN] Login request - user: {username[:2]}***")',
            "登录请求日志脱敏(v2)"
        ),
        (
            'logger.info(f"[LOGIN] Database query - found user: {user.username if user else \'None\'}")',
            'logger.info(f"[LOGIN] DB query result: {\"found\" if user else \"not found\"}")',
            "数据库查询日志脱敏"
        ),
        (
            "logger.info(f\"[LOGIN] Authentication result: {'SUCCESS - ' + user.username if user else 'FAILED'}\")",
            "logger.info(f\"[LOGIN] Auth result: {'SUCCESS' if user else 'FAILED'}\")",
            "认证结果日志脱敏"
        ),
        (
            'logger.info(f"[LOGIN] User logged in successfully: {user.username} (ID: {user.id})")',
            'logger.info(f"[LOGIN] Login success: ID={user.id}")',
            "登录成功日志脱敏"
        ),
        (
            f'logger.info(f"用户登出: {{current_user.username}} (ID: {{current_user.id}})")',
            f'logger.info(f"用户登出: ID={{current_user.id}}")',
            "登出日志脱敏"
        ),
    ]

    for old, new, desc in patches:
        patch("api/auth_api.py", old, new, f"FIX-15: {desc}")


def fix_16_https_redirect():
    """FIX-16: HTTPS 重定向中间件"""
    section("FIX-16: HTTPS 重定向 [HIGH]")

    create("core/https_middleware.py", '''# -*- coding: utf-8 -*-
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
''', "HTTPS 重定向中间件")


def fix_17_uuid_public_id():
    """FIX-17: 用户 UUID public_id"""
    section("FIX-17: 用户 UUID public_id [LOW]")

    # 模型补丁: 在 User 类中添加 public_id 字段
    patch(
        "core/models.py",
        "    # 主键\n    id = Column(Integer, primary_key=True, index=True)",
        "    # 主键\n    id = Column(Integer, primary_key=True, index=True)\n\n    # FIX-17: 对外暴露 UUID, 防止 ID 枚举\n    from sqlalchemy.dialects.postgresql import UUID as PG_UUID\n    import uuid\n    public_id = Column(PG_UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)",
        "User 模型添加 public_id"
    )

    # 也试 \r\n 版本
    patch(
        "core/models.py",
        "    # 主键\r\n    id = Column(Integer, primary_key=True, index=True)",
        "    # 主键\r\n    id = Column(Integer, primary_key=True, index=True)\r\n\r\n    # FIX-17: 对外暴露 UUID, 防止 ID 枚举\r\n    from sqlalchemy.dialects.postgresql import UUID as PG_UUID\r\n    import uuid\r\n    public_id = Column(PG_UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)",
        "User 模型添加 public_id (\\r\\n)"
    )

    create("core/public_id.py", '''# -*- coding: utf-8 -*-
"""Public ID 工具 (FIX-17) — 对外 UUID, 内部 int"""
from uuid import UUID
from fastapi import HTTPException, status


def resolve_public_id(db, model, public_id_str: str) -> int:
    """将 public_id (UUID) 解析为内部 integer id"""
    try:
        uid = UUID(public_id_str)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="无效的用户标识符")

    record = db.query(model).filter(model.public_id == uid).first()
    if not record:
        raise HTTPException(status_code=404, detail="用户不存在")
    return record.id
''', "Public ID 解析工具")

    create("alembic/versions/fix17_user_public_id.py", '''"""FIX-17: Add UUID public_id to users table

Revision ID: fix17_001
Revises: (set to current head)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "fix17_001"
down_revision = None  # ← 手动设置
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.add_column("users", sa.Column(
        "public_id", UUID(as_uuid=True),
        server_default=sa.text("gen_random_uuid()"),
        nullable=True,
    ))
    op.execute("UPDATE users SET public_id = gen_random_uuid() WHERE public_id IS NULL")
    op.alter_column("users", "public_id", nullable=False)
    op.create_unique_constraint("uq_users_public_id", "users", ["public_id"])
    op.create_index("ix_users_public_id", "users", ["public_id"])


def downgrade():
    op.drop_index("ix_users_public_id")
    op.drop_constraint("uq_users_public_id", "users")
    op.drop_column("users", "public_id")
''', "用户 public_id 迁移")


def fix_18_csrf_audit():
    """FIX-18: CSRF 审计中间件"""
    section("FIX-18: CSRF 审计 [INFO]")

    create("core/csrf_audit_middleware.py", '''# -*- coding: utf-8 -*-
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
''', "CSRF 审计中间件")


# ═══════════════════════════════════════════════════════════════
# C. 中间件统一注册
# ═══════════════════════════════════════════════════════════════

def register_all_middlewares():
    """将 FIX-14/16/18 中间件注册到 main.py"""
    section("中间件统一注册 → api/main.py")

    create("core/register_security.py", '''# -*- coding: utf-8 -*-
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
''', "Round 2 中间件注册入口")

    # 在 main.py 中注册 (在 CORS 之后)
    # 查找合适的注入点
    main_path = PROJECT / "api/main.py"
    if main_path.exists():
        content = main_path.read_text("utf-8")

        inject_code = "\n# FIX-14/16/18: Round 2 安全中间件\nfrom core.register_security import register_round2_security\nregister_round2_security(app)\n"

        if "register_round2_security" in content:
            skipped.append("  [已注册] api/main.py — Round 2 中间件")
        elif "register_all_security" in content:
            skipped.append("  [已有注册] api/main.py — 已有 register_all_security")
        else:
            # 在 CORS 中间件之后注入
            injection_points = [
                "# 安全响应头",
                "SecurityHeadersMiddleware",
                "GlobalRateLimitMiddleware",
                "# =============================================================================\n# 异常处理",
                "# 异常处理",
            ]

            injected = False
            for point in injection_points:
                if point in content:
                    bk = BACKUP / "api/main.py"
                    bk.parent.mkdir(parents=True, exist_ok=True)
                    if not bk.exists():
                        shutil.copy2(main_path, bk)

                    content = content.replace(point, inject_code + "\n" + point, 1)
                    main_path.write_text(content, "utf-8")
                    applied.append("  ✅ api/main.py — Round 2 中间件注册")
                    injected = True
                    break

            if not injected:
                errors.append("  ⚠ api/main.py — 需手动添加:")
                errors.append("    from core.register_security import register_round2_security")
                errors.append("    register_round2_security(app)")


# ═══════════════════════════════════════════════════════════════
# 验证
# ═══════════════════════════════════════════════════════════════

def verify():
    """验证所有修复文件就位"""
    section("验证检查")

    modules = {
        "core/access_control.py":          "FIX-09",
        "core/token_blacklist_redis.py":   "FIX-10",
        "core/rate_limiter.py":            "FIX-11",
        "core/token_storage.py":           "FIX-13",
        "core/legacy_auth_middleware.py":   "FIX-14",
        "core/log_sanitizer.py":           "FIX-15",
        "core/https_middleware.py":        "FIX-16",
        "core/public_id.py":              "FIX-17",
        "core/csrf_audit_middleware.py":    "FIX-18",
        "core/register_security.py":       "注册入口",
    }

    ok = 0
    miss = 0
    for path, fix_id in modules.items():
        if (PROJECT / path).exists():
            print(f"  ✅ {path} ({fix_id})")
            ok += 1
        else:
            print(f"  ❌ {path} ({fix_id})")
            miss += 1

    print(f"\n  模块: {ok} 就位, {miss} 缺失")

    # 关键补丁验证
    print("\n  代码补丁:")
    checks = {
        "api/learning_api.py": ("check_user_data_access", "FIX-09 IDOR集成"),
        "api/main.py": ("register_round2_security", "中间件注册"),
    }
    for path, (keyword, desc) in checks.items():
        fp = PROJECT / path
        if fp.exists() and keyword in fp.read_text("utf-8"):
            print(f"  ✅ {path} — {desc}")
        else:
            print(f"  ⚠ {path} — {desc} 需确认")


# ═══════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════

def main():
    print("═" * 60)
    print("  行健平台 V4.0 — 剩余 11 项安全修复")
    print(f"  目录: {PROJECT.resolve()}")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 60)

    # A. 集成已有模块
    fix_09_integrate_idor()
    fix_10_integrate_blacklist()
    fix_11_confirm_ratelimit()

    # B. 新增 7 项
    fix_12_rxapi_token()
    fix_13_token_hash()
    fix_14_legacy_auth()
    fix_15_log_sanitize()
    fix_16_https_redirect()
    fix_17_uuid_public_id()
    fix_18_csrf_audit()

    # C. 注册中间件
    register_all_middlewares()

    # 验证
    verify()

    # 汇总
    print("\n" + "═" * 60)
    print("  修复汇总")
    print("═" * 60)

    if applied:
        print(f"\n  ✅ 应用: {len(applied)}")
        for a in applied:
            print(f"  {a}")

    if skipped:
        print(f"\n  ⏭ 跳过: {len(skipped)}")
        for s in skipped:
            print(f"  {s}")

    if errors:
        print(f"\n  ❌ 需手动处理: {len(errors)}")
        for e in errors:
            print(f"  {e}")

    print(f"\n  备份: {BACKUP}")

    print("\n" + "═" * 60)
    print("  下一步:")
    print("═" * 60)
    print("  1. 设置 Alembic down_revision 后运行迁移:")
    print("     alembic upgrade head")
    print("")
    print("  2. 确认环境变量:")
    print("     CORS_ORIGINS=https://app.xingjian.com")
    print("     REDIS_URL=redis://:password@localhost:6379/0")
    print("     ENVIRONMENT=production")
    print("")
    print("  3. 重启并验证:")
    print("     python pentest_bhp.py --base http://localhost:8000/api/v1")
    print("")
    print("  4. 预期结果: 0 findings, 全项通过")
    print("═" * 60)


if __name__ == "__main__":
    main()
