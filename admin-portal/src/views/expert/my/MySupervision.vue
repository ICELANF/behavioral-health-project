<template>
  <div class="my-supervision">
    <div class="page-header">
      <h2>我的督导</h2>
      <a-button type="primary" @click="showScheduleModal = true">安排新督导</a-button>
    </div>

    <!-- Coach overview -->
    <a-row :gutter="16" style="margin-bottom: 16px">
      <a-col :span="6"><a-card size="small"><a-statistic title="被督导教练" :value="coaches.length" /></a-card></a-col>
      <a-col :span="6"><a-card size="small"><a-statistic title="本月督导次数" :value="12" /></a-card></a-col>
      <a-col :span="6"><a-card size="small"><a-statistic title="平均教练评分" :value="4.3" :precision="1" value-style="color: #3f8600" /></a-card></a-col>
      <a-col :span="6"><a-card size="small"><a-statistic title="待处理事项" :value="3" value-style="color: #cf1322" /></a-card></a-col>
    </a-row>

    <!-- Coach Performance Comparison -->
    <a-card title="教练绩效对比" style="margin-bottom: 16px">
      <a-table :dataSource="coaches" :columns="coachColumns" rowKey="id" size="small">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <div style="display: flex; align-items: center; gap: 8px">
              <a-avatar :size="28" :style="{ background: record.color }">{{ record.name[0] }}</a-avatar>
              <div>
                <div style="font-weight: 500">{{ record.name }}</div>
                <div style="font-size: 11px; color: #999">{{ record.level }}</div>
              </div>
            </div>
          </template>
          <template v-if="column.key === 'success'">
            <a-progress :percent="record.successRate" size="small" :stroke-color="record.successRate >= 70 ? '#52c41a' : '#faad14'" />
          </template>
          <template v-if="column.key === 'score'">
            <a-rate :value="record.score" disabled allow-half :count="5" style="font-size: 12px" />
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a>查看详情</a>
              <a>安排督导</a>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- Supervision Sessions -->
    <a-card title="督导会话记录">
      <div v-for="session in sessions" :key="session.id" class="session-item">
        <div class="session-header">
          <span class="session-coach">{{ session.coach }}</span>
          <a-tag :color="session.status === '已完成' ? 'green' : 'blue'">{{ session.status }}</a-tag>
          <span class="session-date">{{ session.date }}</span>
        </div>
        <p class="session-topic">主题: {{ session.topic }}</p>
        <p v-if="session.notes" class="session-notes">备注: {{ session.notes }}</p>
      </div>
    </a-card>

    <!-- Schedule Modal -->
    <a-modal v-model:open="showScheduleModal" title="安排新督导" @ok="scheduleSupervision" okText="确认">
      <a-form layout="vertical">
        <a-form-item label="选择教练">
          <a-select v-model:value="newSession.coachId" placeholder="请选择" style="width: 100%">
            <a-select-option v-for="c in coaches" :key="c.id" :value="c.id">{{ c.name }} ({{ c.level }})</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="督导主题">
          <a-input v-model:value="newSession.topic" placeholder="输入督导主题" />
        </a-form-item>
        <a-form-item label="日期时间">
          <a-date-picker v-model:value="newSession.date" show-time placeholder="选择时间" style="width: 100%" />
        </a-form-item>
        <a-form-item label="备注">
          <a-textarea v-model:value="newSession.notes" :rows="3" placeholder="其他备注" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { message } from 'ant-design-vue'

const showScheduleModal = ref(false)
const newSession = reactive({ coachId: undefined, topic: '', date: null, notes: '' })

const coaches = ref([
  { id: '1', name: '王教练', level: 'L2 中级', color: '#1890ff', studentCount: 15, successRate: 74, retention: 88, score: 4.5 },
  { id: '2', name: '李教练', level: 'L1 初级', color: '#52c41a', studentCount: 8, successRate: 62, retention: 80, score: 3.8 },
  { id: '3', name: '张教练', level: 'L2 中级', color: '#722ed1', studentCount: 12, successRate: 78, retention: 90, score: 4.2 },
  { id: '4', name: '赵教练', level: 'L1 初级', color: '#fa8c16', studentCount: 6, successRate: 55, retention: 75, score: 3.5 },
])

const coachColumns = [
  { title: '教练', key: 'name', width: 160 },
  { title: '学员数', dataIndex: 'studentCount', width: 80 },
  { title: '干预成功率', key: 'success', width: 160 },
  { title: '留存率', dataIndex: 'retention', width: 80, customRender: ({ text }: any) => `${text}%` },
  { title: '评分', key: 'score', width: 140 },
  { title: '操作', key: 'action', width: 150 },
]

const sessions = ref([
  { id: '1', coach: '李教练', status: '已完成', date: '2025-01-14 14:00', topic: '低成功率案例复盘', notes: '建议加强OARS技术运用，安排模拟练习' },
  { id: '2', coach: '赵教练', status: '已完成', date: '2025-01-12 10:00', topic: '高风险学员处理', notes: '讨论了3例高风险案例的应对策略' },
  { id: '3', coach: '王教练', status: '待进行', date: '2025-01-18 14:00', topic: 'L3晋级准备指导', notes: '' },
])

const scheduleSupervision = () => {
  if (!newSession.coachId || !newSession.topic) {
    message.warning('请填写必要信息')
    return
  }
  const coach = coaches.value.find(c => c.id === newSession.coachId)
  sessions.value.unshift({
    id: `s_${Date.now()}`,
    coach: coach?.name || '',
    status: '待进行',
    date: newSession.date ? newSession.date.format?.('YYYY-MM-DD HH:mm') || '待定' : '待定',
    topic: newSession.topic,
    notes: newSession.notes,
  })
  showScheduleModal.value = false
  newSession.coachId = undefined
  newSession.topic = ''
  newSession.date = null
  newSession.notes = ''
  message.success('督导已安排')
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; }

.session-item { padding: 12px 0; border-bottom: 1px solid #f5f5f5; }
.session-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.session-coach { font-weight: 600; font-size: 14px; }
.session-date { margin-left: auto; font-size: 12px; color: #999; }
.session-topic { font-size: 13px; color: #333; margin: 4px 0 0; }
.session-notes { font-size: 12px; color: #999; margin: 2px 0 0; }
</style>
