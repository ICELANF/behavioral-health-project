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
        <a-spin :spinning="marketplaceLoading">
          <div class="list-card-container">
            <a-empty v-if="marketplaceList.length === 0 && !marketplaceLoading" description="暂无模板" />
            <ListCard v-for="record in marketplaceList" :key="record.id">
              <template #title>{{ record.title }}</template>
              <template #subtitle>
                <a-tag size="small">{{ record.category }}</a-tag>
                <a-tag :color="statusColor(record.status)" size="small">{{ statusLabel(record.status) }}</a-tag>
                <span style="color: #999; font-size: 12px">安装 {{ record.install_count }} 次</span>
              </template>
              <template #meta>
                <a-tag v-for="t in (record.tags || []).slice(0,4)" :key="t" size="small">{{ t }}</a-tag>
                <span style="color: #999; font-size: 12px">{{ record.created_at }}</span>
              </template>
              <template #actions>
                <a-popconfirm v-if="myTenantId && record.status === 'published'" :title="`安装 '${record.title}'?`" @confirm="handleInstallTemplate(record.id)">
                  <a-button type="link" size="small" :loading="installingId === record.id">安装</a-button>
                </a-popconfirm>
                <span v-else-if="!myTenantId" style="color: #999; font-size: 12px">无租户</span>
              </template>
            </ListCard>
          </div>
        </a-spin>
        <div style="display: flex; justify-content: flex-end; margin-top: 16px">
          <a-pagination v-model:current="marketplacePagination.current" :page-size="marketplacePagination.pageSize" :total="marketplacePagination.total" @change="() => loadMarketplace()" />
        </div>
      </a-tab-pane>

      <!-- 待审核 -->
      <a-tab-pane key="pending" tab="待审核" v-if="isAdmin">
        <a-spin :spinning="pendingLoading">
          <div class="list-card-container">
            <a-empty v-if="pendingList.length === 0 && !pendingLoading" description="暂无待审核" />
            <ListCard v-for="record in pendingList" :key="record.id">
              <template #title>
                <span>{{ record.title }}</span>
                <a-tag size="small" style="margin-left: 8px">{{ record.category }}</a-tag>
              </template>
              <template #subtitle>
                <span style="color: #666; font-size: 12px">租户: {{ record.tenant_id }}</span>
                <span style="color: #999; font-size: 12px; margin-left: 8px">{{ record.created_at }}</span>
              </template>
              <template #actions>
                <a-popconfirm title="确认通过?" @confirm="handleApproveListing(record.id)">
                  <a-button type="link" size="small" style="color: #52c41a">通过</a-button>
                </a-popconfirm>
                <a-popconfirm title="确认拒绝?" @confirm="handleRejectListing(record.id)">
                  <a-button type="link" size="small" danger>拒绝</a-button>
                </a-popconfirm>
              </template>
            </ListCard>
          </div>
        </a-spin>
      </a-tab-pane>

      <!-- 组合编排 -->
      <a-tab-pane key="compositions" tab="组合编排">
        <div style="margin-bottom: 16px">
          <a-button type="primary" @click="showCompositionCreate = true">创建组合</a-button>
        </div>
        <a-spin :spinning="compositionLoading">
          <div class="list-card-container">
            <a-empty v-if="compositionList.length === 0 && !compositionLoading" description="暂无组合" />
            <ListCard v-for="record in compositionList" :key="record.id">
              <template #title>
                <span>{{ record.name }}</span>
                <a-tag :color="record.is_enabled ? 'green' : 'default'" size="small" style="margin-left: 8px">{{ record.is_enabled ? '启用' : '停用' }}</a-tag>
              </template>
              <template #subtitle>
                <span style="color: #666">{{ record.description }}</span>
                <span style="color: #999; font-size: 12px; margin-left: 8px">策略: {{ record.merge_strategy }}</span>
              </template>
              <template #meta>
                <a-tag v-for="step in (record.pipeline || [])" :key="step.agent_id" color="blue" size="small">
                  {{ step.order }}. {{ step.agent_id }}
                </a-tag>
              </template>
            </ListCard>
          </div>
        </a-spin>
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
import ListCard from '@/components/core/ListCard.vue'

const activeTab = ref('marketplace')
// 使用 localStorage 存储的角色信息判断 (由 auth store 登录时写入), 不解码 JWT
const isAdmin = computed(() => {
  const role = (localStorage.getItem('admin_role') || '').toUpperCase()
  return role === 'ADMIN'
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

// 我的租户
const myTenantId = ref('')

// marketplaceColumns removed — using ListCard layout

// pendingColumns + compositionColumns removed — using ListCard layout

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
    let pipeline: any
    try {
      pipeline = JSON.parse(pipelineJson.value)
    } catch {
      message.error('Pipeline JSON 格式无效，请检查后重试')
      compositionCreating.value = false
      return
    }
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

// 安装模板
const installingId = ref<number | null>(null)

async function handleInstallTemplate(listingId: number) {
  if (!myTenantId.value) {
    message.warning('未检测到租户信息')
    return
  }
  installingId.value = listingId
  try {
    await request.post(`/v1/agent-ecosystem/marketplace/${listingId}/install`, {
      target_tenant_id: myTenantId.value,
    })
    message.success('安装成功')
    loadMarketplace()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '安装失败')
  } finally {
    installingId.value = null
  }
}

async function detectMyTenant() {
  try {
    const res = await request.get('/v1/tenants/mine')
    myTenantId.value = res.data?.data?.id || ''
  } catch {
    myTenantId.value = ''
  }
}

function handleTabChange(key: string) {
  if (key === 'marketplace') loadMarketplace()
  else if (key === 'pending') loadPending()
  else if (key === 'compositions') loadCompositions()
  else if (key === 'growth') loadGrowth()
}

// handleMarketplaceTableChange removed — standalone a-pagination handles page changes

onMounted(() => {
  loadMarketplace()
  detectMyTenant()
})
</script>

<style scoped>
.agent-marketplace { padding: 0; }
.list-card-container { display: flex; flex-direction: column; gap: 10px; }
</style>
