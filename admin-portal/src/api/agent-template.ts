import request from './request'

/**
 * Agent 模板管理 API
 */
export const agentTemplateApi = {
  /** 列表 */
  list(params?: { agent_type?: string; is_enabled?: boolean; skip?: number; limit?: number }) {
    return request.get('/v1/agent-templates/list', { params })
  },

  /** 仅预置模板 */
  presets() {
    return request.get('/v1/agent-templates/presets')
  },

  /** AgentDomain 枚举 */
  domains() {
    return request.get('/v1/agent-templates/domains')
  },

  /** 详情 */
  get(agentId: string) {
    return request.get(`/v1/agent-templates/${agentId}`)
  },

  /** 创建 */
  create(data: Record<string, unknown>) {
    return request.post('/v1/agent-templates/create', data)
  },

  /** 更新 */
  update(agentId: string, data: Record<string, unknown>) {
    return request.put(`/v1/agent-templates/${agentId}`, data)
  },

  /** 删除 */
  delete(agentId: string) {
    return request.delete(`/v1/agent-templates/${agentId}`)
  },

  /** 启用/停用 */
  toggle(agentId: string) {
    return request.post(`/v1/agent-templates/${agentId}/toggle`)
  },

  /** 克隆 */
  clone(agentId: string, newAgentId: string) {
    return request.post(`/v1/agent-templates/${agentId}/clone`, null, {
      params: { new_agent_id: newAgentId }
    })
  },

  /** 刷新缓存 */
  refreshCache() {
    return request.post('/v1/agent-templates/refresh-cache')
  },
}
