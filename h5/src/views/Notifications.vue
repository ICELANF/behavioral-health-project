<template>
  <div class="page-container">
    <van-nav-bar title="消息通知" left-arrow @click-left="$router.back()" />

    <div class="page-content">
      <van-tabs v-model:active="activeTab">
        <van-tab title="对话消息">
          <van-loading v-if="loadingSessions" class="loading" />
          <template v-else-if="sessions.length">
            <div
              class="session-item"
              v-for="session in sessions"
              :key="session.id"
              @click="goChat(session)"
            >
              <van-icon name="chat-o" size="36" color="#1989fa" />
              <div class="session-info">
                <div class="session-title">{{ session.title || '对话 ' + session.id }}</div>
                <div class="session-preview">{{ session.last_message || '暂无消息' }}</div>
              </div>
              <div class="session-meta">
                <div class="session-time">{{ formatTime(session.updated_at || session.created_at) }}</div>
                <van-badge v-if="session.unread_count" :content="session.unread_count" />
              </div>
            </div>
          </template>
          <van-empty v-else description="暂无对话消息" />
        </van-tab>

        <van-tab :title="coachTabTitle">
          <van-loading v-if="loadingCoachMessages" class="loading" />
          <template v-else-if="coachMessages.length">
            <div
              class="coach-msg-item"
              v-for="msg in coachMessages"
              :key="msg.id"
              @click="markCoachRead(msg)"
            >
              <div class="coach-msg-avatar">
                <van-icon name="manager-o" size="28" :color="msg.is_read ? '#999' : '#1989fa'" />
              </div>
              <div class="coach-msg-content">
                <div class="coach-msg-header">
                  <span class="coach-name">{{ msg.coach_name }}</span>
                  <van-tag v-if="msg.message_type !== 'text'" size="small" :type="coachMsgTagType(msg.message_type)">
                    {{ coachMsgTypeLabel(msg.message_type) }}
                  </van-tag>
                  <van-badge v-if="!msg.is_read" dot />
                </div>
                <div class="coach-msg-body">{{ msg.content }}</div>
                <div class="coach-msg-time">{{ formatTime(msg.created_at) }}</div>
              </div>
            </div>
          </template>
          <van-empty v-else description="暂无教练消息" />
        </van-tab>

        <van-tab :title="pendingAssessTabTitle">
          <van-loading v-if="loadingPendingAssess" class="loading" />
          <template v-else-if="pendingAssessments.length">
            <div
              class="assess-notify-item"
              v-for="a in pendingAssessments"
              :key="a.id"
            >
              <div class="assess-notify-icon">
                <van-icon name="todo-list-o" size="28" color="#1989fa" />
              </div>
              <div class="assess-notify-content">
                <div class="assess-notify-header">
                  <span style="font-weight:500">待完成评估</span>
                  <van-badge dot />
                </div>
                <div class="assess-notify-body">
                  {{ a.coach_name }} 推送了评估量表: {{ (a.scales || []).join(', ').toUpperCase() }}
                </div>
                <div v-if="a.note" class="assess-notify-note">备注: {{ a.note }}</div>
                <div class="assess-notify-time">{{ formatTime(a.created_at) }}</div>
                <van-button
                  type="primary"
                  size="small"
                  round
                  style="margin-top:8px"
                  @click="goAssessment(a)"
                >去完成</van-button>
              </div>
            </div>
          </template>
          <van-empty v-else description="暂无待完成评估" />
        </van-tab>

        <van-tab title="系统通知">
          <template v-if="notifications.length">
            <div class="notify-item" v-for="(n, idx) in notifications" :key="idx">
              <van-icon :name="notifyIcon(n.type)" :color="notifyColor(n.type)" size="24" />
              <div class="notify-content">
                <div class="notify-title">{{ n.title }}</div>
                <div class="notify-body">{{ n.body }}</div>
                <div class="notify-time">{{ formatTime(n.created_at) }}</div>
              </div>
            </div>
          </template>
          <van-empty v-else description="暂无系统通知" />
        </van-tab>

        <van-tab title="健康提醒">
          <van-loading v-if="loadingReminders" class="loading" />
          <template v-if="reminders.length">
            <div class="reminder-item" v-for="r in reminders" :key="r.id">
              <van-icon :name="reminderIcon(r.type)" :color="reminderColor(r.type)" size="24" />
              <div class="reminder-content">
                <div class="reminder-title">{{ r.title }}</div>
                <div class="reminder-body" v-if="r.content">{{ r.content }}</div>
                <div class="reminder-meta">
                  <span v-if="r.cron_expr" class="reminder-cron">每天 {{ r.cron_expr }}</span>
                  <span v-if="r.next_fire_at" class="reminder-next">下次: {{ formatTime(r.next_fire_at) }}</span>
                  <van-tag size="small" :type="r.source === 'coach' ? 'primary' : 'default'">
                    {{ r.source === 'coach' ? '教练设置' : r.source === 'system' ? '系统' : '自定义' }}
                  </van-tag>
                </div>
              </div>
            </div>
          </template>
          <template v-else-if="healthAlerts.length">
            <div class="alert-item" v-for="(a, idx) in healthAlerts" :key="idx">
              <van-icon name="warning-o" :color="a.level === 'high' ? '#ee0a24' : '#ff976a'" size="24" />
              <div class="alert-content">
                <div class="alert-title">{{ a.title }}</div>
                <div class="alert-body">{{ a.message }}</div>
                <div class="alert-time">{{ formatTime(a.created_at) }}</div>
              </div>
            </div>
          </template>
          <van-empty v-else-if="!loadingReminders" description="暂无健康提醒" />
        </van-tab>

        <van-tab :title="alertTabTitle">
          <van-loading v-if="loadingDeviceAlerts" class="loading" />
          <template v-if="deviceAlertList.length">
            <div
              class="alert-item"
              v-for="a in deviceAlertList"
              :key="a.id"
              :style="{ borderLeft: '3px solid ' + (a.severity === 'danger' ? '#ee0a24' : '#ff976a') }"
            >
              <van-icon name="warning-o" :color="a.severity === 'danger' ? '#ee0a24' : '#ff976a'" size="24" />
              <div class="alert-content">
                <div class="alert-title" :style="{ color: a.severity === 'danger' ? '#ee0a24' : '#ff976a' }">
                  {{ a.message }}
                </div>
                <div class="alert-body">
                  {{ a.data_type }} · 当前值: {{ a.data_value }} · 阈值: {{ a.threshold_value }}
                </div>
                <div class="alert-time">{{ formatTime(a.created_at) }}</div>
                <van-button
                  v-if="!a.user_read"
                  type="primary"
                  size="mini"
                  round
                  style="margin-top:6px"
                  @click="markAlertRead(a)"
                >标记已读</van-button>
              </div>
            </div>
          </template>
          <van-empty v-else-if="!loadingDeviceAlerts" description="暂无健康预警" />
        </van-tab>
      </van-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/index'

const router = useRouter()
const activeTab = ref(0)
const sessions = ref<any[]>([])
const notifications = ref<any[]>([])
const healthAlerts = ref<any[]>([])
const loadingSessions = ref(false)

// 教练消息
const loadingCoachMessages = ref(false)
const coachMessages = ref<any[]>([])
const unreadCount = ref(0)

// 提醒
const loadingReminders = ref(false)
const reminders = ref<any[]>([])

// 设备预警
const loadingDeviceAlerts = ref(false)
const deviceAlertList = ref<any[]>([])
const unreadAlertCount = ref(0)

// 待完成评估
const loadingPendingAssess = ref(false)
const pendingAssessments = ref<any[]>([])
const pendingAssessTabTitle = computed(() => {
  return pendingAssessments.value.length > 0 ? `待完成评估(${pendingAssessments.value.length})` : '待完成评估'
})

const coachTabTitle = computed(() => {
  return unreadCount.value > 0 ? `教练消息(${unreadCount.value})` : '教练消息'
})

const alertTabTitle = computed(() => {
  return unreadAlertCount.value > 0 ? `健康预警(${unreadAlertCount.value})` : '健康预警'
})

function formatTime(str: string) {
  if (!str) return ''
  const d = new Date(str)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin}分钟前`
  const diffHour = Math.floor(diffMin / 60)
  if (diffHour < 24) return `${diffHour}小时前`
  return str.replace('T', ' ').slice(0, 16)
}

function notifyIcon(type: string) {
  const map: Record<string, string> = {
    system: 'info-o', appointment: 'calendar-o',
    assessment: 'todo-list-o', task: 'orders-o'
  }
  return map[type] || 'bell'
}
function notifyColor(type: string) {
  const map: Record<string, string> = {
    system: '#1989fa', appointment: '#7c3aed',
    assessment: '#07c160', task: '#ff976a'
  }
  return map[type] || '#999'
}

function coachMsgTagType(type: string) {
  return { encouragement: 'success', reminder: 'warning', advice: 'primary' }[type] || 'default'
}
function coachMsgTypeLabel(type: string) {
  return { encouragement: '鼓励', reminder: '提醒', advice: '建议' }[type] || type
}

function reminderIcon(type: string) {
  return { medication: 'coupon-o', visit: 'calendar-o', behavior: 'fire-o', assessment: 'todo-list-o' }[type] || 'clock-o'
}
function reminderColor(type: string) {
  return { medication: '#f59e0b', visit: '#7c3aed', behavior: '#07c160', assessment: '#1989fa' }[type] || '#ff976a'
}

function goChat(session: any) {
  router.push({ name: 'chat', query: { session_id: session.id } })
}

function goAssessment(assignment: any) {
  router.push({ path: '/behavior-assessment', query: { assignment_id: assignment.id } })
}

async function markCoachRead(msg: any) {
  if (msg.is_read) return
  try {
    await api.post(`/api/v1/messages/${msg.id}/read`)
    msg.is_read = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  } catch { /* ignore */ }
}

async function markAlertRead(alert: any) {
  try {
    await api.post(`/api/v1/alerts/${alert.id}/read`)
    alert.user_read = true
    unreadAlertCount.value = Math.max(0, unreadAlertCount.value - 1)
  } catch { /* ignore */ }
}

onMounted(async () => {
  // 加载对话会话
  loadingSessions.value = true
  try {
    const res: any = await api.get('/api/v1/chat/sessions')
    sessions.value = res.sessions || res.data || res || []
  } catch {
    sessions.value = []
  } finally {
    loadingSessions.value = false
  }

  // 加载教练消息
  loadingCoachMessages.value = true
  try {
    const [msgRes, countRes] = await Promise.all([
      api.get('/api/v1/messages/inbox'),
      api.get('/api/v1/messages/unread-count'),
    ])
    coachMessages.value = (msgRes as any).messages || []
    unreadCount.value = (countRes as any).unread_count || 0
  } catch {
    coachMessages.value = []
  } finally {
    loadingCoachMessages.value = false
  }

  // 加载提醒
  loadingReminders.value = true
  try {
    const res: any = await api.get('/api/v1/reminders')
    reminders.value = res.reminders || []
  } catch {
    reminders.value = []
  } finally {
    loadingReminders.value = false
  }

  // 加载待完成评估
  loadingPendingAssess.value = true
  try {
    const res: any = await api.get('/api/v1/assessment-assignments/my-pending')
    pendingAssessments.value = res.assignments || []
  } catch {
    pendingAssessments.value = []
  } finally {
    loadingPendingAssess.value = false
  }

  // 加载系统通知
  try {
    const res: any = await api.get('/api/v1/notifications/system?limit=20')
    notifications.value = res.notifications || []
  } catch {
    notifications.value = []
  }

  // 加载健康提醒（来自设备）
  try {
    const res: any = await api.get('/api/v1/mp/device/dashboard/today')
    if (res?.alerts) {
      healthAlerts.value = res.alerts
    }
  } catch {}

  // 加载设备预警
  loadingDeviceAlerts.value = true
  try {
    const res: any = await api.get('/api/v1/alerts/my?limit=20')
    deviceAlertList.value = res.alerts || []
    unreadAlertCount.value = (res.alerts || []).filter((a: any) => !a.user_read).length
  } catch {
    deviceAlertList.value = []
  } finally {
    loadingDeviceAlerts.value = false
  }
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.loading { text-align: center; padding: 60px 0; }

.session-item {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  padding: $spacing-md;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;

  &:active { background: #f7f7f7; }

  .session-info {
    flex: 1;
    overflow: hidden;

    .session-title { font-size: $font-size-md; font-weight: 500; }
    .session-preview {
      font-size: $font-size-sm;
      color: $text-color-secondary;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      margin-top: 4px;
    }
  }

  .session-meta {
    text-align: right;
    flex-shrink: 0;
    .session-time { font-size: $font-size-xs; color: $text-color-placeholder; }
  }
}

.coach-msg-item {
  display: flex;
  gap: $spacing-sm;
  padding: $spacing-md;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;

  &:active { background: #f7f7f7; }

  .coach-msg-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: #f0f5ff;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .coach-msg-content {
    flex: 1;

    .coach-msg-header {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 4px;

      .coach-name { font-weight: 500; font-size: $font-size-md; }
    }

    .coach-msg-body {
      font-size: $font-size-sm;
      color: $text-color-secondary;
      line-height: 1.5;
    }

    .coach-msg-time {
      font-size: $font-size-xs;
      color: $text-color-placeholder;
      margin-top: 4px;
    }
  }
}

.reminder-item {
  display: flex;
  gap: $spacing-sm;
  padding: $spacing-md;
  border-bottom: 1px solid #f5f5f5;

  .reminder-content {
    flex: 1;

    .reminder-title { font-size: $font-size-md; font-weight: 500; }
    .reminder-body { font-size: $font-size-sm; color: $text-color-secondary; margin-top: 4px; line-height: 1.5; }
    .reminder-meta {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 6px;
      font-size: $font-size-xs;
      color: $text-color-placeholder;
    }
  }
}

.assess-notify-item {
  display: flex;
  gap: $spacing-sm;
  padding: $spacing-md;
  border-bottom: 1px solid #f5f5f5;

  .assess-notify-icon {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: #e6f7ff;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .assess-notify-content {
    flex: 1;

    .assess-notify-header {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 4px;
    }

    .assess-notify-body {
      font-size: $font-size-sm;
      color: $text-color-secondary;
      line-height: 1.5;
    }

    .assess-notify-note {
      font-size: $font-size-xs;
      color: #1890ff;
      margin-top: 2px;
    }

    .assess-notify-time {
      font-size: $font-size-xs;
      color: $text-color-placeholder;
      margin-top: 4px;
    }
  }
}

.notify-item,
.alert-item {
  display: flex;
  gap: $spacing-sm;
  padding: $spacing-md;
  border-bottom: 1px solid #f5f5f5;

  .notify-content,
  .alert-content {
    flex: 1;

    .notify-title,
    .alert-title { font-size: $font-size-md; font-weight: 500; }
    .notify-body,
    .alert-body { font-size: $font-size-sm; color: $text-color-secondary; margin-top: 4px; line-height: 1.5; }
    .notify-time,
    .alert-time { font-size: $font-size-xs; color: $text-color-placeholder; margin-top: 4px; }
  }
}
</style>
