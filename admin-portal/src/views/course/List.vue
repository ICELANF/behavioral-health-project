<template>
  <div class="course-list">
    <div class="page-header">
      <h2>课程列表</h2>
      <a-button type="primary" @click="$router.push('/course/create')">
        <template #icon><PlusOutlined /></template>
        创建课程
      </a-button>
    </div>

    <!-- 筛选 -->
    <a-card style="margin-bottom: 16px">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-select v-model:value="filters.level" placeholder="认证等级" allowClear style="width: 100%">
            <a-select-option value="L0">L0 公众学习</a-select-option>
            <a-select-option value="L1">L1 初级教练</a-select-option>
            <a-select-option value="L2">L2 中级教练</a-select-option>
            <a-select-option value="L3">L3 高级教练</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-select v-model:value="filters.category" placeholder="课程类别" allowClear style="width: 100%">
            <a-select-option value="knowledge">知识体系</a-select-option>
            <a-select-option value="method">方法体系</a-select-option>
            <a-select-option value="skill">核心技能</a-select-option>
            <a-select-option value="value">观念心智</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-select v-model:value="filters.status" placeholder="状态" allowClear style="width: 100%">
            <a-select-option value="draft">草稿</a-select-option>
            <a-select-option value="published">已上架</a-select-option>
            <a-select-option value="offline">已下架</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-input-search v-model:value="filters.keyword" placeholder="搜索课程名称" @search="fetchCourses" />
        </a-col>
      </a-row>
    </a-card>

    <!-- 课程表格 -->
    <a-table
      :dataSource="courses"
      :columns="columns"
      :loading="loading"
      :pagination="pagination"
      @change="handleTableChange"
      rowKey="course_id"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'cover'">
          <a-image :src="record.cover_url || defaultCover" :width="80" />
        </template>
        <template v-if="column.key === 'title'">
          <div>
            <div class="course-title">{{ record.title }}</div>
            <a-tag :color="levelColors[record.level]">{{ record.level }}</a-tag>
            <a-tag>{{ categoryLabels[record.category] }}</a-tag>
          </div>
        </template>
        <template v-if="column.key === 'stats'">
          <div class="course-stats">
            <span>{{ record.chapter_count || 0 }} 章节</span>
            <span>{{ record.quiz_count || 0 }} 题目</span>
            <span>{{ record.duration_minutes || 0 }} 分钟</span>
          </div>
        </template>
        <template v-if="column.key === 'status'">
          <a-badge
            :status="statusMap[record.status]?.badge"
            :text="statusMap[record.status]?.text"
          />
        </template>
        <template v-if="column.key === 'action'">
          <a-space>
            <a @click="$router.push(`/course/chapters/${record.course_id}`)">章节</a>
            <a @click="$router.push(`/course/edit/${record.course_id}`)">编辑</a>
            <a-dropdown>
              <a>更多</a>
              <template #overlay>
                <a-menu>
                  <a-menu-item v-if="record.status === 'draft'" @click="handlePublish(record)">
                    上架
                  </a-menu-item>
                  <a-menu-item v-if="record.status === 'published'" @click="handleOffline(record)">
                    下架
                  </a-menu-item>
                  <a-menu-item @click="handlePreview(record)">预览</a-menu-item>
                  <a-menu-divider />
                  <a-menu-item danger @click="handleDelete(record)">删除</a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </a-space>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'

const loading = ref(false)
const defaultCover = 'https://via.placeholder.com/160x90?text=Course'

const filters = reactive({
  level: undefined as string | undefined,
  category: undefined as string | undefined,
  status: undefined as string | undefined,
  keyword: ''
})

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0
})

const levelColors: Record<string, string> = {
  L0: 'blue',
  L1: 'green',
  L2: 'orange',
  L3: 'red',
  L4: 'purple'
}

const categoryLabels: Record<string, string> = {
  knowledge: '知识体系',
  method: '方法体系',
  skill: '核心技能',
  value: '观念心智'
}

const statusMap: Record<string, { badge: string; text: string }> = {
  draft: { badge: 'default', text: '草稿' },
  published: { badge: 'success', text: '已上架' },
  offline: { badge: 'error', text: '已下架' }
}

const columns = [
  { title: '封面', key: 'cover', width: 100 },
  { title: '课程信息', key: 'title', width: 300 },
  { title: '内容统计', key: 'stats', width: 200 },
  { title: '学习人数', dataIndex: 'student_count', width: 100 },
  { title: '状态', key: 'status', width: 100 },
  { title: '更新时间', dataIndex: 'updated_at', width: 160 },
  { title: '操作', key: 'action', width: 150, fixed: 'right' }
]

// 模拟数据
const courses = ref([
  {
    course_id: '1',
    title: '行为健康入门',
    level: 'L0',
    category: 'knowledge',
    cover_url: '',
    chapter_count: 6,
    quiz_count: 30,
    duration_minutes: 90,
    student_count: 856,
    status: 'published',
    updated_at: '2026-01-20 10:30'
  },
  {
    course_id: '2',
    title: '代谢与慢病风险入门',
    level: 'L1',
    category: 'knowledge',
    cover_url: '',
    chapter_count: 8,
    quiz_count: 45,
    duration_minutes: 120,
    student_count: 234,
    status: 'published',
    updated_at: '2026-01-19 15:20'
  },
  {
    course_id: '3',
    title: '高级动机访谈技术',
    level: 'L2',
    category: 'skill',
    cover_url: '',
    chapter_count: 10,
    quiz_count: 60,
    duration_minutes: 300,
    student_count: 89,
    status: 'draft',
    updated_at: '2026-01-24 09:00'
  }
])

const fetchCourses = () => {
  loading.value = true
  // TODO: 调用API获取课程列表
  setTimeout(() => {
    loading.value = false
  }, 500)
}

const handleTableChange = (pag: any) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchCourses()
}

const handlePublish = (record: any) => {
  Modal.confirm({
    title: '确认上架',
    content: `确定要上架课程「${record.title}」吗？`,
    onOk() {
      record.status = 'published'
      message.success('上架成功')
    }
  })
}

const handleOffline = (record: any) => {
  Modal.confirm({
    title: '确认下架',
    content: `确定要下架课程「${record.title}」吗？`,
    onOk() {
      record.status = 'offline'
      message.success('下架成功')
    }
  })
}

const handlePreview = (record: any) => {
  message.info('预览功能开发中')
}

const handleDelete = (record: any) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除课程「${record.title}」吗？此操作不可恢复。`,
    okType: 'danger',
    onOk() {
      const index = courses.value.findIndex(c => c.course_id === record.course_id)
      if (index > -1) {
        courses.value.splice(index, 1)
        message.success('删除成功')
      }
    }
  })
}

onMounted(() => {
  fetchCourses()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
}

.course-title {
  font-weight: 500;
  margin-bottom: 4px;
}

.course-stats {
  color: #999;
  font-size: 12px;
}

.course-stats span {
  margin-right: 12px;
}
</style>
