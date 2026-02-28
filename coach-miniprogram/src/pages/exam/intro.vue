<template>
  <view class="ei-page">

    <view class="ei-navbar safe-area-top">
      <view class="ei-navbar__back" @tap="goBack"><text class="ei-navbar__arrow">‹</text></view>
      <text class="ei-navbar__title">考试须知</text>
      <view class="ei-navbar__placeholder"></view>
    </view>

    <scroll-view scroll-y class="ei-body">

      <template v-if="loading">
        <view class="bhp-skeleton" style="height: 300rpx; border-radius: var(--radius-lg);"></view>
      </template>

      <template v-else-if="exam">
        <!-- 考试信息 -->
        <view class="ei-hero">
          <text class="ei-hero__name">{{ exam.name || exam.title }}</text>
          <text class="ei-hero__desc" v-if="exam.description">{{ exam.description }}</text>
        </view>

        <!-- 考试规则 -->
        <view class="ei-card">
          <text class="ei-card__title">考试规则</text>
          <view class="ei-rules">
            <view class="ei-rule">
              <text class="ei-rule__icon">📝</text>
              <text class="ei-rule__label">题目数量</text>
              <text class="ei-rule__val">{{ exam.question_count || exam.total_questions || '-' }} 题</text>
            </view>
            <view class="ei-rule">
              <text class="ei-rule__icon">⏱</text>
              <text class="ei-rule__label">考试时限</text>
              <text class="ei-rule__val">{{ exam.time_limit_minutes || '-' }} 分钟</text>
            </view>
            <view class="ei-rule">
              <text class="ei-rule__icon">🎯</text>
              <text class="ei-rule__label">通过分数</text>
              <text class="ei-rule__val">{{ exam.pass_score || 60 }} 分</text>
            </view>
            <view class="ei-rule">
              <text class="ei-rule__icon">🔄</text>
              <text class="ei-rule__label">允许次数</text>
              <text class="ei-rule__val">{{ exam.max_attempts || '不限' }}</text>
            </view>
          </view>
        </view>

        <!-- 注意事项 -->
        <view class="ei-card">
          <text class="ei-card__title">注意事项</text>
          <view class="ei-notices">
            <view class="ei-notice" v-for="(n, i) in notices" :key="i">
              <text class="ei-notice__num">{{ i + 1 }}</text>
              <text class="ei-notice__text">{{ n }}</text>
            </view>
          </view>
        </view>
      </template>

    </scroll-view>

    <!-- 开始考试按钮 -->
    <view class="ei-footer safe-area-bottom" v-if="exam">
      <view class="ei-start-btn" :class="{ 'ei-start-btn--disabled': starting }" @tap="startExam">
        <text>{{ starting ? '正在进入...' : '开始考试' }}</text>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import examApi from '@/api/exam'

const exam     = ref<any>(null)
const loading  = ref(false)
const starting = ref(false)
const examId   = ref(0)

const notices = [
  '考试开始后将自动计时，请确保网络稳定',
  '每道题只能作答一次，提交后不可修改',
  '考试中途退出将自动提交已作答内容',
  '请在安静环境下独立完成考试',
  '考试通过后可获得相应等级认证',
]

onMounted(() => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1] as any
  examId.value = Number(page.$page?.options?.id || page.options?.id || 0)
  if (examId.value) loadExam()
})

async function loadExam() {
  loading.value = true
  try {
    exam.value = await examApi.getExamDetail(examId.value)
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function startExam() {
  if (starting.value) return
  starting.value = true
  try {
    const res = await examApi.startSession(examId.value) as any
    const sessionId = res.session_id || res.id
    uni.redirectTo({ url: `/pages/exam/do?sessionId=${sessionId}` })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '开始失败', icon: 'none' })
  } finally {
    starting.value = false
  }
}

function goBack() {
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}
</script>

<style scoped>
.ei-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }
.ei-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.ei-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.ei-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.ei-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.ei-navbar__placeholder { width: 64rpx; }

.ei-body { flex: 1; padding: 20rpx 32rpx 160rpx; }

.ei-hero { padding: 32rpx 0; }
.ei-hero__name { display: block; font-size: 36rpx; font-weight: 800; color: var(--text-primary); margin-bottom: 12rpx; }
.ei-hero__desc { display: block; font-size: 26rpx; color: var(--text-secondary); line-height: 1.6; }

.ei-card {
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 24rpx; margin-bottom: 20rpx; border: 1px solid var(--border-light);
}
.ei-card__title { display: block; font-size: 28rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 20rpx; }

.ei-rules { display: flex; flex-wrap: wrap; gap: 16rpx; }
.ei-rule {
  width: calc(50% - 8rpx); display: flex; align-items: center; gap: 10rpx;
  padding: 16rpx; background: var(--surface-secondary); border-radius: var(--radius-md);
}
.ei-rule__icon { font-size: 28rpx; flex-shrink: 0; }
.ei-rule__label { font-size: 22rpx; color: var(--text-secondary); flex: 1; }
.ei-rule__val { font-size: 24rpx; font-weight: 700; color: var(--text-primary); }

.ei-notices { display: flex; flex-direction: column; gap: 16rpx; }
.ei-notice { display: flex; align-items: flex-start; gap: 12rpx; }
.ei-notice__num {
  width: 36rpx; height: 36rpx; border-radius: 50%; flex-shrink: 0;
  background: var(--bhp-primary-50); color: var(--bhp-primary-600);
  display: flex; align-items: center; justify-content: center;
  font-size: 20rpx; font-weight: 700;
}
.ei-notice__text { font-size: 24rpx; color: var(--text-secondary); line-height: 1.6; flex: 1; }

.ei-footer {
  position: fixed; bottom: 0; left: 0; right: 0;
  padding: 16rpx 32rpx 24rpx; background: var(--surface);
  border-top: 1px solid var(--border-light);
}
.ei-start-btn {
  height: 96rpx; border-radius: var(--radius-lg); background: var(--bhp-primary-500);
  display: flex; align-items: center; justify-content: center;
  font-size: 30rpx; font-weight: 700; color: #fff; cursor: pointer;
}
.ei-start-btn:active { opacity: 0.85; }
.ei-start-btn--disabled { background: var(--bhp-gray-200); color: var(--text-tertiary); }
</style>
