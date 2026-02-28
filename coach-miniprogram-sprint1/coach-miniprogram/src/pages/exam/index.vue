<template>
  <view class="exam-home-page">

    <!-- 顶部：用户当前等级 -->
    <view class="exam-level-banner px-4">
      <view class="exam-level-banner__card">
        <view class="exam-level-banner__left">
          <text class="exam-level-banner__title">认证考试</text>
          <text class="exam-level-banner__sub">当前等级：{{ LEVEL_LABEL[userStore.user?.role || 'observer'] || 'L0 观察者' }}</text>
        </view>
        <view class="exam-level-banner__right" @tap="goHistory">
          <text class="exam-level-banner__history">历史记录</text>
          <text class="exam-level-banner__arrow">›</text>
        </view>
      </view>
    </view>

    <!-- 考试说明 -->
    <view class="exam-tips px-4">
      <view class="exam-tips__card">
        <text class="exam-tips__icon">💡</text>
        <view class="exam-tips__content">
          <text class="exam-tips__text">认证考试用于等级晋升资质认定，通过后方可提交晋级申请</text>
        </view>
      </view>
    </view>

    <!-- 考试列表 -->
    <view class="exam-list px-4">

      <!-- 骨架屏 -->
      <template v-if="loading">
        <view v-for="i in 5" :key="i" class="bhp-skeleton exam-skeleton"></view>
      </template>

      <template v-else>
        <view
          v-for="exam in exams"
          :key="exam.id"
          class="exam-card bhp-card bhp-card--flat"
          :class="{
            'exam-card--available': exam.status === 'available',
            'exam-card--passed':    exam.status === 'passed',
            'exam-card--locked':    exam.status === 'locked',
            'exam-card--cooldown':  exam.status === 'cooldown',
          }"
          @tap="goIntro(exam)"
        >
          <!-- 左侧等级圆标 -->
          <view class="exam-card__level-badge" :class="`exam-level-color--${exam.target_level.toLowerCase()}`">
            <text class="exam-card__level-text">{{ exam.target_level }}</text>
          </view>

          <!-- 中间信息 -->
          <view class="exam-card__body">
            <text class="exam-card__title">{{ exam.title }}</text>
            <view class="exam-card__meta flex-start gap-3 mt-1">
              <text class="text-xs text-secondary-color">{{ exam.question_count }} 题</text>
              <text class="text-xs text-secondary-color">{{ exam.time_limit }} 分钟</text>
              <text class="text-xs text-secondary-color">及格 {{ exam.pass_score }} 分</text>
            </view>
            <!-- 上次得分 -->
            <view class="exam-card__last-score" v-if="exam.last_score !== undefined && exam.last_score !== null">
              <text class="text-xs" :class="exam.status === 'passed' ? 'text-success-color' : 'text-secondary-color'">
                上次：{{ exam.last_score }} 分{{ exam.attempt_count ? `（第${exam.attempt_count}次）` : '' }}
              </text>
            </view>
            <!-- 冷却期 -->
            <view v-if="exam.status === 'cooldown' && exam.cooldown_until">
              <text class="text-xs" style="color: var(--bhp-warn-500);">
                {{ formatCooldown(exam.cooldown_until) }} 后可重考
              </text>
            </view>
          </view>

          <!-- 右侧状态 -->
          <view class="exam-card__status">
            <text v-if="exam.status === 'passed'"    class="exam-status exam-status--passed">已通过</text>
            <text v-else-if="exam.status === 'locked'"   class="exam-status exam-status--locked">🔒</text>
            <text v-else-if="exam.status === 'cooldown'" class="exam-status exam-status--cooldown">冷却中</text>
            <text v-else class="exam-status exam-status--available">去考试 ›</text>
          </view>
        </view>

        <!-- 空状态 -->
        <view class="exam-empty" v-if="!loading && !exams.length">
          <text class="exam-empty__icon">📋</text>
          <text class="exam-empty__text">暂无可参加的考试</text>
        </view>
      </template>
    </view>

    <view style="height: 40rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { certExamApi, type ExamInfo } from '@/api/exam'

const userStore = useUserStore()
const exams    = ref<ExamInfo[]>([])
const loading  = ref(false)

const LEVEL_LABEL: Record<string, string> = {
  observer:   'L0 观察者',
  grower:     'L1 成长者',
  sharer:     'L2 分享者',
  coach:      'L3 教练',
  promoter:   'L4 推广者',
  supervisor: 'L4 督导者',
  master:     'L5 行健师',
}

onMounted(() => loadExams())

onPullDownRefresh(async () => {
  await loadExams()
  uni.stopPullDownRefresh()
})

async function loadExams() {
  loading.value = true
  try {
    const data = await certExamApi.available()
    exams.value = Array.isArray(data) ? data : []
  } catch {
    // 降级：展示静态考试列表
    exams.value = FALLBACK_EXAMS
  } finally {
    loading.value = false
  }
}

function goIntro(exam: ExamInfo) {
  if (exam.status === 'locked') {
    uni.showToast({ title: `需达到${exam.level_required}等级`, icon: 'none' })
    return
  }
  if (exam.status === 'cooldown') {
    uni.showToast({ title: '考试冷却中，请稍后再试', icon: 'none' })
    return
  }
  uni.navigateTo({ url: `/pages/exam/intro?exam_id=${exam.id}` })
}

function goHistory() {
  uni.navigateTo({ url: '/pages/exam/history' })
}

function formatCooldown(dateStr: string): string {
  try {
    const diff = new Date(dateStr).getTime() - Date.now()
    if (diff <= 0) return '0小时'
    const h = Math.ceil(diff / 3600000)
    return h >= 24 ? `${Math.ceil(h / 24)}天` : `${h}小时`
  } catch { return '一段时间' }
}

// 离线降级数据
const FALLBACK_EXAMS: ExamInfo[] = [
  { id: 1, title: 'L0→L1 基础认知测评', level_required: 'L0', target_level: 'L1', pass_score: 60, time_limit: 30, question_count: 20, status: 'available' },
  { id: 2, title: 'L1→L2 进阶评估测评', level_required: 'L1', target_level: 'L2', pass_score: 70, time_limit: 45, question_count: 30, status: 'locked' },
  { id: 3, title: 'L2→L3 教练技能认证', level_required: 'L2', target_level: 'L3', pass_score: 75, time_limit: 60, question_count: 40, status: 'locked' },
  { id: 4, title: 'L3→L4 督导能力认证', level_required: 'L3', target_level: 'L4', pass_score: 80, time_limit: 60, question_count: 40, status: 'locked' },
  { id: 5, title: 'L4→L5 行健师认证',   level_required: 'L4', target_level: 'L5', pass_score: 85, time_limit: 90, question_count: 50, status: 'locked' },
]
</script>

<style scoped>
.exam-home-page { background: var(--surface-secondary); min-height: 100vh; }

/* 等级横幅 */
.exam-level-banner { padding-top: 16rpx; }
.exam-level-banner__card {
  background: linear-gradient(135deg, var(--bhp-primary-500), var(--bhp-primary-600, #059669));
  border-radius: var(--radius-xl, 16px);
  padding: 28rpx 32rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.exam-level-banner__title { display: block; font-size: 32rpx; font-weight: 700; color: #fff; }
.exam-level-banner__sub   { display: block; font-size: 24rpx; color: rgba(255,255,255,0.85); margin-top: 4rpx; }
.exam-level-banner__right { display: flex; align-items: center; gap: 4rpx; cursor: pointer; }
.exam-level-banner__history { font-size: 24rpx; color: rgba(255,255,255,0.9); }
.exam-level-banner__arrow   { font-size: 32rpx; color: rgba(255,255,255,0.9); }

/* 提示 */
.exam-tips { padding-top: 16rpx; }
.exam-tips__card {
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
  background: var(--bhp-primary-50);
  border-radius: var(--radius-lg);
  padding: 16rpx 20rpx;
}
.exam-tips__icon { font-size: 28rpx; }
.exam-tips__text { font-size: 24rpx; color: var(--bhp-primary-700, #047857); line-height: 1.5; }

/* 列表 */
.exam-list { padding-top: 16rpx; }
.exam-skeleton { height: 120rpx; margin-bottom: 12rpx; border-radius: var(--radius-lg); }

/* 考试卡 */
.exam-card {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 20rpx 24rpx;
  margin-bottom: 12rpx;
  cursor: pointer;
}
.exam-card:active { opacity: 0.8; }
.exam-card--locked  { opacity: 0.55; }
.exam-card--cooldown { opacity: 0.7; }

/* 等级徽章 */
.exam-card__level-badge {
  width: 72rpx;
  height: 72rpx;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.exam-level-color--l1 { background: #d1fae5; }
.exam-level-color--l2 { background: #bfdbfe; }
.exam-level-color--l3 { background: #fde68a; }
.exam-level-color--l4 { background: #e9d5ff; }
.exam-level-color--l5 { background: #fecaca; }
.exam-card__level-text { font-size: 22rpx; font-weight: 700; color: var(--text-primary); }

.exam-card__body { flex: 1; overflow: hidden; }
.exam-card__title { display: block; font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.exam-card__last-score { margin-top: 4rpx; }

.text-success-color { color: var(--bhp-success-500, #22c55e); }

/* 状态标签 */
.exam-status { font-size: 24rpx; font-weight: 600; }
.exam-status--passed    { color: var(--bhp-success-500, #22c55e); }
.exam-status--locked    { font-size: 32rpx; }
.exam-status--cooldown  { color: var(--bhp-warn-500, #f59e0b); }
.exam-status--available { color: var(--bhp-primary-500); }

/* 空状态 */
.exam-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80rpx 0;
  gap: 16rpx;
}
.exam-empty__icon { font-size: 80rpx; }
.exam-empty__text { font-size: 28rpx; color: var(--text-tertiary); }
</style>
