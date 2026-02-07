/**
 * Agent 元数据 (前端静态配置)
 */
export const AGENT_META: Record<string, { name: string; avatar: string; category: string }> = {
  sleep:         { name: '睡眠管理', avatar: '🌙', category: '专科' },
  glucose:       { name: '血糖管理', avatar: '📊', category: '专科' },
  stress:        { name: '压力管理', avatar: '🧘', category: '专科' },
  mental:        { name: '心理支持', avatar: '💚', category: '专科' },
  nutrition:     { name: '营养指导', avatar: '🥗', category: '专科' },
  exercise:      { name: '运动指导', avatar: '🏃', category: '专科' },
  tcm:           { name: '中医养生', avatar: '🌿', category: '专科' },
  crisis:        { name: '安全守护', avatar: '🛡️', category: '系统' },
  motivation:    { name: '动机激发', avatar: '🔥', category: '专科' },
  behavior_rx:   { name: '行为处方', avatar: '🎯', category: '整合' },
  weight:        { name: '体重管理', avatar: '⚖️', category: '整合' },
  cardiac_rehab: { name: '心脏康复', avatar: '❤️', category: '整合' },
}
