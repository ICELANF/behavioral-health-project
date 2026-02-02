# 行为健康数字平台 - v15 完整版变更日志
# CHANGELOG v15.0 (Full Release)

## 版本: v15.0.0
## 发布日期: 2026-02-01
## 代号: "黑盒评估，白盒干预"

---

## 一、版本演进

```
v11 (用户本地版)
 │  ├── Dify深度集成
 │  ├── Ollama本地备份
 │  ├── 患者H5门户
 │  └── 基础TriggerEngine
 │
 └─► v14 (Claude整合版)
      ├── [v14.0] 功能开关系统
      ├── [v14.0] Trigger事件路由
      ├── [v14.0] 节律模型
      ├── [v14.0] Agent增强
      ├── [v14.0] 质量审计
      │
      └─► v14.1 (增量更新)
           ├── [v14.1] 披露控制模块
           ├── [v14.1] 专家审核工作台
           ├── [v14.1] 四级权限架构
           │
           └─► v15.0 (完整版)
                ├── [v15.0] 评估结果展示适配
                ├── [v15.0] 权限API完整实现
                ├── [v15.0] 前后端接口规范
                └── [v15.0] 部署与测试指南
```

---

## 二、核心设计理念

### "黑盒评估，白盒干预"

| 角色 | 评估过程 | 评估结果 | 干预执行 |
|------|----------|----------|----------|
| 患者 | ✅ 参与 | ❌ 不可见 | ✅ 接收 |
| 教练 | ❌ 不参与 | ✅ 摘要可见 | ✅ 执行 |
| 专家 | ❌ 不参与 | ✅ 完整可见 | ✅ 审核 |
| 管理 | ❌ 不参与 | ✅ 脱敏统计 | ✅ 配置 |

### 四级权限架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        数据流向                                  │
│                                                                  │
│   ┌─────────┐                                                   │
│   │ 患者端   │ ─────────────────────────────────────────────┐   │
│   │ (C端)   │ 完成问卷、打卡                                 │   │
│   └────┬────┘                                                │   │
│        │ 原始数据                                            │   │
│        ▼                                                     │   │
│   ┌─────────┐     ┌─────────┐     ┌─────────┐              │   │
│   │ 评估引擎 │────▶│ 教练端   │────▶│ 专家端   │              │   │
│   │         │     │ (B端)   │     │         │              │   │
│   └────┬────┘     └────┬────┘     └────┬────┘              │   │
│        │              │              │                      │   │
│        │ 评估结果      │ 干预建议      │ 审核批准             │   │
│        │ (不可见)      │ (执行)       │ (确认)              │   │
│        │              │              │                      │   │
│        │              ▼              │                      │   │
│        │         ┌─────────┐        │                      │   │
│        └────────▶│ 正向反馈 │◀───────┘                      │   │
│                  └────┬────┘                                │   │
│                       │                                      │   │
│                       ▼                                      │   │
│                  ┌─────────┐                                │   │
│                  │ 患者端   │ 收到激励消息                    │   │
│                  └─────────┘                                │   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 三、完整模块清单

### 3.1 核心模块 (core/)

| 模块 | 文件 | 说明 |
|------|------|------|
| v14配置 | `core/v14/config.py` | 功能开关系统 |
| 事件路由 | `core/v14/trigger_router.py` | Trigger事件路由 |
| 节律引擎 | `core/v14/rhythm_engine.py` | 节律检测模型 |
| Agent增强 | `core/v14/agents.py` | Safety/Resistance/Explain |

### 3.2 质量审计 (quality/)

| 文件 | 说明 |
|------|------|
| `quality/schema.py` | 审计数据模型 |
| `quality/judge_prompt.py` | Judge Prompt构建 |
| `quality/llm_judge.py` | LLM评判执行器 |

### 3.3 披露控制 (disclosure/)

| 文件 | 说明 |
|------|------|
| `disclosure/blacklist.py` | 敏感词库（60+词条） |
| `disclosure/signature.py` | 双重签名机制 |
| `disclosure/controller.py` | 披露控制器（17章节） |
| `disclosure/rewriter.py` | AI文案重写器（100+规则） |
| `disclosure/permissions.py` | **[NEW]** 四级权限管理 |
| `disclosure/display_adapter.py` | **[NEW]** 展示适配器 |

### 3.4 专家工作台 (workbench/)

| 文件 | 说明 |
|------|------|
| `workbench/expert_review.py` | Streamlit审核界面 |

### 3.5 API路由 (api/v14/)

| 文件 | 路由前缀 | 说明 |
|------|----------|------|
| `routes.py` | `/api/v2/` | v14主路由 |
| `quality_routes.py` | `/api/v2/quality/` | 质量审计API |
| `disclosure_routes.py` | `/api/v2/disclosure/` | 披露控制API |

---

## 四、API端点完整清单

### 4.1 v14核心 (/api/v2/)

| 端点 | 方法 | 说明 |
|------|------|------|
| `/status` | GET | v14状态 |
| `/health` | GET | 健康检查 |
| `/features` | GET | 功能开关 |
| `/trigger/emit` | POST | 发送事件 |
| `/rhythm/detect` | POST | 节律检测 |
| `/agent/process` | POST | Agent处理 |

### 4.2 质量审计 (/api/v2/quality/)

| 端点 | 方法 | 说明 |
|------|------|------|
| `/audit` | POST | 启动审计 |
| `/audit-batch` | POST | 批量审计 |
| `/audit/result/{id}` | GET | 获取结果 |
| `/audit/status` | GET | 系统状态 |

### 4.3 披露控制 (/api/v2/disclosure/)

| 端点 | 方法 | 说明 |
|------|------|------|
| `/decision/create` | POST | 创建披露决策 |
| `/decision/{id}` | GET | 获取决策 |
| `/decision/{id}/sign` | POST | 签名 |
| `/decision/{id}/approve` | POST | 批准 |
| `/decision/{id}/reject` | POST | 驳回 |
| `/chapters` | GET | 章节列表 |
| `/blacklist` | GET | 禁词库 |
| `/blacklist/check` | POST | 检查敏感词 |
| `/rewrite` | POST | AI重写 |
| `/pending` | GET | 待审核列表 |

---

## 五、患者端数据过滤规则

### 5.1 隐藏字段（患者不可见）

```python
HIDDEN_FROM_PATIENT = [
    "ttm_stage",           # 改变阶段
    "ttm_stage_label",     # 阶段标签
    "bpt6_type",           # 行为模式
    "big5_scores",         # 大五人格分数
    "big5_interpretation", # 大五解读
    "risk_level",          # 风险等级
    "risk_assessment",     # 风险评估
    "capacity_score",      # 改变力得分
    "spi_score",           # 成功预测
    "mental_health_risk",  # 心理健康风险
    "expert_notes",        # 专家备注
    "raw_assessment",      # 原始评估
    "coach_notes",         # 教练备注
]
```

### 5.2 转换规则（患者可见版本）

| 原始标签 | 患者端显示 |
|----------|-----------|
| 前意向期 | 健康意识正在觉醒 |
| 意向期 | 开始关注健康了 |
| 准备期 | 准备好迈出第一步 |
| 行动期 | 正在积极行动 |
| 维持期 | 养成了好习惯 |
| 高风险 | 需要更多支持 |
| 低风险 | 状态非常棒 |

---

## 六、教练端数据视图

### 6.1 可见字段

```python
VISIBLE_TO_COACH = [
    "ttm_stage",           # 改变阶段 ✓
    "bpt6_type",           # 行为模式 ✓
    "risk_level",          # 风险等级 ✓
    "intervention_plan",   # 干预计划 ✓
    "ai_recommendations",  # AI建议 ✓
]
```

### 6.2 提供功能

- 学员画像摘要
- 阶段描述和干预建议
- 风险提示
- AI推荐的干预话术
- 观察备注添加

---

## 七、专家端审核流程

### 7.1 审核工作流

```
1. 系统自动评估
      ↓
2. 进入待审核队列
      ↓
3. 专家查看完整报告
      ↓
4. 编辑脱敏内容
      ↓
5. 设置章节可见性
      ↓
6. 第一负责人签名
      ↓
7. 第二负责人签名（高风险）
      ↓
8. 披露至患者端
```

### 7.2 双重签名规则

| 风险等级 | 签名要求 | 超时 |
|----------|----------|------|
| CRITICAL | 双签名必须 | 24h |
| HIGH | 双签名必须 | 48h |
| MODERATE | 单签名 | 72h |
| LOW | 可自动 | - |

---

## 八、部署指南

### 8.1 服务端口规划

| 端口 | 服务 | 说明 |
|------|------|------|
| 8000 | Agent Gateway | Agent网关 |
| 8001 | BAPS API | 评估API |
| 8002 | Decision Engine | 决策引擎(main.py) |
| 8003 | Quality Service | 质量审计服务 |
| 8501 | Expert Workbench | 专家工作台(Streamlit) |

### 8.2 启动命令

```bash
# 1. 主服务（决策引擎）
python main.py  # 端口8002

# 2. 质量审计服务（可选）
python run_quality_service.py --port 8003

# 3. 专家审核工作台
streamlit run workbench/expert_review.py --server.port 8501
```

### 8.3 环境变量

```bash
# v14功能开关
BH_V14_ENABLE_TRIGGER_EVENT_ROUTING=true
BH_V14_ENABLE_RHYTHM_MODEL=true
BH_V14_ENABLE_V14_AGENTS=true

# 披露控制
BH_V14_ENABLE_DISCLOSURE_CONTROL=true
BH_V14_ENABLE_BLACKLIST_FILTER=true
BH_V14_ENABLE_DUAL_SIGNATURE=true

# 质量审计
BH_V14_ENABLE_QUALITY_AUDIT=true
QUALITY_JUDGE_MODEL=qwen2.5:14b
QUALITY_JUDGE_BACKEND=ollama
```

---

## 九、测试用例

### 9.1 患者数据过滤测试

```bash
# 获取患者端视图（应不含敏感字段）
curl "http://localhost:8002/api/v2/disclosure/decision/RPT_001/patient-message"
```

### 9.2 敏感词检测测试

```bash
curl -X POST "http://localhost:8002/api/v2/disclosure/blacklist/check" \
  -H "Content-Type: application/json" \
  -d '{"text": "用户高神经质，处于抗拒阶段"}'
```

### 9.3 AI重写测试

```bash
curl -X POST "http://localhost:8002/api/v2/disclosure/rewrite" \
  -H "Content-Type: application/json" \
  -d '{"text": "用户低尽责性，执行力差"}'
```

---

## 十、文件清单

```
v15/
├── core/
│   └── v14/
│       ├── __init__.py
│       ├── config.py         # 功能开关
│       ├── trigger_router.py # 事件路由
│       ├── rhythm_engine.py  # 节律引擎
│       └── agents.py         # Agent增强
│
├── quality/
│   ├── __init__.py
│   ├── schema.py
│   ├── judge_prompt.py
│   └── llm_judge.py
│
├── disclosure/
│   ├── __init__.py
│   ├── blacklist.py          # 敏感词库
│   ├── signature.py          # 双重签名
│   ├── controller.py         # 披露控制器
│   ├── rewriter.py           # AI重写器
│   ├── permissions.py        # [NEW] 四级权限
│   └── display_adapter.py    # [NEW] 展示适配
│
├── workbench/
│   ├── __init__.py
│   └── expert_review.py      # 专家工作台
│
├── api/v14/
│   ├── __init__.py
│   ├── routes.py
│   ├── quality_routes.py
│   └── disclosure_routes.py
│
├── main.py                   # 主入口
├── run_quality_service.py    # 质量审计服务
├── CHANGELOG_v14.md
├── CHANGELOG_v14.1.md
└── CHANGELOG_v15.md          # 本文件
```

---

## 十一、下一版本规划 (v16)

1. **教练端仪表盘** - Streamlit/React界面
2. **患者端问卷组件** - 不显示结果的评估入口
3. **实时通知系统** - 风险升级通知
4. **审计日志系统** - 操作追溯
5. **多租户支持** - 机构隔离

---

*文档版本: 1.0 | 构建时间: 2026-02-01*
*设计理念: 黑盒评估，白盒干预*
