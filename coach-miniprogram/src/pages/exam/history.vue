<template>
  <view class="eh-page">
    <scroll-view scroll-y class="eh-scroll" refresher-enabled
      @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <view class="eh-list">
        <view v-for="item in records" :key="item.id" class="eh-card" @tap="goResult(item)">
          <view class="eh-card-top">
            <text class="eh-card-name">{{ item.exam_name || '认证考试' }}</text>
            <view class="eh-result-badge" :class="item.passed ? 'eh-badge--pass' : 'eh-badge--fail'">
              {{ item.passed ? '通过' : '未通过' }}
            </view>
          </view>
          <view class="eh-card-meta">
            <text class="eh-meta-item">得分: <text class="eh-meta-em">{{ item.score ?? '—' }}</text></text>
            <text class="eh-meta-item">满分: {{ item.total_score ?? 100 }}</text>
            <text class="eh-meta-item">{{ formatDate(item.created_at) }}</text>
          </view>
        </view>
      </view>

      <view v-if="records.length === 0 && !loading" class="eh-empty">
        <text class="eh-empty-icon">📜</text>
        <text class="eh-empty-text">还没有考试记录</text>
        <view class="eh-go-exam" @tap="goExams"><text>去参加考试</text></view>
      </view>

      <view style="height:80rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const records = ref<any[]>([])
const refreshing = ref(false)
const loading = ref(false)

async function loadData() {
  // /api/v1/certification/sessions/my 后端尚未开放，直接展示空状态
  loading.value = false
  records.value = []
}

function formatDate(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

function goResult(item: any) {
  uni.navigateTo({ url: '/pages/exam/result?session_id=' + item.id })
}
function goExams() { uni.navigateBack({ fail: () => uni.navigateTo({ url: '/pages/exam/index' }) }) }

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }
onMounted(() => { loadData() })
</script>

<style scoped>
.eh-page { min-height: 100vh; background: #F5F6FA; }
.eh-scroll { height: 100vh; }
.eh-list { padding: 16rpx 24rpx; }
.eh-card { background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 16rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.04); }
.eh-card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12rpx; }
.eh-card-name { font-size: 28rpx; font-weight: 600; color: #2C3E50; flex: 1; }
.eh-result-badge { font-size: 22rpx; padding: 4rpx 14rpx; border-radius: 10rpx; font-weight: 600; }
.eh-badge--pass { background: #E8F8F0; color: #2D8E69; }
.eh-badge--fail { background: #FDEDEC; color: #E74C3C; }
.eh-card-meta { display: flex; gap: 20rpx; flex-wrap: wrap; }
.eh-meta-item { font-size: 22rpx; color: #8E99A4; }
.eh-meta-em { color: #2D8E69; font-weight: 600; }
.eh-empty { text-align: center; padding: 120rpx 0; }
.eh-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.eh-empty-text { display: block; font-size: 26rpx; color: #8E99A4; margin-bottom: 32rpx; }
.eh-go-exam { display: inline-block; padding: 16rpx 48rpx; background: #2D8E69; color: #fff; border-radius: 16rpx; font-size: 28rpx; }
</style>
