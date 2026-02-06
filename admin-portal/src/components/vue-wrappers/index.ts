// ============================================================
// index.ts - Vue包装器统一导出
// 位置: src/components/vue-wrappers/index.ts
// ============================================================

// 专家组件
export { default as DualSignPanelVue } from './DualSignPanelVue.vue'
export { default as CGMChartVue } from './CGMChartVue.vue'
export { default as LogicFlowBridgeVue } from './LogicFlowBridgeVue.vue'

// 页面组件
export { default as JourneyPageVue } from './JourneyPageVue.vue'
export { default as ExpertWorkspaceVue } from './ExpertWorkspaceVue.vue'

// 追踪组件
export { default as DecisionTraceVue } from './DecisionTraceVue.vue'
export { default as TraceGraphVue } from './TraceGraphVue.vue'

// 类型重新导出
export type {
  AuditCase,
  DecisionRules,
  TraceNode,
  TraceSession,
  CGMDataPoint,
  AuditLog,
  PublishResult,
} from '@/types/react-components'
