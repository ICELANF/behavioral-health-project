<template>
  <div class="article-list">
    <!-- 搜索筛选区 -->
    <a-card class="filter-card">
      <a-form layout="inline">
        <a-form-item label="关键词">
          <a-input v-model:value="filters.keyword" placeholder="搜索标题或内容" allow-clear style="width: 200px" />
        </a-form-item>
        <a-form-item label="来源">
          <a-select v-model:value="filters.source" placeholder="全部来源" allow-clear style="width: 120px">
            <a-select-option v-for="(config, key) in CONTENT_SOURCE_CONFIG" :key="key" :value="key">
              {{ config.label }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="领域">
          <a-select v-model:value="filters.domain" placeholder="全部领域" allow-clear style="width: 120px">
            <a-select-option v-for="domain in TRIGGER_DOMAINS" :key="domain.value" :value="domain.value">
              {{ domain.label }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="状态">
          <a-select v-model:value="filters.status" placeholder="全部状态" allow-clear style="width: 100px">
            <a-select-option value="draft">草稿</a-select-option>
            <a-select-option value="pending">待审核</a-select-option>
            <a-select-option value="published">已发布</a-select-option>
            <a-select-option value="offline">已下架</a-select-option>
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

    <!-- 操作栏 -->
    <div class="action-bar">
      <a-button type="primary" @click="handleCreate">
        <template #icon><PlusOutlined /></template>
        创建文章
      </a-button>
      <a-button @click="handleBatchReview" :disabled="selectedRows.length === 0">
        批量审核
      </a-button>
      <span class="selected-info" v-if="selectedRows.length > 0">
        已选择 {{ selectedRows.length }} 项
      </span>
    </div>

    <!-- 文章列表 -->
    <a-table
      :columns="columns"
      :data-source="articles"
      :loading="loading"
      :pagination="pagination"
      :row-selection="{ selectedRowKeys: selectedKeys, onChange: onSelectChange }"
      row-key="article_id"
      @change="handleTableChange"
    >
      <!-- 标题列 -->
      <template #title="{ record }">
        <div class="article-title-cell">
          <img v-if="record.cover_url" :src="record.cover_url" class="article-cover" />
          <div class="article-info">
            <div class="title">{{ record.title }}</div>
            <div class="meta">
              <a-tag :color="getSourceColor(record.source)">{{ getSourceLabel(record.source) }}</a-tag>
              <span class="domain">{{ getDomainLabel(record.domain) }}</span>
              <span class="stats">{{ record.word_count }}字 · {{ record.read_time }}分钟</span>
            </div>
          </div>
        </div>
      </template>

      <!-- 作者列 -->
      <template #author="{ record }">
        <div class="author-cell">
          <a-avatar :src="record.author_avatar" size="small">
            {{ record.author_name?.charAt(0) }}
          </a-avatar>
          <span class="author-name">{{ record.author_name }}</span>
          <CheckCircleFilled v-if="record.author_verified" class="verified-icon" />
        </div>
      </template>

      <!-- 状态列 -->
      <template #status="{ record }">
        <a-tag :color="getStatusColor(record.status)">{{ getStatusLabel(record.status) }}</a-tag>
        <a-tag v-if="record.review_status === 'pending'" color="orange">待审核</a-tag>
      </template>

      <!-- 数据列 -->
      <template #stats="{ record }">
        <div class="stats-cell">
          <span><EyeOutlined /> {{ formatNumber(record.view_count) }}</span>
          <span><LikeOutlined /> {{ formatNumber(record.like_count) }}</span>
          <span><StarOutlined /> {{ formatNumber(record.collect_count) }}</span>
        </div>
      </template>

      <!-- 操作列 -->
      <template #action="{ record }">
        <a-space>
          <a @click="handleView(record)">查看</a>
          <a @click="handleEdit(record)">编辑</a>
          <a-dropdown>
            <a>更多 <DownOutlined /></a>
            <template #overlay>
              <a-menu>
                <a-menu-item v-if="record.status === 'draft'" @click="handleSubmitReview(record)">
                  提交审核
                </a-menu-item>
                <a-menu-item v-if="record.status === 'published'" @click="handleOffline(record)">
                  下架
                </a-menu-item>
                <a-menu-item v-if="record.status === 'offline'" @click="handlePublish(record)">
                  重新发布
                </a-menu-item>
                <a-menu-divider />
                <a-menu-item danger @click="handleDelete(record)">删除</a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </a-space>
      </template>
    </a-table>

    <!-- 创建/编辑弹窗 -->
    <a-modal
      v-model:open="editModalVisible"
      :title="editingArticle ? '编辑文章' : '创建文章'"
      width="800px"
      :footer="null"
    >
      <a-form :model="editForm" :label-col="{ span: 4 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="标题" required>
          <a-input v-model:value="editForm.title" placeholder="请输入文章标题" />
        </a-form-item>
        <a-form-item label="摘要">
          <a-textarea v-model:value="editForm.summary" :rows="2" placeholder="200字以内的摘要" :maxlength="200" show-count />
        </a-form-item>
        <a-form-item label="封面">
          <a-upload
            :max-count="1"
            list-type="picture-card"
            accept="image/*"
          >
            <div>
              <PlusOutlined />
              <div style="margin-top: 8px">上传封面</div>
            </div>
          </a-upload>
        </a-form-item>
        <a-form-item label="领域" required>
          <a-select v-model:value="editForm.domain" placeholder="选择所属领域">
            <a-select-option v-for="domain in TRIGGER_DOMAINS" :key="domain.value" :value="domain.value">
              {{ domain.label }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="难度">
          <a-radio-group v-model:value="editForm.level">
            <a-radio-button value="beginner">入门</a-radio-button>
            <a-radio-button value="intermediate">进阶</a-radio-button>
            <a-radio-button value="advanced">高级</a-radio-button>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="标签">
          <a-select v-model:value="editForm.tags" mode="tags" placeholder="添加标签" />
        </a-form-item>
        <a-form-item label="正文" required>
          <a-textarea v-model:value="editForm.content_html" :rows="10" placeholder="支持 HTML 格式" />
        </a-form-item>
        <a-form-item label="可见范围">
          <a-radio-group v-model:value="editForm.visibility">
            <a-radio value="public">公开</a-radio>
            <a-radio value="registered">注册用户</a-radio>
            <a-radio value="level_required">等级限制</a-radio>
            <a-radio value="paid">付费</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item :wrapper-col="{ offset: 4 }">
          <a-space>
            <a-button type="primary" @click="handleSave">保存</a-button>
            <a-button @click="handleSaveAsDraft">存为草稿</a-button>
            <a-button @click="editModalVisible = false">取消</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import {
  SearchOutlined,
  PlusOutlined,
  EyeOutlined,
  LikeOutlined,
  StarOutlined,
  DownOutlined,
  CheckCircleFilled
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import type { ArticleContent, ContentSource, ContentStatus } from '@/types/content'
import { CONTENT_SOURCE_CONFIG } from '@/types/content'
import { TRIGGER_DOMAINS } from '@/constants'

// 筛选条件
const filters = reactive({
  keyword: '',
  source: undefined as ContentSource | undefined,
  domain: undefined as string | undefined,
  status: undefined as ContentStatus | undefined
})

// 表格相关
const loading = ref(false)
const articles = ref<ArticleContent[]>([])
const selectedKeys = ref<string[]>([])
const selectedRows = ref<ArticleContent[]>([])
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`
})

// 编辑弹窗
const editModalVisible = ref(false)
const editingArticle = ref<ArticleContent | null>(null)
const editForm = reactive({
  title: '',
  summary: '',
  cover_url: '',
  domain: '' as string,
  level: 'beginner' as 'beginner' | 'intermediate' | 'advanced',
  tags: [] as string[],
  content_html: '',
  visibility: 'public' as string
})

// 表格列配置
const columns = [
  {
    title: '文章信息',
    dataIndex: 'title',
    key: 'title',
    width: 400,
    slots: { customRender: 'title' }
  },
  {
    title: '作者',
    dataIndex: 'author_name',
    key: 'author',
    width: 150,
    slots: { customRender: 'author' }
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 120,
    slots: { customRender: 'status' }
  },
  {
    title: '数据',
    key: 'stats',
    width: 180,
    slots: { customRender: 'stats' }
  },
  {
    title: '发布时间',
    dataIndex: 'published_at',
    key: 'published_at',
    width: 120,
    customRender: ({ text }: { text: string }) => text ? new Date(text).toLocaleDateString() : '-'
  },
  {
    title: '操作',
    key: 'action',
    width: 150,
    fixed: 'right',
    slots: { customRender: 'action' }
  }
]

// 辅助函数
const getSourceLabel = (source: ContentSource) => CONTENT_SOURCE_CONFIG[source]?.label || source
const getSourceColor = (source: ContentSource) => CONTENT_SOURCE_CONFIG[source]?.color || '#666'
const getDomainLabel = (domain: string) => TRIGGER_DOMAINS.find(d => d.value === domain)?.label || domain
const getStatusLabel = (status: ContentStatus) => {
  const map: Record<ContentStatus, string> = {
    draft: '草稿',
    pending: '待审核',
    revision: '待修改',
    published: '已发布',
    offline: '已下架',
    archived: '已归档'
  }
  return map[status] || status
}
const getStatusColor = (status: ContentStatus) => {
  const map: Record<ContentStatus, string> = {
    draft: 'default',
    pending: 'orange',
    revision: 'warning',
    published: 'green',
    offline: 'red',
    archived: 'gray'
  }
  return map[status] || 'default'
}
const formatNumber = (num: number) => {
  if (num >= 10000) return (num / 10000).toFixed(1) + 'w'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k'
  return num.toString()
}

// 事件处理
const handleSearch = () => {
  pagination.current = 1
  fetchArticles()
}

const handleReset = () => {
  filters.keyword = ''
  filters.source = undefined
  filters.domain = undefined
  filters.status = undefined
  handleSearch()
}

const handleTableChange = (pag: any) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchArticles()
}

const onSelectChange = (keys: string[], rows: ArticleContent[]) => {
  selectedKeys.value = keys
  selectedRows.value = rows
}

const handleCreate = () => {
  editingArticle.value = null
  Object.assign(editForm, {
    title: '',
    summary: '',
    cover_url: '',
    domain: '',
    level: 'beginner',
    tags: [],
    content_html: '',
    visibility: 'public'
  })
  editModalVisible.value = true
}

const handleEdit = (record: ArticleContent) => {
  editingArticle.value = record
  Object.assign(editForm, {
    title: record.title,
    summary: record.summary,
    cover_url: record.cover_url,
    domain: record.domain,
    level: record.level,
    tags: record.tags,
    content_html: record.content_html,
    visibility: record.visibility
  })
  editModalVisible.value = true
}

const handleView = (record: ArticleContent) => {
  // TODO: 打开预览弹窗
  message.info('查看文章: ' + record.title)
}

const handleSave = () => {
  message.success('保存成功')
  editModalVisible.value = false
  fetchArticles()
}

const handleSaveAsDraft = () => {
  message.success('已存为草稿')
  editModalVisible.value = false
  fetchArticles()
}

const handleSubmitReview = (record: ArticleContent) => {
  message.success('已提交审核')
  fetchArticles()
}

const handleOffline = (record: ArticleContent) => {
  message.success('已下架')
  fetchArticles()
}

const handlePublish = (record: ArticleContent) => {
  message.success('已重新发布')
  fetchArticles()
}

const handleDelete = (record: ArticleContent) => {
  message.success('已删除')
  fetchArticles()
}

const handleBatchReview = () => {
  message.info('批量审核 ' + selectedRows.value.length + ' 篇文章')
}

// 获取文章列表
const fetchArticles = async () => {
  loading.value = true
  try {
    // TODO: 调用真实 API
    // 模拟数据
    articles.value = [
      {
        article_id: 'a1',
        type: 'article',
        source: 'platform',
        status: 'published',
        title: '情绪管理入门：认识你的情绪',
        summary: '本文帮助你了解常见的情绪类型，以及如何识别和接纳自己的情绪。',
        cover_url: '',
        content_html: '<p>内容...</p>',
        word_count: 2500,
        read_time: 8,
        domain: 'emotion',
        tags: ['情绪管理', '入门'],
        level: 'beginner',
        target_stages: ['contemplation', 'preparation'],
        author_id: 'platform',
        author_name: '平台运营',
        author_avatar: '',
        author_title: '官方账号',
        author_verified: true,
        visibility: 'public',
        view_count: 12580,
        like_count: 856,
        collect_count: 423,
        comment_count: 67,
        share_count: 128,
        review_status: 'approved',
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z',
        published_at: '2025-01-15T12:00:00Z'
      },
      {
        article_id: 'a2',
        type: 'article',
        source: 'expert',
        status: 'published',
        title: '正念冥想：7天入门指南',
        summary: '由资深正念导师撰写的入门指南，手把手教你开始正念练习。',
        cover_url: '',
        content_html: '<p>内容...</p>',
        word_count: 3200,
        read_time: 12,
        domain: 'mindfulness',
        tags: ['正念', '冥想', '入门'],
        level: 'beginner',
        author_id: 'expert1',
        author_name: '李明远',
        author_avatar: '',
        author_title: '正念导师',
        author_verified: true,
        visibility: 'public',
        view_count: 8920,
        like_count: 672,
        collect_count: 534,
        comment_count: 45,
        share_count: 89,
        review_status: 'approved',
        created_at: '2025-01-20T10:00:00Z',
        updated_at: '2025-01-20T10:00:00Z',
        published_at: '2025-01-20T14:00:00Z'
      },
      {
        article_id: 'a3',
        type: 'article',
        source: 'coach',
        status: 'pending',
        title: '睡眠改善实战：我的教练心得',
        summary: '作为健康教练，分享我帮助学员改善睡眠的实战经验。',
        cover_url: '',
        content_html: '<p>内容...</p>',
        word_count: 1800,
        read_time: 6,
        domain: 'sleep',
        tags: ['睡眠', '教练心得'],
        level: 'intermediate',
        author_id: 'coach1',
        author_name: '张教练',
        author_avatar: '',
        author_title: 'L3教练',
        author_verified: true,
        visibility: 'registered',
        view_count: 0,
        like_count: 0,
        collect_count: 0,
        comment_count: 0,
        share_count: 0,
        review_status: 'pending',
        created_at: '2026-02-04T10:00:00Z',
        updated_at: '2026-02-04T10:00:00Z'
      },
      {
        article_id: 'a4',
        type: 'article',
        source: 'sharer',
        status: 'draft',
        title: '我的戒烟100天',
        summary: '从一天两包到完全戒烟，分享我的心路历程。',
        cover_url: '',
        content_html: '<p>内容...</p>',
        word_count: 1500,
        read_time: 5,
        domain: 'chronic',
        tags: ['戒烟', '用户分享'],
        level: 'beginner',
        author_id: 'user123',
        author_name: '阳光少年',
        author_avatar: '',
        author_verified: false,
        visibility: 'public',
        view_count: 0,
        like_count: 0,
        collect_count: 0,
        comment_count: 0,
        share_count: 0,
        created_at: '2026-02-03T10:00:00Z',
        updated_at: '2026-02-03T10:00:00Z'
      }
    ] as ArticleContent[]
    pagination.total = articles.value.length
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchArticles()
})
</script>

<style scoped>
.article-list {
  padding: 24px;
}

.filter-card {
  margin-bottom: 16px;
}

.action-bar {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.selected-info {
  color: #1890ff;
  font-size: 14px;
}

.article-title-cell {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.article-cover {
  width: 80px;
  height: 60px;
  object-fit: cover;
  border-radius: 4px;
  background: #f5f5f5;
}

.article-info {
  flex: 1;
  min-width: 0;
}

.article-info .title {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.article-info .meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #999;
}

.author-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.author-name {
  font-size: 13px;
}

.verified-icon {
  color: #1890ff;
  font-size: 12px;
}

.stats-cell {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #666;
}

.stats-cell span {
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
