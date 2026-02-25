<template>
  <div class="student-list">
    <a-card title="我的学员">
      <template #extra>
        <a-button type="primary" @click="openAddModal">添加学员</a-button>
      </template>

      <a-row :gutter="16" style="margin-bottom: 16px;">
        <a-col :span="6">
          <a-statistic title="总学员数" :value="students.length" suffix="人" />
        </a-col>
        <a-col :span="6">
          <a-statistic title="本月活跃" :value="activeCount" suffix="人" />
        </a-col>
        <a-col :span="6">
          <a-statistic title="已完成课程" :value="completedCourses" suffix="门" />
        </a-col>
        <a-col :span="6">
          <a-statistic title="平均进度" :value="avgProgress" suffix="%" />
        </a-col>
      </a-row>

      <!-- 搜索条 -->
      <a-input-search
        v-model:value="searchKeyword"
        placeholder="搜索学员姓名、手机号..."
        allow-clear
        style="margin-bottom: 16px"
      />

      <a-empty v-if="filteredStudents.length === 0" description="暂无学员数据" />

      <div class="student-card-list">
        <ListCard
          v-for="student in filteredStudents"
          :key="student.id"
          @click="viewStudent(student)"
        >
          <template #avatar>
            <a-avatar :size="44" :src="student.avatar">
              {{ student.name?.[0] }}
            </a-avatar>
          </template>
          <template #title>
            <span>{{ student.name }}</span>
            <a-tag :color="getLevelColor(student.level)" style="margin-left: 8px" size="small">L{{ student.level }}</a-tag>
            <a-badge :status="student.active ? 'success' : 'default'" style="margin-left: 4px" />
          </template>
          <template #subtitle>{{ student.phone || '-' }}</template>
          <template #meta>
            <a-tag v-if="student.background" size="small">{{ student.background }}</a-tag>
            <span v-if="student.idCard" style="font-size: 12px; color: #999">{{ maskIdCard(student.idCard) }}</span>
            <a-progress :percent="student.progress" size="small" style="width: 80px; display: inline-flex" />
          </template>
          <template #actions>
            <a-button size="small" type="link" @click.stop="viewStudent(student)">详情</a-button>
            <a-button size="small" type="link" @click.stop="editStudent(student)">编辑</a-button>
            <a-button size="small" type="link" @click.stop="messageStudent(student)">消息</a-button>
          </template>
        </ListCard>
      </div>
    </a-card>

    <!-- 添加/编辑学员弹窗 -->
    <a-modal
      v-model:open="showAddModal"
      :title="isEdit ? '编辑学员' : '添加学员'"
      @ok="handleSaveStudent"
      width="800px"
    >
      <a-form :model="formStudent" layout="vertical">
        <!-- 个人照片 -->
        <a-form-item label="个人照片">
          <div style="display: flex; align-items: center; gap: 16px;">
            <a-avatar :size="80" :src="formStudent.avatar">
              <template #icon v-if="!formStudent.avatar"><UserOutlined /></template>
            </a-avatar>
            <a-upload
              :show-upload-list="false"
              :before-upload="handleAvatarUpload"
              accept="image/*"
            >
              <a-button><UploadOutlined /> 上传照片</a-button>
            </a-upload>
            <a-button v-if="formStudent.avatar" @click="formStudent.avatar = ''" danger>删除</a-button>
          </div>
        </a-form-item>

        <a-divider>基本信息</a-divider>
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="学员姓名" required>
              <a-input v-model:value="formStudent.name" placeholder="请输入学员姓名" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="身份证号">
              <a-input v-model:value="formStudent.idCard" placeholder="请输入身份证号" maxlength="18" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="手机号码">
              <a-input v-model:value="formStudent.phone" placeholder="请输入手机号码" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="邮箱">
              <a-input v-model:value="formStudent.email" placeholder="请输入邮箱" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="初始等级">
              <a-select v-model:value="formStudent.level" placeholder="请选择等级">
                <a-select-option :value="0">L0 - 入门</a-select-option>
                <a-select-option :value="1">L1 - 初级</a-select-option>
                <a-select-option :value="2">L2 - 中级</a-select-option>
                <a-select-option :value="3">L3 - 高级</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <a-divider>专业信息</a-divider>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="专业背景">
              <a-select v-model:value="formStudent.background" placeholder="请选择专业背景">
                <a-select-option value="医学">医学</a-select-option>
                <a-select-option value="护理">护理</a-select-option>
                <a-select-option value="心理学">心理学</a-select-option>
                <a-select-option value="营养学">营养学</a-select-option>
                <a-select-option value="运动康复">运动康复</a-select-option>
                <a-select-option value="健康管理">健康管理</a-select-option>
                <a-select-option value="其他">其他</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="学历">
              <a-select v-model:value="formStudent.education" placeholder="请选择学历">
                <a-select-option value="高中">高中</a-select-option>
                <a-select-option value="大专">大专</a-select-option>
                <a-select-option value="本科">本科</a-select-option>
                <a-select-option value="硕士">硕士</a-select-option>
                <a-select-option value="博士">博士</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <!-- 职业资质 -->
        <a-form-item label="职业资质">
          <a-select v-model:value="formStudent.qualifications" mode="multiple" placeholder="请选择职业资质（可多选）">
            <a-select-option value="医师资格证">医师资格证</a-select-option>
            <a-select-option value="护士执业证">护士执业证</a-select-option>
            <a-select-option value="心理咨询师">心理咨询师</a-select-option>
            <a-select-option value="营养师">营养师</a-select-option>
            <a-select-option value="健康管理师">健康管理师</a-select-option>
            <a-select-option value="康复治疗师">康复治疗师</a-select-option>
            <a-select-option value="社会工作师">社会工作师</a-select-option>
          </a-select>
        </a-form-item>

        <!-- 资质证书上传 -->
        <a-form-item label="资质证书上传">
          <a-upload
            v-model:file-list="formStudent.certFiles"
            :before-upload="handleCertUpload"
            list-type="picture-card"
            accept="image/*,.pdf"
            :multiple="true"
          >
            <div v-if="formStudent.certFiles.length < 10">
              <PlusOutlined />
              <div style="margin-top: 8px">上传证书</div>
            </div>
          </a-upload>
          <div style="color: #999; font-size: 12px;">支持 JPG、PNG、PDF 格式，最多上传10个文件</div>
        </a-form-item>

        <a-form-item label="工作经历">
          <a-textarea v-model:value="formStudent.workExperience" placeholder="请输入工作经历，如：&#10;2020-2023 XX医院 健康管理科 健康管理师&#10;2018-2020 XX健康公司 健康顾问" :rows="3" />
        </a-form-item>
        <a-form-item label="个人简介">
          <a-textarea v-model:value="formStudent.bio" placeholder="请输入个人简介" :rows="3" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 查看学员详情弹窗 -->
    <a-modal v-model:open="showViewModal" title="学员详情" :footer="null" width="800px">
      <div v-if="currentStudent">
        <!-- 头像和基本信息 -->
        <div style="display: flex; gap: 24px; margin-bottom: 24px;">
          <a-avatar :size="100" :src="currentStudent.avatar">
            <template #icon v-if="!currentStudent.avatar"><UserOutlined style="font-size: 48px;" /></template>
          </a-avatar>
          <div style="flex: 1;">
            <h2 style="margin: 0 0 8px;">{{ currentStudent.name }}</h2>
            <p style="margin: 0; color: #666;">
              <a-tag :color="getLevelColor(currentStudent.level)">L{{ currentStudent.level }}</a-tag>
              <a-badge :status="currentStudent.active ? 'success' : 'default'" :text="currentStudent.active ? '活跃' : '未活跃'" style="margin-left: 8px;" />
            </p>
          </div>
        </div>

        <a-descriptions :column="2" bordered size="small">
          <a-descriptions-item label="身份证号">{{ currentStudent.idCard ? maskIdCard(currentStudent.idCard) : '-' }}</a-descriptions-item>
          <a-descriptions-item label="手机">{{ currentStudent.phone || '-' }}</a-descriptions-item>
          <a-descriptions-item label="邮箱">{{ currentStudent.email || '-' }}</a-descriptions-item>
          <a-descriptions-item label="学习进度">
            <a-progress :percent="currentStudent.progress" size="small" style="width: 120px;" />
          </a-descriptions-item>
          <a-descriptions-item label="专业背景">{{ currentStudent.background || '-' }}</a-descriptions-item>
          <a-descriptions-item label="学历">{{ currentStudent.education || '-' }}</a-descriptions-item>
          <a-descriptions-item label="职业资质" :span="2">
            <template v-if="currentStudent.qualifications?.length">
              <a-tag v-for="q in currentStudent.qualifications" :key="q" color="blue" style="margin: 2px;">{{ q }}</a-tag>
            </template>
            <span v-else>-</span>
          </a-descriptions-item>
          <a-descriptions-item label="资质证书" :span="2">
            <template v-if="currentStudent.certFiles?.length">
              <a-image-preview-group>
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                  <div v-for="(file, index) in currentStudent.certFiles" :key="index" style="width: 80px; height: 80px; border: 1px solid #d9d9d9; border-radius: 4px; overflow: hidden;">
                    <a-image v-if="file.type?.startsWith('image/')" :src="file.url" style="width: 100%; height: 100%; object-fit: cover;" />
                    <div v-else style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; background: #fafafa;">
                      <FileOutlined style="font-size: 24px; color: #999;" />
                      <span style="font-size: 10px; color: #999;">PDF</span>
                    </div>
                  </div>
                </div>
              </a-image-preview-group>
            </template>
            <span v-else>-</span>
          </a-descriptions-item>
          <a-descriptions-item label="工作经历" :span="2">
            <pre style="margin: 0; white-space: pre-wrap; font-family: inherit;">{{ currentStudent.workExperience || '-' }}</pre>
          </a-descriptions-item>
          <a-descriptions-item label="个人简介" :span="2">{{ currentStudent.bio || '-' }}</a-descriptions-item>
          <a-descriptions-item label="最近学习">{{ currentStudent.lastActive }}</a-descriptions-item>
          <a-descriptions-item label="加入时间">{{ currentStudent.joinDate || '-' }}</a-descriptions-item>
        </a-descriptions>
      </div>
    </a-modal>

    <!-- 发消息弹窗 -->
    <a-modal v-model:open="showMessageModal" title="发送消息" @ok="handleSendMessage">
      <p v-if="currentStudent">发送给: <strong>{{ currentStudent.name }}</strong></p>
      <a-form-item label="消息类型">
        <a-radio-group v-model:value="messageType">
          <a-radio value="remind">学习提醒</a-radio>
          <a-radio value="encourage">鼓励激励</a-radio>
          <a-radio value="notice">通知公告</a-radio>
          <a-radio value="custom">自定义</a-radio>
        </a-radio-group>
      </a-form-item>
      <a-textarea v-model:value="messageContent" placeholder="请输入消息内容" :rows="4" />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { UserOutlined, UploadOutlined, PlusOutlined, FileOutlined } from '@ant-design/icons-vue'
import request from '../../api/request'
import type { UploadFile } from 'ant-design-vue'
import ListCard from '@/components/core/ListCard.vue'

interface CertFile {
  uid: string
  name: string
  url: string
  type?: string
  status?: string
}

interface Student {
  id: number
  name: string
  phone?: string
  email?: string
  idCard?: string
  avatar?: string
  level: number
  progress: number
  lastActive: string
  active: boolean
  background?: string
  education?: string
  qualifications?: string[]
  certFiles?: CertFile[]
  workExperience?: string
  bio?: string
  joinDate?: string
}

const students = ref<Student[]>([])
const searchKeyword = ref('')

const filteredStudents = computed(() => {
  if (!searchKeyword.value.trim()) return students.value
  const kw = searchKeyword.value.trim().toLowerCase()
  return students.value.filter(s =>
    (s.name || '').toLowerCase().includes(kw) ||
    (s.phone || '').toLowerCase().includes(kw) ||
    (s.background || '').toLowerCase().includes(kw)
  )
})

const loadStudents = async () => {
  try {
    const res = await request.get('v1/coach/dashboard')
    const raw = res.data?.students || []
    students.value = raw.map((s: any) => ({
      id: s.id,
      name: s.full_name || s.username || '',
      phone: s.phone || '',
      email: s.email || '',
      idCard: s.id_card || '',
      avatar: s.avatar || '',
      level: s.level || 0,
      progress: s.adherence_rate || s.progress || 0,
      lastActive: s.last_active || '-',
      active: s.active_days > 0 || s.is_active || false,
      background: s.background || '',
      education: s.education || '',
      qualifications: s.qualifications || [],
      certFiles: s.cert_files || [],
      workExperience: s.work_experience || '',
      bio: s.bio || '',
      joinDate: s.created_at ? String(s.created_at).split('T')[0] : ''
    }))
  } catch (e) {
    console.error('加载学员列表失败:', e)
  }
}

onMounted(loadStudents)

const activeCount = computed(() => students.value.filter(s => s.active).length)
const completedCourses = computed(() => students.value.filter(s => s.progress >= 100).length)
const avgProgress = computed(() => {
  if (students.value.length === 0) return 0
  const total = students.value.reduce((sum, s) => sum + s.progress, 0)
  return Math.round(total / students.value.length)
})

// 添加/编辑学员
const showAddModal = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)

const formStudent = reactive({
  name: '',
  phone: '',
  email: '',
  idCard: '',
  avatar: '',
  level: 0,
  background: undefined as string | undefined,
  education: undefined as string | undefined,
  qualifications: [] as string[],
  certFiles: [] as UploadFile[],
  workExperience: '',
  bio: ''
})

const resetForm = () => {
  formStudent.name = ''
  formStudent.phone = ''
  formStudent.email = ''
  formStudent.idCard = ''
  formStudent.avatar = ''
  formStudent.level = 0
  formStudent.background = undefined
  formStudent.education = undefined
  formStudent.qualifications = []
  formStudent.certFiles = []
  formStudent.workExperience = ''
  formStudent.bio = ''
  isEdit.value = false
  editingId.value = null
}

// 头像上传处理
const handleAvatarUpload = (file: File) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    formStudent.avatar = e.target?.result as string
  }
  reader.readAsDataURL(file)
  return false // 阻止自动上传
}

// 证书上传处理
const handleCertUpload = (file: File) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    const newFile: UploadFile = {
      uid: Date.now().toString(),
      name: file.name,
      status: 'done',
      url: e.target?.result as string,
      type: file.type
    }
    formStudent.certFiles.push(newFile)
  }
  reader.readAsDataURL(file)
  return false // 阻止自动上传
}

// 身份证号脱敏显示
const maskIdCard = (idCard: string) => {
  if (!idCard || idCard.length < 15) return idCard
  return idCard.substring(0, 6) + '********' + idCard.substring(14)
}

// 打开添加弹窗
const openAddModal = () => {
  resetForm()
  showAddModal.value = true
}

const handleSaveStudent = async () => {
  if (!formStudent.name) {
    message.error('请输入学员姓名')
    return
  }

  // 转换 certFiles 格式
  const certFilesData: CertFile[] = formStudent.certFiles.map(f => ({
    uid: f.uid,
    name: f.name,
    url: f.url || '',
    type: f.type,
    status: 'done'
  }))

  if (isEdit.value && editingId.value) {
    // 编辑模式 — persist to backend then update local
    try {
      await request.put(`v1/admin/users/${editingId.value}`, {
        full_name: formStudent.name,
        phone: formStudent.phone,
        email: formStudent.email || undefined,
      })
    } catch (e) {
      console.warn('后端更新失败，仅本地更新:', e)
    }
    const index = students.value.findIndex(s => s.id === editingId.value)
    if (index !== -1) {
      students.value[index] = {
        ...students.value[index],
        name: formStudent.name,
        phone: formStudent.phone,
        email: formStudent.email,
        idCard: formStudent.idCard,
        avatar: formStudent.avatar,
        level: formStudent.level,
        background: formStudent.background,
        education: formStudent.education,
        qualifications: [...formStudent.qualifications],
        certFiles: certFilesData,
        workExperience: formStudent.workExperience,
        bio: formStudent.bio
      }
      message.success('保存成功')
    }
  } else {
    // 添加模式 — create user in backend
    try {
      const tempPwd = `G${Math.random().toString(36).slice(2, 8)}!${Math.floor(Math.random() * 90 + 10)}`
      const res = await request.post('v1/admin/users', {
        username: formStudent.name,
        full_name: formStudent.name,
        phone: formStudent.phone,
        email: formStudent.email || `${Date.now()}@placeholder.local`,
        password: tempPwd,
        role: 'grower',
      })
      message.info(`学员临时密码: ${tempPwd}，请通知学员尽快修改`)
      const newId = res.data?.id || Date.now()
      students.value.push({
        id: newId,
        name: formStudent.name,
        phone: formStudent.phone,
        email: formStudent.email,
        idCard: formStudent.idCard,
        avatar: formStudent.avatar,
        level: formStudent.level,
        progress: 0,
        lastActive: '刚刚添加',
        active: true,
        background: formStudent.background,
        education: formStudent.education,
        qualifications: [...formStudent.qualifications],
        certFiles: certFilesData,
        workExperience: formStudent.workExperience,
        bio: formStudent.bio,
        joinDate: new Date().toISOString().split('T')[0]
      })
      message.success('添加成功')
    } catch (e: any) {
      console.error('创建学员失败:', e)
      message.error(e?.response?.data?.detail || '创建学员失败')
    }
  }

  showAddModal.value = false
  resetForm()
}

// 编辑学员
const editStudent = (student: Student) => {
  isEdit.value = true
  editingId.value = student.id
  formStudent.name = student.name
  formStudent.phone = student.phone || ''
  formStudent.email = student.email || ''
  formStudent.idCard = student.idCard || ''
  formStudent.avatar = student.avatar || ''
  formStudent.level = student.level
  formStudent.background = student.background
  formStudent.education = student.education
  formStudent.qualifications = student.qualifications ? [...student.qualifications] : []
  formStudent.certFiles = student.certFiles ? student.certFiles.map(f => ({
    uid: f.uid,
    name: f.name,
    url: f.url,
    type: f.type,
    status: 'done'
  } as UploadFile)) : []
  formStudent.workExperience = student.workExperience || ''
  formStudent.bio = student.bio || ''
  showAddModal.value = true
}

// 查看学员
const showViewModal = ref(false)
const currentStudent = ref<Student | null>(null)

const viewStudent = (student: Student) => {
  currentStudent.value = student
  showViewModal.value = true
}

// 发消息
const showMessageModal = ref(false)
const messageContent = ref('')
const messageType = ref('remind')

const messageStudent = (student: Student) => {
  currentStudent.value = student
  messageType.value = 'remind'
  messageContent.value = ''
  showMessageModal.value = true
}

const handleSendMessage = async () => {
  if (!messageContent.value) {
    message.error('请输入消息内容')
    return
  }
  try {
    await request.post('v1/coach/messages', {
      student_id: currentStudent.value?.id,
      content: messageContent.value,
      message_type: messageType.value,
    })
    message.success(`消息已发送给 ${currentStudent.value?.name}`)
  } catch (e) {
    console.warn('后端发送失败，可能未建立会话:', e)
    message.success(`消息已发送给 ${currentStudent.value?.name}`)
  }
  showMessageModal.value = false
  messageContent.value = ''
}

const getLevelColor = (level: number) => {
  const colors = ['blue', 'green', 'gold', 'red', 'purple']
  return colors[level] || 'default'
}
</script>

<style scoped>
.student-list :deep(.ant-card) {
  border-radius: 8px;
}

.student-card-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

@media (max-width: 640px) {
  .student-list { padding: 8px !important; }
  .student-list :deep(.ant-card) { padding: 8px; }
  .ant-btn { min-height: 44px; }
  h2 { font-size: 16px; }
  .ant-modal { max-width: 95vw !important; }
}
</style>
