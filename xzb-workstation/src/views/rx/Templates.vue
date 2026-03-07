<template>
  <div class="rx-page">
    <div class="header-mini">
      <span @click="router.back()" style="cursor:pointer">&larr;</span>
      处方模板库
    </div>
    <div class="content">
      <button class="btn-main fu" style="width:100%" @click="showAdd = true">+ 新建模板</button>

      <div v-for="t in templates" :key="t.id" class="card fu fu-1">
        <div style="display:flex;gap:4px;margin-bottom:6px">
          <span v-for="tag in (t.tags || []).slice(0,3)" :key="tag" class="chip chip--teal">{{ tag }}</span>
        </div>
        <div style="font-size:12px;color:var(--sub)">证据等级: {{ t.evidence_tier }}</div>
      </div>

      <div v-if="templates.length === 0" class="card fu fu-1" style="text-align:center;padding:32px">
        <div style="font-size:14px;font-weight:700">暂无模板</div>
        <div style="font-size:13px;color:var(--sub)">创建常见场景的处方模板，提高效率。</div>
      </div>

      <div v-if="showAdd" class="modal-mask" @click.self="showAdd = false">
        <div class="modal-body">
          <div style="font-size:16px;font-weight:800;margin-bottom:16px">新建处方模板</div>
          <textarea class="text-input" rows="5" v-model="newContent" placeholder="处方模板内容..." />
          <van-field v-model="newSource" label="来源" placeholder="例如：临床经验" style="margin-top:8px" />
          <div style="display:flex;gap:8px;margin-top:16px">
            <button class="btn-outline" style="flex:1" @click="showAdd = false">取消</button>
            <button class="btn-main" style="flex:1" @click="addTemplate">保存</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listRxTemplates, createRxTemplate } from '@/api/xzb'

const router = useRouter()
const showAdd = ref(false)
const newContent = ref('')
const newSource = ref('')

interface Template { id: string; tags: string[]; evidence_tier: string }
const templates = ref<Template[]>([])

async function loadData() {
  try {
    const res = await listRxTemplates()
    templates.value = res.data.templates || []
  } catch { templates.value = [] }
}

async function addTemplate() {
  try {
    await createRxTemplate({
      type: 'template',
      content: newContent.value,
      evidence_tier: 'expert_opinion',
      source: newSource.value,
      tags: [],
    })
    showAdd.value = false
    newContent.value = ''
    newSource.value = ''
    loadData()
  } catch { /* ignore */ }
}

onMounted(loadData)
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
.modal-mask {
  position: fixed; inset: 0; background: rgba(0,0,0,.5);
  display: flex; align-items: flex-end; z-index: 200;
}
.modal-body {
  background: white; width: 100%; max-width: 480px; margin: 0 auto;
  border-radius: 20px 20px 0 0; padding: 24px 20px env(safe-area-inset-bottom, 20px);
}
</style>
