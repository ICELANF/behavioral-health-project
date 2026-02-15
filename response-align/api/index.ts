/**
 * 业务 API 集合 (V4 响应格式对齐版)
 * ==============================================
 * 在 P3 路径修正基础上，增加响应格式归一化层
 *
 * 架构: View → API(index.ts) → normalizer → http → backend
 *       视图层不再关心后端字段差异
 *
 * 归一化清单:
 *  ✅ journeyApi.getStatus()     — current_stage → journey_stage
 *  ✅ journeyApi.getTransitions() — 数组安全
 *  ✅ learningApi.getStats()      — 嵌套 → 平铺
 *  ✅ challengeApi.list()         — enrollment_count → enrolled_count
 *  ✅ challengeApi.getMy()        — enrollment → Challenge + my_progress
 *  ✅ microActionApi.getToday()   — domain → action_type, scheduled_date → scheduled_at
 *  ✅ contentApi.list()           — level(str) → content_level(num), domain → category
 *  ✅ pointsApi.getBalance()      — total_points → total
 *  ✅ agentApi.*                   — sessionId string
 *  ✅ 分页统一                     — items/data/results → items
 */

import http from './http'
import {
  normalizeJourneyStatus,
  normalizeLearningStats,
  normalizeChallenge,
  normalizeEnrollment,
  normalizeMicroAction,
  normalizeContentItem,
  normalizeCreditsBalance,
  normalizeArray,
  normalizePaginated,
  type LearningStatsFlat,
} from './normalizers'
import type {
  JourneyStatus, UserPermissions, MicroAction,
  Challenge, AssessmentAssignment, AssessmentResult,
  PointTransaction, PaginatedResponse
} from '@/types'

// =====================================================================
// 旅程 (journey_api.py — 15 endpoints)
// =====================================================================

export const journeyApi = {
  /** /journey/state → JourneyStatus (归一化 current_stage→journey_stage) */
  async getStatus(): Promise<JourneyStatus> {
    const raw = await http.get('/journey/state').then(r => r.data)
    return normalizeJourneyStatus(raw)
  },

  /** /journey/stage/transitions → 转换记录数组 */
  async getTransitions(): Promise<any[]> {
    const raw = await http.get('/journey/stage/transitions').then(r => r.data)
    return Array.isArray(raw) ? raw : (raw?.items || raw?.transitions || [])
  },

  getProgress(): Promise<any> {
    return http.get('/journey/stage/progress').then(r => r.data)
  },

  activate(data?: any): Promise<any> {
    return http.post('/journey/activate', data).then(r => r.data)
  },

  getHistory(): Promise<any[]> {
    return http.get('/journey/history').then(r => r.data)
  },
}

// =====================================================================
// 权限分段 (segments_api.py) — 路径+格式均正确
// =====================================================================

export const segmentsApi = {
  getPermissions(): Promise<UserPermissions> {
    return http.get('/segments/permissions').then(r => r.data)
  },
  getRoles(): Promise<any[]> {
    return http.get('/segments/roles').then(r => r.data)
  },
}

// =====================================================================
// 评估 (assessment_assignment_api.py + assessment_api.py)
// =====================================================================

export const assessmentApi = {
  getAssignments(): Promise<AssessmentAssignment[]> {
    return http.get('/assessment-assignments/my-pending').then(r => r.data)
  },

  getResult(assignmentId: number): Promise<AssessmentResult> {
    return http.get(`/assessment-assignments/${assignmentId}/result`).then(r => r.data)
  },

  submit(assignmentId: number, answers: Record<string, any>): Promise<AssessmentResult> {
    return http.post(`/assessment-assignments/${assignmentId}/submit`, { answers }).then(r => r.data)
  },

  runPipeline(userId: number): Promise<any> {
    return http.post('/assessment/evaluate', { user_id: userId }).then(r => r.data)
  },

  getProfile(): Promise<any> {
    return http.get('/assessment/profile/me').then(r => r.data)
  },
}

// =====================================================================
// Agent 对话 (chat_rest_api.py + agent_api.py)
// sessionId 全部 string 类型 (后端用UUID)
// =====================================================================

export const agentApi = {
  listSessions(): Promise<any[]> {
    return http.get('/chat/sessions').then(r => r.data)
  },
  async createSession(agentId?: string): Promise<any> {
    const raw = await http.post('/chat/sessions', { agent_id: agentId }).then(r => r.data)
    // 统一 session_id 字段
    return { ...raw, session_id: raw.session_id || raw.id }
  },
  getMessages(sessionId: string): Promise<any[]> {
    return http.get(`/chat/sessions/${sessionId}/messages`).then(r => r.data)
  },
  sendMessage(sessionId: string, message: string): Promise<any> {
    return http.post(`/chat/sessions/${sessionId}/messages`, { content: message }).then(r => r.data)
  },
  deleteSession(sessionId: string): Promise<void> {
    return http.delete(`/chat/sessions/${sessionId}`).then(r => r.data)
  },
  runAgent(agentId: string, input: string): Promise<any> {
    return http.post('/agent/run', { agent_id: agentId, input }).then(r => r.data)
  },
  listAgents(): Promise<any[]> {
    return http.get('/agent/list').then(r => r.data)
  },
}

// =====================================================================
// 微行动 (micro_action_api.py)
// 归一化: domain → action_type, scheduled_date → scheduled_at
// =====================================================================

export const microActionApi = {
  async getToday(): Promise<MicroAction[]> {
    const raw = await http.get('/micro-actions/today').then(r => r.data)
    return normalizeArray(raw, normalizeMicroAction)
  },

  async complete(taskId: number, state: string): Promise<MicroAction> {
    const raw = await http.post(`/micro-actions/${taskId}/complete`, { state }).then(r => r.data)
    return normalizeMicroAction(raw)
  },

  skip(taskId: number): Promise<any> {
    return http.post(`/micro-actions/${taskId}/skip`).then(r => r.data)
  },

  async getHistory(): Promise<MicroAction[]> {
    const raw = await http.get('/micro-actions/history').then(r => r.data)
    return normalizeArray(raw, normalizeMicroAction)
  },

  getStats(): Promise<any> {
    return http.get('/micro-actions/stats').then(r => r.data)
  },
}

// =====================================================================
// 挑战 (challenge_api.py)
// 归一化: enrollment_count → enrolled_count, enrollment → my_progress
// =====================================================================

export const challengeApi = {
  async list(): Promise<Challenge[]> {
    const raw = await http.get('/challenges').then(r => r.data)
    const arr = Array.isArray(raw) ? raw : (raw?.items || raw?.data || [])
    return arr.map(normalizeChallenge)
  },

  /** /challenges/my-enrollments → 归一化为带 my_progress 的 Challenge[] */
  async getMy(): Promise<any[]> {
    const raw = await http.get('/challenges/my-enrollments').then(r => r.data)
    const arr = Array.isArray(raw) ? raw : (raw?.items || raw?.data || [])
    return arr.map(normalizeEnrollment)
  },

  enroll(challengeId: number): Promise<any> {
    return http.post(`/challenges/${challengeId}/enroll`).then(r => r.data)
  },

  /** checkin = advance enrollment (参数是 enrollment_id, 非 challenge_id) */
  checkin(enrollmentId: number, data?: any): Promise<any> {
    return http.post(`/challenges/enrollments/${enrollmentId}/advance`, data).then(r => r.data)
  },

  getToday(enrollmentId: number): Promise<any> {
    return http.get(`/challenges/enrollments/${enrollmentId}/today`).then(r => r.data)
  },

  getProgress(enrollmentId: number): Promise<any> {
    return http.get(`/challenges/enrollments/${enrollmentId}/progress`).then(r => r.data)
  },
}

// =====================================================================
// 积分 (credits_api.py)
// 归一化: total_points → total
// =====================================================================

export const pointsApi = {
  async getBalance(): Promise<{ total: number; growth: number; contribution: number; influence: number }> {
    const raw = await http.get('/credits/my').then(r => r.data)
    return normalizeCreditsBalance(raw)
  },

  async getHistory(page = 1, pageSize = 20): Promise<PaginatedResponse<PointTransaction>> {
    const raw = await http.get('/credits/my/records', { params: { page, page_size: pageSize } }).then(r => r.data)
    return normalizePaginated<PointTransaction>(raw)
  },

  getModules(): Promise<any[]> {
    return http.get('/credits/modules').then(r => r.data)
  },
}

// =====================================================================
// 学习 (learning_api.py)
// 归一化: 嵌套 {learning_time, learning_points, streak} → 平铺
// =====================================================================

export const learningApi = {
  async getStats(userId: number): Promise<LearningStatsFlat> {
    const raw = await http.get(`/learning/grower/stats/${userId}`).then(r => r.data)
    return normalizeLearningStats(raw)
  },

  recordTime(minutes: number, contentId?: number): Promise<any> {
    return http.post('/learning/grower/time/add', { minutes, content_id: contentId }).then(r => r.data)
  },

  getTime(userId: number): Promise<any> {
    return http.get(`/learning/grower/time/${userId}`).then(r => r.data)
  },

  getStreak(userId: number): Promise<any> {
    return http.get(`/learning/grower/streak/${userId}`).then(r => r.data)
  },

  getLeaderboard(): Promise<any[]> {
    return http.get('/learning/leaderboard/growers').then(r => r.data)
  },
}

// =====================================================================
// 内容 (content_api.py)
// 归一化: level(str) → content_level(num), domain → category
// =====================================================================

export const contentApi = {
  async list(params?: { category?: string; level?: number; page?: number }): Promise<PaginatedResponse<any>> {
    const raw = await http.get('/content', { params }).then(r => r.data)
    return normalizePaginated(raw, normalizeContentItem)
  },

  async getDetail(contentId: number): Promise<any> {
    const raw = await http.get(`/content/stream/${contentId}`).then(r => r.data)
    return normalizeContentItem(raw)
  },

  getDetailByType(contentType: string, contentId: number): Promise<any> {
    return http.get(`/content/detail/${contentType}/${contentId}`).then(r => r.data)
  },

  getRecommended(): Promise<any[]> {
    return http.get('/content/recommended').then(r => r.data)
  },
}

// =====================================================================
// 设备/健康数据 (health-data 路由组)
// =====================================================================

export const deviceApi = {
  getSummary(): Promise<any> {
    return http.get('/health-data/summary').then(r => r.data)
  },
  getBloodGlucose(days?: number): Promise<any[]> {
    return http.get('/health-data/glucose', { params: { days } }).then(r => r.data)
  },
  getHeartRate(days?: number): Promise<any[]> {
    return http.get('/health-data/vitals', { params: { days } }).then(r => r.data)
  },
  getSleep(days?: number): Promise<any[]> {
    return http.get('/health-data/sleep', { params: { days } }).then(r => r.data)
  },
  getSteps(days?: number): Promise<any[]> {
    return http.get('/health-data/activity', { params: { days } }).then(r => r.data)
  },
}

// =====================================================================
// 个人资料
// =====================================================================

export const profileApi = {
  getProfile(): Promise<any> {
    return http.get('/assessment/profile/me').then(r => r.data)
  },
  updateProfile(data: { display_name?: string; email?: string; phone?: string }): Promise<any> {
    return http.put('/api/v3/auth/profile', data, {
      baseURL: ''
    }).then(r => r.data)
  },
  /** @deprecated 使用 authApi.changePassword 代替 */
  changePassword(data: { old_password: string; new_password: string }): Promise<void> {
    return http.put('/auth/password', data).then(r => r.data)
  },
}

// =====================================================================
// 教练 (coach_api.py)
// =====================================================================

export const coachApi = {
  getDashboard(): Promise<any> {
    return http.get('/coach/dashboard').then(r => r.data)
  },
  getClients(): Promise<any[]> {
    return http.get('/coach/students').then(r => r.data)
  },
  getClientDetail(studentId: number): Promise<any> {
    return http.get(`/coach/students/${studentId}`).then(r => r.data)
  },
  getKpi(): Promise<any> {
    return http.get('/coach/performance').then(r => r.data)
  },
  getClientPoints(userId: number): Promise<any> {
    return http.get(`/learning/coach/points/${userId}`).then(r => r.data)
  },
  getSupervisionRecords(): Promise<any[]> {
    return http.get('/coach/push-queue/').then(r => r.data)
  },
  getClientActivity(studentId: number): Promise<any> {
    return http.get(`/coach/students/${studentId}/activity`).then(r => r.data)
  },
  getClientBehavioralProfile(studentId: number): Promise<any> {
    return http.get(`/coach/students/${studentId}/behavioral-profile`).then(r => r.data)
  },
  getClientGlucose(studentId: number): Promise<any> {
    return http.get(`/coach/students/${studentId}/glucose`).then(r => r.data)
  },
}

// =====================================================================
// 管理员
// =====================================================================

export const adminApi = {
  getStats(): Promise<any> {
    return http.get('/admin/stats').then(r => r.data)
  },
  getUsers(params?: { page?: number; role?: string; search?: string }): Promise<PaginatedResponse<any>> {
    return http.get('/admin/users', { params }).then(r => r.data)
  },
  updateUserRole(userId: number, role: string): Promise<any> {
    return http.put(`/admin/users/${userId}`, { role }).then(r => r.data)
  },
  getGovernanceHealth(): Promise<any> {
    return http.get('/governance/dashboard').then(r => r.data)
  },
  getSafetyLogs(params?: { page?: number }): Promise<PaginatedResponse<any>> {
    return http.get('/safety/logs', { params }).then(r => r.data)
  },
  getAuditLogs(params?: { page?: number; activity_type?: string }): Promise<PaginatedResponse<any>> {
    return http.get('/stats/admin/activity-report', { params }).then(r => r.data)
  },
  getAnalyticsOverview(): Promise<any> {
    return http.get('/analytics/admin/overview').then(r => r.data)
  },
  getStageDistribution(): Promise<any> {
    return http.get('/analytics/admin/stage-distribution').then(r => r.data)
  },
}

// =====================================================================
// 反思 (reflection_api.py)
// =====================================================================

export const reflectionApi = {
  list(): Promise<any[]> {
    return http.get('/reflection/entries').then(r => r.data)
  },
  create(data: { content: string; mood?: number }): Promise<any> {
    return http.post('/reflection/entries', data).then(r => r.data)
  },
  getPrompts(): Promise<any[]> {
    return http.get('/reflection/prompts').then(r => r.data)
  },
  getStats(): Promise<any> {
    return http.get('/reflection/stats').then(r => r.data)
  },
}
