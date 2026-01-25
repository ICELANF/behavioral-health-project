// 本地存储工具类

const STORAGE_KEYS = {
  USER_ID: 'xingjian_user_id',
  USER_NAME: 'xingjian_user_name',
  EFFICACY_SCORE: 'xingjian_efficacy_score',
  WEARABLE_DATA: 'xingjian_wearable_data',
  CHAT_MESSAGES: 'xingjian_chat_messages',
  TASKS: 'xingjian_tasks'
}

export const storage = {
  // 用户信息
  getUserId(): string {
    return localStorage.getItem(STORAGE_KEYS.USER_ID) || ''
  },

  setUserId(id: string): void {
    localStorage.setItem(STORAGE_KEYS.USER_ID, id)
  },

  getUserName(): string {
    return localStorage.getItem(STORAGE_KEYS.USER_NAME) || '用户'
  },

  setUserName(name: string): void {
    localStorage.setItem(STORAGE_KEYS.USER_NAME, name)
  },

  // 效能感
  getEfficacyScore(): number {
    const score = localStorage.getItem(STORAGE_KEYS.EFFICACY_SCORE)
    return score ? parseInt(score, 10) : 50
  },

  setEfficacyScore(score: number): void {
    localStorage.setItem(STORAGE_KEYS.EFFICACY_SCORE, score.toString())
  },

  // 穿戴数据
  getWearableData(): Record<string, any> {
    const data = localStorage.getItem(STORAGE_KEYS.WEARABLE_DATA)
    return data ? JSON.parse(data) : {}
  },

  setWearableData(data: Record<string, any>): void {
    localStorage.setItem(STORAGE_KEYS.WEARABLE_DATA, JSON.stringify(data))
  },

  // 对话消息
  getChatMessages(): any[] {
    const messages = localStorage.getItem(STORAGE_KEYS.CHAT_MESSAGES)
    return messages ? JSON.parse(messages) : []
  },

  setChatMessages(messages: any[]): void {
    // 只保留最近 100 条消息
    const recent = messages.slice(-100)
    localStorage.setItem(STORAGE_KEYS.CHAT_MESSAGES, JSON.stringify(recent))
  },

  // 任务
  getTasks(): any[] {
    const tasks = localStorage.getItem(STORAGE_KEYS.TASKS)
    return tasks ? JSON.parse(tasks) : []
  },

  setTasks(tasks: any[]): void {
    localStorage.setItem(STORAGE_KEYS.TASKS, JSON.stringify(tasks))
  },

  // 清除所有数据
  clearAll(): void {
    Object.values(STORAGE_KEYS).forEach(key => {
      localStorage.removeItem(key)
    })
  }
}

export default storage
