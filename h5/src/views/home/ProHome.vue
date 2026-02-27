<template>
  <!--
    Promoter(L4) / Supervisor(L4) 促进师·督导首页
    核心: 团队管理 + 质量指标 + 培训进度 + 审核队列
  -->
  <PageShell :show-nav-bar="false" :show-tab-bar="true" no-padding>
    <UserHero :streak-days="streakDays" />

    <div style="padding: 0 20px;">
      <GlobalSearch />
    </div>

    <!-- ═══ 团队概览 ═══ -->
    <div class="overview-cards">
      <div class="ov-card">
        <span class="ov-num">{{ stats.coachCount }}</span>
        <span class="ov-label">教练</span>
      </div>
      <div class="ov-card">
        <span class="ov-num">{{ stats.studentCount }}</span>
        <span class="ov-label">学员</span>
      </div>
      <div class="ov-card">
        <span class="ov-num">{{ stats.activeToday }}</span>
        <span class="ov-label">今日活跃</span>
      </div>
      <div class="ov-card" :class="{ 'ov-card--alert': stats.pendingReview > 0 }">
        <span class="ov-num">{{ stats.pendingReview }}</span>
        <span class="ov-label">待审核</span>
      </div>
    </div>

    <!-- ═══ 质量指标 ═══ -->
    <div class="section">
      <h2 class="section-title">{{ isSupervisor ? '🛡️ 服务质量' : '⭐ 团队绩效' }}</h2>
      <div class="quality-grid">
        <div class="q-card">
          <div class="q-ring">
            <svg viewBox="0 0 60 60">
              <circle cx="30" cy="30" r="24" class="q-ring-bg" />
              <circle cx="30" cy="30" r="24" class="q-ring-fill"
                :stroke-dasharray="`${quality.satisfaction * 1.508} 150.8`"
                :style="{ stroke: quality.satisfaction >= 80 ? '#10b981' : '#f59e0b' }" />
            </svg>
            <span class="q-ring-val">{{ quality.satisfaction }}</span>
          </div>
          <span class="q-label">满意度</span>
        </div>
        <div class="q-card">
          <div class="q-ring">
            <svg viewBox="0 0 60 60">
              <circle cx="30" cy="30" r="24" class="q-ring-bg" />
              <circle cx="30" cy="30" r="24" class="q-ring-fill"
                :stroke-dasharray="`${quality.completion * 1.508} 150.8`"
                :style="{ stroke: quality.completion >= 70 ? '#3b82f6' : '#f59e0b' }" />
            </svg>
            <span class="q-ring-val">{{ quality.completion }}</span>
          </div>
          <span class="q-label">完成率</span>
        </div>
        <div class="q-card">
          <div class="q-ring">
            <svg viewBox="0 0 60 60">
              <circle cx="30" cy="30" r="24" class="q-ring-bg" />
              <circle cx="30" cy="30" r="24" class="q-ring-fill"
                :stroke-dasharray="`${quality.retention * 1.508} 150.8`"
                :style="{ stroke: quality.retention >= 75 ? '#8b5cf6' : '#f59e0b' }" />
            </svg>
            <span class="q-ring-val">{{ quality.retention }}</span>
          </div>
          <span class="q-label">留存率</span>
        </div>
      </div>
    </div>

    <!-- ═══ 我的教练团队 ═══ -->
    <div class="section">
      <div class="section-header">
        <h2 class="section-title">👥 教练团队</h2>
        <button class="view-all-btn" @click="$router.push('/coach-directory')">管理 →</button>
      </div>
      <div v-if="coaches.length === 0" class="empty-hint">暂无教练数据</div>
      <div v-else class="coach-list">
        <div v-for="c in coaches" :key="c.id" class="coach-card">
          <div class="cc-avatar" :style="{ background: c.color }">{{ (c.name || '?').charAt(0) }}</div>
          <div class="cc-info">
            <div class="cc-name">{{ c.name }}</div>
            <div class="cc-meta">{{ c.studentCount }}学员 · {{ c.sessionCount }}次会话</div>
          </div>
          <div class="cc-score" :class="scoreClass(c.score)">{{ c.score }}</div>
        </div>
      </div>
    </div>

    <!-- ═══ 快捷操作 ═══ -->
    <div class="quick-actions">
      <div class="qa-item" @click="$router.push('/chat')">
        <div class="qa-icon" style="background:#e3f2fd;color:#1565C0">💬</div>
        <span class="qa-label">AI 助手</span>
      </div>
      <div class="qa-item" @click="$router.push('/contribute')">
        <div class="qa-icon" style="background:#e8f5e9;color:#2e7d32">📝</div>
        <span class="qa-label">{{ isSupervisor ? '督导记录' : '课程开发' }}</span>
      </div>
      <div class="qa-item" @click="$router.push('/learn')">
        <div class="qa-icon" style="background:#fff3e0;color:#e65100">📚</div>
        <span class="qa-label">学习中心</span>
      </div>
      <div class="qa-item" @click="$router.push('/promotion-progress')">
        <div class="qa-icon" style="background:#fce4ec;color:#c62828">🏆</div>
        <span class="qa-label">晋级进度</span>
      </div>
    </div>
  </PageShell>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/api/index'
import storage from '@/utils/storage'
import PageShell from '@/components/common/PageShell.vue'
import UserHero from '@/components/common/UserHero.vue'
import GlobalSearch from '@/components/common/GlobalSearch.vue'

const streakDays = ref(0)
const authUser = storage.getAuthUser()
const isSupervisor = (authUser?.role || '').toLowerCase() === 'supervisor'

const stats = ref({
  coachCount: 0,
  studentCount: 0,
  activeToday: 0,
  pendingReview: 0,
})

const quality = ref({
  satisfaction: 0,
  completion: 0,
  retention: 0,
})

interface Coach {
  id: number
  name: string
  studentCount: number
  sessionCount: number
  score: number
  color: string
}
const coaches = ref<Coach[]>([])

const COLORS = ['#e8eaf6', '#e3f2fd', '#e8f5e9', '#fff3e0', '#fce4ec', '#f3e5f5']

function scoreClass(score: number) {
  if (score >= 90) return 'sc--high'
  if (score >= 70) return 'sc--mid'
  return 'sc--low'
}

onMounted(async () => {
  const [statsRes, qualityRes, coachesRes] = await Promise.allSettled([
    api.get('/api/v1/coach/team-stats'),
    api.get('/api/v1/coach/quality-metrics'),
    api.get('/api/v1/coach/team-members?limit=6'),
  ])

  if (statsRes.status === 'fulfilled') {
    const d = statsRes.value as any
    stats.value = {
      coachCount: d.coach_count ?? 0,
      studentCount: d.student_count ?? 0,
      activeToday: d.active_today ?? 0,
      pendingReview: d.pending_review ?? 0,
    }
    streakDays.value = d.streak_days ?? 0
  }

  if (qualityRes.status === 'fulfilled') {
    const d = qualityRes.value as any
    quality.value = {
      satisfaction: d.satisfaction ?? 0,
      completion: d.completion ?? 0,
      retention: d.retention ?? 0,
    }
  }

  if (coachesRes.status === 'fulfilled') {
    const d = coachesRes.value as any
    const list = d.items || d.coaches || d || []
    coaches.value = (Array.isArray(list) ? list : []).slice(0, 6).map((c: any, i: number) => ({
      id: c.id,
      name: c.full_name || c.username || c.name || '教练',
      studentCount: c.student_count ?? 0,
      sessionCount: c.session_count ?? 0,
      score: c.score ?? c.performance_score ?? 0,
      color: COLORS[i % COLORS.length],
    }))
  }
})
</script>

<style scoped>
/* ── 概览 ── */
.overview-cards {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 10px; padding: 16px 20px;
}
.ov-card {
  background: #fff; border-radius: 14px; padding: 14px 8px;
  text-align: center; box-shadow: 0 1px 6px rgba(0,0,0,0.04);
}
.ov-card--alert .ov-num { color: #e53935; }
.ov-num { font-size: 24px; font-weight: 800; color: #111827; display: block; line-height: 1.2; }
.ov-label { font-size: 11px; color: #9ca3af; }

/* ── section ── */
.section { padding: 0 20px 16px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.section-title { font-size: 16px; font-weight: 700; color: #111827; margin: 0 0 12px; }
.view-all-btn {
  background: none; border: none; color: #6b7280; font-size: 13px; cursor: pointer; padding: 0;
}
.empty-hint { font-size: 13px; color: #9ca3af; text-align: center; padding: 20px 0; }

/* ── 质量环 ── */
.quality-grid { display: flex; justify-content: space-around; }
.q-card { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.q-ring { position: relative; width: 60px; height: 60px; }
.q-ring svg { transform: rotate(-90deg); }
.q-ring-bg { fill: none; stroke: #f3f4f6; stroke-width: 5; }
.q-ring-fill { fill: none; stroke-width: 5; stroke-linecap: round; transition: stroke-dasharray 0.8s ease; }
.q-ring-val {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  font-size: 16px; font-weight: 800; color: #111827;
}
.q-label { font-size: 12px; color: #6b7280; }

/* ── 教练列表 ── */
.coach-list { display: flex; flex-direction: column; gap: 8px; }
.coach-card {
  display: flex; align-items: center; gap: 10px;
  background: #fff; border-radius: 12px; padding: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.cc-avatar {
  width: 36px; height: 36px; border-radius: 50%; flex-shrink: 0;
  color: #5c6bc0; font-weight: 700; font-size: 15px;
  display: flex; align-items: center; justify-content: center;
}
.cc-info { flex: 1; min-width: 0; }
.cc-name { font-size: 14px; font-weight: 600; color: #222; }
.cc-meta { font-size: 11px; color: #9ca3af; margin-top: 2px; }
.cc-score {
  font-size: 18px; font-weight: 800; flex-shrink: 0;
}
.sc--high { color: #10b981; }
.sc--mid { color: #3b82f6; }
.sc--low { color: #f59e0b; }

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
.qa-label { font-size: 12px; color: #374151; font-weight: 500; text-align: center; }
</style>
