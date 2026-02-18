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
import { ref, computed } from 'vue'

// ── 告警 ──
const activeAlerts = ref([
  { id: 'a1', level: 'critical', message: 'VLM服务响应超时 >5s (影响图片识别)', time: '2分钟前' },
  { id: 'a2', level: 'warning', message: '微信服务号模板消息发送失败率升高至8%', time: '15分钟前' },
])
function alertIcon(level: string) {
  return level === 'critical' ? '🚨' : level === 'warning' ? '⚠️' : 'ℹ️'
}
function dismissAlert(id: string) {
  activeAlerts.value = activeAlerts.value.filter(a => a.id !== id)
}

// ── 核心KPI ──
const coreKPIs = ref([
  { icon: '👥', value: '1,247', label: 'DAU (全渠道)', sub: 'App 680 · 微信 402 · 小程序 165',
    trendDir: 'up', trendPct: 12, status: 'good' },
  { icon: '🔄', value: '34.2%', label: 'Observer→Grower 转化', sub: '本周 vs 上周 +5.1pp',
    trendDir: 'up', trendPct: 5.1, status: 'good' },
  { icon: '📊', value: '78.5%', label: '7日留存率', sub: 'Grower角色',
    trendDir: 'down', trendPct: 2.3, status: 'warn' },
  { icon: '🤖', value: '1.8s', label: 'AI平均响应', sub: 'P95: 3.2s · 超时率: 0.3%',
    trendDir: 'up', trendPct: 0.5, status: 'good' },
])

// ── 渠道 ──
const channels = ref([
  { icon: '📱', name: 'H5 移动端', status: 'healthy', statusLabel: '正常',
    dau: '680', msgToday: '3,420', avgReply: '1.6s' },
  { icon: '💬', name: '微信服务号', status: 'healthy', statusLabel: '正常',
    dau: '402', msgToday: '1,890', avgReply: '2.1s' },
  { icon: '🟢', name: '微信小程序', status: 'healthy', statusLabel: '正常',
    dau: '165', msgToday: '720', avgReply: '1.4s' },
  { icon: '👔', name: '企业微信', status: 'degraded', statusLabel: '告警',
    dau: '23', msgToday: '156', avgReply: '4.2s' },
])

// ── 漏斗 ──
const funnelSteps = ref([
  { label: '访问', count: '5,280', pct: 100, color: '#93c5fd' },
  { label: '注册(Observer)', count: '2,140', pct: 40, color: '#60a5fa', convRate: '40.5' },
  { label: '完成评估', count: '892', pct: 17, color: '#3b82f6', convRate: '41.7' },
  { label: '升级Grower', count: '731', pct: 14, color: '#2563eb', convRate: '81.9' },
  { label: '7日活跃', count: '574', pct: 11, color: '#1d4ed8', convRate: '78.5' },
])

// ── Agent监控 ──
const agentGroups = ref([
  { name: '用户层', agents: Array.from({length: 14}, (_, i) => ({
    id: `u${i}`, name: `用户Agent${i+1}`, status: i === 4 ? 'slow' : 'ok', statusLabel: i === 4 ? '响应慢' : '正常'
  }))},
  { name: '教练层', agents: Array.from({length: 10}, (_, i) => ({
    id: `c${i}`, name: `教练Agent${i+1}`, status: 'ok', statusLabel: '正常'
  }))},
  { name: '系统层', agents: Array.from({length: 4}, (_, i) => ({
    id: `s${i}`, name: `系统Agent${i+1}`, status: 'ok', statusLabel: '正常'
  }))},
  { name: '中医骨科', agents: Array.from({length: 5}, (_, i) => ({
    id: `t${i}`, name: `中医Agent${i+1}`, status: i === 2 ? 'error' : 'ok', statusLabel: i === 2 ? '异常' : '正常'
  }))},
])

const agentHealthAll = computed(() =>
  agentGroups.value.every(g => g.agents.every(a => a.status === 'ok'))
)
const agentIssueCount = computed(() =>
  agentGroups.value.reduce((sum, g) => sum + g.agents.filter(a => a.status !== 'ok').length, 0)
)

const slowestAgents = ref([
  { name: 'vlm_service (食物)', p95: 3800 },
  { name: 'tcm_ortho_expert', p95: 2400 },
  { name: 'emotion_support', p95: 1900 },
  { name: 'rx_composer', p95: 1600 },
  { name: 'nutrition_guide', p95: 1200 },
])
const maxP95 = computed(() => Math.max(...slowestAgents.value.map(a => a.p95)))

// ── 教练 ──
const coachRanking = ref([
  { name: '张教练', students: 45, todayReviewed: 34, avgSeconds: 28 },
  { name: '李教练', students: 38, todayReviewed: 29, avgSeconds: 35 },
  { name: '王教练', students: 42, todayReviewed: 22, avgSeconds: 42 },
  { name: '陈教练', students: 30, todayReviewed: 18, avgSeconds: 55 },
])

// ── 安全 ──
const safetyMetrics = ref([
  { rule: 'S1', label: '医疗边界', count: 3 },
  { rule: 'S2', label: '隐私保护', count: 0 },
  { rule: 'S3', label: '危机检测', count: 1 },
  { rule: 'S4', label: '内容合规', count: 0 },
  { rule: 'S5', label: '数据最小化', count: 0 },
  { rule: 'S6', label: '微信合规', count: 2 },
])
</script>

<style scoped>
.command-center { min-height: 100vh; background: #0f172a; color: #e2e8f0; }

/* ── 告警横幅 ── */
.alert-banner { background: #7f1d1d; padding: 0; overflow: hidden; }
.alert-scroll { display: flex; flex-direction: column; }
.alert-item {
  display: flex; align-items: center; gap: 8px; padding: 8px 16px;
  font-size: 13px; border-bottom: 1px solid rgba(255,255,255,0.1);
}
.alert-item.critical { background: #991b1b; }
.alert-item.warning { background: #78350f; }
.alert-text { flex: 1; }
.alert-time { font-size: 11px; opacity: 0.6; }
.alert-dismiss { background: none; border: none; color: rgba(255,255,255,0.5); cursor: pointer; font-size: 14px; }

/* ── KPI ── */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; padding: 16px 20px; }
.kpi-card {
  background: rgba(255,255,255,0.05); border-radius: 12px; padding: 14px 16px;
  border: 1px solid rgba(255,255,255,0.08);
}
.kpi-card.warn { border-left: 3px solid #f59e0b; }
.kpi-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.kpi-icon { font-size: 18px; }
.kpi-trend { font-size: 12px; font-weight: 700; }
.kpi-trend.up { color: #4ade80; }
.kpi-trend.down { color: #f87171; }
.kpi-value { font-size: 28px; font-weight: 900; color: #fff; }
.kpi-label { font-size: 12px; color: rgba(255,255,255,0.6); margin-top: 2px; }
.kpi-sublabel { font-size: 10px; color: rgba(255,255,255,0.35); margin-top: 2px; }

/* ── 主体 ── */
.center-body { display: flex; gap: 12px; padding: 0 20px 20px; }
.column-left, .column-right { flex: 1; display: flex; flex-direction: column; gap: 12px; }

.panel {
  background: rgba(255,255,255,0.05); border-radius: 12px; padding: 16px;
  border: 1px solid rgba(255,255,255,0.08);
}
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.panel-header h3 { font-size: 14px; font-weight: 700; margin: 0; }
.panel-badge { font-size: 10px; padding: 2px 8px; border-radius: 4px; font-weight: 700; }
.panel-badge.live { background: rgba(74,222,128,0.15); color: #4ade80; }
.panel-badge.ok { background: rgba(74,222,128,0.15); color: #4ade80; }
.panel-badge.warn { background: rgba(248,113,113,0.15); color: #f87171; }

/* 渠道 */
.channel-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.channel-card { background: rgba(0,0,0,0.2); border-radius: 10px; padding: 12px; }
.ch-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.ch-icon { font-size: 18px; }
.ch-status { font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 600; }
.ch-status.healthy { background: rgba(74,222,128,0.15); color: #4ade80; }
.ch-status.degraded { background: rgba(251,191,36,0.15); color: #fbbf24; }
.ch-status.down { background: rgba(248,113,113,0.15); color: #f87171; }
.ch-name { font-size: 13px; font-weight: 600; margin-bottom: 8px; }
.ch-metrics { display: flex; gap: 12px; }
.ch-metric { text-align: center; }
.ch-num { display: block; font-size: 14px; font-weight: 800; color: #fff; }
.ch-label { font-size: 9px; color: rgba(255,255,255,0.4); }

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
.funnel-rate { font-size: 11px; color: rgba(255,255,255,0.5); white-space: nowrap; }

/* Agent监控 */
.agent-group { margin-bottom: 10px; }
.group-label { font-size: 11px; color: rgba(255,255,255,0.4); margin-bottom: 4px; }
.agent-dots { display: flex; flex-wrap: wrap; gap: 4px; }
.agent-dot { width: 16px; height: 16px; border-radius: 4px; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.agent-dot.ok { background: rgba(74,222,128,0.2); }
.agent-dot.slow { background: rgba(251,191,36,0.2); }
.agent-dot.error { background: rgba(248,113,113,0.2); }
.dot-inner { width: 8px; height: 8px; border-radius: 50%; }
.agent-dot.ok .dot-inner { background: #4ade80; }
.agent-dot.slow .dot-inner { background: #fbbf24; }
.agent-dot.error .dot-inner { background: #f87171; animation: pulse 1.5s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

/* Agent性能 */
.agent-perf { margin-top: 12px; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 10px; }
.perf-header { font-size: 11px; color: rgba(255,255,255,0.4); margin-bottom: 6px; }
.perf-row { display: flex; align-items: center; gap: 8px; padding: 3px 0; font-size: 11px; }
.perf-name { width: 120px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: rgba(255,255,255,0.6); }
.perf-bar-bg { flex: 1; height: 6px; background: rgba(255,255,255,0.06); border-radius: 3px; overflow: hidden; }
.perf-bar-fill { height: 100%; border-radius: 3px; background: #3b82f6; transition: width 0.6s; }
.perf-bar-fill.warn { background: #fbbf24; }
.perf-bar-fill.slow { background: #f87171; }
.perf-value { width: 50px; text-align: right; font-weight: 700; color: rgba(255,255,255,0.6); }
.perf-value.slow { color: #f87171; }

/* 教练排行 */
.coach-row { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.04); font-size: 12px; }
.coach-rank { width: 20px; text-align: center; font-weight: 800; color: rgba(255,255,255,0.3); }
.coach-rank.top { color: #fbbf24; }
.coach-name { flex: 1; font-weight: 600; }
.coach-students { color: rgba(255,255,255,0.4); width: 40px; }
.coach-reviewed { color: #4ade80; font-weight: 700; width: 35px; }
.coach-avg { color: rgba(255,255,255,0.5); width: 50px; text-align: right; }

/* 安全红线 */
.safety-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }
.safety-item { background: rgba(0,0,0,0.2); border-radius: 8px; padding: 10px; text-align: center; }
.safety-rule { font-size: 11px; font-weight: 800; color: rgba(255,255,255,0.4); }
.safety-count { font-size: 22px; font-weight: 900; color: rgba(255,255,255,0.3); margin: 4px 0; }
.safety-count.triggered { color: #f87171; }
.safety-label { font-size: 10px; color: rgba(255,255,255,0.3); }
</style>
