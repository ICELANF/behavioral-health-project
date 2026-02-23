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

    <a-alert v-if="error" :message="error" type="error" show-icon style="margin-bottom: 16px" />

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
    <a-spin :spinning="loading">
      <div class="list-card-container">
        <a-empty v-if="filteredApplications.length === 0 && !loading" description="暂无晋级申请" />
        <ListCard v-for="record in filteredApplications" :key="record.application_id" @click="viewApplication(record)">
          <template #avatar>
            <a-avatar :size="40">{{ record.coach_name?.[0] }}</a-avatar>
          </template>
          <template #title>
            <span>{{ record.coach_name }}</span>
            <a-tag :color="statusColors[record.status]" size="small" style="margin-left: 8px">{{ statusLabels[record.status] }}</a-tag>
          </template>
          <template #subtitle>
            <div class="level-change">
              <a-tag :color="levelColors[record.current_level]" size="small">{{ record.current_level }}</a-tag>
              <ArrowRightOutlined style="margin: 0 4px; color: #999; font-size: 11px" />
              <a-tag :color="levelColors[record.target_level]" size="small">{{ record.target_level }}</a-tag>
            </div>
            <span style="color: #999; margin-left: 8px">{{ record.coach_phone }}</span>
          </template>
          <template #meta>
            <div class="requirements-check">
              <a-tooltip title="课程完成"><span :class="['req-item', { met: record.requirements_met.courses_completed }]"><BookOutlined /></span></a-tooltip>
              <a-tooltip title="考试通过"><span :class="['req-item', { met: record.requirements_met.exams_passed }]"><FileTextOutlined /></span></a-tooltip>
              <a-tooltip title="案例数量"><span :class="['req-item', { met: record.requirements_met.cases_count }]"><SolutionOutlined /></span></a-tooltip>
              <a-tooltip title="督导时长"><span :class="['req-item', { met: record.requirements_met.mentoring_hours }]"><TeamOutlined /></span></a-tooltip>
            </div>
            <span style="color: #999">{{ record.applied_at }}</span>
          </template>
          <template #actions>
            <a-button type="link" size="small" @click.stop="viewApplication(record)">查看</a-button>
            <template v-if="record.status === 'pending'">
              <a-button type="link" size="small" style="color: #52c41a" @click.stop="handleApprove(record)">通过</a-button>
              <a-button type="link" size="small" danger @click.stop="handleReject(record)">拒绝</a-button>
            </template>
          </template>
        </ListCard>
      </div>
    </a-spin>

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
import { ref, reactive, computed, onMounted } from 'vue'
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
import request from '@/api/request'
import ListCard from '@/components/core/ListCard.vue'

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
const error = ref('')
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

// columns removed — using ListCard layout

// 常量
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

const applications = ref<PromotionApplication[]>([])

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

const submitReview = async (appId: string, action: 'approve' | 'reject', comment: string) => {
  await request.post(`/v1/promotion/review/${appId}`, {
    approved: action === 'approve',
    reason: comment,
  })
}

const handleDetailOk = async () => {
  if (!currentApplication.value) return

  submitting.value = true
  try {
    await submitReview(
      currentApplication.value.application_id,
      reviewForm.result === 'approved' ? 'approve' : 'reject',
      reviewForm.comment
    )
    message.success(reviewForm.result === 'approved' ? '申请已通过' : '申请已拒绝')
    detailVisible.value = false
    await loadApplications()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleQuickReviewConfirm = async () => {
  if (!currentApplication.value) return

  submitting.value = true
  try {
    await submitReview(
      currentApplication.value.application_id,
      quickReviewType.value,
      reviewForm.comment
    )
    message.success(quickReviewType.value === 'approve' ? '申请已通过' : '申请已拒绝')
    quickReviewVisible.value = false
    await loadApplications()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

function mapApplication(raw: any): PromotionApplication {
  return {
    application_id: String(raw.application_id ?? raw.id ?? ''),
    coach_id: String(raw.user_id ?? raw.coach_id ?? ''),
    coach_name: raw.coach_name || raw.full_name || raw.username || '',
    coach_phone: raw.coach_phone || raw.phone || '',
    current_level: raw.current_level || raw.from_role || '',
    target_level: raw.target_level || raw.to_role || '',
    applied_at: raw.applied_at || raw.created_at || '',
    status: raw.status || 'pending',
    requirements_met: raw.requirements_met || {
      courses_completed: false,
      exams_passed: false,
      cases_count: false,
      mentoring_hours: false,
    },
    course_stats: raw.course_stats || { completed: 0, required: 0 },
    exam_stats: raw.exam_stats || { passed: 0, required: 0 },
    case_stats: raw.case_stats || { count: 0, required: 0 },
    mentoring_stats: raw.mentoring_stats || { hours: 0, required: 0 },
    materials: raw.materials || [],
    reviewer: raw.reviewer || raw.reviewer_name || '',
    reviewed_at: raw.reviewed_at || '',
    review_comment: raw.review_comment || raw.reviewer_comment || '',
  }
}

const loadApplications = async () => {
  loading.value = true
  error.value = ''
  try {
    const { data } = await request.get('/v1/promotion/applications', { params: { status: statusFilter.value !== 'all' ? statusFilter.value : undefined } })
    const raw = data.applications || data.items || data || []
    applications.value = (Array.isArray(raw) ? raw : []).map(mapApplication)
    pagination.total = applications.value.length
  } catch (e: any) {
    console.error('加载晋级申请失败:', e)
    error.value = '加载晋级申请失败'
    applications.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadApplications()
})
</script>

<style scoped>
.promotion-review {
  padding: 0;
}

.list-card-container { display: flex; flex-direction: column; gap: 10px; }

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
