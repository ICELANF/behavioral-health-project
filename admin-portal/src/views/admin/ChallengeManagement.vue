<template>
  <div class="challenge-management">
    <!-- Page Header -->
    <div class="page-header">
      <h2>挑战管理</h2>
      <div class="header-actions">
        <a-button v-if="isAdmin" @click="openImportDialog">
          <ImportOutlined /> 从配置导入
        </a-button>
        <a-button type="primary" @click="openCreateModal">
          <PlusOutlined /> 创建挑战
        </a-button>
      </div>
    </div>

    <!-- Filters -->
    <a-card style="margin-bottom: 16px">
      <a-row :gutter="16">
        <a-col :span="5">
          <a-input-search
            v-model:value="filters.keyword"
            placeholder="搜索挑战标题"
            @search="loadChallenges"
            allowClear
          />
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="filters.status"
            placeholder="状态筛选"
            allowClear
            style="width: 100%"
            @change="onFilterChange"
          >
            <a-select-option v-for="(item, key) in STATUS_MAP" :key="key" :value="key">
              {{ item.label }}
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="filters.category"
            placeholder="分类筛选"
            allowClear
            style="width: 100%"
            @change="onFilterChange"
          >
            <a-select-option v-for="(label, key) in CATEGORY_MAP" :key="key" :value="key">
              {{ label }}
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="3">
          <a-button @click="resetFilters">重置</a-button>
        </a-col>
      </a-row>
    </a-card>

    <!-- Challenge List -->
    <a-spin :spinning="loading">
      <div class="list-card-container">
        <ListCard
          v-for="record in challenges"
          :key="record.id"
          @click="openPushDrawer(record)"
        >
          <template #title>
            <span style="font-weight: 500">{{ record.title }}</span>
          </template>
          <template #subtitle>
            <a-tag>{{ CATEGORY_MAP[record.category] || record.category }}</a-tag>
            <a-tag :color="STATUS_MAP[record.status]?.color || 'default'">
              {{ STATUS_MAP[record.status]?.label || record.status }}
            </a-tag>
            <template v-if="record.status === 'pending_review' || record.status === 'review_partial'">
              <a-tooltip title="审核人1">
                <a-badge
                  :status="record.reviewer1_status === 'approved' ? 'success' : record.reviewer1_status === 'rejected' ? 'error' : 'default'"
                  :text="record.reviewer1_name || '审核人1'"
                  style="margin-left: 4px; font-size: 11px"
                />
              </a-tooltip>
              <a-tooltip title="审核人2">
                <a-badge
                  :status="record.reviewer2_status === 'approved' ? 'success' : record.reviewer2_status === 'rejected' ? 'error' : 'default'"
                  :text="record.reviewer2_name || '审核人2'"
                  style="margin-left: 4px; font-size: 11px"
                />
              </a-tooltip>
            </template>
          </template>
          <template #meta>
            <span>{{ record.duration_days }} 天</span>
            <span class="meta-divider">|</span>
            <span>报名 {{ record.enrollment_count ?? 0 }}</span>
          </template>
          <template #actions>
            <a-space @click.stop>
              <a @click="editChallenge(record)">编辑</a>
              <a @click="openPushDrawer(record)">推送内容</a>
              <template v-if="record.status === 'draft' && isCreatorOrAdmin(record)">
                <a-popconfirm title="确定提交审核？" @confirm="submitForReview(record)">
                  <a style="color: #1890ff">提交审核</a>
                </a-popconfirm>
              </template>
              <template v-if="canReview && (record.status === 'pending_review' || record.status === 'review_partial')">
                <a style="color: #722ed1" @click="openReviewModal(record)">审核</a>
              </template>
              <template v-if="record.status === 'published' && isAdmin">
                <a-popconfirm title="确定归档此挑战？" @confirm="archiveChallenge(record)">
                  <a style="color: #8c8c8c">归档</a>
                </a-popconfirm>
              </template>
              <template v-if="record.status === 'draft'">
                <a-popconfirm title="确定删除此挑战？" @confirm="deleteChallenge(record)">
                  <a style="color: #ff4d4f">删除</a>
                </a-popconfirm>
              </template>
            </a-space>
          </template>
        </ListCard>
      </div>
      <div v-if="challenges.length === 0 && !loading" style="text-align: center; padding: 40px; color: #999">
        暂无挑战数据
      </div>
    </a-spin>
    <div style="display: flex; justify-content: flex-end; margin-top: 16px">
      <a-pagination
        v-model:current="pagination.page"
        v-model:pageSize="pagination.pageSize"
        :total="pagination.total"
        show-size-changer
        :show-total="(total: number) => `共 ${total} 个挑战`"
        @change="onPageChange"
      />
    </div>

    <!-- Create/Edit Challenge Modal -->
    <a-modal
      v-model:open="showChallengeModal"
      :title="editingChallenge ? '编辑挑战' : '创建挑战'"
      @ok="saveChallenge"
      okText="保存"
      :confirmLoading="saving"
      width="640px"
    >
      <a-form layout="vertical">
        <a-form-item label="挑战标题" required>
          <a-input v-model:value="challengeForm.title" placeholder="请输入挑战标题" :maxlength="100" />
        </a-form-item>
        <a-form-item label="挑战描述">
          <a-textarea
            v-model:value="challengeForm.description"
            placeholder="请输入挑战描述"
            :rows="3"
            :maxlength="500"
            showCount
          />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="分类" required>
              <a-select v-model:value="challengeForm.category" style="width: 100%">
                <a-select-option v-for="(label, key) in CATEGORY_MAP" :key="key" :value="key">
                  {{ label }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="持续天数" required>
              <a-input-number
                v-model:value="challengeForm.duration_days"
                :min="1"
                :max="365"
                style="width: 100%"
                placeholder="例如 14"
              />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="每日推送时间">
          <div style="margin-bottom: 8px">
            <a-tag
              v-for="(time, idx) in challengeForm.daily_push_times"
              :key="idx"
              closable
              @close="removePushTime(idx)"
              color="blue"
            >
              {{ time }}
            </a-tag>
          </div>
          <a-space>
            <a-input
              v-model:value="newPushTime"
              placeholder="HH:mm 如 09:00"
              style="width: 140px"
              @pressEnter="addPushTime"
            />
            <a-button size="small" @click="addPushTime">添加</a-button>
          </a-space>
        </a-form-item>
        <a-form-item label="封面图片">
          <a-input v-model:value="challengeForm.cover_image" placeholder="图片 URL 地址" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Push Content Management Drawer -->
    <a-drawer
      v-model:open="showPushDrawer"
      :title="`推送内容管理 - ${currentChallenge?.title || ''}`"
      width="900"
      @close="closePushDrawer"
    >
      <div style="display: flex; height: 100%">
        <!-- Left sidebar: day list -->
        <div class="day-sidebar">
          <div class="day-sidebar-header">日程列表</div>
          <div
            v-for="day in dayList"
            :key="day"
            :class="['day-item', { active: selectedDay === day }]"
            @click="selectDay(day)"
          >
            Day {{ day }}
          </div>
        </div>

        <!-- Right content: push items -->
        <div class="push-content">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px">
            <h4 style="margin: 0">Day {{ selectedDay }} 推送内容</h4>
            <a-button type="primary" size="small" @click="openPushItemModal(null)">
              <PlusOutlined /> 添加推送
            </a-button>
          </div>

          <a-spin :spinning="pushLoading">
            <div v-if="filteredPushItems.length === 0" style="text-align: center; padding: 40px; color: #999">
              当天暂无推送内容，点击上方按钮添加
            </div>
            <div v-for="item in filteredPushItems" :key="item.id" class="push-card">
              <div class="push-card-header">
                <div style="display: flex; align-items: center; gap: 8px">
                  <a-tag :color="getPushTagColor(item.tag)">{{ getPushTagLabel(item.tag) }}</a-tag>
                  <span style="font-weight: 500">{{ item.push_time }}</span>
                  <a-tag v-if="item.is_core" color="red" size="small">核心</a-tag>
                </div>
                <a-space>
                  <a @click="openPushItemModal(item)">编辑</a>
                  <a-popconfirm title="确定删除此推送？" @confirm="deletePushItem(item)">
                    <a style="color: #ff4d4f">删除</a>
                  </a-popconfirm>
                </a-space>
              </div>
              <div class="push-card-body">
                <div v-if="item.management_content" class="push-field">
                  <div class="push-field-label">管理内容</div>
                  <div class="push-field-value">{{ item.management_content }}</div>
                </div>
                <div v-if="item.behavior_guidance" class="push-field">
                  <div class="push-field-label">行为引导</div>
                  <div class="push-field-value">{{ item.behavior_guidance }}</div>
                </div>
                <div v-if="item.survey && item.survey.length > 0" class="push-field">
                  <div class="push-field-label">问卷调查 ({{ item.survey.length }} 题)</div>
                  <div class="push-field-value">
                    <div v-for="(q, qi) in item.survey" :key="qi" style="font-size: 12px; color: #666; margin-bottom: 2px">
                      {{ qi + 1 }}. {{ q.label }} <a-tag size="small">{{ getSurveyTypeLabel(q.type) }}</a-tag>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </a-spin>
        </div>
      </div>
    </a-drawer>

    <!-- Push Item Sub-Modal -->
    <a-modal
      v-model:open="showPushItemModal"
      :title="editingPushItem ? '编辑推送项' : '添加推送项'"
      @ok="savePushItem"
      okText="保存"
      :confirmLoading="savingPushItem"
      width="720px"
    >
      <a-form layout="vertical">
        <a-row :gutter="16">
          <a-col :span="6">
            <a-form-item label="日期" required>
              <a-input-number
                v-model:value="pushItemForm.day_number"
                :min="0"
                :max="(currentChallenge?.duration_days ?? 30) - 1"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="推送时间" required>
              <a-select v-model:value="pushItemForm.push_time" style="width: 100%">
                <a-select-option value="09:00">09:00</a-select-option>
                <a-select-option value="11:30">11:30</a-select-option>
                <a-select-option value="17:30">17:30</a-select-option>
                <a-select-option value="custom">自定义</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="6" v-if="pushItemForm.push_time === 'custom'">
            <a-form-item label="自定义时间">
              <a-input v-model:value="pushItemForm.custom_time" placeholder="HH:mm" />
            </a-form-item>
          </a-col>
          <a-col :span="4">
            <a-form-item label="核心">
              <a-switch v-model:checked="pushItemForm.is_core" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="标签" required>
          <a-radio-group v-model:value="pushItemForm.tag">
            <a-radio-button value="core">核心</a-radio-button>
            <a-radio-button value="optional">可选</a-radio-button>
            <a-radio-button value="assessment">评估</a-radio-button>
            <a-radio-button value="info">说明</a-radio-button>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="管理内容">
          <a-textarea
            v-model:value="pushItemForm.management_content"
            :rows="3"
            placeholder="推送的管理内容"
            :maxlength="1000"
            showCount
          />
        </a-form-item>
        <a-form-item label="行为引导">
          <a-textarea
            v-model:value="pushItemForm.behavior_guidance"
            :rows="3"
            placeholder="行为引导说明"
            :maxlength="1000"
            showCount
          />
        </a-form-item>

        <!-- Survey Builder -->
        <a-divider>问卷调查</a-divider>
        <div v-for="(question, qi) in pushItemForm.survey" :key="qi" class="survey-question-card">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px">
            <span style="font-weight: 500; color: #333">问题 {{ qi + 1 }}</span>
            <a-button type="text" danger size="small" @click="removeSurveyQuestion(qi)">
              <DeleteOutlined />
            </a-button>
          </div>
          <a-row :gutter="12">
            <a-col :span="8">
              <a-form-item label="题目类型" style="margin-bottom: 8px">
                <a-select v-model:value="question.type" style="width: 100%" @change="onSurveyTypeChange(qi)">
                  <a-select-option value="rating">评分 (rating)</a-select-option>
                  <a-select-option value="text">文本 (text)</a-select-option>
                  <a-select-option value="single_choice">单选 (single_choice)</a-select-option>
                  <a-select-option value="multi_choice">多选 (multi_choice)</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="16">
              <a-form-item label="题目标签" style="margin-bottom: 8px">
                <a-input v-model:value="question.label" placeholder="问题描述" />
              </a-form-item>
            </a-col>
          </a-row>
          <template v-if="question.type === 'rating'">
            <a-row :gutter="12">
              <a-col :span="12">
                <a-form-item label="最小值" style="margin-bottom: 8px">
                  <a-input-number v-model:value="question.min" :min="0" :max="100" style="width: 100%" />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="最大值" style="margin-bottom: 8px">
                  <a-input-number v-model:value="question.max" :min="1" :max="100" style="width: 100%" />
                </a-form-item>
              </a-col>
            </a-row>
          </template>
          <template v-if="question.type === 'single_choice' || question.type === 'multi_choice'">
            <a-form-item label="选项（每行一个）" style="margin-bottom: 8px">
              <a-textarea
                v-model:value="question.options_text"
                :rows="3"
                placeholder="选项A&#10;选项B&#10;选项C"
              />
            </a-form-item>
          </template>
        </div>
        <a-button type="dashed" block @click="addSurveyQuestion" style="margin-top: 8px">
          <PlusOutlined /> 添加问题
        </a-button>
      </a-form>
    </a-modal>

    <!-- Review Modal -->
    <a-modal
      v-model:open="showReviewModal"
      title="审核挑战"
      @ok="submitReview"
      okText="提交审核"
      :confirmLoading="reviewSubmitting"
      width="500px"
    >
      <div v-if="reviewingChallenge" style="margin-bottom: 16px">
        <h4>{{ reviewingChallenge.title }}</h4>
        <p style="color: #666">{{ reviewingChallenge.description }}</p>
        <a-descriptions :column="2" size="small" bordered>
          <a-descriptions-item label="分类">{{ CATEGORY_MAP[reviewingChallenge.category] || reviewingChallenge.category }}</a-descriptions-item>
          <a-descriptions-item label="天数">{{ reviewingChallenge.duration_days }} 天</a-descriptions-item>
          <a-descriptions-item label="推送时间">
            <a-tag v-for="t in (reviewingChallenge.daily_push_times || [])" :key="t" color="blue" style="margin-bottom: 2px">{{ t }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="报名人数">{{ reviewingChallenge.enrollment_count ?? 0 }}</a-descriptions-item>
        </a-descriptions>
      </div>
      <a-divider />
      <a-form layout="vertical">
        <a-form-item label="审核结果" required>
          <a-radio-group v-model:value="reviewForm.decision">
            <a-radio value="approved">通过</a-radio>
            <a-radio value="rejected">驳回</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="审核备注">
          <a-textarea
            v-model:value="reviewForm.note"
            :rows="3"
            placeholder="请输入审核备注（驳回时建议填写原因）"
            :maxlength="500"
            showCount
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Import Dialog (Admin Only) -->
    <a-modal
      v-model:open="showImportDialog"
      title="从配置导入挑战"
      @ok="handleImport"
      okText="导入"
      :confirmLoading="importing"
      width="480px"
    >
      <a-alert
        message="从预置配置导入挑战模板，导入后为草稿状态。"
        type="info"
        show-icon
        style="margin-bottom: 16px"
      />
      <a-form layout="vertical">
        <a-form-item label="配置标识" required>
          <a-input
            v-model:value="importConfigKey"
            placeholder='例如 "glucose_14day"'
          />
        </a-form-item>
        <a-form-item label="常用配置">
          <a-space wrap>
            <a-tag
              v-for="preset in IMPORT_PRESETS"
              :key="preset.key"
              color="blue"
              style="cursor: pointer"
              @click="importConfigKey = preset.key"
            >
              {{ preset.label }}
            </a-tag>
          </a-space>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, ImportOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import request from '@/api/request'
import ListCard from '@/components/core/ListCard.vue'

// ========== Type Definitions ==========

interface SurveyQuestion {
  type: 'rating' | 'text' | 'single_choice' | 'multi_choice'
  label: string
  options?: string[]
  options_text?: string
  min?: number
  max?: number
}

interface PushItem {
  id?: number
  challenge_id?: number
  day_number: number
  push_time: string
  tag: string
  is_core: boolean
  management_content: string
  behavior_guidance: string
  survey: SurveyQuestion[]
}

interface Challenge {
  id: number
  title: string
  description: string
  category: string
  duration_days: number
  daily_push_times: string[]
  cover_image: string
  status: string
  enrollment_count: number
  creator_id?: number
  reviewer1_status?: string
  reviewer1_name?: string
  reviewer2_status?: string
  reviewer2_name?: string
  created_at?: string
}

// ========== Constants ==========

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  draft: { label: '草稿', color: 'default' },
  pending_review: { label: '待审核', color: 'processing' },
  review_partial: { label: '审核中', color: 'blue' },
  published: { label: '已发布', color: 'success' },
  archived: { label: '已归档', color: '' },
}

const CATEGORY_MAP: Record<string, string> = {
  glucose_management: '血糖管理',
  mindfulness: '正念训练',
  exercise: '运动健康',
  nutrition: '营养饮食',
  general: '综合',
}

const PUSH_TAG_MAP: Record<string, { label: string; color: string }> = {
  core: { label: '核心', color: 'red' },
  optional: { label: '可选', color: 'blue' },
  assessment: { label: '评估', color: 'orange' },
  info: { label: '说明', color: 'green' },
}

const SURVEY_TYPE_MAP: Record<string, string> = {
  rating: '评分',
  text: '文本',
  single_choice: '单选',
  multi_choice: '多选',
}

const IMPORT_PRESETS = [
  { key: 'glucose_14day', label: '血糖14天挑战' },
  { key: 'mindfulness_7day', label: '正念7天入门' },
  { key: 'exercise_21day', label: '运动21天养成' },
  { key: 'nutrition_14day', label: '营养14天计划' },
]

// ========== Auth / Role ==========

const currentUser = computed(() => {
  try {
    const raw = localStorage.getItem('admin_user')
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
})

const currentUserRole = computed(() => currentUser.value.role || '')
const currentUserId = computed(() => currentUser.value.id || 0)

const isAdmin = computed(() => currentUserRole.value === 'admin')

const ROLE_LEVELS: Record<string, number> = {
  observer: 1, grower: 2, sharer: 3, coach: 4,
  promoter: 5, supervisor: 5, master: 6, admin: 99,
}

const canReview = computed(() => {
  const level = ROLE_LEVELS[currentUserRole.value] || 0
  return level >= 4
})

const isCreatorOrAdmin = (record: Challenge) => {
  return isAdmin.value || record.creator_id === currentUserId.value
}

// ========== State ==========

const loading = ref(false)
const saving = ref(false)
const challenges = ref<Challenge[]>([])
const editingChallenge = ref<Challenge | null>(null)
const showChallengeModal = ref(false)

const filters = reactive({
  keyword: '',
  status: undefined as string | undefined,
  category: undefined as string | undefined,
})

const pagination = reactive({ page: 1, pageSize: 10, total: 0 })

const challengeForm = reactive({
  title: '',
  description: '',
  category: 'general' as string,
  duration_days: 14 as number,
  daily_push_times: [] as string[],
  cover_image: '',
})

const newPushTime = ref('')

// Push Drawer state
const showPushDrawer = ref(false)
const currentChallenge = ref<Challenge | null>(null)
const selectedDay = ref(0)
const pushItems = ref<PushItem[]>([])
const pushLoading = ref(false)

// Push Item Modal state
const showPushItemModal = ref(false)
const editingPushItem = ref<PushItem | null>(null)
const savingPushItem = ref(false)
const pushItemForm = reactive({
  day_number: 0,
  push_time: '09:00' as string,
  custom_time: '' as string,
  tag: 'core' as string,
  is_core: true,
  management_content: '',
  behavior_guidance: '',
  survey: [] as SurveyQuestion[],
})

// Review Modal state
const showReviewModal = ref(false)
const reviewingChallenge = ref<Challenge | null>(null)
const reviewSubmitting = ref(false)
const reviewForm = reactive({
  decision: 'approved' as 'approved' | 'rejected',
  note: '',
})

// Import Dialog state
const showImportDialog = ref(false)
const importConfigKey = ref('')
const importing = ref(false)

// ========== Table Columns ==========

// columns removed — now using ListCard layout

// ========== Computed ==========

const dayList = computed(() => {
  const days = currentChallenge.value?.duration_days ?? 1
  return Array.from({ length: days }, (_, i) => i)
})

const filteredPushItems = computed(() => {
  return pushItems.value.filter((item) => item.day_number === selectedDay.value)
})

// ========== Helper Functions ==========

function getPushTagColor(tag: string): string {
  return PUSH_TAG_MAP[tag]?.color || 'default'
}

function getPushTagLabel(tag: string): string {
  return PUSH_TAG_MAP[tag]?.label || tag
}

function getSurveyTypeLabel(type: string): string {
  return SURVEY_TYPE_MAP[type] || type
}

// ========== Challenge List API ==========

async function loadChallenges() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (filters.keyword) params.search = filters.keyword
    if (filters.status) params.status = filters.status
    if (filters.category) params.category = filters.category

    const { data } = await request.get('/v1/challenges', { params })
    challenges.value = data.challenges || data.items || []
    pagination.total = data.total || 0
  } catch (e: any) {
    console.error('加载挑战列表失败:', e)
  } finally {
    loading.value = false
  }
}

function onFilterChange() {
  pagination.page = 1
  loadChallenges()
}

function onPageChange(page: number, pageSize: number) {
  pagination.page = page
  pagination.pageSize = pageSize
  loadChallenges()
}

function resetFilters() {
  filters.keyword = ''
  filters.status = undefined
  filters.category = undefined
  pagination.page = 1
  loadChallenges()
}

// ========== Create / Edit Challenge ==========

function openCreateModal() {
  editingChallenge.value = null
  Object.assign(challengeForm, {
    title: '',
    description: '',
    category: 'general',
    duration_days: 14,
    daily_push_times: [],
    cover_image: '',
  })
  newPushTime.value = ''
  showChallengeModal.value = true
}

function editChallenge(record: Challenge) {
  editingChallenge.value = record
  Object.assign(challengeForm, {
    title: record.title,
    description: record.description || '',
    category: record.category,
    duration_days: record.duration_days,
    daily_push_times: [...(record.daily_push_times || [])],
    cover_image: record.cover_image || '',
  })
  newPushTime.value = ''
  showChallengeModal.value = true
}

function addPushTime() {
  const time = newPushTime.value.trim()
  if (!time) {
    message.warning('请输入推送时间')
    return
  }
  const timeRegex = /^([01]\d|2[0-3]):([0-5]\d)$/
  if (!timeRegex.test(time)) {
    message.warning('时间格式不正确，请使用 HH:mm 格式（如 09:00）')
    return
  }
  if (challengeForm.daily_push_times.includes(time)) {
    message.warning('该时间已存在')
    return
  }
  challengeForm.daily_push_times.push(time)
  challengeForm.daily_push_times.sort()
  newPushTime.value = ''
}

function removePushTime(index: number) {
  challengeForm.daily_push_times.splice(index, 1)
}

async function saveChallenge() {
  if (!challengeForm.title.trim()) {
    message.warning('请输入挑战标题')
    return
  }
  if (!challengeForm.category) {
    message.warning('请选择分类')
    return
  }
  if (!challengeForm.duration_days || challengeForm.duration_days < 1) {
    message.warning('请输入持续天数')
    return
  }

  saving.value = true
  try {
    const payload = {
      title: challengeForm.title.trim(),
      description: challengeForm.description.trim(),
      category: challengeForm.category,
      duration_days: challengeForm.duration_days,
      daily_push_times: challengeForm.daily_push_times,
      cover_image: challengeForm.cover_image.trim(),
    }

    if (editingChallenge.value) {
      await request.put(`/v1/challenges/${editingChallenge.value.id}`, payload)
      message.success('挑战已更新')
    } else {
      await request.post('/v1/challenges', payload)
      message.success('挑战已创建')
    }

    showChallengeModal.value = false
    editingChallenge.value = null
    await loadChallenges()
  } catch (e: any) {
    const detail = e.response?.data?.detail
    message.error(detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function deleteChallenge(record: Challenge) {
  try {
    await request.delete(`/v1/challenges/${record.id}`)
    message.success('挑战已删除')
    await loadChallenges()
  } catch (e: any) {
    message.error('删除失败')
  }
}

// ========== Status Operations ==========

async function submitForReview(record: Challenge) {
  try {
    await request.post(`/v1/challenges/${record.id}/submit-review`)
    message.success('已提交审核')
    await loadChallenges()
  } catch (e: any) {
    const detail = e.response?.data?.detail
    message.error(detail || '提交审核失败')
  }
}

async function archiveChallenge(record: Challenge) {
  try {
    await request.post(`/v1/challenges/${record.id}/archive`)
    message.success('挑战已归档')
    await loadChallenges()
  } catch (e: any) {
    message.error('归档失败')
  }
}

// ========== Review Workflow ==========

function openReviewModal(record: Challenge) {
  reviewingChallenge.value = record
  reviewForm.decision = 'approved'
  reviewForm.note = ''
  showReviewModal.value = true
}

async function submitReview() {
  if (!reviewingChallenge.value) return
  if (!reviewForm.decision) {
    message.warning('请选择审核结果')
    return
  }

  reviewSubmitting.value = true
  try {
    await request.post(`/v1/challenges/${reviewingChallenge.value.id}/review`, {
      approved: reviewForm.decision === 'approved',
      note: reviewForm.note.trim(),
    })
    message.success(reviewForm.decision === 'approved' ? '审核通过' : '已驳回')
    showReviewModal.value = false
    reviewingChallenge.value = null
    await loadChallenges()
  } catch (e: any) {
    const detail = e.response?.data?.detail
    message.error(detail || '审核提交失败')
  } finally {
    reviewSubmitting.value = false
  }
}

// ========== Push Content Drawer ==========

function openPushDrawer(record: Challenge) {
  currentChallenge.value = record
  selectedDay.value = 0
  showPushDrawer.value = true
  loadPushItems(record.id)
}

function closePushDrawer() {
  showPushDrawer.value = false
  currentChallenge.value = null
  pushItems.value = []
}

function selectDay(day: number) {
  selectedDay.value = day
}

async function loadPushItems(challengeId: number) {
  pushLoading.value = true
  try {
    const { data } = await request.get(`/v1/challenges/${challengeId}/pushes`)
    pushItems.value = (data.items || data || []).map((item: any) => ({
      ...item,
      survey: item.survey || [],
    }))
  } catch (e: any) {
    console.error('加载推送内容失败:', e)
    pushItems.value = []
  } finally {
    pushLoading.value = false
  }
}

// ========== Push Item Modal ==========

function openPushItemModal(item: PushItem | null) {
  editingPushItem.value = item
  if (item) {
    Object.assign(pushItemForm, {
      day_number: item.day_number,
      push_time: ['09:00', '11:30', '17:30'].includes(item.push_time) ? item.push_time : 'custom',
      custom_time: ['09:00', '11:30', '17:30'].includes(item.push_time) ? '' : item.push_time,
      tag: item.tag,
      is_core: item.is_core,
      management_content: item.management_content || '',
      behavior_guidance: item.behavior_guidance || '',
      survey: (item.survey || []).map((q) => ({
        ...q,
        options_text: (q.options || []).join('\n'),
      })),
    })
  } else {
    Object.assign(pushItemForm, {
      day_number: selectedDay.value,
      push_time: '09:00',
      custom_time: '',
      tag: 'core',
      is_core: true,
      management_content: '',
      behavior_guidance: '',
      survey: [],
    })
  }
  showPushItemModal.value = true
}

function addSurveyQuestion() {
  pushItemForm.survey.push({
    type: 'rating',
    label: '',
    options_text: '',
    min: 1,
    max: 5,
  })
}

function removeSurveyQuestion(index: number) {
  pushItemForm.survey.splice(index, 1)
}

function onSurveyTypeChange(index: number) {
  const question = pushItemForm.survey[index]
  if (question.type === 'rating') {
    question.min = question.min ?? 1
    question.max = question.max ?? 5
    question.options_text = ''
  } else if (question.type === 'text') {
    question.options_text = ''
    question.min = undefined
    question.max = undefined
  } else {
    question.min = undefined
    question.max = undefined
  }
}

async function savePushItem() {
  if (!currentChallenge.value) return

  const resolvedTime = pushItemForm.push_time === 'custom' ? pushItemForm.custom_time.trim() : pushItemForm.push_time
  if (!resolvedTime) {
    message.warning('请选择或输入推送时间')
    return
  }

  const timeRegex = /^([01]\d|2[0-3]):([0-5]\d)$/
  if (!timeRegex.test(resolvedTime)) {
    message.warning('推送时间格式不正确，请使用 HH:mm 格式')
    return
  }

  if (!pushItemForm.tag) {
    message.warning('请选择标签')
    return
  }

  // Build survey with proper options arrays
  const survey: SurveyQuestion[] = pushItemForm.survey.map((q) => {
    const base: SurveyQuestion = {
      type: q.type,
      label: q.label,
    }
    if (q.type === 'rating') {
      base.min = q.min ?? 1
      base.max = q.max ?? 5
    }
    if (q.type === 'single_choice' || q.type === 'multi_choice') {
      base.options = (q.options_text || '')
        .split('\n')
        .map((s: string) => s.trim())
        .filter((s: string) => s.length > 0)
    }
    return base
  })

  // Validate survey questions
  for (let i = 0; i < survey.length; i++) {
    if (!survey[i].label.trim()) {
      message.warning(`问题 ${i + 1} 的标签不能为空`)
      return
    }
    if ((survey[i].type === 'single_choice' || survey[i].type === 'multi_choice') && (!survey[i].options || survey[i].options!.length < 2)) {
      message.warning(`问题 ${i + 1} 的选项至少需要2个`)
      return
    }
    if (survey[i].type === 'rating') {
      const min = survey[i].min ?? 1
      const max = survey[i].max ?? 5
      if (min >= max) {
        message.warning(`问题 ${i + 1} 的最小值必须小于最大值`)
        return
      }
    }
  }

  savingPushItem.value = true
  try {
    const payload = {
      day_number: pushItemForm.day_number,
      push_time: resolvedTime,
      tag: pushItemForm.tag,
      is_core: pushItemForm.is_core,
      management_content: pushItemForm.management_content.trim(),
      behavior_guidance: pushItemForm.behavior_guidance.trim(),
      survey: survey,
    }

    if (editingPushItem.value?.id) {
      await request.put(
        `/v1/challenges/pushes/${editingPushItem.value.id}`,
        payload
      )
      message.success('推送项已更新')
    } else {
      await request.post(
        `/v1/challenges/${currentChallenge.value.id}/pushes`,
        payload
      )
      message.success('推送项已添加')
    }

    showPushItemModal.value = false
    editingPushItem.value = null
    await loadPushItems(currentChallenge.value.id)
  } catch (e: any) {
    const detail = e.response?.data?.detail
    message.error(detail || '保存推送项失败')
  } finally {
    savingPushItem.value = false
  }
}

async function deletePushItem(item: PushItem) {
  if (!currentChallenge.value || !item.id) return
  try {
    await request.delete(`/v1/challenges/pushes/${item.id}`)
    message.success('推送项已删除')
    await loadPushItems(currentChallenge.value.id)
  } catch (e: any) {
    message.error('删除失败')
  }
}

// ========== Import ==========

function openImportDialog() {
  importConfigKey.value = ''
  showImportDialog.value = true
}

async function handleImport() {
  const key = importConfigKey.value.trim()
  if (!key) {
    message.warning('请输入配置标识')
    return
  }

  importing.value = true
  try {
    await request.post(`/v1/challenges/import/${encodeURIComponent(key)}`)
    message.success(`配置 "${key}" 导入成功`)
    showImportDialog.value = false
    importConfigKey.value = ''
    await loadChallenges()
  } catch (e: any) {
    const detail = e.response?.data?.detail
    message.error(detail || '导入失败')
  } finally {
    importing.value = false
  }
}

// ========== Lifecycle ==========

onMounted(() => {
  loadChallenges()
})
</script>

<style scoped>
.list-card-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.challenge-management {
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

.header-actions {
  display: flex;
  gap: 8px;
}

.meta-divider {
  color: #d9d9d9;
  margin: 0 4px;
}

/* Push drawer layout */
.day-sidebar {
  width: 120px;
  min-width: 120px;
  border-right: 1px solid #f0f0f0;
  overflow-y: auto;
  max-height: calc(100vh - 160px);
}

.day-sidebar-header {
  padding: 8px 12px;
  font-weight: 600;
  color: #333;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

.day-item {
  padding: 8px 12px;
  cursor: pointer;
  font-size: 13px;
  color: #666;
  border-bottom: 1px solid #fafafa;
  transition: all 0.2s;
}

.day-item:hover {
  background: #e6f7ff;
  color: #1890ff;
}

.day-item.active {
  background: #1890ff;
  color: #fff;
  font-weight: 500;
}

.push-content {
  flex: 1;
  padding: 0 0 0 16px;
  overflow-y: auto;
  max-height: calc(100vh - 160px);
}

/* Push cards */
.push-card {
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  margin-bottom: 12px;
  overflow: hidden;
}

.push-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

.push-card-body {
  padding: 12px;
}

.push-field {
  margin-bottom: 8px;
}

.push-field:last-child {
  margin-bottom: 0;
}

.push-field-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 2px;
}

.push-field-value {
  font-size: 13px;
  color: #333;
  white-space: pre-wrap;
  line-height: 1.5;
}

/* Survey question card in modal */
.survey-question-card {
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 12px;
  background: #fafafa;
}

/* ListCard items are already clickable */
</style>
