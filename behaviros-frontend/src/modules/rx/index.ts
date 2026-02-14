/**
 * BehaviorOS — 行为处方 UI 模块入口
 * ====================================
 * 
 * 安装步骤:
 * 1. 将整个 rx-ui/ 目录复制到 frontend/src/modules/rx/
 * 2. 在主路由中导入: import { rxRoutes } from '@/modules/rx/router/rx-routes'
 * 3. 在 Pinia 中注册: import { useRxStore } from '@/modules/rx/stores/rxStore'
 * 4. 在菜单中添加: import { rxMenuConfig } from '@/modules/rx/router/rx-routes'
 *
 * 依赖:
 *   - vue 3.x
 *   - pinia
 *   - vue-router 4.x
 *   - ant-design-vue 4.x
 *   - @ant-design/icons-vue
 *   - axios
 *
 * 文件清单 (12 文件):
 *   types/rx.ts                         — TypeScript 类型定义 (镜像后端 schemas)
 *   api/rxApi.ts                        — API 服务层 (8 端点)
 *   stores/rxStore.ts                   — Pinia 全局状态管理
 *   composables/useRx.ts               — 组合逻辑 (轮询/构建器/格式化/分页)
 *   components/rx/BigFiveRadar.vue      — 五因子人格雷达图 (Canvas)
 *   components/rx/TTMProgressBar.vue    — TTM阶段进度条
 *   components/rx/RxPrescriptionCard.vue— 处方卡片 (可展开)
 *   components/rx/RxComputeForm.vue     — 三维上下文计算表单
 *   components/rx/AgentStatusPanel.vue  — 4-Agent 状态监控面板
 *   components/rx/HandoffLogTable.vue   — 交接日志表格
 *   components/rx/StrategyGrid.vue      — 12策略模板卡片网格
 *   components/rx/index.ts             — 组件导出
 *   views/RxDashboard.vue              — 综合仪表盘页面
 *   router/rx-routes.ts                — 路由 + 权限 + 菜单配置
 */

// 组件
export * from './components'

// Store
export { useRxStore } from './stores/rxStore'

// Composables
export {
  useAgentPolling,
  useRxContextBuilder,
  useRxFormatter,
  useRxHistory,
} from './composables/useRx'

// API
export { rxApi } from './api/rxApi'

// 路由
export { rxRoutes, rxMenuConfig, checkRxPermission } from './router/rx-routes'

// 类型
export type * from './types/rx'
