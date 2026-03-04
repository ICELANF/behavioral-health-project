<template>
  <div class="bs-page">
    <van-nav-bar title="成为分享者" left-arrow @click-left="goBack()" />

    <van-loading v-if="loading" size="32" class="bs-loading" />

    <template v-else>
      <!-- 头部说明 -->
      <div class="bs-hero">
        <div class="bs-hero-icon">🌟</div>
        <div class="bs-hero-title">申请成为分享者</div>
        <div class="bs-hero-desc">
          分享者是平台成长社区的核心力量。你的亲身经历、收获与洞见，
          将照亮更多同道者的成长之路。
        </div>
      </div>

      <!-- 四维资质 -->
      <div class="section-card">
        <div class="section-title">资质检验</div>
        <div class="dim-list">
          <div v-for="dim in dims" :key="dim.key" class="dim-item">
            <div class="dim-check" :class="{ done: dim.done }">
              {{ dim.done ? '✓' : '○' }}
            </div>
            <div class="dim-body">
              <div class="dim-name">{{ dim.name }}</div>
              <div class="dim-desc">{{ dim.desc }}</div>
              <div class="dim-action" v-if="!dim.done" @click="$router.push(dim.route)">
                → {{ dim.actionLabel }}
              </div>
            </div>
            <div class="dim-status" :class="dim.done ? 'status-done' : 'status-pending'">
              {{ dim.done ? '达标' : '进行中' }}
            </div>
          </div>
        </div>
      </div>

      <!-- 申请陈述 -->
      <div class="section-card">
        <div class="section-title">申请陈述</div>
        <div class="stmt-guide">
          <div class="stmt-guide-item">📝 我的主要收获：我在健康管理上得到了什么？</div>
          <div class="stmt-guide-item">🌱 我的成长证明：有哪些具体改变？</div>
          <div class="stmt-guide-item">🤝 我的贡献意愿：我能为其他人提供什么？</div>
        </div>
        <van-field
          v-model="statement"
          type="textarea"
          :rows="6"
          placeholder="写下你的申请陈述（至少50字）…"
          maxlength="800"
          show-word-limit
          class="stmt-field"
        />
      </div>

      <!-- 申请历史 -->
      <div class="section-card" v-if="history.length">
        <div class="section-title">申请记录</div>
        <div v-for="h in history" :key="h.id" class="hist-item">
          <span class="hist-date">{{ formatDate(h.applied_at || h.created_at) }}</span>
          <span class="hist-status" :class="h.status">{{ statusLabel(h.status) }}</span>
        </div>
      </div>

      <!-- 提交 -->
      <div class="bs-footer">
        <div class="dim-summary">
          {{ readyCount }}/4 维度达标
          <span v-if="readyCount < 4" class="dim-hint">（未达标维度继续积累，可先提交申请）</span>
        </div>
        <van-button
          type="primary"
          block
          round
          :loading="submitting"
          :disabled="statement.trim().length < 50"
          @click="submitApplication"
          class="submit-btn"
        >
          提交申请
        </van-button>
        <div class="submit-hint">提交后教练将在3个工作日内审核</div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { showSuccessToast, showFailToast } from 'vant'
import { useRouter } from 'vue-router'
import api from '@/api/index'
import { useGoBack } from '@/composables/useGoBack'

const { goBack } = useGoBack()
const router = useRouter()

const loading = ref(false)
const submitting = ref(false)
const statement = ref('')
const history = ref<any[]>([])

// 四维达标状态（从各子系统加载）
const dimStatus = ref({
  reflection: false,  // 有成长感悟
  growth: false,       // TTM S2+
  caseStory: false,    // 有案例贡献
  trajectory: false,   // 行为轨迹达标
})

const dims = computed(() => [
  {
    key: 'reflection',
    name: '自我收获',
    desc: '已写下至少1篇成长感悟，记录你的收获与洞见',
    done: dimStatus.value.reflection,
    route: '/reflection',
    actionLabel: '去写成长感悟',
  },
  {
    key: 'growth',
    name: '在途成长',
    desc: 'TTM行为改变阶段处于S2(沉思)或以上，正在积极改变',
    done: dimStatus.value.growth,
    route: '/behavior-assessment',
    actionLabel: '完成行为评估',
  },
  {
    key: 'caseStory',
    name: '贡献案例',
    desc: '至少发布过1个成长案例，为社区提供参考',
    done: dimStatus.value.caseStory,
    route: '/case-stories',
    actionLabel: '发布成长案例',
  },
  {
    key: 'trajectory',
    name: '行为轨迹',
    desc: '综合成长分≥60，依从率≥50%，连续打卡≥3天',
    done: dimStatus.value.trajectory,
    route: '/trajectory',
    actionLabel: '查看行为轨迹',
  },
])

const readyCount = computed(() => dims.value.filter(d => d.done).length)

function formatDate(iso?: string) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('zh-CN')
}

function statusLabel(s: string) {
  return { pending: '审核中', approved: '已通过', rejected: '未通过' }[s] || s
}

async function loadData() {
  loading.value = true
  try {
    const [reflectRes, journeyRes, caseRes, trajRes, histRes] = await Promise.allSettled([
      api.get('/api/v1/reflection/stats'),
      api.get('/api/v1/journey/overview'),
      api.get('/api/v1/content/cases', { params: { limit: 1 } }),
      api.get('/api/v1/learning/trajectory', { params: { days: 30 } }),
      api.get('/api/v1/promotion/my-history'),
    ])

    if (reflectRes.status === 'fulfilled') {
      const r = reflectRes.value as any
      dimStatus.value.reflection = (r.total_entries ?? r.count ?? 0) >= 1
    }
    if (journeyRes.status === 'fulfilled') {
      const j = journeyRes.value as any
      const stage = j.current_level ?? j.ttm_stage ?? j.stage ?? 0
      dimStatus.value.growth = typeof stage === 'number'
        ? stage >= 2
        : parseInt(String(stage).replace(/\D/g, '') || '0') >= 2
    }
    if (caseRes.status === 'fulfilled') {
      const c = caseRes.value as any
      const list = Array.isArray(c) ? c : (c?.items || c?.cases || [])
      dimStatus.value.caseStory = list.length >= 1
    }
    if (trajRes.status === 'fulfilled') {
      const t = trajRes.value as any
      dimStatus.value.trajectory = t.qualifies_for_sharer === true
    }
    if (histRes.status === 'fulfilled') {
      const h = histRes.value as any
      history.value = Array.isArray(h) ? h : (h?.items || h?.history || [])
    }
  } finally {
    loading.value = false
  }
}

async function submitApplication() {
  if (statement.value.trim().length < 50) return
  submitting.value = true
  try {
    await api.post('/api/v1/promotion/sharer-apply', {
      statement: statement.value.trim(),
      target_role: 'sharer',
      dim_ready: readyCount.value,
    })
    showSuccessToast('申请已提交，等待审核')
    statement.value = ''
    loadData()
  } catch {
    showFailToast('提交失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

onMounted(() => loadData())
</script>

<style scoped>
.bs-page { min-height: 100vh; background: #f7f8fa; padding-bottom: 120px; }
.bs-loading { display: block; text-align: center; padding: 60px; }

.bs-hero {
  text-align: center; padding: 28px 24px 20px;
  background: linear-gradient(135deg, #ede9fe 0%, #dbeafe 100%);
}
.bs-hero-icon { font-size: 40px; margin-bottom: 8px; }
.bs-hero-title { font-size: 20px; font-weight: 800; color: #1e1b4b; margin-bottom: 8px; }
.bs-hero-desc { font-size: 14px; color: #5b21b6; line-height: 1.6; max-width: 300px; margin: 0 auto; }

.section-card {
  background: #fff; margin: 12px 16px; padding: 16px;
  border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,0.05);
}
.section-title { font-size: 15px; font-weight: 700; color: #111; margin-bottom: 14px; }

/* dim list */
.dim-list { display: flex; flex-direction: column; gap: 14px; }
.dim-item { display: flex; gap: 12px; align-items: flex-start; }
.dim-check {
  width: 28px; height: 28px; border-radius: 50%; border: 2px solid #d1d5db;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; color: #9ca3af; flex-shrink: 0; transition: all 0.3s;
}
.dim-check.done { background: #16a34a; border-color: #16a34a; color: #fff; font-weight: 700; }
.dim-body { flex: 1; }
.dim-name { font-size: 14px; font-weight: 700; color: #111; margin-bottom: 2px; }
.dim-desc { font-size: 12px; color: #6b7280; line-height: 1.4; }
.dim-action { font-size: 12px; color: #1565c0; margin-top: 4px; cursor: pointer; }
.dim-status {
  font-size: 11px; padding: 3px 8px; border-radius: 10px; flex-shrink: 0;
  font-weight: 600; margin-top: 2px;
}
.status-done { background: #dcfce7; color: #16a34a; }
.status-pending { background: #f3f4f6; color: #9ca3af; }

/* stmt */
.stmt-guide { margin-bottom: 12px; }
.stmt-guide-item { font-size: 12px; color: #6b7280; padding: 3px 0; }
.stmt-field { border-radius: 8px; background: #f9fafb; }

/* history */
.hist-item { display: flex; align-items: center; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f5f5f5; }
.hist-item:last-child { border-bottom: none; }
.hist-date { font-size: 13px; color: #6b7280; }
.hist-status { font-size: 12px; padding: 2px 8px; border-radius: 10px; font-weight: 600; }
.hist-status.approved { background: #dcfce7; color: #16a34a; }
.hist-status.pending { background: #fef3c7; color: #d97706; }
.hist-status.rejected { background: #fee2e2; color: #dc2626; }

/* footer */
.bs-footer {
  position: fixed; bottom: 0; left: 0; right: 0;
  background: #fff; padding: 16px 20px 32px;
  border-top: 1px solid #f0f0f0; box-shadow: 0 -2px 8px rgba(0,0,0,0.06);
}
.dim-summary { text-align: center; font-size: 13px; color: #6b7280; margin-bottom: 10px; }
.dim-hint { color: #9ca3af; }
.submit-btn { font-size: 15px; font-weight: 700; }
.submit-hint { text-align: center; font-size: 12px; color: #9ca3af; margin-top: 8px; }
</style>
