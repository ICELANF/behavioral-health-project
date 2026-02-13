/**
 * BehaviorOS — 行为处方前端类型定义
 * ====================================
 * 镜像后端 Pydantic schemas, 确保前后端类型一致
 */

// =====================================================================
// 枚举
// =====================================================================

export enum RxStrategyType {
  CONSCIOUSNESS_RAISING = 'consciousness_raising',
  DRAMATIC_RELIEF = 'dramatic_relief',
  SELF_REEVALUATION = 'self_reevaluation',
  DECISIONAL_BALANCE = 'decisional_balance',
  COGNITIVE_RESTRUCTURING = 'cognitive_restructuring',
  SELF_LIBERATION = 'self_liberation',
  STIMULUS_CONTROL = 'stimulus_control',
  CONTINGENCY_MANAGEMENT = 'contingency_management',
  HABIT_STACKING = 'habit_stacking',
  SYSTEMATIC_DESENSITIZATION = 'systematic_desensitization',
  RELAPSE_PREVENTION = 'relapse_prevention',
  SELF_MONITORING = 'self_monitoring',
}

export enum RxIntensity {
  MINIMAL = 'minimal',
  LOW = 'low',
  MODERATE = 'moderate',
  HIGH = 'high',
  INTENSIVE = 'intensive',
}

export enum CommunicationStyle {
  EMPATHETIC = 'empathetic',
  DATA_DRIVEN = 'data_driven',
  EXPLORATORY = 'exploratory',
  SOCIAL_PROOF = 'social_proof',
  CHALLENGE = 'challenge',
  NEUTRAL = 'neutral',
}

export enum ExpertAgentType {
  BEHAVIOR_COACH = 'behavior_coach',
  METABOLIC_EXPERT = 'metabolic_expert',
  CARDIAC_EXPERT = 'cardiac_expert',
  ADHERENCE_EXPERT = 'adherence_expert',
}

export enum HandoffType {
  STAGE_PROMOTION = 'stage_promotion',
  STAGE_REGRESSION = 'stage_regression',
  DOMAIN_COORDINATION = 'domain_coordination',
  CROSS_CUTTING = 'cross_cutting',
  EMERGENCY_TAKEOVER = 'emergency_takeover',
  SCHEDULED_HANDOFF = 'scheduled_handoff',
}

export enum HandoffStatus {
  INITIATED = 'initiated',
  ACCEPTED = 'accepted',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  REJECTED = 'rejected',
  CANCELLED = 'cancelled',
}

// =====================================================================
// BigFive 人格
// =====================================================================

export interface BigFiveProfile {
  O: number  // 开放性 0-100
  C: number  // 尽责性
  E: number  // 外向性
  A: number  // 宜人性
  N: number  // 神经质
}

// =====================================================================
// 三维输入上下文
// =====================================================================

export interface RxContext {
  user_id: string
  session_id?: string

  // 维度 1: TTM
  ttm_stage: number          // 0-6
  stage_readiness: number    // 0-1
  stage_stability: number    // 0-1

  // 维度 2: 人格
  personality: BigFiveProfile

  // 维度 3: 能力
  capacity_score: number     // 0-1
  self_efficacy: number      // 0-1

  // 附加
  domain_data: Record<string, any>
  active_barriers: string[]
  recent_adherence: number   // 0-1
  risk_level: 'low' | 'normal' | 'elevated' | 'high' | 'critical'
}

// =====================================================================
// 微行动
// =====================================================================

export interface MicroAction {
  action_id: string
  title: string
  description: string
  difficulty: number        // 0-1
  duration_minutes: number
  frequency: string
  trigger_cue?: string
  reward_suggestion?: string
  contraindications?: string[]
}

// =====================================================================
// 处方 DTO
// =====================================================================

export interface RxPrescriptionDTO {
  rx_id: string
  user_id: string
  session_id?: string
  created_at: string

  // 三维坐标
  ttm_stage: number
  personality_dominant: string
  capacity_level: string

  // 处方核心
  primary_strategy: RxStrategyType
  secondary_strategies: RxStrategyType[]
  intensity: RxIntensity
  communication_style: CommunicationStyle

  // 微行动
  micro_actions: MicroAction[]

  // 元数据
  confidence_score: number
  reasoning: string
  contraindications: string[]
  review_in_days: number

  // 来源
  computed_by?: ExpertAgentType
  collaboration_agents?: ExpertAgentType[]
}

// =====================================================================
// API 请求 / 响应
// =====================================================================

export interface ComputeRxRequest {
  context: RxContext
  agent_type?: ExpertAgentType
  force_strategy?: RxStrategyType
  override_intensity?: RxIntensity
}

export interface ComputeRxResponse {
  prescription: RxPrescriptionDTO
  agent_used: ExpertAgentType
  computation_time_ms: number
  warnings: string[]
}

export interface RxListResponse {
  items: RxPrescriptionDTO[]
  total: number
  page: number
  page_size: number
}

export interface StrategyTemplate {
  strategy_type: RxStrategyType
  name_zh: string
  name_en: string
  description: string
  applicable_stages: number[]
  personality_affinity: Record<string, string>
  micro_action_templates: MicroAction[]
}

export interface StrategyTemplateResponse {
  strategies: StrategyTemplate[]
  total: number
}

export interface HandoffRequest {
  user_id: string
  session_id?: string
  source_agent: ExpertAgentType
  target_agent: ExpertAgentType
  handoff_type: HandoffType
  reason: string
  context_snapshot: Record<string, any>
  priority: number
}

export interface HandoffResponse {
  handoff_id: string
  status: HandoffStatus
  source_agent: ExpertAgentType
  target_agent: ExpertAgentType
  created_at: string
}

export interface HandoffLogEntry {
  handoff_id: string
  source_agent: ExpertAgentType
  target_agent: ExpertAgentType
  handoff_type: HandoffType
  status: HandoffStatus
  reason: string
  priority: number
  created_at: string
  completed_at?: string
}

export interface HandoffListResponse {
  items: HandoffLogEntry[]
  total: number
}

export interface CollaborateRequest {
  user_id: string
  session_id?: string
  user_input: {
    message?: string
    device_data?: Record<string, any>
    behavioral_profile?: Record<string, any>
    domain_data?: Record<string, any>
  }
  current_agent?: ExpertAgentType
}

export interface CollaborateResponse {
  scenario: string
  agents_involved: ExpertAgentType[]
  combined_prescription?: RxPrescriptionDTO
  agent_responses: Record<string, any>[]
  conflict_resolution?: Record<string, any>
  execution_time_ms: number
}

export interface AgentStatusEntry {
  agent_type: ExpertAgentType
  name: string
  status: 'active' | 'inactive' | 'error'
  capabilities: string[]
  handled_domains: string[]
  active_sessions: number
  total_prescriptions: number
  avg_confidence: number
  last_active: string
}

export interface AgentStatusResponse {
  agents: AgentStatusEntry[]
  orchestrator_status: 'ready' | 'degraded' | 'down'
  registered_scenarios: string[]
}

// =====================================================================
// UI 辅助类型
// =====================================================================

export const TTM_STAGES: Record<number, { label: string; color: string; description: string }> = {
  0: { label: '前意识期', color: '#bfbfbf', description: '尚未意识到需要改变' },
  1: { label: '意识期', color: '#faad14', description: '开始意识到问题，考虑改变' },
  2: { label: '准备期', color: '#1890ff', description: '计划在近期内采取行动' },
  3: { label: '行动期', color: '#52c41a', description: '已开始改变行为' },
  4: { label: '维持期', color: '#13c2c2', description: '持续保持新行为' },
  5: { label: '巩固期', color: '#722ed1', description: '新行为已基本稳定' },
  6: { label: '终止期', color: '#eb2f96', description: '旧行为完全消退' },
}

export const INTENSITY_CONFIG: Record<RxIntensity, { label: string; color: string; level: number }> = {
  [RxIntensity.MINIMAL]:   { label: '极低', color: '#d9d9d9', level: 1 },
  [RxIntensity.LOW]:       { label: '低',   color: '#bae7ff', level: 2 },
  [RxIntensity.MODERATE]:  { label: '中',   color: '#91d5ff', level: 3 },
  [RxIntensity.HIGH]:      { label: '高',   color: '#40a9ff', level: 4 },
  [RxIntensity.INTENSIVE]: { label: '极高', color: '#096dd9', level: 5 },
}

export const STRATEGY_LABELS: Record<RxStrategyType, string> = {
  [RxStrategyType.CONSCIOUSNESS_RAISING]:     '意识提升',
  [RxStrategyType.DRAMATIC_RELIEF]:           '情感唤醒',
  [RxStrategyType.SELF_REEVALUATION]:         '自我再评价',
  [RxStrategyType.DECISIONAL_BALANCE]:        '决策权衡',
  [RxStrategyType.COGNITIVE_RESTRUCTURING]:   '认知重构',
  [RxStrategyType.SELF_LIBERATION]:           '自我解放',
  [RxStrategyType.STIMULUS_CONTROL]:          '刺激控制',
  [RxStrategyType.CONTINGENCY_MANAGEMENT]:    '强化管理',
  [RxStrategyType.HABIT_STACKING]:            '习惯叠加',
  [RxStrategyType.SYSTEMATIC_DESENSITIZATION]:'系统脱敏',
  [RxStrategyType.RELAPSE_PREVENTION]:        '复发预防',
  [RxStrategyType.SELF_MONITORING]:           '自我监控',
}

export const AGENT_LABELS: Record<ExpertAgentType, { name: string; icon: string; color: string }> = {
  [ExpertAgentType.BEHAVIOR_COACH]:   { name: '行为教练',   icon: '🧭', color: '#1890ff' },
  [ExpertAgentType.METABOLIC_EXPERT]: { name: '代谢专家',   icon: '🔬', color: '#52c41a' },
  [ExpertAgentType.CARDIAC_EXPERT]:   { name: '心脏康复专家', icon: '❤️', color: '#f5222d' },
  [ExpertAgentType.ADHERENCE_EXPERT]: { name: '依从性专家',  icon: '📋', color: '#722ed1' },
}
