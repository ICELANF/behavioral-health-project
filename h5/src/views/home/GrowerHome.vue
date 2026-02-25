<!-- ═══════════════════════════════════════════════════════════ -->
<!-- GrowerHome.vue — 成长者首页：进展可见，行为有感知 -->
<!-- ═══════════════════════════════════════════════════════════ -->
<!-- 文件路径: h5/src/views/home/GrowerHome.vue -->
<template>
  <div class="grower-home">
    <!-- 头部：连续天数 + 稳定度 -->
    <div class="grower-hero">
      <div class="hero-bg" />
      <div class="hero-inner">
        <div class="streak-badge">
          <span class="streak-fire">🔥</span>
          <span class="streak-num">{{ streakDays }}</span>
          <span class="streak-label">天连续</span>
        </div>
        <div class="stability-ring">
          <svg viewBox="0 0 80 80" class="ring-svg">
            <circle cx="40" cy="40" r="34" class="ring-bg" />
            <circle
              cx="40" cy="40" r="34"
              class="ring-fill"
              :stroke-dasharray="`${stabilityScore * 2.136} 213.6`"
            />
          </svg>
          <div class="ring-label">
            <span class="ring-score">{{ stabilityScore }}</span>
            <span class="ring-text">行为稳定度</span>
          </div>
        </div>
        <div class="hero-meta">
          <p class="hero-name">{{ userInfo.username || '成长者' }}</p>
          <p class="hero-sub">{{ trendText }}</p>
        </div>
      </div>
    </div>

    <!-- 今日处方任务 -->
    <div class="tasks-section">
      <div class="section-header">
        <span class="section-title">今日行为任务</span>
        <span class="section-count">{{ completedCount }}/{{ tasks.length }}</span>
      </div>
      <div class="tasks-list">
        <div
          v-for="task in tasks"
          :key="task.id"
          class="task-item"
          :class="{ completed: task.done }"
          @click="toggleTask(task)"
        >
          <div class="task-check">
            <van-icon :name="task.done ? 'checked' : 'circle'" />
          </div>
          <div class="task-body">
            <p class="task-name">{{ task.name }}</p>
            <p class="task-meta">{{ task.duration }} · {{ task.domain }}</p>
          </div>
          <van-tag :type="domainColor(task.domain)" size="small">
            {{ task.domain }}
          </van-tag>
        </div>
      </div>
    </div>

    <!-- AI 智能建议（处方联动）-->
    <div class="ai-nudge-card" v-if="aiNudge" @click="openChat">
      <div class="ai-icon">🤖</div>
      <div class="ai-content">
        <p class="ai-title">本周数据洞察 <AiContentBadge compact /></p>
        <p class="ai-text">{{ aiNudge }}</p>
      </div>
      <van-icon name="arrow" color="#aaa" />
    </div>

    <!-- 周报快览 -->
    <div class="weekly-card" @click="router.push('/weekly-report')">
      <div class="wk-header">
        <span class="wk-title">本周总结</span>
        <van-tag type="primary" size="small">查看完整</van-tag>
      </div>
      <div class="wk-metrics">
        <div class="metric-item" v-for="m in weekMetrics" :key="m.label">
          <span class="metric-val" :class="m.trend">{{ m.value }}</span>
          <span class="metric-lbl">{{ m.label }}</span>
          <span class="metric-arrow">{{ m.trend === 'up' ? '↑' : m.trend === 'down' ? '↓' : '─' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/index'
import AiContentBadge from '@/components/common/AiContentBadge.vue'
const router = useRouter()
const userInfo = ref<any>({})
const streakDays = ref(0)
const stabilityScore = ref(0)
const tasks = ref<any[]>([])
const aiNudge = ref<string | null>(null)
const weekMetrics = ref<any[]>([])

const completedCount = computed(() => tasks.value.filter(t => t.done).length)
const trendText = computed(() => {
  if (stabilityScore.value >= 80) return '本周比上周更稳定 ✨'
  if (stabilityScore.value >= 60) return '保持节奏，继续前进'
  return '今天是重新开始的好时机'
})

const domainColor = (d: string) => {
  const map: Record<string, string> = {
    '睡眠': 'primary', '运动': 'success', '营养': 'warning', '情绪': 'danger'
  }
  return map[d] || 'default'
}

const toggleTask = async (task: any) => {
  const newState = !task.done
  task.done = newState
  try {
    if (newState) {
      await api.post(`/api/v1/tasks/${task.id}/complete`)
    } else {
      await api.post(`/api/v1/tasks/${task.id}/uncomplete`)
    }
  } catch { /* 乐观更新已生效 */ }
}

const openChat = () => router.push('/chat')

onMounted(async () => {
  try {
    const res: any = await api.get('/api/v1/home/grower-dashboard')
    const d = res || {}
    streakDays.value = d.streak_days || 0
    stabilityScore.value = d.stability_score || 0
    tasks.value = d.today_tasks || []
    aiNudge.value = d.ai_nudge || null
    weekMetrics.value = d.week_metrics || []
    userInfo.value = d.user || {}
  } catch {}
})
</script>

<style scoped>
.grower-home { min-height: 100vh; background: #F7F8FB; padding-bottom: calc(80px + env(safe-area-inset-bottom, 0px)); }
.grower-hero { position: relative; padding: 52px 20px 28px; }
.hero-bg {
  position: absolute; inset: 0;
  background: linear-gradient(135deg, #1B5E20 0%, #2E7D32 50%, #388E3C 100%);
  border-radius: 0 0 36px 36px;
}
.hero-inner {
  position: relative; z-index: 1;
  display: flex; align-items: center; gap: 16px;
}
.streak-badge {
  display: flex; flex-direction: column; align-items: center;
  background: rgba(255,255,255,0.15); border-radius: 14px;
  padding: 10px 14px; min-width: 64px;
}
.streak-fire { font-size: 22px; }
.streak-num { font-size: 28px; font-weight: 800; color: #FFF9C4; line-height: 1; }
.streak-label { font-size: 11px; color: rgba(255,255,255,0.8); }
.stability-ring { position: relative; width: 80px; height: 80px; flex-shrink: 0; }
.ring-svg { width: 80px; height: 80px; transform: rotate(-90deg); }
.ring-bg { fill: none; stroke: rgba(255,255,255,0.2); stroke-width: 7; }
.ring-fill {
  fill: none; stroke: #A5D6A7; stroke-width: 7;
  stroke-linecap: round; transition: stroke-dasharray 1s ease;
}
.ring-label {
  position: absolute; inset: 0;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
}
.ring-score { font-size: 20px; font-weight: 800; color: #fff; line-height: 1; }
.ring-text { font-size: 9px; color: rgba(255,255,255,0.75); }
.hero-meta { color: #fff; }
.hero-name { font-size: 18px; font-weight: 700; margin: 0 0 4px; }
.hero-sub { font-size: 12px; opacity: 0.8; margin: 0; }
.tasks-section { margin: 16px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.section-title { font-size: 15px; font-weight: 700; color: #222; }
.section-count { font-size: 13px; color: #888; }
.tasks-list { display: flex; flex-direction: column; gap: 10px; }
.task-item {
  display: flex; align-items: center; gap: 12px;
  background: #fff; border-radius: 14px; padding: 14px;
  box-shadow: 0 1px 8px rgba(0,0,0,0.05);
  transition: opacity 0.2s;
}
.task-item.completed { opacity: 0.55; }
.task-check { font-size: 20px; color: #4CAF50; flex-shrink: 0; }
.task-body { flex: 1; }
.task-name { font-size: 14px; color: #333; margin: 0 0 2px; font-weight: 500; }
.task-meta { font-size: 11px; color: #aaa; margin: 0; }
.ai-nudge-card {
  margin: 0 16px 12px;
  background: linear-gradient(135deg, #E3F2FD, #EDE7F6);
  border-radius: 14px; padding: 14px 16px;
  display: flex; align-items: center; gap: 12px; cursor: pointer;
}
.ai-icon { font-size: 28px; flex-shrink: 0; }
.ai-content { flex: 1; }
.ai-title { font-size: 12px; color: #7B1FA2; font-weight: 600; margin: 0 0 4px; }
.ai-text { font-size: 13px; color: #444; margin: 0; line-height: 1.5; }
.weekly-card { margin: 0 16px; background: #fff; border-radius: 16px; padding: 16px; box-shadow: 0 1px 8px rgba(0,0,0,0.04); }
.wk-header { display: flex; justify-content: space-between; margin-bottom: 14px; }
.wk-title { font-size: 15px; font-weight: 700; color: #222; }
.wk-metrics { display: grid; grid-template-columns: repeat(3,1fr); gap: 10px; }
.metric-item { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.metric-val { font-size: 20px; font-weight: 800; color: #222; }
.metric-val.up { color: #4CAF50; }
.metric-val.down { color: #F44336; }
.metric-lbl { font-size: 10px; color: #aaa; }
.metric-arrow { font-size: 12px; color: #888; }
</style>
