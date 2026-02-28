<template>
  <view class="invite-page">

    <!-- 说明卡 -->
    <view class="invite-info px-4">
      <view class="invite-info__card">
        <text class="invite-info__icon">💡</text>
        <view class="invite-info__body">
          <text class="invite-info__title">邀请同道学员</text>
          <text class="invite-info__desc">作为导师邀请学员建立同道关系，帮助其成长并满足您的晋级条件</text>
        </view>
      </view>
    </view>

    <!-- 通过 ID 邀请 -->
    <view class="invite-direct px-4">
      <view class="invite-direct__card bhp-card bhp-card--flat">
        <text class="invite-section-title">通过用户 ID 邀请</text>
        <view class="invite-direct__input-row">
          <input
            class="invite-direct__input"
            v-model="directUserId"
            type="number"
            placeholder="输入对方的用户 ID"
            placeholder-class="invite-input-placeholder"
            @confirm="directInvite"
          />
          <view
            class="invite-direct__btn"
            :class="{ 'invite-direct__btn--active': directUserId && !invitingDirect }"
            @tap="directInvite"
          >
            <text v-if="!invitingDirect">邀请</text>
            <text v-else>邀请中...</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 智能匹配推荐 -->
    <view class="invite-match px-4">
      <view class="invite-section-header">
        <text class="invite-section-title">智能匹配推荐</text>
        <view class="invite-refresh-btn" @tap="loadSuggestions">
          <text class="text-xs text-primary-color">↻ 换一批</text>
        </view>
      </view>

      <!-- 骨架屏 -->
      <template v-if="loadingSuggestions">
        <view v-for="i in 4" :key="i" class="bhp-skeleton" style="height: 110rpx; margin-bottom: 10rpx; border-radius: var(--radius-lg);"></view>
      </template>

      <template v-else-if="suggestions.length">
        <view
          v-for="user in suggestions"
          :key="user.user_id"
          class="invite-suggestion bhp-card bhp-card--flat"
          :class="{ 'invite-suggestion--companion': user.is_companion }"
        >
          <!-- 头像 -->
          <view class="invite-suggestion__avatar" :style="{ background: getRoleColor(user.role) }">
            <text class="invite-suggestion__avatar-text">{{ (user.full_name || user.username || '用')[0] }}</text>
          </view>

          <!-- 信息 -->
          <view class="invite-suggestion__body">
            <view class="invite-suggestion__name-row">
              <text class="invite-suggestion__name">{{ user.full_name || user.username }}</text>
              <view class="invite-suggestion__role-tag" :style="{ background: getRoleColor(user.role) + '20', color: getRoleColor(user.role) }">
                <text>{{ ROLE_LABEL[user.role] || user.role }}</text>
              </view>
            </view>
            <view class="invite-suggestion__meta">
              <text class="text-xs text-secondary-color">成长积分 {{ user.growth_points }}</text>
              <text class="text-xs text-secondary-color" v-if="user.match_score">
                · 匹配度 {{ user.match_score }}%
              </text>
            </view>
            <text class="invite-suggestion__reason text-xs" v-if="user.match_reason">
              {{ user.match_reason }}
            </text>
          </view>

          <!-- 操作 -->
          <view class="invite-suggestion__action">
            <view
              v-if="user.is_companion"
              class="invite-suggestion__invited-tag"
            >
              <text>已是同道</text>
            </view>
            <view
              v-else-if="invitedIds.has(user.user_id)"
              class="invite-suggestion__invited-tag"
            >
              <text>已邀请 ✓</text>
            </view>
            <view
              v-else
              class="invite-suggestion__invite-btn"
              :class="{ 'invite-suggestion__invite-btn--loading': invitingId === user.user_id }"
              @tap="inviteUser(user)"
            >
              <text v-if="invitingId !== user.user_id">邀请</text>
              <text v-else>...</text>
            </view>
          </view>
        </view>
      </template>

      <view class="invite-empty" v-else-if="!loadingSuggestions">
        <text class="invite-empty__icon">🔍</text>
        <text class="invite-empty__text">暂无推荐用户</text>
      </view>
    </view>

    <!-- 使用说明 -->
    <view class="invite-guide px-4">
      <view class="invite-guide__card bhp-card bhp-card--flat">
        <text class="invite-guide__title">📋 同道关系说明</text>
        <text class="invite-guide__item">• 您作为导师，对方作为学员建立关系</text>
        <text class="invite-guide__item">• L3晋升需要4位≥L1等级的同道者</text>
        <text class="invite-guide__item">• L4晋升需要4位≥L2等级的同道者</text>
        <text class="invite-guide__item">• 学员达到目标等级后可毕业</text>
      </view>
    </view>

    <view style="height: 40rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { companionApi, type MatchSuggestion } from '@/api/companion'

const directUserId     = ref('')
const invitingDirect   = ref(false)
const suggestions      = ref<MatchSuggestion[]>([])
const loadingSuggestions = ref(false)
const invitingId       = ref<number | null>(null)
const invitedIds       = ref<Set<number>>(new Set())

const ROLE_LABEL: Record<string, string> = {
  observer: 'L0 观察员', grower: 'L1 成长者', sharer: 'L2 分享者',
  coach: 'L3 教练', promoter: 'L4 促进师', supervisor: 'L4 督导', master: 'L5 大师'
}
const ROLE_COLORS: Record<string, string> = {
  observer: '#8c8c8c', grower: '#52c41a', sharer: '#1890ff',
  coach: '#722ed1', promoter: '#eb2f96', supervisor: '#eb2f96', master: '#faad14'
}

function getRoleColor(role: string): string {
  return ROLE_COLORS[role] || '#8c8c8c'
}

onMounted(() => loadSuggestions())

async function loadSuggestions() {
  loadingSuggestions.value = true
  try {
    const data = await companionApi.matchSuggestions()
    suggestions.value = Array.isArray(data) ? data : []
  } catch { /* 静默 */ } finally {
    loadingSuggestions.value = false
  }
}

async function directInvite() {
  const uid = Number(directUserId.value)
  if (!uid || uid <= 0) {
    uni.showToast({ title: '请输入有效的用户 ID', icon: 'none' })
    return
  }
  invitingDirect.value = true
  try {
    await companionApi.invite(uid)
    directUserId.value = ''
    invitedIds.value = new Set([...invitedIds.value, uid])
    uni.showToast({ title: '邀请成功！', icon: 'success' })
    // 刷新建议列表
    await loadSuggestions()
  } catch (e: any) {
    const msg = e?.data?.detail || e?.message || '邀请失败，请检查用户 ID'
    uni.showToast({ title: msg, icon: 'none' })
  } finally {
    invitingDirect.value = false
  }
}

async function inviteUser(user: MatchSuggestion) {
  if (invitingId.value || user.is_companion || invitedIds.value.has(user.user_id)) return
  uni.showModal({
    title: '确认邀请',
    content: `邀请 ${user.full_name || user.username} 成为您的同道学员？`,
    confirmText: '确认邀请',
    success: async (res) => {
      if (!res.confirm) return
      invitingId.value = user.user_id
      try {
        await companionApi.invite(user.user_id)
        invitedIds.value = new Set([...invitedIds.value, user.user_id])
        uni.showToast({ title: '邀请成功！', icon: 'success' })
        // 更新本地状态
        const idx = suggestions.value.findIndex(s => s.user_id === user.user_id)
        if (idx >= 0) suggestions.value[idx].is_companion = true
      } catch (e: any) {
        const msg = e?.data?.detail || '邀请失败，请重试'
        uni.showToast({ title: msg, icon: 'none' })
      } finally {
        invitingId.value = null
      }
    }
  })
}
</script>

<style scoped>
.invite-page { background: var(--surface-secondary); min-height: 100vh; }

/* 说明卡 */
.invite-info { padding-top: 16rpx; }
.invite-info__card {
  display: flex;
  gap: 16rpx;
  align-items: flex-start;
  background: var(--bhp-primary-50);
  border-radius: var(--radius-lg);
  padding: 20rpx 24rpx;
}
.invite-info__icon  { font-size: 32rpx; }
.invite-info__title { display: block; font-size: 26rpx; font-weight: 600; color: var(--bhp-primary-700, #047857); margin-bottom: 6rpx; }
.invite-info__desc  { display: block; font-size: 22rpx; color: var(--bhp-primary-600, #059669); line-height: 1.5; }

/* 直接邀请 */
.invite-direct { padding-top: 16rpx; }
.invite-section-title { display: block; font-size: 26rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 16rpx; }
.invite-direct__input-row { display: flex; gap: 12rpx; }
.invite-direct__input {
  flex: 1;
  height: 72rpx;
  background: var(--bhp-gray-50, #f9fafb);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: 0 20rpx;
  font-size: 26rpx;
  color: var(--text-primary);
}
.invite-input-placeholder { color: var(--text-tertiary); font-size: 26rpx; }
.invite-direct__btn {
  padding: 0 32rpx;
  height: 72rpx;
  border-radius: var(--radius-lg);
  background: var(--bhp-gray-200);
  color: var(--text-tertiary);
  font-size: 26rpx;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}
.invite-direct__btn--active {
  background: var(--bhp-primary-500);
  color: #fff;
  cursor: pointer;
}
.invite-direct__btn--active:active { opacity: 0.8; }

/* 推荐列表 */
.invite-match { padding-top: 24rpx; }
.invite-section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12rpx; }
.invite-refresh-btn { cursor: pointer; padding: 4rpx 8rpx; }

.invite-suggestion {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 16rpx 20rpx;
  margin-bottom: 10rpx;
}
.invite-suggestion--companion { opacity: 0.6; }

.invite-suggestion__avatar {
  width: 68rpx;
  height: 68rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.invite-suggestion__avatar-text { font-size: 28rpx; color: #fff; font-weight: 700; }

.invite-suggestion__body { flex: 1; overflow: hidden; }
.invite-suggestion__name-row { display: flex; align-items: center; gap: 10rpx; margin-bottom: 4rpx; }
.invite-suggestion__name { font-size: 26rpx; font-weight: 500; color: var(--text-primary); }
.invite-suggestion__role-tag {
  font-size: 18rpx; font-weight: 700;
  padding: 2rpx 10rpx;
  border-radius: var(--radius-full);
}
.invite-suggestion__meta { display: flex; gap: 0; }
.invite-suggestion__reason { color: var(--bhp-primary-500); margin-top: 4rpx; display: block; }

.invite-suggestion__action { flex-shrink: 0; }
.invite-suggestion__invited-tag {
  font-size: 20rpx; color: var(--bhp-success-600, #16a34a);
  background: var(--bhp-success-50, #f0fdf4);
  padding: 6rpx 16rpx;
  border-radius: var(--radius-full);
}
.invite-suggestion__invite-btn {
  font-size: 24rpx; font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #722ed1, #eb2f96);
  padding: 8rpx 24rpx;
  border-radius: var(--radius-full);
  cursor: pointer;
}
.invite-suggestion__invite-btn:active { opacity: 0.8; }
.invite-suggestion__invite-btn--loading { opacity: 0.6; }

/* 空状态 */
.invite-empty { display: flex; flex-direction: column; align-items: center; padding: 60rpx 0; gap: 12rpx; }
.invite-empty__icon { font-size: 60rpx; }
.invite-empty__text { font-size: 26rpx; color: var(--text-tertiary); }

/* 说明 */
.invite-guide { padding-top: 20rpx; }
.invite-guide__card { padding: 20rpx 24rpx; }
.invite-guide__title { display: block; font-size: 26rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 12rpx; }
.invite-guide__item  { display: block; font-size: 24rpx; color: var(--text-secondary); line-height: 1.8; }
</style>
