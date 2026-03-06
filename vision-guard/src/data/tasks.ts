export interface DailyTask {
  id: number
  icon: string
  iconBg: string
  name: string
  meta: string
  done: boolean
}

export const DEFAULT_TASKS: DailyTask[] = [
  { id: 1, icon: '🌳', iconBg: '#E8F5E9', name: '户外活动',     meta: '目标 2小时', done: false },
  { id: 2, icon: '📏', iconBg: '#E3F2FD', name: '用眼距离检查', meta: '阅读距离 > 33cm', done: false },
  { id: 3, icon: '💡', iconBg: '#FFF8E1', name: '台灯照度',     meta: '≥500 lux', done: false },
  { id: 4, icon: '🏃', iconBg: '#F3E5F5', name: '眼保健操',     meta: '09:30 & 14:30 各一次', done: false },
  { id: 5, icon: '📵', iconBg: '#FCE4EC', name: '屏幕时间记录', meta: '工作日上限2h', done: false },
]
