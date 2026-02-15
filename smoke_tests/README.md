# 行健平台 V4.0 — 上线前冒烟测试套件

## 快速开始

```bash
# 1. 复制到项目根目录
cp -r smoke_tests/ /path/to/xingjian-platform/

# 2. 安装依赖
pip install httpx pytest pytest-html

# 3. 配置目标服务（默认 localhost:8000）
export XINGJIAN_BASE_URL=http://localhost:8000

# 4. 运行
chmod +x smoke_tests/run_smoke.sh
./smoke_tests/run_smoke.sh all
```

## 文件清单

```
smoke_tests/
├── run_smoke.sh                          # 主执行器
├── conftest.py                           # 共享配置 + 报告收集
├── seed_smoke_data.py                    # 种子数据（多角色测试账号）
├── test_day1_golden_path_entry.py        # Day1: 访客→注册→HF-20→AI→S0
├── test_day2_golden_path_progression.py  # Day2: S0-S4→积分→晋级→防刷
├── test_day3_safety_governance_rbac.py   # Day3: 安全+治理+RBAC
├── patches/
│   ├── audit_patch_guide.py              # 审计补全（0.5天）
│   └── rbac_gap_fix.py                   # RBAC 93→100%（2天）
└── reports/                              # 自动生成的测试报告
```

## 3天执行计划

| 天 | 命令 | 覆盖Sheet | 验收标准 |
|---|---|---|---|
| Day 1 | `./run_smoke.sh day1` | ③⑤⑧ | 全程无500/403，数据库状态一致 |
| Day 2 | `./run_smoke.sh day2` | ④⑦⑪ | 积分正确累积，双轨4状态可达，防刷触发 |
| Day 3 | `./run_smoke.sh day3` | ②⑥⑨⑬⑮ | 安全拦截可验证，仪表盘可达，越权被拦 |

## 后续任务（冒烟通过后）

| 序号 | 任务 | 工期 |
|---|---|---|
| 1 | 冒烟阻塞bug修复 | 1-2天 |
| 2 | 审计补全（`patches/audit_patch_guide.py`） | 0.5天 |
| 3 | RBAC封口（`patches/rbac_gap_fix.py`） | 2天 |
| 4 | Agent双层架构RFC | 2天 |
| 5 | Agent双层物理分离编码（V4.1主线） | 4周 |

## 适配指南

测试脚本中的API路径基于契约注册表V4.0推断。实际项目中可能存在路径差异，需调整的位置：

1. **API前缀** — 修改 `conftest.py` 中的 `API_PREFIX`
2. **端点路径** — 每个测试类中的路径如果返回404，测试会skip而非fail，日志中会标注具体路径
3. **认证方式** — 默认Bearer Token，如用Cookie认证需修改 `_login` 函数
4. **种子账号** — Admin/Coach需预置，详见 `seed_smoke_data.py` 中的SQL模板
