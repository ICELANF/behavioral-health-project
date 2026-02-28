/**
 * 六级四同道体系 — 等级工具函数
 * 与后端 paths_api._LEVEL_THRESHOLDS 保持一致
 */

export type RoleKey = 'observer' | 'grower' | 'sharer' | 'coach' | 'promoter' | 'supervisor' | 'master' | 'admin'

/** 角色对应等级 */
export const ROLE_LEVEL: Record<RoleKey | string, number> = {
  observer:   1,
  grower:     2,
  sharer:     3,
  coach:      4,
  promoter:   5,
  supervisor: 5,
  master:     6,
  admin:      99,
}

/** 等级对应中文标签 */
export const LEVEL_LABEL: Record<number, string> = {
  1: 'L1 观察者',
  2: 'L2 成长者',
  3: 'L3 分享者',
  4: 'L4 教练',
  5: 'L5 促进师',
  6: 'L6 大师',
}

/** 角色中文名 */
export const ROLE_LABEL: Record<string, string> = {
  observer:   '观察者',
  grower:     '成长者',
  sharer:     '分享者',
  coach:      '教练',
  promoter:   '促进师',
  supervisor: '督导',
  master:     '大师',
  admin:      '管理员',
}

/** 角色颜色 */
export const ROLE_COLOR: Record<string, string> = {
  observer:   '#9ca3af',
  grower:     '#10b981',
  sharer:     '#3b82f6',
  coach:      '#8b5cf6',
  promoter:   '#f59e0b',
  supervisor: '#ec4899',
  master:     '#ef4444',
  admin:      '#111827',
}

/**
 * 成长积分 → 下一级所需积分
 * 对应后端 _LEVEL_THRESHOLDS: L0→L1(100) L1→L2(500) L2→L3(800) L3→L4(1500) L4→L5(3000)
 */
export const LEVEL_THRESHOLDS: Record<number, number> = {
  1: 100,
  2: 500,
  3: 800,
  4: 1500,
  5: 3000,
  6: 0,   // 最高级，无上限
}

/** 当前积分 → 本级起始积分 */
const LEVEL_STARTS: Record<number, number> = {
  1: 0,
  2: 100,
  3: 500,
  4: 800,
  5: 1500,
  6: 3000,
}

/**
 * 计算当前等级进度百分比 (0~100)
 */
export function calcLevelProgress(growthPoints: number, roleLevel: number): number {
  if (roleLevel >= 6) return 100
  const start  = LEVEL_STARTS[roleLevel]  ?? 0
  const target = LEVEL_THRESHOLDS[roleLevel] ?? 100
  const range  = target - start
  if (range <= 0) return 100
  return Math.min(Math.round(((growthPoints - start) / range) * 100), 100)
}

/**
 * 判断角色是否为教练或以上
 */
export function isCoachRole(role: string): boolean {
  return (ROLE_LEVEL[role] ?? 0) >= 4
}

/**
 * 格式化积分显示（超过1000显示 k）
 */
export function formatPoints(pts: number): string {
  if (pts >= 10000) return `${(pts / 10000).toFixed(1)}w`
  if (pts >= 1000)  return `${(pts / 1000).toFixed(1)}k`
  return String(pts)
}
