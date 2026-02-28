<template>
  <view class="cp-detail-page">

    <!-- 用户信息卡 -->
    <view class="cpd-profile px-4">
      <view class="cpd-profile__card bhp-card bhp-card--flat">
        <!-- 头像 + 基础信息 -->
        <view class="cpd-profile__header">
          <view class="cpd-profile__avatar" :style="{ background: roleColor }">
            <text class="cpd-profile__avatar-text">{{ displayName[0] || '用' }}</text>
          </view>
          <view class="cpd-profile__info">
            <text class="cpd-profile__name">{{ displayName }}</text>
            <view class="cpd-profile__level-tag" :style="{ background: roleColor + '20', color: roleColor }">
              <text>{{ ROLE_LABEL[relation?.type === 'mentee' ? (relation.mentee_role || '') : (relation.mentor_role || '')] || '未知' }}</text>
            </view>
          </view>
          <!-- 关系类型 -->
          <view class="cpd-profile__rel-badge" :class="relType === 'mentee' ? 'cpd-badge--mentee' : 'cpd-badge--mentor'">
            <text>{{ relType === 'mentee' ? '我的学员' : '我的导师' }}</text>
          </view>
        </view>

        <!-- 关系信息 -->
        <view class="cpd-profile__rel-info">
          <view class="cpd-rel-item">
            <text class="cpd-rel-item__label">关系状态</text>
            <view class="cpd-rel-item__value-tag" :class="`cp-status--${relation?.status || 'active'}`">
              <text>{{ STATUS_LABEL[relation?.status || 'active'] }}</text>
            </view>
          </view>
          <view class="cpd-rel-item">
            <text class="cpd-rel-item__label">建立时间</text>
            <text class="cpd-rel-item__value">{{ formatDate(relation?.created_at) }}</text>
          </view>
          <view class="cpd-rel-item" v-if="relation?.quality_score">
            <text class="cpd-rel-item__label">关系质量分</text>
            <text class="cpd-rel-item__value">{{ Number(relation.quality_score).toFixed(1) }}</text>
          </view>
          <view class="cpd-rel-item" v-if="relation?.graduated_at">
            <text class="cpd-rel-item__label">毕业时间</text>
            <text class="cpd-rel-item__value">{{ formatDate(relation.graduated_at) }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 互动记录入口（导师视角）-->
    <view class="cpd-interaction px-4" v-if="relType === 'mentee' && relation?.status === 'active'">
      <view class="cpd-section-title">记录互动</view>
      <view class="cpd-interaction-types">
        <view
          v-for="itype in interactionTypes"
          :key="itype.key"
          class="cpd-itype-btn"
          :class="{ 'cpd-itype-btn--selected': selectedInteraction === itype.key }"
          @tap="selectedInteraction = itype.key"
        >
          <text class="cpd-itype-btn__icon">{{ itype.icon }}</text>
          <text class="cpd-itype-btn__label">{{ itype.label }}</text>
        </view>
      </view>

      <!-- 质量评分 -->
      <view class="cpd-quality-row" v-if="selectedInteraction">
        <text class="cpd-quality-label">互动质量评分</text>
        <view class="cpd-stars">
          <view
            v-for="s in 5"
            :key="s"
            class="cpd-star"
            :class="{ 'cpd-star--active': s <= qualityScore }"
            @tap="qualityScore = s"
          >
            <text>★</text>
          </view>
        </view>
        <text class="cpd-quality-hint text-xs text-secondary-color">{{ QUALITY_HINT[qualityScore] }}</text>
      </view>

      <view
        class="cpd-record-btn"
        :class="{ 'cpd-record-btn--active': selectedInteraction && !recordingInteraction }"
        @tap="recordInteraction"
        v-if="selectedInteraction"
      >
        <text v-if="!recordingInteraction">记录此次互动</text>
        <text v-else>记录中...</text>
      </view>
    </view>

    <!-- 导师操作：毕业 -->
    <view class="cpd-actions px-4" v-if="relType === 'mentee' && relation?.status === 'active'">
      <view class="cpd-section-title">导师操作</view>
      <view class="cpd-graduate-card bhp-card bhp-card--flat">
        <view class="cpd-graduate-card__info">
          <text class="cpd-graduate-card__title">🎓 让学员毕业</text>
          <text class="cpd-graduate-card__desc">学员已完成学习目标，可标记为毕业状态</text>
        </view>
        <view
          class="cpd-graduate-btn"
          :class="{ 'cpd-graduate-btn--loading': graduating }"
          @tap="graduateMentee"
        >
          <text v-if="!graduating">毕业</text>
          <text v-else>处理中...</text>
        </view>
      </view>
    </view>

    <!-- 已毕业提示 -->
    <view class="cpd-graduated-banner px-4" v-if="relation?.status === 'graduated'">
      <view class="cpd-graduated-banner__card">
        <text class="cpd-graduated-banner__icon">🎉</text>
        <view>
          <text class="cpd-graduated-banner__title">此同道已毕业</text>
          <text class="cpd-graduated-banner__sub">毕业时间：{{ formatDate(relation.graduated_at) }}</text>
        </view>
      </view>
    </view>

    <view style="height: 60rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { companionApi, type MenteeRelation, type MentorRelation } from '@/api/companion'

const userId     = ref(0)
const relationId = ref(0)
const relType    = ref<'mentee' | 'mentor'>('mentee')
const relation   = ref<any>(null)

const selectedInteraction = ref('')
const qualityScore        = ref(3)
const recordingInteraction = ref(false)
const graduating           = ref(false)

const STATUS_LABEL: Record<string, string> = {
  active: '进行中', graduated: '已毕业', withdrawn: '已退出'
}
const ROLE_LABEL: Record<string, string> = {
  observer: 'L0 观察员', grower: 'L1 成长者', sharer: 'L2 分享者',
  coach: 'L3 教练', promoter: 'L4 促进师', supervisor: 'L4 督导', master: 'L5 大师'
}
const ROLE_COLORS: Record<string, string> = {
  observer: '#8c8c8c', grower: '#52c41a', sharer: '#1890ff',
  coach: '#722ed1', promoter: '#eb2f96', supervisor: '#eb2f96', master: '#faad14'
}
const QUALITY_HINT: Record<number, string> = {
  1: '需要改进', 2: '一般', 3: '良好', 4: '优秀', 5: '卓越'
}
const interactionTypes = [
  { key: 'chat',     icon: '💬', label: '一对一交流' },
  { key: 'review',   icon: '📝', label: '作业点评' },
  { key: 'guidance', icon: '🎯', label: '目标指导' },
  { key: 'checkin',  icon: '✅', label: '定期检查' },
]

const displayName = computed(() => {
  if (relType.value === 'mentee') return relation.value?.mentee_name || `用户${userId.value}`
  return relation.value?.mentor_name || `用户${userId.value}`
})

const roleColor = computed(() => {
  const role = relType.value === 'mentee'
    ? relation.value?.mentee_role
    : relation.value?.mentor_role
  return ROLE_COLORS[role || ''] || '#8c8c8c'
})

onMounted(async () => {
  const pages = getCurrentPages()
  const cur = pages[pages.length - 1] as any
  const query = cur.$page?.options || cur.options || {}
  userId.value     = Number(query.user_id || 0)
  relationId.value = Number(query.relation_id || 0)
  relType.value    = (query.type === 'mentor' ? 'mentor' : 'mentee') as 'mentee' | 'mentor'
  await loadRelation()
})

async function loadRelation() {
  try {
    if (relType.value === 'mentee') {
      const data = await companionApi.myMentees()
      relation.value = (Array.isArray(data) ? data : []).find(m => m.id === relationId.value) || null
    } else {
      const data = await companionApi.myMentors()
      relation.value = (Array.isArray(data) ? data : []).find(m => m.id === relationId.value) || null
    }
    if (relation.value) {
      uni.setNavigationBarTitle({ title: displayName.value })
    }
  } catch { /* 静默 */ }
}

async function recordInteraction() {
  if (!selectedInteraction.value || recordingInteraction.value) return
  recordingInteraction.value = true
  try {
    await companionApi.recordInteraction(relationId.value, selectedInteraction.value, qualityScore.value * 20)
    selectedInteraction.value = ''
    qualityScore.value = 3
    uni.showToast({ title: '互动已记录 ✓', icon: 'none' })
  } catch {
    uni.showToast({ title: '记录失败，请重试', icon: 'none' })
  } finally {
    recordingInteraction.value = false
  }
}

async function graduateMentee() {
  uni.showModal({
    title: '确认毕业',
    content: `确认将 ${displayName.value} 标记为毕业状态？此操作不可撤回。`,
    confirmText: '确认毕业',
    success: async (res) => {
      if (!res.confirm) return
      graduating.value = true
      try {
        await companionApi.graduate(relationId.value, qualityScore.value * 20)
        if (relation.value) {
          relation.value.status = 'graduated'
          relation.value.graduated_at = new Date().toISOString()
        }
        uni.showToast({ title: '已标记毕业 🎓', icon: 'none', duration: 2500 })
      } catch {
        uni.showToast({ title: '操作失败，请重试', icon: 'none' })
      } finally {
        graduating.value = false
      }
    }
  })
}

function formatDate(dateStr?: string): string {
  if (!dateStr) return '-'
  try {
    const d = new Date(dateStr)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  } catch { return dateStr }
}
</script>

<style scoped>
.cp-detail-page { background: var(--surface-secondary); min-height: 100vh; }

/* 资料卡 */
.cpd-profile { padding-top: 16rpx; }
.cpd-profile__header { display: flex; align-items: center; gap: 16rpx; margin-bottom: 20rpx; }
.cpd-profile__avatar {
  width: 88rpx; height: 88rpx;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.cpd-profile__avatar-text { font-size: 40rpx; color: #fff; font-weight: 700; }
.cpd-profile__info { flex: 1; }
.cpd-profile__name { display: block; font-size: 30rpx; font-weight: 700; color: var(--text-primary); }
.cpd-profile__level-tag {
  display: inline-block;
  font-size: 20rpx; font-weight: 700;
  padding: 3rpx 14rpx;
  border-radius: var(--radius-full);
  margin-top: 6rpx;
}
.cpd-profile__rel-badge {
  font-size: 20rpx; font-weight: 600;
  padding: 4rpx 16rpx;
  border-radius: var(--radius-full);
}
.cpd-badge--mentee { background: var(--bhp-primary-50); color: var(--bhp-primary-600, #059669); }
.cpd-badge--mentor { background: #f9f0ff; color: #722ed1; }

.cpd-profile__rel-info { border-top: 1px solid var(--border-light); padding-top: 16rpx; display: flex; flex-direction: column; gap: 12rpx; }
.cpd-rel-item { display: flex; align-items: center; justify-content: space-between; }
.cpd-rel-item__label { font-size: 24rpx; color: var(--text-secondary); }
.cpd-rel-item__value { font-size: 24rpx; color: var(--text-primary); font-weight: 500; }
.cpd-rel-item__value-tag {
  font-size: 20rpx; font-weight: 600;
  padding: 3rpx 12rpx; border-radius: var(--radius-full);
}
.cp-status--active    { background: var(--bhp-primary-50); color: var(--bhp-primary-600, #059669); }
.cp-status--graduated { background: var(--bhp-success-50, #f0fdf4); color: var(--bhp-success-600, #16a34a); }
.cp-status--withdrawn { background: var(--bhp-gray-100); color: var(--text-tertiary); }

/* 互动 */
.cpd-interaction { padding-top: 16rpx; }
.cpd-section-title { display: block; font-size: 26rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 12rpx; }
.cpd-interaction-types { display: flex; gap: 10rpx; flex-wrap: wrap; margin-bottom: 16rpx; }
.cpd-itype-btn {
  display: flex; flex-direction: column; align-items: center; gap: 6rpx;
  padding: 12rpx 20rpx;
  border: 2px solid var(--border-light);
  border-radius: var(--radius-lg);
  cursor: pointer;
  flex: 1; min-width: calc(25% - 8rpx);
}
.cpd-itype-btn--selected {
  border-color: var(--bhp-primary-500);
  background: var(--bhp-primary-50);
}
.cpd-itype-btn__icon  { font-size: 32rpx; }
.cpd-itype-btn__label { font-size: 20rpx; color: var(--text-secondary); }
.cpd-itype-btn--selected .cpd-itype-btn__label { color: var(--bhp-primary-600, #059669); }

.cpd-quality-row { margin-bottom: 16rpx; }
.cpd-quality-label { display: block; font-size: 24rpx; color: var(--text-secondary); margin-bottom: 8rpx; }
.cpd-stars { display: flex; gap: 8rpx; margin-bottom: 6rpx; }
.cpd-star { font-size: 40rpx; color: var(--bhp-gray-300); cursor: pointer; }
.cpd-star--active { color: var(--bhp-warn-400, #fbbf24); }
.cpd-quality-hint { display: block; }

.cpd-record-btn {
  text-align: center; padding: 18rpx;
  background: var(--bhp-gray-200);
  border-radius: var(--radius-lg);
  font-size: 26rpx; color: var(--text-tertiary);
}
.cpd-record-btn--active { background: var(--bhp-primary-500); color: #fff; cursor: pointer; font-weight: 600; }
.cpd-record-btn--active:active { opacity: 0.8; }

/* 导师操作 */
.cpd-actions { padding-top: 16rpx; }
.cpd-graduate-card {
  display: flex; align-items: center; gap: 16rpx; padding: 20rpx 24rpx;
}
.cpd-graduate-card__info { flex: 1; }
.cpd-graduate-card__title { display: block; font-size: 26rpx; font-weight: 600; color: var(--text-primary); }
.cpd-graduate-card__desc  { display: block; font-size: 22rpx; color: var(--text-secondary); margin-top: 4rpx; }
.cpd-graduate-btn {
  padding: 10rpx 28rpx;
  background: var(--bhp-success-500, #22c55e);
  border-radius: var(--radius-full);
  font-size: 24rpx; font-weight: 700; color: #fff;
  cursor: pointer;
}
.cpd-graduate-btn:active { opacity: 0.8; }
.cpd-graduate-btn--loading { opacity: 0.6; }

/* 已毕业横幅 */
.cpd-graduated-banner { padding-top: 16rpx; }
.cpd-graduated-banner__card {
  display: flex; align-items: center; gap: 16rpx;
  background: var(--bhp-success-50, #f0fdf4);
  border: 1px solid var(--bhp-success-200, #bbf7d0);
  border-radius: var(--radius-lg);
  padding: 20rpx 24rpx;
}
.cpd-graduated-banner__icon  { font-size: 40rpx; }
.cpd-graduated-banner__title { display: block; font-size: 26rpx; font-weight: 600; color: var(--bhp-success-700, #15803d); }
.cpd-graduated-banner__sub   { display: block; font-size: 22rpx; color: var(--bhp-success-600, #16a34a); margin-top: 4rpx; }
</style>
