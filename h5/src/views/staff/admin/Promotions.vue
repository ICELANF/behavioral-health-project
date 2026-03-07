<template>
  <div>
    <div class="page-header">
      <h2>晋级申请总览</h2>
      <div class="header-actions">
        <select v-model="stageFilter" class="filter-select" @change="load">
          <option value="">全部阶段</option>
          <option value="L1">L1 教练初审</option>
          <option value="L2">L2 督导复核</option>
          <option value="L3">L3 大师终审</option>
        </select>
        <select v-model="statusFilter" class="filter-select" @change="load">
          <option value="">全部状态</option>
          <option value="pending">待审</option>
          <option value="approved">已通过</option>
          <option value="rejected">已驳回</option>
        </select>
      </div>
    </div>

    <div class="stats-row">
      <div class="stat-card" v-for="s in stats" :key="s.label" :style="{'--c':s.color}">
        <div class="stat-num">{{ s.value }}</div>
        <div class="stat-label">{{ s.label }}</div>
      </div>
    </div>

    <div class="card">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="items.length === 0" class="empty">暂无晋级申请</div>
      <table v-else class="data-table">
        <thead>
          <tr><th>申请人</th><th>当前→目标</th><th>当前阶段</th><th>L1教练</th><th>L2督导</th><th>L3大师</th><th>申请时间</th><th>状态</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td>
              <div class="user-cell">
                <div class="avatar">{{ (item.user_name||item.applicant_name||'?')[0] }}</div>
                <span class="u-name">{{ item.user_name||item.applicant_name||'—' }}</span>
              </div>
            </td>
            <td><span class="level-flow">{{ item.current_level||item.from_level||'—' }} → {{ item.target_level||item.to_level||'—' }}</span></td>
            <td><span class="stage-tag" :class="'sg-'+(item.current_stage||'L1')">{{ item.current_stage||'L1' }}</span></td>
            <td>{{ item.l1_reviewer||'—' }}</td>
            <td>{{ item.l2_reviewer||'—' }}</td>
            <td>{{ item.l3_reviewer||'—' }}</td>
            <td>{{ item.created_at?.slice(0,10)||'—' }}</td>
            <td><span class="status-tag" :class="'st-'+item.status">{{ statusLabel(item.status) }}</span></td>
            <td class="action-cell">
              <button v-if="item.status==='pending'" class="action-btn a-approve" @click="forceApprove(item)">强制通过</button>
              <button v-if="item.status==='pending'" class="action-btn a-reject" @click="forceReject(item)">驳回</button>
            </td>
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
const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const stageFilter = ref('')
const statusFilter = ref('')

const totalPages = computed(() => Math.ceil(total.value / pageSize))
const stats = ref([
  { label: '申请总数', value: 0, color: '#3b82f6' },
  { label: '审核中',   value: 0, color: '#f59e0b' },
  { label: '本月通过', value: 0, color: '#10b981' },
  { label: '驳回',     value: 0, color: '#ef4444' },
])

function statusLabel(s: string) {
  const m: Record<string,string> = { pending:'审核中', approved:'已通过', l1_approved:'L1通过', l2_approved:'L2通过', final_approved:'终审通过', rejected:'已驳回' }
  return m[s] || s || '—'
}

async function load() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (stageFilter.value) params.append('stage', stageFilter.value)
    if (statusFilter.value) params.append('status', statusFilter.value)
    params.append('page', String(page.value))
    params.append('page_size', String(pageSize))
    const res: any = await api.get(`/api/v1/promotion/applications?${params}`)
    items.value = res.items || (Array.isArray(res) ? res : [])
    total.value = res.total ?? items.value.length
    stats.value[0].value = total.value
    stats.value[1].value = items.value.filter((i:any) => i.status?.includes('pending') || i.status?.includes('approved') && !i.status?.includes('final')).length
    stats.value[2].value = items.value.filter((i:any) => i.status === 'final_approved' || i.status === 'approved').length
    stats.value[3].value = items.value.filter((i:any) => i.status === 'rejected').length
  } catch { items.value = []; total.value = 0 }
  loading.value = false
}

async function gotoPage(p: number) { page.value = p; await load() }
async function forceApprove(item: any) {
  if (!confirm('以管理员身份强制通过此申请？')) return
  try { await api.post(`/api/v1/promotion/applications/${item.id}/approve`); item.status = 'final_approved' }
  catch (e: any) { alert(e.response?.data?.detail || '操作失败') }
}
async function forceReject(item: any) {
  const reason = prompt('驳回原因') ?? ''; if (reason === null) return
  try { await api.post(`/api/v1/promotion/applications/${item.id}/reject`, { reason }); item.status = 'rejected' }
  catch (e: any) { alert(e.response?.data?.detail || '操作失败') }
}

onMounted(load)
</script>

<style scoped>
.page-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:16px; }
.page-header h2 { font-size:18px; font-weight:600; color:#111827; margin:0; }
.header-actions { display:flex; gap:8px; }
.filter-select { padding:8px 12px; border:1px solid #e5e7eb; border-radius:8px; font-size:13px; background:#fff; cursor:pointer; }

.stats-row { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:16px; }
.stat-card { background:#fff; border-radius:10px; padding:16px; text-align:center; border-top:3px solid var(--c); box-shadow:0 1px 4px rgba(0,0,0,.06); }
.stat-num { font-size:28px; font-weight:800; color:var(--c); }
.stat-label { font-size:12px; color:#6b7280; margin-top:4px; }

.card { background:#fff; border-radius:12px; padding:20px; box-shadow:0 1px 4px rgba(0,0,0,.06); }
.data-table { width:100%; border-collapse:collapse; font-size:13px; }
.data-table th { text-align:left; padding:10px 12px; color:#6b7280; font-weight:500; border-bottom:2px solid #f3f4f6; }
.data-table td { padding:11px 12px; color:#374151; border-bottom:1px solid #f9fafb; vertical-align:middle; }
.data-table tr:last-child td { border-bottom:none; }

.user-cell { display:flex; align-items:center; gap:8px; }
.avatar { width:30px; height:30px; border-radius:50%; background:linear-gradient(135deg,#6366f1,#3b82f6); color:#fff; font-size:12px; font-weight:700; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.u-name { font-size:13px; font-weight:500; }
.level-flow { font-weight:600; color:#374151; font-size:13px; }

.stage-tag { padding:2px 8px; border-radius:10px; font-size:11px; font-weight:600; }
.sg-L1 { background:#dbeafe; color:#1d4ed8; }
.sg-L2 { background:#ede9fe; color:#5b21b6; }
.sg-L3 { background:#fef9c3; color:#92400e; }

.status-tag { padding:2px 8px; border-radius:10px; font-size:11px; font-weight:500; }
.st-pending { background:#fef3c7; color:#d97706; }
.st-approved,.st-final_approved,.st-l1_approved,.st-l2_approved { background:#d1fae5; color:#065f46; }
.st-rejected { background:#fee2e2; color:#dc2626; }

.action-cell { display:flex; gap:5px; }
.action-btn { padding:4px 10px; border-radius:6px; border:none; font-size:11px; cursor:pointer; }
.a-approve { background:#d1fae5; color:#065f46; }
.a-reject { background:#fee2e2; color:#dc2626; }

.table-footer { display:flex; align-items:center; justify-content:space-between; margin-top:14px; padding-top:12px; border-top:1px solid #f3f4f6; }
.total-hint { font-size:12px; color:#9ca3af; }
.pagination { display:flex; align-items:center; gap:12px; }
.page-btn { padding:5px 12px; border:1px solid #e5e7eb; border-radius:6px; background:#fff; font-size:14px; cursor:pointer; }
.page-btn:disabled { opacity:.4; cursor:not-allowed; }
.page-info { font-size:12px; color:#6b7280; }

.loading,.empty { color:#9ca3af; font-size:13px; text-align:center; padding:32px 0; }
</style>
