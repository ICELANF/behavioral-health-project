<template>
  <div>
    <div class="kpi-grid">
      <div class="kpi-card" style="--accent:#1d4ed8">
        <div class="kpi-icon">👤</div>
        <div class="kpi-body">
          <div class="kpi-num">{{ stats.totalUsers }}</div>
          <div class="kpi-label">总用户</div>
        </div>
      </div>
      <div class="kpi-card" style="--accent:#059669">
        <div class="kpi-icon">🟢</div>
        <div class="kpi-body">
          <div class="kpi-num">{{ stats.activeToday }}</div>
          <div class="kpi-label">今日活跃</div>
        </div>
      </div>
      <div class="kpi-card" style="--accent:#7c3aed">
        <div class="kpi-icon">➕</div>
        <div class="kpi-body">
          <div class="kpi-num">{{ stats.newToday }}</div>
          <div class="kpi-label">今日新增</div>
        </div>
      </div>
      <div class="kpi-card" :style="{ '--accent': stats.alertCount > 0 ? '#dc2626' : '#6b7280' }">
        <div class="kpi-icon">⚠️</div>
        <div class="kpi-body">
          <div class="kpi-num">{{ stats.alertCount }}</div>
          <div class="kpi-label">告警</div>
        </div>
      </div>
    </div>

    <div class="two-col">
      <!-- 系统健康 -->
      <div class="card">
        <div class="card-header"><h2>系统健康</h2></div>
        <div class="health-list">
          <div v-for="h in healthItems" :key="h.label" class="health-item" :class="'h--' + h.status">
            <span class="h-dot"></span>
            <span class="h-label">{{ h.label }}</span>
            <span class="h-status">{{ h.statusText }}</span>
          </div>
        </div>
      </div>

      <!-- 角色分布 -->
      <div class="card">
        <div class="card-header"><h2>角色分布</h2></div>
        <div class="role-dist">
          <div v-for="r in roleDistribution" :key="r.role" class="role-row">
            <span class="role-name">{{ r.label }}</span>
            <div class="role-bar-wrap">
              <div class="role-bar" :style="{ width: r.pct + '%', background: r.color }"></div>
            </div>
            <span class="role-count">{{ r.count }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 监控端点 -->
    <div class="card" style="margin-top: 16px;">
      <div class="card-header">
        <h2>系统监控</h2>
        <button class="refresh-btn" @click="loadMonitoring">刷新</button>
      </div>
      <div class="monitor-grid">
        <div class="monitor-item">
          <div class="mi-label">API路由总数</div>
          <div class="mi-val">{{ monitoring.routes }}</div>
        </div>
        <div class="monitor-item">
          <div class="mi-label">前端合约覆盖</div>
          <div class="mi-val">{{ monitoring.contract }}</div>
        </div>
        <div class="monitor-item">
          <div class="mi-label">AI Agents</div>
          <div class="mi-val">{{ monitoring.agents }}</div>
        </div>
        <div class="monitor-item">
          <div class="mi-label">向量DB条目</div>
          <div class="mi-val">{{ monitoring.vectorDb }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/api/index'

const stats = ref({ totalUsers: 0, activeToday: 0, newToday: 0, alertCount: 0 })
const healthItems = ref([
  { label: 'API 服务', status: 'ok', statusText: '正常' },
  { label: '数据库', status: 'ok', statusText: '正常' },
  { label: 'Redis', status: 'ok', statusText: '正常' },
  { label: '路由模块', status: 'ok', statusText: '正常' },
])
const roleDistribution = ref<{ role: string; label: string; count: number; pct: number; color: string }[]>([])
const monitoring = ref({ routes: '—', contract: '—', agents: '—', vectorDb: '—' })

const ROLE_COLORS: Record<string, string> = {
  observer: '#a5d6a7', grower: '#90caf9', sharer: '#ffcc80',
  coach: '#b39ddb', promoter: '#ef9a9a', supervisor: '#ce93d8',
  master: '#ffe082', admin: '#ef9a9a',
}
const ROLE_LABELS: Record<string, string> = {
  observer: '观察员', grower: '成长者', sharer: '分享者',
  coach: '教练', promoter: '促进师', supervisor: '督导',
  master: '大师', admin: '管理员',
}

async function loadMonitoring() {
  const [routesRes, healthRes, agentsRes] = await Promise.allSettled([
    api.get('/api/v1/system/routes'),
    api.get('/api/v1/system/health'),
    api.get('/api/v1/system/agents/health'),
  ])
  if (routesRes.status === 'fulfilled') {
    const d = routesRes.value as any
    monitoring.value.routes = d.total ?? (Array.isArray(d) ? d.length : '—')
  }
  if (healthRes.status === 'fulfilled') {
    const d = healthRes.value as any
    if (d.checks) {
      const statusMap: Record<string, string> = { healthy: 'ok', unhealthy: 'error', degraded: 'warn' }
      healthItems.value = Object.entries(d.checks).map(([key, val]: [string, any]) => ({
        label: ({ database: '数据库', redis: 'Redis', route_modules: '路由模块' } as any)[key] || key,
        status: statusMap[String(val)] || 'ok',
        statusText: val === 'healthy' ? '正常' : val === 'unhealthy' ? '异常' : '警告',
      }))
    }
  }
  if (agentsRes.status === 'fulfilled') {
    const d = agentsRes.value as any
    monitoring.value.agents = d.total_agents ?? d.count ?? '—'
  }
}

onMounted(async () => {
  const [statsRes] = await Promise.allSettled([
    api.get('/api/v1/analytics/admin/overview'),
  ])
  if (statsRes.status === 'fulfilled') {
    const d = statsRes.value as any
    stats.value = {
      totalUsers: d.total_users ?? 0,
      activeToday: d.active_users ?? d.active_today ?? 0,
      newToday: d.new_today ?? 0,
      alertCount: d.high_risk_count ?? d.alert_count ?? 0,
    }
    const dist = d.role_distribution || d.roles || d.level_distribution || {}
    const total = Object.values(dist).reduce((s: number, n: any) => s + (Number(n) || 0), 0) || 1
    roleDistribution.value = Object.entries(dist).map(([role, count]) => ({
      role,
      label: ROLE_LABELS[role.toLowerCase()] || role,
      count: Number(count) || 0,
      pct: Math.round(((Number(count) || 0) / total) * 100),
      color: ROLE_COLORS[role.toLowerCase()] || '#e0e0e0',
    }))
  }
  await loadMonitoring()
})
</script>

<style scoped>
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.kpi-card {
  background: #fff; border-radius: 12px; padding: 20px;
  display: flex; align-items: center; gap: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06); border-left: 4px solid var(--accent);
}
.kpi-icon { font-size: 28px; }
.kpi-num { font-size: 28px; font-weight: 800; color: var(--accent); line-height: 1; }
.kpi-label { font-size: 12px; color: #6b7280; margin-top: 4px; }

.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.card { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.card-header h2 { font-size: 15px; font-weight: 600; margin: 0; }
.refresh-btn { padding: 6px 12px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fff; font-size: 12px; cursor: pointer; }

.health-list { display: flex; flex-direction: column; gap: 8px; }
.health-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; background: #f9fafb; border-radius: 8px; }
.h-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.h--ok .h-dot { background: #10b981; }
.h--warn .h-dot { background: #f59e0b; }
.h--error .h-dot { background: #ef4444; }
.h-label { flex: 1; font-size: 13px; color: #374151; }
.h-status { font-size: 12px; font-weight: 600; }
.h--ok .h-status { color: #10b981; }
.h--warn .h-status { color: #f59e0b; }
.h--error .h-status { color: #ef4444; }

.role-dist { display: flex; flex-direction: column; gap: 10px; }
.role-row { display: flex; align-items: center; gap: 8px; }
.role-name { font-size: 12px; color: #6b7280; width: 60px; flex-shrink: 0; }
.role-bar-wrap { flex: 1; height: 8px; background: #f3f4f6; border-radius: 4px; overflow: hidden; }
.role-bar { height: 100%; border-radius: 4px; min-width: 2px; transition: width 0.6s; }
.role-count { font-size: 12px; color: #374151; font-weight: 600; width: 32px; text-align: right; }

.monitor-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.monitor-item { background: #f9fafb; border-radius: 10px; padding: 16px; text-align: center; }
.mi-label { font-size: 12px; color: #6b7280; margin-bottom: 8px; }
.mi-val { font-size: 24px; font-weight: 800; color: #1d4ed8; }
</style>
