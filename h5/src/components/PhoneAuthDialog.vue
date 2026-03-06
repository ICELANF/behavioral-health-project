<template>
  <teleport to="body">
    <!-- 遮罩 -->
    <transition name="bhp-fade">
      <div v-if="visible" class="bhp-mask" @click.self="handleClose" />
    </transition>

    <!-- 底部弹窗 -->
    <transition name="bhp-slide">
      <div v-if="visible" class="bhp-sheet">
        <div class="bhp-handle" />

        <button class="bhp-close" @click="handleClose">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <path d="M14 4L4 14M4 4l10 10" stroke="#999" stroke-width="1.8" stroke-linecap="round"/>
          </svg>
        </button>

        <!-- 品牌 -->
        <div class="bhp-brand">
          <div class="bhp-brand-icon">行</div>
          <span class="bhp-brand-name">行健平台</span>
        </div>

        <!-- Tab -->
        <div class="bhp-tabs">
          <button
            v-for="tab in tabs" :key="tab.key"
            class="bhp-tab" :class="{ active: activeTab === tab.key }"
            @click="switchTab(tab.key)"
          >{{ tab.label }}</button>
          <div class="bhp-tab-bar" :style="{ left: activeTab === 'register' ? '0' : '50%' }" />
        </div>

        <!-- 表单 -->
        <div class="bhp-form">
          <!-- 手机号 -->
          <div class="bhp-field" :class="{ focused: phoneFocused }">
            <span class="bhp-prefix">+86</span>
            <input
              v-model="form.phone"
              class="bhp-input"
              type="tel" inputmode="numeric"
              maxlength="11" placeholder="请输入手机号"
              @focus="phoneFocused = true" @blur="phoneFocused = false"
              @input="form.phone = form.phone.replace(/\D/g,'').slice(0,11)"
            />
            <svg v-if="phoneValid" width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="7" fill="#4CAF50"/>
              <path d="M5 8l2.5 2.5L11 6" stroke="#fff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>

          <!-- 验证码 -->
          <div class="bhp-field" :class="{ focused: codeFocused }">
            <input
              v-model="form.code"
              class="bhp-input"
              type="number" inputmode="numeric"
              maxlength="6" placeholder="请输入验证码"
              @focus="codeFocused = true" @blur="codeFocused = false"
            />
            <button
              class="bhp-send" :class="{ counting }"
              :disabled="!phoneValid || counting || sending"
              @click="sendCode"
            >{{ counting ? `${countdown}s` : '获取验证码' }}</button>
          </div>

          <!-- 昵称（注册专用） -->
          <transition name="bhp-expand">
            <div v-if="activeTab === 'register'" class="bhp-field" :class="{ focused: nickFocused }">
              <input
                v-model="form.nickname"
                class="bhp-input"
                type="text" maxlength="16" placeholder="昵称（可选）"
                @focus="nickFocused = true" @blur="nickFocused = false"
              />
            </div>
          </transition>

          <!-- debug 提示 -->
          <transition name="bhp-fade">
            <div v-if="debugCode" class="bhp-debug">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <circle cx="7" cy="7" r="6" stroke="#F59E0B" stroke-width="1.4"/>
                <path d="M7 5.5V8M7 9.5v.1" stroke="#F59E0B" stroke-width="1.4" stroke-linecap="round"/>
              </svg>
              测试模式验证码：<strong>{{ debugCode }}</strong>
            </div>
          </transition>

          <!-- 错误提示 -->
          <transition name="bhp-fade">
            <p v-if="errorMsg" class="bhp-error">{{ errorMsg }}</p>
          </transition>

          <!-- 提交 -->
          <button
            class="bhp-submit" :class="{ loading: submitting }"
            :disabled="!canSubmit || submitting"
            @click="handleSubmit"
          >
            <span v-if="!submitting">{{ activeTab === 'register' ? '立即注册' : '登录' }}</span>
            <span v-else class="bhp-spinner" />
          </button>

          <!-- 协议 -->
          <p class="bhp-agreement">
            {{ activeTab === 'register' ? '注册' : '登录' }}即同意
            <a href="/h5/terms.html">《用户协议》</a>和
            <a href="/h5/privacy.html">《隐私政策》</a>
          </p>

          <!-- 切换 -->
          <p class="bhp-switch">
            <template v-if="activeTab === 'register'">
              已有账号？<button class="bhp-link-btn" @click="switchTab('login')">直接登录</button>
            </template>
            <template v-else>
              还没账号？<button class="bhp-link-btn" @click="switchTab('register')">立即注册</button>
            </template>
          </p>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import axios from 'axios'

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

// ── API base（读 .env 注入的 VITE_API_BASE_URL）─────────────────
const BASE = import.meta.env.VITE_API_BASE_URL ?? ''

async function post(path: string, data: object) {
  const token = localStorage.getItem('access_token')
  const res = await axios.post(`${BASE}${path}`, data, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  })
  return res.data
}

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
    const res = await post('/api/v1/auth/phone/send-code', {
      phone: form.value.phone,
      purpose: activeTab.value,
    })
    debugCode.value = res.debug_code ?? ''
    startCountdown()
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail ?? '发送失败，请重试'
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

  const path = activeTab.value === 'register'
    ? '/api/v1/auth/phone/register'
    : '/api/v1/auth/phone/login'

  const payload: any = { phone: form.value.phone, code: form.value.code }
  if (activeTab.value === 'register' && form.value.nickname.trim()) {
    payload.nickname = form.value.nickname.trim()
  }

  try {
    const res = await post(path, payload)
    localStorage.setItem('access_token',  res.access_token)
    localStorage.setItem('refresh_token', res.refresh_token)
    localStorage.setItem('user_info',     JSON.stringify(res.user))
    emit('success', res.user)
    handleClose()
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail ?? '操作失败，请重试'
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
/* ── 遮罩 ── */
.bhp-mask {
  position: fixed; inset: 0;
  background: rgba(0,0,0,.48);
  backdrop-filter: blur(3px);
  z-index: 1000;
}

/* ── 面板 ── */
.bhp-sheet {
  position: fixed; bottom: 0; left: 0; right: 0;
  background: #fff;
  border-radius: 20px 20px 0 0;
  padding: 12px 24px env(safe-area-inset-bottom, 24px);
  z-index: 1001;
  max-height: 88vh;
  overflow-y: auto;
}

.bhp-handle {
  width: 36px; height: 4px;
  background: #e0e0e0; border-radius: 2px;
  margin: 0 auto 20px;
}

.bhp-close {
  position: absolute; top: 18px; right: 18px;
  width: 30px; height: 30px;
  background: #f5f5f5; border: none; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; padding: 0;
}

/* ── 品牌 ── */
.bhp-brand {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 24px;
}
.bhp-brand-icon {
  width: 40px; height: 40px;
  background: linear-gradient(135deg, #52b788, #2d6a4f);
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 18px; font-weight: 700;
  box-shadow: 0 4px 12px rgba(45,106,79,.3);
}
.bhp-brand-name {
  font-size: 20px; font-weight: 600; color: #1a1a1a;
  letter-spacing: .5px;
}

/* ── Tabs ── */
.bhp-tabs {
  position: relative;
  display: flex;
  border-bottom: 2px solid #f0f0f0;
  margin-bottom: 20px;
}
.bhp-tab {
  flex: 1; padding: 10px 0;
  border: none; background: transparent;
  font-size: 15px; font-weight: 500; color: #999;
  cursor: pointer; transition: color .2s;
}
.bhp-tab.active { color: #2d6a4f; }
.bhp-tab-bar {
  position: absolute; bottom: -2px;
  width: 50%; height: 2px;
  background: #2d6a4f; border-radius: 1px;
  transition: left .25s cubic-bezier(.34,1.56,.64,1);
}

/* ── 字段 ── */
.bhp-field {
  display: flex; align-items: center;
  border: 1.5px solid #e8ede9;
  border-radius: 12px;
  padding: 0 14px;
  margin-bottom: 12px;
  background: #f8faf8;
  transition: border-color .2s, background .2s;
  min-height: 52px;
}
.bhp-field.focused {
  border-color: #40916c;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(64,145,108,.08);
}
.bhp-prefix {
  font-size: 15px; color: #666;
  padding-right: 10px;
  border-right: 1px solid #ddd;
  margin-right: 10px;
  white-space: nowrap;
}
.bhp-input {
  flex: 1; border: none; background: transparent;
  font-size: 15px; color: #1a1a1a;
  outline: none; padding: 14px 0;
}
.bhp-input::placeholder { color: #bbb; }

/* ── 发送按钮 ── */
.bhp-send {
  white-space: nowrap;
  padding: 6px 12px;
  border: 1.5px solid #40916c;
  border-radius: 8px;
  background: transparent;
  color: #40916c;
  font-size: 13px; font-weight: 500;
  cursor: pointer; transition: all .2s;
  flex-shrink: 0;
}
.bhp-send:disabled { opacity: .45; cursor: not-allowed; }
.bhp-send.counting { border-color: #ccc; color: #999; }

/* ── debug ── */
.bhp-debug {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; color: #92400e;
  background: #fef3c7; border-radius: 8px;
  padding: 8px 12px; margin-bottom: 12px;
}
.bhp-debug strong { font-size: 15px; letter-spacing: 2px; }

/* ── 错误 ── */
.bhp-error {
  font-size: 13px; color: #ef4444;
  margin: -4px 0 10px 4px;
}

/* ── 提交 ── */
.bhp-submit {
  width: 100%; padding: 16px;
  background: linear-gradient(135deg, #52b788, #2d6a4f);
  border: none; border-radius: 14px;
  color: #fff; font-size: 16px; font-weight: 600;
  cursor: pointer; margin-top: 4px;
  transition: opacity .2s, transform .1s;
  box-shadow: 0 4px 16px rgba(45,106,79,.35);
  display: flex; align-items: center; justify-content: center;
  min-height: 52px;
}
.bhp-submit:disabled { opacity: .5; cursor: not-allowed; }
.bhp-submit:not(:disabled):active { transform: scale(.98); }

/* ── 加载动画 ── */
.bhp-spinner {
  width: 20px; height: 20px;
  border: 2px solid rgba(255,255,255,.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .7s linear infinite;
  display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── 协议 & 切换 ── */
.bhp-agreement {
  text-align: center; font-size: 12px; color: #999;
  margin: 12px 0 8px;
}
.bhp-agreement a { color: #40916c; text-decoration: none; }
.bhp-switch {
  text-align: center; font-size: 13px; color: #999;
  margin: 0;
}
.bhp-link-btn {
  background: none; border: none;
  color: #40916c; font-size: 13px; font-weight: 500;
  cursor: pointer; padding: 0;
}

/* ── 动画 ── */
.bhp-fade-enter-active, .bhp-fade-leave-active { transition: opacity .2s; }
.bhp-fade-enter-from, .bhp-fade-leave-to { opacity: 0; }

.bhp-slide-enter-active, .bhp-slide-leave-active { transition: transform .32s cubic-bezier(.32,1,.32,1); }
.bhp-slide-enter-from, .bhp-slide-leave-to { transform: translateY(100%); }

.bhp-expand-enter-active, .bhp-expand-leave-active {
  transition: max-height .25s ease, opacity .25s;
  overflow: hidden;
}
.bhp-expand-enter-from, .bhp-expand-leave-to { max-height: 0; opacity: 0; }
.bhp-expand-enter-to, .bhp-expand-leave-from { max-height: 80px; opacity: 1; }
</style>
