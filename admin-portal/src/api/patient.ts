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

export const patientApi = {
  async getProfile(patientId: string) {
    const res = await request.get(`/v1/patient/${patientId}/profile`)
    return res.data
  },

  async updateProfile(patientId: string, data: Partial<PatientProfile>) {
    const res = await request.put(`/v1/patient/${patientId}/profile`, data)
    return res.data
  },

  async getDevices(patientId: string) {
    const res = await request.get(`/v1/patient/${patientId}/devices`)
    return res.data
  },

  async bindDevice(patientId: string, deviceType: string) {
    const res = await request.post(`/v1/patient/${patientId}/devices/bind`, { type: deviceType })
    return res.data
  },

  async unbindDevice(patientId: string, deviceId: string) {
    const res = await request.delete(`/v1/patient/${patientId}/devices/${deviceId}`)
    return res.data
  },

  async getTrajectory(patientId: string, period: string = '30d') {
    const res = await request.get(`/v1/patient/${patientId}/trajectory`, { params: { period } })
    return res.data
  },
}

export default patientApi
