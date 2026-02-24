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
              <a @click="viewCoachDetail(record)">查看详情</a>
              <a @click="openScheduleFor(record)">安排督导</a>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- Supervision Sessions -->
    <a-card title="督导会话记录">
      <a-empty v-if="sessions.length === 0" description="暂无督导记录" />
      <div v-for="session in sessions" :key="session.id" class="session-item">
        <div class="session-header">
          <span class="session-coach">{{ session.coach }}</span>
          <a-tag :color="sessionTagColor(session.status)">{{ session.status }}</a-tag>
          <span class="session-date">{{ session.date }}</span>
        </div>
        <p class="session-topic">主题: {{ session.topic }}</p>
        <p v-if="session.notes" class="session-notes">备注: {{ session.notes }}</p>
      </div>
    </a-card>

    <!-- Coach Detail Drawer -->
    <a-drawer
      v-model:open="showDetailDrawer"
      :title="`教练详情 — ${detailCoach?.name || ''}`"
      width="480"
      placement="right"
    >
      <template v-if="detailCoach">
        <div style="text-align: center; margin-bottom: 20px">
          <a-avatar :size="64" :style="{ background: detailCoach.color, fontSize: '28px' }">
            {{ detailCoach.name[0] }}
          </a-avatar>
          <h3 style="margin: 8px 0 4px">{{ detailCoach.name }}</h3>
          <a-tag>{{ detailCoach.level }}</a-tag>
        </div>

        <a-descriptions :column="1" bordered size="small">
          <a-descriptions-item label="学员数">{{ detailCoach.studentCount }} 人</a-descriptions-item>
          <a-descriptions-item label="干预成功率">
            <a-progress :percent="detailCoach.successRate" size="small" style="width: 120px" />
          </a-descriptions-item>
          <a-descriptions-item label="留存率">{{ detailCoach.retention }}%</a-descriptions-item>
          <a-descriptions-item label="综合评分">
            <a-rate :value="detailCoach.score" disabled allow-half :count="5" style="font-size: 14px" />
          </a-descriptions-item>
        </a-descriptions>

        <a-divider>相关督导记录</a-divider>

        <a-empty v-if="coachSessions.length === 0" description="暂无该教练的督导记录" />
        <div v-for="s in coachSessions" :key="s.id" class="session-item">
          <div class="session-header">
            <a-tag :color="sessionTagColor(s.status)" size="small">{{ s.status }}</a-tag>
            <span class="session-date">{{ s.date }}</span>
          </div>
          <p class="session-topic">{{ s.topic }}</p>
          <p v-if="s.notes" class="session-notes">{{ s.notes }}</p>
        </div>

        <div style="margin-top: 16px">
          <a-button type="primary" block @click="openScheduleFor(detailCoach); showDetailDrawer = false">
            安排督导
          </a-button>
        </div>
      </template>
    </a-drawer>

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
const showDetailDrawer = ref(false)
const detailCoach = ref<CoachItem | null>(null)
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
  id: string; coach: string; coachId: string; status: string; date: string; topic: string; notes: string;
}

const sessions = ref<SessionItem[]>([])

const monthlySessionCount = computed(() => sessions.value.filter(s => s.status === '已完成').length)
const avgCoachScore = computed(() => {
  if (coaches.value.length === 0) return 0
  return coaches.value.reduce((sum, c) => sum + c.score, 0) / coaches.value.length
})
const pendingCount = computed(() => sessions.value.filter(s => s.status !== '已完成' && s.status !== '已拒绝').length)

// Sessions filtered for the detail drawer
const coachSessions = computed(() => {
  if (!detailCoach.value) return []
  return sessions.value.filter(s => s.coachId === detailCoach.value!.id || s.coach === detailCoach.value!.name)
})

const levelColors = ['#1890ff', '#52c41a', '#722ed1', '#fa8c16', '#eb2f96', '#13c2c2']

const sessionTagColor = (status: string) => {
  const map: Record<string, string> = {
    '已完成': 'green', '已审核': 'cyan', '待审核': 'orange',
    '待进行': 'blue', '已拒绝': 'red',
  }
  return map[status] || 'blue'
}

// "查看详情" — open detail drawer
const viewCoachDetail = (coach: CoachItem) => {
  detailCoach.value = coach
  showDetailDrawer.value = true
}

// "安排督导" — open schedule modal pre-filled with the coach
const openScheduleFor = (coach: CoachItem) => {
  newSession.coachId = coach.id
  newSession.topic = ''
  newSession.date = null
  newSession.notes = ''
  showScheduleModal.value = true
}

const loadSupervisionData = async () => {
  try {
    const [coachesRes, sessionsRes, statsRes] = await Promise.allSettled([
      request.get('v1/admin/coaches'),
      request.get('v1/supervision/sessions', { params: { page_size: 50 } }),
      request.get('v1/supervision/stats'),
    ])
    if (coachesRes.status === 'fulfilled') {
      const items = coachesRes.value.data?.items || coachesRes.value.data || []
      coaches.value = (Array.isArray(items) ? items : []).map((c: any, i: number) => ({
        id: String(c.id), name: c.full_name || c.username || '', level: `L${c.level || 0}`,
        color: levelColors[i % levelColors.length],
        studentCount: c.student_count ?? 0,
        successRate: c.success_rate ?? 0,
        retention: c.retention ?? 0,
        score: c.score ?? c.rating ?? 3,
      }))
    } else {
      console.error('加载教练列表失败:', coachesRes.reason)
    }

    // 从督导 API 加载会话记录
    const allSessions: SessionItem[] = []
    if (sessionsRes.status === 'fulfilled') {
      const items = sessionsRes.value.data?.data || sessionsRes.value.data || []
      const statusMap: Record<string, string> = {
        scheduled: '待进行', in_progress: '进行中', completed: '已完成', cancelled: '已取消',
      }
      for (const s of (Array.isArray(items) ? items : [])) {
        allSessions.push({
          id: String(s.id),
          coach: s.coach_name || '',
          coachId: String(s.coach_id),
          status: statusMap[s.status] || s.status,
          date: s.scheduled_at || s.created_at || '',
          topic: s.session_type || '',
          notes: s.session_notes || '',
        })
      }
    }

    sessions.value = allSessions
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
    await request.post('v1/supervision/sessions', {
      coach_id: Number(newSession.coachId),
      session_type: 'individual',
      scheduled_at: newSession.date?.toISOString?.() || newSession.date?.format?.('YYYY-MM-DDTHH:mm:ss') || null,
      notes: `${newSession.topic}${newSession.notes ? '\n' + newSession.notes : ''}`,
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
