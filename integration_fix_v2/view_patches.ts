/**
 * view_patches.md — 前端视图层修正指南
 * =====================================
 * API路径修正后, 部分视图需要更新调用参数
 *
 * 优先级: 🔴 必须修 | 🟡 建议修 | 🔵 可选
 */

// =====================================================================
// 🔴 必须修改的视图
// =====================================================================

/**
 * 1. src/views/JourneyView.vue
 * ──────────────────────────────
 * 旧代码:
 *   journeyApi.getStatus(userId)
 *   journeyApi.getTransitions(userId)
 *
 * 修正:
 *   journeyApi.getStatus()          // 不再需要 userId 参数
 *   journeyApi.getTransitions()     // 不再需要 userId 参数, 使用 token
 *
 * 响应格式可能变化:
 *   旧: { status, stage, ... }
 *   新: { state, current_stage, trust_level, ... }  // 字段名可能不同
 */

/**
 * 2. src/views/LearningView.vue
 * ──────────────────────────────
 * 旧代码:
 *   learningApi.getStats()
 *   learningApi.recordTime(minutes, contentId)
 *
 * 修正:
 *   // getStats 现在需要 userId 参数
 *   const userId = authStore.user?.id
 *   learningApi.getStats(userId)
 *
 *   // recordTime 路径已修正, 参数不变
 *   learningApi.recordTime(minutes, contentId)
 */

/**
 * 3. src/views/ChallengesView.vue
 * ──────────────────────────────
 * 旧代码:
 *   challengeApi.getMy()
 *   challengeApi.checkin(challengeId, data)
 *
 * 修正:
 *   challengeApi.getMy()  // 路径已修正为 /my-enrollments, 无需改调用
 *
 *   // checkin 概念变化: 需要 enrollmentId 而非 challengeId
 *   // 先从 getMy() 返回的 enrollment 列表中获取 enrollmentId
 *   const enrollments = await challengeApi.getMy()
 *   const enrollment = enrollments.find(e => e.challenge_id === challengeId)
 *   challengeApi.checkin(enrollment.id, data)
 */

/**
 * 4. src/views/HealthDataView.vue
 * ──────────────────────────────
 * 旧代码:
 *   deviceApi.getSummary()
 *   deviceApi.getBloodGlucose(days)
 *   deviceApi.getHeartRate(days)
 *   deviceApi.getSleep(days)
 *   deviceApi.getSteps(days)
 *
 * 修正: 调用签名不变, 路径在 api/index.ts 中已修正
 * 但注意响应字段可能不同:
 *   旧 getHeartRate → 返回心率数据
 *   新 (vitals)     → 返回包含心率+血压+HRV的综合数据
 *
 *   旧 getSteps     → 返回步数
 *   新 (activity)   → 返回包含步数+运动时长+卡路里的综合数据
 */

/**
 * 5. src/views/ProfileView.vue
 * ──────────────────────────────
 * 旧代码:
 *   profileApi.getProfile()    // GET /users/me
 *   profileApi.updateProfile() // PUT /users/me
 *
 * 修正:
 *   profileApi.getProfile()    // 路径已修正, 但响应格式可能不同
 *   // getProfile 现在返回评估画像, 包含 big_five, stage 等
 *   // 如果只需要基本信息(名字/邮箱), 使用 authApi.getMe() 即 GET /auth/me
 *
 *   profileApi.updateProfile() // 路径已修正为 PUT /api/v3/auth/profile
 *   // 注意: 这是 v3 路径, http.ts baseURL 是 /api/v1
 *   // 已在 api/index.ts 中用 baseURL: '' 覆盖
 */

/**
 * 6. src/modules/coach/views/ClientsView.vue
 * ──────────────────────────────
 * 旧代码:
 *   coachApi.getClients()
 *   coachApi.getClientDetail(userId)
 *
 * 修正: 调用签名不变, 路径在 api/index.ts 中已修正
 * 但注意:
 *   - "clients" 在后端叫 "students"
 *   - 返回字段可能有 student_id 而非 user_id
 */

/**
 * 7. src/modules/agent/views/AgentChatView.vue
 * ──────────────────────────────
 * 旧代码:
 *   agentApi.getMessages(sessionId: number)
 *   agentApi.sendMessage(sessionId: number, message)
 *   agentApi.deleteSession(sessionId: number)
 *
 * 修正:
 *   // sessionId 类型应为 string, 不是 number
 *   agentApi.getMessages(sessionId: string)
 *   agentApi.sendMessage(sessionId: string, message)
 *   agentApi.deleteSession(sessionId: string)
 */

// =====================================================================
// 🟡 建议修改的视图
// =====================================================================

/**
 * 8. src/views/PointsView.vue
 * ──────────────────────────────
 * 旧代码:
 *   pointsApi.getBalance()
 *   pointsApi.getHistory(page, pageSize)
 *
 * 修正: 调用签名不变, 路径在 api/index.ts 中已修正
 * 返回格式可能变化:
 *   旧: { total, growth, contribution, influence }
 *   新: 可能是 { balance, records: [...] } 的结构
 */

/**
 * 9. src/modules/admin/views/AdminDashboardView.vue
 * ──────────────────────────────
 * 旧代码:
 *   adminApi.getGovernanceHealth()
 *   adminApi.getSafetyLogs()
 *   adminApi.getAuditLogs()
 *
 * 修正: 调用签名不变, 路径在 api/index.ts 中已修正
 * 但注意:
 *   - getGovernanceHealth() 现在返回完整治理仪表盘数据
 *   - getAuditLogs() 现在返回活动报告格式
 */

// =====================================================================
// 🔵 无需修改 (路径修正透明)
// =====================================================================

/**
 * 以下视图的 API 调用签名未变, 路径修正在 api/index.ts 层完成:
 *
 * - src/views/HomeView.vue (journeyApi, microActionApi, challengeApi, pointsApi)
 *   注意: journeyApi.getStatus() 不再需要 userId 参数
 *
 * - src/modules/assessment/views/AssessmentView.vue
 *   注意: assessmentId 在后端叫 assignmentId
 *
 * - src/modules/coach/views/CoachDashboardView.vue
 *   ✅ coachApi.getDashboard() 路径未变
 *
 * - src/modules/behavior/views/ActionsView.vue
 *   ✅ microActionApi 路径未变
 */

// =====================================================================
// 完整修正汇总
// =====================================================================

/**
 * 文件修改清单:
 *
 * 1. src/api/index.ts          — 替换为 fixed_api_index.ts (31个路径修正)
 * 2. src/api/auth.ts           — ✅ 无需修改
 * 3. src/api/http.ts           — ✅ 无需修改
 * 4. src/modules/rx/api/rxApi.ts — 替换为 rxApi_fix.ts (token key修正)
 * 5. src/modules/rx/components/index.ts L51 — './api/rxApi' → '../api/rxApi'
 *
 * 视图层修改:
 * 6. JourneyView.vue           — 移除 getStatus/getTransitions 的 userId 参数
 * 7. LearningView.vue          — getStats() 添加 userId 参数
 * 8. ChallengesView.vue        — checkin(challengeId) → checkin(enrollmentId)
 * 9. AgentChatView.vue         — sessionId: number → string
 * 10. HomeView.vue             — journeyApi.getStatus() 移除 userId
 *
 * 可选:
 * 11. ProfileView.vue          — 检查 getProfile() 返回格式
 * 12. HealthDataView.vue       — 检查 vitals/activity 返回格式
 * 13. AdminDashboardView.vue   — 检查 governance/safety/audit 返回格式
 */
