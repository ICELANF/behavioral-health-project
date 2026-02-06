<template>
  <div class="page-container">
    <van-nav-bar title="健康看板">
      <template #right>
        <span class="date-display">{{ currentDate }}</span>
      </template>
    </van-nav-bar>

    <div class="page-content">
      <!-- 综合评分卡片 -->
      <div class="score-cards">
        <div class="score-card overall">
          <div class="score-value">{{ dashboardData.overall_score }}</div>
          <div class="score-label">综合</div>
        </div>
        <div class="score-card stress">
          <div class="score-value">{{ dashboardData.stress_score }}</div>
          <div class="score-label">压力</div>
        </div>
        <div class="score-card fatigue">
          <div class="score-value">{{ dashboardData.fatigue_score }}</div>
          <div class="score-label">疲劳</div>
        </div>
      </div>

      <!-- 趋势图表 -->
      <div class="trend-card card">
        <h3>趋势分析</h3>
        <div class="chart-container" ref="chartRef"></div>
      </div>

      <!-- 风险评估 -->
      <div class="risk-card card" :class="'risk-' + dashboardData.risk_level">
        <div class="risk-header">
          <van-icon :name="riskIcon" :color="riskColor" size="24" />
          <span class="risk-level">{{ riskText }}风险</span>
        </div>
        <ul class="risk-details">
          <li v-for="(item, index) in dashboardData.recommendations" :key="index">
            {{ item }}
          </li>
        </ul>
      </div>

      <!-- 查看报告按钮 -->
      <van-button type="primary" block round class="report-btn" @click="viewFullReport" :loading="reportLoading">
        查看完整报告
      </van-button>

      <!-- 报告弹层 -->
      <van-popup v-model:show="showReport" position="bottom" round :style="{ height: '85%' }">
        <div class="report-popup">
          <van-nav-bar title="健康报告" left-arrow @click-left="showReport = false" />
          <div class="report-content" v-if="reportData">
            <div class="report-section" v-for="(section, idx) in reportData.sections" :key="idx">
              <h3>{{ section.title }}</h3>
              <p>{{ section.content }}</p>
            </div>
          </div>
          <van-empty v-else description="暂无报告数据" />
        </div>
      </van-popup>
    </div>

    <TabBar />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import * as echarts from 'echarts'
import { showLoadingToast, closeToast, showToast } from 'vant'
import TabBar from '@/components/common/TabBar.vue'
import { useUserStore } from '@/stores/user'
import dashboardApi from '@/api/dashboard'
import { fetchFullReport } from '@/api/report'
import type { DashboardData } from '@/api/types'

const chartRef = ref<HTMLElement>()
const userStore = useUserStore()
const isLoading = ref(false)
const reportLoading = ref(false)
const showReport = ref(false)
const reportData = ref<any>(null)

const dashboardData = ref<DashboardData>({
  overall_score: 0,
  stress_score: 0,
  fatigue_score: 0,
  trend: [],
  risk_level: 'medium',
  recommendations: []
})

const currentDate = computed(() => {
  const now = new Date()
  return `${now.getMonth() + 1}月${now.getDate()}日`
})

const riskIcon = computed(() => {
  const icons: Record<string, string> = {
    low: 'checked',
    medium: 'warning-o',
    high: 'close'
  }
  return icons[dashboardData.value.risk_level]
})

const riskColor = computed(() => {
  const colors: Record<string, string> = {
    low: '#07c160',
    medium: '#ff976a',
    high: '#ee0a24'
  }
  return colors[dashboardData.value.risk_level]
})

const riskText = computed(() => {
  const texts: Record<string, string> = {
    low: '低',
    medium: '中等',
    high: '高'
  }
  return texts[dashboardData.value.risk_level]
})

onMounted(async () => {
  await loadDashboardData()
})

async function loadDashboardData() {
  isLoading.value = true
  showLoadingToast({ message: '加载中...', forbidClick: true })

  try {
    const data = await dashboardApi.getDashboard(userStore.userId)
    dashboardData.value = data
    // 数据加载完成后初始化图表
    setTimeout(() => initChart(), 100)
  } catch (error) {
    console.error('Failed to load dashboard:', error)
    showToast('数据加载失败，显示模拟数据')
    // 使用模拟数据
    dashboardData.value = {
      overall_score: 64,
      stress_score: 55,
      fatigue_score: 50,
      trend: [
        { date: '01-17', score: 58 },
        { date: '01-18', score: 62 },
        { date: '01-19', score: 60 },
        { date: '01-20', score: 65 },
        { date: '01-21', score: 63 },
        { date: '01-22', score: 64 },
        { date: '01-23', score: 64 }
      ],
      risk_level: 'medium',
      recommendations: [
        '压力指数偏高，建议增加放松活动',
        '睡眠质量有待改善',
        '建议每天进行 10 分钟深呼吸练习'
      ]
    }
    setTimeout(() => initChart(), 100)
  } finally {
    isLoading.value = false
    closeToast()
  }
}

async function viewFullReport() {
  reportLoading.value = true
  try {
    const data = await fetchFullReport()
    reportData.value = data
    showReport.value = true
  } catch (error) {
    console.error('Failed to load report:', error)
    // 使用模拟报告数据
    reportData.value = {
      sections: [
        { title: '健康档案', content: `综合评分 ${dashboardData.value.overall_score} 分，压力指数 ${dashboardData.value.stress_score} 分。整体状态${dashboardData.value.risk_level === 'low' ? '良好' : dashboardData.value.risk_level === 'medium' ? '需关注' : '需干预'}。` },
        { title: '行为任务进度', content: '本周完成 3 项微习惯任务，行动阶段稳步推进中。坚持打卡有助于巩固行为转变。' },
        { title: '趋势与建议', content: dashboardData.value.recommendations.join('；') + '。持续保持健康习惯，你的每一步都在被记录。' }
      ]
    }
    showReport.value = true
  } finally {
    reportLoading.value = false
  }
}

function initChart() {
  if (!chartRef.value) return

  const chart = echarts.init(chartRef.value)
  const option = {
    grid: {
      top: 20,
      right: 20,
      bottom: 30,
      left: 40
    },
    xAxis: {
      type: 'category',
      data: dashboardData.value.trend.map(t => t.date),
      axisLine: { lineStyle: { color: '#eee' } },
      axisLabel: { color: '#999', fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLine: { show: false },
      axisLabel: { color: '#999', fontSize: 10 },
      splitLine: { lineStyle: { color: '#f5f5f5' } }
    },
    series: [{
      type: 'line',
      data: dashboardData.value.trend.map(t => t.score),
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: { color: '#1989fa', width: 2 },
      itemStyle: { color: '#1989fa' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(25, 137, 250, 0.3)' },
          { offset: 1, color: 'rgba(25, 137, 250, 0.05)' }
        ])
      }
    }]
  }
  chart.setOption(option)
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.date-display {
  font-size: $font-size-sm;
  color: $text-color-secondary;
}

.score-cards {
  display: flex;
  gap: $spacing-sm;
  margin-bottom: $spacing-md;

  .score-card {
    flex: 1;
    padding: $spacing-md;
    border-radius: $border-radius-lg;
    text-align: center;
    background-color: $background-color-light;
    box-shadow: $shadow-sm;

    .score-value {
      font-size: 28px;
      font-weight: bold;
    }

    .score-label {
      font-size: $font-size-sm;
      color: $text-color-secondary;
      margin-top: 4px;
    }

    &.overall .score-value { color: $primary-color; }
    &.stress .score-value { color: $warning-color; }
    &.fatigue .score-value { color: $expert-mental; }
  }
}

.trend-card {
  h3 {
    font-size: $font-size-lg;
    margin-bottom: $spacing-sm;
  }

  .chart-container {
    height: 200px;
  }
}

.risk-card {
  border-left: 4px solid;

  &.risk-low { border-left-color: $success-color; }
  &.risk-medium { border-left-color: $warning-color; }
  &.risk-high { border-left-color: $danger-color; }

  .risk-header {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    margin-bottom: $spacing-sm;

    .risk-level {
      font-size: $font-size-lg;
      font-weight: 500;
    }
  }

  .risk-details {
    margin: 0;
    padding-left: $spacing-lg;
    color: $text-color-secondary;
    font-size: $font-size-sm;
    line-height: 1.8;
  }
}

.report-btn {
  margin-top: $spacing-md;
}

.report-popup {
  height: 100%;
  display: flex;
  flex-direction: column;

  .report-content {
    flex: 1;
    overflow-y: auto;
    padding: $spacing-md;

    .report-section {
      margin-bottom: $spacing-lg;

      h3 {
        font-size: $font-size-lg;
        margin-bottom: $spacing-xs;
        color: $primary-color;
      }

      p {
        font-size: $font-size-md;
        color: $text-color-secondary;
        line-height: 1.8;
      }
    }
  }
}
</style>
