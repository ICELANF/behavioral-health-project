<template>
  <div class="page-container">
    <van-nav-bar title="健康看板">
      <template #right>
        <span class="date-display">{{ currentDate }}</span>
      </template>
    </van-nav-bar>

    <div class="page-content">
      <!-- 加载失败提示 -->
      <van-empty v-if="loadError" description="数据加载失败">
        <van-button type="primary" size="small" round @click="loadError = false; loadDashboardData()">重新加载</van-button>
      </van-empty>

      <template v-else>
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
          <AiContentBadge :review-status="dashboardData.review_status" compact style="margin-left:auto" />
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
          <van-empty v-else-if="reportError" description="报告加载失败">
            <van-button type="primary" size="small" round @click="viewFullReport()">重新加载</van-button>
          </van-empty>
          <van-empty v-else description="暂无报告数据" />
        </div>
      </van-popup>
      </template>
    </div>

    <TabBar />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { showLoadingToast, closeToast, showToast } from 'vant'
import TabBar from '@/components/common/TabBar.vue'
import AiContentBadge from '@/components/common/AiContentBadge.vue'
import dashboardApi from '@/api/dashboard'
import { fetchFullReport } from '@/api/report'
import type { DashboardData } from '@/api/types'

const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null
const isLoading = ref(false)
const reportLoading = ref(false)
const showReport = ref(false)
const reportData = ref<any>(null)
const reportError = ref(false)

const dashboardData = ref<DashboardData>({
  overall_score: 0,
  stress_score: 0,
  fatigue_score: 0,
  trend: [],
  risk_level: 'medium',
  recommendations: []
})
const loadError = ref(false)

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
    const data = await dashboardApi.getDashboard()
    dashboardData.value = data
    // 数据加载完成后初始化图表
    setTimeout(() => initChart(), 100)
  } catch (error) {
    console.error('Failed to load dashboard:', error)
    loadError.value = true
    showToast('数据加载失败，请稍后重试')
  } finally {
    isLoading.value = false
    closeToast()
  }
}

async function viewFullReport() {
  reportLoading.value = true
  reportError.value = false
  try {
    const data = await fetchFullReport()
    reportData.value = data
    showReport.value = true
  } catch (error) {
    console.error('Failed to load report:', error)
    reportData.value = null
    reportError.value = true
    showReport.value = true
  } finally {
    reportLoading.value = false
  }
}

function initChart() {
  if (!chartRef.value) return

  chartInstance?.dispose()
  const chart = echarts.init(chartRef.value)
  chartInstance = chart
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

onUnmounted(() => {
  chartInstance?.dispose()
  chartInstance = null
})
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
