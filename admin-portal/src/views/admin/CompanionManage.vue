<template>
  <div class="companion-manage">
    <a-page-header title="同道者关系管理" sub-title="查看和管理带教关系" />

    <!-- 筛选栏 -->
    <a-card class="mb-4">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-select v-model:value="filters.status" placeholder="状态筛选" allowClear style="width:100%">
            <a-select-option value="active">进行中</a-select-option>
            <a-select-option value="graduated">已毕业</a-select-option>
            <a-select-option value="dropped">已退出</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-input-number v-model:value="filters.mentor_id" placeholder="导师ID" style="width:100%" />
        </a-col>
        <a-col :span="12" style="text-align:right">
          <a-button type="primary" @click="loadRelations">查询</a-button>
        </a-col>
      </a-row>
    </a-card>

    <!-- 表格 -->
    <a-table
      :columns="columns"
      :data-source="relations"
      :loading="loading"
      :pagination="{ current: page, pageSize, total, onChange: onPageChange }"
      row-key="id"
      size="small"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <a-tag :color="statusColor(record.status)">{{ statusLabel(record.status) }}</a-tag>
        </template>
        <template v-if="column.key === 'quality_score'">
          {{ record.quality_score ? record.quality_score.toFixed(1) : '-' }}
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { companionApi } from '@/api/credit-promotion'

const loading = ref(false)
const relations = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20

const filters = reactive({
  status: undefined as string | undefined,
  mentor_id: undefined as number | undefined,
})

const columns = [
  { title: '导师ID', dataIndex: 'mentor_id', key: 'mentor_id', width: 80 },
  { title: '导师', dataIndex: 'mentor_name', key: 'mentor_name' },
  { title: '学员ID', dataIndex: 'mentee_id', key: 'mentee_id', width: 80 },
  { title: '学员', dataIndex: 'mentee_name', key: 'mentee_name' },
  { title: '导师角色', dataIndex: 'mentor_role', key: 'mentor_role', width: 100 },
  { title: '学员角色', dataIndex: 'mentee_role', key: 'mentee_role', width: 100 },
  { title: '状态', key: 'status', width: 90 },
  { title: '质量分', key: 'quality_score', width: 80 },
  { title: '开始时间', dataIndex: 'started_at', key: 'started_at', width: 160 },
  { title: '毕业时间', dataIndex: 'graduated_at', key: 'graduated_at', width: 160 },
]

function statusColor(s: string) {
  return s === 'active' ? 'blue' : s === 'graduated' ? 'green' : 'red'
}

function statusLabel(s: string) {
  return s === 'active' ? '进行中' : s === 'graduated' ? '已毕业' : '已退出'
}

async function loadRelations() {
  loading.value = true
  try {
    const res = await companionApi.adminListAll({
      status: filters.status,
      mentor_id: filters.mentor_id,
      skip: (page.value - 1) * pageSize,
      limit: pageSize,
    })
    relations.value = res.data.items
    total.value = res.data.total
  } catch (e) {
    console.error('加载失败', e)
  } finally {
    loading.value = false
  }
}

function onPageChange(p: number) {
  page.value = p
  loadRelations()
}

onMounted(loadRelations)
</script>

<style scoped>
.companion-manage { padding: 16px; }
.mb-4 { margin-bottom: 16px; }
</style>
