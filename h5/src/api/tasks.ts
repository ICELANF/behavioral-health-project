import api from './index'

export interface MicroAction {
  id: string
  action_text: string
  category: string
  status: 'pending' | 'done' | 'attempted' | 'skipped' | 'expired'
  created_at: string
}

export interface StageInfo {
  current_stage: string
  stage_label: string
  stage_description: string
  ttm_stage: string
}

/** 今日微行动任务 */
export const fetchTodayTasks = () =>
  api.get('/api/v1/micro-actions/today')

/** 完成任务 */
export const completeTask = (taskId: string) =>
  api.post(`/api/v1/micro-actions/${taskId}/complete`)

/** 尝试但未完成 */
export const attemptTask = (taskId: string) =>
  api.post(`/api/v1/micro-actions/${taskId}/complete`, { status: 'attempted' })

/** 跳过任务 */
export const skipTask = (taskId: string) =>
  api.post(`/api/v1/micro-actions/${taskId}/skip`)

/** 获取当前阶段 */
export const fetchCurrentStage = () =>
  api.get('/api/v1/mp/progress/summary')

/** 获取已发布叙事 (Growth Journey) */
export const fetchPublishedNarrative = () =>
  api.get('/api/v1/messages/inbox')
