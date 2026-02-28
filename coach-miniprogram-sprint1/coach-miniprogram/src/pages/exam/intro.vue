<template>
  <view class="intro-page">

    <!-- 骨架屏 -->
    <template v-if="loading">
      <view class="px-4 mt-4">
        <view class="bhp-skeleton" style="height: 200rpx; border-radius: var(--radius-xl, 16px); margin-bottom: 16rpx;"></view>
        <view class="bhp-skeleton" style="height: 240rpx; border-radius: var(--radius-xl, 16px); margin-bottom: 16rpx;"></view>
        <view class="bhp-skeleton" style="height: 160rpx; border-radius: var(--radius-xl, 16px);"></view>
      </view>
    </template>

    <template v-else-if="exam">
      <!-- 标题卡 -->
      <view class="intro-header px-4">
        <view class="intro-header__card" :class="`intro-level-bg--${exam.target_level.toLowerCase()}`">
          <view class="intro-header__level-tag">
            <text>{{ exam.level_required }} → {{ exam.target_level }}</text>
          </view>
          <text class="intro-header__title">{{ exam.title }}</text>
          <text class="intro-header__desc" v-if="exam.description">{{ exam.description }}</text>
        </view>
      </view>

      <!-- 考试参数 -->
      <view class="intro-params px-4">
        <view class="intro-params__card bhp-card bhp-card--flat">
          <text class="intro-section-title">考试信息</text>
          <view class="intro-params__grid">
            <view class="intro-param-item">
              <text class="intro-param-item__icon">📝</text>
              <text class="intro-param-item__value">{{ exam.question_count }}</text>
              <text class="intro-param-item__label">题目数量</text>
            </view>
            <view class="intro-param-item">
              <text class="intro-param-item__icon">⏱</text>
              <text class="intro-param-item__value">{{ exam.time_limit }}<text style="font-size: 20rpx;">分钟</text></text>
              <text class="intro-param-item__label">考试时长</text>
            </view>
            <view class="intro-param-item">
              <text class="intro-param-item__icon">🎯</text>
              <text class="intro-param-item__value">{{ exam.pass_score }}</text>
              <text class="intro-param-item__label">及格分数</text>
            </view>
            <view class="intro-param-item" v-if="exam.attempt_count !== undefined">
              <text class="intro-param-item__icon">🔄</text>
              <text class="intro-param-item__value">{{ exam.attempt_count || 0 }}</text>
              <text class="intro-param-item__label">已考次数</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 上次成绩 -->
      <view class="intro-last px-4" v-if="exam.last_score !== undefined && exam.last_score !== null">
        <view class="intro-last__card" :class="exam.status === 'passed' ? 'intro-last--passed' : 'intro-last--failed'">
          <text class="intro-last__label">上次成绩</text>
          <text class="intro-last__score">{{ exam.last_score }} 分</text>
          <view class="intro-last__tag">
            <text>{{ exam.status === 'passed' ? '已通过 ✓' : '未通过' }}</text>
          </view>
        </view>
      </view>

      <!-- 考试规则 -->
      <view class="intro-rules px-4">
        <view class="intro-rules__card bhp-card bhp-card--flat">
          <text class="intro-section-title">考试须知</text>
          <view class="intro-rule-item" v-for="(rule, i) in displayRules" :key="i">
            <text class="intro-rule-item__num">{{ i + 1 }}</text>
            <text class="intro-rule-item__text">{{ rule }}</text>
          </view>
        </view>
      </view>

      <!-- 通过奖励预告 -->
      <view class="intro-reward px-4">
        <view class="intro-reward__card">
          <text class="intro-reward__icon">🏆</text>
          <view class="intro-reward__body">
            <text class="intro-reward__title">通过后可获得</text>
            <text class="intro-reward__sub">积分奖励 · 晋级资质解锁 · {{ exam.target_level }} 等级认证</text>
          </view>
        </view>
      </view>

      <!-- 底部操作 -->
      <view class="intro-footer">
        <view
          class="bhp-btn bhp-btn--primary bhp-btn--full"
          :class="{ 'bhp-btn--disabled': exam.status === 'passed' && !allowRetake }"
          @tap="startExam"
        >
          <text v-if="exam.status === 'passed' && !allowRetake">已通过（可重考提分）</text>
          <text v-else>开始考试</text>
        </view>
        <view class="intro-footer__hint" v-if="exam.status === 'passed'">
          <text class="text-xs text-secondary-color">已通过认证，重考仅影响历史记录，不影响等级</text>
        </view>
      </view>
    </template>

    <!-- 错误 -->
    <view class="intro-error" v-else-if="!loading">
      <text class="intro-error__icon">😕</text>
      <text class="intro-error__text">考试信息加载失败</text>
      <view class="bhp-btn bhp-btn--secondary mt-4" @tap="loadExam">重试</view>
    </view>

    <view style="height: 120rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { certExamApi, type ExamInfo } from '@/api/exam'

const examId      = ref(0)
const exam        = ref<ExamInfo | null>(null)
const loading     = ref(false)
const allowRetake = ref(true)

const DEFAULT_RULES = [
  '考试时间一旦开始不可暂停，请确保网络畅通',
  '题型包含单选题、多选题和判断题',
  '答题过程中可随时切换题目，请仔细核查后再提交',
  '提交后将立即显示成绩，未达及格线可于24小时后重考',
  '通过考试后方可提交等级晋升申请',
]

const displayRules = computed(() => exam.value?.rules?.length ? exam.value.rules : DEFAULT_RULES)

onMounted(async () => {
  const pages = getCurrentPages()
  const cur = pages[pages.length - 1] as any
  const query = cur.$page?.options || cur.options || {}
  examId.value = Number(query.exam_id || 0)
  if (examId.value) await loadExam()
})

async function loadExam() {
  loading.value = true
  try {
    exam.value = await certExamApi.detail(examId.value)
    uni.setNavigationBarTitle({ title: exam.value.title })
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function startExam() {
  if (!exam.value?.quiz_id && !examId.value) {
    uni.showToast({ title: '考试信息不完整', icon: 'none' })
    return
  }
  uni.showModal({
    title: '确认开始考试',
    content: `共 ${exam.value!.question_count} 题，限时 ${exam.value!.time_limit} 分钟，开始后无法暂停。确认开始吗？`,
    confirmText: '开始',
    cancelText: '再想想',
    success: (res) => {
      if (res.confirm) {
        uni.navigateTo({
          url: `/pages/exam/session?exam_id=${examId.value}&quiz_id=${exam.value!.quiz_id || ''}`
        })
      }
    }
  })
}
</script>

<style scoped>
.intro-page { background: var(--surface-secondary); min-height: 100vh; }

/* 标题卡 */
.intro-header { padding-top: 16rpx; }
.intro-header__card {
  border-radius: var(--radius-xl, 16px);
  padding: 32rpx;
}
.intro-level-bg--l1 { background: linear-gradient(135deg, #d1fae5, #a7f3d0); }
.intro-level-bg--l2 { background: linear-gradient(135deg, #bfdbfe, #93c5fd); }
.intro-level-bg--l3 { background: linear-gradient(135deg, #fde68a, #fcd34d); }
.intro-level-bg--l4 { background: linear-gradient(135deg, #e9d5ff, #d8b4fe); }
.intro-level-bg--l5 { background: linear-gradient(135deg, #fecaca, #fca5a5); }

.intro-header__level-tag {
  display: inline-block;
  background: rgba(255,255,255,0.6);
  border-radius: var(--radius-full);
  padding: 4rpx 20rpx;
  font-size: 22rpx;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 16rpx;
}
.intro-header__title {
  display: block;
  font-size: 34rpx;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.4;
}
.intro-header__desc {
  display: block;
  font-size: 24rpx;
  color: var(--text-secondary);
  margin-top: 8rpx;
  line-height: 1.5;
}

/* 参数区 */
.intro-params { padding-top: 16rpx; }
.intro-section-title {
  display: block;
  font-size: 26rpx;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 20rpx;
}
.intro-params__grid {
  display: flex;
  align-items: stretch;
  gap: 0;
  flex-wrap: wrap;
}
.intro-param-item {
  flex: 1;
  min-width: 25%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6rpx;
  padding: 12rpx 0;
}
.intro-param-item__icon { font-size: 32rpx; }
.intro-param-item__value { font-size: 32rpx; font-weight: 700; color: var(--text-primary); }
.intro-param-item__label { font-size: 20rpx; color: var(--text-secondary); }

/* 上次成绩 */
.intro-last { padding-top: 16rpx; }
.intro-last__card {
  border-radius: var(--radius-lg);
  padding: 20rpx 24rpx;
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.intro-last--passed { background: var(--bhp-success-50, #f0fdf4); border: 1px solid var(--bhp-success-200, #bbf7d0); }
.intro-last--failed { background: var(--bhp-gray-50, #f9fafb); border: 1px solid var(--border-light); }
.intro-last__label { font-size: 24rpx; color: var(--text-secondary); }
.intro-last__score { font-size: 36rpx; font-weight: 700; color: var(--text-primary); flex: 1; text-align: center; }
.intro-last__tag { font-size: 22rpx; color: var(--bhp-success-500, #22c55e); font-weight: 600; }

/* 规则 */
.intro-rules { padding-top: 16rpx; }
.intro-rule-item { display: flex; gap: 12rpx; margin-bottom: 12rpx; align-items: flex-start; }
.intro-rule-item__num {
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  background: var(--bhp-primary-100, #d1fae5);
  color: var(--bhp-primary-700, #047857);
  font-size: 20rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.intro-rule-item__text { font-size: 26rpx; color: var(--text-secondary); line-height: 1.6; flex: 1; }

/* 奖励 */
.intro-reward { padding-top: 16rpx; }
.intro-reward__card {
  display: flex;
  align-items: center;
  gap: 16rpx;
  background: linear-gradient(135deg, var(--bhp-warn-50, #fffbeb), var(--bhp-warn-100, #fef3c7));
  border: 1px solid var(--bhp-warn-200, #fde68a);
  border-radius: var(--radius-lg);
  padding: 20rpx 24rpx;
}
.intro-reward__icon { font-size: 40rpx; }
.intro-reward__title { display: block; font-size: 26rpx; font-weight: 600; color: var(--bhp-warn-700, #b45309); }
.intro-reward__sub   { display: block; font-size: 22rpx; color: var(--bhp-warn-600, #d97706); margin-top: 4rpx; }

/* 底部 */
.intro-footer {
  position: fixed;
  bottom: 0; left: 0; right: 0;
  padding: 16rpx 32rpx;
  padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
  background: var(--surface);
  border-top: 1px solid var(--border-light);
  box-shadow: 0 -4px 12px rgba(0,0,0,0.06);
}
.intro-footer__hint { text-align: center; margin-top: 8rpx; }

/* 错误 */
.intro-error {
  display: flex; flex-direction: column; align-items: center;
  padding: 120rpx 0; gap: 16rpx;
}
.intro-error__icon { font-size: 80rpx; }
.intro-error__text { font-size: 28rpx; color: var(--text-tertiary); }
</style>
