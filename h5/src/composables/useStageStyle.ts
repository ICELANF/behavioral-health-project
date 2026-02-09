/**
 * BHP 阶段样式 Composable
 * 用途: 在 Vue 组件中快速获取阶段对应的 CSS 类名和配置
 * 
 * 使用:
 *   import { useStageStyle } from '@/composables/useStageStyle'
 *   const { stageKey, stageLabel, stageIcon, headerClass } = useStageStyle('ACTION')
 */

import { computed, type Ref, unref } from 'vue'

export type UIStage = 'AWARENESS' | 'ACTION' | 'STABILIZATION' | 'RELAPSE'
export type TTMStage = 'S0' | 'S1' | 'S2' | 'S3' | 'S4' | 'S5' | 'S6'

interface StageStyleConfig {
  key: string
  label: string
  icon: string
  description: string
  taskTitle: string
  encouragement: string
  gradientFrom: string
  gradientTo: string
  textColor: string
}

const STAGE_CONFIG: Record<UIStage, StageStyleConfig> = {
  AWARENESS: {
    key: 'awareness',
    label: '觉察者',
    icon: '👁️',
    description: '看见，就是改变的开始。',
    taskTitle: '今天只需要记录，不需要改变',
    encouragement: '觉察本身就是力量，你做得很好。',
    gradientFrom: '#7dd3fc',
    gradientTo: '#38bdf8',
    textColor: '#0c4a6e',
  },
  ACTION: {
    key: 'action',
    label: '行动者',
    icon: '🚀',
    description: '你正在真实的生活中迈出步伐。',
    taskTitle: '今天只做这一件事',
    encouragement: '每一个小行动都在重塑你的生活。',
    gradientFrom: '#6ee7b7',
    gradientTo: '#34d399',
    textColor: '#065f46',
  },
  STABILIZATION: {
    key: 'stable',
    label: '稳定者',
    icon: '⚖️',
    description: '节奏感比爆发力更重要。',
    taskTitle: '保持你的节奏',
    encouragement: '稳定的你，正在创造持久的改变。',
    gradientFrom: '#60a5fa',
    gradientTo: '#3b82f6',
    textColor: '#1e40af',
  },
  RELAPSE: {
    key: 'relapse',
    label: '调整者',
    icon: '🔄',
    description: '暂停是为了更好地出发。',
    taskTitle: '做一件最小的事来找回感觉',
    encouragement: '调整不是失败，是成长的一部分。',
    gradientFrom: '#fcd34d',
    gradientTo: '#fbbf24',
    textColor: '#92400e',
  },
}

/** TTM7 → UI4 阶段映射 */
const TTM_TO_UI: Record<TTMStage, UIStage> = {
  S0: 'AWARENESS',
  S1: 'AWARENESS',
  S2: 'AWARENESS',
  S3: 'ACTION',
  S4: 'ACTION',
  S5: 'STABILIZATION',
  S6: 'STABILIZATION',
}

/**
 * 将 TTM7 阶段转换为 UI 阶段
 */
export function mapTTMToUI(ttmStage: TTMStage, isRelapse = false): UIStage {
  if (isRelapse) return 'RELAPSE'
  return TTM_TO_UI[ttmStage] || 'AWARENESS'
}

/**
 * 主 Composable: 根据阶段返回所有样式相关属性
 */
export function useStageStyle(stage: UIStage | Ref<UIStage>) {
  const config = computed(() => {
    const s = unref(stage)
    return STAGE_CONFIG[s] || STAGE_CONFIG.AWARENESS
  })

  return {
    // 基础属性
    stageKey: computed(() => config.value.key),
    stageLabel: computed(() => config.value.label),
    stageIcon: computed(() => config.value.icon),
    stageDescription: computed(() => config.value.description),
    stageTaskTitle: computed(() => config.value.taskTitle),
    stageEncouragement: computed(() => config.value.encouragement),

    // 颜色 (用于 :style 绑定)
    gradientFrom: computed(() => config.value.gradientFrom),
    gradientTo: computed(() => config.value.gradientTo),
    textColor: computed(() => config.value.textColor),
    gradient: computed(() =>
      `linear-gradient(135deg, ${config.value.gradientFrom} 0%, ${config.value.gradientTo} 100%)`
    ),

    // CSS 类名 (用于 :class 绑定)
    headerClass: computed(() => `bhp-stage-header--${config.value.key}`),
    taskClass: computed(() => `bhp-task-card--${config.value.key}`),
    progressClass: computed(() => `bhp-progress__bar--${config.value.key}`),
    dotClass: computed(() => `bhp-student-row__stage--${config.value.key}`),

    // 完整配置 (需要时)
    fullConfig: config,
  }
}

/**
 * 风险等级样式辅助
 */
export function useRiskStyle(level: string) {
  const map: Record<string, { class: string; label: string }> = {
    critical: { class: 'bhp-risk--critical', label: '极高风险' },
    high:     { class: 'bhp-risk--high',     label: '高风险' },
    moderate: { class: 'bhp-risk--moderate',  label: '中等风险' },
    low:      { class: 'bhp-risk--low',       label: '低风险' },
  }
  return map[level] || map.low
}

/**
 * 签名状态样式辅助
 */
export function useSignStatus(status: string) {
  const map: Record<string, { class: string; label: string }> = {
    pending:  { class: 'bhp-sign-status--pending',  label: '待签核' },
    approved: { class: 'bhp-sign-status--approved', label: '已通过' },
    rejected: { class: 'bhp-sign-status--rejected', label: '已驳回' },
  }
  return map[status] || map.pending
}
