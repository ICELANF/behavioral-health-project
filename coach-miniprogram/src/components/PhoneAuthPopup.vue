<template>
  <view v-if="visible" class="bhp-wrap">
    <!-- 遮罩 -->
    <view class="bhp-mask" @tap="handleClose" />

    <!-- 弹窗主体 -->
    <view class="bhp-sheet" :class="{ show: visible }">
      <!-- 把手 -->
      <view class="bhp-handle" />

      <!-- 关闭 -->
      <view class="bhp-close" @tap="handleClose">
        <text class="bhp-close-icon">✕</text>
      </view>

      <!-- 品牌 -->
      <view class="bhp-brand">
        <view class="bhp-brand-icon"><text>行</text></view>
        <text class="bhp-brand-name">行健平台</text>
      </view>

      <!-- Tab -->
      <view class="bhp-tabs">
        <view
          v-for="tab in tabs" :key="tab.key"
          class="bhp-tab" :class="{ active: activeTab === tab.key }"
          @tap="switchTab(tab.key)"
        >
          <text>{{ tab.label }}</text>
        </view>
        <view class="bhp-tab-bar" :class="{ right: activeTab === 'login' }" />
      </view>

      <!-- 表单 -->
      <view class="bhp-form">
        <!-- 手机号 -->
        <view class="bhp-field" :class="{ focused: phoneFocused }">
          <text class="bhp-prefix">+86</text>
          <input
            v-model="form.phone"
            class="bhp-input"
            type="number" maxlength="11"
            placeholder="请输入手机号" placeholder-class="bhp-placeholder"
            @focus="phoneFocused = true" @blur="phoneFocused = false"
          />
          <text v-if="phoneValid" class="bhp-check">✓</text>
        </view>

        <!-- 验证码 -->
        <view class="bhp-field" :class="{ focused: codeFocused }">
          <input
            v-model="form.code"
            class="bhp-input"
            type="number" maxlength="6"
            placeholder="请输入验证码" placeholder-class="bhp-placeholder"
            @focus="codeFocused = true" @blur="codeFocused = false"
          />
          <view
            class="bhp-send" :class="{ counting, disabled: !phoneValid || counting || sending }"
            @tap="sendCode"
          >
            <text>{{ counting ? `${countdown}s` : '获取验证码' }}</text>
          </view>
        </view>

        <!-- 昵称（注册专用） -->
        <view v-if="activeTab === 'register'" class="bhp-field" :class="{ focused: nickFocused }">
          <input
            v-model="form.nickname"
            class="bhp-input"
            type="text" maxlength="16"
            placeholder="昵称（可选）" placeholder-class="bhp-placeholder"
            @focus="nickFocused = true" @blur="nickFocused = false"
          />
        </view>

        <!-- debug 提示 -->
        <view v-if="debugCode" class="bhp-debug">
          <text class="bhp-debug-label">测试验证码：</text>
          <text class="bhp-debug-code">{{ debugCode }}</text>
        </view>

        <!-- 错误提示 -->
        <text v-if="errorMsg" class="bhp-error">{{ errorMsg }}</text>

        <!-- 提交 -->
        <view
          class="bhp-submit" :class="{ disabled: !canSubmit || submitting }"
          @tap="handleSubmit"
        >
          <text v-if="!submitting" class="bhp-submit-text">
            {{ activeTab === 'register' ? '立即注册' : '登录' }}
          </text>
          <view v-else class="bhp-spinner" />
        </view>

        <!-- 协议 -->
        <view class="bhp-agreement">
          <text class="bhp-agreement-text">{{ activeTab === 'register' ? '注册' : '登录' }}即同意</text>
          <text class="bhp-link">《用户协议》</text>
          <text class="bhp-agreement-text">和</text>
          <text class="bhp-link">《隐私政策》</text>
        </view>

        <!-- 切换 -->
        <view class="bhp-switch">
          <template v-if="activeTab === 'register'">
            <text class="bhp-switch-text">已有账号？</text>
            <text class="bhp-link" @tap="switchTab('login')">直接登录</text>
          </template>
          <template v-else>
            <text class="bhp-switch-text">还没账号？</text>
            <text class="bhp-link" @tap="switchTab('register')">立即注册</text>
          </template>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import http from '@/api/request'

// ── Props / Emits ─────────────────────────────────────────────
const props = defineProps<{
  visible: boolean
  defaultTab?: 'register' | 'login'
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'success', user: Record<string, any>): void
}>()

// ── State ─────────────────────────────────────────────────────
const activeTab = ref<'register' | 'login'>(props.defaultTab ?? 'register')
const tabs = [{ key: 'register', label: '注册' }, { key: 'login', label: '登录' }]

const form = ref({ phone: '', code: '', nickname: '' })
const phoneFocused = ref(false)
const codeFocused  = ref(false)
const nickFocused  = ref(false)
const sending    = ref(false)
const submitting = ref(false)
const countdown  = ref(0)
const debugCode  = ref('')
const errorMsg   = ref('')

let timer: ReturnType<typeof setInterval> | null = null

// ── Computed ──────────────────────────────────────────────────
const phoneValid = computed(() => /^1[3-9]\d{9}$/.test(form.value.phone))
const counting   = computed(() => countdown.value > 0)
const canSubmit  = computed(() => phoneValid.value && form.value.code.length === 6)

// ── Methods ───────────────────────────────────────────────────
function switchTab(tab: 'register' | 'login') {
  activeTab.value = tab
  form.value.code = ''
  debugCode.value = ''
  errorMsg.value  = ''
}

async function sendCode() {
  if (!phoneValid.value || counting.value || sending.value) return
  sending.value = true
  errorMsg.value = ''

  try {
    const res = await http.post<any>('/api/v1/auth/phone/send-code', {
      phone: form.value.phone,
      purpose: activeTab.value,
    }, { noAuth: true })
    debugCode.value = res.debug_code ?? ''
    startCountdown()
    uni.showToast({ title: '验证码已发送', icon: 'success' })
  } catch (e: any) {
    errorMsg.value = e?.data?.detail ?? e?.message ?? '发送失败'
  } finally {
    sending.value = false
  }
}

function startCountdown() {
  countdown.value = 60
  timer = setInterval(() => {
    if (--countdown.value <= 0) { clearInterval(timer!); timer = null }
  }, 1000)
}

async function handleSubmit() {
  if (!canSubmit.value || submitting.value) return
  submitting.value = true
  errorMsg.value   = ''

  const url = activeTab.value === 'register'
    ? '/api/v1/auth/phone/register'
    : '/api/v1/auth/phone/login'

  const data: any = { phone: form.value.phone, code: form.value.code }
  if (activeTab.value === 'register' && form.value.nickname.trim()) {
    data.nickname = form.value.nickname.trim()
  }

  try {
    const res = await http.post<any>(url, data, { noAuth: true })
    uni.setStorageSync('access_token',  res.access_token)
    uni.setStorageSync('refresh_token', res.refresh_token)
    uni.setStorageSync('user_info',     JSON.stringify(res.user))

    uni.showToast({ title: res.message, icon: 'success', duration: 1500 })
    emit('success', res.user)
    handleClose()
  } catch (e: any) {
    errorMsg.value = e?.data?.detail ?? e?.message ?? '操作失败'
  } finally {
    submitting.value = false
  }
}

function handleClose() {
  if (timer) clearInterval(timer)
  form.value = { phone: '', code: '', nickname: '' }
  debugCode.value = ''
  errorMsg.value  = ''
  emit('update:visible', false)
}

watch(() => props.visible, (val) => {
  if (val && props.defaultTab) activeTab.value = props.defaultTab
})

onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<style scoped>
.bhp-wrap {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  z-index: 1000;
}
.bhp-mask {
  position: absolute; inset: 0;
  background: rgba(0,0,0,.5);
}
.bhp-sheet {
  position: absolute; bottom: 0; left: 0; right: 0;
  background: #fff;
  border-radius: 40rpx 40rpx 0 0;
  padding: 24rpx 48rpx calc(env(safe-area-inset-bottom) + 48rpx);
  transform: translateY(100%);
  transition: transform .32s cubic-bezier(.32,1,.32,1);
}
.bhp-sheet.show { transform: translateY(0); }

.bhp-handle {
  width: 72rpx; height: 8rpx;
  background: #e0e0e0; border-radius: 4rpx;
  margin: 0 auto 40rpx;
}
.bhp-close {
  position: absolute; top: 36rpx; right: 36rpx;
  width: 60rpx; height: 60rpx;
  background: #f5f5f5; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
}
.bhp-close-icon { font-size: 28rpx; color: #999; }

/* 品牌 */
.bhp-brand {
  display: flex; align-items: center; gap: 20rpx;
  margin-bottom: 48rpx;
}
.bhp-brand-icon {
  width: 80rpx; height: 80rpx;
  background: linear-gradient(135deg, #52b788, #2d6a4f);
  border-radius: 24rpx;
  display: flex; align-items: center; justify-content: center;
}
.bhp-brand-icon text { font-size: 36rpx; color: #fff; font-weight: 700; }
.bhp-brand-name { font-size: 40rpx; font-weight: 600; color: #1a1a1a; }

/* Tabs */
.bhp-tabs {
  position: relative; display: flex;
  border-bottom: 2rpx solid #f0f0f0;
  margin-bottom: 40rpx;
}
.bhp-tab {
  flex: 1; padding: 20rpx 0; text-align: center;
}
.bhp-tab text { font-size: 30rpx; font-weight: 500; color: #999; }
.bhp-tab.active text { color: #2d6a4f; }
.bhp-tab-bar {
  position: absolute; bottom: -2rpx; left: 0;
  width: 50%; height: 4rpx;
  background: #2d6a4f; border-radius: 2rpx;
  transition: left .25s;
}
.bhp-tab-bar.right { left: 50%; }

/* 字段 */
.bhp-field {
  display: flex; align-items: center;
  border: 3rpx solid #e8ede9;
  border-radius: 24rpx;
  padding: 0 28rpx;
  margin-bottom: 24rpx;
  background: #f8faf8;
  min-height: 104rpx;
}
.bhp-field.focused { border-color: #40916c; background: #fff; }
.bhp-prefix {
  font-size: 30rpx; color: #666;
  padding-right: 20rpx;
  border-right: 2rpx solid #ddd;
  margin-right: 20rpx;
}
.bhp-input { flex: 1; font-size: 30rpx; color: #1a1a1a; }
.bhp-placeholder { color: #bbb; }
.bhp-check { font-size: 32rpx; color: #4CAF50; font-weight: 700; }

/* 发送验证码 */
.bhp-send {
  padding: 12rpx 24rpx;
  border: 3rpx solid #40916c;
  border-radius: 16rpx;
  flex-shrink: 0;
}
.bhp-send text { font-size: 26rpx; color: #40916c; font-weight: 500; }
.bhp-send.counting { border-color: #ccc; }
.bhp-send.counting text { color: #999; }
.bhp-send.disabled { opacity: .45; }

/* debug */
.bhp-debug {
  display: flex; align-items: center;
  background: #fef3c7; border-radius: 16rpx;
  padding: 16rpx 24rpx; margin-bottom: 24rpx;
}
.bhp-debug-label { font-size: 26rpx; color: #92400e; }
.bhp-debug-code { font-size: 32rpx; color: #92400e; font-weight: 700; letter-spacing: 4rpx; }

/* 错误 */
.bhp-error { font-size: 26rpx; color: #ef4444; margin: -12rpx 0 16rpx 8rpx; display: block; }

/* 提交 */
.bhp-submit {
  width: 100%; padding: 32rpx;
  background: linear-gradient(135deg, #52b788, #2d6a4f);
  border-radius: 28rpx;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 8rpx 32rpx rgba(45,106,79,.35);
  margin-top: 8rpx;
}
.bhp-submit.disabled { opacity: .5; }
.bhp-submit-text { font-size: 32rpx; color: #fff; font-weight: 600; }
.bhp-spinner {
  width: 40rpx; height: 40rpx;
  border: 4rpx solid rgba(255,255,255,.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* 协议 & 切换 */
.bhp-agreement {
  display: flex; justify-content: center; flex-wrap: wrap;
  margin: 24rpx 0 16rpx; gap: 2rpx;
}
.bhp-agreement-text { font-size: 24rpx; color: #999; }
.bhp-link { font-size: 24rpx; color: #40916c; }
.bhp-switch { display: flex; justify-content: center; gap: 4rpx; }
.bhp-switch-text { font-size: 26rpx; color: #999; }
</style>
