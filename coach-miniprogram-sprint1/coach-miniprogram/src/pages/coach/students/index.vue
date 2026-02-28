<template>
  <view class="students-page">

    <!-- 搜索框 -->
    <view class="stu-search px-4">
      <view class="stu-search__bar">
        <text class="stu-search__icon">🔍</text>
        <input
          class="stu-search__input"
          v-model="searchText"
          placeholder="搜索学员姓名"
          placeholder-class="stu-search-placeholder"
          @input="onSearch"
        />
        <view class="stu-search__clear" v-if="searchText" @tap="searchText = ''">
          <text>✕</text>
        </view>
      </view>
    </view>

    <!-- 风险 Tab -->
    <view class="stu-tabs px-4">
      <scroll-view class="stu-tabs__scroll" scroll-x>
        <view class="stu-tabs__inner">
          <view
            v-for="tab in filterTabs"
            :key="tab.key"
            class="stu-tab"
            :class="{ 'stu-tab--active': activeTab === tab.key }"
            @tap="activeTab = tab.key"
          >
            <text>{{ tab.label }}</text>
            <text class="stu-tab__count" v-if="tabCount(tab.key) > 0">{{ tabCount(tab.key) }}</text>
          </view>
        </view>
      </scroll-view>
    </view>

    <!-- 列表 -->
    <view class="stu-list px-4">

      <template v-if="loading">
        <view v-for="i in 6" :key="i" class="bhp-skeleton" style="height: 120rpx; margin-bottom: 12rpx; border-radius: var(--radius-lg);"></view>
      </template>

      <template v-else-if="filteredStudents.length">
        <view
          v-for="s in filteredStudents"
          :key="s.id"
          class="stu-card bhp-card bhp-card--flat"
          @tap="goDetail(s.id)"
        >
          <!-- 头像 -->
          <view class="stu-card__avatar" :style="{ background: riskColor(s.risk_level) }">
            <text class="stu-card__avatar-text">{{ (s.full_name || s.username || '用')[0] }}</text>
          </view>

          <!-- 信息 -->
          <view class="stu-card__body">
            <view class="stu-card__name-row">
              <text class="stu-card__name">{{ s.full_name || s.username }}</text>
              <view class="stu-card__risk" :style="{ background: riskColor(s.risk_level) + '20', color: riskColor(s.risk_level) }">
                <text>{{ RISK_LABEL[s.risk_level] }}</text>
              </view>
            </view>
            <view class="stu-card__meta">
              <text class="text-xs text-secondary-color">{{ TTM_LABEL[s.ttm_stage] }}</text>
              <text class="text-xs text-secondary-color" v-if="s.latest_glucose">
                · 血糖 {{ s.latest_glucose }}
              </text>
              <text class="text-xs text-secondary-color" v-if="s.sleep_score">
                · 睡眠 {{ s.sleep_score }}分
              </text>
            </view>
            <view class="stu-card__status" :class="`stu-interaction--${s.interaction_status}`">
              <text class="text-xs">{{ INTERACTION_LABEL[s.interaction_status] }}</text>
            </view>
          </view>

          <!-- 最后互动 -->
          <view class="stu-card__right">
            <text class="text-xs text-tertiary-color" v-if="s.last_interaction">
              {{ relativeTime(s.last_interaction) }}
            </text>
            <text class="stu-card__arrow">›</text>
          </view>
        </view>
      </template>

      <view class="stu-empty" v-else-if="!loading">
        <text class="stu-empty__icon">👥</text>
        <text class="stu-empty__text">{{ searchText ? '没有匹配的学员' : '暂无学员' }}</text>
      </view>
    </view>

    <!-- 底部安全区 -->
    <view style="height: 40rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useCoachStore, type Student } from '@/stores/coach'

const coachStore = useCoachStore()

const searchText = ref('')
const activeTab  = ref<'all' | 'critical' | 'high' | 'moderate' | 'low' | 'dormant'>('all')
const loading    = ref(false)

const RISK_LABEL: Record<string, string> = {
  critical: '危急', high: '高风险', moderate: '中风险', low: '低风险', none: '正常'
}
const TTM_LABEL: Record<string, string> = {
  S0: '阶段未知', S1: '前意向期', S2: '意向期', S3: '准备期',
  S4: '行动期', S5: '维持期', S6: '终止'
}
const INTERACTION_LABEL: Record<string, string> = {
  active: '活跃', needs_attention: '需关注', dormant: '休眠'
}

const filterTabs = [
  { key: 'all',      label: '全部' },
  { key: 'critical', label: '危急' },
  { key: 'high',     label: '高风险' },
  { key: 'moderate', label: '中风险' },
  { key: 'dormant',  label: '休眠' },
]

const allStudents = computed(() => coachStore.students)

const filteredStudents = computed(() => {
  let list: Student[] = allStudents.value
  // 按 tab 过滤
  if (activeTab.value === 'dormant') {
    list = list.filter(s => s.interaction_status === 'dormant')
  } else if (activeTab.value !== 'all') {
    list = list.filter(s => s.risk_level === activeTab.value)
  }
  // 按搜索过滤
  if (searchText.value.trim()) {
    const q = searchText.value.trim().toLowerCase()
    list = list.filter(s =>
      (s.full_name || '').toLowerCase().includes(q) ||
      (s.username || '').toLowerCase().includes(q)
    )
  }
  return list
})

function tabCount(key: string): number {
  if (key === 'all') return 0
  if (key === 'dormant') return allStudents.value.filter(s => s.interaction_status === 'dormant').length
  return allStudents.value.filter(s => s.risk_level === key).length
}

function riskColor(level: string): string {
  const map: Record<string, string> = {
    critical: '#f5222d', high: '#ff4d4f', moderate: '#fa8c16', low: '#52c41a', none: '#8c8c8c'
  }
  return map[level] || '#8c8c8c'
}

function relativeTime(dateStr: string): string {
  if (!dateStr) return ''
  try {
    const diff = Date.now() - new Date(dateStr).getTime()
    const days = Math.floor(diff / 86400000)
    if (days === 0) return '今天'
    if (days === 1) return '昨天'
    if (days < 7) return `${days}天前`
    return `${Math.floor(days / 7)}周前`
  } catch { return '' }
}

function onSearch() { /* 实时过滤，computed 自动响应 */ }

function goDetail(id: number) {
  uni.navigateTo({ url: `/pages/coach/students/detail?id=${id}` })
}

onMounted(async () => {
  if (!coachStore.students.length) {
    loading.value = true
    try { await coachStore.loadStudents() } catch { } finally { loading.value = false }
  }
})

onPullDownRefresh(async () => {
  loading.value = true
  try { await coachStore.loadStudents() } catch { } finally {
    loading.value = false
    uni.stopPullDownRefresh()
  }
})
</script>

<style scoped>
.students-page { background: var(--surface-secondary); min-height: 100vh; }

/* 搜索 */
.stu-search { padding-top: 16rpx; }
.stu-search__bar {
  display: flex; align-items: center; gap: 12rpx;
  background: var(--surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-full);
  padding: 0 20rpx; height: 72rpx;
}
.stu-search__icon { font-size: 28rpx; }
.stu-search__input { flex: 1; font-size: 26rpx; color: var(--text-primary); }
.stu-search-placeholder { color: var(--text-tertiary); font-size: 26rpx; }
.stu-search__clear { font-size: 24rpx; color: var(--text-tertiary); padding: 8rpx; cursor: pointer; }

/* Tabs */
.stu-tabs { padding-top: 12rpx; }
.stu-tabs__scroll { white-space: nowrap; }
.stu-tabs__inner { display: inline-flex; gap: 8rpx; padding: 4rpx 0; }
.stu-tab {
  display: inline-flex; align-items: center; gap: 6rpx;
  padding: 10rpx 20rpx;
  border-radius: var(--radius-full);
  font-size: 24rpx; color: var(--text-secondary);
  background: var(--surface);
  border: 1px solid var(--border-light);
  cursor: pointer; white-space: nowrap;
}
.stu-tab--active { background: var(--bhp-primary-500); color: #fff; border-color: transparent; font-weight: 600; }
.stu-tab__count {
  background: rgba(0,0,0,0.15);
  border-radius: var(--radius-full);
  font-size: 18rpx; padding: 0 8rpx;
}
.stu-tab--active .stu-tab__count { background: rgba(255,255,255,0.25); }

/* 列表 */
.stu-list { padding-top: 12rpx; }
.stu-card {
  display: flex; align-items: center; gap: 16rpx;
  padding: 16rpx 20rpx; margin-bottom: 10rpx;
  cursor: pointer;
}
.stu-card:active { opacity: 0.8; }
.stu-card__avatar {
  width: 72rpx; height: 72rpx; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.stu-card__avatar-text { font-size: 28rpx; color: #fff; font-weight: 700; }
.stu-card__body { flex: 1; overflow: hidden; }
.stu-card__name-row { display: flex; align-items: center; gap: 10rpx; margin-bottom: 6rpx; }
.stu-card__name { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.stu-card__risk {
  font-size: 18rpx; font-weight: 700;
  padding: 2rpx 10rpx; border-radius: var(--radius-full);
}
.stu-card__meta { display: flex; flex-wrap: wrap; gap: 0; margin-bottom: 6rpx; }
.stu-card__status {
  display: inline-block;
  font-size: 18rpx; padding: 2rpx 10rpx;
  border-radius: var(--radius-full);
}
.stu-interaction--active        { background: var(--bhp-success-50); color: var(--bhp-success-600, #16a34a); }
.stu-interaction--needs_attention { background: var(--bhp-warn-50, #fffbeb); color: var(--bhp-warn-600, #d97706); }
.stu-interaction--dormant       { background: var(--bhp-gray-100); color: var(--text-tertiary); }

.stu-card__right { flex-shrink: 0; display: flex; flex-direction: column; align-items: flex-end; gap: 8rpx; }
.stu-card__arrow { font-size: 32rpx; color: var(--text-tertiary); }

/* 空状态 */
.stu-empty { display: flex; flex-direction: column; align-items: center; padding: 80rpx 0; gap: 16rpx; }
.stu-empty__icon { font-size: 80rpx; }
.stu-empty__text { font-size: 28rpx; color: var(--text-tertiary); }
</style>
