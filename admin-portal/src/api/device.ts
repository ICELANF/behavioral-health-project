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

// Mock biometric data generator
function generateHeartRateData(hours: number = 24): Array<{ time: string; value: number }> {
  const data = []
  const now = new Date()
  for (let i = hours; i >= 0; i--) {
    const t = new Date(now.getTime() - i * 3600000)
    const baseHR = 70
    const variation = Math.sin(i / 4) * 10 + (Math.random() - 0.5) * 8
    data.push({
      time: `${t.getHours().toString().padStart(2, '0')}:00`,
      value: Math.round(baseHR + variation),
    })
  }
  return data
}

function generateSleepData(days: number = 7): Array<{ date: string; total: number; deep: number; light: number; rem: number }> {
  const data = []
  const labels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  for (let i = 0; i < days; i++) {
    const total = 6 + Math.random() * 2.5
    const deep = total * (0.15 + Math.random() * 0.15)
    const rem = total * (0.18 + Math.random() * 0.07)
    data.push({
      date: labels[i % 7],
      total: parseFloat(total.toFixed(1)),
      deep: parseFloat(deep.toFixed(1)),
      light: parseFloat((total - deep - rem).toFixed(1)),
      rem: parseFloat(rem.toFixed(1)),
    })
  }
  return data
}

function generateStepsData(days: number = 7): Array<{ date: string; steps: number }> {
  const labels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  return labels.slice(0, days).map(label => ({
    date: label,
    steps: Math.round(4000 + Math.random() * 8000),
  }))
}

function generateGlucoseData(): Array<{ time: string; value: number; tag: string }> {
  const readings = [
    { time: '06:30 空腹', base: 5.5 },
    { time: '09:00 早餐后', base: 7.5 },
    { time: '12:30 午餐前', base: 5.2 },
    { time: '14:30 午餐后', base: 8.0 },
    { time: '18:00 晚餐前', base: 5.5 },
    { time: '20:00 晚餐后', base: 7.2 },
    { time: '22:00 睡前', base: 6.0 },
  ]
  return readings.map(r => {
    const value = parseFloat((r.base + (Math.random() - 0.5) * 1.5).toFixed(1))
    let tag = '正常'
    if (value < 3.9) tag = '偏低'
    else if (value > 7.8) tag = '危险'
    else if (value > 6.1) tag = '偏高'
    return { time: r.time, value, tag }
  })
}

function generateBPData(days: number = 7): Array<{ date: string; systolic: number; diastolic: number; pulse: number }> {
  const data = []
  for (let i = 0; i < days; i++) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    data.push({
      date: `${d.getMonth() + 1}/${d.getDate()} 08:00`,
      systolic: Math.round(120 + Math.random() * 20),
      diastolic: Math.round(75 + Math.random() * 15),
      pulse: Math.round(65 + Math.random() * 15),
    })
  }
  return data
}

export const deviceApi = {
  async getDeviceData(patientId: string, period: '7d' | '30d' | '90d' = '7d') {
    try {
      const res = await request.get(`/v1/device/${patientId}/data`, { params: { period } })
      return res.data
    } catch (e) {
      const days = period === '7d' ? 7 : period === '30d' ? 30 : 90
      return {
        heartRate: generateHeartRateData(24),
        sleep: generateSleepData(Math.min(days, 7)),
        steps: generateStepsData(Math.min(days, 7)),
        glucose: generateGlucoseData(),
        bloodPressure: generateBPData(Math.min(days, 7)),
      } as DeviceData
    }
  },

  async getDevices(patientId: string) {
    try {
      const res = await request.get(`/v1/device/${patientId}/list`)
      return res.data
    } catch (e) {
      return {
        devices: [
          { id: 'd1', name: '小米手环 8', model: 'Xiaomi Band 8', type: 'band', online: true, lastSync: '2分钟前', batteryLevel: 75 },
          { id: 'd2', name: '血糖仪', model: 'Dexcom G7', type: 'glucose', online: true, lastSync: '15分钟前', batteryLevel: 90 },
          { id: 'd3', name: '血压计', model: 'Omron HEM-7156', type: 'bp', online: false, lastSync: '2天前', batteryLevel: 30 },
        ] as DeviceInfo[]
      }
    }
  },

  async syncDevice(patientId: string, deviceId: string) {
    try {
      const res = await request.post(`/v1/device/${patientId}/${deviceId}/sync`)
      return res.data
    } catch (e) {
      return { success: true, lastSync: new Date().toISOString() }
    }
  },

  async getAlertThresholds(patientId: string) {
    try {
      const res = await request.get(`/v1/device/${patientId}/thresholds`)
      return res.data
    } catch (e) {
      return {
        thresholds: [
          { key: 'hr_high', name: '心率过高', low: 100, high: 999, unit: 'bpm', triggered: false },
          { key: 'hr_low', name: '心率过低', low: 0, high: 50, unit: 'bpm', triggered: false },
          { key: 'glucose_high', name: '血糖过高', low: 7.8, high: 999, unit: 'mmol/L', triggered: false },
          { key: 'glucose_low', name: '血糖过低', low: 0, high: 3.9, unit: 'mmol/L', triggered: false },
          { key: 'bp_high', name: '血压过高', low: 140, high: 999, unit: 'mmHg', triggered: false },
        ]
      }
    }
  },

  async updateAlertThreshold(patientId: string, key: string, data: { low: number; high: number }) {
    try {
      const res = await request.put(`/v1/device/${patientId}/thresholds/${key}`, data)
      return res.data
    } catch (e) {
      return { success: true }
    }
  },
}

export default deviceApi
