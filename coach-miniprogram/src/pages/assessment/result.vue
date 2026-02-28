<template>
  <view class="ar-page">

    <!-- 顶部信息 -->
    <view class="ar-header">
      <text class="ar-header__title">评估报告</text>
      <text class="ar-header__sub">{{ result?.scale_name || '综合行为评估' }}</text>
      <text class="ar-header__time" v-if="result?.completed_at">完成于 {{ result.completed_at.slice(0, 16).replace('T', ' ') }}</text>
    </view>

    <scroll-view scroll-y class="ar-body">

      <!-- 大五人格 -->
      <view class="ar-card" v-if="result?.big5">
        <text class="ar-card__title">大五人格</text>
        <view class="ar-radar">
          <view class="ar-radar-item" v-for="dim in BIG5" :key="dim.key">
            <text class="ar-radar-item__label">{{ dim.label }}</text>
            <view class="ar-radar-item__bar">
              <view class="ar-radar-item__fill" :style="{ width: (result.big5[dim.key] || 0) + '%', background: dim.color }"></view>
            </view>
            <text class="ar-radar-item__val">{{ result.big5[dim.key] || 0 }}</text>
          </view>
        </view>
      </view>

      <!-- BPT6 行为类型 -->
      <view class="ar-card" v-if="result?.bpt6_tags?.length">
        <text class="ar-card__title">BPT6 行为类型</text>
        <view class="ar-tags">
          <view
            v-for="(tag, i) in result.bpt6_tags.slice(0, 6)"
            :key="i"
            class="ar-tag"
            :style="{ background: BPT_COLORS[i % BPT_COLORS.length] + '18', color: BPT_COLORS[i % BPT_COLORS.length] }"
          >
            <text>{{ tag }}</text>
          </view>
        </view>
      </view>

      <!-- TTM 行为改变阶段 -->
      <view class="ar-card" v-if="result?.ttm_stage">
        <text class="ar-card__title">行为改变阶段</text>
        <view class="ar-ttm">
          <view
            v-for="stage in TTM_STAGES"
            :key="stage.key"
            class="ar-ttm__item"
            :class="{ 'ar-ttm__item--active': result.ttm_stage === stage.key }"
          >
            <view class="ar-ttm__dot"></view>
            <text class="ar-ttm__label">{{ stage.label }}</text>
          </view>
          <view class="ar-ttm__line"></view>
        </view>
        <text class="ar-card__desc" v-if="result.ttm_description">{{ result.ttm_description }}</text>
      </view>

      <!-- 行为处方预览 -->
      <view class="ar-card" v-if="result?.prescriptions?.length">
        <text class="ar-card__title">行为处方预览</text>
        <view class="ar-rx-list">
          <view v-for="(rx, i) in result.prescriptions.slice(0, 3)" :key="i" class="ar-rx-item">
            <view class="ar-rx-num"><text>{{ i + 1 }}</text></view>
            <text class="ar-rx-text">{{ rx.summary || rx.content }}</text>
          </view>
        </view>
      </view>

    </scroll-view>

    <!-- 底部按钮 -->
    <view class="ar-footer safe-area-bottom">
      <view class="ar-footer__btn ar-footer__btn--outline" @tap="shareToCoach">
        <text>分享给教练</text>
      </view>
      <view class="ar-footer__btn ar-footer__btn--primary" @tap="viewFullRx">
        <text>查看完整处方</text>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { onLoad } from '@dcloudio/uni-app'
import { ref, onMounted } from 'vue'
import http from '@/api/request'

const BIG5 = [
  { key: 'openness',          label: '开放性', color: '#10b981' },
  { key: 'conscientiousness', label: '尽责性', color: '#3b82f6' },
  { key: 'extraversion',      label: '外向性', color: '#f59e0b' },
  { key: 'agreeableness',     label: '宜人性', color: '#8b5cf6' },
  { key: 'neuroticism',       label: '神经质', color: '#ef4444' },
]

const BPT_COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ec4899', '#ef4444']

const TTM_STAGES = [
  { key: 'precontemplation', label: '前意向' },
  { key: 'contemplation',    label: '意向' },
  { key: 'preparation',      label: '准备' },
  { key: 'action',           label: '行动' },
  { key: 'maintenance',      label: '维持' },
  { key: 'termination',      label: '终止' },
]

const assessmentId = ref(0)
const result       = ref<any>(null)

onLoad((query: any) => {
  assessmentId.value = Number(query?.id || query?.assignment_id || 0)
})

onMounted(async () => {
  if (assessmentId.value) await loadResult()
})

async function loadResult() {
  try {
    const res = await http.get<any>(`/v1/assessment/results/${assessmentId.value}`)
    result.value = res
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  }
}

function viewFullRx() {
  uni.navigateTo({ url: `/pages/learning/content-detail?id=${assessmentId.value}&tab=prescription` })
}

function shareToCoach() {
  uni.showModal({
    title: '分享给教练',
    content: '确认将本次评估结果分享给您的教练？',
    success: async (res) => {
      if (!res.confirm) return
      try {
        await http.post(`/v1/assessment/results/${assessmentId.value}/share`, {})
        uni.showToast({ title: '已分享', icon: 'success' })
      } catch {
        uni.showToast({ title: '分享失败', icon: 'none' })
      }
    },
  })
}
</script>

<style scoped>
.ar-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }

.ar-header { background: var(--surface); padding: 32rpx; text-align: center; }
.ar-header__title { font-size: 36rpx; font-weight: 800; color: var(--text-primary); display: block; }
.ar-header__sub { font-size: 26rpx; color: var(--bhp-primary-500); font-weight: 600; display: block; margin-top: 8rpx; }
.ar-header__time { font-size: 22rpx; color: var(--text-tertiary); display: block; margin-top: 6rpx; }

.ar-body { flex: 1; padding: 20rpx 32rpx 180rpx; }

.ar-card {
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 24rpx; margin-bottom: 20rpx; border: 1px solid var(--border-light);
}
.ar-card__title { font-size: 28rpx; font-weight: 700; color: var(--text-primary); display: block; margin-bottom: 16rpx; }
.ar-card__desc { font-size: 26rpx; color: var(--text-secondary); line-height: 1.6; display: block; margin-top: 16rpx; }

/* 大五人格 */
.ar-radar { display: flex; flex-direction: column; gap: 16rpx; }
.ar-radar-item { display: flex; align-items: center; gap: 12rpx; }
.ar-radar-item__label { width: 100rpx; font-size: 24rpx; color: var(--text-secondary); text-align: right; flex-shrink: 0; }
.ar-radar-item__bar { flex: 1; height: 20rpx; background: var(--bhp-gray-100); border-radius: var(--radius-full); overflow: hidden; }
.ar-radar-item__fill { height: 100%; border-radius: var(--radius-full); transition: width 0.5s; }
.ar-radar-item__val { width: 60rpx; font-size: 24rpx; font-weight: 700; color: var(--text-primary); }

/* BPT6 标签 */
.ar-tags { display: flex; flex-wrap: wrap; gap: 12rpx; }
.ar-tag { font-size: 24rpx; font-weight: 600; padding: 8rpx 20rpx; border-radius: var(--radius-full); }

/* TTM 时间线 */
.ar-ttm { display: flex; justify-content: space-between; position: relative; padding: 0 4rpx; }
.ar-ttm__item { display: flex; flex-direction: column; align-items: center; gap: 8rpx; z-index: 2; }
.ar-ttm__dot {
  width: 32rpx; height: 32rpx; border-radius: 50%;
  background: var(--bhp-gray-200); border: 2px solid var(--bhp-gray-300);
}
.ar-ttm__item--active .ar-ttm__dot {
  background: var(--bhp-primary-500); border-color: var(--bhp-primary-500);
  box-shadow: 0 0 0 4rpx rgba(16,185,129,0.25);
}
.ar-ttm__label { font-size: 18rpx; color: var(--text-tertiary); }
.ar-ttm__item--active .ar-ttm__label { color: var(--bhp-primary-500); font-weight: 700; }
.ar-ttm__line {
  position: absolute; top: 16rpx; left: 20rpx; right: 20rpx; height: 4rpx;
  background: var(--bhp-gray-200); z-index: 1;
}

/* 行为处方 */
.ar-rx-list { display: flex; flex-direction: column; gap: 12rpx; }
.ar-rx-item { display: flex; align-items: flex-start; gap: 12rpx; }
.ar-rx-num {
  width: 40rpx; height: 40rpx; border-radius: 50%;
  background: var(--bhp-primary-500); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 22rpx; font-weight: 700; flex-shrink: 0;
}
.ar-rx-text { font-size: 26rpx; color: var(--text-primary); line-height: 1.5; flex: 1; }

/* 底部 */
.ar-footer {
  position: fixed; bottom: 0; left: 0; right: 0;
  display: flex; gap: 16rpx; padding: 16rpx 32rpx;
  background: var(--surface); border-top: 1px solid var(--border-light);
}
.ar-footer__btn {
  flex: 1; height: 88rpx; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 28rpx; font-weight: 700; cursor: pointer;
}
.ar-footer__btn:active { opacity: 0.85; }
.ar-footer__btn--primary { background: var(--bhp-primary-500); color: #fff; }
.ar-footer__btn--outline { background: var(--surface); color: var(--bhp-primary-500); border: 2px solid var(--bhp-primary-500); }
</style>
