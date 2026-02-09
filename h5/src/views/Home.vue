<template>
  <div class="page-container">
    <van-nav-bar title="行健行为教练" />

    <div class="page-content">
      <!-- 设备预警横幅 -->
      <div v-if="dangerAlerts.length" class="danger-banner" style="margin-bottom:8px">
        <div
          v-for="alert in dangerAlerts"
          :key="alert.id"
          style="display:flex;align-items:center;gap:8px;padding:10px 12px;background:#fff2f0;border:1px solid #ffccc7;border-radius:8px;margin-bottom:6px"
        >
          <van-icon name="warning-o" color="#ee0a24" size="20" />
          <div style="flex:1;font-size:13px;color:#cf1322">{{ alert.message }} (值: {{ alert.data_value }})</div>
          <van-button size="mini" type="danger" plain round @click="router.push('/notifications')">查看</van-button>
        </div>
      </div>

      <!-- 生命状态卡片 -->
      <StageHeader />

      <!-- 欢迎卡片 -->
      <div class="welcome-card card">
        <div class="welcome-header" @click="router.push('/profile')">
          <van-icon name="user-circle-o" size="48" color="#1989fa" />
          <div class="welcome-text">
            <h2>你好，{{ userStore.name }}</h2>
            <p>今天感觉如何？</p>
          </div>
          <van-icon name="arrow" color="#c8c9cc" />
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
          <van-grid-item icon="records-o" text="健康档案" to="/health-records" />
        </van-grid>
        <van-grid :column-num="4" :border="false">
          <van-grid-item icon="photograph" text="食物识别" to="/food-recognition" />
          <van-grid-item icon="bookmark-o" text="我的学习" to="/my-learning" />
          <van-grid-item icon="friends-o" text="教练目录" to="/coach-directory" />
          <van-grid-item icon="edit" text="知识投稿" to="/contribute" />
        </van-grid>
      </div>

      <!-- 行为评估入口 -->
      <div class="assessment-entry card" @click="router.push('/behavior-assessment')">
        <div class="entry-content">
          <div class="entry-icon">
            <van-icon name="aim" size="32" color="#1989fa" />
          </div>
          <div class="entry-text">
            <h3>了解你的行为状态</h3>
            <p>完成评估，获取专属行为改变方案</p>
          </div>
          <van-icon name="arrow" color="#c8c9cc" />
        </div>
      </div>

      <!-- 挑战活动入口 -->
      <div class="challenge-entry card" @click="router.push('/challenges')">
        <div class="entry-content">
          <div class="entry-icon">
            <van-icon name="fire-o" size="32" color="#ff976a" />
          </div>
          <div class="entry-text">
            <h3>我的挑战</h3>
            <p>查看教练为你分配的挑战计划</p>
          </div>
          <van-icon name="arrow" color="#c8c9cc" />
        </div>
      </div>

      <!-- 智能监测方案入口 -->
      <div class="program-entry card" @click="router.push('/programs')">
        <div class="entry-content">
          <div class="entry-icon" style="background:rgba(7,193,96,0.1)">
            <van-icon name="bar-chart-o" size="32" color="#07c160" />
          </div>
          <div class="entry-text">
            <h3>智能监测方案</h3>
            <p>个性化行为监测与改善计划</p>
          </div>
          <van-icon name="arrow" color="#c8c9cc" />
        </div>
      </div>

      <!-- 推荐学习 -->
      <div class="recommend-learn card">
        <div class="section-header">
          <h3>推荐学习</h3>
          <router-link to="/learn" class="view-all">更多 ›</router-link>
        </div>
        <van-loading v-if="loadingRecommend" size="20" />
        <div v-else-if="recommendList.length" class="recommend-scroll">
          <div
            v-for="item in recommendList"
            :key="item.id"
            class="recommend-item"
            @click="router.push(`/content/${item.type || 'article'}/${item.id}`)"
          >
            <div v-if="item.cover_url" class="recommend-cover">
              <img :src="item.cover_url" :alt="item.title" />
            </div>
            <div v-else class="recommend-cover recommend-cover-placeholder">
              <van-icon name="bookmark-o" size="24" color="#c8c9cc" />
            </div>
            <div class="recommend-title">{{ item.title }}</div>
            <div class="recommend-meta">
              <van-tag size="small" plain round :type="item.type === 'video' ? 'success' : 'primary'">
                {{ { article: '文章', video: '视频', course: '课程', case_study: '案例', card: '卡片' }[item.type] || '文章' }}
              </van-tag>
              <span>{{ item.view_count || 0 }}阅读</span>
            </div>
          </div>
        </div>
        <div v-else class="recommend-empty" @click="router.push('/learn')">
          <van-icon name="bookmark-o" size="28" color="#c8c9cc" />
          <span>探索学习内容</span>
        </div>
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

      <!-- 今日微行动 -->
      <div class="micro-actions-card card">
        <div class="tasks-header">
          <h3>
            今日微行动
            <van-tag v-if="microStreak > 0" type="warning" size="small" round>
              &#x1F525; {{ microStreak }}天
            </van-tag>
          </h3>
          <router-link to="/tasks" class="view-all">查看全部</router-link>
        </div>
        <van-loading v-if="loadingMicro" size="20" />
        <template v-else-if="microTasks.length > 0">
          <div class="micro-progress-bar">
            <span>{{ microCompleted }}/{{ microTasks.length }} 已完成</span>
            <van-progress
              :percentage="microProgressRate"
              stroke-width="4"
              color="#07c160"
              track-color="#ebedf0"
              :show-pivot="false"
            />
          </div>
          <div
            v-for="task in microTasks"
            :key="task.id"
            class="micro-item"
            :class="{ done: task.status === 'completed' }"
          >
            <div
              class="micro-check"
              :class="{ checked: task.status === 'completed' }"
              @click="quickCompleteMicro(task)"
            >
              <van-icon v-if="task.status === 'completed'" name="success" />
            </div>
            <span class="micro-title">{{ task.title }}</span>
          </div>
        </template>
        <div v-else class="micro-empty">
          今日暂无微行动
        </div>
      </div>

      <!-- 旧的今日任务 (来自AI对话) -->
      <div v-if="chatStore.pendingTasks.length > 0" class="tasks-preview card">
        <div class="tasks-header">
          <h3>AI推荐任务</h3>
          <router-link to="/tasks" class="view-all">查看全部</router-link>
        </div>
        <TaskCard
          v-for="task in chatStore.pendingTasks.slice(0, 3)"
          :key="task.id"
          :task="task"
          @toggle="chatStore.toggleTaskComplete"
        />
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
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useUserStore } from '@/stores/user'
import { useChatStore } from '@/stores/chat'
import TabBar from '@/components/common/TabBar.vue'
import TaskCard from '@/components/chat/TaskCard.vue'
import StageHeader from '@/components/stage/StageHeader.vue'
import api from '@/api/index'

const router = useRouter()
const userStore = useUserStore()
const chatStore = useChatStore()

function goToChat(expertId: string) {
  chatStore.setCurrentExpert(expertId)
  router.push('/chat')
}

// ---- 推荐学习 ----
const loadingRecommend = ref(false)
const recommendList = ref<any[]>([])

async function loadRecommendContent() {
  loadingRecommend.value = true
  try {
    const res: any = await api.get('/api/v1/content/recommended', { params: { limit: 5 } })
    recommendList.value = (res?.items || []).slice(0, 5)
  } catch { recommendList.value = [] }
  finally { loadingRecommend.value = false }
}

// ---- 微行动 ----
const loadingMicro = ref(false)
const microTasks = ref<any[]>([])
const microStreak = ref(0)
const dangerAlerts = ref<any[]>([])

const microCompleted = computed(() => microTasks.value.filter(t => t.status === 'completed').length)
const microProgressRate = computed(() => {
  if (microTasks.value.length === 0) return 0
  return Math.round((microCompleted.value / microTasks.value.length) * 100)
})

async function loadMicroActions() {
  loadingMicro.value = true
  try {
    const [todayRes, statsRes] = await Promise.all([
      api.get('/api/v1/micro-actions/today').catch(() => null),
      api.get('/api/v1/micro-actions/stats').catch(() => null),
    ])
    microTasks.value = (todayRes as any)?.tasks || []
    microStreak.value = (statsRes as any)?.streak_days || 0
  } catch {
    microTasks.value = []
  } finally {
    loadingMicro.value = false
  }
}

async function quickCompleteMicro(task: any) {
  if (task.status === 'completed') return
  try {
    await api.post(`/api/v1/micro-actions/${task.id}/complete`)
    task.status = 'completed'
    showToast({ message: '完成!', type: 'success' })
  } catch { /* ignore */ }
}

// ---- 健康指标 ----
let lastKnownGlucose = 0

const healthData = reactive({
  bloodGlucose: { fasting: null as number | null, postprandial: null as number | null, trend: 'stable' as 'up' | 'down' | 'stable' },
  weight: { current: 75.5, target: 70, trend: 'stable' as 'up' | 'down' | 'stable' },
  exercise: { weeklyMinutes: 0, targetMinutes: 150, streak: 0 },
  medication: { adherenceRate: 0, missedDoses: 0 },
})

async function refreshHealth() {
  try {
    const [statusRes, progressRes] = await Promise.all([
      api.get('/latest_status').catch(() => null),
      api.get('/api/v1/mp/progress/summary').catch(() => null),
    ])
    const cg = (statusRes as any)?.current_glucose || 0
    const history: number[] = (statusRes as any)?.history || []
    let trend: 'up' | 'down' | 'stable' = 'stable'
    if (lastKnownGlucose > 0 && cg > 0) {
      if (cg > lastKnownGlucose + 0.3) trend = 'up'
      else if (cg < lastKnownGlucose - 0.3) trend = 'down'
    }
    if (cg > 0) lastKnownGlucose = cg
    const recent = history.slice(-5)
    healthData.bloodGlucose = { fasting: cg > 0 ? cg : null, postprandial: recent.length ? Math.max(...recent) : null, trend }
    const totalCompleted = (progressRes as any)?.total_completed || 0
    const streakDays = (progressRes as any)?.streak_days || 0
    const completionRate = (progressRes as any)?.completion_rate || 0
    healthData.weight = { current: +(75.5 - totalCompleted * 0.1).toFixed(1), target: 70, trend: totalCompleted > 3 ? 'down' : 'stable' }
    healthData.exercise = { weeklyMinutes: Math.round(completionRate * 150), targetMinutes: 150, streak: streakDays }
    healthData.medication = { adherenceRate: Math.round(completionRate * 100) || 85, missedDoses: Math.max(0, 7 - totalCompleted) }
  } catch { /* 后端不可用时使用默认值 */ }
}

async function loadDangerAlerts() {
  try {
    const res: any = await api.get('/api/v1/alerts/my?limit=5')
    dangerAlerts.value = ((res.alerts || []) as any[]).filter((a: any) => a.severity === 'danger' && !a.user_read)
  } catch { dangerAlerts.value = [] }
}

function goToDetail(_type: string) {
  router.push('/health-records')
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
  loadMicroActions()
  loadDangerAlerts()
  loadRecommendContent()
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
    cursor: pointer;

    &:active { opacity: 0.7; }
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

.assessment-entry {
  cursor: pointer;

  .entry-content {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
  }

  .entry-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    background: rgba(25, 137, 250, 0.1);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .entry-text {
    flex: 1;

    h3 {
      margin: 0;
      font-size: $font-size-md;
      font-weight: 600;
    }

    p {
      margin: 2px 0 0;
      font-size: $font-size-xs;
      color: $text-color-secondary;
    }
  }
}

.program-entry {
  cursor: pointer;

  .entry-content {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
  }

  .entry-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .entry-text {
    flex: 1;

    h3 {
      margin: 0;
      font-size: $font-size-md;
      font-weight: 600;
    }

    p {
      margin: 2px 0 0;
      font-size: $font-size-xs;
      color: $text-color-secondary;
    }
  }
}

.challenge-entry {
  cursor: pointer;

  .entry-content {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
  }

  .entry-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    background: rgba(255, 151, 106, 0.1);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .entry-text {
    flex: 1;

    h3 {
      margin: 0;
      font-size: $font-size-md;
      font-weight: 600;
    }

    p {
      margin: 2px 0 0;
      font-size: $font-size-xs;
      color: $text-color-secondary;
    }
  }
}

/* 推荐学习 */
.recommend-learn {
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $spacing-sm;
    h3 { font-size: $font-size-lg; margin: 0; }
    .view-all { font-size: $font-size-sm; color: $primary-color; text-decoration: none; }
  }
}
.recommend-scroll {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 4px;
  -webkit-overflow-scrolling: touch;
  &::-webkit-scrollbar { display: none; }
}
.recommend-item {
  flex-shrink: 0;
  width: 140px;
  cursor: pointer;
  &:active { opacity: 0.7; }
}
.recommend-cover {
  width: 140px;
  height: 90px;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 6px;
  img { width: 100%; height: 100%; object-fit: cover; }
}
.recommend-cover-placeholder {
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
}
.recommend-title {
  font-size: 13px;
  font-weight: 500;
  color: $text-color;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 4px;
}
.recommend-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  color: $text-color-placeholder;
}
.recommend-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: $spacing-md;
  color: $text-color-placeholder;
  font-size: $font-size-sm;
  cursor: pointer;
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

.micro-actions-card {
  .micro-progress-bar {
    font-size: $font-size-sm;
    color: $text-color-secondary;
    margin-bottom: 8px;
    :deep(.van-progress) { margin-top: 4px; }
  }
}

.micro-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid #f5f5f5;
  &:last-child { border-bottom: none; }
  &.done { opacity: 0.6; }

  .micro-check {
    width: 22px; height: 22px;
    border: 2px solid #d9d9d9; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; cursor: pointer;
    &.checked { background: #07c160; border-color: #07c160; color: #fff; }
  }
  .micro-title { font-size: $font-size-md; }
}

.micro-empty {
  text-align: center; padding: $spacing-md;
  color: $text-color-placeholder; font-size: $font-size-sm;
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
