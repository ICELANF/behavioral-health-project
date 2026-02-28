<template>
  <view class="reg-page">

    <!-- 背景装饰 -->
    <view class="reg-page__bg">
      <view class="reg-page__circle reg-page__circle--1"></view>
      <view class="reg-page__circle reg-page__circle--2"></view>
    </view>

    <!-- 顶部导航 -->
    <view class="reg-page__nav safe-area-top">
      <view class="reg-page__back" @tap="goBack">
        <text class="reg-page__back-icon">←</text>
        <text class="reg-page__back-text">返回</text>
      </view>
    </view>

    <!-- 标题 -->
    <view class="reg-page__header">
      <text class="reg-page__title">创建账号</text>
      <text class="reg-page__subtitle">加入行健平台，开启健康成长之旅</text>
    </view>

    <!-- 注册表单 -->
    <scroll-view class="reg-page__scroll" scroll-y>
      <view class="reg-page__form bhp-card px-4">

        <!-- 用户名 -->
        <view class="reg-field">
          <text class="reg-field__label">用户名 <text class="reg-field__required">*</text></text>
          <view class="bhp-input-wrap" :class="{ 'bhp-input-wrap--error': errors.username }">
            <text class="reg-field__icon">👤</text>
            <input
              class="bhp-input"
              v-model="form.username"
              placeholder="4-20位字母、数字或下划线"
              placeholder-class="input-placeholder"
              :maxlength="20"
              @blur="validateUsername"
            />
          </view>
          <text class="reg-field__error" v-if="errors.username">{{ errors.username }}</text>
        </view>

        <!-- 真实姓名 -->
        <view class="reg-field">
          <text class="reg-field__label">姓名</text>
          <view class="bhp-input-wrap">
            <text class="reg-field__icon">📝</text>
            <input
              class="bhp-input"
              v-model="form.full_name"
              placeholder="您的真实姓名（选填）"
              placeholder-class="input-placeholder"
              :maxlength="20"
            />
          </view>
        </view>

        <!-- 邮箱 -->
        <view class="reg-field">
          <text class="reg-field__label">邮箱 <text class="reg-field__required">*</text></text>
          <view class="bhp-input-wrap" :class="{ 'bhp-input-wrap--error': errors.email }">
            <text class="reg-field__icon">📧</text>
            <input
              class="bhp-input"
              v-model="form.email"
              placeholder="请输入邮箱地址"
              placeholder-class="input-placeholder"
              type="email"
              :maxlength="100"
              @blur="validateEmail"
            />
          </view>
          <text class="reg-field__error" v-if="errors.email">{{ errors.email }}</text>
        </view>

        <!-- 密码 -->
        <view class="reg-field">
          <text class="reg-field__label">密码 <text class="reg-field__required">*</text></text>
          <view class="bhp-input-wrap" :class="{ 'bhp-input-wrap--error': errors.password }">
            <text class="reg-field__icon">🔒</text>
            <input
              class="bhp-input"
              v-model="form.password"
              placeholder="8位以上，含字母和数字"
              placeholder-class="input-placeholder"
              :password="!showPwd"
              :maxlength="50"
              @blur="validatePassword"
            />
            <text class="reg-field__eye" @tap="showPwd = !showPwd">{{ showPwd ? '🙈' : '👁' }}</text>
          </view>
          <text class="reg-field__error" v-if="errors.password">{{ errors.password }}</text>
        </view>

        <!-- 确认密码 -->
        <view class="reg-field">
          <text class="reg-field__label">确认密码 <text class="reg-field__required">*</text></text>
          <view class="bhp-input-wrap" :class="{ 'bhp-input-wrap--error': errors.confirm }">
            <text class="reg-field__icon">🔑</text>
            <input
              class="bhp-input"
              v-model="form.confirm"
              placeholder="再次输入密码"
              placeholder-class="input-placeholder"
              :password="!showConfirm"
              :maxlength="50"
              @blur="validateConfirm"
            />
            <text class="reg-field__eye" @tap="showConfirm = !showConfirm">{{ showConfirm ? '🙈' : '👁' }}</text>
          </view>
          <text class="reg-field__error" v-if="errors.confirm">{{ errors.confirm }}</text>
        </view>

        <!-- 密码强度条 -->
        <view class="reg-strength" v-if="form.password">
          <view class="reg-strength__bar">
            <view
              class="reg-strength__fill"
              :class="`reg-strength__fill--${passwordStrength.level}`"
              :style="{ width: passwordStrength.pct + '%' }"
            ></view>
          </view>
          <text class="reg-strength__label" :class="`reg-strength__label--${passwordStrength.level}`">
            {{ passwordStrength.text }}
          </text>
        </view>

        <!-- 协议 -->
        <view class="reg-agree" @tap="agreed = !agreed">
          <view class="reg-agree__box" :class="{ 'reg-agree__box--checked': agreed }">
            <text v-if="agreed" class="reg-agree__check">✓</text>
          </view>
          <text class="reg-agree__text">
            我已阅读并同意
            <text class="reg-agree__link">《用户服务协议》</text>
            和
            <text class="reg-agree__link">《隐私政策》</text>
          </text>
        </view>
        <text class="reg-field__error" v-if="errors.agree">{{ errors.agree }}</text>

        <!-- 注册按钮 -->
        <button
          class="bhp-btn bhp-btn--primary bhp-btn--full bhp-btn--lg reg-submit"
          :class="{ 'bhp-btn--disabled': loading }"
          :loading="loading"
          @tap="handleRegister"
        >
          <text v-if="!loading">注 册</text>
          <text v-else>注册中...</text>
        </button>

        <!-- 已有账号 -->
        <view class="reg-login flex-center">
          <text class="reg-login__text">已有账号？</text>
          <text class="reg-login__link" @tap="goLogin">立即登录</text>
        </view>

      </view>
      <view style="height: 60rpx;"></view>
    </scroll-view>

  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import authApi from '@/api/auth'

const userStore = useUserStore()
const loading     = ref(false)
const showPwd     = ref(false)
const showConfirm = ref(false)
const agreed      = ref(false)

const form = reactive({
  username:  '',
  full_name: '',
  email:     '',
  password:  '',
  confirm:   '',
})
const errors = reactive({
  username: '',
  email:    '',
  password: '',
  confirm:  '',
  agree:    '',
})

// ─── 密码强度 ─────────────────────────────────────────────────
const passwordStrength = computed(() => {
  const p = form.password
  if (!p) return { level: 'weak', pct: 0, text: '' }
  let score = 0
  if (p.length >= 8)  score++
  if (p.length >= 12) score++
  if (/[A-Z]/.test(p)) score++
  if (/[0-9]/.test(p)) score++
  if (/[^A-Za-z0-9]/.test(p)) score++
  if (score <= 1) return { level: 'weak',   pct: 33,  text: '弱' }
  if (score <= 3) return { level: 'medium', pct: 66,  text: '中' }
  return              { level: 'strong', pct: 100, text: '强' }
})

// ─── 校验 ──────────────────────────────────────────────────────
function validateUsername() {
  const v = form.username.trim()
  if (!v) { errors.username = '请输入用户名'; return }
  if (v.length < 4) { errors.username = '用户名至少4位'; return }
  if (!/^[A-Za-z0-9_]+$/.test(v)) { errors.username = '只能包含字母、数字和下划线'; return }
  errors.username = ''
}
function validateEmail() {
  const v = form.email.trim()
  if (!v) { errors.email = '请输入邮箱'; return }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) { errors.email = '邮箱格式不正确'; return }
  errors.email = ''
}
function validatePassword() {
  const v = form.password
  if (!v) { errors.password = '请输入密码'; return }
  if (v.length < 8) { errors.password = '密码至少8位'; return }
  if (!/[A-Za-z]/.test(v) || !/[0-9]/.test(v)) { errors.password = '密码须包含字母和数字'; return }
  errors.password = ''
}
function validateConfirm() {
  if (!form.confirm) { errors.confirm = '请再次输入密码'; return }
  if (form.confirm !== form.password) { errors.confirm = '两次密码不一致'; return }
  errors.confirm = ''
}
function validate(): boolean {
  validateUsername()
  validateEmail()
  validatePassword()
  validateConfirm()
  if (!agreed.value) { errors.agree = '请先同意用户协议' } else { errors.agree = '' }
  return !errors.username && !errors.email && !errors.password && !errors.confirm && !errors.agree
}

// ─── 注册 ──────────────────────────────────────────────────────
async function handleRegister() {
  if (!validate() || loading.value) return
  loading.value = true
  try {
    const res = await authApi.register({
      username:  form.username.trim(),
      password:  form.password,
      email:     form.email.trim(),
      full_name: form.full_name.trim() || undefined,
    })
    userStore.setAuth(
      { access_token: res.access_token, refresh_token: res.refresh_token },
      res.user
    )
    uni.showToast({ title: '注册成功，欢迎加入！', icon: 'success' })
    setTimeout(() => {
      uni.reLaunch({ url: '/pages/home/index' })
    }, 1200)
  } catch (err: any) {
    const msg = err?.data?.detail || '注册失败，请检查信息后重试'
    uni.showToast({ title: msg, icon: 'none', duration: 2500 })
  } finally {
    loading.value = false
  }
}

function goBack()  { uni.navigateBack() }
function goLogin() { uni.navigateBack() }
</script>

<style scoped>
.reg-page {
  min-height: 100vh;
  background: var(--bhp-gray-50);
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 背景 */
.reg-page__bg { position: absolute; inset: 0; pointer-events: none; }
.reg-page__circle {
  position: absolute; border-radius: 50%; opacity: 0.07;
  background: var(--bhp-primary-500);
}
.reg-page__circle--1 { width: 360rpx; height: 360rpx; top: -80rpx; right: -60rpx; }
.reg-page__circle--2 { width: 240rpx; height: 240rpx; bottom: 150rpx; left: -50rpx; background: var(--bhp-accent-500); }

/* 导航栏 */
.reg-page__nav {
  display: flex; align-items: center;
  padding: 12rpx 32rpx 0;
  z-index: 1;
}
.reg-page__back {
  display: flex; align-items: center; gap: 8rpx;
  padding: 12rpx 0; cursor: pointer;
}
.reg-page__back-icon { font-size: 32rpx; color: var(--text-primary); font-weight: 600; }
.reg-page__back-text { font-size: 28rpx; color: var(--text-primary); }

/* 标题 */
.reg-page__header {
  display: flex; flex-direction: column;
  padding: 24rpx 32rpx 20rpx;
  z-index: 1;
}
.reg-page__title    { font-size: 44rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 8rpx; }
.reg-page__subtitle { font-size: 24rpx; color: var(--text-secondary); }

/* 滚动区 */
.reg-page__scroll { flex: 1; }
.reg-page__form   { margin: 0 0 0; padding: 32rpx 28rpx; z-index: 1; }

/* 字段 */
.reg-field { margin-bottom: 24rpx; }
.reg-field__label {
  display: block; font-size: 26rpx; font-weight: 600;
  color: var(--text-primary); margin-bottom: 10rpx;
}
.reg-field__required { color: var(--bhp-danger); font-size: 26rpx; }
.reg-field__icon     { font-size: 28rpx; flex-shrink: 0; }
.reg-field__eye      { font-size: 28rpx; flex-shrink: 0; cursor: pointer; padding: 0 4rpx; }
.reg-field__error    { display: block; font-size: 22rpx; color: var(--bhp-danger); margin-top: 6rpx; }

/* 密码强度 */
.reg-strength { display: flex; align-items: center; gap: 16rpx; margin-top: -12rpx; margin-bottom: 24rpx; }
.reg-strength__bar  { flex: 1; height: 6rpx; background: var(--bhp-gray-200); border-radius: var(--radius-full); overflow: hidden; }
.reg-strength__fill { height: 100%; border-radius: var(--radius-full); transition: width 0.3s; }
.reg-strength__fill--weak   { background: #ff4d4f; }
.reg-strength__fill--medium { background: #fa8c16; }
.reg-strength__fill--strong { background: #52c41a; }
.reg-strength__label        { font-size: 22rpx; flex-shrink: 0; }
.reg-strength__label--weak   { color: #ff4d4f; }
.reg-strength__label--medium { color: #fa8c16; }
.reg-strength__label--strong { color: #52c41a; }

/* 协议 */
.reg-agree {
  display: flex; align-items: flex-start; gap: 12rpx;
  margin-bottom: 8rpx; cursor: pointer;
}
.reg-agree__box {
  width: 32rpx; height: 32rpx; border: 2rpx solid var(--border);
  border-radius: 6rpx; flex-shrink: 0; margin-top: 2rpx;
  display: flex; align-items: center; justify-content: center;
  background: var(--surface);
  transition: background 0.2s, border-color 0.2s;
}
.reg-agree__box--checked { background: var(--bhp-primary-500); border-color: var(--bhp-primary-500); }
.reg-agree__check  { font-size: 20rpx; color: #fff; font-weight: 700; }
.reg-agree__text   { font-size: 24rpx; color: var(--text-secondary); line-height: 1.6; flex: 1; }
.reg-agree__link   { color: var(--bhp-primary-500); }

/* 按钮 */
.reg-submit { margin-top: 24rpx; margin-bottom: 24rpx; }

/* 登录入口 */
.reg-login { gap: 8rpx; }
.reg-login__text { font-size: 26rpx; color: var(--text-secondary); }
.reg-login__link { font-size: 26rpx; color: var(--bhp-primary-500); font-weight: 600; }

/* placeholder */
.input-placeholder { color: var(--text-tertiary); font-size: 28rpx; }
</style>
