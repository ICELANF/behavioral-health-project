<template>
  <div class="login-page">
    <div class="login-header">
      <div class="logo-icon">
        <van-icon name="shield-o" size="48" color="#1989fa" />
      </div>
      <h1>行健行为教练</h1>
      <p>您的专属行为健康管理伙伴</p>
    </div>

    <!-- 登录方式切换 -->
    <van-tabs v-model:active="loginTab" class="login-tabs" shrink>
      <van-tab title="账号密码">
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
      </van-tab>

      <van-tab title="手机验证码">
        <div class="login-form">
          <van-cell-group inset>
            <van-field
              v-model="smsForm.phone"
              type="tel"
              label="手机号"
              placeholder="请输入手机号"
              maxlength="11"
              :rules="[{ pattern: /^1\d{10}$/, message: '请输入正确的手机号' }]"
            />
            <van-field
              v-model="smsForm.code"
              type="digit"
              label="验证码"
              placeholder="请输入验证码"
              maxlength="6"
            >
              <template #button>
                <van-button
                  size="small"
                  type="primary"
                  plain
                  :disabled="smsCooldown > 0 || !isPhoneValid"
                  @click="sendSmsCode"
                >
                  {{ smsCooldown > 0 ? `${smsCooldown}s` : '发送验证码' }}
                </van-button>
              </template>
            </van-field>
          </van-cell-group>

          <div class="form-actions">
            <van-button
              type="primary"
              block
              round
              size="large"
              :loading="loading"
              loading-text="登录中..."
              :disabled="!smsForm.phone || !smsForm.code"
              @click="handleSmsLogin"
            >
              登录
            </van-button>
          </div>

          <p class="sms-hint">未注册的手机号将自动创建账号</p>
        </div>
      </van-tab>
    </van-tabs>

    <!-- 微信登录 -->
    <div class="wechat-login-section">
      <div class="divider">
        <span>其他登录方式</span>
      </div>
      <van-button
        class="wechat-btn"
        :class="{ 'wechat-btn-disabled': !wechatConfigured }"
        block
        round
        plain
        @click="handleWechatLogin"
      >
        <van-icon name="wechat" size="20" :color="wechatConfigured ? '#07C160' : '#ccc'" />
        <span>{{ isWechatBrowser ? '微信一键登录' : '微信扫码登录' }}</span>
      </van-button>
      <p v-if="!wechatConfigured" class="wechat-hint">微信登录需管理员配置 (WECHAT_APP_ID)</p>
      <p v-else-if="!isWechatBrowser" class="wechat-hint">请使用微信扫描二维码完成登录</p>
    </div>

    <!-- 快速体验入口 (仅开发环境) — 全角色切换 -->
    <div v-if="isDev" class="quick-login">
      <div class="quick-header">
        <span class="quick-title">角色切换</span>
        <span class="quick-hint">开发测试专用</span>
      </div>

      <!-- 基础角色 L0-L2 -->
      <div class="role-group">
        <div class="role-group-label">基础</div>
        <div class="role-buttons">
          <div class="role-btn" @click="quickLogin('observer')">
            <div class="role-icon" style="background:#e8f5e9;color:#43a047">L0</div>
            <span class="role-name">观察员</span>
          </div>
          <div class="role-btn" @click="quickLogin('grower')">
            <div class="role-icon" style="background:#e3f2fd;color:#1e88e5">L1</div>
            <span class="role-name">成长者</span>
          </div>
          <div class="role-btn" @click="quickLogin('sharer')">
            <div class="role-icon" style="background:#fff3e0;color:#fb8c00">L2</div>
            <span class="role-name">分享者</span>
          </div>
        </div>
      </div>

      <!-- 进阶角色 L3-L5 -->
      <div class="role-group">
        <div class="role-group-label">进阶</div>
        <div class="role-buttons">
          <div class="role-btn" @click="quickLogin('coach')">
            <div class="role-icon" style="background:#e8eaf6;color:#5c6bc0">L3</div>
            <span class="role-name">教练</span>
          </div>
          <div class="role-btn" @click="quickLogin('promoter')">
            <div class="role-icon" style="background:#fce4ec;color:#e53935">L4</div>
            <span class="role-name">促进师</span>
          </div>
          <div class="role-btn" @click="quickLogin('supervisor')">
            <div class="role-icon" style="background:#f3e5f5;color:#8e24aa">L4</div>
            <span class="role-name">督导</span>
          </div>
          <div class="role-btn" @click="quickLogin('master')">
            <div class="role-icon" style="background:#fff8e1;color:#f9a825">L5</div>
            <span class="role-name">大师</span>
          </div>
        </div>
      </div>

      <!-- 管理角色 -->
      <div class="role-group">
        <div class="role-group-label">管理</div>
        <div class="role-buttons">
          <div class="role-btn" @click="quickLogin('admin')">
            <div class="role-icon" style="background:#ffebee;color:#c62828">99</div>
            <span class="role-name">管理员</span>
          </div>
        </div>
      </div>
    </div>

    <div class="login-footer">
      <p class="register-link">
        还没有账号？<router-link to="/register">立即注册</router-link>
      </p>
      <p>登录即表示您同意 <router-link to="/privacy-policy">用户协议</router-link> 和 <router-link to="/privacy-policy">隐私政策</router-link></p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast, showLoadingToast, closeToast } from 'vant'
import api from '@/api/index'
import storage from '@/utils/storage'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const loading = ref(false)
const isDev = import.meta.env.DEV
const loginTab = ref(0)

// ── 账号密码登录 ──
const form = reactive({
  username: '',
  password: '',
})

// ── 手机验证码登录 ──
const smsForm = reactive({
  phone: '',
  code: '',
})
const smsCooldown = ref(0)
let cooldownTimer: ReturnType<typeof setInterval> | null = null

const isPhoneValid = computed(() => /^1\d{10}$/.test(smsForm.phone))

// 微信登录: 始终显示按钮，未配置时点击提示
const showWechatLogin = ref(true)
const isWechatBrowser = ref(false)
const wechatConfigured = ref(false)

onMounted(async () => {
  // 检测微信浏览器环境
  const ua = navigator.userAgent.toLowerCase()
  isWechatBrowser.value = ua.includes('micromessenger')

  // 检查后端微信配置状态
  try {
    const res: any = await api.get('/api/v1/auth/wechat/config')
    wechatConfigured.value = !!res.configured
  } catch {
    wechatConfigured.value = false
  }
})

onUnmounted(() => {
  if (cooldownTimer) clearInterval(cooldownTimer)
})

// 演示账号仅在开发环境可用 — 全 8 角色
const demoAccounts: Record<string, { password: string; label: string }> = isDev ? {
  observer:   { password: 'Observer@2026',   label: '观察员' },
  grower:     { password: 'Grower@2026',     label: '成长者' },
  sharer:     { password: 'Sharer@2026',     label: '分享者' },
  coach:      { password: 'Coach@2026',      label: '教练' },
  promoter:   { password: 'Promoter@2026',   label: '促进师' },
  supervisor: { password: 'Supervisor@2026', label: '督导' },
  master:     { password: 'Master@2026',     label: '大师' },
  admin:      { password: 'Admin@2026',      label: '管理员' },
} : {}

function quickLogin(role: string) {
  if (!isDev) return
  const account = demoAccounts[role]
  if (!account) return
  form.username = role
  form.password = account.password
  handleLogin()
}

function saveLoginResult(res: any) {
  storage.setToken(res.access_token)
  if (res.refresh_token) {
    localStorage.setItem('refresh_token', res.refresh_token)
  }
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
}

function navigateAfterLogin() {
  const redirect = (route.query.redirect as string) || '/'
  router.replace(redirect)
}

// ── 账号密码登录 ──
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

    saveLoginResult(res)
    closeToast()
    showToast({ message: '登录成功', type: 'success' })
    navigateAfterLogin()
  } catch (e: any) {
    closeToast()
    const msg = e.response?.data?.detail || '登录失败，请检查用户名和密码'
    showToast(msg)
  } finally {
    loading.value = false
  }
}

// ── 发送验证码 ──
async function sendSmsCode() {
  if (!isPhoneValid.value || smsCooldown.value > 0) return

  try {
    await api.post('/api/v1/auth/send-sms-code', { phone: smsForm.phone })
    showToast({ message: '验证码已发送', type: 'success' })

    // 开始倒计时
    smsCooldown.value = 60
    cooldownTimer = setInterval(() => {
      smsCooldown.value--
      if (smsCooldown.value <= 0) {
        if (cooldownTimer) clearInterval(cooldownTimer)
        cooldownTimer = null
      }
    }, 1000)
  } catch (e: any) {
    const msg = e.response?.data?.detail || '发送失败，请稍后重试'
    showToast(msg)
  }
}

// ── 验证码登录 ──
async function handleSmsLogin() {
  if (!smsForm.phone || !smsForm.code) {
    showToast('请输入手机号和验证码')
    return
  }

  loading.value = true
  showLoadingToast({ message: '登录中...', forbidClick: true })
  try {
    const res: any = await api.post('/api/v1/auth/sms-login', {
      phone: smsForm.phone,
      code: smsForm.code,
    })

    saveLoginResult(res)
    closeToast()
    showToast({ message: '登录成功', type: 'success' })
    navigateAfterLogin()
  } catch (e: any) {
    closeToast()
    const msg = e.response?.data?.detail || '登录失败'
    showToast(msg)
  } finally {
    loading.value = false
  }
}

// ── 微信登录 ──
async function handleWechatLogin() {
  if (!wechatConfigured.value) {
    showToast('微信登录尚未配置，请联系管理员设置 WECHAT_APP_ID')
    return
  }

  try {
    const currentUrl = window.location.origin + '/wechat/callback'
    const res: any = await api.get('/api/v1/auth/wechat/login', {
      params: { redirect_uri: currentUrl }
    })
    // 后端返回 oauth_url (非 url)
    const authUrl = res.oauth_url || res.url
    if (authUrl) {
      window.location.href = authUrl
    } else {
      showToast('微信登录暂不可用')
    }
  } catch {
    showToast('微信登录暂不可用')
  }
}
</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 40px 20px 24px;
  background: linear-gradient(135deg, #e8f4fd 0%, #f0f7ff 50%, #fff 100%);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;

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

.login-tabs {
  :deep(.van-tabs__wrap) {
    border-radius: 12px;
  }
}

.login-form {
  padding-top: 16px;

  .form-actions {
    padding: 24px 16px 0;
  }
}

.sms-hint {
  text-align: center;
  font-size: 12px;
  color: #999;
  margin-top: 12px;
}

.wechat-login-section {
  margin-top: 24px;
  padding: 0 16px;
}

.divider {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  color: #ccc;
  font-size: 12px;

  &::before,
  &::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #eee;
  }

  span {
    padding: 0 12px;
    color: #999;
  }
}

.wechat-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 44px;
  border-color: #07C160;
  color: #07C160;
  font-size: 15px;
}

.wechat-btn-disabled {
  border-color: #ddd !important;
  color: #bbb !important;
}

.wechat-hint {
  text-align: center;
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}

.quick-login {
  margin-top: 24px;
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);

  .quick-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }

  .quick-title {
    font-size: 14px;
    font-weight: 600;
    color: #333;
  }

  .quick-hint {
    font-size: 11px;
    color: #bbb;
    background: #f5f5f5;
    padding: 2px 8px;
    border-radius: 10px;
  }

  .role-group {
    margin-bottom: 10px;

    &:last-child {
      margin-bottom: 0;
    }
  }

  .role-group-label {
    font-size: 11px;
    color: #bbb;
    margin-bottom: 6px;
    padding-left: 2px;
  }

  .role-buttons {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }

  .role-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px 6px 6px;
    border: 1px solid #eee;
    border-radius: 20px;
    cursor: pointer;
    transition: all 0.2s;

    &:active {
      background: #f0f7ff;
      border-color: #1989fa;
    }
  }

  .role-icon {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
  }

  .role-name {
    font-size: 13px;
    color: #333;
    font-weight: 500;
  }
}

.login-footer {
  text-align: center;
  margin-top: auto;
  padding-top: 24px;
  font-size: 12px;
  color: #999;

  .register-link {
    font-size: 14px;
    margin-bottom: 12px;
  }

  a {
    color: #1989fa;
    text-decoration: none;
  }
}
</style>
