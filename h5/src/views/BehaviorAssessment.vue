<template>
  <div class="page-container">
    <van-nav-bar
      :title="currentStep === 'result' ? '评估结果' : '行为状态评估'"
      left-arrow
      @click-left="handleBack"
    />

    <div class="page-content">
      <!-- 问卷模式 -->
      <template v-if="currentStep === 'questionnaire'">
        <!-- 教练推送信息 -->
        <div v-if="assignmentInfo" class="card" style="margin-bottom:12px;padding:12px;background:linear-gradient(135deg,#e6f7ff,#f0f5ff)">
          <div style="font-size:13px;color:#1890ff;font-weight:500">教练推送的评估</div>
          <div style="font-size:12px;color:#666;margin-top:4px">来自: {{ assignmentInfo.coach_name }}</div>
          <div v-if="assignmentInfo.note" style="font-size:12px;color:#666;margin-top:2px">备注: {{ assignmentInfo.note }}</div>
        </div>
        <!-- 自由组合模式 -->
        <template v-if="isCustomMode && customQuestions.length > 0">
          <div class="progress-section">
            <van-progress
              :percentage="Math.round((currentIndex + 1) / customQuestions.length * 100)"
              :show-pivot="false"
              color="#722ed1"
              track-color="#e8e8e8"
              stroke-width="6"
            />
            <div class="progress-text">{{ currentIndex + 1 }} / {{ customQuestions.length }}</div>
          </div>

          <div class="question-card card">
            <div class="question-group" style="color:#722ed1">教练自定义题目</div>
            <div class="question-text">{{ currentCustomQuestion?.text }}</div>

            <div class="options">
              <div
                v-for="opt in options"
                :key="opt.value"
                class="option-item"
                :class="{ selected: customAnswers[currentCustomQuestion?.id] === opt.value }"
                @click="selectCustomAnswer(opt.value)"
              >
                <div class="option-circle">{{ opt.value }}</div>
                <div class="option-label">{{ opt.label }}</div>
              </div>
            </div>
          </div>

          <div class="nav-buttons">
            <van-button
              v-if="currentIndex > 0"
              plain
              type="default"
              @click="currentIndex--"
            >上一题</van-button>
            <div v-else />
            <van-button
              v-if="currentIndex < customQuestions.length - 1"
              type="primary"
              :disabled="!customAnswers[currentCustomQuestion?.id]"
              @click="currentIndex++"
            >下一题</van-button>
            <van-button
              v-else
              type="primary"
              :loading="submitting"
              :disabled="!allCustomAnswered"
              @click="submitAssessment"
            >提交评估</van-button>
          </div>
        </template>

        <!-- 个别题目模式 -->
        <template v-else-if="isIndividualMode && individualQuestions.length > 0">
          <div class="progress-section">
            <van-progress
              :percentage="Math.round((currentIndex + 1) / individualQuestions.length * 100)"
              :show-pivot="false"
              color="#1989fa"
              track-color="#e8e8e8"
              stroke-width="6"
            />
            <div class="progress-text">{{ currentIndex + 1 }} / {{ individualQuestions.length }}</div>
          </div>

          <div class="question-card card">
            <div class="question-group">{{ currentIndividualQuestion?.questionnaire?.toUpperCase() }} · {{ currentIndividualQuestion?.dimension }}</div>
            <div class="question-text">{{ currentIndividualQuestion?.text }}</div>

            <div class="options">
              <div
                v-for="opt in individualOptions"
                :key="opt.value"
                class="option-item"
                :class="{ selected: individualAnswers[currentIndividualQuestion?.id] === opt.value }"
                @click="selectIndividualAnswer(opt.value)"
              >
                <div class="option-circle">{{ opt.value }}</div>
                <div class="option-label">{{ opt.label }}</div>
              </div>
            </div>
          </div>

          <div class="nav-buttons">
            <van-button
              v-if="currentIndex > 0"
              plain
              type="default"
              @click="currentIndex--"
            >上一题</van-button>
            <div v-else />
            <van-button
              v-if="currentIndex < individualQuestions.length - 1"
              type="primary"
              :disabled="!individualAnswers[currentIndividualQuestion?.id]"
              @click="currentIndex++"
            >下一题</van-button>
            <van-button
              v-else
              type="primary"
              :loading="submitting"
              :disabled="!allIndividualAnswered"
              @click="submitAssessment"
            >提交评估</van-button>
          </div>
        </template>

        <!-- 标准TTM7模式 -->
        <template v-else>
        <!-- 进度 -->
        <div class="progress-section">
          <van-progress
            :percentage="Math.round((currentIndex + 1) / questions.length * 100)"
            :show-pivot="false"
            color="#1989fa"
            track-color="#e8e8e8"
            stroke-width="6"
          />
          <div class="progress-text">{{ currentIndex + 1 }} / {{ questions.length }}</div>
        </div>

        <!-- 当前题目 -->
        <div class="question-card card">
          <div class="question-group">{{ currentQuestion.group }}</div>
          <div class="question-text">{{ currentQuestion.text }}</div>

          <div class="options">
            <div
              v-for="opt in options"
              :key="opt.value"
              class="option-item"
              :class="{ selected: answers[currentQuestion.id] === opt.value }"
              @click="selectAnswer(opt.value)"
            >
              <div class="option-circle">{{ opt.value }}</div>
              <div class="option-label">{{ opt.label }}</div>
            </div>
          </div>
        </div>

        <!-- 导航按钮 -->
        <div class="nav-buttons">
          <van-button
            v-if="currentIndex > 0"
            plain
            type="default"
            @click="currentIndex--"
          >上一题</van-button>
          <div v-else />
          <van-button
            v-if="currentIndex < questions.length - 1"
            type="primary"
            :disabled="!answers[currentQuestion.id]"
            @click="currentIndex++"
          >下一题</van-button>
          <van-button
            v-else
            type="primary"
            :loading="submitting"
            :disabled="!allAnswered"
            @click="submitAssessment"
          >提交评估</van-button>
        </div>
        </template>
      </template>

      <!-- 结果展示 (去诊断化) -->
      <template v-if="currentStep === 'result' && result">
        <div class="result-card card">
          <div class="result-stage-icon" :class="stageClass">
            {{ result.profile?.stage?.name || '评估中' }}
          </div>
          <h2 class="result-title">{{ result.profile?.stage?.description }}</h2>
        </div>

        <!-- 领域指引 -->
        <div class="card" v-if="result.intervention_plan?.domain_interventions?.length">
          <h3>为你推荐的改变方向</h3>
          <div
            v-for="di in result.intervention_plan.domain_interventions"
            :key="di.domain"
            class="domain-card"
          >
            <div class="domain-header">
              <van-icon :name="domainIcon(di.domain)" size="24" color="#1989fa" />
              <span class="domain-name">{{ di.domain_name }}</span>
            </div>
            <div class="domain-goal">{{ di.core_goal }}</div>
            <div class="domain-first-step" v-if="di.advice?.length">
              <span class="step-label">第一步: </span>
              {{ di.advice[0]?.title }}
            </div>
          </div>
        </div>

        <!-- 行动按钮 -->
        <div class="result-actions">
          <van-button type="primary" block round @click="$router.push('/my-stage')">
            查看我的行为状态
          </van-button>
          <van-button plain block round @click="$router.push('/')">
            返回首页
          </van-button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import api from '@/api/index'

const router = useRouter()
const route = useRoute()
const currentStep = ref<'questionnaire' | 'result'>('questionnaire')
const currentIndex = ref(0)
const submitting = ref(false)
const result = ref<any>(null)
const answers = ref<Record<string, number>>({})

// 教练推送的评估任务
const assignmentId = ref<number | null>(null)
const assignmentInfo = ref<any>(null)
const loadingAssignment = ref(false)

// 个别题目模式（高频题目）
const isIndividualMode = ref(false)
const individualQuestions = ref<any[]>([])
const individualAnswers = ref<Record<string, number>>({})

// 自由组合模式（教练自定义题目）
const isCustomMode = ref(false)
const customQuestions = ref<any[]>([])
const customAnswers = ref<Record<string, number>>({})

// TTM7 21 题 — 从后端加载，硬编码作为兜底
const FALLBACK_QUESTIONS = [
  { id: 'TTM01', group: '第1组', text: '我觉得我的生活方式没什么需要改变的' },
  { id: 'TTM02', group: '第1组', text: '我没有改变日常习惯的想法' },
  { id: 'TTM03', group: '第1组', text: '别人说我需要改变，但我不这样认为' },
  { id: 'TTM04', group: '第2组', text: '我知道有些习惯可能不好，但我不想改' },
  { id: 'TTM05', group: '第2组', text: '改变太难了，我还没准备好' },
  { id: 'TTM06', group: '第2组', text: '现在不是改变的好时机' },
  { id: 'TTM07', group: '第3组', text: '我开始意识到改变可能对我有好处' },
  { id: 'TTM08', group: '第3组', text: '我在考虑是不是该做些改变' },
  { id: 'TTM09', group: '第3组', text: '我偶尔会尝试一些改变，但没有坚持' },
  { id: 'TTM10', group: '第4组', text: '我打算在近期开始做一些改变' },
  { id: 'TTM11', group: '第4组', text: '我在为改变做准备，比如收集信息' },
  { id: 'TTM12', group: '第4组', text: '我已经有了一个初步的行动计划' },
  { id: 'TTM13', group: '第5组', text: '我已经开始改变一些具体的习惯了' },
  { id: 'TTM14', group: '第5组', text: '我正在积极尝试新的健康行为' },
  { id: 'TTM15', group: '第5组', text: '虽然有困难，但我在坚持新习惯' },
  { id: 'TTM16', group: '第6组', text: '新的健康习惯已经成为我日常的一部分' },
  { id: 'TTM17', group: '第6组', text: '我已经坚持改变超过一个月了' },
  { id: 'TTM18', group: '第6组', text: '即使遇到困难，我也能继续保持好习惯' },
  { id: 'TTM19', group: '第7组', text: '健康的生活方式对我来说已经很自然' },
  { id: 'TTM20', group: '第7组', text: '我不再需要刻意提醒自己保持好习惯' },
  { id: 'TTM21', group: '第7组', text: '我经常帮助身边的人也开始改变' },
]
const questions = ref(FALLBACK_QUESTIONS)

const options = [
  { value: 1, label: '完全不符合' },
  { value: 2, label: '比较不符合' },
  { value: 3, label: '不确定' },
  { value: 4, label: '比较符合' },
  { value: 5, label: '非常符合' },
]

const currentQuestion = computed(() => questions.value[currentIndex.value])
const allAnswered = computed(() => questions.value.every(q => answers.value[q.id]))

const currentIndividualQuestion = computed(() => individualQuestions.value[currentIndex.value])
const allIndividualAnswered = computed(() => individualQuestions.value.every(q => individualAnswers.value[q.id]))
const individualOptions = computed(() => {
  if (!currentIndividualQuestion.value) return options
  const q = currentIndividualQuestion.value
  if (q.scale_labels && Object.keys(q.scale_labels).length > 0) {
    return Object.entries(q.scale_labels).map(([k, v]) => ({
      value: Number(k),
      label: v as string,
    })).sort((a, b) => a.value - b.value)
  }
  return options
})

const currentCustomQuestion = computed(() => customQuestions.value[currentIndex.value])
const allCustomAnswered = computed(() => customQuestions.value.every(q => customAnswers.value[q.id]))

const stageClass = computed(() => {
  const stage = result.value?.profile?.stage?.current
  if (!stage) return 'stage-default'
  const idx = parseInt(stage[1])
  if (idx <= 1) return 'stage-early'
  if (idx <= 3) return 'stage-mid'
  return 'stage-late'
})

function selectAnswer(value: number) {
  answers.value[currentQuestion.value.id] = value
  // 自动前进到下一题
  if (currentIndex.value < questions.value.length - 1) {
    setTimeout(() => currentIndex.value++, 200)
  }
}

function selectIndividualAnswer(value: number) {
  individualAnswers.value[currentIndividualQuestion.value.id] = value
  if (currentIndex.value < individualQuestions.value.length - 1) {
    setTimeout(() => currentIndex.value++, 200)
  }
}

function selectCustomAnswer(value: number) {
  customAnswers.value[currentCustomQuestion.value.id] = value
  if (currentIndex.value < customQuestions.value.length - 1) {
    setTimeout(() => currentIndex.value++, 200)
  }
}

function handleBack() {
  if (currentStep.value === 'result') {
    currentStep.value = 'questionnaire'
  } else if (currentIndex.value > 0) {
    currentIndex.value--
  } else {
    router.back()
  }
}

function domainIcon(domain: string) {
  const icons: Record<string, string> = {
    nutrition: 'coupon-o',
    exercise: 'fire-o',
    sleep: 'clock-o',
    emotion: 'smile-o',
    stress: 'warning-o',
    cognitive: 'bulb-o',
    social: 'friends-o',
    tcm: 'flower-o',
  }
  return icons[domain] || 'info-o'
}

async function submitAssessment() {
  submitting.value = true
  try {
    if (assignmentId.value) {
      const body: any = {}
      if (isCustomMode.value) {
        body.custom_answers = customAnswers.value
      } else if (isIndividualMode.value) {
        body.individual_answers = individualAnswers.value
      } else {
        if (!allAnswered.value) {
          showToast('请完成所有题目')
          submitting.value = false
          return
        }
        body.ttm7 = answers.value
      }
      const res = await api.post(`/api/v1/assessment-assignments/${assignmentId.value}/submit`, body)
      result.value = res.pipeline_result || res
      showToast('评估已提交，等待教练审核')
    } else {
      if (!allAnswered.value) {
        showToast('请完成所有题目')
        submitting.value = false
        return
      }
      const res = await api.post('/api/v1/assessment/evaluate', {
        ttm7: answers.value,
      })
      result.value = res
    }
    currentStep.value = 'result'
  } catch (e: any) {
    showToast(e.response?.data?.detail || '评估提交失败')
  } finally {
    submitting.value = false
  }
}

// 加载教练推送的评估任务详情
onMounted(async () => {
  // 尝试从后端加载 TTM7 题目（支持后台管理）
  try {
    const qRes: any = await api.get('/api/v1/assessment/ttm7-questions')
    if (qRes.questions?.length) {
      questions.value = qRes.questions
    }
  } catch { /* 使用内置题目 */ }
  const aid = route.query.assignment_id
  if (aid) {
    assignmentId.value = Number(aid)
    loadingAssignment.value = true
    try {
      const res: any = await api.get('/api/v1/assessment-assignments/my-pending')
      const found = (res.assignments || []).find((a: any) => a.id === assignmentId.value)
      if (found) {
        assignmentInfo.value = found
        // 检查推送模式
        const scales = found.scales
        if (typeof scales === 'object' && !Array.isArray(scales)) {
          const cqs = scales.custom_questions || []
          if (cqs.length > 0) {
            // 自由组合模式
            isCustomMode.value = true
            customQuestions.value = cqs
          } else {
            const preset = scales.question_preset
            const qids = scales.question_ids || []
            if (preset || qids.length > 0) {
              isIndividualMode.value = true
              try {
                if (preset) {
                  const qRes: any = await api.get(`/api/v1/high-freq-questions/${preset}`)
                  individualQuestions.value = qRes.items || qRes || []
                } else if (qids.length > 0) {
                  const params = qids.map((id: string) => `ids=${encodeURIComponent(id)}`).join('&')
                  const qRes: any = await api.get(`/api/v1/high-freq-questions/by-ids?${params}`)
                  individualQuestions.value = qRes.questions || qRes || []
                }
              } catch { /* ignore */ }
            }
          }
        }
      }
    } catch { /* ignore */ }
    finally { loadingAssignment.value = false }
  }
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.progress-section {
  margin-bottom: $spacing-md;

  .progress-text {
    text-align: center;
    font-size: $font-size-sm;
    color: $text-color-secondary;
    margin-top: $spacing-xs;
  }
}

.question-card {
  min-height: 280px;
  display: flex;
  flex-direction: column;

  .question-group {
    font-size: $font-size-xs;
    color: #1989fa;
    margin-bottom: $spacing-xs;
  }

  .question-text {
    font-size: 18px;
    font-weight: 600;
    line-height: 1.5;
    margin-bottom: $spacing-lg;
  }

  .options {
    display: flex;
    flex-direction: column;
    gap: $spacing-sm;
  }

  .option-item {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    padding: 12px $spacing-md;
    border: 1px solid #e8e8e8;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;

    &.selected {
      border-color: #1989fa;
      background: rgba(25, 137, 250, 0.08);
    }
  }

  .option-circle {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    border: 2px solid #d9d9d9;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: $font-size-sm;
    color: #999;
    flex-shrink: 0;

    .selected & {
      border-color: #1989fa;
      background: #1989fa;
      color: #fff;
    }
  }

  .option-label {
    font-size: $font-size-md;
  }
}

.nav-buttons {
  display: flex;
  justify-content: space-between;
  margin-top: $spacing-md;
}

// 结果页
.result-card {
  text-align: center;
  padding: $spacing-lg;

  .result-stage-icon {
    display: inline-block;
    padding: 12px 24px;
    border-radius: 20px;
    font-size: 20px;
    font-weight: 700;
    color: #fff;
    margin-bottom: $spacing-md;
  }

  .stage-early { background: linear-gradient(135deg, #ff9a9e, #fad0c4); }
  .stage-mid { background: linear-gradient(135deg, #ffecd2, #fcb69f); color: #8b4513; }
  .stage-late { background: linear-gradient(135deg, #a1c4fd, #c2e9fb); color: #1a237e; }
  .stage-default { background: #bbb; }

  .result-title {
    font-size: 16px;
    color: $text-color;
    line-height: 1.6;
  }
}

.domain-card {
  padding: $spacing-md;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  margin-bottom: $spacing-sm;

  .domain-header {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    margin-bottom: $spacing-xs;
  }

  .domain-name {
    font-size: $font-size-md;
    font-weight: 600;
  }

  .domain-goal {
    font-size: $font-size-sm;
    color: $text-color-secondary;
    margin-bottom: $spacing-xs;
  }

  .domain-first-step {
    font-size: $font-size-sm;
    background: #f6ffed;
    padding: 8px 12px;
    border-radius: 6px;
    border-left: 3px solid #52c41a;

    .step-label {
      color: #52c41a;
      font-weight: 600;
    }
  }
}

.result-actions {
  margin-top: $spacing-lg;
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
}
</style>
