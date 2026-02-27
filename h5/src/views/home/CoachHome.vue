<template>
  <!--
    Coach(L3) 教练首页
    核心: 学员管理 + 推送审核 + 今日会话 + 内容投稿
  -->
  <PageShell :show-nav-bar="false" :show-tab-bar="true" no-padding>
    <UserHero :streak-days="streakDays" />

    <div style="padding: 0 20px;">
      <GlobalSearch />
    </div>

    <!-- ═══ 教练工作台概览 ═══ -->
    <div class="overview-cards">
      <div class="ov-card" @click="$router.push('/coach-directory')">
        <span class="ov-num">{{ stats.studentCount }}</span>
        <span class="ov-label">学员</span>
      </div>
      <div class="ov-card" @click="$router.push('/chat')">
        <span class="ov-num">{{ stats.todaySessions }}</span>
        <span class="ov-label">今日会话</span>
      </div>
      <div class="ov-card ov-card--alert" @click="$router.push('/tasks')">
        <span class="ov-num">{{ stats.pendingPush }}</span>
        <span class="ov-label">待审推送</span>
      </div>
      <div class="ov-card" @click="$router.push('/my-credits')">
        <span class="ov-num">{{ stats.totalCredits }}</span>
        <span class="ov-label">学分</span>
      </div>
    </div>

    <!-- ═══ 学员动态 ═══ -->
    <div class="section">
      <div class="section-header">
        <h2 class="section-title">🎯 学员动态</h2>
        <button class="view-all-btn" @click="$router.push('/coach-directory')">查看全部 →</button>
      </div>
      <div v-if="students.length === 0" class="empty-hint">暂无学员数据</div>
      <div v-else class="student-list">
        <div v-for="s in students" :key="s.id" class="student-card">
          <div class="stu-avatar">{{ (s.name || '?').charAt(0) }}</div>
          <div class="stu-info">
            <div class="stu-name">{{ s.name }}</div>
            <div class="stu-meta">
              <span v-if="s.streak > 0" class="stu-streak">🔥{{ s.streak }}天</span>
              <span class="stu-stage">{{ s.stage || '评估中' }}</span>
            </div>
          </div>
          <div class="stu-progress">
            <div class="stu-bar">
              <div class="stu-bar-fill" :style="{ width: (s.todayPct || 0) + '%' }"></div>
            </div>
            <span class="stu-pct">{{ s.todayPct || 0 }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ 待审推送队列 ═══ -->
    <div class="section" v-if="pushQueue.length > 0">
      <h2 class="section-title">📋 待审推送</h2>
      <div class="push-list">
        <div v-for="p in pushQueue" :key="p.id" class="push-item">
          <div class="push-type">{{ p.type === 'ai' ? '🤖' : '📝' }}</div>
          <div class="push-body">
            <div class="push-target">给 {{ p.targetName }}</div>
            <div class="push-preview">{{ p.preview }}</div>
          </div>
          <div class="push-actions">
            <button class="push-btn push-btn--approve" @click="approvePush(p)">✓</button>
            <button class="push-btn push-btn--reject" @click="rejectPush(p)">✗</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ 快捷操作 ═══ -->
    <div class="quick-actions">
      <div class="qa-item" @click="$router.push('/chat')">
        <div class="qa-icon" style="background:#e3f2fd;color:#1565C0">💬</div>
        <span class="qa-label">AI 对话</span>
      </div>
      <div class="qa-item" @click="$router.push('/contribute')">
        <div class="qa-icon" style="background:#e8f5e9;color:#2e7d32">📝</div>
        <span class="qa-label">知识投稿</span>
      </div>
      <div class="qa-item" @click="$router.push('/learn')">
        <div class="qa-icon" style="background:#fff3e0;color:#e65100">📚</div>
        <span class="qa-label">学习中心</span>
      </div>
      <div class="qa-item" @click="$router.push('/programs')">
        <div class="qa-icon" style="background:#f3e5f5;color:#7b1fa2">📊</div>
        <span class="qa-label">监测方案</span>
      </div>
    </div>

    <!-- ═══ AI 教练助手提示 ═══ -->
    <div class="coach-tip" v-if="coachTip">
      <div class="tip-avatar">🤖</div>
      <div class="tip-bubble">
        <p class="tip-text">{{ coachTip }}</p>
        <button class="tip-action" @click="$router.push('/chat')">查看详情 →</button>
      </div>
    </div>
  </PageShell>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/api/index'
import PageShell from '@/components/common/PageShell.vue'
import UserHero from '@/components/common/UserHero.vue'
import GlobalSearch from '@/components/common/GlobalSearch.vue'
import { showToast } from 'vant'

const streakDays = ref(0)
const coachTip = ref('')

const stats = ref({
  studentCount: 0,
  todaySessions: 0,
  pendingPush: 0,
  totalCredits: 0,
})

interface Student {
  id: number
  name: string
  streak: number
  stage: string
  todayPct: number
}
const students = ref<Student[]>([])

interface PushItem {
  id: number
  type: string
  targetName: string
  preview: string
}
const pushQueue = ref<PushItem[]>([])

async function approvePush(p: PushItem) {
  try {
    await api.post(`/api/v1/coach-push/${p.id}/approve`)
    pushQueue.value = pushQueue.value.filter(x => x.id !== p.id)
    stats.value.pendingPush = Math.max(0, stats.value.pendingPush - 1)
    showToast({ message: '已审核通过', type: 'success' })
  } catch { showToast('操作失败') }
}

async function rejectPush(p: PushItem) {
  try {
    await api.post(`/api/v1/coach-push/${p.id}/reject`)
    pushQueue.value = pushQueue.value.filter(x => x.id !== p.id)
    stats.value.pendingPush = Math.max(0, stats.value.pendingPush - 1)
    showToast('已驳回')
  } catch { showToast('操作失败') }
}

onMounted(async () => {
  const [statsRes, studentsRes, pushRes, tipRes] = await Promise.allSettled([
    api.get('/api/v1/coach/dashboard-stats'),
    api.get('/api/v1/coach/students?limit=5'),
    api.get('/api/v1/coach-push/pending?limit=5'),
    api.get('/api/v1/coach-tip/today'),
  ])

  if (statsRes.status === 'fulfilled') {
    const d = statsRes.value as any
    stats.value = {
      studentCount: d.student_count ?? d.students ?? 0,
      todaySessions: d.today_sessions ?? 0,
      pendingPush: d.pending_push ?? 0,
      totalCredits: d.total_credits ?? 0,
    }
    streakDays.value = d.streak_days ?? 0
  }

  if (studentsRes.status === 'fulfilled') {
    const d = studentsRes.value as any
    const list = d.items || d.students || d || []
    students.value = (Array.isArray(list) ? list : []).slice(0, 5).map((s: any) => ({
      id: s.id,
      name: s.full_name || s.username || s.name || '学员',
      streak: s.streak_days || 0,
      stage: s.stage_name || s.stage || '',
      todayPct: s.today_completion || s.today_pct || 0,
    }))
  }

  if (pushRes.status === 'fulfilled') {
    const d = pushRes.value as any
    const list = d.items || d || []
    pushQueue.value = (Array.isArray(list) ? list : []).slice(0, 5).map((p: any) => ({
      id: p.id,
      type: p.source || 'ai',
      targetName: p.target_name || p.user_name || '学员',
      preview: (p.content || p.message || '').slice(0, 60),
    }))
  }

  if (tipRes.status === 'fulfilled') {
    coachTip.value = (tipRes.value as any)?.tip || ''
  }
})
</script>

<style scoped>
/* ── 概览卡片 ── */
.overview-cards {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 10px; padding: 16px 20px;
}
.ov-card {
  background: #fff; border-radius: 14px; padding: 14px 8px;
  text-align: center; box-shadow: 0 1px 6px rgba(0,0,0,0.04);
  cursor: pointer; transition: transform 0.15s;
}
.ov-card:active { transform: scale(0.96); }
.ov-card--alert .ov-num { color: #e53935; }
.ov-num { font-size: 24px; font-weight: 800; color: #111827; display: block; line-height: 1.2; }
.ov-label { font-size: 11px; color: #9ca3af; }

/* ── 通用 section ── */
.section { padding: 0 20px 16px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.section-title { font-size: 16px; font-weight: 700; color: #111827; margin: 0; }
.view-all-btn {
  background: none; border: none; color: #6b7280; font-size: 13px;
  cursor: pointer; padding: 0;
}
.empty-hint { font-size: 13px; color: #9ca3af; text-align: center; padding: 20px 0; }

/* ── 学员列表 ── */
.student-list { display: flex; flex-direction: column; gap: 8px; }
.student-card {
  display: flex; align-items: center; gap: 10px;
  background: #fff; border-radius: 12px; padding: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.stu-avatar {
  width: 36px; height: 36px; border-radius: 50%; flex-shrink: 0;
  background: #e8eaf6; color: #5c6bc0; font-weight: 700; font-size: 15px;
  display: flex; align-items: center; justify-content: center;
}
.stu-info { flex: 1; min-width: 0; }
.stu-name { font-size: 14px; font-weight: 600; color: #222; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.stu-meta { display: flex; gap: 8px; font-size: 11px; color: #9ca3af; margin-top: 2px; }
.stu-streak { color: #d97706; }
.stu-progress { display: flex; align-items: center; gap: 6px; flex-shrink: 0; width: 80px; }
.stu-bar { flex: 1; height: 4px; background: #f3f4f6; border-radius: 2px; overflow: hidden; }
.stu-bar-fill { height: 100%; background: #5c6bc0; border-radius: 2px; transition: width 0.3s; }
.stu-pct { font-size: 11px; color: #9ca3af; min-width: 30px; text-align: right; }

/* ── 推送队列 ── */
.push-list { display: flex; flex-direction: column; gap: 8px; }
.push-item {
  display: flex; align-items: center; gap: 10px;
  background: #fff; border-radius: 12px; padding: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.push-type { font-size: 22px; flex-shrink: 0; }
.push-body { flex: 1; min-width: 0; }
.push-target { font-size: 12px; color: #6b7280; font-weight: 500; }
.push-preview { font-size: 13px; color: #374151; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.push-actions { display: flex; gap: 6px; flex-shrink: 0; }
.push-btn {
  width: 32px; height: 32px; border-radius: 50%; border: none;
  font-size: 14px; cursor: pointer; display: flex; align-items: center; justify-content: center;
}
.push-btn--approve { background: #e8f5e9; color: #2e7d32; }
.push-btn--approve:active { background: #c8e6c9; }
.push-btn--reject { background: #fce4ec; color: #c62828; }
.push-btn--reject:active { background: #f8bbd0; }

/* ── 快捷操作 ── */
.quick-actions {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 12px; padding: 0 20px 16px;
}
.qa-item { display: flex; flex-direction: column; align-items: center; gap: 6px; cursor: pointer; }
.qa-item:active { opacity: 0.7; }
.qa-icon {
  width: 48px; height: 48px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px;
}
.qa-label { font-size: 12px; color: #374151; font-weight: 500; }

/* ── AI提示 ── */
.coach-tip {
  display: flex; gap: 10px; margin: 0 20px 20px;
  padding: 16px; background: #f0fdf4; border-radius: 16px;
}
.tip-avatar { font-size: 24px; flex-shrink: 0; }
.tip-bubble { flex: 1; }
.tip-text { font-size: 13px; color: #374151; margin: 0 0 8px; line-height: 1.5; }
.tip-action {
  background: none; border: none; color: #10b981;
  font-size: 13px; font-weight: 600; cursor: pointer; padding: 0;
}
</style>
