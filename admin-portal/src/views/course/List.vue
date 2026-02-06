<template>
  <div class="course-list">
    <div class="page-header">
      <h2>课程列表</h2>
      <a-button type="primary" @click="$router.push('/course/create')">
        <template #icon><PlusOutlined /></template>
        创建课程
      </a-button>
    </div>

    <!-- 筛选 -->
    <a-card style="margin-bottom: 16px">
      <a-row :gutter="16">
        <a-col :span="4">
          <a-select v-model:value="filters.source" placeholder="内容来源" allowClear style="width: 100%">
            <a-select-option v-for="(config, key) in CONTENT_SOURCE_CONFIG" :key="key" :value="key">
              <span :style="{ color: config.color }">●</span> {{ config.label }}
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filters.level" placeholder="认证等级" allowClear style="width: 100%">
            <a-select-option value="L0">L0 公众学习</a-select-option>
            <a-select-option value="L1">L1 初级教练</a-select-option>
            <a-select-option value="L2">L2 中级教练</a-select-option>
            <a-select-option value="L3">L3 高级教练</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filters.domain" placeholder="内容领域" allowClear style="width: 100%">
            <a-select-option v-for="domain in TRIGGER_DOMAINS" :key="domain.value" :value="domain.value">
              {{ domain.label }}
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filters.category" placeholder="课程类别" allowClear style="width: 100%">
            <a-select-option value="knowledge">知识体系</a-select-option>
            <a-select-option value="method">方法体系</a-select-option>
            <a-select-option value="skill">核心技能</a-select-option>
            <a-select-option value="value">观念心智</a-select-option>
            <a-select-option value="practice">实践练习</a-select-option>
            <a-select-option value="case">案例学习</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filters.status" placeholder="状态" allowClear style="width: 100%">
            <a-select-option value="draft">草稿</a-select-option>
            <a-select-option value="pending">待审核</a-select-option>
            <a-select-option value="published">已上架</a-select-option>
            <a-select-option value="offline">已下架</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-input-search v-model:value="filters.keyword" placeholder="搜索课程名称" @search="fetchCourses" />
        </a-col>
      </a-row>
    </a-card>

    <!-- 统计卡片 -->
    <a-row :gutter="16" style="margin-bottom: 16px">
      <a-col :span="6">
        <a-card size="small">
          <a-statistic title="全部课程" :value="stats.total" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card size="small">
          <a-statistic title="官方课程" :value="stats.platform" :value-style="{ color: '#1890ff' }" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card size="small">
          <a-statistic title="专家课程" :value="stats.expert" :value-style="{ color: '#722ed1' }" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card size="small">
          <a-statistic title="待审核" :value="stats.pending" :value-style="{ color: '#faad14' }" />
        </a-card>
      </a-col>
    </a-row>

    <!-- 课程表格 -->
    <a-table
      :dataSource="courses"
      :columns="columns"
      :loading="loading"
      :pagination="pagination"
      @change="handleTableChange"
      rowKey="course_id"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'cover'">
          <a-image :src="record.cover_url || defaultCover" :width="80" />
        </template>
        <template v-if="column.key === 'title'">
          <div>
            <div class="course-title">{{ record.title }}</div>
            <div class="course-tags">
              <a-tag :color="getSourceColor(record.source)" size="small">
                {{ getSourceLabel(record.source) }}
              </a-tag>
              <a-tag :color="levelColors[record.level]" size="small">{{ record.level }}</a-tag>
              <a-tag size="small">{{ categoryLabels[record.category] }}</a-tag>
              <a-tag v-if="record.domain" size="small" color="cyan">{{ getDomainLabel(record.domain) }}</a-tag>
            </div>
          </div>
        </template>
        <template v-if="column.key === 'author'">
          <div class="author-cell">
            <a-avatar :src="record.author_avatar" size="small">
              {{ record.author_name?.charAt(0) }}
            </a-avatar>
            <div class="author-info">
              <span class="author-name">{{ record.author_name }}</span>
              <CheckCircleFilled v-if="record.author_verified" class="verified-icon" />
              <div class="author-title" v-if="record.author_title">{{ record.author_title }}</div>
            </div>
          </div>
        </template>
        <template v-if="column.key === 'stats'">
          <div class="course-stats">
            <span><BookOutlined /> {{ record.chapter_count || 0 }} 章节</span>
            <span><ClockCircleOutlined /> {{ record.duration_minutes || 0 }} 分钟</span>
          </div>
          <div class="course-stats">
            <span><EyeOutlined /> {{ formatNumber(record.view_count || 0) }}</span>
            <span><UserOutlined /> {{ formatNumber(record.enroll_count || 0) }}</span>
            <span v-if="record.avg_rating"><StarFilled style="color: #faad14" /> {{ record.avg_rating }}</span>
          </div>
        </template>
        <template v-if="column.key === 'status'">
          <a-badge
            :status="statusMap[record.status]?.badge"
            :text="statusMap[record.status]?.text"
          />
          <div v-if="record.review_status === 'pending'" style="margin-top: 4px">
            <a-tag color="orange" size="small">待审核</a-tag>
          </div>
        </template>
        <template v-if="column.key === 'action'">
          <a-space>
            <a @click="$router.push(`/course/chapters/${record.course_id}`)">章节</a>
            <a @click="$router.push(`/course/edit/${record.course_id}`)">编辑</a>
            <a-dropdown>
              <a>更多</a>
              <template #overlay>
                <a-menu>
                  <a-menu-item v-if="record.status === 'draft'" @click="handlePublish(record)">
                    上架
                  </a-menu-item>
                  <a-menu-item v-if="record.status === 'published'" @click="handleOffline(record)">
                    下架
                  </a-menu-item>
                  <a-menu-item v-if="record.review_status === 'pending'" @click="handleReview(record)">
                    <span style="color: #faad14">审核</span>
                  </a-menu-item>
                  <a-menu-item @click="handlePreview(record)">预览</a-menu-item>
                  <a-menu-divider />
                  <a-menu-item danger @click="handleDelete(record)">删除</a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </a-space>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  PlusOutlined,
  CheckCircleFilled,
  BookOutlined,
  ClockCircleOutlined,
  EyeOutlined,
  UserOutlined,
  StarFilled
} from '@ant-design/icons-vue'
import { CONTENT_SOURCE_CONFIG } from '@/types/content'
import type { ContentSource } from '@/types/content'
import { TRIGGER_DOMAINS } from '@/constants'

const router = useRouter()
const loading = ref(false)
const defaultCover = 'https://via.placeholder.com/160x90?text=Course'

const filters = reactive({
  source: undefined as ContentSource | undefined,
  level: undefined as string | undefined,
  domain: undefined as string | undefined,
  category: undefined as string | undefined,
  status: undefined as string | undefined,
  keyword: ''
})

const stats = reactive({
  total: 28,
  platform: 12,
  expert: 8,
  pending: 3
})

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 个课程`
})

const levelColors: Record<string, string> = {
  L0: 'blue',
  L1: 'green',
  L2: 'orange',
  L3: 'red',
  L4: 'purple'
}

const categoryLabels: Record<string, string> = {
  knowledge: '知识体系',
  method: '方法体系',
  skill: '核心技能',
  value: '观念心智',
  practice: '实践练习',
  case: '案例学习'
}

const statusMap: Record<string, { badge: string; text: string }> = {
  draft: { badge: 'default', text: '草稿' },
  pending: { badge: 'warning', text: '待审核' },
  published: { badge: 'success', text: '已上架' },
  offline: { badge: 'error', text: '已下架' }
}

const columns = [
  { title: '封面', key: 'cover', width: 100 },
  { title: '课程信息', key: 'title', width: 280 },
  { title: '作者', key: 'author', width: 150 },
  { title: '数据统计', key: 'stats', width: 180 },
  { title: '状态', key: 'status', width: 100 },
  { title: '更新时间', dataIndex: 'updated_at', width: 120 },
  { title: '操作', key: 'action', width: 140, fixed: 'right' }
]

// 辅助函数
const getSourceLabel = (source: ContentSource) => CONTENT_SOURCE_CONFIG[source]?.label || source
const getSourceColor = (source: ContentSource) => CONTENT_SOURCE_CONFIG[source]?.color || '#666'
const getDomainLabel = (domain: string) => TRIGGER_DOMAINS.find(d => d.value === domain)?.label || domain
const formatNumber = (num: number) => {
  if (num >= 10000) return (num / 10000).toFixed(1) + 'w'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k'
  return num.toString()
}

// 模拟数据（扩展多来源）
const courses = ref([
  {
    course_id: '1',
    title: '行为健康入门',
    source: 'platform' as ContentSource,
    level: 'L0',
    category: 'knowledge',
    domain: 'stress',
    cover_url: '',
    chapter_count: 6,
    duration_minutes: 90,
    view_count: 15680,
    enroll_count: 856,
    avg_rating: 4.8,
    author_id: 'platform',
    author_name: '平台官方',
    author_avatar: '',
    author_verified: true,
    status: 'published',
    updated_at: '2026-01-20'
  },
  {
    course_id: '2',
    title: '正念冥想：从入门到精通',
    source: 'expert' as ContentSource,
    level: 'L0',
    category: 'practice',
    domain: 'stress',
    cover_url: '',
    chapter_count: 12,
    duration_minutes: 240,
    view_count: 12340,
    enroll_count: 678,
    avg_rating: 4.9,
    author_id: 'expert1',
    author_name: '李明远',
    author_title: '正念导师',
    author_avatar: '',
    author_verified: true,
    status: 'published',
    updated_at: '2026-01-18'
  },
  {
    course_id: '3',
    title: '代谢与慢病风险入门',
    source: 'platform' as ContentSource,
    level: 'L1',
    category: 'knowledge',
    domain: 'glucose',
    cover_url: '',
    chapter_count: 8,
    duration_minutes: 120,
    view_count: 8920,
    enroll_count: 234,
    avg_rating: 4.7,
    author_id: 'platform',
    author_name: '平台官方',
    author_verified: true,
    status: 'published',
    updated_at: '2026-01-19'
  },
  {
    course_id: '4',
    title: '睡眠改善实战指南',
    source: 'expert' as ContentSource,
    level: 'L0',
    category: 'method',
    domain: 'sleep',
    cover_url: '',
    chapter_count: 8,
    duration_minutes: 150,
    view_count: 9560,
    enroll_count: 432,
    avg_rating: 4.6,
    author_id: 'expert2',
    author_name: '王睡眠专家',
    author_title: '睡眠医学博士',
    author_avatar: '',
    author_verified: true,
    status: 'published',
    updated_at: '2026-01-15'
  },
  {
    course_id: '5',
    title: '高级动机访谈技术',
    source: 'platform' as ContentSource,
    level: 'L2',
    category: 'skill',
    cover_url: '',
    chapter_count: 10,
    duration_minutes: 300,
    view_count: 3450,
    enroll_count: 89,
    avg_rating: 4.9,
    author_id: 'platform',
    author_name: '平台官方',
    author_verified: true,
    status: 'draft',
    updated_at: '2026-01-24'
  },
  {
    course_id: '6',
    title: '情绪管理教练实战',
    source: 'coach' as ContentSource,
    level: 'L1',
    category: 'case',
    domain: 'stress',
    cover_url: '',
    chapter_count: 6,
    duration_minutes: 90,
    view_count: 0,
    enroll_count: 0,
    author_id: 'coach1',
    author_name: '张教练',
    author_title: 'L3高级教练',
    author_avatar: '',
    author_verified: true,
    status: 'pending',
    review_status: 'pending',
    updated_at: '2026-02-03'
  }
])

const fetchCourses = () => {
  loading.value = true
  // TODO: 调用API获取课程列表，支持筛选
  setTimeout(() => {
    loading.value = false
    pagination.total = courses.value.length
  }, 500)
}

const handleTableChange = (pag: any) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchCourses()
}

const handlePublish = (record: any) => {
  Modal.confirm({
    title: '确认上架',
    content: `确定要上架课程「${record.title}」吗？`,
    onOk() {
      record.status = 'published'
      message.success('上架成功')
    }
  })
}

const handleOffline = (record: any) => {
  Modal.confirm({
    title: '确认下架',
    content: `确定要下架课程「${record.title}」吗？`,
    onOk() {
      record.status = 'offline'
      message.success('下架成功')
    }
  })
}

const handleReview = (record: any) => {
  router.push(`/content/review?id=${record.course_id}&type=course`)
}

const handlePreview = (record: any) => {
  message.info('预览功能开发中')
}

const handleDelete = (record: any) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除课程「${record.title}」吗？此操作不可恢复。`,
    okType: 'danger',
    onOk() {
      const index = courses.value.findIndex(c => c.course_id === record.course_id)
      if (index > -1) {
        courses.value.splice(index, 1)
        message.success('删除成功')
      }
    }
  })
}

onMounted(() => {
  fetchCourses()
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

.course-title {
  font-weight: 500;
  margin-bottom: 6px;
}

.course-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.author-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.author-info {
  line-height: 1.4;
}

.author-name {
  font-size: 13px;
}

.verified-icon {
  color: #1890ff;
  font-size: 12px;
  margin-left: 4px;
}

.author-title {
  font-size: 11px;
  color: #999;
}

.course-stats {
  color: #666;
  font-size: 12px;
  margin-bottom: 4px;
}

.course-stats span {
  margin-right: 10px;
}
</style>
