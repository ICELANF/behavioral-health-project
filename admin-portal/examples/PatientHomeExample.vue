<script setup lang="ts">
// ============================================================
// PatientHomeExample.vue - 患者首页使用示例
// 展示如何在Vue中集成JourneyPage React组件
// 位置: src/views/client/HomeView.vue (替换或扩展原有文件)
// ============================================================

import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'

// 导入Vue包装器组件
import JourneyPageVue from '@/components/vue-wrappers/JourneyPageVue.vue'

// 导入类型
import type { AuditLog } from '@/types/react-components'

// 用户信息
const userInfo = reactive({
  name: '张先生',
  patientId: 'PT-8821',
  healthScore: 78,
  streakDays: 15,
  points: 1280
})

// 是否显示成长之旅模块
const showJourneyModule = ref(true)

// 今日任务
const todayTasks = ref([
  { id: 1, title: '记录早餐', completed: true },
  { id: 2, title: '服用降糖药', completed: true },
  { id: 3, title: '15分钟散步', completed: false },
  { id: 4, title: '测量血糖', completed: false },
])

// 健康指标
const healthMetrics = reactive({
  glucose: { value: 6.8, unit: 'mmol/L', trend: 'stable' },
  weight: { value: 72.5, unit: 'kg', trend: 'down' },
  exercise: { value: 45, unit: '分钟', trend: 'up' },
  medication: { value: 95, unit: '%', trend: 'stable' },
})

// 事件处理
const handleMessageReceived = (msg: AuditLog) => {
  console.log('收到新消息:', msg)
  message.success('收到新的健康洞察!')
}

const handleTaskToggle = (taskId: number) => {
  const task = todayTasks.value.find(t => t.id === taskId)
  if (task) {
    task.completed = !task.completed
    if (task.completed) {
      message.success(`${task.title} 完成! +10积分`)
      userInfo.points += 10
    }
  }
}

const toggleJourneyModule = () => {
  showJourneyModule.value = !showJourneyModule.value
}

onMounted(() => {
  console.log('患者首页已挂载')
})
</script>

<template>
  <div class="patient-home">
    <!-- 问候卡片 -->
    <div class="greeting-card">
      <div class="greeting-left">
        <h1 class="greeting-text">
          早上好，{{ userInfo.name }} 👋
        </h1>
        <p class="greeting-sub">
          今天是您连续打卡的第 <strong>{{ userInfo.streakDays }}</strong> 天
        </p>
      </div>
      <div class="greeting-right">
        <div class="score-circle">
          <span class="score-value">{{ userInfo.healthScore }}</span>
          <span class="score-label">健康评分</span>
        </div>
      </div>
    </div>

    <!-- 成长之旅模块 (React组件) -->
    <div class="journey-section" v-if="showJourneyModule">
      <div class="section-header">
        <h2 class="section-title">
          <span class="section-icon">🌱</span>
          成长之旅
        </h2>
        <button class="toggle-btn" @click="toggleJourneyModule">
          收起
        </button>
      </div>
      <JourneyPageVue
        :patient-id="userInfo.patientId"
        :show-header="false"
        container-class="journey-wrapper"
        @message-received="handleMessageReceived"
        @mounted="() => console.log('JourneyPage mounted')"
        @error="(e) => console.error('JourneyPage error:', e)"
      />
    </div>

    <!-- 收起状态的展开按钮 -->
    <div class="journey-collapsed" v-else>
      <button class="expand-btn" @click="toggleJourneyModule">
        <span class="section-icon">🌱</span>
        展开成长之旅
      </button>
    </div>

    <!-- 健康指标卡片 -->
    <div class="metrics-section">
      <h2 class="section-title">
        <span class="section-icon">📊</span>
        今日健康指标
      </h2>
      <div class="metrics-grid">
        <div class="metric-card">
          <span class="metric-icon">🩸</span>
          <span class="metric-value">{{ healthMetrics.glucose.value }}</span>
          <span class="metric-unit">{{ healthMetrics.glucose.unit }}</span>
          <span class="metric-label">空腹血糖</span>
          <span :class="['trend-badge', healthMetrics.glucose.trend]">
            {{ healthMetrics.glucose.trend === 'up' ? '↑' : healthMetrics.glucose.trend === 'down' ? '↓' : '→' }}
          </span>
        </div>
        <div class="metric-card">
          <span class="metric-icon">⚖️</span>
          <span class="metric-value">{{ healthMetrics.weight.value }}</span>
          <span class="metric-unit">{{ healthMetrics.weight.unit }}</span>
          <span class="metric-label">体重</span>
          <span :class="['trend-badge', healthMetrics.weight.trend]">
            {{ healthMetrics.weight.trend === 'up' ? '↑' : healthMetrics.weight.trend === 'down' ? '↓' : '→' }}
          </span>
        </div>
        <div class="metric-card">
          <span class="metric-icon">🏃</span>
          <span class="metric-value">{{ healthMetrics.exercise.value }}</span>
          <span class="metric-unit">{{ healthMetrics.exercise.unit }}</span>
          <span class="metric-label">本周运动</span>
          <span :class="['trend-badge', healthMetrics.exercise.trend]">
            {{ healthMetrics.exercise.trend === 'up' ? '↑' : healthMetrics.exercise.trend === 'down' ? '↓' : '→' }}
          </span>
        </div>
        <div class="metric-card">
          <span class="metric-icon">💊</span>
          <span class="metric-value">{{ healthMetrics.medication.value }}</span>
          <span class="metric-unit">{{ healthMetrics.medication.unit }}</span>
          <span class="metric-label">用药依从</span>
          <span :class="['trend-badge', healthMetrics.medication.trend]">
            {{ healthMetrics.medication.trend === 'up' ? '↑' : healthMetrics.medication.trend === 'down' ? '↓' : '→' }}
          </span>
        </div>
      </div>
    </div>

    <!-- 今日任务 -->
    <div class="tasks-section">
      <h2 class="section-title">
        <span class="section-icon">✅</span>
        今日任务
      </h2>
      <div class="tasks-list">
        <div 
          v-for="task in todayTasks" 
          :key="task.id"
          :class="['task-item', { completed: task.completed }]"
          @click="handleTaskToggle(task.id)"
        >
          <span class="task-checkbox">
            {{ task.completed ? '✓' : '' }}
          </span>
          <span class="task-title">{{ task.title }}</span>
          <span class="task-points" v-if="!task.completed">+10</span>
        </div>
      </div>
    </div>

    <!-- 积分显示 -->
    <div class="points-bar">
      <span class="points-label">我的积分</span>
      <span class="points-value">{{ userInfo.points }}</span>
    </div>
  </div>
</template>

<style scoped>
.patient-home {
  min-height: 100vh;
  background: linear-gradient(to bottom, #f0fdf4, white, #f0fdf4);
  padding: 1rem;
  padding-bottom: 5rem;
}

.greeting-card {
  background: linear-gradient(135deg, #22c55e, #16a34a);
  border-radius: 1.5rem;
  padding: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: white;
  margin-bottom: 1.5rem;
  box-shadow: 0 10px 40px rgba(34, 197, 94, 0.3);
}

.greeting-text {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
}

.greeting-sub {
  font-size: 0.875rem;
  opacity: 0.9;
  margin: 0;
}

.greeting-sub strong {
  font-size: 1.25rem;
}

.score-circle {
  width: 80px;
  height: 80px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}

.score-value {
  font-size: 1.75rem;
  font-weight: 700;
}

.score-label {
  font-size: 0.625rem;
  opacity: 0.9;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #166534;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
}

.section-icon {
  font-size: 1.25rem;
}

.toggle-btn,
.expand-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #bbf7d0;
  background: white;
  color: #16a34a;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-btn:hover,
.expand-btn:hover {
  background: #f0fdf4;
}

.expand-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 1rem;
}

.journey-section {
  margin-bottom: 1.5rem;
}

.journey-wrapper {
  border-radius: 1rem;
  overflow: hidden;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  min-height: 300px;
}

.journey-collapsed {
  margin-bottom: 1.5rem;
}

.metrics-section,
.tasks-section {
  margin-bottom: 1.5rem;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.metric-card {
  background: white;
  border-radius: 1rem;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.metric-icon {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.metric-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #166534;
}

.metric-unit {
  font-size: 0.75rem;
  color: #64748b;
}

.metric-label {
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 0.25rem;
}

.trend-badge {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
}

.trend-badge.up { background: #dcfce7; color: #16a34a; }
.trend-badge.down { background: #fee2e2; color: #dc2626; }
.trend-badge.stable { background: #f1f5f9; color: #64748b; }

.tasks-list {
  background: white;
  border-radius: 1rem;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.task-item {
  display: flex;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #f1f5f9;
  cursor: pointer;
  transition: background 0.2s;
}

.task-item:last-child {
  border-bottom: none;
}

.task-item:hover {
  background: #f0fdf4;
}

.task-item.completed {
  opacity: 0.6;
}

.task-item.completed .task-title {
  text-decoration: line-through;
}

.task-checkbox {
  width: 1.5rem;
  height: 1.5rem;
  border: 2px solid #bbf7d0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 0.75rem;
  color: #22c55e;
  font-weight: 700;
}

.task-item.completed .task-checkbox {
  background: #22c55e;
  border-color: #22c55e;
  color: white;
}

.task-title {
  flex: 1;
  font-size: 0.875rem;
  color: #1e293b;
}

.task-points {
  font-size: 0.75rem;
  color: #f59e0b;
  font-weight: 600;
}

.points-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(135deg, #166534, #15803d);
  padding: 1rem;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  color: white;
}

.points-label {
  font-size: 0.875rem;
  opacity: 0.9;
}

.points-value {
  font-size: 1.25rem;
  font-weight: 700;
}
</style>
