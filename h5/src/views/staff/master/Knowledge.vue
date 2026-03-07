<template>
  <div>
    <div class="page-header">
      <h2>知识库管理</h2>
      <div class="header-actions">
        <select v-model="statusFilter" class="filter-select" @change="load">
          <option value="">全部状态</option>
          <option value="pending">待审核</option>
          <option value="published">已发布</option>
          <option value="rejected">已驳回</option>
        </select>
      </div>
    </div>
    <div class="card">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="items.length === 0" class="empty">暂无知识条目</div>
      <table v-else class="data-table">
        <thead>
          <tr><th>标题</th><th>类型</th><th>作者</th><th>状态</th><th>创建时间</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td class="title-cell">{{ item.title || '—' }}</td>
            <td>{{ item.content_type || item.category || '—' }}</td>
            <td>{{ item.author_name || item.author || '—' }}</td>
            <td><span class="status-tag" :class="'st-' + item.status">{{ statusLabel(item.status) }}</span></td>
            <td>{{ item.created_at?.slice(0, 10) || '—' }}</td>
            <td class="action-cell">
              <button class="action-btn action-view" @click="viewItem(item)">查看</button>
              <button v-if="item.status === 'pending'" class="action-btn action-approve" @click="doPublish(item)">发布</button>
              <button v-if="item.status === 'pending'" class="action-btn action-reject" @click="doReject(item)">驳回</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 详情Modal -->
    <div v-if="viewing" class="modal-overlay" @click.self="viewing = null">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ viewing.title }}</h3>
          <button class="modal-close" @click="viewing = null">✕</button>
        </div>
        <div class="modal-body">
          <div class="meta-row">
            <span class="status-tag" :class="'st-' + viewing.status">{{ statusLabel(viewing.status) }}</span>
            <span class="meta-text">{{ viewing.content_type || viewing.category || '—' }}</span>
            <span class="meta-text">{{ viewing.author_name || '—' }}</span>
          </div>
          <div class="content-preview">{{ viewing.content || viewing.body || viewing.summary || '暂无内容' }}</div>
        </div>
        <div class="modal-footer">
          <button v-if="viewing.status === 'pending'" class="act-btn act-primary" @click="doPublish(viewing); viewing = null">发布</button>
          <button v-if="viewing.status === 'pending'" class="act-btn act-reject" @click="doReject(viewing); viewing = null">驳回</button>
          <button class="act-btn act-secondary" @click="viewing = null">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/api/index'

const loading = ref(true)
const items = ref<any[]>([])
const statusFilter = ref('pending')
const viewing = ref<any>(null)

function statusLabel(s: string) {
  const m: Record<string, string> = { pending: '待审核', published: '已发布', rejected: '已驳回', draft: '草稿' }
  return m[s] || s
}

async function load() {
  loading.value = true
  try {
    const params = statusFilter.value ? `?status=${statusFilter.value}` : ''
    const res: any = await api.get(`/api/v1/knowledge/items${params}`)
    items.value = res.items || (Array.isArray(res) ? res : [])
  } catch { items.value = [] }
  loading.value = false
}

function viewItem(item: any) { viewing.value = item }

async function doPublish(item: any) {
  try {
    await api.post(`/api/v1/knowledge/items/${item.id}/publish`)
    item.status = 'published'
  } catch (e: any) { alert(e.response?.data?.detail || '操作失败') }
}

async function doReject(item: any) {
  const reason = prompt('驳回原因') ?? ''
  try {
    await api.post(`/api/v1/knowledge/items/${item.id}/reject`, { reason })
    item.status = 'rejected'
  } catch (e: any) { alert(e.response?.data?.detail || '操作失败') }
}

onMounted(load)
</script>

<style scoped>
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.page-header h2 { font-size: 18px; font-weight: 600; color: #111827; margin: 0; }
.header-actions { display: flex; gap: 8px; }
.filter-select { padding: 8px 12px; border: 1px solid #e5e7eb; border-radius: 8px; font-size: 13px; background: #fff; cursor: pointer; }

.card { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 10px 12px; color: #6b7280; font-weight: 500; border-bottom: 2px solid #f3f4f6; }
.data-table td { padding: 12px; color: #374151; border-bottom: 1px solid #f9fafb; }
.data-table tr:last-child td { border-bottom: none; }
.title-cell { font-weight: 500; max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.status-tag { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 500; }
.st-pending   { background: #fef3c7; color: #d97706; }
.st-published { background: #d1fae5; color: #065f46; }
.st-rejected  { background: #fee2e2; color: #dc2626; }
.st-draft     { background: #f3f4f6; color: #6b7280; }

.action-cell { display: flex; gap: 6px; white-space: nowrap; }
.action-btn { padding: 4px 10px; border-radius: 6px; border: none; font-size: 12px; cursor: pointer; }
.action-view { background: #eff6ff; color: #1d4ed8; }
.action-approve { background: #d1fae5; color: #065f46; }
.action-reject { background: #fee2e2; color: #dc2626; }

/* modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.45); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #fff; border-radius: 12px; padding: 24px; width: 600px; max-width: 90vw; max-height: 80vh; overflow-y: auto; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
.modal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.modal-header h3 { font-size: 16px; font-weight: 600; margin: 0; }
.modal-close { background: none; border: none; font-size: 18px; cursor: pointer; color: #9ca3af; }
.modal-body { margin-bottom: 20px; }
.modal-footer { display: flex; gap: 8px; justify-content: flex-end; }
.meta-row { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.meta-text { font-size: 13px; color: #6b7280; }
.content-preview { background: #f9fafb; border-radius: 8px; padding: 16px; font-size: 14px; color: #374151; line-height: 1.6; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }

.act-btn { padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 500; cursor: pointer; border: none; }
.act-primary { background: #d1fae5; color: #065f46; }
.act-reject { background: #fee2e2; color: #dc2626; }
.act-secondary { background: #f3f4f6; color: #374151; border: 1px solid #e5e7eb; }

.loading, .empty { color: #9ca3af; font-size: 13px; text-align: center; padding: 32px 0; }
</style>
