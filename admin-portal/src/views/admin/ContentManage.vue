<!--
  内容管理 — ContentItem CRUD + 发布管理
  路由: /admin/content-manage
-->
<template>
  <div class="content-manage">
    <a-page-header title="内容管理" @back="$router.back()" />

    <!-- 过滤栏 -->
    <a-card :bordered="false" style="margin-bottom: 16px">
      <div class="filter-bar">
        <a-input-search
          v-model:value="filters.keyword"
          placeholder="搜索标题"
          style="width: 220px"
          allowClear
          @search="loadContent"
        />
        <a-select
          v-model:value="filters.content_type"
          placeholder="内容类型"
          style="width: 140px"
          allowClear
          @change="loadContent"
        >
          <a-select-option v-for="t in contentTypeOptions" :key="t.value" :value="t.value">
            {{ t.label }}
          </a-select-option>
        </a-select>
        <a-select
          v-model:value="filters.status"
          placeholder="状态"
          style="width: 120px"
          allowClear
          @change="loadContent"
        >
          <a-select-option value="draft">草稿</a-select-option>
          <a-select-option value="published">已发布</a-select-option>
          <a-select-option value="archived">已归档</a-select-option>
        </a-select>
        <a-select
          v-model:value="filters.domain"
          placeholder="所属领域"
          style="width: 140px"
          allowClear
          @change="loadContent"
        >
          <a-select-option v-for="d in domainOptions" :key="d.value" :value="d.value">
            {{ d.label }}
          </a-select-option>
        </a-select>
        <div style="flex: 1" />
        <a-button @click="handleBatchPublish" :disabled="selectedRowKeys.length === 0" :loading="batchPublishing">
          批量发布 ({{ selectedRowKeys.length }})
        </a-button>
        <a-button type="primary" @click="openCreateModal">
          <template #icon><PlusOutlined /></template>
          创建内容
        </a-button>
      </div>
    </a-card>

    <!-- 内容列表 -->
    <a-spin :spinning="tableLoading">
      <div class="list-card-container">
        <ListCard
          v-for="record in contentList"
          :key="record.id"
        >
          <template #title>
            <a-checkbox
              :checked="selectedRowKeys.includes(record.id)"
              @change="toggleSelectItem(record.id)"
              @click.stop
              style="margin-right: 8px"
            />
            <span>{{ record.title }}</span>
          </template>
          <template #subtitle>
            <a-tag :color="typeColor(record.content_type)">{{ typeLabel(record.content_type) }}</a-tag>
            <a-tag v-if="record.domain">{{ domainLabel(record.domain) }}</a-tag>
            <a-badge
              :status="record.status === 'published' ? 'success' : record.status === 'archived' ? 'default' : 'processing'"
              :text="statusLabel(record.status)"
            />
          </template>
          <template #meta>
            <span>浏览 {{ record.view_count ?? 0 }}</span>
            <span class="meta-divider">|</span>
            <span>点赞 {{ record.like_count ?? 0 }}</span>
            <span class="meta-divider">|</span>
            <span>{{ formatDate(record.created_at) }}</span>
          </template>
          <template #actions>
            <a-button size="small" @click="openEditModal(record)">编辑</a-button>
            <a-button
              v-if="record.status === 'draft'"
              size="small"
              type="primary"
              :loading="publishingId === record.id"
              @click="handlePublish(record)"
            >
              发布
            </a-button>
            <a-popconfirm
              title="确定删除此内容？"
              @confirm="handleDelete(record)"
              okText="删除"
              cancelText="取消"
            >
              <a-button size="small" danger>删除</a-button>
            </a-popconfirm>
          </template>
        </ListCard>
      </div>
      <div v-if="contentList.length === 0 && !tableLoading" style="text-align: center; padding: 40px; color: #999">
        暂无内容数据
      </div>
    </a-spin>
    <div style="display: flex; justify-content: flex-end; margin-top: 16px">
      <a-pagination
        v-model:current="pagination.current"
        v-model:pageSize="pagination.pageSize"
        :total="pagination.total"
        show-size-changer
        :show-total="(t: number) => `共 ${t} 条`"
        @change="onPaginationChange"
      />
    </div>

    <!-- 创建/编辑弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      :title="editingRecord ? '编辑内容' : '创建内容'"
      :confirmLoading="modalSaving"
      width="720px"
      @ok="handleModalOk"
      okText="保存"
      cancelText="取消"
    >
      <a-form layout="vertical" :model="formState" ref="formRef">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="内容类型" name="content_type" :rules="[{ required: true, message: '请选择内容类型' }]">
              <a-select v-model:value="formState.content_type" placeholder="选择类型">
                <a-select-option v-for="t in contentTypeOptions" :key="t.value" :value="t.value">
                  {{ t.label }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="所属领域" name="domain">
              <a-select v-model:value="formState.domain" placeholder="选择领域" allowClear>
                <a-select-option v-for="d in domainOptions" :key="d.value" :value="d.value">
                  {{ d.label }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="标题" name="title" :rules="[{ required: true, message: '请输入标题' }]">
          <a-input v-model:value="formState.title" placeholder="输入内容标题" :maxlength="120" showCount />
        </a-form-item>

        <a-form-item label="正文" name="body" :rules="[{ required: true, message: '请输入正文' }]">
          <a-textarea
            v-model:value="formState.body"
            placeholder="输入正文内容（支持 Markdown）"
            :rows="8"
            :maxlength="10000"
            showCount
          />
        </a-form-item>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="封面图 URL" name="cover_url">
              <a-input v-model:value="formState.cover_url" placeholder="https://..." allowClear />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="难度等级" name="level">
              <a-select v-model:value="formState.level" placeholder="选择等级" allowClear>
                <a-select-option :value="1">L1 入门</a-select-option>
                <a-select-option :value="2">L2 基础</a-select-option>
                <a-select-option :value="3">L3 进阶</a-select-option>
                <a-select-option :value="4">L4 高级</a-select-option>
                <a-select-option :value="5">L5 专家</a-select-option>
                <a-select-option :value="6">L6 大师</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import type { TablePaginationConfig } from 'ant-design-vue'
import request from '@/api/request'
import { PlusOutlined } from '@ant-design/icons-vue'
import ListCard from '@/components/core/ListCard.vue'

// ============ 类型定义 ============

interface ContentItem {
  id: number
  content_type: string
  title: string
  body: string
  cover_url?: string
  domain?: string
  level?: number
  status: string
  view_count: number
  like_count: number
  created_at: string
}

// ============ 选项常量 ============

const contentTypeOptions = [
  { value: 'article', label: '文章' },
  { value: 'video', label: '视频' },
  { value: 'audio', label: '音频' },
  { value: 'infographic', label: '信息图' },
  { value: 'quiz', label: '测验' },
  { value: 'guide', label: '指南' },
  { value: 'case_study', label: '案例' },
]

const domainOptions = [
  { value: 'metabolic', label: '代谢' },
  { value: 'sleep', label: '睡眠' },
  { value: 'emotion', label: '情绪' },
  { value: 'motivation', label: '动机' },
  { value: 'nutrition', label: '营养' },
  { value: 'exercise', label: '运动' },
  { value: 'tcm', label: '中医' },
  { value: 'coaching', label: '教练' },
]

// ============ 列表数据 ============

const contentList = ref<ContentItem[]>([])
const tableLoading = ref(false)
const selectedRowKeys = ref<number[]>([])

const filters = reactive({
  keyword: '',
  content_type: undefined as string | undefined,
  status: undefined as string | undefined,
  domain: undefined as string | undefined,
})

const pagination = reactive({
  current: 1,
  pageSize: 15,
  total: 0,
})

// columns removed — now using ListCard layout

const loadContent = async () => {
  tableLoading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.current,
      page_size: pagination.pageSize,
    }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.content_type) params.content_type = filters.content_type
    if (filters.status) params.status = filters.status
    if (filters.domain) params.domain = filters.domain

    const { data } = await request.get('v1/content-manage/list', { params })
    contentList.value = data.items ?? data.content ?? data ?? []
    pagination.total = data.total ?? contentList.value.length
  } catch (e: any) {
    console.error('加载内容列表失败:', e)
  } finally {
    tableLoading.value = false
  }
}

const handleTableChange = (pag: TablePaginationConfig) => {
  pagination.current = pag.current ?? 1
  pagination.pageSize = pag.pageSize ?? 15
  loadContent()
}

const onSelectChange = (keys: number[]) => {
  selectedRowKeys.value = keys
}

const toggleSelectItem = (id: number) => {
  const idx = selectedRowKeys.value.indexOf(id)
  if (idx >= 0) {
    selectedRowKeys.value.splice(idx, 1)
  } else {
    selectedRowKeys.value.push(id)
  }
}

const onPaginationChange = (page: number, pageSize: number) => {
  pagination.current = page
  pagination.pageSize = pageSize
  loadContent()
}

// ============ 创建/编辑弹窗 ============

const modalVisible = ref(false)
const modalSaving = ref(false)
const editingRecord = ref<ContentItem | null>(null)
const formRef = ref()

const formState = reactive({
  content_type: '' as string,
  title: '',
  body: '',
  cover_url: '',
  domain: undefined as string | undefined,
  level: undefined as number | undefined,
})

const openCreateModal = () => {
  editingRecord.value = null
  formState.content_type = ''
  formState.title = ''
  formState.body = ''
  formState.cover_url = ''
  formState.domain = undefined
  formState.level = undefined
  modalVisible.value = true
}

const openEditModal = (record: ContentItem) => {
  editingRecord.value = record
  formState.content_type = record.content_type
  formState.title = record.title
  formState.body = record.body || ''
  formState.cover_url = record.cover_url || ''
  formState.domain = record.domain || undefined
  formState.level = record.level || undefined
  modalVisible.value = true
}

const handleModalOk = async () => {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  modalSaving.value = true
  try {
    const payload = {
      content_type: formState.content_type,
      title: formState.title,
      body: formState.body,
      cover_url: formState.cover_url || undefined,
      domain: formState.domain || undefined,
      level: formState.level || undefined,
    }

    if (editingRecord.value) {
      await request.put(`v1/content-manage/${editingRecord.value.id}`, payload)
      message.success('内容已更新')
    } else {
      await request.post('v1/content-manage/create', payload)
      message.success('内容已创建')
    }

    modalVisible.value = false
    await loadContent()
  } catch (e: any) {
    console.error('保存失败:', e)
    message.error(e.response?.data?.detail || '保存失败')
  } finally {
    modalSaving.value = false
  }
}

// ============ 发布操作 ============

const publishingId = ref<number | null>(null)

const handlePublish = async (record: ContentItem) => {
  publishingId.value = record.id
  try {
    await request.post(`v1/content-manage/${record.id}/publish`)
    message.success(`"${record.title}" 已发布`)
    await loadContent()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '发布失败')
  } finally {
    publishingId.value = null
  }
}

const batchPublishing = ref(false)

const handleBatchPublish = async () => {
  if (selectedRowKeys.value.length === 0) return
  batchPublishing.value = true
  try {
    await request.post('v1/content-manage/batch-publish', {
      ids: selectedRowKeys.value,
    })
    message.success(`已批量发布 ${selectedRowKeys.value.length} 条内容`)
    selectedRowKeys.value = []
    await loadContent()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '批量发布失败')
  } finally {
    batchPublishing.value = false
  }
}

// ============ 删除 ============

const handleDelete = async (record: ContentItem) => {
  try {
    await request.delete(`v1/content-manage/${record.id}`)
    message.success('已删除')
    await loadContent()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '删除失败')
  }
}

// ============ 工具函数 ============

const typeColor = (t: string): string => {
  const map: Record<string, string> = {
    article: 'blue',
    video: 'purple',
    audio: 'cyan',
    infographic: 'geekblue',
    quiz: 'orange',
    guide: 'green',
    case_study: 'magenta',
  }
  return map[t] || 'default'
}

const typeLabel = (t: string): string => {
  const found = contentTypeOptions.find(o => o.value === t)
  return found ? found.label : t
}

const statusLabel = (s: string): string => {
  const map: Record<string, string> = {
    draft: '草稿',
    published: '已发布',
    archived: '已归档',
  }
  return map[s] || s
}

const domainLabel = (d: string | undefined): string => {
  if (!d) return '--'
  const found = domainOptions.find(o => o.value === d)
  return found ? found.label : d
}

const formatDate = (d: string): string => {
  if (!d) return '--'
  return new Date(d).toLocaleString('zh-CN')
}

// ============ 生命周期 ============

onMounted(() => {
  loadContent()
})
</script>

<style scoped>
.list-card-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.content-manage {
  padding: 0;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.meta-divider {
  color: #d9d9d9;
  margin: 0 4px;
}

:deep(.ant-page-header) {
  padding: 0 0 16px 0;
}
</style>
