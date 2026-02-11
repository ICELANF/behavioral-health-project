<template>
  <div class="safety-review">
    <h2>安全审核队列</h2>

    <!-- 筛选 -->
    <a-row :gutter="16" style="margin-bottom: 16px">
      <a-col :span="6">
        <a-select v-model:value="filters.severity" placeholder="严重级别" allowClear style="width: 100%" @change="fetchData">
          <a-select-option value="critical">危急 (Critical)</a-select-option>
          <a-select-option value="high">高 (High)</a-select-option>
          <a-select-option value="medium">中 (Medium)</a-select-option>
          <a-select-option value="low">低 (Low)</a-select-option>
        </a-select>
      </a-col>
      <a-col :span="4">
        <a-button type="primary" @click="fetchData">刷新</a-button>
      </a-col>
    </a-row>

    <!-- 表格 -->
    <a-table
      :dataSource="items"
      :columns="columns"
      :pagination="pagination"
      :loading="loading"
      rowKey="id"
      @change="handleTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'severity'">
          <a-tag :color="severityColor(record.severity)">{{ record.severity }}</a-tag>
        </template>
        <template v-if="column.key === 'event_type'">
          <a-tag>{{ eventTypeLabel(record.event_type) }}</a-tag>
        </template>
        <template v-if="column.key === 'input_text'">
          <a-tooltip :title="record.input_text">
            <span>{{ (record.input_text || '').substring(0, 60) }}{{ (record.input_text || '').length > 60 ? '...' : '' }}</span>
          </a-tooltip>
        </template>
        <template v-if="column.key === 'action'">
          <a-space>
            <a-button size="small" type="primary" @click="showDetail(record)">查看</a-button>
            <a-button size="small" @click="resolve(record.id, 'resolved')">审核通过</a-button>
            <a-button size="small" danger @click="resolve(record.id, 'false_positive')">误报</a-button>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 详情弹窗 -->
    <a-modal v-model:open="detailVisible" title="安全事件详情" width="700px" :footer="null">
      <template v-if="detailData">
        <a-descriptions :column="2" bordered size="small">
          <a-descriptions-item label="事件ID">{{ detailData.id }}</a-descriptions-item>
          <a-descriptions-item label="用户ID">{{ detailData.user_id || '-' }}</a-descriptions-item>
          <a-descriptions-item label="类型">{{ eventTypeLabel(detailData.event_type) }}</a-descriptions-item>
          <a-descriptions-item label="严重级">
            <a-tag :color="severityColor(detailData.severity)">{{ detailData.severity }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="时间" :span="2">{{ detailData.created_at }}</a-descriptions-item>
          <a-descriptions-item label="输入文本" :span="2">
            <div style="max-height: 150px; overflow-y: auto; white-space: pre-wrap">{{ detailData.input_text || '-' }}</div>
          </a-descriptions-item>
          <a-descriptions-item label="输出文本" :span="2">
            <div style="max-height: 150px; overflow-y: auto; white-space: pre-wrap">{{ detailData.output_text || '-' }}</div>
          </a-descriptions-item>
          <a-descriptions-item label="过滤详情" :span="2">
            <pre style="max-height: 150px; overflow-y: auto; font-size: 12px">{{ JSON.stringify(detailData.filter_details, null, 2) }}</pre>
          </a-descriptions-item>
        </a-descriptions>
        <div style="margin-top: 16px; text-align: right" v-if="!detailData.resolved">
          <a-space>
            <a-button type="primary" @click="resolve(detailData.id, 'resolved'); detailVisible = false">审核通过</a-button>
            <a-button @click="resolve(detailData.id, 'false_positive'); detailVisible = false">标记误报</a-button>
            <a-button @click="resolve(detailData.id, 'whitelist'); detailVisible = false">加入白名单</a-button>
          </a-space>
        </div>
      </template>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import request from '@/api/request'

const items = ref<any[]>([])
const loading = ref(false)
const detailVisible = ref(false)
const detailData = ref<any>(null)

const filters = reactive({
  severity: undefined as string | undefined,
})

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
})

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '用户', dataIndex: 'user_id', key: 'user_id', width: 70 },
  { title: '类型', key: 'event_type', width: 110 },
  { title: '严重级', key: 'severity', width: 90 },
  { title: '输入摘要', key: 'input_text' },
  { title: '时间', dataIndex: 'created_at', key: 'created_at', width: 160 },
  { title: '操作', key: 'action', width: 220 },
]

const severityColor = (s: string) => {
  const map: Record<string, string> = { critical: 'red', high: 'orange', medium: 'gold', low: 'green' }
  return map[s] || 'default'
}

const eventTypeLabel = (t: string) => {
  const map: Record<string, string> = {
    input_blocked: '输入拦截',
    output_filtered: '输出过滤',
    crisis_detected: '危机检测',
    daily_report: '日报',
  }
  return map[t] || t
}

const fetchData = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.current,
      page_size: pagination.pageSize,
    }
    if (filters.severity) params.severity = filters.severity

    const res = await request.get('v1/safety/review-queue', { params })
    items.value = res.data.items || []
    pagination.total = res.data.total || 0
  } catch (e) {
    console.error('Failed to load review queue', e)
  } finally {
    loading.value = false
  }
}

const handleTableChange = (pag: any) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchData()
}

const showDetail = async (record: any) => {
  try {
    const res = await request.get(`v1/safety/logs/${record.id}`)
    detailData.value = res.data
    detailVisible.value = true
  } catch {
    message.error('加载详情失败')
  }
}

const resolve = async (id: number, action: string) => {
  try {
    await request.put(`v1/safety/logs/${id}/resolve`, { action })
    message.success('操作成功')
    fetchData()
  } catch {
    message.error('操作失败')
  }
}

onMounted(fetchData)
</script>

<style scoped>
.safety-review h2 {
  margin-bottom: 16px;
}
</style>
