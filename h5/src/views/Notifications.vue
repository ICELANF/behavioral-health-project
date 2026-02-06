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
          <template v-if="healthAlerts.length">
            <div class="alert-item" v-for="(a, idx) in healthAlerts" :key="idx">
              <van-icon name="warning-o" :color="a.level === 'high' ? '#ee0a24' : '#ff976a'" size="24" />
              <div class="alert-content">
                <div class="alert-title">{{ a.title }}</div>
                <div class="alert-body">{{ a.message }}</div>
                <div class="alert-time">{{ formatTime(a.created_at) }}</div>
              </div>
            </div>
          </template>
          <van-empty v-else description="暂无健康提醒" />
        </van-tab>
      </van-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/index'

const router = useRouter()
const activeTab = ref(0)
const sessions = ref<any[]>([])
const notifications = ref<any[]>([])
const healthAlerts = ref<any[]>([])
const loadingSessions = ref(false)

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
    system: 'info-o',
    appointment: 'calendar-o',
    assessment: 'todo-list-o',
    task: 'orders-o'
  }
  return map[type] || 'bell'
}

function notifyColor(type: string) {
  const map: Record<string, string> = {
    system: '#1989fa',
    appointment: '#7c3aed',
    assessment: '#07c160',
    task: '#ff976a'
  }
  return map[type] || '#999'
}

function goChat(session: any) {
  router.push({ name: 'chat', query: { session_id: session.id } })
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

  // 加载健康提醒（来自最新状态）
  try {
    const res: any = await api.get('/api/v1/mp/device/dashboard/today')
    if (res?.alerts) {
      healthAlerts.value = res.alerts
    }
  } catch {}
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

    .session-title {
      font-size: $font-size-md;
      font-weight: 500;
    }

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

    .session-time {
      font-size: $font-size-xs;
      color: $text-color-placeholder;
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
    .alert-title {
      font-size: $font-size-md;
      font-weight: 500;
    }

    .notify-body,
    .alert-body {
      font-size: $font-size-sm;
      color: $text-color-secondary;
      margin-top: 4px;
      line-height: 1.5;
    }

    .notify-time,
    .alert-time {
      font-size: $font-size-xs;
      color: $text-color-placeholder;
      margin-top: 4px;
    }
  }
}
</style>
