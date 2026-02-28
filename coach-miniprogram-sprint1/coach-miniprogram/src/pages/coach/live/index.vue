<template>
  <view class="live-page">

    <!-- 功能横幅 -->
    <view class="live-banner px-4">
      <view class="live-banner__card">
        <view class="live-banner__info">
          <text class="live-banner__title">🎥 直播管理</text>
          <text class="live-banner__sub">管理教练直播会话，与学员实时互动</text>
        </view>
        <view class="live-banner__btn" @tap="createSession">
          <text>+ 新建</text>
        </view>
      </view>
    </view>

    <!-- 状态 Tab -->
    <view class="live-tabs px-4">
      <view class="live-tabs__inner">
        <view
          v-for="tab in TABS"
          :key="tab.key"
          class="live-tab"
          :class="{ 'live-tab--active': activeTab === tab.key }"
          @tap="switchTab(tab.key)"
        >
          <text>{{ tab.label }}</text>
        </view>
      </view>
    </view>

    <!-- 列表 -->
    <view class="live-list px-4">

      <template v-if="loading">
        <view v-for="i in 3" :key="i" class="bhp-skeleton" style="height: 130rpx; margin-bottom: 12rpx; border-radius: var(--radius-lg);"></view>
      </template>

      <template v-else-if="sessions.length">
        <view
          v-for="s in sessions"
          :key="s.id"
          class="live-item bhp-card bhp-card--flat"
          :class="{ 'live-item--live': s.status === 'live' }"
        >
          <!-- 状态指示 -->
          <view class="live-item__status" :class="`live-status--${s.status}`">
            <view class="live-dot" v-if="s.status === 'live'"></view>
            <text>{{ STATUS_LABEL[s.status] }}</text>
          </view>

          <!-- 内容 -->
          <text class="live-item__title">{{ s.title }}</text>
          <view class="live-item__meta">
            <text class="text-xs text-secondary-color">📅 {{ formatDateTime(s.scheduled_at) }}</text>
            <text class="text-xs text-secondary-color">⏱ {{ s.duration_minutes }}分钟</text>
            <text class="text-xs text-secondary-color" v-if="s.participant_count != null">
              👥 {{ s.participant_count }}人参与
            </text>
          </view>

          <!-- 操作 -->
          <view class="live-item__actions">
            <view class="live-action-btn live-action-btn--secondary" @tap="copyLink(s.id)" v-if="s.status !== 'ended'">
              <text>复制链接</text>
            </view>
            <view
              class="live-action-btn"
              :class="s.status === 'live' ? 'live-action-btn--live' : s.status === 'scheduled' ? 'live-action-btn--start' : 'live-action-btn--disabled'"
              @tap="handleAction(s)"
            >
              <text>{{ s.status === 'live' ? '进入直播间' : s.status === 'scheduled' ? '开始直播' : '查看回放' }}</text>
            </view>
          </view>
        </view>
      </template>

      <!-- 空状态 -->
      <view class="live-empty" v-else-if="!loading">
        <text class="live-empty__icon">🎥</text>
        <text class="live-empty__title">{{ emptyText }}</text>
        <text class="live-empty__sub text-secondary-color" v-if="activeTab === 'scheduled'">
          点击右上角"新建"创建直播会话
        </text>
      </view>
    </view>

    <!-- 新建弹窗 -->
    <view class="live-overlay" v-if="showCreate" @tap.self="showCreate = false">
      <view class="live-create-modal">
        <text class="live-create-modal__title">新建直播会话</text>

        <view class="live-form__field">
          <text class="live-form__label">直播主题</text>
          <input
            class="live-form__input"
            v-model="createForm.title"
            placeholder="例：糖尿病饮食管理讲座"
            placeholder-class="live-input-placeholder"
            maxlength="50"
          />
        </view>

        <view class="live-form__field">
          <text class="live-form__label">计划时间</text>
          <view class="live-form__picker" @tap="pickTime">
            <text :class="createForm.scheduled_at ? 'text-primary' : 'text-tertiary-color'">
              {{ createForm.scheduled_at || '选择时间' }}
            </text>
          </view>
        </view>

        <view class="live-form__field">
          <text class="live-form__label">时长（分钟）</text>
          <view class="live-duration-row">
            <view
              v-for="d in [30, 45, 60, 90]"
              :key="d"
              class="live-duration-opt"
              :class="{ 'live-duration-opt--active': createForm.duration_minutes === d }"
              @tap="createForm.duration_minutes = d"
            >
              <text>{{ d }}min</text>
            </view>
          </view>
        </view>

        <view class="live-create-modal__actions">
          <view class="live-modal-cancel" @tap="showCreate = false">
            <text>取消</text>
          </view>
          <view
            class="live-modal-confirm"
            :class="{ 'live-modal-confirm--active': canCreate && !creating }"
            @tap="submitCreate"
          >
            <text v-if="!creating">创建</text>
            <text v-else>创建中...</text>
          </view>
        </view>
      </view>
    </view>

    <view style="height: 40rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { coachApi, type LiveSession } from '@/api/coach'

type TabKey = 'scheduled' | 'live' | 'ended'

const TABS: { key: TabKey; label: string }[] = [
  { key: 'scheduled', label: '待开始' },
  { key: 'live',      label: '进行中' },
  { key: 'ended',     label: '已结束' },
]
const STATUS_LABEL: Record<string, string> = {
  scheduled: '待开始', live: 'LIVE', ended: '已结束'
}

const activeTab  = ref<TabKey>('scheduled')
const sessions   = ref<LiveSession[]>([])
const loading    = ref(false)
const showCreate = ref(false)
const creating   = ref(false)

const createForm = reactive({
  title: '',
  scheduled_at: '',
  duration_minutes: 60
})

const canCreate = computed(() =>
  createForm.title.trim() && createForm.scheduled_at && createForm.duration_minutes > 0
)

const emptyText = computed(() => ({
  scheduled: '暂无待开始的直播',
  live:      '当前无进行中的直播',
  ended:     '暂无历史直播记录'
}[activeTab.value]))

onMounted(() => loadSessions())

async function switchTab(key: TabKey) {
  activeTab.value = key
  await loadSessions()
}

async function loadSessions() {
  loading.value = true
  try {
    const data = await coachApi.liveSessions(activeTab.value)
    sessions.value = Array.isArray(data) ? data : []
  } catch {
    // 降级：静默失败，显示空状态
    sessions.value = []
  } finally {
    loading.value = false
  }
}

function createSession() {
  createForm.title = ''
  createForm.scheduled_at = ''
  createForm.duration_minutes = 60
  showCreate.value = true
}

function pickTime() {
  // uni-app 日期时间选择器
  const now = new Date()
  uni.showModal({
    title: '选择时间',
    content: '请在下方确认时间（格式：YYYY-MM-DD HH:mm）',
    editable: true,
    placeholderText: `例：${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')} 14:00`,
    success: (res) => {
      if (res.confirm && res.content) {
        createForm.scheduled_at = res.content
      }
    }
  })
}

async function submitCreate() {
  if (!canCreate.value || creating.value) return
  creating.value = true
  try {
    await coachApi.createLive({
      title: createForm.title.trim(),
      scheduled_at: new Date(createForm.scheduled_at).toISOString(),
      duration_minutes: createForm.duration_minutes
    })
    showCreate.value = false
    uni.showToast({ title: '直播已创建', icon: 'success' })
    await loadSessions()
  } catch (e: any) {
    uni.showToast({ title: e?.data?.detail || '创建失败', icon: 'none' })
  } finally {
    creating.value = false
  }
}

function handleAction(s: LiveSession) {
  if (s.status === 'ended') {
    uni.showToast({ title: '回放功能开发中', icon: 'none' })
    return
  }
  uni.showModal({
    title: s.status === 'live' ? '进入直播间' : '开始直播',
    content: `${s.title}\n直播功能需要在完整版 APP 中使用`,
    confirmText: '知道了',
    showCancel: false
  })
}

function copyLink(id: number) {
  uni.setClipboardData({
    data: `https://bhp.example.com/live/${id}`,
    success: () => uni.showToast({ title: '链接已复制', icon: 'success' })
  })
}

function formatDateTime(s: string): string {
  if (!s) return ''
  try {
    const d = new Date(s)
    return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  } catch { return s }
}
</script>

<style scoped>
.live-page { background: var(--surface-secondary); min-height: 100vh; }

/* 横幅 */
.live-banner { padding-top: 16rpx; }
.live-banner__card {
  display: flex; align-items: center; justify-content: space-between;
  background: linear-gradient(135deg, #f5222d, #fa8c16);
  border-radius: var(--radius-lg); padding: 20rpx 24rpx;
}
.live-banner__title { display: block; font-size: 30rpx; font-weight: 700; color: #fff; margin-bottom: 4rpx; }
.live-banner__sub { display: block; font-size: 22rpx; color: rgba(255,255,255,0.8); }
.live-banner__btn {
  background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.5);
  border-radius: var(--radius-full); padding: 10rpx 24rpx;
  font-size: 26rpx; font-weight: 600; color: #fff; cursor: pointer;
}
.live-banner__btn:active { opacity: 0.8; }

/* Tabs */
.live-tabs { padding-top: 12rpx; }
.live-tabs__inner {
  display: flex; background: var(--surface);
  border-radius: var(--radius-full); padding: 6rpx;
  border: 1px solid var(--border-light); gap: 4rpx;
}
.live-tab {
  flex: 1; text-align: center; padding: 10rpx 8rpx;
  border-radius: var(--radius-full);
  font-size: 26rpx; color: var(--text-secondary); cursor: pointer;
}
.live-tab--active { background: var(--bhp-primary-500); color: #fff; font-weight: 600; }

/* 列表 */
.live-list { padding-top: 12rpx; }
.live-item {
  padding: 20rpx 24rpx; margin-bottom: 12rpx;
  border-left: 4rpx solid transparent;
}
.live-item--live { border-left-color: #f5222d; background: #fff1f0; }

.live-item__status {
  display: inline-flex; align-items: center; gap: 8rpx;
  font-size: 20rpx; font-weight: 700;
  padding: 3rpx 12rpx; border-radius: var(--radius-full);
  margin-bottom: 10rpx;
}
.live-status--scheduled { background: var(--bhp-warn-50); color: var(--bhp-warn-700, #b45309); }
.live-status--live      { background: #fff1f0; color: #f5222d; }
.live-status--ended     { background: var(--bhp-gray-100); color: var(--text-tertiary); }

.live-dot {
  width: 12rpx; height: 12rpx; border-radius: 50%;
  background: #f5222d;
  animation: live-pulse 1.2s ease-in-out infinite;
}
@keyframes live-pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.3; }
}

.live-item__title { display: block; font-size: 28rpx; font-weight: 600; color: var(--text-primary); margin-bottom: 10rpx; }
.live-item__meta { display: flex; flex-wrap: wrap; gap: 12rpx; margin-bottom: 16rpx; }

.live-item__actions { display: flex; gap: 10rpx; justify-content: flex-end; }
.live-action-btn {
  padding: 10rpx 20rpx; border-radius: var(--radius-full);
  font-size: 22rpx; font-weight: 600; cursor: pointer;
}
.live-action-btn:active { opacity: 0.8; }
.live-action-btn--secondary { background: var(--bhp-gray-100); color: var(--text-secondary); }
.live-action-btn--start    { background: var(--bhp-primary-500); color: #fff; }
.live-action-btn--live     { background: #f5222d; color: #fff; }
.live-action-btn--disabled { background: var(--bhp-gray-100); color: var(--text-tertiary); }

/* 空状态 */
.live-empty { display: flex; flex-direction: column; align-items: center; padding: 80rpx 0; gap: 12rpx; }
.live-empty__icon  { font-size: 80rpx; }
.live-empty__title { font-size: 28rpx; color: var(--text-tertiary); }
.live-empty__sub   { font-size: 24rpx; }

/* 弹窗 */
.live-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex; align-items: flex-end; justify-content: center;
  z-index: 1000;
}
.live-create-modal {
  background: var(--surface); border-radius: var(--radius-xl, 24rpx) var(--radius-xl, 24rpx) 0 0;
  padding: 40rpx 32rpx 60rpx; width: 100%;
}
.live-create-modal__title {
  display: block; font-size: 32rpx; font-weight: 700;
  color: var(--text-primary); text-align: center; margin-bottom: 32rpx;
}
.live-form__field { margin-bottom: 24rpx; }
.live-form__label { display: block; font-size: 24rpx; color: var(--text-secondary); margin-bottom: 10rpx; }
.live-form__input, .live-form__picker {
  width: 100%; height: 72rpx;
  background: var(--bhp-gray-50, #f9fafb);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: 0 20rpx; font-size: 26rpx; color: var(--text-primary);
  box-sizing: border-box; display: flex; align-items: center;
}
.live-input-placeholder { color: var(--text-tertiary); font-size: 26rpx; }

.live-duration-row { display: flex; gap: 10rpx; }
.live-duration-opt {
  flex: 1; text-align: center; padding: 14rpx 8rpx;
  border-radius: var(--radius-lg);
  background: var(--bhp-gray-100); color: var(--text-secondary);
  font-size: 24rpx; cursor: pointer; border: 2rpx solid transparent;
}
.live-duration-opt--active {
  border-color: var(--bhp-primary-500);
  background: var(--bhp-primary-50); color: var(--bhp-primary-600, #059669); font-weight: 600;
}

.live-create-modal__actions { display: flex; gap: 16rpx; margin-top: 32rpx; }
.live-modal-cancel, .live-modal-confirm {
  flex: 1; height: 88rpx; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 28rpx; font-weight: 600; cursor: pointer;
}
.live-modal-cancel  { background: var(--bhp-gray-100); color: var(--text-secondary); }
.live-modal-confirm { background: var(--bhp-gray-200); color: var(--text-tertiary); }
.live-modal-confirm--active { background: var(--bhp-primary-500); color: #fff; }
.live-modal-confirm--active:active { opacity: 0.8; }
</style>
