<template>
  <view class="ci-page">
    <view class="ci-navbar safe-area-top">
      <view class="ci-navbar__back" @tap="goBack"><text class="ci-navbar__arrow">‹</text></view>
      <text class="ci-navbar__title">邀请同道者</text>
      <view class="ci-navbar__placeholder"></view>
    </view>

    <!-- 我的邀请码 -->
    <view class="ci-code-card">
      <text class="ci-code-card__label">我的邀请码</text>
      <text class="ci-code-card__code">{{ inviteCode || '加载中...' }}</text>
      <view class="ci-code-card__btn" @tap="copyCode">
        <text>复制邀请码</text>
      </view>
    </view>

    <!-- 搜索 -->
    <view class="ci-search">
      <view class="ci-search__box">
        <text class="ci-search__icon">🔍</text>
        <input class="ci-search__input" placeholder="搜索用户名或姓名" :value="keyword" @confirm="doSearch" @input="keyword = $event.detail.value" />
      </view>
    </view>

    <scroll-view scroll-y class="ci-body">
      <template v-if="loading">
        <view class="bhp-skeleton" v-for="i in 3" :key="i" style="height: 100rpx; border-radius: var(--radius-lg); margin-bottom: 12rpx;"></view>
      </template>

      <view v-else-if="results.length" class="ci-list">
        <view v-for="user in results" :key="user.id" class="ci-user">
          <image class="ci-user__avatar" :src="user.avatar_url || '/static/default-avatar.png'" mode="aspectFill" />
          <view class="ci-user__info">
            <text class="ci-user__name">{{ user.full_name || user.username }}</text>
            <BHPLevelBadge :role="user.role || 'grower'" size="xs" />
          </view>
          <view class="ci-user__btn" :class="{ 'ci-user__btn--done': user._invited }" @tap="inviteUser(user)">
            <text>{{ user._invited ? '已邀请' : '邀请' }}</text>
          </view>
        </view>
      </view>

      <view v-else-if="searched" class="ci-empty">
        <text class="ci-empty__text">未找到匹配用户</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/api/request'
import { useUserStore } from '@/stores/user'
import BHPLevelBadge from '@/components/BHPLevelBadge.vue'

const userStore  = useUserStore()
const keyword    = ref('')
const results    = ref<any[]>([])
const loading    = ref(false)
const searched   = ref(false)
const inviteCode = ref('')

onMounted(() => {
  inviteCode.value = userStore.userInfo?.invite_code || `BHP${userStore.userInfo?.id || '0000'}`
})

async function doSearch() {
  if (!keyword.value.trim()) return
  loading.value = true
  searched.value = true
  try {
    const res = await http.get<any>('/v1/users/search', { q: keyword.value.trim(), limit: 20 })
    results.value = (res.items || res.users || (Array.isArray(res) ? res : [])).map((u: any) => ({ ...u, _invited: false }))
  } catch {
    results.value = []
  } finally {
    loading.value = false
  }
}

async function inviteUser(user: any) {
  if (user._invited) return
  try {
    await http.post(`/v1/companions/invite/${user.id}`, {})
    user._invited = true
    uni.showToast({ title: '邀请已发送', icon: 'success' })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '邀请失败', icon: 'none' })
  }
}

function copyCode() {
  uni.setClipboardData({ data: inviteCode.value, success: () => uni.showToast({ title: '已复制', icon: 'success' }) })
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

.ci-code-card {
  margin: 20rpx 32rpx; background: linear-gradient(135deg, var(--bhp-primary-500), var(--bhp-primary-700));
  border-radius: var(--radius-xl); padding: 32rpx; text-align: center;
}
.ci-code-card__label { display: block; font-size: 24rpx; color: rgba(255,255,255,0.7); margin-bottom: 12rpx; }
.ci-code-card__code { display: block; font-size: 48rpx; font-weight: 800; color: #fff; letter-spacing: 8rpx; margin-bottom: 20rpx; }
.ci-code-card__btn {
  display: inline-flex; padding: 12rpx 40rpx; border-radius: var(--radius-full);
  background: rgba(255,255,255,0.2); color: #fff; font-size: 24rpx; font-weight: 600; cursor: pointer;
}

.ci-search { padding: 0 32rpx 16rpx; }
.ci-search__box { display: flex; align-items: center; gap: 12rpx; background: var(--surface); border-radius: var(--radius-full); padding: 14rpx 24rpx; border: 1px solid var(--border-light); }
.ci-search__icon { font-size: 28rpx; }
.ci-search__input { flex: 1; font-size: 26rpx; color: var(--text-primary); }

.ci-body { flex: 1; padding: 0 32rpx 40rpx; }
.ci-list { display: flex; flex-direction: column; gap: 12rpx; }
.ci-user { display: flex; align-items: center; gap: 16rpx; background: var(--surface); border-radius: var(--radius-lg); padding: 20rpx; border: 1px solid var(--border-light); }
.ci-user__avatar { width: 72rpx; height: 72rpx; border-radius: 50%; flex-shrink: 0; background: var(--bhp-gray-100); }
.ci-user__info { flex: 1; display: flex; align-items: center; gap: 10rpx; }
.ci-user__name { font-size: 26rpx; font-weight: 600; color: var(--text-primary); }
.ci-user__btn { padding: 10rpx 28rpx; border-radius: var(--radius-full); background: var(--bhp-primary-500); color: #fff; font-size: 22rpx; font-weight: 600; cursor: pointer; }
.ci-user__btn--done { background: var(--bhp-gray-200); color: var(--text-tertiary); }
.ci-empty { text-align: center; padding: 80rpx; }
.ci-empty__text { font-size: 26rpx; color: var(--text-tertiary); }
</style>
