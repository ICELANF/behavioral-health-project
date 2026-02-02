# 行为健康数字平台 - v16 完整版变更日志
# CHANGELOG v16.0 (Full Release)

## 版本: v16.0.0
## 发布日期: 2026-02-02
## 代号: "母库驱动，指令即界面"

---

## 一、版本演进总览

```
v11 (Dify集成版)
 │
 └─► v14 (Claude整合版)
      ├── 功能开关系统
      ├── Trigger事件路由
      ├── 节律模型
      └── Agent增强
           │
           └─► v14.1 (披露控制版)
                ├── 敏感词库
                ├── 双重签名
                ├── 专家工作台
                └── 四级权限
                     │
                     └─► v16.0 (母库驱动版) ← 当前版本
                          ├── 行为逻辑引擎
                          ├── 状态同步服务
                          ├── Admin无代码配置
                          └── Action-to-UI协议
```

---

## 二、v16 核心新增

### 2.1 行为逻辑引擎 (Logic Engine)

**目标**: 将所有 `if user.stage == 'xxx'` 硬编码替换为配置驱动

**文件位置**: `services/logic_engine/`

| 文件 | 大小 | 说明 |
|------|------|------|
| `schema/rules_definition.py` | 12KB | Pydantic模型定义 |
| `behavior_engine.py` | 14KB | 核心引擎实现 |

**使用方式**:
```python
from services.logic_engine import get_behavior_engine

engine = get_behavior_engine()

# 替代 if user.stage == 'S1' and sentiment == 'negative'
result = engine.evaluate_state(
    user_id="user_001",
    user_context={"stage": "S1"},
    new_snippet={"text": "今天压力好大，想吃零食", "sentiment": "negative"}
)

if result:
    trigger, action = result
    print(f"触发: {trigger.id} → 动作: {action.action_id}")
```

### 2.2 状态同步服务 (State Sync)

**目标**: 实现"一套输入，两套表述"

**文件位置**: `services/state_sync/`

| 文件 | 大小 | 说明 |
|------|------|------|
| `manager.py` | 21KB | StateSyncManager实现 |

**C端视图 vs B端视图**:

| 维度 | 患者端（C端） | 教练端（B端） |
|------|---------------|---------------|
| 消息类型 | companion_soft_check | risk_diagnosis |
| 内容 | "感觉到你今天压力不小，要不要试试深呼吸？" | "SICE: Stress-induced Compulsive Eating" |
| 风险标记 | 不显示 | RED/ORANGE/YELLOW/GREEN |
| 建议动作 | 不显示 | ADMINISTER_BAPS_SECTION_4 |

**使用方式**:
```python
from services.state_sync import get_state_sync_manager, EventType, ViewRole

manager = get_state_sync_manager()

# 处理事件
record = manager.process_event(
    user_id=1001,
    event_type=EventType.TEXT_INPUT,
    raw_data={"text": "今天压力好大，想吃零食"}
)

# 获取不同角色视图
client_view = manager.get_view(record.event_id, ViewRole.PATIENT)
coach_view = manager.get_view(record.event_id, ViewRole.COACH)
```

### 2.3 行为母库配置

**文件位置**: `configs/behavior/behavior_rules.json`

**配置结构**:
```json
{
  "version": "1.0.0",
  "stages": {
    "S0": { "name": "前意向期", "name_display": "探索期", ... },
    "S1": { "name": "意向期", "name_display": "思考期", ... }
  },
  "triggers": [
    {
      "id": "T_EMO_EAT",
      "condition": "snippet.sentiment == 'negative' and any(kw in snippet.text for kw in ['零食', '停不下来'])",
      "risk_level": "L2",
      "action_ref": "PKG_STRESS_RELIEF"
    }
  ],
  "action_packages": {
    "PKG_STRESS_RELIEF": {
      "render_type": "INTERACTIVE_CARD",
      "payload": { "title": "感觉到你有些压力", ... }
    }
  }
}
```

### 2.4 Admin API

**文件位置**: `api/v14/admin_routes.py`

**端点列表**:

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v2/admin/behavior/rules` | GET | 获取当前母库 |
| `/api/v2/admin/behavior/rules` | PUT | 更新母库 |
| `/api/v2/admin/behavior/rules/validate` | POST | 验证条件表达式 |
| `/api/v2/admin/behavior/rules/reload` | POST | 热重载配置 |
| `/api/v2/admin/behavior/actions` | GET | 获取动作包列表 |
| `/api/v2/admin/behavior/stages` | GET | 获取阶段定义 |
| `/api/v2/admin/behavior/triggers` | GET | 获取触发规则 |
| `/api/v2/admin/behavior/sync/process` | POST | 处理同步事件 |
| `/api/v2/admin/behavior/sync/view/{id}` | GET | 获取事件视图 |
| `/api/v2/admin/behavior/stats` | GET | 获取系统统计 |

### 2.5 ActionRenderer 前端组件

**文件位置**: `frontend/components/ActionRenderer.js`

**支持的渲染类型**:

| render_type | 组件 | 说明 |
|-------------|------|------|
| INTERACTIVE_CARD | BehaviorCard | 交互卡片 |
| QUICK_REPLY | QuickButtons | 快捷回复 |
| COMPANION_MESSAGE | CompanionMessage | 陪伴消息 |
| NOTIFICATION | NotificationCard | 通知卡片 |
| TASK_CARD | TaskCard | 任务卡片 |
| SURVEY_MINI | StandardSurvey | 迷你问卷 |
| PROGRESS_TRACKER | ProgressTracker | 进度追踪 |

---

## 三、完整模块清单

### 3.1 核心模块

| 目录 | 说明 |
|------|------|
| `core/v14/` | v14功能（开关、路由、节律、Agent） |
| `quality/` | 质量审计模块 |
| `disclosure/` | 披露控制模块（敏感词、签名、权限） |
| `services/logic_engine/` | **[v16-NEW]** 行为逻辑引擎 |
| `services/state_sync/` | **[v16-NEW]** 状态同步服务 |

### 3.2 API路由

| 文件 | 前缀 | 说明 |
|------|------|------|
| `api/v14/routes.py` | `/api/v2/` | v14主路由 |
| `api/v14/quality_routes.py` | `/api/v2/quality/` | 质量审计 |
| `api/v14/disclosure_routes.py` | `/api/v2/disclosure/` | 披露控制 |
| `api/v14/admin_routes.py` | `/api/v2/admin/behavior/` | **[v16-NEW]** Admin配置 |

### 3.3 配置文件

| 文件 | 说明 |
|------|------|
| `configs/behavior/behavior_rules.json` | **[v16-NEW]** 母库配置 |
| `core/v14/config.py` | 功能开关配置 |

### 3.4 前端组件

| 文件 | 说明 |
|------|------|
| `frontend/components/ActionRenderer.js` | **[v16-NEW]** Action渲染器 |

---

## 四、数据库表

### user_state_sync 表

```sql
CREATE TABLE IF NOT EXISTS user_state_sync (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(36) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    
    client_view JSONB NOT NULL,   -- C端视图（脱敏）
    coach_view JSONB NOT NULL,    -- B端视图（诊断）
    expert_view JSONB,            -- 专家视图（完整）
    
    trigger_id VARCHAR(50),
    action_id VARCHAR(50),
    processed INTEGER DEFAULT 1,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_state_sync_user ON user_state_sync(user_id);
CREATE INDEX idx_state_sync_type ON user_state_sync(event_type);
```

---

## 五、部署指南

### 5.1 服务端口

| 端口 | 服务 | 说明 |
|------|------|------|
| 8000 | Agent Gateway | Agent网关 |
| 8001 | BAPS API | 评估API |
| 8002 | Decision Engine | 决策引擎(main.py) |
| 8003 | Quality Service | 质量审计 |
| 8501 | Expert Workbench | 专家工作台 |

### 5.2 启动命令

```bash
# 1. 解压
unzip behavioral-health-platform-v16.zip

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动主服务
python main.py  # 端口8002

# 4. 启动专家工作台（可选）
streamlit run workbench/expert_review.py --server.port 8501
```

### 5.3 测试API

```bash
# 获取母库配置
curl http://localhost:8002/api/v2/admin/behavior/rules

# 验证条件表达式
curl -X POST http://localhost:8002/api/v2/admin/behavior/rules/validate \
  -H "Content-Type: application/json" \
  -d '{"condition": "user.stage == \"S1\" and snippet.sentiment == \"negative\""}'

# 处理事件
curl -X POST http://localhost:8002/api/v2/admin/behavior/sync/process \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1001,
    "event_type": "text_input",
    "raw_data": {"text": "今天压力好大"}
  }'
```

---

## 六、版本对比

| 功能 | v14 | v14.1 | v16 |
|------|-----|-------|-----|
| 功能开关系统 | ✅ | ✅ | ✅ |
| Trigger事件路由 | ✅ | ✅ | ✅ |
| 节律模型 | ✅ | ✅ | ✅ |
| Agent增强 | ✅ | ✅ | ✅ |
| 质量审计 | ✅ | ✅ | ✅ |
| 敏感词库 | ❌ | ✅ | ✅ |
| 双重签名 | ❌ | ✅ | ✅ |
| 四级权限 | ❌ | ✅ | ✅ |
| 专家工作台 | ❌ | ✅ | ✅ |
| **行为母库** | ❌ | ❌ | ✅ |
| **状态同步** | ❌ | ❌ | ✅ |
| **Admin API** | ❌ | ❌ | ✅ |
| **ActionRenderer** | ❌ | ❌ | ✅ |

---

## 七、文件清单

```
v16/
├── configs/behavior/
│   └── behavior_rules.json     [NEW] 母库配置
│
├── services/
│   ├── __init__.py             [NEW]
│   ├── logic_engine/           [NEW] 逻辑引擎
│   │   ├── __init__.py
│   │   ├── behavior_engine.py
│   │   └── schema/
│   │       ├── __init__.py
│   │       └── rules_definition.py
│   │
│   └── state_sync/             [NEW] 状态同步
│       ├── __init__.py
│       └── manager.py
│
├── frontend/components/
│   └── ActionRenderer.js       [NEW] 前端组件
│
├── api/v14/
│   ├── admin_routes.py         [NEW] Admin API
│   └── routes.py               [UPDATED]
│
├── disclosure/                 [v14.1]
├── quality/                    [v14]
├── core/v14/                   [v14]
├── workbench/                  [v14.1]
│
└── CHANGELOG_v16.md            本文件
```

---

*文档版本: 1.0 | 构建时间: 2026-02-02*
*设计理念: 母库驱动，指令即界面*
