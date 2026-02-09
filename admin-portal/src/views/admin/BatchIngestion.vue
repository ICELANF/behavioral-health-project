<!--
  批量知识库导入 — 拖拽上传 + 作业历史
  路由: /admin/batch-ingestion
-->
<template>
  <div class="batch-ingestion">
    <a-page-header title="批量知识导入" @back="$router.back()" />

    <!-- 上传区域 -->
    <a-card title="上传文件" :bordered="false" style="margin-bottom: 16px">
      <a-form layout="vertical" :model="uploadForm">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="知识范围">
              <a-select v-model:value="uploadForm.scope" placeholder="选择范围">
                <a-select-option value="platform">平台级</a-select-option>
                <a-select-option value="domain">领域级</a-select-option>
                <a-select-option value="tenant">租户级</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="领域 ID">
              <a-input
                v-model:value="uploadForm.domain_id"
                placeholder="如 metabolic, sleep, emotion"
                :disabled="uploadForm.scope === 'platform'"
                allowClear
              />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="租户 ID">
              <a-input
                v-model:value="uploadForm.tenant_id"
                placeholder="如 dr-chen-endo"
                :disabled="uploadForm.scope !== 'tenant'"
                allowClear
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="选择文件">
          <a-upload-dragger
            v-model:fileList="fileList"
            :multiple="true"
            :before-upload="beforeUpload"
            :accept="acceptTypes"
            :showUploadList="true"
          >
            <p class="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p class="ant-upload-hint">
              支持 PDF、DOCX、TXT、Markdown、ZIP、7Z、RAR 格式，可批量上传
            </p>
          </a-upload-dragger>
        </a-form-item>

        <a-form-item>
          <a-button
            type="primary"
            :loading="uploading"
            :disabled="fileList.length === 0"
            @click="handleUpload"
          >
            <template #icon><CloudUploadOutlined /></template>
            开始导入
          </a-button>
          <a-button style="margin-left: 8px" @click="resetForm">重置</a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 作业历史 -->
    <a-card title="导入作业历史" :bordered="false">
      <template #extra>
        <a-button size="small" @click="loadJobs" :loading="jobsLoading">
          <template #icon><ReloadOutlined /></template>
          刷新
        </a-button>
      </template>

      <a-table
        :dataSource="jobs"
        :columns="jobColumns"
        :loading="jobsLoading"
        :pagination="{ pageSize: 10, showSizeChanger: true, showTotal: (t: number) => `共 ${t} 条` }"
        rowKey="id"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="jobStatusColor(record.status)">{{ jobStatusLabel(record.status) }}</a-tag>
          </template>
          <template v-if="column.key === 'progress'">
            <a-progress
              :percent="record.progress ?? 0"
              :status="record.status === 'failed' ? 'exception' : record.status === 'completed' ? 'success' : 'active'"
              size="small"
              style="width: 120px"
            />
          </template>
          <template v-if="column.key === 'scope'">
            <a-tag>{{ scopeLabel(record.scope) }}</a-tag>
          </template>
          <template v-if="column.key === 'file_count'">
            {{ record.file_count ?? 0 }} 个文件
          </template>
          <template v-if="column.key === 'created_at'">
            {{ formatDate(record.created_at) }}
          </template>
          <template v-if="column.key === 'error_message'">
            <a-tooltip v-if="record.error_message" :title="record.error_message">
              <span class="error-text">{{ truncate(record.error_message, 40) }}</span>
            </a-tooltip>
            <span v-else style="color: #999">--</span>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import type { UploadFile } from 'ant-design-vue'
import request from '@/api/request'
import {
  InboxOutlined,
  CloudUploadOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue'

// ============ 上传表单 ============

const acceptTypes = '.pdf,.docx,.txt,.md,.zip,.7z,.rar'

const uploadForm = reactive({
  scope: 'platform' as 'platform' | 'domain' | 'tenant',
  domain_id: '',
  tenant_id: '',
})

const fileList = ref<UploadFile[]>([])
const uploading = ref(false)

/** 阻止自动上传，手动管理 */
const beforeUpload = (_file: UploadFile) => {
  return false
}

const handleUpload = async () => {
  if (fileList.value.length === 0) {
    message.warning('请先选择文件')
    return
  }
  if (uploadForm.scope === 'domain' && !uploadForm.domain_id) {
    message.warning('领域级导入请填写领域 ID')
    return
  }
  if (uploadForm.scope === 'tenant' && !uploadForm.tenant_id) {
    message.warning('租户级导入请填写租户 ID')
    return
  }

  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('scope', uploadForm.scope)
    if (uploadForm.domain_id) formData.append('domain_id', uploadForm.domain_id)
    if (uploadForm.tenant_id) formData.append('tenant_id', uploadForm.tenant_id)
    fileList.value.forEach((f) => {
      if (f.originFileObj) {
        formData.append('files', f.originFileObj as File)
      }
    })

    await request.post('v1/knowledge/batch-upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    })
    message.success('导入任务已提交')
    resetForm()
    await loadJobs()
  } catch (e: any) {
    console.error('上传失败:', e)
    message.error(e.response?.data?.detail || '上传失败，请重试')
  } finally {
    uploading.value = false
  }
}

const resetForm = () => {
  fileList.value = []
  uploadForm.scope = 'platform'
  uploadForm.domain_id = ''
  uploadForm.tenant_id = ''
}

// ============ 作业历史 ============

interface BatchJob {
  id: number
  status: string
  progress: number
  scope: string
  domain_id?: string
  tenant_id?: string
  file_count: number
  created_at: string
  completed_at?: string
  error_message?: string
}

const jobs = ref<BatchJob[]>([])
const jobsLoading = ref(false)

const jobColumns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '状态', key: 'status', width: 100 },
  { title: '进度', key: 'progress', width: 160 },
  { title: '范围', key: 'scope', width: 90 },
  { title: '文件数', key: 'file_count', width: 100 },
  { title: '创建时间', key: 'created_at', width: 170 },
  { title: '错误信息', key: 'error_message', ellipsis: true },
]

const loadJobs = async () => {
  jobsLoading.value = true
  try {
    const { data } = await request.get('v1/knowledge/batch-jobs')
    jobs.value = data.jobs ?? data ?? []
  } catch (e: any) {
    console.error('加载作业列表失败:', e)
  } finally {
    jobsLoading.value = false
  }
}

// ============ 工具函数 ============

const jobStatusColor = (s: string): string => {
  const map: Record<string, string> = {
    pending: 'default',
    processing: 'processing',
    completed: 'success',
    failed: 'error',
  }
  return map[s] || 'default'
}

const jobStatusLabel = (s: string): string => {
  const map: Record<string, string> = {
    pending: '排队中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
  }
  return map[s] || s
}

const scopeLabel = (s: string): string => {
  const map: Record<string, string> = {
    platform: '平台级',
    domain: '领域级',
    tenant: '租户级',
  }
  return map[s] || s
}

const formatDate = (d: string): string => {
  if (!d) return '--'
  return new Date(d).toLocaleString('zh-CN')
}

const truncate = (str: string, max: number): string => {
  if (!str) return ''
  return str.length > max ? str.slice(0, max) + '...' : str
}

// ============ 生命周期 ============

onMounted(() => {
  loadJobs()
})
</script>

<style scoped>
.batch-ingestion {
  padding: 0;
}

.error-text {
  color: #ff4d4f;
  font-size: 12px;
}

:deep(.ant-upload-dragger) {
  padding: 20px;
}

:deep(.ant-page-header) {
  padding: 0 0 16px 0;
}
</style>
