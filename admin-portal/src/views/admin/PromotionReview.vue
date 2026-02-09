<template>
  <div class="promotion-review">
    <a-page-header title="晋级审核" sub-title="审核用户晋级申请" />

    <!-- 状态筛选 -->
    <a-card class="mb-4">
      <a-radio-group v-model:value="statusFilter" @change="loadApplications">
        <a-radio-button value="">全部</a-radio-button>
        <a-radio-button value="pending">待审核</a-radio-button>
        <a-radio-button value="approved">已通过</a-radio-button>
        <a-radio-button value="rejected">已拒绝</a-radio-button>
      </a-radio-group>
    </a-card>

    <!-- 申请列表 -->
    <a-table
      :columns="columns"
      :data-source="applications"
      :loading="loading"
      row-key="id"
      size="small"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'transition'">
          {{ record.from_role }} → {{ record.to_role }}
        </template>
        <template v-if="column.key === 'status'">
          <a-tag :color="statusColor(record.status)">{{ statusLabel(record.status) }}</a-tag>
        </template>
        <template v-if="column.key === 'action'">
          <a-space v-if="record.status === 'pending'">
            <a @click="openDetail(record)">查看详情</a>
            <a-popconfirm title="确认通过?" @confirm="handleReview(record.id, 'approved')">
              <a style="color:green">通过</a>
            </a-popconfirm>
            <a style="color:red" @click="openReject(record)">拒绝</a>
          </a-space>
          <a v-else @click="openDetail(record)">查看详情</a>
        </template>
      </template>
    </a-table>

    <!-- 详情抽屉 -->
    <a-drawer v-model:open="drawerVisible" title="晋级申请详情" width="520">
      <template v-if="selectedApp">
        <a-descriptions bordered :column="1" size="small">
          <a-descriptions-item label="申请人">{{ selectedApp.username }}</a-descriptions-item>
          <a-descriptions-item label="晋级路径">{{ selectedApp.from_role }} → {{ selectedApp.to_role }}</a-descriptions-item>
          <a-descriptions-item label="状态">
            <a-tag :color="statusColor(selectedApp.status)">{{ statusLabel(selectedApp.status) }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="申请时间">{{ selectedApp.created_at }}</a-descriptions-item>
          <a-descriptions-item label="审核时间" v-if="selectedApp.reviewed_at">{{ selectedApp.reviewed_at }}</a-descriptions-item>
          <a-descriptions-item label="审核评语" v-if="selectedApp.review_comment">{{ selectedApp.review_comment }}</a-descriptions-item>
        </a-descriptions>

        <a-divider>学分快照</a-divider>
        <pre class="snapshot">{{ formatSnapshot(selectedApp.credit_snapshot) }}</pre>

        <a-divider>积分快照</a-divider>
        <pre class="snapshot">{{ formatSnapshot(selectedApp.point_snapshot) }}</pre>

        <a-divider>同道者快照</a-divider>
        <pre class="snapshot">{{ formatSnapshot(selectedApp.companion_snapshot) }}</pre>

        <a-divider>校验结果</a-divider>
        <pre class="snapshot" v-if="selectedApp.check_result">{{ formatSnapshot(selectedApp.check_result) }}</pre>
        <span v-else>无校验数据</span>
      </template>
    </a-drawer>

    <!-- 拒绝弹窗 -->
    <a-modal v-model:open="rejectVisible" title="拒绝原因" @ok="confirmReject">
      <a-textarea v-model:value="rejectComment" :rows="3" placeholder="请输入拒绝原因" />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { promotionApi } from '@/api/credit-promotion'

const loading = ref(false)
const applications = ref<any[]>([])
const statusFilter = ref('')
const drawerVisible = ref(false)
const rejectVisible = ref(false)
const selectedApp = ref<any>(null)
const rejectComment = ref('')
const rejectingId = ref('')

const columns = [
  { title: '申请人', dataIndex: 'username', key: 'username' },
  { title: '晋级路径', key: 'transition' },
  { title: '状态', key: 'status', width: 100 },
  { title: '申请时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  { title: '操作', key: 'action', width: 200 },
]

function statusColor(s: string) {
  return s === 'pending' ? 'orange' : s === 'approved' ? 'green' : 'red'
}

function statusLabel(s: string) {
  return s === 'pending' ? '待审核' : s === 'approved' ? '已通过' : '已拒绝'
}

function formatSnapshot(data: any) {
  if (!data) return '-'
  if (typeof data === 'string') {
    try { data = JSON.parse(data) } catch { return data }
  }
  return JSON.stringify(data, null, 2)
}

async function loadApplications() {
  loading.value = true
  try {
    const params = statusFilter.value ? { status: statusFilter.value } : undefined
    const res = await promotionApi.listApplications(params)
    applications.value = res.data
  } catch (e) {
    console.error('加载失败', e)
  } finally {
    loading.value = false
  }
}

function openDetail(record: any) {
  selectedApp.value = record
  drawerVisible.value = true
}

function openReject(record: any) {
  rejectingId.value = record.id
  rejectComment.value = ''
  rejectVisible.value = true
}

async function handleReview(id: string, action: string, comment?: string) {
  try {
    await promotionApi.review(id, action, comment)
    message.success(action === 'approved' ? '已通过' : '已拒绝')
    loadApplications()
  } catch (e) {
    console.error('审核失败', e)
  }
}

async function confirmReject() {
  await handleReview(rejectingId.value, 'rejected', rejectComment.value)
  rejectVisible.value = false
}

onMounted(loadApplications)
</script>

<style scoped>
.promotion-review { padding: 16px; }
.mb-4 { margin-bottom: 16px; }
.snapshot {
  background: #f5f5f5;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  max-height: 200px;
  overflow-y: auto;
}
</style>
