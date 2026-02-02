# 行为健康管理系统 - UI 开发总揽

**版本**: v16.0.0
**生成时间**: 2026-02-02
**用途**: 用户交互界面开发准备参考

---

## 一、系统架构总览

```
                       ┌─────────────────────────────────────────┐
                       │              用户交互层                  │
          ┌────────────┼────────────┬────────────┐               │
          │ Admin Portal│   H5 移动端 │ Patient App│               │
          │  :5174      │   :5173    │   :5175    │               │
          │ Ant Design  │   Vant     │   Vant     │               │
          └──────┬──────┴─────┬──────┴─────┬──────┘               │
                 │            │            │                       │
                 └────────────┼────────────┘                       │
                       /api/* │ proxy                              │
                              ▼                                    │
          ┌──────────────────────────────────────┐                │
          │          API 网关层 (Gateway :8000)    │                │
          │  认证 │ 小程序 │ 设备 │ 管理 │ 聊天    │                │
          └────┬─────────┬────────────┬──────────┘                │
               │         │            │                           │
        ┌──────┴──┐ ┌────┴────┐ ┌────┴────────┐                  │
        │BAPS     │ │决策引擎  │ │  AI 编排层   │                  │
        │:8001    │ │:8002    │ │Dify + Ollama │                  │
        │评估系统  │ │干预决策  │ │LLM 推理      │                  │
        └─────────┘ └─────────┘ └──────────────┘                  │
                              │                                    │
                       ┌──────┴──────┐                             │
                       │  SQLite DB   │                            │
                       │  16 张表      │                            │
                       └─────────────┘                             │
                       └─────────────────────────────────────────┘
```

---

## 二、三端前端应用

### 2.1 Admin Portal (管理后台) - 端口 5174

| 技术栈 | 版本 |
|--------|------|
| Vue | 3.x + TypeScript |
| 组件库 | Ant Design Vue 4.2.6 |
| 图标 | @ant-design/icons-vue 7.0.1 |
| 状态管理 | Pinia 3.0.4 |
| HTTP | Axios 1.13.2 |
| 日期 | dayjs 1.11.19 |

**路由与页面**:

| 路由 | 页面 | 角色 | 数据状态 |
|------|------|------|----------|
| `/login` | 登录页 | 全角色 | **真实API** |
| `/dashboard` | 工作平台 | 管理员 | Mock |
| `/client` | 患者健康仪表盘 | 患者(C端) | **Mock** (mockPatientDashboard) |
| `/client/chat` | AI 健康教练对话 | 患者 | 真实API (Dify/Ollama) |
| `/coach-portal` | **教练工作台 (CoachHome)** | 教练 | **部分Mock** |
| `/expert-portal` | 督导工作台 | 专家 | Mock |
| `/course/*` | 课程管理 (列表/创建/编辑/章节) | 管理员 | Mock |
| `/question/*` | 题库管理 | 管理员 | Mock |
| `/exam/*` | 考试管理 (含监考审核) | 管理员 | Mock |
| `/live/*` | 直播管理 | 管理员 | Mock |
| `/coach/*` | 教练管理 (列表/详情/晋升审核) | 管理员 | Mock |
| `/student` | 学员管理 | 管理员 | Mock |
| `/prompts/*` | 提示词模板管理 | 管理员 | Mock |
| `/interventions` | 干预方案包管理 | 管理员 | Mock |
| `/settings` | 系统设置 | 管理员 | Mock |

**CoachHome.vue 已实现的 Tab 页** (学生详情抽屉):

| Tab | Key | 内容 | 数据状态 |
|-----|-----|------|----------|
| 健康数据 | health | 血糖/血压/体重趋势图 | Mock |
| 跟进记录 | followup | 教练跟进日志 | Mock |
| 干预方案 | intervention | 当前干预计划 | Mock |
| **诊断评估** | **diagnosis** | SPI评分 + 六类原因分析 + 心理层次 + 证据 | **Mock** (新增) |
| **行为处方** | **prescription** | 阶段处方 + 目标行为 + 策略 + AI建议 | **Mock** (新增) |

---

### 2.2 H5 移动端 - 端口 5173

| 技术栈 | 版本 |
|--------|------|
| Vue | 3.x + TypeScript |
| 组件库 | Vant 4.8.0 |
| 图表 | ECharts 5.4.0 |
| 状态管理 | Pinia 2.1.0 |
| HTTP | Axios 1.6.0 |

**路由与页面**:

| 路由 | 页面 | 数据状态 |
|------|------|----------|
| `/` | 首页 (任务卡片 + 健康概览) | 部分真实API |
| `/chat` | AI 对话页 | 真实API |
| `/tasks` | 任务列表 | Mock |
| `/dashboard` | 数据仪表盘 | Mock |
| `/profile` | 个人中心 | Mock |

---

### 2.3 Patient App (患者端) - 端口 5175

| 技术栈 | 版本 |
|--------|------|
| Vue | 3.x + TypeScript |
| 组件库 | Vant 4.9.0 |
| 状态管理 | Pinia 3.0.0 |
| HTTP | Axios 1.7.0 |

**路由与页面**:

| 路由 | 页面 | 认证 | 数据状态 |
|------|------|------|----------|
| `/login` | 登录页 | 否 | **真实API** |
| `/register` | 注册页 | 否 | **真实API** |
| `/` | 首页 (健康摘要) | 是 | 部分真实 |
| `/data-input` | 数据录入 (血糖/血压/体重) | 是 | **真实API** |
| `/history` | 评估历史 | 是 | 真实API |
| `/analysis` | 数据分析 | 是 | Mock |
| `/chat` | AI 健康助手 | 是 | 真实API |
| `/health-data` | 健康数据详情 | 是 | 部分真实 |
| `/result/:id` | 评估结果详情 | 是 | 真实API |
| `/settings` | 个人设置 | 是 | Mock |

---

## 三、后端 API 端点清单

### 3.1 Gateway (端口 8000) - 主网关

#### 认证模块 `/api/v1/auth`
| 方法 | 端点 | 说明 | 状态 |
|------|------|------|------|
| POST | /auth/register | 用户注册 | 可用 |
| POST | /auth/login | 用户登录 (返回 JWT) | 可用 |
| POST | /auth/refresh | 刷新令牌 | 可用 |
| POST | /auth/logout | 退出登录 | 可用 |
| GET | /auth/me | 获取当前用户信息 | 可用 |

#### 小程序模块 `/api/v1/mp`
| 方法 | 端点 | 说明 | 状态 |
|------|------|------|------|
| GET | /mp/task/today | 获取今日任务 | 可用 |
| POST | /mp/task/feedback | 提交任务反馈 | 可用 (已修复) |
| GET | /mp/user/state | 获取用户状态 | 可用 |
| GET | /mp/progress/summary | 进度汇总 | 可用 |
| GET | /mp/risk/status | 风险状态 | 可用 |
| GET | /mp/llm/health | LLM 健康检查 | 可用 |
| GET | /mp/chat/sessions | 聊天会话列表 | 可用 |

#### 设备数据模块 `/api/v1/mp/device`
| 方法 | 端点 | 说明 | 状态 |
|------|------|------|------|
| POST | /device/blood-pressure | 上报血压 | 可用 |
| POST | /device/glucose/manual | 手动录入血糖 | 可用 |
| GET | /device/glucose/current | 当前血糖 | 可用 |
| POST | /device/weight | 上报体重 | 可用 |
| GET | /device/dashboard/today | 今日健康概览 | 可用 |

#### 管理模块 `/api/v1/admin`
| 方法 | 端点 | 说明 | 状态 |
|------|------|------|------|
| GET | /admin/behavior/stats | 行为统计 | 可用 |
| GET | /admin/behavior/stages | 行为阶段 | 可用 |
| GET | /admin/behavior/rules | 行为规则库 | 可用 |
| GET | /admin/behavior/actions | 动作包 | 可用 |
| GET | /admin/behavior/triggers | 触发器列表 | 可用 |

#### 其他端点
| 方法 | 端点 | 说明 | 状态 |
|------|------|------|------|
| GET | /api/v1/dashboard/{user_id} | 用户仪表盘 | 可用 |
| GET | /api/v1/experts | 专家列表 | 可用 |
| GET | /orchestrator/status | 编排器状态 | 可用 |
| GET | /health | 健康检查 | 可用 |

---

### 3.2 BAPS 评估系统 (端口 8001)

| 方法 | 端点 | 说明 | 状态 |
|------|------|------|------|
| GET | /health | 健康检查 | 可用 |
| POST | /test/full-assessment | 完整评估 (四合一) | 可用 |
| GET | /questionnaires | 问卷列表 | 可用 |
| GET | /test/sample-answers/big_five | 大五人格样本答案 | 可用 |
| GET | /openapi-tools.json | OpenAPI 工具描述 | 可用 |

**支持的评估类型**:
- **Big Five** - 大五人格测评
- **BPT-6** - 行为变化阶段测评
- **CAPACITY** - 行为能力测评
- **SPI** - 阶段进展指数

---

### 3.3 决策引擎 (端口 8002)

| 方法 | 端点 | 说明 | 状态 |
|------|------|------|------|
| GET | /health | 健康检查 | 可用 |
| GET | /latest_status | 最新决策状态 | 可用 |
| POST | /intervene | 触发干预 | 可用 |

---

## 四、数据模型 (SQLite, 16 张表)

### 核心表

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| **users** | 用户表 | id, username, role(PATIENT/COACH/ADMIN/SYSTEM), profile(JSON) |
| **assessments** | 评估记录 | user_id, risk_level(R0-R4), risk_score, primary_agent |
| **trigger_records** | 触发器记录 | assessment_id, tag_id, category, severity, confidence |
| **interventions** | 干预记录 | assessment_id, agent_type, status, actions(JSON) |

### 设备数据表

| 表名 | 说明 |
|------|------|
| user_devices | 设备绑定 |
| glucose_readings | 血糖读数 |
| heart_rate_readings | 心率数据 |
| hrv_readings | 心率变异性 |
| sleep_records | 睡眠记录 |
| activity_records | 活动记录 |
| workout_records | 运动记录 |
| vital_signs | 生命体征 (血压等) |

### 会话管理表

| 表名 | 说明 |
|------|------|
| user_sessions | 用户会话 |
| chat_messages | 聊天消息 (含 AI 对话) |

---

## 五、认证体系

```
用户登录 ──POST──▶ /api/v1/auth/login
                       │
                       ▼
              验证用户名/密码 (bcrypt)
                       │
                       ▼
              生成 JWT Token
              ┌─────────────────┐
              │ access_token    │  ← 短期有效
              │ refresh_token   │  ← 长期有效
              │ user: {         │
              │   id, role,     │
              │   username      │
              │ }               │
              └─────────────────┘
                       │
                       ▼
              前端存储 Token
              (localStorage)
                       │
                       ▼
              后续请求携带 Header:
              Authorization: Bearer {access_token}
```

**种子账户**:

| 用户名 | 密码 | 角色 | 说明 |
|--------|------|------|------|
| admin | admin123456 | 管理员 | 全权限 |
| coach_carol | coach123 | 教练 | 教练工作台 |
| patient_alice | password123 | 患者 | 测试患者 |
| patient_bob | password123 | 患者 | 测试患者 |

---

## 六、AI 能力层

| 组件 | 用途 | 状态 |
|------|------|------|
| **Ollama** (本地) | 对话推理 (qwen2.5:7b/14b, deepseek-r1:7b) | 可用 |
| **nomic-embed-text** | 文本向量嵌入 | 可用 |
| **Dify** (Docker) | 工作流编排 + Agent 对话 | 需配置 API Key |

**Ollama 模型清单**:

| 模型 | 参数量 | 量化 | 大小 |
|------|--------|------|------|
| qwen2.5:7b | 7.6B | Q4_K_M | 4.7 GB |
| qwen2.5:14b | 14.8B | Q4_K_M | 9.0 GB |
| deepseek-r1:7b | 7.6B | Q4_K_M | 4.7 GB |
| nomic-embed-text | 137M | F16 | 274 MB |

---

## 七、Mock→真实 API 迁移清单

以下列出当前使用 Mock 数据、需要在 UI 开发中对接真实 API 的模块:

### 优先级 P0 (核心交互流程)

| 前端页面 | 当前状态 | 需对接的 API | 说明 |
|----------|----------|-------------|------|
| Admin Portal baseURL | 指向 :8002 | 应统一指向 :8000 | `request.ts` 中 baseURL 需修改 |
| CoachHome 学生列表 | Mock 数据 | GET /api/v1/admin/patients | 需新建或复用 |
| CoachHome 健康数据 Tab | Mock 图表 | GET /api/v1/dashboard/{user_id} | 已有端点 |
| CoachHome 诊断评估 Tab | Mock diagnosisData | POST BAPS :8001/baps/assess/* | 需对接 BAPS |
| CoachHome 行为处方 Tab | Mock prescriptionData | 决策引擎 :8002/intervene | 需对接 |
| 前端登录凭据 | mock fallback | 统一使用种子账户 | 前端 mock 用 coach/123456，后端用 coach_carol/coach123 |

### 优先级 P1 (数据展示)

| 前端页面 | 当前状态 | 需对接的 API |
|----------|----------|-------------|
| H5 首页任务卡 | 部分 Mock | GET /api/v1/mp/task/today |
| Patient App 数据分析 | Mock | GET /api/v1/mp/device/dashboard/today |
| Patient App 设置页 | Mock | GET /api/v1/auth/me + PUT 接口 |
| Admin 课程/考试/题库 | 全 Mock | 需新建 CRUD API |
| Admin 干预方案管理 | Mock | 需新建 API |

### 优先级 P2 (增强功能)

| 功能 | 说明 |
|------|------|
| Dify AI 编排 | 配置 DIFY_API_KEY 后启用 |
| Redis 缓存 | 可选部署，提升性能 |
| WebSocket 实时推送 | 当前为 HTTP 轮询 |
| 设备蓝牙对接 | 当前仅手动录入 |

---

## 八、Vite 代理配置

| 应用 | 端口 | 代理目标 | 配置文件 |
|------|------|----------|----------|
| H5 | 5173 | http://localhost:8000 | h5/vite.config.ts |
| Admin Portal | 5174 | (需配置) | admin-portal/vite.config.ts |
| Patient App | 5175 | http://127.0.0.1:8000 | h5-patient-app/vite.config.ts |

---

## 九、关键文件索引

### 后端
| 文件 | 说明 |
|------|------|
| `api/main.py` | Gateway 主入口，路由注册 |
| `api/auth_api.py` | 认证 API (登录/注册/刷新) |
| `api/miniprogram.py` | 小程序 API (任务/反馈/状态) |
| `api/device_data.py` | 设备数据 API |
| `api/dify_service.py` | Dify 对话服务 |
| `api/llm_service.py` | Ollama LLM 服务 |
| `api/baps_api.py` | BAPS 评估系统入口 |
| `core/models.py` | 数据库模型定义 |
| `core/database.py` | 数据库连接管理 |
| `core/health.py` | 健康检查端点 |
| `core/decision_core.py` | 决策引擎核心 |
| `core/trigger_engine.py` | 触发器引擎 |
| `core/assessment_engine.py` | 评估引擎 (四层诊断) |
| `configs/assessment/*.json` | 评估配置 (诊断提示/处方策略/SPI映射) |

### 前端
| 文件 | 说明 |
|------|------|
| `admin-portal/src/router/index.ts` | Admin 路由定义 |
| `admin-portal/src/api/client.ts` | Admin API 客户端 + Mock 数据 |
| `admin-portal/src/views/coach/CoachHome.vue` | **教练工作台** (含诊断/处方 Tab) |
| `admin-portal/src/views/client/HomeView.vue` | 患者仪表盘 |
| `admin-portal/src/views/expert/ExpertHome.vue` | 督导工作台 |
| `h5/src/views/Home.vue` | H5 首页 |
| `h5-patient-app/src/router/index.ts` | Patient App 路由 |
| `h5-patient-app/src/api/request.ts` | Patient App HTTP 客户端 |

### 运维
| 文件 | 说明 |
|------|------|
| `start_all.bat` | 一键启动全部服务 |
| `stop_all.bat` | 一键停止全部服务 |
| `status.bat` | 服务状态检查 (8 端口) |
| `docker-compose.app.yaml` | Docker 编排 |

---

## 十、UI 开发建议

### 下一步开发优先级

1. **统一 API baseURL** - Admin Portal 的 `request.ts` 从 `:8002` 改为 `:8000`
2. **统一登录凭据** - 前端登录与后端种子数据对齐
3. **CoachHome 对接真实数据** - 将 Mock 数据替换为 BAPS + 决策引擎 API 调用
4. **Patient App 完善** - 数据分析页、设置页对接 API
5. **Admin 管理页面** - 课程/考试/题库等 CRUD 对接后端 (需新建 API)
6. **实时通信** - 考虑 WebSocket 替代轮询

### 组件库使用规范

| 端 | 组件库 | 图标 |
|----|--------|------|
| Admin Portal (PC) | Ant Design Vue 4.x | @ant-design/icons-vue |
| H5 移动端 | Vant 4.x | Vant 内置图标 |
| Patient App | Vant 4.x | Vant 内置图标 |

### 设计原则
- PC 端 (Admin) 使用 Ant Design Vue 的 Layout / Table / Form / Modal 组件
- 移动端 (H5/Patient) 使用 Vant 的 Tab / Card / Cell / Dialog 组件
- 图表统一使用 ECharts 5.x
- 状态管理统一使用 Pinia
- HTTP 请求统一使用 Axios + 拦截器 (Token 自动注入)
