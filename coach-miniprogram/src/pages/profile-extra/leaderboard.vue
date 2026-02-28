<template>
  <view class="lb-page">

    <view class="lb-navbar safe-area-top">
      <view class="lb-navbar__back" @tap="goBack"><text class="lb-navbar__arrow">‹</text></view>
      <text class="lb-navbar__title">排行榜</text>
      <view class="lb-navbar__placeholder"></view>
    </view>

    <!-- Tab -->
    <view class="lb-tabs">
      <view
        v-for="tab in TABS"
        :key="tab.key"
        class="lb-tab"
        :class="{ 'lb-tab--active': activeTab === tab.key }"
        @tap="switchTab(tab.key)"
      >
        <text>{{ tab.label }}</text>
      </view>
    </view>

    <scroll-view scroll-y class="lb-body">

      <!-- 我的排名 -->
      <view class="lb-my-rank" v-if="myRank">
        <view class="lb-my-rank__pos">
          <text>{{ myRank.rank || '-' }}</text>
        </view>
        <image class="lb-my-rank__avatar" :src="myRank.avatar_url || '/static/default-avatar.png'" mode="aspectFill" />
        <view class="lb-my-rank__info">
          <text class="lb-my-rank__name">{{ myRank.full_name || myRank.username }} (我)</text>
          <BHPLevelBadge :role="myRank.role || 'grower'" size="xs" />
        </view>
        <text class="lb-my-rank__pts">{{ myRank.points || 0 }}</text>
      </view>

      <template v-if="loading">
        <view class="bhp-skeleton" v-for="i in 5" :key="i" style="height: 96rpx; border-radius: var(--radius-lg); margin-bottom: 12rpx;"></view>
      </template>

      <view v-else-if="rankings.length" class="lb-list">
        <view
          v-for="(item, idx) in rankings"
          :key="item.id || idx"
          class="lb-item"
          :class="{ 'lb-item--top3': idx < 3 }"
        >
          <view class="lb-item__pos" :class="{ 'lb-item__pos--gold': idx === 0, 'lb-item__pos--silver': idx === 1, 'lb-item__pos--bronze': idx === 2 }">
            <text>{{ idx + 1 }}</text>
          </view>
          <image class="lb-item__avatar" :src="item.avatar_url || '/static/default-avatar.png'" mode="aspectFill" />
          <view class="lb-item__info">
            <text class="lb-item__name">{{ item.full_name || item.username }}</text>
            <BHPLevelBadge :role="item.role || 'grower'" size="xs" />
          </view>
          <text class="lb-item__pts">{{ item.points || 0 }}</text>
        </view>
      </view>

      <view v-else class="lb-empty">
        <text class="lb-empty__icon">🏅</text>
        <text class="lb-empty__text">暂无排行数据</text>
      </view>

    </scroll-view>

  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/api/request'
import BHPLevelBadge from '@/components/BHPLevelBadge.vue'

const TABS = [
  { key: 'growth',       label: '成长积分' },
  { key: 'contribution', label: '贡献积分' },
  { key: 'influence',    label: '影响力' },
]

const activeTab = ref('growth')
const rankings  = ref<any[]>([])
const myRank    = ref<any>(null)
const loading   = ref(false)

onMounted(() => loadRanking())

async function loadRanking() {
  loading.value = true
  try {
    const res = await http.get<any>('/v1/leaderboard', { type: activeTab.value, limit: 20 })
    rankings.value = res.items || res.rankings || (Array.isArray(res) ? res : [])
    myRank.value = res.my_rank || res.me || null
  } catch {
    rankings.value = []
    myRank.value = null
  } finally {
    loading.value = false
  }
}

function switchTab(key: string) {
  activeTab.value = key
  loadRanking()
}

function goBack() {
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}
</script>

<style scoped>
.lb-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }
.lb-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.lb-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.lb-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.lb-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.lb-navbar__placeholder { width: 64rpx; }

.lb-tabs {
  display: flex; background: var(--surface); padding: 12rpx 32rpx 16rpx;
  gap: 16rpx; border-bottom: 1px solid var(--border-light);
}
.lb-tab {
  flex: 1; text-align: center; padding: 12rpx 0; border-radius: var(--radius-full);
  font-size: 24rpx; font-weight: 600; color: var(--text-secondary);
  background: var(--surface-secondary); cursor: pointer;
}
.lb-tab--active { background: var(--bhp-primary-500); color: #fff; }

.lb-body { flex: 1; padding: 20rpx 32rpx 40rpx; }

/* 我的排名 */
.lb-my-rank {
  display: flex; align-items: center; gap: 16rpx;
  background: linear-gradient(135deg, var(--bhp-primary-50), var(--bhp-primary-100));
  border: 2px solid var(--bhp-primary-200); border-radius: var(--radius-lg);
  padding: 20rpx 24rpx; margin-bottom: 20rpx;
}
.lb-my-rank__pos {
  width: 48rpx; height: 48rpx; border-radius: 50%; flex-shrink: 0;
  background: var(--bhp-primary-500); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 24rpx; font-weight: 800;
}
.lb-my-rank__avatar { width: 64rpx; height: 64rpx; border-radius: 50%; flex-shrink: 0; background: #fff; }
.lb-my-rank__info { flex: 1; display: flex; align-items: center; gap: 10rpx; }
.lb-my-rank__name { font-size: 26rpx; font-weight: 700; color: var(--text-primary); }
.lb-my-rank__pts { font-size: 30rpx; font-weight: 800; color: var(--bhp-primary-600); flex-shrink: 0; }

/* 列表 */
.lb-list { display: flex; flex-direction: column; gap: 10rpx; }
.lb-item {
  display: flex; align-items: center; gap: 16rpx;
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 16rpx 20rpx; border: 1px solid var(--border-light);
}
.lb-item__pos {
  width: 44rpx; height: 44rpx; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 22rpx; font-weight: 700; color: var(--text-tertiary);
  background: var(--bhp-gray-100);
}
.lb-item__pos--gold { background: #fef3c7; color: #d97706; }
.lb-item__pos--silver { background: #f1f5f9; color: #64748b; }
.lb-item__pos--bronze { background: #fff7ed; color: #ea580c; }
.lb-item__avatar { width: 56rpx; height: 56rpx; border-radius: 50%; flex-shrink: 0; background: var(--bhp-gray-100); }
.lb-item__info { flex: 1; display: flex; align-items: center; gap: 10rpx; }
.lb-item__name { font-size: 26rpx; font-weight: 600; color: var(--text-primary); }
.lb-item__pts { font-size: 26rpx; font-weight: 700; color: var(--text-primary); flex-shrink: 0; }

.lb-empty { display: flex; flex-direction: column; align-items: center; padding: 120rpx 0; gap: 16rpx; }
.lb-empty__icon { font-size: 64rpx; }
.lb-empty__text { font-size: 26rpx; color: var(--text-tertiary); }
</style>
