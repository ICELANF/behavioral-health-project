<!--
  LoginView.vue — 登录页
  温暖的品牌视觉 + 表单验证 + 错误提示
-->

<template>
  <div class="login-page">
    <div class="login-card">
      <!-- 左侧品牌 -->
      <div class="brand-panel">
        <div class="brand-content">
          <div class="brand-icon">行</div>
          <h1 class="brand-title">行健平台</h1>
          <p class="brand-subtitle">BehaviorOS V4.0</p>
          <div class="brand-tagline">
            <p>天行健，君子以自强不息</p>
            <p class="tagline-en">Empowering Behavioral Health</p>
          </div>
          <div class="brand-features">
            <div class="feature-item">
              <span class="feature-dot"></span>
              <span>AI驱动的行为健康评估</span>
            </div>
            <div class="feature-item">
              <span class="feature-dot"></span>
              <span>个性化行为处方引擎</span>
            </div>
            <div class="feature-item">
              <span class="feature-dot"></span>
              <span>专业教练督导体系</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧表单 -->
      <div class="form-panel">
        <div class="form-content">
          <h2 class="form-title">欢迎回来</h2>
          <p class="form-desc">登录您的账户继续健康旅程</p>

          <a-form
            :model="form"
            layout="vertical"
            @finish="handleLogin"
            class="login-form"
          >
            <a-form-item
              name="username"
              :rules="[{ required: true, message: '请输入用户名' }]"
            >
              <a-input
                v-model:value="form.username"
                placeholder="用户名 / 邮箱"
                size="large"
                :prefix="h(UserOutlined)"
              />
            </a-form-item>

            <a-form-item
              name="password"
              :rules="[{ required: true, message: '请输入密码' }]"
            >
              <a-input-password
                v-model:value="form.password"
                placeholder="密码"
                size="large"
                :prefix="h(LockOutlined)"
              />
            </a-form-item>

            <a-form-item>
              <a-button
                type="primary"
                html-type="submit"
                block
                size="large"
                :loading="authStore.loading"
                class="login-btn"
              >
                登录
              </a-button>
            </a-form-item>
          </a-form>

          <a-alert
            v-if="errorMsg"
            :message="errorMsg"
            type="error"
            show-icon
            closable
            class="error-alert"
            @close="errorMsg = ''"
          />

          <div class="form-footer">
            <span class="footer-text">还没有账户？</span>
            <router-link to="/register" class="register-link">立即注册</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const form = ref({ username: '', password: '' })
const errorMsg = ref('')

async function handleLogin() {
  errorMsg.value = ''
  try {
    await authStore.login(form.value)
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch (err: any) {
    errorMsg.value = err.message || '登录失败，请检查用户名和密码'
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

.login-card {
  display: flex;
  width: 100%;
  max-width: 900px;
  min-height: 560px;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.05);
}

.brand-panel {
  flex: 1;
  background: linear-gradient(160deg, #1a3a2a 0%, #0f2a1e 40%, #1b4332 100%);
  padding: 48px;
  display: flex;
  align-items: center;
  position: relative;
  overflow: hidden;
}

.brand-panel::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -30%;
  width: 80%;
  height: 100%;
  background: radial-gradient(circle, rgba(74, 168, 131, 0.15) 0%, transparent 70%);
}

.brand-content {
  position: relative;
  z-index: 1;
}

.brand-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: linear-gradient(135deg, #4aa883 0%, #2d8e69 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Noto Serif SC', serif;
  font-weight: 700;
  font-size: 24px;
  color: white;
  margin-bottom: 24px;
  box-shadow: 0 4px 16px rgba(74, 168, 131, 0.4);
}

.brand-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 32px;
  font-weight: 700;
  color: white;
  margin: 0 0 4px 0;
}

.brand-subtitle {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.45);
  margin: 0 0 32px 0;
  letter-spacing: 1px;
}

.brand-tagline p {
  color: rgba(255, 255, 255, 0.7);
  font-size: 15px;
  margin: 0;
  line-height: 1.8;
}

.tagline-en {
  font-size: 12px !important;
  color: rgba(255, 255, 255, 0.35) !important;
  letter-spacing: 0.5px;
}

.brand-features {
  margin-top: 40px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
}

.feature-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #4aa883;
  flex-shrink: 0;
}

.form-panel {
  flex: 1;
  background: white;
  padding: 48px;
  display: flex;
  align-items: center;
}

.form-content {
  width: 100%;
  max-width: 340px;
  margin: 0 auto;
}

.form-title {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 26px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 6px 0;
}

.form-desc {
  font-size: 14px;
  color: #999;
  margin: 0 0 32px 0;
}

.login-form :deep(.ant-input-affix-wrapper) {
  border-radius: 10px;
  padding: 8px 14px;
}

.login-btn {
  border-radius: 10px;
  height: 44px;
  font-weight: 600;
  font-size: 15px;
  background: linear-gradient(135deg, #4aa883 0%, #2d8e69 100%);
  border: none;
  margin-top: 8px;
}

.login-btn:hover {
  background: linear-gradient(135deg, #5ab893 0%, #3d9e79 100%);
}

.error-alert {
  margin-bottom: 16px;
  border-radius: 10px;
}

.form-footer {
  text-align: center;
  margin-top: 24px;
}

.footer-text {
  color: #999;
  font-size: 14px;
}

.register-link {
  color: #2d8e69;
  font-weight: 600;
  margin-left: 6px;
}

@media (max-width: 768px) {
  .login-card {
    flex-direction: column;
    max-width: 440px;
  }
  .brand-panel {
    padding: 32px;
    min-height: auto;
  }
  .brand-features {
    display: none;
  }
}
</style>
