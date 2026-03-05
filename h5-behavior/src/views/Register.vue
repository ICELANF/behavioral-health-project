<template>
  <div class="screen">
    <div class="reg-wrap">
      <div class="reg-back" @click="$router.back()">← 返回</div>
      <div class="reg-heading fu">
        <span style="font-size:36px">{{ label?.icon || '🌱' }}</span>
        <div style="margin-top:8px">解锁你的完整方案</div>
      </div>
      <div class="reg-desc fu d1">
        你的<span v-if="label" class="reg-hl">{{ label.name }}</span>状态需要针对性调整
      </div>

      <!-- 模糊报告预览 — 制造好奇心 -->
      <div class="report-preview fu d1">
        <div class="preview-blur">
          <div class="preview-lock">🔒 完整报告已生成</div>
        </div>
        <div class="preview-skeleton">
          <div class="skel-row skel-short" />
          <div class="skel-row" />
          <div class="skel-row skel-mid" />
          <div class="skel-row skel-short" />
        </div>
      </div>

      <div class="reg-form fu d2">
        <div class="reg-field">
          <label class="reg-label">手机号</label>
          <div class="reg-input-row">
            <input v-model="phone" type="tel" maxlength="11" placeholder="请输入手机号"
              class="reg-input" />
          </div>
        </div>

        <div class="reg-field">
          <label class="reg-label">验证码</label>
          <div class="reg-input-row">
            <input v-model="code" type="text" maxlength="6" placeholder="请输入验证码"
              class="reg-input" style="flex:1" />
            <button class="reg-sms-btn" :disabled="countdown > 0 || phone.length < 11"
              @click="sendCode">
              {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
            </button>
          </div>
          <div v-if="demoHint" class="reg-demo-hint">
            演示模式：验证码已自动填入
          </div>
        </div>

        <div class="reg-agree" @click="agreed = !agreed">
          <div :class="['reg-check', { checked: agreed }]">
            {{ agreed ? '✓' : '' }}
          </div>
          <span>我已阅读并同意《用户协议》和《隐私政策》</span>
        </div>

        <button class="btn-main"
          :disabled="!canSubmit"
          :style="{ background: canSubmit ? D.teal : 'rgba(0,0,0,.06)',
                     color: canSubmit ? '#fff' : D.muted, width: '100%' }"
          @click="doRegister">
          {{ loading ? '注册中...' : '注册并开始' }}
        </button>
      </div>

      <!-- 信任标识 -->
      <div class="trust-bar fu d3">
        <div class="trust-item"><span>🛡️</span> 加密存储</div>
        <div class="trust-item"><span>👩‍⚕️</span> 专业建议</div>
        <div class="trust-item"><span>🔐</span> 隐私保护</div>
      </div>

      <div class="reg-footer fu d4">
        已有账号？<span class="reg-link" @click="quickLogin">直接登录</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAssessmentStore } from '@/stores/assessment'
import { D } from '@/design/tokens'

const router = useRouter()
const authStore = useAuthStore()
const assessStore = useAssessmentStore()
const label = computed(() => assessStore.currentLabel)

const phone = ref('')
const code = ref('')
const agreed = ref(false)
const loading = ref(false)
const countdown = ref(0)
const demoHint = ref(false)
let timer: ReturnType<typeof setInterval> | null = null

const canSubmit = computed(() =>
  phone.value.length === 11 && code.value.length >= 4 && agreed.value && !loading.value
)

async function sendCode() {
  if (phone.value.length < 11) return
  countdown.value = 60
  timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0 && timer) {
      clearInterval(timer)
      timer = null
    }
  }, 1000)

  try {
    const { sendSms } = await import('@/api/auth')
    await sendSms(phone.value)
  } catch {
    // SMS API not available — enter demo mode
    code.value = '888888'
    demoHint.value = true
  }
}

async function doRegister() {
  if (!canSubmit.value) return
  loading.value = true
  try {
    const { registerBySms } = await import('@/api/auth')
    const sessionId = sessionStorage.getItem('session_id') || ''
    const res = await registerBySms(phone.value, code.value, sessionId)
    authStore.login(res.data.token, res.data.user)
  } catch {
    // Fallback: mock login for demo
    authStore.login('demo_token_' + Date.now(), { id: 1, phone: phone.value })
  } finally {
    loading.value = false
  }
  router.replace('/unlock')
}

function quickLogin() {
  if (phone.value.length === 11) {
    authStore.login('demo_token_' + Date.now(), { id: 1, phone: phone.value })
    router.replace('/unlock')
  }
}
</script>

<style scoped>
.reg-wrap { flex: 1; padding: 24px 22px 40px; display: flex; flex-direction: column; }
.reg-back { font-size: 13px; color: var(--sub); cursor: pointer; margin-bottom: 20px; padding: 6px 0; }
.reg-heading { font-family: 'ZCOOL XiaoWei', serif; font-size: 24px; color: var(--ink); text-align: center; margin-bottom: 8px; }
.reg-desc { font-size: 13px; color: var(--sub); text-align: center; line-height: 1.6; margin-bottom: 20px; }
.reg-hl { color: var(--teal); font-weight: 700; }

/* 模糊报告预览 */
.report-preview {
  position: relative; overflow: hidden; margin-bottom: 24px;
  border-radius: 20px; padding: 24px 20px; height: 130px;
  background: var(--card); border: 1.5px dashed var(--muted);
  box-shadow: var(--shadow-md);
}
.preview-blur {
  position: absolute; inset: 0; z-index: 2;
  background: rgba(255,255,255,0.65);
  backdrop-filter: blur(5px); -webkit-backdrop-filter: blur(5px);
  display: flex; align-items: center; justify-content: center;
}
.preview-lock {
  background: var(--ink); color: #fff; font-size: 13px; font-weight: 600;
  padding: 8px 20px; border-radius: 20px;
  box-shadow: 0 4px 14px rgba(0,0,0,0.15);
}
.preview-skeleton { display: flex; flex-direction: column; gap: 10px; }
.skel-row {
  height: 10px; border-radius: 5px; width: 100%;
  background: linear-gradient(90deg, var(--bg-m) 30%, var(--bg) 50%, var(--bg-m) 70%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease infinite;
}
.skel-short { width: 45%; }
.skel-mid { width: 70%; }
.reg-form { display: flex; flex-direction: column; gap: 20px; }
.reg-field { display: flex; flex-direction: column; gap: 6px; }
.reg-label { font-size: 12px; font-weight: 600; color: var(--ink); }
.reg-input-row { display: flex; gap: 10px; }
.reg-input {
  flex: 1; padding: 14px 16px; border-radius: 14px; border: 1.5px solid var(--border);
  background: var(--card); font-size: 15px; color: var(--ink); outline: none;
  font-family: 'Noto Sans SC', sans-serif; transition: all .2s;
  box-shadow: var(--shadow-sm);
}
.reg-input:focus { border-color: var(--teal); box-shadow: 0 0 0 3px rgba(0,184,160,.12); }
.reg-input::placeholder { color: var(--muted); }
.reg-sms-btn {
  padding: 12px 16px; border-radius: 12px; border: 1.5px solid var(--teal);
  background: transparent; color: var(--teal); font-size: 13px; font-weight: 600;
  cursor: pointer; white-space: nowrap; font-family: 'Noto Sans SC', sans-serif;
  transition: all .2s;
}
.reg-sms-btn:disabled { border-color: var(--border); color: var(--muted); cursor: not-allowed; }
.reg-demo-hint {
  font-size: 11px; color: var(--teal); background: rgba(0,184,160,.08);
  border-radius: 8px; padding: 6px 10px; margin-top: 2px;
}
.reg-agree { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--sub); cursor: pointer; }
.reg-check {
  width: 18px; height: 18px; border-radius: 4px; border: 1.5px solid var(--border);
  display: flex; align-items: center; justify-content: center; font-size: 11px;
  transition: all .2s; flex-shrink: 0;
}
.reg-check.checked { background: var(--teal); border-color: var(--teal); color: #fff; }
/* 信任标识 */
.trust-bar {
  display: flex; justify-content: center; gap: 20px;
  margin-top: 20px; padding: 14px 0;
  border-top: 1px solid var(--border);
}
.trust-item {
  display: flex; align-items: center; gap: 5px;
  font-size: 11px; color: var(--muted); font-weight: 500;
}
.trust-item span { font-size: 14px; }

.reg-footer { text-align: center; font-size: 13px; color: var(--muted); margin-top: 16px; }
.reg-link { color: var(--teal); font-weight: 600; cursor: pointer; }
</style>
