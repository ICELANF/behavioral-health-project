import api from './index'

export const rxApi = {
  /** 获取处方详情 */
  getDetail(rxId: string) {
    return api.get(`/api/v1/rx/${rxId}`)
  },

  /** 获取我的处方列表 */
  getMyPrescriptions(status = 'active') {
    return api.get('/api/v1/rx/my', { params: { status } })
  },
}
