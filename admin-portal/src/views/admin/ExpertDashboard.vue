<!--
  专家管理面板 — 专家的工作台
  路由: /expert/dashboard/:tenantId
-->
<template>
  <div class="expert-dashboard">
    <a-page-header title="专家工作室管理" @back="$router.back()" style="padding: 0 0 16px" />
    <!-- 顶部信息 -->
    <div class="dash-header" v-if="tenant">
      <span class="dash-avatar">{{ tenant.brand_avatar }}</span>
      <div>
        <h2 class="dash-name">{{ tenant.brand_name }}</h2>
        <a-tag :color="statusColor">{{ statusLabel }}</a-tag>
        <a-tag>{{ tierLabel }}</a-tag>
      </div>
      <a-button type="primary" ghost size="small" @click="previewStudio" style="margin-left:auto">
        预览工作室
      </a-button>
    </div>

    <a-spin :spinning="loading" size="large">
      <a-tabs v-model:activeKey="activeTab" type="card" style="margin-top:16px">
        <!-- 概览 Tab -->
        <a-tab-pane key="overview" tab="概览">
          <a-row :gutter="16" style="margin-bottom:24px">
            <a-col :xs="24" :sm="12" :lg="6">
              <a-statistic title="服务中客户" :value="stats?.clients.active || 0" />
            </a-col>
            <a-col :xs="24" :sm="12" :lg="6">
              <a-statistic title="已毕业" :value="stats?.clients.graduated || 0" />
            </a-col>
            <a-col :xs="24" :sm="12" :lg="6">
              <a-statistic title="本月新增" :value="stats?.new_this_month || 0" />
            </a-col>
            <a-col :xs="24" :sm="12" :lg="6">
              <a-statistic title="启用 Agent" :value="(tenant?.enabled_agents || []).length" />
            </a-col>
          </a-row>

          <div style="margin-bottom:16px">
            <a-button type="primary" @click="goContentStudio">内容管理</a-button>
          </div>

          <a-descriptions bordered :column="2" size="small" v-if="tenant">
            <a-descriptions-item label="合作等级">{{ tierLabel }}</a-descriptions-item>
            <a-descriptions-item label="客户上限">{{ tenant.max_clients }}</a-descriptions-item>
            <a-descriptions-item label="分成比例">{{ Math.round((tenant.revenue_share_expert || 0.8) * 100) }}%</a-descriptions-item>
            <a-descriptions-item label="创建时间">{{ formatDate(tenant.created_at) }}</a-descriptions-item>
          </a-descriptions>
        </a-tab-pane>

        <!-- 客户管理 Tab -->
        <a-tab-pane key="clients" tab="客户管理">
          <div style="margin-bottom:16px;display:flex;gap:8px">
            <a-button
              v-for="f in clientFilters"
              :key="f.value"
              :type="clientFilter === f.value ? 'primary' : 'default'"
              size="small"
              @click="onClientFilter(f.value)"
            >
              {{ f.label }}
            </a-button>
          </div>

          <a-table
            :dataSource="clients"
            :columns="clientColumns"
            :pagination="false"
            :loading="clientsLoading"
            rowKey="id"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-tag :color="clientStatusColor(record.status)">
                  {{ clientStatusLabel(record.status) }}
                </a-tag>
              </template>
              <template v-if="column.key === 'enrolled_at'">
                {{ formatDate(record.enrolled_at) }}
              </template>
            </template>
          </a-table>
        </a-tab-pane>

        <!-- Agent 配置 Tab -->
        <a-tab-pane key="agents" tab="AI助手配置">
          <p style="color:#999;margin-bottom:16px">管理您工作室的 AI 助手团队。危机干预助手始终启用，不可关闭。</p>

          <div class="agent-config-list">
            <div
              v-for="agent in allAgentsConfig"
              :key="agent.id"
              class="agent-config-card"
              :class="{ disabled: !agent.enabled, locked: agent.locked }"
            >
              <div class="ac-left">
                <span class="ac-avatar">{{ agent.avatar }}</span>
                <div>
                  <span class="ac-name">{{ agent.name }}</span>
                  <span class="ac-category">{{ agent.category }}</span>
                </div>
              </div>
              <div v-if="agent.locked" style="color:#d97706;font-size:12px">🔒 始终启用</div>
              <a-switch v-else :checked="agent.enabled" size="small" @change="toggleAgent(agent.id)" />
            </div>
          </div>
        </a-tab-pane>

        <!-- 品牌设置 Tab -->
        <a-tab-pane key="brand" tab="品牌设置">
          <a-form layout="vertical" style="max-width:480px">
            <a-form-item label="工作室名称">
              <a-input v-model:value="brandForm.brand_name" />
            </a-form-item>
            <a-form-item label="品牌标语">
              <a-input v-model:value="brandForm.brand_tagline" />
            </a-form-item>
            <a-form-item label="Emoji 头像">
              <a-input v-model:value="brandForm.brand_avatar" style="width:100px" :maxlength="4" />
            </a-form-item>
            <a-form-item label="主色调">
              <div style="display:flex;gap:10px;align-items:center">
                <input type="color" v-model="brandForm.primary" style="width:40px;height:34px;border:none;cursor:pointer;border-radius:6px" />
                <a-input v-model:value="brandForm.primary" style="width:120px" />
              </div>
            </a-form-item>
            <a-form-item label="强调色">
              <div style="display:flex;gap:10px;align-items:center">
                <input type="color" v-model="brandForm.accent" style="width:40px;height:34px;border:none;cursor:pointer;border-radius:6px" />
                <a-input v-model:value="brandForm.accent" style="width:120px" />
              </div>
            </a-form-item>
            <a-form-item label="欢迎语">
              <a-textarea v-model:value="brandForm.welcome_message" :rows="3" />
            </a-form-item>
            <a-form-item>
              <a-button type="primary" @click="saveBrand">保存品牌设置</a-button>
            </a-form-item>
          </a-form>
        </a-tab-pane>
      </a-tabs>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import api from '../../api/request'
import { AGENT_META } from './expertAgentMeta'

const route = useRoute()
const router = useRouter()
const tenantId = route.params.tenantId as string

const tenant = ref<any>(null)
const clients = ref<any[]>([])
const stats = ref<any>(null)
const loading = ref(false)
const clientsLoading = ref(false)
const activeTab = ref('overview')
const clientFilter = ref('')

const API_BASE = '/v1/tenants'

// --- 加载数据 ---
async function loadTenant() {
  loading.value = true
  try {
    const res = await api.get(`${API_BASE}/${tenantId}`)
    if (res.data?.success) tenant.value = res.data.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadClients(status?: string) {
  clientsLoading.value = true
  try {
    const params: any = {}
    if (status) params.status = status
    const res = await api.get(`${API_BASE}/${tenantId}/clients`, { params })
    if (res.data?.success) clients.value = res.data.data
  } catch (e) {
    console.error(e)
  } finally {
    clientsLoading.value = false
  }
}

async function loadStats() {
  try {
    const res = await api.get(`${API_BASE}/${tenantId}/stats`)
    if (res.data?.success) stats.value = res.data.data
  } catch (e) {
    console.error(e)
  }
}

// --- 客户筛选 ---
const clientFilters = [
  { label: '全部', value: '' },
  { label: '服务中', value: 'active' },
  { label: '已毕业', value: 'graduated' },
  { label: '已暂停', value: 'paused' },
]

const clientColumns = [
  { title: '用户ID', dataIndex: 'user_id', key: 'user_id' },
  { title: '服务包', dataIndex: 'service_package', key: 'service_package' },
  { title: '状态', key: 'status' },
  { title: '加入时间', key: 'enrolled_at' },
  { title: '会话数', dataIndex: 'total_sessions', key: 'total_sessions' },
]

function onClientFilter(val: string) {
  clientFilter.value = val
  loadClients(val || undefined)
}

function clientStatusLabel(s: string) {
  const map: Record<string, string> = { active: '服务中', graduated: '已毕业', paused: '已暂停', exited: '已退出' }
  return map[s] || s
}

function clientStatusColor(s: string) {
  const map: Record<string, string> = { active: 'green', graduated: 'blue', paused: 'orange', exited: 'red' }
  return map[s] || 'default'
}

// --- Agent 配置 ---
const allAgentsConfig = computed(() => {
  const enabled = new Set(tenant.value?.enabled_agents || [])
  return Object.entries(AGENT_META).map(([id, meta]) => ({
    id,
    name: meta.name,
    avatar: meta.avatar,
    category: meta.category,
    enabled: enabled.has(id),
    locked: id === 'crisis',
  }))
})

async function toggleAgent(agentId: string) {
  if (!tenant.value) return
  const current = new Set(tenant.value.enabled_agents || [])
  if (current.has(agentId)) current.delete(agentId)
  else current.add(agentId)
  current.add('crisis')
  try {
    const res = await api.patch(`${API_BASE}/${tenantId}`, {
      enabled_agents: [...current],
    })
    if (res.data?.success) {
      tenant.value = res.data.data
      message.success('Agent 配置已更新')
    }
  } catch (e) {
    message.error('更新失败')
  }
}

// --- 品牌设置 ---
const brandForm = reactive({
  brand_name: '',
  brand_tagline: '',
  brand_avatar: '',
  primary: '#2563EB',
  accent: '#F59E0B',
  welcome_message: '',
})

watch(tenant, (t) => {
  if (t) {
    brandForm.brand_name = t.brand_name
    brandForm.brand_tagline = t.brand_tagline || ''
    brandForm.brand_avatar = t.brand_avatar || ''
    brandForm.primary = t.brand_colors?.primary || '#2563EB'
    brandForm.accent = t.brand_colors?.accent || '#F59E0B'
    brandForm.welcome_message = t.welcome_message || ''
  }
}, { immediate: true })

async function saveBrand() {
  try {
    const res = await api.patch(`${API_BASE}/${tenantId}`, {
      brand_name: brandForm.brand_name,
      brand_tagline: brandForm.brand_tagline,
      brand_avatar: brandForm.brand_avatar,
      brand_colors: {
        primary: brandForm.primary,
        accent: brandForm.accent,
        bg: tenant.value?.brand_colors?.bg || '#F8FAFC',
        text: tenant.value?.brand_colors?.text || '#1E293B',
      },
      welcome_message: brandForm.welcome_message,
    })
    if (res.data?.success) {
      tenant.value = res.data.data
      message.success('品牌设置已保存')
    }
  } catch (e) {
    message.error('保存失败')
  }
}

// --- 工具 ---
const statusLabel = computed(() => {
  const map: Record<string, string> = { active: '运营中', trial: '试用期', suspended: '已暂停', archived: '已归档' }
  return map[tenant.value?.status || ''] || tenant.value?.status
})

const statusColor = computed(() => {
  const map: Record<string, string> = { active: 'green', trial: 'orange', suspended: 'red', archived: 'default' }
  return map[tenant.value?.status || ''] || 'default'
})

const tierLabel = computed(() => {
  const map: Record<string, string> = {
    basic_partner: '基础合作',
    premium_partner: '高级合作',
    strategic_partner: '战略合作',
  }
  return map[tenant.value?.tier || ''] || tenant.value?.tier
})

function formatDate(d: string) {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('zh-CN')
}

function previewStudio() {
  window.open(`/studio/${tenantId}`, '_blank')
}

function goContentStudio() {
  router.push({ name: 'ExpertContentStudio', params: { tenantId } })
}

onMounted(() => {
  loadTenant()
  loadClients()
  loadStats()
})
</script>

<style scoped>
.expert-dashboard {
  padding: 24px;
}

.dash-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 8px;
}

.dash-avatar { font-size: 36px; }
.dash-name { font-size: 20px; font-weight: 600; margin-bottom: 4px; }

.agent-config-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.agent-config-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
}

.agent-config-card.disabled { opacity: 0.5; }
.agent-config-card.locked { border-color: #fde68a; background: #fffbeb; }

.ac-left { display: flex; align-items: center; gap: 12px; }
.ac-avatar { font-size: 24px; }
.ac-name { font-size: 14px; font-weight: 500; display: block; }
.ac-category { font-size: 12px; color: #999; }
</style>
