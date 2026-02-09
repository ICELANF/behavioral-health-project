import request from './request'

/**
 * 学分管理 API
 */
export const creditApi = {
  /** 获取课程模块列表（用户端） */
  listModules(params?: { module_type?: string; tier?: string; target_role?: string }) {
    return request.get('/v1/credits/modules', { params })
  },

  /** 获取我的学分汇总 */
  getMyCredits() {
    return request.get('/v1/credits/my')
  },

  /** 获取我的学分明细 */
  getMyRecords(params?: { skip?: number; limit?: number }) {
    return request.get('/v1/credits/my/records', { params })
  },

  /** 管理员 - 获取所有模块 */
  adminListModules(params?: {
    include_inactive?: boolean
    module_type?: string
    target_role?: string
    skip?: number
    limit?: number
  }) {
    return request.get('/v1/credits/admin/modules', { params })
  },

  /** 管理员 - 创建模块 */
  adminCreateModule(data: Record<string, unknown>) {
    return request.post('/v1/credits/admin/modules', data)
  },

  /** 管理员 - 更新模块 */
  adminUpdateModule(moduleId: string, data: Record<string, unknown>) {
    return request.put(`/v1/credits/admin/modules/${moduleId}`, data)
  },

  /** 管理员 - 停用模块 */
  adminDeleteModule(moduleId: string) {
    return request.delete(`/v1/credits/admin/modules/${moduleId}`)
  },

  /** 管理员 - 学分统计 */
  adminStats() {
    return request.get('/v1/credits/admin/stats')
  },
}

/**
 * 同道者关系 API
 */
export const companionApi = {
  /** 获取我带教的同道者 */
  getMyMentees(params?: { status?: string }) {
    return request.get('/v1/companions/my-mentees', { params })
  },

  /** 获取我的导师 */
  getMyMentors() {
    return request.get('/v1/companions/my-mentors')
  },

  /** 获取同道者统计 */
  getStats() {
    return request.get('/v1/companions/stats')
  },

  /** 邀请同道者 */
  invite(menteeId: number) {
    return request.post('/v1/companions/invite', null, { params: { mentee_id: menteeId } })
  },

  /** 管理员 - 查看所有关系 */
  adminListAll(params?: {
    status?: string
    mentor_id?: number
    skip?: number
    limit?: number
  }) {
    return request.get('/v1/companions/all', { params })
  },

  /** 标记同道者毕业 */
  graduate(relationId: string, params?: { quality_score?: number; notes?: string }) {
    return request.put(`/v1/companions/${relationId}/graduate`, null, { params })
  },
}

/**
 * 晋级系统 API
 */
export const promotionApi = {
  /** 获取晋级进度 */
  getProgress() {
    return request.get('/v1/promotion/progress')
  },

  /** 获取晋级规则 */
  getRules() {
    return request.get('/v1/promotion/rules')
  },

  /** 校验晋级资格 */
  checkEligibility() {
    return request.get('/v1/promotion/check')
  },

  /** 提交晋级申请 */
  apply() {
    return request.post('/v1/promotion/apply')
  },

  /** 获取晋级申请列表 */
  listApplications(params?: { status?: string }) {
    return request.get('/v1/promotion/applications', { params })
  },

  /** 审核晋级申请 */
  review(applicationId: string, action: string, comment?: string) {
    return request.post(`/v1/promotion/review/${applicationId}`, null, {
      params: { action, comment },
    })
  },
}
