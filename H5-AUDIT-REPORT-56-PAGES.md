# H5 移动端 56 页全面逐页审核报告

> 审核日期: 2026-02-25
> 审核版本: V5.3.0
> 审核范围: 55 个 Vue 页面 + 共享基础设施 (GrowerTodayHome.vue 为孤立文件，未被路由引用)
> 审核维度: D1 代码质量 | D2 UI/UX | D3 安全 | D4 铁律合规

---

## 汇总统计

| 严重度 | 数量 | 说明 |
|--------|------|------|
| **CRITICAL** | 14 | 必须立即修复，影响安全或核心功能 |
| **HIGH** | 30 | 高优先级，影响铁律合规/数据安全/功能正确性 |
| **MEDIUM** | 35 | 中优先级，代码质量/UX/防御性编程 |
| **LOW** | 45 | 低优先级，优化建议/技术债 |

**总计: 124 个问题，覆盖 55 个页面 + 8 个 API/Store/共享模块**

---

## 系统性问题 (跨页面)

### S1. 双 Token 键名不一致 (CRITICAL)
- **影响范围**: 所有 v3 页面 (v3/Coach.vue, v3/Assessment.vue, v3/AssessmentBatch.vue, v3/Register.vue, v3/Knowledge.vue)
- **问题**: `api/index.ts` + `request.ts` 使用 `h5_token` (via `storage.getToken()`)；`api/v3/http.js` 使用 `access_token` (直接 `localStorage.getItem`)
- **后果**: 主流程登录写入 `h5_token`，v3 页面读取 `access_token` 找不到 token → 所有 v3 API 调用无认证
- **修复**: 统一 `v3/http.js:18` 改为 `localStorage.getItem('h5_token')`，或登录时同时写入两个 key

### S2. 铁律系统性缺失 (CRITICAL)
- **影响范围**: Chat.vue, v3/Coach.vue, FoodRecognition.vue, WeeklyReport.vue, Dashboard.vue, HistoryReports.vue, v3/Knowledge.vue, GrowerHome.vue, GrowerTodayHome.vue, SharerHome.vue, ObserverHome.vue, Home.vue, BehaviorAssessment.vue, ProgramToday.vue, ProgramProgress.vue, ChallengeDay.vue, LearnCenter.vue, ContentDetail.vue
- **问题**: 平台铁律要求「AI 生成内容 → 教练审核 → 推送用户」，但上述 18 个页面直接展示 AI 内容，无审核门、无审核标识
- **后果**: AI 回复、营养建议、行为处方、周报建议、风险评估、干预计划等 AI 内容直达用户
- **修复**: 后端在所有 AI 内容响应中增加 `review_status: 'approved'|'pending'|'auto'` 字段；前端按状态显示审核标识或隐藏未审核内容

### S3. raw fetch() 绕过认证拦截器 (CRITICAL)
- **影响范围**: ObserverHome.vue, GrowerHome.vue
- **问题**: 使用 `fetch()` 替代 `api` axios 实例，绕过 Bearer token 注入
- **后果**: API 请求无认证 header，可能暴露数据
- **修复**: 替换为 `api.get(...)` / `api.post(...)`

### S4. IDOR (越权访问) 模式 (HIGH)
- **影响范围**: Dashboard.vue, LearnCenter.vue, MyLearning.vue, MyStage.vue, HistoryReports.vue, VisionGuardianView.vue, VisionExamRecord.vue
- **问题**: 客户端 userId 直接拼接到 URL 路径中，localStorage 可被篡改
- **修复**: 后端使用 `/me` 端点从 JWT 提取身份；前端不再传递 userId

### S5. 公开页面数据泄露 (HIGH)
- **影响范围**: CoachDirectory.vue, v3/Knowledge.vue
- **问题**: 公开页面暴露内部用户 ID、角色层级、学员数量等敏感信息；Knowledge 公开页可查询受限知识库
- **修复**: 后端创建公开安全子集端点；Knowledge 端点仅返回公开级文档

### S6. Pervasive `any` 类型 (LOW, 技术债)
- **影响范围**: 几乎所有页面
- **问题**: API 响应未定义 TypeScript 接口，普遍使用 `any`
- **修复**: 创建 `types/api.ts` 定义所有响应接口

---

## Batch 1: 认证/安全/公开入口 (7 页)

| ID | 严重度 | 维度 | 页面:行号 | 描述 |
|----|--------|------|-----------|------|
| B1-001 | CRITICAL | D3 | Login.vue:77-82 | 演示密码 (`Observer@2026` 等) 硬编码在客户端 JS 中 |
| B1-005 | CRITICAL | D3 | Register.vue:36 | Token 存为 `access_token`，路由守卫读 `h5_token` → 注册后立即被踢到登录页 |
| B1-023 | HIGH | D4 | Notifications.vue:50 | 教练消息直接展示无审核标识 |
| B1-006 | HIGH | D3 | Register.vue:37 | refresh_token 存储但主客户端不使用 |
| B1-002 | MEDIUM | D1 | Login.vue:109 | 登录存 `h5_token`，v3 页面读 `access_token` → 认证断裂 |
| B1-010 | MEDIUM | D2 | PrivacyPolicy route | 缺少 `meta: { public: true }`，未登录用户无法访问 |
| B1-012 | MEDIUM | D2 | AboutUs route | 同上，缺少公开标记 |
| B1-019 | MEDIUM | D1 | AccountSettings.vue:84 | ROLE_MAP 缺少 `sharer` 角色 |
| B1-020 | MEDIUM | D2 | AccountSettings.vue:98 | 通知设置开关无持久化，纯装饰 |
| B1-024 | MEDIUM | D3 | Notifications.vue:296 | `router.push(n.link)` 未验证链接，可能开放重定向 |
| B1-025 | MEDIUM | D1 | Notifications.vue:300 | 7 个 API 调用串行执行，应并行 |

**小计**: 2 CRITICAL, 3 HIGH, 6 MEDIUM, 16 LOW = 27 issues

---

## Batch 2: AI 对话 & 铁律合规 (6 页)

| ID | 严重度 | 维度 | 页面:行号 | 描述 |
|----|--------|------|-----------|------|
| B2-001 | CRITICAL | D4 | Chat.vue + chat.ts:69 | MasterAgent AI 回复直推用户消息列表，无教练审核门 |
| B2-002 | CRITICAL | D4 | Chat.vue:245 | 食物识别 `res.advice` AI 营养建议直接展示 |
| B2-005 | CRITICAL | D4 | v3/Coach.vue:65 | `/api/v3/chat/message` AI 回复直接展示 |
| B2-006 | HIGH | D3 | v3/Coach.vue | 双 token 问题导致 v3 API 无认证 |
| B2-007 | HIGH | D1 | v3/Coach.vue:61 | `chatApi.send(null, ...)` 传 null 作为 user_id |
| B2-011 | HIGH | D4 | RxPrescriptionDetail.vue:8 | 草稿状态处方内容全量展示（待审核但内容可见） |
| B2-014 | HIGH | D4 | FoodRecognition.vue:98 | AI 营养建议无审核标识 |
| B2-019 | HIGH | D4 | WeeklyReport.vue:96 | `report.suggestions` AI 建议直接展示 |
| B2-022 | HIGH | D4 | Dashboard.vue:44 | `recommendations` AI 风险评估建议直接展示 |
| B2-024 | HIGH | D3 | Dashboard.vue:148 | userId 路径参数可篡改 → IDOR |
| B2-025 | MEDIUM | D1 | Dashboard.vue:182 | ECharts 未在 unmount 时 dispose → 内存泄漏 |

**小计**: 3 CRITICAL, 9 HIGH, 8 MEDIUM, 7 LOW = 27 issues

---

## Batch 3: 角色主页 & 引导 (8 页)

| ID | 严重度 | 维度 | 页面:行号 | 描述 |
|----|--------|------|-----------|------|
| B3-001 | CRITICAL | D1 | ObserverHome.vue:223 | raw `fetch()` 绕过 auth 拦截器 |
| B3-002 | CRITICAL | D1 | ObserverHome.vue:145 | `userStore.currentUser` 不存在 → 永远 undefined |
| B3-003 | CRITICAL | D1 | GrowerHome.vue:126 | raw `fetch()` 绕过 auth 拦截器 |
| B3-004 | CRITICAL | D4 | GrowerHome.vue:66 | `aiNudge` AI 内容直接展示无审核标识 |
| B3-005 | HIGH | D1 | GrowerHome.vue:117 | `toggleTask()` 只改本地状态，无 API 调用 |
| B3-006 | HIGH | D1 | ObserverHome.vue:213 | `completeTask()` 无 API 持久化 |
| B3-009 | HIGH | D4 | GrowerTodayHome.vue:100 | `coachTip` AI 教练提示无审核标识 |
| B3-010 | HIGH | D4 | SharerHome.vue:164 | 同上 `coachTip` 问题 |
| B3-011 | HIGH | D1 | Router:66 | `/home/today` 指向 GrowerHome (有 bug)，GrowerTodayHome (已修复) 为孤立文件 |
| B3-012 | MEDIUM | D3 | Router:22 | `bhp_role_level` localStorage 可篡改 → 角色伪造 |

**小计**: 4 CRITICAL, 7 HIGH, 5 MEDIUM, 7 LOW = 23 issues

---

## Batch 4: 学习/内容/知识 (6 页)

| ID | 严重度 | 维度 | 页面:行号 | 描述 |
|----|--------|------|-----------|------|
| B4-001 | CRITICAL | D3 | ContentDetail.vue:49 | `v-html="content.body"` 未消毒 → **存储型 XSS** |
| B4-002 | CRITICAL | D4 | Knowledge.vue:21 | 公开页 AI 回答直接展示 "AI 回答" 无审核 |
| B4-003 | CRITICAL | D1 | CoachRecruit.vue:312 | `import coachApi from '@/api/coach-api'` — 文件不存在，构建会失败 |
| B4-004 | HIGH | D1 | CoachRecruit router-patch.ts | 路由未注册，页面无法访问 |
| B4-005 | HIGH | D4 | LearnCenter.vue:59 | 推荐内容无 AI 标识或审核标记 |
| B4-006 | HIGH | D4 | ContentDetail.vue:26 | 内容详情无 AI 来源指示或审核标识 |
| B4-007 | HIGH | D3 | Knowledge.vue (public) | 公开 RAG 端点可能返回受限知识库内容 |
| B4-008 | MEDIUM | D3 | LearnCenter/MyLearning | IDOR: userId 拼接到 URL 路径 |

**小计**: 3 CRITICAL, 4 HIGH, 4 MEDIUM, 4 LOW = 15 issues

---

## Batch 5: 评估/阶段/行为 (7 页)

| ID | 严重度 | 维度 | 页面:行号 | 描述 |
|----|--------|------|-----------|------|
| B5-012 | CRITICAL | D3 | v3/Assessment.vue | 双 token → v3 API 调用无认证 |
| B5-015 | CRITICAL | D3 | v3/AssessmentBatch.vue | 同上双 token 问题 |
| B5-004 | HIGH | D4 | BehaviorAssessment.vue:197 | 自发评估的 AI 干预建议直接展示 |
| B5-006 | HIGH | D3 | MyStage.vue:396 | IDOR: 回退读取 localStorage userId 获取他人档案 |
| B5-017 | MEDIUM | D1 | AssessmentBatch.vue:7 | `questions.length === 0` 时进度条显示 NaN% |
| B5-019 | MEDIUM | D2 | JourneyView.vue | 使用 Tailwind 类但项目可能未配置 Tailwind |

**小计**: 2 CRITICAL, 2 HIGH, 5 MEDIUM, 7 LOW = 16 issues

---

## Batch 6: 项目/挑战/健康数据 (8 页)

| ID | 严重度 | 维度 | 页面:行号 | 描述 |
|----|--------|------|-----------|------|
| B6-001 | HIGH | D4 | ProgramToday.vue:45 | `push.content.knowledge/behavior_guide/recommended_content` AI 内容无审核 |
| B6-002 | HIGH | D4 | ProgramProgress.vue:42 | `data.suggestions` AI 改进建议无审核 |
| B6-003 | MEDIUM | D4 | ChallengeDay.vue:100 | `management_content/behavior_guidance` 可能含 AI 内容 |
| B6-004 | MEDIUM | D1 | ProgramProgress.vue:116 | ECharts resize 监听器未清理 → 内存泄漏 |
| B6-006 | MEDIUM | D3 | HealthRecords.vue:10 | PII (姓名/邮箱) 直接展示，健康数据无额外认证 |
| B6-007 | MEDIUM | D3 | ChallengeDay.vue:408 | IDOR: enrollmentId 从 URL 获取，5 个 API 端点未做前端所有权检查 |

**小计**: 0 CRITICAL, 2 HIGH, 5 MEDIUM, 6 LOW = 13 issues

---

## Batch 7: 专家平台/学分/晋级 (7 页)

| ID | 严重度 | 维度 | 页面:行号 | 描述 |
|----|--------|------|-----------|------|
| B7-001 | HIGH | D3 | ExpertRegister.vue:366 | 银行账户信息未加密存储在 localStorage draft 中 |
| B7-002 | MEDIUM | D1 | ExpertApplicationStatus.vue:41 | Vant `van-step`/`van-steps` 嵌套错误 → 渲染异常 |
| B7-003 | MEDIUM | D1 | PromotionProgress.vue:127 | ECharts 未 dispose → 内存泄漏 |
| B7-004 | MEDIUM | D1 | PromotionProgress.vue:204 | 雷达图 indicator max=0 时轴坍塌 |
| B7-006 | LOW | D3 | ExpertStudio.vue:146 | brand_colors CSS 注入面（风险低但需后端验证） |

**小计**: 0 CRITICAL, 1 HIGH, 3 MEDIUM, 8 LOW = 12 issues

---

## Batch 8: 视力保护 & 剩余 (6 页)

| ID | 严重度 | 维度 | 页面:行号 | 描述 |
|----|--------|------|-----------|------|
| B8-004 | HIGH | D4 | HistoryReports.vue:47 | `report.recommendations` + `chapters[].content` AI 内容直达患者 |
| B8-005 | HIGH | D3 | CoachDirectory.vue:150 | 公开页泄露内部 ID、role_level、学员数量 |
| B8-001 | HIGH | D1 | VisionDailyLog.vue:221 | `getMyLogs(1)` 仅取 1 天数据，历史日期永远匹配不到 |
| B8-002 | HIGH | D1 | VisionGuardianView.vue:194 | 「查看日志」跳转到自己的日志而非孩子的 |
| B8-003 | HIGH | D3 | VisionGuardianView.vue:183 | IDOR: studentId 直传 dashboard 端点 |
| B8-009 | MEDIUM | D3 | VisionExamRecord.vue:24 | 医学数据字段无客户端 min/max 范围限制 |
| B8-010 | MEDIUM | D3 | HistoryReports.vue (report.ts) | `X-Role: 'patient'` 客户端提供 → 权限提升风险 |
| B8-011 | MEDIUM | D4 | VisionGuardianView.vue:144 | 客户端生成健康建议文本无审核 |

**小计**: 0 CRITICAL, 5 HIGH, 7 MEDIUM, 6 LOW = 18 issues

---

## 按维度分类汇总

### D1 代码质量 (48 issues)
- 双 token 键名不一致 (5 页受影响)
- raw fetch() 绕过认证 (2 页)
- userStore.currentUser 不存在 (1 页)
- ECharts 未 dispose 内存泄漏 (3 页)
- toggleTask/completeTask 无 API 持久化 (2 页)
- 串行 API 调用应并行 (4 页)
- CoachRecruit 导入不存在的模块 + 路由未注册

### D2 UI/UX (22 issues)
- PrivacyPolicy/AboutUs 缺少 `public: true` 路由标记
- 多处 safe-area-inset-bottom 未适配
- 版本号硬编码 "v1.0.0" (2 处)
- 通知设置开关无持久化
- loading 初始化为 false → 空状态闪烁

### D3 安全 (32 issues)
- **存储型 XSS**: ContentDetail.vue `v-html` (CRITICAL)
- **硬编码密码**: Login.vue 演示密码 (CRITICAL)
- **双 token 断裂**: v3 页面无认证 (CRITICAL)
- **IDOR**: 7+ 页面 userId 可篡改
- **公开页数据泄露**: CoachDirectory, Knowledge
- **银行信息 localStorage**: ExpertRegister
- **开放重定向**: Notifications.vue `router.push(n.link)`
- **客户端角色伪造**: localStorage `bhp_role_level`

### D4 铁律合规 (22 issues)
- **AI Chat 直推**: Chat.vue, v3/Coach.vue (CRITICAL)
- **AI 营养建议**: FoodRecognition.vue (HIGH)
- **AI 处方草稿可见**: RxPrescriptionDetail.vue (HIGH)
- **AI 周报建议**: WeeklyReport.vue (HIGH)
- **AI 风险评估**: Dashboard.vue, HistoryReports.vue (HIGH)
- **AI 教练提示**: GrowerHome, GrowerTodayHome, SharerHome (HIGH)
- **AI 干预建议**: BehaviorAssessment.vue (HIGH)
- **AI 推送内容**: ProgramToday, ProgramProgress, ChallengeDay (HIGH)
- **AI 推荐内容**: LearnCenter, ContentDetail (HIGH)
- **AI 知识库回答**: v3/Knowledge.vue (CRITICAL)
- **AI 行为数据洞察**: GrowerHome aiNudge (CRITICAL)

---

## 修复优先级排序 (Top 20)

| 优先级 | ID | 描述 | 工作量 |
|--------|-----|------|--------|
| P0-1 | B4-001 | ContentDetail.vue `v-html` XSS → 集成 DOMPurify | 小 |
| P0-2 | S1 | v3/http.js token key 统一为 `h5_token` | 小 |
| P0-3 | B1-001 | Login.vue 演示密码移到 `import.meta.env.DEV` 守卫后 | 小 |
| P0-4 | B3-001/003 | ObserverHome/GrowerHome raw fetch → api 实例 | 小 |
| P0-5 | B3-002 | ObserverHome `userStore.currentUser` → 使用实际属性 | 小 |
| P0-6 | B1-005 | Register.vue 使用 `storage.setToken()` 替代直接 localStorage | 小 |
| P0-7 | B4-003 | CoachRecruit.vue 创建缺失的 API 模块或移除导入 | 小 |
| P1-1 | S2 | 后端: AI 内容响应增加 `review_status` 字段 | 大 |
| P1-2 | S2 | 前端: 所有 AI 内容展示增加审核标识/门控逻辑 | 大 |
| P1-3 | B2-011 | RxPrescriptionDetail: draft 状态隐藏详细内容 | 中 |
| P1-4 | S4 | 所有 userId 路径参数 → 后端 `/me` 端点 | 中 |
| P1-5 | B3-011 | 路由 `/home/today` 指向 GrowerTodayHome.vue | 小 |
| P1-6 | B8-005 | CoachDirectory 后端创建公开安全子集端点 | 中 |
| P1-7 | B7-001 | ExpertRegister 银行信息从 draft 排除 | 小 |
| P1-8 | B3-005/006 | 实现 toggleTask/completeTask API 调用 | 中 |
| P2-1 | B1-010/012 | PrivacyPolicy/AboutUs 添加 `public: true` | 小 |
| P2-2 | B3-012 | 角色重定向从 JWT 解码而非 localStorage | 中 |
| P2-3 | B2-025, B6-004, B7-003 | 所有 ECharts dispose 修复 | 小 |
| P2-4 | B8-001/002 | VisionDailyLog 日期范围 + Guardian 查看子女日志 | 中 |
| P2-5 | B8-009 | VisionExamRecord 医学数据 min/max 范围 | 小 |

---

## 铁律合规模型 (推荐架构)

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│   AI Engine  │ ──→ │ coach_push_queue │ ──→ │  Coach 审核  │
│ (MasterAgent,│     │   (后端网关)      │     │  (Admin Portal)│
│  LLM, RAG)  │     │                 │     │              │
└──────────────┘     └─────────────────┘     └──────┬───────┘
                                                     │ approved
                                                     ▼
                                              ┌──────────────┐
                                              │   H5 前端     │
                                              │ (展示已审核内容)│
                                              │ + "已审核" 标识│
                                              └──────────────┘

前端展示逻辑:
- review_status === 'approved' → 正常展示 + "教练已审核" 标识
- review_status === 'pending'  → 隐藏内容 + "等待教练审核" 提示
- review_status === 'auto'     → 展示 + "AI辅助，仅供参考" 标识 (仅限事实性数据)
```

---

## 结论

H5 移动端存在 **14 个 CRITICAL 级别问题**，其中最紧迫的是:

1. **ContentDetail.vue 存储型 XSS** — 用户提交的内容通过 `v-html` 直接渲染，可注入恶意脚本窃取 token
2. **双 Token 系统** — 5 个 v3 页面的所有 API 调用实际上处于无认证状态
3. **铁律系统性缺失** — 18+ 页面直接展示 AI 内容，完全绕过 `coach_push_queue_service` 审核门
4. **硬编码演示密码** — 4 个角色的密码以明文形式存在于生产代码中

建议按 P0 → P1 → P2 顺序分批修复，P0 级别 (7 项) 可在 1-2 天内完成。
