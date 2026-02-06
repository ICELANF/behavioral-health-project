<template>
  <div class="my-reviews">
    <div class="page-header">
      <h2>我的审核</h2>
    </div>

    <!-- Stats -->
    <a-row :gutter="16" style="margin-bottom: 16px">
      <a-col :span="6"><a-card size="small"><a-statistic title="待审核" :value="pendingQueue.length" value-style="color: #d46b08" /></a-card></a-col>
      <a-col :span="6"><a-card size="small"><a-statistic title="本月已审" :value="32" value-style="color: #3f8600" /></a-card></a-col>
      <a-col :span="6"><a-card size="small"><a-statistic title="通过率" :value="78" suffix="%" /></a-card></a-col>
      <a-col :span="6"><a-card size="small"><a-statistic title="平均审核时长" :value="1.5" suffix="天" /></a-card></a-col>
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
import { ref } from 'vue'
import { message } from 'ant-design-vue'

const activeTab = ref('pending')

const typeLabels: Record<string, string> = { promotion: '晋级审核', content: '内容审核', case: '案例审核' }
const typeColors: Record<string, string> = { promotion: 'purple', content: 'blue', case: 'orange' }

const pendingQueue = ref([
  { id: '1', type: 'promotion', title: '王教练申请L3晋级', description: '已完成所有必修课程，干预成功率74%，申请高级教练认证', submitter: '王教练', submitDate: '2025-01-14', urgency: 'normal' },
  { id: '2', type: 'content', title: '《慢病自我管理》课程审核', description: '新增4个章节，涵盖饮食、运动、用药、心理四个维度', submitter: '张专家', submitDate: '2025-01-13', urgency: 'normal' },
  { id: '3', type: 'case', title: '高风险案例复核', description: '患者周明连续5天未活跃，PSS-10评分28分（高压力）', submitter: '李教练', submitDate: '2025-01-12', urgency: 'high' },
])

const reviewHistory = ref([
  { id: 'h1', type: 'promotion', title: '张教练L2晋级', submitter: '张教练', reviewDate: '2025-01-10', approved: true, comment: '各项指标达标' },
  { id: 'h2', type: 'content', title: '《动机访谈实践》审核', submitter: '王专家', reviewDate: '2025-01-08', approved: true, comment: '内容质量优秀' },
  { id: 'h3', type: 'case', title: '中风险案例复核', submitter: '赵教练', reviewDate: '2025-01-06', approved: false, comment: '干预方案需要调整，建议增加随访频率' },
  { id: 'h4', type: 'promotion', title: '赵教练L1晋级', submitter: '赵教练', reviewDate: '2025-01-04', approved: false, comment: '考试未通过，建议重考后再申请' },
])

const historyColumns = [
  { title: '类型', key: 'type', width: 100 },
  { title: '标题', dataIndex: 'title' },
  { title: '提交人', dataIndex: 'submitter', width: 80 },
  { title: '审核日期', dataIndex: 'reviewDate', width: 110 },
  { title: '结果', key: 'result', width: 80 },
  { title: '意见', dataIndex: 'comment', ellipsis: true },
]

const typeStats = ref([
  { type: 'promotion', label: '晋级审核', count: 12, percent: 38, color: '#722ed1' },
  { type: 'content', label: '内容审核', count: 15, percent: 47, color: '#1890ff' },
  { type: 'case', label: '案例审核', count: 5, percent: 15, color: '#fa8c16' },
])

const monthlyStats = ref([
  { month: '1月', total: 32, approved: 25, rejected: 7 },
  { month: '12月', total: 28, approved: 22, rejected: 6 },
  { month: '11月', total: 25, approved: 20, rejected: 5 },
])

const approveItem = (item: any) => {
  pendingQueue.value = pendingQueue.value.filter(i => i.id !== item.id)
  message.success('已通过审核')
}

const rejectItem = (item: any) => {
  pendingQueue.value = pendingQueue.value.filter(i => i.id !== item.id)
  message.info('已驳回')
}

const viewDetail = (item: any) => {
  message.info(`查看详情: ${item.title}`)
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
