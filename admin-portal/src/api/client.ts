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
 * 模拟获取患者端 Dashboard 数据
 */
export async function getPatientDashboard(): Promise<PatientDashboard> {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve(mockPatientDashboard)
    }, 500) // 模拟网络延迟
  })
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

export async function getHealthSummary(): Promise<HealthSummary> {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve({
        bloodGlucose: {
          fasting: 6.8,
          postprandial: 9.2,
          trend: 'down'
        },
        weight: {
          current: 75.5,
          target: 70,
          trend: 'down'
        },
        exercise: {
          weeklyMinutes: 150,
          targetMinutes: 150,
          streak: 7
        },
        medication: {
          adherenceRate: 92,
          missedDoses: 2
        }
      })
    }, 500)
  })
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
