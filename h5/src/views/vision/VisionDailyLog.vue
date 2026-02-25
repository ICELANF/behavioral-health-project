<template>
  <div class="vision-daily-log">
    <!-- 顶部导航 -->
    <van-nav-bar title="视力行为打卡" left-arrow @click-left="$router.back()" />

    <!-- 日期选择 -->
    <div class="date-selector">
      <van-icon name="arrow-left" @click="changeDate(-1)" />
      <span class="date-text">{{ displayDate }}</span>
      <van-icon name="arrow" @click="changeDate(1)" :class="{ disabled: isToday }" />
    </div>

    <!-- SVG 环形进度图 -->
    <div class="score-ring-container">
      <svg viewBox="0 0 200 200" class="score-ring">
        <circle cx="100" cy="100" r="85" fill="none" stroke="#f0f0f0" stroke-width="12" />
        <circle
          cx="100" cy="100" r="85"
          fill="none"
          :stroke="scoreColor"
          stroke-width="12"
          stroke-linecap="round"
          :stroke-dasharray="`${scoreArc} ${534 - scoreArc}`"
          stroke-dashoffset="133.5"
          class="score-arc"
        />
      </svg>
      <div class="score-center">
        <div class="score-number">{{ currentScore }}</div>
        <div class="score-label">行为评分</div>
      </div>
    </div>

    <!-- 反馈消息 -->
    <div v-if="feedbackMessage" class="feedback-card" :class="feedbackLevel">
      <van-icon :name="feedbackIcon" />
      <span>{{ feedbackMessage }}</span>
    </div>

    <!-- 五维行为卡片 -->
    <div class="dimension-cards">
      <!-- 户外活动 -->
      <div class="dim-card">
        <div class="dim-header">
          <van-icon name="like-o" color="#52c41a" />
          <span>户外活动</span>
          <van-tag v-if="dimensions.outdoor_pct >= 100" type="success" size="mini">达标</van-tag>
        </div>
        <van-stepper v-model="form.outdoor_minutes" :min="0" :max="600" :step="15" integer />
        <div class="dim-unit">分钟 / 目标 {{ goals.outdoor_target_min }} 分钟</div>
        <van-progress :percentage="dimensions.outdoor_pct" :color="dimensions.outdoor_pct >= 100 ? '#52c41a' : '#1890ff'" stroke-width="4" />
      </div>

      <!-- 屏幕使用 -->
      <div class="dim-card">
        <div class="dim-header">
          <van-icon name="tv-o" color="#fa8c16" />
          <span>屏幕使用</span>
          <van-tag v-if="form.screen_total_minutes <= (goals.screen_daily_limit || 120)" type="success" size="mini">达标</van-tag>
          <van-tag v-else type="danger" size="mini">超标</van-tag>
        </div>
        <van-stepper v-model="form.screen_total_minutes" :min="0" :max="600" :step="15" integer />
        <div class="dim-unit">分钟 / 限制 {{ goals.screen_daily_limit }} 分钟</div>
        <van-field v-model="form.screen_sessions" type="digit" label="使用次数" placeholder="几次" input-align="right" />
      </div>

      <!-- 眼保健操 -->
      <div class="dim-card">
        <div class="dim-header">
          <van-icon name="eye-o" color="#722ed1" />
          <span>眼保健操</span>
        </div>
        <van-switch v-model="form.eye_exercise_done" size="24" />
        <div class="dim-unit">{{ form.eye_exercise_done ? '已完成' : '未完成' }}</div>
      </div>

      <!-- 叶黄素 -->
      <div class="dim-card">
        <div class="dim-header">
          <van-icon name="flower-o" color="#eb2f96" />
          <span>叶黄素摄入</span>
        </div>
        <van-stepper v-model="form.lutein_intake_mg" :min="0" :max="30" :step="1" :decimal-length="1" />
        <div class="dim-unit">mg / 目标 {{ goals.lutein_target_mg }} mg</div>
      </div>

      <!-- 睡眠 -->
      <div class="dim-card">
        <div class="dim-header">
          <van-icon name="clock-o" color="#13c2c2" />
          <span>睡眠时长</span>
        </div>
        <van-stepper v-model="sleepHours" :min="0" :max="14" :step="0.5" :decimal-length="1" />
        <div class="dim-unit">小时 / 目标 {{ (goals.sleep_target_min / 60).toFixed(1) }} 小时</div>
      </div>
    </div>

    <!-- 备注 -->
    <van-field v-model="form.notes" type="textarea" label="备注" placeholder="今天有什么特别的？（选填）" rows="2" autosize />

    <!-- 提交按钮 -->
    <div class="submit-area">
      <van-button type="primary" block round :loading="submitting" @click="handleSubmit">
        {{ existingLog ? '更新打卡' : '提交打卡' }}
      </van-button>
    </div>

    <!-- 差距提示 -->
    <div v-if="gaps.length" class="gap-tips">
      <div class="gap-title">今日差距提示</div>
      <div v-for="(gap, i) in gaps" :key="i" class="gap-item">
        <van-icon name="info-o" color="#fa8c16" />
        <span>{{ gap }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { showToast, showSuccessToast } from 'vant'
import { visionApi } from '@/api/vision'

const form = ref({
  outdoor_minutes: 0,
  screen_sessions: 0,
  screen_total_minutes: 0,
  eye_exercise_done: false,
  lutein_intake_mg: 0,
  sleep_minutes: 0,
  notes: '',
})

const sleepHours = ref(0)
watch(sleepHours, (v) => { form.value.sleep_minutes = Math.round(v * 60) })

const goals = ref({
  outdoor_target_min: 120,
  screen_daily_limit: 120,
  screen_session_limit: 6,
  lutein_target_mg: 10,
  sleep_target_min: 480,
})

const currentScore = ref(0)
const feedbackMessage = ref('')
const gaps = ref<string[]>([])
const dimensions = ref({
  outdoor_pct: 0,
  screen_pct: 0,
  eye_exercise: false,
  lutein_pct: 0,
  sleep_pct: 0,
})
const submitting = ref(false)
const existingLog = ref(false)
const selectedDate = ref(new Date())

const isToday = computed(() => {
  const t = new Date()
  return selectedDate.value.toDateString() === t.toDateString()
})

const displayDate = computed(() => {
  const d = selectedDate.value
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const weekDays = ['日', '一', '二', '三', '四', '五', '六']
  return `${y}-${m}-${day} 周${weekDays[d.getDay()]}`
})

const logDateStr = computed(() => {
  const d = selectedDate.value
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
})

const scoreArc = computed(() => Math.min(534, (currentScore.value / 100) * 534))
const scoreColor = computed(() => {
  if (currentScore.value >= 75) return '#52c41a'
  if (currentScore.value >= 45) return '#1890ff'
  return '#fa8c16'
})
const feedbackLevel = computed(() => {
  if (currentScore.value >= 75) return 'level-high'
  if (currentScore.value >= 45) return 'level-mid'
  return 'level-low'
})
const feedbackIcon = computed(() => {
  if (currentScore.value >= 75) return 'like'
  if (currentScore.value >= 45) return 'smile-o'
  return 'info-o'
})

function changeDate(delta: number) {
  if (delta > 0 && isToday.value) return
  const d = new Date(selectedDate.value)
  d.setDate(d.getDate() + delta)
  if (d > new Date()) return
  selectedDate.value = d
  loadExistingLog()
}

async function loadGoals() {
  try {
    const res: any = await visionApi.getMyGoals()
    if (res) {
      goals.value = {
        outdoor_target_min: res.outdoor_target_min || 120,
        screen_daily_limit: res.screen_daily_limit || 120,
        screen_session_limit: res.screen_session_limit || 6,
        lutein_target_mg: res.lutein_target_mg || 10,
        sleep_target_min: res.sleep_target_min || 480,
      }
    }
  } catch { /* use defaults */ }
}

async function loadExistingLog() {
  try {
    const res: any = await visionApi.getMyLogs(30)
    const logs = res?.logs || []
    const todayLog = logs.find((l: any) => l.log_date === logDateStr.value)
    if (todayLog) {
      existingLog.value = true
      form.value.outdoor_minutes = todayLog.outdoor_minutes || 0
      form.value.screen_sessions = todayLog.screen_sessions || 0
      form.value.screen_total_minutes = todayLog.screen_total_minutes || 0
      form.value.eye_exercise_done = todayLog.eye_exercise_done || false
      form.value.lutein_intake_mg = todayLog.lutein_intake_mg || 0
      form.value.sleep_minutes = todayLog.sleep_minutes || 0
      sleepHours.value = (todayLog.sleep_minutes || 0) / 60
      currentScore.value = todayLog.behavior_score || 0
    } else {
      existingLog.value = false
    }
  } catch { /* ignore */ }
}

async function handleSubmit() {
  submitting.value = true
  try {
    const res: any = await visionApi.submitBehaviorLog({
      log_date: logDateStr.value,
      ...form.value,
    })
    currentScore.value = res.behavior_score || 0
    feedbackMessage.value = res.feedback?.message || ''
    gaps.value = res.feedback?.gaps || []
    dimensions.value = res.feedback?.dimensions || dimensions.value
    existingLog.value = true
    showSuccessToast('打卡成功')
  } catch (e: any) {
    showToast(e?.response?.data?.detail || '提交失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadGoals()
  loadExistingLog()
})
</script>

<style scoped>
.vision-daily-log {
  padding-bottom: calc(80px + env(safe-area-inset-bottom, 0px));
  background: #f7f8fa;
  min-height: 100vh;
}
.date-selector {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px 0;
  gap: 16px;
  background: #fff;
}
.date-text {
  font-size: 16px;
  font-weight: 500;
}
.disabled { opacity: 0.3; pointer-events: none; }
.score-ring-container {
  position: relative;
  width: 160px;
  height: 160px;
  margin: 16px auto;
}
.score-ring { width: 100%; height: 100%; }
.score-arc { transition: stroke-dasharray 0.6s ease; }
.score-center {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.score-number { font-size: 36px; font-weight: 700; }
.score-label { font-size: 12px; color: #999; }
.feedback-card {
  margin: 8px 16px;
  padding: 12px 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}
.level-high { background: #f6ffed; color: #52c41a; }
.level-mid { background: #e6f7ff; color: #1890ff; }
.level-low { background: #fff7e6; color: #fa8c16; }
.dimension-cards {
  padding: 0 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 12px;
}
.dim-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
}
.dim-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 15px;
  font-weight: 500;
}
.dim-unit {
  font-size: 12px;
  color: #999;
  margin: 4px 0 8px;
}
.submit-area {
  padding: 16px;
}
.gap-tips {
  margin: 0 16px 16px;
  padding: 12px;
  background: #fff7e6;
  border-radius: 8px;
}
.gap-title {
  font-size: 14px;
  font-weight: 500;
  color: #fa8c16;
  margin-bottom: 8px;
}
.gap-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #666;
  padding: 4px 0;
}
</style>
