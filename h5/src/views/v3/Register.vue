<template>
  <div class="register-page">
    <van-nav-bar title="注册" left-arrow @click-left="$router.back()" />

    <!-- 来源提示 -->
    <div v-if="fromChat" class="source-hint">
      <van-icon name="chat-o" size="16" color="#1565C0" />
      <span>注册后解锁无限 AI 对话 + 个性化健康方案</span>
    </div>

    <van-form @submit="onRegister" class="register-form">
      <van-cell-group inset>
        <van-field v-model="phone" type="tel" label="手机号" placeholder="请输入手机号" maxlength="11"
          :rules="[{ pattern: /^1\d{10}$/, message: '请输入正确的手机号' }]" />

        <!-- 验证码 -->
        <van-field v-model="smsCode" type="digit" label="验证码" placeholder="请输入验证码" maxlength="6">
          <template #button>
            <van-button
              size="small"
              type="primary"
              plain
              :disabled="smsCooldown > 0 || !isPhoneValid"
              @click="sendCode"
            >
              {{ smsCooldown > 0 ? `${smsCooldown}s` : '发送验证码' }}
            </van-button>
          </template>
        </van-field>

        <van-field v-model="nickname" label="昵称" placeholder="选填" maxlength="20" />
        <van-field v-model="password" type="password" label="密码" placeholder="至少6位"
          :rules="[{ validator: v => v.length >= 6, message: '密码至少6位' }]" />
        <van-field v-model="confirmPwd" type="password" label="确认密码" placeholder="再次输入密码"
          :rules="[{ validator: v => v === password, message: '两次密码不一致' }]" />
      </van-cell-group>

      <div class="actions">
        <van-button round block type="primary" native-type="submit" :loading="loading">
          {{ upgradeToGrower ? '注册并成为成长者' : '注 册' }}
        </van-button>
      </div>
    </van-form>

    <div class="footer-links">
      <p>已有账号？<router-link to="/login">去登录</router-link></p>
      <p class="wechat-link">或使用 <router-link to="/login">微信授权登录</router-link></p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import api from '@/api/index'
import { authApi } from '../../api/v3/index.js'
import storage from '@/utils/storage'

const router = useRouter()
const route = useRoute()

const phone = ref('')
const smsCode = ref('')
const nickname = ref('')
const password = ref('')
const confirmPwd = ref('')
const loading = ref(false)
const smsCooldown = ref(0)
let cooldownTimer = null

const isPhoneValid = computed(() => /^1\d{10}$/.test(phone.value))
const fromChat = computed(() => route.query.from === 'chat')
const upgradeToGrower = computed(() => route.query.upgrade === 'grower')

onUnmounted(() => {
  if (cooldownTimer) clearInterval(cooldownTimer)
})

async function sendCode() {
  if (!isPhoneValid.value || smsCooldown.value > 0) return

  try {
    await api.post('/api/v1/auth/send-sms-code', { phone: phone.value })
    showToast({ message: '验证码已发送', type: 'success' })
    smsCooldown.value = 60
    cooldownTimer = setInterval(() => {
      smsCooldown.value--
      if (smsCooldown.value <= 0) {
        clearInterval(cooldownTimer)
        cooldownTimer = null
      }
    }, 1000)
  } catch (e) {
    showToast(e.response?.data?.detail || '发送失败')
  }
}

async function onRegister() {
  if (!smsCode.value) {
    showToast('请输入验证码')
    return
  }

  loading.value = true
  try {
    // 构建注册 URL (支持 upgrade + source 参数)
    let registerUrl = '/api/v3/auth/register'
    const params = new URLSearchParams()
    if (upgradeToGrower.value) {
      params.set('upgrade', 'grower')
      params.set('source', 'chat_trial')
    }
    if (params.toString()) registerUrl += '?' + params.toString()

    const res = await api.post(registerUrl, {
      phone: phone.value,
      password: password.value,
      nickname: nickname.value,
      code: smsCode.value,
    })

    const data = res?.data || res
    if (data?.tokens || data?.access_token) {
      const tokens = data.tokens || data
      const user = data.user || {}
      storage.setToken(tokens.access_token)
      if (tokens.refresh_token) {
        localStorage.setItem('refresh_token', tokens.refresh_token)
      }
      if (user) {
        storage.setAuthUser(user)
      }
      localStorage.setItem('bhp_role_level', String(user.role_level || (upgradeToGrower.value ? 2 : 1)))

      showToast({ message: '注册成功', type: 'success' })

      // 成长者跳到 onboarding, 否则首页
      if (upgradeToGrower.value) {
        router.push('/onboarding/grower')
      } else {
        router.push('/')
      }
    } else {
      showToast(res?.message || data?.message || '注册失败')
    }
  } catch (e) {
    showToast(e.response?.data?.detail || '网络错误')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page { min-height: 100vh; background: #f7f8fa; }
.register-form { max-width: 400px; margin: 20px auto; }
.actions { padding: 24px 16px; }

.source-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  margin: 0 16px 8px;
  background: #E3F0FF;
  border-radius: 12px;
  font-size: 13px;
  color: #1565C0;
}

.footer-links {
  text-align: center;
  margin-top: 16px;
  font-size: 14px;
  color: #999;
}
.footer-links a {
  color: #1989fa;
  text-decoration: none;
}
</style>
