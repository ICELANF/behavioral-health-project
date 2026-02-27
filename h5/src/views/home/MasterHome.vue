<template>
  <!--
    Master(L5) 大师首页
    核心: 平台全局视野 + 社区治理 + 知识贡献 + 标准建设
  -->
  <PageShell :show-nav-bar="false" :show-tab-bar="true" no-padding>
    <UserHero :streak-days="streakDays" />

    <div style="padding: 0 20px;">
      <GlobalSearch />
    </div>

    <!-- ═══ 平台全局概览 ═══ -->
    <div class="overview-cards">
      <div class="ov-card">
        <span class="ov-num">{{ stats.totalUsers }}</span>
        <span class="ov-label">平台用户</span>
      </div>
      <div class="ov-card">
        <span class="ov-num">{{ stats.activeCoaches }}</span>
        <span class="ov-label">活跃教练</span>
      </div>
      <div class="ov-card">
        <span class="ov-num">{{ stats.contentCount }}</span>
        <span class="ov-label">知识内容</span>
      </div>
      <div class="ov-card">
        <span class="ov-num">{{ stats.communityScore }}</span>
        <span class="ov-label">社区健康</span>
      </div>
    </div>

    <!-- ═══ 社区趋势 ═══ -->
    <div class="section">
      <h2 class="section-title">📊 社区趋势</h2>
      <div class="trend-grid">
        <div v-for="t in trends" :key="t.label" class="trend-item">
          <span class="trend-val" :class="t.dir">{{ t.value }}</span>
          <span class="trend-label">{{ t.label }}</span>
          <span class="trend-arrow">{{ t.dir === 'up' ? '↑' : t.dir === 'down' ? '↓' : '─' }}</span>
        </div>
      </div>
    </div>

    <!-- ═══ 知识贡献 ═══ -->
    <div class="section">
      <h2 class="section-title">👑 我的贡献</h2>
      <div class="contrib-row">
        <div class="contrib-item">
          <span class="contrib-num">{{ contrib.articles }}</span>
          <span class="contrib-label">文章</span>
        </div>
        <div class="contrib-item">
          <span class="contrib-num">{{ contrib.courses }}</span>
          <span class="contrib-label">课程</span>
        </div>
        <div class="contrib-item">
          <span class="contrib-num">{{ contrib.mentored }}</span>
          <span class="contrib-label">指导</span>
        </div>
        <div class="contrib-item">
          <span class="contrib-num">{{ contrib.reviews }}</span>
          <span class="contrib-label">审核</span>
        </div>
      </div>
    </div>

    <!-- ═══ 快捷操作 ═══ -->
    <div class="quick-actions">
      <div class="qa-item" @click="$router.push('/chat')">
        <div class="qa-icon" style="background:#fff8e1;color:#f57f17">💬</div>
        <span class="qa-label">AI 助手</span>
      </div>
      <div class="qa-item" @click="$router.push('/contribute')">
        <div class="qa-icon" style="background:#e8f5e9;color:#2e7d32">📝</div>
        <span class="qa-label">知识投稿</span>
      </div>
      <div class="qa-item" @click="$router.push('/coach-directory')">
        <div class="qa-icon" style="background:#e8eaf6;color:#5c6bc0">👥</div>
        <span class="qa-label">教练目录</span>
      </div>
      <div class="qa-item" @click="$router.push('/expert-hub')">
        <div class="qa-icon" style="background:#fce4ec;color:#c62828">🏛️</div>
        <span class="qa-label">专家工作室</span>
      </div>
    </div>

    <!-- ═══ 平台宣言 ═══ -->
    <div class="manifesto">
      <p>以行为科学为基础，以数据为驱动</p>
      <p>构建可持续的全民健康行为生态</p>
    </div>
  </PageShell>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/api/index'
import PageShell from '@/components/common/PageShell.vue'
import UserHero from '@/components/common/UserHero.vue'
import GlobalSearch from '@/components/common/GlobalSearch.vue'

const streakDays = ref(0)

const stats = ref({
  totalUsers: 0,
  activeCoaches: 0,
  contentCount: 0,
  communityScore: 0,
})

interface Trend { label: string; value: string; dir: string }
const trends = ref<Trend[]>([])

const contrib = ref({
  articles: 0,
  courses: 0,
  mentored: 0,
  reviews: 0,
})

onMounted(async () => {
  const [statsRes, contribRes] = await Promise.allSettled([
    api.get('/api/v1/analytics/platform-overview'),
    api.get('/api/v1/sharer/contribution-stats'),
  ])

  if (statsRes.status === 'fulfilled') {
    const d = statsRes.value as any
    stats.value = {
      totalUsers: d.total_users ?? 0,
      activeCoaches: d.active_coaches ?? 0,
      contentCount: d.content_count ?? 0,
      communityScore: d.community_score ?? 0,
    }
    streakDays.value = d.streak_days ?? 0
    trends.value = (d.trends || []).map((t: any) => ({
      label: t.label || '',
      value: String(t.value ?? 0),
      dir: t.dir || t.trend || 'flat',
    }))
  }

  if (contribRes.status === 'fulfilled') {
    const d = contribRes.value as any
    contrib.value = {
      articles: d.published ?? d.articles ?? 0,
      courses: d.courses ?? 0,
      mentored: d.mentored ?? d.submitted ?? 0,
      reviews: d.reviews ?? d.pending ?? 0,
    }
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
.ov-num { font-size: 24px; font-weight: 800; color: #111827; display: block; line-height: 1.2; }
.ov-label { font-size: 11px; color: #9ca3af; }

/* ── section ── */
.section { padding: 0 20px 16px; }
.section-title { font-size: 16px; font-weight: 700; color: #111827; margin: 0 0 12px; }

/* ── 趋势 ── */
.trend-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;
}
.trend-item {
  background: #fff; border-radius: 12px; padding: 12px;
  text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  display: flex; flex-direction: column; align-items: center; gap: 2px;
}
.trend-val { font-size: 20px; font-weight: 800; color: #111827; }
.trend-val.up { color: #10b981; }
.trend-val.down { color: #ef4444; }
.trend-label { font-size: 11px; color: #9ca3af; }
.trend-arrow { font-size: 12px; color: #9ca3af; }

/* ── 贡献 ── */
.contrib-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.contrib-item {
  background: linear-gradient(135deg, #fff8e1, #ffecb3);
  border-radius: 12px; padding: 14px 8px; text-align: center;
}
.contrib-num { font-size: 22px; font-weight: 800; color: #92400e; display: block; }
.contrib-label { font-size: 11px; color: #a16207; }

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

/* ── 宣言 ── */
.manifesto {
  margin: 8px 20px 20px; padding: 16px;
  border-left: 3px solid #f9a825;
  background: rgba(249,168,37,0.06);
  border-radius: 0 12px 12px 0;
}
.manifesto p { font-size: 12px; color: #888; margin: 0; line-height: 2; }
</style>
