<template>
  <div class="xzb-knowledge-confirm">
    <a-page-header title="知识确认" sub-title="审核AI提取的知识条目，确认或拒绝入库" />

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-num pending">{{ healthReport.total - healthReport.confirmed }}</div>
        <div class="stat-label">待确认</div>
      </div>
      <div class="stat-card">
        <div class="stat-num confirmed">{{ healthReport.confirmed }}</div>
        <div class="stat-label">已确认</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">{{ healthReport.total }}</div>
        <div class="stat-label">总条目</div>
      </div>
      <div class="stat-card">
        <div class="stat-num coverage">{{ (healthReport.coverage_rate * 100).toFixed(0) }}%</div>
        <div class="stat-label">覆盖率</div>
      </div>
      <div class="stat-card">
        <div class="stat-num freshness">{{ (healthReport.freshness_rate * 100).toFixed(0) }}%</div>
        <div class="stat-label">新鲜度</div>
      </div>
    </div>

    <!-- Tab 切换 -->
    <a-tabs v-model:activeKey="activeTab" @change="handleTabChange">
      <!-- 待确认 -->
      <a-tab-pane key="pending" :tab="`待确认 (${pendingItems.length})`">
        <a-spin :spinning="pendingLoading">
          <div v-if="!pendingItems.length && !pendingLoading" class="empty-state">
            <div class="empty-icon">&#x2705;</div>
            <h3>全部已确认</h3>
            <p>暂无待确认的知识条目</p>
          </div>
          <div class="list-container" v-else>
            <div v-for="item in pendingItems" :key="item.id" class="knowledge-card">
              <div class="card-header">
                <span class="type-tag" :style="typeStyle(item.type)">{{ typeLabel(item.type) }}</span>
                <span class="tier-tag" :style="tierStyle(item.evidence_tier)">{{ item.evidence_tier || '-' }}</span>
                <span class="time-text">{{ formatTime(item.created_at) }}</span>
              </div>
              <div class="card-content">{{ item.content }}</div>
              <div class="card-meta" v-if="item.source">
                <span class="meta-label">来源:</span> {{ item.source }}
              </div>
              <div class="card-tags" v-if="item.tags && item.tags.length">
                <span class="tag-item" v-for="tag in item.tags" :key="tag">{{ tag }}</span>
              </div>
              <div class="card-actions">
                <a-button size="small" @click="showDetail(item.id)">详情</a-button>
                <a-popconfirm title="确认此条目入库?" @confirm="handleConfirm(item.id)">
                  <a-button type="primary" size="small">确认入库</a-button>
                </a-popconfirm>
                <a-popconfirm title="拒绝此条目? 将标记为不活跃" @confirm="handleReject(item.id)">
                  <a-button danger size="small">拒绝</a-button>
                </a-popconfirm>
              </div>
            </div>
          </div>
        </a-spin>
      </a-tab-pane>

      <!-- 全部知识库 -->
      <a-tab-pane key="all" tab="全部知识库">
        <div class="filter-bar">
          <a-select v-model:value="filterType" placeholder="按类型" allowClear style="width: 140px" @change="loadAllKnowledge">
            <a-select-option value="note">笔记</a-select-option>
            <a-select-option value="rule">规则</a-select-option>
            <a-select-option value="case">案例</a-select-option>
            <a-select-option value="annotation">批注</a-select-option>
            <a-select-option value="template">模板</a-select-option>
            <a-select-option value="forbidden">禁用</a-select-option>
          </a-select>
          <a-select v-model:value="filterConfirmed" placeholder="确认状态" allowClear style="width: 140px" @change="loadAllKnowledge">
            <a-select-option :value="true">已确认</a-select-option>
            <a-select-option :value="false">未确认</a-select-option>
          </a-select>
        </div>
        <a-spin :spinning="allLoading">
          <div class="list-container">
            <div v-for="item in allItems" :key="item.id" class="knowledge-card">
              <div class="card-header">
                <span class="type-tag" :style="typeStyle(item.type)">{{ typeLabel(item.type) }}</span>
                <span class="tier-tag" :style="tierStyle(item.evidence_tier)">{{ item.evidence_tier || '-' }}</span>
                <span class="confirm-status" :class="{ confirmed: item.expert_confirmed }">
                  {{ item.expert_confirmed ? '已确认' : '未确认' }}
                </span>
                <span class="usage-count">引用 {{ item.usage_count ?? 0 }} 次</span>
              </div>
              <div class="card-content-short">{{ truncate(item.content, 200) }}</div>
              <div class="card-tags" v-if="item.tags && item.tags.length">
                <span class="tag-item" v-for="tag in item.tags" :key="tag">{{ tag }}</span>
              </div>
              <div class="card-actions">
                <a-button size="small" @click="showDetail(item.id)">详情</a-button>
                <a-popconfirm v-if="!item.expert_confirmed" title="确认此条目入库?" @confirm="handleConfirm(item.id)">
                  <a-button type="primary" size="small">确认</a-button>
                </a-popconfirm>
              </div>
            </div>
          </div>
        </a-spin>
        <a-pagination
          v-model:current="allPage"
          :total="allTotal"
          :pageSize="allPageSize"
          style="margin-top: 16px; text-align: right"
          @change="loadAllKnowledge"
        />
      </a-tab-pane>
    </a-tabs>

    <!-- 详情弹窗 -->
    <a-modal v-model:open="detailVisible" title="知识条目详情" :footer="null" width="640px">
      <a-spin :spinning="detailLoading">
        <a-descriptions v-if="detailItem" :column="1" bordered size="small">
          <a-descriptions-item label="ID">{{ detailItem.id }}</a-descriptions-item>
          <a-descriptions-item label="类型">
            <span class="type-tag" :style="typeStyle(detailItem.type)">{{ typeLabel(detailItem.type) }}</span>
          </a-descriptions-item>
          <a-descriptions-item label="循证等级">
            <span class="tier-tag" :style="tierStyle(detailItem.evidence_tier)">{{ detailItem.evidence_tier || '-' }}</span>
          </a-descriptions-item>
          <a-descriptions-item label="确认状态">
            <span :class="detailItem.expert_confirmed ? 'text-green' : 'text-orange'">
              {{ detailItem.expert_confirmed ? '已确认' : '未确认' }}
            </span>
          </a-descriptions-item>
          <a-descriptions-item label="引用次数">{{ detailItem.usage_count ?? 0 }}</a-descriptions-item>
          <a-descriptions-item label="来源">{{ detailItem.source || '-' }}</a-descriptions-item>
          <a-descriptions-item label="标签">
            <span v-if="detailItem.tags && detailItem.tags.length">
              <span class="tag-item" v-for="tag in detailItem.tags" :key="tag">{{ tag }}</span>
            </span>
            <span v-else>-</span>
          </a-descriptions-item>
          <a-descriptions-item label="内容">
            <div class="detail-content">{{ detailItem.content }}</div>
          </a-descriptions-item>
        </a-descriptions>
      </a-spin>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import request from '../../api/request'

const activeTab = ref('pending')

// ── 健康报告统计 ──
const healthReport = reactive({
  total: 0, confirmed: 0, needs_review: 0,
  coverage_rate: 0, freshness_rate: 0,
})

// ── 待确认列表 ──
const pendingItems = ref<any[]>([])
const pendingLoading = ref(false)

// ── 全部知识库 ──
const allItems = ref<any[]>([])
const allLoading = ref(false)
const allPage = ref(1)
const allPageSize = 20
const allTotal = ref(0)
const filterType = ref<string | undefined>(undefined)
const filterConfirmed = ref<boolean | undefined>(undefined)

// ── 详情弹窗 ──
const detailVisible = ref(false)
const detailItem = ref<any>(null)
const detailLoading = ref(false)

// ── 加载数据 ──
async function loadHealthReport() {
  try {
    const res = await request.get('/v1/xzb/knowledge/health-report')
    const d = res.data?.data || res.data
    Object.assign(healthReport, d)
  } catch {}
}

async function loadPendingItems() {
  pendingLoading.value = true
  try {
    const res = await request.get('/v1/xzb/knowledge/pending-confirm')
    const d = res.data?.data || res.data
    pendingItems.value = d.items || []
  } catch {
    pendingItems.value = []
  } finally {
    pendingLoading.value = false
  }
}

async function loadAllKnowledge() {
  allLoading.value = true
  try {
    const params: Record<string, any> = { page: allPage.value, page_size: allPageSize }
    if (filterType.value) params.type = filterType.value
    if (filterConfirmed.value !== undefined && filterConfirmed.value !== null) params.confirmed_only = filterConfirmed.value
    const res = await request.get('/v1/xzb/knowledge', { params })
    const d = res.data?.data || res.data
    allItems.value = d.items || []
    allTotal.value = d.total ?? allItems.value.length
  } catch {
    allItems.value = []
  } finally {
    allLoading.value = false
  }
}

// ── 操作 ──
async function handleConfirm(id: string) {
  try {
    await request.post(`/v1/xzb/knowledge/${id}/confirm?action=confirm`)
    message.success('已确认入库')
    pendingItems.value = pendingItems.value.filter(i => i.id !== id)
    loadHealthReport()
    if (activeTab.value === 'all') loadAllKnowledge()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '操作失败')
  }
}

async function handleReject(id: string) {
  try {
    await request.post(`/v1/xzb/knowledge/${id}/confirm?action=reject`)
    message.success('已拒绝')
    pendingItems.value = pendingItems.value.filter(i => i.id !== id)
    loadHealthReport()
    if (activeTab.value === 'all') loadAllKnowledge()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '操作失败')
  }
}

async function showDetail(id: string) {
  detailVisible.value = true
  detailLoading.value = true
  try {
    const res = await request.get(`/v1/xzb/knowledge/${id}`)
    detailItem.value = res.data?.data || res.data
  } catch {
    detailItem.value = null
    message.error('加载详情失败')
  } finally {
    detailLoading.value = false
  }
}

function handleTabChange(key: string) {
  if (key === 'pending') loadPendingItems()
  else if (key === 'all') loadAllKnowledge()
}

// ── 辅助函数 ──
const typeLabels: Record<string, string> = {
  note: '笔记', rule: '规则', case: '案例',
  annotation: '批注', template: '模板', forbidden: '禁用',
}
function typeLabel(t: string) { return typeLabels[t] || t }

const typeColors: Record<string, { bg: string; color: string }> = {
  note: { bg: '#e3f2fd', color: '#1565c0' },
  rule: { bg: '#fce4ec', color: '#c62828' },
  case: { bg: '#e8f5e9', color: '#2e7d32' },
  annotation: { bg: '#fff3e0', color: '#e65100' },
  template: { bg: '#ede7f6', color: '#6a1b9a' },
  forbidden: { bg: '#ffebee', color: '#b71c1c' },
}
function typeStyle(t: string) {
  const s = typeColors[t] || { bg: '#f5f5f5', color: '#616161' }
  return { background: s.bg, color: s.color }
}

const tierColors: Record<string, { bg: string; color: string }> = {
  T1: { bg: '#fff8e1', color: '#f57f17' },
  T2: { bg: '#e3f2fd', color: '#1565c0' },
  T3: { bg: '#e8f5e9', color: '#2e7d32' },
  T4: { bg: '#eceff1', color: '#455a64' },
}
function tierStyle(t: string) {
  const s = tierColors[t] || { bg: '#f5f5f5', color: '#616161' }
  return { background: s.bg, color: s.color }
}

function formatTime(str: string | null) {
  if (!str) return '-'
  return str.replace('T', ' ').slice(0, 16)
}

function truncate(str: string, max: number) {
  if (!str) return ''
  return str.length > max ? str.slice(0, max) + '...' : str
}

onMounted(() => {
  loadHealthReport()
  loadPendingItems()
})
</script>

<style scoped>
.xzb-knowledge-confirm { padding: 0; }

/* 统计卡片 */
.stats-row { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.stat-card {
  flex: 1; min-width: 120px; background: #fff; border: 1px solid #f0f0f0;
  border-radius: 10px; padding: 16px; text-align: center;
}
.stat-num { font-size: 28px; font-weight: 800; color: #111827; }
.stat-num.pending { color: #faad14; }
.stat-num.confirmed { color: #52c41a; }
.stat-num.coverage { color: #1890ff; }
.stat-num.freshness { color: #722ed1; }
.stat-label { font-size: 12px; color: #999; margin-top: 4px; }

/* 筛选栏 */
.filter-bar { display: flex; gap: 10px; margin-bottom: 16px; }

/* 空状态 */
.empty-state { text-align: center; padding: 60px 0; }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-state h3 { font-size: 18px; font-weight: 700; margin: 0 0 8px; color: #111827; }
.empty-state p { color: #999; }

/* 知识卡片 */
.list-container { display: flex; flex-direction: column; gap: 10px; }
.knowledge-card {
  background: #fff; border: 1px solid #f0f0f0; border-radius: 10px;
  padding: 14px 16px; transition: box-shadow 0.2s;
}
.knowledge-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.type-tag {
  font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px;
  display: inline-block;
}
.tier-tag {
  font-size: 11px; font-weight: 700; padding: 2px 6px; border-radius: 3px;
  display: inline-block;
}
.time-text { font-size: 11px; color: #999; margin-left: auto; }
.confirm-status { font-size: 11px; font-weight: 600; padding: 2px 6px; border-radius: 3px; background: #fff7e6; color: #d48806; }
.confirm-status.confirmed { background: #f6ffed; color: #389e0d; }
.usage-count { font-size: 11px; color: #999; margin-left: auto; }

.card-content { font-size: 13px; color: #374151; line-height: 1.6; margin-bottom: 8px; white-space: pre-wrap; }
.card-content-short { font-size: 13px; color: #374151; line-height: 1.5; margin-bottom: 8px; }
.card-meta { font-size: 12px; color: #999; margin-bottom: 6px; }
.meta-label { font-weight: 600; }

.card-tags { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 8px; }
.tag-item {
  font-size: 10px; background: #f5f5f5; color: #666; padding: 1px 6px;
  border-radius: 3px;
}

.card-actions { display: flex; gap: 8px; justify-content: flex-end; }

/* 详情弹窗 */
.detail-content { white-space: pre-wrap; line-height: 1.6; font-size: 13px; color: #374151; }
.text-green { color: #389e0d; font-weight: 600; }
.text-orange { color: #d48806; font-weight: 600; }

@media (max-width: 640px) {
  .stats-row { flex-direction: column; }
  .stat-card { min-width: auto; }
  .card-actions { flex-wrap: wrap; }
}
</style>
