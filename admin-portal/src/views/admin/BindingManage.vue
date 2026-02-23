<template>
  <div class="binding-manage">
    <a-page-header title="绑定管理" sub-title="管理教练-学员绑定关系" />

    <!-- 统计卡片 -->
    <a-row :gutter="16" class="mb-4">
      <a-col :xs="12" :sm="6">
        <a-card size="small">
          <a-statistic title="总绑定数" :value="stats.total_bindings" />
        </a-card>
      </a-col>
      <a-col :xs="12" :sm="6">
        <a-card size="small">
          <a-statistic title="活跃绑定" :value="stats.active_bindings" :value-style="{ color: '#52c41a' }" />
        </a-card>
      </a-col>
      <a-col :xs="12" :sm="6">
        <a-card size="small">
          <a-statistic title="教练数" :value="stats.active_coaches" />
        </a-card>
      </a-col>
      <a-col :xs="12" :sm="6">
        <a-card size="small">
          <a-statistic title="学员数" :value="stats.active_students" />
        </a-card>
      </a-col>
    </a-row>

    <!-- 筛选栏 -->
    <a-card class="mb-4">
      <a-row :gutter="[16, 12]">
        <a-col :xs="12" :sm="6">
          <a-input-number v-model:value="filters.coach_id" placeholder="教练ID" style="width:100%" />
        </a-col>
        <a-col :xs="12" :sm="6">
          <a-input-number v-model:value="filters.student_id" placeholder="学员ID" style="width:100%" />
        </a-col>
        <a-col :xs="12" :sm="6">
          <a-select v-model:value="filters.binding_type" placeholder="绑定类型" allowClear style="width:100%">
            <a-select-option value="assigned">指派</a-select-option>
            <a-select-option value="program">项目</a-select-option>
            <a-select-option value="challenge">挑战</a-select-option>
            <a-select-option value="self_selected">自选</a-select-option>
          </a-select>
        </a-col>
        <a-col :xs="12" :sm="6">
          <a-switch v-model:checked="filters.active_only" checked-children="仅活跃" un-checked-children="全部" />
        </a-col>
      </a-row>
      <a-row style="margin-top:12px">
        <a-col :span="24" style="text-align:right">
          <a-space>
            <a-button type="primary" @click="loadBindings">查询</a-button>
            <a-button @click="showCreateModal = true">创建绑定</a-button>
            <a-button @click="showBatchBindModal = true">批量绑定</a-button>
            <a-button danger :disabled="!selectedRowKeys.length" @click="handleBatchUnbind">批量解绑 ({{ selectedRowKeys.length }})</a-button>
          </a-space>
        </a-col>
      </a-row>
    </a-card>

    <!-- 数据列表 -->
    <a-spin :spinning="loading">
      <div class="list-card-container">
        <a-empty v-if="bindings.length === 0 && !loading" description="暂无绑定数据" />
        <ListCard v-for="record in bindings" :key="record.id">
          <template #avatar>
            <a-checkbox
              :checked="selectedRowKeys.includes(record.id)"
              @change="(e: any) => toggleSelect(record.id, e.target.checked)"
              @click.stop
            />
          </template>
          <template #title>
            <span>{{ record.coach_name || `教练#${record.coach_id}` }}</span>
            <span style="color: #999; margin: 0 6px">→</span>
            <span>{{ record.student_name || `学员#${record.student_id}` }}</span>
            <a-tag :color="record.is_active ? 'green' : 'red'" size="small" style="margin-left: 8px">{{ record.is_active ? '活跃' : '已解绑' }}</a-tag>
          </template>
          <template #subtitle>
            <a-tag :color="typeColor(record.binding_type)" size="small">{{ typeLabel(record.binding_type) }}</a-tag>
            <span style="color: #999; font-size: 12px">ID: {{ record.id?.substring(0, 8) }}...</span>
          </template>
          <template #meta>
            <span>绑定时间: {{ formatTime(record.bound_at) }}</span>
          </template>
          <template #actions>
            <a-button type="link" size="small" @click="openEditDrawer(record)">编辑</a-button>
            <a-popconfirm v-if="record.is_active" title="确定解绑？" @confirm="handleUnbind(record.id)">
              <a-button type="link" size="small" danger>解绑</a-button>
            </a-popconfirm>
          </template>
        </ListCard>
      </div>
    </a-spin>
    <div style="display: flex; justify-content: flex-end; margin-top: 16px">
      <a-pagination v-model:current="page" :page-size="pageSize" :total="total" :show-total="(t: number) => `共 ${t} 条`" @change="onPageChange" />
    </div>

    <!-- 创建绑定 Modal -->
    <a-modal v-model:open="showCreateModal" title="创建绑定" @ok="handleCreate" :confirmLoading="creating">
      <a-form layout="vertical">
        <a-form-item label="教练ID" required>
          <a-input-number v-model:value="createForm.coach_id" placeholder="输入教练用户ID" style="width:100%" />
        </a-form-item>
        <a-form-item label="学员ID" required>
          <a-input-number v-model:value="createForm.student_id" placeholder="输入学员用户ID" style="width:100%" />
        </a-form-item>
        <a-form-item label="绑定类型">
          <a-select v-model:value="createForm.binding_type" style="width:100%">
            <a-select-option value="assigned">指派</a-select-option>
            <a-select-option value="program">项目</a-select-option>
            <a-select-option value="challenge">挑战</a-select-option>
            <a-select-option value="self_selected">自选</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="权限">
          <a-checkbox v-model:checked="createForm.permissions.view_profile">查看档案</a-checkbox>
          <a-checkbox v-model:checked="createForm.permissions.view_assessment_summary">查看评估</a-checkbox>
          <a-checkbox v-model:checked="createForm.permissions.view_chat_summary">查看对话</a-checkbox>
          <a-checkbox v-model:checked="createForm.permissions.send_message">发送消息</a-checkbox>
          <a-checkbox v-model:checked="createForm.permissions.create_rx">创建处方</a-checkbox>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 编辑 Drawer -->
    <a-drawer v-model:open="showEditDrawer" title="编辑绑定" :width="360" placement="right">
      <a-form layout="vertical" v-if="editRecord">
        <a-form-item label="绑定ID">
          <a-input :value="editRecord.id" disabled />
        </a-form-item>
        <a-form-item label="教练">
          {{ editRecord.coach_name }} (ID: {{ editRecord.coach_id }})
        </a-form-item>
        <a-form-item label="学员">
          {{ editRecord.student_name }} (ID: {{ editRecord.student_id }})
        </a-form-item>
        <a-form-item label="绑定类型">
          <a-select v-model:value="editForm.binding_type" style="width:100%">
            <a-select-option value="assigned">指派</a-select-option>
            <a-select-option value="program">项目</a-select-option>
            <a-select-option value="challenge">挑战</a-select-option>
            <a-select-option value="self_selected">自选</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="权限">
          <a-checkbox v-model:checked="editForm.permissions.view_profile">查看档案</a-checkbox>
          <a-checkbox v-model:checked="editForm.permissions.view_assessment_summary">查看评估</a-checkbox>
          <a-checkbox v-model:checked="editForm.permissions.view_chat_summary">查看对话</a-checkbox>
          <a-checkbox v-model:checked="editForm.permissions.send_message">发送消息</a-checkbox>
          <a-checkbox v-model:checked="editForm.permissions.create_rx">创建处方</a-checkbox>
        </a-form-item>
        <a-form-item label="状态">
          <a-switch v-model:checked="editForm.is_active" checked-children="活跃" un-checked-children="解绑" />
        </a-form-item>
        <a-button type="primary" block :loading="updating" @click="handleUpdate">保存修改</a-button>
      </a-form>
    </a-drawer>

    <!-- 批量绑定 Modal -->
    <a-modal v-model:open="showBatchBindModal" title="批量绑定" @ok="handleBatchBind" :confirmLoading="batchBinding">
      <a-form layout="vertical">
        <a-form-item label="教练ID" required>
          <a-input-number v-model:value="batchForm.coach_id" placeholder="输入教练用户ID" style="width:100%" />
        </a-form-item>
        <a-form-item label="学员ID列表 (逗号分隔)" required>
          <a-textarea v-model:value="batchForm.student_ids_str" placeholder="例: 3,5,7,9" :rows="3" />
        </a-form-item>
        <a-form-item label="绑定类型">
          <a-select v-model:value="batchForm.binding_type" style="width:100%">
            <a-select-option value="assigned">指派</a-select-option>
            <a-select-option value="program">项目</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { bindingsApi } from '@/api/bindings'
import ListCard from '@/components/core/ListCard.vue'

const loading = ref(false)
const bindings = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20

const stats = ref({
  total_bindings: 0,
  active_bindings: 0,
  inactive_bindings: 0,
  active_coaches: 0,
  active_students: 0,
})

const filters = reactive({
  coach_id: undefined as number | undefined,
  student_id: undefined as number | undefined,
  binding_type: undefined as string | undefined,
  active_only: true,
})

const selectedRowKeys = ref<string[]>([])

// columns removed — using ListCard layout

function typeColor(t: string) {
  const map: Record<string, string> = { assigned: 'blue', program: 'green', challenge: 'orange', self_selected: 'purple' }
  return map[t] || 'default'
}

function typeLabel(t: string) {
  const map: Record<string, string> = { assigned: '指派', program: '项目', challenge: '挑战', self_selected: '自选' }
  return map[t] || t
}

function formatTime(t: string) {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function toggleSelect(id: string, checked: boolean) {
  if (checked) {
    if (!selectedRowKeys.value.includes(id)) selectedRowKeys.value.push(id)
  } else {
    selectedRowKeys.value = selectedRowKeys.value.filter(k => k !== id)
  }
}

async function loadStats() {
  try {
    const res = await bindingsApi.statsOverview()
    stats.value = res.data.stats
  } catch { /* ignore */ }
}

async function loadBindings() {
  loading.value = true
  try {
    const res = await bindingsApi.list({
      coach_id: filters.coach_id,
      student_id: filters.student_id,
      binding_type: filters.binding_type,
      active_only: filters.active_only,
      page: page.value,
      page_size: pageSize,
    })
    bindings.value = res.data.bindings
    total.value = res.data.total
  } catch (e) {
    console.error('加载绑定失败', e)
  } finally {
    loading.value = false
  }
}

function onPageChange(p: number) {
  page.value = p
  loadBindings()
}

// ── 创建绑定 ──
const showCreateModal = ref(false)
const creating = ref(false)
const createForm = reactive({
  coach_id: undefined as number | undefined,
  student_id: undefined as number | undefined,
  binding_type: 'assigned',
  permissions: {
    view_profile: true,
    view_assessment_summary: true,
    view_chat_summary: false,
    send_message: true,
    create_rx: true,
  },
})

async function handleCreate() {
  if (!createForm.coach_id || !createForm.student_id) {
    message.warning('请填写教练ID和学员ID')
    return
  }
  creating.value = true
  try {
    await bindingsApi.create({
      coach_id: createForm.coach_id,
      student_id: createForm.student_id,
      binding_type: createForm.binding_type,
      permissions: { ...createForm.permissions },
    })
    message.success('绑定创建成功')
    showCreateModal.value = false
    createForm.coach_id = undefined
    createForm.student_id = undefined
    loadBindings()
    loadStats()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

// ── 编辑绑定 ──
const showEditDrawer = ref(false)
const editRecord = ref<any>(null)
const updating = ref(false)
const editForm = reactive({
  binding_type: 'assigned',
  is_active: true,
  permissions: {
    view_profile: true,
    view_assessment_summary: true,
    view_chat_summary: false,
    send_message: true,
    create_rx: true,
  },
})

function openEditDrawer(record: any) {
  editRecord.value = record
  editForm.binding_type = record.binding_type
  editForm.is_active = record.is_active
  const perms = record.permissions || {}
  editForm.permissions.view_profile = perms.view_profile ?? true
  editForm.permissions.view_assessment_summary = perms.view_assessment_summary ?? true
  editForm.permissions.view_chat_summary = perms.view_chat_summary ?? false
  editForm.permissions.send_message = perms.send_message ?? true
  editForm.permissions.create_rx = perms.create_rx ?? true
  showEditDrawer.value = true
}

async function handleUpdate() {
  if (!editRecord.value) return
  updating.value = true
  try {
    await bindingsApi.update(editRecord.value.id, {
      binding_type: editForm.binding_type,
      is_active: editForm.is_active,
      permissions: { ...editForm.permissions },
    })
    message.success('更新成功')
    showEditDrawer.value = false
    loadBindings()
    loadStats()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '更新失败')
  } finally {
    updating.value = false
  }
}

// ── 解绑 ──
async function handleUnbind(bindingId: string) {
  try {
    await bindingsApi.unbind(bindingId)
    message.success('解绑成功')
    loadBindings()
    loadStats()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '解绑失败')
  }
}

// ── 批量绑定 ──
const showBatchBindModal = ref(false)
const batchBinding = ref(false)
const batchForm = reactive({
  coach_id: undefined as number | undefined,
  student_ids_str: '',
  binding_type: 'assigned',
})

async function handleBatchBind() {
  if (!batchForm.coach_id || !batchForm.student_ids_str.trim()) {
    message.warning('请填写教练ID和学员ID列表')
    return
  }
  const studentIds = batchForm.student_ids_str.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n))
  if (!studentIds.length) {
    message.warning('无有效学员ID')
    return
  }
  batchBinding.value = true
  try {
    const res = await bindingsApi.batchBind({
      coach_id: batchForm.coach_id,
      student_ids: studentIds,
      binding_type: batchForm.binding_type,
    })
    const d = res.data
    message.success(`批量绑定完成: 创建${d.created}, 跳过${d.skipped}, 失败${d.errors?.length || 0}`)
    showBatchBindModal.value = false
    batchForm.coach_id = undefined
    batchForm.student_ids_str = ''
    loadBindings()
    loadStats()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '批量绑定失败')
  } finally {
    batchBinding.value = false
  }
}

// ── 批量解绑 ──
async function handleBatchUnbind() {
  if (!selectedRowKeys.value.length) return
  try {
    const res = await bindingsApi.batchUnbind({
      binding_ids: selectedRowKeys.value,
      reason: '管理员批量解绑',
    })
    message.success(`批量解绑: ${res.data.unbound}/${res.data.total}`)
    selectedRowKeys.value = []
    loadBindings()
    loadStats()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '批量解绑失败')
  }
}

onMounted(() => {
  loadStats()
  loadBindings()
})
</script>

<style scoped>
.binding-manage { padding: 16px; }
.mb-4 { margin-bottom: 16px; }
.list-card-container { display: flex; flex-direction: column; gap: 10px; }
</style>
