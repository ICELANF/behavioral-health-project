<template>
  <!--
    VisionDailyLog.vue — 每日护眼打卡核心页
    路由: /vision-daily
    角色: Observer（学员）
    设计原则: 10秒完成打卡，30秒看懂进展
  -->
  <div class="vision-daily-log">

    <!-- ① 顶部评分环形图 -->
    <section class="score-header">
      <div class="score-ring-wrapper">
        <svg class="score-ring" viewBox="0 0 120 120">
          <circle
            class="ring-bg"
            cx="60" cy="60" r="50"
            stroke="#EEF4FF" stroke-width="10" fill="none"
          />
          <circle
            class="ring-progress"
            cx="60" cy="60" r="50"
            :stroke="scoreColor"
            stroke-width="10" fill="none"
            stroke-linecap="round"
            :stroke-dasharray="circumference"
            :stroke-dashoffset="ringOffset"
            transform="rotate(-90 60 60)"
          />
        </svg>
        <div class="score-center">
          <span class="score-number">{{ todayScore }}</span>
          <span class="score-label">今日护眼分</span>
        </div>
      </div>
      <div class="score-meta">
        <p class="greeting">{{ greeting }}</p>
        <p class="streak-badge" v-if="streakDays >= 3">
          🔥 已连续达标 {{ streakDays }} 天
        </p>
        <p class="date-label">{{ todayDateStr }}</p>
      </div>
    </section>

    <!-- ② 智伴提示条 -->
    <div class="agent-tip" v-if="agentTip">
      <span class="tip-icon">💬</span>
      <span class="tip-text">{{ agentTip }}</span>
    </div>

    <!-- ③ 五大行为打卡卡片 -->
    <section class="behavior-cards">

      <!-- 🌿 户外活动 -->
      <div class="bcard" :class="{ done: outdoor.done, over: outdoor.done }">
        <div class="bcard-header">
          <span class="bcard-icon">🌿</span>
          <span class="bcard-title">户外活动</span>
          <span class="bcard-target">目标 {{ goals.outdoor_target_min }} 分钟</span>
        </div>
        <div class="bcard-body">
          <div class="progress-bar">
            <div
              class="progress-fill outdoor-fill"
              :style="{ width: Math.min((outdoor.minutes / goals.outdoor_target_min) * 100, 100) + '%' }"
            />
          </div>
          <div class="bcard-nums">
            <span class="done-num">{{ outdoor.minutes }}</span>
            <span class="gap-num" v-if="!outdoor.done">
              差 {{ goals.outdoor_target_min - outdoor.minutes }} 分钟
            </span>
            <span class="gap-num success" v-else>✅ 达标！</span>
          </div>
        </div>
        <div class="bcard-input">
          <input
            v-model.number="outdoor.inputMinutes"
            type="number" min="0" max="480"
            placeholder="填入分钟数"
          />
          <button class="checkin-btn" @click="checkinOutdoor">记录</button>
        </div>
      </div>

      <!-- 📱 屏幕管理 -->
      <div class="bcard" :class="{ over: screen.overLimit }">
        <div class="bcard-header">
          <span class="bcard-icon">📱</span>
          <span class="bcard-title">屏幕时间</span>
          <span class="bcard-target">上限 {{ goals.screen_daily_limit }} 分钟</span>
        </div>
        <div class="bcard-body">
          <div class="progress-bar">
            <div
              class="progress-fill screen-fill"
              :class="{ over: screen.overLimit }"
              :style="{ width: Math.min((screen.minutes / goals.screen_daily_limit) * 100, 100) + '%' }"
            />
          </div>
          <div class="bcard-nums">
            <span class="done-num">{{ screen.minutes }}</span>
            <span class="gap-num" :class="{ warn: screen.overLimit }">
              {{ screen.overLimit ? `超标 ${screen.minutes - goals.screen_daily_limit} 分钟 ⚠️` : `余 ${goals.screen_daily_limit - screen.minutes} 分钟` }}
            </span>
          </div>
        </div>
        <div class="bcard-input">
          <input
            v-model.number="screen.inputMinutes"
            type="number" min="0" max="720"
            placeholder="填入分钟数"
          />
          <button class="checkin-btn" @click="checkinScreen">记录</button>
        </div>
      </div>

      <!-- 🥦 叶黄素 -->
      <div class="bcard" :class="{ done: lutein.done }">
        <div class="bcard-header">
          <span class="bcard-icon">🥦</span>
          <span class="bcard-title">叶黄素</span>
          <span class="bcard-target">目标 {{ goals.lutein_target_mg }} mg</span>
        </div>
        <div class="bcard-body">
          <div class="bcard-nums">
            <span class="done-num">{{ lutein.mg }} mg</span>
            <span class="gap-num" v-if="!lutein.done">
              差 {{ (goals.lutein_target_mg - lutein.mg).toFixed(1) }} mg
            </span>
            <span class="gap-num success" v-else>✅ 达标！</span>
          </div>
        </div>
        <div class="bcard-input">
          <input
            v-model.number="lutein.inputMg"
            type="number" min="0" max="50" step="0.5"
            placeholder="填入 mg 数"
          />
          <button class="checkin-btn" @click="checkinLutein">记录</button>
        </div>
      </div>

      <!-- 💤 睡眠 -->
      <div class="bcard" :class="{ done: sleep.done }">
        <div class="bcard-header">
          <span class="bcard-icon">💤</span>
          <span class="bcard-title">睡眠</span>
          <span class="bcard-target">目标 {{ (goals.sleep_target_min / 60).toFixed(0) }} 小时</span>
        </div>
        <div class="bcard-body">
          <div class="bcard-nums">
            <span class="done-num">{{ (sleep.minutes / 60).toFixed(1) }} h</span>
            <span class="gap-num success" v-if="sleep.done">✅ 达标！</span>
          </div>
        </div>
        <div class="bcard-input">
          <input
            v-model.number="sleep.inputHours"
            type="number" min="0" max="12" step="0.5"
            placeholder="填入小时数"
          />
          <button class="checkin-btn" @click="checkinSleep">记录</button>
        </div>
      </div>

      <!-- 👁️ 眼保健操 -->
      <div class="bcard eye-exercise" :class="{ done: eyeExerciseDone }">
        <div class="bcard-header">
          <span class="bcard-icon">👁️</span>
          <span class="bcard-title">眼保健操</span>
          <span class="bcard-target">今日完成</span>
        </div>
        <div class="bcard-body exercise-body">
          <button
            class="exercise-toggle"
            :class="{ completed: eyeExerciseDone }"
            @click="toggleEyeExercise"
          >
            {{ eyeExerciseDone ? '✅ 已完成！' : '点击打卡' }}
          </button>
        </div>
      </div>

    </section>

    <!-- ④ 本周趋势迷你图 -->
    <section class="weekly-trend">
      <h3 class="section-title">本周护眼趋势</h3>
      <div class="trend-charts">
        <div
          v-for="(day, idx) in weeklyData"
          :key="idx"
          class="trend-day"
        >
          <div class="trend-bar-wrap">
            <div
              class="trend-bar"
              :style="{
                height: (day.score / 100 * 60) + 'px',
                background: day.score >= 80 ? '#4ade80' : day.score >= 50 ? '#facc15' : '#f87171'
              }"
            />
          </div>
          <span class="trend-date">{{ day.label }}</span>
          <span class="trend-score">{{ day.score }}</span>
        </div>
      </div>
    </section>

    <!-- ⑤ 快捷通道 -->
    <section class="quick-actions">
      <button class="quick-btn" @click="$emit('navigate', '/vision-exam/capture')">
        📷 拍摄报告
      </button>
      <button class="quick-btn" @click="$emit('navigate', '/vision-chat')">
        💬 咨询视力问题
      </button>
    </section>

    <!-- ⑥ 家长同步开关 -->
    <div class="parent-sync">
      <label class="sync-label">
        <input type="checkbox" v-model="syncToParent" @change="handleSyncToggle" />
        今日打卡同步给家长
      </label>
      <span class="sync-hint">（你可以随时关闭）</span>
    </div>

  </div>
</template>


<script setup>
import { ref, computed, onMounted } from 'vue'

// ── props ──────────────────────────────────────────────────────────────────
const props = defineProps({
  userId: { type: String, required: true },
})

const emit = defineEmits(['navigate', 'checkin-done'])

// ── API 占位（替换为平台实际 axios/fetch）─────────────────────────────────
const API_BASE = '/v1/vision/behavior'

async function fetchTodayLog() {
  // const res = await axios.get(`${API_BASE}/log/${props.userId}?days=1`)
  // return res.data[0] || null
  return null
}

async function fetchGoals() {
  // const res = await axios.get(`${API_BASE}/goals/${props.userId}`)
  // return res.data
  return {
    outdoor_target_min: 120,
    screen_daily_limit: 120,
    screen_session_limit: 20,
    lutein_target_mg: 10,
    sleep_target_min: 540,
  }
}

async function fetchWeeklyData() {
  // const res = await axios.get(`${API_BASE}/log/${props.userId}?days=7`)
  // return res.data
  return [
    { label: '周一', score: 72 },
    { label: '周二', score: 85 },
    { label: '周三', score: 60 },
    { label: '周四', score: 90 },
    { label: '周五', score: 45 },
    { label: '周六', score: 88 },
    { label: '今天', score: todayScore.value },
  ]
}

async function submitCheckin(payload) {
  // const res = await axios.post(`${API_BASE}/log`, payload)
  // agentTip.value = res.data.instant_message
  // streakDays.value = res.data.streak_days
  agentTip.value = '打卡成功！继续保持 💪'
}

// ── 状态 ────────────────────────────────────────────────────────────────────
const goals = ref({
  outdoor_target_min: 120,
  screen_daily_limit: 120,
  screen_session_limit: 20,
  lutein_target_mg: 10,
  sleep_target_min: 540,
})

const outdoor = ref({ minutes: 0, inputMinutes: null, done: false })
const screen = ref({ minutes: 0, inputMinutes: null, overLimit: false })
const lutein = ref({ mg: 0, inputMg: null, done: false })
const sleep = ref({ minutes: 0, inputHours: null, done: false })
const eyeExerciseDone = ref(false)
const agentTip = ref('')
const streakDays = ref(0)
const syncToParent = ref(true)

// ── 计算 ────────────────────────────────────────────────────────────────────
const todayScore = computed(() => {
  let s = 0
  const g = goals.value

  if (g.outdoor_target_min > 0)
    s += Math.min(outdoor.value.minutes / g.outdoor_target_min, 1) * 35

  if (g.screen_daily_limit > 0) {
    const ratio = Math.max(0, 1 - (screen.value.minutes / g.screen_daily_limit - 1))
    s += Math.min(ratio, 1) * 30
  }

  if (eyeExerciseDone.value) s += 10

  if (g.lutein_target_mg > 0)
    s += Math.min(lutein.value.mg / g.lutein_target_mg, 1) * 10

  if (g.sleep_target_min > 0)
    s += Math.min(sleep.value.minutes / g.sleep_target_min, 1) * 15

  return Math.round(s)
})

const circumference = computed(() => 2 * Math.PI * 50)
const ringOffset = computed(
  () => circumference.value * (1 - todayScore.value / 100)
)

const scoreColor = computed(() => {
  if (todayScore.value >= 80) return '#4ade80'
  if (todayScore.value >= 50) return '#facc15'
  return '#f87171'
})

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return '早上好！今天护眼目标加油 💪'
  if (h < 18) return '下午好！记得让眼睛休息一下 👀'
  return '晚上好！今天任务完成得怎么样了？'
})

const todayDateStr = computed(() => {
  const d = new Date()
  return `${d.getMonth() + 1}月${d.getDate()}日`
})

const weeklyData = ref([])

// ── 打卡操作 ────────────────────────────────────────────────────────────────
async function checkinOutdoor() {
  if (!outdoor.value.inputMinutes) return
  outdoor.value.minutes = outdoor.value.inputMinutes
  outdoor.value.done = outdoor.value.minutes >= goals.value.outdoor_target_min
  outdoor.value.inputMinutes = null
  await submitCheckin({ outdoor_minutes: outdoor.value.minutes })
}

async function checkinScreen() {
  if (!screen.value.inputMinutes) return
  screen.value.minutes = screen.value.inputMinutes
  screen.value.overLimit = screen.value.minutes > goals.value.screen_daily_limit
  screen.value.inputMinutes = null
  if (screen.value.overLimit) {
    agentTip.value = `今天屏幕时间已经 ${screen.value.minutes} 分钟，建议活动一下眼睛，20 秒看看窗外远处 👀`
  }
  await submitCheckin({ screen_total_minutes: screen.value.minutes })
}

async function checkinLutein() {
  if (!lutein.value.inputMg) return
  lutein.value.mg = lutein.value.inputMg
  lutein.value.done = lutein.value.mg >= goals.value.lutein_target_mg
  lutein.value.inputMg = null
  await submitCheckin({ lutein_intake_mg: lutein.value.mg })
}

async function checkinSleep() {
  if (!sleep.value.inputHours) return
  sleep.value.minutes = sleep.value.inputHours * 60
  sleep.value.done = sleep.value.minutes >= goals.value.sleep_target_min
  sleep.value.inputHours = null
  await submitCheckin({ sleep_minutes: sleep.value.minutes })
}

async function toggleEyeExercise() {
  eyeExerciseDone.value = !eyeExerciseDone.value
  if (eyeExerciseDone.value) {
    agentTip.value = '眼保健操打卡✓ 每一次都在保护你的眼睛！'
    await submitCheckin({ eye_exercise_done: true })
  }
}

function handleSyncToggle() {
  // 调用 API 更新同步偏好
  // axios.patch(`/v1/users/${props.userId}/preferences`, { sync_to_parent: syncToParent.value })
}

// ── 初始化 ──────────────────────────────────────────────────────────────────
onMounted(async () => {
  const [goalsData, logData] = await Promise.all([fetchGoals(), fetchTodayLog()])

  if (goalsData) goals.value = { ...goals.value, ...goalsData }

  if (logData) {
    outdoor.value.minutes = logData.outdoor_minutes || 0
    screen.value.minutes = logData.screen_total_minutes || 0
    lutein.value.mg = parseFloat(logData.lutein_intake_mg) || 0
    sleep.value.minutes = logData.sleep_minutes || 0
    eyeExerciseDone.value = logData.eye_exercise_done || false

    outdoor.value.done = outdoor.value.minutes >= goals.value.outdoor_target_min
    screen.value.overLimit = screen.value.minutes > goals.value.screen_daily_limit
    lutein.value.done = lutein.value.mg >= goals.value.lutein_target_mg
    sleep.value.done = sleep.value.minutes >= goals.value.sleep_target_min
  }

  weeklyData.value = await fetchWeeklyData()
})
</script>


<style scoped>
.vision-daily-log {
  padding: 16px;
  max-width: 480px;
  margin: 0 auto;
  background: #f8faff;
  min-height: 100vh;
}

/* ── 评分环 ── */
.score-header {
  display: flex;
  align-items: center;
  gap: 16px;
  background: white;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,.06);
}

.score-ring-wrapper {
  position: relative;
  width: 100px;
  height: 100px;
  flex-shrink: 0;
}

.score-ring { width: 100%; height: 100%; }

.score-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.score-number { font-size: 26px; font-weight: 700; color: #1a1a2e; }
.score-label  { font-size: 11px; color: #888; }

.greeting     { font-size: 15px; font-weight: 600; color: #1a1a2e; margin: 0 0 4px; }
.streak-badge { font-size: 13px; color: #f97316; font-weight: 600; margin: 0 0 4px; }
.date-label   { font-size: 12px; color: #aaa; margin: 0; }

/* ── 智伴提示 ── */
.agent-tip {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  background: #eff6ff;
  border-left: 3px solid #3b82f6;
  border-radius: 8px;
  padding: 10px 14px;
  margin-bottom: 12px;
  font-size: 13px;
  color: #1e3a5f;
  line-height: 1.5;
}

.tip-icon { font-size: 16px; flex-shrink: 0; }

/* ── 打卡卡片 ── */
.behavior-cards { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }

.bcard {
  background: white;
  border-radius: 12px;
  padding: 14px 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
  border: 2px solid transparent;
  transition: border-color .2s;
}

.bcard.done  { border-color: #4ade80; }
.bcard.over  { border-color: #f87171; }

.bcard-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.bcard-icon   { font-size: 18px; }
.bcard-title  { font-size: 15px; font-weight: 600; flex: 1; }
.bcard-target { font-size: 12px; color: #888; }

.progress-bar {
  background: #f0f0f0;
  border-radius: 4px;
  height: 6px;
  overflow: hidden;
  margin-bottom: 6px;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width .4s ease;
}

.outdoor-fill { background: #4ade80; }
.screen-fill  { background: #60a5fa; }
.screen-fill.over { background: #f87171; }

.bcard-nums {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.done-num   { font-size: 18px; font-weight: 700; color: #1a1a2e; }
.gap-num    { font-size: 12px; color: #888; }
.gap-num.success { color: #22c55e; font-weight: 600; }
.gap-num.warn    { color: #ef4444; font-weight: 600; }

.bcard-input {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.bcard-input input {
  flex: 1;
  padding: 8px 10px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
}

.bcard-input input:focus { border-color: #3b82f6; }

.checkin-btn {
  padding: 8px 16px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity .2s;
}

.checkin-btn:active { opacity: .8; }

.exercise-body { display: flex; justify-content: center; padding: 4px 0; }

.exercise-toggle {
  width: 100%;
  padding: 12px;
  border: 2px dashed #d1d5db;
  border-radius: 10px;
  background: transparent;
  font-size: 16px;
  cursor: pointer;
  transition: all .2s;
}

.exercise-toggle.completed {
  border-style: solid;
  border-color: #4ade80;
  background: #f0fdf4;
  color: #16a34a;
  font-weight: 600;
}

/* ── 趋势图 ── */
.weekly-trend {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #555;
  margin: 0 0 12px;
}

.trend-charts {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 4px;
}

.trend-day {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex: 1;
}

.trend-bar-wrap { height: 60px; display: flex; align-items: flex-end; }

.trend-bar {
  width: 24px;
  border-radius: 4px 4px 0 0;
  min-height: 4px;
  transition: height .4s;
}

.trend-date  { font-size: 11px; color: #aaa; }
.trend-score { font-size: 12px; font-weight: 600; color: #555; }

/* ── 快捷按钮 ── */
.quick-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.quick-btn {
  flex: 1;
  padding: 12px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  font-size: 14px;
  cursor: pointer;
  transition: background .2s;
}

.quick-btn:active { background: #f3f4f6; }

/* ── 家长同步 ── */
.parent-sync {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 0;
  font-size: 13px;
  color: #666;
}

.sync-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.sync-hint { color: #aaa; font-size: 12px; }
</style>
