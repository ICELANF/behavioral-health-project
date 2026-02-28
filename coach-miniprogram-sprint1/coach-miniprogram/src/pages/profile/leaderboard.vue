<template>
  <view class="lb-page">

    <!-- 类型 Tab -->
    <view class="lb-tabs px-4">
      <view class="lb-tabs__inner">
        <view
          v-for="tab in TABS"
          :key="tab.key"
          class="lb-tabs__tab"
          :class="{ 'lb-tabs__tab--active': activeTab === tab.key }"
          @tap="switchTab(tab.key)"
        >
          <text>{{ tab.label }}</text>
        </view>
      </view>
    </view>

    <!-- 我的排名横幅 -->
    <view class="lb-my-rank px-4" v-if="!loading && myRankInfo">
      <view class="lb-my-rank__card" :style="{ background: activeTabMeta.gradient }">
        <view class="lb-my-rank__left">
          <text class="lb-my-rank__pos">{{ myRankInfo.my_rank ? `#${myRankInfo.my_rank}` : '—' }}</text>
          <text class="lb-my-rank__label">我的排名</text>
        </view>
        <view class="lb-my-rank__divider"></view>
        <view class="lb-my-rank__right">
          <text class="lb-my-rank__pts">{{ myRankInfo.my_points ?? 0 }}</text>
          <text class="lb-my-rank__label">{{ activeTabMeta.pointLabel }}</text>
        </view>
        <text class="lb-my-rank__icon">{{ activeTabMeta.icon }}</text>
      </view>
    </view>

    <!-- 列表 -->
    <view class="lb-list px-4">

      <!-- 骨架屏 -->
      <template v-if="loading">
        <view v-for="i in 10" :key="i" class="bhp-skeleton" style="height: 88rpx; margin-bottom: 8rpx; border-radius: var(--radius-lg);"></view>
      </template>

      <template v-else>
        <!-- 前3名奖台区 -->
        <view class="lb-podium" v-if="top3.length">
          <view
            v-for="(entry, idx) in podiumOrder"
            :key="entry.user_id"
            class="lb-podium__item"
            :class="`lb-podium__item--${idx === 0 ? '2' : idx === 1 ? '1' : '3'}`"
          >
            <!-- 头像 -->
            <view class="lb-podium__avatar" :style="{ background: getRoleColor(entry.role) }">
              <text class="lb-podium__avatar-text">{{ (entry.full_name || entry.username || '用')[0] }}</text>
              <!-- 皇冠/勋章 -->
              <view class="lb-podium__crown">
                <text>{{ podiumCrown[idx] }}</text>
              </view>
            </view>
            <text class="lb-podium__name">{{ shortName(entry.full_name || entry.username) }}</text>
            <text class="lb-podium__pts">{{ entry.points }}</text>
          </view>
        </view>

        <!-- 其余排名 -->
        <view
          v-for="entry in rest"
          :key="entry.user_id"
          class="lb-item bhp-card bhp-card--flat"
          :class="{ 'lb-item--me': entry.is_me }"
        >
          <!-- 排名 -->
          <view class="lb-item__rank">
            <text class="lb-item__rank-text">{{ entry.rank }}</text>
          </view>

          <!-- 头像 -->
          <view class="lb-item__avatar" :style="{ background: getRoleColor(entry.role) }">
            <text class="lb-item__avatar-text">{{ (entry.full_name || entry.username || '用')[0] }}</text>
          </view>

          <!-- 信息 -->
          <view class="lb-item__body">
            <view class="lb-item__name-row">
              <text class="lb-item__name">{{ entry.full_name || entry.username }}</text>
              <view class="lb-item__me-badge" v-if="entry.is_me">
                <text>我</text>
              </view>
            </view>
            <view class="lb-item__role-tag" :style="{ background: getRoleColor(entry.role) + '20', color: getRoleColor(entry.role) }">
              <text>{{ ROLE_LABEL[entry.role] || entry.role }}</text>
            </view>
          </view>

          <!-- 积分 -->
          <text class="lb-item__pts">{{ entry.points }}</text>
        </view>

        <!-- 加载更多 -->
        <view class="lb-load-more" v-if="hasMore" @tap="loadMore">
          <text v-if="!loadingMore">加载更多</text>
          <text v-else>加载中...</text>
        </view>
        <view class="lb-load-more lb-load-more--end" v-else-if="items.length > 3">
          <text>已显示全部</text>
        </view>

        <!-- 空状态 -->
        <view class="lb-empty" v-if="!loading && !items.length">
          <text class="lb-empty__icon">🏆</text>
          <text class="lb-empty__text">暂无排行数据</text>
        </view>
      </template>
    </view>

    <view style="height: 40rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { profileApi, type LeaderboardEntry, type LeaderboardResp } from '@/api/profile'

// ─── 常量 ─────────────────────────────────────────────────────
type TabKey = 'growth' | 'contribution' | 'influence'

const TABS: { key: TabKey; label: string }[] = [
  { key: 'growth',       label: '成长积分' },
  { key: 'contribution', label: '贡献积分' },
  { key: 'influence',    label: '影响积分' },
]

const TAB_META: Record<TabKey, { icon: string; pointLabel: string; gradient: string }> = {
  growth:       { icon: '🌱', pointLabel: '成长积分', gradient: 'linear-gradient(135deg, #52c41a, #95de64)' },
  contribution: { icon: '💧', pointLabel: '贡献积分', gradient: 'linear-gradient(135deg, #1890ff, #69b1ff)' },
  influence:    { icon: '✨', pointLabel: '影响积分', gradient: 'linear-gradient(135deg, #722ed1, #eb2f96)' },
}

const ROLE_LABEL: Record<string, string> = {
  observer: 'L0', grower: 'L1', sharer: 'L2',
  coach: 'L3', promoter: 'L4', supervisor: 'L4', master: 'L5'
}
const ROLE_COLORS: Record<string, string> = {
  observer: '#8c8c8c', grower: '#52c41a', sharer: '#1890ff',
  coach: '#722ed1', promoter: '#eb2f96', supervisor: '#eb2f96', master: '#faad14'
}

// 奖台排序：第2→第1→第3（视觉高低）
const podiumCrown = ['🥈', '🥇', '🥉']

// ─── 状态 ─────────────────────────────────────────────────────
const activeTab  = ref<TabKey>('growth')
const items      = ref<LeaderboardEntry[]>([])
const loading    = ref(false)
const loadingMore = ref(false)
const page       = ref(1)
const hasMore    = ref(true)
const myRankInfo = ref<Partial<LeaderboardResp> | null>(null)

// ─── 计算 ─────────────────────────────────────────────────────
const activeTabMeta = computed(() => TAB_META[activeTab.value])

const top3 = computed(() => items.value.slice(0, 3))
const rest = computed(() => items.value.slice(3))

// 奖台排序：[2nd, 1st, 3rd]
const podiumOrder = computed(() => {
  const t = top3.value
  if (t.length === 1) return t
  if (t.length === 2) return [t[1], t[0]]
  return [t[1], t[0], t[2]]
})

// ─── 方法 ─────────────────────────────────────────────────────
function getRoleColor(role: string) {
  return ROLE_COLORS[role] || '#8c8c8c'
}

function shortName(name: string) {
  return name?.length > 5 ? name.slice(0, 5) + '…' : name || '—'
}

onMounted(() => loadLeaderboard(true))

async function switchTab(key: TabKey) {
  if (key === activeTab.value) return
  activeTab.value = key
  await loadLeaderboard(true)
}

async function loadLeaderboard(reset = false) {
  if (reset) { page.value = 1; items.value = []; hasMore.value = true }
  if (!hasMore.value) return
  reset ? (loading.value = true) : (loadingMore.value = true)
  try {
    const resp = await profileApi.leaderboard(activeTab.value, page.value)
    const newItems = resp.items || []
    items.value = reset ? newItems : [...items.value, ...newItems]
    hasMore.value = newItems.length === 20
    page.value++
    if (reset) {
      myRankInfo.value = { my_rank: resp.my_rank, my_points: resp.my_points }
    }
  } catch {
    // 降级：静默失败，显示空状态
    if (reset) items.value = []
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function loadMore() {
  loadLeaderboard(false)
}
</script>

<style scoped>
.lb-page { background: var(--surface-secondary); min-height: 100vh; }

/* Tab */
.lb-tabs { padding-top: 16rpx; padding-bottom: 8rpx; }
.lb-tabs__inner {
  display: flex;
  background: var(--surface);
  border-radius: var(--radius-full);
  padding: 6rpx;
  border: 1px solid var(--border-light);
  gap: 4rpx;
}
.lb-tabs__tab {
  flex: 1; text-align: center;
  padding: 10rpx 8rpx;
  border-radius: var(--radius-full);
  font-size: 26rpx; color: var(--text-secondary);
  cursor: pointer;
}
.lb-tabs__tab--active {
  background: var(--bhp-primary-500); color: #fff; font-weight: 600;
}

/* 我的排名 */
.lb-my-rank { padding-top: 12rpx; }
.lb-my-rank__card {
  display: flex; align-items: center;
  border-radius: var(--radius-lg);
  padding: 20rpx 28rpx;
  gap: 24rpx;
  position: relative;
  overflow: hidden;
}
.lb-my-rank__left, .lb-my-rank__right {
  display: flex; flex-direction: column; align-items: center; gap: 4rpx;
}
.lb-my-rank__pos  { font-size: 48rpx; font-weight: 700; color: #fff; line-height: 1; }
.lb-my-rank__pts  { font-size: 40rpx; font-weight: 700; color: #fff; line-height: 1; }
.lb-my-rank__label { font-size: 22rpx; color: rgba(255,255,255,0.8); }
.lb-my-rank__divider { width: 1px; height: 56rpx; background: rgba(255,255,255,0.3); }
.lb-my-rank__right { flex: 1; }
.lb-my-rank__icon {
  position: absolute; right: 24rpx; top: 50%;
  transform: translateY(-50%);
  font-size: 72rpx; opacity: 0.2;
}

/* 奖台 */
.lb-podium {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 20rpx;
  padding: 24rpx 0 16rpx;
}
.lb-podium__item {
  display: flex; flex-direction: column; align-items: center; gap: 8rpx;
  flex: 1;
}
.lb-podium__item--1 { transform: translateY(-16rpx); }
.lb-podium__item--2 { }
.lb-podium__item--3 { }

.lb-podium__avatar {
  width: 88rpx; height: 88rpx;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  position: relative;
  border: 4rpx solid rgba(255,255,255,0.8);
}
.lb-podium__item--1 .lb-podium__avatar {
  width: 100rpx; height: 100rpx;
}
.lb-podium__avatar-text { font-size: 36rpx; color: #fff; font-weight: 700; }
.lb-podium__crown {
  position: absolute; top: -20rpx; left: 50%;
  transform: translateX(-50%);
  font-size: 28rpx;
}
.lb-podium__name  { font-size: 22rpx; color: var(--text-primary); font-weight: 500; }
.lb-podium__pts   { font-size: 28rpx; font-weight: 700; color: var(--text-primary); }

/* 列表项 */
.lb-list { padding-top: 8rpx; }
.lb-item {
  display: flex; align-items: center;
  gap: 16rpx;
  padding: 16rpx 20rpx;
  margin-bottom: 8rpx;
}
.lb-item--me {
  border: 2px solid var(--bhp-primary-300, #6ee7b7);
  background: var(--bhp-primary-50);
}

.lb-item__rank {
  width: 52rpx;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.lb-item__rank-text {
  font-size: 28rpx; font-weight: 700; color: var(--text-tertiary);
}

.lb-item__avatar {
  width: 64rpx; height: 64rpx;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.lb-item__avatar-text { font-size: 26rpx; color: #fff; font-weight: 700; }

.lb-item__body { flex: 1; overflow: hidden; }
.lb-item__name-row { display: flex; align-items: center; gap: 10rpx; margin-bottom: 4rpx; }
.lb-item__name { font-size: 26rpx; font-weight: 500; color: var(--text-primary); }
.lb-item__me-badge {
  background: var(--bhp-primary-100, #d1fae5);
  color: var(--bhp-primary-700, #047857);
  font-size: 18rpx; font-weight: 700;
  padding: 2rpx 10rpx;
  border-radius: var(--radius-full);
}
.lb-item__role-tag {
  display: inline-block;
  font-size: 18rpx; font-weight: 700;
  padding: 2rpx 10rpx;
  border-radius: var(--radius-full);
}

.lb-item__pts {
  font-size: 30rpx; font-weight: 700; color: var(--text-primary);
  flex-shrink: 0;
}

/* 加载更多 */
.lb-load-more {
  text-align: center; padding: 20rpx;
  font-size: 26rpx; color: var(--bhp-primary-500);
  cursor: pointer;
}
.lb-load-more--end { color: var(--text-tertiary); }

/* 空状态 */
.lb-empty {
  display: flex; flex-direction: column; align-items: center;
  padding: 80rpx 0; gap: 16rpx;
}
.lb-empty__icon { font-size: 80rpx; }
.lb-empty__text { font-size: 28rpx; color: var(--text-tertiary); }
</style>
