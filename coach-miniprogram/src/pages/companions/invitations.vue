<template>
  <view class="ci-page">
    <view class="ci-navbar safe-area-top">
      <view class="ci-navbar__back" @tap="goBack"><text class="ci-navbar__arrow">&#8249;</text></view>
      <text class="ci-navbar__title">邀请记录</text>
      <view class="ci-navbar__placeholder"></view>
    </view>

    <!-- Tab 切换 -->
    <view class="ci-tabs">
      <view v-for="tab in tabs" :key="tab.key" class="ci-tab" :class="{ 'ci-tab--active': activeTab === tab.key }" @tap="activeTab = tab.key">
        <text>{{ tab.label }}</text>
      </view>
    </view>

    <scroll-view scroll-y class="ci-body">
      <template v-if="loading">
        <view class="bhp-skeleton" v-for="i in 4" :key="i" style="height: 120rpx; border-radius: var(--radius-lg); margin-bottom: 16rpx;"></view>
      </template>

      <view v-else-if="filteredList.length" class="ci-list">
        <view v-for="item in filteredList" :key="item.id" class="ci-card">
          <image class="ci-card__avatar" :src="item.avatar_url || '/static/default-avatar.png'" mode="aspectFill" />
          <view class="ci-card__info">
            <text class="ci-card__name">{{ item.full_name || item.username || '用户' }}</text>
            <text class="ci-card__time">{{ formatDate(item.created_at || item.invited_at) }}</text>
          </view>
          <view v-if="activeTab === 'sent'" class="ci-card__status" :class="'ci-card__status--' + (item.status || 'pending')">
            <text>{{ STATUS_MAP[item.status] || '待接受' }}</text>
          </view>
          <template v-else>
            <template v-if="item.status === 'pending'">
              <view class="ci-card__btn ci-card__btn--accept" @tap="handleAccept(item)"><text>接受</text></view>
              <view class="ci-card__btn ci-card__btn--reject" @tap="handleReject(item)"><text>拒绝</text></view>
            </template>
            <view v-else class="ci-card__status" :class="'ci-card__status--' + (item.status || 'pending')">
              <text>{{ STATUS_MAP[item.status] || '待接受' }}</text>
            </view>
          </template>
        </view>
      </view>

      <view v-else class="ci-empty">
        <text class="ci-empty__icon">📩</text>
        <text class="ci-empty__text">{{ activeTab === 'sent' ? '暂无发出的邀请' : '暂无收到的邀请' }}</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import http from '@/api/request'

const tabs = [
  { key: 'sent', label: '发出的邀请' },
  { key: 'received', label: '收到的邀请' },
]
const STATUS_MAP: Record<string, string> = {
  pending: '待接受', accepted: '已接受', rejected: '已拒绝',
}

const activeTab = ref('sent')
const list     = ref<any[]>([])
const loading  = ref(false)

const filteredList = computed(() =>
  list.value.filter(i => i.direction === activeTab.value || i.type === activeTab.value)
)

onMounted(() => loadInvitations())

async function loadInvitations() {
  loading.value = true
  try {
    const res = await http.get<any>('/v1/companions/invitations')
    const items = res.items || res.invitations || (Array.isArray(res) ? res : [])
    list.value = items.map((i: any) => ({
      ...i,
      direction: i.direction || i.type || (i.is_sender ? 'sent' : 'received'),
    }))
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

async function handleAccept(item: any) {
  try {
    await http.post(`/v1/companions/invitations/${item.id}/accept`, {})
    item.status = 'accepted'
    uni.showToast({ title: '已接受', icon: 'success' })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
  }
}

async function handleReject(item: any) {
  try {
    await http.post(`/v1/companions/invitations/${item.id}/reject`, {})
    item.status = 'rejected'
    uni.showToast({ title: '已拒绝', icon: 'none' })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
  }
}

function formatDate(dt: string): string {
  if (!dt) return ''
  const d = new Date(dt)
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`
}

function goBack() { uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) }) }
</script>

<style scoped>
.ci-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }
.ci-navbar { display: flex; align-items: center; justify-content: space-between; padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light); }
.ci-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.ci-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.ci-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.ci-navbar__placeholder { width: 64rpx; }

.ci-tabs { display: flex; background: var(--surface); border-bottom: 1px solid var(--border-light); }
.ci-tab { flex: 1; text-align: center; padding: 20rpx 0; font-size: 26rpx; color: var(--text-secondary); position: relative; cursor: pointer; }
.ci-tab--active { color: var(--bhp-primary-600); font-weight: 700; }
.ci-tab--active::after { content: ''; position: absolute; bottom: 0; left: 30%; right: 30%; height: 4rpx; background: var(--bhp-primary-500); border-radius: 2rpx; }

.ci-body { flex: 1; padding: 20rpx 32rpx 40rpx; }
.ci-list { display: flex; flex-direction: column; gap: 12rpx; }
.ci-card {
  display: flex; align-items: center; gap: 16rpx;
  background: var(--surface); border-radius: var(--radius-lg); padding: 20rpx; border: 1px solid var(--border-light);
}
.ci-card__avatar { width: 72rpx; height: 72rpx; border-radius: 50%; flex-shrink: 0; background: var(--bhp-gray-100); }
.ci-card__info { flex: 1; }
.ci-card__name { display: block; font-size: 26rpx; font-weight: 600; color: var(--text-primary); }
.ci-card__time { display: block; font-size: 22rpx; color: var(--text-tertiary); margin-top: 4rpx; }

.ci-card__status { padding: 6rpx 16rpx; border-radius: var(--radius-full); font-size: 22rpx; font-weight: 600; flex-shrink: 0; }
.ci-card__status--pending { background: var(--bhp-gray-100); color: var(--text-secondary); }
.ci-card__status--accepted { background: #dcfce7; color: #16a34a; }
.ci-card__status--rejected { background: #fee2e2; color: #dc2626; }

.ci-card__btn { padding: 8rpx 20rpx; border-radius: var(--radius-full); font-size: 22rpx; font-weight: 600; cursor: pointer; flex-shrink: 0; }
.ci-card__btn--accept { background: var(--bhp-primary-500); color: #fff; }
.ci-card__btn--reject { background: var(--surface-secondary); color: var(--text-secondary); border: 1px solid var(--border-light); }

.ci-empty { display: flex; flex-direction: column; align-items: center; padding: 120rpx 0; gap: 16rpx; }
.ci-empty__icon { font-size: 64rpx; }
.ci-empty__text { font-size: 26rpx; color: var(--text-tertiary); }
</style>
