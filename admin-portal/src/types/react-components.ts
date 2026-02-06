// ============================================================
// types/react-components.ts - React组件类型定义
// 位置: src/types/react-components.ts
// ============================================================

// 审核案例类型
export interface AuditCase {
  id: string
  patientId: string
  rawMetrics: {
    phq9: number
    cgmTrend: string
    riskLevel: string
  }
  originalL5Output: string
  narrativeL6Preview: string
  status: 'pending' | 'approved' | 'rejected'
  decisionRules?: DecisionRules
  decisionTraceId?: string
  createdAt: Date
}

// 决策规则类型
export interface DecisionRules {
  trigger: string
  logic: string
  octopus_clamp: string
  narrative_override: string
}

// 追踪节点类型
export interface TraceNode {
  id: string
  type: 'INPUT' | 'RULE' | 'AGENT' | 'DECISION' | 'OUTPUT'
  label: string
  value: string
  timestamp: string
  children?: TraceNode[]
  metadata?: Record<string, any>
}

// 追踪会话类型
export interface TraceSession {
  id: string
  patientId: string
  startedAt: string
  endedAt?: string
  nodes: TraceNode[]
  summary?: string
  decisionRules?: DecisionRules
}

// CGM数据点类型
export interface CGMDataPoint {
  time: string
  value: number
  trend?: 'up' | 'down' | 'stable'
}

// 审计日志类型
export interface AuditLog {
  id: string
  trace_id: string
  patient_id: string
  master_signer_id: string
  secondary_signer_id: string
  original_l5_output: string
  approved_l6_output: string
  risk_level: string
  approval_status: 'pending' | 'approved' | 'rejected'
  approved_at?: string
  created_at: string
}

// DualSignPanel Props
export interface DualSignPanelProps {
  auditCase: AuditCase
  onPublish?: (result: PublishResult) => void
  onSignChange?: (signs: { master: boolean; secondary: boolean }) => void
}

// 发布结果
export interface PublishResult {
  success: boolean
  traceId: string
  timestamp: string
  error?: string
}

// LogicFlowBridge Props
export interface LogicFlowBridgeProps {
  decisionRules: DecisionRules
  highlightLine?: number
  onLineHover?: (lineNumber: number | null) => void
}

// CGMChart Props
export interface CGMChartProps {
  data?: CGMDataPoint[]
  patientId?: string
  showRawData?: boolean
  height?: number
  onDataPointClick?: (point: CGMDataPoint) => void
}

// JourneyPage Props
export interface JourneyPageProps {
  patientId?: string
  showHeader?: boolean
  onMessageReceived?: (message: AuditLog) => void
}

// ExpertWorkspace Props
export interface ExpertWorkspaceProps {
  initialTab?: 'audit' | 'trace' | 'brain'
  onTabChange?: (tab: string) => void
  onPublish?: (result: PublishResult) => void
}

// TracePage Props
export interface TracePageProps {
  sessionId?: string
  patientId?: string
  onNodeSelect?: (node: TraceNode) => void
}

// DecisionTrace Props
export interface DecisionTraceProps {
  nodes: TraceNode[]
  selectedNodeId?: string
  onNodeClick?: (node: TraceNode) => void
}

// TraceGraph Props
export interface TraceGraphProps {
  session: TraceSession
  layout?: 'horizontal' | 'vertical'
  onNodeHover?: (node: TraceNode | null) => void
}

// LogicInterpreter Props
export interface LogicInterpreterProps {
  decisionRules: DecisionRules
  showExplanation?: boolean
}

// Brain Context 类型
export interface BrainContextType {
  traces: TraceNode[]
  addDecisionTrace: (node: TraceNode) => void
  clearTraces: () => void
  calculateRiskScore: (metrics: Record<string, number>) => number
}
