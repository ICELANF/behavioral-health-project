<template>
  <div class="config-page">
    <div class="header-mini">
      <span @click="router.back()" style="cursor:pointer">&larr;</span>
      智伴配置
    </div>
    <div class="content">
      <div class="card fu">
        <div class="card-title">基本设置</div>
        <van-field v-model="form.companion_name" label="智伴名称" placeholder="AI 智伴名称" />
        <van-field v-model="form.comm_style" label="沟通风格" placeholder="例如：温暖、专业" style="margin-top:8px" />
      </div>

      <div class="card fu fu-1">
        <div class="card-title">问候语</div>
        <textarea class="text-input" rows="3" v-model="form.greeting" placeholder="求助者看到的第一条消息..." />
      </div>

      <div class="card fu fu-2">
        <div class="card-title">安全边界声明</div>
        <textarea class="text-input" rows="3" v-model="form.boundary_stmt" placeholder="免责声明文本..." />
      </div>

      <div class="card fu fu-3">
        <div class="card-title">高级设置</div>
        <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 0">
          <span style="font-size:13px;font-weight:600">自动开方</span>
          <van-switch v-model="form.auto_rx_enabled" size="20px" />
        </div>
      </div>

      <button class="btn-main fu" style="width:100%" :disabled="saving" @click="save">
        {{ saving ? '保存中...' : '保存配置' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getMyConfig, updateMyConfig } from '@/api/xzb'

const router = useRouter()
const saving = ref(false)

const form = reactive({
  companion_name: '',
  greeting: '',
  comm_style: '',
  boundary_stmt: '',
  auto_rx_enabled: false,
})

onMounted(async () => {
  try {
    const res = await getMyConfig()
    Object.assign(form, res.data)
  } catch { /* not set up yet */ }
})

async function save() {
  saving.value = true
  try {
    await updateMyConfig({
      companion_name: form.companion_name,
      greeting: form.greeting,
      comm_style: form.comm_style,
      boundary_stmt: form.boundary_stmt,
      auto_rx_enabled: form.auto_rx_enabled,
    })
    router.back()
  } catch { alert('保存失败') }
  saving.value = false
}
</script>

<style scoped>
.header-mini {
  background: var(--grad-header); color: white;
  padding: 16px 20px; font-size: 16px; font-weight: 700;
  display: flex; align-items: center; gap: 10px;
}
.content { padding: 14px; display: flex; flex-direction: column; gap: 12px; }
.text-input {
  width: 100%; border: 1.5px solid var(--border); border-radius: 12px;
  padding: 12px; font-size: 13px; resize: none; outline: none;
  color: var(--ink); line-height: 1.6;
}
</style>
