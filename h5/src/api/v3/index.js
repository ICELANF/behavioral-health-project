/**
 * API 模块集合 — 对应后端 26 个端点
 */
import http from './http.js'

// ══════════════════════════════════════════════
// 鉴权
// ══════════════════════════════════════════════
export const authApi = {
  register: (phone, password, nickname = '') =>
    http.post('/auth/register', { phone, password, nickname }),

  login: (phone, password) =>
    http.post('/auth/login', { phone, password }),

  refresh: (refresh_token) =>
    http.post('/auth/refresh', { refresh_token }),

  getMe: () => http.get('/auth/me'),

  changePassword: (old_password, new_password) =>
    http.put('/auth/password', { old_password, new_password }),

  updateProfile: (params) => http.put('/auth/profile', null, { params }),
}

// ══════════════════════════════════════════════
// Coach 对话
// ══════════════════════════════════════════════
export const chatApi = {
  send: (user_id, message, opts = {}) =>
    http.post('/chat/message', { user_id, message, ...opts }),

  knowledge: (question, doc_type = null) =>
    http.post('/chat/knowledge', { question, doc_type }),

  search: (question, top_k = 5) =>
    http.post('/chat/knowledge/search', { question, top_k }),

  prescription: (profile) =>
    http.post('/chat/prescription', profile),

  stats: () => http.get('/chat/stats'),
}

// ══════════════════════════════════════════════
// 诊断管道
// ══════════════════════════════════════════════
export const diagnosticApi = {
  minimal: (data) => http.post('/diagnostic/minimal', data),
  full: (data) => http.post('/diagnostic/full', data),
}

// ══════════════════════════════════════════════
// 渐进式评估
// ══════════════════════════════════════════════
export const assessmentApi = {
  batches: () => http.get('/assessment/batches'),

  session: (userId) => http.get(`/assessment/session/${userId}`),

  submit: (user_id, batch_id, answers, duration_seconds = 0) =>
    http.post('/assessment/submit', { user_id, batch_id, answers, duration_seconds }),

  recommend: (userId) => http.get(`/assessment/recommend/${userId}`),
}

// ══════════════════════════════════════════════
// 效果追踪
// ══════════════════════════════════════════════
export const trackingApi = {
  daily: (data) => http.post('/tracking/daily', data),
  weeklyReview: (user_id) => http.post('/tracking/weekly-review', { user_id }),
}

// ══════════════════════════════════════════════
// 积分激励
// ══════════════════════════════════════════════
export const incentiveApi = {
  checkin: (user_id) => http.post('/incentive/checkin', { user_id }),
  taskComplete: (user_id, task_id) =>
    http.post('/incentive/task-complete', { user_id, task_id }),
  balance: (userId) => http.get(`/incentive/balance/${userId}`),
}

// ══════════════════════════════════════════════
// 系统
// ══════════════════════════════════════════════
export const systemApi = {
  health: () => http.get('/health'),
  status: () => http.get('/status'),
}
