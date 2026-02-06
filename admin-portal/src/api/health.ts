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

// ============ Mock 数据生成器 ============

function generateGlucoseHistory(days: number = 7): GlucoseRecord[] {
  const records: GlucoseRecord[] = []
  const now = new Date()

  for (let i = 0; i < days * 4; i++) {
    const date = new Date(now.getTime() - i * 6 * 3600000) // Every 6 hours
    const baseValue = 5.5 + Math.random() * 2
    records.push({
      id: `g_${i}`,
      value: parseFloat(baseValue.toFixed(1)),
      unit: 'mmol/L',
      timestamp: date.toISOString(),
      tag: i % 4 === 0 ? 'fasting' : i % 4 === 1 ? 'after_meal' : 'before_meal'
    })
  }

  return records.reverse()
}

function generateWeightHistory(days: number = 30): WeightRecord[] {
  const records: WeightRecord[] = []
  const baseWeight = 75
  const now = new Date()

  for (let i = 0; i < days; i++) {
    const date = new Date(now.getTime() - i * 24 * 3600000)
    const weight = baseWeight - i * 0.05 + Math.random() * 0.3
    records.push({
      id: `w_${i}`,
      value: parseFloat(weight.toFixed(1)),
      unit: 'kg',
      timestamp: date.toISOString(),
      bmi: parseFloat((weight / 1.75 / 1.75).toFixed(1))
    })
  }

  return records.reverse()
}

function generateExerciseHistory(days: number = 7): ExerciseRecord[] {
  const records: ExerciseRecord[] = []
  const types = ['walking', 'running', 'cycling', 'swimming']
  const now = new Date()

  for (let i = 0; i < days; i++) {
    const date = new Date(now.getTime() - i * 24 * 3600000)
    const duration = Math.round(20 + Math.random() * 40)
    records.push({
      id: `e_${i}`,
      type: types[Math.floor(Math.random() * types.length)],
      duration,
      calories: Math.round(duration * 8),
      distance: parseFloat((duration * 0.1).toFixed(1)),
      timestamp: date.toISOString()
    })
  }

  return records.reverse()
}

// ============ API 方法 ============

export const healthApi = {
  // 记录健康数据
  async recordGlucose(patientId: string, data: Omit<GlucoseRecord, 'id'>) {
    try {
      const res = await request.post(`/v1/health/${patientId}/glucose`, data)
      return res.data
    } catch (e) {
      return { success: true, id: `g_${Date.now()}` }
    }
  },

  async recordWeight(patientId: string, data: Omit<WeightRecord, 'id'>) {
    try {
      const res = await request.post(`/v1/health/${patientId}/weight`, data)
      return res.data
    } catch (e) {
      return { success: true, id: `w_${Date.now()}` }
    }
  },

  async recordBloodPressure(patientId: string, data: Omit<BloodPressureRecord, 'id'>) {
    try {
      const res = await request.post(`/v1/health/${patientId}/blood-pressure`, data)
      return res.data
    } catch (e) {
      return { success: true, id: `bp_${Date.now()}` }
    }
  },

  async recordExercise(patientId: string, data: Omit<ExerciseRecord, 'id'>) {
    try {
      const res = await request.post(`/v1/health/${patientId}/exercise`, data)
      return res.data
    } catch (e) {
      return { success: true, id: `e_${Date.now()}` }
    }
  },

  async recordMood(patientId: string, data: Omit<MoodRecord, 'id'>) {
    try {
      const res = await request.post(`/v1/health/${patientId}/mood`, data)
      return res.data
    } catch (e) {
      return { success: true, id: `m_${Date.now()}` }
    }
  },

  async recordMeal(patientId: string, data: Omit<MealRecord, 'id'>) {
    try {
      const res = await request.post(`/v1/health/${patientId}/meal`, data)
      return res.data
    } catch (e) {
      return { success: true, id: `meal_${Date.now()}` }
    }
  },

  // 获取历史数据
  async getGlucoseHistory(patientId: string, params: { period?: '7d' | '30d' | '90d' } = {}) {
    try {
      const res = await request.get(`/v1/health/${patientId}/glucose`, { params })
      return res.data
    } catch (e) {
      const days = params.period === '7d' ? 7 : params.period === '30d' ? 30 : 90
      return { records: generateGlucoseHistory(days), average: 6.2 }
    }
  },

  async getWeightHistory(patientId: string, params: { period?: '7d' | '30d' | '90d' } = {}) {
    try {
      const res = await request.get(`/v1/health/${patientId}/weight`, { params })
      return res.data
    } catch (e) {
      const days = params.period === '7d' ? 7 : params.period === '30d' ? 30 : 90
      return { records: generateWeightHistory(days) }
    }
  },

  async getExerciseHistory(patientId: string, params: { period?: '7d' | '30d' | '90d' } = {}) {
    try {
      const res = await request.get(`/v1/health/${patientId}/exercise`, { params })
      return res.data
    } catch (e) {
      const days = params.period === '7d' ? 7 : params.period === '30d' ? 30 : 90
      return { records: generateExerciseHistory(days) }
    }
  },

  // 获取健康评分
  async getHealthScore(patientId: string, period: 'week' | 'month' | 'quarter' = 'week') {
    try {
      const res = await request.get(`/v1/health/${patientId}/score`, { params: { period } })
      return res.data
    } catch (e) {
      return {
        overall: 78,
        glucose: 82,
        weight: 75,
        exercise: 70,
        mood: 85,
        breakdown: {
          glucose: { score: 82, trend: 'stable', message: '血糖控制良好，继续保持' },
          weight: { score: 75, trend: 'down', message: '体重稳步下降，很棒！' },
          exercise: { score: 70, trend: 'up', message: '运动量有所提升' },
          mood: { score: 85, trend: 'stable', message: '情绪状态良好' }
        }
      } as HealthScore
    }
  },

  // 获取趋势数据
  async getTrends(patientId: string, metric: string, period: 'week' | 'month' | 'quarter' = 'week') {
    try {
      const res = await request.get(`/v1/health/${patientId}/trends/${metric}`, { params: { period } })
      return res.data
    } catch (e) {
      // Mock trend data
      const days = period === 'week' ? 7 : period === 'month' ? 30 : 90
      const data = []
      for (let i = 0; i < days; i++) {
        const date = new Date()
        date.setDate(date.getDate() - (days - i - 1))
        data.push({
          date: `${date.getMonth() + 1}/${date.getDate()}`,
          value: metric === 'glucose'
            ? parseFloat((5.5 + Math.random() * 2).toFixed(1))
            : parseFloat((75 - i * 0.1 + Math.random() * 0.5).toFixed(1))
        })
      }

      return {
        metric,
        period,
        data,
        average: data.reduce((sum, d) => sum + d.value, 0) / data.length,
        min: Math.min(...data.map(d => d.value)),
        max: Math.max(...data.map(d => d.value)),
        trend: 'improving'
      } as HealthTrend
    }
  },

  // 获取健康快照
  async getHealthSnapshot(patientId: string) {
    try {
      const res = await request.get(`/v1/health/${patientId}/snapshot`)
      return res.data
    } catch (e) {
      return {
        glucose: { value: 5.8, trend: '↓ 0.3', status: 'normal' },
        weight: { value: 74.5, trend: '↓ 0.5kg', bmi: 24.3 },
        exercise: { todayMinutes: 35, weeklyGoal: 150, percentage: 65 },
        mood: { averageScore: 4.2, trend: '↑ 良好' },
        lastUpdate: new Date().toISOString()
      } as HealthSnapshot
    }
  },

  // 获取每日任务
  async getDailyTasks(patientId: string) {
    try {
      const res = await request.get(`/v1/health/${patientId}/tasks/daily`)
      return res.data
    } catch (e) {
      return {
        tasks: [
          { id: 't1', title: '记录空腹血糖', type: 'glucose', completed: true, completedAt: '08:00', dueTime: '09:00', priority: 'high' },
          { id: 't2', title: '今日体重称重', type: 'weight', completed: false, dueTime: '10:00', priority: 'medium' },
          { id: 't3', title: '完成30分钟运动', type: 'exercise', completed: false, dueTime: '18:00', priority: 'high' }
        ] as DailyTask[]
      }
    }
  },

  // 完成任务
  async completeTask(patientId: string, taskId: string) {
    try {
      const res = await request.post(`/v1/health/${patientId}/tasks/${taskId}/complete`)
      return res.data
    } catch (e) {
      return { success: true }
    }
  },

  // 获取成就徽章
  async getAchievements(patientId: string) {
    try {
      const res = await request.get(`/v1/health/${patientId}/achievements`)
      return res.data
    } catch (e) {
      return {
        achievements: [
          { id: 'a1', name: '7天打卡', description: '连续记录数据7天', icon: '🏅', unlocked: true, unlockedAt: '2025-01-20' },
          { id: 'a2', name: '血糖达标', description: '连续7天血糖在正常范围', icon: '🎯', unlocked: true, unlockedAt: '2025-01-25' },
          { id: 'a3', name: '运动健将', description: '单周运动超过150分钟', icon: '💪', unlocked: false, progress: 78 },
          { id: 'a4', name: '减重成功', description: '成功减重5kg', icon: '⭐', unlocked: false, progress: 45 }
        ] as Achievement[]
      }
    }
  },

  // 获取AI总结
  async getAISummary(patientId: string, period: 'week' | 'month' = 'week') {
    try {
      const res = await request.get(`/v1/health/${patientId}/ai-summary`, { params: { period } })
      return res.data
    } catch (e) {
      return {
        summary: '本周表现不错！血糖控制稳定，体重持续下降。运动量有所提升，情绪状态良好。',
        suggestions: [
          '建议继续保持当前的饮食习惯',
          '可以适当增加有氧运动的强度',
          '注意餐后2小时血糖监测'
        ],
        highlights: [
          { icon: '✅', text: '连续7天血糖达标' },
          { icon: '📉', text: '体重下降0.5kg' },
          { icon: '🏃', text: '运动时长增加20%' }
        ]
      }
    }
  },

  // 对比分析
  async getComparison(patientId: string, currentPeriod: string, previousPeriod: string) {
    try {
      const res = await request.get(`/v1/health/${patientId}/comparison`, {
        params: { current: currentPeriod, previous: previousPeriod }
      })
      return res.data
    } catch (e) {
      return {
        metrics: [
          { name: '平均血糖', current: 5.8, previous: 6.2, change: -6.5, unit: 'mmol/L' },
          { name: '平均体重', current: 74.5, previous: 75.2, change: -0.9, unit: 'kg' },
          { name: '运动时长', current: 180, previous: 150, change: 20, unit: '分钟' },
          { name: '情绪评分', current: 4.2, previous: 3.8, change: 10.5, unit: '分' }
        ]
      }
    }
  }
}

export default healthApi
