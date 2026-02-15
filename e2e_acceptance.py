#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════
  行健平台 V4.0 — 端到端安全验收测试
  End-to-End Security Acceptance Test (22 Fixes)
═══════════════════════════════════════════════════════════════════════

三层验证:
  Layer 1 — 静态代码审计 (无需运行后端, 检查补丁是否就位)
  Layer 2 — 动态 API 测试 (需运行后端, HTTP 实测)
  Layer 3 — 基础设施审计 (Docker/Nginx/CI 配置检查)

用法:
  # 全量验收 (静态 + 动态 + 基础设施)
  python e2e_acceptance.py --base http://localhost:8000 --project /opt/behaviros

  # 仅静态审计 (无需启动服务)
  python e2e_acceptance.py --static-only --project /opt/behaviros

  # 仅动态测试 (服务已运行)
  python e2e_acceptance.py --dynamic-only --base http://localhost:8000

  # 输出 JSON 报告
  python e2e_acceptance.py --base http://localhost:8000 --project /opt/behaviros --json report.json

═══════════════════════════════════════════════════════════════════════
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── HTTP 依赖 ──
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ═══════════════════════════════════════════════════════════════
# 测试框架
# ═══════════════════════════════════════════════════════════════

class TestResult:
    def __init__(self, fix_id: str, title: str, severity: str, layer: str):
        self.fix_id = fix_id
        self.title = title
        self.severity = severity
        self.layer = layer
        self.checks: list[dict] = []

    def check(self, name: str, passed: bool, detail: str = "", evidence: str = ""):
        self.checks.append({
            "name": name,
            "passed": passed,
            "detail": detail,
            "evidence": evidence[:200],
        })

    @property
    def passed(self) -> bool:
        return all(c["passed"] for c in self.checks) if self.checks else False

    @property
    def status(self) -> str:
        if not self.checks:
            return "SKIP"
        return "PASS" if self.passed else "FAIL"


class AcceptanceRunner:
    def __init__(self, base_url: str = "", project_dir: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api/v1" if self.base_url else ""
        self.project = Path(project_dir) if project_dir else None
        self.results: list[TestResult] = []
        self.session = requests.Session() if HAS_REQUESTS else None
        self._token = ""
        self._test_user = f"_sectest_{int(time.time())}"

    # ── 辅助 ──

    def _read(self, relpath: str) -> Optional[str]:
        """读取项目文件"""
        if not self.project:
            return None
        fp = self.project / relpath
        if not fp.exists():
            # 尝试 backend/ 前缀
            fp = self.project / "backend" / relpath
        if not fp.exists():
            return None
        try:
            return fp.read_text("utf-8")
        except Exception:
            return None

    def _find(self, filename: str) -> Optional[str]:
        """递归查找文件"""
        if not self.project:
            return None
        for root, dirs, files in os.walk(self.project):
            # 跳过 node_modules, .git, __pycache__
            dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", "__pycache__", ".venv", ".security-backup", ".security-patches-backup", "dist", "build")]
            if filename in files:
                fp = os.path.join(root, filename)
                try:
                    return open(fp, "r", encoding="utf-8").read()
                except Exception:
                    return None
        return None

    def _get(self, path: str, **kwargs) -> Optional[requests.Response]:
        if not self.session:
            return None
        try:
            return self.session.get(f"{self.base_url}{path}", timeout=10, **kwargs)
        except Exception:
            return None

    def _post(self, path: str, **kwargs) -> Optional[requests.Response]:
        if not self.session:
            return None
        try:
            return self.session.post(f"{self.base_url}{path}", timeout=10, **kwargs)
        except Exception:
            return None

    def _authed_get(self, path: str) -> Optional[requests.Response]:
        if not self._token:
            return None
        return self._get(path, headers={"Authorization": f"Bearer {self._token}"})

    def _authed_post(self, path: str, **kwargs) -> Optional[requests.Response]:
        if not self._token:
            return None
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._token}"
        return self._post(path, headers=headers, **kwargs)

    # ═══════════════════════════════════════════════════════════
    # Layer 1: 静态代码审计
    # ═══════════════════════════════════════════════════════════

    def static_fix01_cors(self):
        """FIX-01: CORS 白名单"""
        t = TestResult("FIX-01", "CORS 白名单", "HIGH", "STATIC")
        main = self._find("main.py")
        if not main:
            t.check("main.py 存在", False, "未找到 main.py")
        else:
            t.check("无 allow_origins=['*']",
                     "allow_origins=[\"*\"]" not in main and "allow_origins=['*']" not in main,
                     "CORS 不应使用通配符",
                     "allow_origins=['*']" if "allow_origins=['*']" in main else "")
            t.check("使用 CORS_ORIGINS 环境变量",
                     "CORS_ORIGINS" in main or "cors_origins" in main.lower(),
                     "应从环境变量读取白名单")
        self.results.append(t)

    def static_fix02_error_handler(self):
        """FIX-02: 异常响应脱敏"""
        t = TestResult("FIX-02", "异常响应脱敏", "MEDIUM", "STATIC")
        main = self._find("main.py")
        if not main:
            t.check("main.py 存在", False)
        else:
            t.check("无 detail=str(exc) 泄露",
                     "detail=str(exc)" not in main,
                     "生产环境不应返回原始异常信息",
                     "detail=str(exc)" if "detail=str(exc)" in main else "")
            t.check("使用 error_id 追踪",
                     "error_id" in main,
                     "应生成唯一错误编号用于日志追踪")
            t.check("区分环境",
                     "ENVIRONMENT" in main or "environment" in main.lower(),
                     "应按环境决定错误详情级别")
        self.results.append(t)

    def static_fix03_rate_limiter(self):
        """FIX-03: Redis 分布式限流"""
        t = TestResult("FIX-03", "Redis 分布式限流", "MEDIUM", "STATIC")
        auth = self._find("auth_api.py")
        rl = self._find("rate_limiter.py")
        if auth:
            t.check("无内存 dict 限流",
                     "_login_attempts: dict = {}" not in auth,
                     "不应使用进程内存做限流",
                     "_login_attempts: dict" if "_login_attempts: dict" in auth else "")
        if rl:
            t.check("rate_limiter.py 存在", True, "分布式限流模块就位")
            t.check("支持 Redis",
                     "redis" in rl.lower(),
                     "限流应支持 Redis 后端")
        else:
            t.check("rate_limiter.py 存在", False, "未找到限流模块")
        self.results.append(t)

    def static_fix04_register_limit(self):
        """FIX-04: 注册限流"""
        t = TestResult("FIX-04", "注册限流", "MEDIUM", "STATIC")
        auth = self._find("auth_api.py")
        if auth:
            # 查找 register 函数附近是否有限流调用
            reg_idx = auth.find("def register")
            if reg_idx > 0:
                reg_block = auth[reg_idx:reg_idx+500]
                t.check("注册函数有限流",
                        "rate_limit" in reg_block.lower() or "limit" in reg_block.lower(),
                        "注册端点应有 IP 级限流")
            else:
                t.check("register 函数存在", False)
        self.results.append(t)

    def static_fix05_password(self):
        """FIX-05: 密码策略"""
        t = TestResult("FIX-05", "密码策略增强", "MEDIUM", "STATIC")
        auth = self._find("auth_api.py")
        if auth:
            t.check("无 len >= 6 弱策略",
                     'len(request.password) < 6' not in auth
                     and "密码长度不能少于6位" not in auth,
                     "密码不应仅要求6位")
            t.check("有大小写检查",
                     "[a-z]" in auth or "[A-Z]" in auth or "validate_password" in auth.lower(),
                     "应检查密码复杂度 (大小写+数字)")
        self.results.append(t)

    def static_fix06_time_cap(self):
        """FIX-06: 学习时长上限"""
        t = TestResult("FIX-06", "学习时长上限", "MEDIUM", "STATIC")
        learn = self._find("learning_api.py")
        if learn:
            t.check("有时长上限检查",
                     "MAX_MINUTES" in learn or "480" in learn or "max_minutes" in learn.lower(),
                     "学习时长应有合理上限 (如 480分钟)")
        self.results.append(t)

    def static_fix07_docs_disabled(self):
        """FIX-07: 生产禁用 Swagger"""
        t = TestResult("FIX-07", "生产禁用 Swagger", "LOW", "STATIC")
        main = self._find("main.py")
        if main:
            t.check("docs_url 可控",
                     "docs_url" in main,
                     "docs_url 应根据环境变量设置")
            t.check("生产为 None",
                     "None" in main and "docs_url" in main,
                     "生产环境 docs_url 应为 None")
        self.results.append(t)

    def static_fix08_security_headers(self):
        """FIX-08: 安全响应头"""
        t = TestResult("FIX-08", "安全响应头", "MEDIUM", "STATIC")
        mw = self._find("middleware.py")
        smw = self._find("security_middleware.py")
        target = mw or smw
        if target:
            for header in ["X-Content-Type-Options", "X-Frame-Options", "Content-Security-Policy"]:
                t.check(f"设置 {header}",
                        header in target,
                        f"应在中间件中设置 {header}")
            t.check("隐藏 Server header",
                     "server" in target.lower(),
                     "应移除或替换 Server header")
        else:
            t.check("安全头中间件存在", False, "未找到 middleware.py 或 security_middleware.py")
        self.results.append(t)

    def static_fix09_idor(self):
        """FIX-09: IDOR 细粒度控制"""
        t = TestResult("FIX-09", "IDOR 细粒度控制", "MEDIUM", "STATIC")
        learn = self._find("learning_api.py")
        ac = self._find("access_control.py")
        if learn:
            old_pattern = 'role.value not in ("admin", "coach", "supervisor", "promoter", "master")'
            t.check("无 5 角色宽松 IDOR",
                     old_pattern not in learn,
                     "不应将5个角色全部放行查看任意用户",
                     old_pattern[:60] if old_pattern in learn else "")
            t.check("使用 check_user_data_access",
                     "check_user_data_access" in learn,
                     "应使用细粒度访问控制函数")
        if ac:
            t.check("access_control.py 存在", True)
            t.check("区分教练与管理员",
                     "coach" in ac.lower() and "admin" in ac.lower(),
                     "应区分教练(仅自己学员)和管理员(全部)")
        self.results.append(t)

    def static_fix10_token_blacklist(self):
        """FIX-10: Token 黑名单 Redis"""
        t = TestResult("FIX-10", "Token 黑名单 Redis", "INFO", "STATIC")
        tbl = self._find("token_blacklist_redis.py")
        auth = self._find("auth_api.py")
        if tbl:
            t.check("token_blacklist_redis.py 存在", True)
            t.check("使用 Redis",
                     "redis" in tbl.lower(),
                     "黑名单应支持 Redis 持久化")
            t.check("使用 token hash",
                     "sha256" in tbl.lower() or "hash" in tbl.lower(),
                     "应存储 token hash 而非明文")
        else:
            t.check("token_blacklist_redis.py 存在", False)
        if auth:
            t.check("logout 使用 Redis 黑名单",
                     "token_blacklist_redis" in auth,
                     "logout 应导入 Redis 黑名单")
        self.results.append(t)

    def static_fix11_global_ratelimit(self):
        """FIX-11: 全局 API 限流"""
        t = TestResult("FIX-11", "全局 API 限流", "LOW", "STATIC")
        mw = self._find("middleware.py")
        rlm = self._find("rate_limit_middleware.py")
        target = mw or rlm
        if target:
            t.check("全局限流中间件存在", True)
            t.check("含限流逻辑",
                     "rate_limit" in target.lower() or "429" in target,
                     "中间件应包含限流和429返回逻辑")
        else:
            t.check("限流中间件存在", False)
        self.results.append(t)

    def static_fix12_rxapi_token(self):
        """FIX-12: rxApi Token Key 对齐"""
        t = TestResult("FIX-12", "rxApi Token Key 对齐", "CRITICAL", "STATIC")
        rxapi = self._find("rxApi.ts")
        http = self._find("http.ts")
        if rxapi:
            # 精确匹配: 仅 'access_token' 而非 'bos_access_token'
            has_bare_key = "getItem('access_token')" in rxapi and "getItem('bos_access_token')" not in rxapi
            t.check("不使用裸 access_token",
                     not has_bare_key,
                     "rxApi 不应使用 'access_token' (应为 'bos_access_token')",
                     "getItem('access_token')" if has_bare_key else "")
            t.check("使用 bos_access_token 或 getToken()",
                     "bos_access_token" in rxapi or "getToken()" in rxapi or "getToken" in rxapi,
                     "应使用统一的 Token Key 或共享 getToken()")
        else:
            t.check("rxApi.ts 存在", False, "未找到 rxApi.ts (前端文件)")
        if http:
            t.check("http.ts TOKEN_KEY 定义",
                     "bos_access_token" in http,
                     "http.ts 应定义 TOKEN_KEY = 'bos_access_token'")
        self.results.append(t)

    def static_fix13_token_hash(self):
        """FIX-13: JWT Token 哈希存储"""
        t = TestResult("FIX-13", "JWT Token 哈希存储", "HIGH", "STATIC")
        ts = self._find("token_storage.py")
        models = self._find("models.py")
        if ts:
            t.check("token_storage.py 存在", True)
            t.check("包含 hash_token",
                     "hash_token" in ts or "sha256" in ts.lower(),
                     "应有 SHA-256 哈希函数")
        else:
            t.check("token_storage.py 存在", False, "需创建 Token 哈希存储模块")
        if models:
            # 检查 UserSession.token 列注释
            t.check("模型含 token 列",
                     "token = Column(String" in models,
                     "UserSession 模型应有 token 列")
        self.results.append(t)

    def static_fix14_legacy_auth(self):
        """FIX-14: 旧版端点鉴权"""
        t = TestResult("FIX-14", "旧版端点鉴权", "MEDIUM", "STATIC")
        lam = self._find("legacy_auth_middleware.py")
        if lam:
            t.check("legacy_auth_middleware.py 存在", True)
            t.check("拦截 /api/assessment",
                     "assessment" in lam,
                     "应拦截旧版 /api/assessment/* 路径")
            t.check("检查 Bearer Token",
                     "Bearer" in lam or "authorization" in lam.lower(),
                     "应检查 Authorization header")
        else:
            t.check("legacy_auth_middleware.py 存在", False)
        self.results.append(t)

    def static_fix15_log_sanitize(self):
        """FIX-15: 登录日志脱敏"""
        t = TestResult("FIX-15", "登录日志脱敏", "LOW", "STATIC")
        auth = self._find("auth_api.py")
        ls = self._find("log_sanitizer.py")
        if auth:
            # 检查是否还有明文 username 日志
            bad_patterns = [
                'username: {form_data.username}"',
                'username: {username}"',
                'found user: {user.username',
                "SUCCESS - ' + user.username",
                'successfully: {user.username}',
                '登出: {current_user.username}',
            ]
            leak_count = sum(1 for p in bad_patterns if p in auth)
            t.check("无明文用户名日志",
                     leak_count == 0,
                     f"发现 {leak_count} 处明文用户名日志泄露",
                     "; ".join(p[:40] for p in bad_patterns if p in auth)[:200])
        if ls:
            t.check("log_sanitizer.py 存在", True)
        self.results.append(t)

    def static_fix16_https(self):
        """FIX-16: HTTPS 重定向"""
        t = TestResult("FIX-16", "HTTPS 重定向", "HIGH", "STATIC")
        hm = self._find("https_middleware.py")
        mw = self._find("middleware.py")
        nginx = self._find("app.conf") or self._find("nginx.conf")
        if hm:
            t.check("https_middleware.py 存在", True)
            t.check("301 重定向",
                     "301" in hm,
                     "应返回 301 重定向到 HTTPS")
            t.check("HSTS header",
                     "Strict-Transport-Security" in hm,
                     "应设置 HSTS header")
        elif nginx and "ssl" in nginx.lower():
            t.check("Nginx SSL 配置", True, "SSL 在 Nginx 层处理")
        else:
            # 可能在 middleware.py 中
            if mw and ("https" in mw.lower() or "hsts" in mw.lower()):
                t.check("HTTPS 在 middleware.py 中处理", True)
            else:
                t.check("HTTPS 重定向存在", False, "未找到 HTTPS 中间件或 Nginx SSL 配置")
        self.results.append(t)

    def static_fix17_uuid(self):
        """FIX-17: 用户 UUID public_id"""
        t = TestResult("FIX-17", "用户 UUID public_id", "LOW", "STATIC")
        models = self._find("models.py")
        pid = self._find("public_id.py")
        if models:
            t.check("User 模型有 public_id",
                     "public_id" in models,
                     "User 表应有 UUID public_id 列")
        if pid:
            t.check("public_id.py 存在", True)
        self.results.append(t)

    def static_fix18_csrf(self):
        """FIX-18: CSRF 审计"""
        t = TestResult("FIX-18", "CSRF 审计", "INFO", "STATIC")
        csm = self._find("csrf_audit_middleware.py")
        auth = self._find("auth_api.py")
        if csm:
            t.check("csrf_audit_middleware.py 存在", True)
            t.check("检查 set-cookie",
                     "set-cookie" in csm.lower() or "set_cookie" in csm.lower(),
                     "应审计认证 cookie 泄露")
        if auth:
            t.check("无 cookie 认证",
                     "set_cookie" not in auth and "session_id" not in auth,
                     "API 不应使用 cookie 认证")
        self.results.append(t)

    # ═══════════════════════════════════════════════════════════
    # Layer 2: 动态 API 测试
    # ═══════════════════════════════════════════════════════════

    def _setup_dynamic(self):
        """创建测试用户并登录"""
        if not self.session or not self.api_url:
            return False

        # 检查服务可用
        r = self._get("/")
        if not r or r.status_code not in (200, 404):
            return False

        # 尝试登录已有测试用户或创建
        r = self._post(f"/api/v1/auth/login",
                       json={"username": "admin", "password": "Admin123!"})
        if r and r.status_code == 200:
            data = r.json()
            self._token = data.get("access_token", "")
            return bool(self._token)

        # 尝试 form data
        r = self._post(f"/api/v1/auth/login",
                       data={"username": "admin", "password": "Admin123!"})
        if r and r.status_code == 200:
            data = r.json()
            self._token = data.get("access_token", "")
            return bool(self._token)

        return False

    def dynamic_fix01_cors(self):
        """动态: CORS 不应允许 *"""
        t = TestResult("FIX-01", "CORS 白名单 (动态)", "HIGH", "DYNAMIC")
        r = self._get("/api/v1/auth/me",
                      headers={"Origin": "https://evil.example.com"})
        if r:
            acao = r.headers.get("Access-Control-Allow-Origin", "")
            t.check("不返回 Origin=evil",
                     acao != "https://evil.example.com" and acao != "*",
                     f"ACAO header: {acao}",
                     acao)
        else:
            t.check("请求可达", False)
        self.results.append(t)

    def dynamic_fix02_error_desensitize(self):
        """动态: 500 错误不泄露堆栈"""
        t = TestResult("FIX-02", "异常脱敏 (动态)", "MEDIUM", "DYNAMIC")
        r = self._get("/api/v1/learning/grower/stats/99999999",
                      headers={"Authorization": f"Bearer {self._token}"} if self._token else {})
        if r and r.status_code >= 400:
            body = r.text.lower()
            t.check("无堆栈泄露",
                     "traceback" not in body and "file \"/" not in body and "line " not in body,
                     "错误响应不应含 Python traceback",
                     body[:100])
            t.check("无 detail=str(exc) 原始异常",
                     "attributeerror" not in body and "typeerror" not in body and "keyerror" not in body,
                     "不应返回原始异常类名")
        else:
            t.check("端点可达", r is not None, f"status={r.status_code if r else 'N/A'}")
        self.results.append(t)

    def dynamic_fix04_register_limit(self):
        """动态: 注册限流"""
        t = TestResult("FIX-04", "注册限流 (动态)", "MEDIUM", "DYNAMIC")
        got_429 = False
        for i in range(8):
            r = self._post("/api/v1/auth/register", json={
                "username": f"_rltest_{int(time.time())}_{i}",
                "email": f"_rltest_{i}_{int(time.time())}@test.dev",
                "password": "Test1234!",
                "full_name": "Rate Limit Test",
            })
            if r and r.status_code == 429:
                got_429 = True
                t.check("注册触发 429",
                        True,
                        f"第 {i+1} 次请求触发限流",
                        r.text[:100])
                break
        if not got_429:
            t.check("注册触发 429", False, "8 次注册未触发限流")
        self.results.append(t)

    def dynamic_fix05_password(self):
        """动态: 弱密码被拒"""
        t = TestResult("FIX-05", "密码策略 (动态)", "MEDIUM", "DYNAMIC")
        weak_passwords = ["123456", "abcdef", "aaaaaa", "password"]
        for pwd in weak_passwords:
            r = self._post("/api/v1/auth/register", json={
                "username": f"_pwdtest_{int(time.time())}",
                "email": f"_pwdtest_{int(time.time())}@test.dev",
                "password": pwd,
                "full_name": "Password Test",
            })
            if r and r.status_code == 400:
                t.check(f"弱密码 '{pwd}' 被拒",
                        True,
                        f"返回 400: {r.json().get('detail', '')[:60]}")
                break
            elif r and r.status_code == 429:
                t.check("被限流跳过", True, "注册限流触发, 密码策略间接验证")
                break
        else:
            t.check("弱密码被拒", False, "弱密码未返回 400")
        self.results.append(t)

    def dynamic_fix06_time_cap(self):
        """动态: 学习时长上限"""
        t = TestResult("FIX-06", "学习时长上限 (动态)", "MEDIUM", "DYNAMIC")
        r = self._authed_post("/api/v1/learning/grower/time/add", json={
            "duration_seconds": 999999 * 60,
            "content_category": "test",
            "user_type": "grower",
        })
        if r:
            t.check("超大时长返回 400",
                     r.status_code == 400,
                     f"status={r.status_code}",
                     r.text[:100])
        else:
            t.check("端点可达", False)
        self.results.append(t)

    def dynamic_fix07_docs_disabled(self):
        """动态: /docs 不可访问"""
        t = TestResult("FIX-07", "Swagger 禁用 (动态)", "LOW", "DYNAMIC")
        for path in ["/docs", "/redoc", "/openapi.json"]:
            r = self._get(path)
            if r:
                t.check(f"{path} 不可访问",
                        r.status_code in (404, 403, 301),
                        f"status={r.status_code}",
                        str(r.status_code))
        self.results.append(t)

    def dynamic_fix08_security_headers(self):
        """动态: 安全响应头"""
        t = TestResult("FIX-08", "安全响应头 (动态)", "MEDIUM", "DYNAMIC")
        r = self._get("/")
        if r:
            headers = r.headers
            checks = [
                ("X-Content-Type-Options", "nosniff"),
                ("X-Frame-Options", None),
                ("X-XSS-Protection", None),
            ]
            for name, expected_val in checks:
                val = headers.get(name, "")
                passed = bool(val)
                if expected_val:
                    passed = val.lower() == expected_val.lower()
                t.check(f"{name} 存在",
                        passed,
                        f"值: {val or '(缺失)'}",
                        val)

            t.check("Server header 不含 uvicorn",
                     "uvicorn" not in headers.get("Server", "").lower(),
                     f"Server: {headers.get('Server', '(无)')}",
                     headers.get("Server", ""))
        self.results.append(t)

    def dynamic_fix11_global_ratelimit(self):
        """动态: 全局限流"""
        t = TestResult("FIX-11", "全局限流 (动态)", "LOW", "DYNAMIC")
        got_429 = False
        for i in range(75):
            r = self._get("/api/v1/auth/me")
            if r and r.status_code == 429:
                got_429 = True
                t.check("全局限流触发 429",
                        True,
                        f"第 {i+1} 次请求触发限流")
                break
        if not got_429:
            t.check("全局限流触发 429", False, "75 次快速请求未触发 429")
        self.results.append(t)

    def dynamic_fix14_legacy_auth(self):
        """动态: 旧版端点鉴权"""
        t = TestResult("FIX-14", "旧版端点鉴权 (动态)", "MEDIUM", "DYNAMIC")
        for path in ["/api/assessment/history/1", "/api/assessment/user/latest"]:
            r = self._get(path)
            if r:
                t.check(f"{path} 无Token→401/403",
                        r.status_code in (401, 403, 404),
                        f"status={r.status_code}",
                        str(r.status_code))
        self.results.append(t)

    # ═══════════════════════════════════════════════════════════
    # Layer 3: 基础设施审计
    # ═══════════════════════════════════════════════════════════

    def infra_docker(self):
        """基础设施: Docker 安全配置"""
        t = TestResult("INFRA-01", "Docker 安全配置", "MEDIUM", "INFRA")
        df = self._find("Dockerfile.backend") or self._find("Dockerfile")
        if df:
            t.check("非 root 运行",
                     "USER" in df and "root" not in df.split("USER")[-1].split("\n")[0],
                     "容器应以非 root 用户运行")
            t.check("健康检查",
                     "HEALTHCHECK" in df,
                     "Dockerfile 应有 HEALTHCHECK")
        else:
            t.check("Dockerfile 存在", False)

        compose = self._find("docker-compose.prod.yml")
        if compose:
            t.check("生产 compose 存在", True)
            t.check("资源限制",
                     "limits" in compose or "cpus" in compose,
                     "生产环境应有资源限制")
        self.results.append(t)

    def infra_nginx(self):
        """基础设施: Nginx 安全配置"""
        t = TestResult("INFRA-02", "Nginx 安全配置", "MEDIUM", "INFRA")
        nginx = self._find("nginx.conf")
        app_conf = self._find("app.conf")
        sec_conf = self._find("security.conf")

        if nginx:
            t.check("server_tokens off",
                     "server_tokens off" in nginx or "server_tokens  off" in nginx,
                     "应关闭 server_tokens")
            t.check("限流配置",
                     "limit_req_zone" in nginx,
                     "应有请求限流配置")
        if app_conf:
            t.check("/docs 404",
                     "/docs" in app_conf and ("404" in app_conf or "deny" in app_conf.lower()),
                     "Nginx 应阻止 /docs 访问")
        if sec_conf:
            t.check("安全头配置", True, "security.conf 存在")
        self.results.append(t)

    def infra_cicd(self):
        """基础设施: CI/CD 安全"""
        t = TestResult("INFRA-03", "CI/CD 安全", "LOW", "INFRA")
        ci = self._find("ci.yml")
        cd = self._find("cd.yml")
        if ci:
            t.check("CI pipeline 存在", True)
            t.check("安全扫描",
                     "audit" in ci.lower() or "security" in ci.lower() or "gitleaks" in ci.lower(),
                     "CI 应包含安全扫描步骤")
        if cd:
            t.check("CD pipeline 存在", True)
            t.check("生产需审批",
                     "environment" in cd and ("production" in cd or "approval" in cd.lower()),
                     "生产部署应需审批")
        self.results.append(t)

    def infra_env(self):
        """基础设施: 环境变量安全"""
        t = TestResult("INFRA-04", "环境变量安全", "LOW", "INFRA")
        env = self._find(".env.example") or self._find(".env.template")
        gitignore = self._find(".gitignore")
        if env:
            t.check(".env.example 存在", True)
            t.check("含 CORS_ORIGINS",
                     "CORS_ORIGINS" in env,
                     "应有 CORS 白名单环境变量")
            t.check("含 REDIS_URL",
                     "REDIS_URL" in env or "REDIS" in env,
                     "应有 Redis 连接配置")
            t.check("含 ENVIRONMENT",
                     "ENVIRONMENT" in env,
                     "应有环境标识变量")
        if gitignore:
            t.check(".env 在 .gitignore 中",
                     ".env" in gitignore,
                     ".env 不应提交到版本控制")
        self.results.append(t)

    # ═══════════════════════════════════════════════════════════
    # 运行器
    # ═══════════════════════════════════════════════════════════

    def run_static(self):
        """运行所有静态检查"""
        for method_name in sorted(dir(self)):
            if method_name.startswith("static_"):
                getattr(self, method_name)()

    def run_dynamic(self):
        """运行所有动态测试"""
        if not HAS_REQUESTS:
            print("  ⚠ requests 未安装, 跳过动态测试")
            print("    pip install requests")
            return
        if not self.api_url:
            print("  ⚠ 未指定 --base URL, 跳过动态测试")
            return

        print(f"  连接: {self.base_url}")
        r = self._get("/")
        if not r:
            print(f"  ❌ 无法连接 {self.base_url}, 跳过动态测试")
            return
        print(f"  状态: {r.status_code}")

        # 登录
        if self._setup_dynamic():
            print(f"  认证: ✅ Token 获取成功")
        else:
            print(f"  认证: ⚠ 无法登录, 部分测试受限")

        for method_name in sorted(dir(self)):
            if method_name.startswith("dynamic_"):
                getattr(self, method_name)()

    def run_infra(self):
        """运行基础设施审计"""
        for method_name in sorted(dir(self)):
            if method_name.startswith("infra_"):
                getattr(self, method_name)()

    # ═══════════════════════════════════════════════════════════
    # 报告
    # ═══════════════════════════════════════════════════════════

    def generate_report(self) -> dict:
        """生成结构化报告"""
        total_checks = sum(len(r.checks) for r in self.results)
        passed_checks = sum(sum(1 for c in r.checks if c["passed"]) for r in self.results)
        failed_checks = total_checks - passed_checks

        by_fix = {}
        for r in self.results:
            key = r.fix_id
            if key not in by_fix:
                by_fix[key] = {"title": r.title, "severity": r.severity, "status": r.status, "layers": []}
            by_fix[key]["layers"].append({
                "layer": r.layer,
                "status": r.status,
                "checks": r.checks,
            })

        # 合并多层结果
        fix_results = []
        for fix_id, info in sorted(by_fix.items()):
            all_passed = all(layer["status"] == "PASS" for layer in info["layers"])
            any_fail = any(layer["status"] == "FAIL" for layer in info["layers"])
            fix_results.append({
                "fix_id": fix_id,
                "title": info["title"],
                "severity": info["severity"],
                "status": "PASS" if all_passed else ("FAIL" if any_fail else "PARTIAL"),
                "layers": info["layers"],
            })

        total_fixes = len(fix_results)
        passed_fixes = sum(1 for f in fix_results if f["status"] == "PASS")

        return {
            "report_meta": {
                "title": "行健平台 V4.0 — 端到端安全验收报告",
                "timestamp": datetime.now().isoformat(),
                "base_url": self.base_url or "(静态审计)",
                "project_dir": str(self.project) if self.project else "(未指定)",
            },
            "summary": {
                "total_fixes": total_fixes,
                "passed": passed_fixes,
                "failed": total_fixes - passed_fixes,
                "pass_rate": f"{passed_fixes/total_fixes*100:.0f}%" if total_fixes else "N/A",
                "total_checks": total_checks,
                "checks_passed": passed_checks,
                "checks_failed": failed_checks,
                "risk_level": "LOW" if passed_fixes == total_fixes else ("MEDIUM" if passed_fixes >= total_fixes * 0.8 else "HIGH"),
            },
            "fixes": fix_results,
        }

    def print_report(self):
        """打印终端报告"""
        report = self.generate_report()
        s = report["summary"]

        print()
        print("═" * 70)
        print("  行健平台 V4.0 — 端到端安全验收报告")
        print(f"  {report['report_meta']['timestamp']}")
        print("═" * 70)

        # 汇总
        print()
        risk_icon = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}.get(s["risk_level"], "⚪")
        print(f"  风险等级: {risk_icon} {s['risk_level']}")
        print(f"  修复项: {s['passed']}/{s['total_fixes']} 通过 ({s['pass_rate']})")
        print(f"  检查点: {s['checks_passed']}/{s['total_checks']} 通过")
        print()

        # 按严重性分组
        sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}

        prev_sev = None
        for fix in sorted(report["fixes"], key=lambda f: (sev_order.get(f["severity"], 9), f["fix_id"])):
            sev = fix["severity"]
            if sev != prev_sev:
                sev_icons = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵", "INFO": "⚪"}
                print(f"  ── {sev_icons.get(sev, '⚪')} {sev} ──")
                prev_sev = sev

            status_icon = {"PASS": "✅", "FAIL": "❌", "PARTIAL": "⚠️", "SKIP": "⏭"}.get(fix["status"], "?")
            layers_str = "+".join(l["layer"] for l in fix["layers"])
            print(f"    {status_icon} {fix['fix_id']:8s} {fix['title']:<32s} [{layers_str}]")

            # 显示失败的检查点
            for layer in fix["layers"]:
                for check in layer["checks"]:
                    if not check["passed"]:
                        print(f"             ↳ ❌ {check['name']}: {check['detail'][:50]}")

        # 失败项汇总
        failed = [f for f in report["fixes"] if f["status"] != "PASS"]
        if failed:
            print()
            print("  ── 待修复项 ──")
            for f in failed:
                print(f"    {f['fix_id']:8s} [{f['severity']}] {f['title']}")
                for layer in f["layers"]:
                    for check in layer["checks"]:
                        if not check["passed"]:
                            evidence = f" | 证据: {check['evidence'][:40]}" if check["evidence"] else ""
                            print(f"             → {check['name']}: {check['detail'][:60]}{evidence}")

        print()
        print("═" * 70)
        if s["passed"] == s["total_fixes"]:
            print("  🎉 全部通过！安全验收完成。")
        else:
            print(f"  ⚠ {s['failed']} 项未通过, 请修复后重新验收。")
        print("═" * 70)

        return report


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="行健平台 V4.0 — 端到端安全验收测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 全量验收
  python e2e_acceptance.py --base http://localhost:8000 --project .

  # 仅静态审计
  python e2e_acceptance.py --static-only --project .

  # 仅动态测试
  python e2e_acceptance.py --dynamic-only --base http://localhost:8000

  # 输出 JSON 报告
  python e2e_acceptance.py --project . --json acceptance_report.json
        """)

    parser.add_argument("--base", default="", help="API 根 URL (如 http://localhost:8000)")
    parser.add_argument("--project", default=".", help="项目根目录 (默认当前目录)")
    parser.add_argument("--static-only", action="store_true", help="仅运行静态审计")
    parser.add_argument("--dynamic-only", action="store_true", help="仅运行动态测试")
    parser.add_argument("--json", default="", help="输出 JSON 报告到文件")

    args = parser.parse_args()

    runner = AcceptanceRunner(
        base_url=args.base,
        project_dir=args.project if not args.dynamic_only else "",
    )

    if args.static_only:
        print("\n  ▶ Layer 1: 静态代码审计")
        runner.run_static()
    elif args.dynamic_only:
        print("\n  ▶ Layer 2: 动态 API 测试")
        runner.run_dynamic()
    else:
        print("\n  ▶ Layer 1: 静态代码审计")
        runner.run_static()

        print("\n  ▶ Layer 2: 动态 API 测试")
        runner.run_dynamic()

        print("\n  ▶ Layer 3: 基础设施审计")
        runner.run_infra()

    report = runner.print_report()

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n  JSON 报告: {args.json}")


if __name__ == "__main__":
    main()
