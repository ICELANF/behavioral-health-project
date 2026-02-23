<template>
  <div class="login-container">
    <div class="login-wrapper">
      <!-- Logo 和标题 -->
      <div class="login-brand">
        <div class="brand-logo">🌿</div>
        <h1 class="brand-title">行为健康平台</h1>
        <p class="brand-subtitle">专业的健康行为改变管理系统</p>
      </div>

      <!-- 登录卡片 -->
      <div class="login-card">
        <div class="step-content">
          <h2 class="step-title">账号登录</h2>

          <a-form :model="formState" @finish="handleLogin" layout="vertical">
            <a-form-item name="username" :rules="[{ required: true, message: '请输入用户名' }]">
              <a-input
                v-model:value="formState.username"
                size="large"
                placeholder="请输入用户名"
              >
                <template #prefix><UserOutlined /></template>
              </a-input>
            </a-form-item>

            <a-form-item name="password" :rules="[{ required: true, message: '请输入密码' }]">
              <a-input-password
                v-model:value="formState.password"
                size="large"
                placeholder="请输入密码"
              >
                <template #prefix><LockOutlined /></template>
              </a-input-password>
            </a-form-item>

            <a-form-item>
              <div class="form-actions">
                <a-checkbox v-model:checked="rememberMe">记住登录</a-checkbox>
                <a class="forgot-link" @click="message.info('请联系管理员重置密码')">忘记密码？</a>
              </div>
            </a-form-item>

            <a-form-item>
              <a-button
                type="primary"
                html-type="submit"
                size="large"
                block
                :loading="loading"
              >
                登录
              </a-button>
            </a-form-item>
          </a-form>

          <div class="login-footer">
            <div class="demo-accounts">
              <p>测试账号：</p>
              <div class="account-tags">
                <a-tag color="default" @click="fillDemo('observer')">L1 观察员</a-tag>
                <a-tag color="green" @click="fillDemo('grower')">L2 成长者</a-tag>
                <a-tag color="cyan" @click="fillDemo('sharer')">L3 分享者</a-tag>
                <a-tag color="blue" @click="fillDemo('coach')">L4 教练</a-tag>
                <a-tag color="geekblue" @click="fillDemo('promoter')">L5 促进师</a-tag>
                <a-tag color="purple" @click="fillDemo('supervisor')">L5 督导</a-tag>
                <a-tag color="gold" @click="fillDemo('master')">L6 大师</a-tag>
                <a-tag color="orange" @click="fillDemo('admin')">L99 管理</a-tag>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部版权 -->
      <div class="login-copyright">
        <p>© 2024 行为健康平台 · 专注行为改变科学</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  UserOutlined,
  LockOutlined
} from '@ant-design/icons-vue'
import request from '@/api/request'

const router = useRouter()
const loading = ref(false)
const selectedRole = ref<string>('')
const rememberMe = ref(true)

const formState = reactive({
  username: '',
  password: ''
})


const getRoleIcon = (role: string) => {
  const icons: Record<string, string> = {
    observer: '👁️',
    grower: '🌱',
    sharer: '🤝',
    coach: '🧑‍⚕️',
    promoter: '🚀',
    supervisor: '👨‍🔬',
    master: '👑',
    admin: '⚙️'
  }
  return icons[role] || '🌱'
}

const getRoleName = (role: string) => {
  const names: Record<string, string> = {
    observer: '行为健康观察员',
    grower: '成长者',
    sharer: '分享者',
    coach: '健康教练',
    promoter: '行为健康促进师',
    supervisor: '促进师',
    master: '行为健康促进大师',
    admin: '系统管理员'
  }
  return names[role] || '用户'
}

const fillDemo = (role: string) => {
  selectedRole.value = role
  formState.username = role
  // 统一密码格式: 首字母大写 + @2026
  const pwd = role.charAt(0).toUpperCase() + role.slice(1) + '@2026'
  formState.password = pwd
}

// v18统一角色名称映射（用于 localStorage 和后台权限判断）
const ROLE_LEVELS: Record<string, number> = {
  observer: 1,
  grower: 2,
  sharer: 3,
  coach: 4,
  promoter: 5,
  supervisor: 5,
  master: 6,
  admin: 99,
}

const handleLogin = async () => {
  loading.value = true
  try {
    // 先尝试调用后端 API
    const params = new URLSearchParams()
    params.append('username', formState.username)
    params.append('password', formState.password)
    const res = await request.post('v1/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
    const data = res.data
    if (data.access_token) {
      saveLoginState(data.access_token, formState.username, data.user?.role || selectedRole.value, data.user?.level || 0, data.user?.full_name || data.user?.username || formState.username, data.user?.id)
      if (data.refresh_token) {
        localStorage.setItem('admin_refresh_token', data.refresh_token)
      }
      if (data.user?.avatar_url) {
        localStorage.setItem('admin_avatar', data.user.avatar_url)
      }
      navigateToHome(data.user?.role || selectedRole.value)
    } else {
      message.error('登录失败')
    }
  } catch (e: any) {
    const msg = e?.response?.data?.detail || '登录失败，请检查网络连接'
    message.error(msg)
  } finally {
    loading.value = false
  }
}

const saveLoginState = (token: string, username: string, role: string, level: number, name: string, userId?: number | string) => {
  localStorage.setItem('admin_token', token)
  localStorage.setItem('admin_username', username)
  localStorage.setItem('admin_role', role.toUpperCase())
  localStorage.setItem('admin_level', String(ROLE_LEVELS[role] || level))
  localStorage.setItem('admin_name', name)
  if (userId) localStorage.setItem('admin_user_id', String(userId))
}

const navigateToHome = (role: string) => {
  message.success(`登录成功，欢迎 ${getRoleName(role)}！`)
  const level = ROLE_LEVELS[role] || 0

  // 根据角色等级跳转到不同的首页
  if (level >= 99) {
    router.push('/dashboard')       // 管理员 → 工作台
  } else if (level >= 5) {
    router.push('/expert-portal')   // 促进师/督导/大师 → 专家门户
  } else if (level >= 4) {
    router.push('/coach-portal')    // 教练 → 教练门户
  } else {
    router.push('/client')          // 观察员/成长者/分享者 → 客户端
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-wrapper {
  width: 100%;
  max-width: 480px;
}

.login-brand {
  text-align: center;
  margin-bottom: 32px;
}

.brand-logo {
  font-size: 48px;
  margin-bottom: 12px;
}

.brand-title {
  font-size: 28px;
  color: #fff;
  font-weight: 600;
  margin-bottom: 8px;
}

.brand-subtitle {
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
}

.login-card {
  background: #fff;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
}

.step-title {
  font-size: 22px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
  text-align: center;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.forgot-link {
  color: #667eea;
  font-size: 13px;
}

.login-footer {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}

.demo-accounts p {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 8px;
}

.account-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.account-tags :deep(.ant-tag) {
  cursor: pointer;
  margin: 0;
}

.login-copyright {
  text-align: center;
  margin-top: 24px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
}
</style>
