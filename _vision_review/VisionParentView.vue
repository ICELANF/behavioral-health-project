<template>
  <!--
    VisionParentView.vue — 家长专属视图
    路由: /vision-parent
    角色: 绑定家长账号
    核心: 孩子摘要 + 家长任务 + 绑定管理
  -->
  <div class="vision-parent-view">

    <!-- 顶部：选择孩子 -->
    <div class="child-selector" v-if="children.length > 1">
      <button
        v-for="child in children"
        :key="child.id"
        class="child-tab"
        :class="{ active: selectedChildId === child.id }"
        @click="selectChild(child.id)"
      >
        {{ child.name }}
      </button>
    </div>

    <template v-if="currentChild">

      <!-- ① 孩子风险摘要卡 -->
      <section class="risk-card" :class="`risk-${currentChild.risk_level.toLowerCase()}`">
        <div class="risk-header">
          <div>
            <p class="child-name">{{ currentChild.name }}</p>
            <p class="child-meta">{{ currentChild.age }}岁 · {{ currentChild.school_grade }}</p>
          </div>
          <div class="risk-badge">
            <span class="risk-icon">{{ riskIcon }}</span>
            <span class="risk-text">{{ riskLabel }}</span>
          </div>
        </div>

        <div class="risk-stats">
          <div class="stat-item">
            <span class="stat-val">{{ currentChild.latest_exam?.right_eye || '--' }}D</span>
            <span class="stat-key">右眼度数</span>
          </div>
          <div class="stat-item">
            <span class="stat-val">{{ currentChild.latest_exam?.left_eye || '--' }}D</span>
            <span class="stat-key">左眼度数</span>
          </div>
          <div class="stat-item">
            <span class="stat-val">{{ currentChild.week_compliance_pct }}%</span>
            <span class="stat-key">本周达标率</span>
          </div>
        </div>
      </section>

      <!-- ② 家长今日任务 -->
      <section class="parent-tasks-section">
        <h3 class="section-title">今日家长任务</h3>
        <div
          v-for="(task, idx) in todayParentTasks"
          :key="idx"
          class="task-item"
          :class="{ done: task.done }"
          @click="toggleTask(idx)"
        >
          <span class="task-check">{{ task.done ? '✅' : '⬜' }}</span>
          <span class="task-text">{{ task.text }}</span>
        </div>

        <!-- 快捷求助 -->
        <button class="help-btn" @click="requestCoachHelp">
          🆘 向教练求助
        </button>
      </section>

      <!-- ③ 孩子本周行为进展 -->
      <section class="week-progress">
        <h3 class="section-title">{{ currentChild.name }} 本周进展</h3>
        <div class="progress-rows">
          <div class="prog-row" v-for="dim in weeklyDimensions" :key="dim.key">
            <span class="prog-icon">{{ dim.icon }}</span>
            <div class="prog-info">
              <span class="prog-name">{{ dim.name }}</span>
              <div class="prog-bar-wrap">
                <div
                  class="prog-bar-fill"
                  :style="{ width: dim.pct + '%', background: dim.color }"
                />
              </div>
            </div>
            <span class="prog-val">{{ dim.val }}</span>
          </div>
        </div>
      </section>

      <!-- ④ 专家/教练建议摘要 -->
      <section class="expert-summary" v-if="expertSummary">
        <h3 class="section-title">专家 / 教练建议</h3>
        <div class="summary-card">
          <p class="summary-from">{{ expertSummary.from }}</p>
          <p class="summary-content">{{ expertSummary.content }}</p>
          <p class="summary-time">{{ expertSummary.time }}</p>
        </div>
      </section>

      <!-- ⑤ 绑定管理 -->
      <section class="binding-mgmt">
        <h3 class="section-title">绑定设置</h3>
        <div class="binding-item">
          <span class="binding-label">接收推送的最低风险等级</span>
          <select v-model="bindingSetting.notifyThreshold" @change="saveBindingSetting">
            <option value="NORMAL">全部（NORMAL+）</option>
            <option value="WATCH">观察期+（WATCH+）</option>
            <option value="ALERT">警示期+（ALERT+）</option>
            <option value="URGENT">仅紧急（URGENT）</option>
          </select>
        </div>
        <div class="binding-item">
          <span class="binding-label">允许代录行为数据</span>
          <label class="toggle-switch">
            <input
              type="checkbox"
              v-model="bindingSetting.canInputBehavior"
              @change="saveBindingSetting"
            />
            <span class="toggle-slider" />
          </label>
        </div>
      </section>

    </template>

    <!-- 未绑定状态 -->
    <div class="no-binding" v-else>
      <p>暂未绑定孩子的账号</p>
      <button class="bind-btn" @click="showBindModal = true">+ 绑定孩子账号</button>
    </div>

  </div>
</template>


<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  parentUserId: { type: String, required: true },
})

const children = ref([])
const selectedChildId = ref(null)

const currentChild = computed(
  () => children.value.find(c => c.id === selectedChildId.value) || null
)

// 风险等级展示映射
const RISK_ICON  = { NORMAL: '🟢', WATCH: '🟡', ALERT: '🟠', URGENT: '🔴' }
const RISK_LABEL = { NORMAL: '正常', WATCH: '观察期', ALERT: '警示期', URGENT: '紧急' }

const riskIcon  = computed(() => RISK_ICON[currentChild.value?.risk_level] || '⚪')
const riskLabel = computed(() => RISK_LABEL[currentChild.value?.risk_level] || '未知')

// 今日家长任务（从 VisionRxAgent 最新家长版处方中提取）
const todayParentTasks = ref([
  { text: '晚饭后陪孩子户外活动 30 分钟', done: false },
  { text: '检查作业台灯照度 > 500lux', done: false },
  { text: '确认孩子今日屏幕时间是否超标', done: false },
])

function toggleTask(idx) {
  todayParentTasks.value[idx].done = !todayParentTasks.value[idx].done
}

// 本周维度进展
const weeklyDimensions = computed(() => {
  const c = currentChild.value
  if (!c) return []
  return [
    {
      key: 'outdoor', icon: '🌿', name: '户外活动',
      pct: Math.min((c.avg_outdoor_minutes || 0) / 120 * 100, 100),
      val: `${c.avg_outdoor_minutes || 0} 分钟/天均`,
      color: '#4ade80',
    },
    {
      key: 'screen', icon: '📱', name: '屏幕控制',
      pct: Math.max(0, 100 - ((c.avg_screen_minutes || 120) - 120) / 120 * 100),
      val: `${c.avg_screen_minutes || '--'} 分钟/天均`,
      color: c.avg_screen_minutes > 120 ? '#f87171' : '#60a5fa',
    },
    {
      key: 'sleep', icon: '💤', name: '睡眠',
      pct: Math.min((c.avg_sleep_hours || 0) / 9 * 100, 100),
      val: `${(c.avg_sleep_hours || 0).toFixed(1)} 小时/天均`,
      color: '#a78bfa',
    },
    {
      key: 'exercise', icon: '👁️', name: '眼保健操',
      pct: (c.exercise_days_this_week || 0) / 7 * 100,
      val: `本周 ${c.exercise_days_this_week || 0}/7 天`,
      color: '#fb923c',
    },
  ]
})

const expertSummary = ref({
  from: '李主任（行诊智伴）',
  content: '孩子目前处于观察期，建议继续保持每日户外时间，下次检查前重点关注屏幕时间控制。',
  time: '昨天 14:30',
})

const bindingSetting = ref({
  notifyThreshold: 'WATCH',
  canInputBehavior: true,
})

function saveBindingSetting() {
  // axios.put(`/v1/vision/behavior/parent-binding`, {
  //   student_user_id: selectedChildId.value,
  //   parent_user_id: props.parentUserId,
  //   notify_risk_threshold: bindingSetting.value.notifyThreshold,
  //   can_input_behavior: bindingSetting.value.canInputBehavior,
  // })
}

function requestCoachHelp() {
  // axios.post(`/v1/coach/help-request`, {
  //   parent_user_id: props.parentUserId,
  //   student_user_id: selectedChildId.value,
  //   priority: 'HIGH',
  // })
  alert('已向教练发送求助请求，通常 2 小时内响应。')
}

function selectChild(id) {
  selectedChildId.value = id
}

onMounted(async () => {
  // const res = await axios.get(`/v1/vision/behavior/parent-binding/${props.parentUserId}`)
  // children.value = res.data  // 包含聚合摘要数据
  // if (children.value.length > 0) selectedChildId.value = children.value[0].id

  // Mock 数据
  children.value = [{
    id: 'mock-student-1',
    name: '小明',
    age: 12,
    school_grade: '初一',
    risk_level: 'WATCH',
    week_compliance_pct: 72,
    avg_outdoor_minutes: 85,
    avg_screen_minutes: 140,
    avg_sleep_hours: 8.5,
    exercise_days_this_week: 4,
    latest_exam: { right_eye: -2.75, left_eye: -2.50 },
  }]
  selectedChildId.value = children.value[0].id
})
</script>


<style scoped>
.vision-parent-view {
  padding: 16px;
  max-width: 480px;
  margin: 0 auto;
  background: #f8faff;
  min-height: 100vh;
}

/* 孩子选择器 */
.child-selector {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  overflow-x: auto;
}

.child-tab {
  padding: 6px 16px;
  border: 1px solid #d1d5db;
  border-radius: 20px;
  background: white;
  font-size: 14px;
  cursor: pointer;
  white-space: nowrap;
}

.child-tab.active {
  background: #3b82f6;
  border-color: #3b82f6;
  color: white;
}

/* 风险卡 */
.risk-card {
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 12px;
  color: white;
}

.risk-card.risk-normal  { background: linear-gradient(135deg, #22c55e, #16a34a); }
.risk-card.risk-watch   { background: linear-gradient(135deg, #facc15, #ca8a04); }
.risk-card.risk-alert   { background: linear-gradient(135deg, #fb923c, #ea580c); }
.risk-card.risk-urgent  { background: linear-gradient(135deg, #f87171, #dc2626); }

.risk-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.child-name { font-size: 18px; font-weight: 700; margin: 0; }
.child-meta { font-size: 13px; opacity: .85; margin: 4px 0 0; }

.risk-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(255,255,255,.25);
  border-radius: 10px;
  padding: 6px 12px;
}

.risk-icon { font-size: 20px; }
.risk-text { font-size: 12px; font-weight: 600; }

.risk-stats {
  display: flex;
  justify-content: space-around;
}

.stat-item { text-align: center; }
.stat-val { display: block; font-size: 22px; font-weight: 700; }
.stat-key { font-size: 11px; opacity: .8; }

/* 通用 section */
section {
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

/* 家长任务 */
.task-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid #f3f4f6;
  cursor: pointer;
}

.task-check { font-size: 18px; }
.task-text  { font-size: 14px; color: #333; }
.task-item.done .task-text { color: #aaa; text-decoration: line-through; }

.help-btn {
  width: 100%;
  margin-top: 12px;
  padding: 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

/* 进展条 */
.prog-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.prog-icon { font-size: 18px; flex-shrink: 0; }

.prog-info { flex: 1; }
.prog-name { font-size: 12px; color: #666; display: block; margin-bottom: 4px; }

.prog-bar-wrap {
  background: #f3f4f6;
  border-radius: 4px;
  height: 6px;
  overflow: hidden;
}

.prog-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width .4s;
}

.prog-val { font-size: 12px; color: #888; white-space: nowrap; }

/* 专家摘要 */
.summary-card {
  background: #f8faff;
  border-radius: 8px;
  padding: 12px;
}

.summary-from    { font-size: 13px; font-weight: 600; color: #3b82f6; margin: 0 0 6px; }
.summary-content { font-size: 14px; color: #333; line-height: 1.6; margin: 0 0 6px; }
.summary-time    { font-size: 12px; color: #aaa; margin: 0; }

/* 绑定设置 */
.binding-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f3f4f6;
}

.binding-label { font-size: 14px; color: #333; }

.binding-item select {
  padding: 4px 8px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
}

.toggle-switch { position: relative; width: 44px; height: 24px; }

.toggle-switch input { opacity: 0; width: 0; height: 0; }

.toggle-slider {
  position: absolute;
  inset: 0;
  background: #e5e7eb;
  border-radius: 24px;
  cursor: pointer;
  transition: background .2s;
}

.toggle-switch input:checked + .toggle-slider { background: #3b82f6; }

.toggle-slider::before {
  content: '';
  position: absolute;
  width: 18px; height: 18px;
  left: 3px; top: 3px;
  background: white;
  border-radius: 50%;
  transition: transform .2s;
}

.toggle-switch input:checked + .toggle-slider::before { transform: translateX(20px); }

/* 空状态 */
.no-binding {
  text-align: center;
  padding: 60px 20px;
  color: #888;
}

.bind-btn {
  margin-top: 16px;
  padding: 12px 24px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  cursor: pointer;
}
</style>
