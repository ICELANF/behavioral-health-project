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
            <a-tag :color="typeColors[item.type] || 'default'">{{ typeLabels[item.type] || item.type }}</a-tag>
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
              <a-tag :color="typeColors[record.type] || 'default'">{{ typeLabels[record.type] || record.type }}</a-tag>
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
              <a-empty v-if="typeStats.length === 0" description="暂无统计" />
            </a-card>
          </a-col>
          <a-col :span="12">
            <a-card title="月度审核量" size="small">
              <div v-for="m in monthlyStats" :key="m.month" class="stat-row">
                <span class="stat-label">{{ m.month }}</span>
                <div class="stat-bars">
                  <div class="stat-bar approved" :style="{ width: (m.approved / (m.total || 1) * 100) + '%' }"></div>
                  <div class="stat-bar rejected" :style="{ width: (m.rejected / (m.total || 1) * 100) + '%' }"></div>
                </div>
                <span class="stat-count">{{ m.total }}</span>
              </div>
              <a-empty v-if="monthlyStats.length === 0" description="暂无统计" />
            </a-card>
          </a-col>
        </a-row>
      </a-tab-pane>
    </a-tabs>

    <!-- Detail Drawer -->
    <a-drawer v-model:open="detailVisible" :title="detailItem?.title || '审核详情'" width="500">
      <template v-if="detailItem">
        <a-descriptions :column="1" bordered size="small">
          <a-descriptions-item label="类型">
            <a-tag :color="typeColors[detailItem.type] || 'default'">{{ typeLabels[detailItem.type] || detailItem.type }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="提交人">{{ detailItem.submitter }}</a-descriptions-item>
          <a-descriptions-item label="提交时间">{{ detailItem.submitDate }}</a-descriptions-item>
          <a-descriptions-item label="内容">
            <pre style="white-space: pre-wrap; margin: 0; font-family: inherit">{{ detailItem.description }}</pre>
          </a-descriptions-item>
        </a-descriptions>
        <div style="margin-top: 16px; display: flex; gap: 8px">
          <a-button type="primary" @click="approveItem(detailItem); detailVisible = false">通过</a-button>
          <a-button danger @click="rejectItem(detailItem); detailVisible = false">驳回</a-button>
        </div>
      </template>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { expertFlywheelApi } from '@/api/expert-api'
import request from '@/api/request'

const activeTab = ref('pending')

const typeLabels: Record<string, string> = {
  promotion: '晋级审核', content: '内容审核', case: '案例审核',
  push: '推送审批', supervision: '督导安排', safety: '安全审计',
  prescription: '处方审计', ai_dialogue: 'AI对话审计', agent_behavior: 'Agent审计',
}
const typeColors: Record<string, string> = {
  promotion: 'purple', content: 'blue', case: 'orange',
  push: 'cyan', supervision: 'gold', safety: 'red',
  prescription: 'magenta', ai_dialogue: 'geekblue', agent_behavior: 'volcano',
}
const typeColorMap: Record<string, string> = {
  promotion: '#722ed1', content: '#1890ff', case: '#fa8c16',
  push: '#13c2c2', supervision: '#faad14', safety: '#f5222d',
}

interface ReviewItem {
  id: string; type: string; title: string; description: string;
  submitter: string; submitDate: string; urgency: string;
  /** 原始数据源，用于审批操作 */
  _source: 'audit' | 'push' | 'promotion';
  _rawId: number | string;
}

const pendingQueue = ref<ReviewItem[]>([])
const reviewHistory = ref<any[]>([])
const detailVisible = ref(false)
const detailItem = ref<ReviewItem | null>(null)

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

const loadReviewData = async () => {
  const allPending: ReviewItem[] = []
  const allHistory: any[] = []

  // ── 数据源 1: expert audit-queue (AI安全审计) ──
  const [pendingRes, historyRes] = await Promise.allSettled([
    expertFlywheelApi.getAuditQueue(),
    expertFlywheelApi.getAuditQueue({ status: 'completed' } as any),
  ])
  if (pendingRes.status === 'fulfilled') {
    for (const r of pendingRes.value.items || []) {
      allPending.push({
        id: `audit-${r.id}`, type: r.type || 'safety', title: r.title || '',
        description: r.description || '', submitter: r.userName || r.submitter || '',
        submitDate: r.time || '', urgency: r.risk === 'critical' || r.risk === 'high' ? 'high' : 'normal',
        _source: 'audit', _rawId: r.id,
      })
    }
  }
  if (historyRes.status === 'fulfilled') {
    for (const r of historyRes.value.items || []) {
      allHistory.push({
        id: `audit-${r.id}`, type: r.type || 'safety', title: r.title || '',
        submitter: r.userName || '', reviewDate: r.time || '',
        approved: r.verdict === 'pass' || r.approved || false,
        comment: r.note || r.comment || '',
      })
    }
  }

  // ── 数据源 2: coach push-queue (推送消息审批) ──
  try {
    const [qPending, qDone] = await Promise.allSettled([
      request.get('v1/coach/push-queue', { params: { status: 'pending', page_size: 50 } }),
      request.get('v1/coach/push-queue', { params: { status: 'sent', page_size: 50 } }),
    ])
    if (qPending.status === 'fulfilled') {
      for (const item of qPending.value.data?.items || []) {
        const isSupervision = item.content?.startsWith('[督导安排]')
        allPending.push({
          id: `push-${item.id}`,
          type: isSupervision ? 'supervision' : 'push',
          title: item.title || '推送消息',
          description: item.content || '',
          submitter: `教练#${item.coach_id}`,
          submitDate: item.created_at || '',
          urgency: item.priority === 'high' ? 'high' : 'normal',
          _source: 'push', _rawId: item.id,
        })
      }
    }
    if (qDone.status === 'fulfilled') {
      for (const item of qDone.value.data?.items || []) {
        allHistory.push({
          id: `push-${item.id}`, type: 'push', title: item.title || '推送消息',
          submitter: `教练#${item.coach_id}`, reviewDate: item.reviewed_at || item.sent_at || '',
          approved: true, comment: item.coach_note || '',
        })
      }
    }
  } catch { /* optional */ }

  // ── 数据源 3: promotion applications (晋级申请审核) ──
  try {
    const [pPending, pDone] = await Promise.allSettled([
      request.get('v1/promotion/applications', { params: { status: 'pending' } }),
      request.get('v1/promotion/applications', { params: { status: 'approved' } }),
    ])
    if (pPending.status === 'fulfilled') {
      for (const a of pPending.value.data?.applications || []) {
        allPending.push({
          id: `promo-${a.application_id}`, type: 'promotion',
          title: `${a.full_name || a.username || ''}: ${a.current_level} → ${a.target_level}`,
          description: `晋级申请 — 当前等级 ${a.current_level}，目标等级 ${a.target_level}`,
          submitter: a.full_name || a.username || '',
          submitDate: a.applied_at || '', urgency: 'normal',
          _source: 'promotion', _rawId: a.application_id,
        })
      }
    }
    if (pDone.status === 'fulfilled') {
      for (const a of pDone.value.data?.applications || []) {
        allHistory.push({
          id: `promo-${a.application_id}`, type: 'promotion',
          title: `${a.full_name || a.username || ''}: ${a.current_level} → ${a.target_level}`,
          submitter: a.full_name || '', reviewDate: a.reviewed_at || '',
          approved: true, comment: a.reviewer_comment || '',
        })
      }
    }
  } catch { /* optional */ }

  pendingQueue.value = allPending
  reviewHistory.value = allHistory

  // Build type stats
  const counts: Record<string, number> = {}
  const totalAll = allPending.length + allHistory.length || 1
  ;[...allPending, ...allHistory].forEach(r => { counts[r.type] = (counts[r.type] || 0) + 1 })
  typeStats.value = Object.entries(counts).map(([type, count]) => ({
    type, label: typeLabels[type] || type, count,
    percent: Math.round(count / totalAll * 100), color: typeColorMap[type] || '#999',
  }))

  // Build monthly stats
  const monthly: Record<string, { total: number; approved: number; rejected: number }> = {}
  allHistory.forEach((r: any) => {
    const d = r.reviewDate || ''
    const m = d ? d.substring(0, 7) : '未知'
    if (!monthly[m]) monthly[m] = { total: 0, approved: 0, rejected: 0 }
    monthly[m].total++
    if (r.approved) monthly[m].approved++; else monthly[m].rejected++
  })
  monthlyStats.value = Object.entries(monthly).sort((a, b) => b[0].localeCompare(a[0])).slice(0, 6)
    .map(([month, s]) => ({ month, ...s }))
}

onMounted(loadReviewData)

const approveItem = async (item: ReviewItem) => {
  try {
    if (item._source === 'audit') {
      await expertFlywheelApi.submitVerdict(item._rawId as string, { verdict: 'pass', score: 100, issues: [], note: '' })
    } else if (item._source === 'push') {
      await request.post(`v1/coach/push-queue/${item._rawId}/approve`)
    } else if (item._source === 'promotion') {
      await request.post(`v1/promotion/applications/${item._rawId}/approve`)
    }
    pendingQueue.value = pendingQueue.value.filter(i => i.id !== item.id)
    message.success('已通过审核')
  } catch (e) {
    console.error('审核失败:', e)
    message.error('操作失败，请重试')
  }
}

const rejectItem = async (item: ReviewItem) => {
  try {
    if (item._source === 'audit') {
      await expertFlywheelApi.submitVerdict(item._rawId as string, { verdict: 'block', score: 0, issues: ['rejected'], note: '' })
    } else if (item._source === 'push') {
      await request.post(`v1/coach/push-queue/${item._rawId}/reject`)
    } else if (item._source === 'promotion') {
      await request.post(`v1/promotion/applications/${item._rawId}/reject`)
    }
    pendingQueue.value = pendingQueue.value.filter(i => i.id !== item.id)
    message.info('已驳回')
  } catch (e) {
    console.error('驳回失败:', e)
    message.error('操作失败，请重试')
  }
}

const viewDetail = (item: ReviewItem) => {
  detailItem.value = item
  detailVisible.value = true
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
.review-desc { font-size: 13px; color: #666; margin: 0 0 8px; white-space: pre-line; }
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
