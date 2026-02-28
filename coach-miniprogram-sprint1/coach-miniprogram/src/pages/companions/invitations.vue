<template>
  <view class="invitations-page">

    <!-- 说明卡 -->
    <view class="iv-info px-4">
      <view class="iv-info__card">
        <text class="iv-info__icon">💌</text>
        <view class="iv-info__body">
          <text class="iv-info__title">同道邀请说明</text>
          <text class="iv-info__desc">平台采用导师主动邀请模式，当导师邀请您时关系自动建立，无需手动确认</text>
        </view>
      </view>
    </view>

    <!-- 我的导师 -->
    <view class="iv-section px-4">
      <text class="iv-section-title">我的导师</text>

      <template v-if="loadingMentors">
        <view v-for="i in 2" :key="i" class="bhp-skeleton" style="height: 100rpx; margin-bottom: 10rpx; border-radius: var(--radius-lg);"></view>
      </template>

      <template v-else-if="mentors.length">
        <view
          v-for="mentor in mentors"
          :key="mentor.id"
          class="iv-mentor-card bhp-card bhp-card--flat"
        >
          <view class="iv-mentor__avatar" :style="{ background: getRoleColor(mentor.mentor_role || '') }">
            <text class="iv-mentor__avatar-text">{{ (mentor.mentor_name || '导')[0] }}</text>
          </view>
          <view class="iv-mentor__body">
            <view class="iv-mentor__name-row">
              <text class="iv-mentor__name">{{ mentor.mentor_name || `用户${mentor.mentor_id}` }}</text>
              <view
                class="iv-mentor__role-tag"
                :style="{ background: getRoleColor(mentor.mentor_role || '') + '20', color: getRoleColor(mentor.mentor_role || '') }"
              >
                <text>{{ ROLE_LABEL[mentor.mentor_role || ''] || mentor.mentor_role }}</text>
              </view>
            </view>
            <text class="text-xs text-secondary-color">建立于 {{ formatDate(mentor.created_at) }}</text>
          </view>
          <view class="iv-mentor__status-dot" :class="`iv-status--${mentor.status}`"></view>
        </view>
      </template>

      <view class="iv-empty-inline" v-else-if="!loadingMentors">
        <text class="text-sm text-tertiary-color">暂无导师，等待导师邀请您加入同道关系</text>
      </view>
    </view>

    <!-- 推荐导师 -->
    <view class="iv-section px-4">
      <view class="iv-section-header">
        <text class="iv-section-title">推荐导师</text>
        <view class="iv-refresh-btn" @tap="loadSuggestions">
          <text class="text-xs text-primary-color">↻ 换一批</text>
        </view>
      </view>
      <text class="iv-section-sub text-xs text-secondary-color">以下高级别用户可能成为您的导师</text>

      <template v-if="loadingSuggestions">
        <view v-for="i in 3" :key="i" class="bhp-skeleton" style="height: 100rpx; margin-bottom: 10rpx; border-radius: var(--radius-lg);"></view>
      </template>

      <template v-else-if="suggestions.length">
        <view
          v-for="user in suggestions"
          :key="user.user_id"
          class="iv-suggestion bhp-card bhp-card--flat"
          :class="{ 'iv-suggestion--companion': user.is_companion }"
        >
          <!-- 头像 -->
          <view class="iv-suggestion__avatar" :style="{ background: getRoleColor(user.role) }">
            <text class="iv-suggestion__avatar-text">{{ (user.full_name || user.username || '用')[0] }}</text>
          </view>

          <!-- 信息 -->
          <view class="iv-suggestion__body">
            <view class="iv-suggestion__name-row">
              <text class="iv-suggestion__name">{{ user.full_name || user.username }}</text>
              <view
                class="iv-suggestion__role-tag"
                :style="{ background: getRoleColor(user.role) + '20', color: getRoleColor(user.role) }"
              >
                <text>{{ ROLE_LABEL[user.role] || user.role }}</text>
              </view>
            </view>
            <view class="iv-suggestion__meta">
              <text class="text-xs text-secondary-color">成长积分 {{ user.growth_points }}</text>
              <text class="text-xs text-secondary-color" v-if="user.match_score">
                · 匹配度 {{ user.match_score }}%
              </text>
            </view>
            <text class="iv-suggestion__reason text-xs" v-if="user.match_reason">
              {{ user.match_reason }}
            </text>
          </view>

          <!-- 状态标签 -->
          <view class="iv-suggestion__action">
            <view v-if="user.is_companion" class="iv-tag iv-tag--companion">
              <text>已关联</text>
            </view>
            <view v-else class="iv-tag iv-tag--tip">
              <text>等待邀请</text>
            </view>
          </view>
        </view>
      </template>

      <view class="iv-empty" v-else-if="!loadingSuggestions">
        <text class="iv-empty__icon">🔍</text>
        <text class="iv-empty__text">暂无推荐导师</text>
      </view>
    </view>

    <!-- 底部提示 -->
    <view class="iv-tip px-4">
      <view class="iv-tip__card">
        <text class="iv-tip__text">💡 当高级别导师邀请您成为同道学员时，关系将自动建立，您可在"我的同道"中查看</text>
      </view>
    </view>

    <view style="height: 40rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { companionApi, type MentorRelation, type MatchSuggestion } from '@/api/companion'

const mentors            = ref<MentorRelation[]>([])
const loadingMentors     = ref(false)
const suggestions        = ref<MatchSuggestion[]>([])
const loadingSuggestions = ref(false)

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

onMounted(() => {
  loadMentors()
  loadSuggestions()
})

async function loadMentors() {
  loadingMentors.value = true
  try {
    const data = await companionApi.myMentors()
    mentors.value = Array.isArray(data) ? data : []
  } catch { /* 静默 */ } finally {
    loadingMentors.value = false
  }
}

async function loadSuggestions() {
  loadingSuggestions.value = true
  try {
    const data = await companionApi.matchSuggestions()
    const all = Array.isArray(data) ? data : []
    // 过滤高级别用户作为潜在导师
    suggestions.value = all
      .filter(u => ['coach', 'promoter', 'supervisor', 'master'].includes(u.role))
      .slice(0, 5)
  } catch { /* 静默 */ } finally {
    loadingSuggestions.value = false
  }
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  } catch { return dateStr }
}
</script>

<style scoped>
.invitations-page { background: var(--surface-secondary); min-height: 100vh; }

/* 说明卡 */
.iv-info { padding-top: 16rpx; }
.iv-info__card {
  display: flex;
  gap: 16rpx;
  align-items: flex-start;
  background: var(--bhp-primary-50);
  border-radius: var(--radius-lg);
  padding: 20rpx 24rpx;
}
.iv-info__icon  { font-size: 32rpx; }
.iv-info__title { display: block; font-size: 26rpx; font-weight: 600; color: var(--bhp-primary-700, #047857); margin-bottom: 6rpx; }
.iv-info__desc  { display: block; font-size: 22rpx; color: var(--bhp-primary-600, #059669); line-height: 1.5; }

/* section */
.iv-section { padding-top: 24rpx; }
.iv-section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8rpx; }
.iv-section-title { display: block; font-size: 26rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 16rpx; }
.iv-section-sub { display: block; margin-bottom: 16rpx; }
.iv-refresh-btn { cursor: pointer; padding: 4rpx 8rpx; }

/* 导师卡 */
.iv-mentor-card {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 16rpx 20rpx;
  margin-bottom: 10rpx;
}
.iv-mentor__avatar {
  width: 68rpx; height: 68rpx;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.iv-mentor__avatar-text { font-size: 28rpx; color: #fff; font-weight: 700; }
.iv-mentor__body { flex: 1; overflow: hidden; }
.iv-mentor__name-row { display: flex; align-items: center; gap: 10rpx; margin-bottom: 4rpx; }
.iv-mentor__name { font-size: 26rpx; font-weight: 500; color: var(--text-primary); }
.iv-mentor__role-tag {
  font-size: 18rpx; font-weight: 700;
  padding: 2rpx 10rpx;
  border-radius: var(--radius-full);
}
.iv-mentor__status-dot {
  width: 14rpx; height: 14rpx;
  border-radius: 50%;
  flex-shrink: 0;
}
.iv-status--active    { background: var(--bhp-success-500, #22c55e); }
.iv-status--graduated { background: var(--bhp-primary-400, #34d399); }
.iv-status--withdrawn { background: var(--bhp-gray-300); }

/* 空状态 inline */
.iv-empty-inline {
  padding: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface);
  border-radius: var(--radius-lg);
  margin-bottom: 10rpx;
}

/* 推荐导师 */
.iv-suggestion {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 16rpx 20rpx;
  margin-bottom: 10rpx;
}
.iv-suggestion--companion { opacity: 0.65; }
.iv-suggestion__avatar {
  width: 68rpx; height: 68rpx;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.iv-suggestion__avatar-text { font-size: 28rpx; color: #fff; font-weight: 700; }
.iv-suggestion__body { flex: 1; overflow: hidden; }
.iv-suggestion__name-row { display: flex; align-items: center; gap: 10rpx; margin-bottom: 4rpx; }
.iv-suggestion__name { font-size: 26rpx; font-weight: 500; color: var(--text-primary); }
.iv-suggestion__role-tag {
  font-size: 18rpx; font-weight: 700;
  padding: 2rpx 10rpx;
  border-radius: var(--radius-full);
}
.iv-suggestion__meta { display: flex; gap: 0; }
.iv-suggestion__reason { color: var(--bhp-primary-500); margin-top: 4rpx; display: block; }
.iv-suggestion__action { flex-shrink: 0; }

/* 标签 */
.iv-tag {
  font-size: 20rpx;
  padding: 6rpx 16rpx;
  border-radius: var(--radius-full);
}
.iv-tag--companion {
  color: var(--bhp-success-600, #16a34a);
  background: var(--bhp-success-50, #f0fdf4);
}
.iv-tag--tip {
  color: var(--text-tertiary);
  background: var(--bhp-gray-100);
}

/* 空状态 */
.iv-empty { display: flex; flex-direction: column; align-items: center; padding: 60rpx 0; gap: 12rpx; }
.iv-empty__icon { font-size: 60rpx; }
.iv-empty__text { font-size: 26rpx; color: var(--text-tertiary); }

/* 底部提示 */
.iv-tip { padding-top: 16rpx; }
.iv-tip__card {
  background: var(--bhp-gray-50, #f9fafb);
  border-radius: var(--radius-lg);
  padding: 16rpx 20rpx;
  border: 1px solid var(--border-light);
}
.iv-tip__text { font-size: 22rpx; color: var(--text-secondary); line-height: 1.6; display: block; }
</style>
