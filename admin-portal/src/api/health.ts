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

// ============ API 方法 ============

export const healthApi = {
  async recordGlucose(patientId: string, data: Omit<GlucoseRecord, 'id'>) {
    const res = await request.post(`/v1/health/${patientId}/glucose`, data)
    return res.data
  },

  async recordWeight(patientId: string, data: Omit<WeightRecord, 'id'>) {
    const res = await request.post(`/v1/health/${patientId}/weight`, data)
    return res.data
  },

  async recordBloodPressure(patientId: string, data: Omit<BloodPressureRecord, 'id'>) {
    const res = await request.post(`/v1/health/${patientId}/blood-pressure`, data)
    return res.data
  },

  async recordExercise(patientId: string, data: Omit<ExerciseRecord, 'id'>) {
    const res = await request.post(`/v1/health/${patientId}/exercise`, data)
    return res.data
  },

  async recordMood(patientId: string, data: Omit<MoodRecord, 'id'>) {
    const res = await request.post(`/v1/health/${patientId}/mood`, data)
    return res.data
  },

  async recordMeal(patientId: string, data: Omit<MealRecord, 'id'>) {
    const res = await request.post(`/v1/health/${patientId}/meal`, data)
    return res.data
  },

  async getGlucoseHistory(patientId: string, params: { period?: '7d' | '30d' | '90d' } = {}) {
    const res = await request.get(`/v1/health/${patientId}/glucose`, { params })
    return res.data
  },

  async getWeightHistory(patientId: string, params: { period?: '7d' | '30d' | '90d' } = {}) {
    const res = await request.get(`/v1/health/${patientId}/weight`, { params })
    return res.data
  },

  async getExerciseHistory(patientId: string, params: { period?: '7d' | '30d' | '90d' } = {}) {
    const res = await request.get(`/v1/health/${patientId}/exercise`, { params })
    return res.data
  },

  async getHealthScore(patientId: string, period: 'week' | 'month' | 'quarter' = 'week') {
    const res = await request.get(`/v1/health/${patientId}/score`, { params: { period } })
    return res.data
  },

  async getTrends(patientId: string, metric: string, period: 'week' | 'month' | 'quarter' = 'week') {
    const res = await request.get(`/v1/health/${patientId}/trends/${metric}`, { params: { period } })
    return res.data
  },

  async getHealthSnapshot(patientId: string) {
    const res = await request.get(`/v1/health/${patientId}/snapshot`)
    return res.data
  },

  async getDailyTasks(patientId: string) {
    const res = await request.get(`/v1/health/${patientId}/tasks/daily`)
    return res.data
  },

  async completeTask(patientId: string, taskId: string) {
    const res = await request.post(`/v1/health/${patientId}/tasks/${taskId}/complete`)
    return res.data
  },

  async getAchievements(patientId: string) {
    const res = await request.get(`/v1/health/${patientId}/achievements`)
    return res.data
  },

  async getAISummary(patientId: string, period: 'week' | 'month' = 'week') {
    const res = await request.get(`/v1/health/${patientId}/ai-summary`, { params: { period } })
    return res.data
  },

  async getComparison(patientId: string, currentPeriod: string, previousPeriod: string) {
    const res = await request.get(`/v1/health/${patientId}/comparison`, {
      params: { current: currentPeriod, previous: previousPeriod }
    })
    return res.data
  },
}

export default healthApi
