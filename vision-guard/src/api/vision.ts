import http from './request'

// -- Behavior Logs --
export const submitLog = (data: Record<string, unknown>) =>
  http.post('/api/v1/vision/log', data)

export const getMyLogs = (params?: { limit?: number }) =>
  http.get('/api/v1/vision/log/me', { params })

export const getDashboard = (userId: number) =>
  http.get(`/api/v1/vision/dashboard/${userId}`)

// -- Goals --
export const getGoals = () =>
  http.get('/api/v1/vision/goals/me')

export const updateGoal = (goalId: number, data: Record<string, unknown>) =>
  http.patch(`/api/v1/vision/goals/${goalId}`, data)

// -- Profile --
export const getProfile = () =>
  http.get('/api/v1/vision/profile/me')

export const updateProfile = (data: Record<string, unknown>) =>
  http.put('/api/v1/vision/profile/me', data)

// -- Exam Records --
export const submitExam = (data: Record<string, unknown>) =>
  http.post('/api/v1/vision/exam', data)

export const getExamHistory = () =>
  http.get('/api/v1/vision/exam/me')

// -- Guardian --
export const bindGuardian = (data: { guardian_phone: string; relationship: string }) =>
  http.post('/api/v1/vision/guardian/bind', data)

export const getGuardianBindings = () =>
  http.get('/api/v1/vision/guardian/me')

// -- AI Food Analysis (backend proxy, NOT direct Claude API) --
export const analyzeFood = (data: FormData) =>
  http.post('/api/v1/vision/ai/analyze-food', data)

// -- Nutrition Survey --
export const submitNutritionSurvey = (data: Record<string, unknown>) =>
  http.post('/api/v1/vision/behavior/nutrition-survey', data)
