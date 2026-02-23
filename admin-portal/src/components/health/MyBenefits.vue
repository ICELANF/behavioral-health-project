<template>
  <div class="my-benefits">
    <!-- Current level benefits -->
    <div class="section-card">
      <div class="section-title">当前权益 · {{ currentLevel?.name || '加载中...' }}</div>
      <div class="benefit-grid">
        <div
          v-for="b in currentBenefits" :key="b.label"
          class="benefit-card unlocked"
        >
          <div class="benefit-icon">{{ b.icon }}</div>
          <div class="benefit-label">{{ b.label }}</div>
          <div class="benefit-status unlocked-status">已解锁</div>
        </div>
      </div>
    </div>

    <!-- Next level benefits -->
    <div class="section-card" v-if="nextLevel">
      <div class="section-title-row">
        <div class="section-title">下一级解锁 · {{ nextLevel.name }}</div>
        <span class="locked-badge">待解锁</span>
      </div>
      <div class="benefit-grid">
        <div
          v-for="b in nextBenefits" :key="b.label"
          class="benefit-card locked"
        >
          <div class="benefit-icon">{{ b.icon }}</div>
          <div class="benefit-label">{{ b.label }}</div>
          <div class="benefit-status locked-status">待解锁</div>
        </div>
      </div>
    </div>

    <!-- Points guide -->
    <div class="section-card">
      <div class="section-title">积分获取指南</div>
      <div class="guide-list">
        <div class="guide-group">
          <div class="guide-group-title">成长积分</div>
          <div class="guide-item">持续学习 <span class="guide-pts">+3/节</span></div>
          <div class="guide-item">深度复习 <span class="guide-pts">+10/模块</span></div>
          <div class="guide-item">完成测评 <span class="guide-pts">+15/次</span></div>
        </div>
        <div class="guide-group">
          <div class="guide-group-title">贡献积分</div>
          <div class="guide-item">成功引领同道者 <span class="guide-pts">+50/人</span></div>
          <div class="guide-item">经验分享 <span class="guide-pts">+10/篇</span></div>
          <div class="guide-item">社区答疑 <span class="guide-pts">+5/次</span></div>
        </div>
        <div class="guide-group">
          <div class="guide-group-title">影响力积分</div>
          <div class="guide-item">内容被点赞 <span class="guide-pts">+1</span></div>
          <div class="guide-item">内容被收藏 <span class="guide-pts">+2</span></div>
          <div class="guide-item">内容被引用 <span class="guide-pts">+5</span></div>
        </div>
      </div>
    </div>

    <!-- Promotion checklist -->
    <div class="section-card" v-if="nextLevel">
      <div class="section-title">晋级条件 ({{ currentLevel?.name }} → {{ nextLevel.name }})</div>
      <div class="checklist">
        <div class="check-item" v-for="item in promotionChecklist" :key="item.label">
          <span class="check-icon" :class="{ checked: item.met }">{{ item.met ? '&#9745;' : '&#9744;' }}</span>
          <span class="check-label">{{ item.label }}</span>
          <span class="check-gap" v-if="!item.met && item.gap">{{ item.gap }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import request from '@/api/request'

const currentLevel = ref<any>(null)
const nextLevel = ref<any>(null)
const points = ref<any>({})
const companions = ref<any>({})

// --- Level Benefits (static, from contract registry) ---
interface Benefit { icon: string; label: string }

const LEVEL_BENEFITS: Record<number, Benefit[]> = {
  0: [
    { icon: '👀', label: '浏览公开内容' },
    { icon: '🤖', label: '3个基础Agent' },
    { icon: '📝', label: '基础测评' },
  ],
  1: [
    { icon: '📖', label: '全部学习内容' },
    { icon: '🤖', label: '9个Agent' },
    { icon: '📊', label: '学习进度追踪' },
    { icon: '🎯', label: '个性化推荐' },
    { icon: '💬', label: '社区互动' },
  ],
  2: [
    { icon: '💬', label: '发布分享' },
    { icon: '🤝', label: '引领新人' },
    { icon: '🏅', label: '分享者徽章' },
    { icon: '🤖', label: '14个Agent' },
    { icon: '📚', label: '投稿内容' },
    { icon: '⭐', label: '影响力积分' },
  ],
  3: [
    { icon: '🎓', label: '一对一辅导' },
    { icon: '👥', label: '带学习小组' },
    { icon: '📜', label: '认证证书' },
    { icon: '💰', label: '收取费用' },
    { icon: '📊', label: 'KPI仪表盘' },
  ],
  4: [
    { icon: '🏢', label: '区域管理' },
    { icon: '📋', label: '培训课程设计' },
    { icon: '🔬', label: '数据分析权限' },
    { icon: '🎖️', label: '推广者认证' },
  ],
  5: [
    { icon: '🌐', label: '平台共建' },
    { icon: '📖', label: '课程审核权' },
    { icon: '🏆', label: '大师荣誉' },
    { icon: '🔑', label: '全部高级功能' },
  ],
}

const currentLevelNum = computed(() => {
  if (!currentLevel.value) return 2
  const lvl = currentLevel.value.level ?? currentLevel.value.role_level
  if (typeof lvl === 'number') return lvl
  return 2
})

const nextLevelNum = computed(() => {
  return currentLevelNum.value + 1
})

const currentBenefits = computed(() => {
  const all: Benefit[] = []
  for (let i = 0; i <= currentLevelNum.value; i++) {
    if (LEVEL_BENEFITS[i]) {
      all.push(...LEVEL_BENEFITS[i])
    }
  }
  return all
})

const nextBenefits = computed(() => {
  return LEVEL_BENEFITS[nextLevelNum.value] || []
})

const promotionChecklist = computed(() => {
  const items: { label: string; met: boolean; gap?: string }[] = []
  const p = points.value

  if (p.growth) {
    const cur = p.growth.current ?? 0
    const req = p.growth.required ?? 0
    const met = cur >= req
    items.push({
      label: `成长积分 ≥ ${req}  (当前 ${cur})`,
      met,
      gap: met ? undefined : `还差 ${req - cur}`
    })
  }
  if (p.contribution) {
    const cur = p.contribution.current ?? 0
    const req = p.contribution.required ?? 0
    const met = cur >= req
    items.push({
      label: `贡献积分 ≥ ${req}  (当前 ${cur})`,
      met,
      gap: met ? undefined : `还差 ${req - cur}`
    })
  }
  if (p.influence) {
    const cur = p.influence.current ?? 0
    const req = p.influence.required ?? 0
    const met = cur >= req
    items.push({
      label: `影响力积分 ≥ ${req}  (当前 ${cur})`,
      met,
      gap: met ? undefined : `还差 ${req - cur}`
    })
  }

  if (currentLevelNum.value >= 2) {
    items.push({ label: '通过考试', met: false, gap: '未完成' })
  }

  if (companions.value.required) {
    const cur = companions.value.current ?? 0
    const req = companions.value.required ?? 4
    const met = cur >= req
    items.push({
      label: `${req}位同道者达L${currentLevelNum.value - 1}  (当前 ${cur}/${req})`,
      met,
      gap: met ? undefined : `还差 ${req - cur} 位`
    })
  }

  return items
})

async function loadData() {
  try {
    const res = await request.get('/v1/coach-levels/progress')
    const d = res.data
    currentLevel.value = d.current_level
    nextLevel.value = d.next_level
    points.value = d.points || {}
    companions.value = d.companions || {}
  } catch (e) {
    console.warn('Failed to load benefits data:', e)
  }
}

onMounted(loadData)
</script>

<style scoped>
.my-benefits {
  padding: 0;
}

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

/* Benefits Grid */
.benefit-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.benefit-card {
  border-radius: 10px;
  padding: 16px;
  text-align: center;
  transition: transform 0.15s;
}
.benefit-card:hover {
  transform: translateY(-2px);
}
.benefit-card.unlocked {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
}
.benefit-card.locked {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}
.benefit-icon {
  font-size: 28px;
  margin-bottom: 8px;
}
.benefit-label {
  font-size: 13px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 6px;
}
.benefit-status {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  display: inline-block;
}
.unlocked-status {
  background: #dcfce7;
  color: #166534;
}
.locked-status {
  background: #f3f4f6;
  color: #9ca3af;
}
.locked-badge {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 10px;
  background: #f3f4f6;
  color: #9ca3af;
}

/* Points Guide */
.guide-list {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.guide-group-title {
  font-size: 13px;
  font-weight: 700;
  color: #374151;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 2px solid #e5e7eb;
}
.guide-item {
  font-size: 13px;
  color: #4b5563;
  padding: 4px 0;
  display: flex;
  justify-content: space-between;
}
.guide-pts {
  font-weight: 700;
  color: #059669;
  white-space: nowrap;
  margin-left: 8px;
}

/* Promotion Checklist */
.checklist {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.check-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #374151;
  padding: 8px 12px;
  border-radius: 8px;
  background: #f9fafb;
}
.check-icon {
  font-size: 18px;
  color: #d1d5db;
  flex-shrink: 0;
}
.check-icon.checked {
  color: #16a34a;
}
.check-label {
  flex: 1;
}
.check-gap {
  font-size: 12px;
  font-weight: 600;
  color: #f59e0b;
  white-space: nowrap;
}

/* Responsive */
@media (max-width: 768px) {
  .benefit-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .guide-list {
    grid-template-columns: 1fr;
  }
}
</style>
