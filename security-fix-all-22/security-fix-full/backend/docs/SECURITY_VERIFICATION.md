# 行健平台 V4.0 — 安全修复验证清单 (22/22)

## 验证命令

```bash
# 1. 运行渗透测试脚本
python pentest_bhp.py --base http://localhost:8000/api/v1

# 2. 检查新模块存在
ls core/rate_limiter.py \
   core/security_middleware.py \
   core/access_control.py \
   core/token_blacklist_redis.py \
   core/rate_limit_middleware.py \
   core/token_storage.py \
   core/legacy_auth_middleware.py \
   core/log_sanitizer.py \
   core/https_middleware.py \
   core/public_id.py \
   core/csrf_audit_middleware.py \
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
