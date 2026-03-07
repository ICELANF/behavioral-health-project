<template>
  <div>
    <div class="page-header">
      <h2>内容管理</h2>
      <div class="header-actions">
        <select v-model="typeFilter" class="filter-select" @change="load">
          <option value="">全部类型</option>
          <option value="article">文章</option>
          <option value="video">视频</option>
          <option value="course">课程</option>
          <option value="knowledge">知识库</option>
        </select>
        <select v-model="statusFilter" class="filter-select" @change="load">
          <option value="">全部状态</option>
          <option value="draft">草稿</option>
          <option value="pending">待审</option>
          <option value="published">已发布</option>
          <option value="rejected">已驳回</option>
        </select>
        <input v-model="searchQ" type="text" placeholder="搜索标题..." class="search-input" @keyup.enter="load" />
      </div>
    </div>

    <div class="tab-row">
      <button v-for="t in tabs" :key="t.key" class="tab-btn" :class="{ active: activeTab === t.key }" @click="switchTab(t.key)">
        {{ t.label }}<span v-if="t.count" class="tab-badge">{{ t.count }}</span>
      </button>
    </div>

    <div class="card">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="items.length === 0" class="empty">暂无内容</div>
      <table v-else class="data-table">
        <thead>
          <tr><th>标题</th><th>类型</th><th>作者</th><th>浏览/点赞</th><th>状态</th><th>发布时间</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td class="title-cell">
              <div class="content-title">{{ item.title || '—' }}</div>
              <div class="content-sub">{{ (item.summary || item.description || '').slice(0, 40) }}</div>
            </td>
            <td><span class="type-tag">{{ typeLabel(item.content_type || item.type) }}</span></td>
            <td>{{ item.author_name || item.created_by_name || '—' }}</td>
            <td class="num-cell">{{ item.view_count ?? 0 }} / {{ item.like_count ?? 0 }}</td>
            <td><span class="status-tag" :class="'st-' + item.status">{{ statusLabel(item.status) }}</span></td>
            <td>{{ item.published_at?.slice(0,10) || item.created_at?.slice(0,10) || '—' }}</td>
            <td class="action-cell">
              <button v-if="item.status !== 'published'" class="action-btn action-publish" @click="publish(item)">发布</button>
              <button v-if="item.status === 'published'" class="action-btn action-unpublish" @click="unpublish(item)">下线</button>
              <button v-if="item.status === 'pending'" class="action-btn action-reject" @click="reject(item)">驳回</button>
              <button class="action-btn action-del" @click="del(item)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="table-footer">
        <span class="total-hint">共 {{ total }} 条</span>
        <div class="pagination">
          <button class="page-btn" :disabled="page <= 1" @click="gotoPage(page-1)">‹</button>
          <span class="page-info">{{ page }} / {{ totalPages || 1 }}</span>
          <button class="page-btn" :disabled="page >= (totalPages||1)" @click="gotoPage(page+1)">›</button>
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
const typeFilter = ref('')
const statusFilter = ref('')
const searchQ = ref('')
const activeTab = ref('all')
const pendingCount = ref(0)

const totalPages = computed(() => Math.ceil(total.value / pageSize))

const tabs = computed(() => [
  { key: 'all',       label: '全部' },
  { key: 'pending',   label: '待审核', count: pendingCount.value },
  { key: 'published', label: '已发布' },
  { key: 'draft',     label: '草稿' },
])

function typeLabel(t: string) {
  const m: Record<string,string> = { article:'文章', video:'视频', course:'课程', knowledge:'知识', tip:'健康贴士' }
  return m[t] || t || '—'
}
function statusLabel(s: string) {
  const m: Record<string,string> = { draft:'草稿', pending:'待审', published:'已发布', rejected:'驳回', unpublished:'已下线' }
  return m[s] || s || '—'
}

async function load() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    const st = activeTab.value !== 'all' ? activeTab.value : statusFilter.value
    if (st) params.append('status', st)
    if (typeFilter.value) params.append('content_type', typeFilter.value)
    if (searchQ.value) params.append('q', searchQ.value)
    params.append('page', String(page.value))
    params.append('page_size', String(pageSize))
    const res: any = await api.get(`/api/v1/content/items?${params}`)
    items.value = res.items || (Array.isArray(res) ? res : [])
    total.value = res.total ?? items.value.length
  } catch { items.value = []; total.value = 0 }
  loading.value = false
}

async function switchTab(t: string) {
  activeTab.value = t; page.value = 1; await load()
}
async function gotoPage(p: number) { page.value = p; await load() }

async function publish(item: any) {
  try { await api.post(`/api/v1/content/items/${item.id}/publish`); item.status = 'published' }
  catch (e: any) { alert(e.response?.data?.detail || '操作失败') }
}
async function unpublish(item: any) {
  try { await api.post(`/api/v1/content/items/${item.id}/unpublish`); item.status = 'unpublished' }
  catch (e: any) { alert(e.response?.data?.detail || '操作失败') }
}
async function reject(item: any) {
  const reason = prompt('驳回原因') ?? ''; if (reason === null) return
  try { await api.post(`/api/v1/content/items/${item.id}/reject`, { reason }); item.status = 'rejected' }
  catch (e: any) { alert(e.response?.data?.detail || '操作失败') }
}
async function del(item: any) {
  if (!confirm(`确认删除「${item.title}」？`)) return
  try { await api.delete(`/api/v1/content/items/${item.id}`); items.value = items.value.filter(i => i.id !== item.id); total.value-- }
  catch (e: any) { alert(e.response?.data?.detail || '操作失败') }
}

onMounted(async () => {
  await load()
  try {
    const res: any = await api.get('/api/v1/content/items?status=pending&page_size=1')
    pendingCount.value = res.total ?? 0
  } catch {}
})
</script>

<style scoped>
.page-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; }
.page-header h2 { font-size:18px; font-weight:600; color:#111827; margin:0; }
.header-actions { display:flex; gap:8px; align-items:center; }
.filter-select { padding:8px 10px; border:1px solid #e5e7eb; border-radius:8px; font-size:13px; background:#fff; cursor:pointer; }
.search-input { padding:8px 12px; border:1px solid #e5e7eb; border-radius:8px; font-size:13px; width:180px; outline:none; }
.search-input:focus { border-color:#3b82f6; }

.tab-row { display:flex; gap:4px; margin-bottom:14px; }
.tab-btn { padding:7px 14px; border:1px solid #e5e7eb; border-radius:8px; background:#fff; font-size:13px; cursor:pointer; color:#6b7280; display:flex; align-items:center; gap:5px; }
.tab-btn.active { background:#3b82f6; color:#fff; border-color:#3b82f6; }
.tab-badge { background:#ef4444; color:#fff; border-radius:10px; font-size:11px; padding:1px 6px; }

.card { background:#fff; border-radius:12px; padding:20px; box-shadow:0 1px 4px rgba(0,0,0,0.06); }
.data-table { width:100%; border-collapse:collapse; font-size:13px; }
.data-table th { text-align:left; padding:10px 12px; color:#6b7280; font-weight:500; border-bottom:2px solid #f3f4f6; }
.data-table td { padding:11px 12px; color:#374151; border-bottom:1px solid #f9fafb; vertical-align:top; }
.data-table tr:last-child td { border-bottom:none; }
.title-cell { max-width:260px; }
.content-title { font-weight:500; color:#111827; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.content-sub { font-size:11px; color:#9ca3af; margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.type-tag { background:#ede9fe; color:#5b21b6; padding:2px 8px; border-radius:10px; font-size:11px; white-space:nowrap; }
.num-cell { font-size:12px; color:#6b7280; white-space:nowrap; }
.status-tag { padding:2px 8px; border-radius:10px; font-size:11px; font-weight:500; white-space:nowrap; }
.st-draft { background:#f3f4f6; color:#6b7280; }
.st-pending { background:#fef3c7; color:#d97706; }
.st-published { background:#d1fae5; color:#065f46; }
.st-rejected,.st-unpublished { background:#fee2e2; color:#dc2626; }
.action-cell { display:flex; gap:5px; flex-wrap:wrap; }
.action-btn { padding:4px 9px; border-radius:6px; border:none; font-size:11px; cursor:pointer; white-space:nowrap; }
.action-publish { background:#d1fae5; color:#065f46; }
.action-unpublish { background:#fef9c3; color:#92400e; }
.action-reject { background:#ffedd5; color:#c2410c; }
.action-del { background:#fee2e2; color:#dc2626; }
.table-footer { display:flex; align-items:center; justify-content:space-between; margin-top:16px; padding-top:12px; border-top:1px solid #f3f4f6; }
.total-hint { font-size:12px; color:#9ca3af; }
.pagination { display:flex; align-items:center; gap:12px; }
.page-btn { padding:5px 12px; border:1px solid #e5e7eb; border-radius:6px; background:#fff; font-size:14px; cursor:pointer; }
.page-btn:disabled { opacity:.4; cursor:not-allowed; }
.page-info { font-size:12px; color:#6b7280; }
.loading,.empty { color:#9ca3af; font-size:13px; text-align:center; padding:32px 0; }
</style>
