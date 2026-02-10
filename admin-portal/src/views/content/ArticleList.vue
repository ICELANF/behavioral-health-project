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
            <a-select-option v-for="(domain, key) in TRIGGER_DOMAINS" :key="key" :value="key">
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
            <a-select-option v-for="(domain, key) in TRIGGER_DOMAINS" :key="key" :value="key">
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
import request from '@/api/request'
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
const getDomainLabel = (domain: string) => (TRIGGER_DOMAINS as any)[domain]?.label || domain
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
  window.open(`/content/articles?preview=${record.article_id}`, '_blank')
}

const handleSave = async () => {
  try {
    if (editingArticle.value) {
      await request.put(`/v1/content-manage/${editingArticle.value.article_id}`, {
        title: editForm.title,
        body: editForm.content_html,
        domain: editForm.domain,
        level: editForm.level,
      })
    } else {
      await request.post('/v1/content-manage/create', {
        content_type: 'article',
        title: editForm.title,
        body: editForm.content_html,
        domain: editForm.domain,
        level: editForm.level,
      })
    }
    message.success('保存成功')
    editModalVisible.value = false
    fetchArticles()
  } catch (e) {
    console.error('Save failed:', e)
  }
}

const handleSaveAsDraft = async () => {
  try {
    await request.post('/v1/content-manage/create', {
      content_type: 'article',
      title: editForm.title,
      body: editForm.content_html,
      domain: editForm.domain,
      level: editForm.level,
    })
    message.success('已存为草稿')
    editModalVisible.value = false
    fetchArticles()
  } catch (e) {
    console.error('Save draft failed:', e)
  }
}

const handleSubmitReview = (record: ArticleContent) => {
  message.success('已提交审核')
  fetchArticles()
}

const handleOffline = async (record: ArticleContent) => {
  try {
    await request.delete(`/v1/content-manage/${record.article_id}`)
    message.success('已下架')
    fetchArticles()
  } catch (e) {
    console.error('Offline failed:', e)
  }
}

const handlePublish = async (record: ArticleContent) => {
  try {
    await request.post(`/v1/content-manage/${record.article_id}/publish`)
    message.success('已重新发布')
    fetchArticles()
  } catch (e) {
    console.error('Publish failed:', e)
  }
}

const handleDelete = async (record: ArticleContent) => {
  try {
    await request.delete(`/v1/content-manage/${record.article_id}`)
    message.success('已删除')
    fetchArticles()
  } catch (e) {
    console.error('Delete failed:', e)
  }
}

const handleBatchReview = () => {
  message.info('批量审核 ' + selectedRows.value.length + ' 篇文章')
}

// 获取文章列表 (调用真实 API)
const fetchArticles = async () => {
  loading.value = true
  try {
    const params: Record<string, any> = {
      content_type: 'article',
      skip: (pagination.current - 1) * pagination.pageSize,
      limit: pagination.pageSize,
    }
    if (filters.status) params.status = filters.status
    if (filters.domain) params.domain = filters.domain

    const { data } = await request.get('/v1/content-manage/list', { params })

    articles.value = (data.items || []).map((item: any) => ({
      article_id: String(item.id),
      type: 'article',
      source: item.tenant_id ? 'expert' : 'platform',
      status: item.status || 'draft',
      title: item.title,
      summary: item.body?.substring(0, 100) || '',
      cover_url: item.cover_url || '',
      content_html: item.body || '',
      word_count: item.body ? item.body.length : 0,
      read_time: item.body ? Math.max(1, Math.ceil(item.body.length / 300)) : 1,
      domain: item.domain || '',
      tags: [],
      level: item.level || 'beginner',
      author_id: String(item.author_id || ''),
      author_name: '平台管理员',
      author_avatar: '',
      author_title: '',
      author_verified: true,
      visibility: 'public',
      view_count: item.view_count || 0,
      like_count: item.like_count || 0,
      collect_count: item.collect_count || 0,
      comment_count: item.comment_count || 0,
      share_count: 0,
      review_status: item.status === 'published' ? 'approved' : 'pending',
      created_at: item.created_at,
      updated_at: item.updated_at,
      published_at: item.status === 'published' ? item.updated_at : null,
    })) as ArticleContent[]
    pagination.total = data.total || 0

    // 客户端关键词过滤
    if (filters.keyword) {
      const kw = filters.keyword.toLowerCase()
      articles.value = articles.value.filter(a => a.title.toLowerCase().includes(kw))
    }
  } catch (e) {
    console.error('Failed to fetch articles:', e)
    message.error('获取文章列表失败')
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
