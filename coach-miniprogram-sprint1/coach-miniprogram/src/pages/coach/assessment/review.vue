<template>
  <view class="review-page">

    <template v-if="loading">
      <view class="px-4 pt-4">
        <view v-for="i in 5" :key="i" class="bhp-skeleton" style="height: 120rpx; margin-bottom: 12rpx; border-radius: var(--radius-lg);"></view>
      </view>
    </template>

    <template v-else-if="assignment">

      <!-- 学员信息头 -->
      <view class="rv-header px-4">
        <view class="rv-header__card bhp-card bhp-card--flat">
          <view class="rv-header__avatar">
            <text>{{ (assignment.student_name || '用')[0] }}</text>
          </view>
          <view class="rv-header__info">
            <text class="rv-header__student">{{ assignment.student_name || `学员${assignment.student_id}` }}</text>
            <text class="rv-header__assessment">{{ assignment.assessment_title }}</text>
            <view class="rv-header__meta">
              <view class="rv-type-badge">
                <text>{{ TYPE_LABEL[assignment.assessment_type] || assignment.assessment_type }}</text>
              </view>
              <text class="text-xs text-secondary-color" v-if="assignment.submitted_at">
                提交于 {{ formatDate(assignment.submitted_at) }}
              </text>
            </view>
          </view>
          <view class="rv-status-badge" :class="`rv-status--${assignment.status}`">
            <text>{{ STATUS_LABEL[assignment.status] }}</text>
          </view>
        </view>
      </view>

      <!-- 作答记录 -->
      <view class="rv-responses px-4" v-if="assignment.responses?.length">
        <text class="rv-section-title">学员作答</text>
        <view
          v-for="(resp, idx) in assignment.responses"
          :key="resp.question_id"
          class="rv-response bhp-card bhp-card--flat"
        >
          <view class="rv-response__qnum">
            <text>Q{{ idx + 1 }}</text>
          </view>
          <view class="rv-response__body">
            <text class="rv-response__question">{{ resp.question_text }}</text>
            <view class="rv-response__answer">
              <text class="rv-response__answer-label text-xs text-secondary-color">学员回答：</text>
              <text class="rv-response__answer-text">
                {{ Array.isArray(resp.answer) ? resp.answer.join('、') : resp.answer }}
              </text>
            </view>
          </view>
        </view>
      </view>

      <!-- 无作答记录 -->
      <view class="rv-no-response px-4" v-else>
        <view class="rv-no-response__card bhp-card bhp-card--flat">
          <text class="text-secondary-color">暂无作答记录，该评估可能尚未提交</text>
        </view>
      </view>

      <!-- 审核意见（仅已提交状态可编辑） -->
      <view class="rv-review px-4">
        <text class="rv-section-title">审核意见</text>
        <view class="rv-review__card bhp-card bhp-card--flat">

          <!-- 评分 -->
          <view class="rv-score-row">
            <text class="rv-score-label">综合评分（可选）</text>
            <view class="rv-score-stars">
              <view
                v-for="star in 5"
                :key="star"
                class="rv-star"
                :class="{ 'rv-star--active': star <= reviewScore }"
                @tap="reviewScore = reviewScore === star ? 0 : star"
              >
                <text>{{ star <= reviewScore ? '★' : '☆' }}</text>
              </view>
              <text class="rv-score-val text-xs text-secondary-color" v-if="reviewScore">
                {{ reviewScore * 20 }}/100
              </text>
            </view>
          </view>

          <!-- 文字意见 -->
          <textarea
            class="rv-review__input"
            v-model="reviewNote"
            :placeholder="assignment.status === 'reviewed' ? (assignment.coach_note || '暂无审核意见') : '输入审核意见、建议或改进方向…'"
            placeholder-class="rv-input-placeholder"
            :disabled="assignment.status === 'reviewed'"
            :maxlength="1000"
            auto-height
          />
          <text class="rv-char-count text-xs text-tertiary-color" v-if="assignment.status !== 'reviewed'">
            {{ reviewNote.length }}/1000
          </text>

          <!-- 已审核时显示原有意见 -->
          <view class="rv-reviewed-note" v-if="assignment.status === 'reviewed' && assignment.coach_note">
            <text class="text-xs text-secondary-color">审核意见：{{ assignment.coach_note }}</text>
          </view>
        </view>
      </view>

      <!-- 操作按钮（仅待审核） -->
      <view class="rv-actions px-4" v-if="assignment.status === 'submitted'">
        <view class="rv-actions__row">
          <view class="rv-action-return" @tap="returnAssessment">
            <text>退回重做</text>
          </view>
          <view
            class="rv-action-approve"
            :class="{ 'rv-action-approve--active': !submitting }"
            @tap="submitReview"
          >
            <text v-if="!submitting">提交审核</text>
            <text v-else>提交中...</text>
          </view>
        </view>
        <text class="rv-actions__hint text-xs text-tertiary-color">审核后学员将收到结果通知</text>
      </view>

      <!-- 已审核提示 -->
      <view class="rv-done px-4" v-else-if="assignment.status === 'reviewed'">
        <view class="rv-done__card">
          <text class="rv-done__icon">✅</text>
          <text class="rv-done__text">已完成审核</text>
          <text class="text-xs text-tertiary-color" v-if="assignment.reviewed_at">
            审核于 {{ formatDate(assignment.reviewed_at) }}
          </text>
        </view>
      </view>
    </template>

    <view class="rv-not-found px-4" v-else-if="!loading">
      <view class="rv-not-found__card bhp-card bhp-card--flat">
        <text>评估记录未找到或加载失败</text>
      </view>
    </view>

    <view style="height: 60rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { assignmentApi, type AssessmentAssignment } from '@/api/coach'

const assignment  = ref<AssessmentAssignment | null>(null)
const loading     = ref(false)
const reviewNote  = ref('')
const reviewScore = ref(0)
const submitting  = ref(false)

const STATUS_LABEL: Record<string, string> = {
  assigned: '未开始', in_progress: '进行中', submitted: '待审核', reviewed: '已审核'
}
const TYPE_LABEL: Record<string, string> = {
  baps: 'BAPS评估', survey: '问卷调查', health_check: '健康检查', custom: '自定义'
}

onMounted(async () => {
  const pages = getCurrentPages()
  const cur = pages[pages.length - 1] as any
  const id = Number(cur?.options?.id || 0)
  if (!id) return

  loading.value = true
  try {
    assignment.value = await assignmentApi.detail(id)
    if (assignment.value?.coach_note) {
      reviewNote.value = assignment.value.coach_note
    }
    if (assignment.value?.score) {
      reviewScore.value = Math.round(assignment.value.score / 20)
    }
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
})

async function submitReview() {
  if (submitting.value || !assignment.value) return
  submitting.value = true
  try {
    await assignmentApi.submitReview(assignment.value.id, {
      coach_note: reviewNote.value,
      score: reviewScore.value ? reviewScore.value * 20 : undefined,
      status: 'reviewed'
    })
    assignment.value.status = 'reviewed'
    assignment.value.coach_note = reviewNote.value
    uni.showToast({ title: '审核已提交', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 1200)
  } catch (e: any) {
    uni.showToast({ title: e?.data?.detail || '提交失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

function returnAssessment() {
  uni.showModal({
    title: '退回评估',
    content: '退回后学员需重新完成评估，确认吗？',
    confirmText: '确认退回',
    confirmColor: '#ef4444',
    success: async (res) => {
      if (!res.confirm || !assignment.value) return
      try {
        await assignmentApi.submitReview(assignment.value.id, {
          coach_note: reviewNote.value || '请重新完成评估',
          status: 'reviewed'
        })
        uni.showToast({ title: '已退回', icon: 'none' })
        setTimeout(() => uni.navigateBack(), 1000)
      } catch {
        uni.showToast({ title: '操作失败', icon: 'none' })
      }
    }
  })
}

function formatDate(s: string): string {
  if (!s) return ''
  try {
    const d = new Date(s)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  } catch { return s }
}
</script>

<style scoped>
.review-page { background: var(--surface-secondary); min-height: 100vh; }

/* 头部 */
.rv-header { padding-top: 16rpx; }
.rv-header__card { display: flex; align-items: flex-start; gap: 16rpx; padding: 20rpx 24rpx; }
.rv-header__avatar {
  width: 72rpx; height: 72rpx; border-radius: 50%;
  background: var(--bhp-primary-100, #d1fae5);
  display: flex; align-items: center; justify-content: center;
  font-size: 30rpx; color: var(--bhp-primary-700, #047857); font-weight: 700;
  flex-shrink: 0;
}
.rv-header__info { flex: 1; }
.rv-header__student { display: block; font-size: 28rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 4rpx; }
.rv-header__assessment { display: block; font-size: 24rpx; color: var(--text-secondary); margin-bottom: 8rpx; }
.rv-header__meta { display: flex; align-items: center; gap: 10rpx; }
.rv-type-badge {
  display: inline-block; font-size: 18rpx;
  background: var(--bhp-primary-50); color: var(--bhp-primary-600, #059669);
  padding: 2rpx 10rpx; border-radius: var(--radius-full);
}
.rv-status-badge {
  font-size: 20rpx; font-weight: 600;
  padding: 4rpx 14rpx; border-radius: var(--radius-full);
  flex-shrink: 0;
}
.rv-status--submitted  { background: var(--bhp-warn-50); color: var(--bhp-warn-700, #b45309); }
.rv-status--reviewed   { background: var(--bhp-success-50); color: var(--bhp-success-700, #15803d); }
.rv-status--assigned   { background: var(--bhp-gray-100); color: var(--text-tertiary); }
.rv-status--in_progress { background: #e6f7ff; color: #096dd9; }

.rv-section-title { display: block; font-size: 26rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 12rpx; }

/* 作答 */
.rv-responses { padding-top: 20rpx; }
.rv-response {
  display: flex; gap: 16rpx; padding: 16rpx 20rpx; margin-bottom: 10rpx;
}
.rv-response__qnum {
  width: 44rpx; height: 44rpx; border-radius: 50%;
  background: var(--bhp-primary-500); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 20rpx; font-weight: 700; flex-shrink: 0;
}
.rv-response__body { flex: 1; }
.rv-response__question { display: block; font-size: 26rpx; color: var(--text-primary); margin-bottom: 10rpx; line-height: 1.5; }
.rv-response__answer { background: var(--bhp-gray-50, #f9fafb); border-radius: var(--radius-md); padding: 10rpx 14rpx; }
.rv-response__answer-label { display: block; margin-bottom: 4rpx; }
.rv-response__answer-text { font-size: 24rpx; color: var(--text-primary); line-height: 1.5; }

.rv-no-response { padding-top: 16rpx; }
.rv-no-response__card { padding: 24rpx; text-align: center; }

/* 审核 */
.rv-review { padding-top: 20rpx; }
.rv-review__card { padding: 20rpx 24rpx; }
.rv-score-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16rpx; }
.rv-score-label { font-size: 26rpx; color: var(--text-secondary); }
.rv-score-stars { display: flex; align-items: center; gap: 8rpx; }
.rv-star { font-size: 36rpx; cursor: pointer; color: var(--bhp-gray-300); }
.rv-star--active { color: #faad14; }
.rv-score-val { margin-left: 8rpx; }

.rv-review__input {
  width: 100%; min-height: 160rpx;
  background: var(--bhp-gray-50, #f9fafb);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: 16rpx 20rpx; font-size: 26rpx; color: var(--text-primary);
  box-sizing: border-box; line-height: 1.6;
}
.rv-input-placeholder { color: var(--text-tertiary); font-size: 26rpx; }
.rv-char-count { display: block; text-align: right; margin-top: 6rpx; }
.rv-reviewed-note {
  margin-top: 12rpx; padding: 12rpx 16rpx;
  background: var(--bhp-success-50); border-radius: var(--radius-md);
}

/* 操作 */
.rv-actions { padding-top: 20rpx; }
.rv-actions__row { display: flex; gap: 16rpx; margin-bottom: 12rpx; }
.rv-action-return, .rv-action-approve {
  flex: 1; height: 88rpx;
  border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 28rpx; font-weight: 600; cursor: pointer;
}
.rv-action-return   { background: var(--bhp-gray-100); color: var(--text-secondary); }
.rv-action-approve  { background: var(--bhp-gray-200); color: var(--text-tertiary); }
.rv-action-approve--active { background: var(--bhp-primary-500); color: #fff; }
.rv-action-approve--active:active { opacity: 0.8; }
.rv-actions__hint { display: block; text-align: center; }

/* 完成提示 */
.rv-done { padding-top: 20rpx; }
.rv-done__card {
  background: var(--bhp-success-50);
  border: 1px solid var(--bhp-success-200, #bbf7d0);
  border-radius: var(--radius-lg);
  padding: 32rpx; display: flex; flex-direction: column; align-items: center; gap: 10rpx;
}
.rv-done__icon { font-size: 60rpx; }
.rv-done__text { font-size: 28rpx; font-weight: 600; color: var(--bhp-success-700, #15803d); }

/* 未找到 */
.rv-not-found { padding-top: 20rpx; }
.rv-not-found__card { padding: 32rpx; text-align: center; color: var(--text-tertiary); }
</style>
