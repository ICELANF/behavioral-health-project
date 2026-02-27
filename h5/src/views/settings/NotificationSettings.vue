<template>
  <div class="page-container">
    <van-nav-bar title="通知设置" left-arrow @click-left="$router.back()" />

    <div class="page-content">
      <van-loading v-if="loading" class="loading" />
      <template v-else>
        <div class="settings-section">
          <div class="section-title">通知渠道</div>
          <div class="section-desc">选择您希望接收通知的方式</div>

          <van-cell-group inset>
            <van-cell
              v-for="ch in channels"
              :key="ch.value"
              :title="ch.label"
              :label="ch.desc"
              clickable
              @click="selectChannel(ch.value)"
            >
              <template #right-icon>
                <van-icon
                  :name="currentChannel === ch.value ? 'checked' : 'circle'"
                  :color="currentChannel === ch.value ? '#1989fa' : '#c8c9cc'"
                  size="22"
                />
              </template>
              <template #icon>
                <van-icon :name="ch.icon" size="22" :color="ch.color" style="margin-right: 12px" />
              </template>
            </van-cell>
          </van-cell-group>
        </div>

        <div class="save-area" v-if="dirty">
          <van-button type="primary" block round :loading="saving" @click="save">
            保存设置
          </van-button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { showToast } from 'vant'
import api from '@/api/index'

const loading = ref(true)
const saving = ref(false)
const currentChannel = ref('app')
const originalChannel = ref('app')
const dirty = ref(false)

const channels = [
  { value: 'app', label: '应用内通知', desc: '通过APP推送消息（默认）', icon: 'bell', color: '#1989fa' },
  { value: 'wechat', label: '微信通知', desc: '通过微信服务号推送', icon: 'wechat', color: '#07c160' },
  { value: 'sms', label: '短信通知', desc: '通过短信发送重要提醒', icon: 'comment-o', color: '#ff976a' },
  { value: 'email', label: '邮件通知', desc: '通过邮件发送详细报告', icon: 'envelop-o', color: '#7c3aed' },
]

function selectChannel(val: string) {
  currentChannel.value = val
  dirty.value = val !== originalChannel.value
}

async function save() {
  saving.value = true
  try {
    await api.put('/api/v1/admin/user-notification-preferences', {
      preferred_channel: currentChannel.value,
    })
    originalChannel.value = currentChannel.value
    dirty.value = false
    showToast('设置已保存')
  } catch {
    showToast('保存失败，请重试')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    const res: any = await api.get('/api/v1/admin/user-notification-preferences')
    currentChannel.value = res.preferred_channel || 'app'
    originalChannel.value = currentChannel.value
  } catch {
    // 使用默认值
  } finally {
    loading.value = false
  }
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.loading { text-align: center; padding: 60px 0; }

.settings-section {
  padding: $spacing-md;

  .section-title {
    font-size: $font-size-lg;
    font-weight: 600;
    color: #111827;
    margin-bottom: 4px;
  }

  .section-desc {
    font-size: $font-size-sm;
    color: $text-color-secondary;
    margin-bottom: $spacing-md;
  }
}

.save-area {
  padding: $spacing-lg $spacing-md;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #fff;
  box-shadow: 0 -2px 8px rgba(0,0,0,0.06);
}
</style>
