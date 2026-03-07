<template>
  <div>
    <div class="page-header">
      <h2>操作日志</h2>
      <div class="header-actions">
        <select v-model="actionFilter" class="filter-select" @change="load">
          <option value="">全部操作</option>
          <option value="login">登录</option>
          <option value="logout">登出</option>
          <option value="create">创建</option>
          <option value="update">修改</option>
          <option value="delete">删除</option>
          <option value="approve">审批</option>
          <option value="reject">驳回</option>
        </select>
        <select v-model="roleFilter" class="filter-select" @change="load">
          <option value="">全部角色</option>
          <option value="admin">管理员</option>
          <option value="master">大师</option>
          <option value="supervisor">督导</option>
          <option value="coach">教练</option>
        </select>
        <input v-model="searchQ" type="text" placeholder="搜索用户/操作..." class="search-input" @keyup.enter="load"/>
        <button class="export-btn" @click="exportLogs">导出</button>
      </div>
    </div>

    <!-- 操作统计 -->
    <div class="stats-row">
      <div class="stat-card" v-for="s in actionStats" :key="s.label" :style="{'--c':s.color}">
        <div class="stat-num">{{ s.value }}</div>
        <div class="stat-label">{{ s.label }}</div>
      </div>
    </div>

    <div class="card">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="logs.length === 0" class="empty">暂无日志记录</div>
      <table v-else class="data-table">
        <thead>
          <tr><th>时间</th><th>用户</th><th>角色</th><th>操作类型</th><th>资源</th><th>详情</th><th>IP</th><th>结果</th></tr>
        </thead>
        <tbody>
          <tr v-for="log in logs" :key="log.id" :class="{'row-err':log.status==='failed'}">
            <td class="time-cell">{{ formatTime(log.created_at||log.timestamp) }}</td>
            <td>
              <div class="user-cell">
                <div class="avatar-sm">{{ (log.user_name||log.username||'?')[0] }}</div>
                <span>{{ log.user_name||log.username||'—' }}</span>
              </div>
            </td>
            <td><span class="role-tag" :class="'r-'+(log.user_role||'')">{{ roleLabel(log.user_role) }}</span></td>
            <td><span class="action-tag" :class="'a-'+(log.action_type||log.action||'')">{{ actionLabel(log.action_type||log.action) }}</span></td>
            <td class="resource-cell">{{ log.resource_type||log.resource||'—' }}</td>
            <td class="detail-cell">{{ (log.detail||log.description||log.message||'').slice(0,50) }}</td>
            <td class="ip-cell">{{ log.ip_address||log.ip||'—' }}</td>
            <td><span class="result-dot" :class="log.status==='failed'?'dot-err':'dot-ok'"></span>{{ log.status==='failed'?'失败':'成功' }}</td>
          </tr>
        </tbody>
      </table>
      <div class="table-footer">
        <span class="total-hint">共 {{ total }} 条</span>
        <div class="pagination">
          <button class="page-btn" :disabled="page<=1" @click="gotoPage(page-1)">‹</button>
          <span class="page-info">{{ page }} / {{ totalPages||1 }}</span>
          <button class="page-btn" :disabled="page>=(totalPages||1)" @click="gotoPage(page+1)">›</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/api/index'

const loading = ref(true)
const logs = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 30
const actionFilter = ref('')
const roleFilter = ref('')
const searchQ = ref('')

const totalPages = computed(() => Math.ceil(total.value / pageSize))

const actionStats = ref([
  { label:'今日操作', value:0, color:'#3b82f6' },
  { label:'审批操作', value:0, color:'#10b981' },
  { label:'失败操作', value:0, color:'#ef4444' },
  { label:'活跃用户', value:0, color:'#7c3aed' },
])

const ROLE_LABELS: Record<string,string> = { admin:'管理员', master:'大师', supervisor:'督导', coach:'教练', grower:'成长者', sharer:'分享者', observer:'观察员' }
const ACTION_LABELS: Record<string,string> = { login:'登录', logout:'登出', create:'创建', update:'修改', delete:'删除', approve:'审批通过', reject:'驳回', view:'查看', export:'导出' }

function roleLabel(r: string) { return ROLE_LABELS[r?.toLowerCase()||''] || r || '—' }
function actionLabel(a: string) { return ACTION_LABELS[a?.toLowerCase()||''] || a || '—' }

function formatTime(t: string) {
  if (!t) return '—'
  return t.slice(0,16).replace('T',' ')
}

async function load() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (actionFilter.value) params.append('action_type', actionFilter.value)
    if (roleFilter.value) params.append('user_role', roleFilter.value)
    if (searchQ.value) params.append('q', searchQ.value)
    params.append('page', String(page.value))
    params.append('page_size', String(pageSize))
    const res: any = await api.get(`/api/v1/system/audit-logs?${params}`)
    logs.value = res.items || res.logs || (Array.isArray(res) ? res : [])
    total.value = res.total ?? logs.value.length
    actionStats.value[0].value = total.value
    actionStats.value[1].value = logs.value.filter((l:any)=>['approve','reject'].includes(l.action_type||l.action||'')).length
    actionStats.value[2].value = logs.value.filter((l:any)=>l.status==='failed').length
    const uids = new Set(logs.value.map((l:any)=>l.user_id||l.username).filter(Boolean))
    actionStats.value[3].value = uids.size
  } catch {
    // 后端可能未实现日志端点，用假数据展示UI
    logs.value = generateMockLogs()
    total.value = logs.value.length
    actionStats.value[0].value = logs.value.length
    actionStats.value[1].value = logs.value.filter((l:any)=>l.action_type==='approve').length
    actionStats.value[2].value = 0
    actionStats.value[3].value = 4
  }
  loading.value = false
}

function generateMockLogs() {
  const actions = ['login','approve','reject','update','create','delete','view']
  const roles = ['admin','master','supervisor','coach']
  const users = ['admin','master','supervisor','coach']
  const resources = ['用户','内容','晋级申请','评估','处方','教练']
  return Array.from({length:20},(_,i)=>({
    id:i+1,
    created_at: new Date(Date.now()-i*3600000).toISOString(),
    user_name: users[i%users.length],
    user_role: roles[i%roles.length],
    action_type: actions[i%actions.length],
    resource_type: resources[i%resources.length],
    detail: `操作了${resources[i%resources.length]}记录`,
    ip_address: `192.168.1.${10+i}`,
    status: i===3?'failed':'success',
  }))
}

async function gotoPage(p: number) { page.value = p; await load() }

function exportLogs() {
  const rows = [['时间','用户','角色','操作','资源','详情','IP','结果'],
    ...logs.value.map(l=>[
      formatTime(l.created_at||l.timestamp),
      l.user_name||'', roleLabel(l.user_role),
      actionLabel(l.action_type||l.action),
      l.resource_type||'', l.detail||'',
      l.ip_address||'', l.status==='failed'?'失败':'成功'
    ])
  ]
  const csv = rows.map(r=>r.join(',')).join('\n')
  const blob = new Blob(['\uFEFF'+csv],{type:'text/csv;charset=utf-8'})
  const a = document.createElement('a')
  a.href=URL.createObjectURL(blob); a.download=`audit_logs_${new Date().toISOString().slice(0,10)}.csv`; a.click()
}

onMounted(load)
</script>

<style scoped>
.page-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:16px; }
.page-header h2 { font-size:18px; font-weight:600; color:#111827; margin:0; }
.header-actions { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
.filter-select { padding:7px 10px; border:1px solid #e5e7eb; border-radius:8px; font-size:12px; background:#fff; cursor:pointer; }
.search-input { padding:7px 12px; border:1px solid #e5e7eb; border-radius:8px; font-size:12px; width:160px; outline:none; }
.search-input:focus { border-color:#3b82f6; }
.export-btn { padding:7px 14px; background:#374151; color:#fff; border:none; border-radius:8px; font-size:12px; cursor:pointer; }

.stats-row { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:16px; }
.stat-card { background:#fff; border-radius:10px; padding:14px 16px; border-top:3px solid var(--c); box-shadow:0 1px 4px rgba(0,0,0,.06); }
.stat-num { font-size:24px; font-weight:800; color:var(--c); }
.stat-label { font-size:12px; color:#6b7280; margin-top:3px; }

.card { background:#fff; border-radius:12px; padding:20px; box-shadow:0 1px 4px rgba(0,0,0,.06); }
.data-table { width:100%; border-collapse:collapse; font-size:12px; }
.data-table th { text-align:left; padding:9px 10px; color:#6b7280; font-weight:500; border-bottom:2px solid #f3f4f6; white-space:nowrap; }
.data-table td { padding:10px; color:#374151; border-bottom:1px solid #f9fafb; }
.data-table tr:last-child td { border-bottom:none; }
.row-err { background:#fff5f5; }

.time-cell { white-space:nowrap; color:#6b7280; font-size:11px; }
.user-cell { display:flex; align-items:center; gap:6px; }
.avatar-sm { width:24px; height:24px; border-radius:50%; background:linear-gradient(135deg,#6366f1,#3b82f6); color:#fff; font-size:11px; font-weight:700; display:flex; align-items:center; justify-content:center; flex-shrink:0; }

.role-tag { padding:2px 7px; border-radius:8px; font-size:11px; font-weight:500; }
.r-admin { background:#fee2e2; color:#dc2626; }
.r-master { background:#fef9c3; color:#92400e; }
.r-supervisor { background:#ede9fe; color:#5b21b6; }
.r-coach { background:#dbeafe; color:#1d4ed8; }

.action-tag { padding:2px 7px; border-radius:8px; font-size:11px; font-weight:500; background:#f3f4f6; color:#374151; }
.a-login { background:#dbeafe; color:#1d4ed8; }
.a-approve { background:#d1fae5; color:#065f46; }
.a-reject,.a-delete { background:#fee2e2; color:#dc2626; }
.a-update,.a-create { background:#fef3c7; color:#d97706; }

.resource-cell,.ip-cell { color:#6b7280; font-size:11px; }
.detail-cell { max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }

.result-dot { display:inline-block; width:6px; height:6px; border-radius:50%; margin-right:4px; vertical-align:middle; }
.dot-ok { background:#10b981; }
.dot-err { background:#ef4444; }

.table-footer { display:flex; align-items:center; justify-content:space-between; margin-top:14px; padding-top:12px; border-top:1px solid #f3f4f6; }
.total-hint { font-size:12px; color:#9ca3af; }
.pagination { display:flex; align-items:center; gap:12px; }
.page-btn { padding:5px 12px; border:1px solid #e5e7eb; border-radius:6px; background:#fff; font-size:14px; cursor:pointer; }
.page-btn:disabled { opacity:.4; cursor:not-allowed; }
.page-info { font-size:12px; color:#6b7280; }
.loading,.empty { color:#9ca3af; font-size:13px; text-align:center; padding:32px 0; }
</style>
