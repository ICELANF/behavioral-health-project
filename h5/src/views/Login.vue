<template>
  <div class="login-page">
    <div class="login-header">
      <div class="logo-icon">
        <van-icon name="shield-o" size="48" color="#1989fa" />
      </div>
      <h1>行健行为教练</h1>
      <p>您的专属行为健康管理伙伴</p>
    </div>

    <div class="login-form">
      <van-cell-group inset>
        <van-field
          v-model="form.username"
          label="用户名"
          placeholder="请输入用户名"
          :rules="[{ required: true, message: '请输入用户名' }]"
        />
        <van-field
          v-model="form.password"
          type="password"
          label="密码"
          placeholder="请输入密码"
          :rules="[{ required: true, message: '请输入密码' }]"
        />
      </van-cell-group>

      <div class="form-actions">
        <van-button
          type="primary"
          block
          round
          size="large"
          :loading="loading"
          loading-text="登录中..."
          @click="handleLogin"
        >
          登录
        </van-button>
      </div>
    </div>

    <!-- 快速体验入口 -->
    <div class="quick-login">
      <p class="quick-title">快速体验</p>
      <div class="quick-buttons">
        <van-button size="small" round @click="quickLogin('grower')">成长者</van-button>
        <van-button size="small" round @click="quickLogin('observer')">观察员</van-button>
        <van-button size="small" round @click="quickLogin('sharer')">分享者</van-button>
        <van-button size="small" round type="primary" plain @click="quickLogin('coach')">教练</van-button>
      </div>
    </div>

    <div class="login-footer">
      <p>登录即表示您同意 <a href="#">用户协议</a> 和 <a href="#">隐私政策</a></p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast } from 'vant'
import api from '@/api/index'
import storage from '@/utils/storage'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const demoAccounts: Record<string, { password: string; label: string }> = {
  observer: { password: 'Observer@2026', label: '观察员' },
  grower:   { password: 'Grower@2026',   label: '成长者' },
  sharer:   { password: 'Sharer@2026',   label: '分享者' },
  coach:    { password: 'Coach@2026',    label: '教练' },
}

function quickLogin(role: string) {
  const account = demoAccounts[role]
  if (!account) return
  form.username = role
  form.password = account.password
  handleLogin()
}

async function handleLogin() {
  if (!form.username || !form.password) {
    showToast('请输入用户名和密码')
    return
  }

  loading.value = true
  showLoadingToast({ message: '登录中...', forbidClick: true })
  try {
    const params = new URLSearchParams()
    params.append('username', form.username)
    params.append('password', form.password)

    const res: any = await api.post('/api/v1/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })

    storage.setToken(res.access_token)
    if (res.user) {
      storage.setAuthUser(res.user)
      userStore.setUserInfo({
        id: String(res.user.id),
        name: res.user.full_name || res.user.username,
      })
    }

    closeToast()
    showToast({ message: '登录成功', type: 'success' })
    router.replace('/')
  } catch (e: any) {
    closeToast()
    const msg = e.response?.data?.detail || '登录失败，请检查用户名和密码'
    showToast(msg)
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 40px 20px;
  background: linear-gradient(135deg, #e8f4fd 0%, #f0f7ff 50%, #fff 100%);
}

.login-header {
  text-align: center;
  margin-bottom: 40px;

  .logo-icon {
    width: 80px;
    height: 80px;
    margin: 0 auto 16px;
    background: #fff;
    border-radius: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 12px rgba(25, 137, 250, 0.15);
  }

  h1 {
    font-size: 24px;
    color: #333;
    margin-bottom: 8px;
  }

  p {
    font-size: 14px;
    color: #999;
  }
}

.login-form {
  .form-actions {
    padding: 24px 16px 0;
  }
}

.quick-login {
  margin-top: 32px;
  text-align: center;

  .quick-title {
    font-size: 13px;
    color: #999;
    margin-bottom: 12px;
  }

  .quick-buttons {
    display: flex;
    justify-content: center;
    gap: 10px;
    flex-wrap: wrap;
  }
}

.login-footer {
  text-align: center;
  margin-top: 32px;
  font-size: 12px;
  color: #999;

  a {
    color: #1989fa;
    text-decoration: none;
  }
}
</style>
