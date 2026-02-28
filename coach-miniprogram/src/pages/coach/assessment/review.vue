<template>
  <view class="ar-page">
    <view class="ar-navbar safe-area-top">
      <view class="ar-navbar__back" @tap="goBack"><text class="ar-navbar__arrow">‹</text></view>
      <text class="ar-navbar__title">评估审核</text>
      <view class="ar-navbar__placeholder"></view>
    </view>

    <scroll-view scroll-y class="ar-body">
      <template v-if="loading">
        <view class="bhp-skeleton" style="height: 400rpx; border-radius: var(--radius-lg);"></view>
      </template>
      <template v-else-if="result">

        <!-- 学员信息 -->
        <view class="ar-student">
          <image class="ar-student__avatar" :src="result.student?.avatar_url || '/static/default-avatar.png'" mode="aspectFill" />
          <view class="ar-student__info">
            <text class="ar-student__name">{{ result.student?.full_name || result.student?.username || '学员' }}</text>
            <text class="ar-student__scales">{{ result.scales?.join(' + ') || '综合评估' }}</text>
          </view>
        </view>

        <!-- 大五人格 -->
        <view class="ar-card" v-if="result.big_five">
          <text class="ar-card__title">大五人格画像</text>
          <view class="ar-bars">
            <view v-for="(val, key) in BIG_FIVE_MAP" :key="key" class="ar-bar-row">
              <text class="ar-bar-row__label">{{ val }}</text>
              <view class="ar-bar-row__track">
                <view class="ar-bar-row__fill" :style="{ width: (result.big_five[key] || 0) + '%', background: BAR_COLORS[key] || '#3b82f6' }"></view>
              </view>
              <text class="ar-bar-row__val">{{ result.big_five[key] || 0 }}</text>
            </view>
          </view>
        </view>

        <!-- BPT6 标签 -->
        <view class="ar-card" v-if="result.bpt6_tags?.length">
          <text class="ar-card__title">BPT6 行为标签</text>
          <view class="ar-tags">
            <view v-for="tag in result.bpt6_tags" :key="tag" class="ar-tag">
              <text>{{ tag }}</text>
            </view>
          </view>
        </view>

        <!-- TTM 阶段 -->
        <view class="ar-card" v-if="result.ttm_stage">
          <text class="ar-card__title">TTM 行为阶段</text>
          <view class="ar-ttm">
            <view v-for="stage in TTM_STAGES" :key="stage.key" class="ar-ttm-step" :class="{ 'ar-ttm-step--active': result.ttm_stage === stage.key }">
              <text class="ar-ttm-step__name">{{ stage.label }}</text>
            </view>
          </view>
        </view>

        <!-- 教练备注 -->
        <view class="ar-card">
          <text class="ar-card__title">教练备注</text>
          <textarea class="ar-note" v-model="reviewNote" placeholder="输入审核备注..." />
        </view>

      </template>
    </scroll-view>

    <!-- 底部按钮 -->
    <view class="ar-footer safe-area-bottom" v-if="result">
      <view class="ar-footer__btn ar-footer__btn--reject" @tap="handleReject">
        <text>退回修改</text>
      </view>
      <view class="ar-footer__btn ar-footer__btn--approve" @tap="handleApprove">
        <text>审核通过</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/api/request'

const BIG_FIVE_MAP: Record<string, string> = {
  openness: '开放性', conscientiousness: '责任心',
  extraversion: '外向性', agreeableness: '宜人性', neuroticism: '神经质',
}
const BAR_COLORS: Record<string, string> = {
  openness: '#8b5cf6', conscientiousness: '#10b981',
  extraversion: '#f59e0b', agreeableness: '#3b82f6', neuroticism: '#ef4444',
}
const TTM_STAGES = [
  { key: 'precontemplation', label: '前意向' },
  { key: 'contemplation', label: '意向' },
  { key: 'preparation', label: '准备' },
  { key: 'action', label: '行动' },
  { key: 'maintenance', label: '维持' },
]

const result     = ref<any>(null)
const reviewNote = ref('')
const loading    = ref(false)
const assignId   = ref(0)

onMounted(() => {
  const pages = getCurrentPages()
  const pg = pages[pages.length - 1] as any
  assignId.value = Number(pg.$page?.options?.id || pg.options?.id || 0)
  if (assignId.value) loadResult()
})

async function loadResult() {
  loading.value = true
  try {
    result.value = await http.get<any>(`/v1/assessment-assignments/${assignId.value}/result`)
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function handleApprove() {
  try {
    // 逐条审核 review_items，全部通过后推送
    const items = result.value?.review_items || []
    for (const item of items) {
      await http.put(`/v1/assessment-assignments/review-items/${item.id}`, {
        status: 'approved',
        coach_note: reviewNote.value,
      })
    }
    // 推送结果给学员
    await http.post(`/v1/assessment-assignments/${assignId.value}/push`, {})
    uni.showToast({ title: '已通过并推送', icon: 'success' })
    setTimeout(() => goBack(), 1000)
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
  }
}

async function handleReject() {
  if (!reviewNote.value.trim()) {
    uni.showToast({ title: '请填写退回原因', icon: 'none' })
    return
  }
  try {
    const items = result.value?.review_items || []
    for (const item of items) {
      await http.put(`/v1/assessment-assignments/review-items/${item.id}`, {
        status: 'rejected',
        coach_note: reviewNote.value,
      })
    }
    uni.showToast({ title: '已退回', icon: 'none' })
    setTimeout(() => goBack(), 1000)
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
  }
}

function goBack() { uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) }) }
</script>

<style scoped>
.ar-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }
.ar-navbar { display: flex; align-items: center; justify-content: space-between; padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light); }
.ar-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.ar-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.ar-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.ar-navbar__placeholder { width: 64rpx; }
.ar-body { flex: 1; padding: 20rpx 32rpx 160rpx; }

.ar-student {
  display: flex; align-items: center; gap: 16rpx;
  background: var(--surface); border-radius: var(--radius-lg); padding: 24rpx; margin-bottom: 20rpx; border: 1px solid var(--border-light);
}
.ar-student__avatar { width: 80rpx; height: 80rpx; border-radius: 50%; flex-shrink: 0; background: var(--bhp-gray-100); }
.ar-student__info { flex: 1; }
.ar-student__name { display: block; font-size: 28rpx; font-weight: 700; color: var(--text-primary); }
.ar-student__scales { display: block; font-size: 22rpx; color: var(--text-secondary); margin-top: 4rpx; }

.ar-card { background: var(--surface); border-radius: var(--radius-lg); padding: 24rpx; margin-bottom: 20rpx; border: 1px solid var(--border-light); }
.ar-card__title { display: block; font-size: 28rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 20rpx; }

.ar-bars { display: flex; flex-direction: column; gap: 16rpx; }
.ar-bar-row { display: flex; align-items: center; gap: 12rpx; }
.ar-bar-row__label { font-size: 22rpx; color: var(--text-secondary); width: 80rpx; flex-shrink: 0; }
.ar-bar-row__track { flex: 1; height: 20rpx; background: var(--bhp-gray-100); border-radius: var(--radius-full); overflow: hidden; }
.ar-bar-row__fill { height: 100%; border-radius: var(--radius-full); transition: width 0.4s; }
.ar-bar-row__val { font-size: 22rpx; font-weight: 700; color: var(--text-primary); width: 48rpx; text-align: right; }

.ar-tags { display: flex; flex-wrap: wrap; gap: 12rpx; }
.ar-tag { padding: 8rpx 20rpx; border-radius: var(--radius-full); background: var(--bhp-primary-50); color: var(--bhp-primary-600); font-size: 22rpx; font-weight: 600; }

.ar-ttm { display: flex; gap: 8rpx; }
.ar-ttm-step {
  flex: 1; text-align: center; padding: 12rpx 4rpx; border-radius: var(--radius-md);
  background: var(--surface-secondary); font-size: 20rpx; color: var(--text-tertiary);
}
.ar-ttm-step--active { background: var(--bhp-primary-500); color: #fff; font-weight: 700; }
.ar-ttm-step__name { display: block; }

.ar-note {
  width: 100%; min-height: 160rpx; border: 1px solid var(--border-light); border-radius: var(--radius-md);
  padding: 16rpx; font-size: 26rpx; color: var(--text-primary); background: var(--surface-secondary);
}

.ar-footer {
  position: fixed; bottom: 0; left: 0; right: 0; display: flex; gap: 16rpx;
  padding: 16rpx 32rpx 24rpx; background: var(--surface); border-top: 1px solid var(--border-light);
}
.ar-footer__btn {
  flex: 1; height: 88rpx; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 28rpx; font-weight: 700; cursor: pointer;
}
.ar-footer__btn--reject { background: var(--surface-secondary); color: var(--text-secondary); border: 1px solid var(--border-light); }
.ar-footer__btn--approve { background: var(--bhp-primary-500); color: #fff; }
.ar-footer__btn:active { opacity: 0.85; }
</style>
