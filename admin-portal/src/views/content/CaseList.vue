<template>
  <div class="case-list">
    <!-- 筛选区 -->
    <a-card class="filter-card">
      <a-form layout="inline">
        <a-form-item label="关键词">
          <a-input v-model:value="filters.keyword" placeholder="搜索标题" allow-clear style="width: 180px" />
        </a-form-item>
        <a-form-item label="来源">
          <a-select v-model:value="filters.source" placeholder="全部来源" allow-clear style="width: 120px">
            <a-select-option value="sharer">用户分享</a-select-option>
            <a-select-option value="coach">教练</a-select-option>
            <a-select-option value="expert">专家</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="领域">
          <a-select v-model:value="filters.domain" placeholder="全部领域" allow-clear style="width: 120px">
            <a-select-option v-for="domain in TRIGGER_DOMAINS" :key="domain.value" :value="domain.value">
              {{ domain.label }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="审核状态">
          <a-select v-model:value="filters.reviewStatus" placeholder="全部" allow-clear style="width: 100px">
            <a-select-option value="pending">待审核</a-select-option>
            <a-select-option value="approved">已通过</a-select-option>
            <a-select-option value="rejected">已拒绝</a-select-option>
            <a-select-option value="revision">待修改</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item>
          <a-button type="primary" @click="handleSearch">
            <template #icon><SearchOutlined /></template>
            搜索
          </a-button>
          <a-button style="margin-left: 8px" @click="handleReset">重置</a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 统计卡片 -->
    <a-row :gutter="16" class="stats-row">
      <a-col :span="6">
        <a-card class="stat-card">
          <a-statistic title="待审核" :value="stats.pending" :value-style="{ color: '#faad14' }">
            <template #suffix>篇</template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stat-card">
          <a-statistic title="已发布" :value="stats.published" :value-style="{ color: '#52c41a' }">
            <template #suffix>篇</template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stat-card">
          <a-statistic title="本周新增" :value="stats.weekNew" :value-style="{ color: '#1890ff' }">
            <template #suffix>篇</template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stat-card">
          <a-statistic title="累计点赞" :value="stats.totalLikes" :value-style="{ color: '#eb2f96' }">
            <template #suffix>次</template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <!-- 案例列表 -->
    <a-table
      :columns="columns"
      :data-source="cases"
      :loading="loading"
      :pagination="pagination"
      row-key="case_id"
      @change="handleTableChange"
    >
      <!-- 案例信息 -->
      <template #caseInfo="{ record }">
        <div class="case-info-cell">
          <div class="case-title">
            {{ record.title }}
            <a-tag v-if="record.is_anonymous" size="small">匿名</a-tag>
          </div>
          <div class="case-meta">
            <a-tag :color="getSourceColor(record.source)" size="small">{{ getSourceLabel(record.source) }}</a-tag>
            <span class="domain-tag">{{ getDomainLabel(record.domain) }}</span>
          </div>
          <div class="case-excerpt">
            {{ truncate(record.challenge, 60) }}
          </div>
        </div>
      </template>

      <!-- 作者 -->
      <template #author="{ record }">
        <div class="author-cell">
          <span class="display-name">{{ record.display_name }}</span>
          <div class="author-role">{{ record.author_role }}</div>
        </div>
      </template>

      <!-- 审核状态 -->
      <template #reviewStatus="{ record }">
        <a-tag :color="getReviewStatusColor(record.review_status)">
          {{ getReviewStatusLabel(record.review_status) }}
        </a-tag>
        <div v-if="record.reviewed_at" class="review-time">
          {{ formatDate(record.reviewed_at) }}
        </div>
      </template>

      <!-- 互动数据 -->
      <template #interactions="{ record }">
        <div class="interaction-cell">
          <span><LikeOutlined /> {{ record.like_count }}</span>
          <span><CheckCircleOutlined /> {{ record.helpful_count }}</span>
          <span><MessageOutlined /> {{ record.comment_count }}</span>
        </div>
      </template>

      <!-- 操作 -->
      <template #action="{ record }">
        <a-space>
          <a @click="handleView(record)">查看</a>
          <a v-if="record.review_status === 'pending'" @click="handleReview(record)" style="color: #faad14">
            审核
          </a>
          <a-dropdown>
            <a>更多 <DownOutlined /></a>
            <template #overlay>
              <a-menu>
                <a-menu-item v-if="record.status === 'published'" @click="handleFeature(record)">
                  <StarOutlined /> 设为精选
                </a-menu-item>
                <a-menu-item v-if="record.status === 'published'" @click="handleOffline(record)">
                  下架
                </a-menu-item>
                <a-menu-divider />
                <a-menu-item danger @click="handleDelete(record)">
                  删除
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </a-space>
      </template>
    </a-table>

    <!-- 查看/审核弹窗 -->
    <a-modal
      v-model:open="viewModalVisible"
      :title="currentCase?.title"
      width="700px"
      :footer="reviewMode ? undefined : null"
    >
      <template v-if="currentCase">
        <a-descriptions :column="2" bordered size="small" class="case-detail-desc">
          <a-descriptions-item label="作者">
            {{ currentCase.display_name }}
            <a-tag v-if="currentCase.is_anonymous" size="small">匿名</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="角色">{{ currentCase.author_role }}</a-descriptions-item>
          <a-descriptions-item label="领域">{{ getDomainLabel(currentCase.domain) }}</a-descriptions-item>
          <a-descriptions-item label="来源">{{ getSourceLabel(currentCase.source) }}</a-descriptions-item>
          <a-descriptions-item label="提交时间" :span="2">{{ formatDateTime(currentCase.created_at) }}</a-descriptions-item>
        </a-descriptions>

        <a-divider>案例内容</a-divider>

        <div class="case-section">
          <h4>遇到的问题</h4>
          <p>{{ currentCase.challenge }}</p>
        </div>

        <div class="case-section">
          <h4>采取的方法</h4>
          <p>{{ currentCase.approach }}</p>
        </div>

        <div class="case-section">
          <h4>结果与收获</h4>
          <p>{{ currentCase.outcome }}</p>
        </div>

        <div v-if="currentCase.reflection" class="case-section">
          <h4>心得反思</h4>
          <p>{{ currentCase.reflection }}</p>
        </div>

        <!-- 审核区域 -->
        <template v-if="reviewMode">
          <a-divider>审核操作</a-divider>
          <a-form :model="reviewForm" layout="vertical">
            <a-form-item label="审核检查">
              <a-checkbox-group v-model:value="reviewForm.checklist" :options="checklistOptions" />
            </a-form-item>
            <a-form-item label="审核意见">
              <a-textarea v-model:value="reviewForm.comments" :rows="3" placeholder="请输入审核意见" />
            </a-form-item>
            <a-form-item v-if="reviewForm.decision === 'revision'" label="修改建议">
              <a-textarea v-model:value="reviewForm.revision_notes" :rows="2" placeholder="请说明需要修改的内容" />
            </a-form-item>
          </a-form>
        </template>
      </template>

      <template #footer v-if="reviewMode">
        <a-space>
          <a-button @click="viewModalVisible = false">取消</a-button>
          <a-button type="primary" danger @click="submitReview('rejected')">
            拒绝
          </a-button>
          <a-button type="default" @click="submitReview('revision')">
            需修改
          </a-button>
          <a-button type="primary" @click="submitReview('approved')">
            通过
          </a-button>
        </a-space>
      </template>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import {
  SearchOutlined,
  LikeOutlined,
  MessageOutlined,
  CheckCircleOutlined,
  DownOutlined,
  StarOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import type { CaseShare, ContentSource, ReviewStatus } from '@/types/content'
import { CONTENT_SOURCE_CONFIG } from '@/types/content'
import { TRIGGER_DOMAINS } from '@/constants'

// 筛选
const filters = reactive({
  keyword: '',
  source: undefined as ContentSource | undefined,
  domain: undefined as string | undefined,
  reviewStatus: undefined as ReviewStatus | undefined
})

// 统计
const stats = reactive({
  pending: 12,
  published: 156,
  weekNew: 8,
  totalLikes: 4523
})

// 表格
const loading = ref(false)
const cases = ref<CaseShare[]>([])
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`
})

// 查看/审核弹窗
const viewModalVisible = ref(false)
const currentCase = ref<CaseShare | null>(null)
const reviewMode = ref(false)
const reviewForm = reactive({
  checklist: [] as string[],
  comments: '',
  revision_notes: '',
  decision: '' as ReviewStatus
})

const checklistOptions = [
  { label: '内容真实可信', value: 'authentic' },
  { label: '无敏感信息', value: 'no_sensitive' },
  { label: '无医学诊断声称', value: 'no_medical' },
  { label: '隐私已保护', value: 'privacy' },
  { label: '质量达标', value: 'quality' }
]

// 列配置
const columns = [
  {
    title: '案例信息',
    key: 'caseInfo',
    width: 350,
    slots: { customRender: 'caseInfo' }
  },
  {
    title: '作者',
    key: 'author',
    width: 120,
    slots: { customRender: 'author' }
  },
  {
    title: '审核状态',
    key: 'reviewStatus',
    width: 120,
    slots: { customRender: 'reviewStatus' }
  },
  {
    title: '互动',
    key: 'interactions',
    width: 150,
    slots: { customRender: 'interactions' }
  },
  {
    title: '提交时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 110,
    customRender: ({ text }: { text: string }) => formatDate(text)
  },
  {
    title: '操作',
    key: 'action',
    width: 140,
    fixed: 'right',
    slots: { customRender: 'action' }
  }
]

// 辅助函数
const getSourceLabel = (source: ContentSource) => CONTENT_SOURCE_CONFIG[source]?.label || source
const getSourceColor = (source: ContentSource) => CONTENT_SOURCE_CONFIG[source]?.color || '#666'
const getDomainLabel = (domain: string) => TRIGGER_DOMAINS.find(d => d.value === domain)?.label || domain
const getReviewStatusLabel = (status: ReviewStatus) => {
  const map: Record<ReviewStatus, string> = {
    pending: '待审核',
    in_review: '审核中',
    approved: '已通过',
    rejected: '已拒绝',
    revision: '待修改'
  }
  return map[status] || status
}
const getReviewStatusColor = (status: ReviewStatus) => {
  const map: Record<ReviewStatus, string> = {
    pending: 'orange',
    in_review: 'processing',
    approved: 'green',
    rejected: 'red',
    revision: 'warning'
  }
  return map[status] || 'default'
}
const truncate = (str: string, len: number) => str.length > len ? str.slice(0, len) + '...' : str
const formatDate = (str: string) => str ? new Date(str).toLocaleDateString() : '-'
const formatDateTime = (str: string) => str ? new Date(str).toLocaleString() : '-'

// 事件处理
const handleSearch = () => {
  pagination.current = 1
  fetchCases()
}

const handleReset = () => {
  filters.keyword = ''
  filters.source = undefined
  filters.domain = undefined
  filters.reviewStatus = undefined
  handleSearch()
}

const handleTableChange = (pag: any) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchCases()
}

const handleView = (record: CaseShare) => {
  currentCase.value = record
  reviewMode.value = false
  viewModalVisible.value = true
}

const handleReview = (record: CaseShare) => {
  currentCase.value = record
  reviewMode.value = true
  reviewForm.checklist = []
  reviewForm.comments = ''
  reviewForm.revision_notes = ''
  viewModalVisible.value = true
}

const submitReview = (decision: ReviewStatus) => {
  reviewForm.decision = decision
  message.success(`审核完成：${getReviewStatusLabel(decision)}`)
  viewModalVisible.value = false
  fetchCases()
}

const handleFeature = (record: CaseShare) => {
  message.success('已设为精选')
}

const handleOffline = (record: CaseShare) => {
  message.success('已下架')
  fetchCases()
}

const handleDelete = (record: CaseShare) => {
  message.success('已删除')
  fetchCases()
}

// 获取数据
const fetchCases = async () => {
  loading.value = true
  try {
    // 模拟数据
    cases.value = [
      {
        case_id: 'c1',
        type: 'case_share',
        source: 'sharer',
        status: 'published',
        title: '从焦虑到平静：我的21天正念之旅',
        domain: 'emotion',
        challenge: '工作压力大，经常焦虑失眠，情绪波动明显，影响了生活质量和人际关系。',
        approach: '参加了平台的21天正念打卡活动，每天坚持10分钟冥想，记录情绪变化。',
        outcome: '焦虑感明显减轻，睡眠质量提升，学会了在情绪来临时先暂停观察，而不是立即反应。',
        reflection: '正念不是要消除负面情绪，而是学会与它们和平共处。',
        is_anonymous: false,
        display_name: '成长ing',
        author_id: 'user1',
        author_role: '平台用户',
        behavior_stage: 'action',
        allow_comments: true,
        comment_count: 23,
        like_count: 156,
        helpful_count: 89,
        review_status: 'approved',
        reviewed_by: 'admin1',
        reviewed_at: '2025-01-10T14:00:00Z',
        created_at: '2025-01-08T10:00:00Z',
        published_at: '2025-01-10T15:00:00Z'
      },
      {
        case_id: 'c2',
        type: 'case_share',
        source: 'coach',
        status: 'published',
        title: '帮助学员建立运动习惯的教练心得',
        domain: 'exercise',
        challenge: '学员总是坚持不了运动计划，三分钟热度后就放弃了。',
        approach: '采用渐进式目标设定，从每天5分钟开始，配合打卡激励和定期沟通反馈。',
        outcome: '学员从完全不运动到能稳定保持每周3次运动，持续了3个月。',
        reflection: '小步前进比大步跨越更容易成功，教练的陪伴和鼓励至关重要。',
        is_anonymous: false,
        display_name: '张教练',
        author_id: 'coach1',
        author_role: 'L3健康教练',
        allow_comments: true,
        comment_count: 12,
        like_count: 87,
        helpful_count: 56,
        review_status: 'approved',
        reviewed_by: 'admin1',
        reviewed_at: '2025-01-15T10:00:00Z',
        created_at: '2025-01-14T16:00:00Z',
        published_at: '2025-01-15T11:00:00Z'
      },
      {
        case_id: 'c3',
        type: 'case_share',
        source: 'sharer',
        status: 'pending',
        title: '戒烟100天的心路历程',
        domain: 'chronic',
        challenge: '烟龄15年，每天一包，多次戒烟失败。',
        approach: '使用平台的28天戒烟打卡，结合尼古丁替代疗法，每次想抽烟就做深呼吸。',
        outcome: '已经100天没抽烟了，体力明显恢复，家人也很开心。',
        is_anonymous: true,
        display_name: '匿名用户',
        author_id: 'user2',
        author_role: '平台用户',
        behavior_stage: 'maintenance',
        allow_comments: true,
        comment_count: 0,
        like_count: 0,
        helpful_count: 0,
        review_status: 'pending',
        created_at: '2026-02-04T09:00:00Z'
      },
      {
        case_id: 'c4',
        type: 'case_share',
        source: 'sharer',
        status: 'revision',
        title: '我的减肥经历',
        domain: 'diet',
        challenge: '体重超标，尝试过很多减肥方法都失败了。',
        approach: '配合某某减肥药...',
        outcome: '一个月瘦了20斤。',
        is_anonymous: false,
        display_name: '小胖墩',
        author_id: 'user3',
        author_role: '平台用户',
        allow_comments: true,
        comment_count: 0,
        like_count: 0,
        helpful_count: 0,
        review_status: 'revision',
        review_comment: '内容涉及减肥药物推荐，需要删除相关内容；减重速度不科学，建议修改表述。',
        created_at: '2026-02-03T14:00:00Z'
      }
    ] as CaseShare[]
    pagination.total = cases.value.length
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchCases()
})
</script>

<style scoped>
.case-list {
  padding: 24px;
}

.filter-card {
  margin-bottom: 16px;
}

.stats-row {
  margin-bottom: 16px;
}

.stat-card {
  text-align: center;
}

.case-info-cell {
  padding: 4px 0;
}

.case-title {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.case-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.domain-tag {
  font-size: 12px;
  color: #666;
}

.case-excerpt {
  font-size: 12px;
  color: #999;
  line-height: 1.4;
}

.author-cell {
  line-height: 1.5;
}

.display-name {
  font-weight: 500;
}

.author-role {
  font-size: 12px;
  color: #999;
}

.review-time {
  font-size: 11px;
  color: #999;
  margin-top: 2px;
}

.interaction-cell {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #666;
}

.interaction-cell span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.case-detail-desc {
  margin-bottom: 16px;
}

.case-section {
  margin-bottom: 16px;
}

.case-section h4 {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.case-section p {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  margin: 0;
}
</style>
