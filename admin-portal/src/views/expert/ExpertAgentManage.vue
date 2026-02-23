<template>
  <div class="expert-agent-manage">
    <a-page-header title="我的 Agent" sub-title="管理自定义 Agent 模板与路由">
      <template #extra>
        <a-button type="primary" @click="showCreateModal = true">创建 Agent</a-button>
      </template>
    </a-page-header>

    <!-- 租户选择 (如果有多个) -->
    <a-alert v-if="!tenantId" type="warning" message="未检测到租户信息, 请先在专家租户管理中创建租户" show-icon style="margin-bottom: 16px" />

    <!-- 发现更多 Agent 入口 -->
    <a-card v-if="tenantId" style="margin-bottom: 16px; background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); border-color: #BFDBFE" :bordered="true" size="small">
      <div style="display: flex; align-items: center; justify-content: space-between">
        <div>
          <div style="font-weight: 600; font-size: 14px; color: #1E40AF">发现更多 Agent</div>
          <div style="font-size: 12px; color: #6B7280; margin-top: 2px">浏览同领域专家分享的 Agent 模板</div>
        </div>
        <a-button type="primary" ghost size="small" @click="$router.push('/admin/agent-ecosystem')">
          去市场看看 →
        </a-button>
      </div>
    </a-card>

    <!-- Agent 列表 -->
    <a-spin :spinning="loading">
      <div class="list-card-container">
        <a-empty v-if="agents.length === 0 && !loading" description="暂无 Agent" />
        <ListCard v-for="record in agents" :key="record.agent_id">
          <template #title>
            <span style="font-weight: 600">{{ record.display_name }}</span>
            <a-tag v-if="record.is_preset" color="blue" size="small" style="margin-left: 8px">预置</a-tag>
            <a-tag v-else color="green" size="small" style="margin-left: 8px">自建</a-tag>
            <span style="color: #999; font-size: 12px; margin-left: 8px">{{ record.agent_id }}</span>
          </template>
          <template #subtitle>
            <span style="color: #666; font-size: 12px">优先级: {{ record.priority }} · 类型: {{ record.agent_type }}</span>
          </template>
          <template #meta>
            <a-tag v-for="kw in (record.custom_keywords || []).slice(0, 5)" :key="kw" size="small">{{ kw }}</a-tag>
            <span v-if="(record.custom_keywords || []).length > 5" style="color: #999">+{{ record.custom_keywords.length - 5 }}</span>
          </template>
          <template #actions>
            <a-switch :checked="record.is_enabled" :disabled="record.agent_id === 'crisis'" @change="handleToggle(record)" :loading="toggleLoading === record.agent_id" />
            <a-button size="small" @click="openEdit(record)">编辑</a-button>
            <a-button v-if="!record.is_preset" size="small" danger @click="handleDelete(record)">删除</a-button>
          </template>
        </ListCard>
      </div>
    </a-spin>

    <!-- 路由测试面板 -->
    <a-card title="路由测试" style="margin-top: 24px" v-if="tenantId">
      <a-input-search
        v-model:value="testMessage"
        placeholder="输入测试消息, 查看路由结果..."
        enter-button="测试"
        :loading="testLoading"
        @search="handleTestRouting"
        style="max-width: 600px"
      />
      <div v-if="testResult" style="margin-top: 16px">
        <a-descriptions :column="1" bordered size="small">
          <a-descriptions-item label="平台默认路由">
            <a-tag v-for="r in testResult.platform_route" :key="r" color="default">{{ r }}</a-tag>
            <span v-if="!testResult.platform_route?.length" style="color: #999">无匹配</span>
          </a-descriptions-item>
          <a-descriptions-item label="租户定制路由">
            <a-tag v-for="r in testResult.tenant_route" :key="r" color="blue">{{ r }}</a-tag>
            <span v-if="!testResult.tenant_route?.length" style="color: #999">无匹配</span>
          </a-descriptions-item>
        </a-descriptions>
      </div>
    </a-card>

    <!-- 创建弹窗 -->
    <a-modal
      v-model:open="showCreateModal"
      title="创建自定义 Agent"
      @ok="handleCreate"
      :confirm-loading="createLoading"
      width="640px"
    >
      <a-form layout="vertical">
        <a-form-item label="Agent 后缀名" required>
          <a-input v-model:value="createForm.name_suffix" placeholder="如 gut_health (小写字母开头, 3-20位)" />
          <div style="color: #999; font-size: 12px; margin-top: 4px">
            最终 ID: {{ tenantSlug }}_{{ createForm.name_suffix || '...' }}
          </div>
        </a-form-item>
        <a-form-item label="显示名称" required>
          <a-input v-model:value="createForm.display_name" placeholder="如: 肠道健康Agent" />
        </a-form-item>
        <a-form-item label="描述">
          <a-input v-model:value="createForm.description" placeholder="简要描述 Agent 的职责" />
        </a-form-item>
        <a-form-item label="系统提示词">
          <a-textarea v-model:value="createForm.system_prompt" :rows="4" placeholder="指导 Agent 行为的系统提示词" />
        </a-form-item>
        <a-form-item label="路由关键词">
          <a-select
            v-model:value="createForm.keywords"
            mode="tags"
            placeholder="输入后按 Enter 添加"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="关联 Agent">
          <a-select
            v-model:value="createForm.correlations"
            mode="multiple"
            placeholder="选择关联的 Agent"
            :options="correlationOptions"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="优先级">
          <a-slider v-model:value="createForm.priority" :min="1" :max="10" :marks="{ 1: '低', 5: '中', 10: '高' }" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 编辑弹窗 -->
    <a-modal
      v-model:open="showEditModal"
      title="编辑 Agent"
      @ok="handleUpdate"
      :confirm-loading="updateLoading"
      width="640px"
    >
      <a-form layout="vertical">
        <a-form-item label="Agent ID">
          <a-input :value="editForm.agent_id" disabled />
        </a-form-item>
        <a-form-item label="显示名称">
          <a-input v-model:value="editForm.display_name" />
        </a-form-item>
        <a-form-item label="描述">
          <a-input v-model:value="editForm.description" />
        </a-form-item>
        <a-form-item label="系统提示词" v-if="!editForm.is_preset">
          <a-textarea v-model:value="editForm.system_prompt" :rows="4" />
        </a-form-item>
        <a-form-item v-if="editForm.is_preset" label="系统提示词">
          <a-alert type="info" message="预置 Agent 不可修改系统提示词" />
        </a-form-item>
        <a-form-item label="路由关键词">
          <a-select
            v-model:value="editForm.keywords"
            mode="tags"
            placeholder="输入后按 Enter 添加"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="关联 Agent">
          <a-select
            v-model:value="editForm.correlations"
            mode="multiple"
            :options="correlationOptions"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="优先级">
          <a-slider v-model:value="editForm.priority" :min="1" :max="10" :marks="{ 1: '低', 5: '中', 10: '高' }" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import request from '../../api/request'
import ListCard from '@/components/core/ListCard.vue'

// 租户 ID (从用户关联信息获取)
const tenantId = ref('')
const tenantSlug = computed(() => {
  return tenantId.value.replace(/[^a-z0-9]/g, '').slice(0, 16) || '...'
})

const loading = ref(false)
const agents = ref<any[]>([])

// columns removed — using ListCard layout

const correlationOptions = computed(() => {
  return agents.value.map(a => ({ label: a.display_name, value: a.agent_id }))
})

// 创建表单
const showCreateModal = ref(false)
const createLoading = ref(false)
const createForm = ref({
  name_suffix: '',
  display_name: '',
  description: '',
  system_prompt: '',
  keywords: [] as string[],
  correlations: [] as string[],
  priority: 5,
})

// 编辑表单
const showEditModal = ref(false)
const updateLoading = ref(false)
const editForm = ref({
  agent_id: '',
  display_name: '',
  description: '',
  system_prompt: '',
  keywords: [] as string[],
  correlations: [] as string[],
  priority: 5,
  is_preset: false,
})

// Toggle
const toggleLoading = ref('')

// 路由测试
const testMessage = ref('')
const testLoading = ref(false)
const testResult = ref<any>(null)

// 获取当前用户的租户 ID
async function detectTenant() {
  try {
    const res = await request.get('v1/tenants/mine')
    if (res.data?.data?.id) {
      tenantId.value = res.data.data.id
    } else if (res.data?.id) {
      tenantId.value = res.data.id
    }
  } catch {
    // 尝试从用户信息推断
    try {
      const res = await request.get('v1/tenants')
      const tenants = res.data?.data || res.data || []
      if (tenants.length > 0) {
        tenantId.value = tenants[0].id
      }
    } catch {
      // 无租户
    }
  }
}

async function fetchAgents() {
  if (!tenantId.value) return
  loading.value = true
  try {
    const res = await request.get(`v1/tenants/${tenantId.value}/my-agents`)
    agents.value = res.data?.data || []
  } catch (e) {
    console.error('加载 Agent 列表失败', e)
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!createForm.value.name_suffix || !createForm.value.display_name) {
    message.warning('请填写必填项')
    return
  }
  createLoading.value = true
  try {
    await request.post(`v1/tenants/${tenantId.value}/my-agents`, createForm.value)
    message.success('Agent 创建成功')
    showCreateModal.value = false
    createForm.value = { name_suffix: '', display_name: '', description: '', system_prompt: '', keywords: [], correlations: [], priority: 5 }
    await fetchAgents()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '创建失败')
  } finally {
    createLoading.value = false
  }
}

function openEdit(record: any) {
  editForm.value = {
    agent_id: record.agent_id,
    display_name: record.display_name,
    description: record.description || '',
    system_prompt: record.system_prompt || '',
    keywords: [...(record.custom_keywords || [])],
    correlations: [...(record.correlations || [])],
    priority: record.priority || 5,
    is_preset: record.is_preset,
  }
  showEditModal.value = true
}

async function handleUpdate() {
  updateLoading.value = true
  try {
    const payload: any = {
      display_name: editForm.value.display_name,
      keywords: editForm.value.keywords,
      correlations: editForm.value.correlations,
      priority: editForm.value.priority,
      description: editForm.value.description,
    }
    if (!editForm.value.is_preset) {
      payload.system_prompt = editForm.value.system_prompt
    }
    await request.put(`v1/tenants/${tenantId.value}/my-agents/${editForm.value.agent_id}`, payload)
    message.success('更新成功')
    showEditModal.value = false
    await fetchAgents()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '更新失败')
  } finally {
    updateLoading.value = false
  }
}

async function handleToggle(record: any) {
  toggleLoading.value = record.agent_id
  try {
    await request.post(`v1/tenants/${tenantId.value}/my-agents/${record.agent_id}/toggle`)
    message.success(record.is_enabled ? '已停用' : '已启用')
    await fetchAgents()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '操作失败')
  } finally {
    toggleLoading.value = ''
  }
}

function handleDelete(record: any) {
  Modal.confirm({
    title: `确认删除 Agent "${record.display_name}"?`,
    content: '删除后不可恢复',
    okText: '删除',
    okType: 'danger',
    onOk: async () => {
      try {
        await request.delete(`v1/tenants/${tenantId.value}/my-agents/${record.agent_id}`)
        message.success('已删除')
        await fetchAgents()
      } catch (e: any) {
        message.error(e.response?.data?.detail || '删除失败')
      }
    },
  })
}

async function handleTestRouting() {
  if (!testMessage.value.trim()) return
  testLoading.value = true
  testResult.value = null
  try {
    const res = await request.post(`v1/tenants/${tenantId.value}/my-agents/test-routing`, {
      message: testMessage.value,
    })
    testResult.value = res.data?.data || {}
  } catch (e: any) {
    message.error(e.response?.data?.detail || '测试失败')
  } finally {
    testLoading.value = false
  }
}

onMounted(async () => {
  await detectTenant()
  if (tenantId.value) {
    await fetchAgents()
  }
})
</script>

<style scoped>
.expert-agent-manage {
  padding: 0;
}

.list-card-container { display: flex; flex-direction: column; gap: 10px; }
</style>
