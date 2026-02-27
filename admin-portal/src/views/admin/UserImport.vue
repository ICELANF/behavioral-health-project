<template>
  <div class="user-import">
    <a-page-header title="批量用户导入" sub-title="通过 CSV 文件批量导入或更新用户" @back="$router.back()" />

    <a-card title="上传文件" class="import-card">
      <a-space direction="vertical" :size="16" style="width: 100%">
        <a-alert
          message="导入规则"
          type="info"
          show-icon
        >
          <template #description>
            <ul style="margin: 0; padding-left: 20px">
              <li>CSV 必须包含 <code>phone</code> 列 (手机号, 必填)</li>
              <li>可选列: <code>name</code> (姓名), <code>role</code> (角色: observer/grower/sharer/coach), <code>wx_openid</code> (微信 OpenID)</li>
              <li>手机号已存在的用户会更新信息, 不会重复创建</li>
              <li>微信 OpenID 已存在的用户也会自动关联</li>
              <li>新用户会生成随机密码, 可通过短信验证码登录</li>
            </ul>
          </template>
        </a-alert>

        <a-space>
          <a-button @click="downloadTemplate">
            <template #icon><DownloadOutlined /></template>
            下载导入模板
          </a-button>
        </a-space>

        <a-upload-dragger
          v-model:fileList="fileList"
          :before-upload="beforeUpload"
          :max-count="1"
          accept=".csv"
          @remove="handleRemove"
        >
          <p class="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p class="ant-upload-text">点击或拖拽 CSV 文件到此处</p>
          <p class="ant-upload-hint">仅支持 CSV 格式, 编码 UTF-8 或 GBK</p>
        </a-upload-dragger>

        <!-- 预览 -->
        <template v-if="previewData.length > 0">
          <a-divider>数据预览 (前 10 行)</a-divider>
          <a-table
            :columns="previewColumns"
            :data-source="previewData"
            :pagination="false"
            size="small"
            bordered
          />
        </template>

        <a-button
          type="primary"
          size="large"
          :loading="importing"
          :disabled="!fileList.length"
          @click="handleImport"
        >
          确认导入
        </a-button>
      </a-space>
    </a-card>

    <!-- 导入结果 -->
    <a-card v-if="importResult" title="导入结果" class="result-card">
      <a-result
        :status="importResult.errors.length === 0 ? 'success' : 'warning'"
        :title="resultTitle"
      >
        <template #extra>
          <a-descriptions bordered :column="1" size="small">
            <a-descriptions-item label="成功创建">{{ importResult.created }} 人</a-descriptions-item>
            <a-descriptions-item label="成功更新">{{ importResult.updated }} 人</a-descriptions-item>
            <a-descriptions-item label="处理总数">{{ importResult.total_processed }} 条</a-descriptions-item>
            <a-descriptions-item v-if="importResult.errors.length" label="失败条数">
              <a-tag color="red">{{ importResult.errors.length }}</a-tag>
            </a-descriptions-item>
          </a-descriptions>
        </template>
      </a-result>

      <!-- 错误详情 -->
      <template v-if="importResult.errors.length > 0">
        <a-divider>错误详情</a-divider>
        <a-table
          :columns="errorColumns"
          :data-source="importResult.errors"
          :pagination="{ pageSize: 10 }"
          size="small"
          row-key="row"
        />
      </template>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { DownloadOutlined, InboxOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import axios from 'axios'

const token = localStorage.getItem('admin_token')
const api = axios.create({
  baseURL: '/api',
  headers: { Authorization: `Bearer ${token}` },
})

const fileList = ref<any[]>([])
const importing = ref(false)
const importResult = ref<any>(null)
const previewData = ref<any[]>([])

const previewColumns = [
  { title: '行号', dataIndex: 'row', width: 60 },
  { title: '手机号', dataIndex: 'phone' },
  { title: '姓名', dataIndex: 'name' },
  { title: '角色', dataIndex: 'role' },
  { title: '微信 OpenID', dataIndex: 'wx_openid' },
]

const errorColumns = [
  { title: '行号', dataIndex: 'row', width: 60 },
  { title: '手机号', dataIndex: 'phone' },
  { title: '错误原因', dataIndex: 'error' },
]

const resultTitle = computed(() => {
  if (!importResult.value) return ''
  const { created, updated, errors } = importResult.value
  if (errors.length === 0) return `导入完成: 创建 ${created} 人, 更新 ${updated} 人`
  return `部分导入: 创建 ${created} 人, 更新 ${updated} 人, ${errors.length} 条失败`
})

function beforeUpload(file: File) {
  // 解析 CSV 预览
  const reader = new FileReader()
  reader.onload = (e) => {
    const text = e.target?.result as string
    const lines = text.split('\n').filter(l => l.trim())
    if (lines.length < 2) {
      message.error('CSV 文件至少需要表头 + 1 行数据')
      return
    }
    const headers = lines[0].split(',').map(h => h.trim().replace(/^\uFEFF/, ''))
    const preview = lines.slice(1, 11).map((line, i) => {
      const cols = line.split(',').map(c => c.trim())
      const row: any = { row: i + 2, key: i }
      headers.forEach((h, j) => { row[h] = cols[j] || '' })
      return row
    })
    previewData.value = preview
  }
  reader.readAsText(file)

  fileList.value = [file]
  return false // prevent auto upload
}

function handleRemove() {
  fileList.value = []
  previewData.value = []
}

async function downloadTemplate() {
  try {
    const res = await api.get('/v1/admin/users/import-template', { responseType: 'blob' })
    const url = URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = 'user_import_template.csv'
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    message.error('下载模板失败')
  }
}

async function handleImport() {
  if (!fileList.value.length) return
  importing.value = true
  importResult.value = null

  try {
    const formData = new FormData()
    formData.append('file', fileList.value[0])

    const res = await api.post('/v1/admin/users/batch-import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    importResult.value = res.data
    message.success(`导入完成: 创建 ${res.data.created}, 更新 ${res.data.updated}`)
    fileList.value = []
    previewData.value = []
  } catch (e: any) {
    message.error(e.response?.data?.detail || '导入失败')
  } finally {
    importing.value = false
  }
}
</script>

<style scoped>
.user-import {
  padding: 24px;
}
.import-card {
  margin-bottom: 24px;
}
.result-card {
  margin-bottom: 24px;
}
</style>
