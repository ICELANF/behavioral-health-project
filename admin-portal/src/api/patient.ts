import request from './request'

export interface PatientProfile {
  id: string
  name: string
  gender: 'male' | 'female'
  age: number
  height: string
  weight: string
  diagnosis: string
  diagnosisDate: string
  medicalNotes: string
  medications: Array<{ name: string; dosage: string; frequency: string }>
  allergies: string[]
  emergencyContact: { name: string; relation: string; phone: string }
}

export interface PatientTrajectory {
  ttmTimeline: Array<{ name: string; date: string; duration: string; color: string; current?: boolean; completed?: boolean }>
  implicitData: Array<{ icon: string; value: string; label: string; trend: string }>
  explicitData: Array<{ icon: string; value: string; label: string; trend: string }>
  recentEvents: Array<{ id: number; text: string; time: string; type: string; color: string }>
}

// Mock profile
const mockProfile: PatientProfile = {
  id: 'p001',
  name: '张三',
  gender: 'male',
  age: 45,
  height: '172',
  weight: '78',
  diagnosis: '2型糖尿病',
  diagnosisDate: '2023-06-15',
  medicalNotes: '空腹血糖偏高，HbA1c 7.2%，合并轻度高血压',
  medications: [
    { name: '二甲双胍', dosage: '500mg', frequency: '每日两次' },
    { name: '氨氯地平', dosage: '5mg', frequency: '每日一次' },
  ],
  allergies: ['青霉素', '磺胺类'],
  emergencyContact: { name: '李四', relation: '配偶', phone: '13800138000' },
}

export const patientApi = {
  async getProfile(patientId: string) {
    try {
      const res = await request.get(`/v1/patient/${patientId}/profile`)
      return res.data
    } catch (e) {
      return mockProfile
    }
  },

  async updateProfile(patientId: string, data: Partial<PatientProfile>) {
    try {
      const res = await request.put(`/v1/patient/${patientId}/profile`, data)
      return res.data
    } catch (e) {
      return { success: true }
    }
  },

  async getDevices(patientId: string) {
    try {
      const res = await request.get(`/v1/patient/${patientId}/devices`)
      return res.data
    } catch (e) {
      return {
        devices: [
          { id: 'd1', name: '小米手环 8', model: 'Xiaomi Band 8', type: 'band', online: true, lastSync: '2分钟前' },
          { id: 'd2', name: '血糖仪', model: 'Dexcom G7', type: 'glucose', online: true, lastSync: '15分钟前' },
        ]
      }
    }
  },

  async bindDevice(patientId: string, deviceType: string) {
    try {
      const res = await request.post(`/v1/patient/${patientId}/devices/bind`, { type: deviceType })
      return res.data
    } catch (e) {
      return { success: true, deviceId: `d_${Date.now()}` }
    }
  },

  async unbindDevice(patientId: string, deviceId: string) {
    try {
      const res = await request.delete(`/v1/patient/${patientId}/devices/${deviceId}`)
      return res.data
    } catch (e) {
      return { success: true }
    }
  },

  async getTrajectory(patientId: string, period: string = '30d') {
    try {
      const res = await request.get(`/v1/patient/${patientId}/trajectory`, { params: { period } })
      return res.data
    } catch (e) {
      return {
        ttmTimeline: [
          { name: '前思考期', date: '2024-10-01', duration: '45天', color: '#ff4d4f', completed: true },
          { name: '思考期', date: '2024-11-15', duration: '30天', color: '#fa8c16', completed: true },
          { name: '准备期', date: '2024-12-15', duration: '15天', color: '#fadb14', completed: true },
          { name: '行动期', date: '2025-01-01', duration: '至今', color: '#52c41a', current: true },
        ],
        implicitData: [
          { icon: '📱', value: '45min', label: 'App日均使用', trend: '↑ 12%' },
          { icon: '🚶', value: '6,850', label: '日均步数', trend: '↑ 8%' },
        ],
      }
    }
  },
}

export default patientApi
