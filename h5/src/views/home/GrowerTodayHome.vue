<template>
  <!--
    Grower 今日行动首页
    飞轮目标: 留存 — 每天打开就知道"今天做什么"，行动完成获得正反馈循环
    核心设计: 
      ❌ 旧版: 数据概览Dashboard（血糖图、步数图、BMI卡片）→ 信息过载，不知道做什么
      ✅ 新版: 今日行动卡片流 → 每张卡片 = 一个具体行动 → 完成打卡 → 即时反馈
    替换: h5/src/views/home/index.vue (当Grower角色时渲染此组件)
  -->
  <div class="grower-today">
    <!-- ═══ 顶部: 问候+连续天数 ═══ -->
    <div class="today-header">
      <div class="greeting">
        <span class="greeting-time">{{ greetingText }}</span>
        <h1 class="user-name">{{ userName }}</h1>
      </div>
      <div class="streak-badge" v-if="streakDays > 0">
        <span class="streak-fire">🔥</span>
        <span class="streak-num">{{ streakDays }}</span>
        <span class="streak-label">天</span>
      </div>
    </div>

    <!-- ═══ 今日进度环 ═══ -->
    <div class="progress-hero">
      <div class="progress-circle">
        <svg viewBox="0 0 100 100">
          <circle class="prog-bg" cx="50" cy="50" r="42" />
          <circle class="prog-fill" cx="50" cy="50" r="42"
            :stroke-dasharray="`${completionPct * 2.64} 264`"
            :style="{ stroke: completionColor }" />
        </svg>
        <div class="prog-center">
          <span class="prog-done">{{ doneCount }}</span>
          <span class="prog-slash">/</span>
          <span class="prog-total">{{ totalCount }}</span>
        </div>
      </div>
      <div class="progress-label">
        <span v-if="completionPct === 0">今天的旅程开始了 ✨</span>
        <span v-else-if="completionPct < 50">继续加油 💪</span>
        <span v-else-if="completionPct < 100">快完成了！🎯</span>
        <span v-else>今天全部完成！🏆</span>
      </div>
    </div>

    <!-- ═══ 今日行动卡片流 (核心区域) ═══ -->
    <div class="actions-section">
      <h2 class="section-title">今日行动</h2>

      <div class="action-list">
        <div v-for="action in todayActions" :key="action.id"
          class="action-card" :class="{ done: action.done, active: !action.done }"
          @click="handleAction(action)">

          <!-- 左: 完成圆圈 -->
          <div class="action-check">
            <div class="check-circle" :class="{ checked: action.done }">
              <span v-if="action.done" class="check-icon">✓</span>
              <span v-else class="action-order">{{ action.order }}</span>
            </div>
          </div>

          <!-- 中: 内容 -->
          <div class="action-body">
            <div class="action-title" :class="{ 'line-through': action.done }">
              {{ action.title }}
            </div>
            <div class="action-meta">
              <span class="meta-tag" :style="{ background: action.tagColor + '20', color: action.tagColor }">
                {{ action.tag }}
              </span>
              <span class="meta-time">{{ action.timeHint }}</span>
              <span class="meta-mode" v-if="action.inputMode">
                {{ inputModeIcon(action.inputMode) }}
              </span>
            </div>
          </div>

          <!-- 右: 快捷操作 -->
          <div class="action-quick" v-if="!action.done">
            <button class="quick-btn" @click.stop="quickCheckin(action)">
              {{ action.quickLabel || '打卡' }}
            </button>
          </div>
          <div class="action-quick" v-else>
            <span class="done-time">{{ action.doneTime }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ AI 教练提示 (个性化一句话) ═══ -->
    <div class="coach-tip" v-if="coachTip">
      <div class="tip-avatar">🤖</div>
      <div class="tip-bubble">
        <p class="tip-text">{{ coachTip }}</p>
        <button class="tip-action" @click="openChat">
          和我聊聊 →
        </button>
      </div>
    </div>

    <!-- ═══ 本周趋势 (极简, 不是数据墙) ═══ -->
    <div class="week-glance">
      <h2 class="section-title">本周一览</h2>
      <div class="week-dots">
        <div v-for="day in weekDays" :key="day.label" class="week-day">
          <span class="day-label">{{ day.label }}</span>
          <div class="day-dot" :class="day.status">
            <span v-if="day.status === 'full'">✓</span>
            <span v-else-if="day.status === 'partial'">·</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ 打卡成功动画 ═══ -->
    <Transition name="checkin-toast">
      <div class="checkin-toast" v-if="showCheckinToast">
        <span class="toast-emoji">{{ checkinEmoji }}</span>
        <span class="toast-text">{{ checkinMessage }}</span>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// ── 用户状态 ──
const userName = ref('张三')
const streakDays = ref(7)
const coachTip = ref('昨天的步数比前天多了800步，今天试试走一个新路线？')

// ── 今日行动 ──
interface TodayAction {
  id: string
  order: number
  title: string
  tag: string
  tagColor: string
  timeHint: string
  inputMode?: 'photo' | 'voice' | 'text' | 'device'
  quickLabel?: string
  done: boolean
  doneTime?: string
}

const todayActions = ref<TodayAction[]>([
  {
    id: 'a1', order: 1, title: '记录早餐',
    tag: '营养', tagColor: '#f59e0b', timeHint: '7:00-9:00',
    inputMode: 'photo', quickLabel: '拍照', done: false
  },
  {
    id: 'a2', order: 2, title: '晨起血糖测量',
    tag: '监测', tagColor: '#3b82f6', timeHint: '空腹',
    inputMode: 'device', quickLabel: '记录', done: false
  },
  {
    id: 'a3', order: 3, title: '八段锦第三式 · 调理脾胃须单举',
    tag: '运动', tagColor: '#10b981', timeHint: '10分钟',
    inputMode: 'voice', quickLabel: '开始', done: false
  },
  {
    id: 'a4', order: 4, title: '记录午餐',
    tag: '营养', tagColor: '#f59e0b', timeHint: '12:00-13:00',
    inputMode: 'photo', quickLabel: '拍照', done: false
  },
  {
    id: 'a5', order: 5, title: '下午散步15分钟',
    tag: '运动', tagColor: '#10b981', timeHint: '14:00-16:00',
    inputMode: 'device', quickLabel: '打卡', done: false
  },
])

const doneCount = computed(() => todayActions.value.filter(a => a.done).length)
const totalCount = computed(() => todayActions.value.length)
const completionPct = computed(() => totalCount.value > 0 ? Math.round((doneCount.value / totalCount.value) * 100) : 0)
const completionColor = computed(() => {
  if (completionPct.value >= 100) return '#10b981'
  if (completionPct.value >= 50) return '#3b82f6'
  return '#f59e0b'
})

// ── 问候 ──
const greetingText = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 11) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

// ── 本周 ──
const weekDays = ref([
  { label: '一', status: 'full' },
  { label: '二', status: 'full' },
  { label: '三', status: 'partial' },
  { label: '四', status: 'full' },
  { label: '五', status: 'today' },
  { label: '六', status: 'future' },
  { label: '日', status: 'future' },
])

// ── 打卡交互 ──
const showCheckinToast = ref(false)
const checkinEmoji = ref('🎉')
const checkinMessage = ref('')

function inputModeIcon(mode: string) {
  const map: Record<string, string> = { photo: '📷', voice: '🎤', text: '✏️', device: '⌚' }
  return map[mode] || ''
}

function handleAction(action: TodayAction) {
  if (action.done) return
  // 根据inputMode跳转到对应的多模态入口
  switch (action.inputMode) {
    case 'photo':
      router.push({ path: '/chat', query: { action: 'camera', type: 'food', taskId: action.id } })
      break
    case 'voice':
      router.push({ path: '/chat', query: { action: 'voice', taskId: action.id } })
      break
    case 'device':
      router.push({ path: '/health-records', query: { taskId: action.id } })
      break
    default:
      router.push({ path: '/chat', query: { taskId: action.id } })
  }
}

function quickCheckin(action: TodayAction) {
  action.done = true
  action.doneTime = new Date().toTimeString().slice(0, 5)
  
  // 即时反馈
  const emojis = ['🎉', '💪', '✨', '🔥', '👏']
  const messages = ['太棒了！', '做到了！', '继续保持！', '又进一步！', '好样的！']
  const idx = Math.floor(Math.random() * emojis.length)
  checkinEmoji.value = emojis[idx]
  checkinMessage.value = messages[idx]
  showCheckinToast.value = true
  setTimeout(() => showCheckinToast.value = false, 2000)
  
  // TODO: 调用后端API记录打卡
  // await checkinApi.complete(action.id)
}

function openChat() {
  router.push('/chat')
}

onMounted(async () => {
  // const tasks = await dailyTaskApi.getToday()
  // todayActions.value = tasks.map(...)
})
</script>

<style scoped>
.grower-today {
  min-height: 100vh;
  background: #ffffff;
  padding-bottom: calc(60px + env(safe-area-inset-bottom, 0px));
}

/* ── 头部 ── */
.today-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px 0;
}
.greeting-time { font-size: 13px; color: #9ca3af; }
.user-name { font-size: 22px; font-weight: 800; color: #111827; margin: 2px 0 0; }
.streak-badge {
  display: flex; align-items: baseline; gap: 2px;
  background: #fef3c7; border-radius: 20px; padding: 6px 12px;
}
.streak-fire { font-size: 16px; }
.streak-num { font-size: 20px; font-weight: 900; color: #d97706; }
.streak-label { font-size: 11px; color: #92400e; }

/* ── 进度环 ── */
.progress-hero { display: flex; flex-direction: column; align-items: center; padding: 20px 0 16px; }
.progress-circle { width: 100px; height: 100px; position: relative; }
.progress-circle svg { transform: rotate(-90deg); }
.prog-bg { fill: none; stroke: #f3f4f6; stroke-width: 6; }
.prog-fill { fill: none; stroke-width: 6; stroke-linecap: round; transition: stroke-dasharray 0.6s ease; }
.prog-center {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
}
.prog-done { font-size: 28px; font-weight: 900; color: #111827; }
.prog-slash { font-size: 16px; color: #d1d5db; margin: 0 2px; }
.prog-total { font-size: 16px; color: #9ca3af; }
.progress-label { font-size: 14px; color: #6b7280; margin-top: 8px; }

/* ── 行动卡片 ── */
.actions-section { padding: 0 20px; }
.section-title { font-size: 16px; font-weight: 700; color: #111827; margin: 0 0 12px; }
.action-list { display: flex; flex-direction: column; gap: 8px; }
.action-card {
  display: flex; align-items: center; gap: 12px;
  background: #fff; border: 1px solid #e5e7eb; border-radius: 14px;
  padding: 14px 16px; transition: all 0.2s; cursor: pointer;
}
.action-card.active:active { transform: scale(0.98); background: #f9fafb; }
.action-card.done { background: #f9fafb; border-color: #f3f4f6; }

.check-circle {
  width: 32px; height: 32px; border-radius: 50%;
  border: 2.5px solid #d1d5db; display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 700; color: #9ca3af; transition: all 0.3s; flex-shrink: 0;
}
.check-circle.checked {
  border-color: var(--bhp-brand-primary, #10b981);
  background: var(--bhp-brand-primary, #10b981); color: #fff;
}
.check-icon { font-size: 16px; }

.action-body { flex: 1; min-width: 0; }
.action-title { font-size: 14px; font-weight: 600; color: #111827; }
.action-title.line-through { text-decoration: line-through; color: #9ca3af; }
.action-meta { display: flex; align-items: center; gap: 8px; margin-top: 4px; }
.meta-tag { font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: 600; }
.meta-time { font-size: 11px; color: #9ca3af; }
.meta-mode { font-size: 14px; }

.quick-btn {
  background: var(--bhp-brand-primary, #10b981); color: #fff;
  border: none; border-radius: 8px; padding: 6px 14px;
  font-size: 13px; font-weight: 600; cursor: pointer;
  white-space: nowrap; transition: all 0.2s;
}
.quick-btn:active { transform: scale(0.95); }
.done-time { font-size: 12px; color: #9ca3af; }

/* ── AI教练提示 ── */
.coach-tip {
  display: flex; gap: 10px; padding: 20px; margin: 16px 20px 0;
  background: #f0fdf4; border-radius: 16px;
}
.tip-avatar { font-size: 24px; flex-shrink: 0; }
.tip-bubble { flex: 1; }
.tip-text { font-size: 13px; color: #374151; margin: 0 0 8px; line-height: 1.5; }
.tip-action {
  background: none; border: none; color: var(--bhp-brand-primary, #10b981);
  font-size: 13px; font-weight: 600; cursor: pointer; padding: 0;
}

/* ── 本周一览 ── */
.week-glance { padding: 20px; }
.week-dots { display: flex; justify-content: space-between; }
.week-day { text-align: center; flex: 1; }
.day-label { font-size: 11px; color: #9ca3af; display: block; margin-bottom: 6px; }
.day-dot {
  width: 28px; height: 28px; border-radius: 50%; margin: 0 auto;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 700;
}
.day-dot.full { background: var(--bhp-brand-primary, #10b981); color: #fff; }
.day-dot.partial { background: #bbf7d0; color: #16a34a; }
.day-dot.today { background: #dbeafe; color: #2563eb; border: 2px solid #3b82f6; }
.day-dot.future { background: #f3f4f6; color: #d1d5db; }

/* ── 打卡Toast ── */
.checkin-toast {
  position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
  background: rgba(0,0,0,0.85); color: #fff; border-radius: 16px;
  padding: 20px 32px; text-align: center; z-index: 999;
  display: flex; flex-direction: column; align-items: center; gap: 8px;
}
.toast-emoji { font-size: 40px; }
.toast-text { font-size: 16px; font-weight: 700; }
.checkin-toast-enter-active { animation: toastIn 0.3s; }
.checkin-toast-leave-active { animation: toastOut 0.3s; }
@keyframes toastIn { from { opacity: 0; transform: translate(-50%,-50%) scale(0.8); } to { opacity: 1; transform: translate(-50%,-50%) scale(1); } }
@keyframes toastOut { from { opacity: 1; } to { opacity: 0; transform: translate(-50%,-50%) scale(0.8); } }
</style>
