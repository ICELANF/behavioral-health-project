import http from './request'

// TODO: 后端决策文档确认后替换 mock
export async function submitAssessment(payload: {
  door: string
  scene: number
  belief: number
  answers: Record<number, number | number[]>
  concerns?: { worry: string; confusion: string; desire: string; aversion: string }
  voiceEmotions?: Record<string, string>
  sessionId: string
}) {
  try {
    const res = await http.post('/v1/assessment', payload)
    return res.data
  } catch {
    // mock fallback — 本地计算
    return null
  }
}

export async function getAssessment(id: string) {
  const res = await http.get(`/v1/assessment/${id}`)
  return res.data
}
