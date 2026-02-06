<template>
  <div class="dynamic-tool-wrapper stress-form">
    <div class="tool-header">
      <span class="tool-icon">📋</span>
      <span class="tool-title">压力快速测评</span>
      <span v-if="type" class="tool-type">{{ type }}</span>
    </div>

    <!-- 未开始状态 -->
    <template v-if="phase === 'intro'">
      <div class="tool-body">
        <p class="tool-desc">请引导学员完成以下压力筛查评估（共 {{ questions.length }} 题）：</p>
        <div v-for="(q, i) in questions" :key="i" class="question-item">
          <span class="q-num">Q{{ i + 1 }}</span>
          <span class="q-text">{{ q.text }}</span>
        </div>
        <div v-if="limitTime" class="time-limit">
          限时: {{ Math.floor(limitTime / 60) }} 分钟
        </div>
      </div>
      <div class="tool-actions">
        <button class="tool-btn primary" @click="startAssessment">开始测评</button>
        <button class="tool-btn" @click="$emit('action', { tool: 'stress_form', action: 'skip' })">跳过</button>
      </div>
    </template>

    <!-- 测评进行中 -->
    <template v-if="phase === 'testing'">
      <div class="tool-body">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
        </div>
        <p class="progress-text">{{ currentIndex + 1 }} / {{ questions.length }}</p>

        <div class="question-card">
          <p class="question-text">{{ currentQuestion.text }}</p>
          <div class="slider-wrapper">
            <div class="slider-labels">
              <span>{{ currentQuestion.minLabel }}</span>
              <span>{{ currentQuestion.maxLabel }}</span>
            </div>
            <input
              type="range"
              :min="0"
              :max="10"
              :value="answers[currentIndex]"
              class="score-slider"
              @input="updateAnswer($event)"
            />
            <div class="score-display">
              <span class="score-value" :style="{ color: scoreColor(answers[currentIndex]) }">
                {{ answers[currentIndex] }}
              </span>
              <span class="score-label">/ 10</span>
            </div>
          </div>
        </div>

        <div v-if="limitTime" class="timer">
          <span class="timer-icon">⏱</span>
          <span :class="{ 'timer-warn': remainingTime < 60 }">{{ formatTime(remainingTime) }}</span>
        </div>
      </div>
      <div class="tool-actions">
        <button class="tool-btn" :disabled="currentIndex === 0" @click="prevQuestion">上一题</button>
        <button v-if="currentIndex < questions.length - 1" class="tool-btn primary" @click="nextQuestion">下一题</button>
        <button v-else class="tool-btn primary" @click="submitAssessment">提交</button>
      </div>
    </template>

    <!-- 结果展示 -->
    <template v-if="phase === 'result'">
      <div class="tool-body">
        <div class="result-card" :class="'risk-' + riskLevel">
          <div class="result-score">
            <span class="total-score">{{ totalScore }}</span>
            <span class="max-score">/ {{ questions.length * 10 }}</span>
          </div>
          <div class="risk-badge" :class="'risk-' + riskLevel">
            {{ riskLabels[riskLevel] }}
          </div>
          <p class="risk-desc">{{ riskDescriptions[riskLevel] }}</p>
        </div>

        <div class="detail-section">
          <p class="detail-title">各项得分：</p>
          <div v-for="(q, i) in questions" :key="i" class="detail-item">
            <span class="detail-label">{{ q.short }}</span>
            <div class="detail-bar-wrapper">
              <div class="detail-bar" :style="{ width: (answers[i] / 10 * 100) + '%', background: scoreColor(answers[i]) }"></div>
            </div>
            <span class="detail-score" :style="{ color: scoreColor(answers[i]) }">{{ answers[i] }}</span>
          </div>
        </div>

        <div class="suggestion-section">
          <p class="detail-title">建议干预方向：</p>
          <ul class="suggestion-list">
            <li v-for="(s, i) in suggestions" :key="i">{{ s }}</li>
          </ul>
        </div>
      </div>
      <div class="tool-actions">
        <button class="tool-btn primary" @click="handleSubmitResult">保存并通知教练</button>
        <button class="tool-btn" @click="resetAssessment">重新测评</button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'

const props = defineProps({
  type: { type: String, default: 'quick_check' },
  limitTime: { type: Number, default: 300 },
})
const emit = defineEmits(['action'])

const questions = [
  { text: '过去一周，你感到情绪低落或烦躁的频率是？', short: '情绪低落', minLabel: '从不', maxLabel: '每天' },
  { text: '你是否经常用进食来缓解压力？', short: '压力进食', minLabel: '从不', maxLabel: '总是' },
  { text: '最近是否有影响心情的重大事件？', short: '重大事件', minLabel: '没有', maxLabel: '非常严重' },
  { text: '你是否感到睡眠质量下降（入睡困难/早醒）？', short: '睡眠质量', minLabel: '无影响', maxLabel: '严重失眠' },
  { text: '你对日常活动是否失去兴趣或乐趣？', short: '兴趣丧失', minLabel: '没有', maxLabel: '完全丧失' },
  { text: '你是否经常感到疲劳或精力不足？', short: '疲劳感', minLabel: '精力充沛', maxLabel: '极度疲劳' },
  { text: '你是否出现注意力难以集中的情况？', short: '注意力', minLabel: '集中', maxLabel: '无法集中' },
  { text: '你是否感到自己没有价值或对自己失望？', short: '自我价值', minLabel: '自信', maxLabel: '非常失望' },
]

const phase = ref('intro')
const currentIndex = ref(0)
const answers = ref(questions.map(() => 5))
const remainingTime = ref(props.limitTime)
let timer = null

const currentQuestion = computed(() => questions[currentIndex.value])
const progressPercent = computed(() => ((currentIndex.value + 1) / questions.length) * 100)
const totalScore = computed(() => answers.value.reduce((sum, v) => sum + v, 0))

const riskLevel = computed(() => {
  const avg = totalScore.value / questions.length
  if (avg >= 7) return 'high'
  if (avg >= 4) return 'medium'
  return 'low'
})

const riskLabels = { high: '高风险', medium: '中等风险', low: '低风险' }
const riskDescriptions = {
  high: '压力水平较高，建议立即安排专业心理评估和干预，密切关注情绪变化。',
  medium: '存在一定压力，建议增加放松训练和社会支持，定期复评。',
  low: '压力在可控范围内，建议保持良好的生活习惯和社交活动。',
}

const suggestions = computed(() => {
  const s = []
  if (answers.value[0] >= 6) s.push('情绪调节训练（正念/冥想）')
  if (answers.value[1] >= 6) s.push('饮食行为干预与压力管理替代策略')
  if (answers.value[2] >= 6) s.push('危机事件心理疏导')
  if (answers.value[3] >= 6) s.push('睡眠卫生教育与认知行为治疗')
  if (answers.value[4] >= 6) s.push('行为激活干预')
  if (answers.value[5] >= 6) s.push('精力管理与运动处方')
  if (answers.value[6] >= 6) s.push('注意力训练与环境调整')
  if (answers.value[7] >= 6) s.push('认知重建与自我肯定训练')
  if (s.length === 0) s.push('维持当前良好状态，定期复评')
  return s
})

const scoreColor = (val) => {
  if (val >= 7) return '#dc2626'
  if (val >= 4) return '#f59e0b'
  return '#16a34a'
}

const formatTime = (seconds) => {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

const startAssessment = () => {
  phase.value = 'testing'
  currentIndex.value = 0
  answers.value = questions.map(() => 5)
  remainingTime.value = props.limitTime
  emit('action', { tool: 'stress_form', action: 'start' })
  if (props.limitTime) {
    timer = setInterval(() => {
      remainingTime.value--
      if (remainingTime.value <= 0) {
        clearInterval(timer)
        submitAssessment()
      }
    }, 1000)
  }
}

const updateAnswer = (e) => {
  answers.value[currentIndex.value] = parseInt(e.target.value)
}

const prevQuestion = () => { if (currentIndex.value > 0) currentIndex.value-- }
const nextQuestion = () => { if (currentIndex.value < questions.length - 1) currentIndex.value++ }

const submitAssessment = () => {
  if (timer) clearInterval(timer)
  phase.value = 'result'
}

const handleSubmitResult = () => {
  emit('action', {
    tool: 'stress_form',
    action: 'submit',
    data: {
      answers: answers.value,
      totalScore: totalScore.value,
      riskLevel: riskLevel.value,
      suggestions: suggestions.value,
      timestamp: new Date().toISOString(),
    }
  })
}

const resetAssessment = () => {
  phase.value = 'intro'
  currentIndex.value = 0
  answers.value = questions.map(() => 5)
}

onBeforeUnmount(() => { if (timer) clearInterval(timer) })
</script>

<style scoped>
.stress-form { background: #fff5f5; border: 1px solid #fecaca; border-radius: 8px; padding: 12px; }
.tool-header { display: flex; align-items: center; gap: 6px; margin-bottom: 8px; }
.tool-icon { font-size: 16px; }
.tool-title { font-weight: 600; font-size: 13px; color: #dc2626; }
.tool-type { font-size: 11px; background: #fee2e2; color: #b91c1c; padding: 1px 6px; border-radius: 4px; }
.tool-body { font-size: 12px; color: #666; }
.tool-desc { margin-bottom: 6px; }
.question-item { display: flex; gap: 6px; padding: 4px 0; border-bottom: 1px dashed #fecaca; }
.q-num { font-weight: 600; color: #dc2626; min-width: 24px; }
.q-text { color: #444; }
.time-limit { margin-top: 8px; font-size: 11px; color: #b91c1c; }
.tool-actions { display: flex; gap: 8px; margin-top: 10px; }
.tool-btn { font-size: 12px; padding: 4px 12px; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; background: #fff; }
.tool-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.tool-btn.primary { background: #dc2626; color: #fff; border-color: #dc2626; }

.progress-bar { height: 4px; background: #fecaca; border-radius: 2px; overflow: hidden; margin-bottom: 4px; }
.progress-fill { height: 100%; background: #dc2626; transition: width 0.3s; }
.progress-text { text-align: center; font-size: 11px; color: #999; margin-bottom: 8px; }

.question-card { background: #fff; border-radius: 6px; padding: 12px; border: 1px solid #fecaca; }
.question-text { font-size: 13px; color: #333; font-weight: 500; margin-bottom: 12px; }
.slider-wrapper { margin-top: 8px; }
.slider-labels { display: flex; justify-content: space-between; font-size: 11px; color: #999; margin-bottom: 4px; }
.score-slider { width: 100%; accent-color: #dc2626; cursor: pointer; }
.score-display { text-align: center; margin-top: 4px; }
.score-value { font-size: 24px; font-weight: 700; }
.score-label { font-size: 12px; color: #999; }

.timer { text-align: center; margin-top: 8px; font-size: 12px; color: #666; }
.timer-icon { margin-right: 4px; }
.timer-warn { color: #dc2626; font-weight: 600; }

.result-card { background: #fff; border-radius: 8px; padding: 16px; text-align: center; border: 2px solid #ddd; margin-bottom: 12px; }
.result-card.risk-high { border-color: #dc2626; }
.result-card.risk-medium { border-color: #f59e0b; }
.result-card.risk-low { border-color: #16a34a; }
.result-score { margin-bottom: 8px; }
.total-score { font-size: 32px; font-weight: 700; color: #333; }
.max-score { font-size: 14px; color: #999; }
.risk-badge { display: inline-block; padding: 2px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; color: #fff; margin-bottom: 8px; }
.risk-badge.risk-high { background: #dc2626; }
.risk-badge.risk-medium { background: #f59e0b; }
.risk-badge.risk-low { background: #16a34a; }
.risk-desc { font-size: 12px; color: #666; margin: 0; }

.detail-section { margin-bottom: 12px; }
.detail-title { font-size: 12px; font-weight: 600; color: #333; margin-bottom: 6px; }
.detail-item { display: flex; align-items: center; gap: 8px; padding: 3px 0; }
.detail-label { font-size: 11px; color: #666; min-width: 56px; }
.detail-bar-wrapper { flex: 1; height: 6px; background: #f3f4f6; border-radius: 3px; overflow: hidden; }
.detail-bar { height: 100%; border-radius: 3px; transition: width 0.3s; }
.detail-score { font-size: 12px; font-weight: 600; min-width: 20px; text-align: right; }

.suggestion-section { margin-bottom: 4px; }
.suggestion-list { padding-left: 16px; margin: 0; font-size: 12px; color: #444; }
.suggestion-list li { padding: 2px 0; }
</style>
