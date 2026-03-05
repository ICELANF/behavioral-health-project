<template>
  <view class="pending-page">
    <view class="pending-navbar">
      <view class="pending-nav-back" @tap="goBack">←</view>
      <text class="pending-nav-title">我的评估</text>
    </view>

    <scroll-view scroll-y class="pending-content" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <!-- 待完成 -->
      <view class="pending-section" v-if="pendingList.length">
        <text class="pending-section-title">⏳ 待完成 ({{ pendingList.length }})</text>
        <view v-for="item in pendingList" :key="item.id" class="pending-card pending-card--active" @tap="goAssessment(item)">
          <view class="pending-card-icon">📝</view>
          <view class="pending-card-info">
            <text class="pending-card-title">{{ item.assessment_name || item.scale_names || '综合评估' }}</text>
            <text class="pending-card-meta">分配教练: {{ item.coach_name || '系统分配' }}</text>
            <text class="pending-card-meta" v-if="item.deadline">截止: {{ formatDate(item.deadline) }}</text>
          </view>
          <view class="pending-go-btn">开始 →</view>
        </view>
      </view>

      <!-- 进行中（有草稿） -->
      <view class="pending-section" v-if="inProgressList.length">
        <text class="pending-section-title">✍️ 进行中 ({{ inProgressList.length }})</text>
        <view v-for="item in inProgressList" :key="item.id" class="pending-card pending-card--progress" @tap="goAssessment(item)">
          <view class="pending-card-icon">📊</view>
          <view class="pending-card-info">
            <text class="pending-card-title">{{ item.assessment_name || item.scale_names || '综合评估' }}</text>
            <view class="pending-progress-bar">
              <view class="pending-progress-fill" :style="{ width: (item.progress || 30) + '%' }"></view>
            </view>
            <text class="pending-card-meta">已完成 {{ item.progress || 30 }}%</text>
          </view>
          <view class="pending-go-btn">继续 →</view>
        </view>
      </view>

      <!-- 已完成 -->
      <view class="pending-section" v-if="completedList.length">
        <text class="pending-section-title">✅ 已完成 ({{ completedList.length }})</text>
        <view v-for="item in completedList" :key="item.id" class="pending-card pending-card--done" @tap="goResult(item)">
          <view class="pending-card-icon">📈</view>
          <view class="pending-card-info">
            <text class="pending-card-title">{{ item.assessment_name || item.scale_names || '综合评估' }}</text>
            <text class="pending-card-meta">完成时间: {{ formatDate(item.completed_at) }}</text>
            <text class="pending-card-meta" v-if="item.score != null">得分: {{ item.score }}</text>
          </view>
          <view class="pending-go-btn pending-go-view">查看 →</view>
        </view>
      </view>

      <!-- 空状态 -->
      <view v-if="!loading && allItems.length === 0" class="pending-empty">
        <text class="pending-empty-icon">📋</text>
        <text class="pending-empty-text">暂无评估任务</text>
        <text class="pending-empty-hint">教练分配评估后会在这里显示</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const loading = ref(false)
const refreshing = ref(false)
const allItems = ref<any[]>([])

const pendingList = computed(() => allItems.value.filter(a => ['pending', 'assigned'].includes(a.status)))
const inProgressList = computed(() => allItems.value.filter(a => a.status === 'in_progress'))
const completedList = computed(() => allItems.value.filter(a => ['completed', 'submitted', 'reviewed'].includes(a.status)))

const SCALE_LABELS: Record<string, string> = {
  ttm7: 'TTM 行为阶段', big5: 'BIG5 大五人格', bpt6: 'BPT6 行为类型',
  capacity: '能力评估', spi: 'SPI 自我评估',
}

function formatDate(d: string): string { return d ? d.slice(0, 10) : '-' }

function normalizeItem(item: any, defaultStatus = 'pending'): any {
  // 补充 status（my-pending 接口不返回 status 字段）
  if (!item.status) item.status = defaultStatus
  // 补充 assessment_name（从 scales 结构格式化）
  if (!item.assessment_name) {
    const keys: string[] = Array.isArray(item.scales)
      ? item.scales
      : (item.scales?.scales || [])
    item.assessment_name = keys.map((k: string) => SCALE_LABELS[k] || k).join(' + ') || '综合评估'
  }
  return item
}

async function loadData() {
  loading.value = true
  try {
    // my-all 返回学员自己所有评估（含已完成），无权限问题
    const res = await http<any>('/api/v1/assessment-assignments/my-all')
    const list: any[] = res.assignments || res.items || (Array.isArray(res) ? res : [])
    allItems.value = list.map(item => normalizeItem(item))
  } catch {
    // 降级：仅加载待完成
    try {
      const res = await http<any>('/api/v1/assessment-assignments/my-pending')
      const list: any[] = res.assignments || res.items || (Array.isArray(res) ? res : [])
      allItems.value = list.map(item => normalizeItem(item, 'pending'))
    } catch { /* 无评估任务 */ }
  }
  loading.value = false
}

async function onRefresh() { refreshing.value = true; allItems.value = []; await loadData(); refreshing.value = false }

function goAssessment(item: any) {
  // 缓存 assignment 供 do.vue 使用（读取 scales 配置生成对应题目）
  try { uni.setStorageSync('assignment_' + item.id, JSON.stringify(item)) } catch (e) { /* ignore */ }
  uni.navigateTo({ url: '/assessment/do?id=' + item.id })
}

function goResult(item: any) {
  uni.navigateTo({ url: '/assessment/result?id=' + item.id })
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/home/index' })
}

onMounted(() => { loadData() })
</script>

<style scoped>
.pending-page { min-height: 100vh; background: #F5F6FA; }
.pending-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #9B59B6 0%, #8E44AD 100%); color: #fff; }
.pending-nav-back { font-size: 40rpx; padding: 16rpx; }
.pending-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }

.pending-content { height: calc(100vh - 180rpx); padding: 24rpx; }
.pending-section { margin-bottom: 24rpx; }
.pending-section-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; margin-bottom: 16rpx; }

.pending-card { display: flex; align-items: center; gap: 16rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 12rpx; }
.pending-card--active { border-left: 6rpx solid #E67E22; }
.pending-card--progress { border-left: 6rpx solid #3498DB; }
.pending-card--done { border-left: 6rpx solid #27AE60; opacity: 0.85; }

.pending-card-icon { font-size: 48rpx; }
.pending-card-info { flex: 1; }
.pending-card-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; margin-bottom: 6rpx; }
.pending-card-meta { display: block; font-size: 22rpx; color: #8E99A4; }

.pending-progress-bar { height: 8rpx; background: #F0F0F0; border-radius: 4rpx; margin: 8rpx 0; overflow: hidden; }
.pending-progress-fill { height: 100%; background: #3498DB; border-radius: 4rpx; }

.pending-go-btn { padding: 12rpx 24rpx; background: #9B59B6; color: #fff; border-radius: 8rpx; font-size: 24rpx; white-space: nowrap; }
.pending-go-view { background: #27AE60; }

.pending-empty { text-align: center; padding: 200rpx 0; }
.pending-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.pending-empty-text { display: block; font-size: 30rpx; color: #5B6B7F; margin-bottom: 8rpx; }
.pending-empty-hint { display: block; font-size: 24rpx; color: #8E99A4; }
</style>