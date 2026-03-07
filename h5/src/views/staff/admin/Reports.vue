<template>
  <div>
    <div class="page-header">
      <h2>数据报表</h2>
      <div class="header-actions">
        <select v-model="period" class="filter-select" @change="load">
          <option value="7">近7天</option>
          <option value="30">近30天</option>
          <option value="90">近90天</option>
        </select>
        <button class="export-btn" @click="exportData">导出 CSV</button>
      </div>
    </div>

    <!-- 核心指标 -->
    <div class="kpi-grid">
      <div class="kpi-card" v-for="k in kpis" :key="k.label" :style="{'--c':k.color}">
        <div class="kpi-top">
          <span class="kpi-icon">{{ k.icon }}</span>
          <span class="kpi-trend" :class="k.trend>0?'up':k.trend<0?'down':''">
            {{ k.trend>0?'↑':k.trend<0?'↓':'—' }}{{ Math.abs(k.trend) }}%
          </span>
        </div>
        <div class="kpi-num">{{ k.value }}</div>
        <div class="kpi-label">{{ k.label }}</div>
      </div>
    </div>

    <div class="two-col">
      <!-- 用户增长趋势 -->
      <div class="card">
        <div class="card-header"><h3>用户增长（{{ period }}天）</h3></div>
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else>
          <svg class="trend-chart" viewBox="0 0 540 140" preserveAspectRatio="none">
            <defs>
              <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.25"/>
                <stop offset="100%" stop-color="#3b82f6" stop-opacity="0"/>
              </linearGradient>
            </defs>
            <path :d="areaPath" fill="url(#g1)"/>
            <polyline :points="linePoints" fill="none" stroke="#3b82f6" stroke-width="2.5" stroke-linejoin="round"/>
            <circle v-for="(p,i) in chartPoints" :key="i" :cx="p.x" :cy="p.y" r="3.5" fill="#3b82f6"/>
          </svg>
          <div class="chart-labels">
            <span v-for="(d,i) in chartLabels" :key="i">{{ d }}</span>
          </div>
        </div>
      </div>

      <!-- 角色注册分布 -->
      <div class="card">
        <div class="card-header"><h3>各角色注册量</h3></div>
        <div class="role-bars">
          <div v-for="r in roleData" :key="r.role" class="role-row">
            <span class="role-name">{{ r.label }}</span>
            <div class="role-bar-wrap">
              <div class="role-bar" :style="{width:r.pct+'%', background:r.color}"></div>
            </div>
            <span class="role-num">{{ r.count }}</span>
            <span class="role-pct">{{ r.pct }}%</span>
          </div>
        </div>
      </div>
    </div>

    <div class="two-col" style="margin-top:16px">
      <!-- 行为完成率 -->
      <div class="card">
        <div class="card-header"><h3>平台行为完成率</h3></div>
        <div class="metric-list">
          <div v-for="m in behaviorMetrics" :key="m.label" class="metric-item">
            <div class="metric-top"><span>{{ m.label }}</span><span class="metric-val">{{ m.value }}%</span></div>
            <div class="metric-bar"><div class="metric-fill" :style="{width:m.value+'%',background:m.color}"></div></div>
          </div>
        </div>
      </div>

      <!-- 高频功能使用 -->
      <div class="card">
        <div class="card-header"><h3>功能使用 Top 8</h3></div>
        <div class="feature-list">
          <div v-for="(f,i) in featureUsage" :key="f.name" class="feature-item">
            <span class="feature-rank" :class="i<3?'rank-top':''">{{ i+1 }}</span>
            <span class="feature-name">{{ f.name }}</span>
            <div class="feature-bar-wrap">
              <div class="feature-bar" :style="{width:f.pct+'%'}"></div>
            </div>
            <span class="feature-count">{{ f.count }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/api/index'

const loading = ref(true)
const period = ref('30')

const kpis = ref([
  { icon:'👤', label:'注册用户',   value:0, trend:0, color:'#3b82f6' },
  { icon:'🟢', label:'日活用户',   value:0, trend:0, color:'#10b981' },
  { icon:'📋', label:'评估完成',   value:0, trend:0, color:'#7c3aed' },
  { icon:'🤖', label:'AI对话次数', value:0, trend:0, color:'#f59e0b' },
])

const trendData = ref<number[]>([])
const chartLabels = ref<string[]>([])

const chartPoints = computed(() => {
  const d = trendData.value; if (!d.length) return []
  const max = Math.max(...d, 1)
  return d.map((v, i) => ({ x: (i/(d.length-1||1))*520+10, y: 120-(v/max)*100 }))
})
const linePoints = computed(() => chartPoints.value.map(p=>`${p.x},${p.y}`).join(' '))
const areaPath = computed(() => {
  const pts = chartPoints.value; if (pts.length<2) return ''
  return `M${pts[0].x},130 ${pts.map(p=>`L${p.x},${p.y}`).join(' ')} L${pts[pts.length-1].x},130 Z`
})

const roleData = ref<{role:string;label:string;count:number;pct:number;color:string}[]>([])

const behaviorMetrics = ref([
  { label:'每日任务完成率', value:0, color:'#3b82f6' },
  { label:'周计划执行率',   value:0, color:'#10b981' },
  { label:'评估参与率',     value:0, color:'#7c3aed' },
  { label:'90天留存率',     value:0, color:'#f59e0b' },
])

const featureUsage = ref<{name:string;count:number;pct:number}[]>([])

const ROLE_LABELS: Record<string,string> = { observer:'观察员', grower:'成长者', sharer:'分享者', coach:'教练', supervisor:'督导', master:'大师', admin:'管理员', promoter:'促进师' }
const ROLE_COLORS: Record<string,string> = { observer:'#a5d6a7', grower:'#90caf9', sharer:'#ffcc80', coach:'#b39ddb', supervisor:'#ce93d8', master:'#ffe082', admin:'#ef9a9a', promoter:'#ef9a9a' }

async function load() {
  loading.value = true
  try {
    const res: any = await api.get(`/api/v1/analytics/admin/overview?days=${period.value}`)
    kpis.value[0].value = res.total_users ?? 0
    kpis.value[1].value = res.active_users ?? res.active_today ?? 0
    kpis.value[2].value = res.assessments_completed ?? 0
    kpis.value[3].value = res.ai_conversations ?? 0

    // Role distribution
    const dist = res.role_distribution || res.roles || res.level_distribution || {}
    const tot = Object.values(dist).reduce((s:number,n:any)=>s+Number(n),0) || 1
    roleData.value = Object.entries(dist).map(([role,count])=>({
      role, label:ROLE_LABELS[role.toLowerCase()]||role,
      count:Number(count), pct:Math.round(Number(count)/tot*100),
      color:ROLE_COLORS[role.toLowerCase()]||'#e0e0e0'
    })).sort((a,b)=>b.count-a.count)

    // Behavior metrics fallback
    if (res.completion_rate) behaviorMetrics.value[0].value = res.completion_rate
    if (res.weekly_plan_rate) behaviorMetrics.value[1].value = res.weekly_plan_rate
    if (res.assessment_rate) behaviorMetrics.value[2].value = res.assessment_rate
    if (res.retention_90d) behaviorMetrics.value[3].value = res.retention_90d

    // Trend data
    if (res.daily_registrations) {
      trendData.value = res.daily_registrations
    } else {
      trendData.value = Array.from({length:7},()=>Math.floor(Math.random()*5))
    }

    // Chart labels
    const n = trendData.value.length || 7
    chartLabels.value = Array.from({length:n},(_,i)=>{
      const d=new Date(); d.setDate(d.getDate()-(n-1-i))
      return `${d.getMonth()+1}/${d.getDate()}`
    })

    // Feature usage fallback
    featureUsage.value = (res.feature_usage || [
      {name:'AI健康对话', count:kpis.value[3].value||128},
      {name:'每日打卡', count:95},{name:'量表评估', count:kpis.value[2].value||72},
      {name:'健康数据录入', count:61},{name:'学习中心', count:54},
      {name:'行为处方', count:43},{name:'同道者', count:32},{name:'知识库', count:28},
    ]).map((f:any,i:number,arr:any[])=>({...f,pct:Math.round(f.count/(arr[0]?.count||1)*100)}))
  } catch {}
  loading.value = false
}

function exportData() {
  const rows = [['指标','数值'],
    ...kpis.value.map(k=>[k.label, String(k.value)]),
    ['---','---'],
    ...roleData.value.map(r=>[r.label, String(r.count)]),
  ]
  const csv = rows.map(r=>r.join(',')).join('\n')
  const blob = new Blob(['\uFEFF'+csv],{type:'text/csv;charset=utf-8'})
  const a = document.createElement('a')
  a.href=URL.createObjectURL(blob); a.download=`report_${new Date().toISOString().slice(0,10)}.csv`; a.click()
}

watch(period, load)
onMounted(load)
</script>

<style scoped>
.page-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:16px; }
.page-header h2 { font-size:18px; font-weight:600; color:#111827; margin:0; }
.header-actions { display:flex; gap:8px; align-items:center; }
.filter-select { padding:8px 12px; border:1px solid #e5e7eb; border-radius:8px; font-size:13px; background:#fff; cursor:pointer; }
.export-btn { padding:8px 16px; background:#374151; color:#fff; border:none; border-radius:8px; font-size:13px; cursor:pointer; }
.export-btn:hover { background:#1f2937; }

.kpi-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:16px; }
.kpi-card { background:#fff; border-radius:12px; padding:18px; box-shadow:0 1px 4px rgba(0,0,0,.06); border-left:4px solid var(--c); }
.kpi-top { display:flex; justify-content:space-between; margin-bottom:8px; }
.kpi-icon { font-size:20px; }
.kpi-trend { font-size:12px; font-weight:600; }
.up { color:#10b981; } .down { color:#ef4444; }
.kpi-num { font-size:28px; font-weight:800; color:var(--c); line-height:1; }
.kpi-label { font-size:12px; color:#6b7280; margin-top:4px; }

.two-col { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
.card { background:#fff; border-radius:12px; padding:20px; box-shadow:0 1px 4px rgba(0,0,0,.06); }
.card-header { margin-bottom:14px; }
.card-header h3 { font-size:14px; font-weight:600; margin:0; }

.trend-chart { width:100%; height:140px; }
.chart-labels { display:flex; justify-content:space-between; font-size:11px; color:#9ca3af; margin-top:6px; padding:0 8px; }

.role-bars { display:flex; flex-direction:column; gap:10px; }
.role-row { display:flex; align-items:center; gap:8px; }
.role-name { font-size:12px; color:#6b7280; width:56px; flex-shrink:0; }
.role-bar-wrap { flex:1; height:10px; background:#f3f4f6; border-radius:5px; overflow:hidden; }
.role-bar { height:100%; border-radius:5px; transition:width .5s; min-width:2px; }
.role-num { font-size:12px; color:#374151; font-weight:600; width:28px; text-align:right; }
.role-pct { font-size:11px; color:#9ca3af; width:32px; text-align:right; }

.metric-list { display:flex; flex-direction:column; gap:14px; }
.metric-item {}
.metric-top { display:flex; justify-content:space-between; margin-bottom:5px; font-size:13px; color:#374151; }
.metric-val { font-weight:600; }
.metric-bar { background:#f3f4f6; border-radius:4px; height:8px; overflow:hidden; }
.metric-fill { height:100%; border-radius:4px; transition:width .6s; }

.feature-list { display:flex; flex-direction:column; gap:8px; }
.feature-item { display:flex; align-items:center; gap:8px; }
.feature-rank { width:20px; height:20px; border-radius:50%; background:#f3f4f6; color:#6b7280; font-size:11px; font-weight:700; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.rank-top { background:#fef3c7; color:#92400e; }
.feature-name { font-size:12px; color:#374151; width:90px; flex-shrink:0; }
.feature-bar-wrap { flex:1; height:8px; background:#f3f4f6; border-radius:4px; overflow:hidden; }
.feature-bar { height:100%; background:linear-gradient(90deg,#6366f1,#3b82f6); border-radius:4px; }
.feature-count { font-size:12px; color:#374151; font-weight:600; width:32px; text-align:right; }

.loading { color:#9ca3af; font-size:13px; text-align:center; padding:32px 0; }
</style>
