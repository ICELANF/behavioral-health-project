<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import type { LoginRequest } from '@/types'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 表单数据
const formData = ref<LoginRequest>({
  username: '',
  password: ''
})

// 加载状态
const loading = ref(false)

/**
 * 提交登录
 */
const onSubmit = async () => {
  loading.value = true
  try {
    await userStore.login(formData.value)

    // 登录成功，跳转到目标页面或首页
    const redirect = (route.query.redirect as string) || '/'
    router.replace(redirect)
  } catch (error) {
    console.error('Login error:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 跳转到注册页
 */
const goToRegister = () => {
  router.push('/register')
}
</script>

<template>
  <div class="login-page page-container">
    <van-nav-bar title="用户登录" />

    <div class="content-wrapper">
      <!-- Logo区域 -->
      <div class="logo-section">
        <div class="logo-icon">🏥</div>
        <div class="logo-title">行为健康平台</div>
        <div class="logo-subtitle">您的健康管理助手</div>
      </div>

      <!-- 登录表单 -->
      <van-form @submit="onSubmit">
        <van-cell-group inset>
          <van-field
            v-model="formData.username"
            name="username"
            label="用户名"
            placeholder="请输入用户名或邮箱"
            :rules="[{ required: true, message: '请填写用户名' }]"
            clearable
          />
          <van-field
            v-model="formData.password"
            type="password"
            name="password"
            label="密码"
            placeholder="请输入密码"
            :rules="[{ required: true, message: '请填写密码' }]"
            clearable
          />
        </van-cell-group>

        <div class="button-group">
          <van-button
            round
            block
            type="primary"
            native-type="submit"
            :loading="loading"
            loading-text="登录中..."
          >
            登录
          </van-button>

          <van-button round block plain type="primary" @click="goToRegister">
            还没有账号？立即注册
          </van-button>
        </div>
      </van-form>

      <!-- 测试账号提示 -->
      <div class="test-account-hint">
        <van-divider>测试账号</van-divider>
        <div class="hint-content">
          <p>患者账号：patient_alice / password123</p>
          <p>教练账号：coach_carol / coach123</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
}

.logo-section {
  text-align: center;
  padding: 60px 0 40px;
}

.logo-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.logo-title {
  font-size: 24px;
  font-weight: bold;
  color: #323233;
  margin-bottom: 8px;
}

.logo-subtitle {
  font-size: 14px;
  color: #969799;
}

.test-account-hint {
  margin-top: 40px;
  padding: 0 16px;
}

.hint-content {
  font-size: 12px;
  color: #969799;
  line-height: 1.8;
  text-align: center;
}

.hint-content p {
  margin: 4px 0;
}
</style>
