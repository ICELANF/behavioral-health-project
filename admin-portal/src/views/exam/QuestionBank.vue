<template>
  <div class="question-bank">
    <div class="page-header">
      <h2>题库管理</h2>
      <a-button type="primary" @click="$router.push('/question/create')">
        <template #icon><PlusOutlined /></template>
        创建题目
      </a-button>
    </div>

    <a-card>
      <a-row :gutter="16" style="margin-bottom: 16px">
        <a-col :span="6">
          <a-select v-model:value="filters.type" placeholder="题目类型" allowClear style="width: 100%">
            <a-select-option value="single">单选题</a-select-option>
            <a-select-option value="multiple">多选题</a-select-option>
            <a-select-option value="truefalse">判断题</a-select-option>
            <a-select-option value="short_answer">简答题</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-select v-model:value="filters.level" placeholder="认证等级" allowClear style="width: 100%">
            <a-select-option value="L0">L0</a-select-option>
            <a-select-option value="L1">L1</a-select-option>
            <a-select-option value="L2">L2</a-select-option>
            <a-select-option value="L3">L3</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-select v-model:value="filters.difficulty" placeholder="难度" allowClear style="width: 100%">
            <a-select-option :value="1">简单</a-select-option>
            <a-select-option :value="2">较易</a-select-option>
            <a-select-option :value="3">中等</a-select-option>
            <a-select-option :value="4">较难</a-select-option>
            <a-select-option :value="5">困难</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-input-search v-model:value="filters.keyword" placeholder="搜索题目" />
        </a-col>
      </a-row>

      <a-table :dataSource="questions" :columns="columns" rowKey="question_id">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'content'">
            <div class="question-content">{{ record.content.substring(0, 50) }}...</div>
          </template>
          <template v-if="column.key === 'type'">
            <a-tag :color="typeColors[record.type]">{{ typeLabels[record.type] }}</a-tag>
          </template>
          <template v-if="column.key === 'difficulty'">
            <a-rate :value="record.difficulty" disabled :count="5" />
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a @click="editQuestion(record)">编辑</a>
              <a-popconfirm title="确定删除？" @confirm="deleteQuestion(record)">
                <a style="color: #ff4d4f">删除</a>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'

const router = useRouter()

const filters = reactive({
  type: undefined,
  level: undefined,
  difficulty: undefined,
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

const columns = [
  { title: '题目内容', key: 'content', width: 300 },
  { title: '类型', key: 'type', width: 100 },
  { title: '等级', dataIndex: 'level', width: 80 },
  { title: '难度', key: 'difficulty', width: 150 },
  { title: '使用次数', dataIndex: 'use_count', width: 100 },
  { title: '操作', key: 'action', width: 120 }
]

const questions = ref([
  { question_id: '1', content: '行为健康的核心理念是什么？', type: 'single', level: 'L0', difficulty: 2, use_count: 45 },
  { question_id: '2', content: '以下哪些属于行为健康干预领域？', type: 'multiple', level: 'L0', difficulty: 3, use_count: 38 },
  { question_id: '3', content: 'TTM模型将行为改变分为几个阶段？', type: 'single', level: 'L1', difficulty: 2, use_count: 52 },
  { question_id: '4', content: '动机访谈(MI)的核心精神包括哪些？', type: 'multiple', level: 'L2', difficulty: 4, use_count: 23 }
])

const editQuestion = (record: any) => {
  router.push(`/question/edit/${record.question_id}`)
}

const deleteQuestion = (record: any) => {
  const index = questions.value.findIndex(q => q.question_id === record.question_id)
  if (index > -1) {
    questions.value.splice(index, 1)
    message.success('题目已删除')
  }
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.question-content {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
