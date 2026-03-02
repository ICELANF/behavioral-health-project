<template>
  <view class="er-page">
    <view v-if="loading" class="er-loading"><text>加载中...</text></view>

    <scroll-view v-else scroll-y class="er-scroll">
      <!-- 结果卡 -->
      <view class="er-hero" :class="passed ? 'er-hero--pass' : 'er-hero--fail'">
        <text class="er-result-icon">{{ passed ? '🎉' : '😔' }}</text>
        <text class="er-result-text">{{ passed ? '恭喜通过!' : '未能通过' }}</text>
        <text class="er-score">{{ result.score ?? '—' }} 分</text>
        <text class="er-score-hint">满分 {{ result.total_score ?? 100 }} 分 · 通过线 {{ result.passing_score ?? 60 }} 分</text>
      </view>

      <!-- 详情 -->
      <view v-if="result.exam_name" class="er-detail">
        <view class="er-detail-row">
          <text class="er-detail-label">考试名称</text>
          <text class="er-detail-value">{{ result.exam_name }}</text>
        </view>
        <view class="er-detail-row">
          <text class="er-detail-label">答题数量</text>
          <text class="er-detail-value">{{ result.answered ?? '—' }} / {{ result.total_questions ?? '—' }}</text>
        </view>
        <view class="er-detail-row">
          <text class="er-detail-label">用时</text>
          <text class="er-detail-value">{{ result.time_spent_min ?? '—' }} 分钟</text>
        </view>
        <view class="er-detail-row">
          <text class="er-detail-label">考试时间</text>
          <text class="er-detail-value">{{ formatDate(result.finished_at) }}</text>
        </view>
      </view>

      <!-- 提示 (no result) -->
      <view v-if="!result.score && !loading" class="er-empty">
        <text class="er-empty-icon">📋</text>
        <text class="er-empty-text">暂无结果数据</text>
      </view>

      <!-- 操作 -->
      <view class="er-actions">
        <view class="er-action-btn" @tap="goBack"><text>返回考试列表</text></view>
        <view v-if="!passed" class="er-action-btn er-action-btn--retry" @tap="goRetry"><text>再次挑战</text></view>
      </view>

      <view style="height:80rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const BASE_URL = 'http://localhost:8000'
function getToken() { return uni.getStorageSync('access_token') || '' }

async function http<T = any>(url: string): Promise<T> {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url, method: 'GET',
      header: { 'Authorization': 'Bearer ' + getToken(), 'Content-Type': 'application/json' },
      success: (res: any) => {
        if (res.statusCode === 401) { uni.removeStorageSync('access_token'); uni.reLaunch({ url: '/pages/auth/login' }); reject(new Error('401')); return }
        res.statusCode < 300 ? resolve(res.data as T) : reject(new Error(`${res.statusCode}`))
      },
      fail: (e: any) => reject(e),
    })
  })
}

const result = ref<any>({})
const loading = ref(false)
let sessionId = 0

const passed = computed(() => {
  const score = result.value?.score ?? 0
  const pass = result.value?.passing_score ?? 60
  return score >= pass
})

onMounted(() => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1] as any
  sessionId = Number(page?.options?.session_id || 0)
  if (sessionId) loadData()
})

async function loadData() {
  loading.value = true
  try {
    result.value = await http<any>(`/api/v1/certification/sessions/${sessionId}/result`)
  } catch { result.value = {} } finally { loading.value = false }
}

function formatDate(iso: string): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

function goBack() { uni.navigateTo({ url: '/pages/exam/index' }) }
function goRetry() { uni.navigateBack({ delta: 2, fail: () => uni.navigateTo({ url: '/pages/exam/index' }) }) }
</script>

<style scoped>
.er-page { min-height: 100vh; background: #F5F6FA; }
.er-loading { display: flex; align-items: center; justify-content: center; height: 100vh; font-size: 28rpx; color: #8E99A4; }
.er-scroll { height: 100vh; }

.er-hero { text-align: center; padding: 80rpx 32rpx 48rpx; color: #fff; }
.er-hero--pass { background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); }
.er-hero--fail { background: linear-gradient(135deg, #E74C3C 0%, #C0392B 100%); }
.er-result-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.er-result-text { display: block; font-size: 40rpx; font-weight: 700; margin-bottom: 24rpx; }
.er-score { display: block; font-size: 80rpx; font-weight: 700; margin-bottom: 8rpx; }
.er-score-hint { display: block; font-size: 24rpx; opacity: 0.85; }

.er-detail { background: #fff; margin: 24rpx; border-radius: 16rpx; padding: 8rpx 24rpx; }
.er-detail-row { display: flex; justify-content: space-between; padding: 18rpx 0; border-bottom: 1rpx solid #F8F8F8; }
.er-detail-row:last-child { border-bottom: none; }
.er-detail-label { font-size: 26rpx; color: #8E99A4; }
.er-detail-value { font-size: 26rpx; color: #2C3E50; font-weight: 600; }

.er-empty { text-align: center; padding: 80rpx; }
.er-empty-icon { display: block; font-size: 64rpx; margin-bottom: 16rpx; }
.er-empty-text { font-size: 26rpx; color: #8E99A4; }

.er-actions { padding: 0 24rpx; display: flex; gap: 16rpx; }
.er-action-btn { flex: 1; background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); border-radius: 16rpx; padding: 20rpx; text-align: center; color: #fff; font-size: 28rpx; font-weight: 600; }
.er-action-btn--retry { background: #fff; color: #E74C3C; border: 2rpx solid #E74C3C; }
</style>
