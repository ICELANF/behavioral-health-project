import request from './request'

// === Types ===
export interface AuditCase {
  id: string
  patientId: string
  originalL5Output: string
  narrativeL6Preview: string
  rawMetrics: {
    riskLevel: string
    phq9: number
    cgmTrend: string
    cgmCV?: number
    bigFive?: { N: number; E: number; O: number; A: number; C: number }
  }
  bapsProfile?: {
    combination: string
    risk_level: string
    stage: string
    type: string
  }
  status: 'pending' | 'approved' | 'rejected'
  decisionRules?: DecisionRules
  createdAt: string
}

export interface DecisionRules {
  trigger: string
  logic: string
  octopus_clamp: string
  narrative_override: string
}

export interface PublishPayload {
  caseId: string
  patientId: string
  masterSignerId: string
  secondarySignerId: string
  originalL5Output: string
  approvedL6Output: string
  riskLevel: string
}

// === API calls ===

/** Fetch audit queue */
export const fetchAuditQueue = (params?: { riskLevel?: string; page?: number }) =>
  request.get<{ items: AuditCase[]; total: number }>('/v1/agent/pending-reviews', { params })

/** Fetch BAPS profile */
export const fetchBapsProfile = (userId: number) =>
  request.get(`/v1/assessment/pipeline/${userId}/profile`)

/** Fetch CGM data */
export const fetchCGMData = (userId: number, params?: { startDate?: string; endDate?: string }) =>
  request.get(`/v1/mp/device/glucose/${userId}`, { params })

/** Fetch assessment history */
export const fetchAssessmentHistory = (userId: number) =>
  request.get(`/v1/assessment/history/${userId}`)

/** Publish audit result (dual sign + publish) */
export const publishAuditResult = (payload: PublishPayload) =>
  request.post('/v1/agent/feedback', {
    action: 'approve',
    trace_id: payload.caseId,
    patient_id: payload.patientId,
    master_signer_id: payload.masterSignerId,
    secondary_signer_id: payload.secondarySignerId,
    original_output: payload.originalL5Output,
    approved_output: payload.approvedL6Output,
    risk_level: payload.riskLevel,
  })

/** Reject audit case */
export const rejectAuditCase = (caseId: string, reason: string) =>
  request.post('/v1/agent/feedback', { action: 'reject', trace_id: caseId, reason })
