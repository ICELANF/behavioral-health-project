<template>
  <view class="cf-page">

    <!-- 导航栏 -->
    <view class="cf-navbar safe-area-top">
      <view class="cf-navbar__back" @tap="goBack">
        <text class="cf-navbar__arrow">&#8249;</text>
      </view>
      <text class="cf-navbar__title">AI 飞轮审核</text>
      <view class="cf-navbar__placeholder"></view>
    </view>

    <!-- 今日统计 -->
    <view class="cf-stats">
      <view class="cf-stat">
        <text class="cf-stat__val cf-stat__val--orange">{{ stats.pending }}</text>
        <text class="cf-stat__label">待审核</text>
      </view>
      <view class="cf-stat">
        <text class="cf-stat__val cf-stat__val--blue">{{ stats.total_reviewed }}</text>
        <text class="cf-stat__label">已审核</text>
      </view>
      <view class="cf-stat">
        <text class="cf-stat__val cf-stat__val--green">{{ stats.approved }}</text>
        <text class="cf-stat__label">已通过</text>
      </view>
      <view class="cf-stat">
        <text class="cf-stat__val cf-stat__val--red">{{ stats.rejected }}</text>
        <text class="cf-stat__label">已退回</text>
      </view>
    </view>

    <!-- 审核队列 -->
    <scroll-view scroll-y class="cf-body">

      <template v-if="loading">
        <view class="bhp-skeleton" v-for="i in 3" :key="i" style="height: 240rpx; border-radius: var(--radius-lg); margin-bottom: 16rpx;"></view>
      </template>

      <template v-else-if="queue.length">
        <view
          v-for="item in queue"
          :key="item.id"
          class="cf-card"
          :class="{ 'cf-card--done': item._handled }"
        >
          <!-- 已处理遮罩 -->
          <view class="cf-card__done-overlay" v-if="item._handled">
            <text class="cf-card__done-text" :class="item._action === 'approved' ? 'cf-card__done-text--green' : 'cf-card__done-text--red'">
              {{ item._action === 'approved' ? '已通过 ✓' : '已退回' }}
            </text>
          </view>

          <!-- 卡片头部 -->
          <view class="cf-card__header">
            <text class="cf-card__name">{{ item.student_name }}</text>
            <view class="cf-card__type" :class="`cf-card__type--${item.type}`">
              <text>{{ TYPE_LABEL[item.type] || item.type }}</text>
            </view>
            <view class="cf-card__priority" v-if="item.priority === 'urgent'">
              <text>紧急</text>
            </view>
          </view>

          <!-- AI 摘要 -->
          <text class="cf-card__summary" v-if="item.ai_summary">{{ item.ai_summary }}</text>

          <!-- AI 草稿（可折叠） -->
          <view class="cf-card__draft" v-if="item.ai_draft" @tap="toggleDraft(item)">
            <text class="cf-card__draft-label">AI 草稿 {{ item._expanded ? '▼' : '▶' }}</text>
            <text class="cf-card__draft-text" v-if="item._expanded">{{ item.ai_draft }}</text>
            <text class="cf-card__draft-text cf-card__draft-text--collapsed" v-else>{{ item.ai_draft }}</text>
          </view>

          <!-- 处方字段 -->
          <view class="cf-card__rx" v-if="item.rx_fields && item._expanded">
            <view v-for="(val, key) in item.rx_fields" :key="key" class="cf-card__rx-row">
              <text class="cf-card__rx-key">{{ key }}</text>
              <text class="cf-card__rx-val">{{ val }}</text>
            </view>
          </view>

          <!-- 操作按钮 -->
          <view class="cf-card__actions" v-if="!item._handled">
            <view class="cf-btn cf-btn--approve" @tap="handleApprove(item)">
              <text>✓ 通过</text>
            </view>
            <view class="cf-btn cf-btn--reject" @tap="showRejectModal(item)">
              <text>✗ 退回</text>
            </view>
          </view>

          <!-- 等待时间 -->
          <text class="cf-card__wait" v-if="item.wait_seconds > 0 && !item._handled">
            等待 {{ formatWait(item.wait_seconds) }}
          </text>
        </view>
      </template>

      <!-- 空状态 -->
      <view v-else class="cf-empty">
        <text class="cf-empty__icon">✓</text>
        <text class="cf-empty__text">今日审核已全部完成!</text>
      </view>

    </scroll-view>

    <!-- 底部生成按钮 -->
    <view class="cf-footer">
      <view class="cf-gen-btn" @tap="showStudentPicker = true" :class="{ 'cf-gen-btn--loading': generating }">
        <text class="cf-gen-btn__text">{{ generating ? 'AI 分析中...' : '生成跟进计划' }}</text>
      </view>
    </view>

    <!-- 学员选择器弹窗 -->
    <view class="cf-modal-mask" v-if="showStudentPicker" @tap="showStudentPicker = false">
      <view class="cf-modal" @tap.stop>
        <text class="cf-modal__title">选择学员</text>
        <picker :range="studentNames" @change="onPickStudent">
          <view class="cf-picker-trigger">
            <text>{{ pickedStudent ? (pickedStudent.name || pickedStudent.full_name || pickedStudent.username) : '请选择学员' }}</text>
            <text class="cf-picker-trigger__arrow">▼</text>
          </view>
        </picker>
        <view class="cf-modal__actions">
          <view class="cf-modal__btn cf-modal__btn--cancel" @tap="showStudentPicker = false">
            <text>取消</text>
          </view>
          <view class="cf-modal__btn cf-modal__btn--confirm" @tap="runFollowup">
            <text>开始生成</text>
          </view>
        </view>
      </view>
    </view>

    <!-- AI 结果弹窗 -->
    <view class="cf-modal-mask" v-if="agentResult" @tap="agentResult = null">
      <view class="cf-modal cf-modal--result" @tap.stop>
        <text class="cf-modal__title">AI 跟进建议</text>
        <view class="cf-result-confidence">
          <text class="cf-result-confidence__label">置信度</text>
          <text class="cf-result-confidence__val">{{ Math.round((agentResult.confidence || 0) * 100) }}%</text>
        </view>
        <view class="cf-result-list">
          <view v-for="(sug, idx) in (agentResult.suggestions || [])" :key="idx" class="cf-result-item">
            <view class="cf-result-item__idx"><text>{{ idx + 1 }}</text></view>
            <text class="cf-result-item__text">{{ sug.text || sug.content || sug }}</text>
          </view>
          <view v-if="!(agentResult.suggestions || []).length" class="cf-empty-inline">
            <text>暂无建议</text>
          </view>
        </view>
        <view class="cf-modal__actions">
          <view class="cf-modal__btn cf-modal__btn--confirm cf-modal__btn--full" @tap="agentResult = null">
            <text>关闭</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 退回原因弹窗 -->
    <view class="cf-modal-mask" v-if="rejectTarget" @tap="rejectTarget = null">
      <view class="cf-modal" @tap.stop>
        <text class="cf-modal__title">退回原因</text>
        <textarea
          class="cf-modal__input"
          v-model="rejectReason"
          placeholder="请输入退回原因..."
          :maxlength="200"
        />
        <view class="cf-modal__actions">
          <view class="cf-modal__btn cf-modal__btn--cancel" @tap="rejectTarget = null">
            <text>取消</text>
          </view>
          <view class="cf-modal__btn cf-modal__btn--ok" @tap="confirmReject">
            <text>确认退回</text>
          </view>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import coachApi from '@/api/coach'

const TYPE_LABEL: Record<string, string> = {
  rx_push: '处方推送', prescription: '行为处方', assessment: '评估',
  ai_reply: 'AI回复', push: '内容推送',
}

const loading       = ref(false)
const queue         = ref<any[]>([])
const stats         = ref<any>({ pending: 0, total_reviewed: 0, approved: 0, rejected: 0 })
const rejectTarget  = ref<any>(null)
const rejectReason  = ref('')

// AI 跟进计划
const showStudentPicker = ref(false)
const studentList       = ref<any[]>([])
const pickedStudent     = ref<any>(null)
const generating        = ref(false)
const agentResult       = ref<any>(null)

const studentNames = computed(() =>
  studentList.value.map(s => s.name || s.full_name || s.username)
)

onMounted(() => {
  loadQueue()
  loadStats()
  loadStudentList()
})

async function loadQueue() {
  loading.value = true
  try {
    const res = await coachApi.getFlywheelQueue()
    queue.value = (res.items || []).map((item: any) => ({
      ...item,
      _handled: false,
      _action: '',
      _expanded: false,
    }))
  } catch {
    queue.value = []
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    const res = await coachApi.getFlywheelStats()
    stats.value = {
      pending: res.pending ?? 0,
      total_reviewed: res.total_reviewed ?? 0,
      approved: res.approved ?? 0,
      rejected: res.rejected ?? 0,
    }
  } catch { /* keep defaults */ }
}

function toggleDraft(item: any) {
  item._expanded = !item._expanded
}

async function handleApprove(item: any) {
  try {
    await coachApi.approveReview(item.id)
    item._handled = true
    item._action = 'approved'
    uni.showToast({ title: '审核通过', icon: 'success' })
    loadStats()
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
  }
}

function showRejectModal(item: any) {
  rejectTarget.value = item
  rejectReason.value = ''
}

async function confirmReject() {
  if (!rejectReason.value.trim()) {
    uni.showToast({ title: '请输入退回原因', icon: 'none' })
    return
  }
  const item = rejectTarget.value
  try {
    await coachApi.rejectReview(item.id, rejectReason.value.trim())
    item._handled = true
    item._action = 'rejected'
    rejectTarget.value = null
    uni.showToast({ title: '已退回', icon: 'none' })
    loadStats()
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
  }
}

function formatWait(seconds: number): string {
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`
  return `${Math.floor(seconds / 3600)}小时`
}

async function loadStudentList() {
  try {
    const res = await coachApi.getDashboard()
    studentList.value = (res.students || []).map((s: any) => ({
      ...s,
      name: s.name || s.full_name || s.username,
    }))
  } catch { studentList.value = [] }
}

function onPickStudent(e: any) {
  const idx = Number(e.detail.value)
  pickedStudent.value = studentList.value[idx] || null
}

async function runFollowup() {
  if (!pickedStudent.value) {
    uni.showToast({ title: '请选择学员', icon: 'none' })
    return
  }
  showStudentPicker.value = false
  generating.value = true
  try {
    console.log('=== runFollowup 调用 ===')
    console.log('pickedStudent:', JSON.stringify(pickedStudent.value))
    console.log('id:', pickedStudent.value?.id, typeof pickedStudent.value?.id)
    const res = await coachApi.runAgent(pickedStudent.value.id, '生成个性化跟进计划')
    agentResult.value = res.data || res
  } catch (e: any) {
    uni.showToast({ title: e?.message || '生成失败', icon: 'none' })
  } finally {
    generating.value = false
  }
}

function goBack() {
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}
</script>

<style scoped>
.cf-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }

.cf-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.cf-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.cf-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.cf-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.cf-navbar__placeholder { width: 64rpx; }

/* 今日统计 */
.cf-stats {
  display: flex; background: var(--surface); padding: 24rpx 32rpx;
  border-bottom: 1px solid var(--border-light); gap: 8rpx;
}
.cf-stat { flex: 1; text-align: center; }
.cf-stat__val { display: block; font-size: 40rpx; font-weight: 800; }
.cf-stat__val--orange { color: #f59e0b; }
.cf-stat__val--blue { color: #3b82f6; }
.cf-stat__val--green { color: #10b981; }
.cf-stat__val--red { color: #ef4444; }
.cf-stat__label { display: block; font-size: 22rpx; color: var(--text-secondary); margin-top: 4rpx; }

.cf-body { flex: 1; padding: 20rpx 32rpx 140rpx; }

/* 审核卡片 */
.cf-card {
  position: relative; background: var(--surface); border-radius: var(--radius-lg);
  padding: 24rpx; margin-bottom: 20rpx; border: 1px solid var(--border-light);
  overflow: hidden; transition: opacity 0.3s;
}
.cf-card--done { opacity: 0.55; }

.cf-card__done-overlay {
  position: absolute; top: 16rpx; right: 16rpx; z-index: 2;
}
.cf-card__done-text {
  font-size: 24rpx; font-weight: 700; padding: 4rpx 16rpx;
  border-radius: var(--radius-full);
}
.cf-card__done-text--green { background: #f0fdf4; color: #16a34a; }
.cf-card__done-text--red { background: #fef2f2; color: #dc2626; }

.cf-card__header { display: flex; align-items: center; gap: 12rpx; margin-bottom: 12rpx; flex-wrap: wrap; }
.cf-card__name { font-size: 28rpx; font-weight: 700; color: var(--text-primary); }
.cf-card__type {
  font-size: 20rpx; font-weight: 600; padding: 4rpx 14rpx;
  border-radius: var(--radius-full);
}
.cf-card__type--rx_push,
.cf-card__type--prescription { background: #eff6ff; color: #2563eb; }
.cf-card__type--assessment { background: #faf5ff; color: #7c3aed; }
.cf-card__type--ai_reply { background: #f0fdf4; color: #16a34a; }
.cf-card__type--push { background: #fffbeb; color: #d97706; }
.cf-card__priority {
  font-size: 18rpx; font-weight: 700; padding: 2rpx 12rpx;
  border-radius: var(--radius-full); background: #fef2f2; color: #dc2626;
}

.cf-card__summary {
  display: block; font-size: 24rpx; color: var(--text-tertiary);
  line-height: 1.5; margin-bottom: 12rpx;
}

/* AI 草稿 */
.cf-card__draft {
  background: var(--surface-secondary); border-radius: var(--radius-md);
  padding: 16rpx 20rpx; margin-bottom: 12rpx; cursor: pointer;
}
.cf-card__draft-label {
  display: block; font-size: 22rpx; font-weight: 600; color: var(--text-secondary);
  margin-bottom: 8rpx;
}
.cf-card__draft-text {
  display: block; font-size: 26rpx; color: var(--text-primary);
  line-height: 1.6; white-space: pre-wrap; word-break: break-all;
}
.cf-card__draft-text--collapsed {
  overflow: hidden; text-overflow: ellipsis;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  white-space: normal;
}

/* 处方字段 */
.cf-card__rx { margin-bottom: 12rpx; }
.cf-card__rx-row { display: flex; gap: 12rpx; padding: 6rpx 0; border-bottom: 1px solid var(--border-light); }
.cf-card__rx-row:last-child { border-bottom: none; }
.cf-card__rx-key { font-size: 22rpx; color: var(--text-secondary); width: 160rpx; flex-shrink: 0; }
.cf-card__rx-val { font-size: 22rpx; color: var(--text-primary); flex: 1; }

/* 操作按钮 */
.cf-card__actions { display: flex; gap: 16rpx; margin-top: 16rpx; }
.cf-btn {
  flex: 1; height: 72rpx; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 26rpx; font-weight: 700; cursor: pointer;
}
.cf-btn:active { opacity: 0.8; }
.cf-btn--approve { background: #10b981; color: #fff; }
.cf-btn--reject { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }

.cf-card__wait {
  display: block; font-size: 20rpx; color: var(--text-tertiary);
  margin-top: 8rpx; text-align: right;
}

/* 空状态 */
.cf-empty {
  display: flex; flex-direction: column; align-items: center;
  padding: 160rpx 0; gap: 20rpx;
}
.cf-empty__icon {
  width: 120rpx; height: 120rpx; border-radius: 50%;
  background: #f0fdf4; color: #10b981;
  display: flex; align-items: center; justify-content: center;
  font-size: 56rpx; font-weight: 700;
}
.cf-empty__text { font-size: 28rpx; color: var(--text-secondary); font-weight: 600; }

/* 退回弹窗 */
.cf-modal-mask {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 999;
}
.cf-modal {
  width: 85%; background: var(--surface); border-radius: var(--radius-xl);
  padding: 32rpx;
}
.cf-modal__title { display: block; font-size: 30rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 24rpx; }
.cf-modal__input {
  width: 100%; height: 180rpx; padding: 16rpx 20rpx;
  background: var(--surface-secondary); border-radius: var(--radius-lg);
  border: 1px solid var(--border-light); font-size: 26rpx;
  color: var(--text-primary); box-sizing: border-box;
}
.cf-modal__actions { display: flex; gap: 16rpx; margin-top: 24rpx; }
.cf-modal__btn {
  flex: 1; height: 80rpx; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 28rpx; font-weight: 600; cursor: pointer;
}
.cf-modal__btn--cancel { background: var(--surface-secondary); color: var(--text-secondary); }
.cf-modal__btn--ok { background: #ef4444; color: #fff; }
.cf-modal__btn--confirm { background: #10b981; color: #fff; }
.cf-modal__btn--full { flex: 1; }

/* 底部生成按钮 */
.cf-footer {
  position: fixed; bottom: 0; left: 0; right: 0;
  padding: 20rpx 32rpx; padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  background: var(--surface); border-top: 1px solid var(--border-light);
}
.cf-gen-btn {
  height: 88rpx; border-radius: var(--radius-lg);
  background: linear-gradient(135deg, #059669 0%, #10b981 100%);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; box-shadow: 0 4rpx 16rpx rgba(16,185,129,0.3);
}
.cf-gen-btn--loading { opacity: 0.7; pointer-events: none; }
.cf-gen-btn__text { font-size: 30rpx; font-weight: 700; color: #fff; }
.cf-gen-btn:active { opacity: 0.85; }

/* 学员选择器 */
.cf-picker-trigger {
  display: flex; justify-content: space-between; align-items: center;
  padding: 20rpx 24rpx; background: var(--surface-secondary); border-radius: var(--radius-lg);
  border: 1px solid var(--border-light); font-size: 28rpx; color: var(--text-primary);
  margin-bottom: 24rpx;
}
.cf-picker-trigger__arrow { font-size: 22rpx; color: var(--text-tertiary); }

/* AI 结果弹窗 */
.cf-modal--result { max-height: 80vh; overflow-y: auto; }
.cf-result-confidence {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16rpx 20rpx; background: #f0fdf4; border-radius: var(--radius-md);
  margin-bottom: 20rpx;
}
.cf-result-confidence__label { font-size: 24rpx; color: var(--text-secondary); }
.cf-result-confidence__val { font-size: 32rpx; font-weight: 800; color: #10b981; }
.cf-result-list { display: flex; flex-direction: column; gap: 12rpx; margin-bottom: 20rpx; }
.cf-result-item {
  display: flex; gap: 12rpx; padding: 16rpx 20rpx;
  background: var(--surface-secondary); border-radius: var(--radius-md);
}
.cf-result-item__idx {
  width: 40rpx; height: 40rpx; border-radius: 50%; flex-shrink: 0;
  background: var(--bhp-primary-500); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 22rpx; font-weight: 700;
}
.cf-result-item__text {
  flex: 1; font-size: 26rpx; color: var(--text-primary);
  line-height: 1.5; word-break: break-all; white-space: normal;
}
.cf-empty-inline { text-align: center; padding: 32rpx; font-size: 24rpx; color: var(--text-tertiary); }
</style>
