<template>
  <PageShell title="账号设置" :show-back="true">
      <!-- 账号信息 -->
      <div class="card">
        <h3>账号信息</h3>
        <van-cell-group :border="false">
          <van-cell title="用户名" :value="userInfo.username" />
          <van-cell title="邮箱" :value="userInfo.email" />
          <van-cell title="角色" :value="roleLabel" />
          <van-cell title="状态">
            <template #value>
              <van-tag :type="userInfo.is_active ? 'success' : 'danger'">
                {{ userInfo.is_active ? '正常' : '已禁用' }}
              </van-tag>
            </template>
          </van-cell>
        </van-cell-group>
      </div>

      <!-- 修改密码 -->
      <div class="card">
        <h3>修改密码</h3>
        <van-cell-group :border="false">
          <van-field
            v-model="pwForm.old_password"
            type="password"
            label="当前密码"
            placeholder="请输入当前密码"
          />
          <van-field
            v-model="pwForm.new_password"
            type="password"
            label="新密码"
            placeholder="请输入新密码（至少6位）"
          />
          <van-field
            v-model="pwForm.confirm_password"
            type="password"
            label="确认密码"
            placeholder="请再次输入新密码"
          />
        </van-cell-group>
        <div class="form-actions">
          <van-button type="primary" block round :loading="changingPw" @click="changePassword">
            确认修改
          </van-button>
        </div>
      </div>

      <!-- 其他设置 -->
      <div class="card">
        <h3>通知设置</h3>
        <van-cell-group :border="false">
          <van-cell title="健康提醒" center>
            <template #right-icon>
              <van-switch v-model="settings.healthReminder" size="24" />
            </template>
          </van-cell>
          <van-cell title="消息推送" center>
            <template #right-icon>
              <van-switch v-model="settings.messagePush" size="24" />
            </template>
          </van-cell>
          <van-cell title="运动提醒" center>
            <template #right-icon>
              <van-switch v-model="settings.exerciseReminder" size="24" />
            </template>
          </van-cell>
        </van-cell-group>
      </div>
  </PageShell>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { showToast } from 'vant'
import PageShell from '@/components/common/PageShell.vue'
import api from '@/api/index'
import storage from '@/utils/storage'

const ROLE_MAP: Record<string, string> = {
  admin: '管理员', coach: '健康教练', grower: '成长者', sharer: '分享者',
  observer: '观察员', supervisor: '督导', promoter: '推广者', master: '大师',
  ADMIN: '管理员', COACH: '健康教练', GROWER: '成长者', SHARER: '分享者',
  OBSERVER: '观察员', SUPERVISOR: '督导', PROMOTER: '推广者', MASTER: '大师',
}

const userInfo = ref<Record<string, any>>({})
const changingPw = ref(false)

const pwForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const SETTINGS_KEY = 'bhp_notification_settings'
function loadSettings() {
  try {
    const saved = localStorage.getItem(SETTINGS_KEY)
    if (saved) return JSON.parse(saved)
  } catch { /* use defaults */ }
  return { healthReminder: true, messagePush: true, exerciseReminder: false }
}
const settings = reactive(loadSettings())

watch(settings, (val) => {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(val))
})

const roleLabel = computed(() => ROLE_MAP[userInfo.value.role] || userInfo.value.role || '--')

async function changePassword() {
  if (!pwForm.old_password || !pwForm.new_password) {
    showToast('请填写完整密码信息')
    return
  }
  if (pwForm.new_password.length < 6) {
    showToast('新密码长度不能少于6位')
    return
  }
  if (pwForm.new_password !== pwForm.confirm_password) {
    showToast('两次输入的密码不一致')
    return
  }

  changingPw.value = true
  try {
    await api.put('/api/v1/auth/password', {
      old_password: pwForm.old_password,
      new_password: pwForm.new_password
    })
    showToast({ message: '密码修改成功', type: 'success' })
    pwForm.old_password = ''
    pwForm.new_password = ''
    pwForm.confirm_password = ''
  } catch (e: any) {
    showToast(e.response?.data?.detail || '密码修改失败')
  } finally {
    changingPw.value = false
  }
}

onMounted(async () => {
  const cached = storage.getAuthUser()
  if (cached) userInfo.value = cached
  try {
    const res: any = await api.get('/api/v1/auth/me')
    userInfo.value = res
  } catch {}
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.card {
  h3 {
    font-size: $font-size-lg;
    margin-bottom: $spacing-sm;
  }
}

.form-actions {
  padding: $spacing-md 0 0;
}
</style>
