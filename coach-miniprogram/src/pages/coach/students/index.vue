<template>
  <view class="cs-page">

    <!-- 导航栏 -->
    <view class="cs-navbar">
      <view class="cs-navbar__back" @tap="goBack"><text class="cs-navbar__arrow">&#8249;</text></view>
      <text class="cs-navbar__title">我的学员</text>
      <view class="cs-navbar__sort" @tap="toggleSort">
        <text>{{ sortLabel }}</text>
      </view>
    </view>

    <!-- 搜索框 -->
    <view class="cs-search">
      <view class="cs-search__box">
        <text class="cs-search__icon">🔍</text>
        <input class="cs-search__input" placeholder="搜索学员姓名" :value="keyword" @input="onSearch" />
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
          <text>{{ tab.count > 99 ? '99+' : tab.count }}</text>
        </view>
      </view>
    </view>

    <!-- 学员列表 -->
    <scroll-view
      scroll-y class="cs-body"
      refresher-enabled :refresher-triggered="refreshing"
      @refresherrefresh="onRefresh"
      @scrolltolower="loadMore"
    >
      <template v-if="loading && !students.length">
        <view class="bhp-skeleton" v-for="i in 4" :key="i" style="height: 140rpx; border-radius: var(--radius-lg); margin-bottom: 16rpx;"></view>
      </template>

      <view v-else-if="filteredStudents.length" class="cs-list">
        <view v-for="stu in filteredStudents" :key="stu.id" class="cs-card" @tap="goDetail(stu.id)">
          <view class="cs-card__top">
            <view class="cs-card__avatar-wrap">
              <image class="cs-card__avatar" :src="stu.avatar_url || '/static/default-avatar.png'" mode="aspectFill" />
              <view class="cs-card__online" v-if="stu.is_online"></view>
            </view>
            <view class="cs-card__info">
              <view class="cs-card__name-row">
                <text class="cs-card__name">{{ stu.full_name || stu.username || stu.name }}</text>
                <!-- 内联等级标签 -->
                <view class="cs-level-badge" v-if="stu.role">
                  <text>{{ ROLE_LABEL[stu.role] || '学员' }}</text>
                </view>
              </view>
              <view class="cs-card__tags">
                <!-- 内联风险标签 -->
                <view class="cs-risk-tag" :class="`cs-risk-tag--${normalizeRisk(stu.risk_level || stu.priority)}`">
                  <text>{{ RISK_LABEL[stu.risk_level || stu.priority] || '未评估' }}</text>
                </view>
                <view class="cs-stage-tag" v-if="stu.ttm_stage">
                  <text>{{ TTM_LABEL[stu.ttm_stage] || stu.ttm_stage }}</text>
                </view>
              </view>
            </view>
            <text class="cs-card__arrow">›</text>
          </view>
          <view class="cs-card__bottom">
            <text class="cs-card__meta">最近活跃：{{ formatTime(stu.last_active_at || stu.last_contact) }}</text>
            <text class="cs-card__warn" v-if="(stu.days_since_contact ?? 0) > 3">
              ⚠ {{ stu.days_since_contact }}天未联系
            </text>
          </view>
          <!-- 微行动进度 -->
          <view class="cs-card__micro" v-if="stu.micro_action_7d">
            <text class="cs-card__micro-label">7天微行动</text>
            <view class="cs-card__micro-bar">
              <view class="cs-card__micro-fill" :style="{ width: getMicroPct(stu) + '%' }"></view>
            </view>
            <text class="cs-card__micro-val">{{ stu.micro_action_7d.completed || 0 }}/{{ (stu.micro_action_7d.completed || 0) + (stu.micro_action_7d.pending || 0) }}</text>
          </view>
        </view>
      </view>

      <view v-else class="cs-empty">
        <text class="cs-empty__icon">📋</text>
        <text class="cs-empty__text">{{ keyword ? '无匹配学员' : '暂无学员' }}</text>
      </view>

      <view class="cs-load-more" v-if="hasMore && filteredStudents.length">
        <text>{{ loading ? '加载中...' : '上拉加载更多' }}</text>
      </view>
    </scroll-view>

  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

// ============================================================
// 内联 HTTP
// ============================================================
const BASE_URL = 'http://localhost:8000/api'

function _request<T = any>(method: 'GET' | 'POST', path: string, data?: any): Promise<T> {
  return new Promise((resolve, reject) => {
    const token = uni.getStorageSync('access_token') || ''
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (token) headers['Authorization'] = `Bearer ${token}`
    const url = `${BASE_URL}/${path.replace(/^\//, '')}`
    uni.request({
      url, method, data, header: headers,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data as T)
        else if (res.statusCode === 401) {
          uni.removeStorageSync('access_token'); uni.removeStorageSync('refresh_token'); uni.removeStorageSync('user_info')
          uni.reLaunch({ url: '/pages/auth/login' }); reject(new Error('Session expired'))
        } else reject({ statusCode: res.statusCode, data: res.data })
      },
      fail(err) { uni.showToast({ title: '网络异常', icon: 'none' }); reject(err) },
    })
  })
}

function _get<T = any>(path: string): Promise<T> { return _request<T>('GET', path) }

// ============================================================
// 常量
// ============================================================
const TTM_LABEL: Record<string, string> = {
  precontemplation: '前意向期', contemplation: '意向期', preparation: '准备期',
  action: '行动期', maintenance: '维持期', relapse: '复发期', termination: '终止期',
}
const RISK_LABEL: Record<string, string> = {
  critical: '危急', high: '高风险', medium: '中风险', low: '低风险', unknown: '未评估',
  R4: '高危', R3: '警惕', R2: '关注', R1: '正常',
}
const ROLE_LABEL: Record<string, string> = {
  grower: '学员', bhp_coach: '教练', admin: '管理员',
}
const SORT_MODES = [
  { key: 'risk',    label: '按风险排序' },
  { key: 'active',  label: '按活跃排序' },
  { key: 'name',    label: '按姓名排序' },
]
const RISK_ORDER: Record<string, number> = { critical: 0, R4: 0, high: 1, R3: 1, medium: 2, R2: 2, low: 3, R1: 3, unknown: 4 }

// ============================================================
// 状态
// ============================================================
const keyword    = ref('')
const activeTab  = ref('all')
const students   = ref<any[]>([])
const loading    = ref(false)
const refreshing = ref(false)
const hasMore    = ref(false)
const sortMode   = ref('risk')

const sortLabel = computed(() => SORT_MODES.find(s => s.key === sortMode.value)?.label || '排序')

const highRiskCount = computed(() => students.value.filter(s => ['high', 'critical', 'R4', 'R3'].includes(s.risk_level || s.priority)).length)
const midRiskCount  = computed(() => students.value.filter(s => ['medium', 'R2'].includes(s.risk_level || s.priority)).length)
const pendingCount  = computed(() => students.value.filter(s => (s.days_since_contact ?? 0) > 3).length)

const TABS = computed(() => [
  { key: 'all',     label: '全部',     count: students.value.length },
  { key: 'high',    label: '高风险',   count: highRiskCount.value },
  { key: 'medium',  label: '中风险',   count: midRiskCount.value },
  { key: 'pending', label: '待跟进',   count: pendingCount.value },
])

const filteredStudents = computed(() => {
  let list = [...students.value]

  // Tab 筛选
  if (activeTab.value === 'high') {
    list = list.filter(s => ['high', 'critical', 'R4', 'R3'].includes(s.risk_level || s.priority))
  } else if (activeTab.value === 'medium') {
    list = list.filter(s => ['medium', 'R2'].includes(s.risk_level || s.priority))
  } else if (activeTab.value === 'pending') {
    list = list.filter(s => (s.days_since_contact ?? 0) > 3)
  }

  // 搜索
  if (keyword.value.trim()) {
    const kw = keyword.value.trim().toLowerCase()
    list = list.filter(s => (s.full_name || s.username || s.name || '').toLowerCase().includes(kw))
  }

  // 排序
  if (sortMode.value === 'risk') {
    list.sort((a, b) => (RISK_ORDER[a.risk_level || a.priority || 'unknown'] ?? 4) - (RISK_ORDER[b.risk_level || b.priority || 'unknown'] ?? 4))
  } else if (sortMode.value === 'active') {
    list.sort((a, b) => new Date(b.last_active_at || b.last_contact || 0).getTime() - new Date(a.last_active_at || a.last_contact || 0).getTime())
  } else if (sortMode.value === 'name') {
    list.sort((a, b) => (a.full_name || a.username || '').localeCompare(b.full_name || b.username || ''))
  }

  return list
})

// ============================================================
// 数据加载
// ============================================================
onMounted(() => loadStudents())

async function loadStudents() {
  loading.value = true
  try {
    const res = await _get<any>('/v1/coach/students')
    students.value = res.students || res.items || []
    hasMore.value = false
  } catch {
    students.value = []
  } finally {
    loading.value = false
  }
}

async function onRefresh() {
  refreshing.value = true
  await loadStudents()
  refreshing.value = false
}

function loadMore() {
  if (!hasMore.value || loading.value) return
}

// ============================================================
// 交互
// ============================================================
function switchTab(key: string) { activeTab.value = key }

function onSearch(e: any) { keyword.value = e.detail.value || '' }

function toggleSort() {
  const idx = SORT_MODES.findIndex(s => s.key === sortMode.value)
  sortMode.value = SORT_MODES[(idx + 1) % SORT_MODES.length].key
  uni.showToast({ title: sortLabel.value, icon: 'none', duration: 1000 })
}

function normalizeRisk(level: string): string {
  if (['critical', 'R4', 'high', 'R3'].includes(level)) return 'high'
  if (['medium', 'R2'].includes(level)) return 'medium'
  if (['low', 'R1'].includes(level)) return 'low'
  return 'unknown'
}

function getMicroPct(stu: any): number {
  const ma = stu.micro_action_7d || {}
  const total = (ma.completed || 0) + (ma.pending || 0) + (ma.active || 0)
  if (!total) return 0
  return Math.round(((ma.completed || 0) / total) * 100)
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

function goDetail(id: number) { uni.navigateTo({ url: `/pages/coach/students/detail?id=${id}` }) }
function goBack() { uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) }) }
</script>

<style scoped>
.cs-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }

/* 导航 */
.cs-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top));
  background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.cs-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; }
.cs-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.cs-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.cs-navbar__sort {
  font-size: 22rpx; font-weight: 600; color: var(--bhp-primary-500, #10b981);
  padding: 8rpx 16rpx; border-radius: var(--radius-full); background: rgba(16,185,129,0.08);
}

/* 搜索 */
.cs-search { padding: 16rpx 32rpx; background: var(--surface); }
.cs-search__box {
  display: flex; align-items: center; gap: 12rpx;
  background: var(--surface-secondary); border-radius: var(--radius-full); padding: 14rpx 24rpx;
}
.cs-search__icon { font-size: 28rpx; flex-shrink: 0; }
.cs-search__input { flex: 1; font-size: 26rpx; color: var(--text-primary); background: transparent; }
.cs-search__clear { font-size: 24rpx; color: var(--text-tertiary); padding: 4rpx; }

/* Tab */
.cs-tabs {
  display: flex; background: var(--surface); padding: 0 24rpx 16rpx;
  gap: 12rpx; border-bottom: 1px solid var(--border-light); overflow-x: auto;
}
.cs-tab {
  position: relative; display: flex; align-items: center; gap: 6rpx;
  padding: 10rpx 20rpx; border-radius: var(--radius-full);
  font-size: 22rpx; font-weight: 600; color: var(--text-secondary);
  background: var(--surface-secondary); flex-shrink: 0;
}
.cs-tab--active { background: var(--bhp-primary-500, #10b981); color: #fff; }
.cs-tab__badge {
  min-width: 28rpx; height: 28rpx; border-radius: var(--radius-full);
  background: #ef4444; color: #fff; font-size: 18rpx; font-weight: 700;
  display: flex; align-items: center; justify-content: center; padding: 0 6rpx;
}
.cs-tab--active .cs-tab__badge { background: rgba(255,255,255,0.3); }

/* 列表 */
.cs-body { flex: 1; padding: 20rpx 32rpx 40rpx; }
.cs-list { display: flex; flex-direction: column; gap: 16rpx; }

/* 学员卡片 */
.cs-card {
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 24rpx; border: 1px solid var(--border-light);
}
.cs-card:active { opacity: 0.85; }
.cs-card__top { display: flex; align-items: center; gap: 16rpx; }
.cs-card__avatar-wrap { position: relative; flex-shrink: 0; }
.cs-card__avatar { width: 80rpx; height: 80rpx; border-radius: 50%; background: var(--bhp-gray-100, #f3f4f6); }
.cs-card__online {
  position: absolute; bottom: 2rpx; right: 2rpx; width: 20rpx; height: 20rpx;
  border-radius: 50%; background: #10b981; border: 3rpx solid var(--surface);
}
.cs-card__info { flex: 1; display: flex; flex-direction: column; gap: 8rpx; }
.cs-card__name-row { display: flex; align-items: center; gap: 10rpx; }
.cs-card__name { font-size: 28rpx; font-weight: 700; color: var(--text-primary); }
.cs-card__tags { display: flex; align-items: center; gap: 10rpx; flex-wrap: wrap; }
.cs-card__arrow { font-size: 36rpx; color: var(--text-tertiary); flex-shrink: 0; }

/* 内联等级标签 */
.cs-level-badge {
  font-size: 18rpx; font-weight: 600; padding: 2rpx 10rpx;
  border-radius: var(--radius-full); background: #eff6ff; color: #2563eb;
}

/* 内联风险标签 */
.cs-risk-tag { font-size: 20rpx; font-weight: 600; padding: 2rpx 12rpx; border-radius: var(--radius-full); }
.cs-risk-tag--high { background: #fef2f2; color: #dc2626; }
.cs-risk-tag--medium { background: #fffbeb; color: #d97706; }
.cs-risk-tag--low { background: #f0fdf4; color: #16a34a; }
.cs-risk-tag--unknown { background: var(--bhp-gray-100, #f3f4f6); color: var(--text-tertiary); }

/* TTM阶段 */
.cs-stage-tag {
  font-size: 20rpx; font-weight: 600; color: #059669;
  background: rgba(16,185,129,0.1); padding: 2rpx 12rpx; border-radius: var(--radius-full);
}

/* 底部信息 */
.cs-card__bottom {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 12rpx; padding-top: 12rpx; border-top: 1px solid var(--border-light);
}
.cs-card__meta { font-size: 22rpx; color: var(--text-tertiary); }
.cs-card__warn { font-size: 22rpx; font-weight: 600; color: #ef4444; }

/* 微行动进度 */
.cs-card__micro {
  display: flex; align-items: center; gap: 12rpx; margin-top: 12rpx;
}
.cs-card__micro-label { font-size: 20rpx; color: var(--text-tertiary); flex-shrink: 0; }
.cs-card__micro-bar { flex: 1; height: 12rpx; background: var(--bhp-gray-100, #f3f4f6); border-radius: var(--radius-full); overflow: hidden; }
.cs-card__micro-fill { height: 100%; background: #10b981; border-radius: var(--radius-full); transition: width 0.3s; }
.cs-card__micro-val { font-size: 20rpx; font-weight: 600; color: var(--text-secondary); flex-shrink: 0; }

/* 空 / 加载 */
.cs-empty { display: flex; flex-direction: column; align-items: center; padding: 120rpx 0; gap: 16rpx; }
.cs-empty__icon { font-size: 64rpx; }
.cs-empty__text { font-size: 26rpx; color: var(--text-tertiary); }
.cs-load-more { text-align: center; padding: 24rpx; font-size: 24rpx; color: var(--text-tertiary); }
</style>
