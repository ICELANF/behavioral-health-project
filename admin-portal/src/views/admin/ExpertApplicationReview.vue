<template>
  <div class="expert-application-review">
    <a-page-header title="专家入驻审核" sub-title="审核专家入驻申请">
      <template #extra>
        <a-button @click="fetchApplications">刷新</a-button>
      </template>
    </a-page-header>

    <!-- 统计卡片 -->
    <a-row :gutter="16" style="margin-bottom: 16px">
      <a-col :span="8">
        <a-statistic title="待审核" :value="stats.pending" :value-style="{ color: '#d48806' }" />
      </a-col>
      <a-col :span="8">
        <a-statistic title="已通过" :value="stats.approved" :value-style="{ color: '#389e0d' }" />
      </a-col>
      <a-col :span="8">
        <a-statistic title="已拒绝" :value="stats.rejected" :value-style="{ color: '#cf1322' }" />
      </a-col>
    </a-row>

    <!-- Tab 切换 -->
    <a-tabs v-model:activeKey="activeTab" @change="fetchApplications">
      <a-tab-pane key="pending_review" tab="待审核" />
      <a-tab-pane key="all" tab="全部" />
    </a-tabs>

    <!-- 列表 -->
    <a-spin :spinning="loading">
      <div class="list-card-container">
        <a-empty v-if="applications.length === 0 && !loading" description="暂无申请" />
        <ListCard v-for="record in applications" :key="record.tenant_id" @click="openDetail(record)">
          <template #avatar>
            <span style="font-size: 28px">{{ record.brand_avatar }}</span>
          </template>
          <template #title>
            <span style="font-weight: 600">{{ record.brand_name }}</span>
            <a-tag :color="statusColor(record.application_status)" size="small" style="margin-left: 8px">{{ statusLabel(record.application_status) }}</a-tag>
          </template>
          <template #subtitle>
            <span style="color: #666">{{ record.expert_title }}</span>
            <span style="color: #999; margin-left: 8px">{{ record.domain_id }}</span>
          </template>
          <template #meta>
            <a-tag v-for="s in (record.expert_specialties || []).slice(0, 3)" :key="s" size="small">{{ s }}</a-tag>
            <span style="color: #999; font-size: 12px">{{ record.applied_at }}</span>
          </template>
          <template #actions>
            <a-button type="link" size="small" @click.stop="openDetail(record)">详情</a-button>
          </template>
        </ListCard>
      </div>
    </a-spin>
    <div style="display: flex; justify-content: flex-end; margin-top: 16px">
      <a-pagination v-model:current="pagination.current" :page-size="pagination.pageSize" :total="pagination.total" @change="(p: number) => { pagination.current = p; fetchApplications() }" />
    </div>

    <!-- 详情弹窗 -->
    <a-modal
      v-model:open="showDetail"
      :title="`申请详情 — ${detailData?.brand_name || ''}`"
      width="640px"
      :footer="null"
    >
      <template v-if="detailData">
        <a-descriptions :column="2" bordered size="small" style="margin-bottom: 16px">
          <a-descriptions-item label="工作室" :span="2">{{ detailData.brand_name }}</a-descriptions-item>
          <a-descriptions-item label="头衔">{{ detailData.expert_title }}</a-descriptions-item>
          <a-descriptions-item label="领域">{{ detailData.domain_id }}</a-descriptions-item>
          <a-descriptions-item label="资质" :span="2">
            <a-tag v-for="c in (detailData.expert_credentials || [])" :key="c" size="small">{{ c }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="专长" :span="2">
            <a-tag v-for="s in (detailData.expert_specialties || [])" :key="s" size="small" color="blue">{{ s }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="Agent" :span="2">
            <a-tag v-for="a in (detailData.enabled_agents || [])" :key="a" size="small" color="green">{{ a }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="自我介绍" :span="2">
            {{ detailData.expert_self_intro || '(未填写)' }}
          </a-descriptions-item>
          <a-descriptions-item label="申请人" :span="2" v-if="detailData.applicant">
            {{ detailData.applicant.username }} (ID: {{ detailData.applicant.id }}, 角色: {{ detailData.applicant.role }})
          </a-descriptions-item>
          <a-descriptions-item label="申请时间" :span="2">{{ detailData.applied_at }}</a-descriptions-item>
        </a-descriptions>

        <!-- 拒绝原因 (如已拒绝) -->
        <a-alert v-if="detailData.reject_reason" type="error" :message="`拒绝原因: ${detailData.reject_reason}`" style="margin-bottom: 16px" />

        <!-- 操作按钮 -->
        <div v-if="detailData.application_status === 'pending_review'" style="display: flex; gap: 12px; justify-content: flex-end">
          <a-popconfirm title="确认通过此申请？审核通过后将开通工作室并升级角色为教练" @confirm="handleApprove(detailData.tenant_id)">
            <a-button type="primary" :loading="approving">通过</a-button>
          </a-popconfirm>
          <a-button danger @click="showRejectForm = true">拒绝</a-button>
        </div>

        <!-- 拒绝表单 -->
        <div v-if="showRejectForm" style="margin-top: 12px">
          <a-textarea v-model:value="rejectReason" :rows="3" placeholder="请填写拒绝原因" />
          <div style="display: flex; gap: 8px; justify-content: flex-end; margin-top: 8px">
            <a-button @click="showRejectForm = false">取消</a-button>
            <a-button danger :loading="rejecting" @click="handleReject(detailData.tenant_id)" :disabled="!rejectReason.trim()">确认拒绝</a-button>
          </div>
        </div>
      </template>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import request from '../../api/request'
import ListCard from '@/components/core/ListCard.vue'

const activeTab = ref('pending_review')
const loading = ref(false)
const applications = ref<any[]>([])
const pagination = reactive({ current: 1, pageSize: 20, total: 0 })
const stats = reactive({ pending: 0, approved: 0, rejected: 0 })

const showDetail = ref(false)
const detailData = ref<any>(null)
const detailLoading = ref(false)
const showRejectForm = ref(false)
const rejectReason = ref('')
const approving = ref(false)
const rejecting = ref(false)

// columns removed — using ListCard layout

function statusColor(s: string) {
  return { pending_review: 'orange', approved: 'green', rejected: 'red' }[s] || 'default'
}

function statusLabel(s: string) {
  return { pending_review: '待审核', approved: '已通过', rejected: '已拒绝' }[s] || s
}

async function fetchApplications() {
  loading.value = true
  try {
    const statusParam = activeTab.value === 'all' ? undefined : activeTab.value
    const params: any = {
      skip: (pagination.current - 1) * pagination.pageSize,
      limit: pagination.pageSize,
    }
    if (statusParam) params.status = statusParam
    const res = await request.get('/v1/expert-registration/admin/applications', { params })
    applications.value = res.data?.data?.items || []
    pagination.total = res.data?.data?.total || 0
  } catch {
    applications.value = []
  } finally {
    loading.value = false
  }
  // 统计
  fetchStats()
}

async function fetchStats() {
  try {
    const [pRes, aRes, rRes] = await Promise.all([
      request.get('/v1/expert-registration/admin/applications', { params: { status: 'pending_review', limit: 1 } }),
      request.get('/v1/expert-registration/admin/applications', { params: { status: 'approved', limit: 1 } }),
      request.get('/v1/expert-registration/admin/applications', { params: { status: 'rejected', limit: 1 } }),
    ])
    stats.pending = pRes.data?.data?.total || 0
    stats.approved = aRes.data?.data?.total || 0
    stats.rejected = rRes.data?.data?.total || 0
  } catch {}
}

async function openDetail(record: any) {
  showDetail.value = true
  showRejectForm.value = false
  rejectReason.value = ''
  detailLoading.value = true
  try {
    const res = await request.get(`/v1/expert-registration/admin/applications/${record.tenant_id}`)
    detailData.value = res.data?.data || record
  } catch {
    detailData.value = record
  } finally {
    detailLoading.value = false
  }
}

async function handleApprove(tenantId: string) {
  approving.value = true
  try {
    await request.post(`/v1/expert-registration/admin/applications/${tenantId}/approve`)
    message.success('审核通过，工作室已开通')
    showDetail.value = false
    fetchApplications()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '操作失败')
  } finally {
    approving.value = false
  }
}

async function handleReject(tenantId: string) {
  if (!rejectReason.value.trim()) {
    message.warning('请填写拒绝原因')
    return
  }
  rejecting.value = true
  try {
    await request.post(`/v1/expert-registration/admin/applications/${tenantId}/reject`, {
      reason: rejectReason.value.trim(),
    })
    message.success('已拒绝')
    showDetail.value = false
    fetchApplications()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '操作失败')
  } finally {
    rejecting.value = false
  }
}

// handleTableChange removed — standalone a-pagination handles page changes

onMounted(() => {
  fetchApplications()
})
</script>

<style scoped>
.expert-application-review {
  padding: 0;
}

.list-card-container { display: flex; flex-direction: column; gap: 10px; }
</style>
