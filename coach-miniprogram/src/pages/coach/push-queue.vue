<template>
  <view class="pq-page">

    <!-- 顶部操作栏 -->
    <view class="pq-header">
      <text class="pq-header__title">推送审批</text>
      <view class="pq-header__batch" v-if="queue.length > 0" @tap="confirmBatchApprove">
        <text class="pq-header__batch-text">全部通过 ({{ queue.length }})</text>
      </view>
    </view>

    <!-- 列表 -->
    <scroll-view scroll-y class="pq-list" v-if="queue.length" enable-pull-down-refresh @refresherrefresh="onRefresh">
      <view v-for="item in queue" :key="item.id" class="pq-item">
        <view class="pq-item__body">
          <view class="pq-item__row1">
            <text class="pq-item__name">{{ item.student_name }}</text>
            <view class="pq-item__source">
              <text>{{ SOURCE_LABEL[item.content_type] || item.content_type }}</text>
            </view>
          </view>
          <text class="pq-item__title">{{ item.content_title }}</text>
          <text class="pq-item__summary" v-if="item.ai_summary">{{ item.ai_summary }}</text>
          <text class="pq-item__time">{{ formatTime(item.created_at) }}</text>
        </view>
        <view class="pq-item__actions">
          <view class="pq-btn pq-btn--approve" @tap="handleApprove(item.id)">
            <text>通过</text>
          </view>
          <view class="pq-btn pq-btn--reject" @tap="handleReject(item.id)">
            <text>拒绝</text>
          </view>
        </view>
      </view>
    </scroll-view>

    <!-- 空状态 -->
    <view class="pq-empty" v-else-if="!loading">
      <text class="pq-empty__icon">📭</text>
      <text class="pq-empty__text">暂无待审批内容</text>
    </view>

    <!-- 加载中 -->
    <view class="pq-loading" v-if="loading">
      <view class="bhp-skeleton" style="height:120rpx;border-radius:var(--radius-lg);margin:16rpx 32rpx;" v-for="i in 3" :key="i"></view>
    </view>

    <!-- 批量确认弹窗 -->
    <view class="pq-modal-mask" v-if="showBatchModal">
      <view class="pq-modal" @tap.stop>
        <text class="pq-modal__title">批量通过</text>
        <text class="pq-modal__desc">确认通过全部 {{ queue.length }} 条待审批推送？</text>
        <view class="pq-modal__btns">
          <view class="pq-modal__btn pq-modal__btn--secondary" @tap="showBatchModal = false">
            <text>取消</text>
          </view>
          <view class="pq-modal__btn pq-modal__btn--primary" @tap="doBatchApprove">
            <text>全部通过</text>
          </view>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useCoachStore } from '@/stores/coach'
import http from '@/api/request'

const coachStore = useCoachStore()

const SOURCE_LABEL: Record<string, string> = {
  ai_recommended:   'AI推荐',
  assessment_trigger: '评估触发',
  coach_manual:      '手动推送',
  system:            '系统',
}

const queue         = ref<any[]>([])
const loading       = ref(false)
const showBatchModal = ref(false)

onMounted(() => { loadQueue() })

async function loadQueue() {
  loading.value = true
  try {
    const res = await http.get<{ items: any[] }>('/v1/coach-push/pending', { page_size: 100 })
    queue.value = res.items || []
  } catch {
    queue.value = []
  } finally {
    loading.value = false
  }
}

async function onRefresh() {
  await loadQueue()
  uni.stopPullDownRefresh()
}

async function handleApprove(id: number) {
  const ok = await coachStore.approvePush(id)
  if (ok) {
    queue.value = queue.value.filter(i => i.id !== id)
    uni.showToast({ title: '已通过', icon: 'success' })
  }
}

async function handleReject(id: number) {
  const ok = await coachStore.rejectPush(id)
  if (ok) {
    queue.value = queue.value.filter(i => i.id !== id)
    uni.showToast({ title: '已拒绝', icon: 'none' })
  }
}

function confirmBatchApprove() {
  showBatchModal.value = true
}

async function doBatchApprove() {
  showBatchModal.value = false
  const ids = queue.value.map(i => i.id)
  let successCount = 0
  for (const id of ids) {
    const ok = await coachStore.approvePush(id)
    if (ok) successCount++
  }
  queue.value = queue.value.filter(i => !ids.includes(i.id) || false)
  await loadQueue()
  uni.showToast({ title: `已通过 ${successCount} 条`, icon: 'success' })
}

function formatTime(dateStr: string): string {
  if (!dateStr) return ''
  return dateStr.slice(0, 16).replace('T', ' ')
}
</script>

<style scoped>
.pq-page { background: var(--surface-secondary); min-height: 100vh; }

.pq-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 24rpx 32rpx; background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.pq-header__title { font-size: 32rpx; font-weight: 700; color: var(--text-primary); }
.pq-header__batch {
  background: var(--bhp-primary-500); border-radius: var(--radius-full);
  padding: 10rpx 24rpx; cursor: pointer;
}
.pq-header__batch:active { opacity: 0.85; }
.pq-header__batch-text { font-size: 24rpx; font-weight: 600; color: #fff; }

.pq-list { padding: 16rpx 32rpx; }
.pq-item {
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 24rpx; margin-bottom: 16rpx; border: 1px solid var(--border-light);
}
.pq-item__body { margin-bottom: 16rpx; }
.pq-item__row1 { display: flex; align-items: center; gap: 12rpx; margin-bottom: 8rpx; }
.pq-item__name { font-size: 28rpx; font-weight: 700; color: var(--text-primary); }
.pq-item__source {
  font-size: 20rpx; font-weight: 600; color: #8b5cf6;
  background: rgba(139,92,246,0.1); padding: 2rpx 12rpx; border-radius: var(--radius-full);
}
.pq-item__title { font-size: 26rpx; color: var(--text-primary); display: block; margin-bottom: 4rpx; }
.pq-item__summary { font-size: 24rpx; color: var(--text-tertiary); display: block; margin-bottom: 4rpx; line-height: 1.4; }
.pq-item__time { font-size: 22rpx; color: var(--text-tertiary); display: block; }

.pq-item__actions { display: flex; gap: 16rpx; }
.pq-btn {
  flex: 1; height: 68rpx; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 26rpx; font-weight: 600; cursor: pointer;
}
.pq-btn:active { opacity: 0.8; }
.pq-btn--approve { background: var(--bhp-primary-500); color: #fff; }
.pq-btn--reject { background: var(--bhp-gray-100); color: var(--text-secondary); }

.pq-empty {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; padding-top: 200rpx; gap: 16rpx;
}
.pq-empty__icon { font-size: 80rpx; }
.pq-empty__text { font-size: 28rpx; color: var(--text-secondary); }

.pq-loading { padding-top: 16rpx; }

/* 弹窗 */
.pq-modal-mask {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center;
  z-index: 999;
}
.pq-modal {
  width: 560rpx; background: var(--surface); border-radius: var(--radius-xl);
  padding: 48rpx 40rpx 36rpx; display: flex; flex-direction: column; gap: 20rpx;
}
.pq-modal__title { font-size: 32rpx; font-weight: 700; color: var(--text-primary); text-align: center; }
.pq-modal__desc { font-size: 26rpx; color: var(--text-secondary); text-align: center; }
.pq-modal__btns { display: flex; gap: 20rpx; margin-top: 12rpx; }
.pq-modal__btn {
  flex: 1; height: 80rpx; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 28rpx; font-weight: 600; cursor: pointer;
}
.pq-modal__btn:active { opacity: 0.8; }
.pq-modal__btn--primary { background: var(--bhp-primary-500); color: #fff; }
.pq-modal__btn--secondary { background: var(--bhp-gray-100); color: var(--text-secondary); }
</style>
