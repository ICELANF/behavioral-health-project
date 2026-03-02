<template>
  <view class="reg-page">
    <view class="reg-header">
      <view class="reg-logo">
        <image src="/static/logo.png" mode="aspectFit" class="reg-logo-img" />
      </view>
      <text class="reg-title">创建账号</text>
      <text class="reg-sub">加入行健平台教练团队</text>
    </view>

    <view class="reg-form">
      <view class="reg-field">
        <text class="reg-label">用户名</text>
        <input v-model="form.username" class="reg-input" placeholder="请输入用户名（字母/数字/下划线）"
          placeholder-class="reg-ph" maxlength="30" />
      </view>

      <view class="reg-field">
        <text class="reg-label">真实姓名</text>
        <input v-model="form.full_name" class="reg-input" placeholder="请输入您的真实姓名"
          placeholder-class="reg-ph" maxlength="20" />
      </view>

      <view class="reg-field">
        <text class="reg-label">手机号</text>
        <input v-model="form.phone" class="reg-input" placeholder="请输入手机号"
          placeholder-class="reg-ph" type="number" maxlength="11" />
      </view>

      <view class="reg-field">
        <text class="reg-label">密码</text>
        <input v-model="form.password" class="reg-input" placeholder="至少8位，含字母和数字"
          placeholder-class="reg-ph" password maxlength="50" />
      </view>

      <view class="reg-field">
        <text class="reg-label">确认密码</text>
        <input v-model="form.confirmPwd" class="reg-input" placeholder="再次输入密码"
          placeholder-class="reg-ph" password maxlength="50" />
      </view>

      <view v-if="errMsg" class="reg-error">
        <text>{{ errMsg }}</text>
      </view>

      <view class="reg-submit" :class="{ 'reg-submit--loading': loading }" @tap="doRegister">
        <text>{{ loading ? '注册中...' : '立即注册' }}</text>
      </view>

      <view class="reg-login-link" @tap="goLogin">
        <text class="reg-login-text">已有账号？</text>
        <text class="reg-login-btn">立即登录</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const BASE_URL = 'http://localhost:8000'

const form = ref({
  username: '',
  full_name: '',
  phone: '',
  password: '',
  confirmPwd: '',
})
const loading = ref(false)
const errMsg = ref('')

function validate(): string {
  const f = form.value
  if (!f.username.trim()) return '请输入用户名'
  if (!/^[a-zA-Z0-9_]{3,30}$/.test(f.username)) return '用户名只能含字母、数字、下划线，3-30位'
  if (!f.full_name.trim()) return '请输入真实姓名'
  if (f.phone && !/^1\d{10}$/.test(f.phone)) return '手机号格式不正确'
  if (!f.password) return '请输入密码'
  if (f.password.length < 8) return '密码至少8位'
  if (!/[a-zA-Z]/.test(f.password) || !/[0-9]/.test(f.password)) return '密码须包含字母和数字'
  if (f.password !== f.confirmPwd) return '两次输入的密码不一致'
  return ''
}

async function doRegister() {
  if (loading.value) return
  errMsg.value = validate()
  if (errMsg.value) return

  loading.value = true
  try {
    await new Promise<void>((resolve, reject) => {
      uni.request({
        url: BASE_URL + '/api/v1/auth/register',
        method: 'POST',
        data: {
          username: form.value.username.trim(),
          password: form.value.password,
          full_name: form.value.full_name.trim(),
          phone: form.value.phone || undefined,
          role: 'coach',
        },
        header: { 'Content-Type': 'application/json' },
        success: (res: any) => {
          if (res.statusCode >= 200 && res.statusCode < 300) resolve()
          else {
            const detail = res.data?.detail || res.data?.message || `注册失败(${res.statusCode})`
            reject(new Error(typeof detail === 'string' ? detail : JSON.stringify(detail)))
          }
        },
        fail: (e: any) => reject(new Error(e?.errMsg || '网络错误')),
      })
    })
    uni.showToast({ title: '注册成功，请登录', icon: 'success', duration: 1800 })
    setTimeout(() => goLogin(), 1800)
  } catch (e: any) {
    errMsg.value = e?.message || '注册失败，请重试'
  } finally {
    loading.value = false
  }
}

function goLogin() {
  uni.redirectTo({ url: '/pages/auth/login' })
}
</script>

<style scoped>
.reg-page { min-height: 100vh; background: linear-gradient(160deg, #F0FBF6 0%, #F5F6FA 50%); display: flex; flex-direction: column; }

.reg-header { align-items: center; padding: 60rpx 40rpx 40rpx; display: flex; flex-direction: column; }
.reg-logo { margin-bottom: 24rpx; }
.reg-logo-img { width: 120rpx; height: 120rpx; }
.reg-title { font-size: 40rpx; font-weight: 700; color: #2C3E50; }
.reg-sub { font-size: 26rpx; color: #8E99A4; margin-top: 8rpx; }

.reg-form { flex: 1; background: #fff; margin: 0 32rpx; border-radius: 24rpx; padding: 40rpx 32rpx; box-shadow: 0 8rpx 32rpx rgba(0,0,0,0.06); }

.reg-field { margin-bottom: 28rpx; }
.reg-label { display: block; font-size: 26rpx; font-weight: 600; color: #5B6B7F; margin-bottom: 12rpx; }
.reg-input {
  width: 100%; height: 88rpx; border: 2rpx solid #E8ECF0; border-radius: 16rpx;
  padding: 0 24rpx; font-size: 28rpx; color: #2C3E50; background: #FAFBFC;
  box-sizing: border-box;
}
.reg-ph { color: #BDC3C7; }

.reg-error { background: #FFF0F0; border-radius: 12rpx; padding: 16rpx 20rpx; margin-bottom: 20rpx; }
.reg-error text { font-size: 26rpx; color: #E74C3C; }

.reg-submit {
  width: 100%; height: 96rpx; background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%);
  border-radius: 48rpx; display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 32rpx; font-weight: 700; margin-top: 8rpx;
  box-shadow: 0 8rpx 24rpx rgba(45,142,105,0.35);
}
.reg-submit--loading { opacity: 0.7; }

.reg-login-link { display: flex; justify-content: center; align-items: center; gap: 8rpx; margin-top: 32rpx; }
.reg-login-text { font-size: 26rpx; color: #8E99A4; }
.reg-login-btn { font-size: 26rpx; color: #2D8E69; font-weight: 600; }
</style>
