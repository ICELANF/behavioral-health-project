import api from './index'
import type { DashboardData } from './types'

export const dashboardApi = {
  // 获取当前用户看板数据（从 JWT 提取身份，防止 IDOR）
  async getDashboard(): Promise<DashboardData> {
    return api.get('/api/v1/dashboard/me')
  }
}

export default dashboardApi
