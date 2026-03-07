<template>
  <div class="faq-page">
    <div class="header-mini">
      <span @click="router.back()" style="cursor:pointer">&larr;</span>
      常见问题库
    </div>
    <div class="content">
      <!-- 领域筛选 -->
      <div class="filter-row fu">
        <div v-for="d in domains" :key="d.key"
          class="filter-chip" :class="{ sel: activeDomain === d.key }"
          @click="activeDomain = d.key; loadData()">{{ d.label }}</div>
      </div>

      <button class="btn-main fu fu-1" style="width:100%" @click="showAdd = true">+ 新建问答</button>

      <!-- FAQ 列表 -->
      <div v-for="item in faqs" :key="item.id" class="card fu fu-2">
        <div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:8px">
          <div class="q-badge">Q</div>
          <div style="flex:1;font-size:14px;font-weight:700;color:var(--ink);line-height:1.4">{{ item.question }}</div>
          <span class="chip chip--teal">{{ item.domain }}</span>
        </div>
        <div style="font-size:13px;color:var(--ink);line-height:1.6;padding-left:30px;margin-bottom:8px">
          {{ item.answer }}
        </div>
        <div style="display:flex;align-items:center;gap:8px;padding-left:30px">
          <div style="font-size:10px;color:var(--sub)">使用 {{ item.usage_count }} 次</div>
          <span style="flex:1" />
          <span style="font-size:11px;color:var(--xzb-primary);cursor:pointer;font-weight:600" @click="startEdit(item)">编辑</span>
          <span style="font-size:11px;color:var(--xzb-red);cursor:pointer;font-weight:600" @click="handleDelete(item.id)">删除</span>
        </div>
      </div>

      <div v-if="faqs.length === 0" class="card fu fu-2" style="text-align:center;padding:32px">
        <div style="font-size:14px;font-weight:700;margin-bottom:6px">暂无常见问题</div>
        <div style="font-size:13px;color:var(--sub);line-height:1.6">
          创建领域内常见问题，AI 智伴会优先匹配这些问答来服务求助者。与行为处方结合，可实现精准引导。
        </div>
      </div>

      <!-- 新建/编辑弹窗 -->
      <div v-if="showAdd" class="modal-mask" @click.self="showAdd = false">
        <div class="modal-body">
          <div style="font-size:16px;font-weight:800;margin-bottom:16px">{{ editId ? '编辑问答' : '新建问答' }}</div>
          <van-field v-model="formQ" label="问题" type="textarea" rows="2" placeholder="用户/患者最常问的问题..." />
          <van-field v-model="formA" label="回答" type="textarea" rows="4" placeholder="专业且通俗的回答...&#10;提示：可包含行为处方建议，如：建议每天饭后散步15分钟" style="margin-top:8px" />
          <div style="margin-top:8px">
            <div style="font-size:12px;font-weight:600;color:var(--sub);margin-bottom:4px">所属领域</div>
            <div style="display:flex;gap:6px;flex-wrap:wrap">
              <div v-for="d in domains.slice(1)" :key="d.key"
                class="filter-chip" :class="{ sel: formDomain === d.key }"
                @click="formDomain = d.key">{{ d.label }}</div>
            </div>
          </div>
          <div style="display:flex;gap:8px;margin-top:16px">
            <button class="btn-outline" style="flex:1" @click="showAdd = false; editId = ''">取消</button>
            <button class="btn-main" style="flex:1" :disabled="!formQ.trim() || !formA.trim()" @click="submitFAQ">
              {{ editId ? '保存修改' : '创建' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listFAQ, createFAQ, updateFAQ, deleteFAQ } from '@/api/xzb'

const router = useRouter()
const showAdd = ref(false)
const formQ = ref('')
const formA = ref('')
const formDomain = ref('general')
const editId = ref('')
const activeDomain = ref('all')

interface FAQ {
  id: string; question: string; answer: string; domain: string
  tags: string[]; usage_count: number
}

const faqs = ref<FAQ[]>([])

const domains = [
  { key: 'all', label: '全部' },
  { key: '2型糖尿病', label: '糖尿病' },
  { key: '高血压', label: '高血压' },
  { key: '肥胖', label: '肥胖' },
  { key: '失眠', label: '失眠' },
  { key: '焦虑', label: '焦虑/情绪' },
  { key: '营养', label: '营养' },
  { key: '运动', label: '运动' },
  { key: '中医', label: '中医养生' },
  { key: 'general', label: '通用' },
]

async function loadData() {
  try {
    const params: Record<string, unknown> = {}
    if (activeDomain.value !== 'all') params.domain = activeDomain.value
    const res = await listFAQ(params)
    faqs.value = res.data.items || []
  } catch { faqs.value = [] }
}

function startEdit(item: FAQ) {
  editId.value = item.id
  formQ.value = item.question
  formA.value = item.answer
  formDomain.value = item.domain
  showAdd.value = true
}

async function submitFAQ() {
  const data = { question: formQ.value, answer: formA.value, domain: formDomain.value, tags: [] as string[] }
  try {
    if (editId.value) {
      await updateFAQ(editId.value, data)
    } else {
      await createFAQ(data)
    }
    showAdd.value = false
    formQ.value = ''
    formA.value = ''
    editId.value = ''
    loadData()
  } catch { /* ignore */ }
}

async function handleDelete(id: string) {
  if (!confirm('确认删除这条问答？')) return
  try {
    await deleteFAQ(id)
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
.filter-row { display: flex; gap: 6px; overflow-x: auto; }
.filter-chip {
  padding: 6px 12px; border-radius: 20px; font-size: 11px; font-weight: 600;
  border: 1.5px solid var(--border); color: var(--sub); cursor: pointer;
  white-space: nowrap; transition: all .2s;
}
.filter-chip.sel { border-color: var(--xzb-primary); background: var(--xzb-primary-l); color: var(--xzb-primary); }
.q-badge {
  width: 22px; height: 22px; border-radius: 6px; flex-shrink: 0;
  background: var(--xzb-primary); color: white;
  font-size: 11px; font-weight: 900;
  display: flex; align-items: center; justify-content: center;
}
.modal-mask {
  position: fixed; inset: 0; background: rgba(0,0,0,.5);
  display: flex; align-items: flex-end; z-index: 200;
}
.modal-body {
  background: white; width: 100%; max-width: 480px; margin: 0 auto;
  border-radius: 20px 20px 0 0; padding: 24px 20px env(safe-area-inset-bottom, 20px);
  max-height: 85vh; overflow-y: auto;
}
</style>
