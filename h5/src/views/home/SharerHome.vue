<template>
  <!--
    Sharer(L2) 分享者首页
    核心设计: 在Grower飞轮基础上新增3个分享者专属区块
      - 同道者进度卡片 (引领4名同道者)
      - 投稿统计 (知识分享)
      - 影响力积分 (社会认可)
  -->
  <div class="sharer-home">
    <!-- ═══ 顶部: 问候+连续天数+分享者标签 ═══ -->
    <div class="today-header">
      <div class="greeting">
        <span class="greeting-time">{{ greetingText }}</span>
        <h1 class="user-name">{{ userName }}</h1>
      </div>
      <div class="header-badges">
        <div class="role-badge">
          <span class="role-icon">💬</span>
          <span class="role-text">分享者</span>
        </div>
        <div class="streak-badge" v-if="streakDays > 0">
          <span class="streak-fire">🔥</span>
          <span class="streak-num">{{ streakDays }}</span>
          <span class="streak-label">天</span>
        </div>
      </div>
    </div>

    <!-- ═══ 今日进度环 (复用Grower) ═══ -->
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

    <!-- ═══ 今日行动卡片流 (复用Grower打卡逻辑) ═══ -->
    <div class="actions-section">
      <h2 class="section-title">今日行动</h2>
      <div class="action-list">
        <div v-for="action in todayActions" :key="action.id"
          class="action-card" :class="{ done: action.done, active: !action.done }"
          @click="handleAction(action)">
          <div class="action-check">
            <div class="check-circle" :class="{ checked: action.done }">
              <span v-if="action.done" class="check-icon">✓</span>
              <span v-else class="action-order">{{ action.order }}</span>
            </div>
          </div>
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

    <!-- ═══ 🤝 我的同道者 (NEW) ═══ -->
    <div class="mentee-section">
      <div class="section-header">
        <h2 class="section-title">🤝 我的同道者</h2>
        <button class="view-all-btn" @click="goCompanions">查看全部 →</button>
      </div>
      <div class="mentee-grid">
        <div v-for="(slot, idx) in menteeSlots" :key="idx"
          class="mentee-card" :class="{ empty: slot.status === 'empty' }"
          @click="slot.status === 'empty' ? goInvite() : null">
          <template v-if="slot.status !== 'empty'">
            <div class="mentee-avatar">{{ slot.name.charAt(0) }}</div>
            <div class="mentee-name">{{ slot.name }}</div>
            <div class="mentee-streak" v-if="slot.streak > 0">🔥{{ slot.streak }}天</div>
            <div class="mentee-progress">
              <div class="mentee-bar">
                <div class="mentee-bar-fill" :style="{ width: slot.today_pct + '%' }"></div>
              </div>
              <span class="mentee-pct">{{ slot.today_pct }}%</span>
            </div>
          </template>
          <template v-else>
            <div class="mentee-empty-icon">+</div>
            <div class="mentee-empty-text">邀请</div>
          </template>
        </div>
      </div>
    </div>

    <!-- ═══ 📝 我的分享 (NEW) ═══ -->
    <div class="contribution-section">
      <h2 class="section-title">📝 我的分享</h2>
      <div class="contrib-stats">
        <div class="contrib-stat">
          <span class="contrib-num">{{ contribStats.submitted }}</span>
          <span class="contrib-label">投稿</span>
        </div>
        <div class="contrib-stat pub">
          <span class="contrib-num">{{ contribStats.published }}</span>
          <span class="contrib-label">✅ 发布</span>
        </div>
        <div class="contrib-stat pending">
          <span class="contrib-num">{{ contribStats.pending }}</span>
          <span class="contrib-label">⏳ 待审</span>
        </div>
      </div>
      <div class="contrib-actions">
        <button class="contrib-btn primary" @click="goContribute">+ 写经验</button>
        <button class="contrib-btn" @click="goChat">+ 答疑</button>
      </div>
    </div>

    <!-- ═══ ⭐ 影响力 (NEW) ═══ -->
    <div class="influence-section">
      <h2 class="section-title">⭐ 影响力</h2>
      <div class="influence-row">
        <div class="influence-total">
          <span class="influence-num">{{ influenceScore.total }}</span>
          <span class="influence-unit">分</span>
        </div>
        <div class="influence-detail">
          <span class="inf-item">👍 {{ influenceScore.likes }} 赞</span>
          <span class="inf-item">📌 {{ influenceScore.saves }} 藏</span>
          <span class="inf-item">📎 {{ influenceScore.citations }} 引</span>
        </div>
      </div>
    </div>

    <!-- ═══ AI 教练提示 (分享者侧重带教建议) ═══ -->
    <div class="coach-tip" v-if="coachTip">
      <div class="tip-avatar">🤖</div>
      <div class="tip-bubble">
        <p class="tip-text">{{ coachTip }}</p>
        <button class="tip-action" @click="openChat">和我聊聊 →</button>
      </div>
    </div>

    <!-- ═══ 本周一览 7日点阵 (复用Grower) ═══ -->
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
import api from '@/api/index'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

// ── 用户状态 ──
const userName = ref(userStore.name || '用户')
const streakDays = ref(0)
const coachTip = ref('')

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

const todayActions = ref<TodayAction[]>([])

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

// ── 分享者专属数据 ──
interface MenteeSlot {
  user_id: number | null
  name: string
  role: string
  status: string
  streak: number
  today_pct: number
}
const menteeSlots = ref<MenteeSlot[]>([
  { user_id: null, name: '', role: '', status: 'empty', streak: 0, today_pct: 0 },
  { user_id: null, name: '', role: '', status: 'empty', streak: 0, today_pct: 0 },
  { user_id: null, name: '', role: '', status: 'empty', streak: 0, today_pct: 0 },
  { user_id: null, name: '', role: '', status: 'empty', streak: 0, today_pct: 0 },
])

const contribStats = ref({ submitted: 0, pending: 0, published: 0, rejected: 0 })
const influenceScore = ref({ total: 0, likes: 0, saves: 0, citations: 0, official_points: 0 })

// ── 本周 ──
const weekDays = ref<{ label: string; status: string }[]>([])

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
  if (action.inputMode === 'photo' && action.tag === '营养') {
    router.push({ path: '/food-recognition', query: { taskId: action.id } })
    return
  }
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

async function quickCheckin(action: TodayAction) {
  action.done = true
  action.doneTime = new Date().toTimeString().slice(0, 5)

  const emojis = ['🎉', '💪', '✨', '🔥', '👏']
  const messages = ['太棒了！', '做到了！', '继续保持！', '又进一步！', '好样的！']
  const idx = Math.floor(Math.random() * emojis.length)
  checkinEmoji.value = emojis[idx]
  checkinMessage.value = messages[idx]

  try {
    const res: any = await api.post(`/api/v1/daily-tasks/${action.id}/checkin`)
    if (res.emoji) checkinEmoji.value = res.emoji
    if (res.message) checkinMessage.value = res.message
    if (res.streak_days) streakDays.value = res.streak_days
  } catch { /* optimistic update */ }

  showCheckinToast.value = true
  setTimeout(() => showCheckinToast.value = false, 2000)
}

function openChat() { router.push('/chat') }
function goCompanions() { router.push('/my-companions') }
function goInvite() { router.push({ path: '/my-companions', query: { action: 'invite' } }) }
function goContribute() { router.push('/contribute') }
function goChat() { router.push('/chat') }

onMounted(async () => {
  // 并行加载: 3个Grower复用API + 3个Sharer新API
  const [tasksRes, tipRes, weekRes, menteeRes, contribRes, influenceRes] = await Promise.allSettled([
    api.get('/api/v1/daily-tasks/today'),
    api.get('/api/v1/coach-tip/today'),
    api.get('/api/v1/weekly-summary'),
    api.get('/api/v1/sharer/mentee-progress'),
    api.get('/api/v1/sharer/contribution-stats'),
    api.get('/api/v1/sharer/influence-score'),
  ])

  // 今日任务
  if (tasksRes.status === 'fulfilled') {
    const data = tasksRes.value as any
    todayActions.value = (data.tasks || []).map((t: any) => ({
      id: t.id,
      order: t.order,
      title: t.title,
      tag: t.tag,
      tagColor: t.tag_color,
      timeHint: t.time_hint,
      inputMode: t.input_mode,
      quickLabel: t.quick_label,
      done: t.done,
      doneTime: t.done_time,
    }))
    streakDays.value = data.streak_days || 0
  }

  // 教练提示
  if (tipRes.status === 'fulfilled') {
    const data = tipRes.value as any
    coachTip.value = data.tip || ''
  }

  // 本周一览
  if (weekRes.status === 'fulfilled') {
    const data = weekRes.value as any
    weekDays.value = (data.days || []).map((d: any) => ({
      label: d.label,
      status: d.status,
    }))
  }

  // 同道者进度
  if (menteeRes.status === 'fulfilled') {
    const data = menteeRes.value as any
    if (data.mentees) {
      menteeSlots.value = data.mentees
    }
  }

  // 投稿统计
  if (contribRes.status === 'fulfilled') {
    const data = contribRes.value as any
    contribStats.value = {
      submitted: data.submitted || 0,
      pending: data.pending || 0,
      published: data.published || 0,
      rejected: data.rejected || 0,
    }
  }

  // 影响力
  if (influenceRes.status === 'fulfilled') {
    const data = influenceRes.value as any
    influenceScore.value = {
      total: data.total || 0,
      likes: data.likes || 0,
      saves: data.saves || 0,
      citations: data.citations || 0,
      official_points: data.official_points || 0,
    }
  }
})
</script>

<style scoped>
.sharer-home {
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
.header-badges { display: flex; align-items: center; gap: 8px; }
.role-badge {
  display: flex; align-items: center; gap: 4px;
  background: #ede9fe; border-radius: 20px; padding: 6px 12px;
}
.role-icon { font-size: 14px; }
.role-text { font-size: 12px; font-weight: 700; color: #7c3aed; }
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

/* ── 同道者区块 ── */
.mentee-section { padding: 20px 20px 0; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.view-all-btn {
  background: none; border: none; color: #6b7280; font-size: 13px;
  cursor: pointer; padding: 0;
}
.mentee-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.mentee-card {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 12px;
  padding: 12px 8px; text-align: center; cursor: default;
}
.mentee-card.empty {
  border-style: dashed; border-color: #d1d5db; cursor: pointer;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-height: 110px;
}
.mentee-card.empty:active { background: #f9fafb; }
.mentee-avatar {
  width: 36px; height: 36px; border-radius: 50%;
  background: #dbeafe; color: #2563eb; font-size: 16px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; margin: 0 auto 6px;
}
.mentee-name { font-size: 12px; font-weight: 600; color: #374151; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.mentee-streak { font-size: 11px; color: #d97706; margin: 2px 0; }
.mentee-progress { display: flex; align-items: center; gap: 4px; margin-top: 4px; }
.mentee-bar { flex: 1; height: 4px; background: #f3f4f6; border-radius: 2px; overflow: hidden; }
.mentee-bar-fill { height: 100%; background: #10b981; border-radius: 2px; transition: width 0.3s; }
.mentee-pct { font-size: 10px; color: #9ca3af; min-width: 28px; text-align: right; }
.mentee-empty-icon { font-size: 24px; color: #d1d5db; font-weight: 300; }
.mentee-empty-text { font-size: 12px; color: #9ca3af; margin-top: 4px; }

/* ── 投稿统计 ── */
.contribution-section { padding: 20px; }
.contrib-stats { display: flex; gap: 16px; margin-bottom: 12px; }
.contrib-stat { text-align: center; flex: 1; }
.contrib-num { font-size: 22px; font-weight: 800; color: #111827; display: block; }
.contrib-label { font-size: 12px; color: #6b7280; }
.contrib-stat.pub .contrib-num { color: #10b981; }
.contrib-stat.pending .contrib-num { color: #f59e0b; }
.contrib-actions { display: flex; gap: 10px; }
.contrib-btn {
  flex: 1; padding: 10px; border-radius: 10px; border: 1px solid #e5e7eb;
  background: #fff; font-size: 14px; font-weight: 600; color: #374151;
  cursor: pointer; text-align: center;
}
.contrib-btn.primary {
  background: var(--bhp-brand-primary, #10b981); color: #fff; border-color: transparent;
}
.contrib-btn:active { transform: scale(0.98); }

/* ── 影响力 ── */
.influence-section {
  padding: 16px 20px;
  margin: 0 20px;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-radius: 16px;
}
.influence-section .section-title { margin-bottom: 8px; }
.influence-row { display: flex; align-items: center; gap: 16px; }
.influence-total { display: flex; align-items: baseline; gap: 2px; }
.influence-num { font-size: 32px; font-weight: 900; color: #92400e; }
.influence-unit { font-size: 14px; color: #a16207; }
.influence-detail { display: flex; gap: 12px; flex-wrap: wrap; }
.inf-item { font-size: 13px; color: #78350f; }

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
.day-dot.missed { background: #f3f4f6; color: #d1d5db; }

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
