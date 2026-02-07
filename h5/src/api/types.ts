// API 类型定义

// ── RAG 引用数据 ──

export interface Citation {
  index: number
  label: string
  shortLabel: string
  docTitle: string
  heading: string
  author: string
  source: string
  pageNumber: number | null
  relevanceScore: number
  contentPreview: string
  chunkId: number
  documentId: number
  scope: 'tenant' | 'domain' | 'platform'
  scopeLabel: string
  sourceType: 'knowledge' | 'model'
}

export interface SourceStats {
  knowledgeCount: number
  modelSupplement: boolean
  scopeBreakdown: Record<string, number>
}

export interface RAGData {
  text: string
  hasKnowledge: boolean
  citationsUsed: number[]
  citations: Citation[]
  knowledgeCitations: Citation[]
  hasModelSupplement: boolean
  modelSupplementSections: string[]
  allCitations: Citation[]
  domainsSearched: string[]
  sourceStats: SourceStats
}

// ── 聊天消息 ──

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  expert?: string
  timestamp: number
  tasks?: Task[]
  // RAG 引用数据
  citations?: Citation[]
  hasKnowledge?: boolean
  hasModelSupplement?: boolean
  modelSupplementSections?: string[]
  sourceStats?: SourceStats
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
  agent_id?: string
  tenant_id?: string
}

export interface ChatResponse {
  status: string
  source: string
  answer: string
  conversation_id?: string
  tasks?: Task[]
  rag?: RAGData
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
