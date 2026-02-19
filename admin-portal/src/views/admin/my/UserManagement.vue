<template>
  <div class="user-management">
    <div class="page-header">
      <h2>用户管理</h2>
      <div class="header-actions">
        <a-button @click="showImportModal = true"><UploadOutlined /> 批量导入</a-button>
        <a-button type="primary" @click="openCreateModal"><PlusOutlined /> 创建用户</a-button>
      </div>
    </div>

    <!-- Filters -->
    <a-card style="margin-bottom: 16px">
      <a-row :gutter="16">
        <a-col :span="5">
          <a-input-search v-model:value="filters.keyword" placeholder="搜索用户名/姓名/邮箱" @search="loadUsers" allowClear />
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filters.role" placeholder="角色" allowClear style="width: 100%" @change="loadUsers">
            <a-select-option value="admin">管理员</a-select-option>
            <a-select-option value="supervisor">督导</a-select-option>
            <a-select-option value="coach">教练</a-select-option>
            <a-select-option value="grower">成长者</a-select-option>
            <a-select-option value="observer">观察员</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filters.status" placeholder="状态" allowClear style="width: 100%" @change="loadUsers">
            <a-select-option value="active">正常</a-select-option>
            <a-select-option value="inactive">停用</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="3">
          <a-button @click="resetFilters">重置</a-button>
        </a-col>
      </a-row>
    </a-card>

    <!-- Stats -->
    <a-row :gutter="16" style="margin-bottom: 16px">
      <a-col :span="6"><a-card size="small"><a-statistic title="总用户数" :value="stats.total" :loading="statsLoading" /></a-card></a-col>
      <a-col :span="6"><a-card size="small"><a-statistic title="管理/督导" :value="stats.admin_count + stats.supervisor_count" :loading="statsLoading" /></a-card></a-col>
      <a-col :span="6"><a-card size="small"><a-statistic title="教练" :value="stats.coach_count" :loading="statsLoading" /></a-card></a-col>
      <a-col :span="6"><a-card size="small"><a-statistic title="成长者" :value="stats.grower_count" :loading="statsLoading" /></a-card></a-col>
    </a-row>

    <!-- User Table -->
    <a-card>
      <a-table
        :dataSource="users"
        :columns="columns"
        rowKey="id"
        size="small"
        :loading="loading"
        :pagination="{
          current: pagination.page,
          pageSize: pagination.pageSize,
          total: pagination.total,
          showTotal: (total: number) => `共 ${total} 用户`,
          onChange: onPageChange,
        }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <div style="display: flex; align-items: center; gap: 8px">
              <a-avatar :size="28" :style="{ background: roleColor(record.role) }">
                {{ (record.full_name || record.username)[0] }}
              </a-avatar>
              <div>
                <div style="font-weight: 500">{{ record.full_name || record.username }}</div>
                <div style="font-size: 11px; color: #999">{{ record.username }}</div>
              </div>
            </div>
          </template>
          <template v-if="column.key === 'role'">
            <a-tag :color="roleColor(record.role)">{{ roleLabel(record.role) }}</a-tag>
          </template>
          <template v-if="column.key === 'status'">
            <a-badge :status="record.is_active ? 'success' : 'error'" :text="record.is_active ? '正常' : '停用'" />
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a @click="editUser(record)">编辑</a>
              <a @click="toggleStatus(record)">{{ record.is_active ? '停用' : '启用' }}</a>
              <a-popconfirm title="确定删除?" @confirm="deleteUser(record)">
                <a style="color: #ff4d4f">删除</a>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- Create/Edit Modal -->
    <a-modal v-model:open="showCreateModal" :title="editingUser ? '编辑用户' : '创建用户'" @ok="saveUser" okText="保存" :confirmLoading="saving">
      <a-form layout="vertical">
        <a-form-item label="用户名" required>
          <a-input v-model:value="formData.username" :disabled="!!editingUser" placeholder="登录用户名" />
        </a-form-item>
        <a-form-item label="姓名">
          <a-input v-model:value="formData.full_name" placeholder="真实姓名" />
        </a-form-item>
        <a-form-item v-if="!editingUser" label="密码" required>
          <a-input-password v-model:value="formData.password" placeholder="登录密码（至少6位）" />
        </a-form-item>
        <a-form-item label="角色" required>
          <a-select v-model:value="formData.role" style="width: 100%">
            <a-select-option value="admin">管理员</a-select-option>
            <a-select-option value="supervisor">督导</a-select-option>
            <a-select-option value="coach">教练</a-select-option>
            <a-select-option value="grower">成长者</a-select-option>
            <a-select-option value="observer">观察员</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="邮箱" required>
          <a-input v-model:value="formData.email" placeholder="电子邮箱" />
        </a-form-item>
        <a-form-item label="手机号">
          <a-input v-model:value="formData.phone" placeholder="手机号码" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Import Modal -->
    <a-modal v-model:open="showImportModal" title="批量导入用户" @ok="handleImport" okText="导入">
      <a-alert message="CSV 格式：用户名,姓名,角色,邮箱,手机号,密码" type="info" show-icon style="margin-bottom: 12px" />
      <a-upload-dragger :before-upload="() => false" :maxCount="1" accept=".csv,.xlsx">
        <p style="font-size: 28px; margin-bottom: 8px">📁</p>
        <p>点击或拖拽文件到此区域</p>
      </a-upload-dragger>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, UploadOutlined } from '@ant-design/icons-vue'
import request from '@/api/request'

const showCreateModal = ref(false)
const showImportModal = ref(false)
const editingUser = ref<any>(null)
const loading = ref(false)
const saving = ref(false)
const statsLoading = ref(false)

const filters = reactive({
  keyword: '',
  role: undefined as string | undefined,
  status: undefined as string | undefined,
})

const pagination = reactive({ page: 1, pageSize: 10, total: 0 })

const stats = reactive({
  total: 0,
  admin_count: 0,
  supervisor_count: 0,
  coach_count: 0,
  grower_count: 0,
  observer_count: 0,
  active_count: 0,
})

const formData = reactive({
  username: '',
  full_name: '',
  password: '',
  role: 'grower',
  email: '',
  phone: '',
})

const users = ref<any[]>([])

const columns = [
  { title: '用户', key: 'name', width: 200 },
  { title: '角色', key: 'role', width: 100 },
  { title: '状态', key: 'status', width: 80 },
  { title: '邮箱', dataIndex: 'email', width: 180, ellipsis: true },
  { title: '手机', dataIndex: 'phone', width: 130 },
  { title: '创建时间', dataIndex: 'created_at', width: 120, customRender: ({ text }: any) => text ? new Date(text).toLocaleDateString('zh-CN') : '-' },
  { title: '操作', key: 'action', width: 160 },
]

const roleLabel = (role: string) => {
  const map: Record<string, string> = {
    admin: '管理员', supervisor: '督导', promoter: '促进师',
    master: '大师', coach: '教练', sharer: '分享者',
    grower: '成长者', observer: '观察员', patient: '患者',
  }
  return map[role] || role
}

const roleColor = (role: string) => {
  const map: Record<string, string> = {
    admin: '#cf1322', supervisor: '#722ed1', promoter: '#eb2f96',
    master: '#faad14', coach: '#1890ff', sharer: '#52c41a',
    grower: '#fa8c16', observer: '#8c8c8c', patient: '#fa8c16',
  }
  return map[role] || '#999'
}

// === API calls ===

const loadUsers = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (filters.keyword) params.search = filters.keyword
    if (filters.role) params.role = filters.role
    if (filters.status) params.is_active = filters.status === 'active'

    const { data } = await request.get('/v1/admin/users', { params })
    users.value = data.users || []
    pagination.total = data.total || 0
  } catch (e: any) {
    console.error('加载用户列表失败:', e)
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  statsLoading.value = true
  try {
    const { data } = await request.get('/v1/admin/stats')
    Object.assign(stats, data)
  } catch (e: any) {
    console.error('加载统计数据失败:', e)
    // Calculate from local data
    stats.total = users.value.length
  } finally {
    statsLoading.value = false
  }
}

const openCreateModal = () => {
  editingUser.value = null
  Object.assign(formData, { username: '', full_name: '', password: '', role: 'grower', email: '', phone: '' })
  showCreateModal.value = true
}

const editUser = (record: any) => {
  editingUser.value = record
  Object.assign(formData, {
    username: record.username,
    full_name: record.full_name,
    role: record.role,
    email: record.email,
    phone: record.phone,
    password: '',
  })
  showCreateModal.value = true
}

const saveUser = async () => {
  if (!formData.username || !formData.role || !formData.email) {
    message.warning('请填写必要信息（用户名、角色、邮箱）')
    return
  }

  saving.value = true
  try {
    if (editingUser.value) {
      // 编辑用户
      await request.put(`/v1/admin/users/${editingUser.value.id}`, {
        full_name: formData.full_name,
        role: formData.role,
        email: formData.email,
        phone: formData.phone,
      })
      message.success('用户已更新')
    } else {
      // 创建用户
      if (!formData.password || formData.password.length < 6) {
        message.warning('密码长度不能少于6位')
        saving.value = false
        return
      }
      await request.post('/v1/admin/users', {
        username: formData.username,
        full_name: formData.full_name,
        password: formData.password,
        role: formData.role,
        email: formData.email,
        phone: formData.phone,
      })
      message.success('用户已创建')
    }
    showCreateModal.value = false
    editingUser.value = null
    await loadUsers()
    await loadStats()
  } catch (e: any) {
    const detail = e.response?.data?.detail
    message.error(detail || '操作失败')
  } finally {
    saving.value = false
  }
}

const toggleStatus = async (record: any) => {
  try {
    await request.put(`/v1/admin/users/${record.id}/status`, {
      is_active: !record.is_active,
    })
    record.is_active = !record.is_active
    message.success(`用户已${record.is_active ? '启用' : '停用'}`)
  } catch (e: any) {
    message.error('操作失败')
  }
}

const deleteUser = async (record: any) => {
  try {
    await request.delete(`/v1/admin/users/${record.id}`)
    message.success('用户已删除')
    await loadUsers()
    await loadStats()
  } catch (e: any) {
    message.error('删除失败')
  }
}

const onPageChange = (page: number, pageSize: number) => {
  pagination.page = page
  pagination.pageSize = pageSize
  loadUsers()
}

const resetFilters = () => {
  filters.keyword = ''
  filters.role = undefined
  filters.status = undefined
  pagination.page = 1
  loadUsers()
}

const handleImport = () => {
  message.info('批量导入功能即将上线')
  showImportModal.value = false
}

onMounted(() => {
  loadUsers()
  loadStats()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; }
.header-actions { display: flex; gap: 8px; }
</style>
