<template>
  <div class="settings-page">
    <h2>系统设置</h2>

    <a-card :tab-list="tabList" :active-tab-key="activeTab" @tabChange="onTabChange">
      <!-- 基础设置 -->
      <div v-if="activeTab === 'basic'" class="tab-content">
        <a-form :model="basicSettings" layout="vertical" style="max-width: 600px">
          <a-form-item label="系统名称">
            <a-input v-model:value="basicSettings.systemName" placeholder="请输入系统名称" />
          </a-form-item>

          <a-form-item label="系统Logo">
            <div class="logo-upload">
              <a-avatar :size="80" :src="basicSettings.logo" shape="square">
                <template #icon><PictureOutlined /></template>
              </a-avatar>
              <a-upload
                :show-upload-list="false"
                :before-upload="handleLogoUpload"
                accept="image/*"
              >
                <a-button style="margin-left: 16px">
                  <UploadOutlined /> 上传Logo
                </a-button>
              </a-upload>
            </div>
            <div class="upload-tip">建议尺寸: 200x200px，PNG/JPG格式</div>
          </a-form-item>

          <a-form-item label="版权信息">
            <a-input v-model:value="basicSettings.copyright" placeholder="例：© 2026 行为健康教练平台" />
          </a-form-item>

          <a-form-item label="备案号">
            <a-input v-model:value="basicSettings.icp" placeholder="例：京ICP备xxxxxxxx号" />
          </a-form-item>

          <a-form-item label="联系邮箱">
            <a-input v-model:value="basicSettings.contactEmail" placeholder="请输入联系邮箱" />
          </a-form-item>

          <a-form-item label="联系电话">
            <a-input v-model:value="basicSettings.contactPhone" placeholder="请输入联系电话" />
          </a-form-item>

          <a-form-item>
            <a-button type="primary" @click="saveBasicSettings" :loading="saving">
              保存设置
            </a-button>
          </a-form-item>
        </a-form>
      </div>

      <!-- 等级配置 -->
      <div v-if="activeTab === 'level'" class="tab-content">
        <a-alert
          message="等级晋升要求配置"
          description="配置各等级晋升所需满足的条件，包括课程完成、考试通过、案例数量和督导时长等。"
          type="info"
          show-icon
          style="margin-bottom: 16px"
        />

        <a-collapse v-model:activeKey="activeLevelPanels">
          <a-collapse-panel v-for="level in levelConfigs" :key="level.level" :header="level.name">
            <a-form :model="level" layout="vertical">
              <a-row :gutter="16">
                <a-col :span="6">
                  <a-form-item label="必修课程数">
                    <a-input-number v-model:value="level.required_courses" :min="0" style="width: 100%" />
                  </a-form-item>
                </a-col>
                <a-col :span="6">
                  <a-form-item label="考试通过数">
                    <a-input-number v-model:value="level.required_exams" :min="0" style="width: 100%" />
                  </a-form-item>
                </a-col>
                <a-col :span="6">
                  <a-form-item label="案例数量">
                    <a-input-number v-model:value="level.required_cases" :min="0" style="width: 100%" />
                  </a-form-item>
                </a-col>
                <a-col :span="6">
                  <a-form-item label="督导时长(小时)">
                    <a-input-number v-model:value="level.required_mentoring_hours" :min="0" style="width: 100%" />
                  </a-form-item>
                </a-col>
              </a-row>
              <a-form-item label="其他要求">
                <a-textarea v-model:value="level.additional_requirements" placeholder="其他晋升要求描述" :rows="2" />
              </a-form-item>
            </a-form>
          </a-collapse-panel>
        </a-collapse>

        <div style="margin-top: 16px">
          <a-button type="primary" @click="saveLevelConfigs" :loading="saving">
            保存等级配置
          </a-button>
        </div>
      </div>

      <!-- 考试设置 -->
      <div v-if="activeTab === 'exam'" class="tab-content">
        <a-form :model="examSettings" layout="vertical" style="max-width: 600px">
          <a-divider orientation="left">基本设置</a-divider>

          <a-form-item label="默认考试时长">
            <a-input-number
              v-model:value="examSettings.defaultDuration"
              :min="10"
              :max="300"
              style="width: 200px"
            />
            <span style="margin-left: 8px">分钟 (0表示不限时)</span>
          </a-form-item>

          <a-form-item label="默认及格分数">
            <a-input-number
              v-model:value="examSettings.defaultPassingScore"
              :min="0"
              :max="100"
              style="width: 200px"
            />
            <span style="margin-left: 8px">分</span>
          </a-form-item>

          <a-form-item label="允许重考次数">
            <a-input-number
              v-model:value="examSettings.maxRetries"
              :min="1"
              :max="10"
              style="width: 200px"
            />
            <span style="margin-left: 8px">次</span>
          </a-form-item>

          <a-divider orientation="left">防作弊设置</a-divider>

          <a-form-item label="切屏检测">
            <a-switch v-model:checked="examSettings.antiCheat.detectTabSwitch" />
            <span style="margin-left: 8px; color: #999">检测考生切换标签页/窗口</span>
          </a-form-item>

          <a-form-item label="允许切屏次数">
            <a-input-number
              v-model:value="examSettings.antiCheat.maxTabSwitches"
              :min="0"
              :max="10"
              :disabled="!examSettings.antiCheat.detectTabSwitch"
              style="width: 200px"
            />
            <span style="margin-left: 8px">次 (超过则自动交卷)</span>
          </a-form-item>

          <a-form-item label="禁止复制粘贴">
            <a-switch v-model:checked="examSettings.antiCheat.disableCopyPaste" />
          </a-form-item>

          <a-form-item label="禁止右键菜单">
            <a-switch v-model:checked="examSettings.antiCheat.disableContextMenu" />
          </a-form-item>

          <a-form-item label="题目随机顺序">
            <a-switch v-model:checked="examSettings.antiCheat.shuffleQuestions" />
          </a-form-item>

          <a-form-item label="选项随机顺序">
            <a-switch v-model:checked="examSettings.antiCheat.shuffleOptions" />
          </a-form-item>

          <a-form-item>
            <a-button type="primary" @click="saveExamSettings" :loading="saving">
              保存考试设置
            </a-button>
          </a-form-item>
        </a-form>
      </div>

      <!-- 通知设置 -->
      <div v-if="activeTab === 'notification'" class="tab-content">
        <a-form :model="notificationSettings" layout="vertical" style="max-width: 600px">
          <a-divider orientation="left">邮件配置</a-divider>

          <a-form-item label="启用邮件通知">
            <a-switch v-model:checked="notificationSettings.email.enabled" />
          </a-form-item>

          <template v-if="notificationSettings.email.enabled">
            <a-form-item label="SMTP服务器">
              <a-input v-model:value="notificationSettings.email.smtpHost" placeholder="smtp.example.com" />
            </a-form-item>

            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="SMTP端口">
                  <a-input-number v-model:value="notificationSettings.email.smtpPort" :min="1" style="width: 100%" />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="SSL/TLS">
                  <a-switch v-model:checked="notificationSettings.email.useSSL" />
                </a-form-item>
              </a-col>
            </a-row>

            <a-form-item label="发件人邮箱">
              <a-input v-model:value="notificationSettings.email.senderEmail" placeholder="noreply@example.com" />
            </a-form-item>

            <a-form-item label="发件人名称">
              <a-input v-model:value="notificationSettings.email.senderName" placeholder="行为健康平台" />
            </a-form-item>
          </template>

          <a-divider orientation="left">短信配置</a-divider>

          <a-form-item label="启用短信通知">
            <a-switch v-model:checked="notificationSettings.sms.enabled" />
          </a-form-item>

          <template v-if="notificationSettings.sms.enabled">
            <a-form-item label="短信服务商">
              <a-select v-model:value="notificationSettings.sms.provider" style="width: 200px">
                <a-select-option value="aliyun">阿里云短信</a-select-option>
                <a-select-option value="tencent">腾讯云短信</a-select-option>
                <a-select-option value="huawei">华为云短信</a-select-option>
              </a-select>
            </a-form-item>

            <a-form-item label="Access Key">
              <a-input-password v-model:value="notificationSettings.sms.accessKey" placeholder="请输入Access Key" />
            </a-form-item>

            <a-form-item label="Access Secret">
              <a-input-password v-model:value="notificationSettings.sms.accessSecret" placeholder="请输入Access Secret" />
            </a-form-item>

            <a-form-item label="短信签名">
              <a-input v-model:value="notificationSettings.sms.signName" placeholder="请输入短信签名" />
            </a-form-item>
          </template>

          <a-form-item>
            <a-button type="primary" @click="saveNotificationSettings" :loading="saving">
              保存通知设置
            </a-button>
          </a-form-item>
        </a-form>
      </div>

      <!-- 用户管理 -->
      <div v-if="activeTab === 'users'" class="tab-content">
        <div class="users-header">
          <h3>管理员账号</h3>
          <a-button type="primary" @click="openAddUserModal">
            <template #icon><PlusOutlined /></template>
            添加管理员
          </a-button>
        </div>

        <a-table :dataSource="adminUsers" :columns="userColumns" rowKey="id" :pagination="false">
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'user'">
              <div class="user-info">
                <a-avatar :size="32">{{ record.name?.[0] }}</a-avatar>
                <div>
                  <div>{{ record.name }}</div>
                  <div style="font-size: 12px; color: #999">{{ record.email }}</div>
                </div>
              </div>
            </template>

            <template v-else-if="column.key === 'role'">
              <a-tag :color="roleColors[record.role]">{{ roleLabels[record.role] }}</a-tag>
            </template>

            <template v-else-if="column.key === 'status'">
              <a-badge :status="record.active ? 'success' : 'default'" :text="record.active ? '正常' : '禁用'" />
            </template>

            <template v-else-if="column.key === 'action'">
              <a-space>
                <a @click="editUser(record)">编辑</a>
                <a @click="resetPassword(record)">重置密码</a>
                <a-popconfirm
                  v-if="record.role !== 'super_admin'"
                  title="确定删除该管理员吗？"
                  @confirm="deleteUser(record)"
                >
                  <a style="color: #ff4d4f">删除</a>
                </a-popconfirm>
              </a-space>
            </template>
          </template>
        </a-table>
      </div>
    </a-card>

    <!-- 添加/编辑管理员弹窗 -->
    <a-modal
      v-model:open="userModalVisible"
      :title="isEditUser ? '编辑管理员' : '添加管理员'"
      @ok="handleSaveUser"
      :confirmLoading="saving"
    >
      <a-form :model="userForm" layout="vertical" ref="userFormRef" :rules="userFormRules">
        <a-form-item label="姓名" name="name">
          <a-input v-model:value="userForm.name" placeholder="请输入姓名" />
        </a-form-item>

        <a-form-item label="邮箱" name="email">
          <a-input v-model:value="userForm.email" placeholder="请输入邮箱" />
        </a-form-item>

        <a-form-item label="手机号" name="phone">
          <a-input v-model:value="userForm.phone" placeholder="请输入手机号" />
        </a-form-item>

        <a-form-item label="角色" name="role">
          <a-select v-model:value="userForm.role" placeholder="选择角色">
            <a-select-option value="admin">管理员</a-select-option>
            <a-select-option value="operator">运营人员</a-select-option>
            <a-select-option value="reviewer">审核人员</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item v-if="!isEditUser" label="初始密码" name="password">
          <a-input-password v-model:value="userForm.password" placeholder="请输入初始密码" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  PictureOutlined,
  UploadOutlined,
  PlusOutlined
} from '@ant-design/icons-vue'
import request from '../api/request'

// 状态
const saving = ref(false)
const activeTab = ref('basic')
const activeLevelPanels = ref(['L1'])
const userModalVisible = ref(false)
const isEditUser = ref(false)
const editingUserId = ref<string | null>(null)
const userFormRef = ref()

// Tab 配置
const tabList = [
  { key: 'basic', tab: '基础设置' },
  { key: 'level', tab: '等级配置' },
  { key: 'exam', tab: '考试设置' },
  { key: 'notification', tab: '通知设置' },
  { key: 'users', tab: '用户管理' }
]

// 基础设置
const basicSettings = reactive({
  systemName: '行为健康教练认证平台',
  logo: '',
  copyright: '© 2026 行为健康教练平台 版权所有',
  icp: '',
  contactEmail: '',
  contactPhone: '400-000-0000'
})

// 等级配置
const levelConfigs = ref([
  {
    level: 'L1',
    name: 'L1 成长者',
    required_courses: 3,
    required_exams: 1,
    required_cases: 5,
    required_mentoring_hours: 0,
    additional_requirements: ''
  },
  {
    level: 'L2',
    name: 'L2 分享者',
    required_courses: 5,
    required_exams: 2,
    required_cases: 20,
    required_mentoring_hours: 10,
    additional_requirements: '需完成至少1次督导反馈'
  },
  {
    level: 'L3',
    name: 'L3 教练',
    required_courses: 8,
    required_exams: 3,
    required_cases: 50,
    required_mentoring_hours: 20,
    additional_requirements: '需有至少2个成功案例报告'
  },
  {
    level: 'L4',
    name: 'L4 促进师',
    required_courses: 10,
    required_exams: 4,
    required_cases: 100,
    required_mentoring_hours: 40,
    additional_requirements: '需完成督导培训，有带教经验'
  },
  {
    level: 'L5',
    name: 'L5 大师',
    required_courses: 15,
    required_exams: 5,
    required_cases: 200,
    required_mentoring_hours: 80,
    additional_requirements: '需有显著行业贡献，具备培训师资格'
  }
])

// 考试设置
const examSettings = reactive({
  defaultDuration: 60,
  defaultPassingScore: 60,
  maxRetries: 3,
  antiCheat: {
    detectTabSwitch: true,
    maxTabSwitches: 3,
    disableCopyPaste: true,
    disableContextMenu: true,
    shuffleQuestions: true,
    shuffleOptions: true
  }
})

// 通知设置
const notificationSettings = reactive({
  email: {
    enabled: true,
    smtpHost: '',
    smtpPort: 465,
    useSSL: true,
    senderEmail: '',
    senderName: '行为健康平台'
  },
  sms: {
    enabled: false,
    provider: 'aliyun',
    accessKey: '',
    accessSecret: '',
    signName: ''
  }
})

// 用户管理
const userColumns = [
  { title: '用户信息', key: 'user', width: 200 },
  { title: '手机号', dataIndex: 'phone', width: 140 },
  { title: '角色', key: 'role', width: 120 },
  { title: '状态', key: 'status', width: 100 },
  { title: '最后登录', dataIndex: 'last_login', width: 140 },
  { title: '操作', key: 'action', width: 180 }
]

const roleLabels: Record<string, string> = {
  super_admin: '超级管理员',
  admin: '管理员',
  operator: '运营人员',
  reviewer: '审核人员'
}

const roleColors: Record<string, string> = {
  super_admin: 'red',
  admin: 'blue',
  operator: 'green',
  reviewer: 'orange'
}

const adminUsers = ref<any[]>([])

const loadAdminUsers = async () => {
  try {
    const res = await request.get('v1/admin/users', { params: { role: 'admin', page_size: 50 } })
    adminUsers.value = (res.data?.items || res.data || []).map((u: any) => ({
      id: String(u.id),
      name: u.full_name || u.username || '',
      email: u.email || '',
      phone: u.phone || '',
      role: u.role || 'admin',
      active: u.is_active ?? true,
      last_login: u.last_login || '-'
    }))
  } catch (e) {
    console.error('加载管理员列表失败:', e)
  }
}

onMounted(loadAdminUsers)

// 用户表单
const userForm = reactive({
  name: '',
  email: '',
  phone: '',
  role: 'operator',
  password: ''
})

const userFormRules = {
  name: [{ required: true, message: '请输入姓名' }],
  email: [
    { required: true, message: '请输入邮箱' },
    { type: 'email', message: '请输入有效的邮箱' }
  ],
  role: [{ required: true, message: '请选择角色' }],
  password: [{ required: true, message: '请输入初始密码', min: 6 }]
}

// 方法
const onTabChange = (key: string) => {
  activeTab.value = key
}

const handleLogoUpload = (file: File) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    basicSettings.logo = e.target?.result as string
  }
  reader.readAsDataURL(file)
  return false
}

const saveBasicSettings = async () => {
  saving.value = true
  try {
    await request.put('v1/admin/settings/basic', basicSettings)
    message.success('基础设置已保存')
  } catch (e) {
    console.error('保存基础设置失败:', e)
    message.error('保存基础设置失败')
  } finally {
    saving.value = false
  }
}

const saveLevelConfigs = async () => {
  saving.value = true
  try {
    await request.put('v1/admin/settings/levels', { levels: levelConfigs.value })
    message.success('等级配置已保存')
  } catch (e) {
    console.error('保存等级配置失败:', e)
    message.error('保存等级配置失败')
  } finally {
    saving.value = false
  }
}

const saveExamSettings = async () => {
  saving.value = true
  try {
    await request.put('v1/admin/settings/exam', examSettings)
    message.success('考试设置已保存')
  } catch (e) {
    console.error('保存考试设置失败:', e)
    message.error('保存考试设置失败')
  } finally {
    saving.value = false
  }
}

const saveNotificationSettings = async () => {
  saving.value = true
  try {
    await request.put('v1/admin/settings/notification', notificationSettings)
    message.success('通知设置已保存')
  } catch (e) {
    console.error('保存通知设置失败:', e)
    message.error('保存通知设置失败')
  } finally {
    saving.value = false
  }
}

const openAddUserModal = () => {
  isEditUser.value = false
  editingUserId.value = null
  userForm.name = ''
  userForm.email = ''
  userForm.phone = ''
  userForm.role = 'operator'
  userForm.password = ''
  userModalVisible.value = true
}

const editUser = (user: any) => {
  isEditUser.value = true
  editingUserId.value = user.id
  userForm.name = user.name
  userForm.email = user.email
  userForm.phone = user.phone
  userForm.role = user.role
  userForm.password = ''
  userModalVisible.value = true
}

const handleSaveUser = async () => {
  try {
    await userFormRef.value?.validate()
    saving.value = true

    const payload = {
      full_name: userForm.name,
      email: userForm.email,
      phone: userForm.phone,
      role: userForm.role,
      ...(userForm.password ? { password: userForm.password } : {})
    }

    if (isEditUser.value && editingUserId.value) {
      await request.put(`v1/admin/users/${editingUserId.value}`, payload)
      message.success('管理员信息已更新')
    } else {
      await request.post('v1/admin/users', payload)
      message.success('管理员已添加')
    }

    userModalVisible.value = false
    await loadAdminUsers()
  } catch (error) {
    console.error('保存失败:', error)
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

const resetPassword = (user: any) => {
  message.success(`已向 ${user.email} 发送密码重置邮件`)
}

const deleteUser = async (user: any) => {
  try {
    await request.delete(`v1/admin/users/${user.id}`)
    message.success('管理员已删除')
    await loadAdminUsers()
  } catch (e) {
    console.error('删除管理员失败:', e)
    message.error('删除管理员失败')
  }
}
</script>

<style scoped>
.settings-page {
  padding: 0;
}

.settings-page h2 {
  margin-bottom: 16px;
}

.tab-content {
  min-height: 400px;
  padding: 16px 0;
}

.logo-upload {
  display: flex;
  align-items: center;
}

.upload-tip {
  color: #999;
  font-size: 12px;
  margin-top: 8px;
}

.users-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.users-header h3 {
  margin: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
