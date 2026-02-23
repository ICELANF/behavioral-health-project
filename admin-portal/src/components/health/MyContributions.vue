<template>
  <div class="my-contributions">
    <!-- Level Progress -->
    <div class="section-card" v-if="currentLevel && nextLevel">
      <div class="section-title">等级进度</div>
      <div class="level-header">
        <span>{{ currentLevel.icon }} {{ currentLevel.name }}</span>
        <span class="level-arrow">&rarr;</span>
        <span>{{ nextLevel.icon }} {{ nextLevel.name }}</span>
      </div>
      <div class="progress-list">
        <div class="progress-item" v-for="dim in progressDimensions" :key="dim.key">
          <div class="progress-label">
            <span>{{ dim.label }}</span>
            <span class="progress-numbers">{{ dim.current }}/{{ dim.required }}</span>
          </div>
          <div class="progress-bar-bg">
            <div class="progress-bar-fill" :style="{ width: dim.pct + '%', background: dim.color }"></div>
          </div>
          <div class="progress-pct">{{ dim.pct }}%</div>
        </div>
      </div>
    </div>
    <div class="section-card" v-else-if="currentLevel && !nextLevel">
      <div class="section-title">等级进度</div>
      <div class="level-header">{{ currentLevel.icon }} {{ currentLevel.name }} - 已达最高等级</div>
    </div>

    <!-- Two-column body -->
    <div class="wb-body">
      <!-- Left: Contributions -->
      <div class="section-card wb-col">
        <div class="section-title-row">
          <div class="section-title">我的分享记录</div>
          <button class="btn-primary" @click="goContribute">+ 投稿新知识</button>
        </div>
        <div v-if="contributions.length === 0" class="empty-state">暂无分享记录，快去投稿吧</div>
        <div v-else class="contrib-list">
          <div class="contrib-item" v-for="c in contributions" :key="c.id">
            <div class="contrib-main">
              <div class="contrib-title">{{ c.title }}</div>
              <div class="contrib-meta">
                <span class="contrib-domain" v-if="c.domain_id">{{ c.domain_id }}</span>
                <span class="contrib-time">{{ formatDate(c.created_at) }}</span>
              </div>
            </div>
            <span class="status-tag" :class="'status-' + c.status">{{ statusLabel(c.status) }}</span>
          </div>
        </div>
      </div>

      <!-- Right: Companions -->
      <div class="section-card wb-col">
        <div class="section-title-row">
          <div class="section-title">我的同道者</div>
          <button class="btn-primary" @click="goInvite">+ 邀请同道者</button>
        </div>
        <div class="companion-summary">
          <span class="cs-item">活跃 <b>{{ companionStats.active_count ?? 0 }}</b></span>
          <span class="cs-item">毕业 <b>{{ companionStats.graduated_count ?? 0 }}</b></span>
          <span class="cs-item">退出 <b>{{ companionStats.dropped_count ?? 0 }}</b></span>
          <span class="cs-item" v-if="companionStats.avg_quality != null">平均质量 <b>{{ companionStats.avg_quality?.toFixed(1) }}</b></span>
        </div>
        <div v-if="mentees.length === 0" class="empty-state">暂无同道者关系</div>
        <div v-else class="mentee-list">
          <div class="mentee-card" v-for="m in mentees" :key="m.id">
            <div class="mentee-avatar">{{ (m.mentee_name || '?')[0] }}</div>
            <div class="mentee-info">
              <div class="mentee-name">{{ m.mentee_name || '未知' }}</div>
              <div class="mentee-meta">
                <span class="mentee-role" v-if="m.mentee_current_role">{{ roleLabel(m.mentee_current_role) }}</span>
                <span class="mentee-status" :class="'ms-' + (m.status || '').toLowerCase()">{{ companionStatusLabel(m.status) }}</span>
              </div>
            </div>
            <div class="mentee-score" v-if="m.quality_score != null">{{ m.quality_score.toFixed(1) }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'

const router = useRouter()

const currentLevel = ref<any>(null)
const nextLevel = ref<any>(null)
const points = ref<any>({})
const companions = ref<any>({})
const contributions = ref<any[]>([])
const mentees = ref<any[]>([])
const companionStats = ref<any>({})

const progressDimensions = computed(() => {
  const dims: any[] = []
  const p = points.value
  if (p.growth) {
    const req = p.growth.required || 1
    dims.push({ key: 'growth', label: '成长', current: p.growth.current, required: req, pct: Math.min(100, Math.round(p.growth.current / req * 100)), color: '#3b82f6' })
  }
  if (p.contribution) {
    const req = p.contribution.required || 1
    dims.push({ key: 'contribution', label: '贡献', current: p.contribution.current, required: req, pct: Math.min(100, Math.round(p.contribution.current / req * 100)), color: '#10b981' })
  }
  if (p.influence) {
    const req = p.influence.required || 1
    dims.push({ key: 'influence', label: '影响力', current: p.influence.current, required: req, pct: Math.min(100, Math.round(p.influence.current / req * 100)), color: '#f59e0b' })
  }
  if (companions.value.required) {
    const req = companions.value.required || 1
    const cur = companions.value.current || 0
    dims.push({ key: 'companions', label: '同道者', current: cur, required: req, pct: Math.min(100, Math.round(cur / req * 100)), color: '#8b5cf6' })
  }
  return dims
})

// --- Helpers ---
function formatDate(iso: string) {
  if (!iso) return ''
  return iso.slice(0, 10)
}

function statusLabel(s: string) {
  const map: Record<string, string> = { draft: '草稿', pending: '待审核', approved: '已通过', rejected: '未通过', error: '错误' }
  return map[s] || s
}

function roleLabel(r: string) {
  const map: Record<string, string> = { OBSERVER: '观察者', GROWER: '成长者', SHARER: '分享者', COACH: '教练', PROMOTER: '推广者', SUPERVISOR: '督导', MASTER: '大师', ADMIN: '管理员' }
  return map[r] || r
}

function companionStatusLabel(s: string) {
  const map: Record<string, string> = { ACTIVE: '活跃', GRADUATED: '毕业', DROPPED: '退出' }
  return map[s] || s || '未知'
}

function goContribute() {
  router.push('/content/review')
}

function goInvite() {
  router.push('/admin/credit-system/companions')
}

async function loadData() {
  const results = await Promise.allSettled([
    request.get('/v1/coach-levels/progress'),
    request.get('/v1/contributions/my'),
    request.get('/v1/companions/my-mentees'),
    request.get('/v1/companions/stats'),
  ])

  if (results[0].status === 'fulfilled') {
    const d = results[0].value.data
    currentLevel.value = d.current_level
    nextLevel.value = d.next_level
    points.value = d.points || {}
    companions.value = d.companions || {}
  }

  if (results[1].status === 'fulfilled') {
    const d = results[1].value.data
    contributions.value = d.data || d || []
  }

  if (results[2].status === 'fulfilled') {
    mentees.value = results[2].value.data || []
  }

  if (results[3].status === 'fulfilled') {
    companionStats.value = results[3].value.data || {}
  }
}

onMounted(loadData)
</script>

<style scoped>
.my-contributions {
  padding: 0;
}

/* Section Card */
.section-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}
.section-title {
  font-size: 15px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 12px;
}
.section-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.section-title-row .section-title {
  margin-bottom: 0;
}

/* Level Progress */
.level-header {
  font-size: 14px;
  color: #374151;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.level-arrow {
  color: #9ca3af;
}
.progress-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.progress-item {
  display: flex;
  align-items: center;
  gap: 12px;
}
.progress-label {
  width: 140px;
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #374151;
}
.progress-numbers {
  color: #9ca3af;
  font-size: 12px;
}
.progress-bar-bg {
  flex: 1;
  height: 8px;
  background: #f3f4f6;
  border-radius: 4px;
  overflow: hidden;
}
.progress-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}
.progress-pct {
  width: 40px;
  text-align: right;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
}

/* Two-column body */
.wb-body {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
.wb-col {
  margin-bottom: 0;
}

/* Button */
.btn-primary {
  font-size: 13px;
  font-weight: 600;
  padding: 6px 14px;
  border-radius: 8px;
  border: none;
  background: #3b82f6;
  color: #fff;
  cursor: pointer;
}
.btn-primary:hover {
  background: #2563eb;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 32px 0;
  color: #9ca3af;
  font-size: 14px;
}

/* Contributions list */
.contrib-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 360px;
  overflow-y: auto;
}
.contrib-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border: 1px solid #f3f4f6;
  border-radius: 8px;
}
.contrib-item:hover {
  background: #f9fafb;
}
.contrib-title {
  font-size: 13px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 2px;
}
.contrib-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
  color: #9ca3af;
}
.contrib-domain {
  color: #6b7280;
}
.status-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  white-space: nowrap;
}
.status-draft { background: #f3f4f6; color: #6b7280; }
.status-pending { background: #fef3c7; color: #92400e; }
.status-approved { background: #dcfce7; color: #166534; }
.status-rejected { background: #fee2e2; color: #991b1b; }
.status-error { background: #fee2e2; color: #991b1b; }

/* Companion Summary */
.companion-summary {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 13px;
  color: #6b7280;
}
.cs-item b {
  color: #111827;
}

/* Mentee list */
.mentee-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 360px;
  overflow-y: auto;
}
.mentee-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid #f3f4f6;
  border-radius: 8px;
}
.mentee-card:hover {
  background: #f9fafb;
}
.mentee-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #dbeafe;
  color: #2563eb;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}
.mentee-info {
  flex: 1;
  min-width: 0;
}
.mentee-name {
  font-size: 13px;
  font-weight: 600;
  color: #111827;
}
.mentee-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
  margin-top: 2px;
}
.mentee-role {
  color: #6b7280;
}
.mentee-status {
  font-weight: 600;
}
.ms-active { color: #16a34a; }
.ms-graduated { color: #2563eb; }
.ms-dropped { color: #dc2626; }
.mentee-score {
  font-size: 14px;
  font-weight: 700;
  color: #f59e0b;
}

/* Responsive */
@media (max-width: 768px) {
  .wb-body {
    grid-template-columns: 1fr;
  }
}
</style>
