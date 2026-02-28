<template>
  <view class="companion-page">

    <!-- 统计横幅 -->
    <view class="cp-banner">
      <view class="cp-banner__inner">
        <view class="cp-banner__stat">
          <text class="cp-banner__val">{{ stats?.active_count || 0 }}</text>
          <text class="cp-banner__lbl">进行中</text>
        </view>
        <view class="cp-banner__divider"></view>
        <view class="cp-banner__stat">
          <text class="cp-banner__val">{{ stats?.graduated_count || 0 }}</text>
          <text class="cp-banner__lbl">已毕业</text>
        </view>
        <view class="cp-banner__divider"></view>
        <view class="cp-banner__stat">
          <text class="cp-banner__val">{{ stats?.avg_quality ? Number(stats.avg_quality).toFixed(1) : '-' }}</text>
          <text class="cp-banner__lbl">质量分</text>
        </view>
        <view class="cp-banner__divider"></view>
        <view class="cp-banner__stat" @tap="goInvitations">
          <text class="cp-banner__val">{{ stats?.qualified_count || 0 }}</text>
          <text class="cp-banner__lbl">符合晋级</text>
        </view>
      </view>
    </view>

    <!-- 晋级资格提示 -->
    <view class="cp-promo-tip px-4" v-if="showPromoTip">
      <view class="cp-promo-tip__card" @tap="goJourney">
        <text class="cp-promo-tip__icon">🚀</text>
        <text class="cp-promo-tip__text">同道者条件已满足，可查看晋级进度</text>
        <text class="cp-promo-tip__arrow">›</text>
      </view>
    </view>

    <!-- Tab 切换 -->
    <view class="cp-tabs">
      <view
        class="cp-tab"
        :class="{ 'cp-tab--active': activeTab === 'mentees' }"
        @tap="setTab('mentees')"
      >
        <text>我带教的</text>
        <text class="cp-tab__count" v-if="mentees.length">{{ mentees.length }}</text>
      </view>
      <view
        class="cp-tab"
        :class="{ 'cp-tab--active': activeTab === 'mentors' }"
        @tap="setTab('mentors')"
      >
        <text>指导我的</text>
        <text class="cp-tab__count" v-if="mentors.length">{{ mentors.length }}</text>
      </view>
    </view>

    <!-- 学员列表 -->
    <view class="cp-list px-4" v-show="activeTab === 'mentees'">

      <template v-if="loadingMentees">
        <view v-for="i in 3" :key="i" class="bhp-skeleton" style="height: 110rpx; margin-bottom: 12rpx; border-radius: var(--radius-lg);"></view>
      </template>

      <template v-else>
        <!-- 筛选按钮 -->
        <view class="cp-list-filter">
          <view
            v-for="f in statusFilters"
            :key="f.key"
            class="cp-list-filter__btn"
            :class="{ 'cp-list-filter__btn--active': menteeFilter === f.key }"
            @tap="menteeFilter = f.key"
          >
            <text>{{ f.label }}</text>
          </view>
        </view>

        <view
          v-for="m in filteredMentees"
          :key="m.id"
          class="cp-item bhp-card bhp-card--flat"
          @tap="goDetail(m.mentee_id, m.id, 'mentee')"
        >
          <!-- 头像占位 -->
          <view class="cp-item__avatar" :style="{ background: getRoleColor(m.mentee_role) }">
            <text class="cp-item__avatar-text">{{ (m.mentee_name || '用')[0] }}</text>
          </view>
          <view class="cp-item__body">
            <view class="cp-item__name-row">
              <text class="cp-item__name">{{ m.mentee_name || `用户${m.mentee_id}` }}</text>
              <view class="cp-item__role-tag" :style="{ background: getRoleColor(m.mentee_role) + '20', color: getRoleColor(m.mentee_role) }">
                <text>{{ ROLE_LABEL[m.mentee_role || ''] || m.mentee_role || '-' }}</text>
              </view>
            </view>
            <view class="cp-item__meta">
              <text class="text-xs text-secondary-color">加入 {{ formatDate(m.created_at) }}</text>
              <text class="text-xs text-secondary-color" v-if="m.quality_score">
                · 质量分 {{ Number(m.quality_score).toFixed(1) }}
              </text>
            </view>
          </view>
          <view class="cp-item__status-tag" :class="`cp-status--${m.status}`">
            <text>{{ STATUS_LABEL[m.status] }}</text>
          </view>
        </view>

        <view class="cp-empty" v-if="!loadingMentees && !filteredMentees.length">
          <text class="cp-empty__icon">👥</text>
          <text class="cp-empty__text">{{ menteeFilter === 'all' ? '还没有带教学员' : '该状态暂无记录' }}</text>
          <view class="bhp-btn bhp-btn--primary mt-4" @tap="goInvite" v-if="menteeFilter === 'all'">
            <text>邀请学员</text>
          </view>
        </view>
      </template>
    </view>

    <!-- 导师列表 -->
    <view class="cp-list px-4" v-show="activeTab === 'mentors'">

      <template v-if="loadingMentors">
        <view v-for="i in 2" :key="i" class="bhp-skeleton" style="height: 110rpx; margin-bottom: 12rpx; border-radius: var(--radius-lg);"></view>
      </template>

      <template v-else>
        <view
          v-for="m in mentors"
          :key="m.id"
          class="cp-item bhp-card bhp-card--flat"
          @tap="goDetail(m.mentor_id, m.id, 'mentor')"
        >
          <view class="cp-item__avatar" :style="{ background: getRoleColor(m.mentor_role) }">
            <text class="cp-item__avatar-text">{{ (m.mentor_name || '导')[0] }}</text>
          </view>
          <view class="cp-item__body">
            <view class="cp-item__name-row">
              <text class="cp-item__name">{{ m.mentor_name || `用户${m.mentor_id}` }}</text>
              <view class="cp-item__role-tag" :style="{ background: getRoleColor(m.mentor_role) + '20', color: getRoleColor(m.mentor_role) }">
                <text>{{ ROLE_LABEL[m.mentor_role || ''] || m.mentor_role || '-' }}</text>
              </view>
            </view>
            <view class="cp-item__meta">
              <text class="text-xs text-secondary-color">带教自 {{ formatDate(m.created_at) }}</text>
            </view>
          </view>
          <view class="cp-item__status-tag" :class="`cp-status--${m.status}`">
            <text>{{ STATUS_LABEL[m.status] }}</text>
          </view>
        </view>

        <view class="cp-empty" v-if="!loadingMentors && !mentors.length">
          <text class="cp-empty__icon">🎓</text>
          <text class="cp-empty__text">暂无导师关系</text>
          <view class="bhp-btn bhp-btn--secondary mt-4" @tap="goInvitations">
            <text>查看匹配推荐</text>
          </view>
        </view>
      </template>
    </view>

    <!-- FAB：邀请学员 -->
    <view class="cp-fab" @tap="goInvite" v-if="activeTab === 'mentees'">
      <text class="cp-fab__icon">+</text>
      <text class="cp-fab__label">邀请学员</text>
    </view>

    <view style="height: 100rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { companionApi, type MenteeRelation, type MentorRelation, type CompanionStats } from '@/api/companion'

const userStore = useUserStore()

const stats          = ref<CompanionStats | null>(null)
const mentees        = ref<MenteeRelation[]>([])
const mentors        = ref<MentorRelation[]>([])
const loadingMentees = ref(false)
const loadingMentors = ref(false)
const activeTab      = ref<'mentees' | 'mentors'>('mentees')
const menteeFilter   = ref<'all' | 'active' | 'graduated'>('all')

const STATUS_LABEL: Record<string, string> = {
  active: '进行中', graduated: '已毕业', withdrawn: '已退出'
}
const ROLE_LABEL: Record<string, string> = {
  observer: 'L0', grower: 'L1', sharer: 'L2',
  coach: 'L3', promoter: 'L4', supervisor: 'L4', master: 'L5'
}
const ROLE_COLORS: Record<string, string> = {
  observer: '#8c8c8c', grower: '#52c41a', sharer: '#1890ff',
  coach: '#722ed1', promoter: '#eb2f96', supervisor: '#eb2f96', master: '#faad14'
}
const statusFilters = [
  { key: 'all', label: '全部' },
  { key: 'active', label: '进行中' },
  { key: 'graduated', label: '已毕业' },
]

const filteredMentees = computed(() =>
  menteeFilter.value === 'all'
    ? mentees.value
    : mentees.value.filter(m => m.status === menteeFilter.value)
)

// 是否满足晋级同道者条件
const showPromoTip = computed(() => {
  const qualified = stats.value?.qualified_count || 0
  const level = userStore.roleLevel
  if (level >= 3 && level <= 4) return qualified >= 4
  return false
})

function getRoleColor(role?: string): string {
  return ROLE_COLORS[role || ''] || '#8c8c8c'
}

onMounted(async () => {
  await Promise.all([loadStats(), loadMentees()])
})

onPullDownRefresh(async () => {
  await Promise.all([loadStats(), loadMentees(),
    activeTab.value === 'mentors' ? loadMentors() : Promise.resolve()])
  uni.stopPullDownRefresh()
})

async function loadStats() {
  try { stats.value = await companionApi.stats() } catch { /* 静默 */ }
}

async function loadMentees() {
  loadingMentees.value = true
  try {
    const data = await companionApi.myMentees()
    mentees.value = Array.isArray(data) ? data : []
  } catch { /* 静默 */ } finally {
    loadingMentees.value = false
  }
}

async function loadMentors() {
  if (mentors.value.length) return  // 已加载
  loadingMentors.value = true
  try {
    const data = await companionApi.myMentors()
    mentors.value = Array.isArray(data) ? data : []
  } catch { /* 静默 */ } finally {
    loadingMentors.value = false
  }
}

function setTab(tab: 'mentees' | 'mentors') {
  activeTab.value = tab
  if (tab === 'mentors') loadMentors()
}

function goDetail(userId: number, relationId: number, type: string) {
  uni.navigateTo({
    url: `/pages/companions/detail?user_id=${userId}&relation_id=${relationId}&type=${type}`
  })
}
function goInvite()      { uni.navigateTo({ url: '/pages/companions/invite' }) }
function goInvitations() { uni.navigateTo({ url: '/pages/companions/invitations' }) }
function goJourney()     { uni.navigateTo({ url: '/pages/journey/progress' }) }

function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr)
    return `${d.getFullYear()}.${d.getMonth() + 1}.${d.getDate()}`
  } catch { return '' }
}
</script>

<style scoped>
.companion-page { background: var(--surface-secondary); min-height: 100vh; }

/* 统计横幅 */
.cp-banner {
  background: linear-gradient(135deg, #722ed1, #eb2f96);
  padding: 40rpx 0 28rpx;
}
.cp-banner__inner { display: flex; align-items: center; }
.cp-banner__stat { flex: 1; text-align: center; cursor: pointer; }
.cp-banner__val { display: block; font-size: 44rpx; font-weight: 700; color: #fff; }
.cp-banner__lbl { display: block; font-size: 20rpx; color: rgba(255,255,255,0.8); margin-top: 4rpx; }
.cp-banner__divider { width: 1px; height: 48rpx; background: rgba(255,255,255,0.3); }

/* 晋级提示 */
.cp-promo-tip { padding-top: 12rpx; }
.cp-promo-tip__card {
  display: flex;
  align-items: center;
  gap: 12rpx;
  background: var(--bhp-primary-50);
  border: 1px solid var(--bhp-primary-200, #a7f3d0);
  border-radius: var(--radius-lg);
  padding: 14rpx 20rpx;
  cursor: pointer;
}
.cp-promo-tip__icon  { font-size: 28rpx; }
.cp-promo-tip__text  { flex: 1; font-size: 24rpx; color: var(--bhp-primary-700, #047857); }
.cp-promo-tip__arrow { font-size: 28rpx; color: var(--bhp-primary-500); }

/* Tab */
.cp-tabs {
  display: flex;
  background: var(--surface);
  border-bottom: 1px solid var(--border-light);
}
.cp-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  padding: 22rpx 0;
  font-size: 26rpx;
  color: var(--text-secondary);
  position: relative;
  cursor: pointer;
}
.cp-tab--active {
  color: var(--bhp-primary-500);
  font-weight: 600;
}
.cp-tab--active::after {
  content: '';
  position: absolute;
  bottom: 0; left: 20%; right: 20%;
  height: 4rpx;
  background: var(--bhp-primary-500);
  border-radius: 9999px;
}
.cp-tab__count {
  background: var(--bhp-primary-500);
  color: #fff;
  font-size: 18rpx;
  min-width: 28rpx;
  height: 28rpx;
  border-radius: 9999px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 6rpx;
}

/* 列表 */
.cp-list { padding-top: 12rpx; }

.cp-list-filter {
  display: flex;
  gap: 10rpx;
  margin-bottom: 12rpx;
}
.cp-list-filter__btn {
  padding: 8rpx 20rpx;
  border-radius: var(--radius-full);
  font-size: 22rpx;
  color: var(--text-secondary);
  border: 1px solid var(--border-default);
  cursor: pointer;
}
.cp-list-filter__btn--active {
  background: var(--bhp-primary-500);
  color: #fff;
  border-color: var(--bhp-primary-500);
  font-weight: 600;
}

/* 条目 */
.cp-item {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 18rpx 20rpx;
  margin-bottom: 10rpx;
  cursor: pointer;
}
.cp-item:active { opacity: 0.8; }

.cp-item__avatar {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.cp-item__avatar-text { font-size: 28rpx; color: #fff; font-weight: 700; }

.cp-item__body { flex: 1; overflow: hidden; }
.cp-item__name-row { display: flex; align-items: center; gap: 10rpx; margin-bottom: 6rpx; }
.cp-item__name { font-size: 28rpx; font-weight: 500; color: var(--text-primary); }
.cp-item__role-tag {
  font-size: 20rpx;
  font-weight: 700;
  padding: 2rpx 12rpx;
  border-radius: var(--radius-full);
}
.cp-item__meta { display: flex; gap: 0; }

.cp-item__status-tag {
  font-size: 20rpx;
  font-weight: 600;
  padding: 4rpx 14rpx;
  border-radius: var(--radius-full);
}
.cp-status--active    { background: var(--bhp-primary-50); color: var(--bhp-primary-600, #059669); }
.cp-status--graduated { background: var(--bhp-success-50, #f0fdf4); color: var(--bhp-success-600, #16a34a); }
.cp-status--withdrawn { background: var(--bhp-gray-100); color: var(--text-tertiary); }

/* 空状态 */
.cp-empty {
  display: flex; flex-direction: column; align-items: center;
  padding: 80rpx 0; gap: 16rpx;
}
.cp-empty__icon { font-size: 80rpx; }
.cp-empty__text { font-size: 26rpx; color: var(--text-tertiary); }

/* FAB */
.cp-fab {
  position: fixed;
  bottom: 40rpx; right: 40rpx;
  background: linear-gradient(135deg, #722ed1, #eb2f96);
  border-radius: var(--radius-full);
  padding: 16rpx 28rpx;
  display: flex; align-items: center; gap: 8rpx;
  box-shadow: 0 4px 16px rgba(114,46,209,0.4);
  cursor: pointer; z-index: 50;
}
.cp-fab:active { opacity: 0.8; transform: scale(0.95); }
.cp-fab__icon  { font-size: 32rpx; color: #fff; font-weight: 700; }
.cp-fab__label { font-size: 26rpx; color: #fff; font-weight: 600; }
</style>
