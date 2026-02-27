<template>
  <div class="wechat-callback">
    <van-loading type="spinner" size="36" color="#07C160" />
    <p class="status-text">{{ statusText }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import api from '@/api/index'
import storage from '@/utils/storage'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const statusText = ref('微信登录中...')

onMounted(async () => {
  const code = route.query.code as string
  const token = route.query.token as string

  // 方式1: 直接回调带 token (后端 redirect 模式)
  if (token) {
    storage.setToken(token)
    statusText.value = '登录成功，正在跳转...'
    showToast({ message: '登录成功', type: 'success' })
    router.replace('/')
    return
  }

  // 方式2: 带 code 参数，需要前端调后端换 token
  if (code) {
    try {
      const state = (route.query.state as string) || ''
      const res: any = await api.post('/api/v1/auth/wechat/exchange', {
        code, state
      })

      if (res.access_token || res.token) {
        const accessToken = res.access_token || res.token
        storage.setToken(accessToken)

        if (res.user) {
          storage.setAuthUser(res.user)
          userStore.setUserInfo({
            id: String(res.user.id),
            name: res.user.full_name || res.user.username,
          })
          const ROLE_LEVELS: Record<string, number> = {
            observer: 1, grower: 2, sharer: 3, coach: 4,
            promoter: 5, supervisor: 5, master: 6, admin: 99
          }
          const userRole = (res.user.role || 'observer').toLowerCase()
          localStorage.setItem('bhp_role_level', String(res.user.role_level || ROLE_LEVELS[userRole] || 1))
        }

        statusText.value = '登录成功，正在跳转...'
        showToast({ message: '登录成功', type: 'success' })
        router.replace('/')
      } else {
        throw new Error('未获取到登录凭证')
      }
    } catch (e: any) {
      statusText.value = '登录失败'
      showToast(e.response?.data?.detail || '微信登录失败，请重试')
      setTimeout(() => router.replace('/login'), 2000)
    }
  } else {
    statusText.value = '参数缺失'
    showToast('微信授权失败')
    setTimeout(() => router.replace('/login'), 2000)
  }
})
</script>

<style scoped>
.wechat-callback {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #f7f8fa;
}

.status-text {
  margin-top: 16px;
  font-size: 14px;
  color: #666;
}
</style>
