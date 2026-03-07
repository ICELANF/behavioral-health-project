<template>
  <div class="motivation-quiz">
    <!-- 进度条 -->
    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: progressPct + '%' }"></div>
      <span class="progress-text">{{ currentIndex + 1 }} / {{ totalQuestions }}</span>
    </div>

    <!-- 动机4题 -->
    <template v-if="phase === 'motivation'">
      <div class="question-card">
        <h2 class="question-title">{{ currentMotivationQ.title }}</h2>
        <p class="question-hint">选择最符合你的选项</p>
        <div class="options">
          <div
            v-for="(opt, oi) in currentMotivationQ.options"
            :key="oi"
            class="option-card"
            :class="{ selected: motivationAnswers[motivationIndex] === oi }"
            @click="answerMotivation(oi)"
          >
            <span class="option-label">{{ String.fromCharCode(65 + oi) }}</span>
            <span class="option-text">{{ opt.text }}</span>
          </div>
        </div>
      </div>
    </template>

    <!-- 大五10题快速版 -->
    <template v-if="phase === 'big5'">
      <div class="question-card">
        <h2 class="question-title">{{ currentBig5Q.title }}</h2>
        <p class="question-hint">按直觉选择，没有对错</p>
        <div class="scale-options">
          <div
            v-for="s in 5"
            :key="s"
            class="scale-dot"
            :class="{ active: big5Answers[big5Index] === s }"
            @click="answerBig5(s)"
          >
            <span class="dot"></span>
            <span class="scale-label">{{ scaleLabels[s - 1] }}</span>
          </div>
        </div>
      </div>
    </template>

    <!-- 四所4题 (UI-02) -->
    <template v-if="phase === 'sisuo'">
      <div class="question-card sisuo">
        <h2 class="question-title">{{ currentSisuoQ.title }}</h2>
        <p class="question-hint">探索你的内心驱动</p>
        <div class="options">
          <div
            v-for="(opt, oi) in currentSisuoQ.options"
            :key="oi"
            class="option-card"
            :class="{ selected: sisuoAnswers[sisuoIndex] === oi }"
            @click="answerSisuo(oi)"
          >
            <span class="option-label">{{ String.fromCharCode(65 + oi) }}</span>
            <span class="option-text">{{ opt.text }}</span>
          </div>
        </div>
      </div>
    </template>

    <!-- 完成 -->
    <template v-if="phase === 'done'">
      <div class="done-card">
        <div class="done-icon">&#10003;</div>
        <h2>评估完成</h2>
        <p>正在生成你的专属画像...</p>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'

const router = useRouter()

// ── 动机4题 ──
const motivationQuestions = [
  {
    title: '什么最能驱动你改善健康？',
    options: [
      { text: '预防疾病，守护健康', keyword: '健康' },
      { text: '为家人活得更好', keyword: '家庭' },
      { text: '追求更自由的生活', keyword: '自由' },
      { text: '内心的平静与安宁', keyword: '平静' },
    ],
  },
  {
    title: '你更看重哪种改变的回报？',
    options: [
      { text: '身体指标的改善', keyword: '指标' },
      { text: '家人的放心和认可', keyword: '认可' },
      { text: '更高效地工作和生活', keyword: '效率' },
      { text: '找到人生的意义', keyword: '意义' },
    ],
  },
  {
    title: '遇到困难时，什么让你坚持？',
    options: [
      { text: '对健康后果的担忧', keyword: '担忧' },
      { text: '不想让家人失望', keyword: '责任' },
      { text: '不甘心放弃目标', keyword: '成就' },
      { text: '相信一切会好起来', keyword: '信念' },
    ],
  },
  {
    title: '你理想中的健康生活是？',
    options: [
      { text: '指标正常，远离医院', keyword: '安全' },
      { text: '全家人一起健康快乐', keyword: '家人' },
      { text: '精力充沛做想做的事', keyword: '能量' },
      { text: '身心合一，内外平衡', keyword: '平衡' },
    ],
  },
]

// ── 大五10题快速版 ──
const big5Questions = [
  { title: '我喜欢和很多人在一起', dim: 'E', reverse: false },
  { title: '我经常感到焦虑或紧张', dim: 'N', reverse: false },
  { title: '我做事有计划、有条理', dim: 'C', reverse: false },
  { title: '我愿意帮助他人，即使不方便', dim: 'A', reverse: false },
  { title: '我对新事物充满好奇', dim: 'O', reverse: false },
  { title: '在聚会中我更喜欢安静待着', dim: 'E', reverse: true },
  { title: '我很少担心未来的事', dim: 'N', reverse: true },
  { title: '我有时会拖延重要的事', dim: 'C', reverse: true },
  { title: '我倾向于先考虑自己的需求', dim: 'A', reverse: true },
  { title: '我更喜欢熟悉的方式做事', dim: 'O', reverse: true },
]

const scaleLabels = ['完全不符', '不太符合', '一般', '比较符合', '完全符合']

// ── 四所4题 (UI-02) ──
const sisuoQuestions = [
  {
    title: '让你最想改变健康的原因是？',
    options: [
      { text: '我想成为更好的自己', sisuo: 'desire' },
      { text: '我害怕身体出问题', sisuo: 'fear' },
    ],
  },
  {
    title: '面对困难时你更多感到？',
    options: [
      { text: '厌恶现状，想要逃离', sisuo: 'aversion' },
      { text: '困惑不知从何下手', sisuo: 'confusion' },
    ],
  },
  {
    title: '什么最能触动你立即行动？',
    options: [
      { text: '看到具体的健康风险数据', sisuo: 'fear' },
      { text: '感受到某种强烈的情绪', sisuo: 'desire' },
    ],
  },
  {
    title: '你的改变动力来自？',
    options: [
      { text: '内心深处的价值认同', sisuo: 'desire' },
      { text: '外部的压力或他人期待', sisuo: 'fear' },
    ],
  },
]

// ── State ──
const motivationAnswers = ref<Record<number, number>>({})
const big5Answers = ref<Record<number, number>>({})
const sisuoAnswers = ref<Record<number, number>>({})
const motivationIndex = ref(0)
const big5Index = ref(0)
const sisuoIndex = ref(0)
const phase = ref<'motivation' | 'big5' | 'sisuo' | 'done'>('motivation')

const totalQuestions = motivationQuestions.length + big5Questions.length + sisuoQuestions.length

const currentIndex = computed(() => {
  if (phase.value === 'motivation') return motivationIndex.value
  if (phase.value === 'big5') return motivationQuestions.length + big5Index.value
  if (phase.value === 'sisuo') return motivationQuestions.length + big5Questions.length + sisuoIndex.value
  return totalQuestions
})

const progressPct = computed(() => ((currentIndex.value + 1) / totalQuestions) * 100)

const currentMotivationQ = computed(() => motivationQuestions[motivationIndex.value])
const currentBig5Q = computed(() => big5Questions[big5Index.value])
const currentSisuoQ = computed(() => sisuoQuestions[sisuoIndex.value])

// ── Handlers ──
function answerMotivation(optIndex: number) {
  motivationAnswers.value[motivationIndex.value] = optIndex
  setTimeout(() => {
    if (motivationIndex.value < motivationQuestions.length - 1) {
      motivationIndex.value++
    } else {
      phase.value = 'big5'
    }
  }, 300)
}

function answerBig5(score: number) {
  big5Answers.value[big5Index.value] = score
  setTimeout(() => {
    if (big5Index.value < big5Questions.length - 1) {
      big5Index.value++
    } else {
      phase.value = 'sisuo'
    }
  }, 300)
}

function answerSisuo(optIndex: number) {
  sisuoAnswers.value[sisuoIndex.value] = optIndex
  setTimeout(() => {
    if (sisuoIndex.value < sisuoQuestions.length - 1) {
      sisuoIndex.value++
    } else {
      phase.value = 'done'
      submitAll()
    }
  }, 300)
}

// ── 提交 ──
async function submitAll() {
  // 收集动机关键词
  const keywords: string[] = []
  for (const [qi, oi] of Object.entries(motivationAnswers.value)) {
    const q = motivationQuestions[Number(qi)]
    if (q && q.options[oi]) {
      keywords.push(q.options[oi].keyword)
    }
  }

  // 计算大五原始分
  const dimScores: Record<string, number[]> = { E: [], N: [], C: [], A: [], O: [] }
  for (const [qi, score] of Object.entries(big5Answers.value)) {
    const q = big5Questions[Number(qi)]
    const val = q.reverse ? (6 - score) : score  // 反向计分
    dimScores[q.dim].push((val - 3) * 10)  // 转为 -20 ~ +20
  }
  const big5: Record<string, number> = {}
  for (const [dim, scores] of Object.entries(dimScores)) {
    big5[dim] = scores.reduce((a, b) => a + b, 0)
  }

  // 收集四所结果
  const sisuo: Record<string, string> = {}
  for (const [qi, oi] of Object.entries(sisuoAnswers.value)) {
    const q = sisuoQuestions[Number(qi)]
    if (q && q.options[oi]) {
      const key = q.options[oi].sisuo
      sisuo[key] = (sisuo[key] || '') + q.title.slice(0, 10) + '; '
    }
  }

  try {
    const res = await request.post('/api/v1/guixin/rx/prescription', {
      motivation_keywords: keywords,
      sisuo,
    })
    // 跳转画像页
    router.push({ path: '/v3/profile-card', query: { fresh: '1' } })
  } catch (e) {
    console.error('提交失败', e)
    router.push('/v3/profile-card')
  }
}
</script>

<style scoped>
.motivation-quiz {
  max-width: 430px;
  margin: 0 auto;
  padding: 20px 16px;
  min-height: 100vh;
  background: linear-gradient(180deg, #f0f4ff 0%, #fff 40%);
}

.progress-bar {
  position: relative;
  height: 6px;
  background: #e8ecf4;
  border-radius: 3px;
  margin-bottom: 32px;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4f6ef7, #7b61ff);
  border-radius: 3px;
  transition: width 0.3s ease;
}
.progress-text {
  position: absolute;
  right: 0;
  top: 12px;
  font-size: 12px;
  color: #999;
}

.question-card {
  animation: fadeIn 0.3s ease;
}
.question-title {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 8px;
  line-height: 1.4;
}
.question-hint {
  font-size: 13px;
  color: #999;
  margin-bottom: 24px;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.option-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #fff;
  border: 2px solid #e8ecf4;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.option-card.selected {
  border-color: #4f6ef7;
  background: #f0f4ff;
}
.option-label {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #f0f4ff;
  color: #4f6ef7;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}
.option-card.selected .option-label {
  background: #4f6ef7;
  color: #fff;
}
.option-text {
  font-size: 15px;
  color: #333;
}

.scale-options {
  display: flex;
  justify-content: space-between;
  padding: 20px 0;
}
.scale-dot {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  flex: 1;
}
.dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 2px solid #d0d5dd;
  transition: all 0.2s;
}
.scale-dot.active .dot {
  background: #4f6ef7;
  border-color: #4f6ef7;
  transform: scale(1.2);
}
.scale-label {
  font-size: 11px;
  color: #999;
  text-align: center;
}

.done-card {
  text-align: center;
  padding: 60px 20px;
}
.done-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4f6ef7, #7b61ff);
  color: #fff;
  font-size: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
}
.done-card h2 {
  font-size: 22px;
  color: #1a1a2e;
  margin-bottom: 8px;
}
.done-card p {
  color: #666;
  font-size: 14px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
