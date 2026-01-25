<template>
  <div class="coach-detail">
    <a-breadcrumb style="margin-bottom: 16px">
      <a-breadcrumb-item><router-link to="/coach/list">教练管理</router-link></a-breadcrumb-item>
      <a-breadcrumb-item>教练详情</a-breadcrumb-item>
    </a-breadcrumb>

    <a-spin :spinning="loading">
      <a-row :gutter="16">
        <!-- 左侧：基本信息卡片 -->
        <a-col :span="8">
          <a-card :bordered="false">
            <div class="profile-header">
              <a-avatar :size="100" :src="coach.avatar">
                <template #icon v-if="!coach.avatar">
                  <UserOutlined style="font-size: 48px" />
                </template>
              </a-avatar>
              <div class="profile-info">
                <h2>{{ coach.name }}</h2>
                <div class="level-badge">
                  <a-tag :color="levelColors[coach.level]" size="large">
                    {{ levelLabels[coach.level] }}
                  </a-tag>
                  <a-badge :status="statusBadges[coach.status]" :text="statusLabels[coach.status]" />
                </div>
              </div>
            </div>

            <a-divider />

            <div class="profile-stats">
              <div class="stat-item">
                <div class="stat-value">{{ coach.student_count }}</div>
                <div class="stat-label">学员</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ coach.case_count }}</div>
                <div class="stat-label">案例</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ coach.mentoring_hours || 0 }}</div>
                <div class="stat-label">督导时长</div>
              </div>
            </div>

            <a-divider />

            <a-descriptions :column="1" size="small">
              <a-descriptions-item label="手机">
                <PhoneOutlined /> {{ coach.phone }}
              </a-descriptions-item>
              <a-descriptions-item label="邮箱">
                <MailOutlined /> {{ coach.email || '-' }}
              </a-descriptions-item>
              <a-descriptions-item label="专业方向">
                <template v-if="coach.specialty?.length > 0">
                  <a-tag v-for="s in coach.specialty" :key="s" color="blue" style="margin: 2px">
                    {{ specialtyLabels[s] || s }}
                  </a-tag>
                </template>
                <span v-else>-</span>
              </a-descriptions-item>
              <a-descriptions-item label="加入时间">
                <CalendarOutlined /> {{ coach.joined_at }}
              </a-descriptions-item>
              <a-descriptions-item label="最后活跃">
                <ClockCircleOutlined /> {{ formatTime(coach.last_active) }}
              </a-descriptions-item>
            </a-descriptions>

            <a-divider />

            <a-space direction="vertical" style="width: 100%">
              <a-button type="primary" block @click="handleEdit">
                <EditOutlined /> 编辑信息
              </a-button>
              <a-button block @click="handlePromotion" :disabled="coach.level === 'L4'">
                <RiseOutlined /> 申请晋级
              </a-button>
              <a-button block @click="handleMessage">
                <MessageOutlined /> 发送消息
              </a-button>
            </a-space>
          </a-card>
        </a-col>

        <!-- 右侧：详细信息 Tab -->
        <a-col :span="16">
          <a-card :bordered="false" :tab-list="tabList" :active-tab-key="activeTab" @tabChange="onTabChange">
            <!-- 资质证书 -->
            <div v-if="activeTab === 'certificates'" class="tab-content">
              <div v-if="coach.certificates?.length > 0" class="certificate-grid">
                <div v-for="cert in coach.certificates" :key="cert.id" class="certificate-item">
                  <a-card hoverable size="small">
                    <template #cover>
                      <div class="cert-image">
                        <img v-if="cert.image" :src="cert.image" alt="证书" />
                        <div v-else class="cert-placeholder">
                          <SafetyCertificateOutlined style="font-size: 48px; color: #999" />
                        </div>
                      </div>
                    </template>
                    <a-card-meta :title="cert.name">
                      <template #description>
                        <div>颁发机构: {{ cert.issuer }}</div>
                        <div>有效期至: {{ cert.expiry_date || '长期' }}</div>
                      </template>
                    </a-card-meta>
                  </a-card>
                </div>
              </div>
              <a-empty v-else description="暂无资质证书" />
            </div>

            <!-- 学习进度 -->
            <div v-if="activeTab === 'progress'" class="tab-content">
              <a-row :gutter="16" style="margin-bottom: 24px">
                <a-col :span="8">
                  <a-statistic title="已完成课程" :value="completedCourses" suffix="门" />
                </a-col>
                <a-col :span="8">
                  <a-statistic title="进行中课程" :value="ongoingCourses" suffix="门" />
                </a-col>
                <a-col :span="8">
                  <a-statistic title="平均考试成绩" :value="avgExamScore" suffix="分" />
                </a-col>
              </a-row>

              <h4>课程学习记录</h4>
              <a-table :dataSource="courseProgress" :columns="courseColumns" :pagination="false" size="small">
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'progress'">
                    <a-progress :percent="record.progress" size="small" :status="record.progress === 100 ? 'success' : 'active'" />
                  </template>
                  <template v-else-if="column.key === 'status'">
                    <a-tag :color="record.status === 'completed' ? 'success' : 'processing'">
                      {{ record.status === 'completed' ? '已完成' : '学习中' }}
                    </a-tag>
                  </template>
                </template>
              </a-table>

              <h4 style="margin-top: 24px">考试成绩</h4>
              <a-table :dataSource="examResults" :columns="examColumns" :pagination="false" size="small">
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'score'">
                    <span :style="{ color: record.score >= record.passing_score ? '#52c41a' : '#ff4d4f' }">
                      {{ record.score }}
                    </span>
                    <span style="color: #999"> / {{ record.passing_score }}</span>
                  </template>
                  <template v-else-if="column.key === 'status'">
                    <a-tag :color="record.passed ? 'success' : 'error'">
                      {{ record.passed ? '通过' : '未通过' }}
                    </a-tag>
                  </template>
                </template>
              </a-table>
            </div>

            <!-- 晋级历史 -->
            <div v-if="activeTab === 'promotion'" class="tab-content">
              <a-timeline>
                <a-timeline-item v-for="item in promotionHistory" :key="item.id" :color="item.approved ? 'green' : 'red'">
                  <div class="timeline-item">
                    <div class="timeline-header">
                      <span class="timeline-title">
                        {{ item.from_level }} <ArrowRightOutlined /> {{ item.to_level }}
                      </span>
                      <a-tag :color="item.approved ? 'success' : 'error'">
                        {{ item.approved ? '已通过' : '已拒绝' }}
                      </a-tag>
                    </div>
                    <div class="timeline-time">{{ item.date }}</div>
                    <div class="timeline-content" v-if="item.comment">
                      审核意见: {{ item.comment }}
                    </div>
                  </div>
                </a-timeline-item>
              </a-timeline>
              <a-empty v-if="promotionHistory.length === 0" description="暂无晋级记录" />
            </div>

            <!-- 学员列表 -->
            <div v-if="activeTab === 'students'" class="tab-content">
              <a-table :dataSource="students" :columns="studentColumns" :pagination="{ pageSize: 5 }" size="small">
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'name'">
                    <div class="student-info">
                      <a-avatar :size="32">{{ record.name[0] }}</a-avatar>
                      <span>{{ record.name }}</span>
                    </div>
                  </template>
                  <template v-else-if="column.key === 'progress'">
                    <a-progress :percent="record.progress" size="small" style="width: 100px" />
                  </template>
                  <template v-else-if="column.key === 'status'">
                    <a-badge :status="record.active ? 'success' : 'default'" :text="record.active ? '活跃' : '未活跃'" />
                  </template>
                </template>
              </a-table>
            </div>

            <!-- 案例记录 -->
            <div v-if="activeTab === 'cases'" class="tab-content">
              <a-list :dataSource="cases" :pagination="{ pageSize: 5 }">
                <template #renderItem="{ item }">
                  <a-list-item>
                    <a-list-item-meta :title="item.title" :description="item.description">
                      <template #avatar>
                        <a-avatar :style="{ backgroundColor: caseTypeColors[item.type] }">
                          {{ caseTypeLabels[item.type]?.[0] || '案' }}
                        </a-avatar>
                      </template>
                    </a-list-item-meta>
                    <template #actions>
                      <span>{{ item.date }}</span>
                      <a>查看详情</a>
                    </template>
                  </a-list-item>
                </template>
              </a-list>
              <a-empty v-if="cases.length === 0" description="暂无案例记录" />
            </div>

            <!-- 督导记录 -->
            <div v-if="activeTab === 'mentoring'" class="tab-content">
              <a-table :dataSource="mentoringRecords" :columns="mentoringColumns" :pagination="{ pageSize: 5 }" size="small">
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'supervisor'">
                    <div class="supervisor-info">
                      <a-avatar :size="24">{{ record.supervisor_name[0] }}</a-avatar>
                      <span>{{ record.supervisor_name }}</span>
                    </div>
                  </template>
                  <template v-else-if="column.key === 'rating'">
                    <a-rate :value="record.rating" disabled :count="5" style="font-size: 12px" />
                  </template>
                </template>
              </a-table>
              <a-empty v-if="mentoringRecords.length === 0" description="暂无督导记录" />
            </div>
          </a-card>
        </a-col>
      </a-row>
    </a-spin>

    <!-- 发送消息弹窗 -->
    <a-modal v-model:open="messageModalVisible" title="发送消息" @ok="handleSendMessage">
      <a-form layout="vertical">
        <a-form-item label="消息类型">
          <a-radio-group v-model:value="messageForm.type">
            <a-radio value="remind">学习提醒</a-radio>
            <a-radio value="encourage">鼓励激励</a-radio>
            <a-radio value="notice">系统通知</a-radio>
            <a-radio value="custom">自定义</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="消息内容">
          <a-textarea v-model:value="messageForm.content" placeholder="请输入消息内容" :rows="4" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  UserOutlined,
  PhoneOutlined,
  MailOutlined,
  CalendarOutlined,
  ClockCircleOutlined,
  EditOutlined,
  RiseOutlined,
  MessageOutlined,
  SafetyCertificateOutlined,
  ArrowRightOutlined
} from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const route = useRoute()
const router = useRouter()
const coachId = computed(() => route.params.id as string)

// 状态
const loading = ref(false)
const activeTab = ref('certificates')
const messageModalVisible = ref(false)

// Tab 配置
const tabList = [
  { key: 'certificates', tab: '资质证书' },
  { key: 'progress', tab: '学习进度' },
  { key: 'promotion', tab: '晋级历史' },
  { key: 'students', tab: '学员管理' },
  { key: 'cases', tab: '案例记录' },
  { key: 'mentoring', tab: '督导记录' }
]

// 常量
const levelColors: Record<string, string> = {
  L0: 'blue',
  L1: 'green',
  L2: 'orange',
  L3: 'red',
  L4: 'purple'
}

const levelLabels: Record<string, string> = {
  L0: 'L0 入门学员',
  L1: 'L1 初级教练',
  L2: 'L2 中级教练',
  L3: 'L3 高级教练',
  L4: 'L4 督导专家'
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

const caseTypeLabels: Record<string, string> = {
  diabetes: '糖尿病',
  hypertension: '高血压',
  weight: '体重管理',
  psychology: '心理健康'
}

const caseTypeColors: Record<string, string> = {
  diabetes: '#1890ff',
  hypertension: '#f5222d',
  weight: '#52c41a',
  psychology: '#722ed1'
}

// 教练数据
const coach = ref<any>({
  coach_id: '',
  name: '',
  avatar: '',
  phone: '',
  email: '',
  level: 'L0',
  specialty: [],
  student_count: 0,
  case_count: 0,
  mentoring_hours: 0,
  status: 'active',
  joined_at: '',
  last_active: '',
  bio: '',
  certificates: []
})

// 课程进度
const courseProgress = ref([
  { course_id: '1', course_name: '行为健康入门', progress: 100, status: 'completed', completed_at: '2025-12-15' },
  { course_id: '2', course_name: '慢病管理基础', progress: 80, status: 'ongoing', completed_at: null },
  { course_id: '3', course_name: '动机访谈技术', progress: 45, status: 'ongoing', completed_at: null }
])

const courseColumns = [
  { title: '课程名称', dataIndex: 'course_name' },
  { title: '学习进度', key: 'progress', width: 150 },
  { title: '状态', key: 'status', width: 100 },
  { title: '完成时间', dataIndex: 'completed_at', width: 120 }
]

// 考试成绩
const examResults = ref([
  { exam_id: '1', exam_name: 'L1 理论考试', score: 85, passing_score: 60, passed: true, date: '2025-12-20' },
  { exam_id: '2', exam_name: 'L1 案例模拟', score: 78, passing_score: 70, passed: true, date: '2025-12-22' }
])

const examColumns = [
  { title: '考试名称', dataIndex: 'exam_name' },
  { title: '成绩', key: 'score', width: 100 },
  { title: '状态', key: 'status', width: 100 },
  { title: '考试时间', dataIndex: 'date', width: 120 }
]

// 晋级历史
const promotionHistory = ref([
  { id: '1', from_level: 'L0', to_level: 'L1', date: '2025-11-01', approved: true, comment: '考核通过，学习表现优秀' },
  { id: '2', from_level: 'L1', to_level: 'L2', date: '2026-01-15', approved: true, comment: '案例数量达标，督导评价良好' }
])

// 学员列表
const students = ref([
  { id: '1', name: '王小明', phone: '138****0001', progress: 65, active: true, last_active: '今天' },
  { id: '2', name: '李小红', phone: '138****0002', progress: 30, active: true, last_active: '昨天' },
  { id: '3', name: '张小强', phone: '138****0003', progress: 85, active: false, last_active: '3天前' }
])

const studentColumns = [
  { title: '学员', key: 'name' },
  { title: '手机号', dataIndex: 'phone', width: 120 },
  { title: '学习进度', key: 'progress', width: 150 },
  { title: '状态', key: 'status', width: 100 },
  { title: '最后活跃', dataIndex: 'last_active', width: 100 }
]

// 案例记录
const cases = ref([
  { id: '1', title: '2型糖尿病逆转案例', type: 'diabetes', description: '患者男性，52岁，通过8周干预成功逆转糖尿病前期...', date: '2026-01-10' },
  { id: '2', title: '高血压综合管理', type: 'hypertension', description: '患者女性，48岁，高血压3年，通过生活方式干预...', date: '2026-01-05' },
  { id: '3', title: '体重管理成功案例', type: 'weight', description: '患者男性，35岁，BMI 32，12周减重12公斤...', date: '2025-12-28' }
])

// 督导记录
const mentoringRecords = ref([
  { id: '1', supervisor_name: '孙七', topic: '案例讨论：糖尿病患者沟通技巧', duration: 60, rating: 5, date: '2026-01-20', feedback: '表现出色' },
  { id: '2', supervisor_name: '孙七', topic: '技能培训：动机访谈实践', duration: 90, rating: 4, date: '2026-01-15', feedback: '需要加强提问技巧' }
])

const mentoringColumns = [
  { title: '督导师', key: 'supervisor' },
  { title: '主题', dataIndex: 'topic', ellipsis: true },
  { title: '时长(分钟)', dataIndex: 'duration', width: 100 },
  { title: '评分', key: 'rating', width: 120 },
  { title: '日期', dataIndex: 'date', width: 100 }
]

// 消息表单
const messageForm = reactive({
  type: 'remind',
  content: ''
})

// 计算属性
const completedCourses = computed(() => courseProgress.value.filter(c => c.status === 'completed').length)
const ongoingCourses = computed(() => courseProgress.value.filter(c => c.status === 'ongoing').length)
const avgExamScore = computed(() => {
  if (examResults.value.length === 0) return 0
  const total = examResults.value.reduce((sum, e) => sum + e.score, 0)
  return Math.round(total / examResults.value.length)
})

// 方法
const formatTime = (time: string) => {
  if (!time) return '-'
  return dayjs(time).fromNow()
}

const onTabChange = (key: string) => {
  activeTab.value = key
}

const handleEdit = () => {
  router.push(`/coach/list?edit=${coachId.value}`)
}

const handlePromotion = () => {
  router.push(`/coach/review?coach_id=${coachId.value}`)
}

const handleMessage = () => {
  messageForm.type = 'remind'
  messageForm.content = ''
  messageModalVisible.value = true
}

const handleSendMessage = () => {
  if (!messageForm.content) {
    message.error('请输入消息内容')
    return
  }
  message.success(`消息已发送给 ${coach.value.name}`)
  messageModalVisible.value = false
}

// 加载数据
const loadCoachData = async () => {
  loading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 500))

    // 模拟数据
    coach.value = {
      coach_id: coachId.value || 'C001',
      name: '张三',
      avatar: '',
      phone: '13800138001',
      email: 'zhangsan@example.com',
      level: 'L2',
      specialty: ['diabetes_reversal', 'weight_management'],
      student_count: 28,
      case_count: 45,
      mentoring_hours: 36,
      status: 'active',
      joined_at: '2024-03-15',
      last_active: '2026-01-24T10:30:00Z',
      bio: '5年健康管理经验，专注于糖尿病逆转和体重管理领域',
      certificates: [
        { id: '1', name: '健康管理师（二级）', issuer: '人力资源和社会保障部', expiry_date: '2027-06-30', image: '' },
        { id: '2', name: '营养师资格证', issuer: '中国营养学会', expiry_date: null, image: '' },
        { id: '3', name: '心理咨询师', issuer: '中科院心理所', expiry_date: '2028-12-31', image: '' }
      ]
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadCoachData()
})
</script>

<style scoped>
.coach-detail {
  padding: 0;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 20px;
}

.profile-info h2 {
  margin: 0 0 8px 0;
}

.level-badge {
  display: flex;
  align-items: center;
  gap: 12px;
}

.profile-stats {
  display: flex;
  justify-content: space-around;
  text-align: center;
}

.stat-item {
  padding: 0 16px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #1890ff;
}

.stat-label {
  font-size: 12px;
  color: #999;
}

.tab-content {
  min-height: 400px;
}

.certificate-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.certificate-item :deep(.ant-card-cover) {
  padding: 16px;
  background: #f5f5f5;
}

.cert-image {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.cert-image img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.cert-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.timeline-item {
  padding-bottom: 8px;
}

.timeline-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.timeline-title {
  font-weight: 500;
  font-size: 15px;
}

.timeline-time {
  font-size: 12px;
  color: #999;
  margin: 4px 0;
}

.timeline-content {
  font-size: 13px;
  color: #666;
}

.student-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.supervisor-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

h4 {
  margin: 0 0 12px 0;
  font-size: 15px;
  font-weight: 500;
}
</style>
