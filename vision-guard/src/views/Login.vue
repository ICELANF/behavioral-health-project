<template>
  <div class="login-page">
    <div class="login-hero">
      <div style="font-size:56px;margin-bottom:16px">👁️</div>
      <h1>VisionGuard</h1>
      <p>青少年科学使用视力</p>
    </div>
    <div class="login-form">
      <van-field v-model="phone" label="手机号" placeholder="请输入手机号" type="tel" />
      <van-field v-model="code" label="验证码" placeholder="请输入验证码">
        <template #button>
          <van-button size="small" type="primary" @click="sendCode" :disabled="countdown > 0">
            {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
          </van-button>
        </template>
      </van-field>
      <van-button type="primary" block round class="login-btn" @click="login">登录</van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const phone = ref('')
const code = ref('')
const countdown = ref(0)

function sendCode() {
  countdown.value = 60
  const timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) clearInterval(timer)
  }, 1000)
}

function login() {
  // TODO: real auth
  localStorage.setItem('access_token', 'dev_token')
  router.push('/')
}
</script>

<style scoped>
.login-page {
  min-height: 100vh; display: flex; flex-direction: column;
  justify-content: center; padding: 32px 24px;
}
.login-hero { text-align: center; margin-bottom: 40px; }
.login-hero h1 { font-size: 28px; font-weight: 900; color: var(--teal); }
.login-hero p { font-size: 14px; color: var(--sub); margin-top: 4px; }
.login-form { display: flex; flex-direction: column; gap: 16px; }
.login-btn { margin-top: 8px; --van-button-primary-background: var(--teal); --van-button-primary-border-color: var(--teal); }
</style>
