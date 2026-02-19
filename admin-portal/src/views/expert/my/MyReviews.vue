<template>
  <div class="my-reviews">
    <div class="page-header">
      <h2>我的审核</h2>
    </div>

    <!-- Stats -->
    <a-row :gutter="16" style="margin-bottom: 16px">
      <a-col :span="6"><a-card size="small"><a-statistic title="待审核" :value="pendingQueue.length" value-style="color: #d46b08" /></a-card></a-col>
      <a-col :span="6"><a-card size="small"><a-statistic title="本月已审" :value="monthlyReviewed" value-style="color: #3f8600" /></a-card></a-col>
      <a-col :span="6"><a-card size="small"><a-statistic title="通过率" :value="approvalRate" suffix="%" /></a-card></a-col>
      <a-col :span="6"><a-card size="small"><a-statistic title="平均审核时长" :value="avgReviewDays" suffix="天" /></a-card></a-col>
    </a-row>

    <!-- Tabs -->
    <a-tabs v-model:activeKey="activeTab">
      <!-- Pending Queue -->
      <a-tab-pane key="pending" :tab="`待审核 (${pendingQueue.length})`">
        <div v-for="item in pendingQueue" :key="item.id" class="review-card pending">
          <div class="review-header">
            <a-tag :color="typeColors[item.type]">{{ typeLabels[item.type] }}</a-tag>
            <span class="review-title">{{ item.title }}</span>
            <span class="review-date">提交于 {{ item.submitDate }}</span>
          </div>
          <p class="review-desc">{{ item.description }}</p>
          <div class="review-submitter">
            <span>提交人: {{ item.submitter }}</span>
            <span v-if="item.urgency === 'high'" class="urgency high">紧急</span>
          </div>
          <div class="review-actions">
            <a-button type="primary" size="small" @click="approveItem(item)">通过</a-button>
            <a-button size="small" danger @click="rejectItem(item)">驳回</a-button>
            <a-button size="small" @click="viewDetail(item)">查看详情</a-button>
          </div>
        </div>
        <a-empty v-if="pendingQueue.length === 0" description="暂无待审核项" />
      </a-tab-pane>

      <!-- History -->
      <a-tab-pane key="history" tab="审核历史">
        <a-table :dataSource="reviewHistory" :columns="historyColumns" rowKey="id" size="small">
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'type'">
              <a-tag :color="typeColors[record.type]">{{ typeLabels[record.type] }}</a-tag>
            </template>
            <template v-if="column.key === 'result'">
              <a-tag :color="record.approved ? 'green' : 'red'">{{ record.approved ? '通过' : '驳回' }}</a-tag>
            </template>
          </template>
        </a-table>
      </a-tab-pane>

      <!-- Statistics -->
      <a-tab-pane key="stats" tab="统计面板">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-card title="审核类型分布" size="small">
              <div v-for="stat in typeStats" :key="stat.type" class="stat-row">
                <span class="stat-label">{{ stat.label }}</span>
                <a-progress :percent="stat.percent" size="small" :stroke-color="stat.color" />
                <span class="stat-count">{{ stat.count }}</span>
              </div>
            </a-card>
          </a-col>
          <a-col :span="12">
            <a-card title="月度审核量" size="small">
              <div v-for="m in monthlyStats" :key="m.month" class="stat-row">
                <span class="stat-label">{{ m.month }}</span>
                <div class="stat-bars">
                  <div class="stat-bar approved" :style="{ width: (m.approved / m.total * 100) + '%' }"></div>
                  <div class="stat-bar rejected" :style="{ width: (m.rejected / m.total * 100) + '%' }"></div>
                </div>
                <span class="stat-count">{{ m.total }}</span>
              </div>
            </a-card>
          </a-col>
        </a-row>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { expertApi } from '@/api/expert-api'

const router = useRouter()

const activeTab = ref('pending')

const typeLabels: Record<string, string> = { promotion: '晋级审核', content: '内容审核', case: '案例审核' }
const typeColors: Record<string, string> = { promotion: 'purple', content: 'blue', case: 'orange' }

const pendingQueue = ref<any[]>([])
const reviewHistory = ref<any[]>([])

const monthlyReviewed = computed(() => reviewHistory.value.length)
const approvalRate = computed(() => {
  if (reviewHistory.value.length === 0) return 0
  return Math.round(reviewHistory.value.filter(r => r.approved).length / reviewHistory.value.length * 100)
})
const avgReviewDays = ref(0)

const historyColumns = [
  { title: '类型', key: 'type', width: 100 },
  { title: '标题', dataIndex: 'title' },
  { title: '提交人', dataIndex: 'submitter', width: 80 },
  { title: '审核日期', dataIndex: 'reviewDate', width: 110 },
  { title: '结果', key: 'result', width: 80 },
  { title: '意见', dataIndex: 'comment', ellipsis: true },
]

const typeStats = ref<{ type: string; label: string; count: number; percent: number; color: string }[]>([])
const monthlyStats = ref<{ month: string; total: number; approved: number; rejected: number }[]>([])

const typeColorMap: Record<string, string> = { promotion: '#722ed1', content: '#1890ff', case: '#fa8c16' }

const loadReviewData = async () => {
  const expertId = localStorage.getItem('admin_user_id') || '0'
  const [pendingRes, historyRes] = await Promise.allSettled([
    expertApi.getReviewQueue(expertId),
    expertApi.getReviewHistory(expertId),
  ])
  if (pendingRes.status === 'fulfilled') {
    pendingQueue.value = (pendingRes.value.items || pendingRes.value || []).map((r: any) => ({
      id: String(r.id), type: r.type || 'case', title: r.title || '',
      description: r.description || '', submitter: r.submitter || r.coach_name || '',
      submitDate: r.submit_date || r.submitDate || '', urgency: r.urgency || 'normal',
    }))
  } else {
    console.error('加载待审核列表失败:', pendingRes.reason)
  }
  if (historyRes.status === 'fulfilled') {
    const items = historyRes.value.items || historyRes.value || []
    reviewHistory.value = items.map((r: any) => ({
      id: String(r.id), type: r.type || 'case', title: r.title || '',
      submitter: r.submitter || '', reviewDate: r.review_date || r.reviewDate || '',
      approved: r.approved ?? false, comment: r.comment || '',
    }))
    avgReviewDays.value = historyRes.value.avg_review_days ?? 0
    // Build type stats from history
    const counts: Record<string, number> = {}
    const total = items.length || 1
    items.forEach((r: any) => { counts[r.type] = (counts[r.type] || 0) + 1 })
    typeStats.value = Object.entries(counts).map(([type, count]) => ({
      type, label: typeLabels[type] || type, count,
      percent: Math.round(count / total * 100), color: typeColorMap[type] || '#999',
    }))
    // Build monthly stats from history
    const monthly: Record<string, { total: number; approved: number; rejected: number }> = {}
    items.forEach((r: any) => {
      const d = r.review_date || r.reviewDate || ''
      const m = d ? d.substring(0, 7) : '未知'
      if (!monthly[m]) monthly[m] = { total: 0, approved: 0, rejected: 0 }
      monthly[m].total++
      if (r.approved) monthly[m].approved++; else monthly[m].rejected++
    })
    monthlyStats.value = Object.entries(monthly).sort((a, b) => b[0].localeCompare(a[0])).slice(0, 6)
      .map(([month, s]) => ({ month, ...s }))
  } else {
    console.error('加载审核历史失败:', historyRes.reason)
  }
}

onMounted(loadReviewData)

const approveItem = async (item: any) => {
  try {
    await expertApi.submitReview(item.id, { approved: true, comment: '' })
    pendingQueue.value = pendingQueue.value.filter(i => i.id !== item.id)
    message.success('已通过审核')
  } catch (e) {
    console.error('审核失败:', e)
    message.error('操作失败，请重试')
  }
}

const rejectItem = async (item: any) => {
  try {
    await expertApi.submitReview(item.id, { approved: false, comment: '' })
    pendingQueue.value = pendingQueue.value.filter(i => i.id !== item.id)
    message.info('已驳回')
  } catch (e) {
    console.error('驳回失败:', e)
    message.error('操作失败，请重试')
  }
}

const viewDetail = (item: any) => {
  router.push(`/content/review?id=${item.id}`)
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; }

.review-card { background: #fff; border: 1px solid #f0f0f0; border-radius: 8px; padding: 16px; margin-bottom: 12px; }
.review-card.pending { border-left: 3px solid #d46b08; }
.review-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.review-title { font-weight: 600; font-size: 14px; flex: 1; }
.review-date { font-size: 12px; color: #999; }
.review-desc { font-size: 13px; color: #666; margin: 0 0 8px; }
.review-submitter { font-size: 12px; color: #999; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
.urgency.high { color: #cf1322; font-weight: 600; background: #fff1f0; padding: 1px 6px; border-radius: 3px; }
.review-actions { display: flex; gap: 8px; }

.stat-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.stat-label { min-width: 60px; font-size: 13px; color: #666; }
.stat-count { min-width: 30px; text-align: right; font-size: 13px; color: #999; }
.stat-bars { flex: 1; height: 16px; display: flex; border-radius: 4px; overflow: hidden; background: #f5f5f5; }
.stat-bar.approved { background: #52c41a; }
.stat-bar.rejected { background: #ff4d4f; }
</style>
