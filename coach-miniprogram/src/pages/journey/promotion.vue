<template>
  <view class="jp-page">
    <view class="jp-navbar safe-area-top">
      <view class="jp-navbar__back" @tap="goBack"><text class="jp-navbar__arrow">‹</text></view>
      <text class="jp-navbar__title">申请晋级</text>
      <view class="jp-navbar__placeholder"></view>
    </view>

    <scroll-view scroll-y class="jp-body">
      <template v-if="loading">
        <view class="bhp-skeleton" style="height: 300rpx; border-radius: var(--radius-lg);"></view>
      </template>
      <template v-else>
        <!-- 等级对比 -->
        <view class="jp-compare">
          <view class="jp-level jp-level--current">
            <text class="jp-level__label">当前等级</text>
            <text class="jp-level__name">{{ currentLevel }}</text>
          </view>
          <view class="jp-compare__arrow">
            <text>→</text>
          </view>
          <view class="jp-level jp-level--target">
            <text class="jp-level__label">目标等级</text>
            <text class="jp-level__name">{{ targetLevel }}</text>
          </view>
        </view>

        <!-- 晋级条件 -->
        <view class="jp-card">
          <text class="jp-card__title">晋级条件</text>
          <view class="jp-conditions">
            <view v-for="(cond, idx) in conditions" :key="idx" class="jp-cond">
              <text class="jp-cond__icon">{{ cond.met ? '✅' : '❌' }}</text>
              <view class="jp-cond__body">
                <text class="jp-cond__name">{{ cond.name }}</text>
                <text class="jp-cond__detail">{{ cond.current }} / {{ cond.required }}</text>
              </view>
            </view>
          </view>
        </view>

        <!-- 提交按钮 -->
        <view class="jp-submit" :class="{ 'jp-submit--disabled': !allMet || submitting }" @tap="submitAdvance">
          <text>{{ submitting ? '提交中...' : allMet ? '提交晋级申请' : '条件未满足' }}</text>
        </view>
      </template>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import http from '@/api/request'

const loading      = ref(false)
const submitting   = ref(false)
const currentLevel = ref('')
const targetLevel  = ref('')
const conditions   = ref<{ name: string; met: boolean; current: string; required: string }[]>([])

const allMet = computed(() => conditions.value.length > 0 && conditions.value.every(c => c.met))

onMounted(() => loadProgress())

async function loadProgress() {
  loading.value = true
  try {
    const res = await http.get<any>('/v1/journey/stage/progress')
    currentLevel.value = res.current_stage || res.current_level || 'L1'
    targetLevel.value = res.next_stage || res.next_level || 'L2'
    const reqs = res.requirements || res.conditions || []
    conditions.value = reqs.map((r: any) => ({
      name: r.name || r.label,
      met: r.met ?? (r.current >= r.required),
      current: String(r.current ?? 0),
      required: String(r.required ?? 0),
    }))
  } catch {
    conditions.value = []
  } finally {
    loading.value = false
  }
}

async function submitAdvance() {
  if (!allMet.value || submitting.value) return
  submitting.value = true
  try {
    await http.post('/v1/journey/stage/advance', {})
    uni.showToast({ title: '申请已提交', icon: 'success' })
    setTimeout(() => goBack(), 1500)
  } catch (e: any) {
    uni.showToast({ title: e?.message || '提交失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

function goBack() { uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) }) }
</script>

<style scoped>
.jp-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }
.jp-navbar { display: flex; align-items: center; justify-content: space-between; padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light); }
.jp-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.jp-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.jp-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.jp-navbar__placeholder { width: 64rpx; }
.jp-body { flex: 1; padding: 20rpx 32rpx 40rpx; }

.jp-compare { display: flex; align-items: center; gap: 16rpx; margin-bottom: 24rpx; }
.jp-level { flex: 1; padding: 32rpx 16rpx; border-radius: var(--radius-lg); text-align: center; border: 1px solid var(--border-light); }
.jp-level--current { background: var(--surface); }
.jp-level--target { background: linear-gradient(135deg, var(--bhp-primary-50), var(--bhp-primary-100)); border-color: var(--bhp-primary-200); }
.jp-level__label { display: block; font-size: 22rpx; color: var(--text-secondary); margin-bottom: 8rpx; }
.jp-level__name { display: block; font-size: 36rpx; font-weight: 800; color: var(--text-primary); }
.jp-level--target .jp-level__name { color: var(--bhp-primary-600); }
.jp-compare__arrow { font-size: 40rpx; color: var(--bhp-primary-500); font-weight: 700; flex-shrink: 0; }

.jp-card { background: var(--surface); border-radius: var(--radius-lg); padding: 24rpx; border: 1px solid var(--border-light); margin-bottom: 24rpx; }
.jp-card__title { display: block; font-size: 28rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 20rpx; }
.jp-conditions { display: flex; flex-direction: column; gap: 16rpx; }
.jp-cond { display: flex; align-items: center; gap: 16rpx; }
.jp-cond__icon { font-size: 28rpx; flex-shrink: 0; }
.jp-cond__body { flex: 1; }
.jp-cond__name { display: block; font-size: 26rpx; font-weight: 600; color: var(--text-primary); }
.jp-cond__detail { display: block; font-size: 22rpx; color: var(--text-tertiary); }

.jp-submit {
  height: 96rpx; border-radius: var(--radius-lg); background: var(--bhp-primary-500);
  display: flex; align-items: center; justify-content: center;
  font-size: 30rpx; font-weight: 700; color: #fff; cursor: pointer;
}
.jp-submit:active { opacity: 0.85; }
.jp-submit--disabled { background: var(--bhp-gray-200); color: var(--text-tertiary); }
</style>
