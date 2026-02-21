import request from './request'

// ============ 类型定义 ============

export interface HealthMetric {
  id: string
  type: 'glucose' | 'weight' | 'bloodPressure' | 'exercise' | 'mood' | 'meal'
  value: number | { systolic: number; diastolic: number } | string
  unit: string
  timestamp: string
  note?: string
}

export interface GlucoseRecord {
  id: string
  value: number
  unit: 'mmol/L'
  timestamp: string
  note?: string
  tag?: 'fasting' | 'before_meal' | 'after_meal' | 'bedtime'
}

export interface WeightRecord {
  id: string
  value: number
  unit: 'kg'
  timestamp: string
  bmi?: number
}

export interface BloodPressureRecord {
  id: string
  systolic: number
  diastolic: number
  pulse?: number
  timestamp: string
  note?: string
}

export interface ExerciseRecord {
  id: string
  type: string // 'walking' | 'running' | 'cycling' | 'swimming' | 'other'
  duration: number // minutes
  calories?: number
  distance?: number // km
  timestamp: string
}

export interface MoodRecord {
  id: string
  score: number // 1-5
  note?: string
  timestamp: string
}

export interface MealRecord {
  id: string
  type: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  description: string
  calories?: number
  timestamp: string
  imageUrl?: string
}

export interface HealthScore {
  overall: number // 0-100
  glucose: number
  weight: number
  exercise: number
  mood: number
  breakdown: {
    glucose: { score: number; trend: 'up' | 'down' | 'stable'; message: string }
    weight: { score: number; trend: 'up' | 'down' | 'stable'; message: string }
    exercise: { score: number; trend: 'up' | 'down' | 'stable'; message: string }
    mood: { score: number; trend: 'up' | 'down' | 'stable'; message: string }
  }
}

export interface HealthTrend {
  metric: string
  period: 'week' | 'month' | 'quarter'
  data: Array<{ date: string; value: number }>
  average: number
  min: number
  max: number
  trend: 'improving' | 'stable' | 'declining'
}

export interface Achievement {
  id: string
  name: string
  description: string
  icon: string
  unlocked: boolean
  unlockedAt?: string
  progress?: number // 0-100
}

export interface DailyTask {
  id: string
  title: string
  type: 'glucose' | 'weight' | 'exercise' | 'mood' | 'assessment'
  completed: boolean
  completedAt?: string
  dueTime?: string
  priority: 'high' | 'medium' | 'low'
}

export interface HealthSnapshot {
  glucose: { value: number; trend: string; status: 'normal' | 'warning' | 'danger' }
  weight: { value: number; trend: string; bmi: number }
  exercise: { todayMinutes: number; weeklyGoal: number; percentage: number }
  mood: { averageScore: number; trend: string }
  lastUpdate: string
}

// ============ API 方法 — 对接真实后端 ============
// All methods are JWT-scoped (no patientId needed)

const periodToDays: Record<string, number> = { '7d': 7, '30d': 30, '90d': 90, week: 7, month: 30, quarter: 90 }

function dateRange(days: number): { start_date: string; end_date: string } {
  const end = new Date()
  const start = new Date(end.getTime() - days * 86400000)
  return {
    start_date: start.toISOString().slice(0, 10),
    end_date: end.toISOString().slice(0, 10),
  }
}

export const healthApi = {
  // ── Data Recording ──
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

  // ── Data Retrieval ──
  async getGlucoseHistory(params: { period?: string } = {}) {
    const days = periodToDays[params.period || '7d'] || 7
    const res = await request.get('/v1/mp/device/glucose', { params: { ...dateRange(days), limit: days * 4 } })
    return res.data
  },
  async getWeightHistory(params: { period?: string } = {}) {
    const days = periodToDays[params.period || '7d'] || 7
    const res = await request.get('/v1/mp/device/weight', { params: { ...dateRange(days), limit: days } })
    return res.data
  },
  async getBloodPressureHistory(params: { limit?: number } = {}) {
    const res = await request.get('/v1/mp/device/blood-pressure', { params: { limit: params.limit || 30 } })
    return res.data
  },
  async getExerciseHistory(params: { period?: string } = {}) {
    const days = periodToDays[params.period || '7d'] || 7
    const res = await request.get('/v1/mp/device/activity', { params: dateRange(days) })
    return res.data
  },

  // ── Scores & Summaries ──
  async getHealthScore() {
    const res = await request.get('/v1/health-data/summary')
    return res.data
  },
  async getHealthSnapshot() {
    const res = await request.get('/v1/mp/device/dashboard/today')
    return res.data
  },
  async getDailyTasks() {
    const res = await request.get('/v1/daily-tasks/today')
    return res.data
  },
  async completeTask(taskId: string) {
    const res = await request.post(`/v1/daily-tasks/${taskId}/checkin`)
    return res.data
  },
  async getAchievements() {
    const res = await request.get('/v1/credits/my')
    return res.data
  },
  async getAISummary() {
    const res = await request.get('/v1/coach-tip/today')
    return res.data
  },
  async getTrends(metric: string, params: { period?: string } = {}) {
    const days = periodToDays[params.period || '30d'] || 30
    const res = await request.get(`/v1/mp/device/${metric}`, { params: { ...dateRange(days), limit: days * 4 } })
    return res.data
  },
  async getTaskCatalog() {
    const res = await request.get('/v1/daily-tasks/catalog')
    return res.data
  },
  async addTaskFromCatalog(catalogId: string, customTitle?: string) {
    const res = await request.post('/v1/daily-tasks/add-from-catalog', {
      catalog_id: catalogId,
      custom_title: customTitle || undefined,
    })
    return res.data
  },
  async removeTask(taskId: string) {
    const res = await request.delete(`/v1/daily-tasks/${taskId}`)
    return res.data
  },
}

export default healthApi
