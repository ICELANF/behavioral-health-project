<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDeviceStore } from '@/stores/device'
import { showToast } from 'vant'

const router = useRouter()
const deviceStore = useDeviceStore()

// 录入弹窗状态
const showGlucoseDialog = ref(false)
const showWeightDialog = ref(false)
const showBPDialog = ref(false)

// 录入表单
const glucoseForm = ref({
  value: '',
  mealTag: 'fasting'
})

const weightForm = ref({
  value: '',
  bodyFat: ''
})

const bpForm = ref({
  systolic: '',
  diastolic: '',
  pulse: ''
})

// 餐标选项
const mealTagOptions = [
  { text: '空腹', value: 'fasting' },
  { text: '餐前', value: 'before_meal' },
  { text: '餐后', value: 'after_meal' },
  { text: '睡前', value: 'bedtime' }
]

// 血糖状态颜色
const glucoseStatusColor = computed(() => {
  const status = deviceStore.dashboard?.glucose?.status
  if (status === 'low') return '#ee0a24'
  if (status === 'high') return '#ff976a'
  return '#07c160'
})

// 血糖状态文字
const glucoseStatusText = computed(() => {
  const status = deviceStore.dashboard?.glucose?.status
  if (status === 'low') return '偏低'
  if (status === 'high') return '偏高'
  return '正常'
})

// 格式化时间
const formatTime = (isoString: string) => {
  if (!isoString) return ''
  const date = new Date(isoString)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

// 提交血糖
const submitGlucose = async () => {
  const value = parseFloat(glucoseForm.value.value)
  if (isNaN(value) || value < 1 || value > 35) {
    showToast('请输入有效的血糖值 (1-35)')
    return
  }

  try {
    await deviceStore.recordGlucose(value, glucoseForm.value.mealTag)
    showGlucoseDialog.value = false
    glucoseForm.value.value = ''
    await deviceStore.loadDashboard()
  } catch (error) {
    console.error('Submit glucose error:', error)
  }
}

// 提交体重
const submitWeight = async () => {
  const weight = parseFloat(weightForm.value.value)
  if (isNaN(weight) || weight < 20 || weight > 300) {
    showToast('请输入有效的体重 (20-300 kg)')
    return
  }

  const bodyFat = weightForm.value.bodyFat ? parseFloat(weightForm.value.bodyFat) : undefined

  try {
    await deviceStore.recordWeight(weight, bodyFat)
    showWeightDialog.value = false
    weightForm.value.value = ''
    weightForm.value.bodyFat = ''
    await deviceStore.loadDashboard()
  } catch (error) {
    console.error('Submit weight error:', error)
  }
}

// 提交血压
const submitBP = async () => {
  const systolic = parseInt(bpForm.value.systolic)
  const diastolic = parseInt(bpForm.value.diastolic)
  const pulse = bpForm.value.pulse ? parseInt(bpForm.value.pulse) : undefined

  if (isNaN(systolic) || systolic < 60 || systolic > 250) {
    showToast('请输入有效的收缩压 (60-250)')
    return
  }
  if (isNaN(diastolic) || diastolic < 40 || diastolic > 150) {
    showToast('请输入有效的舒张压 (40-150)')
    return
  }

  try {
    await deviceStore.recordBloodPressure(systolic, diastolic, pulse)
    showBPDialog.value = false
    bpForm.value.systolic = ''
    bpForm.value.diastolic = ''
    bpForm.value.pulse = ''
    await deviceStore.loadDashboard()
  } catch (error) {
    console.error('Submit BP error:', error)
  }
}

// 返回
const goBack = () => {
  router.back()
}

// 刷新数据
const onRefresh = async () => {
  await deviceStore.loadDashboard()
}

onMounted(async () => {
  await deviceStore.init()
})
</script>

<template>
  <div class="health-data-page">
    <!-- 导航栏 -->
    <van-nav-bar
      title="健康数据"
      left-arrow
      @click-left="goBack"
    />

    <!-- 下拉刷新 -->
    <van-pull-refresh v-model="deviceStore.loading" @refresh="onRefresh">
      <div class="content">
        <!-- 血糖卡片 -->
        <div class="data-card glucose-card">
          <div class="card-header">
            <div class="card-title">
              <van-icon name="chart-trending-o" />
              <span>血糖</span>
            </div>
            <van-button size="small" type="primary" plain @click="showGlucoseDialog = true">
              记录
            </van-button>
          </div>

          <div class="card-body" v-if="deviceStore.dashboard?.glucose">
            <div class="main-value">
              <span class="value" :style="{ color: glucoseStatusColor }">
                {{ deviceStore.dashboard.glucose.current }}
              </span>
              <span class="unit">mmol/L</span>
              <span class="trend" v-if="deviceStore.dashboard.glucose.trend_arrow">
                {{ deviceStore.dashboard.glucose.trend_arrow }}
              </span>
            </div>
            <div class="status-row">
              <van-tag :type="deviceStore.dashboard.glucose.status === 'good' ? 'success' : 'warning'">
                {{ glucoseStatusText }}
              </van-tag>
              <span class="time">{{ formatTime(deviceStore.dashboard.glucose.last_reading_at) }}</span>
            </div>
            <div class="stats-row">
              <div class="stat-item">
                <span class="label">今日均值</span>
                <span class="value">{{ deviceStore.dashboard.glucose.avg_today || '-' }}</span>
              </div>
              <div class="stat-item">
                <span class="label">TIR</span>
                <span class="value">{{ deviceStore.dashboard.glucose.tir_today || '-' }}%</span>
              </div>
              <div class="stat-item">
                <span class="label">记录数</span>
                <span class="value">{{ deviceStore.dashboard.glucose.readings_count }}</span>
              </div>
            </div>
          </div>
          <div class="card-body empty" v-else>
            <van-empty description="暂无血糖数据" image-size="60" />
          </div>
        </div>

        <!-- 体重卡片 -->
        <div class="data-card weight-card">
          <div class="card-header">
            <div class="card-title">
              <van-icon name="user-o" />
              <span>体重</span>
            </div>
            <van-button size="small" type="primary" plain @click="showWeightDialog = true">
              记录
            </van-button>
          </div>

          <div class="card-body" v-if="deviceStore.dashboard?.weight">
            <div class="main-value">
              <span class="value">{{ deviceStore.dashboard.weight.weight_kg }}</span>
              <span class="unit">kg</span>
            </div>
            <div class="info-row" v-if="deviceStore.dashboard.weight.bmi">
              <span>BMI: {{ deviceStore.dashboard.weight.bmi }}</span>
            </div>
          </div>
          <div class="card-body empty" v-else>
            <van-empty description="暂无体重数据" image-size="60" />
          </div>
        </div>

        <!-- 睡眠卡片 -->
        <div class="data-card sleep-card">
          <div class="card-header">
            <div class="card-title">
              <van-icon name="clock-o" />
              <span>昨晚睡眠</span>
            </div>
          </div>

          <div class="card-body" v-if="deviceStore.lastNightSleep">
            <div class="main-value">
              <span class="value sleep-value">{{ deviceStore.lastNightSleep.duration }}</span>
            </div>
            <div class="status-row">
              <van-tag :type="deviceStore.lastNightSleep.score >= 80 ? 'success' : deviceStore.lastNightSleep.score >= 60 ? 'warning' : 'danger'">
                睡眠评分 {{ deviceStore.lastNightSleep.score }}
              </van-tag>
              <span class="time">{{ deviceStore.lastNightSleep.sleep_start }} - {{ deviceStore.lastNightSleep.sleep_end }}</span>
            </div>
            <div class="sleep-stages" v-if="deviceStore.lastNightSleep.stages">
              <div class="stage-item">
                <span class="label">深睡</span>
                <span class="value">{{ deviceStore.lastNightSleep.stages.deep_min }}分</span>
              </div>
              <div class="stage-item">
                <span class="label">浅睡</span>
                <span class="value">{{ deviceStore.lastNightSleep.stages.light_min }}分</span>
              </div>
              <div class="stage-item">
                <span class="label">REM</span>
                <span class="value">{{ deviceStore.lastNightSleep.stages.rem_min }}分</span>
              </div>
              <div class="stage-item">
                <span class="label">清醒</span>
                <span class="value">{{ deviceStore.lastNightSleep.stages.awake_min }}分</span>
              </div>
            </div>
            <div class="insights" v-if="deviceStore.lastNightSleep.insights?.length">
              <van-tag plain type="primary" v-for="(insight, i) in deviceStore.lastNightSleep.insights" :key="i">
                {{ insight }}
              </van-tag>
            </div>
          </div>
          <div class="card-body empty" v-else>
            <van-empty description="暂无睡眠数据" image-size="60" />
          </div>
        </div>

        <!-- 活动卡片 -->
        <div class="data-card activity-card">
          <div class="card-header">
            <div class="card-title">
              <van-icon name="fire-o" />
              <span>今日活动</span>
            </div>
          </div>

          <div class="card-body" v-if="deviceStore.todayActivity">
            <div class="main-value">
              <span class="value activity-value">{{ deviceStore.todayActivity.steps.toLocaleString() }}</span>
              <span class="unit">步</span>
            </div>
            <div class="activity-stats">
              <div class="stat-item">
                <span class="label">距离</span>
                <span class="value">{{ deviceStore.todayActivity.distance_km }} km</span>
              </div>
              <div class="stat-item">
                <span class="label">消耗</span>
                <span class="value">{{ deviceStore.todayActivity.calories_active }} 千卡</span>
              </div>
              <div class="stat-item">
                <span class="label">活跃</span>
                <span class="value">{{ deviceStore.todayActivity.active_minutes }} 分钟</span>
              </div>
            </div>
          </div>
          <div class="card-body empty" v-else>
            <van-empty description="暂无活动数据" image-size="60" />
          </div>
        </div>

        <!-- 心率/HRV 卡片 -->
        <div class="data-card hr-card" v-if="deviceStore.heartRateStats || deviceStore.hrvStats">
          <div class="card-header">
            <div class="card-title">
              <van-icon name="like-o" />
              <span>心率 / HRV</span>
            </div>
          </div>

          <div class="card-body">
            <div class="hr-hrv-row">
              <div class="hr-section" v-if="deviceStore.heartRateStats">
                <div class="section-title">心率</div>
                <div class="hr-value">
                  <span class="value">{{ deviceStore.heartRateStats.avg_hr || '-' }}</span>
                  <span class="unit">bpm</span>
                </div>
                <div class="hr-range">
                  {{ deviceStore.heartRateStats.min_hr }} - {{ deviceStore.heartRateStats.max_hr }}
                </div>
              </div>
              <div class="hrv-section" v-if="deviceStore.hrvStats">
                <div class="section-title">HRV</div>
                <div class="hrv-value">
                  <span class="value">{{ deviceStore.hrvStats.avg_hrv?.toFixed(1) || '-' }}</span>
                  <span class="unit">ms</span>
                </div>
                <div class="stress-level">
                  压力指数: {{ deviceStore.hrvStats.avg_stress?.toFixed(0) || '-' }}
                  <van-tag size="mini" :type="deviceStore.hrvStats.avg_stress < 40 ? 'success' : 'warning'">
                    {{ deviceStore.hrvStats.trend || '稳定' }}
                  </van-tag>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 快捷记录区 -->
        <div class="quick-actions">
          <div class="action-title">快捷记录</div>
          <van-grid :column-num="3" :border="false">
            <van-grid-item icon="chart-trending-o" text="血糖" @click="showGlucoseDialog = true" />
            <van-grid-item icon="user-o" text="体重" @click="showWeightDialog = true" />
            <van-grid-item icon="like-o" text="血压" @click="showBPDialog = true" />
          </van-grid>
        </div>

        <!-- 告警提示 -->
        <div class="alerts" v-if="deviceStore.dashboard?.alerts?.length">
          <van-notice-bar
            v-for="(alert, index) in deviceStore.dashboard.alerts"
            :key="index"
            :color="alert.severity === 'danger' ? '#ee0a24' : '#ff976a'"
            :background="alert.severity === 'danger' ? '#fff0f0' : '#fff7e8'"
            left-icon="warning-o"
          >
            {{ alert.message }}
          </van-notice-bar>
        </div>

        <!-- 目标范围说明 -->
        <div class="info-section">
          <div class="info-title">血糖目标范围</div>
          <div class="range-bar">
            <div class="range-low">低血糖 &lt;3.9</div>
            <div class="range-target">目标 3.9-10.0</div>
            <div class="range-high">高血糖 &gt;10.0</div>
          </div>
        </div>
      </div>
    </van-pull-refresh>

    <!-- 血糖录入弹窗 -->
    <van-dialog
      v-model:show="showGlucoseDialog"
      title="记录血糖"
      show-cancel-button
      @confirm="submitGlucose"
    >
      <div class="dialog-content">
        <van-field
          v-model="glucoseForm.value"
          type="number"
          label="血糖值"
          placeholder="请输入血糖值"
          input-align="right"
        >
          <template #button>
            <span class="unit-text">mmol/L</span>
          </template>
        </van-field>
        <van-field label="测量时间">
          <template #input>
            <van-radio-group v-model="glucoseForm.mealTag" direction="horizontal">
              <van-radio
                v-for="opt in mealTagOptions"
                :key="opt.value"
                :name="opt.value"
              >
                {{ opt.text }}
              </van-radio>
            </van-radio-group>
          </template>
        </van-field>
      </div>
    </van-dialog>

    <!-- 体重录入弹窗 -->
    <van-dialog
      v-model:show="showWeightDialog"
      title="记录体重"
      show-cancel-button
      @confirm="submitWeight"
    >
      <div class="dialog-content">
        <van-field
          v-model="weightForm.value"
          type="number"
          label="体重"
          placeholder="请输入体重"
          input-align="right"
        >
          <template #button>
            <span class="unit-text">kg</span>
          </template>
        </van-field>
        <van-field
          v-model="weightForm.bodyFat"
          type="number"
          label="体脂率"
          placeholder="选填"
          input-align="right"
        >
          <template #button>
            <span class="unit-text">%</span>
          </template>
        </van-field>
      </div>
    </van-dialog>

    <!-- 血压录入弹窗 -->
    <van-dialog
      v-model:show="showBPDialog"
      title="记录血压"
      show-cancel-button
      @confirm="submitBP"
    >
      <div class="dialog-content">
        <van-field
          v-model="bpForm.systolic"
          type="number"
          label="收缩压"
          placeholder="高压"
          input-align="right"
        >
          <template #button>
            <span class="unit-text">mmHg</span>
          </template>
        </van-field>
        <van-field
          v-model="bpForm.diastolic"
          type="number"
          label="舒张压"
          placeholder="低压"
          input-align="right"
        >
          <template #button>
            <span class="unit-text">mmHg</span>
          </template>
        </van-field>
        <van-field
          v-model="bpForm.pulse"
          type="number"
          label="脉搏"
          placeholder="选填"
          input-align="right"
        >
          <template #button>
            <span class="unit-text">次/分</span>
          </template>
        </van-field>
      </div>
    </van-dialog>
  </div>
</template>

<style scoped>
.health-data-page {
  min-height: 100vh;
  background-color: #f7f8fa;
}

.content {
  padding: 16px;
  padding-bottom: 80px;
}

.data-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 500;
  color: #323233;
}

.card-title .van-icon {
  font-size: 20px;
  color: #1989fa;
}

.card-body.empty {
  padding: 20px 0;
}

.main-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 12px;
}

.main-value .value {
  font-size: 42px;
  font-weight: 600;
  color: #323233;
}

.main-value .unit {
  font-size: 14px;
  color: #969799;
}

.main-value .trend {
  font-size: 24px;
  margin-left: 8px;
}

.status-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.status-row .time {
  font-size: 12px;
  color: #969799;
}

.stats-row {
  display: flex;
  justify-content: space-around;
  padding-top: 12px;
  border-top: 1px solid #ebedf0;
}

.stat-item {
  text-align: center;
}

.stat-item .label {
  display: block;
  font-size: 12px;
  color: #969799;
  margin-bottom: 4px;
}

.stat-item .value {
  font-size: 16px;
  font-weight: 500;
  color: #323233;
}

.info-row {
  font-size: 14px;
  color: #646566;
}

.quick-actions {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}

.action-title {
  font-size: 14px;
  color: #969799;
  margin-bottom: 12px;
}

.quick-actions :deep(.van-grid-item__content) {
  padding: 12px 8px;
}

.quick-actions :deep(.van-grid-item__icon) {
  font-size: 24px;
  color: #1989fa;
}

.quick-actions :deep(.van-grid-item__text) {
  margin-top: 8px;
  font-size: 12px;
}

.alerts {
  margin-bottom: 16px;
}

.alerts .van-notice-bar {
  border-radius: 8px;
  margin-bottom: 8px;
}

.info-section {
  background: white;
  border-radius: 12px;
  padding: 16px;
}

.info-title {
  font-size: 14px;
  color: #969799;
  margin-bottom: 12px;
}

.range-bar {
  display: flex;
  height: 24px;
  border-radius: 4px;
  overflow: hidden;
  font-size: 10px;
  color: white;
  text-align: center;
  line-height: 24px;
}

.range-low {
  flex: 1;
  background: #ee0a24;
}

.range-target {
  flex: 2;
  background: #07c160;
}

.range-high {
  flex: 1;
  background: #ff976a;
}

.dialog-content {
  padding: 16px;
}

.unit-text {
  font-size: 14px;
  color: #969799;
}

.dialog-content :deep(.van-radio-group) {
  flex-wrap: wrap;
  gap: 8px;
}

.dialog-content :deep(.van-radio) {
  margin-right: 0;
}

/* Phase 2: 睡眠/活动/心率 卡片样式 */

.sleep-card .card-title .van-icon {
  color: #7232dd;
}

.sleep-value {
  font-size: 32px !important;
  color: #7232dd !important;
}

.sleep-stages {
  display: flex;
  justify-content: space-between;
  padding-top: 12px;
  border-top: 1px solid #ebedf0;
  margin-top: 8px;
}

.sleep-stages .stage-item {
  text-align: center;
}

.sleep-stages .stage-item .label {
  display: block;
  font-size: 11px;
  color: #969799;
  margin-bottom: 2px;
}

.sleep-stages .stage-item .value {
  font-size: 13px;
  font-weight: 500;
  color: #323233;
}

.insights {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.activity-card .card-title .van-icon {
  color: #ff6b00;
}

.activity-value {
  color: #ff6b00 !important;
}

.activity-stats {
  display: flex;
  justify-content: space-around;
  padding-top: 12px;
  border-top: 1px solid #ebedf0;
}

.hr-card .card-title .van-icon {
  color: #ee0a24;
}

.hr-hrv-row {
  display: flex;
  justify-content: space-around;
}

.hr-section,
.hrv-section {
  text-align: center;
  flex: 1;
}

.hr-section {
  border-right: 1px solid #ebedf0;
}

.section-title {
  font-size: 12px;
  color: #969799;
  margin-bottom: 8px;
}

.hr-value .value,
.hrv-value .value {
  font-size: 28px;
  font-weight: 600;
}

.hr-value .value {
  color: #ee0a24;
}

.hrv-value .value {
  color: #07c160;
}

.hr-value .unit,
.hrv-value .unit {
  font-size: 12px;
  color: #969799;
  margin-left: 2px;
}

.hr-range {
  font-size: 11px;
  color: #969799;
  margin-top: 4px;
}

.stress-level {
  font-size: 11px;
  color: #969799;
  margin-top: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}
</style>
