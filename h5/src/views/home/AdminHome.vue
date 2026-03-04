<template>
  <!--
    Admin(L99) 管理员首页
    核心: 系统健康 + 用户管理 + 快捷操作 + 近期活动
  -->
  <PageShell :show-nav-bar="false" :show-tab-bar="true" no-padding>
    <UserHero :streak-days="0" />

    <div style="padding: 0 20px;">
      <GlobalSearch />
    </div>

    <!-- ═══ 系统概览 ═══ -->
    <div class="overview-cards">
      <div class="ov-card">
        <span class="ov-num">{{ stats.totalUsers }}</span>
        <span class="ov-label">总用户</span>
      </div>
      <div class="ov-card">
        <span class="ov-num">{{ stats.activeToday }}</span>
        <span class="ov-label">今日活跃</span>
      </div>
      <div class="ov-card">
        <span class="ov-num">{{ stats.newToday }}</span>
        <span class="ov-label">今日新增</span>
      </div>
      <div class="ov-card" :class="{ 'ov-card--alert': stats.alertCount > 0 }">
        <span class="ov-num">{{ stats.alertCount }}</span>
        <span class="ov-label">告警</span>
      </div>
    </div>

    <!-- ═══ 用户分布 ═══ -->
    <div class="section">
      <h2 class="section-title">🔧 用户角色分布</h2>
      <div class="role-dist">
        <div v-for="r in roleDistribution" :key="r.role" class="role-bar-row">
          <span class="rb-label">{{ r.label }}</span>
          <div class="rb-track">
            <div class="rb-fill" :style="{ width: r.pct + '%', background: r.color }"></div>
          </div>
          <span class="rb-count">{{ r.count }}</span>
        </div>
      </div>
    </div>

    <!-- ═══ 系统健康 ═══ -->
    <div class="section">
      <h2 class="section-title">🏥 系统健康</h2>
      <div class="health-grid">
        <div v-for="h in healthItems" :key="h.label" class="health-item" :class="'h--' + h.status">
          <span class="h-dot"></span>
          <span class="h-label">{{ h.label }}</span>
          <span class="h-status">{{ h.statusText }}</span>
        </div>
      </div>
    </div>

    <!-- ═══ 快捷操作 ═══ -->
    <div class="quick-actions">
      <div class="qa-item" @click="$router.push('/chat')">
        <div class="qa-icon" style="background:#e3f2fd;color:#1565C0">💬</div>
        <span class="qa-label">AI 对话</span>
      </div>
      <div class="qa-item" @click="$router.push('/dashboard')">
        <div class="qa-icon" style="background:#e8f5e9;color:#2e7d32">📊</div>
        <span class="qa-label">健康看板</span>
      </div>
      <div class="qa-item" @click="$router.push('/learn')">
        <div class="qa-icon" style="background:#fff3e0;color:#e65100">📚</div>
        <span class="qa-label">学习中心</span>
      </div>
      <div class="qa-item" @click="$router.push('/expert-hub')">
        <div class="qa-icon" style="background:#fce4ec;color:#c62828">🏛️</div>
        <span class="qa-label">专家工作室</span>
      </div>
    </div>

    <!-- ═══ 管理后台入口 ═══ -->
    <div class="admin-portal-card" @click="openAdminPortal">
      <div class="ap-icon">🖥️</div>
      <div class="ap-text">
        <div class="ap-title">管理后台</div>
        <div class="ap-desc">完整的后台管理面板 (Admin Portal)</div>
      </div>
      <van-icon name="arrow" color="#999" />
    </div>
  </PageShell>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/api/index'
import PageShell from '@/components/common/PageShell.vue'
import UserHero from '@/components/common/UserHero.vue'
import GlobalSearch from '@/components/common/GlobalSearch.vue'

const stats = ref({
  totalUsers: 0,
  activeToday: 0,
  newToday: 0,
  alertCount: 0,
})

interface RoleDist { role: string; label: string; count: number; pct: number; color: string }
const roleDistribution = ref<RoleDist[]>([])

interface HealthItem { label: string; status: string; statusText: string }
const healthItems = ref<HealthItem[]>([
  { label: 'API 服务', status: 'ok', statusText: '正常' },
  { label: '数据库', status: 'ok', statusText: '正常' },
  { label: 'Redis', status: 'ok', statusText: '正常' },
  { label: 'AI 服务', status: 'ok', statusText: '正常' },
])

const ROLE_COLORS: Record<string, string> = {
  observer: '#a5d6a7', grower: '#90caf9', sharer: '#ffcc80',
  coach: '#b39ddb', promoter: '#ef9a9a', supervisor: '#ce93d8',
  master: '#ffe082', admin: '#ef9a9a',
}
const ROLE_LABELS: Record<string, string> = {
  observer: '观察员', grower: '成长者', sharer: '分享者',
  coach: '行为健康教练', promoter: '行为健康促进师', supervisor: '行为健康促进师',
  master: '行为健康大师', admin: '管理员',
}

function openAdminPortal() {
  // Admin portal runs on :5174
  const url = window.location.protocol + '//' + window.location.hostname + ':5174'
  window.open(url, '_blank')
}

onMounted(async () => {
  const [statsRes, healthRes] = await Promise.allSettled([
    api.get('/api/v1/analytics/admin/overview'),
    api.get('/api/v1/system/health'),
  ])

  if (statsRes.status === 'fulfilled') {
    const d = statsRes.value as any
    stats.value = {
      totalUsers: d.total_users ?? 0,
      activeToday: d.active_users ?? d.active_today ?? 0,
      newToday: d.new_today ?? 0,
      alertCount: d.high_risk_count ?? d.alert_count ?? 0,
    }

    // 角色分布：后端返回 level_distribution（中文key）或 role_distribution
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

  if (healthRes.status === 'fulfilled') {
    const d = healthRes.value as any
    // 后端返回 {status, checks:{database,redis,route_modules}} 格式
    if (d.checks) {
      const statusMap: Record<string, string> = { healthy: 'ok', unhealthy: 'error', degraded: 'warn' }
      healthItems.value = Object.entries(d.checks).map(([key, val]: [string, any]) => ({
        label: ({ database: '数据库', redis: 'Redis', route_modules: '路由模块' } as any)[key] || key,
        status: statusMap[String(val)] || (val === 'healthy' ? 'ok' : 'warn'),
        statusText: val === 'healthy' ? '正常' : val === 'unhealthy' ? '异常' : '警告',
      }))
    } else if (d.services) {
      healthItems.value = (d.services || []).map((s: any) => ({
        label: s.name || s.label || '',
        status: s.status || 'ok',
        statusText: s.status === 'ok' ? '正常' : s.status === 'warn' ? '警告' : '异常',
      }))
    }
  }
})
</script>

<style scoped>
/* ── 概览 ── */
.overview-cards {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 10px; padding: 16px 20px;
}
.ov-card {
  background: #fff; border-radius: 14px; padding: 14px 8px;
  text-align: center; box-shadow: 0 1px 6px rgba(0,0,0,0.04);
}
.ov-card--alert .ov-num { color: #e53935; }
.ov-num { font-size: 24px; font-weight: 800; color: #111827; display: block; line-height: 1.2; }
.ov-label { font-size: 11px; color: #9ca3af; }

/* ── section ── */
.section { padding: 0 20px 16px; }
.section-title { font-size: 16px; font-weight: 700; color: #111827; margin: 0 0 12px; }

/* ── 角色分布 ── */
.role-dist { display: flex; flex-direction: column; gap: 8px; }
.role-bar-row { display: flex; align-items: center; gap: 8px; }
.rb-label { font-size: 12px; color: #6b7280; width: 48px; text-align: right; flex-shrink: 0; }
.rb-track { flex: 1; height: 8px; background: #f3f4f6; border-radius: 4px; overflow: hidden; }
.rb-fill { height: 100%; border-radius: 4px; transition: width 0.6s ease; min-width: 2px; }
.rb-count { font-size: 12px; color: #374151; font-weight: 600; width: 32px; flex-shrink: 0; }

/* ── 系统健康 ── */
.health-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.health-item {
  display: flex; align-items: center; gap: 8px;
  background: #fff; border-radius: 10px; padding: 10px 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.h-dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}
.h--ok .h-dot { background: #10b981; }
.h--warn .h-dot { background: #f59e0b; }
.h--error .h-dot { background: #ef4444; }
.h-label { flex: 1; font-size: 13px; color: #374151; }
.h-status { font-size: 12px; font-weight: 600; }
.h--ok .h-status { color: #10b981; }
.h--warn .h-status { color: #f59e0b; }
.h--error .h-status { color: #ef4444; }

/* ── 快捷操作 ── */
.quick-actions {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 12px; padding: 0 20px 16px;
}
.qa-item { display: flex; flex-direction: column; align-items: center; gap: 6px; cursor: pointer; }
.qa-item:active { opacity: 0.7; }
.qa-icon {
  width: 48px; height: 48px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px;
}
.qa-label { font-size: 12px; color: #374151; font-weight: 500; }

/* ── 管理后台入口 ── */
.admin-portal-card {
  display: flex; align-items: center; gap: 12px;
  margin: 0 20px 20px; padding: 16px;
  background: linear-gradient(135deg, #263238, #37474f);
  border-radius: 14px; cursor: pointer;
  transition: transform 0.15s;
}
.admin-portal-card:active { transform: scale(0.98); }
.ap-icon { font-size: 28px; flex-shrink: 0; }
.ap-text { flex: 1; }
.ap-title { font-size: 15px; font-weight: 700; color: #fff; }
.ap-desc { font-size: 12px; color: rgba(255,255,255,0.65); margin-top: 2px; }
</style>
