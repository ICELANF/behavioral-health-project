<!--
  专家内容工作室 — 知识文档 CRUD + 发布 / 挑战模板管理
  路由: /expert/content-studio/:tenantId
-->
<template>
  <div class="content-studio">
    <div class="cs-header">
      <h2>内容工作室</h2>
      <a-button size="small" @click="goBack">返回专家面板</a-button>
    </div>

    <a-tabs v-model:activeKey="activeTab" type="card">
      <!-- Tab 1: 知识库文档 -->
      <a-tab-pane key="documents" tab="知识库文档">
        <!-- 过滤栏 -->
        <div class="filter-bar">
          <a-input-search
            v-model:value="docFilters.keyword"
            placeholder="搜索标题"
            style="width:220px"
            @search="loadDocuments"
            allowClear
          />
          <a-select
            v-model:value="docFilters.status"
            placeholder="状态"
            style="width:120px"
            allowClear
            @change="loadDocuments"
          >
            <a-select-option value="draft">草稿</a-select-option>
            <a-select-option value="processing">处理中</a-select-option>
            <a-select-option value="ready">已发布</a-select-option>
            <a-select-option value="error">错误</a-select-option>
          </a-select>
          <a-select
            v-model:value="docFilters.domain"
            placeholder="领域"
            style="width:120px"
            allowClear
            @change="loadDocuments"
          >
            <a-select-option v-for="d in domainOptions" :key="d.value" :value="d.value">
              {{ d.label }}
            </a-select-option>
          </a-select>
          <a-button type="primary" @click="openCreateModal">创建文档</a-button>
        </div>

        <!-- 文档列表 -->
        <a-spin :spinning="docLoading">
          <div class="list-card-container">
            <ListCard v-for="record in documents" :key="record.id">
              <template #title>
                <span>{{ record.title }}</span>
                <a-tag :color="tierColor(record.evidence_tier)" style="margin-left: 8px">{{ record.evidence_tier || 'T3' }}</a-tag>
                <a-tag :color="statusColor(record.status)" style="margin-left: 4px">{{ statusLabel(record.status) }}</a-tag>
              </template>
              <template #subtitle>
                领域: {{ domainLabel(record.domain_id) }} | 块数: {{ record.chunk_count }}
              </template>
              <template #meta>
                <span>创建: {{ formatDate(record.created_at) }}</span>
              </template>
              <template #actions>
                <a-space wrap>
                  <a-button size="small" @click="openEditModal(record)">编辑</a-button>
                  <a-button
                    v-if="record.status === 'draft' || record.status === 'error'"
                    size="small"
                    type="primary"
                    :loading="publishingId === record.id"
                    @click="onPublish(record)"
                  >发布</a-button>
                  <a-button
                    v-if="record.status === 'ready'"
                    size="small"
                    @click="onUnpublish(record)"
                  >撤回</a-button>
                  <a-popconfirm title="确定删除此文档？" @confirm="onDelete(record)">
                    <a-button size="small" danger>删除</a-button>
                  </a-popconfirm>
                </a-space>
              </template>
            </ListCard>
          </div>
        </a-spin>
      </a-tab-pane>

      <!-- Tab 2: 挑战活动 -->
      <a-tab-pane key="challenges" tab="挑战活动">
        <a-spin :spinning="challengeLoading">
          <div class="list-card-container">
            <ListCard v-for="record in challenges" :key="record.id">
              <template #title>
                <span>{{ record.title }}</span>
                <a-tag :color="challengeStatusColor(record.status)" style="margin-left: 8px">{{ record.status }}</a-tag>
              </template>
              <template #subtitle>
                类别: {{ record.category }} | {{ record.duration_days }}天 | 报名: {{ record.enrollment_count }}人
              </template>
              <template #meta>
                <span>创建: {{ formatDate(record.created_at) }}</span>
              </template>
              <template #actions>
                <a-button size="small" @click="goToChallenge(record.id)">查看详情</a-button>
              </template>
            </ListCard>
          </div>
        </a-spin>
      </a-tab-pane>
    </a-tabs>

    <!-- 文档编辑 Modal -->
    <a-modal
      v-model:open="editModalVisible"
      :title="isCreate ? '创建知识文档' : '编辑知识文档'"
      :width="900"
      :confirmLoading="saving"
      @ok="onSaveDocument"
      @cancel="editModalVisible = false"
    >
      <a-form layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="标题" required>
              <a-input v-model:value="editForm.title" placeholder="文档标题" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="作者">
              <a-input v-model:value="editForm.author" placeholder="作者名" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="领域">
              <a-select v-model:value="editForm.domain_id" placeholder="选择领域" allowClear>
                <a-select-option v-for="d in domainOptions" :key="d.value" :value="d.value">
                  {{ d.label }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="优先级">
              <a-slider v-model:value="editForm.priority" :min="1" :max="10" :marks="{ 1: '1', 5: '5', 10: '10' }" />
            </a-form-item>
          </a-col>
        </a-row>
        <!-- 内容治理字段 -->
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="证据分层">
              <a-select v-model:value="editForm.evidence_tier" placeholder="选择证据等级" allowClear>
                <a-select-option v-for="t in tierOptions" :key="t.value" :value="t.value">
                  <a-tag :color="t.color" style="margin-right:4px">{{ t.value }}</a-tag>{{ t.label }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="内容类型">
              <a-select v-model:value="editForm.content_type" placeholder="选择内容类型" allowClear>
                <a-select-option v-for="ct in contentTypeOptions" :key="ct.value" :value="ct.value">
                  {{ ct.label }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="原始发布日期">
              <a-date-picker v-model:value="editForm.published_date" style="width:100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="过期时间">
              <a-date-picker v-model:value="editForm.expires_at" style="width:100%" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="文档内容 (Markdown)">
          <MdEditor
            v-model="editForm.raw_content"
            language="zh-CN"
            :style="{ height: '500px' }"
            :preview="true"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { MdEditor } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import dayjs from 'dayjs'
import type { Dayjs } from 'dayjs'
import { expertContentAPI } from '../../api/expert-content'
import ListCard from '@/components/core/ListCard.vue'

const route = useRoute()
const router = useRouter()
const tenantId = route.params.tenantId as string

const activeTab = ref('documents')

// ========== 证据分层 & 内容类型常量 ==========
const tierOptions = [
  { value: 'T1', label: '临床指南', color: 'red' },
  { value: 'T2', label: 'RCT/系统综述', color: 'orange' },
  { value: 'T3', label: '专家共识', color: 'blue' },
  { value: 'T4', label: '个人经验', color: 'default' },
]

const contentTypeOptions = [
  { value: 'guideline', label: '临床指南' },
  { value: 'consensus', label: '专家共识' },
  { value: 'rct', label: '随机对照试验' },
  { value: 'review', label: '综述/荟萃分析' },
  { value: 'expert_opinion', label: '专家意见' },
  { value: 'case_report', label: '病例报告' },
  { value: 'experience_sharing', label: '个人经验分享' },
]

function tierColor(tier: string) {
  const map: Record<string, string> = { T1: 'red', T2: 'orange', T3: 'blue', T4: 'default' }
  return map[tier] || 'default'
}

// ========== 知识文档 ==========
const documents = ref<any[]>([])
const docLoading = ref(false)
const docFilters = reactive({ keyword: '', status: undefined as string | undefined, domain: undefined as string | undefined })

// docColumns removed — replaced by ListCard layout

const domainOptions = [
  { value: 'nutrition', label: '营养' },
  { value: 'exercise', label: '运动' },
  { value: 'sleep', label: '睡眠' },
  { value: 'mental', label: '心理' },
  { value: 'glucose', label: '血糖' },
  { value: 'tcm', label: '中医' },
  { value: 'cardiac', label: '心脏' },
  { value: 'metabolism', label: '代谢' },
  { value: 'behavior', label: '行为' },
  { value: 'general', label: '综合' },
]

async function loadDocuments() {
  docLoading.value = true
  try {
    const filters: any = {}
    if (docFilters.keyword) filters.keyword = docFilters.keyword
    if (docFilters.status) filters.status = docFilters.status
    if (docFilters.domain) filters.domain = docFilters.domain
    const res = await expertContentAPI.listDocuments(tenantId, filters)
    if (res.data?.success) documents.value = res.data.data
  } catch (e) {
    console.error(e)
  } finally {
    docLoading.value = false
  }
}

function statusColor(s: string) {
  const map: Record<string, string> = { draft: 'default', processing: 'blue', ready: 'green', error: 'red' }
  return map[s] || 'default'
}

function statusLabel(s: string) {
  const map: Record<string, string> = { draft: '草稿', processing: '处理中', ready: '已发布', error: '错误' }
  return map[s] || s
}

function domainLabel(d: string) {
  if (!d) return '-'
  const opt = domainOptions.find(o => o.value === d)
  return opt ? opt.label : d
}

function formatDate(d: string) {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('zh-CN')
}

// ========== 文档编辑 Modal ==========
const editModalVisible = ref(false)
const isCreate = ref(true)
const saving = ref(false)
const editingDocId = ref<number | null>(null)
const editForm = reactive({
  title: '',
  author: '',
  domain_id: '' as string,
  priority: 5,
  raw_content: '',
  evidence_tier: undefined as string | undefined,
  content_type: undefined as string | undefined,
  published_date: null as Dayjs | null,
  expires_at: null as Dayjs | null,
})

function openCreateModal() {
  isCreate.value = true
  editingDocId.value = null
  editForm.title = ''
  editForm.author = ''
  editForm.domain_id = ''
  editForm.priority = 5
  editForm.raw_content = ''
  editForm.evidence_tier = undefined
  editForm.content_type = undefined
  editForm.published_date = null
  editForm.expires_at = null
  editModalVisible.value = true
}

async function openEditModal(record: any) {
  isCreate.value = false
  editingDocId.value = record.id
  try {
    const res = await expertContentAPI.getDocument(tenantId, record.id)
    if (res.data?.success) {
      const d = res.data.data
      editForm.title = d.title
      editForm.author = d.author || ''
      editForm.domain_id = d.domain_id || ''
      editForm.priority = d.priority || 5
      editForm.raw_content = d.raw_content || ''
      editForm.evidence_tier = d.evidence_tier || undefined
      editForm.content_type = d.content_type || undefined
      editForm.published_date = d.published_date ? dayjs(d.published_date) : null
      editForm.expires_at = d.expires_at ? dayjs(d.expires_at) : null
    }
  } catch (e) {
    message.error('加载文档失败')
    return
  }
  editModalVisible.value = true
}

async function onSaveDocument() {
  if (!editForm.title.trim()) {
    message.warning('请输入标题')
    return
  }
  saving.value = true
  try {
    const payload: any = {
      title: editForm.title,
      raw_content: editForm.raw_content,
      author: editForm.author,
      domain_id: editForm.domain_id,
      priority: editForm.priority,
    }
    if (editForm.evidence_tier) payload.evidence_tier = editForm.evidence_tier
    if (editForm.content_type) payload.content_type = editForm.content_type
    if (editForm.published_date) payload.published_date = editForm.published_date.toISOString()
    if (editForm.expires_at) payload.expires_at = editForm.expires_at.toISOString()

    if (isCreate.value) {
      const res = await expertContentAPI.createDocument(tenantId, payload)
      if (res.data?.success) {
        message.success('文档已创建')
        editModalVisible.value = false
        loadDocuments()
      }
    } else {
      const res = await expertContentAPI.updateDocument(tenantId, editingDocId.value!, payload)
      if (res.data?.success) {
        message.success('文档已更新')
        editModalVisible.value = false
        loadDocuments()
      }
    }
  } catch (e) {
    // error handled by interceptor
  } finally {
    saving.value = false
  }
}

// ========== 发布 / 撤回 / 删除 ==========
const publishingId = ref<number | null>(null)

async function onPublish(record: any) {
  publishingId.value = record.id
  try {
    const res = await expertContentAPI.publishDocument(tenantId, record.id)
    if (res.data?.success) {
      message.success(res.data.message || '发布成功')
      loadDocuments()
    }
  } catch (e) {
    // error handled by interceptor
  } finally {
    publishingId.value = null
  }
}

async function onUnpublish(record: any) {
  try {
    const res = await expertContentAPI.unpublishDocument(tenantId, record.id)
    if (res.data?.success) {
      message.success('已撤回')
      loadDocuments()
    }
  } catch (e) {
    // error handled by interceptor
  }
}

async function onDelete(record: any) {
  try {
    const res = await expertContentAPI.deleteDocument(tenantId, record.id)
    if (res.data?.success) {
      message.success('已删除')
      loadDocuments()
    }
  } catch (e) {
    // error handled by interceptor
  }
}

// ========== 挑战活动 ==========
const challenges = ref<any[]>([])
const challengeLoading = ref(false)

// challengeColumns removed — replaced by ListCard layout

async function loadChallenges() {
  challengeLoading.value = true
  try {
    const res = await expertContentAPI.listChallenges(tenantId)
    if (res.data?.success) challenges.value = res.data.data
  } catch (e) {
    console.error(e)
  } finally {
    challengeLoading.value = false
  }
}

function challengeStatusColor(s: string) {
  const map: Record<string, string> = { draft: 'default', pending_review: 'orange', approved: 'green', active: 'blue', archived: 'default' }
  return map[s] || 'default'
}

function goToChallenge(id: number) {
  router.push({ name: 'ChallengeManagement' })
}

function goBack() {
  router.push({ name: 'ExpertDashboard', params: { tenantId } })
}

// ========== 初始化 ==========
watch(activeTab, (tab) => {
  if (tab === 'challenges' && challenges.value.length === 0) {
    loadChallenges()
  }
})

onMounted(() => {
  loadDocuments()
})
</script>

<style scoped>
.content-studio {
  padding: 24px;
}

.cs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.cs-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.filter-bar {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 16px;
}

.list-card-container { display: flex; flex-direction: column; gap: 10px; }
</style>
