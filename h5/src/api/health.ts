/**
 * 健康数据 API — H5 端
 * 复用后端 device_rest_api / daily-tasks / food_recognition 端点
 */
import request from './request'

export const healthApi = {
  // ── 数据录入 ──
  async recordGlucose(data: any) {
    const res = await request.post('/v1/mp/device/glucose/manual', data)
    return res.data
  },
  async recordWeight(data: any) {
    const res = await request.post('/v1/mp/device/weight', data)
    return res.data
  },
  async recordBloodPressure(data: any) {
    const res = await request.post('/v1/mp/device/blood-pressure', data)
    return res.data
  },
  async recordExercise(data: any) {
    const res = await request.post('/v1/daily-tasks/quick-checkin', { domain: 'exercise', ...data })
    return res.data
  },
  async recordMood(data: any) {
    const res = await request.post('/v1/daily-tasks/quick-checkin', { domain: 'emotion', ...data })
    return res.data
  },
  async recordMeal(data: any) {
    const res = await request.post('/v1/daily-tasks/quick-checkin', { domain: 'nutrition', ...data })
    return res.data
  },

  // ── 食物识别 ──
  async recognizeFood(formData: FormData) {
    const res = await request.post('/v1/food/recognize', formData, { timeout: 120000 })
    return res.data
  },

  // ── 语音转文字 (ASR) ──
  async transcribeAudio(formData: FormData) {
    const res = await request.post('/v1/audio/transcribe', formData, { timeout: 60000 })
    return res.data
  },
}

export default healthApi
