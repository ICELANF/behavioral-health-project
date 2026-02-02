/**
 * C端患者 API - 模拟数据接口
 */
import { BEHAVIOR_STAGE_MAP } from '@/constants/index'

// 定义 C 端需要的 Task 类型
export interface Task {
  id: string
  name: string
  description: string
  completed: boolean
  priority: 'high' | 'medium' | 'low'
}

// 模拟的患者端 Dashboard 数据
interface PatientDashboard {
  currentBehaviorStage: keyof typeof BEHAVIOR_STAGE_MAP
  stageProgress: number
  todayTasks: Task[]
}

// 模拟数据
const mockPatientDashboard: PatientDashboard = {
  currentBehaviorStage: 'preparation',
  stageProgress: 60,
  todayTasks: [
    {
      id: 't001',
      name: '记录今日血糖',
      description: '请在早、中、晚三餐后记录',
      completed: false,
      priority: 'high'
    },
    {
      id: 't002',
      name: '完成运动打卡',
      description: '进行30分钟有氧运动',
      completed: true,
      priority: 'medium'
    },
    {
      id: 't003',
      name: '阅读健康小贴士',
      description: '了解糖尿病饮食指南',
      completed: false,
      priority: 'low'
    },
  ],
}

/**
 * 获取患者端 Dashboard 数据 - 从后端引擎获取实时数据
 */
export async function getPatientDashboard(): Promise<PatientDashboard> {
  try {
    const res = await fetch('http://127.0.0.1:8002/api/v1/mp/task/today', {
      headers: { 'Content-Type': 'application/json', 'X-User-ID': '1' }
    })
    const data = await res.json()

    // 将后端任务映射为前端格式
    const stage = (data.stage || 'preparation') as keyof typeof BEHAVIOR_STAGE_MAP
    return {
      currentBehaviorStage: stage,
      stageProgress: Math.round((data.progress || 0) * 100),
      todayTasks: [
        {
          id: data.task_code || 't001',
          name: data.task || '今日健康任务',
          description: data.agent_greeting || '完成每日健康打卡',
          completed: false,
          priority: data.risk_level === 'HIGH' ? 'high' : data.risk_level === 'MEDIUM' ? 'medium' : 'low'
        },
        ...mockPatientDashboard.todayTasks.slice(1)  // 保留其他模拟任务
      ]
    }
  } catch {
    return mockPatientDashboard
  }
}

/**
 * 模拟更新任务完成状态
 * @param taskId 任务ID
 * @param completed 是否完成
 */
export async function updateTaskStatus(taskId: string, completed: boolean): Promise<boolean> {
  return new Promise(resolve => {
    setTimeout(() => {
      const task = mockPatientDashboard.todayTasks.find(t => t.id === taskId)
      if (task) {
        task.completed = completed
        console.log(`Task ${taskId} status updated to: ${completed}`)
        resolve(true)
      } else {
        resolve(false)
      }
    }, 300)
  })
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

const ENGINE_API = 'http://127.0.0.1:8002'
const MP_HEADERS = { 'Content-Type': 'application/json', 'X-User-ID': '1' }

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
  return new Promise(resolve => {
    setTimeout(() => {
      resolve([
        {
          id: 'rec001',
          type: 'exercise',
          title: '饭后散步',
          description: '餐后30分钟进行15分钟轻度散步',
          duration: 15,
          points: 10
        },
        {
          id: 'rec002',
          type: 'diet',
          title: '记录今日饮食',
          description: '拍照记录三餐饮食内容',
          points: 15
        },
        {
          id: 'rec003',
          type: 'education',
          title: '学习血糖管理知识',
          description: '完成今日健康小课堂',
          duration: 5,
          points: 20
        }
      ])
    }, 500)
  })
}
