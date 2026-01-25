<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  Card,
  Table,
  Button,
  Input,
  Select,
  Space,
  Tag,
  message,
  Popconfirm
} from 'ant-design-vue'
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  CopyOutlined
} from '@ant-design/icons-vue'
import type { PromptTemplate } from '@/types'
import { TTM_STAGES, TRIGGER_DOMAINS } from '@/constants'

const router = useRouter()

// 筛选条件
const filters = reactive({
  keyword: '',
  category: undefined as string | undefined,
  ttm_stage: undefined as string | undefined,
  trigger_domain: undefined as string | undefined
})

// 分类选项
const categories = [
  { value: 'greeting', label: '开场问候' },
  { value: 'assessment', label: '评估询问' },
  { value: 'education', label: '健康教育' },
  { value: 'motivation', label: '动机激励' },
  { value: 'goal_setting', label: '目标设定' },
  { value: 'follow_up', label: '随访跟进' },
  { value: 'crisis', label: '危机干预' }
]

// 模拟数据
const mockData: PromptTemplate[] = [
  {
    prompt_id: '1',
    name: '血糖异常问候',
    description: '当检测到血糖异常时的开场白',
    category: 'greeting',
    content: '您好{{name}}，我注意到您最近的血糖读数是{{value}}，这比正常范围稍高一些。我想和您聊聊这个情况，可以吗？',
    variables: ['name', 'value'],
    ttm_stage: 'contemplation',
    trigger_domain: 'glucose',
    is_active: true,
    created_at: '2024-01-15 10:30:00',
    updated_at: '2024-01-15 10:30:00'
  },
  {
    prompt_id: '2',
    name: '运动动机激励',
    description: '鼓励用户开始运动的激励话术',
    category: 'motivation',
    content: '{{name}}，我知道开始运动可能不容易，但每一小步都是进步。您觉得这周可以尝试{{activity}}吗？哪怕只是{{duration}}分钟也很棒！',
    variables: ['name', 'activity', 'duration'],
    ttm_stage: 'preparation',
    trigger_domain: 'exercise',
    is_active: true,
    created_at: '2024-01-14 14:20:00',
    updated_at: '2024-01-14 14:20:00'
  },
  {
    prompt_id: '3',
    name: '饮食评估询问',
    description: '了解用户饮食习惯的评估问题',
    category: 'assessment',
    content: '{{name}}，我想了解一下您的日常饮食。能告诉我您昨天的三餐分别吃了什么吗？包括任何零食或饮料。',
    variables: ['name'],
    ttm_stage: 'action',
    trigger_domain: 'diet',
    is_active: true,
    created_at: '2024-01-13 09:15:00',
    updated_at: '2024-01-13 09:15:00'
  },
  {
    prompt_id: '4',
    name: '用药提醒跟进',
    description: '药物依从性跟进话术',
    category: 'follow_up',
    content: '{{name}}，我想确认一下您的用药情况。您这周的{{medication}}都按时服用了吗？有没有遇到什么困难？',
    variables: ['name', 'medication'],
    ttm_stage: 'maintenance',
    trigger_domain: 'medication',
    is_active: false,
    created_at: '2024-01-12 16:45:00',
    updated_at: '2024-01-12 16:45:00'
  }
]

const dataSource = ref<PromptTemplate[]>(mockData)
const loading = ref(false)

// 筛选后的数据
const filteredData = computed(() => {
  return dataSource.value.filter(item => {
    if (filters.keyword && !item.name.includes(filters.keyword) && !item.content.includes(filters.keyword)) {
      return false
    }
    if (filters.category && item.category !== filters.category) {
      return false
    }
    if (filters.ttm_stage && item.ttm_stage !== filters.ttm_stage) {
      return false
    }
    if (filters.trigger_domain && item.trigger_domain !== filters.trigger_domain) {
      return false
    }
    return true
  })
})

// 表格列定义
const columns = [
  {
    title: '模板名称',
    dataIndex: 'name',
    key: 'name',
    width: 200
  },
  {
    title: '分类',
    dataIndex: 'category',
    key: 'category',
    width: 120
  },
  {
    title: 'TTM阶段',
    dataIndex: 'ttm_stage',
    key: 'ttm_stage',
    width: 120
  },
  {
    title: '触发域',
    dataIndex: 'trigger_domain',
    key: 'trigger_domain',
    width: 120
  },
  {
    title: '变量',
    dataIndex: 'variables',
    key: 'variables',
    width: 150
  },
  {
    title: '状态',
    dataIndex: 'is_active',
    key: 'is_active',
    width: 100
  },
  {
    title: '更新时间',
    dataIndex: 'updated_at',
    key: 'updated_at',
    width: 180
  },
  {
    title: '操作',
    key: 'action',
    width: 200,
    fixed: 'right' as const
  }
]

const getCategoryLabel = (value: string) => {
  return categories.find(c => c.value === value)?.label || value
}

// 格式化变量显示
const formatVariable = (v: string) => {
  return '{{' + v + '}}'
}

const handleCreate = () => {
  router.push('/prompts/create')
}

const handleEdit = (record: PromptTemplate) => {
  router.push(`/prompts/edit/${record.prompt_id}`)
}

const handleCopy = (record: PromptTemplate) => {
  const newPrompt = {
    ...record,
    prompt_id: Date.now().toString(),
    name: `${record.name} (副本)`,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
  dataSource.value.unshift(newPrompt)
  message.success('已复制模板')
}

const handleDelete = (record: PromptTemplate) => {
  dataSource.value = dataSource.value.filter(item => item.prompt_id !== record.prompt_id)
  message.success('已删除模板')
}

const handleToggleStatus = (record: PromptTemplate) => {
  record.is_active = !record.is_active
  message.success(record.is_active ? '已启用' : '已停用')
}

const handleReset = () => {
  filters.keyword = ''
  filters.category = undefined
  filters.ttm_stage = undefined
  filters.trigger_domain = undefined
}
</script>

<template>
  <div class="prompts-page">
    <Card title="Prompt 模板管理" :bordered="false">
      <!-- 筛选区域 -->
      <div class="filter-section">
        <Space wrap>
          <Input
            v-model:value="filters.keyword"
            placeholder="搜索模板名称或内容"
            style="width: 200px"
            allow-clear
          >
            <template #prefix>
              <SearchOutlined />
            </template>
          </Input>

          <Select
            v-model:value="filters.category"
            placeholder="选择分类"
            style="width: 150px"
            allow-clear
            :options="categories"
          />

          <Select
            v-model:value="filters.ttm_stage"
            placeholder="TTM阶段"
            style="width: 150px"
            allow-clear
          >
            <a-select-option
              v-for="(config, key) in TTM_STAGES"
              :key="key"
              :value="key"
            >
              {{ config.label }}
            </a-select-option>
          </Select>

          <Select
            v-model:value="filters.trigger_domain"
            placeholder="触发域"
            style="width: 150px"
            allow-clear
          >
            <a-select-option
              v-for="(config, key) in TRIGGER_DOMAINS"
              :key="key"
              :value="key"
            >
              {{ config.label }}
            </a-select-option>
          </Select>

          <Button @click="handleReset">重置</Button>
          <Button type="primary" @click="handleCreate">
            <template #icon><PlusOutlined /></template>
            新建模板
          </Button>
        </Space>
      </div>

      <!-- 数据表格 -->
      <Table
        :columns="columns"
        :data-source="filteredData"
        :loading="loading"
        :pagination="{ pageSize: 10, showSizeChanger: true, showTotal: (total: number) => `共 ${total} 条` }"
        :scroll="{ x: 1200 }"
        row-key="prompt_id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'category'">
            <Tag color="blue">{{ getCategoryLabel(record.category) }}</Tag>
          </template>

          <template v-else-if="column.key === 'ttm_stage'">
            <Tag v-if="record.ttm_stage" :color="TTM_STAGES[record.ttm_stage as keyof typeof TTM_STAGES]?.color">
              {{ TTM_STAGES[record.ttm_stage as keyof typeof TTM_STAGES]?.label }}
            </Tag>
            <span v-else>-</span>
          </template>

          <template v-else-if="column.key === 'trigger_domain'">
            <Tag v-if="record.trigger_domain" :color="TRIGGER_DOMAINS[record.trigger_domain as keyof typeof TRIGGER_DOMAINS]?.color">
              {{ TRIGGER_DOMAINS[record.trigger_domain as keyof typeof TRIGGER_DOMAINS]?.label }}
            </Tag>
            <span v-else>-</span>
          </template>

          <template v-else-if="column.key === 'variables'">
            <Space v-if="record.variables?.length" wrap>
              <Tag v-for="v in record.variables" :key="v" color="cyan">
                {{ formatVariable(v) }}
              </Tag>
            </Space>
            <span v-else>-</span>
          </template>

          <template v-else-if="column.key === 'is_active'">
            <Tag :color="record.is_active ? 'success' : 'default'">
              {{ record.is_active ? '启用' : '停用' }}
            </Tag>
          </template>

          <template v-else-if="column.key === 'action'">
            <Space>
              <Button type="link" size="small" @click="handleEdit(record as PromptTemplate)">
                <template #icon><EditOutlined /></template>
                编辑
              </Button>
              <Button type="link" size="small" @click="handleCopy(record as PromptTemplate)">
                <template #icon><CopyOutlined /></template>
                复制
              </Button>
              <Button
                type="link"
                size="small"
                @click="handleToggleStatus(record as PromptTemplate)"
              >
                {{ record.is_active ? '停用' : '启用' }}
              </Button>
              <Popconfirm
                title="确定删除此模板吗？"
                @confirm="handleDelete(record as PromptTemplate)"
              >
                <Button type="link" size="small" danger>
                  <template #icon><DeleteOutlined /></template>
                  删除
                </Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>
  </div>
</template>

<style scoped>
.prompts-page {
  padding: 24px;
}

.filter-section {
  margin-bottom: 16px;
}
</style>
