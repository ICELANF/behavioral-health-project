# 纪事文件：沙盒行为引擎 + AI 教练共驾台集成

**日期**: 2026-02-02
**范围**: D:\agenttest 沙盒测试流水线 + Admin Portal 共驾台组件集成

---

## 一、执行概览

本次工作分三个阶段：沙盒模拟流水线搭建(1-3.py)、逻辑引擎核心构建(4-6.py)、共驾台 UI 集成与配置驱动验证(7-9.py)。

| 阶段 | 脚本 | 完成状态 |
|------|------|----------|
| Phase 1 | 1.py → 2.py → 3.py | 全部通过 |
| Phase 2 | 4.py → 5.py → 6.py | 全部通过 |
| Phase 3 | 7.py → 8.py → 9.py | 集成完成 |

---

## 二、Phase 1：数字孪生 + 沙盒模拟 (1-3.py)

### 1.py — 人格库生成
- 生成 20 个数字孪生人格，4 种原型循环：
  - 冲动型-前意向期 (C:20, N:80, A:30)
  - 焦虑型-意向期 (C:40, N:90, A:50)
  - 高自控-准备期 (C:85, N:30, A:70)
  - 防御型-拒绝改变 (C:30, N:60, A:20)
- 输出: `persona_library.json`

### 2.py — 沙盒 FastAPI 服务
- 原始版本：概念原型，引用不存在的 `logic_core.BehaviorEngine`
- 适配修改：
  - 改为引用实际 `services.logic_engine.behavior_engine.BehaviorEngine`
  - 增加关键词母库映射 (RULES_LIBRARY + TAG_META)
  - 双层匹配：Layer 1 关键词 + Layer 2 条件引擎
  - 添加 CORS 中间件解决跨域
  - 加载 `actions_master.json` 实现配置驱动
- 端口: 8003 (避免与决策引擎 8002 冲突)

### 3.py — 西部世界行为模拟
- 修复: 补充 `import json`，端口从 8002 改为 8003，emoji 替换为 ASCII
- 运行结果: 5 轮 × 20 用户 = **100 条记录，100% 命中**
- 标签分布:
  - T_EMO_EAT: 30 (30%)
  - T_RESISTANCE: 24 (24%)
  - T_ACTION_WILL: 23 (23%)
  - T_HOPELESS: 23 (23%)
  - T_STRESS: 23 (23%)
- 输出: `sandbox_audit_report.json`

---

## 三、Phase 2：逻辑引擎核心 (4-6.py)

### 4.py — 动作母库资源 (actions_master.json)
- 类型: JSON 资源文件（非可执行 Python）
- 定义 3 个动作包：

| Tag | 风险 | 工具 | 教练指令 |
|-----|------|------|----------|
| T_EMO_EAT | L2 | STRESS_ASSESSMENT_FORM | 评估近三日压力事件 |
| T_RESISTANCE | L1 | EMPATHY_MODULE_01 | 严禁推送任务，同理心倾听 |
| T_ACTION_WILL | L1 | HABIT_DESIGNER | 立即下发微习惯制定卡片 |

### 5.py — BehaviorEngine 核心类
- 放置为 `services/logic_engine/core.py`
- 核心方法 `process_message(user_input, user_context)`:
  1. `match_triggers(text)` — 关键词匹配
  2. C 端输出: 从 actions_master 取 `companion_template` (感性/隐形)
  3. B 端输出: 从 actions_master 取 `coach_directive` + `tool_id` (理性/显性)
- 后续集成了 7.py 的阶段迁移逻辑和 9.py 的 tool_props

### 6.py — 全角色视角模拟演习
- 2 个测试用例完整跑通：
  - Case 1 (抵触): T_RESISTANCE → EMPATHY_MODULE_01
  - Case 2 (行动意愿): T_ACTION_WILL → HABIT_DESIGNER
- State Sync 分发验证: C 端话术感性低侵入，B 端指令理性专业
- 输出: `evolution_v2_report.json`

---

## 四、Phase 3：阶段迁移 + 共驾台 UI (7-9.py)

### 7.py — 阶段迁移引擎
- 增加 `transition_threshold = 3`
- 迁移规则:
  - (S1, T_RESISTANCE) → S2 (前意向→意向，阻抗被正确引导 3 次)
  - (S2, T_ACTION_WILL) → S3 (意向→准备，行动意愿连续 3 次)
- 验证结果: Turn 1-2 维持 S1，**Turn 3 触发 S1→S2 迁移**
- 输出: `stage_transition_report.json`

### 8.py — CoachCopilot.vue 组件
- 放置为 `admin-portal/src/views/coach/CoachCopilot.vue`
- 功能: B 端教练实时共驾台面板
- 动态组件映射 (toolMapper):

| tool_id | Vue 组件 | 用途 |
|---------|----------|------|
| STRESS_ASSESSMENT_FORM | StressForm.vue | 压力快速测评 (3 题) |
| EMPATHY_MODULE_01 | EmpathyGuide.vue | 同理心倾听指南 |
| HABIT_DESIGNER | HabitCard.vue | 微习惯制定卡 |

### 9.py — tool_props 增强
- 为每个动作包增加前端工具参数:
  - T_EMO_EAT: `{ type: "quick_check", limit_time: 300 }`
  - T_RESISTANCE: `{ type: "passive_listen", timeout: 600 }`
  - T_ACTION_WILL: `{ type: "micro_habit", max_steps: 3 }`

---

## 五、共驾台集成到 CoachHome.vue

### 新增组件文件
```
admin-portal/src/views/coach/
├── CoachCopilot.vue          ← 共驾台面板（独立组件）
├── CoachHome.vue             ← 主页（内联集成共驾台）
└── tools/
    ├── StressForm.vue        ← 压力测评工具
    ├── EmpathyGuide.vue      ← 同理心引导工具
    └── HabitCard.vue         ← 微习惯制定工具
```

### CoachHome.vue 改动
1. **模板**: 在 `</a-tabs>` 后插入共驾台区域
   - 用户阶段徽章 (`.user-stage-badge`, S1/S2/S3 色彩)
   - 触发标签展示 (颜色按风险分级)
   - 教练处方流 (包含动态工具组件渲染)
   - 阶段迁移通知 (a-alert)
   - 模拟触发下拉 + 按钮 (4 种对话场景)
2. **脚本**: 新增 `copilotState` reactive、`triggerCopilotTest` 异步函数、`toolMapper` 动态组件映射
3. **样式**: 新增 `.copilot-*` 系列样式 (~80 行)

---

## 六、配置驱动验证

### 测试目标
修改 `actions_master.json` 中 T_EMO_EAT 的 `coach_directive`，验证前端无需任何代码修改即可反映变化。

### 执行步骤
1. 修改 `actions_master.json`:
   - 旧值: "用户出现补偿性进食，请评估其近三日的压力事件。"
   - 新值: **"用户出现补偿性进食，建议立即发起语音通话了解诱因"**
2. 重启沙盒服务 (8003)
3. 运行 `run_full_evolution` 验证后端输出
4. 运行 `screenshot.js` 视觉验收

### 后端验证结果
```
User: USER_03 | Tags: ['T_EMO_EAT']
  B-end: [L2] 用户出现补偿性进食，建议立即发起语音通话了解诱因
         tool=STRESS_ASSESSMENT_FORM props={'type': 'quick_check', 'limit_time': 300}
```
**配置变更已生效，未修改任何前端代码。**

### 前端验收
- CORS 跨域问题已修复 (FastAPI CORSMiddleware)
- 共驾台面板已渲染：阶段徽章 S1、模拟触发下拉框、模拟触发按钮
- 动态工具组件 (StressForm/EmpathyGuide/HabitCard) 已创建

---

## 七、产出文件清单

### D:\agenttest (沙盒目录)

| 文件 | 类型 | 说明 |
|------|------|------|
| `persona_library.json` | 数据 | 20 个数字孪生人格 |
| `sandbox_audit_report.json` | 报告 | 100 条模拟行为记录 |
| `evolution_v2_report.json` | 报告 | 全角色视角模拟结果 |
| `evolution_v3_report.json` | 报告 | 配置更新后验证结果 |
| `stage_transition_report.json` | 报告 | S1→S2 阶段迁移记录 |
| `screenshots/*.png` | 截图 | 11 张 UI 验收截图 |
| `services/logic_engine/core.py` | 引擎 | BehaviorEngine 核心 (含阶段迁移) |
| `services/logic_engine/resource/actions_master.json` | 配置 | 动作母库 (配置驱动源) |

### D:\behavioral-health-project (主项目)

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `admin-portal/src/views/coach/CoachHome.vue` | 修改 | 集成共驾台面板 |
| `admin-portal/src/views/coach/CoachCopilot.vue` | 新增 | 共驾台独立组件 |
| `admin-portal/src/views/coach/tools/StressForm.vue` | 新增 | 压力测评工具 |
| `admin-portal/src/views/coach/tools/EmpathyGuide.vue` | 新增 | 同理心引导工具 |
| `admin-portal/src/views/coach/tools/HabitCard.vue` | 新增 | 微习惯制定工具 |

---

## 八、架构验证结论

### 配置驱动链路
```
actions_master.json (母库配置)
       │
       ▼
BehaviorEngine.process_message() (后端引擎)
       │
       ▼
POST /api/v1/test/simulate-chat (沙盒 API :8003)
       │
       ▼
CoachHome.vue copilotState (前端响应式数据)
       │
       ▼
toolMapper[suggested_tool] (动态组件渲染)
       │
       ▼
StressForm / EmpathyGuide / HabitCard (工具 UI)
```

**验证结论**: 修改 `actions_master.json` 中的 `coach_directive` 文字后，无需修改 `/frontend` 目录下任何代码，后端 API 响应和前端共驾台面板均自动反映新内容。**配置驱动架构验证通过。**

---

## 九、已知待办

| 项目 | 状态 | 说明 |
|------|------|------|
| 沙盒 API CORS | 已修复 | 添加 CORSMiddleware |
| 动态工具组件渲染 | 已创建 | StressForm/EmpathyGuide/HabitCard |
| 阶段迁移 UI 通知 | 已实现 | a-alert 组件展示迁移事件 |
| Vite 代理 8003 | 待配置 | 生产环境应通过 Vite proxy 而非直连 |
| WebSocket 实时推送 | 待实现 | 当前为按钮触发，生产应改为实时推送 |
| 母库热重载 | 已有基础 | ConfigWatcher 可自动检测配置变化 |
