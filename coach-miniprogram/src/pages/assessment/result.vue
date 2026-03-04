<template>
  <view class="result-page">
    <view class="result-navbar">
      <view class="result-nav-back" @tap="goBack">←</view>
      <text class="result-nav-title">评估结果</text>
      <view class="result-nav-share" @tap="shareResult">分享</view>
    </view>

    <scroll-view scroll-y class="result-content" v-if="!loading">
      <!-- 总分概览 -->
      <view class="result-header">
        <view class="result-score-ring">
          <text class="result-score-num">{{ totalScore }}</text>
          <text class="result-score-label">综合评分</text>
        </view>
        <view class="result-header-info">
          <text class="result-header-title">行为健康画像</text>
          <text class="result-header-date">{{ formatDate(data.completed_at) }}</text>
          <text class="result-header-scales">{{ data.scale_names || '综合评估' }}</text>
        </view>
      </view>

      <!-- 大五人格 -->
      <view class="result-section" v-if="big5Data.length">
        <text class="result-section-title">🧠 人格特质 · 大五人格</text>
        <view class="result-big5">
          <view class="big5-row" v-for="item in big5Data" :key="item.name">
            <text class="big5-name">{{ item.name }}</text>
            <view class="big5-bar-track">
              <view class="big5-bar-fill" :style="{ width: item.percent + '%', background: item.color }"></view>
            </view>
            <text class="big5-score">{{ item.score }}<text class="big5-max">/7</text></text>
          </view>
        </view>
        <text class="result-summary" v-if="big5Summary">{{ big5Summary }}</text>
      </view>

      <!-- BPT6 行为类型 -->
      <view class="result-section" v-if="bptTags.length">
        <text class="result-section-title">🏷️ 行为类型标签</text>
        <view class="result-bpt-tags">
          <view class="bpt-tag" v-for="(tag, i) in bptTags" :key="i" :style="{ background: bptColors[i % bptColors.length] }">
            {{ tag }}
          </view>
        </view>
      </view>

      <!-- TTM 阶段 -->
      <view class="result-section" v-if="ttmStage">
        <text class="result-section-title">📈 行为改变阶段</text>
        <view class="result-ttm">
          <view
            v-for="(stage, i) in ttmStages" :key="i"
            class="ttm-step" :class="{ 'ttm-step--done': i < ttmIndex, 'ttm-step--current': i === ttmIndex }"
          >
            <view class="ttm-step-dot">
              <text v-if="i < ttmIndex">✓</text>
              <text v-else-if="i === ttmIndex">●</text>
              <text v-else>○</text>
            </view>
            <view class="ttm-step-info">
              <text class="ttm-step-name">{{ stage.name }}</text>
              <text class="ttm-step-desc">{{ stage.desc }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 待审核提示横幅 -->
      <view class="result-pending-notice" v-if="data.status === 'completed' && !data.pushed_at">
        <text class="result-pending-icon">⏳</text>
        <view class="result-pending-body">
          <text class="result-pending-title">评估已提交，等待教练审核</text>
          <text class="result-pending-desc">教练将在3个工作日内完成审核，届时您将收到通知</text>
        </view>
      </view>

      <!-- AI 行为处方预览 -->
      <view class="result-section">
        <text class="result-section-title">🤖 AI 行为处方建议</text>
        <view v-if="prescriptions.length" class="result-rx-list">
          <view class="result-rx-card" v-for="(rx, i) in prescriptions" :key="i">
            <text class="result-rx-num">{{ i + 1 }}</text>
            <view class="result-rx-body">
              <text class="result-rx-title">{{ rx.title || rx }}</text>
              <text class="result-rx-desc" v-if="rx.description">{{ rx.description }}</text>
            </view>
          </view>
        </view>
        <view v-else class="result-rx-placeholder">
          <text>AI处方将在教练审核后生成</text>
        </view>
      </view>

      <!-- 操作按钮 -->
      <view class="result-footer">
        <view class="result-btn result-btn-detail" @tap="viewFullReport">查看完整报告</view>
        <view class="result-btn result-btn-share" @tap="shareToCoach">分享给教练</view>
      </view>
    </scroll-view>

    <view v-if="loading" class="result-loading">
      <text>加载评估结果...</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const loading = ref(true)
const data = ref<any>({})

const ttmStages = [
  { name: '前意向期', desc: '尚未意识到需要改变' },
  { name: '意向期', desc: '开始考虑改变的可能' },
  { name: '准备期', desc: '制定改变计划' },
  { name: '行动期', desc: '正在积极改变行为' },
  { name: '维持期', desc: '保持健康行为6个月以上' },
  { name: '巩固期', desc: '行为已成为习惯' },
]

const bptColors = ['#3498DB', '#E67E22', '#27AE60', '#9B59B6', '#E74C3C', '#1ABC9C']

const totalScore = computed(() => data.value.total_score || data.value.score || '—')

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

const big5Summary = computed(() => {
  if (!big5Data.value.length) return ''
  const top = [...big5Data.value].sort((a, b) => b.score - a.score).slice(0, 2)
  return `您在${top.map(d => d.name).join('和')}方面表现突出`
})

const bptTags = computed(() => {
  const r = data.value.bpt6 || data.value.behavior_types || data.value.results?.bpt6
  if (Array.isArray(r)) return r.slice(0, 6)
  if (r && typeof r === 'object') return Object.keys(r).slice(0, 6)
  return []
})

const ttmStage = computed(() => data.value.ttm_stage || data.value.ttm || data.value.results?.ttm || '')
const ttmIndex = computed(() => {
  const s = ttmStage.value
  if (!s) return -1
  const map: Record<string, number> = { precontemplation: 0, contemplation: 1, preparation: 2, action: 3, maintenance: 4, termination: 5 }
  return map[s] ?? ttmStages.findIndex(st => s.includes(st.name)) ?? -1
})

const prescriptions = computed(() => {
  const rx = data.value.prescriptions || data.value.suggestions || data.value.results?.prescriptions
  if (Array.isArray(rx)) return rx.slice(0, 5)
  if (typeof rx === 'string') return rx.split('\n').filter(Boolean)
  return []
})

function formatDate(d: string): string { return d ? d.slice(0, 10) : '-' }

async function loadData() {
  loading.value = true
  const page = getCurrentPages().slice(-1)[0] as any
  const id = page?.options?.id

  // /assessment-assignments/{id}/result 是学员可用的真实端点，优先调用
  const endpoints = id ? [
    `/api/v1/assessment-assignments/${id}/result`,
    `/api/v1/assessment/results/${id}`,
    `/api/v1/assessment/${id}`,
  ] : ['/api/v1/assessment/profile/me', '/api/v1/assessment/user/latest']

  for (const ep of endpoints) {
    try {
      const res = await http<any>(ep)
      // 将嵌套的 profile_summary 字段展开，兼容旧格式
      const raw: any = res.result || res.profile || res || {}
      data.value = {
        ...raw,
        ...(raw.profile_summary || {}),
        // TTM 阶段：优先 stage_decision.to_stage，其次 profile_summary.current_stage
        ttm_stage: raw.stage_decision?.to_stage || raw.ttm_stage || raw.profile_summary?.current_stage || '',
        // 保留原始字段（供模板使用）
        status: raw.status,
        pushed_at: raw.pushed_at,
        completed_at: raw.completed_at,
      }
      break
    } catch { continue }
  }
  loading.value = false
}

function viewFullReport() {
  uni.showToast({ title: '完整报告生成中...', icon: 'none' })
}

async function shareToCoach() {
  const page = getCurrentPages().slice(-1)[0] as any
  let assignmentId = data.value.assignment_id || page?.options?.id

  // 无 id 时从 my-pending 拿最近一条
  if (!assignmentId) {
    try {
      const res = await http<any>('/api/v1/assessment-assignments/my-pending')
      const items = res.assignments || res.items || (Array.isArray(res) ? res : [])
      assignmentId = items[0]?.id
    } catch (e) { console.warn('[assessment/result] shareToCoach fetch:', e) }
  }

  if (!assignmentId) {
    uni.showToast({ title: '暂无可分享的评估', icon: 'none' })
    return
  }
  try {
    await http(`/api/v1/assessment-assignments/${assignmentId}/notify-coach`, { method: 'POST' })
    uni.showToast({ title: '已通知教练查看', icon: 'success' })
  } catch (e) {
    console.warn('[assessment/result] shareToCoach:', e)
    uni.showToast({ title: '通知失败，请重试', icon: 'none' })
  }
}

function shareResult() {
  uni.showToast({ title: '分享功能即将开放', icon: 'none' })
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

onMounted(() => { loadData() })
</script>

<style scoped>
.result-page { min-height: 100vh; background: #F5F6FA; }
.result-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #9B59B6 0%, #8E44AD 100%); color: #fff; }
.result-nav-back { font-size: 40rpx; padding: 16rpx; }
.result-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.result-nav-share { font-size: 26rpx; padding: 8rpx 16rpx; background: rgba(255,255,255,0.2); border-radius: 8rpx; }

.result-loading { text-align: center; padding: 200rpx 0; color: #8E99A4; font-size: 28rpx; }
.result-content { height: calc(100vh - 180rpx); padding: 24rpx; }

.result-header { display: flex; align-items: center; gap: 24rpx; background: linear-gradient(135deg, #9B59B6 0%, #8E44AD 100%); border-radius: 20rpx; padding: 32rpx; color: #fff; margin-bottom: 16rpx; }
.result-score-ring { width: 120rpx; height: 120rpx; border-radius: 50%; border: 6rpx solid rgba(255,255,255,0.3); display: flex; flex-direction: column; align-items: center; justify-content: center; }
.result-score-num { font-size: 40rpx; font-weight: 700; }
.result-score-label { font-size: 18rpx; opacity: 0.8; }
.result-header-info { flex: 1; }
.result-header-title { display: block; font-size: 32rpx; font-weight: 600; }
.result-header-date { display: block; font-size: 24rpx; opacity: 0.8; margin-top: 4rpx; }
.result-header-scales { display: block; font-size: 22rpx; opacity: 0.7; margin-top: 4rpx; }

.result-section { background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 16rpx; }
.result-section-title { display: block; font-size: 30rpx; font-weight: 600; color: #2C3E50; margin-bottom: 20rpx; }

.big5-row { display: flex; align-items: center; gap: 12rpx; margin-bottom: 16rpx; }
.big5-name { width: 100rpx; font-size: 24rpx; color: #5B6B7F; text-align: right; }
.big5-bar-track { flex: 1; height: 24rpx; background: #F0F0F0; border-radius: 12rpx; overflow: hidden; }
.big5-bar-fill { height: 100%; border-radius: 12rpx; transition: width 0.8s ease; }
.big5-score { width: 80rpx; font-size: 26rpx; color: #2C3E50; font-weight: 600; }
.big5-max { font-size: 20rpx; color: #8E99A4; font-weight: 400; }

.result-summary { display: block; font-size: 24rpx; color: #5B6B7F; background: #F8F9FA; padding: 16rpx; border-radius: 12rpx; margin-top: 12rpx; line-height: 1.5; }

.result-bpt-tags { display: flex; flex-wrap: wrap; gap: 12rpx; }
.bpt-tag { padding: 12rpx 24rpx; border-radius: 24rpx; color: #fff; font-size: 26rpx; }

.result-ttm { }
.ttm-step { display: flex; align-items: flex-start; gap: 16rpx; padding: 16rpx 0; position: relative; }
.ttm-step::before { content: ''; position: absolute; left: 18rpx; top: 52rpx; bottom: -16rpx; width: 4rpx; background: #E0E0E0; }
.ttm-step:last-child::before { display: none; }
.ttm-step--done::before { background: #27AE60; }
.ttm-step-dot { width: 40rpx; height: 40rpx; border-radius: 50%; background: #F0F0F0; display: flex; align-items: center; justify-content: center; font-size: 24rpx; color: #8E99A4; flex-shrink: 0; position: relative; z-index: 1; }
.ttm-step--done .ttm-step-dot { background: #27AE60; color: #fff; }
.ttm-step--current .ttm-step-dot { background: #9B59B6; color: #fff; width: 48rpx; height: 48rpx; margin: -4rpx; box-shadow: 0 0 0 8rpx rgba(155,89,182,0.15); }
.ttm-step-info { flex: 1; }
.ttm-step-name { display: block; font-size: 28rpx; color: #2C3E50; font-weight: 500; }
.ttm-step--current .ttm-step-name { color: #9B59B6; font-weight: 600; }
.ttm-step-desc { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }

.result-rx-list { }
.result-rx-card { display: flex; gap: 16rpx; margin-bottom: 16rpx; padding: 16rpx; background: #F8F9FA; border-radius: 12rpx; }
.result-rx-num { width: 40rpx; height: 40rpx; border-radius: 50%; background: #9B59B6; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 22rpx; flex-shrink: 0; }
.result-rx-body { flex: 1; }
.result-rx-title { display: block; font-size: 26rpx; color: #2C3E50; font-weight: 500; }
.result-rx-desc { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 6rpx; line-height: 1.5; }
.result-rx-placeholder { text-align: center; padding: 40rpx; color: #8E99A4; font-size: 26rpx; }

.result-pending-notice { display: flex; align-items: flex-start; gap: 16rpx; background: #FFF8E1; border-left: 6rpx solid #F59E0B; border-radius: 12rpx; padding: 24rpx; margin-bottom: 16rpx; }
.result-pending-icon { font-size: 44rpx; flex-shrink: 0; }
.result-pending-body { flex: 1; }
.result-pending-title { display: block; font-size: 28rpx; font-weight: 600; color: #92400E; margin-bottom: 4rpx; }
.result-pending-desc { display: block; font-size: 24rpx; color: #78350F; line-height: 1.5; }

.result-footer { display: flex; gap: 16rpx; padding: 24rpx 0 48rpx; }
.result-btn { flex: 1; text-align: center; padding: 24rpx 0; border-radius: 16rpx; font-size: 28rpx; font-weight: 600; }
.result-btn-detail { background: #9B59B6; color: #fff; }
.result-btn-share { background: #F0E6F6; color: #9B59B6; }
</style>