<template>
  <div class="bg-slate-700/40 backdrop-blur-sm rounded-xl border border-slate-400/60 p-4 shadow-lg">
    <v-chart :option="chartOption" :style="{ height: '280px', width: '100%' }" autoresize />
    <div class="mt-3 flex items-center justify-between text-xs text-slate-300">
      <div class="flex items-center gap-4">
        <span class="flex items-center gap-1.5">
          <span class="w-4 h-0.5 bg-amber-500"></span>
          <span class="text-slate-100">血糖曲线</span>
        </span>
        <span class="flex items-center gap-1.5">
          <span class="w-4 h-0.5 border-t-2 border-dashed border-red-500"></span>
          <span class="text-slate-100">安全阈值</span>
        </span>
      </div>
      <span class="font-mono font-bold text-amber-300">CV: {{ cv }}%</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, TitleComponent, MarkLineComponent } from 'echarts/components'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, TitleComponent, MarkLineComponent])

interface CGMDataPoint { time: string; glucose: number }

const props = withDefaults(defineProps<{
  data?: CGMDataPoint[]
  cv?: number
}>(), {
  cv: 42,
})

const cgmData = computed(() => {
  if (props.data?.length) return props.data
  const result: CGMDataPoint[] = []
  const start = new Date('2024-01-15T00:00:00')
  for (let i = 0; i < 48; i++) {
    const t = new Date(start.getTime() + i * 30 * 60000)
    const h = t.getHours()
    let base = 100
    if (h >= 7 && h <= 9) base = 160
    else if (h >= 12 && h <= 14) base = 180
    else if (h >= 18 && h <= 20) base = 170
    else if (h >= 2 && h <= 4) base = 70
    result.push({
      time: t.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      glucose: Math.round(Math.max(60, Math.min(250, base + (Math.random() - 0.5) * 40))),
    })
  }
  return result
})

const chartOption = computed(() => ({
  backgroundColor: 'transparent',
  title: { text: '连续血糖监测 (CGM)', textStyle: { fontSize: 14, fontWeight: 'bold', color: '#f1f5f9' }, left: 10, top: 10 },
  tooltip: {
    trigger: 'axis',
    formatter: (params: any) => `${params[0].name}<br/>血糖: ${params[0].value} mg/dL`,
  },
  grid: { left: 50, right: 20, top: 50, bottom: 40 },
  xAxis: {
    type: 'category',
    data: cgmData.value.map(d => d.time),
    axisLabel: { rotate: 45, fontSize: 10, interval: 5, color: '#cbd5e1' },
    axisLine: { lineStyle: { color: '#94a3b8' } },
  },
  yAxis: {
    type: 'value', name: 'mg/dL', min: 60, max: 250,
    nameTextStyle: { color: '#cbd5e1' },
    axisLabel: { color: '#cbd5e1' },
    splitLine: { lineStyle: { color: '#64748b', type: 'dashed' } },
  },
  series: [{
    name: '血糖', type: 'line', data: cgmData.value.map(d => d.glucose),
    smooth: true, symbolSize: 4,
    lineStyle: { width: 3, color: '#f59e0b' },
    itemStyle: { color: '#f59e0b' },
    areaStyle: {
      color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [{ offset: 0, color: 'rgba(245,158,11,0.4)' }, { offset: 1, color: 'rgba(245,158,11,0.05)' }] },
    },
    markLine: {
      silent: true,
      lineStyle: { color: '#ef4444', type: 'dashed', width: 2 },
      label: { color: '#fca5a5', fontSize: 10 },
      data: [
        { yAxis: 180, label: { formatter: '高血糖线', position: 'end' } },
        { yAxis: 70, label: { formatter: '低血糖线', position: 'end' } },
      ],
    },
  }],
}))
</script>
