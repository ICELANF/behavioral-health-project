<template>
  <div class="user-hero">
    <div class="hero-left" @click="goProfile">
      <div class="hero-avatar-wrap">
        <img class="hero-avatar" :src="userStore.avatarUrl" alt="avatar" />
        <div class="hero-camera-badge">
          <van-icon name="photograph" size="10" color="#fff" />
        </div>
      </div>
      <div class="hero-role-badge" :class="'role--' + userStore.role">
        {{ userStore.roleLabel }}
      </div>
    </div>
    <div class="hero-center">
      <span class="hero-greeting">{{ greetingText }}</span>
      <span class="hero-name">{{ userStore.name || '用户' }}</span>
    </div>
    <div class="hero-right">
      <div class="streak-badge" v-if="streakDays > 0">
        <span class="streak-fire">&#x1F525;</span>
        <span class="streak-num">{{ streakDays }}</span>
        <span class="streak-label">天</span>
      </div>
      <div class="hero-icon touch-target" @click="goSettings">
        <van-icon name="setting-o" size="20" color="#6b7280" />
      </div>
      <NotificationBell />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import api from '@/api/index'
import NotificationBell from '@/components/common/NotificationBell.vue'

const props = withDefaults(defineProps<{
  streakDays?: number
}>(), {
  streakDays: 0,
})

const router = useRouter()
const userStore = useUserStore()

const greetingText = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 11) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

function goProfile() {
  router.push('/profile')
}

function goSettings() {
  router.push({ name: 'account-settings' })
}

// 挂载时刷新用户信息到 store
onMounted(async () => {
  try {
    const me: any = await api.get('/api/v1/auth/me')
    if (me) {
      userStore.setUserInfo({
        id: me.id ? String(me.id) : undefined,
        name: me.full_name || me.username || me.name,
        role: me.role?.toLowerCase(),
        avatar: me.avatar || '',
        growth_points: me.growth_points ?? me.total_growth_points ?? 0,
      } as any)
    }
  } catch { /* 使用缓存 */ }
})
</script>

<style scoped>
.user-hero {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
}

.hero-left {
  position: relative;
  flex-shrink: 0;
  cursor: pointer;
}

.hero-avatar-wrap {
  position: relative;
  width: 48px;
  height: 48px;
}

.hero-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #e5e7eb;
}

.hero-camera-badge {
  position: absolute;
  bottom: -1px;
  right: -1px;
  width: 18px;
  height: 18px;
  background: rgba(0, 0, 0, 0.55);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1.5px solid #fff;
}

.hero-role-badge {
  position: absolute;
  bottom: -4px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  font-weight: 600;
  padding: 1px 8px;
  border-radius: 10px;
  white-space: nowrap;
  color: #fff;
  background: #10b981;
}

.role--observer { background: #f59e0b; }
.role--grower   { background: #10b981; }
.role--sharer   { background: #7c3aed; }
.role--coach    { background: #3b82f6; }
.role--promoter { background: #6366f1; }
.role--supervisor { background: #ec4899; }
.role--master   { background: #ef4444; }
.role--admin    { background: #1f2937; }

.hero-center {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.hero-greeting {
  font-size: 13px;
  color: #9ca3af;
}

.hero-name {
  font-size: 18px;
  font-weight: 700;
  color: #111827;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hero-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.streak-badge {
  display: flex;
  align-items: baseline;
  gap: 2px;
  background: #fef3c7;
  border-radius: 20px;
  padding: 4px 10px;
}
.streak-fire { font-size: 14px; }
.streak-num { font-size: 18px; font-weight: 800; color: #d97706; }
.streak-label { font-size: 10px; color: #92400e; }

.hero-icon {
  cursor: pointer;
}
</style>
