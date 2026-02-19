<template>
  <div class="medical-assistant">
    <!-- 顶部区域 -->
    <div class="header-section">
      <div class="header-content">
        <div class="header-row">
          <div>
            <div class="header-title">基层医护处方助手</div>
            <div class="header-subtitle">行为处方智能开具与管理</div>
          </div>
          <a-avatar :size="44" class="header-avatar">
            <template #icon><UserOutlined /></template>
          </a-avatar>
        </div>
      </div>
    </div>

    <div class="main-content">
      <!-- 患者搜索 -->
      <div class="section-card">
        <a-input-search
          v-model:value="patientSearch"
          placeholder="搜索患者姓名、ID..."
          size="large"
          @search="onPatientSearch"
        />
      </div>

      <!-- 快捷功能 -->
      <div class="section-card">
        <div class="card-header">
          <span class="card-title">快捷功能</span>
        </div>
        <div class="action-grid">
          <div v-for="action in quickActions" :key="action.key" class="action-item" @click="goAction(action.key)">
            <div class="action-icon" :style="{ background: action.bg }">{{ action.icon }}</div>
            <div class="action-name">{{ action.label }}</div>
          </div>
        </div>
      </div>

      <!-- 行为处方模板 -->
      <div class="section-card">
        <div class="card-header">
          <span class="card-title">行为处方模板</span>
          <a class="more-link" @click="router.push('/rx/strategies')">管理 ></a>
        </div>
        <div class="template-list">
          <div v-for="tpl in prescriptionTemplates" :key="tpl.id" class="template-item" @click="goPrescription(tpl)">
            <div class="template-icon" :style="{ background: tpl.bg, color: tpl.color }">{{ tpl.icon }}</div>
            <div class="template-info">
              <div class="template-name">{{ tpl.name }}</div>
              <div class="template-desc">{{ tpl.desc }}</div>
            </div>
            <div class="template-badge">{{ tpl.items }}项</div>
          </div>
        </div>
      </div>

      <!-- 今日待办 -->
      <div class="section-card">
        <div class="card-header">
          <span class="card-title">今日待办</span>
          <span class="todo-count">{{ pendingCount }} 待处理</span>
        </div>
        <div class="todo-list">
          <div v-for="todo in todayTodos" :key="todo.id" class="todo-item" :class="{ done: todo.done }">
            <div class="todo-check" @click="toggleTodo(todo)">
              <div class="todo-checkbox" :class="{ checked: todo.done }">
                <CheckOutlined v-if="todo.done" />
              </div>
            </div>
            <div class="todo-info">
              <div class="todo-title">{{ todo.title }}</div>
              <div class="todo-meta">
                <span class="todo-patient">{{ todo.patient }}</span>
                <span class="todo-time">{{ todo.time }}</span>
              </div>
            </div>
            <div class="todo-type" :class="todo.type">{{ todo.typeLabel }}</div>
          </div>
        </div>
      </div>

      <!-- 最近处方 -->
      <div class="section-card">
        <div class="card-header">
          <span class="card-title">最近开具</span>
        </div>
        <div class="recent-list">
          <div v-for="rx in recentPrescriptions" :key="rx.id" class="recent-item" @click="goViewRx(rx)">
            <div class="recent-left">
              <div class="recent-patient">{{ rx.patient }}</div>
              <div class="recent-rx">{{ rx.name }}</div>
            </div>
            <div class="recent-right">
              <div class="recent-date">{{ rx.date }}</div>
              <div class="recent-status" :class="rx.status">{{ rx.statusLabel }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 返回入口 -->
      <div class="section-card entry-card">
        <div class="entry-row" @click="router.push('/portal/public')">
          <div class="entry-icon">🌐</div>
          <div class="entry-info">
            <div class="entry-title">健康科普入口</div>
            <div class="entry-desc">面向公众的行为健康科普平台</div>
          </div>
          <RightOutlined class="entry-arrow" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { UserOutlined, CheckOutlined, RightOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import request from '@/api/request'

const router = useRouter()
const patientSearch = ref('')

const quickActions = [
  { key: 'new-rx', icon: '📝', label: '开具处方', bg: '#dcfce7' },
  { key: 'follow-up', icon: '📞', label: '随访记录', bg: '#dbeafe' },
  { key: 'assessment', icon: '📋', label: '行为评估', bg: '#fef3c7' },
  { key: 'referral', icon: '🔗', label: '转介上级', bg: '#fce7f3' },
  { key: 'education', icon: '📚', label: '健康宣教', bg: '#f3e8ff' },
  { key: 'data', icon: '📊', label: '数据统计', bg: '#ecfeff' },
]

const prescriptionTemplates = ref([
  { id: 1, icon: '🩸', name: '血糖管理行为处方', desc: '饮食+运动+监测+用药4维度', items: 12, bg: '#fef2f2', color: '#dc2626' },
  { id: 2, icon: '⚖️', name: '体重控制行为处方', desc: '热量限制+运动计划+行为记录', items: 8, bg: '#fffbeb', color: '#d97706' },
  { id: 3, icon: '🧘', name: '心理干预行为处方', desc: '正念+认知重构+社交支持', items: 6, bg: '#fdf4ff', color: '#9333ea' },
  { id: 4, icon: '😴', name: '睡眠改善行为处方', desc: '睡眠卫生+放松训练', items: 5, bg: '#ecfeff', color: '#0891b2' },
])

const todayTodos = ref<{ id: number; title: string; patient: string; time: string; done: boolean; type: string; typeLabel: string }[]>([])

const pendingCount = computed(() => todayTodos.value.filter(t => !t.done).length)

const recentPrescriptions = ref<{ id: number; patient: string; name: string; date: string; status: string; statusLabel: string }[]>([])

const statusLabelMap: Record<string, string> = { active: '执行中', completed: '已完成', paused: '已暂停', pending: '待开始' }

onMounted(async () => {
  // Load today's todos from daily-tasks API
  try {
    const res = await request.get('v1/daily-tasks/today')
    const tasks = res.data?.tasks || (Array.isArray(res.data) ? res.data : [])
    todayTodos.value = tasks.slice(0, 5).map((t: any) => ({
      id: t.id, title: t.title || t.tag || '任务',
      patient: '', time: t.due_time || '',
      done: t.done ?? t.completed ?? false,
      type: t.tag || 'task', typeLabel: t.tag || '任务',
    }))
  } catch { /* API unavailable — keep empty */ }

  // Load recent prescriptions from coach review queue
  try {
    const res = await request.get('v1/coach/review-queue')
    const items = res.data?.items || res.data || []
    recentPrescriptions.value = (Array.isArray(items) ? items : []).slice(0, 5).map((rx: any) => ({
      id: rx.id, patient: rx.user_name || rx.patient || '',
      name: rx.title || rx.name || '行为处方',
      date: (rx.created_at || rx.date || '').slice(0, 10),
      status: rx.status || 'active',
      statusLabel: statusLabelMap[rx.status] || rx.status || '执行中',
    }))
  } catch { /* API unavailable — keep empty */ }
})

// ---- 患者搜索 → 学员管理页 ----
const onPatientSearch = (value: string) => {
  if (!value.trim()) return
  router.push({ path: '/student', query: { search: value.trim() } })
}

// ---- 快捷功能路由映射 ----
const actionRouteMap: Record<string, string> = {
  'new-rx': '/rx/dashboard',
  'follow-up': '/coach/messages',
  'assessment': '/client/assessment/list',
  'referral': '/coach/my/students',
  'education': '/portal/public',
  'data': '/admin/analytics',
}

const goAction = (key: string) => {
  const target = actionRouteMap[key] || '/rx/dashboard'
  router.push(target)
}

// ---- 处方模板 → 行为处方仪表盘 ----
const goPrescription = (tpl: { id: number; name: string }) => {
  router.push({ path: '/rx/strategies', query: { template: String(tpl.id) } })
}

// ---- 待办勾选 ----
const toggleTodo = (todo: { done: boolean; title: string }) => {
  todo.done = !todo.done
  if (todo.done) message.success(`完成: ${todo.title}`)
}

// ---- 查看历史处方 → 处方详情 ----
const goViewRx = (rx: { id: number; name: string }) => {
  router.push({ path: `/rx/detail/${rx.id}` })
}
</script>

<style scoped>
.medical-assistant {
  min-height: 100vh;
  background: #f5f7fa;
}

.header-section {
  background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
  padding: 30px 16px 50px;
  border-radius: 0 0 24px 24px;
}

.header-content {
  max-width: 500px;
  margin: 0 auto;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 4px;
}

.header-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
}

.header-avatar {
  background: rgba(255, 255, 255, 0.2);
  border: 2px solid rgba(255, 255, 255, 0.5);
}

.main-content {
  max-width: 500px;
  margin: -30px auto 0;
  padding: 0 16px 32px;
  position: relative;
  z-index: 10;
}

.section-card {
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.more-link {
  color: #2563eb;
  font-size: 13px;
  cursor: pointer;
}

/* 快捷功能 */
.action-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: transform 0.2s;
}

.action-item:hover {
  transform: translateY(-2px);
}

.action-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}

.action-name {
  font-size: 12px;
  color: #4b5563;
  font-weight: 500;
}

/* 处方模板 */
.template-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.template-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.template-item:hover {
  background: #f3f4f6;
}

.template-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.template-info {
  flex: 1;
  min-width: 0;
}

.template-name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.template-desc {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

.template-badge {
  background: #e0e7ff;
  color: #4f46e5;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 500;
}

/* 待办 */
.todo-count {
  background: #fee2e2;
  color: #dc2626;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 500;
}

.todo-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.todo-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 12px;
  transition: all 0.2s;
}

.todo-item.done {
  opacity: 0.6;
}

.todo-checkbox {
  width: 22px;
  height: 22px;
  border: 2px solid #d1d5db;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.todo-checkbox.checked {
  background: #10b981;
  border-color: #10b981;
  color: #fff;
}

.todo-info {
  flex: 1;
  min-width: 0;
}

.todo-title {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
}

.todo-item.done .todo-title {
  text-decoration: line-through;
  color: #9ca3af;
}

.todo-meta {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

.todo-type {
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
}

.todo-type.review {
  background: #dbeafe;
  color: #2563eb;
}

.todo-type.followup {
  background: #dcfce7;
  color: #16a34a;
}

.todo-type.rx {
  background: #fef3c7;
  color: #d97706;
}

.todo-type.assess {
  background: #f3e8ff;
  color: #7c3aed;
}

/* 最近处方 */
.recent-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.recent-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f9fafb;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.recent-item:hover {
  background: #f3f4f6;
}

.recent-patient {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.recent-rx {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

.recent-right {
  text-align: right;
}

.recent-date {
  font-size: 12px;
  color: #9ca3af;
}

.recent-status {
  font-size: 11px;
  margin-top: 2px;
  font-weight: 500;
}

.recent-status.active {
  color: #10b981;
}

.recent-status.completed {
  color: #6b7280;
}

/* 入口 */
.entry-card {
  padding: 0;
  overflow: hidden;
}

.entry-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.entry-row:hover {
  background: #f9fafb;
}

.entry-icon {
  font-size: 28px;
}

.entry-info {
  flex: 1;
}

.entry-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.entry-desc {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

.entry-arrow {
  color: #d1d5db;
  font-size: 12px;
}
</style>
