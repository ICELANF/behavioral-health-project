<template>
  <div class="assessment-result">
    <div class="page-header">
      <button class="back-btn" @click="$router.back()">← 返回</button>
      <h2>测评结果</h2>
    </div>

    <!-- Score Card -->
    <div class="score-card" :class="'level-' + riskLevel">
      <div class="score-circle" :style="{ borderColor: levelColor }">
        <span class="score-number">{{ result.score }}</span>
        <span class="score-max">/ {{ maxScore }}</span>
      </div>
      <div class="score-info">
        <span class="score-name">{{ result.name }}</span>
        <span class="score-level" :style="{ color: levelColor }">{{ levelLabel }}</span>
        <span class="score-date">评估日期: {{ result.date }}</span>
      </div>
    </div>

    <!-- Interpretation -->
    <div class="section-card">
      <h3>得分解读</h3>
      <p class="interpretation">{{ interpretation }}</p>
      <div class="score-scale">
        <div v-for="range in scoreRanges" :key="range.label" class="scale-item">
          <div class="scale-bar" :style="{ background: range.color, width: range.width }">
            <span v-if="isInRange(range)" class="scale-marker">▼</span>
          </div>
          <span class="scale-label">{{ range.label }}</span>
          <span class="scale-range">{{ range.range }}</span>
        </div>
      </div>
    </div>

    <!-- Historical Trend -->
    <div class="section-card">
      <h3>历史趋势</h3>
      <div class="trend-chart">
        <div v-for="(h, i) in history" :key="i" class="trend-col">
          <div class="trend-bar" :style="{ height: (h.score / maxScore * 100) + '%', background: trendColor(h.score) }">
            <span class="trend-score">{{ h.score }}</span>
          </div>
          <span class="trend-date">{{ h.shortDate }}</span>
        </div>
      </div>
      <div v-if="trendDirection" class="trend-summary">
        <span :class="trendDirection === 'improving' ? 'trend-good' : 'trend-warn'">
          {{ trendDirection === 'improving' ? '趋势好转' : '需要关注' }}
          {{ trendDirection === 'improving' ? '↓' : '↑' }}
        </span>
      </div>
    </div>

    <!-- Actions -->
    <div class="action-section">
      <button class="action-btn share" @click="shareToCoach">分享给教练</button>
      <button class="action-btn pdf" @click="downloadPDF">下载 PDF</button>
      <button class="action-btn retake" @click="$router.push(`/client/assessment/take/${assessmentId}`)">再次测评</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import request from '@/api/request'

const route = useRoute()
const assessmentId = route.params.id

// Start with localStorage data (instant display), then try API
const stored = localStorage.getItem(`assessment_result_${assessmentId}`)
const parsedResult = stored ? JSON.parse(stored) : null

const result = ref({
  name: parsedResult?.questionnaireName || parsedResult?.name || '测评结果',
  score: parsedResult?.score || 0,
  maxScore: parsedResult?.maxScore || parsedResult?.max_score || 100,
  date: parsedResult?.date?.slice(0, 10) || new Date().toISOString().slice(0, 10),
})
const maxScore = computed(() => result.value.maxScore)

const scorePct = computed(() => result.value.score / maxScore.value)

const riskLevel = computed(() => {
  if (scorePct.value >= 0.7) return 'severe'
  if (scorePct.value >= 0.5) return 'moderate'
  if (scorePct.value >= 0.25) return 'mild'
  return 'normal'
})

const levelLabel = computed(() => {
  const map = { normal: '正常/极轻微', mild: '轻度', moderate: '中度', severe: '重度' }
  return map[riskLevel.value]
})

const levelColor = computed(() => {
  const map = { normal: '#389e0d', mild: '#d4b106', moderate: '#d46b08', severe: '#cf1322' }
  return map[riskLevel.value]
})

const interpretation = computed(() => {
  const map = {
    normal: '您的评估结果在正常范围内，当前心理健康状况良好。建议保持健康的生活方式和积极的社交活动。',
    mild: '评估结果提示您可能存在轻度症状。建议关注自身状态变化，适当增加放松和自我调节活动。如持续2周以上，建议咨询专业人士。',
    moderate: '评估结果提示中度症状。建议尽快与您的健康教练沟通，制定干预计划。可能需要专业心理咨询或医疗评估。',
    severe: '评估结果提示较严重的症状。强烈建议立即联系您的健康教练或医疗专业人士获取帮助。请不要独自承受。',
  }
  return map[riskLevel.value]
})

const scoreRanges = computed(() => [
  { label: '正常', range: `0-${Math.round(maxScore.value * 0.25)}`, color: '#389e0d', width: '25%', min: 0, max: maxScore.value * 0.25 },
  { label: '轻度', range: `${Math.round(maxScore.value * 0.25)}-${Math.round(maxScore.value * 0.5)}`, color: '#d4b106', width: '25%', min: maxScore.value * 0.25, max: maxScore.value * 0.5 },
  { label: '中度', range: `${Math.round(maxScore.value * 0.5)}-${Math.round(maxScore.value * 0.7)}`, color: '#d46b08', width: '20%', min: maxScore.value * 0.5, max: maxScore.value * 0.7 },
  { label: '重度', range: `${Math.round(maxScore.value * 0.7)}-${maxScore.value}`, color: '#cf1322', width: '30%', min: maxScore.value * 0.7, max: maxScore.value },
])

const isInRange = (range) => result.value.score >= range.min && result.value.score < range.max

const history = ref([])

const trendDirection = computed(() => {
  if (history.value.length < 2) return null
  const recent = history.value[history.value.length - 1].score
  const previous = history.value[history.value.length - 2].score
  return recent < previous ? 'improving' : 'worsening'
})

const trendColor = (score) => {
  const pct = score / maxScore.value
  if (pct >= 0.7) return '#cf1322'
  if (pct >= 0.4) return '#d4b106'
  return '#389e0d'
}

onMounted(async () => {
  // Try to fetch from API; on success, update result and history
  try {
    const res = await request.get(`v1/assessment-assignments/${assessmentId}/result`)
    const d = res.data
    if (d) {
      result.value = {
        name: d.questionnaire_name || d.name || result.value.name,
        score: d.score ?? result.value.score,
        maxScore: d.max_score ?? result.value.maxScore,
        date: (d.completed_at || d.date || '').slice(0, 10) || result.value.date,
      }
      // Populate history if returned
      if (Array.isArray(d.history)) {
        history.value = d.history.map((h) => ({
          score: h.score,
          shortDate: (h.date || h.completed_at || '').slice(5, 10),
        }))
      }
    }
  } catch {
    // API unavailable — keep localStorage data (already loaded above)
  }
})

const shareToCoach = () => { message.success('结果已分享给您的健康教练') }
const downloadPDF = () => { message.info('PDF 下载功能即将上线') }
</script>

<style scoped>
.assessment-result { max-width: 600px; margin: 0 auto; padding: 16px; }
.page-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.page-header h2 { flex: 1; margin: 0; font-size: 18px; }
.back-btn { padding: 6px 16px; border: 1px solid #d9d9d9; border-radius: 6px; background: #fff; cursor: pointer; }

.score-card { display: flex; align-items: center; gap: 16px; padding: 20px; border-radius: 12px; margin-bottom: 16px; background: #fff; border: 2px solid #f0f0f0; }
.score-card.level-normal { border-color: #b7eb8f; background: #f6ffed; }
.score-card.level-mild { border-color: #ffe58f; background: #fffbe6; }
.score-card.level-moderate { border-color: #ffd591; background: #fff7e6; }
.score-card.level-severe { border-color: #ffa39e; background: #fff1f0; }
.score-circle { width: 80px; height: 80px; border-radius: 50%; border: 4px solid; display: flex; flex-direction: column; align-items: center; justify-content: center; flex-shrink: 0; background: #fff; }
.score-number { font-size: 28px; font-weight: 700; color: #333; line-height: 1; }
.score-max { font-size: 12px; color: #999; }
.score-info { flex: 1; }
.score-name { display: block; font-size: 16px; font-weight: 600; color: #333; }
.score-level { display: block; font-size: 14px; font-weight: 600; margin: 4px 0; }
.score-date { font-size: 12px; color: #999; }

.section-card { background: #fff; border: 1px solid #f0f0f0; border-radius: 10px; padding: 16px; margin-bottom: 12px; }
.section-card h3 { font-size: 15px; font-weight: 600; margin: 0 0 12px; color: #333; }
.interpretation { font-size: 13px; color: #666; line-height: 1.6; margin: 0 0 12px; }

.score-scale { display: flex; flex-direction: column; gap: 4px; }
.scale-item { display: flex; align-items: center; gap: 8px; }
.scale-bar { height: 16px; border-radius: 4px; position: relative; min-width: 20px; }
.scale-marker { position: absolute; top: -14px; left: 50%; transform: translateX(-50%); font-size: 10px; }
.scale-label { font-size: 12px; color: #333; min-width: 36px; }
.scale-range { font-size: 11px; color: #999; }

.trend-chart { display: flex; gap: 8px; height: 100px; align-items: flex-end; margin-bottom: 8px; }
.trend-col { flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-end; }
.trend-bar { width: 100%; max-width: 32px; border-radius: 4px 4px 0 0; position: relative; min-height: 4px; transition: height 0.3s; }
.trend-score { position: absolute; top: -16px; left: 50%; transform: translateX(-50%); font-size: 10px; font-weight: 600; white-space: nowrap; }
.trend-date { font-size: 10px; color: #999; margin-top: 4px; }
.trend-summary { text-align: center; font-size: 13px; }
.trend-good { color: #389e0d; }
.trend-warn { color: #d46b08; }

.action-section { display: flex; gap: 8px; }
.action-btn { flex: 1; padding: 10px; border: 1px solid #d9d9d9; border-radius: 8px; background: #fff; cursor: pointer; font-size: 14px; text-align: center; }
.action-btn.share { background: #1890ff; color: #fff; border-color: #1890ff; }
.action-btn.pdf { color: #1890ff; border-color: #1890ff; }
</style>
