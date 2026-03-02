<template>
  <view class="review-page">
    <view class="review-navbar">
      <view class="review-nav-back" @tap="goBack">←</view>
      <text class="review-nav-title">评估审核</text>
    </view>

    <!-- 加载中 -->
    <view v-if="loading" class="review-loading">
      <text>加载评估数据...</text>
    </view>

    <scroll-view v-else scroll-y class="review-content">
      <!-- 学员信息 -->
      <view class="review-student">
        <view class="review-avatar" :style="{ background: avatarColor(data.student_name) }">
          {{ (data.student_name || '?')[0] }}
        </view>
        <view class="review-student-info">
          <text class="review-student-name">{{ data.student_name || '未知学员' }}</text>
          <text class="review-student-meta">评估时间: {{ formatDate(data.completed_at || data.created_at) }}</text>
        </view>
        <view class="review-status" :style="{ background: statusColor(data.status) }">
          {{ statusLabel(data.status) }}
        </view>
      </view>

      <!-- 大五人格 -->
      <view class="review-section" v-if="big5Data.length">
        <text class="review-section-title">🧠 大五人格 BIG5</text>
        <view class="review-big5">
          <view class="big5-item" v-for="item in big5Data" :key="item.name">
            <text class="big5-label">{{ item.name }}</text>
            <view class="big5-bar-bg">
              <view class="big5-bar-fill" :style="{ width: item.percent + '%', background: item.color }"></view>
            </view>
            <text class="big5-value">{{ item.score }}</text>
          </view>
        </view>
      </view>

      <!-- BPT6 行为类型 -->
      <view class="review-section" v-if="bptTags.length">
        <text class="review-section-title">🏷️ BPT6 行为类型</text>
        <view class="review-tags">
          <view class="review-tag" v-for="(tag, i) in bptTags" :key="i" :style="{ background: tagColors[i % tagColors.length] }">
            {{ tag }}
          </view>
        </view>
      </view>

      <!-- TTM 行为阶段 -->
      <view class="review-section" v-if="ttmStage">
        <text class="review-section-title">📈 TTM 行为改变阶段</text>
        <view class="ttm-timeline">
          <view
            v-for="(stage, i) in ttmStages" :key="i"
            class="ttm-stage" :class="{ 'ttm-stage--active': i === ttmStageIndex, 'ttm-stage--done': i < ttmStageIndex }"
          >
            <view class="ttm-dot"></view>
            <text class="ttm-label">{{ stage }}</text>
          </view>
        </view>
      </view>

      <!-- SPI/能力评估 -->
      <view class="review-section" v-if="capacityScores.length">
        <text class="review-section-title">💪 能力评估</text>
        <view class="capacity-list">
          <view class="capacity-item" v-for="c in capacityScores" :key="c.name">
            <text class="capacity-name">{{ c.name }}</text>
            <view class="capacity-bar-bg">
              <view class="capacity-bar-fill" :style="{ width: (c.score / c.max * 100) + '%' }"></view>
            </view>
            <text class="capacity-score">{{ c.score }}/{{ c.max }}</text>
          </view>
        </view>
      </view>

      <!-- AI 建议摘要 -->
      <view class="review-section" v-if="aiSuggestions.length">
        <text class="review-section-title">🤖 AI 分析建议</text>
        <view class="ai-suggestion" v-for="(s, i) in aiSuggestions" :key="i">
          <text class="ai-suggestion-num">{{ i + 1 }}</text>
          <text class="ai-suggestion-text">{{ s }}</text>
        </view>
      </view>

      <!-- 教练备注 -->
      <view class="review-section">
        <text class="review-section-title">📝 教练备注</text>
        <textarea
          class="review-note-input"
          placeholder="输入您的专业评估意见和建议..."
          v-model="coachNote"
          maxlength="500"
        />
        <text class="review-note-count">{{ coachNote.length }}/500</text>
      </view>

      <!-- 审核操作 -->
      <view class="review-actions" v-if="canReview">
        <view class="review-btn review-btn-reject" @tap="doReview('rejected')">退回修改</view>
        <view class="review-btn review-btn-approve" @tap="doReview('approved')">通过审核</view>
      </view>

      <view class="review-actions" v-else-if="data.status === 'completed' || data.status === 'reviewed'">
        <view class="review-completed-tag">✅ 评估已完成审核</view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const BASE_URL = 'http://localhost:8000'

function getToken(): string {
  return uni.getStorageSync('access_token') || ''
}

async function http<T = any>(url: string, options: any = {}): Promise<T> {
  const { method = 'GET', data } = options
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url,
      method,
      data,
      header: {
        'Authorization': 'Bearer ' + getToken(),
        'Content-Type': 'application/json'
      },
      success: (res: any) => {
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data as T)
        else reject(new Error(`HTTP ${res.statusCode}`))
      },
      fail: (err: any) => reject(err)
    })
  })
}

const loading = ref(true)
const data = ref<any>({})
const coachNote = ref('')

const ttmStages = ['前意向', '意向', '准备', '行动', '维持', '终止']
const tagColors = ['#3498DB', '#E67E22', '#27AE60', '#9B59B6', '#E74C3C', '#1ABC9C']
const AVATAR_COLORS = ['#3498DB', '#E67E22', '#27AE60', '#9B59B6', '#E74C3C', '#1ABC9C']

function avatarColor(name: string): string {
  if (!name) return '#8E99A4'
  let hash = 0; for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash)
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length]
}
function statusColor(s: string): string {
  const map: Record<string, string> = { pending: '#E67E22', assigned: '#E67E22', in_progress: '#3498DB', submitted: '#9B59B6', review: '#9B59B6', completed: '#27AE60', reviewed: '#27AE60', approved: '#27AE60', rejected: '#E74C3C' }
  return map[s] || '#8E99A4'
}
function statusLabel(s: string): string {
  const map: Record<string, string> = { pending: '待分配', assigned: '已分配', in_progress: '进行中', submitted: '待审核', review: '待审核', completed: '已完成', reviewed: '已审核', approved: '已通过', rejected: '已退回' }
  return map[s] || s
}
function formatDate(d: string): string { return d ? d.slice(0, 10) : '-' }

const canReview = computed(() => ['submitted', 'review', 'completed_pending_review'].includes(data.value.status))

const big5Data = computed(() => {
  const r = data.value.big5 || data.value.personality || data.value.results?.big5
  if (!r) return []
  const dims = [
    { key: 'openness', name: '开放性', color: '#3498DB' },
    { key: 'conscientiousness', name: '尽责性', color: '#27AE60' },
    { key: 'extraversion', name: '外向性', color: '#E67E22' },
    { key: 'agreeableness', name: '宜人性', color: '#9B59B6' },
    { key: 'neuroticism', name: '神经质', color: '#E74C3C' },
  ]
  return dims.map(d => {
    const score = r[d.key] ?? r[d.name] ?? 0
    return { ...d, score: Math.round(score * 10) / 10, percent: Math.min(100, Math.round((score / 7) * 100)) }
  })
})

const bptTags = computed(() => {
  const r = data.value.bpt6 || data.value.behavior_types || data.value.results?.bpt6
  if (Array.isArray(r)) return r.slice(0, 6)
  if (r && typeof r === 'object') return Object.keys(r).slice(0, 6)
  return []
})

const ttmStage = computed(() => data.value.ttm_stage || data.value.ttm || data.value.results?.ttm || '')
const ttmStageIndex = computed(() => {
  const s = ttmStage.value
  if (!s) return -1
  const map: Record<string, number> = { precontemplation: 0, contemplation: 1, preparation: 2, action: 3, maintenance: 4, termination: 5 }
  if (map[s] !== undefined) return map[s]
  return ttmStages.findIndex(st => s.includes(st))
})

const capacityScores = computed(() => {
  const r = data.value.capacity || data.value.results?.capacity
  if (!r) return []
  if (Array.isArray(r)) return r
  return Object.entries(r).map(([k, v]) => ({ name: k, score: Number(v) || 0, max: 10 }))
})

const aiSuggestions = computed(() => {
  const s = data.value.ai_suggestions || data.value.suggestions || data.value.results?.suggestions
  if (Array.isArray(s)) return s.slice(0, 5)
  if (typeof s === 'string') return s.split('\n').filter(Boolean).slice(0, 5)
  return []
})

async function loadData() {
  loading.value = true
  const id = (getCurrentPages().slice(-1)[0] as any)?.options?.id
  if (!id) { loading.value = false; return }

  // 尝试多个端点获取评估详情
  const endpoints = [
    `/api/v1/assessment-assignments/${id}/result`,
    `/api/v1/assessment-assignments/${id}`,
    `/api/v1/assessment/results/${id}`,
    `/api/v1/assessment/${id}`,
  ]
  for (const ep of endpoints) {
    try {
      const res = await http<any>(ep)
      data.value = res.result || res.assignment || res || {}
      break
    } catch { continue }
  }
  loading.value = false
}

async function doReview(action: string) {
  const id = data.value.id
  if (!id) return

  const confirmText = action === 'approved' ? '确认通过此评估？' : '确认退回此评估？'
  uni.showModal({
    title: '确认操作',
    content: confirmText,
    success: async (res) => {
      if (!res.confirm) return
      try {
        // 尝试多个审核端点
        try {
          await http(`/api/v1/assessment-assignments/${id}/review`, {
            method: 'POST',
            data: { action, note: coachNote.value }
          })
        } catch {
          await http(`/api/v1/assessment-assignments/${id}/${action === 'approved' ? 'approve' : 'reject'}`, {
            method: 'POST',
            data: { note: coachNote.value }
          })
        }
        uni.showToast({ title: action === 'approved' ? '审核通过' : '已退回', icon: 'success' })
        setTimeout(() => uni.navigateBack(), 800)
      } catch (e: any) {
        uni.showToast({ title: '操作失败', icon: 'none' })
      }
    }
  })
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

onMounted(() => { loadData() })
</script>

<style scoped>
.review-page { min-height: 100vh; background: #F5F6FA; }
.review-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #9B59B6 0%, #8E44AD 100%); color: #fff; }
.review-nav-back { font-size: 40rpx; padding: 16rpx; }
.review-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }

.review-loading { text-align: center; padding: 200rpx 0; color: #8E99A4; font-size: 28rpx; }
.review-content { height: calc(100vh - 180rpx); padding: 24rpx; }

.review-student { display: flex; align-items: center; gap: 16rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 16rpx; }
.review-avatar { width: 80rpx; height: 80rpx; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 34rpx; font-weight: 600; }
.review-student-info { flex: 1; }
.review-student-name { display: block; font-size: 32rpx; font-weight: 600; color: #2C3E50; }
.review-student-meta { display: block; font-size: 24rpx; color: #8E99A4; margin-top: 4rpx; }
.review-status { padding: 8rpx 20rpx; border-radius: 8rpx; color: #fff; font-size: 24rpx; }

.review-section { background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 16rpx; }
.review-section-title { display: block; font-size: 30rpx; font-weight: 600; color: #2C3E50; margin-bottom: 20rpx; }

.review-big5 { }
.big5-item { display: flex; align-items: center; gap: 12rpx; margin-bottom: 16rpx; }
.big5-label { width: 100rpx; font-size: 24rpx; color: #5B6B7F; text-align: right; }
.big5-bar-bg { flex: 1; height: 20rpx; background: #F0F0F0; border-radius: 10rpx; overflow: hidden; }
.big5-bar-fill { height: 100%; border-radius: 10rpx; transition: width 0.6s; }
.big5-value { width: 60rpx; font-size: 24rpx; color: #2C3E50; font-weight: 600; }

.review-tags { display: flex; flex-wrap: wrap; gap: 12rpx; }
.review-tag { padding: 8rpx 20rpx; border-radius: 20rpx; color: #fff; font-size: 24rpx; }

.ttm-timeline { display: flex; align-items: flex-start; gap: 0; padding: 16rpx 0; }
.ttm-stage { flex: 1; text-align: center; position: relative; }
.ttm-stage::before { content: ''; position: absolute; top: 14rpx; left: 0; right: 0; height: 4rpx; background: #E0E0E0; z-index: 0; }
.ttm-stage:first-child::before { left: 50%; }
.ttm-stage:last-child::before { right: 50%; }
.ttm-dot { width: 28rpx; height: 28rpx; border-radius: 50%; background: #E0E0E0; margin: 0 auto 8rpx; position: relative; z-index: 1; }
.ttm-stage--done .ttm-dot { background: #27AE60; }
.ttm-stage--done::before { background: #27AE60; }
.ttm-stage--active .ttm-dot { background: #9B59B6; width: 36rpx; height: 36rpx; margin-top: -4rpx; box-shadow: 0 0 0 8rpx rgba(155,89,182,0.2); }
.ttm-label { font-size: 20rpx; color: #8E99A4; }
.ttm-stage--active .ttm-label { color: #9B59B6; font-weight: 600; }
.ttm-stage--done .ttm-label { color: #27AE60; }

.capacity-list { }
.capacity-item { display: flex; align-items: center; gap: 12rpx; margin-bottom: 12rpx; }
.capacity-name { width: 120rpx; font-size: 24rpx; color: #5B6B7F; }
.capacity-bar-bg { flex: 1; height: 16rpx; background: #F0F0F0; border-radius: 8rpx; overflow: hidden; }
.capacity-bar-fill { height: 100%; background: linear-gradient(90deg, #3498DB, #2ECC71); border-radius: 8rpx; }
.capacity-score { width: 80rpx; font-size: 22rpx; color: #8E99A4; text-align: right; }

.ai-suggestion { display: flex; gap: 12rpx; margin-bottom: 16rpx; }
.ai-suggestion-num { width: 40rpx; height: 40rpx; border-radius: 50%; background: #9B59B6; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 22rpx; flex-shrink: 0; }
.ai-suggestion-text { flex: 1; font-size: 26rpx; color: #5B6B7F; line-height: 1.6; }

.review-note-input { width: 100%; height: 160rpx; padding: 16rpx; background: #F5F6FA; border-radius: 12rpx; font-size: 26rpx; line-height: 1.6; }
.review-note-count { display: block; text-align: right; font-size: 22rpx; color: #8E99A4; margin-top: 8rpx; }

.review-actions { display: flex; gap: 16rpx; padding: 24rpx 0 48rpx; }
.review-btn { flex: 1; text-align: center; padding: 24rpx 0; border-radius: 16rpx; font-size: 30rpx; font-weight: 600; }
.review-btn-reject { background: #FFF0ED; color: #E74C3C; }
.review-btn-approve { background: #9B59B6; color: #fff; }
.review-completed-tag { flex: 1; text-align: center; padding: 24rpx; background: #E8F8F0; color: #27AE60; border-radius: 16rpx; font-size: 28rpx; font-weight: 500; }
</style>