<template>
  <div class="trigger-page">
    <div class="header-mini">
      <span @click="router.back()" style="cursor:pointer">&larr;</span>
      为求助者 #{{ route.params.seekerId }} 开处方
    </div>
    <div class="content">
      <div class="card fu">
        <div class="card-title">处方草案</div>
        <textarea class="text-input" rows="5" v-model="note" placeholder="添加自定义策略或备注..." />
      </div>

      <button class="btn-main fu fu-1" style="width:100%" :disabled="submitting" @click="submit">
        {{ submitting ? '生成中...' : '触发处方草案' }}
      </button>

      <div v-if="result" class="card fu fu-2">
        <div style="font-size:14px;font-weight:700;color:var(--xzb-green);margin-bottom:6px">
          处方草案已创建
        </div>
        <div style="font-size:12px;color:var(--sub)">片段ID: {{ result.fragment_id }}</div>
        <div style="font-size:12px;color:var(--sub)">状态: {{ result.status }} &rarr; {{ result.next }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { triggerRx } from '@/api/xzb'

const route = useRoute()
const router = useRouter()
const note = ref('')
const submitting = ref(false)
const result = ref<{ fragment_id: string; status: string; next: string } | null>(null)

async function submit() {
  submitting.value = true
  try {
    const res = await triggerRx(Number(route.params.seekerId), {
      note: note.value,
      custom_strategies: [],
    })
    result.value = res.data
  } catch { alert('触发失败') }
  submitting.value = false
}

void router
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
