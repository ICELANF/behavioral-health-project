<template>
  <div class="student-health-data">
    <a-page-header
      :title="studentName"
      sub-title="健康数据"
      @back="() => $router.back()"
    />

    <a-spin :spinning="loading">
      <!-- 时间范围选择 -->
      <a-card size="small" style="margin-bottom: 16px">
        <a-space>
          <span>时间范围：</span>
          <a-radio-group v-model:value="days" @change="loadAll" button-style="solid" size="small">
            <a-radio-button :value="3">3天</a-radio-button>
            <a-radio-button :value="7">7天</a-radio-button>
            <a-radio-button :value="14">14天</a-radio-button>
            <a-radio-button :value="30">30天</a-radio-button>
          </a-radio-group>
        </a-space>
      </a-card>

      <a-row :gutter="16">
        <!-- 血糖趋势 -->
        <a-col :span="12">
          <a-card title="血糖趋势" size="small" style="margin-bottom: 16px">
            <template #extra>
              <a-tag color="blue">{{ glucoseData.length }} 条记录</a-tag>
            </template>
            <div v-if="glucoseData.length === 0" class="empty-hint">暂无血糖数据</div>
            <div v-else>
              <!-- 统计概览 -->
              <a-row :gutter="8" style="margin-bottom: 12px">
                <a-col :span="8">
                  <a-statistic title="平均值" :value="glucoseStats.avg" suffix="mmol/L" :precision="1" :value-style="{ fontSize: '18px' }" />
                </a-col>
                <a-col :span="8">
                  <a-statistic title="最高" :value="glucoseStats.max" suffix="mmol/L" :precision="1" :value-style="{ fontSize: '18px', color: glucoseStats.max > 10 ? '#ff4d4f' : '#52c41a' }" />
                </a-col>
                <a-col :span="8">
                  <a-statistic title="最低" :value="glucoseStats.min" suffix="mmol/L" :precision="1" :value-style="{ fontSize: '18px' }" />
                </a-col>
              </a-row>
              <!-- 简易条形图 -->
              <div class="bar-chart">
                <div v-for="(item, idx) in glucoseChartData" :key="idx" class="bar-item">
                  <div class="bar-value">{{ item.value.toFixed(1) }}</div>
                  <div class="bar" :style="{ height: item.height + 'px', background: item.color }" />
                  <div class="bar-label">{{ item.label }}</div>
                </div>
              </div>
            </div>
          </a-card>
        </a-col>

        <!-- 睡眠评分 -->
        <a-col :span="12">
          <a-card title="睡眠评分" size="small" style="margin-bottom: 16px">
            <template #extra>
              <a-tag color="purple">{{ sleepData.length }} 条记录</a-tag>
            </template>
            <div v-if="sleepData.length === 0" class="empty-hint">暂无睡眠数据</div>
            <div v-else>
              <a-row :gutter="8" style="margin-bottom: 12px">
                <a-col :span="8">
                  <a-statistic title="平均时长" :value="sleepStats.avgMinutes" suffix="分钟" :value-style="{ fontSize: '18px' }" />
                </a-col>
                <a-col :span="8">
                  <a-statistic title="平均评分" :value="sleepStats.avgScore" :precision="0" :value-style="{ fontSize: '18px' }" />
                </a-col>
                <a-col :span="8">
                  <a-statistic title="深睡占比" :value="sleepStats.deepPercent" suffix="%" :precision="0" :value-style="{ fontSize: '18px' }" />
                </a-col>
              </a-row>
              <div class="bar-chart">
                <div v-for="(item, idx) in sleepChartData" :key="idx" class="bar-item">
                  <div class="bar-value">{{ item.value }}</div>
                  <div class="bar" :style="{ height: item.height + 'px', background: '#722ed1' }" />
                  <div class="bar-label">{{ item.label }}</div>
                </div>
              </div>
            </div>
          </a-card>
        </a-col>

        <!-- 运动步数 -->
        <a-col :span="12">
          <a-card title="运动步数" size="small" style="margin-bottom: 16px">
            <template #extra>
              <a-tag color="green">{{ activityData.length }} 条记录</a-tag>
            </template>
            <div v-if="activityData.length === 0" class="empty-hint">暂无运动数据</div>
            <div v-else>
              <a-row :gutter="8" style="margin-bottom: 12px">
                <a-col :span="8">
                  <a-statistic title="日均步数" :value="activityStats.avgSteps" :value-style="{ fontSize: '18px' }" />
                </a-col>
                <a-col :span="8">
                  <a-statistic title="最高步数" :value="activityStats.maxSteps" :value-style="{ fontSize: '18px', color: '#52c41a' }" />
                </a-col>
                <a-col :span="8">
                  <a-statistic title="日均活跃" :value="activityStats.avgActiveMin" suffix="分钟" :value-style="{ fontSize: '18px' }" />
                </a-col>
              </a-row>
              <div class="bar-chart">
                <div v-for="(item, idx) in activityChartData" :key="idx" class="bar-item">
                  <div class="bar-value">{{ formatSteps(item.value) }}</div>
                  <div class="bar" :style="{ height: item.height + 'px', background: '#52c41a' }" />
                  <div class="bar-label">{{ item.label }}</div>
                </div>
              </div>
            </div>
          </a-card>
        </a-col>

        <!-- 体重变化 -->
        <a-col :span="12">
          <a-card title="体重变化" size="small" style="margin-bottom: 16px">
            <template #extra>
              <a-tag color="orange">{{ vitalsData.length }} 条记录</a-tag>
            </template>
            <div v-if="vitalsData.length === 0" class="empty-hint">暂无体重数据</div>
            <div v-else>
              <a-row :gutter="8" style="margin-bottom: 12px">
                <a-col :span="8">
                  <a-statistic title="最新体重" :value="vitalsStats.latest" suffix="kg" :precision="1" :value-style="{ fontSize: '18px' }" />
                </a-col>
                <a-col :span="8">
                  <a-statistic title="变化" :precision="1" :value-style="{ fontSize: '18px', color: vitalsStats.change > 0 ? '#ff4d4f' : '#52c41a' }">
                    <template #formatter>
                      {{ vitalsStats.change > 0 ? '+' : '' }}{{ vitalsStats.change.toFixed(1) }} kg
                    </template>
                  </a-statistic>
                </a-col>
                <a-col :span="8">
                  <a-statistic title="最低" :value="vitalsStats.min" suffix="kg" :precision="1" :value-style="{ fontSize: '18px' }" />
                </a-col>
              </a-row>
              <div class="bar-chart">
                <div v-for="(item, idx) in vitalsChartData" :key="idx" class="bar-item">
                  <div class="bar-value">{{ item.value.toFixed(1) }}</div>
                  <div class="bar" :style="{ height: item.height + 'px', background: '#fa8c16' }" />
                  <div class="bar-label">{{ item.label }}</div>
                </div>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import request from '@/api/request'

const route = useRoute()
const studentId = route.params.id as string
const studentName = ref('学员')
const loading = ref(false)
const days = ref(7)

const glucoseData = ref<any[]>([])
const sleepData = ref<any[]>([])
const activityData = ref<any[]>([])
const vitalsData = ref<any[]>([])

// 统计计算
const glucoseStats = computed(() => {
  if (glucoseData.value.length === 0) return { avg: 0, max: 0, min: 0 }
  const values = glucoseData.value.map(r => r.value)
  return {
    avg: values.reduce((a, b) => a + b, 0) / values.length,
    max: Math.max(...values),
    min: Math.min(...values),
  }
})

const sleepStats = computed(() => {
  if (sleepData.value.length === 0) return { avgMinutes: 0, avgScore: 0, deepPercent: 0 }
  const mins = sleepData.value.map(r => r.total_minutes || 0)
  const scores = sleepData.value.map(r => r.sleep_score || 0).filter(s => s > 0)
  const deepMins = sleepData.value.map(r => r.deep_minutes || 0)
  const totalMins = mins.reduce((a, b) => a + b, 0)
  const totalDeep = deepMins.reduce((a, b) => a + b, 0)
  return {
    avgMinutes: Math.round(totalMins / mins.length),
    avgScore: scores.length > 0 ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0,
    deepPercent: totalMins > 0 ? Math.round(totalDeep / totalMins * 100) : 0,
  }
})

const activityStats = computed(() => {
  if (activityData.value.length === 0) return { avgSteps: 0, maxSteps: 0, avgActiveMin: 0 }
  const steps = activityData.value.map(r => r.steps || 0)
  const activeMins = activityData.value.map(r => r.active_minutes || 0)
  return {
    avgSteps: Math.round(steps.reduce((a, b) => a + b, 0) / steps.length),
    maxSteps: Math.max(...steps),
    avgActiveMin: Math.round(activeMins.reduce((a, b) => a + b, 0) / activeMins.length),
  }
})

const vitalsStats = computed(() => {
  if (vitalsData.value.length === 0) return { latest: 0, change: 0, min: 0 }
  const values = vitalsData.value.map(r => r.value)
  return {
    latest: values[0],
    change: values[0] - values[values.length - 1],
    min: Math.min(...values),
  }
})

// 图表数据生成（简易条形图）
const makeChartData = (data: any[], valueKey: string, labelKey: string, maxBarHeight: number = 80) => {
  if (data.length === 0) return []
  const values = data.map(d => d[valueKey] || 0)
  const maxVal = Math.max(...values, 1)
  // 最多显示最近10条，从旧到新
  const recent = data.slice(0, 10).reverse()
  return recent.map(d => {
    const val = d[valueKey] || 0
    const label = d[labelKey] || ''
    const shortLabel = typeof label === 'string' && label.length > 5 ? label.slice(5) : label
    return {
      value: val,
      height: Math.max(4, (val / maxVal) * maxBarHeight),
      label: shortLabel,
      color: val > maxVal * 0.8 ? '#ff4d4f' : '#1890ff',
    }
  })
}

const glucoseChartData = computed(() =>
  makeChartData(glucoseData.value, 'value', 'recorded_at')
)

const sleepChartData = computed(() =>
  makeChartData(sleepData.value, 'sleep_score', 'sleep_date')
)

const activityChartData = computed(() =>
  makeChartData(activityData.value, 'steps', 'activity_date')
)

const vitalsChartData = computed(() =>
  makeChartData(vitalsData.value, 'value', 'recorded_at')
)

const formatSteps = (val: number) => {
  if (val >= 10000) return (val / 10000).toFixed(1) + 'w'
  if (val >= 1000) return (val / 1000).toFixed(1) + 'k'
  return String(val)
}

// API 调用
const loadGlucose = async () => {
  try {
    const res = await request.get(`/v1/coach/students/${studentId}/glucose`, { params: { days: days.value } })
    glucoseData.value = res.data.readings || []
    if (res.data.student_name) studentName.value = res.data.student_name
  } catch (e) {
    console.warn('Failed to load glucose', e)
  }
}

const loadSleep = async () => {
  try {
    const res = await request.get(`/v1/coach/students/${studentId}/sleep`, { params: { days: days.value } })
    sleepData.value = res.data.records || []
    if (res.data.student_name) studentName.value = res.data.student_name
  } catch (e) {
    console.warn('Failed to load sleep', e)
  }
}

const loadActivity = async () => {
  try {
    const res = await request.get(`/v1/coach/students/${studentId}/activity`, { params: { days: days.value } })
    activityData.value = res.data.records || []
  } catch (e) {
    console.warn('Failed to load activity', e)
  }
}

const loadVitals = async () => {
  try {
    const res = await request.get(`/v1/coach/students/${studentId}/vitals`, { params: { data_type: 'weight', days: Math.max(days.value, 30) } })
    vitalsData.value = res.data.records || []
  } catch (e) {
    console.warn('Failed to load vitals', e)
  }
}

const loadAll = async () => {
  loading.value = true
  await Promise.all([loadGlucose(), loadSleep(), loadActivity(), loadVitals()])
  loading.value = false
}

onMounted(() => {
  loadAll()
})
</script>

<style scoped>
.student-health-data {
  padding: 0;
}

.empty-hint {
  text-align: center;
  color: #999;
  padding: 32px 0;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  gap: 6px;
  height: 120px;
  padding-top: 20px;
}

.bar-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 0;
}

.bar-value {
  font-size: 10px;
  color: #666;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.bar {
  width: 100%;
  max-width: 24px;
  border-radius: 2px 2px 0 0;
  min-height: 4px;
  transition: height 0.3s;
}

.bar-label {
  font-size: 9px;
  color: #999;
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}
</style>
