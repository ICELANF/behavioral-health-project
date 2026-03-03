<template>
  <!--
    Admin 指挥中心 Dashboard
    飞轮目标: 全局管控 — 一屏看全局，异常秒感知，决策有数据
    核心设计:
      ❌ 旧版: Admin与Coach共用界面，看到的是学员列表而非系统全局
      ✅ 新版: 指挥中心式布局 — 顶部告警→4大指标→渠道健康→Agent监控→人员效率
    位置: admin-portal/src/views/admin/AdminCommandCenter.vue
  -->
  <div class="command-center">
    <!-- ═══ 告警横幅 (有异常时才出现) ═══ -->
    <div class="alert-banner" v-if="activeAlerts.length > 0">
      <div class="alert-scroll">
        <div v-for="alert in activeAlerts" :key="alert.id" class="alert-item" :class="alert.level">
          <span class="alert-icon">{{ alertIcon(alert.level) }}</span>
          <span class="alert-text">{{ alert.message }}</span>
          <span class="alert-time">{{ alert.time }}</span>
          <button class="alert-dismiss" @click="dismissAlert(alert.id)">✕</button>
        </div>
      </div>
    </div>

    <!-- ═══ 四大核心指标 ═══ -->
    <div class="kpi-grid">
      <div v-for="kpi in coreKPIs" :key="kpi.label" class="kpi-card" :class="kpi.status">
        <div class="kpi-header">
          <span class="kpi-icon">{{ kpi.icon }}</span>
          <span class="kpi-trend" :class="kpi.trendDir">
            {{ kpi.trendDir === 'up' ? '↑' : kpi.trendDir === 'down' ? '↓' : '→' }}
            {{ kpi.trendPct }}%
          </span>
        </div>
        <div class="kpi-value">{{ kpi.value }}</div>
        <div class="kpi-label">{{ kpi.label }}</div>
        <div class="kpi-sublabel">{{ kpi.sub }}</div>
      </div>
    </div>

    <div class="center-body">
      <!-- ═══ 左列 ═══ -->
      <div class="column-left">
        <!-- 渠道健康 -->
        <div class="panel">
          <div class="panel-header">
            <h3>渠道健康</h3>
            <span class="panel-badge live">实时</span>
          </div>
          <div class="channel-grid">
            <div v-for="ch in channels" :key="ch.name" class="channel-card">
              <div class="ch-header">
                <span class="ch-icon">{{ ch.icon }}</span>
                <span class="ch-status" :class="ch.status">{{ ch.statusLabel }}</span>
              </div>
              <div class="ch-name">{{ ch.name }}</div>
              <div class="ch-metrics">
                <div class="ch-metric">
                  <span class="ch-num">{{ ch.dau }}</span>
                  <span class="ch-label">DAU</span>
                </div>
                <div class="ch-metric">
                  <span class="ch-num">{{ ch.msgToday }}</span>
                  <span class="ch-label">今日消息</span>
                </div>
                <div class="ch-metric">
                  <span class="ch-num">{{ ch.avgReply }}</span>
                  <span class="ch-label">平均回复</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 用户漏斗 -->
        <div class="panel">
          <div class="panel-header">
            <h3>用户转化漏斗</h3>
          </div>
          <div class="funnel">
            <div v-for="(step, i) in funnelSteps" :key="step.label" class="funnel-row">
              <div class="funnel-bar" :style="{ width: step.pct + '%', background: step.color }">
                <span class="funnel-label">{{ step.label }}</span>
                <span class="funnel-value">{{ step.count }}</span>
              </div>
              <span class="funnel-rate" v-if="i > 0">{{ step.convRate }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══ 右列 ═══ -->
      <div class="column-right">
        <!-- Agent 监控 -->
        <div class="panel">
          <div class="panel-header">
            <h3>Agent 监控 (33个)</h3>
            <span class="panel-badge" :class="agentHealthAll ? 'ok' : 'warn'">
              {{ agentHealthAll ? '全部正常' : `${agentIssueCount}个异常` }}
            </span>
          </div>
          <div class="agent-monitor">
            <div v-for="group in agentGroups" :key="group.name" class="agent-group">
              <div class="group-label">{{ group.name }} ({{ group.agents.length }})</div>
              <div class="agent-dots">
                <div v-for="a in group.agents" :key="a.id"
                  class="agent-dot" :class="a.status" :title="`${a.name}: ${a.statusLabel}`">
                  <span class="dot-inner" />
                </div>
              </div>
            </div>
          </div>

          <!-- Agent性能Top5 -->
          <div class="agent-perf">
            <div class="perf-header">
              <span>最慢Agent (P95响应)</span>
            </div>
            <div v-for="a in slowestAgents" :key="a.name" class="perf-row">
              <span class="perf-name">{{ a.name }}</span>
              <div class="perf-bar-bg">
                <div class="perf-bar-fill" :style="{ width: (a.p95 / maxP95 * 100) + '%' }"
                  :class="{ slow: a.p95 > 3000, warn: a.p95 > 2000 }" />
              </div>
              <span class="perf-value" :class="{ slow: a.p95 > 3000 }">{{ a.p95 }}ms</span>
            </div>
          </div>
        </div>

        <!-- 教练效率 -->
        <div class="panel">
          <div class="panel-header">
            <h3>教练效率排行</h3>
          </div>
          <div class="coach-ranking">
            <div v-for="(c, i) in coachRanking" :key="c.name" class="coach-row">
              <span class="coach-rank" :class="{ top: i < 3 }">{{ i + 1 }}</span>
              <span class="coach-name">{{ c.name }}</span>
              <span class="coach-students">{{ c.students }}人</span>
              <span class="coach-reviewed">{{ c.todayReviewed }}审</span>
              <span class="coach-avg">{{ c.avgSeconds }}s/条</span>
            </div>
          </div>
        </div>

        <!-- 安全红线 -->
        <div class="panel panel-safety">
          <div class="panel-header">
            <h3>安全红线 24h</h3>
          </div>
          <div class="safety-grid">
            <div v-for="s in safetyMetrics" :key="s.rule" class="safety-item">
              <div class="safety-rule">{{ s.rule }}</div>
              <div class="safety-count" :class="{ triggered: s.count > 0 }">{{ s.count }}</div>
              <div class="safety-label">{{ s.label }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { adminFlywheelApi, type CoreKPI, type ChannelHealth, type FunnelStep, type AgentGroup, type AgentPerf, type CoachRank, type SafetyMetric, type ActiveAlert } from '@/api/admin-flywheel-api'

// ── Reactive state ──
const activeAlerts = ref<ActiveAlert[]>([])
const coreKPIs = ref<CoreKPI[]>([])
const channels = ref<ChannelHealth[]>([])
const funnelSteps = ref<FunnelStep[]>([])
const agentGroups = ref<AgentGroup[]>([])
const slowestAgents = ref<AgentPerf[]>([])
const coachRanking = ref<CoachRank[]>([])
const safetyMetrics = ref<SafetyMetric[]>([])
const loading = ref(true)

function alertIcon(level: string) {
  return level === 'critical' ? '🚨' : level === 'warning' ? '⚠️' : 'ℹ️'
}

async function dismissAlert(id: string) {
  activeAlerts.value = activeAlerts.value.filter(a => a.id !== id)
  try {
    await adminFlywheelApi.dismissAlert(id)
  } catch (e) {
    console.warn('Dismiss alert API failed', e)
  }
}

const agentHealthAll = computed(() =>
  agentGroups.value.every(g => g.agents.every(a => a.status === 'ok'))
)
const agentIssueCount = computed(() =>
  agentGroups.value.reduce((sum, g) => sum + g.agents.filter(a => a.status !== 'ok').length, 0)
)
const maxP95 = computed(() => {
  const vals = slowestAgents.value.map(a => a.p95)
  return vals.length > 0 ? Math.max(...vals) : 1
})

async function loadAll() {
  loading.value = true
  const [kpiR, chR, funR, agMonR, agPerfR, coachR, safeR, alertR] = await Promise.allSettled([
    adminFlywheelApi.getKpiRealtime(),
    adminFlywheelApi.getChannelsHealth(),
    adminFlywheelApi.getFunnel(),
    adminFlywheelApi.getAgentsMonitor(),
    adminFlywheelApi.getAgentsPerformance(5),
    adminFlywheelApi.getCoachesRanking(),
    adminFlywheelApi.getSafety24h(),
    adminFlywheelApi.getActiveAlerts(),
  ])

  if (kpiR.status === 'fulfilled') coreKPIs.value = kpiR.value
  else console.warn('KPI load failed:', kpiR.reason)

  if (chR.status === 'fulfilled') channels.value = chR.value
  else console.warn('Channel load failed:', chR.reason)

  if (funR.status === 'fulfilled') funnelSteps.value = funR.value
  else console.warn('Funnel load failed:', funR.reason)

  if (agMonR.status === 'fulfilled') agentGroups.value = agMonR.value
  else console.warn('Agent monitor load failed:', agMonR.reason)

  if (agPerfR.status === 'fulfilled') slowestAgents.value = agPerfR.value
  else console.warn('Agent perf load failed:', agPerfR.reason)

  if (coachR.status === 'fulfilled') coachRanking.value = coachR.value
  else console.warn('Coach ranking load failed:', coachR.reason)

  if (safeR.status === 'fulfilled') safetyMetrics.value = safeR.value
  else console.warn('Safety load failed:', safeR.reason)

  if (alertR.status === 'fulfilled') activeAlerts.value = alertR.value
  else console.warn('Alerts load failed:', alertR.reason)
  loading.value = false
}

// Polling: refresh KPI + alerts every 5 minutes
let pollTimer: ReturnType<typeof setInterval> | null = null

async function pollRefresh() {
  const [kpiR, alertR] = await Promise.allSettled([
    adminFlywheelApi.getKpiRealtime(),
    adminFlywheelApi.getActiveAlerts(),
  ])
  if (kpiR.status === 'fulfilled') coreKPIs.value = kpiR.value
  if (alertR.status === 'fulfilled') activeAlerts.value = alertR.value
}

onMounted(() => {
  loadAll()
  pollTimer = setInterval(pollRefresh, 5 * 60 * 1000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
/* ── 页面底色：浅蓝 ── */
.command-center { min-height: 100vh; background: #EEF4FB; color: #1E3A5F; }

/* ── 告警横幅（保留深色，告警需强对比） ── */
.alert-banner { background: #7f1d1d; padding: 0; overflow: hidden; }
.alert-scroll { display: flex; flex-direction: column; }
.alert-item {
  display: flex; align-items: center; gap: 8px; padding: 8px 16px;
  font-size: 13px; border-bottom: 1px solid rgba(255,255,255,0.1);
  color: #f1f5f9;
}
.alert-item.critical { background: #991b1b; }
.alert-item.warning { background: #78350f; }
.alert-text { flex: 1; }
.alert-time { font-size: 11px; opacity: 0.6; }
.alert-dismiss { background: none; border: none; color: rgba(255,255,255,0.5); cursor: pointer; font-size: 14px; }

/* ── KPI ── */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; padding: 16px 20px; }
.kpi-card {
  background: #fff; border-radius: 12px; padding: 14px 16px;
  border: 1px solid #DBEAFE; box-shadow: 0 1px 4px rgba(59,130,246,0.07);
}
.kpi-card.warn { border-left: 3px solid #f59e0b; }
.kpi-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.kpi-icon { font-size: 18px; }
.kpi-trend { font-size: 12px; font-weight: 700; }
.kpi-trend.up { color: #16a34a; }
.kpi-trend.down { color: #dc2626; }
.kpi-value { font-size: 28px; font-weight: 900; color: #1E3A5F; }
.kpi-label { font-size: 12px; color: #5B7EA6; margin-top: 2px; }
.kpi-sublabel { font-size: 10px; color: #93B5D0; margin-top: 2px; }

/* ── 主体 ── */
.center-body { display: flex; gap: 12px; padding: 0 20px 20px; }
.column-left, .column-right { flex: 1; display: flex; flex-direction: column; gap: 12px; }

.panel {
  background: #fff; border-radius: 12px; padding: 16px;
  border: 1px solid #DBEAFE; box-shadow: 0 1px 4px rgba(59,130,246,0.07);
}
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.panel-header h3 { font-size: 14px; font-weight: 700; margin: 0; color: #1E3A5F; }
.panel-badge { font-size: 10px; padding: 2px 8px; border-radius: 4px; font-weight: 700; }
.panel-badge.live { background: #dcfce7; color: #15803d; }
.panel-badge.ok { background: #dcfce7; color: #15803d; }
.panel-badge.warn { background: #fee2e2; color: #dc2626; }

/* 渠道 */
.channel-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.channel-card { background: #F0F7FF; border-radius: 10px; padding: 12px; border: 1px solid #BFDBFE; }
.ch-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.ch-icon { font-size: 18px; }
.ch-status { font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 600; }
.ch-status.healthy { background: #dcfce7; color: #15803d; }
.ch-status.degraded { background: #fef3c7; color: #b45309; }
.ch-status.down { background: #fee2e2; color: #dc2626; }
.ch-name { font-size: 13px; font-weight: 600; color: #1E3A5F; margin-bottom: 8px; }
.ch-metrics { display: flex; gap: 12px; }
.ch-metric { text-align: center; }
.ch-num { display: block; font-size: 14px; font-weight: 800; color: #1E3A5F; }
.ch-label { font-size: 9px; color: #93B5D0; }

/* 漏斗 */
.funnel { display: flex; flex-direction: column; gap: 6px; }
.funnel-row { display: flex; align-items: center; gap: 8px; }
.funnel-bar {
  height: 32px; border-radius: 6px; display: flex; align-items: center; justify-content: space-between;
  padding: 0 10px; font-size: 12px; font-weight: 600; color: #fff; min-width: 100px;
  transition: width 0.6s ease;
}
.funnel-label { white-space: nowrap; }
.funnel-value { font-weight: 800; }
.funnel-rate { font-size: 11px; color: #93B5D0; white-space: nowrap; }

/* Agent监控 */
.agent-group { margin-bottom: 10px; }
.group-label { font-size: 11px; color: #93B5D0; margin-bottom: 4px; }
.agent-dots { display: flex; flex-wrap: wrap; gap: 4px; }
.agent-dot { width: 16px; height: 16px; border-radius: 4px; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.agent-dot.ok { background: #dcfce7; }
.agent-dot.slow { background: #fef3c7; }
.agent-dot.error { background: #fee2e2; }
.dot-inner { width: 8px; height: 8px; border-radius: 50%; }
.agent-dot.ok .dot-inner { background: #16a34a; }
.agent-dot.slow .dot-inner { background: #d97706; }
.agent-dot.error .dot-inner { background: #dc2626; animation: pulse 1.5s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

/* Agent性能 */
.agent-perf { margin-top: 12px; border-top: 1px solid #DBEAFE; padding-top: 10px; }
.perf-header { font-size: 11px; color: #93B5D0; margin-bottom: 6px; }
.perf-row { display: flex; align-items: center; gap: 8px; padding: 3px 0; font-size: 11px; }
.perf-name { width: 120px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #5B7EA6; }
.perf-bar-bg { flex: 1; height: 6px; background: #DBEAFE; border-radius: 3px; overflow: hidden; }
.perf-bar-fill { height: 100%; border-radius: 3px; background: #3b82f6; transition: width 0.6s; }
.perf-bar-fill.warn { background: #d97706; }
.perf-bar-fill.slow { background: #dc2626; }
.perf-value { width: 50px; text-align: right; font-weight: 700; color: #5B7EA6; }
.perf-value.slow { color: #dc2626; }

/* 教练排行 */
.coach-row { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid #EBF3FB; font-size: 12px; color: #1E3A5F; }
.coach-rank { width: 20px; text-align: center; font-weight: 800; color: #AABDD0; }
.coach-rank.top { color: #d97706; }
.coach-name { flex: 1; font-weight: 600; }
.coach-students { color: #93B5D0; width: 40px; }
.coach-reviewed { color: #16a34a; font-weight: 700; width: 35px; }
.coach-avg { color: #93B5D0; width: 50px; text-align: right; }

/* 安全红线 */
.safety-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }
.safety-item { background: #F0F7FF; border-radius: 8px; padding: 10px; text-align: center; border: 1px solid #BFDBFE; }
.safety-rule { font-size: 11px; font-weight: 800; color: #5B7EA6; }
.safety-count { font-size: 22px; font-weight: 900; color: #AABDD0; margin: 4px 0; }
.safety-count.triggered { color: #dc2626; }
.safety-label { font-size: 10px; color: #93B5D0; }

@media (max-width: 1024px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr) !important; }
  .center-body { flex-direction: column !important; }
}
@media (max-width: 640px) {
  .kpi-grid { grid-template-columns: 1fr !important; }
  .channel-grid { grid-template-columns: 1fr !important; }
  .safety-grid { grid-template-columns: repeat(2, 1fr) !important; }
  .perf-name { width: 80px !important; }
}
</style>
