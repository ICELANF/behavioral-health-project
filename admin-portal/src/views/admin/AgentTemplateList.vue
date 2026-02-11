<template>
  <div class="agent-template-list">
    <a-page-header title="Agent 模板管理" sub-title="管理预置和自定义 Agent 模板">
      <template #extra>
        <a-space>
          <a-button @click="handleRefreshCache" :loading="refreshing">
            <template #icon><ReloadOutlined /></template>
            刷新缓存
          </a-button>
          <a-button type="primary" @click="$router.push('/admin/agent-templates/create')">
            <template #icon><PlusOutlined /></template>
            创建 Agent
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <!-- 筛选 -->
    <a-card class="filter-card" :bordered="false">
      <a-space>
        <a-select v-model:value="filters.agent_type" placeholder="Agent 类型" allow-clear style="width: 160px" @change="loadData">
          <a-select-option value="specialist">specialist</a-select-option>
          <a-select-option value="integrative">integrative</a-select-option>
          <a-select-option value="dynamic_llm">dynamic_llm</a-select-option>
        </a-select>
        <a-select v-model:value="filters.is_enabled" placeholder="状态" allow-clear style="width: 120px" @change="loadData">
          <a-select-option :value="true">启用</a-select-option>
          <a-select-option :value="false">停用</a-select-option>
        </a-select>
      </a-space>
    </a-card>

    <!-- 列表 -->
    <a-card :bordered="false" style="margin-top: 16px">
      <a-table
        :dataSource="templates"
        :columns="columns"
        :loading="loading"
        :pagination="{ total, current: page, pageSize: 20, onChange: onPageChange }"
        rowKey="agent_id"
        size="middle"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'display_name'">
            <a @click="$router.push(`/admin/agent-templates/edit/${record.agent_id}`)">{{ record.display_name }}</a>
            <div style="color: #999; font-size: 12px">{{ record.agent_id }}</div>
          </template>
          <template v-if="column.key === 'agent_type'">
            <a-tag :color="typeColor(record.agent_type)">{{ record.agent_type }}</a-tag>
          </template>
          <template v-if="column.key === 'is_preset'">
            <a-tag v-if="record.is_preset" color="blue">预置</a-tag>
            <a-tag v-else color="green">自定义</a-tag>
          </template>
          <template v-if="column.key === 'is_enabled'">
            <a-switch :checked="record.is_enabled" @change="handleToggle(record)" size="small" />
          </template>
          <template v-if="column.key === 'keywords'">
            <a-tag v-for="kw in (record.keywords || []).slice(0, 3)" :key="kw" size="small">{{ kw }}</a-tag>
            <span v-if="(record.keywords || []).length > 3" style="color: #999">+{{ record.keywords.length - 3 }}</span>
          </template>
          <template v-if="column.key === 'actions'">
            <a-space>
              <a-button type="link" size="small" @click="$router.push(`/admin/agent-templates/edit/${record.agent_id}`)">编辑</a-button>
              <a-button type="link" size="small" @click="handleClone(record)">克隆</a-button>
              <a-popconfirm v-if="!record.is_preset" title="确定删除?" @confirm="handleDelete(record)">
                <a-button type="link" size="small" danger>删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 克隆对话框 -->
    <a-modal v-model:open="cloneModal.visible" title="克隆 Agent 模板" @ok="doClone" :confirmLoading="cloneModal.loading">
      <a-form layout="vertical">
        <a-form-item label="新 Agent ID">
          <a-input v-model:value="cloneModal.newId" placeholder="例: custom_fatigue" />
          <div style="color: #999; font-size: 12px; margin-top: 4px">小写字母开头, 仅含小写字母/数字/下划线, 3-32 字符</div>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { ReloadOutlined, PlusOutlined } from '@ant-design/icons-vue'
import { agentTemplateApi } from '../../api/agent-template'

const loading = ref(false)
const refreshing = ref(false)
const templates = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const filters = reactive<{ agent_type?: string; is_enabled?: boolean }>({})

const columns = [
  { title: '名称', key: 'display_name', width: 180 },
  { title: '类型', key: 'agent_type', dataIndex: 'agent_type', width: 120 },
  { title: '优先级', dataIndex: 'priority', width: 80, sorter: (a: any, b: any) => a.priority - b.priority },
  { title: '权重', dataIndex: 'base_weight', width: 80 },
  { title: '关键词', key: 'keywords', width: 200 },
  { title: '预置', key: 'is_preset', width: 80 },
  { title: '状态', key: 'is_enabled', width: 80 },
  { title: '操作', key: 'actions', width: 180 },
]

const cloneModal = reactive({ visible: false, loading: false, sourceId: '', newId: '' })

function typeColor(t: string) {
  return t === 'specialist' ? 'purple' : t === 'integrative' ? 'orange' : 'cyan'
}

async function loadData() {
  loading.value = true
  try {
    const res = await agentTemplateApi.list({
      ...filters,
      skip: (page.value - 1) * 20,
      limit: 20,
    })
    templates.value = res.data.items
    total.value = res.data.total
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

function onPageChange(p: number) {
  page.value = p
  loadData()
}

async function handleToggle(record: any) {
  try {
    await agentTemplateApi.toggle(record.agent_id)
    message.success(`${record.is_enabled ? '已停用' : '已启用'} ${record.display_name}`)
    loadData()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '操作失败')
  }
}

async function handleDelete(record: any) {
  try {
    await agentTemplateApi.delete(record.agent_id)
    message.success('已删除')
    loadData()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '删除失败')
  }
}

function handleClone(record: any) {
  cloneModal.sourceId = record.agent_id
  cloneModal.newId = ''
  cloneModal.visible = true
}

async function doClone() {
  if (!cloneModal.newId) {
    message.warning('请输入新的 Agent ID')
    return
  }
  cloneModal.loading = true
  try {
    await agentTemplateApi.clone(cloneModal.sourceId, cloneModal.newId)
    message.success('克隆成功')
    cloneModal.visible = false
    loadData()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '克隆失败')
  } finally {
    cloneModal.loading = false
  }
}

async function handleRefreshCache() {
  refreshing.value = true
  try {
    const res = await agentTemplateApi.refreshCache()
    message.success(`缓存已刷新, 共 ${res.data.count} 个模板`)
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '刷新失败')
  } finally {
    refreshing.value = false
  }
}

onMounted(() => loadData())
</script>

<style scoped>
.agent-template-list { padding: 0; }
.filter-card { margin-top: 16px; }
</style>
