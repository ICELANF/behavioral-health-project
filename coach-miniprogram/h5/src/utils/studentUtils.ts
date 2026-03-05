/**
 * Shared student/risk/avatar utilities — single source of truth.
 * Replaces 18+ duplicate definitions across pages.
 */

const AVATAR_COLORS = [
  '#3498DB', '#E67E22', '#27AE60', '#9B59B6',
  '#E74C3C', '#1ABC9C', '#F39C12', '#2980B9',
]

export function avatarColor(name: string): string {
  if (!name) return '#8E99A4'
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash)
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length]
}

export function parseRisk(r: any): number {
  return parseInt(String(r ?? '0').replace(/\D/g, '') || '0')
}

export function riskColor(level: number | string): string {
  const n = typeof level === 'string' ? parseRisk(level) : (level || 0)
  if (n >= 4) return '#C0392B'
  if (n >= 3) return '#E74C3C'
  if (n >= 2) return '#E67E22'
  if (n >= 1) return '#F39C12'
  return '#27AE60'
}

export function riskBg(level: number | string): string {
  const n = typeof level === 'string' ? parseRisk(level) : (level || 0)
  if (n >= 4) return '#FDEDEC'
  if (n >= 3) return '#FFF0F0'
  if (n >= 2) return '#FFF8F0'
  if (n >= 1) return '#FEFCE8'
  return '#F0FFF4'
}

export function riskColorText(level: number | string): string {
  const n = typeof level === 'string' ? parseRisk(level) : (level || 0)
  if (n >= 3) return '#E74C3C'
  if (n >= 2) return '#E67E22'
  return '#27AE60'
}

export function normalizeStudent(s: any): any {
  return {
    ...s,
    id: s.id || s.user_id,
    name: s.name || s.full_name || s.username || '未知',
    stage: (s.ttm_stage && s.ttm_stage !== 'unknown') ? s.ttm_stage
      : (s.stage && s.stage !== 'unknown') ? s.stage : '未评估',
    stage_label: s.stage_label || s.stage || '',
    risk_level: parseRisk(s.risk_level),
  }
}
