/**
 * C端患者 API
 */
import { BEHAVIOR_STAGE_MAP } from '@/constants/index'

export interface Task {
  id: string
  name: string
  description: string
  completed: boolean
  priority: 'high' | 'medium' | 'low'
}

interface PatientDashboard {
  currentBehaviorStage: keyof typeof BEHAVIOR_STAGE_MAP
  stageProgress: number
  todayTasks: Task[]
}

const ENGINE_API = import.meta.env.VITE_ENGINE_API_URL || 'http://127.0.0.1:8002'
const MP_HEADERS = { 'Content-Type': 'application/json', 'X-User-ID': '1' }

export async function getPatientDashboard(): Promise<PatientDashboard> {
  const res = await fetch(`${ENGINE_API}/api/v1/mp/task/today`, {
    headers: MP_HEADERS
  })
  const data = await res.json()
  const stage = (data.stage || 'preparation') as keyof typeof BEHAVIOR_STAGE_MAP
  return {
    currentBehaviorStage: stage,
    stageProgress: Math.round((data.progress || 0) * 100),
    todayTasks: (data.tasks || []).map((t: any) => ({
      id: t.task_code || t.id,
      name: t.task || t.name || '健康任务',
      description: t.description || '',
      completed: t.completed || false,
      priority: t.risk_level === 'HIGH' ? 'high' : t.risk_level === 'MEDIUM' ? 'medium' : 'low' as const,
    })),
  }
}

export async function updateTaskStatus(taskId: string, completed: boolean): Promise<boolean> {
  const res = await fetch(`${ENGINE_API}/api/v1/mp/task/${taskId}/status`, {
    method: 'POST',
    headers: MP_HEADERS,
    body: JSON.stringify({ completed }),
  })
  return res.ok
}

/**
 * 获取用户健康数据摘要
 */
export interface HealthSummary {
  bloodGlucose: {
    fasting: number | null
    postprandial: number | null
    trend: 'up' | 'down' | 'stable'
  }
  weight: {
    current: number
    target: number
    trend: 'up' | 'down' | 'stable'
  }
  exercise: {
    weeklyMinutes: number
    targetMinutes: number
    streak: number
  }
  medication: {
    adherenceRate: number
    missedDoses: number
  }
}

// 上次已知的血糖值（用于计算趋势）
let lastKnownGlucose = 0

export async function getHealthSummary(): Promise<HealthSummary> {
  try {
    // 并行请求后端三个接口
    const [statusRes, stateRes, progressRes] = await Promise.all([
      fetch(`${ENGINE_API}/latest_status`).then(r => r.json()).catch(() => null),
      fetch(`${ENGINE_API}/api/v1/mp/user/state`, { headers: MP_HEADERS }).then(r => r.json()).catch(() => null),
      fetch(`${ENGINE_API}/api/v1/mp/progress/summary`, { headers: MP_HEADERS }).then(r => r.json()).catch(() => null)
    ])

    // 从 latest_status 获取血糖数据
    const currentGlucose = statusRes?.current_glucose || 0
    const history: number[] = statusRes?.history || []

    // 计算趋势
    let glucoseTrend: 'up' | 'down' | 'stable' = 'stable'
    if (lastKnownGlucose > 0 && currentGlucose > 0) {
      if (currentGlucose > lastKnownGlucose + 0.3) glucoseTrend = 'up'
      else if (currentGlucose < lastKnownGlucose - 0.3) glucoseTrend = 'down'
    }
    if (currentGlucose > 0) lastKnownGlucose = currentGlucose

    // 计算餐后血糖（取历史最高值作为餐后参考）
    const recentHistory = history.slice(-5)
    const postprandial = recentHistory.length > 0 ? Math.max(...recentHistory) : null

    // 从 user/state 获取积分和天数
    const points = stateRes?.points || 0
    const dayIndex = stateRes?.day_index || 1

    // 从 progress/summary 获取完成数据
    const totalCompleted = progressRes?.total_completed || 0
    const streakDays = progressRes?.streak_days || 0
    const completionRate = progressRes?.completion_rate || 0

    // 运动量基于完成率估算
    const exerciseMinutes = Math.round(completionRate * 150)

    return {
      bloodGlucose: {
        fasting: currentGlucose > 0 ? currentGlucose : null,
        postprandial: postprandial,
        trend: glucoseTrend
      },
      weight: {
        current: 75.5 - (totalCompleted * 0.1),  // 模拟体重随任务完成减少
        target: 70,
        trend: totalCompleted > 3 ? 'down' : 'stable'
      },
      exercise: {
        weeklyMinutes: exerciseMinutes,
        targetMinutes: 150,
        streak: streakDays
      },
      medication: {
        adherenceRate: Math.round(completionRate * 100) || 85,
        missedDoses: Math.max(0, 7 - totalCompleted)
      }
    }
  } catch {
    // 后端不可用时返回默认值
    return {
      bloodGlucose: { fasting: null, postprandial: null, trend: 'stable' },
      weight: { current: 75.5, target: 70, trend: 'stable' },
      exercise: { weeklyMinutes: 0, targetMinutes: 150, streak: 0 },
      medication: { adherenceRate: 0, missedDoses: 0 }
    }
  }
}

/**
 * 获取推荐任务
 */
export interface RecommendedTask {
  id: string
  type: 'diet' | 'exercise' | 'medication' | 'education' | 'monitoring'
  title: string
  description: string
  duration?: number
  points: number
}

export async function getRecommendedTasks(): Promise<RecommendedTask[]> {
  const res = await fetch(`${ENGINE_API}/api/v1/mp/task/recommended`, {
    headers: MP_HEADERS,
  })
  const data = await res.json()
  return (data.tasks || []).map((t: any) => ({
    id: t.id,
    type: t.type || 'education',
    title: t.title || '',
    description: t.description || '',
    duration: t.duration,
    points: t.points || 0,
  }))
}
