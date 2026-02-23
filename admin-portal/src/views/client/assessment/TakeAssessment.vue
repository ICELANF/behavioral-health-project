<template>
  <div class="take-assessment">
    <div class="assessment-header">
      <button class="back-btn" @click="confirmExit">← 退出</button>
      <h2>{{ questionnaire.name }}</h2>
      <span class="progress-text">{{ currentIndex + 1 }} / {{ questionnaire.questions.length }}</span>
    </div>

    <!-- Progress bar -->
    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
    </div>

    <!-- Question -->
    <div class="question-area">
      <div class="question-number">第 {{ currentIndex + 1 }} 题</div>
      <p class="question-text">{{ currentQuestion.text }}</p>

      <!-- Single / Multiple choice -->
      <div v-if="currentQuestion.type === 'single' || currentQuestion.type === 'multiple'" class="options-list">
        <div
          v-for="(opt, i) in currentQuestion.options"
          :key="i"
          class="option-item"
          :class="{ selected: isSelected(i), hovered: hoveredOption === i }"
          @click="selectOption(i)"
          @mouseenter="hoveredOption = i"
          @mouseleave="hoveredOption = -1"
        >
          <span class="option-index">{{ String.fromCharCode(65 + i) }}</span>
          <span class="option-text">{{ opt.text }}</span>
          <span v-if="currentQuestion.type === 'single' && opt.score !== undefined" class="option-score">{{ opt.score }}分</span>
        </div>
      </div>

      <!-- Scale (0-N) -->
      <div v-if="currentQuestion.type === 'scale'" class="scale-options">
        <div class="scale-labels">
          <span>{{ currentQuestion.minLabel }}</span>
          <span>{{ currentQuestion.maxLabel }}</span>
        </div>
        <div class="scale-buttons">
          <button
            v-for="n in (currentQuestion.maxValue + 1)"
            :key="n - 1"
            class="scale-btn"
            :class="{ selected: answers[currentIndex] === (n - 1) }"
            @click="answers[currentIndex] = n - 1"
          >{{ n - 1 }}</button>
        </div>
      </div>
    </div>

    <!-- Navigation -->
    <div class="nav-actions">
      <button class="nav-btn" :disabled="currentIndex === 0" @click="currentIndex--">上一题</button>
      <button class="nav-btn draft" @click="saveDraft">暂存草稿</button>
      <button v-if="currentIndex < questionnaire.questions.length - 1" class="nav-btn primary" :disabled="answers[currentIndex] === null" @click="currentIndex++">下一题</button>
      <button v-else class="nav-btn primary" :disabled="!allAnswered || submitting" @click="submitAssessment">
        {{ submitting ? '提交中...' : '提交' }}
      </button>
    </div>

    <!-- Question dots -->
    <div class="question-dots">
      <button
        v-for="(q, i) in questionnaire.questions"
        :key="i"
        class="dot"
        :class="{ current: i === currentIndex, answered: answers[i] !== null }"
        @click="currentIndex = i"
      >{{ i + 1 }}</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import request from '@/api/request'

const route = useRoute()
const router = useRouter()
const assessmentId = route.params.id as string
const submitting = ref(false)

// Questionnaire definitions
const questionnaires: Record<string, any> = {
  phq9: {
    name: 'PHQ-9 抑郁筛查问卷',
    questions: [
      { text: '做事时提不起劲或没有兴趣', type: 'single', options: [{ text: '完全不会', score: 0 }, { text: '好几天', score: 1 }, { text: '一半以上的天数', score: 2 }, { text: '几乎每天', score: 3 }] },
      { text: '感到心情低落、沮丧或绝望', type: 'single', options: [{ text: '完全不会', score: 0 }, { text: '好几天', score: 1 }, { text: '一半以上的天数', score: 2 }, { text: '几乎每天', score: 3 }] },
      { text: '入睡困难、睡不安稳或睡眠过多', type: 'single', options: [{ text: '完全不会', score: 0 }, { text: '好几天', score: 1 }, { text: '一半以上的天数', score: 2 }, { text: '几乎每天', score: 3 }] },
      { text: '感觉疲倦或没有活力', type: 'single', options: [{ text: '完全不会', score: 0 }, { text: '好几天', score: 1 }, { text: '一半以上的天数', score: 2 }, { text: '几乎每天', score: 3 }] },
      { text: '食欲不振或吃太多', type: 'single', options: [{ text: '完全不会', score: 0 }, { text: '好几天', score: 1 }, { text: '一半以上的天数', score: 2 }, { text: '几乎每天', score: 3 }] },
      { text: '觉得自己很糟——或觉得自己很失败', type: 'single', options: [{ text: '完全不会', score: 0 }, { text: '好几天', score: 1 }, { text: '一半以上的天数', score: 2 }, { text: '几乎每天', score: 3 }] },
      { text: '对事物专注有困难', type: 'single', options: [{ text: '完全不会', score: 0 }, { text: '好几天', score: 1 }, { text: '一半以上的天数', score: 2 }, { text: '几乎每天', score: 3 }] },
      { text: '动作或说话缓慢到别人注意到——或相反', type: 'single', options: [{ text: '完全不会', score: 0 }, { text: '好几天', score: 1 }, { text: '一半以上的天数', score: 2 }, { text: '几乎每天', score: 3 }] },
      { text: '有不如死掉或用某种方式伤害自己的念头', type: 'single', options: [{ text: '完全不会', score: 0 }, { text: '好几天', score: 1 }, { text: '一半以上的天数', score: 2 }, { text: '几乎每天', score: 3 }] },
    ]
  },
  gad7: {
    name: 'GAD-7 焦虑评估',
    questions: [
      { text: '感觉紧张、不安或急躁', type: 'single', options: [{ text: '完全不会', score: 0 }, { text: '好几天', score: 1 }, { text: '一半以上的天数', score: 2 }, { text: '几乎每天', score: 3 }] },
      { text: '不能够停止或控制担忧', type: 'single', options: [{ text: '完全不会', score: 0 }, { text: '好几天', score: 1 }, { text: '一半以上的天数', score: 2 }, { text: '几乎每天', score: 3 }] },
      { text: '对各种各样的事情担忧过多', type: 'single', options: [{ text: '完全不会', score: 0 }, { text: '好几天', score: 1 }, { text: '一半以上的天数', score: 2 }, { text: '几乎每天', score: 3 }] },
      { text: '很难放松下来', type: 'single', options: [{ text: '完全不会', score: 0 }, { text: '好几天', score: 1 }, { text: '一半以上的天数', score: 2 }, { text: '几乎每天', score: 3 }] },
      { text: '由于不安而无法静坐', type: 'single', options: [{ text: '完全不会', score: 0 }, { text: '好几天', score: 1 }, { text: '一半以上的天数', score: 2 }, { text: '几乎每天', score: 3 }] },
      { text: '变得容易烦恼或急躁', type: 'single', options: [{ text: '完全不会', score: 0 }, { text: '好几天', score: 1 }, { text: '一半以上的天数', score: 2 }, { text: '几乎每天', score: 3 }] },
      { text: '感到似乎将有可怕的事情发生而害怕', type: 'single', options: [{ text: '完全不会', score: 0 }, { text: '好几天', score: 1 }, { text: '一半以上的天数', score: 2 }, { text: '几乎每天', score: 3 }] },
    ]
  },
  pss10: {
    name: 'PSS-10 压力感知量表',
    questions: Array.from({ length: 10 }, (_, i) => ({
      text: ['被意外发生的事情打扰', '感觉无法控制生活中重要的事', '感到紧张和压力', '成功处理日常烦恼', '感觉有效应对了重要变化', '对处理私人问题没有信心', '感觉事情顺利发展', '发现自己无法处理该做的事', '能够控制生活中的烦恼', '感觉掌控一切'][i],
      type: 'scale', minLabel: '从不', maxLabel: '总是', maxValue: 4,
    }))
  },
}

const defaultQ = {
  name: '通用测评',
  questions: [
    { text: '您目前的整体健康状况如何？', type: 'scale', minLabel: '很差', maxLabel: '很好', maxValue: 10 },
    { text: '您对目前生活满意吗？', type: 'scale', minLabel: '非常不满意', maxLabel: '非常满意', maxValue: 10 },
    { text: '您最近一周的压力水平？', type: 'scale', minLabel: '没有压力', maxLabel: '压力极大', maxValue: 10 },
  ]
}

const questionnaire = ref(questionnaires[assessmentId] || defaultQ)
const currentIndex = ref(0)
const answers = ref<(number | number[] | null)[]>(questionnaire.value.questions.map(() => null))
const hoveredOption = ref(-1)

const currentQuestion = computed(() => questionnaire.value.questions[currentIndex.value])
const progressPercent = computed(() => ((currentIndex.value + 1) / questionnaire.value.questions.length) * 100)
const allAnswered = computed(() => answers.value.every((a: any) => a !== null))

const isSelected = (optionIndex: number) => {
  const answer = answers.value[currentIndex.value]
  if (Array.isArray(answer)) return answer.includes(optionIndex)
  return answer === optionIndex
}

const selectOption = (optionIndex: number) => {
  const q = currentQuestion.value
  if (q.type === 'multiple') {
    let current = answers.value[currentIndex.value] || []
    if (!Array.isArray(current)) current = []
    const idx = (current as number[]).indexOf(optionIndex)
    if (idx > -1) (current as number[]).splice(idx, 1)
    else (current as number[]).push(optionIndex)
    answers.value[currentIndex.value] = [...(current as number[])]
  } else {
    answers.value[currentIndex.value] = optionIndex
  }
}

const saveDraft = () => {
  localStorage.setItem(`assessment_draft_${assessmentId}`, JSON.stringify({ answers: answers.value, currentIndex: currentIndex.value }))
  message.success('草稿已保存')
}

const submitAssessment = async () => {
  // Calculate score locally
  let totalScore = 0
  questionnaire.value.questions.forEach((q: any, i: number) => {
    if (q.type === 'single' && q.options) {
      totalScore += q.options[answers.value[i] as number]?.score || 0
    } else if (q.type === 'scale') {
      totalScore += (answers.value[i] as number) || 0
    }
  })

  submitting.value = true
  try {
    // Submit to backend API
    const { data } = await request.post('/assessment/submit', {
      text_content: `${questionnaire.value.name} 评估结果：总分 ${totalScore}`,
      questionnaire_type: assessmentId,
      answers: answers.value,
      total_score: totalScore,
    })

    // Store result for the result page
    localStorage.setItem(`assessment_result_${assessmentId}`, JSON.stringify({
      score: totalScore,
      answers: answers.value,
      date: new Date().toISOString(),
      questionnaireName: questionnaire.value.name,
      assessment_id: data.assessment_id,
      risk_level: data.risk_level,
      risk_score: data.risk_score,
    }))
    localStorage.removeItem(`assessment_draft_${assessmentId}`)
    router.push(`/client/assessment/result/${assessmentId}`)
  } catch (e: any) {
    console.error('提交评估失败:', e)
    // Fallback: store locally and navigate
    localStorage.setItem(`assessment_result_${assessmentId}`, JSON.stringify({
      score: totalScore,
      answers: answers.value,
      date: new Date().toISOString(),
      questionnaireName: questionnaire.value.name,
    }))
    localStorage.removeItem(`assessment_draft_${assessmentId}`)
    router.push(`/client/assessment/result/${assessmentId}`)
  } finally {
    submitting.value = false
  }
}

const confirmExit = () => {
  if (answers.value.some((a: any) => a !== null)) {
    if (confirm('测评进行中，确定退出吗？可先暂存草稿。')) {
      router.back()
    }
  } else {
    router.back()
  }
}

// Load draft
const draft = localStorage.getItem(`assessment_draft_${assessmentId}`)
if (draft) {
  try {
    const d = JSON.parse(draft)
    if (d.answers) answers.value = d.answers
    if (d.currentIndex != null) currentIndex.value = d.currentIndex
  } catch (e) { /* ignore */ }
}
</script>

<style scoped>
.take-assessment { max-width: 600px; margin: 0 auto; padding: 16px; min-height: 100vh; display: flex; flex-direction: column; }
.assessment-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.assessment-header h2 { flex: 1; margin: 0; font-size: 16px; }
.back-btn { padding: 6px 12px; border: 1px solid #d9d9d9; border-radius: 6px; background: #fff; cursor: pointer; font-size: 13px; }
.progress-text { font-size: 13px; color: #999; }

.progress-bar { height: 4px; background: #f0f0f0; border-radius: 2px; margin-bottom: 20px; }
.progress-fill { height: 100%; background: #1890ff; border-radius: 2px; transition: width 0.3s; }

.question-area { flex: 1; }
.question-number { font-size: 12px; color: #1890ff; font-weight: 600; margin-bottom: 8px; }
.question-text { font-size: 16px; color: #333; font-weight: 500; margin-bottom: 20px; line-height: 1.5; }

.options-list { display: flex; flex-direction: column; gap: 8px; }
.option-item { display: flex; align-items: center; gap: 12px; padding: 14px; border: 2px solid #f0f0f0; border-radius: 10px; cursor: pointer; transition: all 0.2s; }
.option-item.hovered { border-color: #91d5ff; background: #f0f8ff; }
.option-item.selected { border-color: #1890ff; background: #e6f7ff; }
.option-index { width: 28px; height: 28px; border: 2px solid #d9d9d9; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 600; color: #999; flex-shrink: 0; }
.option-item.selected .option-index { background: #1890ff; color: #fff; border-color: #1890ff; }
.option-text { flex: 1; font-size: 14px; color: #333; }
.option-score { font-size: 12px; color: #999; }

.scale-options { margin-top: 8px; }
.scale-labels { display: flex; justify-content: space-between; font-size: 12px; color: #999; margin-bottom: 12px; }
.scale-buttons { display: flex; gap: 6px; flex-wrap: wrap; justify-content: center; }
.scale-btn { width: 44px; height: 44px; border: 2px solid #d9d9d9; border-radius: 50%; background: #fff; cursor: pointer; font-size: 14px; font-weight: 600; color: #666; transition: all 0.2s; }
.scale-btn:hover { border-color: #1890ff; color: #1890ff; }
.scale-btn.selected { background: #1890ff; color: #fff; border-color: #1890ff; }

.nav-actions { display: flex; gap: 8px; margin-top: 24px; }
.nav-btn { flex: 1; padding: 10px; border: 1px solid #d9d9d9; border-radius: 8px; background: #fff; cursor: pointer; font-size: 14px; }
.nav-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.nav-btn.primary { background: #1890ff; color: #fff; border-color: #1890ff; }
.nav-btn.draft { color: #999; }

.question-dots { display: flex; gap: 4px; justify-content: center; margin-top: 16px; flex-wrap: wrap; }
.dot { width: 28px; height: 28px; border-radius: 50%; border: 1px solid #d9d9d9; background: #fff; font-size: 11px; cursor: pointer; color: #999; display: flex; align-items: center; justify-content: center; }
.dot.answered { background: #e6f7ff; border-color: #91d5ff; color: #1890ff; }
.dot.current { background: #1890ff; border-color: #1890ff; color: #fff; }
</style>
