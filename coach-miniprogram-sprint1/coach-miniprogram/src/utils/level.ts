/**
 * 级别工具函数
 * 处理六级体系的颜色/标签/图标/晋级计算
 */

import { ROLE_COLOR_MAP, ROLE_LABEL_MAP, ROLE_LEVEL_MAP } from '@/stores/user'

// ─── 晋级阈值（与后端 paths_api.py::_LEVEL_THRESHOLDS 对齐）─
export const LEVEL_THRESHOLDS = {
  L1: { growth: 100,  contribution: 0,    influence: 0,   exam: false, companions: 0 },
  L2: { growth: 500,  contribution: 50,   influence: 0,   exam: false, companions: 0 },
  L3: { growth: 800,  contribution: 200,  influence: 50,  exam: true,  companions: 4 },
  L4: { growth: 1500, contribution: 600,  influence: 200, exam: true,  companions: 4 },
  L5: { growth: 3000, contribution: 1500, influence: 600, exam: true,  companions: 4 }
}

// ─── 积分来源中文名 ─────────────────────────────────────────
export const POINT_SOURCE_LABEL: Record<string, string> = {
  quiz:                   '测验通过',
  complete:               '完成学习',
  share:                  '分享内容',
  comment:                '发表评论',
  login:                  '每日登录',
  streak:                 '连续打卡',
  coach_mentor:           '带教学员',
  knowledge_contribution: '知识投稿'
}

// ─── 工具函数 ────────────────────────────────────────────────

/** 获取角色颜色 */
export function getRoleColor(role: string): string {
  return ROLE_COLOR_MAP[role] || '#8c8c8c'
}

/** 获取角色标签 */
export function getRoleLabel(role: string): string {
  return ROLE_LABEL_MAP[role] || '未知'
}

/** 获取角色等级数字 */
export function getRoleLevel(role: string): number {
  return ROLE_LEVEL_MAP[role as keyof typeof ROLE_LEVEL_MAP] || 1
}

/** 获取角色对应的下一级 */
export function getNextRole(role: string): string | null {
  const map: Record<string, string> = {
    observer: 'grower',
    grower:   'sharer',
    sharer:   'coach',
    coach:    'promoter',
    promoter: 'master'
  }
  return map[role] || null
}

/** 计算晋级进度（0-100） */
export function calcPromotionProgress(
  currentRole: string,
  growth: number,
  contribution: number,
  influence: number
): number {
  const nextRole = getNextRole(currentRole)
  if (!nextRole) return 100

  const levelKey = `L${getRoleLevel(nextRole)}` as keyof typeof LEVEL_THRESHOLDS
  const threshold = LEVEL_THRESHOLDS[levelKey]
  if (!threshold) return 0

  const g = threshold.growth      > 0 ? Math.min(growth / threshold.growth, 1)           : 1
  const c = threshold.contribution> 0 ? Math.min(contribution / threshold.contribution, 1): 1
  const i = threshold.influence   > 0 ? Math.min(influence / threshold.influence, 1)      : 1

  return Math.round(((g + c + i) / 3) * 100)
}

/** 格式化积分数字（1000 → 1k） */
export function formatPoints(n: number): string {
  if (n >= 10000) return `${(n / 10000).toFixed(1)}w`
  if (n >= 1000)  return `${(n / 1000).toFixed(1)}k`
  return String(n)
}

/** TTM 阶段中文标签（学员侧友好表述） */
export const TTM_LABELS: Record<string, { label: string; desc: string; color: string }> = {
  S0: { label: '觉察中',   desc: '正在了解行为健康',   color: '#8c8c8c' },
  S1: { label: '思考中',   desc: '开始考虑做出改变',   color: '#0ea5e9' },
  S2: { label: '准备中',   desc: '已在准备行动',       color: '#0ea5e9' },
  S3: { label: '初步行动', desc: '开始尝试新行为',     color: '#10b981' },
  S4: { label: '积极尝试', desc: '坚持践行新习惯',     color: '#10b981' },
  S5: { label: '规律实践', desc: '习惯已成自然',       color: '#3b82f6' },
  S6: { label: '已内化',   desc: '成为生活方式',       color: '#3b82f6' }
}

/** 连续打卡激励文案 */
export function getStreakMessage(days: number): string {
  if (days === 0)   return '今天开始打卡吧 💪'
  if (days < 3)     return `已连续 ${days} 天，继续加油！`
  if (days < 7)     return `已连续 ${days} 天，状态很好！🔥`
  if (days < 30)    return `已连续 ${days} 天，习惯正在形成！⭐`
  if (days < 100)   return `已连续 ${days} 天，你真的很厉害！🏆`
  return `已连续 ${days} 天，已是行为健康榜样！🌟`
}

/** 格式化学习时长 */
export function formatMinutes(minutes: number): string {
  if (minutes < 60) return `${minutes}分钟`
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return m > 0 ? `${h}小时${m}分钟` : `${h}小时`
}
