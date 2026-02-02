<template>
  <div class="page-container">
    <van-nav-bar title="行健行为教练" />

    <div class="page-content">
      <!-- 欢迎卡片 -->
      <div class="welcome-card card">
        <div class="welcome-header">
          <van-icon name="user-circle-o" size="48" color="#1989fa" />
          <div class="welcome-text">
            <h2>你好，{{ userStore.name }}</h2>
            <p>今天感觉如何？</p>
          </div>
        </div>
        <div class="efficacy-display" :style="{ backgroundColor: userStore.efficacyColor + '20' }">
          <span class="efficacy-number" :style="{ color: userStore.efficacyColor }">
            {{ userStore.efficacyScore }}
          </span>
          <span class="efficacy-label">效能感</span>
        </div>
      </div>

      <!-- 快捷入口 -->
      <div class="quick-actions card">
        <h3>快捷服务</h3>
        <van-grid :column-num="4" :border="false">
          <van-grid-item icon="chat-o" text="开始对话" to="/chat" />
          <van-grid-item icon="todo-list-o" text="我的任务" to="/tasks" />
          <van-grid-item icon="chart-trending-o" text="健康看板" to="/dashboard" />
          <van-grid-item icon="records-o" text="健康档案" to="/profile" />
        </van-grid>
      </div>

      <!-- 专家团队 -->
      <div class="experts-card card">
        <h3>专家团队</h3>
        <div class="expert-list">
          <div
            v-for="expert in chatStore.experts"
            :key="expert.id"
            class="expert-item"
            @click="goToChat(expert.id)"
          >
            <div class="expert-avatar" :class="'avatar-' + expert.id">
              <van-icon name="manager" />
            </div>
            <div class="expert-info">
              <div class="expert-name">{{ expert.name }}</div>
              <div class="expert-role">{{ expert.role }}</div>
            </div>
            <van-icon name="arrow" class="expert-arrow" />
          </div>
        </div>
      </div>

      <!-- 今日任务 -->
      <div v-if="chatStore.pendingTasks.length > 0" class="tasks-preview card">
        <div class="tasks-header">
          <h3>今日任务</h3>
          <router-link to="/tasks" class="view-all">查看全部</router-link>
        </div>
        <TaskCard
          v-for="task in chatStore.pendingTasks.slice(0, 3)"
          :key="task.id"
          :task="task"
          @toggle="chatStore.toggleTaskComplete"
        />
      </div>
    </div>

      <!-- 健康指标卡片组 -->
      <div class="health-metrics card">
        <h3>健康指标</h3>
        <div class="metrics-grid">
          <div class="metric-card glucose" @click="goToDetail('glucose')">
            <div class="metric-bar" style="background:linear-gradient(90deg,#ef4444,#f87171)"></div>
            <div class="metric-icon">🩸</div>
            <div class="metric-value">{{ healthData.bloodGlucose.fasting || '--' }}</div>
            <div class="metric-label">空腹血糖</div>
            <div class="metric-trend" :class="healthData.bloodGlucose.trend">
              <van-icon :name="healthData.bloodGlucose.trend === 'up' ? 'arrow-up' : healthData.bloodGlucose.trend === 'down' ? 'arrow-down' : 'minus'" />
            </div>
          </div>
          <div class="metric-card weight" @click="goToDetail('weight')">
            <div class="metric-bar" style="background:linear-gradient(90deg,#8b5cf6,#a78bfa)"></div>
            <div class="metric-icon">⚖️</div>
            <div class="metric-value">{{ healthData.weight.current || '--' }}</div>
            <div class="metric-label">当前体重</div>
            <div class="metric-trend" :class="healthData.weight.trend">
              <van-icon :name="healthData.weight.trend === 'up' ? 'arrow-up' : healthData.weight.trend === 'down' ? 'arrow-down' : 'minus'" />
            </div>
          </div>
          <div class="metric-card exercise" @click="goToDetail('exercise')">
            <div class="metric-bar" style="background:linear-gradient(90deg,#10b981,#34d399)"></div>
            <div class="metric-icon">🏃</div>
            <div class="metric-value">{{ healthData.exercise.weeklyMinutes }}</div>
            <div class="metric-label">本周运动</div>
            <van-progress :percentage="Math.min(100, Math.round(healthData.exercise.weeklyMinutes / healthData.exercise.targetMinutes * 100))" stroke-width="4" color="#10b981" track-color="#e5e7eb" :show-pivot="false" />
          </div>
          <div class="metric-card medication" @click="showMedPopup = true">
            <div class="metric-bar" style="background:linear-gradient(90deg,#f59e0b,#fbbf24)"></div>
            <div class="metric-icon">💊</div>
            <div class="metric-value">{{ healthData.medication.adherenceRate }}%</div>
            <div class="metric-label">用药提醒</div>
            <van-progress :percentage="healthData.medication.adherenceRate" stroke-width="4" :color="healthData.medication.adherenceRate >= 90 ? '#10b981' : '#f59e0b'" track-color="#e5e7eb" :show-pivot="false" />
          </div>
        </div>
      </div>
    </div>

    <!-- 用药提醒弹出层 -->
    <van-popup v-model:show="showMedPopup" position="bottom" round :style="{ height: '85%' }">
      <div class="med-popup">
        <div class="med-popup-header">
          <h3>💊 用药提醒</h3>
          <van-icon name="cross" @click="showMedPopup = false" />
        </div>
        <div class="med-popup-body">
          <!-- 今日用药打卡 -->
          <div class="med-section">
            <h4>📋 今日用药打卡</h4>
            <div v-for="med in medReminders" :key="med.id" class="med-item" :class="{taken: med.taken}" @click="toggleMedTaken(med)">
              <div class="med-check-box" :class="{checked: med.taken}">
                <van-icon v-if="med.taken" name="success" />
              </div>
              <div class="med-detail">
                <div class="med-name">{{ med.name }} <span class="med-dosage">{{ med.dosage }}</span></div>
                <div class="med-time">⏰ {{ med.time }} · {{ med.frequency }}</div>
              </div>
            </div>
          </div>

          <!-- 药物功能说明 -->
          <div class="med-section">
            <h4>💡 药物功能说明</h4>
            <div v-for="med in medReminders" :key="'info-'+med.id" class="drug-info-card">
              <div class="drug-header">
                <span class="drug-name">{{ med.name }}</span>
                <van-tag type="primary" size="small">{{ med.dosage }}</van-tag>
              </div>
              <div class="drug-freq">{{ med.frequency }}</div>
              <div class="drug-note">{{ med.notes }}</div>
            </div>
          </div>

          <!-- 注意事项 -->
          <div class="med-section">
            <h4>⚠️ 用药注意事项</h4>
            <div v-for="(p, i) in medPrecautions" :key="i" class="precaution-item">
              <div class="precaution-icon">{{ p.icon }}</div>
              <div class="precaution-body">
                <div class="precaution-title">{{ p.title }}</div>
                <div class="precaution-desc">{{ p.desc }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </van-popup>

    <TabBar />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useUserStore } from '@/stores/user'
import { useChatStore } from '@/stores/chat'
import TabBar from '@/components/common/TabBar.vue'
import TaskCard from '@/components/chat/TaskCard.vue'

const router = useRouter()
const userStore = useUserStore()
const chatStore = useChatStore()

function goToChat(expertId: string) {
  chatStore.setCurrentExpert(expertId)
  router.push('/chat')
}

// ---- 健康指标（与 admin-portal 同源数据） ----
const ENGINE_API = 'http://127.0.0.1:8002'
const MP_HEADERS = { 'Content-Type': 'application/json', 'X-User-ID': '1' }
let lastKnownGlucose = 0

const healthData = reactive({
  bloodGlucose: { fasting: null as number | null, postprandial: null as number | null, trend: 'stable' as 'up' | 'down' | 'stable' },
  weight: { current: 75.5, target: 70, trend: 'stable' as 'up' | 'down' | 'stable' },
  exercise: { weeklyMinutes: 0, targetMinutes: 150, streak: 0 },
  medication: { adherenceRate: 0, missedDoses: 0 },
})

async function refreshHealth() {
  try {
    const [statusRes, stateRes, progressRes] = await Promise.all([
      fetch(`${ENGINE_API}/latest_status`).then(r => r.json()).catch(() => null),
      fetch(`${ENGINE_API}/api/v1/mp/user/state`, { headers: MP_HEADERS }).then(r => r.json()).catch(() => null),
      fetch(`${ENGINE_API}/api/v1/mp/progress/summary`, { headers: MP_HEADERS }).then(r => r.json()).catch(() => null),
    ])
    const cg = statusRes?.current_glucose || 0
    const history: number[] = statusRes?.history || []
    let trend: 'up' | 'down' | 'stable' = 'stable'
    if (lastKnownGlucose > 0 && cg > 0) {
      if (cg > lastKnownGlucose + 0.3) trend = 'up'
      else if (cg < lastKnownGlucose - 0.3) trend = 'down'
    }
    if (cg > 0) lastKnownGlucose = cg
    const recent = history.slice(-5)
    healthData.bloodGlucose = { fasting: cg > 0 ? cg : null, postprandial: recent.length ? Math.max(...recent) : null, trend }
    const totalCompleted = progressRes?.total_completed || 0
    const streakDays = progressRes?.streak_days || 0
    const completionRate = progressRes?.completion_rate || 0
    healthData.weight = { current: +(75.5 - totalCompleted * 0.1).toFixed(1), target: 70, trend: totalCompleted > 3 ? 'down' : 'stable' }
    healthData.exercise = { weeklyMinutes: Math.round(completionRate * 150), targetMinutes: 150, streak: streakDays }
    healthData.medication = { adherenceRate: Math.round(completionRate * 100) || 85, missedDoses: Math.max(0, 7 - totalCompleted) }
  } catch { /* 后端不可用 */ }
}

function goToDetail(type: string) {
  showToast(`${type} 详情`)
}

// ---- 用药提醒 ----
const showMedPopup = ref(false)
const medReminders = ref([
  { id: 1, name: '二甲双胍', dosage: '500mg', time: '08:00', frequency: '每日2次（早/晚餐后）', taken: false, notes: '餐后服用，避免空腹；如出现胃肠不适可随餐服用' },
  { id: 2, name: '格列美脲', dosage: '2mg', time: '07:30', frequency: '每日1次（早餐前）', taken: true, notes: '早餐前15分钟服用；注意低血糖风险，随身携带糖果' },
  { id: 3, name: '阿卡波糖', dosage: '50mg', time: '12:00', frequency: '每日3次（随餐）', taken: false, notes: '与第一口饭同时嚼服；可能引起腹胀、排气增多' },
])
const medPrecautions = [
  { icon: '⏰', title: '按时服药', desc: '设定闹钟提醒，固定时间服药，不要随意更改服药时间' },
  { icon: '🚫', title: '不可自行停药', desc: '即使血糖正常也不要自行停药或减量，需遵医嘱调整' },
  { icon: '🍺', title: '避免饮酒', desc: '服药期间避免饮酒，酒精可能加重低血糖风险' },
  { icon: '📋', title: '记录不良反应', desc: '如出现恶心、腹泻、头晕等不适，及时记录并告知医生' },
  { icon: '💊', title: '勿与部分食物同服', desc: '避免与柚子汁同服；二甲双胍避免与含碘造影剂同用' },
  { icon: '🔄', title: '定期复查', desc: '每1-3个月复查糖化血红蛋白和肝肾功能' },
]
function toggleMedTaken(med: typeof medReminders.value[0]) {
  med.taken = !med.taken
  if (med.taken) showToast({ message: `${med.name} 已打卡 ✓`, type: 'success' })
}

// ---- 定时刷新 ----
let refreshTimer: ReturnType<typeof setInterval> | null = null
onMounted(() => {
  refreshHealth()
  refreshTimer = setInterval(refreshHealth, 10000)
})
onUnmounted(() => { if (refreshTimer) clearInterval(refreshTimer) })
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.welcome-card {
  .welcome-header {
    display: flex;
    align-items: center;
    margin-bottom: $spacing-md;
  }

  .welcome-text {
    margin-left: $spacing-md;

    h2 {
      font-size: $font-size-xl;
      margin-bottom: 4px;
    }

    p {
      color: $text-color-secondary;
      font-size: $font-size-sm;
    }
  }

  .efficacy-display {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: $spacing-md;
    border-radius: $border-radius;
    gap: $spacing-xs;

    .efficacy-number {
      font-size: 32px;
      font-weight: bold;
    }

    .efficacy-label {
      font-size: $font-size-sm;
      color: $text-color-secondary;
    }
  }
}

.quick-actions {
  h3 {
    margin-bottom: $spacing-sm;
    font-size: $font-size-lg;
  }
}

.experts-card {
  h3 {
    margin-bottom: $spacing-sm;
    font-size: $font-size-lg;
  }
}

.expert-list {
  .expert-item {
    display: flex;
    align-items: center;
    padding: $spacing-sm 0;
    border-bottom: 1px solid $border-color;

    &:last-child {
      border-bottom: none;
    }
  }

  .expert-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 20px;

    &.avatar-mental_health { background-color: $expert-mental; }
    &.avatar-nutrition { background-color: $expert-nutrition; }
    &.avatar-sports_rehab { background-color: $expert-sports; }
    &.avatar-tcm_wellness { background-color: $expert-tcm; }
  }

  .expert-info {
    flex: 1;
    margin-left: $spacing-sm;

    .expert-name {
      font-weight: 500;
    }

    .expert-role {
      font-size: $font-size-xs;
      color: $text-color-secondary;
    }
  }

  .expert-arrow {
    color: $text-color-placeholder;
  }
}

.tasks-preview {
  .tasks-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $spacing-sm;

    h3 {
      font-size: $font-size-lg;
    }

    .view-all {
      font-size: $font-size-sm;
      color: $primary-color;
      text-decoration: none;
    }
  }
}

/* 健康指标 */
.health-metrics {
  h3 { font-size: $font-size-lg; margin-bottom: $spacing-sm; }
}
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}
.metric-card {
  background: #fff;
  border-radius: 12px;
  padding: 14px;
  box-shadow: $shadow-sm;
  position: relative;
  overflow: hidden;
  cursor: pointer;
  .metric-bar { position: absolute; top: 0; left: 0; right: 0; height: 3px; }
  .metric-icon { font-size: 22px; margin-bottom: 6px; }
  .metric-value { font-size: 22px; font-weight: 700; color: $text-color; }
  .metric-label { font-size: 12px; color: $text-color-secondary; margin-top: 2px; }
  .metric-trend {
    position: absolute; top: 10px; right: 10px;
    width: 22px; height: 22px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center; font-size: 12px;
    &.down { background: #dcfce7; color: #16a34a; }
    &.up { background: #fee2e2; color: #dc2626; }
    &.stable { background: #f3f4f6; color: #6b7280; }
  }
  :deep(.van-progress) { margin-top: 8px; }
}

/* 用药提醒弹出层 */
.med-popup {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.med-popup-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px; border-bottom: 1px solid $border-color;
  h3 { margin: 0; font-size: 18px; }
}
.med-popup-body {
  flex: 1; overflow-y: auto; padding: 16px;
}
.med-section {
  margin-bottom: 24px;
  h4 { font-size: 15px; margin-bottom: 12px; }
}
.med-item {
  display: flex; align-items: center; gap: 12px;
  padding: 14px; background: #f9fafb; border-radius: 12px; margin-bottom: 10px;
  &.taken { opacity: 0.6; }
}
.med-check-box {
  width: 24px; height: 24px; border: 2px solid #d1d5db; border-radius: 6px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  &.checked { background: $success-color; border-color: $success-color; color: #fff; }
}
.med-detail { flex: 1; }
.med-name { font-weight: 600; font-size: 15px; }
.med-dosage { font-weight: 400; font-size: 13px; color: $text-color-secondary; margin-left: 6px; }
.med-time { font-size: 12px; color: $text-color-secondary; margin-top: 4px; }
.drug-info-card {
  background: #eff6ff; border-radius: 12px; padding: 14px; margin-bottom: 10px;
  border-left: 4px solid $primary-color;
}
.drug-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.drug-name { font-weight: 600; font-size: 15px; }
.drug-freq { font-size: 12px; color: $text-color-secondary; margin-bottom: 6px; }
.drug-note { font-size: 13px; color: #4b5563; line-height: 1.6; }
.precaution-item {
  display: flex; gap: 12px; padding: 12px; background: #fffbeb; border-radius: 12px; margin-bottom: 10px;
}
.precaution-icon { font-size: 22px; flex-shrink: 0; }
.precaution-title { font-weight: 600; font-size: 14px; margin-bottom: 4px; }
.precaution-desc { font-size: 13px; color: $text-color-secondary; line-height: 1.5; }
</style>
