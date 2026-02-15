<!--
  RegisterView.vue — 注册页
-->

<template>
  <div class="login-page">
    <div class="register-card">
      <div class="form-content">
        <div class="brand-row">
          <div class="brand-icon-sm">行</div>
          <span class="brand-name">行健平台</span>
        </div>
        <h2 class="form-title">创建账户</h2>
        <p class="form-desc">开始您的行为健康旅程</p>

        <a-form :model="form" layout="vertical" @finish="handleRegister">
          <a-form-item name="username" :rules="[{ required: true, message: '请输入用户名' }]">
            <a-input v-model:value="form.username" placeholder="用户名" size="large" />
          </a-form-item>
          <a-form-item name="email" :rules="[{ required: true, type: 'email', message: '请输入有效邮箱' }]">
            <a-input v-model:value="form.email" placeholder="邮箱地址" size="large" />
          </a-form-item>
          <a-form-item name="display_name">
            <a-input v-model:value="form.display_name" placeholder="显示名称（选填）" size="large" />
          </a-form-item>
          <a-form-item name="password" :rules="[{ required: true, min: 6, message: '密码至少6位' }]">
            <a-input-password v-model:value="form.password" placeholder="设置密码" size="large" />
          </a-form-item>
          <a-form-item>
            <a-button type="primary" html-type="submit" block size="large" :loading="authStore.loading" class="submit-btn">
              注册
            </a-button>
          </a-form-item>
        </a-form>

        <a-alert v-if="errorMsg" :message="errorMsg" type="error" show-icon closable @close="errorMsg = ''" style="margin-bottom: 16px; border-radius: 10px;" />

        <div class="form-footer">
          <span style="color: #999; font-size: 14px;">已有账户？</span>
          <router-link to="/login" style="color: #2d8e69; font-weight: 600; margin-left: 6px;">立即登录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const form = ref({ username: '', email: '', password: '', display_name: '' })
const errorMsg = ref('')

async function handleRegister() {
  errorMsg.value = ''
  try {
    await authStore.register(form.value)
    router.push('/')
  } catch (err: any) {
    errorMsg.value = err.message || '注册失败'
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0f7f4 0%, #e8f0ee 50%, #f5f0eb 100%);
  padding: 24px;
}
.register-card {
  width: 100%;
  max-width: 440px;
  background: white;
  border-radius: 20px;
  padding: 48px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.1);
}
.brand-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 24px;
}
.brand-icon-sm {
  width: 36px; height: 36px; border-radius: 10px;
  background: linear-gradient(135deg, #4aa883, #2d8e69);
  display: flex; align-items: center; justify-content: center;
  font-family: 'Noto Serif SC', serif; font-weight: 700; font-size: 16px; color: white;
}
.brand-name {
  font-family: 'Noto Serif SC', serif; font-weight: 600; font-size: 16px; color: #333;
}
.form-title {
  font-size: 26px; font-weight: 700; color: #1a1a1a; margin: 0 0 6px;
}
.form-desc {
  font-size: 14px; color: #999; margin: 0 0 28px;
}
.submit-btn {
  border-radius: 10px; height: 44px; font-weight: 600;
  background: linear-gradient(135deg, #4aa883, #2d8e69); border: none; margin-top: 8px;
}
.form-footer { text-align: center; margin-top: 20px; }
</style>
