<template>
  <a-popover trigger="click" placement="bottomRight">
    <template #content>
      <div class="uap-menu">
        <div class="uap-user">
          <div class="uap-name">{{ userName }}</div>
          <div class="uap-role">{{ roleName }}</div>
        </div>
        <div class="uap-divider" />
        <div class="uap-item" @click="$router.push('/client/my/profile')">
          <UserOutlined /> 个人档案
        </div>
        <div class="uap-divider" />
        <div class="uap-item danger" @click="handleLogout">
          <LogoutOutlined /> 退出登录
        </div>
      </div>
    </template>
    <a-avatar
      :size="size"
      :src="avatarSrc || undefined"
      class="uap-avatar"
      :class="{ 'uap-dark': theme === 'dark' }"
    >
      <template v-if="!avatarSrc">{{ avatarText }}</template>
    </a-avatar>
  </a-popover>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { UserOutlined, LogoutOutlined } from '@ant-design/icons-vue'
import { useCurrentUser } from '@/composables/useCurrentUser'

withDefaults(defineProps<{
  size?: number
  theme?: 'light' | 'dark'
}>(), {
  size: 48,
  theme: 'light',
})

const { userName, avatarSrc, avatarText, roleName, handleLogout, refreshUserInfo } = useCurrentUser()

onMounted(() => {
  refreshUserInfo()
})
</script>

<style scoped>
.uap-avatar {
  cursor: pointer;
  transition: transform 0.2s;
  background: #1890ff !important;
  color: #fff !important;
  font-weight: 700;
}
.uap-avatar:hover {
  transform: scale(1.05);
}
.uap-dark {
  background: rgba(255,255,255,0.25) !important;
  border: 2px solid rgba(255,255,255,0.5);
}

.uap-menu {
  min-width: 180px;
}
.uap-user {
  padding: 8px 4px 10px;
}
.uap-name {
  font-size: 15px;
  font-weight: 700;
  color: #111827;
}
.uap-role {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}
.uap-divider {
  height: 1px;
  background: #f3f4f6;
  margin: 4px 0;
}
.uap-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 4px;
  font-size: 14px;
  color: #374151;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
}
.uap-item:hover {
  background: #f3f4f6;
}
.uap-item.danger {
  color: #dc2626;
}
.uap-item.danger:hover {
  background: #fef2f2;
}
</style>
