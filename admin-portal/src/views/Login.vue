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
        <!-- 步骤一：选择身份 -->
        <div v-if="step === 'role'" class="step-content">
          <h2 class="step-title">选择您的身份</h2>
          <p class="step-desc">请选择您要登录的身份类型</p>

          <div class="role-grid">
            <div
              class="role-card"
              :class="{ selected: selectedRole === 'patient' }"
              @click="selectRole('patient')"
            >
              <div class="role-icon patient">👤</div>
              <div class="role-info">
                <div class="role-name">自我管理</div>
                <div class="role-desc">管理个人健康，完成任务打卡</div>
              </div>
              <div class="role-check" v-if="selectedRole === 'patient'">
                <CheckCircleFilled />
              </div>
            </div>

            <div
              class="role-card"
              :class="{ selected: selectedRole === 'coach' }"
              @click="selectRole('coach')"
            >
              <div class="role-icon coach">🧑‍⚕️</div>
              <div class="role-info">
                <div class="role-name">健康教练</div>
                <div class="role-desc">管理学员，执行干预，跟进健康</div>
              </div>
              <div class="role-check" v-if="selectedRole === 'coach'">
                <CheckCircleFilled />
              </div>
            </div>

            <div
              class="role-card"
              :class="{ selected: selectedRole === 'expert' }"
              @click="selectRole('expert')"
            >
              <div class="role-icon expert">👨‍🔬</div>
              <div class="role-info">
                <div class="role-name">督导专家</div>
                <div class="role-desc">督导教练，审核晋级，培训直播</div>
              </div>
              <div class="role-check" v-if="selectedRole === 'expert'">
                <CheckCircleFilled />
              </div>
            </div>

            <div
              class="role-card"
              :class="{ selected: selectedRole === 'admin' }"
              @click="selectRole('admin')"
            >
              <div class="role-icon admin">⚙️</div>
              <div class="role-info">
                <div class="role-name">系统管理</div>
                <div class="role-desc">平台配置，用户管理，数据统计</div>
              </div>
              <div class="role-check" v-if="selectedRole === 'admin'">
                <CheckCircleFilled />
              </div>
            </div>
          </div>

          <a-button
            type="primary"
            size="large"
            block
            :disabled="!selectedRole"
            @click="goToLogin"
          >
            下一步
          </a-button>
        </div>

        <!-- 步骤二：登录表单 -->
        <div v-else class="step-content">
          <div class="login-header">
            <a class="back-link" @click="step = 'role'">
              <ArrowLeftOutlined /> 返回选择身份
            </a>
            <div class="current-role">
              <span class="role-badge" :class="selectedRole">
                {{ getRoleIcon(selectedRole) }} {{ getRoleName(selectedRole) }}
              </span>
            </div>
          </div>

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
                <a class="forgot-link">忘记密码？</a>
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
                <a-tag color="blue" @click="fillDemo('patient')">patient / 123456</a-tag>
                <a-tag color="green" @click="fillDemo('coach')">coach / 123456</a-tag>
                <a-tag color="purple" @click="fillDemo('expert')">expert / 123456</a-tag>
                <a-tag color="orange" @click="fillDemo('admin')">admin / admin123</a-tag>
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
  LockOutlined,
  CheckCircleFilled,
  ArrowLeftOutlined
} from '@ant-design/icons-vue'
import request from '@/api/request'

const router = useRouter()
const loading = ref(false)
const step = ref<'role' | 'login'>('role')
const selectedRole = ref<string>('')
const rememberMe = ref(true)

const formState = reactive({
  username: '',
  password: ''
})

// 模拟用户数据
const mockUsers: Record<string, { password: string; role: string; level: number; name: string }> = {
  admin: { password: 'admin123', role: 'admin', level: 4, name: '管理员' },
  expert: { password: '123456', role: 'expert', level: 3, name: '张专家' },
  coach: { password: '123456', role: 'coach', level: 2, name: '李教练' },
  patient: { password: '123456', role: 'patient', level: 0, name: '小明' }
}

const getRoleIcon = (role: string) => {
  const icons: Record<string, string> = {
    patient: '👤',
    coach: '🧑‍⚕️',
    expert: '👨‍🔬',
    admin: '⚙️'
  }
  return icons[role] || '👤'
}

const getRoleName = (role: string) => {
  const names: Record<string, string> = {
    patient: '自我管理',
    coach: '健康教练',
    expert: '督导专家',
    admin: '系统管理'
  }
  return names[role] || '用户'
}

const selectRole = (role: string) => {
  selectedRole.value = role
}

const goToLogin = () => {
  step.value = 'login'
}

const fillDemo = (role: string) => {
  selectedRole.value = role
  formState.username = role
  formState.password = role === 'admin' ? 'admin123' : '123456'
}

const handleLogin = async () => {
  loading.value = true
  try {
    // 先尝试调用后端 API
    const res = await request.post('/auth/login', {
      username: formState.username,
      password: formState.password,
      role: selectedRole.value
    })
    const data = res.data
    if (data.success && data.token) {
      saveLoginState(data.token, formState.username, data.user?.role || selectedRole.value, data.user?.level || 0, data.user?.name || formState.username)
      navigateToHome(data.user?.role || selectedRole.value)
    } else {
      message.error('登录失败')
    }
  } catch {
    // 后端不可用时使用模拟登录
    const user = mockUsers[formState.username]
    if (user && user.password === formState.password) {
      // 检查角色是否匹配
      if (user.role !== selectedRole.value && selectedRole.value !== 'admin') {
        message.warning(`该账号是 ${getRoleName(user.role)} 身份，请选择正确的身份登录`)
        return
      }
      const mockToken = 'mock_token_' + Date.now()
      saveLoginState(mockToken, formState.username, user.role, user.level, user.name)
      navigateToHome(user.role)
    } else {
      message.error('用户名或密码错误')
    }
  } finally {
    loading.value = false
  }
}

const saveLoginState = (token: string, username: string, role: string, level: number, name: string) => {
  localStorage.setItem('admin_token', token)
  localStorage.setItem('admin_username', username)
  localStorage.setItem('admin_role', role)
  localStorage.setItem('admin_level', String(level))
  localStorage.setItem('admin_name', name)
}

const navigateToHome = (role: string) => {
  message.success(`登录成功，欢迎回来！`)

  // 根据角色跳转到不同的首页
  switch (role) {
    case 'patient':
      router.push('/client')
      break
    case 'coach':
      router.push('/coach-portal')
      break
    case 'expert':
      router.push('/expert-portal')
      break
    case 'admin':
    default:
      router.push('/dashboard')
      break
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

.step-desc {
  color: #6b7280;
  font-size: 14px;
  text-align: center;
  margin-bottom: 24px;
}

/* 角色选择网格 */
.role-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

.role-card {
  position: relative;
  padding: 16px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.role-card:hover {
  border-color: #667eea;
  background: #f8faff;
}

.role-card.selected {
  border-color: #667eea;
  background: linear-gradient(135deg, #f0f5ff 0%, #e8efff 100%);
}

.role-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.role-name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.role-desc {
  font-size: 11px;
  color: #6b7280;
  line-height: 1.4;
}

.role-check {
  position: absolute;
  top: 8px;
  right: 8px;
  color: #667eea;
  font-size: 18px;
}

/* 登录表单 */
.login-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.back-link {
  color: #6b7280;
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}

.back-link:hover {
  color: #667eea;
}

.role-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.role-badge.patient {
  background: #e0f2fe;
  color: #0369a1;
}

.role-badge.coach {
  background: #dcfce7;
  color: #16a34a;
}

.role-badge.expert {
  background: #f3e8ff;
  color: #9333ea;
}

.role-badge.admin {
  background: #fef3c7;
  color: #d97706;
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
