<template>
  <div class="review-queue">
    <div class="page-header">
      <h2>内容审核</h2>
      <div class="header-stats">
        <a-tag color="orange">待审核 {{ stats.pending }}</a-tag>
        <a-tag color="blue">今日已审 {{ stats.reviewed_today }}</a-tag>
      </div>
    </div>

    <!-- 筛选条件 -->
    <a-card style="margin-bottom: 16px">
      <a-row :gutter="16">
        <a-col :span="5">
          <a-select v-model:value="filters.type" placeholder="内容类型" allowClear style="width: 100%">
            <a-select-option v-for="(cfg, key) in CONTENT_TYPE_CONFIG" :key="key" :value="key">
              {{ cfg.label }}
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="5">
          <a-select v-model:value="filters.source" placeholder="内容来源" allowClear style="width: 100%">
            <a-select-option v-for="(cfg, key) in CONTENT_SOURCE_CONFIG" :key="key" :value="key">
              {{ cfg.label }}
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="5">
          <a-select v-model:value="filters.priority" placeholder="优先级" allowClear style="width: 100%">
            <a-select-option value="high">高优先级</a-select-option>
            <a-select-option value="normal">普通</a-select-option>
            <a-select-option value="low">低优先级</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="5">
          <a-select v-model:value="filters.domain" placeholder="所属领域" allowClear style="width: 100%">
            <a-select-option v-for="(cfg, key) in TRIGGER_DOMAINS" :key="key" :value="key">
              {{ cfg.label }}
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-button type="primary" @click="fetchQueue">刷新</a-button>
        </a-col>
      </a-row>
    </a-card>

    <!-- 审核队列表格 -->
    <a-table
      :dataSource="queue"
      :columns="columns"
      :loading="loading"
      :pagination="pagination"
      @change="handleTableChange"
      rowKey="content_id"
    >
      <template #bodyCell="{ column, record }">
        <!-- 内容信息 -->
        <template v-if="column.key === 'content'">
          <div class="content-info">
            <div class="content-title">{{ record.title }}</div>
            <div class="content-meta">
              <a-tag :color="CONTENT_TYPE_CONFIG[record.type]?.color || '#8c8c8c'">
                {{ CONTENT_TYPE_CONFIG[record.type]?.label || record.type }}
              </a-tag>
              <a-tag v-if="record.domain" size="small">
                {{ TRIGGER_DOMAINS[record.domain]?.label || record.domain }}
              </a-tag>
            </div>
          </div>
        </template>

        <!-- 来源 -->
        <template v-if="column.key === 'source'">
          <a-tag :color="CONTENT_SOURCE_CONFIG[record.source]?.color || '#8c8c8c'">
            {{ CONTENT_SOURCE_CONFIG[record.source]?.badge || record.source }}
          </a-tag>
          <div class="author-name">{{ record.author_name }}</div>
        </template>

        <!-- 优先级 -->
        <template v-if="column.key === 'priority'">
          <a-badge
            :status="priorityStatus[record.priority]"
            :text="priorityLabels[record.priority]"
          />
        </template>

        <!-- 提交时间 -->
        <template v-if="column.key === 'submitted_at'">
          <div>{{ formatDate(record.submitted_at) }}</div>
          <div class="wait-time">等待 {{ getWaitTime(record.submitted_at) }}</div>
        </template>

        <!-- 操作 -->
        <template v-if="column.key === 'action'">
          <a-space>
            <a-button type="primary" size="small" @click="openReview(record)">
              审核
            </a-button>
            <a-button size="small" @click="previewContent(record)">
              预览
            </a-button>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 审核弹窗 -->
    <a-modal
      v-model:open="reviewModalVisible"
      :title="`审核: ${currentItem?.title || ''}`"
      width="720px"
      :footer="null"
    >
      <div v-if="currentItem" class="review-modal">
        <!-- 内容预览区 -->
        <a-card title="内容预览" size="small" style="margin-bottom: 16px">
          <div class="preview-content">
            <p><strong>类型：</strong>{{ CONTENT_TYPE_CONFIG[currentItem.type]?.label }}</p>
            <p><strong>来源：</strong>{{ CONTENT_SOURCE_CONFIG[currentItem.source]?.label }} - {{ currentItem.author_name }}</p>
            <p><strong>领域：</strong>{{ TRIGGER_DOMAINS[currentItem.domain]?.label || '未分类' }}</p>
            <a-divider />
            <div v-if="currentItem.summary" class="summary-text">
              {{ currentItem.summary }}
            </div>
            <a-button type="link" @click="previewContent(currentItem)">查看完整内容 →</a-button>
          </div>
        </a-card>

        <!-- 审核检查项 -->
        <a-card title="审核检查" size="small" style="margin-bottom: 16px">
          <a-form :label-col="{ span: 8 }" :wrapper-col="{ span: 16 }">
            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="内容准确性">
                  <a-switch v-model:checked="checklist.content_accurate" />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="无医学诊断">
                  <a-switch v-model:checked="checklist.no_medical_claims" />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="无敏感内容">
                  <a-switch v-model:checked="checklist.no_sensitive" />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="质量达标">
                  <a-switch v-model:checked="checklist.quality_ok" />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="版权无问题">
                  <a-switch v-model:checked="checklist.copyright_clear" />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="隐私保护">
                  <a-switch v-model:checked="checklist.privacy_protected" />
                </a-form-item>
              </a-col>
            </a-row>
          </a-form>
        </a-card>

        <!-- 审核意见 -->
        <a-card title="审核意见" size="small" style="margin-bottom: 16px">
          <a-textarea
            v-model:value="reviewComment"
            placeholder="请输入审核意见（拒绝或需修改时必填）"
            :rows="3"
          />
        </a-card>

        <!-- 操作按钮 -->
        <div class="review-actions">
          <a-space>
            <a-button @click="reviewModalVisible = false">取消</a-button>
            <a-button type="default" danger @click="handleReject">
              拒绝
            </a-button>
            <a-button type="default" @click="handleRevision">
              需修改
            </a-button>
            <a-button type="primary" @click="handleApprove" :disabled="!allChecked">
              通过
            </a-button>
          </a-space>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { TRIGGER_DOMAINS } from '../../constants'
import { CONTENT_TYPE_CONFIG, CONTENT_SOURCE_CONFIG } from '../../types/content'
import type { ReviewQueueItem, ReviewChecklist } from '../../types/content'

const loading = ref(false)
const reviewModalVisible = ref(false)
const currentItem = ref<ReviewQueueItem | null>(null)
const reviewComment = ref('')

const stats = reactive({
  pending: 12,
  reviewed_today: 5
})

const filters = reactive({
  type: undefined as string | undefined,
  source: undefined as string | undefined,
  priority: undefined as string | undefined,
  domain: undefined as string | undefined,
})

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0
})

const checklist = reactive<ReviewChecklist>({
  content_accurate: false,
  no_medical_claims: false,
  no_sensitive: false,
  quality_ok: false,
  copyright_clear: false,
  privacy_protected: false,
})

const priorityLabels: Record<string, string> = {
  high: '高优先级',
  normal: '普通',
  low: '低优先级'
}

const priorityStatus: Record<string, string> = {
  high: 'error',
  normal: 'processing',
  low: 'default'
}

const columns = [
  { title: '内容信息', key: 'content', width: 300 },
  { title: '来源/作者', key: 'source', width: 150 },
  { title: '优先级', key: 'priority', width: 100 },
  { title: '提交时间', key: 'submitted_at', width: 150 },
  { title: '操作', key: 'action', width: 150, fixed: 'right' }
]

// 模拟数据
const queue = ref<(ReviewQueueItem & { summary?: string })[]>([
  {
    content_id: '1',
    content_type: 'case_share',
    type: 'case_share',
    content_title: '我是如何通过正念练习改善焦虑的',
    title: '我是如何通过正念练习改善焦虑的',
    source: 'sharer',
    author_name: '匿名用户A',
    submitted_at: '2026-02-05 10:30:00',
    priority: 'high',
    domain: 'stress',
    summary: '分享我三个月来坚持正念练习的心得，从每天焦虑发作到现在基本平静...'
  },
  {
    content_id: '2',
    content_type: 'article',
    type: 'article',
    content_title: '糖尿病患者的运动指南',
    title: '糖尿病患者的运动指南',
    source: 'coach',
    author_name: '李教练',
    submitted_at: '2026-02-05 09:15:00',
    priority: 'normal',
    domain: 'exercise',
    summary: '针对糖尿病患者制定的安全运动方案，包括运动前准备、运动强度控制...'
  },
  {
    content_id: '3',
    content_type: 'article',
    type: 'article',
    content_title: '睡眠质量提升的5个小技巧',
    title: '睡眠质量提升的5个小技巧',
    source: 'ai_generated',
    author_name: 'AI助手',
    submitted_at: '2026-02-05 08:00:00',
    priority: 'low',
    domain: 'sleep',
    summary: '基于睡眠科学研究总结的5个实用睡眠改善技巧...'
  },
  {
    content_id: '4',
    content_type: 'case_share',
    type: 'case_share',
    content_title: '戒烟100天，我的真实经历',
    title: '戒烟100天，我的真实经历',
    source: 'sharer',
    author_name: '老烟枪小张',
    submitted_at: '2026-02-04 22:00:00',
    priority: 'high',
    domain: 'stress',
    summary: '从每天两包烟到完全戒断，中间的挣扎和最终的成功...'
  },
])

const allChecked = computed(() => {
  return Object.values(checklist).every(v => v === true)
})

const fetchQueue = () => {
  loading.value = true
  // TODO: 调用API获取审核队列
  setTimeout(() => {
    loading.value = false
    stats.pending = queue.value.length
  }, 500)
}

const handleTableChange = (pag: any) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchQueue()
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`
}

const getWaitTime = (dateStr: string) => {
  const now = new Date()
  const submitted = new Date(dateStr)
  const hours = Math.floor((now.getTime() - submitted.getTime()) / (1000 * 60 * 60))
  if (hours < 1) return '< 1小时'
  if (hours < 24) return `${hours}小时`
  return `${Math.floor(hours / 24)}天`
}

const openReview = (item: ReviewQueueItem) => {
  currentItem.value = item
  reviewComment.value = ''
  // 重置检查项
  Object.keys(checklist).forEach(key => {
    (checklist as any)[key] = false
  })
  reviewModalVisible.value = true
}

const previewContent = (item: ReviewQueueItem) => {
  message.info(`预览功能开发中: ${item.title}`)
  // TODO: 打开内容预览页面
}

const handleApprove = () => {
  if (!allChecked.value) {
    message.warning('请完成所有检查项')
    return
  }

  Modal.confirm({
    title: '确认通过',
    content: '确定通过该内容的审核吗？通过后将立即发布。',
    onOk() {
      // TODO: 调用API
      message.success('审核通过，内容已发布')
      reviewModalVisible.value = false
      // 从队列中移除
      queue.value = queue.value.filter(q => q.content_id !== currentItem.value?.content_id)
      stats.pending = queue.value.length
      stats.reviewed_today++
    }
  })
}

const handleReject = () => {
  if (!reviewComment.value.trim()) {
    message.warning('请填写拒绝原因')
    return
  }

  Modal.confirm({
    title: '确认拒绝',
    content: '确定拒绝该内容吗？',
    okType: 'danger',
    onOk() {
      // TODO: 调用API
      message.success('已拒绝该内容')
      reviewModalVisible.value = false
      queue.value = queue.value.filter(q => q.content_id !== currentItem.value?.content_id)
      stats.pending = queue.value.length
      stats.reviewed_today++
    }
  })
}

const handleRevision = () => {
  if (!reviewComment.value.trim()) {
    message.warning('请填写修改建议')
    return
  }

  Modal.confirm({
    title: '确认退回修改',
    content: '确定退回该内容让作者修改吗？',
    onOk() {
      // TODO: 调用API
      message.success('已退回作者修改')
      reviewModalVisible.value = false
      queue.value = queue.value.filter(q => q.content_id !== currentItem.value?.content_id)
      stats.pending = queue.value.length
      stats.reviewed_today++
    }
  })
}

onMounted(() => {
  fetchQueue()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
}

.header-stats {
  display: flex;
  gap: 8px;
}

.content-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.content-title {
  font-weight: 500;
  color: #1f1f1f;
}

.content-meta {
  display: flex;
  gap: 4px;
}

.author-name {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.wait-time {
  font-size: 12px;
  color: #999;
}

.review-modal {
  max-height: 70vh;
  overflow-y: auto;
}

.preview-content {
  font-size: 14px;
}

.summary-text {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 6px;
  color: #666;
  line-height: 1.6;
}

.review-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}
</style>
