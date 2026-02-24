/**
 * 行为处方 (Behavioral Prescription) 类型定义
 */

export interface RxPrescription {
  id: string
  user_id?: number
  target_behavior: string
  frequency_dose: string
  time_place: string
  trigger_cue: string
  obstacle_plan: string
  support_resource: string
  domain: string
  difficulty_level: string
  cultivation_stage: string
  status: string
  approved_by_review?: string
  created_at: string | null
}

export interface MicroAction {
  action: string
  difficulty: number
  trigger: string
  duration_min: number
  frequency: string
  domain: string
}

/** TTM 阶段中文映射 */
export const TTM_STAGES: Record<string, string> = {
  S0: '前意识期',
  S1: '意识期',
  S2: '准备期',
  S3: '行动期',
  S4: '维持期',
  S5: '巩固期',
  S6: '终止期',
  startup: '启动期',
}

/** 策略类型中文映射 */
export const STRATEGY_LABELS: Record<string, string> = {
  consciousness_raising: '意识唤醒',
  dramatic_relief: '戏剧性解脱',
  self_reevaluation: '自我再评价',
  decisional_balance: '决策平衡',
  cognitive_restructuring: '认知重构',
  self_liberation: '自我解放',
  stimulus_control: '刺激控制',
  contingency_management: '强化管理',
  habit_stacking: '习惯叠加',
  systematic_desensitization: '系统脱敏',
  relapse_prevention: '复发预防',
  self_monitoring: '自我监控',
}

/** 强度中文映射 */
export const INTENSITY_LABELS: Record<string, string> = {
  minimal: '极低',
  low: '低',
  moderate: '中等',
  high: '高',
  intensive: '强化',
  easy: '简单',
  medium: '中等',
  hard: '困难',
}

/** 领域中文映射 */
export const DOMAIN_LABELS: Record<string, string> = {
  nutrition: '营养',
  exercise: '运动',
  sleep: '睡眠',
  emotion: '情绪',
  glucose: '血糖',
  cardiac: '心血管',
  general: '综合',
}
