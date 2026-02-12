<template>
  <div class="agent-marketplace">
    <a-page-header title="Agent 生态" sub-title="模板市场、组合编排、成长积分" />

    <a-tabs v-model:activeKey="activeTab" @change="handleTabChange">
      <!-- 模板市场 -->
      <a-tab-pane key="marketplace" tab="模板市场">
        <div style="margin-bottom: 16px">
          <a-input-search v-model:value="searchText" placeholder="搜索模板..." style="width: 300px; margin-right: 8px" @search="loadMarketplace" />
          <a-select v-model:value="categoryFilter" placeholder="分类" allowClear style="width: 150px" @change="loadMarketplace">
            <a-select-option value="health">健康管理</a-select-option>
            <a-select-option value="nutrition">营养</a-select-option>
            <a-select-option value="mental">心理</a-select-option>
            <a-select-option value="exercise">运动</a-select-option>
            <a-select-option value="tcm">中医</a-select-option>
          </a-select>
        </div>
        <a-table
          :dataSource="marketplaceList"
          :columns="marketplaceColumns"
          :loading="marketplaceLoading"
          :pagination="marketplacePagination"
          @change="handleMarketplaceTableChange"
          rowKey="id"
          size="middle"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'tags'">
              <a-tag v-for="t in (record.tags || [])" :key="t" size="small">{{ t }}</a-tag>
            </template>
            <template v-if="column.key === 'status'">
              <a-tag :color="statusColor(record.status)">{{ statusLabel(record.status) }}</a-tag>
            </template>
          </template>
        </a-table>
      </a-tab-pane>

      <!-- 待审核 -->
      <a-tab-pane key="pending" tab="待审核" v-if="isAdmin">
        <a-table
          :dataSource="pendingList"
          :columns="pendingColumns"
          :loading="pendingLoading"
          rowKey="id"
          size="middle"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'action'">
              <a-space>
                <a-popconfirm title="确认通过?" @confirm="handleApproveListing(record.id)">
                  <a-button type="link" size="small" style="color: #52c41a">通过</a-button>
                </a-popconfirm>
                <a-popconfirm title="确认拒绝?" @confirm="handleRejectListing(record.id)">
                  <a-button type="link" size="small" danger>拒绝</a-button>
                </a-popconfirm>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-tab-pane>

      <!-- 组合编排 -->
      <a-tab-pane key="compositions" tab="组合编排">
        <div style="margin-bottom: 16px">
          <a-button type="primary" @click="showCompositionCreate = true">创建组合</a-button>
        </div>
        <a-table
          :dataSource="compositionList"
          :columns="compositionColumns"
          :loading="compositionLoading"
          rowKey="id"
          size="middle"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'pipeline'">
              <a-tag v-for="step in (record.pipeline || [])" :key="step.agent_id" color="blue">
                {{ step.order }}. {{ step.agent_id }}
              </a-tag>
            </template>
            <template v-if="column.key === 'is_enabled'">
              <a-tag :color="record.is_enabled ? 'green' : 'default'">{{ record.is_enabled ? '启用' : '停用' }}</a-tag>
            </template>
          </template>
        </a-table>
      </a-tab-pane>

      <!-- 成长积分 -->
      <a-tab-pane key="growth" tab="成长积分">
        <a-row :gutter="16" style="margin-bottom: 16px">
          <a-col :span="8">
            <a-statistic title="我的总积分" :value="growthData.total_points || 0" :value-style="{ color: '#1890ff' }" />
          </a-col>
        </a-row>
        <a-descriptions title="积分来源" :column="2" bordered size="small" style="margin-bottom: 16px">
          <a-descriptions-item v-for="(pts, evt) in (growthData.by_event || {})" :key="evt" :label="eventLabel(evt)">
            {{ pts }} 分
          </a-descriptions-item>
        </a-descriptions>
        <a-card title="积分事件配置" :bordered="false" size="small">
          <a-table :dataSource="pointsConfig" :columns="configColumns" :pagination="false" rowKey="event_type" size="small" />
        </a-card>
      </a-tab-pane>
    </a-tabs>

    <!-- 创建组合弹窗 -->
    <a-modal v-model:open="showCompositionCreate" title="创建 Agent 组合" @ok="handleCreateComposition" :confirmLoading="compositionCreating" width="600px">
      <a-form layout="vertical">
        <a-form-item label="名称">
          <a-input v-model:value="compositionForm.name" placeholder="例: 代谢综合评估" />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="compositionForm.description" :rows="2" />
        </a-form-item>
        <a-form-item label="合并策略">
          <a-select v-model:value="compositionForm.merge_strategy" style="width: 200px">
            <a-select-option value="weighted_average">加权平均</a-select-option>
            <a-select-option value="priority_first">优先级优先</a-select-option>
            <a-select-option value="consensus">共识决策</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="流水线 (JSON)">
          <a-textarea v-model:value="pipelineJson" :rows="6" style="font-family: monospace" placeholder='[{"agent_id": "glucose", "order": 1, "condition": "always"}]' />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import request from '../../api/request'

const activeTab = ref('marketplace')
const isAdmin = computed(() => {
  try {
    const token = localStorage.getItem('admin_token')
    if (!token) return false
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.role === 'admin'
  } catch { return false }
})

// Marketplace
const marketplaceLoading = ref(false)
const marketplaceList = ref<any[]>([])
const marketplacePagination = reactive({ current: 1, pageSize: 20, total: 0 })
const searchText = ref('')
const categoryFilter = ref<string | undefined>(undefined)

// Pending
const pendingLoading = ref(false)
const pendingList = ref<any[]>([])

// Compositions
const compositionLoading = ref(false)
const compositionList = ref<any[]>([])
const showCompositionCreate = ref(false)
const compositionCreating = ref(false)
const compositionForm = reactive({ name: '', description: '', merge_strategy: 'weighted_average' })
const pipelineJson = ref('[]')

// Growth
const growthData = ref<any>({})
const pointsConfig = ref<any[]>([])

const marketplaceColumns = [
  { title: 'ID', dataIndex: 'id', width: 50 },
  { title: '标题', dataIndex: 'title', ellipsis: true },
  { title: '分类', dataIndex: 'category', width: 80 },
  { title: '标签', key: 'tags', width: 200 },
  { title: '安装数', dataIndex: 'install_count', width: 70 },
  { title: '状态', key: 'status', width: 80 },
  { title: '发布时间', dataIndex: 'created_at', width: 150 },
]

const pendingColumns = [
  { title: 'ID', dataIndex: 'id', width: 50 },
  { title: '标题', dataIndex: 'title', ellipsis: true },
  { title: '租户', dataIndex: 'tenant_id', width: 140 },
  { title: '分类', dataIndex: 'category', width: 80 },
  { title: '时间', dataIndex: 'created_at', width: 150 },
  { title: '操作', key: 'action', width: 130 },
]

const compositionColumns = [
  { title: 'ID', dataIndex: 'id', width: 50 },
  { title: '名称', dataIndex: 'name', width: 140 },
  { title: '描述', dataIndex: 'description', ellipsis: true },
  { title: '流水线', key: 'pipeline', width: 300 },
  { title: '策略', dataIndex: 'merge_strategy', width: 120 },
  { title: '状态', key: 'is_enabled', width: 70 },
]

const configColumns = [
  { title: '事件类型', dataIndex: 'event_type' },
  { title: '积分值', dataIndex: 'points' },
]

function statusColor(s: string) {
  return { draft: 'default', submitted: 'orange', approved: 'blue', published: 'green', rejected: 'red', archived: 'gray' }[s] || 'default'
}
function statusLabel(s: string) {
  return { draft: '草稿', submitted: '待审核', approved: '已通过', published: '已发布', rejected: '已拒绝', archived: '已下架' }[s] || s
}
function eventLabel(e: string) {
  const labels: Record<string, string> = {
    create_agent: '创建Agent', optimize_prompt: '优化Prompt', share_knowledge: '共享知识',
    template_published: '发布模板', template_installed: '模板被安装', feedback_positive: '正面反馈',
    composition_created: '创建组合',
  }
  return labels[e] || e
}

async function loadMarketplace() {
  marketplaceLoading.value = true
  try {
    const params: any = { skip: (marketplacePagination.current - 1) * marketplacePagination.pageSize, limit: marketplacePagination.pageSize }
    if (searchText.value) params.search = searchText.value
    if (categoryFilter.value) params.category = categoryFilter.value
    const res = await request.get('/v1/agent-ecosystem/marketplace', { params })
    marketplaceList.value = res.data.data?.items || []
    marketplacePagination.total = res.data.data?.total || 0
  } catch {} finally { marketplaceLoading.value = false }
}

async function loadPending() {
  pendingLoading.value = true
  try {
    const res = await request.get('/v1/agent-ecosystem/marketplace/pending')
    pendingList.value = res.data.data?.items || []
  } catch {} finally { pendingLoading.value = false }
}

async function loadCompositions() {
  compositionLoading.value = true
  try {
    const res = await request.get('/v1/agent-ecosystem/compositions')
    compositionList.value = res.data.data?.items || []
  } catch {} finally { compositionLoading.value = false }
}

async function loadGrowth() {
  try {
    const [gpRes, cfgRes] = await Promise.all([
      request.get('/v1/agent-ecosystem/growth-points'),
      request.get('/v1/agent-ecosystem/growth-points/config'),
    ])
    growthData.value = gpRes.data.data || {}
    pointsConfig.value = cfgRes.data.data || []
  } catch {}
}

async function handleApproveListing(id: number) {
  try {
    await request.post(`/v1/agent-ecosystem/marketplace/${id}/approve`, { comment: '' })
    message.success('已通过')
    loadPending()
  } catch (e: any) { message.error(e?.response?.data?.detail || '操作失败') }
}

async function handleRejectListing(id: number) {
  try {
    await request.post(`/v1/agent-ecosystem/marketplace/${id}/reject`, { comment: '' })
    message.success('已拒绝')
    loadPending()
  } catch (e: any) { message.error(e?.response?.data?.detail || '操作失败') }
}

async function handleCreateComposition() {
  compositionCreating.value = true
  try {
    const pipeline = JSON.parse(pipelineJson.value)
    await request.post('/v1/agent-ecosystem/compositions', {
      ...compositionForm,
      pipeline,
    })
    message.success('组合已创建')
    showCompositionCreate.value = false
    loadCompositions()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '创建失败')
  } finally { compositionCreating.value = false }
}

function handleTabChange(key: string) {
  if (key === 'marketplace') loadMarketplace()
  else if (key === 'pending') loadPending()
  else if (key === 'compositions') loadCompositions()
  else if (key === 'growth') loadGrowth()
}

function handleMarketplaceTableChange(p: any) {
  marketplacePagination.current = p.current
  loadMarketplace()
}

onMounted(() => {
  loadMarketplace()
})
</script>

<style scoped>
.agent-marketplace { padding: 0; }
</style>
