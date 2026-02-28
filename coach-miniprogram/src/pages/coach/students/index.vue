<template>
  <view class="cs-page">

    <!-- 导航栏 -->
    <view class="cs-navbar safe-area-top">
      <view class="cs-navbar__back" @tap="goBack">
        <text class="cs-navbar__arrow">‹</text>
      </view>
      <text class="cs-navbar__title">我的学员</text>
      <view class="cs-navbar__placeholder"></view>
    </view>

    <!-- 搜索框 -->
    <view class="cs-search">
      <view class="cs-search__box">
        <text class="cs-search__icon">🔍</text>
        <input
          class="cs-search__input"
          placeholder="搜索学员姓名"
          :value="keyword"
          @input="onSearch"
        />
        <text v-if="keyword" class="cs-search__clear" @tap="keyword = ''">✕</text>
      </view>
    </view>

    <!-- 筛选 Tab -->
    <view class="cs-tabs">
      <view
        v-for="tab in TABS"
        :key="tab.key"
        class="cs-tab"
        :class="{ 'cs-tab--active': activeTab === tab.key }"
        @tap="switchTab(tab.key)"
      >
        <text>{{ tab.label }}</text>
        <view class="cs-tab__badge" v-if="tab.count > 0">
          <text>{{ tab.count }}</text>
        </view>
      </view>
    </view>

    <!-- 学员列表 -->
    <scroll-view scroll-y class="cs-body" @scrolltolower="loadMore">

      <template v-if="loading && !students.length">
        <view class="cs-skeleton" v-for="i in 4" :key="i">
          <view class="bhp-skeleton" style="height: 140rpx; border-radius: var(--radius-lg); margin-bottom: 16rpx;"></view>
        </view>
      </template>

      <view v-else-if="filteredStudents.length" class="cs-list">
        <view
          v-for="stu in filteredStudents"
          :key="stu.id"
          class="cs-card"
          @tap="goDetail(stu.id)"
        >
          <view class="cs-card__top">
            <image
              class="cs-card__avatar"
              :src="stu.avatar_url || '/static/default-avatar.png'"
              mode="aspectFill"
            />
            <view class="cs-card__info">
              <view class="cs-card__name-row">
                <text class="cs-card__name">{{ stu.full_name || stu.username }}</text>
                <BHPLevelBadge :role="stu.role || 'grower'" size="xs" />
              </view>
              <view class="cs-card__tags">
                <BHPRiskTag :level="stu.risk_level || stu.priority" />
                <text class="cs-card__stage" v-if="stu.ttm_stage">{{ TTM_LABEL[stu.ttm_stage] || stu.ttm_stage }}</text>
              </view>
            </view>
            <text class="cs-card__arrow">›</text>
          </view>
          <view class="cs-card__bottom">
            <text class="cs-card__meta">最近活跃：{{ formatTime(stu.last_active_at || stu.last_contact) }}</text>
            <text class="cs-card__meta" v-if="stu.days_since_contact > 3" style="color: var(--bhp-error-500);">
              {{ stu.days_since_contact }}天未联系
            </text>
          </view>
        </view>
      </view>

      <view v-else class="cs-empty">
        <text class="cs-empty__icon">📋</text>
        <text class="cs-empty__text">{{ keyword ? '无匹配学员' : '暂无学员' }}</text>
      </view>

      <!-- 加载更多 -->
      <view class="cs-load-more" v-if="hasMore && filteredStudents.length">
        <text class="text-sm text-secondary-color">{{ loading ? '加载中...' : '上拉加载更多' }}</text>
      </view>

    </scroll-view>

  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import http from '@/api/request'
import BHPLevelBadge from '@/components/BHPLevelBadge.vue'
import BHPRiskTag from '@/components/BHPRiskTag.vue'

const TTM_LABEL: Record<string, string> = {
  precontemplation: '前意向期',
  contemplation:    '意向期',
  preparation:      '准备期',
  action:           '行动期',
  maintenance:      '维持期',
  relapse:          '复发期',
}

const keyword   = ref('')
const activeTab = ref('all')
const students  = ref<any[]>([])
const loading   = ref(false)
const page      = ref(1)
const hasMore   = ref(true)

const highRiskCount   = computed(() => students.value.filter(s => s.priority === 'high' || s.risk_level === 'high').length)
const pendingCount    = computed(() => students.value.filter(s => (s.days_since_contact ?? 0) > 3).length)

const TABS = computed(() => [
  { key: 'all',     label: '全部',     count: students.value.length },
  { key: 'high',    label: '高风险',   count: highRiskCount.value },
  { key: 'pending', label: '待跟进',   count: pendingCount.value },
])

const filteredStudents = computed(() => {
  let list = students.value
  // tab filter
  if (activeTab.value === 'high') {
    list = list.filter(s => s.priority === 'high' || s.risk_level === 'high')
  } else if (activeTab.value === 'pending') {
    list = list.filter(s => (s.days_since_contact ?? 0) > 3)
  }
  // keyword filter
  if (keyword.value.trim()) {
    const kw = keyword.value.trim().toLowerCase()
    list = list.filter(s =>
      (s.full_name || '').toLowerCase().includes(kw) ||
      (s.username || '').toLowerCase().includes(kw)
    )
  }
  return list
})

onMounted(() => {
  loadStudents()
})

async function loadStudents() {
  loading.value = true
  try {
    const res = await http.get<{ students: any[]; total: number }>('/v1/coach/students')
    students.value = res.students || []
    hasMore.value = false // single page from dashboard
  } catch {
    students.value = []
  } finally {
    loading.value = false
  }
}

function loadMore() {
  if (!hasMore.value || loading.value) return
  page.value++
  loadStudents()
}

function switchTab(key: string) {
  activeTab.value = key
}

function onSearch(e: any) {
  keyword.value = e.detail.value || ''
}

function formatTime(dt: string | null | undefined): string {
  if (!dt) return '暂无'
  const d = new Date(dt)
  const now = new Date()
  const diff = Math.floor((now.getTime() - d.getTime()) / 60000)
  if (diff < 1) return '刚刚'
  if (diff < 60) return `${diff}分钟前`
  if (diff < 1440) return `${Math.floor(diff / 60)}小时前`
  const days = Math.floor(diff / 1440)
  if (days < 7) return `${days}天前`
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function goDetail(id: number) {
  uni.navigateTo({ url: `/pages/coach/students/detail?id=${id}` })
}

function goBack() {
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}
</script>

<style scoped>
.cs-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }

/* 导航栏 */
.cs-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.cs-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.cs-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.cs-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.cs-navbar__placeholder { width: 64rpx; }

/* 搜索框 */
.cs-search { padding: 16rpx 32rpx; background: var(--surface); }
.cs-search__box {
  display: flex; align-items: center; gap: 12rpx;
  background: var(--surface-secondary); border-radius: var(--radius-full);
  padding: 14rpx 24rpx;
}
.cs-search__icon { font-size: 28rpx; flex-shrink: 0; }
.cs-search__input { flex: 1; font-size: 26rpx; color: var(--text-primary); background: transparent; }
.cs-search__clear { font-size: 24rpx; color: var(--text-tertiary); cursor: pointer; padding: 4rpx; }

/* Tab */
.cs-tabs {
  display: flex; background: var(--surface); padding: 0 32rpx 16rpx;
  gap: 16rpx; border-bottom: 1px solid var(--border-light);
}
.cs-tab {
  position: relative; display: flex; align-items: center; gap: 6rpx;
  padding: 12rpx 24rpx; border-radius: var(--radius-full);
  font-size: 24rpx; font-weight: 600; color: var(--text-secondary);
  background: var(--surface-secondary); cursor: pointer;
}
.cs-tab--active { background: var(--bhp-primary-500); color: #fff; }
.cs-tab__badge {
  min-width: 28rpx; height: 28rpx; border-radius: var(--radius-full);
  background: var(--bhp-error-500); color: #fff; font-size: 18rpx; font-weight: 700;
  display: flex; align-items: center; justify-content: center; padding: 0 6rpx;
}
.cs-tab--active .cs-tab__badge { background: rgba(255,255,255,0.3); color: #fff; }

/* 列表 */
.cs-body { flex: 1; padding: 20rpx 32rpx 40rpx; }
.cs-list { display: flex; flex-direction: column; gap: 16rpx; }

/* 学员卡片 */
.cs-card {
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 24rpx; border: 1px solid var(--border-light); cursor: pointer;
}
.cs-card:active { opacity: 0.85; }
.cs-card__top { display: flex; align-items: center; gap: 16rpx; }
.cs-card__avatar {
  width: 80rpx; height: 80rpx; border-radius: 50%; flex-shrink: 0;
  background: var(--bhp-gray-100);
}
.cs-card__info { flex: 1; display: flex; flex-direction: column; gap: 8rpx; }
.cs-card__name-row { display: flex; align-items: center; gap: 10rpx; }
.cs-card__name { font-size: 28rpx; font-weight: 700; color: var(--text-primary); }
.cs-card__tags { display: flex; align-items: center; gap: 10rpx; flex-wrap: wrap; }
.cs-card__stage {
  font-size: 20rpx; font-weight: 600; color: var(--bhp-primary-600);
  background: var(--bhp-primary-50); padding: 2rpx 12rpx; border-radius: var(--radius-full);
}
.cs-card__arrow { font-size: 36rpx; color: var(--text-tertiary); flex-shrink: 0; }

.cs-card__bottom {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 12rpx; padding-top: 12rpx; border-top: 1px solid var(--border-light);
}
.cs-card__meta { font-size: 22rpx; color: var(--text-tertiary); }

/* 空状态 */
.cs-empty {
  display: flex; flex-direction: column; align-items: center;
  padding: 120rpx 0; gap: 16rpx;
}
.cs-empty__icon { font-size: 64rpx; }
.cs-empty__text { font-size: 26rpx; color: var(--text-tertiary); }

.cs-load-more { text-align: center; padding: 24rpx; }
</style>
