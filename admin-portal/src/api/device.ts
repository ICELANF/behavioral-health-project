import request from './request'

export interface DeviceData {
  heartRate: Array<{ time: string; value: number }>
  sleep: Array<{ date: string; total: number; deep: number; light: number; rem: number }>
  steps: Array<{ date: string; steps: number }>
  glucose: Array<{ time: string; value: number; tag: string }>
  bloodPressure: Array<{ date: string; systolic: number; diastolic: number; pulse: number }>
}

export interface DeviceInfo {
  id: string
  name: string
  model: string
  type: 'band' | 'glucose' | 'bp' | 'scale'
  online: boolean
  lastSync: string
  batteryLevel?: number
}

export const deviceApi = {
  async getDeviceData(patientId: string, period: '7d' | '30d' | '90d' = '7d') {
    const res = await request.get(`/v1/device/${patientId}/data`, { params: { period } })
    return res.data
  },

  async getDevices(patientId: string) {
    const res = await request.get(`/v1/device/${patientId}/list`)
    return res.data
  },

  async syncDevice(patientId: string, deviceId: string) {
    const res = await request.post(`/v1/device/${patientId}/${deviceId}/sync`)
    return res.data
  },

  async getAlertThresholds(patientId: string) {
    const res = await request.get(`/v1/device/${patientId}/thresholds`)
    return res.data
  },

  async updateAlertThreshold(patientId: string, key: string, data: { low: number; high: number }) {
    const res = await request.put(`/v1/device/${patientId}/thresholds/${key}`, data)
    return res.data
  },
}

export default deviceApi
