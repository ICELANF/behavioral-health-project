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
        <a-col :span="4">
          <a-select v-model:value="filters.riskFilter" placeholder="风险等级" allowClear style="width: 100%" @change="loadUsers">
            <a-select-option v-for="opt in RISK_OPTIONS" :key="opt.value" :value="opt.value">
              <a-badge :color="opt.color" :text="opt.label" />
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filters.activityFilter" placeholder="活跃度" allowClear style="width: 100%" @change="loadUsers">
            <a-select-option v-for="opt in ACTIVITY_OPTIONS" :key="opt.value" :value="opt.value">
              <a-badge :color="opt.color" :text="opt.label" />
            </a-select-option>
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

    <!-- User List -->
    <a-spin :spinning="loading">
      <div class="list-card-container">
        <ListCard
          v-for="record in users"
          :key="record.id"
          @click="openProfile(record.id)"
        >
          <template #avatar>
            <a-avatar :size="36" :style="{ background: roleColor(record.role) }">
              {{ (record.full_name || record.username)[0] }}
            </a-avatar>
          </template>
          <template #title>
            <span>{{ record.full_name || record.username }}</span>
            <span style="font-size: 11px; color: #999; margin-left: 8px">{{ record.username }}</span>
          </template>
          <template #subtitle>
            <a-tag :color="roleColor(record.role)">{{ roleLabel(record.role) }}</a-tag>
            <a-badge :status="record.is_active ? 'success' : 'error'" :text="record.is_active ? '正常' : '停用'" />
            <template v-if="record.classification && ['observer','grower','sharer'].includes(record.role)">
              <a-tag :color="getTagColor('risk', record.classification.risk)" size="small">
                {{ getValueLabel('risk', record.classification.risk) }}
              </a-tag>
              <a-tag :color="getTagColor('activity', record.classification.activity)" size="small">
                {{ getValueLabel('activity', record.classification.activity) }}
              </a-tag>
            </template>
          </template>
          <template #meta>
            <span v-if="record.email">{{ record.email }}</span>
            <span v-if="record.phone" class="meta-divider">|</span>
            <span v-if="record.phone">{{ record.phone }}</span>
            <span class="meta-divider">|</span>
            <span>{{ record.created_at ? new Date(record.created_at).toLocaleDateString('zh-CN') : '-' }}</span>
          </template>
          <template #actions>
            <a-space @click.stop>
              <a @click="openProfile(record.id)">查看</a>
              <a @click="editUser(record)">编辑</a>
              <a @click="toggleStatus(record)">{{ record.is_active ? '停用' : '启用' }}</a>
              <a-popconfirm title="确定删除?" @confirm="deleteUser(record)">
                <a style="color: #ff4d4f">删除</a>
              </a-popconfirm>
            </a-space>
          </template>
        </ListCard>
      </div>
      <div v-if="users.length === 0 && !loading" style="text-align: center; padding: 40px; color: #999">
        暂无用户数据
      </div>
    </a-spin>
    <div style="display: flex; justify-content: flex-end; margin-top: 16px">
      <a-pagination
        v-model:current="pagination.page"
        v-model:pageSize="pagination.pageSize"
        :total="pagination.total"
        show-size-changer
        :show-total="(total: number) => `共 ${total} 用户`"
        @change="onPageChange"
      />
    </div>

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

    <!-- Role Profile Drawer -->
    <UserRoleProfileDrawer v-model:open="profileDrawerOpen" :userId="profileUserId" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, UploadOutlined } from '@ant-design/icons-vue'
import request from '@/api/request'
import UserRoleProfileDrawer from '@/components/UserRoleProfileDrawer.vue'
import ListCard from '@/components/core/ListCard.vue'
import { RISK_OPTIONS, ACTIVITY_OPTIONS, getTagColor, getValueLabel } from '@/composables/useStudentClassification'

const showCreateModal = ref(false)
const showImportModal = ref(false)
const editingUser = ref<any>(null)
const loading = ref(false)
const saving = ref(false)
const statsLoading = ref(false)
const profileDrawerOpen = ref(false)
const profileUserId = ref<number | null>(null)

const openProfile = (userId: number) => {
  profileUserId.value = userId
  profileDrawerOpen.value = true
}

const filters = reactive({
  keyword: '',
  role: undefined as string | undefined,
  status: undefined as string | undefined,
  riskFilter: undefined as string | undefined,
  activityFilter: undefined as string | undefined,
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

// columns removed — now using ListCard layout

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
    if (filters.riskFilter) params.risk = filters.riskFilter
    if (filters.activityFilter) params.activity = filters.activityFilter

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
  filters.riskFilter = undefined
  filters.activityFilter = undefined
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
.list-card-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; }
.header-actions { display: flex; gap: 8px; }

.meta-divider {
  color: #d9d9d9;
  margin: 0 4px;
}
</style>
