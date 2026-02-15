<!--
  HomeView.vue — 首页仪表盘
  根据角色显示不同面板：用户看旅程/行动/积分，教练看学员/处方，管理员看全局
-->

<template>
  <div class="home-view">
    <!-- 欢迎卡 -->
    <div class="welcome-card" :style="{ background: welcomeGradient }">
      <div class="welcome-content">
        <div class="welcome-text">
          <h1 class="welcome-title">{{ greeting }}，{{ authStore.displayName }}</h1>
          <p class="welcome-desc">{{ motivationText }}</p>
        </div>
        <div class="welcome-stage" v-if="journey">
          <div class="stage-badge">{{ stageLabel }}</div>
          <div class="stage-days">第 {{ journey.days_in_stage }} 天</div>
        </div>
      </div>
    </div>

    <!-- 统计卡片行 -->
    <div class="stat-row">
      <div class="stat-card">
        <div class="stat-icon" style="background: #eef8f4;">
          <star-outlined style="color: #2d8e69;" />
        </div>
        <div>
          <div class="stat-value">{{ points?.total || 0 }}</div>
          <div class="stat-label">总积分</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #fff8ee;">
          <thunder-bolt-outlined style="color: #d07031;" />
        </div>
        <div>
          <div class="stat-value">{{ todayActions.length }}</div>
          <div class="stat-label">今日行动</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #f0f0ff;">
          <trophy-outlined style="color: #5b21b6;" />
        </div>
        <div>
          <div class="stat-value">{{ activeChallenges.length }}</div>
          <div class="stat-label">进行中挑战</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #fef2f2;">
          <heart-outlined style="color: #dc2626;" />
        </div>
        <div>
          <div class="stat-value">{{ journey?.trust_score?.toFixed(0) || '—' }}</div>
          <div class="stat-label">信任分</div>
        </div>
      </div>
    </div>

    <!-- 主内容网格 -->
    <div class="content-grid">
      <!-- 今日微行动 -->
      <div class="grid-card actions-card">
        <div class="card-header">
          <h3>今日行动</h3>
          <router-link to="/actions" class="card-link">查看全部</router-link>
        </div>
        <div v-if="todayActions.length" class="action-list">
          <div v-for="action in todayActions.slice(0, 3)" :key="action.id" class="action-item">
            <div class="action-status" :class="action.status"></div>
            <div class="action-info">
              <div class="action-title">{{ action.title }}</div>
              <div class="action-type">{{ action.action_type }}</div>
            </div>
          </div>
        </div>
        <a-empty v-else description="今天还没有行动安排" :image-style="{ height: '48px' }" />
      </div>

      <!-- AI助手入口 -->
      <div class="grid-card agent-card" @click="$router.push('/agent')">
        <div class="agent-icon">
          <robot-outlined />
        </div>
        <h3>AI健康助手</h3>
        <p>与12位专业Agent对话，获取个性化健康指导</p>
        <a-button type="primary" ghost>开始对话</a-button>
      </div>

      <!-- 旅程进度 -->
      <div class="grid-card journey-card">
        <div class="card-header">
          <h3>旅程进度</h3>
          <router-link to="/journey" class="card-link">详情</router-link>
        </div>
        <div class="journey-stages">
          <div
            v-for="(stage, idx) in stages"
            :key="stage.key"
            class="stage-item"
            :class="{ active: idx <= currentStageIndex, current: idx === currentStageIndex }"
          >
            <div class="stage-dot"></div>
            <div class="stage-name">{{ stage.label }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { journeyApi, microActionApi, challengeApi, pointsApi } from '@/api'
import { JourneyStage, STAGE_LABELS, STAGE_COLORS, type JourneyStatus, type MicroAction, type Challenge } from '@/types'
import {
  StarOutlined, ThunderboltOutlined as ThunderBoltOutlined,
  TrophyOutlined, HeartOutlined, RobotOutlined,
} from '@ant-design/icons-vue'

const authStore = useAuthStore()

const journey = ref<JourneyStatus | null>(null)
const todayActions = ref<MicroAction[]>([])
const activeChallenges = ref<Challenge[]>([])
const points = ref<any>(null)

const stages = [
  { key: JourneyStage.S0_AUTHORIZATION, label: 'S0 授权' },
  { key: JourneyStage.S1_EXPLORATION, label: 'S1 探索' },
  { key: JourneyStage.S2_ENGAGEMENT, label: 'S2 投入' },
  { key: JourneyStage.S3_PRACTICE, label: 'S3 实践' },
  { key: JourneyStage.S4_MASTERY, label: 'S4 精通' },
  { key: JourneyStage.S5_GRADUATION, label: 'S5 毕业' },
]

const currentStageIndex = computed(() => {
  if (!journey.value) return 0
  return stages.findIndex(s => s.key === journey.value!.journey_stage)
})

const stageLabel = computed(() => {
  if (!journey.value) return ''
  return STAGE_LABELS[journey.value.journey_stage] || ''
})

const welcomeGradient = computed(() => {
  const color = journey.value ? STAGE_COLORS[journey.value.journey_stage] || '#4aa883' : '#4aa883'
  return `linear-gradient(135deg, ${color}22 0%, ${color}11 100%)`
})

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 12) return '早上好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const motivationText = computed(() => {
  if (!journey.value) return '准备好开始今天的健康之旅了吗？'
  const stage = journey.value.journey_stage
  const map: Record<string, string> = {
    [JourneyStage.S0_AUTHORIZATION]: '看见，就是改变的开始。',
    [JourneyStage.S1_EXPLORATION]: '探索中发现属于你的节奏。',
    [JourneyStage.S2_ENGAGEMENT]: '你正在真实的生活中迈出步伐。',
    [JourneyStage.S3_PRACTICE]: '坚持本身就是一种力量。',
    [JourneyStage.S4_MASTERY]: '节奏感比爆发力更重要。',
    [JourneyStage.S5_GRADUATION]: '你已经成为自己的健康引导者。',
  }
  return map[stage] || '继续你的健康之旅。'
})

onMounted(async () => {
  try {
    const [j, a, c, p] = await Promise.allSettled([
      journeyApi.getStatus(),
      microActionApi.getToday(),
      challengeApi.getMy(),
      pointsApi.getBalance(),
    ])
    if (j.status === 'fulfilled') {
      const raw = j.value
      // 兼容后端字段: current_stage / stage → journey_stage
      journey.value = {
        ...raw,
        journey_stage: raw.journey_stage || raw.current_stage || raw.stage,
        days_in_stage: raw.days_in_stage ?? raw.days ?? 0,
      }
    }
    if (a.status === 'fulfilled') todayActions.value = a.value
    if (c.status === 'fulfilled') activeChallenges.value = c.value.filter((ch: Challenge) => ch.status === 'active')
    if (p.status === 'fulfilled') points.value = p.value
  } catch { /* graceful degradation */ }
})
</script>

<style scoped>
.home-view {
  max-width: 1200px;
  margin: 0 auto;
}
.welcome-card {
  border-radius: 16px;
  padding: 32px;
  margin-bottom: 20px;
  border: 1px solid rgba(0,0,0,0.04);
}
.welcome-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.welcome-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 24px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 6px;
}
.welcome-desc {
  font-size: 15px;
  color: #666;
  margin: 0;
}
.stage-badge {
  background: white;
  padding: 8px 20px;
  border-radius: 24px;
  font-weight: 600;
  font-size: 14px;
  color: #333;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  text-align: center;
}
.stage-days {
  text-align: center;
  font-size: 12px;
  color: #999;
  margin-top: 6px;
}
.stat-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.stat-card {
  background: white;
  border-radius: 14px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  border: 1px solid #f0f0f0;
}
.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}
.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: #1a1a1a;
  line-height: 1.2;
}
.stat-label {
  font-size: 12px;
  color: #999;
}
.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.grid-card {
  background: white;
  border-radius: 14px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  border: 1px solid #f0f0f0;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.card-header h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}
.card-link {
  font-size: 13px;
  color: #2d8e69;
}
.action-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.action-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 10px;
}
.action-status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.action-status.pending { background: #d1d5db; }
.action-status.done { background: #34d399; }
.action-status.attempted { background: #fbbf24; }
.action-title { font-size: 14px; font-weight: 500; color: #333; }
.action-type { font-size: 12px; color: #999; }
.agent-card {
  text-align: center;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}
.agent-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}
.agent-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: linear-gradient(135deg, #e0f2fe, #bae6fd);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: #0284c7;
}
.agent-card h3 { margin: 0; font-size: 16px; }
.agent-card p { margin: 0; font-size: 13px; color: #999; }
.journey-card {
  grid-column: 1 / -1;
}
.journey-stages {
  display: flex;
  align-items: center;
  gap: 0;
  position: relative;
}
.stage-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  position: relative;
}
.stage-item::before {
  content: '';
  position: absolute;
  top: 7px;
  left: -50%;
  right: 50%;
  height: 2px;
  background: #e5e7eb;
}
.stage-item:first-child::before { display: none; }
.stage-item.active::before { background: #4aa883; }
.stage-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #e5e7eb;
  position: relative;
  z-index: 1;
  transition: all 0.3s;
}
.stage-item.active .stage-dot { background: #4aa883; }
.stage-item.current .stage-dot {
  background: #4aa883;
  box-shadow: 0 0 0 4px rgba(74, 168, 131, 0.2);
  transform: scale(1.2);
}
.stage-name {
  font-size: 11px;
  color: #999;
  text-align: center;
}
.stage-item.active .stage-name { color: #333; font-weight: 500; }

@media (max-width: 768px) {
  .stat-row { grid-template-columns: repeat(2, 1fr); }
  .content-grid { grid-template-columns: 1fr; }
}
</style>
