<template>
  <view class="qr-page">
    <view class="qr-hero" :class="passed ? 'qr-hero--pass' : 'qr-hero--fail'">
      <text class="qr-icon">{{ passed ? '🎉' : '📝' }}</text>
      <text class="qr-result-text">{{ passed ? '测验通过' : '继续加油' }}</text>
      <text class="qr-score">{{ score }} / {{ total }}</text>
      <text class="qr-pct">正确率 {{ pct }}%</text>
    </view>

    <view class="qr-actions">
      <view class="qr-btn qr-btn--back" @tap="goBack"><text>返回内容</text></view>
      <view v-if="!passed" class="qr-btn qr-btn--retry" @tap="retry"><text>重新测验</text></view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const score = ref(0)
const total = ref(0)
let contentId = 0

const pct = computed(() => total.value > 0 ? Math.round(score.value / total.value * 100) : 0)
const passed = computed(() => pct.value >= 60)

onMounted(() => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1] as any
  score.value = Number(page?.options?.score || 0)
  total.value = Number(page?.options?.total || 0)
  contentId = Number(page?.options?.content_id || 0)
})

function goBack() { uni.navigateBack({ delta: 2 }) }
function retry() { uni.navigateBack() }
</script>

<style scoped>
.qr-page { min-height: 100vh; background: #F5F6FA; }
.qr-hero { display: flex; flex-direction: column; align-items: center; padding: 100rpx 32rpx 60rpx; color: #fff; }
.qr-hero--pass { background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); }
.qr-hero--fail { background: linear-gradient(135deg, #E67E22 0%, #E74C3C 100%); }
.qr-icon { font-size: 80rpx; margin-bottom: 16rpx; }
.qr-result-text { font-size: 40rpx; font-weight: 700; margin-bottom: 24rpx; }
.qr-score { font-size: 80rpx; font-weight: 700; margin-bottom: 8rpx; }
.qr-pct { font-size: 28rpx; opacity: 0.85; }
.qr-actions { display: flex; gap: 16rpx; padding: 40rpx 24rpx; }
.qr-btn { flex: 1; padding: 24rpx; border-radius: 16rpx; text-align: center; font-size: 30rpx; font-weight: 600; }
.qr-btn--back { background: #fff; color: #2D8E69; border: 2rpx solid #2D8E69; }
.qr-btn--retry { background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); color: #fff; }
</style>
