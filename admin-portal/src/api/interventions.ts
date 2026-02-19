/**
 * 干预包 API 和匹配逻辑
 */
import request from './request'
import type { InterventionPack, TTMStage, RiskLevel, TriggerDomain, CoachLevel } from '@/types'

// 触发标签定义
export const TRIGGER_TAGS = [
  { tag: 'high_glucose', label: '高血糖', domain: 'glucose' as TriggerDomain },
  { tag: 'low_glucose', label: '低血糖', domain: 'glucose' as TriggerDomain },
  { tag: 'glucose_spike', label: '血糖骤升', domain: 'glucose' as TriggerDomain },
  { tag: 'glucose_fluctuation', label: '血糖波动', domain: 'glucose' as TriggerDomain },
  { tag: 'overeating', label: '暴饮暴食', domain: 'diet' as TriggerDomain },
  { tag: 'high_carb', label: '高碳水摄入', domain: 'diet' as TriggerDomain },
  { tag: 'irregular_meals', label: '饮食不规律', domain: 'diet' as TriggerDomain },
  { tag: 'low_activity', label: '活动量不足', domain: 'exercise' as TriggerDomain },
  { tag: 'sedentary', label: '久坐', domain: 'exercise' as TriggerDomain },
  { tag: 'missed_medication', label: '漏服药物', domain: 'medication' as TriggerDomain },
  { tag: 'irregular_medication', label: '用药不规律', domain: 'medication' as TriggerDomain },
  { tag: 'poor_sleep', label: '睡眠质量差', domain: 'sleep' as TriggerDomain },
  { tag: 'insomnia', label: '失眠', domain: 'sleep' as TriggerDomain },
  { tag: 'high_stress', label: '压力过大', domain: 'stress' as TriggerDomain },
  { tag: 'anxiety', label: '焦虑', domain: 'stress' as TriggerDomain }
]

// 任务类型标签映射
export const TASK_CATEGORY_MAP = {
  behavior_experiment: { label: '行为实验', color: '#52c41a' },
  activation: { label: '行为激活', color: '#1890ff' },
  self_monitoring: { label: '自我监测', color: '#faad14' },
  skill_training: { label: '技能训练', color: '#722ed1' }
}

// 教练动作类型映射
export const ACTION_CATEGORY_MAP = {
  education: { label: '健康教育', color: '#1890ff' },
  guidance: { label: '行为指导', color: '#52c41a' },
  coaching: { label: '教练辅导', color: '#722ed1' },
  support: { label: '情感支持', color: '#eb2f96' }
}

/**
 * 获取所有干预包
 */
export async function getAllInterventionPacks(): Promise<InterventionPack[]> {
  const res = await request.get('/v1/interventions')
  return res.data
}

// 教练等级顺序（用于比较）
const COACH_LEVEL_ORDER = ['L0', 'L1', 'L2', 'L3', 'L4']

/**
 * 比较教练等级是否满足要求
 */
export function isCoachLevelSufficient(userLevel: CoachLevel, requiredLevel: CoachLevel): boolean {
  const userIndex = COACH_LEVEL_ORDER.indexOf(userLevel)
  const requiredIndex = COACH_LEVEL_ORDER.indexOf(requiredLevel)
  return userIndex >= requiredIndex
}

/**
 * 匹配结果接口
 */
export interface MatchResult {
  pack: InterventionPack
  matchedActions: InterventionPack['coach_actions']
  canExecute: boolean
  reason?: string
}

/**
 * GET /api/v1/interventions/match
 * 根据触发标签、行为阶段和教练等级匹配干预包
 */
export async function matchInterventionPack(
  trigger_tag: string,
  behavior_stage: TTMStage,
  coach_level?: CoachLevel
): Promise<MatchResult[]> {
  const res = await request.get('/v1/interventions/match', {
    params: { trigger_tag, behavior_stage, coach_level }
  })
  return res.data
}

/**
 * 根据触发标签和行为阶段匹配干预包（支持可选参数）
 */
export async function matchInterventionPacks(
  triggerTag: string,
  behaviorStage?: TTMStage,
  riskLevel?: RiskLevel
): Promise<InterventionPack[]> {
  const res = await request.get('/v1/interventions/match', {
    params: { trigger_tag: triggerTag, behavior_stage: behaviorStage, risk_level: riskLevel }
  })
  return res.data
}

/**
 * 根据 ID 获取干预包
 */
export async function getInterventionPackById(packId: string): Promise<InterventionPack | undefined> {
  const res = await request.get(`/v1/interventions/${packId}`)
  return res.data
}

/**
 * 根据触发域获取干预包
 */
export async function getInterventionPacksByDomain(domain: TriggerDomain): Promise<InterventionPack[]> {
  const res = await request.get('/v1/interventions', { params: { domain } })
  return res.data
}

/**
 * 根据教练等级筛选可执行的干预包
 */
export async function getInterventionPacksByCoachLevel(level: CoachLevel): Promise<InterventionPack[]> {
  const res = await request.get('/v1/interventions', { params: { coach_level: level } })
  return res.data
}
