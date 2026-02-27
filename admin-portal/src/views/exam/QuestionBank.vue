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
      <a-col :xs="24" :sm="12" :lg="6">
        <a-card size="small">
          <a-statistic title="题目总数" :value="stats.total" />
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <a-card size="small">
          <a-statistic title="本月新增" :value="stats.monthNew" value-style="color: #3f8600" />
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <a-card size="small">
          <a-statistic title="平均使用次数" :value="stats.avgUse" :precision="1" />
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <a-card size="small">
          <a-statistic title="平均正确率" :value="stats.avgCorrectRate" :precision="1" suffix="%" />
        </a-card>
      </a-col>
    </a-row>

    <a-card>
      <!-- Filters -->
      <a-row :gutter="16" style="margin-bottom: 16px">
        <a-col :span="4">
          <a-select v-model:value="filters.question_type" placeholder="题目类型" allowClear style="width: 100%" @change="handleSearch">
            <a-select-option value="single">单选题</a-select-option>
            <a-select-option value="multiple">多选题</a-select-option>
            <a-select-option value="truefalse">判断题</a-select-option>
            <a-select-option value="short_answer">简答题</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filters.domain" placeholder="领域" allowClear style="width: 100%" @change="handleSearch">
            <a-select-option value="行为健康">行为健康</a-select-option>
            <a-select-option value="营养学">营养学</a-select-option>
            <a-select-option value="运动科学">运动科学</a-select-option>
            <a-select-option value="心理学">心理学</a-select-option>
            <a-select-option value="慢病管理">慢病管理</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filters.difficulty" placeholder="难度" allowClear style="width: 100%" @change="handleSearch">
            <a-select-option value="easy">简单</a-select-option>
            <a-select-option value="medium">中等</a-select-option>
            <a-select-option value="hard">困难</a-select-option>
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

      <!-- 题目列表 -->
      <div class="list-card-container">
        <a-empty v-if="filteredQuestions.length === 0" description="暂无题目" />
        <ListCard v-for="record in filteredQuestions" :key="record.question_id" @click="showPreview(record)">
          <template #avatar>
            <a-checkbox
              :checked="selectedRowKeys.includes(record.question_id)"
              @change="(e: any) => toggleQuestionSelect(record.question_id, e.target.checked)"
              @click.stop
            />
          </template>
          <template #title>
            <span class="question-content">{{ record.content.substring(0, 60) }}{{ record.content.length > 60 ? '...' : '' }}</span>
          </template>
          <template #subtitle>
            <a-tag :color="typeColors[record.question_type]" size="small">{{ typeLabels[record.question_type] }}</a-tag>
            <a-tag :color="difficultyColors[record.difficulty]" size="small">{{ difficultyLabels[record.difficulty] || record.difficulty }}</a-tag>
            <span v-if="record.domain" style="color: #666; font-size: 12px">{{ record.domain }}</span>
          </template>
          <template #meta>
            <a-tag v-for="tag in (record.tags || []).slice(0, 3)" :key="tag" size="small">{{ tag }}</a-tag>
            <span v-if="(record.tags || []).length > 3" style="color: #999">+{{ record.tags.length - 3 }}</span>
            <span style="color: #999">使用 {{ record.use_count || 0 }} 次</span>
          </template>
          <template #actions>
            <a-button type="link" size="small" @click.stop="showPreview(record)">预览</a-button>
            <a-button type="link" size="small" @click.stop="editQuestion(record)">编辑</a-button>
            <a-popconfirm title="确定删除？" @confirm="deleteQuestion(record)">
              <a-button type="link" size="small" danger @click.stop>删除</a-button>
            </a-popconfirm>
          </template>
        </ListCard>
      </div>

      <!-- Pagination -->
      <div style="margin-top: 16px; text-align: right">
        <a-pagination
          v-model:current="pagination.current"
          v-model:pageSize="pagination.pageSize"
          :total="questionStore.total"
          show-size-changer
          show-quick-jumper
          :show-total="(total: number) => `共 ${total} 条`"
          @change="handlePageChange"
          @showSizeChange="handlePageChange"
        />
      </div>
    </a-card>

    <!-- Preview Modal -->
    <a-modal v-model:open="previewVisible" title="题目预览" :footer="null" width="640px">
      <div v-if="previewQuestion" class="preview-content">
        <a-descriptions :column="2" bordered size="small">
          <a-descriptions-item label="题目类型">
            <a-tag :color="typeColors[previewQuestion.question_type]">{{ typeLabels[previewQuestion.question_type] }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="领域">{{ previewQuestion.domain || '--' }}</a-descriptions-item>
          <a-descriptions-item label="难度" :span="2">
            <a-tag :color="difficultyColors[previewQuestion.difficulty]">{{ difficultyLabels[previewQuestion.difficulty] || previewQuestion.difficulty }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="题目内容" :span="2">
            <p style="white-space: pre-wrap; margin: 0">{{ previewQuestion.content }}</p>
          </a-descriptions-item>
          <a-descriptions-item v-if="previewQuestion.options" label="选项" :span="2">
            <div v-for="(opt, i) in previewQuestion.options" :key="opt.key || i" style="padding: 2px 0">
              <a-tag :color="(previewQuestion.answer || []).includes(opt.key) ? 'green' : 'default'" size="small">
                {{ opt.key }}
              </a-tag>
              {{ opt.text }}
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
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, UploadOutlined, DownOutlined, InboxOutlined } from '@ant-design/icons-vue'
import { useQuestionStore } from '../../stores/question'
import { questionApi } from '../../api/question'
import ListCard from '@/components/core/ListCard.vue'
import * as XLSX from 'xlsx'

const router = useRouter()
const questionStore = useQuestionStore()
const loading = ref(false)

const filters = reactive({
  question_type: undefined as string | undefined,
  domain: undefined as string | undefined,
  difficulty: undefined as string | undefined,
  tag: undefined as string | undefined,
  keyword: ''
})

const pagination = reactive({
  current: 1,
  pageSize: 20,
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

const difficultyLabels: Record<string, string> = {
  easy: '简单',
  medium: '中等',
  hard: '困难'
}

const difficultyColors: Record<string, string> = {
  easy: 'green',
  medium: 'blue',
  hard: 'red'
}

const allTags = ['行为健康基础', 'TTM模型', '动机访谈', '认知行为', '压力管理', '营养学', '运动科学', '睡眠医学', '慢病管理', '心理学基础']

const importPreviewColumns = [
  { title: '内容', dataIndex: 'content', ellipsis: true },
  { title: '类型', dataIndex: 'question_type', width: 80 },
  { title: '领域', dataIndex: 'domain', width: 80 },
]

const questions = computed(() => questionStore.questions)

const loadQuestions = async () => {
  loading.value = true
  try {
    const params: Record<string, any> = {
      skip: (pagination.current - 1) * pagination.pageSize,
      limit: pagination.pageSize,
    }
    if (filters.question_type) params.question_type = filters.question_type
    if (filters.domain) params.domain = filters.domain
    if (filters.difficulty) params.difficulty = filters.difficulty
    if (filters.keyword) params.keyword = filters.keyword
    await questionStore.fetchQuestions(params)
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
  total: questionStore.total,
  monthNew: questions.value.filter(q => {
    const d = new Date(q.created_at || '')
    const now = new Date()
    return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()
  }).length,
  avgUse: questions.value.reduce((s: number, q: any) => s + (q.use_count || 0), 0) / (questions.value.length || 1),
  avgCorrectRate: questions.value.length
    ? questions.value.reduce((s: number, q: any) => s + (q.correct_rate || 0), 0) / questions.value.length
    : 0,
}))

// Client-side: only filter by tag (server handles question_type/domain/difficulty/keyword)
const filteredQuestions = computed(() => {
  if (!filters.tag) return questions.value
  return questions.value.filter((q: any) => (q.tags || []).includes(filters.tag))
})

function toggleQuestionSelect(id: string, checked: boolean) {
  if (checked) {
    if (!selectedRowKeys.value.includes(id)) selectedRowKeys.value.push(id)
  } else {
    selectedRowKeys.value = selectedRowKeys.value.filter(k => k !== id)
  }
}

const handleSearch = () => {
  pagination.current = 1
  loadQuestions()
}

const handlePageChange = (page: number, pageSize: number) => {
  pagination.current = page
  pagination.pageSize = pageSize
  loadQuestions()
}

const resetFilters = () => {
  filters.question_type = undefined
  filters.domain = undefined
  filters.difficulty = undefined
  filters.tag = undefined
  filters.keyword = ''
  pagination.current = 1
  loadQuestions()
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
    // Fix 7: use correct field names
    const selected = questions.value.filter((q: any) => selectedRowKeys.value.includes(q.question_id))
    const csv = ['题目内容,类型,领域,难度,使用次数']
    selected.forEach((q: any) => csv.push(`"${q.content}",${q.question_type},${q.domain || ''},${q.difficulty},${q.use_count}`))
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

// Fix 6: Parse imported Excel/CSV file
const headerMap: Record<string, string> = {
  '题目内容': 'content', '内容': 'content',
  '类型': 'question_type', '题目类型': 'question_type',
  '领域': 'domain',
  '难度': 'difficulty',
  '选项': '_options_raw',
  '答案': '_answer_raw',
  '解析': 'explanation',
  '标签': '_tags_raw',
}

const difficultyMap: Record<string, string> = {
  '简单': 'easy', '容易': 'easy',
  '中等': 'medium', '一般': 'medium',
  '困难': 'hard', '难': 'hard',
}

const typeMap: Record<string, string> = {
  '单选': 'single', '单选题': 'single',
  '多选': 'multiple', '多选题': 'multiple',
  '判断': 'truefalse', '判断题': 'truefalse',
  '简答': 'short_answer', '简答题': 'short_answer',
}

function parseOptions(raw: string): { key: string; text: string }[] {
  if (!raw) return []
  // Format: "A.选项1;B.选项2" or "A、选项1;B、选项2"
  const parts = raw.split(/[;；]/).map(s => s.trim()).filter(Boolean)
  return parts.map(part => {
    const m = part.match(/^([A-Z])[.、．]\s*(.+)/)
    if (m) return { key: m[1], text: m[2] }
    // Fallback: auto-assign key
    const idx = parts.indexOf(part)
    return { key: String.fromCharCode(65 + idx), text: part }
  })
}

function parseAnswer(raw: string): string[] {
  if (!raw) return []
  // Format: "A,C" or "A、C" or "A;C" or just "A"
  return raw.split(/[,，;；、\s]+/).map(s => s.trim().toUpperCase()).filter(Boolean)
}

watch(importFileList, async (list) => {
  if (!list || list.length === 0) {
    importPreview.value = []
    return
  }
  const file = list[0].originFileObj || list[0]
  try {
    const data = await file.arrayBuffer()
    const workbook = XLSX.read(data, { type: 'array' })
    const sheet = workbook.Sheets[workbook.SheetNames[0]]
    const rows: Record<string, any>[] = XLSX.utils.sheet_to_json(sheet, { defval: '' })

    const parsed = rows.slice(0, 100).map(row => {
      const mapped: Record<string, any> = {}
      for (const [header, value] of Object.entries(row)) {
        const key = headerMap[header.trim()] || header.trim()
        mapped[key] = String(value).trim()
      }
      // Transform fields
      if (mapped.question_type) mapped.question_type = typeMap[mapped.question_type] || mapped.question_type
      if (mapped.difficulty) mapped.difficulty = difficultyMap[mapped.difficulty] || mapped.difficulty
      if (mapped._options_raw) {
        mapped.options = parseOptions(mapped._options_raw)
        delete mapped._options_raw
      }
      if (mapped._answer_raw) {
        mapped.answer = parseAnswer(mapped._answer_raw)
        delete mapped._answer_raw
      }
      if (mapped._tags_raw) {
        mapped.tags = mapped._tags_raw.split(/[,，;；、]/).map((s: string) => s.trim()).filter(Boolean)
        delete mapped._tags_raw
      }
      return mapped
    }).filter(r => r.content)

    importPreview.value = parsed
  } catch (e) {
    console.error('文件解析失败:', e)
    message.error('文件解析失败，请检查格式')
    importPreview.value = []
  }
})

const handleImport = async () => {
  if (importPreview.value.length === 0) {
    message.warning('没有可导入的题目')
    return
  }
  importing.value = true
  try {
    const res = await questionApi.bulkImport(importPreview.value)
    const body = res.data as any
    const imported = body?.imported || body?.data?.imported || importPreview.value.length
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

.list-card-container { display: flex; flex-direction: column; gap: 10px; }

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
