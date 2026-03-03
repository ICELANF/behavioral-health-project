<template>
  <view class="cr-page">
    <!-- 总学分卡 -->
    <view class="cr-hero">
      <text class="cr-total-num">{{ totalCredits }}</text>
      <text class="cr-total-label">累计学分</text>
    </view>

    <scroll-view scroll-y class="cr-scroll">
      <view v-if="items.length > 0" class="cr-list">
        <view class="cr-section-title">获得记录</view>
        <view v-for="item in items" :key="item.id" class="cr-item">
          <view class="cr-item-left">
            <text class="cr-item-icon">🏅</text>
          </view>
          <view class="cr-item-body">
            <text class="cr-item-title">{{ item.title || item.source || '学习积分' }}</text>
            <text class="cr-item-time">{{ formatTime(item.created_at) }}</text>
          </view>
          <view class="cr-item-right">
            <text class="cr-item-points">+{{ item.credits || item.points || 0 }}</text>
          </view>
        </view>
      </view>

      <view v-else class="cr-empty">
        <text class="cr-empty-icon">🏅</text>
        <text class="cr-empty-text">完成学习内容获得学分</text>
        <view class="cr-go-learn" @tap="goLearn">
          <text>去学习</text>
        </view>
      </view>

      <view style="height:80rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const totalCredits = ref(0)
const items = ref<any[]>([])

async function loadData() {
  try {
    const res = await http<any>('/api/v1/learning/credits')
    totalCredits.value = res?.total_credits ?? 0
    items.value = res?.items || []
  } catch { totalCredits.value = 0; items.value = [] }
}

function formatTime(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

function goLearn() { uni.navigateBack({ fail: () => uni.navigateTo({ url: '/pages/learning/index' }) }) }

onMounted(() => { loadData() })
</script>

<style scoped>
.cr-page { min-height: 100vh; background: #F5F6FA; }

.cr-hero {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 60rpx 32rpx;
  background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%);
  color: #fff;
}
.cr-total-num { font-size: 80rpx; font-weight: 700; }
.cr-total-label { font-size: 26rpx; opacity: 0.85; margin-top: 8rpx; }

.cr-scroll { height: calc(100vh - 300rpx); }

.cr-section-title { font-size: 26rpx; color: #8E99A4; padding: 24rpx 32rpx 12rpx; }
.cr-list { background: #fff; margin: 16rpx 24rpx; border-radius: 16rpx; }
.cr-item { display: flex; align-items: center; gap: 16rpx; padding: 20rpx 24rpx; border-bottom: 1rpx solid #F8F8F8; }
.cr-item:last-child { border-bottom: none; }
.cr-item-left { flex-shrink: 0; }
.cr-item-icon { font-size: 36rpx; }
.cr-item-body { flex: 1; }
.cr-item-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.cr-item-time { font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.cr-item-right { flex-shrink: 0; }
.cr-item-points { font-size: 32rpx; font-weight: 700; color: #2D8E69; }

.cr-empty { text-align: center; padding: 100rpx 0; }
.cr-empty-icon { display: block; font-size: 64rpx; margin-bottom: 16rpx; }
.cr-empty-text { display: block; font-size: 26rpx; color: #8E99A4; margin-bottom: 32rpx; }
.cr-go-learn { display: inline-block; padding: 16rpx 48rpx; background: #2D8E69; color: #fff; border-radius: 16rpx; font-size: 28rpx; }
</style>
