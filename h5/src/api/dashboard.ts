import api from './index'
import type { DashboardData } from './types'

export const dashboardApi = {
  // 获取个人看板数据
  async getDashboard(userId: string): Promise<DashboardData> {
    return api.get(`/api/v1/dashboard/${userId}`)
  }
}

export default dashboardApi
