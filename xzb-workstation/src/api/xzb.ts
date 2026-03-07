import http from './request'

const P = '/api/v1/xzb'

// Expert management
export const registerExpert = (data: Record<string, unknown>) => http.post(`${P}/experts/register`, data)
export const getMyProfile = () => http.get(`${P}/experts/me/profile`)
export const updateMyProfile = (data: Record<string, unknown>) => http.put(`${P}/experts/me/profile`, data)
export const getMyConfig = () => http.get(`${P}/experts/me/config`)
export const updateMyConfig = (data: Record<string, unknown>) => http.put(`${P}/experts/me/config`, data)
export const startCalibration = () => http.post(`${P}/experts/me/calibrate`)
export const getDashboard = () => http.get(`${P}/experts/me/dashboard`)
export const setOnline = () => http.post(`${P}/experts/me/online`)

// Knowledge
export const listKnowledge = (params?: Record<string, unknown>) => http.get(`${P}/knowledge`, { params })
export const createKnowledge = (data: Record<string, unknown>) => http.post(`${P}/knowledge`, data)
export const getKnowledge = (id: string) => http.get(`${P}/knowledge/${id}`)
export const updateKnowledge = (id: string, data: Record<string, unknown>) => http.put(`${P}/knowledge/${id}`, data)
export const deleteKnowledge = (id: string) => http.delete(`${P}/knowledge/${id}`)
export const listPendingConfirm = () => http.get(`${P}/knowledge/pending-confirm`)
export const confirmKnowledge = (id: string, action: 'confirm' | 'reject') => http.post(`${P}/knowledge/${id}/confirm`, null, { params: { action } })
export const listRules = () => http.get(`${P}/knowledge/rules`)
export const createRule = (data: Record<string, unknown>) => http.post(`${P}/knowledge/rules`, data)
export const knowledgeHealthReport = () => http.get(`${P}/knowledge/health-report`)

// Batch knowledge ingestion (platform-level endpoint)
export const batchUploadKnowledge = (file: File, evidenceTier = 'T3') => {
  const form = new FormData()
  form.append('file', file)
  form.append('scope', 'expert')
  form.append('evidence_tier', evidenceTier)
  return http.post('/api/v1/knowledge/batch-upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  })
}
export const getBatchJob = (jobId: number) => http.get(`/api/v1/knowledge/batch-jobs/${jobId}`)

// Chat & intervention
export const getChatHistory = (convId: string) => http.get(`${P}/chat/${convId}/history`)
export const expertIntervene = (convId: string, content: string) => http.post(`${P}/chat/me/intervene/${convId}`, null, { params: { content } })
export const asyncReply = (convId: string, content: string) => http.post(`${P}/chat/me/async-reply/${convId}`, null, { params: { content } })

// Prescriptions
export const triggerRx = (seekerId: number, data: Record<string, unknown>) => http.post(`${P}/rx/trigger/${seekerId}`, data)
export const listRxTemplates = () => http.get(`${P}/rx/templates`)
export const createRxTemplate = (data: Record<string, unknown>) => http.post(`${P}/rx/templates`, data)
export const getExpertRxSource = (rxId: string) => http.get(`${P}/rx/${rxId}/expert-source`)

// Seekers (服务对象管理)
export const listSeekers = () => http.get(`${P}/seekers`)
export const getSeekerDetail = (id: number) => http.get(`${P}/seekers/${id}/detail`)
export const listSeekerConversations = (id: number, params?: Record<string, unknown>) => http.get(`${P}/seekers/${id}/conversations`, { params })
export const getSeekerHealthSummary = (id: number) => http.get(`${P}/seekers/${id}/health-summary`)
export const listExpertConversations = (params?: Record<string, unknown>) => http.get(`${P}/conversations`, { params })

// FAQ (常见问题库)
export const listFAQ = (params?: Record<string, unknown>) => http.get(`${P}/faq`, { params })
export const createFAQ = (data: { question: string; answer: string; domain?: string; tags?: string[] }) => http.post(`${P}/faq`, data)
export const updateFAQ = (id: string, data: { question: string; answer: string; domain?: string; tags?: string[] }) => http.put(`${P}/faq/${id}`, data)
export const deleteFAQ = (id: string) => http.delete(`${P}/faq/${id}`)

// Med Circle
export const listMedCircle = (params?: Record<string, unknown>) => http.get(`${P}/med-circle`, { params })
export const createMedCirclePost = (data: Record<string, unknown>) => http.post(`${P}/med-circle`, null, { params: data })
export const commentOnPost = (postId: string, content: string, parentId?: string) => http.post(`${P}/med-circle/${postId}/comment`, null, { params: { content, parent_id: parentId } })
