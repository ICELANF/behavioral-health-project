<template>
  <div class="question-bank">
    <div class="page-header">
      <h2>题库管理</h2>
      <div class="header-actions">
        <a-button @click="showImportModal = true">
          <template #icon><UploadOutlined /></template>
          批量导入
        </a-button>
        <a-dropdown v-if="selectedRowKeys.length > 0">
          <a-button>
            批量操作 ({{ selectedRowKeys.length }})
            <DownOutlined />
          </a-button>
          <template #overlay>
            <a-menu @click="handleBatchAction">
              <a-menu-item key="export">导出选中</a-menu-item>
              <a-menu-item key="move">移动分类</a-menu-item>
              <a-menu-item key="delete" danger>批量删除</a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
        <a-button type="primary" @click="$router.push('/question/create')">
          <template #icon><PlusOutlined /></template>
          创建题目
        </a-button>
      </div>
    </div>

    <!-- Statistics panel -->
    <a-row :gutter="16" style="margin-bottom: 16px">
      <a-col :span="6">
        <a-card size="small">
          <a-statistic title="题目总数" :value="stats.total" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card size="small">
          <a-statistic title="本月新增" :value="stats.monthNew" value-style="color: #3f8600" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card size="small">
          <a-statistic title="平均使用次数" :value="stats.avgUse" :precision="1" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card size="small">
          <a-statistic title="被引用考试数" :value="stats.examCount" />
        </a-card>
      </a-col>
    </a-row>

    <a-card>
      <!-- Filters -->
      <a-row :gutter="16" style="margin-bottom: 16px">
        <a-col :span="4">
          <a-select v-model:value="filters.type" placeholder="题目类型" allowClear style="width: 100%">
            <a-select-option value="single">单选题</a-select-option>
            <a-select-option value="multiple">多选题</a-select-option>
            <a-select-option value="truefalse">判断题</a-select-option>
            <a-select-option value="short_answer">简答题</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filters.level" placeholder="认证等级" allowClear style="width: 100%">
            <a-select-option value="L0">L0</a-select-option>
            <a-select-option value="L1">L1</a-select-option>
            <a-select-option value="L2">L2</a-select-option>
            <a-select-option value="L3">L3</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filters.difficulty" placeholder="难度" allowClear style="width: 100%">
            <a-select-option :value="1">简单</a-select-option>
            <a-select-option :value="2">较易</a-select-option>
            <a-select-option :value="3">中等</a-select-option>
            <a-select-option :value="4">较难</a-select-option>
            <a-select-option :value="5">困难</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filters.tag" placeholder="知识点标签" allowClear style="width: 100%">
            <a-select-option v-for="tag in allTags" :key="tag" :value="tag">{{ tag }}</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="5">
          <a-input-search v-model:value="filters.keyword" placeholder="搜索题目" @search="handleSearch" />
        </a-col>
        <a-col :span="3">
          <a-button @click="resetFilters">重置</a-button>
        </a-col>
      </a-row>

      <!-- Table -->
      <a-table
        :dataSource="filteredQuestions"
        :columns="columns"
        rowKey="question_id"
        :row-selection="{ selectedRowKeys, onChange: onSelectChange }"
        :pagination="{ pageSize: 10, showTotal: (total) => `共 ${total} 题` }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'content'">
            <a class="question-content" @click="showPreview(record)">
              {{ record.content.substring(0, 50) }}{{ record.content.length > 50 ? '...' : '' }}
            </a>
          </template>
          <template v-if="column.key === 'type'">
            <a-tag :color="typeColors[record.type]">{{ typeLabels[record.type] }}</a-tag>
          </template>
          <template v-if="column.key === 'tags'">
            <a-tag v-for="tag in (record.tags || [])" :key="tag" size="small" style="margin-bottom: 2px">{{ tag }}</a-tag>
          </template>
          <template v-if="column.key === 'difficulty'">
            <a-rate :value="record.difficulty" disabled :count="5" style="font-size: 12px" />
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a @click="showPreview(record)">预览</a>
              <a @click="editQuestion(record)">编辑</a>
              <a-popconfirm title="确定删除？" @confirm="deleteQuestion(record)">
                <a style="color: #ff4d4f">删除</a>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- Preview Modal -->
    <a-modal v-model:open="previewVisible" title="题目预览" :footer="null" width="640px">
      <div v-if="previewQuestion" class="preview-content">
        <a-descriptions :column="2" bordered size="small">
          <a-descriptions-item label="题目类型">
            <a-tag :color="typeColors[previewQuestion.type]">{{ typeLabels[previewQuestion.type] }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="认证等级">{{ previewQuestion.level }}</a-descriptions-item>
          <a-descriptions-item label="难度" :span="2">
            <a-rate :value="previewQuestion.difficulty" disabled :count="5" />
          </a-descriptions-item>
          <a-descriptions-item label="题目内容" :span="2">
            <p style="white-space: pre-wrap; margin: 0">{{ previewQuestion.content }}</p>
          </a-descriptions-item>
          <a-descriptions-item v-if="previewQuestion.options" label="选项" :span="2">
            <div v-for="(opt, i) in previewQuestion.options" :key="i" style="padding: 2px 0">
              <a-tag :color="(previewQuestion.answer || []).includes(i) ? 'green' : 'default'" size="small">
                {{ String.fromCharCode(65 + i) }}
              </a-tag>
              {{ opt }}
            </div>
          </a-descriptions-item>
          <a-descriptions-item v-if="previewQuestion.explanation" label="解析" :span="2">
            {{ previewQuestion.explanation }}
          </a-descriptions-item>
          <a-descriptions-item label="知识点标签" :span="2">
            <a-tag v-for="tag in (previewQuestion.tags || [])" :key="tag">{{ tag }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="使用次数">{{ previewQuestion.use_count }}</a-descriptions-item>
          <a-descriptions-item label="正确率">{{ previewQuestion.correct_rate || '--' }}%</a-descriptions-item>
        </a-descriptions>
      </div>
    </a-modal>

    <!-- Import Modal -->
    <a-modal v-model:open="showImportModal" title="批量导入题目" @ok="handleImport" okText="导入" :confirmLoading="importing">
      <a-alert message="支持 Excel (.xlsx) 和 CSV 格式文件，请确保包含以下列：题目内容、类型、等级、难度、选项、答案" type="info" show-icon style="margin-bottom: 16px" />
      <a-upload-dragger
        v-model:fileList="importFileList"
        :before-upload="() => false"
        :maxCount="1"
        accept=".xlsx,.xls,.csv"
      >
        <p class="ant-upload-drag-icon"><InboxOutlined /></p>
        <p class="ant-upload-text">点击或拖拽文件到此区域</p>
        <p class="ant-upload-hint">支持 .xlsx、.xls、.csv 格式</p>
      </a-upload-dragger>
      <div v-if="importPreview.length > 0" style="margin-top: 16px">
        <p>预览（前 {{ importPreview.length }} 条）：</p>
        <a-table :dataSource="importPreview" :columns="importPreviewColumns" size="small" :pagination="false" />
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, UploadOutlined, DownOutlined, InboxOutlined } from '@ant-design/icons-vue'
import { useQuestionStore } from '../../stores/question'
import { questionApi } from '../../api/question'

const router = useRouter()
const questionStore = useQuestionStore()
const loading = ref(false)

const filters = reactive({
  type: undefined as string | undefined,
  level: undefined as string | undefined,
  difficulty: undefined as number | undefined,
  tag: undefined as string | undefined,
  keyword: ''
})

const typeLabels: Record<string, string> = {
  single: '单选题',
  multiple: '多选题',
  truefalse: '判断题',
  short_answer: '简答题'
}

const typeColors: Record<string, string> = {
  single: 'blue',
  multiple: 'green',
  truefalse: 'orange',
  short_answer: 'purple'
}

const allTags = ['行为健康基础', 'TTM模型', '动机访谈', '认知行为', '压力管理', '营养学', '运动科学', '睡眠医学', '慢病管理', '心理学基础']

const columns = [
  { title: '题目内容', key: 'content', width: 260 },
  { title: '类型', key: 'type', width: 80 },
  { title: '等级', dataIndex: 'level', width: 60 },
  { title: '标签', key: 'tags', width: 160 },
  { title: '难度', key: 'difficulty', width: 130 },
  { title: '使用次数', dataIndex: 'use_count', width: 90, sorter: (a: any, b: any) => a.use_count - b.use_count },
  { title: '操作', key: 'action', width: 140 }
]

const importPreviewColumns = [
  { title: '内容', dataIndex: 'content', ellipsis: true },
  { title: '类型', dataIndex: 'type', width: 80 },
  { title: '等级', dataIndex: 'level', width: 60 },
]

const questions = computed(() => questionStore.questions)

const loadQuestions = async () => {
  loading.value = true
  try {
    await questionStore.fetchQuestions({})
  } catch (e) {
    console.error('加载题库失败:', e)
  }
  loading.value = false
}

onMounted(loadQuestions)

const selectedRowKeys = ref<string[]>([])
const previewVisible = ref(false)
const previewQuestion = ref<any>(null)
const showImportModal = ref(false)
const importFileList = ref<any[]>([])
const importPreview = ref<any[]>([])
const importing = ref(false)

const stats = computed(() => ({
  total: questions.value.length,
  monthNew: questions.value.filter(q => {
    const d = new Date(q.created_at || '')
    const now = new Date()
    return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()
  }).length,
  avgUse: questions.value.reduce((s: number, q: any) => s + (q.use_count || 0), 0) / (questions.value.length || 1),
  examCount: questionStore.total || questions.value.length,
}))

const filteredQuestions = computed(() => {
  return questions.value.filter(q => {
    if (filters.type && q.type !== filters.type) return false
    if (filters.level && q.level !== filters.level) return false
    if (filters.difficulty && q.difficulty !== filters.difficulty) return false
    if (filters.tag && !(q.tags || []).includes(filters.tag)) return false
    if (filters.keyword && !q.content.includes(filters.keyword)) return false
    return true
  })
})

const onSelectChange = (keys: string[]) => { selectedRowKeys.value = keys }

const handleSearch = () => { /* computed filteredQuestions handles it */ }

const resetFilters = () => {
  filters.type = undefined
  filters.level = undefined
  filters.difficulty = undefined
  filters.tag = undefined
  filters.keyword = ''
}

const showPreview = (record: any) => {
  previewQuestion.value = record
  previewVisible.value = true
}

const editQuestion = (record: any) => {
  router.push(`/question/edit/${record.question_id}`)
}

const deleteQuestion = async (record: any) => {
  try {
    await questionStore.deleteQuestion(record.question_id)
    message.success('题目已删除')
  } catch (e) {
    console.error('删除题目失败:', e)
    message.error('删除失败')
  }
}

const handleBatchAction = ({ key }: { key: string }) => {
  if (key === 'delete') {
    Modal.confirm({
      title: '确认批量删除',
      content: `确定要删除选中的 ${selectedRowKeys.value.length} 道题目吗？此操作不可撤销。`,
      okType: 'danger',
      async onOk() {
        try {
          await Promise.all(selectedRowKeys.value.map(id => questionStore.deleteQuestion(id)))
          selectedRowKeys.value = []
          message.success('批量删除成功')
        } catch (e) {
          console.error('批量删除失败:', e)
          message.error('部分题目删除失败')
          await loadQuestions()
        }
      }
    })
  } else if (key === 'export') {
    const selected = questions.value.filter((q: any) => selectedRowKeys.value.includes(q.question_id))
    const csv = ['题目内容,类型,等级,难度,使用次数']
    selected.forEach((q: any) => csv.push(`"${q.content}",${q.type},${q.level},${q.difficulty},${q.use_count}`))
    const blob = new Blob(['\uFEFF' + csv.join('\n')], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `question_export_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
    message.success(`已导出 ${selected.length} 道题目`)
  } else if (key === 'move') {
    message.info('移动分类功能即将上线')
  }
}

const handleImport = async () => {
  if (importPreview.value.length === 0) {
    message.warning('没有可导入的题目')
    return
  }
  importing.value = true
  try {
    const res = await questionApi.bulkImport(importPreview.value)
    const imported = res.data?.data?.imported || importPreview.value.length
    showImportModal.value = false
    importFileList.value = []
    importPreview.value = []
    message.success(`成功导入 ${imported} 道题目`)
    await loadQuestions()
  } catch (e) {
    console.error('导入失败:', e)
    message.error('导入失败')
  }
  importing.value = false
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.question-content {
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
  cursor: pointer;
}

.question-content:hover {
  color: #1890ff;
}

.preview-content p {
  margin: 0;
}
</style>
