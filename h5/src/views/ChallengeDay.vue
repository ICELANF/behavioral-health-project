<template>
  <div class="page-container">
    <van-nav-bar
      :title="headerTitle"
      left-arrow
      @click-left="$router.back()"
    />

    <div class="page-content">
      <van-loading v-if="loading" class="loading" />

      <!-- Challenge completed congratulations -->
      <template v-else-if="challengeCompleted">
        <div class="congrats-card card">
          <div class="congrats-icon">&#127942;</div>
          <h2 class="congrats-title">恭喜完成挑战!</h2>
          <p class="congrats-desc">
            你已经坚持完成了全部 {{ progress.total_days || 0 }} 天的挑战，非常棒!
          </p>
          <div class="congrats-stats">
            <div class="stat-item">
              <div class="stat-value">{{ progress.total_days || 0 }}</div>
              <div class="stat-label">总天数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ progress.completed_days || 0 }}</div>
              <div class="stat-label">完成天数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ progress.max_streak || 0 }}</div>
              <div class="stat-label">最长连续</div>
            </div>
          </div>
          <van-button
            type="primary"
            block
            round
            @click="$router.push('/challenges')"
          >
            返回挑战列表
          </van-button>
        </div>
      </template>

      <!-- Normal day view -->
      <template v-else>
        <!-- Progress header -->
        <div class="day-header card">
          <div class="day-progress-bar">
            <van-progress
              :percentage="dayProgressPercent"
              stroke-width="6"
              color="#1989fa"
              track-color="#e8e8e8"
              :show-pivot="false"
            />
            <span class="day-progress-text">
              {{ progress.current_day || 0 }} / {{ progress.total_days || 0 }} 天
            </span>
          </div>
          <div class="day-topic" v-if="todayData.day_topic">
            {{ todayData.day_topic }}
          </div>
        </div>

        <!-- Push cards timeline -->
        <div class="push-timeline" v-if="pushes.length > 0">
          <div
            v-for="(push, pushIndex) in sortedPushes"
            :key="push.id || pushIndex"
            class="push-card card"
          >
            <!-- Time + tag row -->
            <div class="push-top">
              <div class="time-badge">
                <van-icon name="clock-o" size="12" />
                <span>{{ push.push_time || '--:--' }}</span>
              </div>
              <van-tag
                :color="pushTagColor(push.tag)"
                text-color="#fff"
                size="medium"
                round
              >
                {{ pushTagLabel(push.tag) }}
              </van-tag>
              <div class="read-indicator" v-if="push.is_read">
                <van-icon name="success" color="#07c160" size="16" />
              </div>
            </div>

            <!-- Management content (collapsible) -->
            <van-collapse v-model="push._expandedSections" class="push-collapse">
              <van-collapse-item
                v-if="push.management_content"
                :title="'管理内容'"
                :name="'mgmt-' + push.id"
                icon="notes-o"
              >
                <div class="content-block management-content">
                  {{ push.management_content }}
                </div>
              </van-collapse-item>

              <van-collapse-item
                v-if="push.behavior_guidance"
                :title="'行为指导'"
                :name="'behavior-' + push.id"
                icon="guide-o"
              >
                <div class="content-block behavior-content">
                  {{ push.behavior_guidance }}
                </div>
              </van-collapse-item>
            </van-collapse>

            <!-- Survey interaction -->
            <div v-if="push.survey" class="survey-section">
              <div class="survey-header">
                <van-icon name="edit" size="16" color="#1989fa" />
                <span>{{ push.survey.title || '互动问答' }}</span>
              </div>

              <div class="survey-body">
                <div
                  v-for="(question, qIndex) in push.survey.questions"
                  :key="question.id || qIndex"
                  class="survey-question"
                >
                  <div class="question-label">
                    {{ qIndex + 1 }}. {{ question.label }}
                  </div>

                  <!-- Rating type -->
                  <template v-if="question.type === 'rating'">
                    <div class="rating-wrapper">
                      <van-rate
                        v-if="(question.max || 5) <= 10"
                        v-model="surveyResponses[push.id][question.id]"
                        :count="question.max || 5"
                        allow-half
                        color="#ffd21e"
                        void-color="#eee"
                        size="24"
                      />
                      <van-stepper
                        v-else
                        v-model="surveyResponses[push.id][question.id]"
                        :min="question.min || 0"
                        :max="question.max || 100"
                        theme="round"
                      />
                    </div>
                  </template>

                  <!-- Text type -->
                  <template v-else-if="question.type === 'text'">
                    <van-field
                      v-model="surveyResponses[push.id][question.id]"
                      type="textarea"
                      :placeholder="question.placeholder || '请输入...'"
                      rows="3"
                      maxlength="500"
                      show-word-limit
                      autosize
                      class="survey-textarea"
                    />
                  </template>

                  <!-- Single choice -->
                  <template v-else-if="question.type === 'single_choice'">
                    <van-radio-group
                      v-model="surveyResponses[push.id][question.id]"
                      direction="vertical"
                      class="choice-group"
                    >
                      <van-radio
                        v-for="option in question.options"
                        :key="option.value"
                        :name="option.value"
                        icon-size="18"
                      >
                        {{ option.label }}
                      </van-radio>
                    </van-radio-group>
                  </template>

                  <!-- Multi choice -->
                  <template v-else-if="question.type === 'multi_choice'">
                    <van-checkbox-group
                      v-model="surveyResponses[push.id][question.id]"
                      direction="vertical"
                      class="choice-group"
                    >
                      <van-checkbox
                        v-for="option in question.options"
                        :key="option.value"
                        :name="option.value"
                        shape="square"
                        icon-size="18"
                      >
                        {{ option.label }}
                      </van-checkbox>
                    </van-checkbox-group>
                  </template>
                </div>
              </div>

              <van-button
                type="primary"
                size="small"
                round
                block
                :loading="submittingSurvey === push.id"
                :disabled="push.survey_submitted"
                @click="submitSurvey(push)"
                class="survey-submit-btn"
              >
                {{ push.survey_submitted ? '已提交' : '提交' }}
              </van-button>
            </div>

            <!-- Mark as read button (if not yet read and no survey, or just a read action) -->
            <div class="push-bottom" v-if="!push.is_read">
              <van-button
                plain
                type="primary"
                size="small"
                round
                :loading="markingReadId === push.id"
                @click="markRead(push)"
              >
                <van-icon name="eye-o" />
                <span style="margin-left:4px">标记已读</span>
              </van-button>
            </div>
          </div>
        </div>

        <van-empty
          v-if="!loading && pushes.length === 0"
          description="今天暂无推送内容"
        />

        <!-- Advance to next day button -->
        <div class="advance-section" v-if="pushes.length > 0">
          <van-button
            type="success"
            block
            round
            size="large"
            :loading="advancing"
            :disabled="!canAdvance"
            @click="advanceDay"
          >
            {{ advanceButtonText }}
          </van-button>
          <p class="advance-hint" v-if="!canAdvance && pushes.length > 0">
            请先查看所有推送内容
          </p>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import api from '@/api/index'

interface SurveyQuestion {
  id: string
  type: 'rating' | 'text' | 'single_choice' | 'multi_choice'
  label: string
  placeholder?: string
  min?: number
  max?: number
  options?: { value: string; label: string }[]
}

interface Survey {
  title?: string
  questions: SurveyQuestion[]
}

interface Push {
  id: number
  push_time?: string
  tag?: string
  management_content?: string
  behavior_guidance?: string
  survey?: Survey | null
  is_read?: boolean
  survey_submitted?: boolean
  _expandedSections: string[]
}

interface ProgressInfo {
  current_day: number
  total_days: number
  completed_days: number
  max_streak: number
  status: string
}

const route = useRoute()
const router = useRouter()
const enrollmentId = route.params.id as string

const loading = ref(false)
const pushes = ref<Push[]>([])
const progress = reactive<ProgressInfo>({
  current_day: 0,
  total_days: 0,
  completed_days: 0,
  max_streak: 0,
  status: 'active',
})
const todayData = reactive<{ day_topic: string }>({ day_topic: '' })

const markingReadId = ref<number | null>(null)
const submittingSurvey = ref<number | null>(null)
const advancing = ref(false)
const challengeCompleted = ref(false)

// Survey responses keyed by pushId -> questionId -> value
const surveyResponses = reactive<Record<number, Record<string, any>>>({})

const headerTitle = computed(() => {
  if (challengeCompleted.value) return '挑战完成'
  if (todayData.day_topic) {
    return `第${progress.current_day}天 - ${todayData.day_topic}`
  }
  return `第${progress.current_day}天`
})

const dayProgressPercent = computed(() => {
  if (progress.total_days === 0) return 0
  return Math.min(100, Math.round((progress.current_day / progress.total_days) * 100))
})

const sortedPushes = computed(() => {
  return [...pushes.value].sort((a, b) => {
    const timeA = a.push_time || '00:00'
    const timeB = b.push_time || '00:00'
    return timeA.localeCompare(timeB)
  })
})

const canAdvance = computed(() => {
  if (pushes.value.length === 0) return false
  return pushes.value.every(p => p.is_read)
})

const advanceButtonText = computed(() => {
  if (progress.current_day >= progress.total_days) {
    return '完成挑战'
  }
  return '完成今天'
})

function pushTagColor(tag?: string): string {
  const map: Record<string, string> = {
    core: '#fa8c16',
    optional: '#52c41a',
    assessment: '#722ed1',
    info: '#1989fa',
  }
  return map[tag || ''] || '#999'
}

function pushTagLabel(tag?: string): string {
  const map: Record<string, string> = {
    core: '核心',
    optional: '可选',
    assessment: '评估',
    info: '说明',
  }
  return map[tag || ''] || tag || '推送'
}

function initSurveyResponses(pushList: Push[]) {
  for (const push of pushList) {
    if (push.survey && push.survey.questions && !surveyResponses[push.id]) {
      surveyResponses[push.id] = {}
      for (const q of push.survey.questions) {
        if (q.type === 'multi_choice') {
          surveyResponses[push.id][q.id] = []
        } else if (q.type === 'rating') {
          surveyResponses[push.id][q.id] = q.min || 0
        } else {
          surveyResponses[push.id][q.id] = ''
        }
      }
    }
    // Initialize expand state if not present
    if (!push._expandedSections) {
      push._expandedSections = []
    }
  }
}

async function loadToday() {
  loading.value = true
  try {
    const [todayRes, progressRes] = await Promise.all([
      api.get(`/v1/challenges/enrollments/${enrollmentId}/today`),
      api.get(`/v1/challenges/enrollments/${enrollmentId}/progress`),
    ])

    const todayPayload = todayRes as any
    const progressPayload = progressRes as any

    // Set progress info
    progress.current_day = progressPayload.current_day || 0
    progress.total_days = progressPayload.duration_days || progressPayload.total_days || 0
    progress.completed_days = progressPayload.completed_days || 0
    progress.max_streak = progressPayload.max_streak || 0
    progress.status = progressPayload.status || 'active'

    // Check if challenge is completed
    if (progress.status === 'completed') {
      challengeCompleted.value = true
      return
    }

    // Set today's data
    todayData.day_topic = todayPayload.day_topic || ''

    // Process pushes
    const rawPushes: any[] = todayPayload.pushes || todayPayload.items || []
    pushes.value = rawPushes.map((p: any) => ({
      id: p.push_id || p.id,
      push_time: p.push_time || p.time,
      tag: p.tag || p.type,
      management_content: p.management_content || p.content,
      behavior_guidance: p.behavior_guidance || p.guidance,
      survey: p.survey || null,
      is_read: p.is_read || p.status === 'read' || false,
      survey_submitted: p.survey_completed || p.survey_submitted || false,
      _expandedSections: [],
    }))

    initSurveyResponses(pushes.value)
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '加载失败'
    showToast(msg)
    pushes.value = []
  } finally {
    loading.value = false
  }
}

async function markRead(push: Push) {
  markingReadId.value = push.id
  try {
    await api.post(`/v1/challenges/enrollments/${enrollmentId}/read/${push.id}`)
    push.is_read = true
    showToast({ message: '已标记已读', position: 'bottom' })
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '操作失败'
    showToast(msg)
  } finally {
    markingReadId.value = null
  }
}

async function submitSurvey(push: Push) {
  if (!push.survey || push.survey_submitted) return

  const responses = surveyResponses[push.id]
  if (!responses) {
    showToast('请先填写问卷')
    return
  }

  // Validate that required questions have answers
  const hasEmptyRequired = push.survey.questions.some(q => {
    const val = responses[q.id]
    if (q.type === 'text') return !val || (val as string).trim() === ''
    if (q.type === 'multi_choice') return !val || (val as string[]).length === 0
    if (q.type === 'single_choice') return val === '' || val === undefined || val === null
    if (q.type === 'rating') return val === 0 || val === undefined || val === null
    return false
  })

  if (hasEmptyRequired) {
    showToast('请完成所有问题')
    return
  }

  submittingSurvey.value = push.id
  try {
    await api.post(
      `/v1/challenges/enrollments/${enrollmentId}/survey/${push.id}`,
      { responses }
    )
    push.survey_submitted = true
    showSuccessToast('提交成功')

    // Also mark as read automatically
    if (!push.is_read) {
      push.is_read = true
    }
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '提交失败'
    showToast(msg)
  } finally {
    submittingSurvey.value = null
  }
}

async function advanceDay() {
  if (!canAdvance.value) {
    showToast('请先查看所有推送内容')
    return
  }

  advancing.value = true
  try {
    const res: any = await api.post(`/v1/challenges/enrollments/${enrollmentId}/advance`)

    if (res.completed || res.status === 'completed') {
      challengeCompleted.value = true
      showSuccessToast('挑战完成!')
    } else {
      showSuccessToast('进入下一天!')
      // Reload today's data for the new day
      await loadToday()
    }
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '操作失败'
    showToast(msg)
  } finally {
    advancing.value = false
  }
}

// Watch route params in case navigating between enrollments
watch(
  () => route.params.id,
  (newId) => {
    if (newId) {
      challengeCompleted.value = false
      pushes.value = []
      loadToday()
    }
  }
)

onMounted(() => {
  loadToday()
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.loading {
  text-align: center;
  padding: 60px 0;
}

// Congratulations card
.congrats-card {
  text-align: center;
  padding: 40px $spacing-lg;

  .congrats-icon {
    font-size: 64px;
    margin-bottom: $spacing-md;
  }

  .congrats-title {
    font-size: 22px;
    font-weight: 700;
    color: $text-color;
    margin-bottom: $spacing-xs;
  }

  .congrats-desc {
    font-size: $font-size-md;
    color: $text-color-secondary;
    line-height: 1.6;
    margin-bottom: $spacing-lg;
  }

  .congrats-stats {
    display: flex;
    justify-content: space-around;
    margin-bottom: $spacing-lg;
    padding: $spacing-md 0;
    border-top: 1px solid #f0f0f0;
    border-bottom: 1px solid #f0f0f0;

    .stat-item {
      text-align: center;
    }

    .stat-value {
      font-size: 28px;
      font-weight: 700;
      color: #1989fa;
    }

    .stat-label {
      font-size: $font-size-sm;
      color: $text-color-secondary;
      margin-top: 4px;
    }
  }
}

// Day header
.day-header {
  .day-progress-bar {
    display: flex;
    align-items: center;
    gap: $spacing-sm;

    :deep(.van-progress) {
      flex: 1;
    }
  }

  .day-progress-text {
    font-size: $font-size-sm;
    color: $text-color-secondary;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .day-topic {
    font-size: $font-size-lg;
    font-weight: 600;
    color: $text-color;
    margin-top: $spacing-sm;
    line-height: 1.4;
  }
}

// Push timeline
.push-timeline {
  position: relative;
  padding-left: 4px;

  &::before {
    content: '';
    position: absolute;
    left: 20px;
    top: 24px;
    bottom: 24px;
    width: 2px;
    background: #e8e8e8;
  }
}

.push-card {
  position: relative;
  margin-left: 12px;
  margin-bottom: $spacing-sm;

  .push-top {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    margin-bottom: $spacing-sm;
  }

  .time-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 10px;
    background: #f7f8fa;
    border-radius: 16px;
    font-size: $font-size-sm;
    color: $text-color;
    font-weight: 500;
  }

  .read-indicator {
    margin-left: auto;
    display: flex;
    align-items: center;
  }

  .push-collapse {
    margin-bottom: $spacing-sm;

    :deep(.van-collapse-item) {
      margin-bottom: 0;
    }

    :deep(.van-collapse-item__title) {
      padding: 10px 0;
      font-size: $font-size-md;
    }

    :deep(.van-collapse-item__wrapper) {
      .van-collapse-item__content {
        padding: 0 0 $spacing-sm;
      }
    }

    :deep(.van-cell) {
      padding-left: 0;
      padding-right: 0;
    }

    :deep(.van-cell::after) {
      left: 0;
      right: 0;
    }
  }

  .content-block {
    font-size: $font-size-md;
    color: $text-color;
    line-height: 1.7;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .management-content {
    padding: $spacing-sm;
    background: #fffbe6;
    border-radius: $border-radius;
    border-left: 3px solid #faad14;
  }

  .behavior-content {
    padding: $spacing-sm;
    background: #f6ffed;
    border-radius: $border-radius;
    border-left: 3px solid #52c41a;
  }

  .push-bottom {
    display: flex;
    justify-content: flex-end;
    padding-top: $spacing-xs;
  }
}

// Survey section
.survey-section {
  margin-top: $spacing-sm;
  padding: $spacing-md;
  background: #f0f5ff;
  border-radius: $border-radius;
  border: 1px solid #d6e4ff;

  .survey-header {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: $font-size-md;
    font-weight: 600;
    color: #1989fa;
    margin-bottom: $spacing-sm;
  }

  .survey-body {
    margin-bottom: $spacing-md;
  }

  .survey-question {
    margin-bottom: $spacing-md;

    &:last-child {
      margin-bottom: 0;
    }
  }

  .question-label {
    font-size: $font-size-md;
    color: $text-color;
    font-weight: 500;
    margin-bottom: $spacing-xs;
    line-height: 1.5;
  }

  .rating-wrapper {
    padding: $spacing-xs 0;
  }

  .survey-textarea {
    border-radius: $border-radius;
    overflow: hidden;

    :deep(.van-field__body) {
      background: #fff;
      border-radius: $border-radius;
    }
  }

  .choice-group {
    padding: $spacing-xs 0;

    :deep(.van-radio),
    :deep(.van-checkbox) {
      padding: 6px 0;
    }

    :deep(.van-radio__label),
    :deep(.van-checkbox__label) {
      font-size: $font-size-md;
      color: $text-color;
    }
  }

  .survey-submit-btn {
    margin-top: $spacing-sm;
  }
}

// Advance section
.advance-section {
  padding: $spacing-md 0 $spacing-lg;

  .advance-hint {
    text-align: center;
    font-size: $font-size-sm;
    color: $text-color-placeholder;
    margin-top: $spacing-xs;
  }
}

:deep(.van-empty) {
  padding: 40px 0;
}
</style>
