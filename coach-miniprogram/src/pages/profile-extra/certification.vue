<template>
  <view class="cert-page">
    <view class="cert-navbar safe-area-top">
      <view class="cert-navbar__back" @tap="goBack"><text class="cert-navbar__arrow">‹</text></view>
      <text class="cert-navbar__title">成就与证书</text>
      <view class="cert-navbar__placeholder"></view>
    </view>

    <scroll-view scroll-y class="cert-body">

      <!-- 成就徽章 -->
      <view class="cert-section">
        <text class="cert-section__title">成就徽章</text>
        <view v-if="badges.length" class="cert-badges">
          <view v-for="badge in badges" :key="badge.id || badge.name" class="cert-badge" :class="{ 'cert-badge--locked': !badge.earned }">
            <text class="cert-badge__icon">{{ badge.icon || '🏅' }}</text>
            <text class="cert-badge__name">{{ badge.name }}</text>
          </view>
        </view>
        <view v-else class="cert-no-data">
          <text class="text-sm text-secondary-color">暂无成就</text>
        </view>
      </view>

      <!-- 证书列表 -->
      <view class="cert-section">
        <text class="cert-section__title">我的证书</text>
        <view v-if="certs.length" class="cert-list">
          <view v-for="cert in certs" :key="cert.id" class="cert-card">
            <view class="cert-card__left">
              <text class="cert-card__icon">📜</text>
            </view>
            <view class="cert-card__center">
              <text class="cert-card__name">{{ cert.name || cert.title }}</text>
              <text class="cert-card__date">获得时间：{{ formatDate(cert.issued_at || cert.created_at) }}</text>
            </view>
            <view class="cert-card__btn" @tap="viewCert(cert)">
              <text>查看</text>
            </view>
          </view>
        </view>
        <view v-else class="cert-no-data">
          <text class="text-sm text-secondary-color">暂无证书</text>
        </view>
      </view>

    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/api/request'

const certs  = ref<any[]>([])
const badges = ref<any[]>([])
const loading = ref(false)

onMounted(() => loadData())

async function loadData() {
  loading.value = true
  try {
    const [certsRes, badgesRes] = await Promise.allSettled([
      http.get<any>('/v1/certification/my-certs'),
      http.get<any>('/v1/certification/my-badges'),
    ])
    if (certsRes.status === 'fulfilled') {
      const d = certsRes.value as any
      certs.value = d.items || d.certs || (Array.isArray(d) ? d : [])
    }
    if (badgesRes.status === 'fulfilled') {
      const d = badgesRes.value as any
      badges.value = d.items || d.badges || (Array.isArray(d) ? d : [])
    }
  } finally {
    loading.value = false
  }
}

function formatDate(dt: string): string {
  if (!dt) return ''
  const d = new Date(dt)
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`
}

function viewCert(cert: any) {
  uni.showToast({ title: '查看证书功能开发中', icon: 'none' })
}

function goBack() { uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) }) }
</script>

<style scoped>
.cert-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }
.cert-navbar { display: flex; align-items: center; justify-content: space-between; padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light); }
.cert-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.cert-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.cert-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.cert-navbar__placeholder { width: 64rpx; }
.cert-body { flex: 1; padding: 20rpx 32rpx 40rpx; }

.cert-section { margin-bottom: 24rpx; }
.cert-section__title { display: block; font-size: 28rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 16rpx; }

.cert-badges { display: flex; flex-wrap: wrap; gap: 16rpx; }
.cert-badge {
  width: calc(25% - 12rpx); display: flex; flex-direction: column; align-items: center; gap: 6rpx;
  padding: 16rpx 8rpx; background: var(--surface); border-radius: var(--radius-lg); border: 1px solid var(--border-light);
}
.cert-badge--locked { opacity: 0.4; }
.cert-badge__icon { font-size: 40rpx; }
.cert-badge__name { font-size: 18rpx; color: var(--text-secondary); text-align: center; }

.cert-list { display: flex; flex-direction: column; gap: 12rpx; }
.cert-card {
  display: flex; align-items: center; gap: 16rpx;
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 20rpx; border: 1px solid var(--border-light);
}
.cert-card__left { flex-shrink: 0; }
.cert-card__icon { font-size: 40rpx; }
.cert-card__center { flex: 1; display: flex; flex-direction: column; gap: 4rpx; }
.cert-card__name { font-size: 26rpx; font-weight: 600; color: var(--text-primary); }
.cert-card__date { font-size: 22rpx; color: var(--text-tertiary); }
.cert-card__btn {
  padding: 10rpx 24rpx; border-radius: var(--radius-full);
  background: var(--bhp-primary-50); color: var(--bhp-primary-600);
  font-size: 22rpx; font-weight: 600; cursor: pointer;
}

.cert-no-data { text-align: center; padding: 40rpx; background: var(--surface); border-radius: var(--radius-lg); border: 1px solid var(--border-light); }
</style>
