import http from './request'

export async function sendSms(phone: string) {
  const res = await http.post('/auth/sms/send', { phone })
  return res.data
}

export async function registerBySms(phone: string, code: string, sessionId: string) {
  const res = await http.post('/auth/register/sms', { phone, code, session_id: sessionId })
  return res.data
}
