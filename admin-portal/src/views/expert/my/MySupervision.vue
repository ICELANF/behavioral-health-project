<template>
  <div class="my-supervision">
    <div class="page-header">
      <h2>我的督导</h2>
      <a-button type="primary" @click="showScheduleModal = true">安排新督导</a-button>
    </div>

    <!-- Coach overview -->
    <a-row :gutter="16" style="margin-bottom: 16px">
      <a-col :span="6"><a-card size="small"><a-statistic title="被督导教练" :value="coaches.length" /></a-card></a-col>
      <a-col :span="6"><a-card size="small"><a-statistic title="本月督导次数" :value="monthlySessionCount" /></a-card></a-col>
      <a-col :span="6"><a-card size="small"><a-statistic title="平均教练评分" :value="avgCoachScore" :precision="1" value-style="color: #3f8600" /></a-card></a-col>
      <a-col :span="6"><a-card size="small"><a-statistic title="待处理事项" :value="pendingCount" value-style="color: #cf1322" /></a-card></a-col>
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
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import request from '@/api/request'

const showScheduleModal = ref(false)
const newSession = reactive({ coachId: undefined as string | undefined, topic: '', date: null as any, notes: '' })

interface CoachItem {
  id: string; name: string; level: string; color: string;
  studentCount: number; successRate: number; retention: number; score: number;
}

const coaches = ref<CoachItem[]>([])

const coachColumns = [
  { title: '教练', key: 'name', width: 160 },
  { title: '学员数', dataIndex: 'studentCount', width: 80 },
  { title: '干预成功率', key: 'success', width: 160 },
  { title: '留存率', dataIndex: 'retention', width: 80, customRender: ({ text }: any) => `${text}%` },
  { title: '评分', key: 'score', width: 140 },
  { title: '操作', key: 'action', width: 150 },
]

interface SessionItem {
  id: string; coach: string; status: string; date: string; topic: string; notes: string;
}

const sessions = ref<SessionItem[]>([])

const monthlySessionCount = computed(() => sessions.value.filter(s => s.status === '已完成').length)
const avgCoachScore = computed(() => {
  if (coaches.value.length === 0) return 0
  return coaches.value.reduce((sum, c) => sum + c.score, 0) / coaches.value.length
})
const pendingCount = computed(() => sessions.value.filter(s => s.status === '待进行').length)

const levelColors = ['#1890ff', '#52c41a', '#722ed1', '#fa8c16', '#eb2f96', '#13c2c2']

const loadSupervisionData = async () => {
  try {
    const expertId = localStorage.getItem('admin_user_id') || '0'
    const [coachesRes, sessionsRes] = await Promise.allSettled([
      request.get(`v1/expert/${expertId}/supervised-coaches`),
      request.get(`v1/expert/${expertId}/supervision-sessions`),
    ])
    if (coachesRes.status === 'fulfilled') {
      const items = coachesRes.value.data?.coaches || coachesRes.value.data?.items || coachesRes.value.data || []
      coaches.value = items.map((c: any, i: number) => ({
        id: String(c.id), name: c.name || c.username || '', level: c.level || 'L1',
        color: levelColors[i % levelColors.length],
        studentCount: c.student_count ?? c.studentCount ?? 0,
        successRate: c.success_rate ?? c.successRate ?? 0,
        retention: c.retention ?? 0,
        score: c.score ?? c.rating ?? 0,
      }))
    } else {
      console.error('加载教练列表失败:', coachesRes.reason)
    }
    if (sessionsRes.status === 'fulfilled') {
      const items = sessionsRes.value.data?.sessions || sessionsRes.value.data?.items || sessionsRes.value.data || []
      sessions.value = items.map((s: any) => ({
        id: String(s.id), coach: s.coach || s.coach_name || '',
        status: s.status || '待进行', date: s.date || s.scheduled_at || '',
        topic: s.topic || '', notes: s.notes || '',
      }))
    } else {
      console.error('加载督导会话失败:', sessionsRes.reason)
    }
  } catch (e) {
    console.error('加载督导数据失败:', e)
  }
}

onMounted(loadSupervisionData)

const scheduleSupervision = async () => {
  if (!newSession.coachId || !newSession.topic) {
    message.warning('请填写必要信息')
    return
  }
  try {
    const expertId = localStorage.getItem('admin_user_id') || '0'
    await request.post(`v1/expert/${expertId}/supervision-sessions`, {
      coach_id: newSession.coachId,
      topic: newSession.topic,
      date: newSession.date ? newSession.date.format?.('YYYY-MM-DD HH:mm') || '' : '',
      notes: newSession.notes,
    })
    showScheduleModal.value = false
    newSession.coachId = undefined
    newSession.topic = ''
    newSession.date = null
    newSession.notes = ''
    message.success('督导已安排')
    await loadSupervisionData()
  } catch (e) {
    console.error('安排督导失败:', e)
    message.error('安排督导失败')
  }
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
