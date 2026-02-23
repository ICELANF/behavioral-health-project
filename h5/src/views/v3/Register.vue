<template>
  <div class="login-page">
    <van-nav-bar title="注册" left-arrow @click-left="$router.back()" />
    <van-form @submit="onRegister" class="login-form">
      <van-cell-group inset>
        <van-field v-model="phone" type="tel" label="手机号" placeholder="请输入手机号" maxlength="11"
          :rules="[{ pattern: /^1\d{10}$/, message: '请输入正确的手机号' }]" />
        <van-field v-model="nickname" label="昵称" placeholder="选填" maxlength="20" />
        <van-field v-model="password" type="password" label="密码" placeholder="至少6位"
          :rules="[{ validator: v => v.length >= 6, message: '密码至少6位' }]" />
        <van-field v-model="confirmPwd" type="password" label="确认密码" placeholder="再次输入密码"
          :rules="[{ validator: v => v === password, message: '两次密码不一致' }]" />
      </van-cell-group>
      <div class="actions">
        <van-button round block type="primary" native-type="submit" :loading="loading">注 册</van-button>
      </div>
    </van-form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { authApi } from '../../api/v3/index.js'

const router = useRouter()
const phone = ref(''); const nickname = ref(''); const password = ref(''); const confirmPwd = ref('')
const loading = ref(false)

async function onRegister() {
  loading.value = true
  try {
    const res = await authApi.register(phone.value, password.value, nickname.value)
    if (res?.data) {
      localStorage.setItem('access_token', res.data.tokens.access_token)
      localStorage.setItem('refresh_token', res.data.tokens.refresh_token)
      // 新注册用户默认Observer(level=1)
      localStorage.setItem('bhp_role_level', String(res.data.user?.role_level || 1))
      showToast('注册成功')
      router.push('/')
    } else {
      showToast(res?.message || '注册失败')
    }
  } catch (e) { showToast(e.response?.data?.detail || '网络错误') }
  finally { loading.value = false }
}
</script>

<style scoped>
.login-page { min-height: 100vh; background: #f7f8fa; }
.login-form { max-width: 400px; margin: 20px auto; }
.actions { padding: 24px 16px; }
</style>
