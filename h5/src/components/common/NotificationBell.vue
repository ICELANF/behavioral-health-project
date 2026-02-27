<template>
  <div class="notification-bell" @click="goNotifications">
    <van-icon name="bell" size="22" color="#374151" />
    <span v-if="unreadCount > 0" class="bell-badge">
      {{ unreadCount > 99 ? '99+' : unreadCount }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/index'
import { useNotificationStore } from '@/stores/notification'

const router = useRouter()
const notifStore = useNotificationStore()

const unreadCount = computed(() => notifStore.unreadCount)

// 首次加载时从REST API获取未读数作为fallback
onMounted(async () => {
  try {
    const res: any = await api.get('/api/v1/messages/unread-count')
    notifStore.setCount(res.unread_count || 0)
  } catch {
    // 静默失败
  }
})

function goNotifications() {
  router.push('/notifications')
}
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
