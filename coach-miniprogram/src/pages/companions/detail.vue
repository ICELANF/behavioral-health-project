<template>
  <view class="cpd-page">
    <view class="cpd-navbar safe-area-top">
      <view class="cpd-navbar__back" @tap="goBack"><text class="cpd-navbar__arrow">‹</text></view>
      <text class="cpd-navbar__title">同道者详情</text>
      <view class="cpd-navbar__placeholder"></view>
    </view>

    <scroll-view scroll-y class="cpd-body">
      <template v-if="loading">
        <view class="bhp-skeleton" style="height: 200rpx; border-radius: var(--radius-lg); margin-bottom: 20rpx;"></view>
      </template>
      <template v-else-if="companion">
        <!-- 个人信息 -->
        <view class="cpd-profile">
          <image class="cpd-profile__avatar" :src="companion.avatar_url || '/static/default-avatar.png'" mode="aspectFill" />
          <text class="cpd-profile__name">{{ companion.full_name || companion.username }}</text>
          <BHPLevelBadge :role="companion.role || 'grower'" size="sm" />
          <text class="cpd-profile__date" v-if="companion.started_at">加入时间：{{ formatDate(companion.started_at) }}</text>
        </view>

        <!-- 互动统计 -->
        <view class="cpd-stats">
          <view class="cpd-stat">
            <text class="cpd-stat__val">{{ companion.interaction_count || 0 }}</text>
            <text class="cpd-stat__lbl">互动次数</text>
          </view>
          <view class="cpd-stat__divider"></view>
          <view class="cpd-stat">
            <text class="cpd-stat__val">{{ companion.quality_score || '-' }}</text>
            <text class="cpd-stat__lbl">互动质量</text>
          </view>
          <view class="cpd-stat__divider"></view>
          <view class="cpd-stat">
            <text class="cpd-stat__val">{{ formatTime(companion.last_interaction_at) }}</text>
            <text class="cpd-stat__lbl">最近互动</text>
          </view>
        </view>

        <!-- 互动记录 -->
        <view class="cpd-section">
          <text class="cpd-section__title">互动记录</text>
          <view v-if="interactions.length" class="cpd-interactions">
            <view v-for="(item, idx) in interactions" :key="idx" class="cpd-interaction">
              <view class="cpd-interaction__dot"></view>
              <view class="cpd-interaction__body">
                <text class="cpd-interaction__text">{{ item.content || item.description }}</text>
                <text class="cpd-interaction__time">{{ formatDate(item.created_at) }}</text>
              </view>
            </view>
          </view>
          <view v-else class="cpd-no-data">
            <text class="text-sm text-secondary-color">暂无互动记录</text>
          </view>
        </view>
      </template>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/api/request'
import BHPLevelBadge from '@/components/BHPLevelBadge.vue'

const companion    = ref<any>(null)
const interactions = ref<any[]>([])
const loading      = ref(false)
const companionId  = ref(0)

onMounted(() => {
  const pages = getCurrentPages()
  const pg = pages[pages.length - 1] as any
  companionId.value = Number(pg.$page?.options?.id || pg.options?.id || 0)
  if (companionId.value) loadDetail()
})

async function loadDetail() {
  loading.value = true
  try {
    const res = await http.get<any>(`/v1/companions/${companionId.value}`)
    companion.value = res
    interactions.value = res.interactions || res.records || []
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function formatDate(dt: string): string {
  if (!dt) return ''
  const d = new Date(dt)
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`
}

function formatTime(dt: string | null): string {
  if (!dt) return '暂无'
  const d = new Date(dt)
  const diff = Math.floor((Date.now() - d.getTime()) / 60000)
  if (diff < 60) return `${diff}分钟前`
  if (diff < 1440) return `${Math.floor(diff / 60)}小时前`
  return `${Math.floor(diff / 1440)}天前`
}

function goBack() { uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) }) }
</script>

<style scoped>
.cpd-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }
.cpd-navbar { display: flex; align-items: center; justify-content: space-between; padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light); }
.cpd-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.cpd-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.cpd-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.cpd-navbar__placeholder { width: 64rpx; }
.cpd-body { flex: 1; padding: 20rpx 32rpx 40rpx; }

.cpd-profile { display: flex; flex-direction: column; align-items: center; gap: 10rpx; padding: 40rpx 0; background: var(--surface); border-radius: var(--radius-lg); margin-bottom: 20rpx; border: 1px solid var(--border-light); }
.cpd-profile__avatar { width: 120rpx; height: 120rpx; border-radius: 50%; background: var(--bhp-gray-100); }
.cpd-profile__name { font-size: 32rpx; font-weight: 700; color: var(--text-primary); }
.cpd-profile__date { font-size: 22rpx; color: var(--text-tertiary); }

.cpd-stats { display: flex; align-items: center; background: var(--surface); border-radius: var(--radius-lg); padding: 24rpx; margin-bottom: 20rpx; border: 1px solid var(--border-light); }
.cpd-stat { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4rpx; }
.cpd-stat__val { font-size: 32rpx; font-weight: 800; color: var(--text-primary); }
.cpd-stat__lbl { font-size: 20rpx; color: var(--text-secondary); }
.cpd-stat__divider { width: 1px; height: 48rpx; background: var(--border-light); }

.cpd-section { background: var(--surface); border-radius: var(--radius-lg); padding: 24rpx; border: 1px solid var(--border-light); }
.cpd-section__title { display: block; font-size: 28rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 20rpx; }
.cpd-interactions { display: flex; flex-direction: column; gap: 16rpx; }
.cpd-interaction { display: flex; gap: 16rpx; }
.cpd-interaction__dot { width: 16rpx; height: 16rpx; border-radius: 50%; background: var(--bhp-primary-500); flex-shrink: 0; margin-top: 8rpx; }
.cpd-interaction__body { flex: 1; }
.cpd-interaction__text { display: block; font-size: 24rpx; color: var(--text-primary); margin-bottom: 4rpx; }
.cpd-interaction__time { font-size: 20rpx; color: var(--text-tertiary); }
.cpd-no-data { text-align: center; padding: 40rpx; }
</style>
