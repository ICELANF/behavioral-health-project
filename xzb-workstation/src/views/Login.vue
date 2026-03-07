<template>
  <div class="login-page">
    <div class="login-hero">
      <div class="logo-ring">XZB</div>
      <h1>行诊智伴</h1>
      <p>专家知识工作站</p>
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
      <button class="btn-main" style="width:100%;margin-top:12px" @click="login">登录</button>
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
  // TODO: real auth — POST /api/v1/auth/login
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
.logo-ring {
  width: 80px; height: 80px; border-radius: 50%; margin: 0 auto 16px;
  background: var(--grad-header); color: white;
  font-size: 24px; font-weight: 900; letter-spacing: 2px;
  display: flex; align-items: center; justify-content: center;
}
.login-hero h1 { font-size: 24px; font-weight: 900; color: var(--xzb-primary); }
.login-hero p { font-size: 13px; color: var(--sub); margin-top: 4px; }
.login-form { display: flex; flex-direction: column; gap: 12px; }
</style>
