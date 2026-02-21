/**
 * 业务 API 集合 (V4 联调修正版)
 * ================================
 * 基于 actual_routes.txt (562条实际路由) 逐条校正
 *
 * 修正清单 (31个404 → 0个404):
 * ┌────────────────┬────────────────────────────────┬────────────────────────────────────┐
 * │ 功能域          │ 前端旧路径 (404)               │ 后端实际路径 (修正后)                │
 * ├────────────────┼────────────────────────────────┼────────────────────────────────────┤
 * │ journey        │ /journey/status                │ /journey/state                     │
 * │ journey        │ /journey/transitions/{userId}  │ /journey/stage/transitions         │
 * │ assessment     │ /assessments/assignments       │ /assessment-assignments/my-pending │
 * │ assessment     │ /assessments/{id}/result       │ /assessment-assignments/{id}/result│
 * │ assessment     │ /assessments/{id}/submit       │ /assessment-assignments/{id}/submit│
 * │ assessment     │ /assessment-pipeline/run       │ /assessment/evaluate               │
 * │ challenge      │ /challenges/{id}/checkin       │ /challenges/enrollments/{id}/advance│
 * │ credits        │ /credits/balance               │ /credits/my                        │
 * │ credits        │ /credits/history               │ /credits/my/records                │
 * │ learning       │ /learning/grower/stats         │ /learning/grower/stats/{userId}    │
 * │ learning       │ /learning/time                 │ /learning/grower/time/add          │
 * │ content        │ /content/{id}                  │ /content/stream/{id}               │
 * │ device         │ /device/summary                │ /health-data/summary               │
 * │ device         │ /device/blood-glucose          │ /health-data/glucose               │
 * │ device         │ /device/heart-rate             │ /health-data/vitals                │
 * │ device         │ /device/sleep                  │ /health-data/sleep                 │
 * │ device         │ /device/steps                  │ /health-data/activity              │
 * │ profile        │ /users/me                      │ /assessment/profile/me             │
 * │ profile        │ PUT /users/me                  │ PUT /auth/profile (v3 降级)         │
 * │ coach          │ /coach/clients                 │ /coach/students                    │
 * │ coach          │ /coach/clients/{id}            │ /coach/students/{id}               │
 * │ coach          │ /coach/kpi                     │ /coach/performance                 │
 * │ coach          │ /coach/supervision             │ /coach/push-queue/                 │
 * │ admin          │ /admin/users/{id}/role         │ /admin/users/{id} (PUT)            │
 * │ admin          │ /admin/governance/health       │ /governance/dashboard              │
 * │ admin          │ /admin/safety-logs             │ /safety/logs                       │
 * │ admin          │ /admin/audit-logs              │ /stats/admin/activity-report       │
 * │ reflection     │ /reflections                   │ /reflection/entries                │
 * │ reflection     │ POST /reflections              │ POST /reflection/entries           │
 * └────────────────┴────────────────────────────────┴────────────────────────────────────┘
 *
 * 另外 4个 "测试ID无效" 的404 (端点本身存在, 不需修路径):
 *   - POST /chat/sessions/{session_id}/messages  ← session_id=1 不存在
 *   - DELETE /chat/sessions/{session_id}         ← session_id=1 不存在
 *   - GET /content/{id}                          ← 路径结构变化, 已修
 *   - POST /challenges/{id}/checkin              ← 概念变化, 已修
 */

import http from './http'
import type {
  JourneyStatus, UserPermissions, MicroAction,
  Challenge, AssessmentAssignment, AssessmentResult,
  PointTransaction, PaginatedResponse
} from '@/types'

// Re-export flywheel APIs for convenience
export { coachFlywheelApi } from './coach-api'
export { expertFlywheelApi } from './expert-api'
export { adminFlywheelApi } from './admin-flywheel-api'

// =====================================================================
// 旅程 (journey_api.py — 15 endpoints)
// =====================================================================

export const journeyApi = {
  /** 旧: /journey/status → 实际: /journey/state */
  getStatus(): Promise<JourneyStatus> {
    return http.get('/v1/journey/state').then(r => r.data)
  },

  /** 旧: /journey/transitions/{userId} → 实际: /journey/stage/transitions (当前用户) */
  getTransitions(): Promise<any[]> {
    return http.get('/v1/journey/stage/transitions').then(r => r.data)
  },

  /** 额外: 阶段进度 */
  getProgress(): Promise<any> {
    return http.get('/v1/journey/stage/progress').then(r => r.data)
  },

  /** 额外: 激活旅程 */
  activate(data?: any): Promise<any> {
    return http.post('/v1/journey/activate', data).then(r => r.data)
  },

  /** 额外: 历史记录 */
  getHistory(): Promise<any[]> {
    return http.get('/v1/journey/history').then(r => r.data)
  },
}

// =====================================================================
// 权限分段 (segments_api.py) — ✅ 路径正确, 无需修改
// =====================================================================

export const segmentsApi = {
  getPermissions(): Promise<UserPermissions> {
    return http.get('/v1/segments/permissions').then(r => r.data)
  },
  getRoles(): Promise<any[]> {
    return http.get('/v1/segments/roles').then(r => r.data)
  },
}

// =====================================================================
// 评估 (assessment_assignment_api.py + assessment_api.py)
// =====================================================================

export const assessmentApi = {
  /** 旧: /assessments/assignments → 实际: /assessment-assignments/my-pending */
  getAssignments(): Promise<AssessmentAssignment[]> {
    return http.get('/v1/assessment-assignments/my-pending').then(r => r.data)
  },

  /** 旧: /assessments/{id}/result → 实际: /assessment-assignments/{id}/result */
  getResult(assignmentId: number): Promise<AssessmentResult> {
    return http.get(`/v1/assessment-assignments/${assignmentId}/result`).then(r => r.data)
  },

  /** 旧: /assessments/{id}/submit → 实际: /assessment-assignments/{id}/submit */
  submit(assignmentId: number, answers: Record<string, any>): Promise<AssessmentResult> {
    return http.post(`/v1/assessment-assignments/${assignmentId}/submit`, { answers }).then(r => r.data)
  },

  /** 旧: /assessment-pipeline/run → 实际: /assessment/evaluate */
  runPipeline(userId: number): Promise<any> {
    return http.post('/v1/assessment/evaluate', { user_id: userId }).then(r => r.data)
  },

  /** 额外: 获取个人评估画像 */
  getProfile(): Promise<any> {
    return http.get('/v1/assessment/profile/me').then(r => r.data)
  },
}

// =====================================================================
// Agent 对话 (chat_rest_api.py + agent_api.py) — ✅ 路径正确
// 注: session_id 需要用真实ID, 不能用整数1
// =====================================================================

export const agentApi = {
  listSessions(): Promise<any[]> {
    return http.get('/v1/chat/sessions').then(r => r.data)
  },
  createSession(agentId?: string): Promise<any> {
    return http.post('/v1/chat/sessions', { agent_id: agentId }).then(r => r.data)
  },
  getMessages(sessionId: string): Promise<any[]> {
    return http.get(`/v1/chat/sessions/${sessionId}/messages`).then(r => r.data)
  },
  sendMessage(sessionId: string, message: string): Promise<any> {
    return http.post(`/v1/chat/sessions/${sessionId}/messages`, { content: message }).then(r => r.data)
  },
  deleteSession(sessionId: string): Promise<void> {
    return http.delete(`/v1/chat/sessions/${sessionId}`).then(r => r.data)
  },
  /** ✅ 路径正确 */
  runAgent(agentId: string, input: string): Promise<any> {
    return http.post('/v1/agent/run', { agent_id: agentId, input }).then(r => r.data)
  },
  /** ✅ 路径正确 */
  listAgents(): Promise<any[]> {
    return http.get('/v1/agent/list').then(r => r.data)
  },
}

// =====================================================================
// 微行动 (micro_action_api.py)
// 注: 路径参数名 {id} → {task_id}
// =====================================================================

export const microActionApi = {
  /** ✅ 路径正确 */
  getToday(): Promise<MicroAction[]> {
    return http.get('/v1/micro-actions/today').then(r => r.data)
  },
  /** 旧: /micro-actions/{id}/complete → 实际: /micro-actions/{task_id}/complete */
  complete(taskId: number, state: string): Promise<MicroAction> {
    return http.post(`/v1/micro-actions/${taskId}/complete`, { state }).then(r => r.data)
  },
  /** 额外: 跳过任务 */
  skip(taskId: number): Promise<any> {
    return http.post(`/v1/micro-actions/${taskId}/skip`).then(r => r.data)
  },
  /** 额外: 历史记录 */
  getHistory(): Promise<any[]> {
    return http.get('/v1/micro-actions/history').then(r => r.data)
  },
  /** 额外: 统计 */
  getStats(): Promise<any> {
    return http.get('/v1/micro-actions/stats').then(r => r.data)
  },
}

// =====================================================================
// 挑战 (challenge_api.py)
// =====================================================================

export const challengeApi = {
  /** ✅ 路径正确 */
  list(): Promise<Challenge[]> {
    return http.get('/v1/challenges').then(r => r.data)
  },

  /** 旧: /challenges/my → 实际: /challenges/my-enrollments */
  getMy(): Promise<Challenge[]> {
    return http.get('/v1/challenges/my-enrollments').then(r => r.data)
  },

  /** ✅ 路径正确: /challenges/{challenge_id}/enroll */
  enroll(challengeId: number): Promise<any> {
    return http.post(`/v1/challenges/${challengeId}/enroll`).then(r => r.data)
  },

  /**
   * 旧: /challenges/{id}/checkin
   * 实际: /challenges/enrollments/{enrollment_id}/advance
   * 注意: 参数从 challengeId 变为 enrollmentId
   */
  checkin(enrollmentId: number, data?: any): Promise<any> {
    return http.post(`/v1/challenges/enrollments/${enrollmentId}/advance`, data).then(r => r.data)
  },

  /** 额外: 获取今日推送 */
  getToday(enrollmentId: number): Promise<any> {
    return http.get(`/v1/challenges/enrollments/${enrollmentId}/today`).then(r => r.data)
  },

  /** 额外: 进度查询 */
  getProgress(enrollmentId: number): Promise<any> {
    return http.get(`/v1/challenges/enrollments/${enrollmentId}/progress`).then(r => r.data)
  },
}

// =====================================================================
// 积分 (credits_api.py)
// =====================================================================

export const pointsApi = {
  /** 旧: /credits/balance → 实际: /credits/my */
  getBalance(): Promise<{ total: number; growth: number; contribution: number; influence: number }> {
    return http.get('/v1/credits/my').then(r => r.data)
  },

  /** 旧: /credits/history → 实际: /credits/my/records */
  getHistory(page = 1, pageSize = 20): Promise<PaginatedResponse<PointTransaction>> {
    return http.get('/v1/credits/my/records', { params: { page, page_size: pageSize } }).then(r => r.data)
  },

  /** 额外: 积分模块列表 */
  getModules(): Promise<any[]> {
    return http.get('/v1/credits/modules').then(r => r.data)
  },
}

// =====================================================================
// 学习 (learning_api.py)
// =====================================================================

export const learningApi = {
  /**
   * 旧: /learning/grower/stats
   * 实际: /learning/grower/stats/{user_id}
   * 注: 需要传 userId
   */
  getStats(userId: number): Promise<any> {
    return http.get(`/v1/learning/grower/stats/${userId}`).then(r => r.data)
  },

  /** 旧: /learning/time → 实际: /learning/grower/time/add */
  recordTime(minutes: number, contentId?: number): Promise<any> {
    return http.post('/v1/learning/grower/time/add', { minutes, content_id: contentId }).then(r => r.data)
  },

  /** 额外: 获取学习时长 */
  getTime(userId: number): Promise<any> {
    return http.get(`/v1/learning/grower/time/${userId}`).then(r => r.data)
  },

  /** 额外: 学习连续天数 */
  getStreak(userId: number): Promise<any> {
    return http.get(`/v1/learning/grower/streak/${userId}`).then(r => r.data)
  },

  /** 额外: 排行榜 */
  getLeaderboard(): Promise<any[]> {
    return http.get('/v1/learning/leaderboard/growers').then(r => r.data)
  },

  /** 里程碑和奖励 */
  getRewards(userId: number): Promise<any> {
    return http.get(`/v1/learning/rewards/${userId}`).then(r => r.data)
  },
}

// =====================================================================
// 内容 (content_api.py)
// =====================================================================

export const contentApi = {
  /** ✅ 路径正确: /content (列表+推荐) */
  list(params?: { category?: string; level?: number; page?: number }): Promise<PaginatedResponse<any>> {
    return http.get('/v1/content', { params }).then(r => r.data)
  },

  /**
   * 旧: /content/{id}
   * 实际: /content/stream/{content_id} 或 /content/detail/{content_type}/{content_id}
   * 使用 stream 版本 (更通用, 不需要 content_type)
   */
  getDetail(contentId: number): Promise<any> {
    return http.get(`/v1/content/stream/${contentId}`).then(r => r.data)
  },

  /** 额外: 按类型获取详情 */
  getDetailByType(contentType: string, contentId: number): Promise<any> {
    return http.get(`/v1/content/detail/${contentType}/${contentId}`).then(r => r.data)
  },

  /** 额外: 推荐内容 */
  getRecommended(): Promise<any[]> {
    return http.get('/v1/content/recommended').then(r => r.data)
  },
}

// =====================================================================
// 设备/健康数据 (health-data 路由组, 非 device)
// =====================================================================

export const deviceApi = {
  /** 旧: /device/summary → 实际: /health-data/summary */
  getSummary(): Promise<any> {
    return http.get('/v1/health-data/summary').then(r => r.data)
  },

  /** 旧: /device/blood-glucose → 实际: /health-data/glucose */
  getBloodGlucose(days?: number): Promise<any[]> {
    return http.get('/v1/health-data/glucose', { params: { days } }).then(r => r.data)
  },

  /** 旧: /device/heart-rate → 实际: /health-data/vitals */
  getHeartRate(days?: number): Promise<any[]> {
    return http.get('/v1/health-data/vitals', { params: { days } }).then(r => r.data)
  },

  /** 旧: /device/sleep → 实际: /health-data/sleep */
  getSleep(days?: number): Promise<any[]> {
    return http.get('/v1/health-data/sleep', { params: { days } }).then(r => r.data)
  },

  /** 旧: /device/steps → 实际: /health-data/activity */
  getSteps(days?: number): Promise<any[]> {
    return http.get('/v1/health-data/activity', { params: { days } }).then(r => r.data)
  },
}

// =====================================================================
// 个人资料
// =====================================================================

export const profileApi = {
  /** 获取健康档案 */
  getProfile(): Promise<any> {
    return http.get('/v1/assessment/profile/me').then(r => r.data)
  },

  /** 保存健康档案 (诊断、用药、过敏、紧急联系人等) */
  updateProfile(data: Record<string, any>): Promise<any> {
    return http.put('/v1/assessment/profile/me', data).then(r => r.data)
  },

  /**
   * 密码修改 — 已移至 authApi, 此处保留向后兼容
   * @deprecated 使用 authApi.changePassword 代替
   */
  changePassword(data: { old_password: string; new_password: string }): Promise<void> {
    return http.put('/v1/auth/password', data).then(r => r.data)
  },
}

// =====================================================================
// 教练 (coach_api.py)
// =====================================================================

export const coachApi = {
  /** ✅ 路径正确 */
  getDashboard(): Promise<any> {
    return http.get('/v1/coach/dashboard').then(r => r.data)
  },

  /** 旧: /coach/clients → 实际: /coach/students */
  getClients(): Promise<any[]> {
    return http.get('/v1/coach/students').then(r => r.data)
  },

  /** 旧: /coach/clients/{userId} → 实际: /coach/students/{student_id} */
  getClientDetail(studentId: number): Promise<any> {
    return http.get(`/v1/coach/students/${studentId}`).then(r => r.data)
  },

  /** 旧: /coach/kpi → 实际: /coach/performance */
  getKpi(): Promise<any> {
    return http.get('/v1/coach/performance').then(r => r.data)
  },

  /** ✅ 路径正确: /learning/coach/points/{user_id} */
  getClientPoints(userId: number): Promise<any> {
    return http.get(`/v1/learning/coach/points/${userId}`).then(r => r.data)
  },

  /** 旧: /coach/supervision → 实际: /coach/push-queue/ */
  getSupervisionRecords(): Promise<any[]> {
    return http.get('/v1/coach/push-queue/').then(r => r.data)
  },

  /** 额外: 学员活动详情 */
  getClientActivity(studentId: number): Promise<any> {
    return http.get(`/v1/coach/students/${studentId}/activity`).then(r => r.data)
  },

  /** 额外: 学员行为画像 */
  getClientBehavioralProfile(studentId: number): Promise<any> {
    return http.get(`/v1/coach/students/${studentId}/behavioral-profile`).then(r => r.data)
  },

  /** 额外: 学员血糖数据 */
  getClientGlucose(studentId: number): Promise<any> {
    return http.get(`/v1/coach/students/${studentId}/glucose`).then(r => r.data)
  },
}

// =====================================================================
// 管理员
// =====================================================================

export const adminApi = {
  /** ✅ 路径正确 */
  getStats(): Promise<any> {
    return http.get('/v1/admin/stats').then(r => r.data)
  },

  /** ✅ 路径正确 */
  getUsers(params?: { page?: number; role?: string; search?: string }): Promise<PaginatedResponse<any>> {
    return http.get('/v1/admin/users', { params }).then(r => r.data)
  },

  /**
   * 旧: PUT /admin/users/{userId}/role  → 实际: PUT /admin/users/{user_id}
   * 后端是通用 PUT, 包含 role 在请求体中
   */
  updateUserRole(userId: number, role: string): Promise<any> {
    return http.put(`/v1/admin/users/${userId}`, { role }).then(r => r.data)
  },

  /** 旧: /admin/governance/health → 实际: /governance/dashboard */
  getGovernanceHealth(): Promise<any> {
    return http.get('/v1/governance/dashboard').then(r => r.data)
  },

  /** 旧: /admin/safety-logs → 实际: /safety/logs */
  getSafetyLogs(params?: { page?: number }): Promise<PaginatedResponse<any>> {
    return http.get('/v1/safety/logs', { params }).then(r => r.data)
  },

  /** 旧: /admin/audit-logs → 实际: /stats/admin/activity-report */
  getAuditLogs(params?: { page?: number; activity_type?: string }): Promise<PaginatedResponse<any>> {
    return http.get('/v1/stats/admin/activity-report', { params }).then(r => r.data)
  },

  /** 额外: 分析概览 */
  getAnalyticsOverview(): Promise<any> {
    return http.get('/v1/analytics/admin/overview').then(r => r.data)
  },

  /** 额外: 阶段分布 */
  getStageDistribution(): Promise<any> {
    return http.get('/v1/analytics/admin/stage-distribution').then(r => r.data)
  },
}

// =====================================================================
// 反思 (reflection_api.py)
// =====================================================================

export const reflectionApi = {
  /** 旧: /reflections → 实际: /reflection/entries */
  list(): Promise<any[]> {
    return http.get('/v1/reflection/entries').then(r => r.data)
  },

  /** 旧: POST /reflections → 实际: POST /reflection/entries */
  create(data: { content: string; mood?: number }): Promise<any> {
    return http.post('/v1/reflection/entries', data).then(r => r.data)
  },

  /** 额外: 反思提示 */
  getPrompts(): Promise<any[]> {
    return http.get('/v1/reflection/prompts').then(r => r.data)
  },

  /** 额外: 反思统计 */
  getStats(): Promise<any> {
    return http.get('/v1/reflection/stats').then(r => r.data)
  },
}
