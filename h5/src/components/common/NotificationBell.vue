<template>
  <div class="notification-bell" @click="goNotifications">
    <van-icon name="bell" size="22" color="#374151" />
    <span v-if="unreadCount > 0" class="bell-badge">
      {{ unreadCount > 99 ? '99+' : unreadCount }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/index'

const router = useRouter()
const unreadCount = ref(0)
let pollTimer: ReturnType<typeof setInterval> | null = null

async function fetchUnread() {
  try {
    const res: any = await api.get('/api/v1/messages/unread-count')
    unreadCount.value = res.unread_count || 0
  } catch {
    // 静默失败，不影响用户体验
  }
}

function goNotifications() {
  router.push('/notifications')
}

onMounted(() => {
  fetchUnread()
  pollTimer = setInterval(fetchUnread, 30000)
})

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
})
</script>

<style scoped>
.notification-bell {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.bell-badge {
  position: absolute;
  top: 0;
  right: 0;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  font-size: 10px;
  font-weight: 700;
  line-height: 16px;
  text-align: center;
  color: #fff;
  background: #ff4d4f;
  border-radius: 8px;
  transform: translate(25%, -25%);
}
</style>
