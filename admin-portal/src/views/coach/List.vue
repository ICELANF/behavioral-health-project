<template>
  <div class="coach-list">
    <div class="page-header">
      <h2>教练管理</h2>
      <a-button type="primary" @click="openAddModal">
        <template #icon><PlusOutlined /></template>
        添加教练
      </a-button>
    </div>

    <!-- 统计卡片 -->
    <a-row :gutter="16" class="stats-row">
      <a-col :span="6">
        <a-card>
          <a-statistic
            title="总教练数"
            :value="totalCoaches"
            :value-style="{ color: '#1890ff' }"
          >
            <template #prefix><TeamOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="活跃教练" :value="activeCoaches" :value-style="{ color: '#52c41a' }">
            <template #suffix>
              <span style="font-size: 14px; color: #999">
                / {{ totalCoaches }}
              </span>
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="本月新增" :value="newCoachesThisMonth" :value-style="{ color: '#722ed1' }" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <div class="level-distribution">
            <div class="dist-title">等级分布</div>
            <div class="dist-bars">
              <a-tooltip v-for="(count, level) in levelDistribution" :key="level" :title="`${level}: ${count}人`">
                <div class="dist-bar">
                  <div class="bar-fill" :style="{ height: `${(count / maxLevelCount) * 100}%`, backgroundColor: levelColors[level] }"></div>
                  <span class="bar-label">{{ level }}</span>
                </div>
              </a-tooltip>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <a-alert v-if="error" :message="error" type="error" show-icon style="margin-bottom: 16px" />

    <!-- 筛选区域 -->
    <a-card style="margin-bottom: 16px">
      <a-row :gutter="16">
        <a-col :span="5">
          <a-select
            v-model:value="filters.level"
            placeholder="教练等级"
            allowClear
            style="width: 100%"
            @change="handleSearch"
          >
            <a-select-option value="L0">L0 观察员</a-select-option>
            <a-select-option value="L1">L1 成长者</a-select-option>
            <a-select-option value="L2">L2 分享者</a-select-option>
            <a-select-option value="L3">L3 教练</a-select-option>
            <a-select-option value="L4">L4 促进师</a-select-option>
            <a-select-option value="L5">L5 大师</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="5">
          <a-select
            v-model:value="filters.status"
            placeholder="状态"
            allowClear
            style="width: 100%"
            @change="handleSearch"
          >
            <a-select-option value="active">活跃</a-select-option>
            <a-select-option value="inactive">未活跃</a-select-option>
            <a-select-option value="suspended">已停用</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="5">
          <a-select
            v-model:value="filters.specialty"
            placeholder="专业方向"
            allowClear
            style="width: 100%"
            @change="handleSearch"
          >
            <a-select-option value="diabetes_reversal">糖尿病逆转</a-select-option>
            <a-select-option value="hypertension">高血压管理</a-select-option>
            <a-select-option value="weight_management">体重管理</a-select-option>
            <a-select-option value="stress_psychology">心理压力</a-select-option>
            <a-select-option value="metabolic_syndrome">代谢综合征</a-select-option>
            <a-select-option value="sleep_optimization">睡眠优化</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-input-search
            v-model:value="filters.keyword"
            placeholder="搜索姓名/手机号"
            @search="handleSearch"
          />
        </a-col>
        <a-col :span="3">
          <a-button @click="resetFilters">重置</a-button>
        </a-col>
      </a-row>
    </a-card>

    <!-- 教练表格 -->
    <a-card>
      <a-table
        :dataSource="filteredCoaches"
        :columns="columns"
        :loading="loading"
        :pagination="pagination"
        rowKey="coach_id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'coach'">
            <div class="coach-info">
              <a-avatar :size="40" :src="record.avatar">
                <template #icon v-if="!record.avatar">
                  {{ record.name?.[0] || 'U' }}
                </template>
              </a-avatar>
              <div class="coach-detail">
                <div class="coach-name">{{ record.name }}</div>
                <div class="coach-phone">{{ record.phone }}</div>
              </div>
            </div>
          </template>

          <template v-else-if="column.key === 'level'">
            <a-tag :color="levelColors[record.level]">
              {{ levelLabels[record.level] }}
            </a-tag>
          </template>

          <template v-else-if="column.key === 'specialty'">
            <template v-if="record.specialty?.length > 0">
              <a-tag v-for="s in record.specialty.slice(0, 2)" :key="s" color="blue">
                {{ specialtyLabels[s] || s }}
              </a-tag>
              <a-tooltip v-if="record.specialty.length > 2" :title="record.specialty.slice(2).map(s => specialtyLabels[s]).join(', ')">
                <a-tag>+{{ record.specialty.length - 2 }}</a-tag>
              </a-tooltip>
            </template>
            <span v-else style="color: #999">-</span>
          </template>

          <template v-else-if="column.key === 'stats'">
            <div class="stats-cell">
              <span><UserOutlined /> {{ record.student_count }} 学员</span>
              <span><FileTextOutlined /> {{ record.case_count }} 案例</span>
            </div>
          </template>

          <template v-else-if="column.key === 'status'">
            <a-badge
              :status="statusBadges[record.status]"
              :text="statusLabels[record.status]"
            />
          </template>

          <template v-else-if="column.key === 'lastActive'">
            <span>{{ formatTime(record.last_active) }}</span>
          </template>

          <template v-else-if="column.key === 'action'">
            <a-space>
              <a @click="viewCoach(record)">详情</a>
              <a @click="editCoach(record)">编辑</a>
              <a-dropdown>
                <a>更多 <DownOutlined /></a>
                <template #overlay>
                  <a-menu>
                    <a-menu-item @click="applyPromotion(record)">
                      <RiseOutlined /> 晋级申请
                    </a-menu-item>
                    <a-menu-item v-if="record.status !== 'suspended'" @click="suspendCoach(record)">
                      <StopOutlined /> 停用
                    </a-menu-item>
                    <a-menu-item v-else @click="activateCoach(record)">
                      <CheckCircleOutlined /> 启用
                    </a-menu-item>
                    <a-menu-divider />
                    <a-menu-item danger @click="deleteCoach(record)">
                      <DeleteOutlined /> 删除
                    </a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 添加/编辑教练弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      :title="isEdit ? '编辑教练' : '添加教练'"
      width="700px"
      @ok="handleSave"
      :confirmLoading="saving"
    >
      <a-form :model="formState" layout="vertical" ref="formRef" :rules="formRules">
        <a-row :gutter="16">
          <a-col :span="24">
            <a-form-item label="头像">
              <div class="avatar-upload">
                <a-avatar :size="80" :src="formState.avatar">
                  <template #icon><UserOutlined /></template>
                </a-avatar>
                <a-upload
                  :show-upload-list="false"
                  :before-upload="handleAvatarUpload"
                  accept="image/*"
                >
                  <a-button size="small" style="margin-left: 16px">
                    <UploadOutlined /> 上传头像
                  </a-button>
                </a-upload>
              </div>
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="姓名" name="name">
              <a-input v-model:value="formState.name" placeholder="请输入姓名" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="手机号" name="phone">
              <a-input v-model:value="formState.phone" placeholder="请输入手机号" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="邮箱" name="email">
              <a-input v-model:value="formState.email" placeholder="请输入邮箱" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="教练等级" name="level">
              <a-select v-model:value="formState.level" placeholder="选择等级">
                <a-select-option value="L0">L0 观察员</a-select-option>
                <a-select-option value="L1">L1 成长者</a-select-option>
                <a-select-option value="L2">L2 分享者</a-select-option>
                <a-select-option value="L3">L3 教练</a-select-option>
                <a-select-option value="L4">L4 促进师</a-select-option>
                <a-select-option value="L5">L5 大师</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="16">
            <a-form-item label="专业方向" name="specialty">
              <a-select
                v-model:value="formState.specialty"
                mode="multiple"
                placeholder="选择专业方向（可多选）"
              >
                <a-select-option value="diabetes_reversal">糖尿病逆转</a-select-option>
                <a-select-option value="hypertension">高血压管理</a-select-option>
                <a-select-option value="weight_management">体重管理</a-select-option>
                <a-select-option value="stress_psychology">心理压力</a-select-option>
                <a-select-option value="metabolic_syndrome">代谢综合征</a-select-option>
                <a-select-option value="sleep_optimization">睡眠优化</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="个人简介">
          <a-textarea
            v-model:value="formState.bio"
            placeholder="请输入个人简介"
            :rows="3"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  PlusOutlined,
  UserOutlined,
  TeamOutlined,
  FileTextOutlined,
  DownOutlined,
  RiseOutlined,
  StopOutlined,
  CheckCircleOutlined,
  DeleteOutlined,
  UploadOutlined
} from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'
import request from '@/api/request'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const router = useRouter()

// 接口定义
interface Coach {
  coach_id: string
  name: string
  avatar?: string
  phone: string
  email?: string
  level: 'L0' | 'L1' | 'L2' | 'L3' | 'L4' | 'L5'
  specialty?: string[]
  student_count: number
  case_count: number
  status: 'active' | 'inactive' | 'suspended'
  joined_at: string
  last_active: string
  bio?: string
}

// 状态
const loading = ref(false)
const saving = ref(false)
const modalVisible = ref(false)
const isEdit = ref(false)
const editingId = ref<string | null>(null)
const formRef = ref()

// 筛选条件
const filters = reactive({
  level: undefined as string | undefined,
  status: undefined as string | undefined,
  specialty: undefined as string | undefined,
  keyword: ''
})

// 分页
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条记录`
})

// 表格列
const columns = [
  { title: '教练信息', key: 'coach', width: 200 },
  { title: '等级', key: 'level', width: 120 },
  { title: '专业方向', key: 'specialty', width: 200 },
  { title: '数据统计', key: 'stats', width: 180 },
  { title: '状态', key: 'status', width: 100 },
  { title: '最后活跃', key: 'lastActive', width: 120 },
  { title: '操作', key: 'action', width: 150, fixed: 'right' }
]

// 常量映射
const levelColors: Record<string, string> = {
  L0: 'blue',
  L1: 'green',
  L2: 'orange',
  L3: 'red',
  L4: 'purple',
  L5: 'gold'
}

const levelLabels: Record<string, string> = {
  L0: 'L0 观察员',
  L1: 'L1 成长者',
  L2: 'L2 分享者',
  L3: 'L3 教练',
  L4: 'L4 促进师',
  L5: 'L5 大师'
}

const specialtyLabels: Record<string, string> = {
  diabetes_reversal: '糖尿病逆转',
  hypertension: '高血压',
  weight_management: '体重管理',
  stress_psychology: '心理压力',
  metabolic_syndrome: '代谢综合征',
  sleep_optimization: '睡眠优化'
}

const statusLabels: Record<string, string> = {
  active: '活跃',
  inactive: '未活跃',
  suspended: '已停用'
}

const statusBadges: Record<string, 'success' | 'default' | 'error'> = {
  active: 'success',
  inactive: 'default',
  suspended: 'error'
}

const coaches = ref<Coach[]>([])
const error = ref('')

// Map backend response to Coach interface
const _ROLE_LEVEL: Record<string, string> = {
  observer: 'L0', grower: 'L1', sharer: 'L2', coach: 'L3',
  promoter: 'L4', supervisor: 'L4', master: 'L5', admin: 'L5',
}

function mapBackendCoach(raw: any): Coach {
  const levelFromProfile = (raw.level || '').replace(/\s.*/, '')  // "L2 中级" → "L2"
  return {
    coach_id: String(raw.id),
    name: raw.name || raw.full_name || raw.username,
    avatar: '',
    phone: raw.phone || '',
    email: raw.email || '',
    level: (levelFromProfile || _ROLE_LEVEL[raw.role] || 'L0') as Coach['level'],
    specialty: raw.domains || raw.specializations || [],
    student_count: raw.currentLoad ?? 0,
    case_count: 0,
    status: raw.is_active === false ? 'suspended' : 'active',
    joined_at: raw.created_at ? raw.created_at.split('T')[0] : '',
    last_active: raw.last_login_at || raw.created_at || '',
    bio: '',
  }
}

// 计算属性
const totalCoaches = computed(() => coaches.value.length)
const activeCoaches = computed(() => coaches.value.filter(c => c.status === 'active').length)
const newCoachesThisMonth = computed(() => {
  const thisMonth = dayjs().format('YYYY-MM')
  return coaches.value.filter(c => c.joined_at.startsWith(thisMonth)).length
})

const levelDistribution = computed(() => {
  const dist: Record<string, number> = { L0: 0, L1: 0, L2: 0, L3: 0, L4: 0, L5: 0 }
  coaches.value.forEach(c => {
    dist[c.level] = (dist[c.level] || 0) + 1
  })
  return dist
})

const maxLevelCount = computed(() => Math.max(...Object.values(levelDistribution.value), 1))

const filteredCoaches = computed(() => {
  let result = [...coaches.value]

  if (filters.level) {
    result = result.filter(c => c.level === filters.level)
  }
  if (filters.status) {
    result = result.filter(c => c.status === filters.status)
  }
  if (filters.specialty) {
    result = result.filter(c => c.specialty?.includes(filters.specialty!))
  }
  if (filters.keyword) {
    const kw = filters.keyword.toLowerCase()
    result = result.filter(c =>
      c.name.toLowerCase().includes(kw) ||
      c.phone.includes(kw)
    )
  }

  pagination.total = result.length
  return result
})

// 表单数据
const formState = reactive({
  name: '',
  phone: '',
  email: '',
  level: 'L0' as string,
  specialty: [] as string[],
  avatar: '',
  bio: ''
})

const formRules = {
  name: [{ required: true, message: '请输入姓名' }],
  phone: [
    { required: true, message: '请输入手机号' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号' }
  ],
  level: [{ required: true, message: '请选择等级' }]
}

// 方法
const handleSearch = () => {
  pagination.current = 1
}

const resetFilters = () => {
  filters.level = undefined
  filters.status = undefined
  filters.specialty = undefined
  filters.keyword = ''
  pagination.current = 1
}

const handleTableChange = (pag: any) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
}

const formatTime = (time: string) => {
  return dayjs(time).fromNow()
}

const openAddModal = () => {
  isEdit.value = false
  editingId.value = null
  resetForm()
  modalVisible.value = true
}

const resetForm = () => {
  formState.name = ''
  formState.phone = ''
  formState.email = ''
  formState.level = 'L0'
  formState.specialty = []
  formState.avatar = ''
  formState.bio = ''
}

const handleAvatarUpload = (file: File) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    formState.avatar = e.target?.result as string
  }
  reader.readAsDataURL(file)
  return false
}

const handleSave = async () => {
  try {
    await formRef.value?.validate()
    saving.value = true

    if (isEdit.value && editingId.value) {
      await request.put(`/v1/admin/users/${editingId.value}`, {
        full_name: formState.name,
        email: formState.email,
        phone: formState.phone,
      })
      message.success('教练信息已更新')
    } else {
      const username = formState.phone || `coach_${Date.now()}`
      await request.post('/v1/admin/users', {
        username,
        password: 'Coach@2026',
        full_name: formState.name,
        role: 'coach',
        email: formState.email || `${username}@placeholder.com`,
        phone: formState.phone,
      })
      message.success('教练已添加')
    }

    modalVisible.value = false
    await loadCoaches()
  } catch (err: any) {
    console.error('保存失败:', err)
    message.error(err?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const viewCoach = (coach: Coach) => {
  router.push(`/coach/detail/${coach.coach_id}`)
}

const editCoach = (coach: Coach) => {
  isEdit.value = true
  editingId.value = coach.coach_id  // numeric id from backend
  formState.name = coach.name
  formState.phone = coach.phone
  formState.email = coach.email || ''
  formState.level = coach.level
  formState.specialty = coach.specialty ? [...coach.specialty] : []
  formState.avatar = coach.avatar || ''
  formState.bio = coach.bio || ''
  modalVisible.value = true
}

const applyPromotion = (coach: Coach) => {
  router.push(`/coach/review?coach_id=${coach.coach_id}`)
}

const suspendCoach = (coach: Coach) => {
  Modal.confirm({
    title: '确认停用',
    content: `确定要停用教练 ${coach.name} 吗？停用后该教练将无法登录系统。`,
    okText: '确认停用',
    okType: 'danger',
    onOk: async () => {
      try {
        await request.put(`/v1/admin/users/${coach.coach_id}/status`, { is_active: false })
        message.success('教练已停用')
        await loadCoaches()
      } catch (e: any) {
        message.error(e?.response?.data?.detail || '操作失败')
      }
    }
  })
}

const activateCoach = async (coach: Coach) => {
  try {
    await request.put(`/v1/admin/users/${coach.coach_id}/status`, { is_active: true })
    message.success('教练已启用')
    await loadCoaches()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '操作失败')
  }
}

const deleteCoach = (coach: Coach) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除教练 ${coach.name} 吗？此操作不可恢复。`,
    okText: '确认删除',
    okType: 'danger',
    onOk: async () => {
      try {
        await request.delete(`/v1/admin/users/${coach.coach_id}`)
        message.success('教练已删除')
        await loadCoaches()
      } catch (e: any) {
        message.error(e?.response?.data?.detail || '删除失败')
      }
    }
  })
}

const loadCoaches = async () => {
  loading.value = true
  error.value = ''
  try {
    const { data } = await request.get('/v1/admin/coaches')
    coaches.value = (data.coaches || []).map(mapBackendCoach)
    pagination.total = coaches.value.length
  } catch (e: any) {
    console.error('加载教练列表失败:', e)
    error.value = '加载教练列表失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadCoaches()
})
</script>

<style scoped>
.coach-list {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
}

.stats-row {
  margin-bottom: 16px;
}

.level-distribution {
  height: 100%;
}

.dist-title {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.dist-bars {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  height: 50px;
}

.dist-bar {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 30px;
}

.bar-fill {
  width: 20px;
  min-height: 4px;
  border-radius: 2px;
  transition: height 0.3s;
}

.bar-label {
  font-size: 10px;
  color: #999;
  margin-top: 4px;
}

.coach-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.coach-detail {
  display: flex;
  flex-direction: column;
}

.coach-name {
  font-weight: 500;
}

.coach-phone {
  font-size: 12px;
  color: #999;
}

.stats-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
  color: #666;
}

.stats-cell span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.avatar-upload {
  display: flex;
  align-items: center;
}
</style>
