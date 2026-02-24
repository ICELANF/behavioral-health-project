<template>
  <div class="vision-rx-queue">
    <a-page-header title="视力处方审批队列" sub-title="VisionGuard · AI→教练审核→推送">
      <template #extra>
        <a-space>
          <a-select v-model:value="riskFilter" style="width: 120px" placeholder="风险等级" allowClear @change="fetchQueue">
            <a-select-option value="urgent">紧急</a-select-option>
            <a-select-option value="alert">警惕</a-select-option>
            <a-select-option value="watch">关注</a-select-option>
            <a-select-option value="normal">正常</a-select-option>
          </a-select>
          <a-select v-model:value="statusFilter" style="width: 120px" placeholder="状态" allowClear @change="fetchQueue">
            <a-select-option value="pending">待审批</a-select-option>
            <a-select-option value="approved">已通过</a-select-option>
            <a-select-option value="rejected">已拒绝</a-select-option>
          </a-select>
          <a-button @click="fetchQueue">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <!-- 统计卡片 -->
    <a-row :gutter="16" style="margin-bottom: 16px;">
      <a-col :span="6">
        <a-card>
          <a-statistic title="待审批" :value="stats.pending" :value-style="{ color: '#fa8c16' }" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="今日通过" :value="stats.approved_today" :value-style="{ color: '#52c41a' }" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="高风险" :value="stats.high_risk" :value-style="{ color: '#ff4d4f' }" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="本周处理" :value="stats.weekly_total" />
        </a-card>
      </a-col>
    </a-row>

    <!-- 审批表格 -->
    <a-table
      :columns="columns"
      :data-source="queueItems"
      :loading="loading"
      :pagination="{ pageSize: 20, showTotal: (t: number) => `共 ${t} 条` }"
      row-key="id"
      @change="handleTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'priority'">
          <a-tag :color="record.priority === 'high' ? 'red' : record.priority === 'normal' ? 'blue' : 'default'">
            {{ record.priority === 'high' ? '高' : record.priority === 'normal' ? '普通' : '低' }}
          </a-tag>
        </template>
        <template v-if="column.key === 'status'">
          <a-tag :color="statusColor(record.status)">{{ statusLabel(record.status) }}</a-tag>
        </template>
        <template v-if="column.key === 'student'">
          <a @click="showStudentDetail(record.student_id)">{{ record.student_name || `#${record.student_id}` }}</a>
        </template>
        <template v-if="column.key === 'action'">
          <a-space v-if="record.status === 'pending'">
            <a-button type="primary" size="small" @click="handleApprove(record)">通过</a-button>
            <a-button size="small" @click="handleModify(record)">修改</a-button>
            <a-popconfirm title="确定拒绝?" @confirm="handleReject(record)">
              <a-button danger size="small">拒绝</a-button>
            </a-popconfirm>
          </a-space>
          <span v-else class="text-gray">{{ record.reviewed_by ? `由 #${record.reviewed_by} 处理` : '-' }}</span>
        </template>
      </template>
    </a-table>

    <!-- 学生详情侧边栏 -->
    <a-drawer
      v-model:open="drawerVisible"
      title="学生视力详情"
      :width="480"
      placement="right"
    >
      <template v-if="studentDetail">
        <!-- 仪表盘概览 -->
        <a-descriptions title="视力概览" :column="2" bordered size="small">
          <a-descriptions-item label="风险等级">
            <a-tag :color="riskColor(studentDetail.risk_level)">{{ studentDetail.risk_level }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="连续打卡">{{ studentDetail.streak_days }} 天</a-descriptions-item>
          <a-descriptions-item label="今日评分">{{ studentDetail.today?.score ?? '未打卡' }}</a-descriptions-item>
          <a-descriptions-item label="TTM 阶段">{{ studentDetail.profile?.ttm_stage || '-' }}</a-descriptions-item>
        </a-descriptions>

        <!-- 近7天评分 -->
        <div style="margin-top: 16px;">
          <h4>近 7 天评分</h4>
          <div class="score-bars">
            <div v-for="s in (studentDetail.week_scores || [])" :key="s.date" class="score-bar-item">
              <div class="bar-label">{{ s.date?.slice(5) }}</div>
              <div class="bar-container">
                <div class="bar-fill" :style="{ width: `${s.score}%`, background: s.score >= 75 ? '#52c41a' : s.score >= 45 ? '#1890ff' : '#fa8c16' }" />
              </div>
              <div class="bar-value">{{ s.score }}</div>
            </div>
          </div>
        </div>

        <!-- 最近检查 -->
        <div v-if="studentDetail.latest_exam" style="margin-top: 16px;">
          <h4>最近检查</h4>
          <a-descriptions :column="2" size="small">
            <a-descriptions-item label="日期">{{ studentDetail.latest_exam.exam_date }}</a-descriptions-item>
            <a-descriptions-item label="左眼 SPH">{{ studentDetail.latest_exam.left_sph ?? '-' }}</a-descriptions-item>
            <a-descriptions-item label="右眼 SPH">{{ studentDetail.latest_exam.right_sph ?? '-' }}</a-descriptions-item>
            <a-descriptions-item label="风险">
              <a-tag :color="riskColor(studentDetail.latest_exam.risk_level)">{{ studentDetail.latest_exam.risk_level }}</a-tag>
            </a-descriptions-item>
          </a-descriptions>
        </div>
      </template>
      <a-spin v-else tip="加载中..." />
    </a-drawer>

    <!-- 修改弹窗 -->
    <a-modal v-model:open="modifyVisible" title="修改推送内容" @ok="submitModify" ok-text="保存并通过">
      <a-form layout="vertical">
        <a-form-item label="推送标题">
          <a-input v-model:value="modifyForm.title" />
        </a-form-item>
        <a-form-item label="推送内容">
          <a-textarea v-model:value="modifyForm.content" :rows="4" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { ReloadOutlined } from '@ant-design/icons-vue'
import axios from 'axios'

const token = localStorage.getItem('admin_token') || ''
const api = axios.create({
  baseURL: '/api',
  headers: { Authorization: `Bearer ${token}` },
})

const loading = ref(false)
const queueItems = ref<any[]>([])
const riskFilter = ref<string | undefined>()
const statusFilter = ref<string | undefined>('pending')
const drawerVisible = ref(false)
const studentDetail = ref<any>(null)
const modifyVisible = ref(false)
const modifyForm = reactive({ id: 0, title: '', content: '' })

const stats = reactive({
  pending: 0,
  approved_today: 0,
  high_risk: 0,
  weekly_total: 0,
})

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '学员', key: 'student', dataIndex: 'student_id' },
  { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '内容', dataIndex: 'content', key: 'content', ellipsis: true, width: 200 },
  { title: '优先级', key: 'priority', dataIndex: 'priority', width: 80 },
  { title: '状态', key: 'status', dataIndex: 'status', width: 80 },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 160 },
  { title: '操作', key: 'action', width: 180, fixed: 'right' as const },
]

function statusColor(s: string) {
  if (s === 'pending') return 'orange'
  if (s === 'approved') return 'green'
  if (s === 'rejected') return 'red'
  return 'default'
}
function statusLabel(s: string) {
  const map: Record<string, string> = { pending: '待审批', approved: '已通过', rejected: '已拒绝', sent: '已发送' }
  return map[s] || s
}
function riskColor(r: string) {
  if (r === 'urgent') return 'red'
  if (r === 'alert') return 'orange'
  if (r === 'watch') return 'blue'
  return 'green'
}

async function fetchQueue() {
  loading.value = true
  try {
    // 使用现有 coach_push_queue API, 过滤 source_type=vision_rx
    const params: any = { source_type: 'vision_rx', limit: 100 }
    if (statusFilter.value) params.status = statusFilter.value
    const res = await api.get('/v1/coach/push-queue', { params })
    const items = res.data?.items || res.data || []
    queueItems.value = Array.isArray(items) ? items : []

    // 计算统计
    stats.pending = queueItems.value.filter((i: any) => i.status === 'pending').length
    stats.approved_today = queueItems.value.filter((i: any) =>
      i.status === 'approved' && i.reviewed_at?.startsWith(new Date().toISOString().slice(0, 10))
    ).length
    stats.high_risk = queueItems.value.filter((i: any) => i.priority === 'high').length
    stats.weekly_total = queueItems.value.length
  } catch (e: any) {
    // 如果 push-queue API 不支持 source_type 过滤, 退回到全量获取
    try {
      const res = await api.get('/v1/coach/push-queue')
      const all = res.data?.items || res.data || []
      queueItems.value = (Array.isArray(all) ? all : []).filter((i: any) => i.source_type === 'vision_rx')
      stats.pending = queueItems.value.filter((i: any) => i.status === 'pending').length
    } catch {
      queueItems.value = []
    }
  }
  loading.value = false
}

async function showStudentDetail(studentId: number) {
  drawerVisible.value = true
  studentDetail.value = null
  try {
    const res = await api.get(`/v1/vision/dashboard/${studentId}`)
    studentDetail.value = res.data
  } catch {
    message.error('加载学生详情失败')
  }
}

async function handleApprove(record: any) {
  try {
    await api.put(`/v1/coach/push-queue/${record.id}/approve`)
    message.success('已通过')
    fetchQueue()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '操作失败')
  }
}

async function handleReject(record: any) {
  try {
    await api.put(`/v1/coach/push-queue/${record.id}/reject`)
    message.success('已拒绝')
    fetchQueue()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '操作失败')
  }
}

function handleModify(record: any) {
  modifyForm.id = record.id
  modifyForm.title = record.title || ''
  modifyForm.content = record.content || ''
  modifyVisible.value = true
}

async function submitModify() {
  try {
    await api.put(`/v1/coach/push-queue/${modifyForm.id}/approve`, {
      title: modifyForm.title,
      content: modifyForm.content,
    })
    message.success('已修改并通过')
    modifyVisible.value = false
    fetchQueue()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '操作失败')
  }
}

function handleTableChange() { /* pagination handled by a-table */ }

onMounted(fetchQueue)
</script>

<style scoped>
.vision-rx-queue {
  padding: 0;
}
.text-gray { color: #999; font-size: 12px; }
.score-bars {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.score-bar-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.bar-label {
  width: 40px;
  font-size: 12px;
  color: #666;
  text-align: right;
}
.bar-container {
  flex: 1;
  height: 16px;
  background: #f0f0f0;
  border-radius: 8px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  border-radius: 8px;
  transition: width 0.3s;
}
.bar-value {
  width: 30px;
  font-size: 12px;
  color: #333;
  font-weight: 500;
}
</style>
