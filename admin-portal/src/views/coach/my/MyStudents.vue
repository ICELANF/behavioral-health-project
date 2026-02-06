<template>
  <div class="my-students">
    <div class="page-header">
      <h2>我的学员</h2>
      <div class="header-actions">
        <a-input-search v-model:value="searchText" placeholder="搜索学员" style="width: 200px" @search="loadStudents" allowClear />
        <a-select v-model:value="viewMode" style="width: 120px">
          <a-select-option value="kanban">看板视图</a-select-option>
          <a-select-option value="list">列表视图</a-select-option>
        </a-select>
      </div>
    </div>

    <!-- Stats -->
    <a-row :gutter="16" style="margin-bottom: 16px">
      <a-col :span="6">
        <a-card size="small"><a-statistic title="总学员数" :value="allStudents.length" :loading="loading" /></a-card>
      </a-col>
      <a-col :span="6">
        <a-card size="small"><a-statistic title="高风险" :value="riskCounts.high" value-style="color: #cf1322" :loading="loading" /></a-card>
      </a-col>
      <a-col :span="6">
        <a-card size="small"><a-statistic title="本周活跃" :value="activeCounts" value-style="color: #3f8600" :loading="loading" /></a-card>
      </a-col>
      <a-col :span="6">
        <a-card size="small"><a-statistic title="待跟进" :value="pendingFollowUp" value-style="color: #d46b08" :loading="loading" /></a-card>
      </a-col>
    </a-row>

    <!-- Kanban View -->
    <div v-if="viewMode === 'kanban'" class="kanban-board">
      <div v-for="group in kanbanGroups" :key="group.key" class="kanban-column">
        <div class="column-header" :style="{ borderColor: group.color }">
          <span class="column-title">{{ group.title }}</span>
          <span class="column-count">{{ group.students.length }}</span>
        </div>
        <div class="column-body">
          <div v-for="s in group.students" :key="s.id" class="student-card">
            <div class="student-top">
              <a-avatar :size="32" :style="{ background: group.color }">{{ s.name[0] }}</a-avatar>
              <div class="student-info">
                <span class="student-name">{{ s.name }}</span>
                <span class="student-stage">{{ s.stage }}</span>
              </div>
              <a-tag :color="riskColorMap[s.risk]" size="small">{{ s.risk }}</a-tag>
            </div>
            <div class="student-metrics">
              <span>完成率 {{ s.completion }}%</span>
              <span>活跃{{ s.activeDays }}天</span>
            </div>
            <div class="student-actions">
              <a-button size="small" type="link" @click="$router.push(`/coach/student-assessment/${s.id}`)">查看</a-button>
              <a-button size="small" type="link">消息</a-button>
              <a-button size="small" type="link">测评</a-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- List View -->
    <a-card v-if="viewMode === 'list'">
      <a-table :dataSource="filteredStudents" :columns="listColumns" rowKey="id" size="small" :loading="loading">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <div style="display: flex; align-items: center; gap: 8px">
              <a-avatar :size="28">{{ record.name[0] }}</a-avatar>
              <span>{{ record.name }}</span>
            </div>
          </template>
          <template v-if="column.key === 'risk'">
            <a-tag :color="riskColorMap[record.risk]">{{ record.risk }}</a-tag>
          </template>
          <template v-if="column.key === 'completion'">
            <a-progress :percent="record.completion" size="small" :stroke-color="record.completion >= 80 ? '#52c41a' : '#faad14'" />
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a @click="$router.push(`/coach/student-assessment/${record.id}`)">查看轨迹</a>
              <a>发消息</a>
              <a>安排测评</a>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import request from '@/api/request'

const searchText = ref('')
const viewMode = ref('kanban')
const loading = ref(false)

const riskColorMap: Record<string, string> = { '高风险': 'red', '中风险': 'orange', '低风险': 'green' }

const stageMap: Record<string, { label: string; group: string }> = {
  precontemplation: { label: '前思考期', group: 'precontemplation' },
  contemplation: { label: '思考期', group: 'contemplation' },
  preparation: { label: '准备期', group: 'preparation' },
  action: { label: '行动期', group: 'action' },
  maintenance: { label: '维持期', group: 'maintenance' },
}

const allStudents = ref<any[]>([])

const loadStudents = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (searchText.value) params.search = searchText.value
    const { data } = await request.get('/v1/coach/students', { params })
    allStudents.value = (data.students || []).map((s: any) => {
      const profile = s.profile || {}
      const ttmStage = profile.ttm_stage || 'contemplation'
      const stageInfo = stageMap[ttmStage] || { label: ttmStage, group: 'contemplation' }
      const riskMap: Record<string, string> = { R0: '低风险', R1: '低风险', R2: '中风险', R3: '高风险', R4: '高风险' }
      return {
        id: s.id,
        name: s.full_name || s.username,
        stage: stageInfo.label,
        risk: riskMap[s.latest_risk || 'R0'] || '低风险',
        completion: s.adherence_rate || 0,
        activeDays: s.active_days || 0,
        lastActive: s.last_active || '-',
        group: stageInfo.group,
      }
    })
  } catch (e: any) {
    console.error('加载学员列表失败:', e)
    // Fallback mock data
    if (!allStudents.value.length) {
      allStudents.value = [
        { id: '1', name: '张伟', stage: '行动期', risk: '低风险', completion: 85, activeDays: 6, lastActive: '今天', group: 'action' },
        { id: '2', name: '李娜', stage: '思考期', risk: '中风险', completion: 45, activeDays: 3, lastActive: '昨天', group: 'contemplation' },
        { id: '3', name: '王芳', stage: '前思考期', risk: '高风险', completion: 15, activeDays: 1, lastActive: '3天前', group: 'precontemplation' },
        { id: '4', name: '赵强', stage: '准备期', risk: '中风险', completion: 60, activeDays: 4, lastActive: '今天', group: 'preparation' },
        { id: '5', name: '刘洋', stage: '维持期', risk: '低风险', completion: 92, activeDays: 7, lastActive: '今天', group: 'maintenance' },
        { id: '6', name: '陈静', stage: '行动期', risk: '中风险', completion: 70, activeDays: 5, lastActive: '今天', group: 'action' },
      ]
    }
  } finally {
    loading.value = false
  }
}

const filteredStudents = computed(() => {
  if (!searchText.value) return allStudents.value
  return allStudents.value.filter(s => s.name.includes(searchText.value))
})

const riskCounts = computed(() => {
  const counts = { high: 0, medium: 0, low: 0 }
  allStudents.value.forEach(s => {
    if (s.risk === '高风险') counts.high++
    else if (s.risk === '中风险') counts.medium++
    else counts.low++
  })
  return counts
})

const activeCounts = computed(() => allStudents.value.filter(s => s.activeDays >= 3).length)
const pendingFollowUp = computed(() => allStudents.value.filter(s => s.activeDays <= 1).length)

const kanbanGroups = computed(() => {
  const groups = [
    { key: 'precontemplation', title: '前思考期', color: '#ff4d4f' },
    { key: 'contemplation', title: '思考期', color: '#fa8c16' },
    { key: 'preparation', title: '准备期', color: '#fadb14' },
    { key: 'action', title: '行动期', color: '#52c41a' },
    { key: 'maintenance', title: '维持期', color: '#1890ff' },
  ]
  return groups.map(g => ({
    ...g,
    students: filteredStudents.value.filter(s => s.group === g.key)
  }))
})

const listColumns = [
  { title: '学员', key: 'name', width: 150 },
  { title: '阶段', dataIndex: 'stage', width: 100 },
  { title: '风险', key: 'risk', width: 80 },
  { title: '完成率', key: 'completion', width: 150 },
  { title: '活跃天数', dataIndex: 'activeDays', width: 80 },
  { title: '最近活跃', dataIndex: 'lastActive', width: 100 },
  { title: '操作', key: 'action', width: 200 },
]

onMounted(() => {
  loadStudents()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; }
.header-actions { display: flex; gap: 8px; }

.kanban-board { display: flex; gap: 12px; overflow-x: auto; padding-bottom: 8px; }
.kanban-column { min-width: 220px; flex: 1; background: #fafafa; border-radius: 8px; }
.column-header { padding: 10px 12px; font-weight: 600; font-size: 14px; border-top: 3px solid; display: flex; justify-content: space-between; align-items: center; }
.column-count { background: #e8e8e8; padding: 1px 8px; border-radius: 10px; font-size: 12px; font-weight: 400; }
.column-body { padding: 8px; max-height: 500px; overflow-y: auto; }
.student-card { background: #fff; border: 1px solid #f0f0f0; border-radius: 6px; padding: 10px; margin-bottom: 8px; }
.student-top { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.student-info { flex: 1; }
.student-name { display: block; font-size: 13px; font-weight: 500; }
.student-stage { font-size: 11px; color: #999; }
.student-metrics { display: flex; gap: 12px; font-size: 11px; color: #666; margin-bottom: 6px; }
.student-actions { display: flex; gap: 4px; }
</style>
