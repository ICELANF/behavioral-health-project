# 行为健康数字平台 - v14 变更日志
# CHANGELOG v14

## 版本: v14.0.0
## 发布日期: 2026-02-01
## 基础版本: v11 (commit f2fd215)

---

## 一、版本演进

```
v10 (基础平台 + BAPS评估)
 │
 └─► v11 (2026-01-31)
      │  ├── Dify深度集成
      │  ├── Ollama智能回退
      │  ├── 患者门户H5
      │  └── TriggerEngine基础版
      │
      └─► v14 (2026-02-01) [本次发布]
           ├── [v14-NEW] 功能开关系统
           ├── [v14-NEW] Trigger事件路由
           ├── [v14-NEW] 节律模型
           ├── [v14-NEW] Agent增强框架
           └── [v14-ENHANCED] 安全兜底机制
```

---

## 二、新增文件清单

### 2.1 核心模块 (core/v14/)

| 文件 | 大小 | 说明 |
|------|------|------|
| `core/v14/__init__.py` | ~2KB | v14模块入口，导出所有功能 |
| `core/v14/config.py` | ~4KB | **[v14-NEW]** 功能开关配置系统 |
| `core/v14/trigger_router.py` | ~10KB | **[v14-NEW]** Trigger事件路由 |
| `core/v14/rhythm_engine.py` | ~12KB | **[v14-NEW]** 节律引擎 |
| `core/v14/agents.py` | ~15KB | **[v14-NEW]** Agent增强框架 |

### 2.2 API路由 (api/v14/)

| 文件 | 说明 |
|------|------|
| `api/v14/__init__.py` | v14 API模块入口 |
| `api/v14/routes.py` | **[v14-NEW]** v2 API路由（/api/v2/） |

### 2.3 更新文件

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `main.py` | **[v14-ENHANCED]** | 添加v14模块加载、v2路由挂载、安全检查 |

---

## 三、功能开关详情

### 3.1 功能开关列表

| 开关名 | 默认值 | 说明 |
|--------|--------|------|
| **v11原有功能** | | |
| `ENABLE_DIFY_INTEGRATION` | `true` | Dify集成 |
| `ENABLE_OLLAMA_FALLBACK` | `true` | Ollama回退 |
| `ENABLE_TRIGGER_ENGINE` | `true` | v11 Trigger引擎 |
| **v14新增功能** | | |
| `ENABLE_TRIGGER_EVENT_ROUTING` | `false` | Trigger事件路由 |
| `ENABLE_TRIGGER_TASK_EVENTS` | `false` | 任务触发事件 |
| `ENABLE_TRIGGER_USAGE_EVENTS` | `false` | 使用行为触发 |
| `ENABLE_RHYTHM_MODEL` | `false` | 节律模型 |
| `ENABLE_V14_AGENTS` | `false` | v14 Agent总开关 |
| `ENABLE_EXPLAIN_AGENT` | `false` | 行为解释Agent |
| `ENABLE_RESISTANCE_AGENT` | `false` | 阻抗识别Agent |
| `ENABLE_SAFETY_AGENT` | `true` | 安全兜底Agent（始终启用） |

### 3.2 启用方式

```bash
# .env 文件
BH_V14_ENABLE_TRIGGER_EVENT_ROUTING=true
BH_V14_ENABLE_RHYTHM_MODEL=true
BH_V14_ENABLE_V14_AGENTS=true
```

---

## 四、新增功能详解

### 4.1 Trigger事件路由系统

**来源**: 专家workflow_AGENT规划.ini 第1372-1492行

```
行为/生理/使用事件 → Event Normalizer → Trigger Router 
→ Decision Engine → Workflow裁剪 → Agent执行/人工升级
```

**事件类型**:
- `CGM`: low_glucose(critical), high_glucose(risk), glucose_spike(warn)
- `TASK`: task_fail(info), task_fail_3d(warn), task_skip_chain(risk)
- `USAGE`: inactive_24h(info), inactive_48h(warn), inactive_7d(risk), rage_exit(critical)
- `RHYTHM`: rhythm_drift(info), rhythm_strain(warn), rhythm_collapse(critical)

**引擎动作**:
- `LOG`: 仅记录
- `RUN`: 运行决策引擎
- `FREEZE`: 冻结Workflow
- `DOWNGRADE`: 降级干预
- `ESCALATE`: 升级到人工

### 4.2 节律模型

**来源**: 专家workflow_AGENT规划.ini 第1873-1960行

**核心概念**: 行为健康失败有"相位变化"
- `STABLE` (稳定期) → 正常执行
- `DRIFT` (漂移期) → 监控记录
- `STRAIN` (压力期) → 降级干预
- `COLLAPSE_RISK` (崩溃风险期) → 冻结+升级

**伦理约束**: **节律只能降低系统强度，不能提高**

**检测方法**:
- `detect_cgm_rhythm()`: 血糖变异系数分析
- `detect_task_rhythm()`: 任务完成率趋势
- `detect_activity_rhythm()`: 不活跃时长检测
- `detect_composite_rhythm()`: 多域加权融合

### 4.3 Agent增强框架

**来源**: 专家workflow_AGENT规划.ini 第295-315行, 519-538行

**三类Agent**:

| Agent | 职责 | 专家可配置 |
|-------|------|-----------|
| **SafetyAgent** | 安全兜底，检测危急关键词 | ❌ 系统固定 |
| **ResistanceAgent** | 阻抗识别（拖延/回避/情绪/能力/环境） | ✅ 阈值 |
| **ExplainAgent** | 行为解释，阶段化话术 | ✅ 触发条件 |

**执行顺序**: SafetyAgent → ResistanceAgent → ExplainAgent

**SafetyAgent关键词**:
- 自杀、自残、不想活、结束生命...
- 检测到立即升级到人工，不可配置

---

## 五、API变更

### 5.1 新增API端点 (路由前缀: /api/v2/)

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v2/status` | GET | v14版本状态 |
| `/api/v2/health` | GET | v14健康检查 |
| `/api/v2/features` | GET | 功能开关状态 |
| `/api/v2/trigger/emit` | POST | 发射触发事件 |
| `/api/v2/trigger/process` | POST | 处理待处理事件 |
| `/api/v2/trigger/stats` | GET | 触发统计 |
| `/api/v2/rhythm/detect` | POST | 检测节律 |
| `/api/v2/rhythm/current/{user_id}` | GET | 获取当前节律 |
| `/api/v2/agent/process` | POST | Agent处理消息 |
| `/api/v2/agent/safety-check` | POST | 安全检查 |
| `/api/v2/integrated/process` | POST | 整合处理接口 |

### 5.2 增强的原有端点

| 端点 | 变更 |
|------|------|
| `/` | 增加v14版本信息和功能状态 |
| `/health` | 增加v14模块状态 |
| `/intervene` | **[v14-ENHANCED]** 增加事件路由 |
| `/chat_sync` | **[v14-ENHANCED]** 增加SafetyAgent安全检查 |

---

## 六、向后兼容性

### 6.1 保证兼容

- ✅ 所有v11 API保持不变
- ✅ 原有数据模型不修改
- ✅ v14功能默认关闭，不影响现有流程
- ✅ 可通过环境变量逐步启用v14功能

### 6.2 不修改的文件

```
✅ core/trigger_engine.py      - v11原版保留
✅ core/decision_core.py       - 不动
✅ core/dify_client.py         - 不动
✅ api/baps_api.py             - 不动
✅ api/device_data.py          - 不动
✅ agents/orchestrator.py      - 不动
```

---

## 七、升级指南

### 7.1 从v11升级到v14

```bash
# 1. 解压v14包（覆盖v11目录）
unzip behavioral-health-platform-v14.zip -d /path/to/project

# 2. 验证v14模块加载
python -c "from core.v14 import get_version_info; print(get_version_info())"

# 3. 默认状态下，v14功能全部关闭，行为与v11完全一致
uvicorn main:app --port 8002

# 4. 逐步启用v14功能
echo "BH_V14_ENABLE_TRIGGER_EVENT_ROUTING=true" >> .env
echo "BH_V14_ENABLE_RHYTHM_MODEL=true" >> .env
```

### 7.2 回滚到v11

```bash
# 方法1: 禁用所有v14功能
BH_V14_ENABLE_TRIGGER_EVENT_ROUTING=false
BH_V14_ENABLE_RHYTHM_MODEL=false
BH_V14_ENABLE_V14_AGENTS=false

# 方法2: 删除v14目录
rm -rf core/v14 api/v14
# 恢复原始main.py
```

---

## 八、测试验证

```bash
# 1. 健康检查
curl http://localhost:8002/health

# 2. v14状态
curl http://localhost:8002/api/v2/status

# 3. 功能开关
curl http://localhost:8002/api/v2/features

# 4. 安全检查测试
curl -X POST http://localhost:8002/api/v2/agent/safety-check \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1001, "message": "今天感觉不错"}'

# 5. 节律检测测试（需启用）
curl -X POST http://localhost:8002/api/v2/rhythm/detect \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1001, "domain": "cgm", "data": [5.5, 6.2, 7.8, 11.2, 8.5]}'
```

---

## 九、已知限制

1. **节律模型需要历史数据**: 首次检测可能不准确
2. **SafetyAgent关键词列表**: 目前硬编码，后续可配置化
3. **事件路由规则**: 默认14条规则，后续支持动态配置
4. **质量审计**: 依赖LLM评判，模型能力影响准确性

---

## 十、质量审计模块 [v14-NEW]

### 10.1 概述

质量审计模块用于对AI陪伴响应进行事后质量评估，与SafetyAgent（实时检测）形成互补。

### 10.2 评分维度

| 维度 | 说明 | 阈值 |
|------|------|------|
| Adherence | 对Prompt指令的服从度 | < 3 需复核 |
| Safety | 伦理与行为边界安全 | < 4 不通过 |
| Empathy | 陪伴的共情度与温度 | 参考 |
| Consistency | 与TTM阶段的一致性 | < 3 不通过 |

### 10.3 新增文件

| 文件 | 说明 |
|------|------|
| `quality/__init__.py` | 模块入口 |
| `quality/schema.py` | 数据模型 |
| `quality/judge_prompt.py` | Prompt构建器 |
| `quality/llm_judge.py` | 评判执行器 |
| `api/v14/quality_routes.py` | API路由 |
| `run_quality_service.py` | 独立执行文件 |

### 10.4 API端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v2/quality/audit` | POST | 启动审计 |
| `/api/v2/quality/audit-batch` | POST | 批量审计 |
| `/api/v2/quality/audit/result/{trace_id}` | GET | 获取结果 |
| `/api/v2/quality/audit/status` | GET | 系统状态 |
| `/api/v2/quality/audit/list` | GET | 结果列表 |
| `/api/v2/quality/audit/safety-check` | POST | 安全专项检查 |

### 10.5 独立运行

```bash
# 启动质量审计服务（端口8003）
python run_quality_service.py

# 指定模型和后端
python run_quality_service.py --model qwen2.5:14b --backend ollama

# 同时启动主服务
python run_quality_service.py --with-main
```

### 10.6 使用示例

```bash
# 同步审计
curl -X POST "http://localhost:8003/api/v2/quality/audit?sync=true" \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "trace_001",
    "ttm_stage": "S2",
    "trigger_tags": ["high_glucose"],
    "response_text": "建议您现在喝一杯水，并进行15分钟的轻度活动。"
  }'

# 异步审计
curl -X POST "http://localhost:8003/api/v2/quality/audit" \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "trace_002",
    "response_text": "..."
  }'

# 查询结果
curl "http://localhost:8003/api/v2/quality/audit/result/trace_002"
```

---

## 十一、下一版本规划 (v15)

- [ ] 专家规则配置UI
- [ ] 节律模型机器学习版本
- [ ] Agent训练与优化
- [ ] 多专家路由（L2层）
- [ ] 事件路由规则动态配置

---

*文档版本: 1.0 | 构建时间: 2026-02-01*
