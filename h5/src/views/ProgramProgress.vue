<template>
  <div class="page-container">
    <van-nav-bar title="行为特征" left-arrow @click-left="$router.back()">
      <template #right>
        <van-icon name="clock-o" size="20" @click="$router.push(`/program/${eid}/timeline`)" />
      </template>
    </van-nav-bar>

    <div class="page-content">
      <van-loading v-if="loading" class="loading" />

      <template v-else-if="data">
        <!-- 雷达图 -->
        <div class="radar-card">
          <div class="radar-title">行为特征雷达图</div>
          <div ref="chartRef" class="radar-chart"></div>
        </div>

        <!-- 维度详情 -->
        <div class="dims-card">
          <div class="dims-title">各维度详情</div>
          <div v-for="dim in dimensions" :key="dim.key" class="dim-item">
            <div class="dim-header">
              <span class="dim-label">{{ dim.label }}</span>
              <span class="dim-value">{{ dim.score }}/100</span>
            </div>
            <van-progress
              :percentage="dim.score"
              stroke-width="6"
              :color="dim.color"
              track-color="#ebedf0"
              :show-pivot="false"
            />
            <div v-if="dim.trend" class="dim-trend">
              <van-icon :name="dim.trend > 0 ? 'arrow-up' : 'arrow-down'" :color="dim.trend > 0 ? '#07c160' : '#ee0a24'" size="12" />
              <span :style="{ color: dim.trend > 0 ? '#07c160' : '#ee0a24' }">较上周{{ dim.trend > 0 ? '+' : '' }}{{ dim.trend }}%</span>
            </div>
          </div>
        </div>

        <!-- 建议 -->
        <div v-if="data.suggestions && data.suggestions.length" class="suggest-card">
          <div class="suggest-title">改善建议</div>
          <div v-for="(s, i) in data.suggestions" :key="i" class="suggest-item">
            <van-icon name="bulb-o" color="#fa8c16" />
            <span>{{ s }}</span>
          </div>
        </div>
      </template>

      <van-empty v-else description="暂无数据" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { programApi } from '@/api/program'
import * as echarts from 'echarts'

const route = useRoute()
const eid = route.params.id as string

const loading = ref(true)
const data = ref<any>(null)
const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null
let resizeHandler: (() => void) | null = null

const DIM_META: Record<string, { label: string; color: string }> = {
  compliance: { label: '依从性', color: '#1989fa' },
  knowledge: { label: '知识掌握', color: '#07c160' },
  emotion: { label: '情绪管理', color: '#ff976a' },
  behavior: { label: '行为改善', color: '#7232dd' },
  engagement: { label: '参与度', color: '#fa8c16' },
}

const dimensions = computed(() => {
  if (!data.value?.profile) return []
  const p = data.value.profile
  return Object.keys(DIM_META).map(k => ({
    key: k,
    label: DIM_META[k].label,
    color: DIM_META[k].color,
    score: Math.round((p[k] || 0) * 100) / 100,
    trend: p[`${k}_trend`] || null,
  }))
})

const initChart = () => {
  if (!chartRef.value || !data.value?.profile) return
  chartInstance?.dispose()
  const chart = echarts.init(chartRef.value)
  chartInstance = chart
  const profile = data.value.profile
  const keys = Object.keys(DIM_META)
  const labels = keys.map(k => DIM_META[k].label)
  const values = keys.map(k => Math.round((profile[k] || 0) * 100) / 100)

  chart.setOption({
    radar: {
      indicator: labels.map(name => ({ name, max: 100 })),
      shape: 'polygon',
      radius: '65%',
      axisName: { color: '#666', fontSize: 12 },
    },
    series: [{
      type: 'radar',
      data: [{
        value: values,
        name: '行为特征',
        areaStyle: { color: 'rgba(25,137,250,0.15)' },
        lineStyle: { color: '#1989fa', width: 2 },
        itemStyle: { color: '#1989fa' },
      }],
    }],
  })

  resizeHandler = () => chart.resize()
  window.addEventListener('resize', resizeHandler)
}

onUnmounted(() => {
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
    resizeHandler = null
  }
  chartInstance?.dispose()
  chartInstance = null
})

onMounted(async () => {
  try {
    const res: any = await programApi.getProgress(eid)
    data.value = res
    await nextTick()
    initChart()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-container { min-height: 100vh; background: #f5f5f5; }
.page-content { padding: 12px; }
.loading { text-align: center; padding: 60px 0; }

.radar-card, .dims-card, .suggest-card {
  background: #fff; border-radius: 12px; padding: 14px; margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.radar-title, .dims-title, .suggest-title {
  font-size: 15px; font-weight: 600; color: #333; margin-bottom: 10px;
}
.radar-chart { width: 100%; height: 260px; }

.dim-item { margin-bottom: 14px; }
.dim-header { display: flex; justify-content: space-between; margin-bottom: 6px; }
.dim-label { font-size: 13px; color: #333; }
.dim-value { font-size: 13px; color: #1989fa; font-weight: 600; }
.dim-trend { display: flex; align-items: center; gap: 4px; margin-top: 4px; font-size: 12px; }

.suggest-item { display: flex; align-items: flex-start; gap: 6px; font-size: 13px; color: #666; margin-bottom: 8px; line-height: 1.5; }
</style>
