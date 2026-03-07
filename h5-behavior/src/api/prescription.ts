import http from './request'

// TODO: 后端决策文档确认后替换 mock
export async function generatePrescription(payload: {
  label: string
  scores: Record<string, number>
  expectations: string[]
  sessionId: string
}) {
  try {
    const res = await http.post('/v1/rx/prescription', payload)
    return res.data
  } catch {
    return null
  }
}
