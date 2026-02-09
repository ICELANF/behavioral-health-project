import api from './index'

/**
 * 学分相关 API
 */
export const creditApi = {
  /** 获取课程模块列表 */
  listModules(params?: { module_type?: string; target_role?: string }) {
    return api.get('/api/v1/credits/modules', { params })
  },

  /** 获取我的学分汇总 */
  getMyCredits() {
    return api.get('/api/v1/credits/my')
  },

  /** 获取我的学分记录 */
  getMyRecords(params?: { skip?: number; limit?: number }) {
    return api.get('/api/v1/credits/my/records', { params })
  },
}

/**
 * 同道者关系 API
 */
export const companionApi = {
  /** 获取我带教的同道者 */
  getMyMentees(params?: { status?: string }) {
    return api.get('/api/v1/companions/my-mentees', { params })
  },

  /** 获取我的导师 */
  getMyMentors() {
    return api.get('/api/v1/companions/my-mentors')
  },

  /** 获取同道者统计 */
  getStats() {
    return api.get('/api/v1/companions/stats')
  },

  /** 邀请同道者 */
  invite(menteeId: number) {
    return api.post('/api/v1/companions/invite', null, { params: { mentee_id: menteeId } })
  },

  /** 标记同道者毕业 */
  graduate(relationId: string, params?: { quality_score?: number; notes?: string }) {
    return api.put(`/api/v1/companions/${relationId}/graduate`, null, { params })
  },
}

/**
 * 晋级系统 API
 */
export const promotionApi = {
  /** 获取晋级进度 */
  getProgress() {
    return api.get('/api/v1/promotion/progress')
  },

  /** 获取晋级规则 */
  getRules() {
    return api.get('/api/v1/promotion/rules')
  },

  /** 校验晋级资格 */
  checkEligibility() {
    return api.get('/api/v1/promotion/check')
  },

  /** 提交晋级申请 */
  apply() {
    return api.post('/api/v1/promotion/apply')
  },
}
