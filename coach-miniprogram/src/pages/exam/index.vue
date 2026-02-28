<template>
  <view class="ex-page">

    <view class="ex-navbar safe-area-top">
      <view class="ex-navbar__back" @tap="goBack"><text class="ex-navbar__arrow">‹</text></view>
      <text class="ex-navbar__title">认证考试</text>
      <view class="ex-navbar__placeholder"></view>
    </view>

    <!-- 考试记录摘要 -->
    <view class="ex-summary">
      <view class="ex-summary__item">
        <text class="ex-summary__val text-primary-color">{{ passedCount }}</text>
        <text class="ex-summary__lbl">已通过</text>
      </view>
      <view class="ex-summary__divider"></view>
      <view class="ex-summary__item">
        <text class="ex-summary__val">{{ totalCount }}</text>
        <text class="ex-summary__lbl">总考试</text>
      </view>
      <view class="ex-summary__divider"></view>
      <view class="ex-summary__item">
        <text class="ex-summary__val" :style="{ color: passRate ? '#10b981' : '' }">{{ passRate }}%</text>
        <text class="ex-summary__lbl">通过率</text>
      </view>
    </view>

    <scroll-view scroll-y class="ex-body">

      <text class="ex-section-title">可用考试</text>

      <template v-if="loading">
        <view class="bhp-skeleton" v-for="i in 3" :key="i" style="height: 180rpx; border-radius: var(--radius-lg); margin-bottom: 16rpx;"></view>
      </template>

      <view v-else-if="exams.length" class="ex-list">
        <view v-for="exam in exams" :key="exam.id" class="ex-card" @tap="goIntro(exam.id)">
          <view class="ex-card__header">
            <text class="ex-card__name">{{ exam.name || exam.title }}</text>
            <view class="ex-card__level" v-if="exam.required_level">
              <text>{{ exam.required_level }}</text>
            </view>
          </view>
          <view class="ex-card__info">
            <view class="ex-card__tag"><text>{{ exam.question_count || exam.total_questions || '?' }} 题</text></view>
            <view class="ex-card__tag"><text>{{ exam.time_limit_minutes || '?' }} 分钟</text></view>
            <view class="ex-card__tag"><text>{{ exam.pass_score || 60 }} 分通过</text></view>
          </view>
          <view class="ex-card__desc" v-if="exam.description">
            <text>{{ exam.description }}</text>
          </view>
          <view class="ex-card__action">
            <text class="ex-card__btn">进入考试 ›</text>
          </view>
        </view>
      </view>

      <view v-else class="ex-empty">
        <text class="ex-empty__icon">📝</text>
        <text class="ex-empty__text">暂无可用考试</text>
      </view>

    </scroll-view>

  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import examApi from '@/api/exam'

const exams    = ref<any[]>([])
const results  = ref<any[]>([])
const loading  = ref(false)

const passedCount = computed(() => results.value.filter(r => r.passed).length)
const totalCount  = computed(() => results.value.length)
const passRate    = computed(() => totalCount.value ? Math.round((passedCount.value / totalCount.value) * 100) : 0)

onMounted(async () => {
  loading.value = true
  try {
    const [examsRes, resultsRes] = await Promise.allSettled([
      examApi.getExams(),
      examApi.getMyResults(),
    ])
    if (examsRes.status === 'fulfilled') {
      const d = examsRes.value as any
      exams.value = d.items || d.exams || (Array.isArray(d) ? d : [])
    }
    if (resultsRes.status === 'fulfilled') {
      const d = resultsRes.value as any
      results.value = d.items || d.sessions || (Array.isArray(d) ? d : [])
    }
  } finally {
    loading.value = false
  }
})

function goIntro(id: number) {
  uni.navigateTo({ url: `/pages/exam/intro?id=${id}` })
}

function goBack() {
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}
</script>

<style scoped>
.ex-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }
.ex-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.ex-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.ex-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.ex-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.ex-navbar__placeholder { width: 64rpx; }

.ex-summary {
  display: flex; align-items: center; justify-content: center;
  background: var(--surface); padding: 28rpx 32rpx; margin: 0;
  border-bottom: 1px solid var(--border-light);
}
.ex-summary__item { display: flex; flex-direction: column; align-items: center; flex: 1; gap: 4rpx; }
.ex-summary__val { font-size: 40rpx; font-weight: 800; color: var(--text-primary); }
.ex-summary__lbl { font-size: 22rpx; color: var(--text-secondary); }
.ex-summary__divider { width: 1px; height: 60rpx; background: var(--border-light); }

.ex-body { flex: 1; padding: 20rpx 32rpx 40rpx; }
.ex-section-title { display: block; font-size: 28rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 16rpx; }
.ex-list { display: flex; flex-direction: column; gap: 16rpx; }

.ex-card {
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 24rpx; border: 1px solid var(--border-light); cursor: pointer;
}
.ex-card:active { opacity: 0.85; }
.ex-card__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12rpx; }
.ex-card__name { font-size: 28rpx; font-weight: 700; color: var(--text-primary); flex: 1; }
.ex-card__level {
  font-size: 20rpx; font-weight: 600; padding: 4rpx 14rpx; border-radius: var(--radius-full);
  background: var(--bhp-primary-50); color: var(--bhp-primary-600);
}
.ex-card__info { display: flex; gap: 12rpx; margin-bottom: 10rpx; }
.ex-card__tag {
  font-size: 20rpx; color: var(--text-secondary); background: var(--surface-secondary);
  padding: 4rpx 14rpx; border-radius: var(--radius-full);
}
.ex-card__desc { font-size: 24rpx; color: var(--text-tertiary); margin-bottom: 12rpx; }
.ex-card__desc text { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.ex-card__action { display: flex; justify-content: flex-end; }
.ex-card__btn { font-size: 24rpx; font-weight: 600; color: var(--bhp-primary-500); }

.ex-empty { display: flex; flex-direction: column; align-items: center; padding: 120rpx 0; gap: 16rpx; }
.ex-empty__icon { font-size: 64rpx; }
.ex-empty__text { font-size: 26rpx; color: var(--text-tertiary); }
</style>
