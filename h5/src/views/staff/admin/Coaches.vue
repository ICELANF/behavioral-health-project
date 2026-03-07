<template>
  <div>
    <div class="page-header">
      <h2>教练审核与管理</h2>
      <div class="header-actions">
        <select v-model="statusFilter" class="filter-select" @change="load">
          <option value="">全部状态</option>
          <option value="active">在职</option>
          <option value="pending">待审核</option>
          <option value="suspended">已停职</option>
        </select>
        <input v-model="searchQ" type="text" placeholder="搜索教练..." class="search-input" @keyup.enter="load" />
      </div>
    </div>

    <div class="stats-row">
      <div class="stat-card" v-for="s in stats" :key="s.label" :style="{'--c': s.color}">
        <div class="stat-num">{{ s.value }}</div>
        <div class="stat-label">{{ s.label }}</div>
      </div>
    </div>

    <div class="card">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="coaches.length === 0" class="empty">暂无数据</div>
      <table v-else class="data-table">
        <thead>
          <tr><th>教练</th><th>等级</th><th>学员数</th><th>完成率</th><th>督导</th><th>状态</th><th>加入时间</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="c in coaches" :key="c.id">
            <td>
              <div class="user-cell">
                <div class="avatar">{{ (c.name||c.full_name||'?')[0] }}</div>
                <div>
                  <div class="u-name">{{ c.name||c.full_name }}</div>
                  <div class="u-sub">{{ c.email||c.username||'' }}</div>
                </div>
              </div>
            </td>
            <td><span class="level-tag">{{ c.stage||c.level||'L3' }}</span></td>
            <td>{{ c.student_count??'—' }}</td>
            <td>
              <div class="bar-wrap"><div class="bar-fill" :style="{width:(c.completion_rate||0)+'%'}"></div></div>
              <span class="bar-pct">{{ c.completion_rate||0 }}%</span>
            </td>
            <td>{{ c.supervisor_name||'—' }}</td>
            <td><span class="status-tag" :class="'st-'+(c.status||'active')">{{ statusLabel(c.status) }}</span></td>
            <td>{{ c.created_at?.slice(0,10)||'—' }}</td>
            <td class="action-cell">
              <button v-if="c.status==='pending'" class="action-btn a-approve" @click="approve(c)">审批通过</button>
              <button v-if="c.status==='active'" class="action-btn a-suspend" @click="suspend(c)">停职</button>
              <button v-if="c.status==='suspended'" class="action-btn a-restore" @click="restore(c)">恢复</button>
              <button class="action-btn a-view" @click="viewDetail(c)">详情</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 详情抽屉 -->
    <div v-if="detail" class="drawer-overlay" @click.self="detail=null">
      <div class="drawer">
        <div class="drawer-header">
          <h3>{{ detail.name||detail.full_name }} 的档案</h3>
          <button class="close-btn" @click="detail=null">✕</button>
        </div>
        <div class="drawer-body">
          <div class="info-grid">
            <div class="info-item"><span class="ik">ID</span><span class="iv">{{ detail.id }}</span></div>
            <div class="info-item"><span class="ik">等级</span><span class="iv">{{ detail.stage||detail.level||'L3' }}</span></div>
            <div class="info-item"><span class="ik">学员数</span><span class="iv">{{ detail.student_count??'—' }}</span></div>
            <div class="info-item"><span class="ik">完成率</span><span class="iv">{{ detail.completion_rate||0 }}%</span></div>
            <div class="info-item"><span class="ik">高危学员</span><span class="iv">{{ detail.high_risk_count||0 }}</span></div>
            <div class="info-item"><span class="ik">督导</span><span class="iv">{{ detail.supervisor_name||'—' }}</span></div>
            <div class="info-item"><span class="ik">加入时间</span><span class="iv">{{ detail.created_at?.slice(0,10)||'—' }}</span></div>
            <div class="info-item"><span class="ik">状态</span><span class="iv">{{ statusLabel(detail.status) }}</span></div>
          </div>
          <div class="drawer-actions">
            <button v-if="detail.status==='pending'" class="act-btn act-primary" @click="approve(detail);detail=null">审批通过</button>
            <button v-if="detail.status==='active'" class="act-btn act-warn" @click="suspend(detail);detail=null">停职</button>
            <button class="act-btn act-secondary" @click="detail=null">关闭</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/api/index'

const loading = ref(true)
const coaches = ref<any[]>([])
const statusFilter = ref('')
const searchQ = ref('')
const detail = ref<any>(null)

const stats = ref([
  { label: '教练总数', value: 0, color: '#3b82f6' },
  { label: '待审核',   value: 0, color: '#f59e0b' },
  { label: '在职',     value: 0, color: '#10b981' },
  { label: '停职',     value: 0, color: '#ef4444' },
])

function statusLabel(s: string) {
  const m: Record<string,string> = { active:'在职', pending:'待审核', suspended:'已停职', inactive:'未激活' }
  return m[s||'active'] || s || '在职'
}

async function load() {
  loading.value = true
  try {
    const params: string[] = []
    if (statusFilter.value) params.push(`status=${statusFilter.value}`)
    if (searchQ.value) params.push(`q=${encodeURIComponent(searchQ.value)}`)
    const res: any = await api.get(`/api/v1/supervisor/coaches${params.length?'?'+params.join('&'):''}`)
    coaches.value = res.items || res.coaches || (Array.isArray(res) ? res : [])
    stats.value[0].value = coaches.value.length
    stats.value[1].value = coaches.value.filter((c:any) => c.status==='pending').length
    stats.value[2].value = coaches.value.filter((c:any) => !c.status || c.status==='active').length
    stats.value[3].value = coaches.value.filter((c:any) => c.status==='suspended').length
  } catch { coaches.value = [] }
  loading.value = false
}

async function approve(c: any) {
  try { await api.post(`/api/v1/users/${c.id}/approve-coach`); c.status = 'active' }
  catch (e: any) { alert(e.response?.data?.detail || '操作失败') }
}
async function suspend(c: any) {
  const reason = prompt('停职原因') ?? ''; if (reason === null) return
  try { await api.post(`/api/v1/users/${c.id}/suspend`, { reason }); c.status = 'suspended' }
  catch (e: any) { alert(e.response?.data?.detail || '操作失败') }
}
async function restore(c: any) {
  try { await api.post(`/api/v1/users/${c.id}/restore`); c.status = 'active' }
  catch (e: any) { alert(e.response?.data?.detail || '操作失败') }
}
function viewDetail(c: any) { detail.value = c }

onMounted(load)
</script>

<style scoped>
.page-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:16px; }
.page-header h2 { font-size:18px; font-weight:600; color:#111827; margin:0; }
.header-actions { display:flex; gap:8px; }
.filter-select,.search-input { padding:8px 12px; border:1px solid #e5e7eb; border-radius:8px; font-size:13px; background:#fff; outline:none; }
.search-input { width:180px; }
.search-input:focus { border-color:#3b82f6; }

.stats-row { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:16px; }
.stat-card { background:#fff; border-radius:10px; padding:16px; text-align:center; border-top:3px solid var(--c); box-shadow:0 1px 4px rgba(0,0,0,.06); }
.stat-num { font-size:28px; font-weight:800; color:var(--c); }
.stat-label { font-size:12px; color:#6b7280; margin-top:4px; }

.card { background:#fff; border-radius:12px; padding:20px; box-shadow:0 1px 4px rgba(0,0,0,.06); }
.data-table { width:100%; border-collapse:collapse; font-size:13px; }
.data-table th { text-align:left; padding:10px 12px; color:#6b7280; font-weight:500; border-bottom:2px solid #f3f4f6; }
.data-table td { padding:11px 12px; color:#374151; border-bottom:1px solid #f9fafb; vertical-align:middle; }
.data-table tr:last-child td { border-bottom:none; }

.user-cell { display:flex; align-items:center; gap:10px; }
.avatar { width:34px; height:34px; border-radius:50%; background:linear-gradient(135deg,#6366f1,#3b82f6); color:#fff; font-size:13px; font-weight:700; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.u-name { font-size:13px; font-weight:500; color:#111827; }
.u-sub { font-size:11px; color:#9ca3af; }

.level-tag { background:#ede9fe; color:#5b21b6; padding:2px 8px; border-radius:10px; font-size:11px; }
.bar-wrap { display:inline-block; width:60px; height:6px; background:#f3f4f6; border-radius:3px; vertical-align:middle; margin-right:6px; overflow:hidden; }
.bar-fill { height:100%; background:linear-gradient(90deg,#3b82f6,#10b981); border-radius:3px; }
.bar-pct { font-size:12px; color:#374151; }

.status-tag { padding:2px 8px; border-radius:10px; font-size:11px; font-weight:500; }
.st-active { background:#d1fae5; color:#065f46; }
.st-pending { background:#fef3c7; color:#d97706; }
.st-suspended { background:#fee2e2; color:#dc2626; }

.action-cell { display:flex; gap:5px; flex-wrap:wrap; }
.action-btn { padding:4px 9px; border-radius:6px; border:none; font-size:11px; cursor:pointer; }
.a-approve { background:#d1fae5; color:#065f46; }
.a-suspend { background:#fee2e2; color:#dc2626; }
.a-restore { background:#dbeafe; color:#1d4ed8; }
.a-view { background:#f3f4f6; color:#374151; }

/* drawer */
.drawer-overlay { position:fixed; inset:0; background:rgba(0,0,0,.3); z-index:100; display:flex; justify-content:flex-end; }
.drawer { width:400px; background:#fff; height:100%; box-shadow:-4px 0 20px rgba(0,0,0,.1); display:flex; flex-direction:column; }
.drawer-header { display:flex; align-items:center; justify-content:space-between; padding:20px; border-bottom:1px solid #f3f4f6; }
.drawer-header h3 { font-size:16px; font-weight:600; margin:0; }
.close-btn { background:none; border:none; font-size:18px; color:#9ca3af; cursor:pointer; }
.drawer-body { flex:1; overflow-y:auto; padding:20px; }
.info-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:20px; }
.info-item { background:#f9fafb; border-radius:8px; padding:10px; }
.ik { font-size:11px; color:#9ca3af; display:block; margin-bottom:4px; }
.iv { font-size:14px; font-weight:500; color:#111827; }
.drawer-actions { display:flex; gap:8px; }
.act-btn { padding:9px 18px; border-radius:8px; font-size:13px; font-weight:500; cursor:pointer; border:none; }
.act-primary { background:#d1fae5; color:#065f46; }
.act-warn { background:#fee2e2; color:#dc2626; }
.act-secondary { background:#f3f4f6; color:#374151; border:1px solid #e5e7eb; }

.loading,.empty { color:#9ca3af; font-size:13px; text-align:center; padding:32px 0; }
</style>
