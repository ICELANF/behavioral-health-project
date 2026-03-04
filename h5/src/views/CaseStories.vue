<template>
  <div class="cs-page">
    <van-nav-bar title="成长案例" left-arrow @click-left="goBack()" >
      <template #right>
        <van-button size="mini" type="primary" round @click="openPublish">发布</van-button>
      </template>
    </van-nav-bar>

    <!-- 分类筛选 -->
    <div class="domain-tabs">
      <button
        v-for="d in domains"
        :key="d.key"
        class="domain-tab"
        :class="{ active: selectedDomain === d.key }"
        @click="selectDomain(d.key)"
      >{{ d.label }}</button>
    </div>

    <!-- 案例列表 -->
    <div class="cs-list">
      <van-loading v-if="loading" size="24" class="cs-loading" />
      <van-empty v-else-if="!cases.length" description="暂无案例，成为第一个分享者吧" />
      <template v-else>
        <div v-for="c in cases" :key="c.id" class="cs-card" @click="viewCase(c)">
          <div class="cs-card-header">
            <span class="cs-domain-tag">{{ domainLabel(c.domain) }}</span>
            <span class="cs-anon" v-if="c.detail?.is_anonymous || c.is_anonymous">匿名</span>
            <span class="cs-author" v-else>{{ c.author_name || c.created_by_name || '成长者' }}</span>
          </div>
          <div class="cs-title">{{ c.title }}</div>
          <div class="cs-preview">{{ c.content?.slice(0, 80) }}{{ (c.content?.length || 0) > 80 ? '…' : '' }}</div>
          <div class="cs-meta">
            <span class="cs-date">{{ formatDate(c.created_at) }}</span>
            <span class="cs-likes" v-if="c.likes_count">👍 {{ c.likes_count }}</span>
          </div>
        </div>

        <div class="cs-load-more" v-if="hasMore">
          <van-button plain round size="small" :loading="loadingMore" @click="loadMore">加载更多</van-button>
        </div>
      </template>
    </div>

    <!-- 案例详情弹窗 -->
    <van-popup v-model:show="showDetail" position="bottom" round :style="{ maxHeight: '85vh', overflowY: 'auto' }">
      <div class="detail-popup" v-if="selectedCase">
        <div class="detail-top">
          <span class="cs-domain-tag">{{ domainLabel(selectedCase.domain) }}</span>
          <span class="detail-close-btn" @click="showDetail = false">✕</span>
        </div>
        <div class="detail-title">{{ selectedCase.title }}</div>
        <div class="detail-author">
          {{ selectedCase.detail?.is_anonymous || selectedCase.is_anonymous ? '匿名成长者' : (selectedCase.author_name || '成长者') }}
          · {{ formatDate(selectedCase.created_at) }}
        </div>
        <div class="detail-section">
          <div class="detail-section-label">遇到的挑战</div>
          <div class="detail-section-body">{{ extractSection(selectedCase, 'challenge') }}</div>
        </div>
        <div class="detail-section">
          <div class="detail-section-label">我的方法</div>
          <div class="detail-section-body">{{ extractSection(selectedCase, 'approach') }}</div>
        </div>
        <div class="detail-section">
          <div class="detail-section-label">取得的成果</div>
          <div class="detail-section-body">{{ extractSection(selectedCase, 'outcome') }}</div>
        </div>
        <div class="detail-section" v-if="extractSection(selectedCase, 'reflection')">
          <div class="detail-section-label">深度反思</div>
          <div class="detail-section-body">{{ extractSection(selectedCase, 'reflection') }}</div>
        </div>
      </div>
    </van-popup>

    <!-- 发布案例弹窗 -->
    <van-popup v-model:show="showPublish" position="bottom" round :style="{ maxHeight: '92vh', overflowY: 'auto' }">
      <div class="publish-popup">
        <div class="publish-header">
          <span class="publish-title">分享成长案例</span>
          <span class="publish-close" @click="showPublish = false">✕</span>
        </div>

        <van-field v-model="form.title" label="标题" placeholder="用一句话概括你的故事" clearable maxlength="50" show-word-limit />

        <div class="field-row">
          <span class="field-label">领域</span>
          <div class="domain-pills">
            <span
              v-for="d in domains.slice(1)"
              :key="d.key"
              class="domain-pill"
              :class="{ active: form.domain === d.key }"
              @click="form.domain = d.key"
            >{{ d.label }}</span>
          </div>
        </div>

        <van-field v-model="form.challenge" type="textarea" :rows="3" label="遇到的挑战" placeholder="描述你面对的困难或挑战…" maxlength="500" show-word-limit />
        <van-field v-model="form.approach" type="textarea" :rows="3" label="我的方法" placeholder="你是如何应对的？用了什么策略？" maxlength="500" show-word-limit />
        <van-field v-model="form.outcome" type="textarea" :rows="3" label="取得的成果" placeholder="结果如何？有哪些具体的改变？" maxlength="500" show-word-limit />
        <van-field v-model="form.reflection" type="textarea" :rows="2" label="深度反思（选填）" placeholder="这段经历让你对自己或健康有什么新认识？" maxlength="300" show-word-limit />

        <div class="anon-row">
          <span class="anon-label">{{ form.is_anonymous ? '匿名发布' : '实名发布' }}</span>
          <van-switch v-model="form.is_anonymous" size="20px" />
        </div>

        <div class="publish-actions">
          <van-button plain round @click="showPublish = false">取消</van-button>
          <van-button type="primary" round :loading="submitting" :disabled="!canSubmit" @click="submitCase">发布案例</van-button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { showSuccessToast, showFailToast } from 'vant'
import api from '@/api/index'
import { useGoBack } from '@/composables/useGoBack'

const { goBack } = useGoBack()

const domains = [
  { key: '', label: '全部' },
  { key: 'blood_glucose', label: '血糖管理' },
  { key: 'weight', label: '体重管理' },
  { key: 'exercise', label: '运动习惯' },
  { key: 'diet', label: '饮食调整' },
  { key: 'sleep', label: '睡眠改善' },
  { key: 'stress', label: '压力管理' },
  { key: 'medication', label: '用药依从' },
  { key: 'mental', label: '心理调适' },
]

function domainLabel(key?: string) {
  return domains.find(d => d.key === key)?.label || key || '综合'
}

function formatDate(iso?: string) {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

function extractSection(c: any, key: string): string {
  // The content is stored as markdown in content field; parse using detail if available
  if (c.detail?.[key]) return c.detail[key]
  // Fallback: parse markdown sections
  const content: string = c.content || ''
  const markers: Record<string, string> = {
    challenge: '**挑战：**',
    approach: '**方法：**',
    outcome: '**成果：**',
    reflection: '**反思：**',
  }
  const start = markers[key]
  if (!start) return ''
  const idx = content.indexOf(start)
  if (idx < 0) return ''
  const after = content.slice(idx + start.length).trimStart()
  const nextMatch = after.search(/\*\*[^*]+：\*\*/)
  return nextMatch > 0 ? after.slice(0, nextMatch).trim() : after.trim()
}

// ── State ──
const loading = ref(false)
const loadingMore = ref(false)
const submitting = ref(false)
const showDetail = ref(false)
const showPublish = ref(false)
const selectedDomain = ref('')
const cases = ref<any[]>([])
const selectedCase = ref<any>(null)
const hasMore = ref(false)
const skip = ref(0)
const LIMIT = 10

const form = reactive({
  title: '',
  domain: 'diet',
  challenge: '',
  approach: '',
  outcome: '',
  reflection: '',
  is_anonymous: false,
})

const canSubmit = computed(() =>
  form.title.trim().length >= 2 &&
  form.challenge.trim().length >= 10 &&
  form.approach.trim().length >= 10 &&
  form.outcome.trim().length >= 10
)

function selectDomain(key: string) {
  selectedDomain.value = key
  loadCases(true)
}

function viewCase(c: any) {
  selectedCase.value = c
  showDetail.value = true
}

function openPublish() {
  Object.assign(form, {
    title: '', domain: 'diet',
    challenge: '', approach: '', outcome: '', reflection: '', is_anonymous: false,
  })
  showPublish.value = true
}

async function loadCases(reset = false) {
  if (reset) { skip.value = 0; cases.value = [] }
  reset ? (loading.value = true) : (loadingMore.value = true)
  try {
    const params: Record<string, any> = { skip: skip.value, limit: LIMIT }
    if (selectedDomain.value) params.domain = selectedDomain.value
    const res: any = await api.get('/api/v1/content/cases', { params })
    const list = Array.isArray(res) ? res : (res?.items || res?.cases || [])
    cases.value = reset ? list : [...cases.value, ...list]
    hasMore.value = list.length === LIMIT
    skip.value += list.length
  } catch {
    // silent
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function loadMore() {
  loadCases(false)
}

async function submitCase() {
  submitting.value = true
  try {
    await api.post('/api/v1/content/case', {
      title: form.title.trim(),
      domain: form.domain,
      challenge: form.challenge.trim(),
      approach: form.approach.trim(),
      outcome: form.outcome.trim(),
      reflection: form.reflection.trim() || undefined,
      is_anonymous: form.is_anonymous,
      allow_comments: true,
    })
    showSuccessToast('案例发布成功')
    showPublish.value = false
    loadCases(true)
  } catch {
    showFailToast('发布失败，请重试')
  } finally {
    submitting.value = false
  }
}

onMounted(() => loadCases(true))
</script>

<style scoped>
.cs-page { min-height: 100vh; background: #f7f8fa; }

.domain-tabs {
  display: flex; gap: 8px; padding: 12px 16px; overflow-x: auto;
  background: #fff; border-bottom: 1px solid #f0f0f0;
}
.domain-tabs::-webkit-scrollbar { display: none; }
.domain-tab {
  flex-shrink: 0; background: #f3f4f6; border: none; border-radius: 20px;
  padding: 6px 14px; font-size: 13px; color: #666; cursor: pointer; transition: all 0.2s;
}
.domain-tab.active { background: #722ed1; color: #fff; }

.cs-list { padding: 12px 16px; }
.cs-loading { text-align: center; padding: 32px; display: block; }

.cs-card {
  background: #fff; border-radius: 12px; padding: 16px;
  margin-bottom: 12px; cursor: pointer; transition: transform 0.2s;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.cs-card:active { transform: scale(0.98); }

.cs-card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.cs-domain-tag {
  font-size: 11px; background: #f9f0ff; color: #722ed1;
  padding: 2px 8px; border-radius: 10px; font-weight: 600;
}
.cs-anon { font-size: 11px; color: #bbb; }
.cs-author { font-size: 11px; color: #999; }
.cs-title { font-size: 15px; font-weight: 700; color: #111; margin-bottom: 6px; }
.cs-preview { font-size: 13px; color: #666; line-height: 1.5; margin-bottom: 8px; }
.cs-meta { display: flex; gap: 12px; align-items: center; }
.cs-date { font-size: 12px; color: #bbb; }
.cs-likes { font-size: 12px; color: #999; }

.cs-load-more { text-align: center; padding: 12px 0; }

/* detail */
.detail-popup { padding: 20px 16px 32px; }
.detail-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.detail-close-btn { font-size: 18px; color: #bbb; cursor: pointer; padding: 4px; }
.detail-title { font-size: 18px; font-weight: 700; color: #111; margin-bottom: 6px; }
.detail-author { font-size: 12px; color: #bbb; margin-bottom: 16px; }
.detail-section { margin-bottom: 14px; }
.detail-section-label {
  font-size: 12px; font-weight: 700; color: #722ed1;
  text-transform: uppercase; margin-bottom: 6px; letter-spacing: 0.5px;
}
.detail-section-body { font-size: 14px; color: #333; line-height: 1.7; white-space: pre-wrap; }

/* publish */
.publish-popup { padding: 16px 0 32px; }
.publish-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 16px 12px; border-bottom: 1px solid #f0f0f0; margin-bottom: 8px;
}
.publish-title { font-size: 16px; font-weight: 700; }
.publish-close { font-size: 18px; color: #bbb; cursor: pointer; padding: 4px; }

.field-row { padding: 10px 16px; }
.field-label { font-size: 14px; color: #646566; display: block; margin-bottom: 8px; }
.domain-pills { display: flex; flex-wrap: wrap; gap: 8px; }
.domain-pill {
  padding: 5px 12px; border-radius: 20px; border: 1px solid #e5e7eb;
  font-size: 13px; color: #666; cursor: pointer; transition: all 0.2s;
}
.domain-pill.active { background: #722ed1; color: #fff; border-color: #722ed1; }

.anon-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; border-top: 1px solid #f5f5f5; margin-top: 4px;
}
.anon-label { font-size: 14px; color: #555; }
.publish-actions {
  display: flex; gap: 12px; padding: 16px 16px 0; justify-content: flex-end;
}
</style>
