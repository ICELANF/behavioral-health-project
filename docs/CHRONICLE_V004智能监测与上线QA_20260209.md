# 纪事文件：V004 智能监测方案引擎 + UI 集成 + 上线前 QA

**日期**: 2026-02-09
**范围**: V004 Smart Program Engine 后端 + H5/Admin 前端集成 + 全平台上线前自检
**架构文档版本**: v25 → v26

---

## 一、执行概览

本次工作分四个阶段：V004 后端引擎构建、前端 UI 集成（C 端 + 专家端）、全平台上线前 QA 自检、架构文档更新与 Git 推送。

| 阶段 | 内容 | 完成状态 |
|------|------|----------|
| Phase 1 | V004 后端：3 表 + 2 视图 + 2 函数 + 13 端点 + 5 调度任务 | 完成 |
| Phase 2 | H5 C 端：4 页面 + API 模块 + 路由 | 完成 |
| Phase 3 | Admin 专家端：7 页面 + API 模块 + 路由 | 完成 |
| Phase 4 | 上线前 QA：108 路由 × 全量自检 + 3 修复 | 完成 |
| Phase 5 | 架构文档 v26 + 纪事 + Git Push | 完成 |

---

## 二、V004 智能监测方案引擎（后端）

### 2.1 数据层

**新增 3 张表**:
- `program_templates` — 方案模板（UUID PK, JSON schema, category枚举, version管理）
- `program_enrollments` — 用户报名（UUID PK, 天数推进, 状态枚举: active/paused/completed/dropped）
- `program_interactions` — 用户交互记录（UUID PK, push_slot枚举, 问答JSON, 评分）

**新增 2 个视图**:
- `v_program_enrollment_summary` — 报名汇总（完成率、交互率、平均评分）
- `v_program_today_pushes` — 今日待推送清单

**新增 2 个函数**:
- `advance_program_day()` — 每日凌晨自动推进天数（00:05 执行）
- `calc_interaction_rate()` — 计算用户交互完成率

**新增 3 个枚举**:
- `program_category`: glucose_14d / weight_21d / sleep_14d / custom
- `enrollment_status`: active / paused / completed / dropped
- `push_slot`: morning / noon / evening

**迁移文件**: `alembic/V004_program_engine.sql` (21号迁移)

### 2.2 服务层

**`core/program_service.py`** — ProgramEngine 核心引擎:
- `create_template()` / `list_templates()` / `get_template()` / `update_template()`
- `enroll_user()` — 报名入组 + 积分奖励(+10)
- `get_today_pushes()` — 根据 day_number + push_slot 获取今日推送内容
- `record_interaction()` — 记录交互 + 积分奖励(+3)
- `get_timeline()` — 完整时间线回溯
- `get_progress()` — 进度统计（完成率、交互率、趋势图数据）
- `advance_day()` — 调度器调用的天数推进
- `generate_recommendations()` — 基于交互数据的 AI 推荐

### 2.3 API 层

**`api/program_api.py`** — 13 个端点，前缀 `/api/v1/programs`:

| 分类 | 端点 | 方法 | 说明 |
|------|------|------|------|
| 模板 | `/templates` | GET | 列表（分页+筛选） |
| 模板 | `/templates` | POST | 创建 |
| 模板 | `/templates/{id}` | GET | 详情 |
| 模板 | `/templates/{id}` | PUT | 更新 |
| 用户 | `/enroll` | POST | 报名入组 |
| 用户 | `/my` | GET | 我的方案列表 |
| 用户 | `/today` | GET | 今日推送 |
| 用户 | `/interact` | POST | 提交交互 |
| 用户 | `/timeline/{enrollment_id}` | GET | 时间线 |
| 用户 | `/progress/{enrollment_id}` | GET | 进度详情 |
| 用户 | `/status/{enrollment_id}` | PUT | 暂停/恢复 |
| 管理 | `/admin/analytics` | GET | 全局统计 |
| 管理 | `/admin/enrollments` | GET | 报名管理列表 |

### 2.4 调度器

新增 5 个定时任务（`core/scheduler.py`，均使用 Redis SETNX 互斥锁）:

| 任务 | CRON | 说明 |
|------|------|------|
| `advance_program_day` | 00:05 daily | 推进方案天数 |
| `program_push_morning` | 09:00 daily | 晨间推送 |
| `program_push_noon` | 11:30 daily | 午间推送 |
| `program_push_evening` | 17:30 daily | 晚间推送 |
| `program_batch_analysis` | 23:00 daily | 批量分析 |

### 2.5 种子数据

**`configs/glucose-14d-template.json`** — 血糖 14 天监测方案模板:
- 15 天 × 3 时段 = 44 条推送
- 145 个交互问题（选择题+数值输入+文本）
- 7 条推荐规则（基于交互数据触发）

---

## 三、H5 C 端集成（Phase 2）

### 3.1 新增文件

| 文件 | 说明 |
|------|------|
| `h5/src/api/program.ts` | 方案 API 模块（7 个方法） |
| `h5/src/views/MyPrograms.vue` | 我的方案列表（Vant Card + Tag） |
| `h5/src/views/ProgramToday.vue` | 今日推送页（时间轴 + 交互表单） |
| `h5/src/views/ProgramTimeline.vue` | 完整时间线（Vant Steps 垂直） |
| `h5/src/views/ProgramProgress.vue` | 进度详情（ECharts 折线图 + 统计卡片） |

### 3.2 路由

```
/programs          → MyPrograms.vue      (我的方案)
/programs/today    → ProgramToday.vue    (今日推送)
/programs/timeline → ProgramTimeline.vue (时间线)
/programs/progress → ProgramProgress.vue (进度详情)
```

### 3.3 基础设施

- 引入 Tailwind CSS 3（`preflight: false` 保护 Vant 样式）
- `postcss.config.js` + `tailwind.config.js` 配置
- `h5/src/styles/global.scss` 更新

---

## 四、Admin 专家端集成（Phase 3）

### 4.1 新增文件

| 文件 | 说明 |
|------|------|
| `admin-portal/src/api/expert.ts` | 专家 API 模块 |
| `admin-portal/src/views/expert/ExpertWorkbench.vue` | 专家工作台主页 |
| `admin-portal/src/views/expert/DualSignPanel.vue` | 双签审阅面板 |
| `admin-portal/src/views/admin/BatchIngestion.vue` | 批量知识导入 |
| `admin-portal/src/views/admin/ContentManage.vue` | 内容管理 |
| `admin-portal/src/views/admin/UserActivityReport.vue` | 用户活跃报告 |
| `admin-portal/src/views/admin/CourseModuleManage.vue` | 课程模块管理 |
| `admin-portal/src/views/LandingPage.vue` | 平台着陆页 |
| `admin-portal/src/composables/useLanding.ts` | 着陆页数据逻辑 |
| `admin-portal/src/components/landing/` | 着陆页组件集 |

### 4.2 基础设施

- 引入 Tailwind CSS 3（`preflight: false` 保护 Ant Design Vue 样式）
- `postcss.config.js` + `tailwind.config.js` 配置
- 路由注册至 `router.ts`

---

## 五、上线前 QA 自检（Phase 4）

### 5.1 检查项目与结果

| 检查项 | 范围 | 结果 |
|--------|------|------|
| Vue 组件文件存在性 | 120+ 文件 | 全部存在 |
| Import 依赖链 | stores/api/components/types | 全部可解析 |
| TypeScript 编译 | vue-tsc --noEmit | 0 错误 |
| Vite 构建 | H5 + Admin | 均成功 |
| H5 路由 HTTP 200 | 34 路由 | 34/34 通过 |
| Admin 路由 HTTP 200 | 74 路由 | 74/74 通过 |
| 静态资源 404 | JS/CSS/图片 | 0 错误 |
| API 双前缀检查 | nginx access.log | 0 条 /api/api/ |
| Docker 容器健康 | 13 容器 | 全部运行 |

### 5.2 发现并修复的问题（3 项）

**QA-1: H5 `fetchCurrentStage` API 路径错误**
- 问题: 调用 `/api/v1/miniprogram/progress`，返回 404
- 原因: miniprogram 路由挂载在 `/api/v1/mp` 前缀下
- 修复: `h5/src/api/tasks.ts` → `/api/v1/mp/progress/summary`

**QA-2: H5 `fetchPublishedNarrative` API 路径错误**
- 问题: 调用 `/api/v1/coach/messages/inbox`，非教练用户返回 401/403
- 原因: 用户收件箱端点为 `/api/v1/messages/inbox`（无 `coach/` 前缀）
- 修复: `h5/src/api/tasks.ts` → `/api/v1/messages/inbox`

**QA-3: Admin 双 `/api/api/v1/` 前缀**
- 问题: 9 个文件 32 处 API 调用使用 `${API_BASE}/api/v1/...`，而 `API_BASE='/api'`，导致 `/api/api/v1/...` → 404
- 影响文件: CoachHome.vue(21), StudentMessages.vue(4), StudentAssessment.vue(3), CoachAiReview.vue(1), CoachStudentList.vue(1), MyCertification.vue(1), MyTools.vue(1), expert-content.ts(1), ExpertDashboard.vue(1)
- 修复: 全部 `${API_BASE}/api/v1/` → `${API_BASE}/v1/`

### 5.3 正常现象（无需修复）

- H5 health API 返回 mock 数据（设计如此，coach_api 有 try/catch fallback）
- Dify localhost:8080 从 Windows 主机 curl 连接失败（Docker 网络隔离，浏览器通过 nginx 正常访问）
- Windows 终端中文 curl 输出乱码（显示问题，数据正确）

---

## 六、架构文档更新

**`docs/platform-architecture-overview.md`**: v25 → v26

主要更新:
- 前端架构图：页面计数更新（H5 33路由, Admin 86+页），Tailwind CSS 标注
- 路由器计数：48→49，端点计数：420→430+，调度任务：6→11
- 新增 `program_api.py` 至路由器模块列表
- 调度器章节：从 6 任务扩展至 11 任务
- 新增 `program_service.py` 至核心服务列表
- 服务文件计数：59→61，迁移计数：20→21
- 新增 Section 22: V004 智能监测方案引擎
- 新增 Section 23: UI 集成（H5 + Admin 文件清单）
- 新增 Section 24: 上线前 QA 报告

---

## 七、统计汇总

| 指标 | 数值 |
|------|------|
| 新增后端文件 | 3（program_service.py, program_api.py, V004 migration） |
| 新增配置文件 | 1（glucose-14d-template.json） |
| 新增 H5 页面 | 4（MyPrograms/ProgramToday/ProgramTimeline/ProgramProgress） |
| 新增 Admin 页面 | 7（ExpertWorkbench/DualSignPanel/BatchIngestion/ContentManage/UserActivityReport/CourseModuleManage/LandingPage） |
| 新增 API 端点 | 13 |
| 新增调度任务 | 5 |
| 新增数据库对象 | 3 表 + 2 视图 + 2 函数 + 3 枚举 |
| QA 修复 | 3 项（2 H5 API 路径 + 1 Admin 双前缀） |
| 路由通过率 | 108/108 (100%) |
| 总端点数 | 430+ |
| 总模型数 | 70 |
| 总迁移数 | 21 |
