<template>
  <view class="reg-page">

    <view class="reg-header">
      <text class="reg-header__title">注册行健平台</text>
      <text class="reg-header__sub">开启您的健康成长之旅</text>
    </view>

    <view class="reg-form">
      <!-- 手机号 -->
      <view class="reg-field">
        <text class="reg-field__label">手机号</text>
        <input class="reg-field__input" type="number" maxlength="11" placeholder="请输入手机号" v-model="form.phone" />
      </view>

      <!-- 验证码 -->
      <view class="reg-field">
        <text class="reg-field__label">验证码</text>
        <view class="reg-field__row">
          <input class="reg-field__input reg-field__input--code" type="number" maxlength="6" placeholder="请输入验证码" v-model="form.code" />
          <view class="reg-code-btn" :class="{ 'reg-code-btn--disabled': codeCd > 0 }" @tap="sendCode">
            <text>{{ codeCd > 0 ? codeCd + 's' : '获取验证码' }}</text>
          </view>
        </view>
      </view>

      <!-- 用户名 -->
      <view class="reg-field">
        <text class="reg-field__label">用户名</text>
        <input class="reg-field__input" placeholder="请输入用户名（登录用）" v-model="form.username" />
      </view>

      <!-- 密码 -->
      <view class="reg-field">
        <text class="reg-field__label">密码</text>
        <input class="reg-field__input" type="password" placeholder="请输入密码（6位以上）" v-model="form.password" />
      </view>

      <!-- 确认密码 -->
      <view class="reg-field">
        <text class="reg-field__label">确认密码</text>
        <input class="reg-field__input" type="password" placeholder="再次输入密码" v-model="form.confirmPwd" />
      </view>

      <!-- 角色选择 -->
      <view class="reg-field">
        <text class="reg-field__label">我要成为</text>
        <view class="reg-roles">
          <view class="reg-role" :class="{ 'reg-role--active': form.role === 'grower' }" @tap="form.role = 'grower'">
            <text class="reg-role__icon">🌱</text>
            <text class="reg-role__name">成长者</text>
            <text class="reg-role__desc">开始健康管理之旅</text>
          </view>
          <view class="reg-role" :class="{ 'reg-role--active': form.role === 'sharer' }" @tap="form.role = 'sharer'">
            <text class="reg-role__icon">🤝</text>
            <text class="reg-role__name">分享者</text>
            <text class="reg-role__desc">分享健康带动他人</text>
          </view>
        </view>
      </view>

      <!-- 协议 -->
      <view class="reg-agree" @tap="agreed = !agreed">
        <view class="reg-agree__check" :class="{ 'reg-agree__check--on': agreed }">
          <text v-if="agreed">✓</text>
        </view>
        <text class="reg-agree__text">我已阅读并同意</text>
        <text class="reg-agree__link">《用户服务协议》</text>
        <text class="reg-agree__text">和</text>
        <text class="reg-agree__link">《隐私政策》</text>
      </view>

      <!-- 注册按钮 -->
      <view class="reg-btn" :class="{ 'reg-btn--disabled': !canSubmit }" @tap="handleRegister">
        <text>{{ submitting ? '注册中...' : '注 册' }}</text>
      </view>

      <view class="reg-login-link" @tap="goLogin">
        <text class="text-secondary-color text-sm">已有账号？</text>
        <text class="text-primary-color text-sm font-semibold">去登录</text>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import http from '@/api/request'

const form = reactive({
  phone: '', code: '', username: '', password: '', confirmPwd: '', role: 'grower',
})
const agreed     = ref(false)
const submitting = ref(false)
const codeCd     = ref(0)

const canSubmit = computed(() =>
  form.phone.length === 11 &&
  form.username.trim().length >= 2 &&
  form.password.length >= 6 &&
  form.password === form.confirmPwd &&
  agreed.value && !submitting.value
)

function sendCode() {
  if (codeCd.value > 0 || form.phone.length !== 11) return
  uni.showToast({ title: '验证码已发送', icon: 'none' })
  codeCd.value = 60
  const timer = setInterval(() => { codeCd.value--; if (codeCd.value <= 0) clearInterval(timer) }, 1000)
}

async function handleRegister() {
  if (!canSubmit.value) return
  submitting.value = true
  try {
    await http.post('/v1/auth/register', {
      username: form.username.trim(),
      password: form.password,
      email: `${form.phone}@bhp.local`,
      full_name: form.username.trim(),
    })
    uni.showToast({ title: '注册成功', icon: 'success' })
    setTimeout(() => uni.navigateTo({ url: '/pages/auth/login' }), 1500)
  } catch (e: any) {
    uni.showToast({ title: e?.message || '注册失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

function goLogin() { uni.navigateTo({ url: '/pages/auth/login' }) }
</script>

<style scoped>
.reg-page { min-height: 100vh; background: var(--surface); padding: 0 40rpx 60rpx; }
.reg-header { padding: 80rpx 0 48rpx; }
.reg-header__title { display: block; font-size: 44rpx; font-weight: 800; color: var(--text-primary); }
.reg-header__sub { display: block; font-size: 26rpx; color: var(--text-secondary); margin-top: 8rpx; }
.reg-form { display: flex; flex-direction: column; gap: 28rpx; }
.reg-field__label { display: block; font-size: 24rpx; font-weight: 600; color: var(--text-secondary); margin-bottom: 10rpx; }
.reg-field__input {
  width: 100%; height: 88rpx; border: 1px solid var(--border-light); border-radius: var(--radius-lg);
  padding: 0 24rpx; font-size: 28rpx; color: var(--text-primary); background: var(--surface-secondary);
}
.reg-field__row { display: flex; gap: 16rpx; }
.reg-field__input--code { flex: 1; }
.reg-code-btn {
  flex-shrink: 0; height: 88rpx; padding: 0 28rpx; border-radius: var(--radius-lg);
  background: var(--bhp-primary-500); color: #fff; font-size: 24rpx; font-weight: 600;
  display: flex; align-items: center; justify-content: center; cursor: pointer;
}
.reg-code-btn--disabled { background: var(--bhp-gray-200); color: var(--text-tertiary); }
.reg-roles { display: flex; gap: 16rpx; }
.reg-role {
  flex: 1; padding: 24rpx 16rpx; border-radius: var(--radius-lg);
  border: 2px solid var(--border-light); background: var(--surface-secondary);
  display: flex; flex-direction: column; align-items: center; gap: 6rpx; cursor: pointer;
}
.reg-role--active { border-color: var(--bhp-primary-500); background: var(--bhp-primary-50); }
.reg-role__icon { font-size: 40rpx; }
.reg-role__name { font-size: 28rpx; font-weight: 700; color: var(--text-primary); }
.reg-role__desc { font-size: 20rpx; color: var(--text-tertiary); }
.reg-agree { display: flex; align-items: center; gap: 8rpx; flex-wrap: wrap; }
.reg-agree__check {
  width: 32rpx; height: 32rpx; border-radius: 6rpx; border: 2px solid var(--bhp-gray-300);
  display: flex; align-items: center; justify-content: center; font-size: 20rpx; cursor: pointer;
}
.reg-agree__check--on { background: var(--bhp-primary-500); border-color: var(--bhp-primary-500); color: #fff; }
.reg-agree__text { font-size: 22rpx; color: var(--text-secondary); }
.reg-agree__link { font-size: 22rpx; color: var(--bhp-primary-600); }
.reg-btn {
  height: 96rpx; border-radius: var(--radius-lg); background: var(--bhp-primary-500);
  display: flex; align-items: center; justify-content: center; cursor: pointer;
  font-size: 30rpx; font-weight: 700; color: #fff; margin-top: 12rpx;
}
.reg-btn:active { opacity: 0.85; }
.reg-btn--disabled { background: var(--bhp-gray-200); color: var(--text-tertiary); }
.reg-login-link { display: flex; align-items: center; justify-content: center; gap: 8rpx; padding: 32rpx 0; }
</style>
