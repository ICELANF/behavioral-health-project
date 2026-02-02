import api from './index'

/**
 * 获取完整报告（患者视角）
 * 后端 L6 层会根据 X-Role 自动过滤：
 *   - patient: 17 章中仅返回经过"人文改写"后的 3 章
 *   - doctor/admin: 返回完整 17 章
 */
export function fetchFullReport() {
  return api.get('/api/v1/reports/full', {
    headers: { 'X-Role': 'patient' }
  })
}
