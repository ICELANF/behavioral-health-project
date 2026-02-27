<template>
  <PageShell :show-nav-bar="false" :show-tab-bar="true" no-padding>
    <!-- ═══ 顶部: UserHero (头像+问候+streak+设置+通知) ═══ -->
    <UserHero :streak-days="streakDays" />

    <!-- ═══ 全局搜索 ═══ -->
    <div style="padding: 0 20px;">
      <GlobalSearch />
    </div>

    <!-- ═══ 今日进度环 + 积分 ═══ -->
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
      <div class="progress-right">
        <div class="progress-label">
          <span v-if="completionPct === 0">今天的旅程开始了 ✨</span>
          <span v-else-if="completionPct < 50">继续加油 💪</span>
          <span v-else-if="completionPct < 100">快完成了！🎯</span>
          <span v-else>今天全部完成！🏆</span>
        </div>
        <div class="daily-points" v-if="dailyPoints > 0">
          <span class="points-badge">+{{ dailyPoints }} 积分 🏆</span>
        </div>
      </div>
    </div>

    <!-- ═══ 执行统计 ═══ -->
    <MotivationCard ref="motivationCardRef" />

    <!-- ═══ 分组任务区 ═══ -->
    <!-- 教练推荐 -->
    <TaskGroupSection
      v-if="coachTasks.length > 0"
      title="教练推荐" icon="🏥" color="blue"
      :tasks="coachTasks"
      :default-expanded="true"
      @checkin="handleCheckin"
      @click-action="handleAction"
    />

    <!-- AI推荐 -->
    <TaskGroupSection
      v-if="aiTasks.length > 0"
      title="AI推荐" icon="🤖" color="green"
      :tasks="aiTasks"
      :default-expanded="true"
      @checkin="handleCheckin"
      @click-action="handleAction"
    />

    <!-- 自选任务 -->
    <TaskGroupSection
      title="自选任务" icon="📝" color="gray"
      :tasks="selfTasks"
      :default-expanded="true"
      @checkin="handleCheckin"
      @click-action="handleAction"
    >
      <template #header-action>
        <button class="add-self-btn" @click.stop="showCatalog = true">+ 添加</button>
      </template>
    </TaskGroupSection>

    <!-- 已完成 -->
    <TaskGroupSection
      v-if="doneTasks.length > 0"
      title="已完成" icon="✅" color="emerald"
      :tasks="doneTasks"
      :default-expanded="false"
      :max-visible="3"
      @click-action="handleAction"
    />

    <!-- 空状态: 没有任何任务 -->
    <div class="empty-tasks" v-if="totalCount === 0">
      <span class="empty-icon">📋</span>
      <p class="empty-text">今天还没有任务</p>
      <button class="empty-add-btn" @click="showCatalog = true">+ 添加自选任务</button>
    </div>

    <!-- ═══ 自选目录弹层 ═══ -->
    <CatalogSheet
      v-model:show="showCatalog"
      :catalog="catalog"
      :catalog-loading="catalogLoading"
      @add-from-catalog="handleAddFromCatalog"
    />

    <!-- ═══ AI 教练提示 (个性化一句话) ═══ -->
    <div class="coach-tip" v-if="coachTip">
      <div class="tip-avatar">🤖</div>
      <div class="tip-bubble">
        <p class="tip-text">{{ coachTip }}</p>
        <div class="tip-footer">
          <AiContentBadge compact />
          <button class="tip-action" @click="openChat">
            和我聊聊 →
          </button>
        </div>
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

    <!-- ═══ 打卡成功动画 (增强: 积分明细+徽章+里程碑) ═══ -->
    <Transition name="checkin-toast">
      <div class="checkin-toast" v-if="showCheckinToast">
        <span class="toast-emoji">{{ checkinEmoji }}</span>
        <span class="toast-text">{{ checkinMessage }}</span>
        <span class="toast-points" v-if="checkinPoints > 0">+{{ checkinPoints }} 积分</span>
        <div class="toast-breakdown" v-if="checkinBreakdown && Object.keys(checkinBreakdown).length > 1">
          <span v-for="(val, key) in checkinBreakdown" :key="key" class="breakdown-item">
            {{ breakdownLabel(String(key)) }} +{{ val }}
          </span>
        </div>
        <span class="toast-streak" v-if="checkinStreak > 0">🔥 连续 {{ checkinStreak }} 天</span>
        <span class="toast-badge" v-if="checkinBadge">🏅 {{ checkinBadge }}</span>
        <span class="toast-milestone" v-if="checkinMilestone">🎯 {{ milestoneLabel(checkinMilestone) }}</span>
      </div>
    </Transition>

  </PageShell>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import api from '@/api/index'
import { useUserStore } from '@/stores/user'
import { useTaskGroups, type TodayAction } from '@/composables/useTaskGroups'
import PageShell from '@/components/common/PageShell.vue'
import UserHero from '@/components/common/UserHero.vue'
import GlobalSearch from '@/components/common/GlobalSearch.vue'
import AiContentBadge from '@/components/common/AiContentBadge.vue'
import TaskGroupSection from '@/components/task/TaskGroupSection.vue'
import CatalogSheet from '@/components/task/CatalogSheet.vue'
import MotivationCard from '@/components/home/MotivationCard.vue'

const router = useRouter()
const userStore = useUserStore()

// ── 任务分组 ──
const {
  coachTasks, aiTasks, selfTasks, doneTasks,
  dailyPoints, streakDays,
  totalCount, doneCount, completionPct,
  loadTodayTasks, checkin,
  catalog, catalogLoading, loadCatalog, addFromCatalog,
} = useTaskGroups()

const motivationCardRef = ref<InstanceType<typeof MotivationCard>>()

const completionColor = ref('#f59e0b')
// 用 watch 替代 computed 以简化 (直接在打卡回调里更新)
function updateCompletionColor() {
  const pct = completionPct.value
  if (pct >= 100) completionColor.value = '#10b981'
  else if (pct >= 50) completionColor.value = '#3b82f6'
  else completionColor.value = '#f59e0b'
}

// ── 教练提示 ──
const coachTip = ref('')

// ── 本周 ──
const weekDays = ref<{ label: string; status: string }[]>([])

// ── 自选目录弹层 ──
const showCatalog = ref(false)

// ── 打卡交互 ──
const showCheckinToast = ref(false)
const checkinEmoji = ref('🎉')
const checkinMessage = ref('')
const checkinPoints = ref(0)
const checkinStreak = ref(0)
const checkinBreakdown = ref<Record<string, number> | null>(null)
const checkinBadge = ref('')
const checkinMilestone = ref('')

function breakdownLabel(key: string): string {
  const map: Record<string, string> = {
    base: '基础', streak_7d: '连续7天', streak_14d: '连续14天',
    streak_30d: '连续30天', first_time: '首次完成',
    domain_diversity: '领域多样', all_done: '全部完成', self_select: '自选积极',
  }
  return map[key] || key
}

function milestoneLabel(m: string): string {
  const map: Record<string, string> = {
    SELF_TASK_10: '自选探索者', SELF_TASK_50: '自选实践者',
    SELF_TASK_100: '自选大师', SELF_TASK_365: '自选传奇',
  }
  return map[m] || m
}

function inputModeIcon(mode: string) {
  const map: Record<string, string> = { photo: '📷', voice: '🎤', text: '✏️', device: '⌚' }
  return map[mode] || ''
}

function handleAction(action: TodayAction) {
  if (action.done) return
  // 营养拍照任务 → 直接跳转食物识别页
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

async function handleCheckin(action: TodayAction) {
  // 默认反馈
  const emojis = ['🎉', '💪', '✨', '🔥', '👏']
  const messages = ['太棒了！', '做到了！', '继续保持！', '又进一步！', '好样的！']
  const idx = Math.floor(Math.random() * emojis.length)
  checkinEmoji.value = emojis[idx]
  checkinMessage.value = messages[idx]
  checkinPoints.value = 0
  checkinStreak.value = 0
  checkinBreakdown.value = null
  checkinBadge.value = ''
  checkinMilestone.value = ''

  const result = await checkin(action)

  if (result.emoji) checkinEmoji.value = result.emoji
  if (result.message) checkinMessage.value = result.message
  if (result.points_earned) checkinPoints.value = result.points_earned
  if (result.streak_days) checkinStreak.value = result.streak_days
  if (result.points_breakdown) checkinBreakdown.value = result.points_breakdown
  if (result.badge_name) checkinBadge.value = result.badge_name
  if (result.milestone_reached) checkinMilestone.value = result.milestone_reached

  updateCompletionColor()

  showCheckinToast.value = true
  // 有额外奖励时显示更久
  const hasExtras = checkinBadge.value || checkinMilestone.value
  setTimeout(() => { showCheckinToast.value = false }, hasExtras ? 3500 : 2500)

  // 刷新激励统计
  motivationCardRef.value?.reload()
}

async function handleAddFromCatalog(catalogId: string, customTitle?: string) {
  const ok = await addFromCatalog(catalogId || '', customTitle)
  if (ok) {
    showToast('已添加')
    updateCompletionColor()
  } else {
    showToast('添加失败')
  }
}

function openChat() {
  router.push('/chat')
}

onMounted(async () => {
  // 并行加载今日任务、目录、教练提示、本周一览
  const [, tipRes, weekRes] = await Promise.allSettled([
    loadTodayTasks(),
    api.get('/api/v1/coach-tip/today'),
    api.get('/api/v1/weekly-summary'),
    loadCatalog(),
  ])

  updateCompletionColor()

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
})
</script>

<style scoped>
/* ── 进度环 + 积分 ── */
.progress-hero {
  display: flex; align-items: center; justify-content: center;
  gap: 20px; padding: 20px 20px 16px;
}
.progress-circle { width: 100px; height: 100px; position: relative; flex-shrink: 0; }
.progress-circle svg { transform: rotate(-90deg); }
.prog-bg { fill: none; stroke: #f3f4f6; stroke-width: 6; }
.prog-fill { fill: none; stroke-width: 6; stroke-linecap: round; transition: stroke-dasharray 0.6s ease; }
.prog-center {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
}
.prog-done { font-size: 28px; font-weight: 900; color: #111827; }
.prog-slash { font-size: 16px; color: #d1d5db; margin: 0 2px; }
.prog-total { font-size: 16px; color: #9ca3af; }
.progress-right { display: flex; flex-direction: column; gap: 6px; }
.progress-label { font-size: 14px; color: #6b7280; }
.daily-points { }
.points-badge {
  display: inline-block; font-size: 13px; font-weight: 700;
  color: #d97706; background: #fef3c7; padding: 3px 10px;
  border-radius: 12px;
}

/* ── 自选区添加按钮 ── */
.add-self-btn {
  background: none; border: 1px solid #d1d5db; border-radius: 6px;
  padding: 3px 10px; font-size: 12px; font-weight: 600;
  color: #6b7280; cursor: pointer; transition: all 0.2s;
}
.add-self-btn:active { background: #f3f4f6; transform: scale(0.95); }

/* ── 空任务状态 ── */
.empty-tasks { text-align: center; padding: 32px 20px; }
.empty-icon { font-size: 36px; display: block; margin-bottom: 8px; }
.empty-text { font-size: 14px; color: #9ca3af; margin: 0 0 12px; }
.empty-add-btn {
  background: var(--bhp-brand-primary, #10b981); color: #fff;
  border: none; border-radius: 10px; padding: 10px 24px;
  font-size: 14px; font-weight: 600; cursor: pointer;
}
.empty-add-btn:active { transform: scale(0.95); }

/* ── section-title ── */
.section-title { font-size: 16px; font-weight: 700; color: #111827; margin: 0 0 12px; }

/* ── AI教练提示 ── */
.coach-tip {
  display: flex; gap: 10px; padding: 20px; margin: 16px 20px 0;
  background: #f0fdf4; border-radius: 16px;
}
.tip-avatar { font-size: 24px; flex-shrink: 0; }
.tip-bubble { flex: 1; }
.tip-text { font-size: 13px; color: #374151; margin: 0 0 8px; line-height: 1.5; }
.tip-footer { display: flex; align-items: center; justify-content: space-between; }
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

/* ── 打卡Toast (增强: 积分+连续天数) ── */
.checkin-toast {
  position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
  background: rgba(0,0,0,0.85); color: #fff; border-radius: 16px;
  padding: 20px 32px; text-align: center; z-index: 999;
  display: flex; flex-direction: column; align-items: center; gap: 6px;
}
.toast-emoji { font-size: 40px; }
.toast-text { font-size: 16px; font-weight: 700; }
.toast-points { font-size: 14px; color: #fbbf24; font-weight: 600; }
.toast-breakdown {
  display: flex; flex-wrap: wrap; gap: 4px 8px; justify-content: center;
  margin-top: 2px;
}
.breakdown-item {
  font-size: 11px; color: #d1d5db; background: rgba(255,255,255,0.1);
  padding: 1px 6px; border-radius: 4px;
}
.toast-streak { font-size: 12px; color: #9ca3af; }
.toast-badge { font-size: 13px; color: #a78bfa; font-weight: 600; margin-top: 2px; }
.toast-milestone { font-size: 13px; color: #34d399; font-weight: 600; margin-top: 2px; }
.checkin-toast-enter-active { animation: toastIn 0.3s; }
.checkin-toast-leave-active { animation: toastOut 0.3s; }
@keyframes toastIn { from { opacity: 0; transform: translate(-50%,-50%) scale(0.8); } to { opacity: 1; transform: translate(-50%,-50%) scale(1); } }
@keyframes toastOut { from { opacity: 1; } to { opacity: 0; transform: translate(-50%,-50%) scale(0.8); } }
</style>
