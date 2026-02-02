<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import type { RegisterRequest } from '@/types'

const router = useRouter()
const userStore = useUserStore()

// 表单数据
const formData = ref<RegisterRequest>({
  username: '',
  email: '',
  password: '',
  full_name: ''
})

// 确认密码
const confirmPassword = ref('')

// 加载状态
const loading = ref(false)

/**
 * 密码验证
 */
const validatePassword = (val: string) => {
  if (val.length < 6) {
    return '密码长度至少6位'
  }
  return true
}

/**
 * 确认密码验证
 */
const validateConfirmPassword = (val: string) => {
  if (val !== formData.value.password) {
    return '两次密码输入不一致'
  }
  return true
}

/**
 * 提交注册
 */
const onSubmit = async () => {
  // 再次检查密码一致性
  if (confirmPassword.value !== formData.value.password) {
    return
  }

  loading.value = true
  try {
    await userStore.register(formData.value)

    // 注册成功，跳转到首页
    router.replace('/')
  } catch (error) {
    console.error('Register error:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 返回登录页
 */
const goToLogin = () => {
  router.push('/login')
}
</script>

<template>
  <div class="register-page page-container">
    <van-nav-bar title="用户注册" left-text="返回" left-arrow @click-left="goToLogin" />

    <div class="content-wrapper">
      <!-- 注册表单 -->
      <van-form @submit="onSubmit">
        <van-cell-group inset>
          <van-field
            v-model="formData.username"
            name="username"
            label="用户名"
            placeholder="请输入用户名（字母、数字、下划线）"
            :rules="[
              { required: true, message: '请填写用户名' },
              { pattern: /^[a-zA-Z0-9_]{3,20}$/, message: '用户名格式不正确' }
            ]"
            clearable
          />

          <van-field
            v-model="formData.email"
            name="email"
            type="email"
            label="邮箱"
            placeholder="请输入邮箱地址"
            :rules="[
              { required: true, message: '请填写邮箱' },
              { pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: '邮箱格式不正确' }
            ]"
            clearable
          />

          <van-field
            v-model="formData.full_name"
            name="full_name"
            label="姓名"
            placeholder="请输入真实姓名（可选）"
            clearable
          />

          <van-field
            v-model="formData.password"
            type="password"
            name="password"
            label="密码"
            placeholder="请输入密码（至少6位）"
            :rules="[{ required: true, message: '请填写密码' }, { validator: validatePassword }]"
            clearable
          />

          <van-field
            v-model="confirmPassword"
            type="password"
            name="confirmPassword"
            label="确认密码"
            placeholder="请再次输入密码"
            :rules="[
              { required: true, message: '请确认密码' },
              { validator: validateConfirmPassword }
            ]"
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
            loading-text="注册中..."
          >
            立即注册
          </van-button>

          <van-button round block plain type="primary" @click="goToLogin">
            已有账号？去登录
          </van-button>
        </div>
      </van-form>

      <!-- 提示信息 -->
      <div class="register-hint">
        <van-notice-bar
          left-icon="info-o"
          text="注册即表示您同意我们的服务条款和隐私政策"
          color="#1989fa"
          background="#ecf9ff"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.register-page {
  min-height: 100vh;
}

.register-hint {
  margin-top: 20px;
  padding: 0 16px;
}
</style>
