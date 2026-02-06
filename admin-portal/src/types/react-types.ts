export interface AuditCase {
  id: string;
  patientId: string;
  originalL5Output: string;
  narrativeL6Preview: string;
  rawMetrics: {
    riskLevel: string;
    phq9: number;
    cgmTrend: string;
  };
  status: 'pending' | 'approved' | 'rejected';
  decisionRules?: DecisionRules;
  decisionTraceId?: string;
  createdAt: Date;
}

export interface TraceNode {
  id: string;
  type: 'INPUT' | 'RULE' | 'DECISION' | 'OUTPUT';
  label: string;
  value: string;
  timestamp: string;
}

export interface TraceLink {
  source: string;
  target: string;
  weight: number;
}

export interface DecisionRules {
  trigger: string;
  logic: string;
  octopus_clamp: string;
  narrative_override: string;
}

export interface TraceSession {
  id: string;
  caseId: string;
  patientId: string;
  nodes: TraceNode[];
  links: TraceLink[];
  decisionRules?: DecisionRules;
  createdAt: Date;
}
