<template>
  <view class="cp-page">

    <!-- 导航栏 -->
    <view class="cp-navbar safe-area-top">
      <view class="cp-navbar__back" @tap="goBack">
        <text class="cp-navbar__arrow">‹</text>
      </view>
      <text class="cp-navbar__title">我的同道者</text>
      <view class="cp-navbar__placeholder"></view>
    </view>

    <!-- 顶部统计 -->
    <view class="cp-stats">
      <view class="cp-stats__item">
        <text class="cp-stats__val">{{ stats.total }}</text>
        <text class="cp-stats__label">同道者</text>
      </view>
      <view class="cp-stats__divider"></view>
      <view class="cp-stats__item">
        <text class="cp-stats__val cp-stats__val--pending">{{ stats.pending }}</text>
        <text class="cp-stats__label">邀请中</text>
      </view>
      <view class="cp-stats__divider"></view>
      <view class="cp-stats__item">
        <text class="cp-stats__val cp-stats__val--target">{{ stats.required }}</text>
        <text class="cp-stats__label">本级需要</text>
      </view>
    </view>

    <scroll-view scroll-y class="cp-body" @scrolltolower="loadMore">

      <!-- 同道者列表 -->
      <template v-if="companions.length">
        <view
          v-for="item in companions"
          :key="item.id"
          class="cp-item"
        >
          <image
            class="cp-item__avatar"
            :src="item.avatar || '/static/default-avatar.png'"
            mode="aspectFill"
          />
          <view class="cp-item__info">
            <view class="cp-item__row">
              <text class="cp-item__name">{{ item.full_name || item.username }}</text>
              <text class="cp-item__level" :style="{ color: getLevelColor(item.role) }">
                {{ getLevelLabel(item.role) }}
              </text>
            </view>
            <text class="cp-item__time">加入于 {{ formatDate(item.joined_at) }}</text>
          </view>
          <view
            class="cp-item__status"
            :class="item.is_active ? 'cp-item__status--active' : 'cp-item__status--silent'"
          >
            <text>{{ item.is_active ? '活跃' : '沉默' }}</text>
          </view>
        </view>

        <!-- 加载更多 -->
        <view class="cp-loading" v-if="hasMore">
          <text>加载更多...</text>
        </view>
      </template>

      <!-- 空状态 -->
      <view class="cp-empty" v-else-if="!loading">
        <text class="cp-empty__icon">👥</text>
        <text class="cp-empty__title">还没有同道者</text>
        <text class="cp-empty__sub">邀请志同道合的伙伴，一起成长</text>
      </view>

    </scroll-view>

    <!-- 底部邀请按钮 -->
    <view class="cp-footer safe-area-bottom">
      <view class="cp-footer__btn" @tap="goInvite">
        <text>+ 邀请新同道者</text>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import http from '@/api/request'
import { ROLE_COLOR, ROLE_LABEL } from '@/utils/level'

interface Companion {
  id: number
  username: string
  full_name?: string
  avatar?: string
  role: string
  joined_at: string
  is_active: boolean
}

const loading    = ref(false)
const companions = ref<Companion[]>([])
const hasMore    = ref(false)
const page       = ref(1)

const stats = reactive({
  total: 0,
  pending: 0,
  required: 0,
})

onMounted(async () => {
  await loadCompanions()
})

async function loadCompanions() {
  if (loading.value) return
  loading.value = true
  try {
    const res = await http.get<any>('/v1/companions/all', { page: page.value, page_size: 20 })
    const items: Companion[] = res.items || res.companions || []
    if (page.value === 1) {
      companions.value = items
    } else {
      companions.value = [...companions.value, ...items]
    }
    hasMore.value = items.length >= 20
    stats.total    = res.total ?? items.length
    stats.pending  = res.pending_count ?? 0
    stats.required = res.required_count ?? 0
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function loadMore() {
  if (!hasMore.value || loading.value) return
  page.value++
  loadCompanions()
}

function getLevelColor(role: string): string {
  return ROLE_COLOR[role] || '#9ca3af'
}

function getLevelLabel(role: string): string {
  return ROLE_LABEL[role] || role
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  return dateStr.slice(0, 10)
}

function goInvite() {
  uni.navigateTo({ url: '/pages/companions/invite' })
}

function goBack() {
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}
</script>

<style scoped>
.cp-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }

.cp-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.cp-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.cp-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.cp-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.cp-navbar__placeholder { width: 64rpx; }

/* 统计 */
.cp-stats {
  display: flex; align-items: center; background: var(--surface);
  padding: 24rpx 32rpx; border-bottom: 1px solid var(--border-light);
}
.cp-stats__item { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4rpx; }
.cp-stats__val { font-size: 40rpx; font-weight: 800; color: var(--text-primary); }
.cp-stats__val--pending { color: #f59e0b; }
.cp-stats__val--target { color: var(--bhp-primary-500); }
.cp-stats__label { font-size: 22rpx; color: var(--text-secondary); }
.cp-stats__divider { width: 1px; height: 48rpx; background: var(--border-light); }

/* 列表区 */
.cp-body { flex: 1; padding: 20rpx 32rpx 180rpx; }

.cp-item {
  display: flex; align-items: center; gap: 16rpx;
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 20rpx 24rpx; margin-bottom: 16rpx;
  border: 1px solid var(--border-light);
}
.cp-item__avatar { width: 80rpx; height: 80rpx; border-radius: 50%; flex-shrink: 0; background: var(--bhp-gray-100); }
.cp-item__info { flex: 1; overflow: hidden; }
.cp-item__row { display: flex; align-items: center; gap: 12rpx; }
.cp-item__name { font-size: 28rpx; font-weight: 700; color: var(--text-primary); }
.cp-item__level { font-size: 22rpx; font-weight: 600; }
.cp-item__time { font-size: 22rpx; color: var(--text-tertiary); display: block; margin-top: 4rpx; }

.cp-item__status {
  font-size: 20rpx; font-weight: 700; padding: 4rpx 16rpx;
  border-radius: var(--radius-full); flex-shrink: 0;
}
.cp-item__status--active { background: rgba(16,185,129,0.1); color: #10b981; }
.cp-item__status--silent { background: var(--bhp-gray-100); color: var(--text-tertiary); }

.cp-loading { text-align: center; padding: 20rpx; font-size: 24rpx; color: var(--text-tertiary); }

/* 空状态 */
.cp-empty {
  display: flex; flex-direction: column; align-items: center;
  padding: 120rpx 32rpx; gap: 12rpx;
}
.cp-empty__icon { font-size: 80rpx; }
.cp-empty__title { font-size: 30rpx; font-weight: 700; color: var(--text-primary); }
.cp-empty__sub { font-size: 26rpx; color: var(--text-secondary); }

/* 底部 */
.cp-footer {
  position: fixed; bottom: 0; left: 0; right: 0;
  padding: 16rpx 32rpx; background: var(--surface); border-top: 1px solid var(--border-light);
}
.cp-footer__btn {
  width: 100%; height: 88rpx; border-radius: var(--radius-lg);
  background: var(--bhp-primary-500); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 30rpx; font-weight: 700; cursor: pointer;
}
.cp-footer__btn:active { opacity: 0.85; }
</style>
