import api from './index'

export const visionApi = {
  /** 行为打卡 (UPSERT) */
  submitBehaviorLog(data: {
    log_date?: string
    outdoor_minutes: number
    screen_sessions: number
    screen_total_minutes: number
    eye_exercise_done: boolean
    lutein_intake_mg: number
    sleep_minutes: number
    input_source?: string
    notes?: string
  }) {
    return api.post('/api/v1/vision/log', data)
  },

  /** 查询我的行为日志 */
  getMyLogs(days = 30) {
    return api.get('/api/v1/vision/log/me', { params: { days } })
  },

  /** 查询指定用户日志 (教练/监护人) */
  getUserLogs(userId: number, days = 30) {
    return api.get(`/api/v1/vision/log/${userId}`, { params: { days } })
  },

  /** 查询我的目标 */
  getMyGoals() {
    return api.get('/api/v1/vision/goals/me')
  },

  /** 更新我的目标 */
  updateMyGoals(data: {
    outdoor_target_min?: number
    screen_session_limit?: number
    screen_daily_limit?: number
    lutein_target_mg?: number
    sleep_target_min?: number
    auto_adjust?: boolean
  }) {
    return api.put('/api/v1/vision/goals/me', data)
  },

  /** 创建监护关系 */
  bindGuardian(data: {
    student_user_id: number
    relationship?: string
    notify_risk_threshold?: string
    can_input_behavior?: boolean
  }) {
    return api.post('/api/v1/vision/guardian/bind', data)
  },

  /** 查询我监护的学生 */
  getMyStudents() {
    return api.get('/api/v1/vision/guardian/students')
  },

  /** 查询我的监护人 */
  getMyGuardians() {
    return api.get('/api/v1/vision/guardian/guardians')
  },

  /** 解除监护关系 */
  unbindGuardian(bindingId: number) {
    return api.delete(`/api/v1/vision/guardian/${bindingId}`)
  },

  /** 我的视力档案 */
  getMyProfile() {
    return api.get('/api/v1/vision/profile/me')
  },

  /** 更新视力档案 */
  updateProfile(data: {
    is_vision_student?: boolean
    myopia_onset_age?: number
    ttm_vision_stage?: string
    notes?: string
  }) {
    return api.put('/api/v1/vision/profile/me', data)
  },

  /** 录入视力检查记录 */
  createExam(data: {
    user_id?: number
    exam_date: string
    left_eye_sph?: number
    right_eye_sph?: number
    left_eye_cyl?: number
    right_eye_cyl?: number
    left_eye_axial_len?: number
    right_eye_axial_len?: number
    left_eye_va?: number
    right_eye_va?: number
    exam_type?: string
    examiner_name?: string
    institution?: string
    notes?: string
  }) {
    return api.post('/api/v1/vision/exam', data)
  },

  /** 查询检查记录 */
  getExamRecords(userId: number, limit = 20) {
    return api.get(`/api/v1/vision/exam/${userId}`, { params: { limit } })
  },

  /** 视力保护仪表盘 */
  getDashboard(userId: number) {
    return api.get(`/api/v1/vision/dashboard/${userId}`)
  },
}
