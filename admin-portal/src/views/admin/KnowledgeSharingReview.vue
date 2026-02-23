<template>
  <div class="knowledge-sharing">
    <a-page-header title="知识共享管理" sub-title="审核专家贡献、查看领域共享池" />

    <!-- 统计卡片 -->
    <a-row :gutter="16" style="margin-bottom: 16px">
      <a-col :span="6">
        <a-statistic title="待审核" :value="stats.pending" :value-style="{ color: '#faad14' }" />
      </a-col>
      <a-col :span="6">
        <a-statistic title="已通过" :value="stats.approved" :value-style="{ color: '#52c41a' }" />
      </a-col>
      <a-col :span="6">
        <a-statistic title="已拒绝" :value="stats.rejected" :value-style="{ color: '#ff4d4f' }" />
      </a-col>
      <a-col :span="6">
        <a-statistic title="已撤回" :value="stats.revoked" />
      </a-col>
    </a-row>

    <!-- Tab切换 -->
    <a-tabs v-model:activeKey="activeTab" @change="handleTabChange">
      <!-- 待审核 -->
      <a-tab-pane key="pending" tab="待审核">
        <a-spin :spinning="loading">
          <div class="list-card-container">
            <ListCard v-for="record in pendingList" :key="record.id">
              <template #title>
                <span>{{ record.document_title }}</span>
                <a-tag :color="statusColor(record.status)" style="margin-left: 8px">{{ statusLabel(record.status) }}</a-tag>
              </template>
              <template #subtitle>
                租户: {{ record.tenant_id }} | 领域: {{ record.domain_id }}
              </template>
              <template #meta>
                <span v-if="record.reason">理由: {{ record.reason }}</span>
                <span>提交: {{ record.created_at }}</span>
              </template>
              <template #actions>
                <a-space>
                  <a-button type="link" size="small" @click="showDetail(record)">详情</a-button>
                  <a-popconfirm title="确认通过?" @confirm="handleApprove(record.id)">
                    <a-button type="link" size="small" style="color: #52c41a">通过</a-button>
                  </a-popconfirm>
                  <a-button type="link" size="small" danger @click="showReject(record)">拒绝</a-button>
                </a-space>
              </template>
            </ListCard>
          </div>
        </a-spin>
        <a-pagination
          v-model:current="pagination.current"
          :total="pagination.total"
          :pageSize="pagination.pageSize"
          style="margin-top: 16px; text-align: right"
          @change="(page: number) => { pagination.current = page; loadPendingList() }"
        />
      </a-tab-pane>

      <!-- 领域共享池 -->
      <a-tab-pane key="domain-pool" tab="领域共享池">
        <div style="margin-bottom: 16px">
          <a-select
            v-model:value="poolDomainFilter"
            placeholder="按领域筛选"
            allowClear
            style="width: 200px"
            :options="domainOptions"
            @change="loadDomainPool"
          />
        </div>
        <a-spin :spinning="poolLoading">
          <div class="list-card-container">
            <ListCard v-for="record in poolList" :key="record.id">
              <template #title>{{ record.title }}</template>
              <template #subtitle>
                领域: {{ record.domain_id }} | 来源租户: {{ record.tenant_id }}
                <a-tag :color="tierColor(record.evidence_tier)" style="margin-left: 8px">{{ record.evidence_tier }}</a-tag>
              </template>
              <template #meta>
                <span>分片数: {{ record.chunk_count }}</span>
                <span>更新: {{ record.updated_at }}</span>
              </template>
            </ListCard>
          </div>
        </a-spin>
        <a-pagination
          v-model:current="poolPagination.current"
          :total="poolPagination.total"
          :pageSize="poolPagination.pageSize"
          style="margin-top: 16px; text-align: right"
          @change="(page: number) => { poolPagination.current = page; loadDomainPool() }"
        />
      </a-tab-pane>

      <!-- 全部记录 -->
      <a-tab-pane key="all" tab="全部记录">
        <div style="margin-bottom: 16px">
          <a-select
            v-model:value="allStatusFilter"
            placeholder="按状态筛选"
            allowClear
            style="width: 150px; margin-right: 8px"
            :options="statusOptions"
            @change="loadAllContributions"
          />
          <a-select
            v-model:value="allDomainFilter"
            placeholder="按领域筛选"
            allowClear
            style="width: 200px"
            :options="domainOptions"
            @change="loadAllContributions"
          />
        </div>
        <a-spin :spinning="allLoading">
          <div class="list-card-container">
            <ListCard v-for="record in allList" :key="record.id">
              <template #title>
                <span>{{ record.document_title }}</span>
                <a-tag :color="statusColor(record.status)" style="margin-left: 8px">{{ statusLabel(record.status) }}</a-tag>
              </template>
              <template #subtitle>
                租户: {{ record.tenant_id }} | 领域: {{ record.domain_id }}
              </template>
              <template #meta>
                <span v-if="record.review_comment">审核意见: {{ record.review_comment }}</span>
                <span>提交: {{ record.created_at }}</span>
              </template>
            </ListCard>
          </div>
        </a-spin>
        <a-pagination
          v-model:current="allPagination.current"
          :total="allPagination.total"
          :pageSize="allPagination.pageSize"
          style="margin-top: 16px; text-align: right"
          @change="(page: number) => { allPagination.current = page; loadAllContributions() }"
        />
      </a-tab-pane>
    </a-tabs>

    <!-- 详情弹窗 -->
    <a-modal v-model:open="detailVisible" title="贡献详情" :footer="null" width="600px">
      <a-descriptions v-if="detailRecord" :column="1" bordered size="small">
        <a-descriptions-item label="文档标题">{{ detailRecord.document_title }}</a-descriptions-item>
        <a-descriptions-item label="贡献者租户">{{ detailRecord.tenant_id }}</a-descriptions-item>
        <a-descriptions-item label="目标领域">{{ detailRecord.domain_id }}</a-descriptions-item>
        <a-descriptions-item label="贡献理由">{{ detailRecord.reason || '-' }}</a-descriptions-item>
        <a-descriptions-item label="状态">
          <a-tag :color="statusColor(detailRecord.status)">{{ statusLabel(detailRecord.status) }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="审核意见" v-if="detailRecord.review_comment">{{ detailRecord.review_comment }}</a-descriptions-item>
        <a-descriptions-item label="审核时间" v-if="detailRecord.reviewed_at">{{ detailRecord.reviewed_at }}</a-descriptions-item>
        <a-descriptions-item label="提交时间">{{ detailRecord.created_at }}</a-descriptions-item>
      </a-descriptions>
    </a-modal>

    <!-- 拒绝弹窗 -->
    <a-modal v-model:open="rejectVisible" title="拒绝贡献" @ok="handleReject" :confirmLoading="rejectLoading">
      <a-form layout="vertical">
        <a-form-item label="拒绝理由">
          <a-textarea v-model:value="rejectComment" :rows="3" placeholder="请说明拒绝原因..." />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import request from '../../api/request'
import ListCard from '@/components/core/ListCard.vue'

const activeTab = ref('pending')
const loading = ref(false)
const poolLoading = ref(false)
const allLoading = ref(false)

// 统计
const stats = reactive({ pending: 0, approved: 0, rejected: 0, revoked: 0 })

// 待审核
const pendingList = ref<any[]>([])
const pagination = reactive({ current: 1, pageSize: 20, total: 0 })

// 领域共享池
const poolList = ref<any[]>([])
const poolDomainFilter = ref<string | undefined>(undefined)
const poolPagination = reactive({ current: 1, pageSize: 20, total: 0 })

// 全部记录
const allList = ref<any[]>([])
const allStatusFilter = ref<string | undefined>(undefined)
const allDomainFilter = ref<string | undefined>(undefined)
const allPagination = reactive({ current: 1, pageSize: 20, total: 0 })

// 领域选项
const domainOptions = ref<{ label: string; value: string }[]>([])

// 详情弹窗
const detailVisible = ref(false)
const detailRecord = ref<any>(null)

// 拒绝弹窗
const rejectVisible = ref(false)
const rejectComment = ref('')
const rejectLoading = ref(false)
const rejectTarget = ref<any>(null)

const statusOptions = [
  { label: '待审核', value: 'pending' },
  { label: '已通过', value: 'approved' },
  { label: '已拒绝', value: 'rejected' },
  { label: '已撤回', value: 'revoked' },
]

// columns removed — replaced by ListCard layout

function statusColor(s: string) {
  return { pending: 'orange', approved: 'green', rejected: 'red', revoked: 'default' }[s] || 'default'
}

function statusLabel(s: string) {
  return { pending: '待审核', approved: '已通过', rejected: '已拒绝', revoked: '已撤回' }[s] || s
}

function tierColor(t: string) {
  return { T1: 'gold', T2: 'blue', T3: 'green', T4: 'default' }[t] || 'default'
}

function showDetail(record: any) {
  detailRecord.value = record
  detailVisible.value = true
}

function showReject(record: any) {
  rejectTarget.value = record
  rejectComment.value = ''
  rejectVisible.value = true
}

async function loadStats() {
  try {
    const res = await request.get('/v1/knowledge-sharing/stats')
    Object.assign(stats, res.data.data)
  } catch {}
}

async function loadDomains() {
  try {
    const res = await request.get('/v1/knowledge-sharing/domains')
    domainOptions.value = (res.data.data || []).map((d: any) => ({
      label: `${d.label} (${d.domain_id})`,
      value: d.domain_id,
    }))
  } catch {}
}

async function loadPendingList() {
  loading.value = true
  try {
    const res = await request.get('/v1/knowledge-sharing/review-queue', {
      params: { skip: (pagination.current - 1) * pagination.pageSize, limit: pagination.pageSize },
    })
    pendingList.value = res.data.data.items
    pagination.total = res.data.data.total
  } catch {} finally { loading.value = false }
}

async function loadDomainPool() {
  poolLoading.value = true
  try {
    const params: any = { skip: (poolPagination.current - 1) * poolPagination.pageSize, limit: poolPagination.pageSize }
    if (poolDomainFilter.value) params.domain_id = poolDomainFilter.value
    const res = await request.get('/v1/knowledge-sharing/domain-pool', { params })
    poolList.value = res.data.data.items
    poolPagination.total = res.data.data.total
  } catch {} finally { poolLoading.value = false }
}

async function loadAllContributions() {
  allLoading.value = true
  try {
    const params: any = { skip: (allPagination.current - 1) * allPagination.pageSize, limit: allPagination.pageSize }
    if (allStatusFilter.value) params.status = allStatusFilter.value
    if (allDomainFilter.value) params.domain_id = allDomainFilter.value
    const res = await request.get('/v1/knowledge-sharing/my-contributions', { params })
    allList.value = res.data.data.items
    allPagination.total = res.data.data.total
  } catch {} finally { allLoading.value = false }
}

async function handleApprove(id: number) {
  try {
    await request.post(`/v1/knowledge-sharing/${id}/approve`, { comment: '' })
    message.success('已通过')
    loadPendingList()
    loadStats()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '操作失败')
  }
}

async function handleReject() {
  if (!rejectTarget.value) return
  rejectLoading.value = true
  try {
    await request.post(`/v1/knowledge-sharing/${rejectTarget.value.id}/reject`, {
      comment: rejectComment.value,
    })
    message.success('已拒绝')
    rejectVisible.value = false
    loadPendingList()
    loadStats()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '操作失败')
  } finally { rejectLoading.value = false }
}

function handleTabChange(key: string) {
  if (key === 'pending') loadPendingList()
  else if (key === 'domain-pool') loadDomainPool()
  else if (key === 'all') loadAllContributions()
}

// table change handlers removed — standalone a-pagination handles page changes

onMounted(() => {
  loadStats()
  loadDomains()
  loadPendingList()
})
</script>

<style scoped>
.knowledge-sharing { padding: 0; }
.list-card-container { display: flex; flex-direction: column; gap: 10px; }
</style>
