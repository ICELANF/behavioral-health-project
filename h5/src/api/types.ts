// API 类型定义

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  expert?: string
  timestamp: number
  tasks?: Task[]
}

export interface Task {
  id: number
  content: string
  difficulty: 1 | 2 | 3 | 4 | 5
  type: 'mental' | 'nutrition' | 'exercise' | 'tcm'
  completed: boolean
  expert?: string
}

export interface ChatRequest {
  user_id: string
  message: string
  mode?: 'dify' | 'ollama'
  efficacy_score?: number
  wearable_data?: WearableData
}

export interface ChatResponse {
  status: string
  source: string
  answer: string
  conversation_id?: string
  tasks?: Task[]
}

export interface WearableData {
  hr?: number
  steps?: number
  sleep_hours?: number
  hrv?: number
}

export interface Expert {
  id: string
  name: string
  role: string
  avatar?: string
}

export interface UserState {
  id: string
  name: string
  efficacy_score: number
  current_expert: string
}

export interface DashboardData {
  overall_score: number
  stress_score: number
  fatigue_score: number
  trend: TrendData[]
  risk_level: 'low' | 'medium' | 'high'
  recommendations: string[]
}

export interface TrendData {
  date: string
  score: number
}
