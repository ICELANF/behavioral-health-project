<template>
  <div class="upload-page">
    <div class="header-mini">
      <span @click="router.back()" style="cursor:pointer">&larr;</span>
      上传知识
    </div>
    <div class="content">
      <!-- 模式切换 -->
      <div class="mode-row fu">
        <div class="mode-btn" :class="{ sel: mode === 'text' }" @click="mode = 'text'">手动录入</div>
        <div class="mode-btn" :class="{ sel: mode === 'file' }" @click="mode = 'file'">文件灌注</div>
      </div>

      <!-- ===== 手动录入模式 ===== -->
      <template v-if="mode === 'text'">
        <div class="card fu fu-1">
          <div class="card-title">知识类型</div>
          <div class="type-row">
            <div v-for="t in types" :key="t.key"
              class="type-chip" :class="{ sel: form.type === t.key }"
              @click="form.type = t.key">
              <div class="type-icon">{{ t.icon }}</div>
              {{ t.label }}
            </div>
          </div>
        </div>

        <div class="card fu fu-1">
          <div class="card-title">知识内容</div>
          <textarea class="text-input" rows="6" v-model="form.content"
            placeholder="粘贴或输入您的临床知识...&#10;&#10;提示：使用清晰、可操作的语言。'奶奶测试' — 如果60岁老人能理解，就是好知识。" />
        </div>

        <div class="card fu fu-2">
          <div class="card-title">证据等级</div>
          <div class="type-row">
            <div v-for="e in tiers" :key="e.key"
              class="type-chip" :class="{ sel: form.evidence_tier === e.key }"
              @click="form.evidence_tier = e.key">{{ e.label }}</div>
          </div>
        </div>

        <div class="card fu fu-2">
          <div class="card-title">来源</div>
          <van-field v-model="form.source" placeholder="例如：ADA 2024指南、临床经验" />

          <div class="card-title" style="margin-top:12px">标签</div>
          <div class="tag-grid">
            <div v-for="t in tagOptions" :key="t"
              class="filter-chip" :class="{ sel: form.tags.includes(t) }"
              @click="toggleTag(t)">{{ t }}</div>
          </div>
        </div>

        <div style="display:flex;gap:8px">
          <button class="btn-outline" @click="router.back()">取消</button>
          <button class="btn-main" style="flex:1" :disabled="!canSubmitText" @click="submitText">
            {{ submitting ? '保存中...' : '保存知识（实时向量化）' }}
          </button>
        </div>
      </template>

      <!-- ===== 文件灌注模式 ===== -->
      <template v-if="mode === 'file'">
        <div class="card fu fu-1">
          <div class="card-title">上传文件</div>
          <div class="step-desc">支持 PDF、DOCX、TXT、Markdown 以及 ZIP/7Z/RAR 压缩包，单文件最大 100MB。系统将自动完成：</div>
          <div style="font-size:12px;color:var(--ink);line-height:1.8;margin-bottom:12px">
            1. 格式识别 &rarr; 2. 转 Markdown &rarr; 3. 智能切片 &rarr; 4. 1024维向量化 &rarr; 5. 入库检索就绪
          </div>
          <div class="upload-zone" :class="{ 'has-file': !!selectedFile }" @click="fileInput?.click()">
            <template v-if="!selectedFile">
              <div style="font-size:32px;margin-bottom:8px">+</div>
              <div style="font-size:14px;font-weight:700;color:var(--xzb-primary)">点击选择文件</div>
              <div style="font-size:11px;color:var(--sub);margin-top:4px">PDF / DOCX / MD / TXT / ZIP</div>
            </template>
            <template v-else>
              <div style="font-size:13px;font-weight:700;color:var(--ink)">{{ selectedFile.name }}</div>
              <div style="font-size:11px;color:var(--sub)">{{ (selectedFile.size / 1024).toFixed(0) }} KB</div>
            </template>
          </div>
          <input ref="fileInput" type="file" accept=".pdf,.docx,.txt,.md,.zip,.7z,.rar" style="display:none" @change="onFileSelect" />
        </div>

        <div class="card fu fu-2">
          <div class="card-title">证据等级</div>
          <div class="type-row">
            <div v-for="e in fileTiers" :key="e.key"
              class="type-chip" :class="{ sel: fileEvidenceTier === e.key }"
              @click="fileEvidenceTier = e.key">{{ e.label }}</div>
          </div>
        </div>

        <div style="display:flex;gap:8px">
          <button class="btn-outline" @click="router.back()">取消</button>
          <button class="btn-main" style="flex:1" :disabled="!selectedFile || uploading" @click="submitFile">
            {{ uploading ? '灌注中...' : '开始灌注' }}
          </button>
        </div>

        <!-- 灌注结果 -->
        <div v-if="batchResult" class="card fu" style="margin-top:4px">
          <div style="font-size:14px;font-weight:700;color:var(--xzb-green);margin-bottom:6px">
            灌注任务已提交
          </div>
          <div style="font-size:12px;color:var(--sub);line-height:1.8">
            任务ID: {{ batchResult.job_id }}<br/>
            状态: {{ batchResult.status }}<br/>
            文件数: {{ batchResult.total_files }}<br/>
            切片数: {{ batchResult.total_chunks }}
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { createKnowledge, batchUploadKnowledge } from '@/api/xzb'

const router = useRouter()
const mode = ref<'text' | 'file'>('text')
const submitting = ref(false)
const uploading = ref(false)
const fileInput = ref<HTMLInputElement>()
const selectedFile = ref<File | null>(null)
const fileEvidenceTier = ref('T3')

interface BatchResult {
  job_id: number; status: string; filename: string
  total_files: number; processed_files: number; total_chunks: number
}
const batchResult = ref<BatchResult | null>(null)

const form = reactive({
  type: 'clinical_note',
  content: '',
  evidence_tier: 'expert_opinion',
  source: '',
  tags: [] as string[],
  applicable_conditions: [] as string[],
})

const types = [
  { key: 'clinical_note', icon: '临', label: '临床笔记' },
  { key: 'evidence', icon: '证', label: '循证依据' },
  { key: 'template', icon: '方', label: '处方模板' },
  { key: 'faq', icon: '问', label: '常见问答' },
]

const tiers = [
  { key: 'rct', label: 'RCT' },
  { key: 'meta_analysis', label: '荟萃分析' },
  { key: 'guideline', label: '指南' },
  { key: 'expert_opinion', label: '专家意见' },
  { key: 'clinical_exp', label: '临床经验' },
]

const fileTiers = [
  { key: 'T1', label: 'T1 权威指南' },
  { key: 'T2', label: 'T2 专家共识' },
  { key: 'T3', label: 'T3 研究文献' },
  { key: 'T4', label: 'T4 经验资料' },
]

const tagOptions = [
  '2型糖尿病', '高血压', '肥胖', '失眠', '焦虑',
  '营养', '运动', '中医', '生活方式', '用药',
]

function toggleTag(t: string) {
  const idx = form.tags.indexOf(t)
  if (idx >= 0) form.tags.splice(idx, 1)
  else form.tags.push(t)
}

const canSubmitText = computed(() => form.content.trim().length >= 10)

async function submitText() {
  submitting.value = true
  try {
    await createKnowledge({
      type: form.type,
      content: form.content,
      evidence_tier: form.evidence_tier,
      source: form.source,
      tags: form.tags,
      applicable_conditions: form.applicable_conditions,
    })
    router.push('/knowledge')
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '保存失败'
    alert(msg)
  }
  submitting.value = false
}

function onFileSelect(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]
  if (f) selectedFile.value = f
}

async function submitFile() {
  if (!selectedFile.value) return
  uploading.value = true
  try {
    const res = await batchUploadKnowledge(selectedFile.value, fileEvidenceTier.value)
    batchResult.value = res.data
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '灌注失败'
    alert(msg)
  }
  uploading.value = false
}
</script>

<style scoped>
.header-mini {
  background: var(--grad-header); color: white;
  padding: 16px 20px; font-size: 16px; font-weight: 700;
  display: flex; align-items: center; gap: 10px;
}
.content { padding: 14px; display: flex; flex-direction: column; gap: 12px; }
.mode-row { display: flex; gap: 0; border-radius: var(--radius-sm); overflow: hidden; border: 1.5px solid var(--xzb-primary); }
.mode-btn {
  flex: 1; padding: 10px; text-align: center; font-size: 13px; font-weight: 700;
  cursor: pointer; color: var(--xzb-primary); background: white; transition: all .2s;
}
.mode-btn.sel { background: var(--xzb-primary); color: white; }
.step-desc { font-size: 12px; color: var(--sub); line-height: 1.6; }
.type-row { display: flex; gap: 6px; flex-wrap: wrap; }
.type-chip {
  padding: 8px 14px; border-radius: 10px; font-size: 12px; font-weight: 600;
  border: 1.5px solid var(--border); color: var(--sub); cursor: pointer;
  display: flex; align-items: center; gap: 6px; transition: all .2s;
}
.type-chip.sel { border-color: var(--xzb-primary); background: var(--xzb-primary-l); color: var(--xzb-primary); }
.type-icon { font-size: 11px; font-weight: 900; }
.text-input {
  width: 100%; border: 1.5px solid var(--border); border-radius: 12px;
  padding: 12px; font-size: 13px; resize: none; outline: none;
  color: var(--ink); background: white; transition: border-color .2s; line-height: 1.6;
}
.text-input:focus { border-color: var(--xzb-primary); }
.tag-grid { display: flex; flex-wrap: wrap; gap: 6px; }
.filter-chip {
  padding: 6px 12px; border-radius: 20px; font-size: 11px; font-weight: 600;
  border: 1.5px solid var(--border); color: var(--sub); cursor: pointer; transition: all .2s;
}
.filter-chip.sel { border-color: var(--xzb-primary); background: var(--xzb-primary-l); color: var(--xzb-primary); }
.upload-zone {
  border: 2px dashed var(--border-m); border-radius: 16px;
  background: var(--xzb-primary-l); padding: 28px 20px;
  text-align: center; cursor: pointer; transition: all .2s;
}
.upload-zone.has-file { border-style: solid; border-color: var(--xzb-primary); padding: 16px 20px; }
</style>
