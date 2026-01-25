<template>
  <div class="promotion-review">
    <div class="page-header">
      <h2>晋级审核</h2>
      <a-radio-group v-model:value="statusFilter" button-style="solid">
        <a-radio-button value="all">全部</a-radio-button>
        <a-radio-button value="pending">
          待审核 <a-badge :count="pendingCount" :offset="[8, -2]" />
        </a-radio-button>
        <a-radio-button value="approved">已通过</a-radio-button>
        <a-radio-button value="rejected">已拒绝</a-radio-button>
      </a-radio-group>
    </div>

    <!-- 统计卡片 -->
    <a-row :gutter="16" class="stats-row">
      <a-col :span="6">
        <a-card>
          <a-statistic title="待审核申请" :value="pendingCount" :value-style="{ color: '#faad14' }">
            <template #prefix><ClockCircleOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="本月通过" :value="approvedThisMonth" :value-style="{ color: '#52c41a' }">
            <template #prefix><CheckCircleOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="本月拒绝" :value="rejectedThisMonth" :value-style="{ color: '#ff4d4f' }">
            <template #prefix><CloseCircleOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="通过率" :value="passRate" suffix="%" :value-style="{ color: '#1890ff' }" />
        </a-card>
      </a-col>
    </a-row>

    <!-- 申请列表 -->
    <a-card>
      <a-table
        :dataSource="filteredApplications"
        :columns="columns"
        :loading="loading"
        :pagination="pagination"
        rowKey="application_id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'coach'">
            <div class="coach-info">
              <a-avatar :size="40">{{ record.coach_name?.[0] }}</a-avatar>
              <div class="coach-detail">
                <div class="coach-name">{{ record.coach_name }}</div>
                <div class="coach-phone">{{ record.coach_phone }}</div>
              </div>
            </div>
          </template>

          <template v-else-if="column.key === 'level'">
            <div class="level-change">
              <a-tag :color="levelColors[record.current_level]">{{ record.current_level }}</a-tag>
              <ArrowRightOutlined style="margin: 0 8px; color: #999" />
              <a-tag :color="levelColors[record.target_level]">{{ record.target_level }}</a-tag>
            </div>
          </template>

          <template v-else-if="column.key === 'requirements'">
            <div class="requirements-check">
              <a-tooltip title="课程完成">
                <span :class="['req-item', { met: record.requirements_met.courses_completed }]">
                  <BookOutlined />
                </span>
              </a-tooltip>
              <a-tooltip title="考试通过">
                <span :class="['req-item', { met: record.requirements_met.exams_passed }]">
                  <FileTextOutlined />
                </span>
              </a-tooltip>
              <a-tooltip title="案例数量">
                <span :class="['req-item', { met: record.requirements_met.cases_count }]">
                  <SolutionOutlined />
                </span>
              </a-tooltip>
              <a-tooltip title="督导时长">
                <span :class="['req-item', { met: record.requirements_met.mentoring_hours }]">
                  <TeamOutlined />
                </span>
              </a-tooltip>
            </div>
          </template>

          <template v-else-if="column.key === 'status'">
            <a-tag :color="statusColors[record.status]">
              {{ statusLabels[record.status] }}
            </a-tag>
          </template>

          <template v-else-if="column.key === 'action'">
            <a-space>
              <a @click="viewApplication(record)">查看</a>
              <template v-if="record.status === 'pending'">
                <a-divider type="vertical" />
                <a style="color: #52c41a" @click="handleApprove(record)">通过</a>
                <a style="color: #ff4d4f" @click="handleReject(record)">拒绝</a>
              </template>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 申请详情弹窗 -->
    <a-modal
      v-model:open="detailVisible"
      title="晋级申请详情"
      width="800px"
      :footer="currentApplication?.status === 'pending' ? undefined : null"
      @ok="handleDetailOk"
    >
      <template v-if="currentApplication">
        <a-descriptions :column="2" bordered size="small">
          <a-descriptions-item label="申请人">
            <div class="coach-info">
              <a-avatar :size="32">{{ currentApplication.coach_name?.[0] }}</a-avatar>
              <span style="margin-left: 8px">{{ currentApplication.coach_name }}</span>
            </div>
          </a-descriptions-item>
          <a-descriptions-item label="申请时间">{{ currentApplication.applied_at }}</a-descriptions-item>
          <a-descriptions-item label="当前等级">
            <a-tag :color="levelColors[currentApplication.current_level]">
              {{ levelLabels[currentApplication.current_level] }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="目标等级">
            <a-tag :color="levelColors[currentApplication.target_level]">
              {{ levelLabels[currentApplication.target_level] }}
            </a-tag>
          </a-descriptions-item>
        </a-descriptions>

        <a-divider>晋级条件检查</a-divider>

        <a-row :gutter="16">
          <a-col :span="6">
            <a-card size="small" :class="{ 'condition-met': currentApplication.requirements_met.courses_completed }">
              <a-statistic
                title="课程完成"
                :value="currentApplication.course_stats?.completed || 0"
                :suffix="`/ ${currentApplication.course_stats?.required || 0}`"
              >
                <template #prefix>
                  <CheckCircleOutlined v-if="currentApplication.requirements_met.courses_completed" style="color: #52c41a" />
                  <CloseCircleOutlined v-else style="color: #ff4d4f" />
                </template>
              </a-statistic>
            </a-card>
          </a-col>
          <a-col :span="6">
            <a-card size="small" :class="{ 'condition-met': currentApplication.requirements_met.exams_passed }">
              <a-statistic
                title="考试通过"
                :value="currentApplication.exam_stats?.passed || 0"
                :suffix="`/ ${currentApplication.exam_stats?.required || 0}`"
              >
                <template #prefix>
                  <CheckCircleOutlined v-if="currentApplication.requirements_met.exams_passed" style="color: #52c41a" />
                  <CloseCircleOutlined v-else style="color: #ff4d4f" />
                </template>
              </a-statistic>
            </a-card>
          </a-col>
          <a-col :span="6">
            <a-card size="small" :class="{ 'condition-met': currentApplication.requirements_met.cases_count }">
              <a-statistic
                title="案例数量"
                :value="currentApplication.case_stats?.count || 0"
                :suffix="`/ ${currentApplication.case_stats?.required || 0}`"
              >
                <template #prefix>
                  <CheckCircleOutlined v-if="currentApplication.requirements_met.cases_count" style="color: #52c41a" />
                  <CloseCircleOutlined v-else style="color: #ff4d4f" />
                </template>
              </a-statistic>
            </a-card>
          </a-col>
          <a-col :span="6">
            <a-card size="small" :class="{ 'condition-met': currentApplication.requirements_met.mentoring_hours }">
              <a-statistic
                title="督导时长"
                :value="currentApplication.mentoring_stats?.hours || 0"
                :suffix="`/ ${currentApplication.mentoring_stats?.required || 0}h`"
              >
                <template #prefix>
                  <CheckCircleOutlined v-if="currentApplication.requirements_met.mentoring_hours" style="color: #52c41a" />
                  <CloseCircleOutlined v-else style="color: #ff4d4f" />
                </template>
              </a-statistic>
            </a-card>
          </a-col>
        </a-row>

        <a-divider>申请材料</a-divider>

        <div class="materials-section" v-if="currentApplication.materials?.length > 0">
          <div v-for="(material, index) in currentApplication.materials" :key="index" class="material-item">
            <FileOutlined />
            <a :href="material.url" target="_blank">{{ material.name }}</a>
          </div>
        </div>
        <a-empty v-else description="暂无申请材料" :image="Empty.PRESENTED_IMAGE_SIMPLE" />

        <template v-if="currentApplication.status !== 'pending'">
          <a-divider>审核结果</a-divider>
          <a-descriptions :column="1" size="small">
            <a-descriptions-item label="审核状态">
              <a-tag :color="statusColors[currentApplication.status]">
                {{ statusLabels[currentApplication.status] }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="审核人">{{ currentApplication.reviewer }}</a-descriptions-item>
            <a-descriptions-item label="审核时间">{{ currentApplication.reviewed_at }}</a-descriptions-item>
            <a-descriptions-item label="审核意见">{{ currentApplication.review_comment || '-' }}</a-descriptions-item>
          </a-descriptions>
        </template>

        <template v-if="currentApplication.status === 'pending'">
          <a-divider>审核操作</a-divider>
          <a-form layout="vertical">
            <a-form-item label="审核结果">
              <a-radio-group v-model:value="reviewForm.result" button-style="solid">
                <a-radio-button value="approved">
                  <CheckCircleOutlined /> 通过
                </a-radio-button>
                <a-radio-button value="rejected">
                  <CloseCircleOutlined /> 拒绝
                </a-radio-button>
              </a-radio-group>
            </a-form-item>
            <a-form-item label="审核意见">
              <a-textarea
                v-model:value="reviewForm.comment"
                placeholder="请输入审核意见"
                :rows="3"
              />
            </a-form-item>
          </a-form>
        </template>
      </template>

      <template #footer v-if="currentApplication?.status === 'pending'">
        <a-button @click="detailVisible = false">取消</a-button>
        <a-button type="primary" :loading="submitting" @click="handleDetailOk">
          提交审核
        </a-button>
      </template>
    </a-modal>

    <!-- 快速审核弹窗 -->
    <a-modal
      v-model:open="quickReviewVisible"
      :title="quickReviewType === 'approve' ? '通过申请' : '拒绝申请'"
      @ok="handleQuickReviewConfirm"
      :confirmLoading="submitting"
    >
      <p v-if="currentApplication">
        确定要{{ quickReviewType === 'approve' ? '通过' : '拒绝' }}
        <strong>{{ currentApplication.coach_name }}</strong>
        的晋级申请（{{ currentApplication.current_level }} -> {{ currentApplication.target_level }}）吗？
      </p>
      <a-form-item label="审核意见">
        <a-textarea
          v-model:value="reviewForm.comment"
          placeholder="请输入审核意见（可选）"
          :rows="3"
        />
      </a-form-item>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { message, Empty } from 'ant-design-vue'
import {
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ArrowRightOutlined,
  BookOutlined,
  FileTextOutlined,
  SolutionOutlined,
  TeamOutlined,
  FileOutlined
} from '@ant-design/icons-vue'

// 接口定义
interface PromotionApplication {
  application_id: string
  coach_id: string
  coach_name: string
  coach_phone: string
  current_level: string
  target_level: string
  applied_at: string
  status: 'pending' | 'approved' | 'rejected'
  requirements_met: {
    courses_completed: boolean
    exams_passed: boolean
    cases_count: boolean
    mentoring_hours: boolean
  }
  course_stats?: { completed: number; required: number }
  exam_stats?: { passed: number; required: number }
  case_stats?: { count: number; required: number }
  mentoring_stats?: { hours: number; required: number }
  materials: { name: string; url: string }[]
  reviewer?: string
  reviewed_at?: string
  review_comment?: string
}

// 状态
const loading = ref(false)
const submitting = ref(false)
const statusFilter = ref('all')
const detailVisible = ref(false)
const quickReviewVisible = ref(false)
const quickReviewType = ref<'approve' | 'reject'>('approve')
const currentApplication = ref<PromotionApplication | null>(null)

// 分页
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条记录`
})

// 表格列
const columns = [
  { title: '申请人', key: 'coach', width: 180 },
  { title: '等级变更', key: 'level', width: 180 },
  { title: '条件满足', key: 'requirements', width: 140 },
  { title: '申请时间', dataIndex: 'applied_at', width: 120 },
  { title: '状态', key: 'status', width: 100 },
  { title: '操作', key: 'action', width: 150, fixed: 'right' }
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

const statusLabels: Record<string, string> = {
  pending: '待审核',
  approved: '已通过',
  rejected: '已拒绝'
}

const statusColors: Record<string, string> = {
  pending: 'warning',
  approved: 'success',
  rejected: 'error'
}

// 审核表单
const reviewForm = reactive({
  result: 'approved' as 'approved' | 'rejected',
  comment: ''
})

// 模拟数据
const applications = ref<PromotionApplication[]>([
  {
    application_id: 'A001',
    coach_id: 'C002',
    coach_name: '李四',
    coach_phone: '138****8002',
    current_level: 'L1',
    target_level: 'L2',
    applied_at: '2026-01-20',
    status: 'pending',
    requirements_met: {
      courses_completed: true,
      exams_passed: true,
      cases_count: true,
      mentoring_hours: false
    },
    course_stats: { completed: 5, required: 5 },
    exam_stats: { passed: 2, required: 2 },
    case_stats: { count: 25, required: 20 },
    mentoring_stats: { hours: 8, required: 10 },
    materials: [
      { name: '案例报告汇总.pdf', url: '#' },
      { name: '督导评价表.pdf', url: '#' }
    ]
  },
  {
    application_id: 'A002',
    coach_id: 'C003',
    coach_name: '王五',
    coach_phone: '138****8003',
    current_level: 'L2',
    target_level: 'L3',
    applied_at: '2026-01-18',
    status: 'pending',
    requirements_met: {
      courses_completed: true,
      exams_passed: true,
      cases_count: true,
      mentoring_hours: true
    },
    course_stats: { completed: 8, required: 8 },
    exam_stats: { passed: 3, required: 3 },
    case_stats: { count: 60, required: 50 },
    mentoring_stats: { hours: 25, required: 20 },
    materials: [
      { name: '高级案例报告.pdf', url: '#' },
      { name: '带教学员记录.xlsx', url: '#' },
      { name: '督导推荐信.pdf', url: '#' }
    ]
  },
  {
    application_id: 'A003',
    coach_id: 'C001',
    coach_name: '张三',
    coach_phone: '138****8001',
    current_level: 'L1',
    target_level: 'L2',
    applied_at: '2026-01-15',
    status: 'approved',
    requirements_met: {
      courses_completed: true,
      exams_passed: true,
      cases_count: true,
      mentoring_hours: true
    },
    course_stats: { completed: 5, required: 5 },
    exam_stats: { passed: 2, required: 2 },
    case_stats: { count: 30, required: 20 },
    mentoring_stats: { hours: 15, required: 10 },
    materials: [],
    reviewer: '管理员',
    reviewed_at: '2026-01-16',
    review_comment: '考核全部通过，表现优秀'
  },
  {
    application_id: 'A004',
    coach_id: 'C004',
    coach_name: '赵六',
    coach_phone: '138****8004',
    current_level: 'L0',
    target_level: 'L1',
    applied_at: '2026-01-10',
    status: 'rejected',
    requirements_met: {
      courses_completed: true,
      exams_passed: false,
      cases_count: false,
      mentoring_hours: false
    },
    course_stats: { completed: 3, required: 3 },
    exam_stats: { passed: 0, required: 1 },
    case_stats: { count: 0, required: 5 },
    mentoring_stats: { hours: 0, required: 0 },
    materials: [],
    reviewer: '管理员',
    reviewed_at: '2026-01-12',
    review_comment: '考试未通过，案例数量不足，建议继续学习后再申请'
  }
])

// 计算属性
const filteredApplications = computed(() => {
  if (statusFilter.value === 'all') {
    return applications.value
  }
  return applications.value.filter(a => a.status === statusFilter.value)
})

const pendingCount = computed(() => applications.value.filter(a => a.status === 'pending').length)
const approvedThisMonth = computed(() => applications.value.filter(a => a.status === 'approved').length)
const rejectedThisMonth = computed(() => applications.value.filter(a => a.status === 'rejected').length)
const passRate = computed(() => {
  const total = approvedThisMonth.value + rejectedThisMonth.value
  if (total === 0) return 0
  return Math.round((approvedThisMonth.value / total) * 100)
})

// 方法
const viewApplication = (record: PromotionApplication) => {
  currentApplication.value = record
  reviewForm.result = 'approved'
  reviewForm.comment = ''
  detailVisible.value = true
}

const handleApprove = (record: PromotionApplication) => {
  currentApplication.value = record
  quickReviewType.value = 'approve'
  reviewForm.comment = ''
  quickReviewVisible.value = true
}

const handleReject = (record: PromotionApplication) => {
  currentApplication.value = record
  quickReviewType.value = 'reject'
  reviewForm.comment = ''
  quickReviewVisible.value = true
}

const handleDetailOk = async () => {
  if (!currentApplication.value) return

  submitting.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 500))

    const index = applications.value.findIndex(a => a.application_id === currentApplication.value?.application_id)
    if (index > -1) {
      applications.value[index] = {
        ...applications.value[index],
        status: reviewForm.result,
        reviewer: '管理员',
        reviewed_at: new Date().toISOString().split('T')[0],
        review_comment: reviewForm.comment
      }
    }

    message.success(reviewForm.result === 'approved' ? '申请已通过' : '申请已拒绝')
    detailVisible.value = false
  } finally {
    submitting.value = false
  }
}

const handleQuickReviewConfirm = async () => {
  if (!currentApplication.value) return

  submitting.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 500))

    const status = quickReviewType.value === 'approve' ? 'approved' : 'rejected'
    const index = applications.value.findIndex(a => a.application_id === currentApplication.value?.application_id)
    if (index > -1) {
      applications.value[index] = {
        ...applications.value[index],
        status,
        reviewer: '管理员',
        reviewed_at: new Date().toISOString().split('T')[0],
        review_comment: reviewForm.comment
      }
    }

    message.success(status === 'approved' ? '申请已通过' : '申请已拒绝')
    quickReviewVisible.value = false
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.promotion-review {
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

.level-change {
  display: flex;
  align-items: center;
}

.requirements-check {
  display: flex;
  gap: 8px;
}

.req-item {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #f5f5f5;
  color: #d9d9d9;
  font-size: 14px;
}

.req-item.met {
  background: #f6ffed;
  color: #52c41a;
}

.condition-met {
  border-color: #b7eb8f;
  background: #f6ffed;
}

.materials-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.material-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #fafafa;
  border-radius: 4px;
}

.material-item a {
  color: #1890ff;
}
</style>
