<template>
  <div class="sharer-workbench">
    <!-- Header -->
    <div class="wb-header">
      <div class="wb-header-left">
        <h1 class="wb-title">{{ greeting }}, {{ username }}</h1>
        <div class="wb-subtitle">
          <span class="role-badge">分享者</span>
          <span v-if="currentLevel" class="level-badge">{{ currentLevel.icon }} {{ currentLevel.name }}</span>
        </div>
      </div>
      <UserAvatarPopover :size="48" />
    </div>

    <!-- Stats Bar -->
    <div class="stats-bar">
      <div class="stat-card">
        <div class="stat-value">{{ points.growth?.current ?? 0 }}</div>
        <div class="stat-label">成长积分</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ points.contribution?.current ?? 0 }}</div>
        <div class="stat-label">贡献积分</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ points.influence?.current ?? 0 }}</div>
        <div class="stat-label">影响力积分</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ companionStats.active_count ?? 0 }}</div>
        <div class="stat-label">同道者</div>
      </div>
    </div>

    <!-- Tab Bar -->
    <div class="tab-bar">
      <button
        class="tab-btn" :class="{ active: activeTab === 'contributions' }"
        @click="activeTab = 'contributions'"
      >我的分享</button>
      <button
        class="tab-btn" :class="{ active: activeTab === 'benefits' }"
        @click="activeTab = 'benefits'"
      >我的权益</button>
      <button
        class="tab-btn" :class="{ active: activeTab === 'profile' }"
        @click="activeTab = 'profile'"
      >个人档案</button>
    </div>

    <!-- Tab Content -->
    <div v-show="activeTab === 'contributions'">
      <MyContributions />
    </div>
    <div v-show="activeTab === 'benefits'">
      <MyBenefits />
    </div>
    <div v-show="activeTab === 'profile'">
      <PersonalHealthProfile :embedded="true" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import request from '@/api/request'
import { UserAvatarPopover, PersonalHealthProfile, MyContributions, MyBenefits } from '@/components/health'

const username = localStorage.getItem('admin_username') || '分享者'
const activeTab = ref('contributions')
const currentLevel = ref<any>(null)
const points = ref<any>({})
const companionStats = ref<any>({})

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 12) return '早上好'
  if (h < 18) return '下午好'
  return '晚上好'
})

async function loadHeaderData() {
  const results = await Promise.allSettled([
    request.get('/v1/coach-levels/progress'),
    request.get('/v1/companions/stats'),
  ])

  if (results[0].status === 'fulfilled') {
    const d = results[0].value.data
    currentLevel.value = d.current_level
    points.value = d.points || {}
  }

  if (results[1].status === 'fulfilled') {
    companionStats.value = results[1].value.data || {}
  }
}

onMounted(loadHeaderData)
</script>

<style scoped>
.sharer-workbench {
  min-height: 100vh;
  background: #f8fafc;
  padding: 24px;
}

/* Header */
.wb-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.wb-title {
  font-size: 22px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 6px 0;
}
.wb-subtitle {
  display: flex;
  gap: 8px;
  align-items: center;
}
.role-badge {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 12px;
  background: #dbeafe;
  color: #2563eb;
}
.level-badge {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 12px;
  background: #fef3c7;
  color: #92400e;
}

/* Stats Bar */
.stats-bar {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}
.stat-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  text-align: center;
}
.stat-value {
  font-size: 24px;
  font-weight: 800;
  color: #111827;
}
.stat-label {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}

/* Tab Bar */
.tab-bar {
  display: flex;
  gap: 4px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 4px;
  margin-bottom: 20px;
}
.tab-btn {
  flex: 1;
  padding: 10px 0;
  font-size: 14px;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
}
.tab-btn:hover {
  color: #374151;
  background: #f9fafb;
}
.tab-btn.active {
  background: #3b82f6;
  color: #fff;
}

/* Responsive */
@media (max-width: 768px) {
  .stats-bar {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
