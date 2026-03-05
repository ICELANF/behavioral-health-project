<template>
  <view class="exam-page">
    <view class="exam-header">
      <text class="exam-title">认证考试</text>
      <text class="exam-sub">通过考试获得教练认证资格</text>
    </view>

    <scroll-view scroll-y class="exam-scroll" refresher-enabled
      @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <view class="exam-list">
        <view v-for="exam in exams" :key="exam.id" class="exam-card" @tap="goIntro(exam)">
          <view class="exam-card-top">
            <view class="exam-level-badge">{{ exam.level || 'L1' }}</view>
            <text class="exam-card-title">{{ exam.exam_name || exam.title }}</text>
            <view class="exam-status-badge" :class="'exam-status--' + exam.status">
              {{ statusLabel(exam.status) }}
            </view>
          </view>
          <text class="exam-card-desc">{{ exam.description }}</text>
          <view class="exam-card-meta">
            <text class="exam-meta-item">📝 {{ exam.question_count || 0 }}题</text>
            <text class="exam-meta-item">⏱ {{ exam.duration_minutes }}分钟</text>
            <text class="exam-meta-item">🎯 {{ exam.passing_score }}分通过</text>
            <text class="exam-meta-item">🔁 {{ exam.max_attempts }}次机会</text>
          </view>
          <view class="exam-card-btn">
            <text>进入考试 →</text>
          </view>
        </view>
      </view>

      <view v-if="exams.length === 0 && !loading" class="exam-empty">
        <text class="exam-empty-icon">📝</text>
        <text class="exam-empty-text">暂无可用考试</text>
      </view>

      <view style="height:80rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const exams = ref<any[]>([])
const refreshing = ref(false)
const loading = ref(false)

async function loadData() {
  loading.value = true
  try {
    const res = await http<any>('/api/v1/certification/exams')
    exams.value = res?.items || (Array.isArray(res) ? res : [])
  } catch { exams.value = [] } finally { loading.value = false }
}

function statusLabel(s: string): string {
  return { published: '可参加', draft: '未开放', closed: '已关闭', active: '可参加' }[s] || s
}

function goIntro(exam: any) {
  uni.navigateTo({ url: '/exam/intro?id=' + exam.id })
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }
onMounted(() => { loadData() })
</script>

<style scoped>
.exam-page { min-height: 100vh; background: #F5F6FA; }

.exam-header {
  padding: 24rpx 32rpx;
  padding-top: calc(80rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%);
  color: #fff;
}
.exam-title { display: block; font-size: 38rpx; font-weight: 700; }
.exam-sub { display: block; font-size: 24rpx; opacity: 0.85; margin-top: 8rpx; }

.exam-scroll { height: calc(100vh - 200rpx); }

.exam-list { padding: 24rpx; }
.exam-card { background: #fff; border-radius: 20rpx; padding: 28rpx; margin-bottom: 20rpx; box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.06); }
.exam-card-top { display: flex; align-items: center; gap: 12rpx; margin-bottom: 16rpx; }
.exam-level-badge { background: #2D8E69; color: #fff; font-size: 22rpx; font-weight: 700; padding: 4rpx 14rpx; border-radius: 10rpx; }
.exam-card-title { flex: 1; font-size: 30rpx; font-weight: 700; color: #2C3E50; }
.exam-status-badge { font-size: 20rpx; padding: 4rpx 12rpx; border-radius: 8rpx; }
.exam-status--published, .exam-status--active { background: #E8F8F0; color: #2D8E69; }
.exam-status--draft { background: #F5F5F5; color: #8E99A4; }
.exam-status--closed { background: #FDEDEC; color: #E74C3C; }

.exam-card-desc { display: block; font-size: 24rpx; color: #5B6B7F; line-height: 1.6; margin-bottom: 20rpx; }
.exam-card-meta { display: flex; flex-wrap: wrap; gap: 16rpx; margin-bottom: 24rpx; }
.exam-meta-item { font-size: 22rpx; color: #8E99A4; }

.exam-card-btn { background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); border-radius: 12rpx; padding: 16rpx; text-align: center; color: #fff; font-size: 28rpx; font-weight: 600; }

.exam-empty { text-align: center; padding: 120rpx 0; }
.exam-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.exam-empty-text { font-size: 28rpx; color: #8E99A4; }
</style>
