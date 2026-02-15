# CI/CD 集成指南 — 行健平台 V4.0

## 架构概览

```
  开发者 push/PR
       │
       ▼
  ┌─────────────────────────────────────────────────────────┐
  │  CI — ci-security.yml                                   │
  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
  │  │ 静态审计     │→ │ E2E 验收     │→ │ 渗透测试     │  │
  │  │ bandit       │  │ 125 tests    │  │ (仅 main)    │  │
  │  │ pip-audit    │  │ 10 phases    │  │ 60+ checks   │  │
  │  │ 自定义检查   │  │ 8 roles      │  │              │  │
  │  └──────────────┘  └──────────────┘  └──────────────┘  │
  └─────────────────────────────────────────────────────────┘
       │ CI 通过
       ▼
  ┌─────────────────────────────────────────────────────────┐
  │  CD — cd-deploy.yml                                     │
  │  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐  │
  │  │ Deploy   │→ │ Staging 验收 │→ │ Deploy Prod      │  │
  │  │ Staging  │  │ acceptance   │  │ (需 GitHub 审批)  │  │
  │  │          │  │ + pentest    │  │ + 生产验收        │  │
  │  └──────────┘  └──────────────┘  └──────────────────┘  │
  └─────────────────────────────────────────────────────────┘
       │
       ▼ 每季度自动
  ┌─────────────────────────────────────────────────────────┐
  │  quarterly-scan.yml                                     │
  │  完整渗透 + 依赖审计 + 报告归档 (保留 365 天)          │
  └─────────────────────────────────────────────────────────┘
```

## 快速接入步骤

### 1. 复制文件到项目

```bash
# 复制 CI/CD 配置
cp -r .github/ /你的项目路径/
cp Makefile /你的项目路径/

# 确保测试脚本在位
ls scripts/e2e_acceptance.py     # E2E 验收
ls scripts/pentest_bhp.py        # 渗透测试
ls scripts/seed_demo_accounts.py # Demo 账号
```

### 2. 配置 GitHub Secrets

到仓库 Settings → Secrets and variables → Actions，添加：

| Secret | 说明 | 示例 |
|--------|------|------|
| `STAGING_HOST` | Staging 服务器 IP | `10.0.1.50` |
| `STAGING_USER` | SSH 用户名 | `deploy` |
| `STAGING_SSH_KEY` | SSH 私钥 | `-----BEGIN OPENSSH...` |
| `STAGING_URL` | Staging 访问 URL | `http://staging.xingjian.com` |
| `STAGING_PATH` | 服务器项目路径 | `/opt/behaviros` |
| `PROD_HOST` | 生产服务器 IP | `10.0.0.10` |
| `PROD_USER` | SSH 用户名 | `deploy` |
| `PROD_SSH_KEY` | SSH 私钥 | `-----BEGIN OPENSSH...` |
| `PROD_URL` | 生产访问 URL | `https://app.xingjian.com` |
| `PROD_PATH` | 服务器项目路径 | `/opt/behaviros` |

### 3. 配置 GitHub Environments

到 Settings → Environments：

**staging**
- 无需审批 (CI 通过后自动部署)

**production**
- Required reviewers: 添加审批人 (至少 1 人)
- Wait timer: 可选 5 分钟冷静期
- Deployment branches: 仅 `main`

### 4. 确保服务器环境变量

Staging 和 Production 的 `.env` 文件：

```env
ENVIRONMENT=production          # staging 用 staging
CORS_ORIGINS=https://app.xingjian.com
REDIS_URL=redis://:密码@localhost:6379/0
DATABASE_URL=postgresql://bhp:密码@localhost:5432/bhp
JWT_SECRET=你的密钥
JWT_ALGORITHM=HS256
```

### 5. 服务器 systemd 配置

```ini
# /etc/systemd/system/behaviros-api.service
[Unit]
Description=BehaviorOS API
After=network.target postgresql.service redis.service

[Service]
User=deploy
WorkingDirectory=/opt/behaviros
EnvironmentFile=/opt/behaviros/.env
ExecStart=/opt/behaviros/venv/bin/uvicorn api.main:app \
    --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## 日常使用

### 本地开发

```bash
make test          # 单元测试
make acceptance    # E2E 验收 (需要本地服务运行)
make pentest       # 渗透测试
make security      # 全套: audit + acceptance + pentest
make seed          # 初始化 demo 账号
```

### 部署

```bash
# 自动: push 到 main → CI 通过 → 自动部署 staging → staging 验收

# 手动部署 staging
make deploy-stg

# 手动部署 production (先过安全检查 + 确认)
make deploy-prod

# GitHub Actions 手动触发
gh workflow run "CD — Deploy & Verify" --field target=production
```

### 季度安全扫描

自动在 1/4/7/10 月第一个周一运行。手动触发：

```bash
gh workflow run "Quarterly Security Scan"
# 或指定目标
gh workflow run "Quarterly Security Scan" --field target_url=https://app.xingjian.com
```

## CI 安全门禁标准

| 检查项 | 阈值 | 阻断 |
|--------|------|------|
| Bandit HIGH | 0 | ✅ 阻断 PR |
| pip-audit CRITICAL/HIGH | 0 | ✅ 阻断 PR |
| E2E acceptance FAIL | 0 | ✅ 阻断部署 |
| E2E risk_level | 必须 LOW | ✅ 阻断部署 |
| Pentest CRITICAL/HIGH | 0 | ✅ 阻断生产 |
| f-string SQL | 0 | ✅ 阻断 PR |
| CORS wildcard | 0 | ✅ 阻断 PR |

## 报告归档

| 报告 | 位置 | 保留 |
|------|------|------|
| CI 验收 | Actions Artifacts → acceptance-report | 90 天 |
| Staging 验收 | Actions Artifacts → staging-reports | 90 天 |
| 生产验收 | Actions Artifacts → production-reports | 180 天 |
| 季度扫描 | Actions Artifacts → quarterly-scan-N | 365 天 |

## 紧急部署 (跳过渗透测试)

```bash
gh workflow run "CD — Deploy & Verify" \
  --field target=production \
  --field skip_pentest=true
```

注意: 紧急部署仅跳过渗透测试，E2E 验收仍然执行。部署后应尽快补跑完整安全扫描。
