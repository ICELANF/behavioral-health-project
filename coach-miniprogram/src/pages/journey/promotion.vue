<template>
  <view class="prom-page">
    <scroll-view scroll-y class="prom-scroll">
      <view class="prom-hero">
        <text class="prom-hero-icon">🚀</text>
        <text class="prom-hero-title">申请晋级</text>
        <text class="prom-hero-sub">当前：{{ levelName(currentLevel) }} → 目标：{{ levelName(targetLevel) }}</text>
      </view>

      <view class="prom-form">
        <view class="prom-field">
          <text class="prom-label">目标级别</text>
          <view class="prom-select-row">
            <view v-for="level in availableLevels" :key="level.key"
              class="prom-level-chip" :class="{ 'prom-level-chip--active': targetLevel === level.key }"
              @tap="targetLevel = level.key">
              {{ level.icon }} {{ level.name }}
            </view>
          </view>
        </view>

        <view class="prom-field">
          <text class="prom-label">申请理由 *</text>
          <textarea class="prom-textarea" v-model="reason"
            placeholder="请描述您的成长经历和晋级理由（至少20字）..."
            :maxlength="500" />
          <text class="prom-char-count">{{ reason.length }}/500</text>
        </view>

        <view class="prom-field">
          <text class="prom-label">支持材料（可选）</text>
          <text class="prom-hint">如认证证书、学习成果截图等</text>
          <view class="prom-upload-placeholder">
            <text>📎 上传材料功能即将上线</text>
          </view>
        </view>
      </view>

      <view class="prom-submit-btn" :class="{ 'prom-submit-btn--disabled': !canSubmit }" @tap="submitPromotion">
        <text>{{ submitting ? '提交中...' : '提交申请' }}</text>
      </view>

      <view style="height:80rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const levelOrder = ['observer', 'grower', 'sharer', 'guide', 'master']
const levels = [
  { key: 'observer',  name: '观察者', icon: '👁' },
  { key: 'grower',    name: '成长者', icon: '🌱' },
  { key: 'sharer',    name: '分享者', icon: '🤝' },
  { key: 'guide',     name: '向导者', icon: '🧭' },
  { key: 'master',    name: '大师',   icon: '⭐' },
]

const currentLevel = ref('observer')
const targetLevel = ref('grower')
const reason = ref('')
const submitting = ref(false)

const availableLevels = computed(() => {
  const idx = levelOrder.indexOf(currentLevel.value)
  return levels.filter(l => levelOrder.indexOf(l.key) > idx)
})
const canSubmit = computed(() => reason.value.length >= 20 && !submitting.value)

function levelName(k: string) { return levels.find(l => l.key === k)?.name || k }

async function loadOverview() {
  try {
    const res = await http<any>('/api/v1/journey/overview')
    currentLevel.value = res?.current_level || 'observer'
    const nextIdx = levelOrder.indexOf(currentLevel.value) + 1
    targetLevel.value = levelOrder[nextIdx] || 'grower'
  } catch (e) { console.warn('[journey/promotion] overview:', e) }
}

async function submitPromotion() {
  if (!canSubmit.value) return
  submitting.value = true
  try {
    await http('/api/v1/journey/promotion/apply', {
      method: 'POST',
      data: { target_level: targetLevel.value, reason: reason.value }
    })
    uni.showToast({ title: '申请已提交', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 1500)
  } catch {
    uni.showToast({ title: '提交失败，请重试', icon: 'none' })
  } finally { submitting.value = false }
}

onMounted(() => { loadOverview() })
</script>

<style scoped>
.prom-page { min-height: 100vh; background: #F5F6FA; }
.prom-scroll { height: 100vh; }

.prom-hero {
  display: flex; flex-direction: column; align-items: center; padding: 48rpx 32rpx;
  background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); color: #fff;
  padding-top: calc(48rpx + env(safe-area-inset-top));
}
.prom-hero-icon { font-size: 64rpx; margin-bottom: 16rpx; }
.prom-hero-title { font-size: 40rpx; font-weight: 700; margin-bottom: 12rpx; }
.prom-hero-sub { font-size: 24rpx; opacity: 0.85; }

.prom-form { background: #fff; margin: 24rpx; border-radius: 16rpx; padding: 24rpx; }
.prom-field { margin-bottom: 28rpx; }
.prom-label { display: block; font-size: 26rpx; font-weight: 600; color: #2C3E50; margin-bottom: 12rpx; }
.prom-hint { display: block; font-size: 22rpx; color: #8E99A4; margin-bottom: 10rpx; }
.prom-select-row { display: flex; flex-wrap: wrap; gap: 12rpx; }
.prom-level-chip { padding: 10rpx 20rpx; border-radius: 20rpx; font-size: 24rpx; background: #F5F6FA; color: #5B6B7F; border: 1rpx solid #E0E0E0; }
.prom-level-chip--active { background: #2D8E69; color: #fff; border-color: #2D8E69; }
.prom-textarea { width: 100%; min-height: 200rpx; background: #F8F9FA; border-radius: 12rpx; padding: 16rpx; font-size: 26rpx; color: #2C3E50; border: 1rpx solid #E0E0E0; box-sizing: border-box; }
.prom-char-count { display: block; text-align: right; font-size: 20rpx; color: #BDC3C7; margin-top: 8rpx; }
.prom-upload-placeholder { background: #F8F9FA; border: 2rpx dashed #D0D5DD; border-radius: 12rpx; padding: 32rpx; text-align: center; font-size: 24rpx; color: #8E99A4; }

.prom-submit-btn { margin: 0 24rpx; background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); border-radius: 16rpx; padding: 24rpx; text-align: center; color: #fff; font-size: 32rpx; font-weight: 700; }
.prom-submit-btn--disabled { opacity: 0.5; }
</style>
