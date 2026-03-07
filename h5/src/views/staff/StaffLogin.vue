<template>
  <div class="staff-login">
    <div class="login-card">
      <div class="login-logo">
        <div class="logo-mark">行健</div>
        <div class="login-titles">
          <h1>Staff Portal</h1>
          <p>教练 · 督导 · 大师 · 管理员</p>
        </div>
      </div>

      <div class="login-form">
        <div class="field-group">
          <label>用户名</label>
          <input v-model="form.username" type="text" placeholder="请输入用户名" @keyup.enter="handleLogin" />
        </div>
        <div class="field-group">
          <label>密码</label>
          <input v-model="form.password" type="password" placeholder="请输入密码" @keyup.enter="handleLogin" />
        </div>

        <button class="login-btn" :disabled="loading" @click="handleLogin">
          {{ loading ? '登录中...' : '登录' }}
        </button>

        <p v-if="error" class="error-msg">{{ error }}</p>
      </div>

      <!-- 开发环境快速切换 -->
      <div v-if="isDev" class="quick-roles">
        <p class="quick-title">快速切换角色（开发专用）</p>
        <div class="role-chips">
          <button v-for="r in staffRoles" :key="r.role" class="role-chip" @click="quickLogin(r.role, r.pwd)">
            <span class="chip-label">{{ r.label }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/index'
import storage from '@/utils/storage'

const router = useRouter()
const isDev = import.meta.env.DEV

const loading = ref(false)
const error = ref('')
const form = reactive({ username: '', password: '' })

const staffRoles = [
  { role: 'coach',      label: '教练',    pwd: 'Coach@2026' },
  { role: 'supervisor', label: '督导',    pwd: 'Supervisor@2026' },
  { role: 'master',     label: '大师',    pwd: 'Master@2026' },
  { role: 'admin',      label: '管理员',  pwd: 'Admin@2026' },
]

const ROLE_DEST: Record<string, string> = {
  coach:      '/staff/coach/dashboard',
  promoter:   '/staff/supervisor/dashboard',
  supervisor: '/staff/supervisor/dashboard',
  master:     '/staff/master/dashboard',
  admin:      '/staff/admin/overview',
}

function quickLogin(role: string, pwd: string) {
  form.username = role
  form.password = pwd
  handleLogin()
}

async function handleLogin() {
  if (!form.username || !form.password) { error.value = '请输入用户名和密码'; return }
  loading.value = true
  error.value = ''
  try {
    const params = new URLSearchParams()
    params.append('username', form.username)
    params.append('password', form.password)
    const res: any = await api.post('/api/v1/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
    storage.setToken(res.access_token)
    if (res.refresh_token) localStorage.setItem('refresh_token', res.refresh_token)
    if (res.user) storage.setAuthUser(res.user)
    const role = (res.user?.role || 'coach').toLowerCase()
    router.replace(ROLE_DEST[role] || '/staff/coach/dashboard')
  } catch (e: any) {
    error.value = e.response?.data?.detail || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.staff-login {
  min-height: 100vh;
  background: linear-gradient(135deg, #1e2330 0%, #2d3748 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.login-card {
  background: #fff;
  border-radius: 16px;
  padding: 40px;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}

.login-logo {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 32px;
}

.logo-mark {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 15px;
  font-weight: 800;
  flex-shrink: 0;
}

.login-titles h1 {
  font-size: 20px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 4px;
}
.login-titles p {
  font-size: 12px;
  color: #9ca3af;
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-group label {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.field-group input {
  padding: 10px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  color: #111827;
  transition: border-color 0.15s;
  outline: none;
}

.field-group input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
}

.login-btn {
  margin-top: 4px;
  padding: 12px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
}

.login-btn:hover { opacity: 0.9; }
.login-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.error-msg {
  font-size: 13px;
  color: #ef4444;
  text-align: center;
  margin: 0;
}

.quick-roles {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #f3f4f6;
}

.quick-title {
  font-size: 11px;
  color: #9ca3af;
  margin: 0 0 10px;
  text-align: center;
}

.role-chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}

.role-chip {
  padding: 6px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  background: #f9fafb;
  cursor: pointer;
  transition: all 0.15s;
}

.role-chip:hover {
  background: #eff6ff;
  border-color: #3b82f6;
  color: #3b82f6;
}

.chip-label { font-size: 13px; }
</style>
