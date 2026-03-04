<template>
  <view class="login-page safe-area-top">

    <!-- 背景装饰 -->
    <view class="login-page__bg">
      <view class="login-page__circle login-page__circle--1"></view>
      <view class="login-page__circle login-page__circle--2"></view>
    </view>

    <!-- Logo + 标题 -->
    <view class="login-page__header">
      <image class="login-page__logo" src="/static/logo.png" mode="aspectFit" />
      <text class="login-page__title">行健平台</text>
      <text class="login-page__subtitle">行为重塑 · 认知重塑 · 大脑重塑</text>
    </view>

    <!-- 登录表单 -->
    <view class="login-page__form bhp-card">

      <!-- 微信一键登录（小程序首选）-->
      <view class="login-page__wx-btn" @tap="handleWxLogin" v-if="isMiniprogram">
        <text class="login-page__wx-icon">💬</text>
        <text class="login-page__wx-text">微信一键登录</text>
      </view>

      <view class="login-page__divider" v-if="isMiniprogram">
        <view class="login-page__divider-line"></view>
        <text class="login-page__divider-text">或账号登录</text>
        <view class="login-page__divider-line"></view>
      </view>

      <!-- 用户名 -->
      <view class="login-page__field">
        <text class="login-page__field-label">账号</text>
        <view class="bhp-input-wrap" :class="{ 'bhp-input-wrap--error': errors.username }">
          <text class="login-page__input-icon">👤</text>
          <input
            class="bhp-input"
            v-model="form.username"
            placeholder="请输入用户名"
            placeholder-class="input-placeholder"
            :maxlength="50"
            @blur="validateUsername"
          />
        </view>
        <text class="login-page__error" v-if="errors.username">{{ errors.username }}</text>
      </view>

      <!-- 密码 -->
      <view class="login-page__field">
        <text class="login-page__field-label">密码</text>
        <view class="bhp-input-wrap" :class="{ 'bhp-input-wrap--error': errors.password }">
          <text class="login-page__input-icon">🔒</text>
          <!-- v-if/v-else 强制销毁重建，否则微信原生 input 不响应 password 动态切换 -->
          <input
            v-if="showPwd"
            class="bhp-input"
            v-model="form.password"
            placeholder="请输入密码"
            placeholder-class="input-placeholder"
            :maxlength="50"
            @blur="validatePassword"
          />
          <input
            v-else
            class="bhp-input"
            v-model="form.password"
            placeholder="请输入密码"
            placeholder-class="input-placeholder"
            password
            :maxlength="50"
            @blur="validatePassword"
          />
          <text class="login-page__pwd-eye" @tap="showPwd = !showPwd">
            {{ showPwd ? '🙈' : '👁' }}
          </text>
        </view>
        <text class="login-page__error" v-if="errors.password">{{ errors.password }}</text>
      </view>

      <!-- 登录按钮 -->
      <button
        class="bhp-btn bhp-btn--primary bhp-btn--full bhp-btn--lg login-page__submit"
        :class="{ 'bhp-btn--disabled': loading }"
        :loading="loading"
        @tap="handleLogin"
      >
        <text v-if="!loading">登 录</text>
        <text v-else>登录中...</text>
      </button>

      <!-- 注册入口 -->
      <view class="login-page__register flex-center">
        <text class="login-page__register-text">还没有账号？</text>
        <text class="login-page__register-link" @tap="goRegister">立即注册</text>
      </view>

    </view>

    <!-- 底部版权 -->
    <text class="login-page__footer">北京康润普科信息技术有限公司</text>

  </view>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import authApi from '@/api/auth'
import { wechatLogin, isMiniprogram } from '@/utils/wechat'

const userStore = useUserStore()
const loading   = ref(false)
const showPwd   = ref(false)

const form   = reactive({ username: '', password: '' })
const errors = reactive({ username: '', password: '' })

function validateUsername() {
  errors.username = form.username.trim() ? '' : '请输入账号'
}
function validatePassword() {
  errors.password = form.password ? '' : '请输入密码'
}
function validate(): boolean {
  validateUsername(); validatePassword()
  return !errors.username && !errors.password
}

async function handleLogin() {
  if (!validate() || loading.value) return
  loading.value = true
  try {
    const res = await authApi.login({
      username: form.username.trim(),
      password: form.password,
    })
    userStore.setAuth(
      { access_token: res.access_token, refresh_token: res.refresh_token },
      res.user
    )
    afterLogin()
  } catch (err: any) {
    const msg = err?.data?.detail || '账号或密码错误，请确认后重试'
    uni.showModal({ title: '登录失败', content: String(msg), showCancel: false, confirmText: '好的' })
  } finally {
    loading.value = false
  }
}

async function handleWxLogin() {
  if (loading.value) return
  loading.value = true
  try {
    const ok = await wechatLogin()
    if (ok) afterLogin()
    else uni.showToast({ title: '微信登录失败，请重试', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function afterLogin() {
  uni.reLaunch({ url: '/pages/home/index' })
}

function goRegister() {
  uni.navigateTo({ url: '/pages/auth/register' })
}

onMounted(() => {
  userStore.restoreFromStorage()
  if (userStore.isLoggedIn) afterLogin()
})
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: var(--bhp-gray-50);
  position: relative; overflow: hidden;
  display: flex; flex-direction: column; align-items: center;
  padding: 0 32rpx;
}

/* 背景装饰圆 */
.login-page__bg { position: absolute; inset: 0; pointer-events: none; }
.login-page__circle {
  position: absolute; border-radius: 50%; opacity: 0.08;
  background: var(--bhp-primary-500);
}
.login-page__circle--1 { width: 400rpx; height: 400rpx; top: -100rpx; right: -80rpx; }
.login-page__circle--2 { width: 280rpx; height: 280rpx; bottom: 100rpx; left: -60rpx; background: var(--bhp-accent-500); }

/* Logo */
.login-page__header {
  display: flex; flex-direction: column; align-items: center;
  margin-top: 100rpx; margin-bottom: 48rpx; z-index: 1;
}
.login-page__logo      { width: 120rpx; height: 120rpx; margin-bottom: 16rpx; }
.login-page__title     { font-size: 48rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 8rpx; }
.login-page__subtitle  { font-size: 24rpx; color: var(--text-secondary); letter-spacing: 1px; }

/* 表单 */
.login-page__form { width: 100%; z-index: 1; padding: 32rpx 28rpx; }

/* 微信按钮 */
.login-page__wx-btn {
  display: flex; align-items: center; justify-content: center; gap: 12rpx;
  background: #07c160; border-radius: var(--radius-md);
  padding: 24rpx; margin-bottom: 24rpx; cursor: pointer;
}
.login-page__wx-btn:active { opacity: 0.85; }
.login-page__wx-icon { font-size: 36rpx; }
.login-page__wx-text { font-size: 32rpx; font-weight: 600; color: #fff; }

/* 分割线 */
.login-page__divider {
  display: flex; align-items: center; gap: 16rpx; margin-bottom: 24rpx;
}
.login-page__divider-line { flex: 1; height: 1px; background: var(--border); }
.login-page__divider-text { font-size: 22rpx; color: var(--text-tertiary); white-space: nowrap; }

/* 字段 */
.login-page__field           { margin-bottom: 24rpx; }
.login-page__field-label     { display: block; font-size: 26rpx; font-weight: 600; color: var(--text-primary); margin-bottom: 10rpx; }
.login-page__input-icon      { font-size: 28rpx; flex-shrink: 0; }
.login-page__pwd-eye         { font-size: 28rpx; flex-shrink: 0; cursor: pointer; padding: 0 4rpx; }
.login-page__error           { display: block; font-size: 22rpx; color: var(--bhp-danger); margin-top: 6rpx; }
.login-page__submit          { margin-top: 8rpx; margin-bottom: 24rpx; }
.login-page__register        { gap: 8rpx; }
.login-page__register-text   { font-size: 26rpx; color: var(--text-secondary); }
.login-page__register-link   { font-size: 26rpx; color: var(--bhp-primary-500); font-weight: 600; }

/* 版权 */
.login-page__footer {
  position: absolute; bottom: 40rpx;
  font-size: 22rpx; color: var(--text-tertiary);
}

.input-placeholder { color: var(--text-tertiary); font-size: 28rpx; }
</style>
