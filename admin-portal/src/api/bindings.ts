import request from './request'

/**
 * 绑定管理 API — Admin 教练-学员绑定 CRUD
 */
export const bindingsApi = {
  /** 查询绑定列表 */
  list(params?: {
    coach_id?: number
    student_id?: number
    binding_type?: string
    active_only?: boolean
    page?: number
    page_size?: number
  }) {
    return request.get('/v1/admin/bindings', { params })
  },

  /** 获取单个绑定详情 */
  get(bindingId: string) {
    return request.get(`/v1/admin/bindings/${bindingId}`)
  },

  /** 创建绑定 */
  create(data: {
    coach_id: number
    student_id: number
    binding_type?: string
    permissions?: Record<string, boolean>
  }) {
    return request.post('/v1/admin/bindings', data)
  },

  /** 更新绑定 */
  update(bindingId: string, data: {
    permissions?: Record<string, boolean>
    binding_type?: string
    is_active?: boolean
  }) {
    return request.put(`/v1/admin/bindings/${bindingId}`, data)
  },

  /** 解绑 (软删除) */
  unbind(bindingId: string) {
    return request.delete(`/v1/admin/bindings/${bindingId}`)
  },

  /** 批量绑定 */
  batchBind(data: {
    coach_id: number
    student_ids: number[]
    binding_type?: string
  }) {
    return request.post('/v1/admin/bindings/batch', data)
  },

  /** 批量解绑 */
  batchUnbind(data: {
    binding_ids: string[]
    reason?: string
  }) {
    return request.post('/v1/admin/bindings/batch-unbind', data)
  },

  /** 统计总览 */
  statsOverview() {
    return request.get('/v1/admin/bindings/stats/overview')
  },

  /** 教练负载 */
  coachLoad(params?: { min_students?: number }) {
    return request.get('/v1/admin/bindings/stats/coach-load', { params })
  },
}
