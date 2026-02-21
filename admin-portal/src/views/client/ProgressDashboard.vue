<template>
  <div class="progress-dashboard">
    <!-- 顶部导航 -->
    <div class="dashboard-header">
      <div class="header-left" @click="goBack">
        <LeftOutlined />
      </div>
      <h1 class="header-title">我的进展</h1>
      <div class="header-right" @click="showPeriodSelector = true">
        <CalendarOutlined />
      </div>
    </div>

    <!-- 主内容 -->
    <div class="dashboard-content">
      <!-- 周期选择器 -->
      <div class="period-selector">
        <div
          v-for="period in periods"
          :key="period.value"
          class="period-btn"
          :class="{ active: selectedPeriod === period.value }"
          @click="selectPeriod(period.value)"
        >
          {{ period.label }}
        </div>
      </div>

      <!-- 总体评分卡片 - 使用 HealthScoreCircle 组件 -->
      <div class="score-card">
        <div class="score-header">
          <div class="score-title">{{ periodText }}健康评分</div>
          <div class="score-trend" :class="scoreTrend.type">
            {{ scoreTrend.text }}
          </div>
        </div>
        <div class="score-visual-wrapper">
          <HealthScoreCircle
            :score="overallScore"
            :size="140"
            :stroke-width="12"
            :color-theme="scoreColorTheme"
            :show-info="false"
          />
          <div class="score-details">
            <div class="detail-item">
              <div class="detail-icon">🎯</div>
              <div class="detail-info">
                <div class="detail-label">目标达成率</div>
                <div class="detail-value">{{ achievementRate }}%</div>
              </div>
            </div>
            <div class="detail-item">
              <div class="detail-icon">🔥</div>
              <div class="detail-info">
                <div class="detail-label">连续打卡</div>
                <div class="detail-value">{{ streakDays }} 天</div>
              </div>
            </div>
          </div>
        </div>
        <div class="score-message">
          {{ scoreMessage }}
        </div>
      </div>

      <!-- 成就徽章 - 使用 AchievementBadge 组件 -->
      <div class="achievement-section" v-if="recentAchievements.length > 0">
        <div class="section-header">
          <h3 class="section-title">🏆 最新成就</h3>
          <a class="view-all" @click="showAllAchievements">查看全部 ›</a>
        </div>
        <div class="achievement-grid">
          <AchievementBadge
            v-for="badge in recentAchievements"
            :key="badge.id"
            :icon="badge.icon"
            :name="badge.name"
            :unlocked="badge.unlocked"
            :unlocked-date="badge.unlockedDate"
            size="medium"
            @click="showBadgeDetail(badge)"
          />
        </div>
      </div>

      <!-- 各项指标趋势 - 使用 TrendChart 组件 -->
      <div class="metrics-section">
        <h3 class="section-title">📊 指标趋势</h3>

        <!-- 血糖趋势 -->
        <div class="metric-card-wrapper">
          <TrendChart
            type="line"
            :data="glucoseData"
            :labels="dateLabels"
            title="血糖趋势"
            icon="🩸"
            line-color="#ef4444"
            :show-area="true"
            :show-dots="true"
            :show-stats="true"
            :trend-text="glucoseTrend.text"
            :trend-direction="glucoseTrend.status === 'good' ? 'down' : 'stable'"
          />
        </div>

        <!-- 体重趋势 -->
        <div class="metric-card-wrapper">
          <TrendChart
            type="line"
            :data="weightData"
            :labels="dateLabels"
            title="体重趋势"
            icon="⚖️"
            line-color="#8b5cf6"
            :show-area="true"
            :show-dots="true"
            :show-stats="true"
            :trend-text="weightTrend.text"
            :trend-direction="weightTrend.status === 'good' ? 'down' : 'stable'"
          />
        </div>

        <!-- 运动统计 -->
        <div class="metric-card-wrapper">
          <TrendChart
            type="bar"
            :data="exerciseStats.weeklyData.map((d: any) => d.minutes)"
            :labels="exerciseStats.weeklyData.map((d: any) => d.label)"
            title="每日运动"
            subtitle="分钟数"
            icon="🏃"
            bar-color="#10b981"
            :show-values="true"
            :show-stats="true"
            :trend-text="`周均 ${exerciseStats.dailyAverage} 分钟，已完成 ${exerciseStats.completedDays}/7 天`"
            trend-direction="up"
          />
        </div>
      </div>

      <!-- 周期对比 -->
      <div class="comparison-section">
        <h3 class="section-title">📈 周期对比</h3>
        <div class="comparison-grid">
          <div class="comparison-item">
            <div class="comparison-label">平均血糖</div>
            <div class="comparison-values">
              <div class="value-current">5.8 <span class="unit">mmol/L</span></div>
              <div class="value-compare good">↓ 6.5%</div>
            </div>
          </div>
          <div class="comparison-item">
            <div class="comparison-label">平均体重</div>
            <div class="comparison-values">
              <div class="value-current">74.5 <span class="unit">kg</span></div>
              <div class="value-compare good">↓ 0.9%</div>
            </div>
          </div>
          <div class="comparison-item">
            <div class="comparison-label">运动时长</div>
            <div class="comparison-values">
              <div class="value-current">180 <span class="unit">分钟</span></div>
              <div class="value-compare good">↑ 20%</div>
            </div>
          </div>
          <div class="comparison-item">
            <div class="comparison-label">情绪评分</div>
            <div class="comparison-values">
              <div class="value-current">4.2 <span class="unit">分</span></div>
              <div class="value-compare good">↑ 10.5%</div>
            </div>
          </div>
        </div>
      </div>

      <!-- AI 总结 -->
      <div class="ai-summary-card">
        <div class="summary-header">
          <div class="ai-avatar">🤖</div>
          <div class="summary-title">AI 健康总结</div>
        </div>
        <div class="ai-message">{{ aiSummary }}</div>
        <div class="ai-suggestions" v-if="aiSuggestions.length > 0">
          <div class="suggestions-title">💡 建议</div>
          <ul class="suggestion-list">
            <li v-for="(suggestion, index) in aiSuggestions" :key="index">
              {{ suggestion }}
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- 周期选择抽屉 -->
    <a-drawer
      v-model:open="showPeriodSelector"
      title="选择查看周期"
      placement="bottom"
      :height="'50vh'"
    >
      <div class="period-list">
        <div
          v-for="period in allPeriods"
          :key="period.value"
          class="period-option"
          :class="{ selected: selectedPeriod === period.value }"
          @click="selectPeriod(period.value)"
        >
          <div class="period-icon">{{ period.icon }}</div>
          <div class="period-label">{{ period.label }}</div>
          <CheckOutlined v-if="selectedPeriod === period.value" class="check-icon" />
        </div>
      </div>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  LeftOutlined,
  CalendarOutlined,
  CheckOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { healthApi } from '@/api/health'
import { HealthScoreCircle, TrendChart, AchievementBadge } from '@/components/health'

const router = useRouter()

// patientId no longer needed — real endpoints are JWT-scoped
const loading = ref(true)

// 周期选择
const periods = [
  { label: '本周', value: 'week' },
  { label: '本月', value: 'month' },
  { label: '3个月', value: 'quarter' }
]

const allPeriods = [
  { label: '最近7天', value: 'week', icon: '📅' },
  { label: '最近30天', value: 'month', icon: '📆' },
  { label: '最近3个月', value: 'quarter', icon: '🗓️' },
  { label: '最近半年', value: 'half-year', icon: '📊' },
  { label: '最近一年', value: 'year', icon: '📈' }
]

const selectedPeriod = ref<'week' | 'month' | 'quarter'>('week')
const showPeriodSelector = ref(false)

const periodText = computed(() => {
  const period = periods.find(p => p.value === selectedPeriod.value)
  return period ? period.label : '本周'
})

const selectPeriod = (value: string) => {
  selectedPeriod.value = value as 'week' | 'month' | 'quarter'
  showPeriodSelector.value = false
  loadData()
}

// 总体评分
const overallScore = ref(0)
const achievementRate = ref(0)
const streakDays = ref(0)
const scoreTrendDiff = ref(0)

const scoreTrend = computed(() => {
  const diff = scoreTrendDiff.value
  if (diff > 0) {
    return { type: 'up', text: `↗ 比上周提升 ${diff}分` }
  } else if (diff < 0) {
    return { type: 'down', text: `↘ 比上周下降 ${Math.abs(diff)}分` }
  }
  return { type: 'same', text: '→ 与上周持平' }
})

const scoreColorTheme = computed(() => {
  if (overallScore.value >= 90) return 'green'
  if (overallScore.value >= 70) return 'blue'
  if (overallScore.value >= 50) return 'orange'
  return 'red'
})

const scoreMessage = computed(() => {
  if (overallScore.value >= 90) return '🎉 太棒了！您的健康状态非常好，继续保持！'
  if (overallScore.value >= 70) return '👍 不错！您的健康管理做得很好，再接再厉！'
  if (overallScore.value >= 50) return '💪 加油！距离目标越来越近了！'
  return '🤗 别气馁，每一天的坚持都会有收获！'
})

// 成就徽章
const recentAchievements = ref<any[]>([])

// 血糖数据
const glucoseData = ref<number[]>([])
const dateLabels = ref<string[]>([])

const glucoseTrend = ref({
  status: 'good',
  text: '加载中...'
})

const glucoseStats = ref({
  average: '--',
  max: '--',
  min: '--'
})

// 体重数据
const weightData = ref<number[]>([])

const weightTrend = ref({
  status: 'good',
  text: '加载中...'
})

const weightStats = ref({
  current: '--',
  target: '70.0kg',
  lost: '--'
})

// 运动数据
const exerciseStats = ref({
  weeklyTotal: 0,
  dailyTarget: 30,
  completedDays: 0,
  dailyAverage: 0,
  weeklyData: [] as Array<{ label: string; minutes: number }>
})

// AI总结
const aiSummary = ref('加载中...')
const aiSuggestions = ref<string[]>([])

// 加载数据
const loadData = async () => {
  if (!localStorage.getItem('admin_token')) return
  try {
    loading.value = true

    const periodDays = selectedPeriod.value === 'week' ? '7d' : selectedPeriod.value === 'month' ? '30d' : '90d'

    // 并行加载数据（JWT-scoped, no patientId）
    const [scoreRes, glucoseRes, weightRes, exerciseRes, achieveRes, summaryRes] = await Promise.allSettled([
      healthApi.getHealthScore(),
      healthApi.getTrends('glucose', { period: selectedPeriod.value }),
      healthApi.getTrends('weight', { period: selectedPeriod.value }),
      healthApi.getExerciseHistory({ period: periodDays }),
      healthApi.getAchievements(),
      healthApi.getAISummary(),
    ])

    // 更新健康评分
    if (scoreRes.status === 'fulfilled' && scoreRes.value) {
      const sd = scoreRes.value
      overallScore.value = sd.overall_score ?? sd.overall ?? sd.score ?? 0
      achievementRate.value = overallScore.value
      streakDays.value = sd.streak_days ?? sd.streakDays ?? 0
      scoreTrendDiff.value = sd.trend_diff ?? sd.trendDiff ?? 0
    }

    // 更新血糖趋势
    if (glucoseRes.status === 'fulfilled' && glucoseRes.value) {
      const tg = glucoseRes.value
      const records = tg.data || tg.records || tg.items || (Array.isArray(tg) ? tg : [])
      if (records.length > 0) {
        glucoseData.value = records.map((d: any) => d.value || d.glucose || 0)
        dateLabels.value = records.map((d: any) => (d.date || d.measured_at || '').slice(5, 10))
        const vals = glucoseData.value.filter((v: number) => v > 0)
        const avg = vals.length ? vals.reduce((s: number, v: number) => s + v, 0) / vals.length : 0
        glucoseStats.value = {
          average: avg.toFixed(1),
          max: vals.length ? Math.max(...vals).toFixed(1) : '--',
          min: vals.length ? Math.min(...vals).toFixed(1) : '--',
        }
        glucoseTrend.value = {
          status: tg.trend === 'improving' ? 'good' : 'warning',
          text: tg.trend === 'improving' ? '平稳下降 ✓' : tg.trend === 'declining' ? '需要注意 ⚠' : '保持稳定',
        }
      }
    }

    // 更新体重趋势
    if (weightRes.status === 'fulfilled' && weightRes.value) {
      const tw = weightRes.value
      const records = tw.data || tw.records || tw.items || (Array.isArray(tw) ? tw : [])
      if (records.length > 0) {
        weightData.value = records.map((d: any) => d.value || d.weight || 0)
        const first = weightData.value[0] || 0
        const last = weightData.value[weightData.value.length - 1] || 0
        const lost = first - last
        weightStats.value = {
          current: `${last.toFixed(1)}kg`,
          target: tw.target ? `${tw.target}kg` : '--',
          lost: `${lost.toFixed(1)}kg`,
        }
        weightTrend.value = {
          status: lost > 0 ? 'good' : 'warning',
          text: lost > 0 ? `已减 ${lost.toFixed(1)}kg ✓` : '保持中',
        }
      }
    }

    // 更新运动数据
    if (exerciseRes.status === 'fulfilled' && exerciseRes.value) {
      const ex = exerciseRes.value
      const records = ex.records || ex.items || (Array.isArray(ex) ? ex : [])
      const weeklyData = records.slice(-7).map((r: any, i: number) => ({
        label: ['一', '二', '三', '四', '五', '六', '日'][i] || `${i + 1}`,
        minutes: r.duration || r.minutes || 0,
      }))
      const total = weeklyData.reduce((sum: number, d: any) => sum + d.minutes, 0)
      exerciseStats.value = {
        weeklyTotal: total,
        dailyTarget: 30,
        completedDays: weeklyData.filter((d: any) => d.minutes > 0).length,
        dailyAverage: Math.round(total / Math.max(weeklyData.length, 1)),
        weeklyData,
      }
    }

    // 更新成就徽章 (credits/my returns credit records)
    if (achieveRes.status === 'fulfilled' && achieveRes.value) {
      const ad = achieveRes.value
      const items = ad.achievements || ad.records || ad.items || (Array.isArray(ad) ? ad : [])
      recentAchievements.value = items.slice(0, 4).map((a: any) => ({
        id: a.id,
        icon: a.icon || '🏅',
        name: a.name || a.description || a.event_type || '',
        unlocked: a.unlocked ?? true,
        unlockedDate: a.unlockedAt || a.created_at || undefined,
      }))
    }

    // 更新AI总结
    if (summaryRes.status === 'fulfilled' && summaryRes.value) {
      const sm = summaryRes.value
      aiSummary.value = sm.tip || sm.summary || sm.content || '暂无总结'
      aiSuggestions.value = sm.suggestions || []
    }

  } catch (error) {
    console.error('加载数据失败:', error)
    message.error('加载数据失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 格式化日期
const formatDate = (timestamp: number) => {
  const date = new Date(timestamp)
  const month = date.getMonth() + 1
  const day = date.getDate()
  return `${month}月${day}日解锁`
}

// 显示徽章详情
const showBadgeDetail = (badge: any) => {
  if (badge.unlocked) {
    message.success(`🎉 ${badge.name}\n解锁于 ${formatDate(badge.unlockedDate)}`)
  } else {
    message.info(`🔒 ${badge.name}\n继续努力，即将解锁！`)
  }
}

// 查看所有成就 → 学习进度页
const showAllAchievements = () => {
  router.push('/client/learning-progress')
}

// 返回
const goBack = () => {
  router.back()
}

// 初始化
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.progress-dashboard {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 20px;
}

/* 顶部导航 */
.dashboard-header {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.header-left,
.header-right {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 50%;
  transition: background 0.2s;
}

.header-left:hover,
.header-right:hover {
  background: rgba(255,255,255,0.2);
}

.header-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
}

/* 主内容 */
.dashboard-content {
  max-width: 640px;
  margin: 0 auto;
  padding: 16px;
}

/* 周期选择器 */
.period-selector {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  background: #fff;
  padding: 6px;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.period-btn {
  flex: 1;
  padding: 10px;
  text-align: center;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
}

.period-btn.active {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  color: #fff;
}

/* 总体评分卡片 */
.score-card {
  background: #fff;
  border-radius: 20px;
  padding: 24px;
  margin-bottom: 16px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.06);
}

.score-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.score-title {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
}

.score-trend {
  font-size: 13px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 12px;
}

.score-trend.up {
  background: #dcfce7;
  color: #16a34a;
}

.score-trend.down {
  background: #fee2e2;
  color: #dc2626;
}

.score-trend.same {
  background: #f3f4f6;
  color: #6b7280;
}

.score-visual-wrapper {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 16px;
}

.score-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-icon {
  font-size: 28px;
}

.detail-info {
  flex: 1;
}

.detail-label {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 2px;
}

.detail-value {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
}

.score-message {
  font-size: 14px;
  color: #6b7280;
  text-align: center;
  padding: 12px;
  background: #f9fafb;
  border-radius: 12px;
}

/* 成就徽章 */
.achievement-section {
  background: #fff;
  border-radius: 20px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.06);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.view-all {
  font-size: 14px;
  color: #10b981;
  cursor: pointer;
  font-weight: 500;
}

.achievement-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

/* 指标趋势 */
.metrics-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.metric-card-wrapper {
  background: #fff;
  border-radius: 20px;
  padding: 20px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.06);
}

/* 周期对比 */
.comparison-section {
  background: #fff;
  border-radius: 20px;
  padding: 20px;
  margin-top: 16px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.06);
}

.comparison-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.comparison-item {
  padding: 16px;
  background: #f9fafb;
  border-radius: 12px;
}

.comparison-label {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 8px;
}

.comparison-values {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.value-current {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
}

.value-current .unit {
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  margin-left: 2px;
}

.value-compare {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 8px;
}

.value-compare.good {
  background: #dcfce7;
  color: #16a34a;
}

/* AI总结 */
.ai-summary-card {
  background: #fff;
  border-radius: 20px;
  padding: 20px;
  margin-top: 16px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.06);
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.ai-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.summary-title {
  font-size: 16px;
  font-weight: 700;
  color: #1f2937;
}

.ai-message {
  font-size: 14px;
  color: #4b5563;
  line-height: 1.6;
  margin-bottom: 16px;
}

.ai-suggestions {
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

.suggestions-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 12px;
}

.suggestion-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.suggestion-list li {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.6;
  padding-left: 20px;
  position: relative;
  margin-bottom: 8px;
}

.suggestion-list li::before {
  content: '•';
  position: absolute;
  left: 8px;
  color: #10b981;
  font-weight: 700;
}

/* 周期选择抽屉 */
.period-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.period-option {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.period-option:hover {
  background: #f3f4f6;
}

.period-option.selected {
  background: #f0fdf4;
  border-color: #10b981;
}

.period-icon {
  font-size: 24px;
}

.period-label {
  flex: 1;
  font-size: 15px;
  font-weight: 500;
  color: #1f2937;
}

.check-icon {
  color: #10b981;
  font-size: 18px;
}
</style>
