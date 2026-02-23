/**
 * 学员多维分类 — composable
 *
 * 提供4维分类选项定义、快捷预设、标签颜色/样式工具函数。
 */
import { reactive, ref, computed } from 'vue'

// ── 分类过滤器 ──

export interface ClassificationFilter {
  behavior?: string
  needs?: string
  risk?: string
  activity?: string
  priority?: string
  sort_by: string
}

// ── 维度选项定义 ──

export const BEHAVIOR_OPTIONS = [
  { label: '前意识期', value: 'precontemplation', color: '#8c8c8c' },
  { label: '意识期', value: 'contemplation', color: '#faad14' },
  { label: '准备期', value: 'preparation', color: '#1890ff' },
  { label: '行动期', value: 'action', color: '#52c41a' },
  { label: '维持期', value: 'maintenance', color: '#389e0d' },
  { label: '复发', value: 'relapse', color: '#ff4d4f' },
  { label: '成长', value: 'growth', color: '#722ed1' },
  { label: '倡导', value: 'advocacy', color: '#eb2f96' },
  { label: '未评估', value: 'unassessed', color: '#d9d9d9' },
]

export const NEEDS_OPTIONS = [
  { label: '代谢管理', value: 'metabolic', color: '#fa541c' },
  { label: '情绪调节', value: 'emotional', color: '#722ed1' },
  { label: '饮食营养', value: 'nutrition', color: '#fa8c16' },
  { label: '运动锻炼', value: 'exercise', color: '#52c41a' },
  { label: '依从管理', value: 'adherence', color: '#1890ff' },
  { label: '综合', value: 'general', color: '#d9d9d9' },
]

export const RISK_OPTIONS = [
  { label: '危机', value: 'crisis', color: '#ff4d4f' },
  { label: '高风险', value: 'high', color: '#fa541c' },
  { label: '中风险', value: 'moderate', color: '#faad14' },
  { label: '低风险', value: 'low', color: '#52c41a' },
  { label: '正常', value: 'normal', color: '#d9d9d9' },
]

export const ACTIVITY_OPTIONS = [
  { label: '非常活跃', value: 'highly_active', color: '#52c41a' },
  { label: '活跃', value: 'active', color: '#389e0d' },
  { label: '一般', value: 'moderate', color: '#faad14' },
  { label: '不活跃', value: 'inactive', color: '#fa541c' },
  { label: '沉寂', value: 'dormant', color: '#8c8c8c' },
]

export const PRIORITY_OPTIONS = [
  { label: '紧急', value: 'urgent', color: '#ff4d4f', bg: '#fff2f0' },
  { label: '重要', value: 'important', color: '#fa8c16', bg: '#fff7e6' },
  { label: '常规', value: 'normal', color: '#1890ff', bg: '#e6f7ff' },
  { label: '例行', value: 'routine', color: '#8c8c8c', bg: '#fafafa' },
]

// ── 快捷预设 ──

export const PRESETS = [
  { label: '紧急分诊', filters: { risk: 'crisis,high', sort_by: 'risk' } },
  { label: '回退预警', filters: { behavior: 'relapse', activity: 'inactive,dormant', sort_by: 'priority' } },
  { label: '可推进', filters: { behavior: 'preparation,action', activity: 'active,highly_active', sort_by: 'stage' } },
  { label: '情绪关注', filters: { needs: 'emotional', sort_by: 'priority' } },
  { label: '新学员', filters: { behavior: 'unassessed', sort_by: 'activity' } },
]

// ── 维度定义 (供 FilterBar 遍历) ──

export const DIMENSIONS = [
  { key: 'behavior', label: '行为阶段', options: BEHAVIOR_OPTIONS },
  { key: 'needs', label: '需求类型', options: NEEDS_OPTIONS },
  { key: 'risk', label: '风险等级', options: RISK_OPTIONS },
  { key: 'activity', label: '活跃度', options: ACTIVITY_OPTIONS },
]

// ── Label helpers ──

const _optionMap = new Map<string, Map<string, { label: string; color: string }>>()

function _buildMap() {
  if (_optionMap.size > 0) return
  for (const dim of DIMENSIONS) {
    const m = new Map<string, { label: string; color: string }>()
    for (const opt of dim.options) {
      m.set(opt.value, { label: opt.label, color: opt.color })
    }
    _optionMap.set(dim.key, m)
  }
  const pm = new Map<string, { label: string; color: string }>()
  for (const opt of PRIORITY_OPTIONS) {
    pm.set(opt.value, { label: opt.label, color: opt.color })
  }
  _optionMap.set('priority', pm)
}

export function getTagColor(dimension: string, value: string): string {
  _buildMap()
  return _optionMap.get(dimension)?.get(value)?.color || '#d9d9d9'
}

export function getDimensionLabel(dimension: string): string {
  const labels: Record<string, string> = {
    behavior: '行为阶段', needs: '需求类型', risk: '风险等级', activity: '活跃度', priority: '优先级',
  }
  return labels[dimension] || dimension
}

export function getValueLabel(dimension: string, value: string): string {
  _buildMap()
  return _optionMap.get(dimension)?.get(value)?.label || value
}

export function getPriorityStyle(bucket: string): { color: string; bg: string } {
  const opt = PRIORITY_OPTIONS.find(o => o.value === bucket)
  return opt ? { color: opt.color, bg: opt.bg } : { color: '#8c8c8c', bg: '#fafafa' }
}

// ── Composable ──

export function useStudentClassification() {
  const filters = reactive<ClassificationFilter>({ sort_by: 'priority' })
  const activePreset = ref<string | null>(null)

  function applyPreset(preset: typeof PRESETS[0]) {
    // Clear existing
    filters.behavior = undefined
    filters.needs = undefined
    filters.risk = undefined
    filters.activity = undefined
    filters.priority = undefined
    // Apply preset filters
    Object.assign(filters, preset.filters)
    activePreset.value = preset.label
  }

  function clearFilters() {
    filters.behavior = undefined
    filters.needs = undefined
    filters.risk = undefined
    filters.activity = undefined
    filters.priority = undefined
    filters.sort_by = 'priority'
    activePreset.value = null
  }

  function setFilter(dimension: string, value: string) {
    ;(filters as any)[dimension] = value || undefined
    activePreset.value = null
  }

  const activeFilterCount = computed(() => {
    let count = 0
    if (filters.behavior) count++
    if (filters.needs) count++
    if (filters.risk) count++
    if (filters.activity) count++
    if (filters.priority) count++
    return count
  })

  const activeFilters = computed(() => {
    const result: Record<string, string> = {}
    if (filters.behavior) result.behavior = filters.behavior
    if (filters.needs) result.needs = filters.needs
    if (filters.risk) result.risk = filters.risk
    if (filters.activity) result.activity = filters.activity
    if (filters.priority) result.priority = filters.priority
    return result
  })

  return {
    filters,
    activePreset,
    activeFilterCount,
    activeFilters,
    applyPreset,
    clearFilters,
    setFilter,
    getTagColor,
    getValueLabel,
    getDimensionLabel,
    getPriorityStyle,
    PRESETS,
    DIMENSIONS,
    BEHAVIOR_OPTIONS,
    NEEDS_OPTIONS,
    RISK_OPTIONS,
    ACTIVITY_OPTIONS,
    PRIORITY_OPTIONS,
  }
}
