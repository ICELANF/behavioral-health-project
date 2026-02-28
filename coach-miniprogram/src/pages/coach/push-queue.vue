<template>
  <view class="pq-page">

    <!-- 导航栏 -->
    <view class="pq-navbar">
      <view class="pq-navbar__back" @tap="goBack">
        <text class="pq-navbar__arrow">&#8249;</text>
      </view>
      <text class="pq-navbar__title">推送审批</text>
      <view class="pq-navbar__action" v-if="activeTab === 'pending' && pendingList.length > 0" @tap="showBatchModal = true">
        <text class="pq-navbar__action-text">全部通过</text>
      </view>
      <view class="pq-navbar__placeholder" v-else></view>
    </view>

    <!-- 统计栏 -->
    <view class="pq-stats">
      <view class="pq-stat">
        <text class="pq-stat__val pq-stat__val--orange">{{ pendingList.length }}</text>
        <text class="pq-stat__label">待审批</text>
      </view>
      <view class="pq-stat">
        <text class="pq-stat__val pq-stat__val--green">{{ approvedCount }}</text>
        <text class="pq-stat__label">已通过</text>
      </view>
      <view class="pq-stat">
        <text class="pq-stat__val pq-stat__val--red">{{ rejectedCount }}</text>
        <text class="pq-stat__label">已拒绝</text>
      </view>
    </view>

    <!-- Tab 切换 -->
    <view class="pq-tabs">
      <view class="pq-tab" :class="{ 'pq-tab--active': activeTab === 'pending' }" @tap="activeTab = 'pending'">
        <text>待审批</text>
        <view class="pq-tab__badge" v-if="pendingList.length > 0">
          <text>{{ pendingList.length }}</text>
        </view>
      </view>
      <view class="pq-tab" :class="{ 'pq-tab--active': activeTab === 'history' }" @tap="activeTab = 'history'">
        <text>已处理</text>
      </view>
    </view>

    <!-- ═══ 待审批列表 ═══ -->
    <scroll-view scroll-y class="pq-body" v-if="activeTab === 'pending'">
      <template v-if="loading">
        <view class="bhp-skeleton" v-for="i in 3" :key="i" style="height: 200rpx; border-radius: var(--radius-lg); margin-bottom: 16rpx;"></view>
      </template>

      <template v-else-if="pendingList.length">
        <view v-for="item in pendingList" :key="item.id" class="pq-card">
          <!-- 卡片头 -->
          <view class="pq-card__header">
            <text class="pq-card__name">{{ item.student_name }}</text>
            <view class="pq-card__source" :class="`pq-card__source--${item.content_type}`">
              <text>{{ SOURCE_LABEL[item.content_type] || item.content_type }}</text>
            </view>
            <text class="pq-card__time">{{ formatTime(item.created_at) }}</text>
          </view>

          <!-- 标题 -->
          <text class="pq-card__title">{{ item.content_title }}</text>

          <!-- AI 摘要 -->
          <text class="pq-card__summary" v-if="item.ai_summary">{{ item.ai_summary }}</text>

          <!-- 内容预览（可展开） -->
          <view class="pq-card__content" v-if="item.content_body || item.ai_summary" @tap="toggleExpand(item)">
            <text class="pq-card__content-label">推送内容 {{ item._expanded ? '▼' : '▶' }}</text>
            <text class="pq-card__content-text" v-if="item._expanded">{{ item.content_body || item.ai_summary }}</text>
            <text class="pq-card__content-text pq-card__content-text--collapsed" v-else>{{ item.content_body || item.ai_summary }}</text>
          </view>

          <!-- 操作按钮 -->
          <view class="pq-card__actions">
            <view class="pq-btn pq-btn--edit" @tap="openEditModal(item)">
              <text>✎ 编辑后通过</text>
            </view>
            <view class="pq-btn pq-btn--approve" @tap="handleApprove(item)">
              <text>✓ 通过</text>
            </view>
            <view class="pq-btn pq-btn--reject" @tap="openRejectModal(item)">
              <text>✗ 拒绝</text>
            </view>
          </view>
        </view>
      </template>

      <view v-else class="pq-empty">
        <text class="pq-empty__icon">📭</text>
        <text class="pq-empty__text">暂无待审批内容</text>
        <text class="pq-empty__sub">所有推送已处理完毕</text>
      </view>
    </scroll-view>

    <!-- ═══ 已处理列表 ═══ -->
    <scroll-view scroll-y class="pq-body" v-if="activeTab === 'history'">
      <template v-if="historyLoading">
        <view class="bhp-skeleton" v-for="i in 3" :key="i" style="height: 140rpx; border-radius: var(--radius-lg); margin-bottom: 16rpx;"></view>
      </template>

      <template v-else-if="historyList.length">
        <view v-for="item in historyList" :key="item.id" class="pq-card pq-card--done">
          <view class="pq-card__header">
            <text class="pq-card__name">{{ item.student_name }}</text>
            <view class="pq-card__source" :class="`pq-card__source--${item.content_type}`">
              <text>{{ SOURCE_LABEL[item.content_type] || item.content_type }}</text>
            </view>
            <view class="pq-card__status" :class="item.status === 'approved' ? 'pq-card__status--green' : 'pq-card__status--red'">
              <text>{{ item.status === 'approved' ? '已通过' : '已拒绝' }}</text>
            </view>
          </view>
          <text class="pq-card__title">{{ item.content_title }}</text>
          <text class="pq-card__summary" v-if="item.reject_reason">拒绝原因：{{ item.reject_reason }}</text>
          <text class="pq-card__time-bottom">{{ formatTime(item.reviewed_at || item.updated_at || item.created_at) }}</text>
        </view>
      </template>

      <view v-else class="pq-empty">
        <text class="pq-empty__icon">📋</text>
        <text class="pq-empty__text">暂无已处理记录</text>
      </view>
    </scroll-view>

    <!-- ═══ 拒绝原因弹窗 ═══ -->
    <view class="pq-modal-mask" v-if="rejectTarget" @tap="rejectTarget = null">
      <view class="pq-modal" @tap.stop>
        <text class="pq-modal__title">拒绝推送</text>
        <text class="pq-modal__subtitle">{{ rejectTarget.student_name }} · {{ rejectTarget.content_title }}</text>
        <textarea
          class="pq-modal__textarea"
          v-model="rejectReason"
          placeholder="请输入拒绝原因（AI将据此优化后续推送）"
          :maxlength="300"
        />
        <view class="pq-modal__hint">
          <text class="pq-modal__hint-text">💡 详细的拒绝原因能帮助AI更好地学习，下次生成更精准的推送内容</text>
        </view>
        <view class="pq-modal__btns">
          <view class="pq-modal__btn pq-modal__btn--secondary" @tap="rejectTarget = null">
            <text>取消</text>
          </view>
          <view class="pq-modal__btn pq-modal__btn--danger" @tap="confirmReject">
            <text>确认拒绝</text>
          </view>
        </view>
      </view>
    </view>

    <!-- ═══ 编辑草稿弹窗 ═══ -->
    <view class="pq-modal-mask" v-if="editTarget" @tap="editTarget = null">
      <view class="pq-modal pq-modal--large" @tap.stop>
        <text class="pq-modal__title">编辑推送内容</text>
        <text class="pq-modal__subtitle">{{ editTarget.student_name }} · {{ SOURCE_LABEL[editTarget.content_type] || editTarget.content_type }}</text>

        <text class="pq-edit-label">标题</text>
        <input class="pq-edit-input" v-model="editTitle" placeholder="推送标题" />

        <text class="pq-edit-label">内容</text>
        <textarea
          class="pq-modal__textarea pq-modal__textarea--tall"
          v-model="editContent"
          placeholder="推送正文内容"
          :maxlength="2000"
        />

        <view class="pq-modal__btns">
          <view class="pq-modal__btn pq-modal__btn--secondary" @tap="editTarget = null">
            <text>取消</text>
          </view>
          <view class="pq-modal__btn pq-modal__btn--primary" @tap="confirmEditApprove">
            <text>保存并通过</text>
          </view>
        </view>
      </view>
    </view>

    <!-- ═══ 批量通过确认弹窗 ═══ -->
    <view class="pq-modal-mask" v-if="showBatchModal" @tap="showBatchModal = false">
      <view class="pq-modal" @tap.stop>
        <text class="pq-modal__title">批量通过</text>
        <text class="pq-modal__subtitle">确认通过全部 {{ pendingList.length }} 条待审批推送？</text>
        <view class="pq-modal__hint">
          <text class="pq-modal__hint-text">⚠️ 批量通过后，所有推送将直接发送给学员</text>
        </view>
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
import { ref, computed, onMounted } from 'vue'

// ============================================================
// 内联 HTTP — 完全自包含，零主包依赖
// ============================================================
const BASE_URL = 'http://localhost:8000/api'

function _request<T = any>(method: 'GET' | 'POST', path: string, data?: any): Promise<T> {
  return new Promise((resolve, reject) => {
    const token = uni.getStorageSync('access_token') || ''
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (token) headers['Authorization'] = `Bearer ${token}`
    const url = `${BASE_URL}/${path.replace(/^\//, '')}`

    uni.request({
      url, method, data, header: headers,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as T)
        } else if (res.statusCode === 401) {
          uni.removeStorageSync('access_token')
          uni.removeStorageSync('refresh_token')
          uni.removeStorageSync('user_info')
          uni.reLaunch({ url: '/pages/auth/login' })
          reject(new Error('Session expired'))
        } else {
          const errData = res.data as any
          uni.showToast({ title: String(errData?.detail || errData?.message || `请求失败 (${res.statusCode})`).slice(0, 30), icon: 'none' })
          reject({ statusCode: res.statusCode, data: errData })
        }
      },
      fail(err) {
        uni.showToast({ title: '网络异常，请检查连接', icon: 'none' })
        reject(err)
      },
    })
  })
}

function _get<T = any>(path: string, params?: Record<string, any>): Promise<T> {
  if (params && Object.keys(params).length) {
    const qs = Object.entries(params)
      .filter(([, v]) => v !== undefined && v !== null)
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
      .join('&')
    path = `${path}?${qs}`
  }
  return _request<T>('GET', path)
}

function _post<T = any>(path: string, data?: any): Promise<T> {
  return _request<T>('POST', path, data)
}

// ============================================================
// API
// ============================================================
const api = {
  getPending: (p?: Record<string, any>) => _get<{ items: any[] }>('/v1/coach-push/pending', { page_size: 100, ...p }),
  approve:    (id: number, data?: Record<string, any>) => _post<any>(`/v1/coach-push/${id}/approve`, data || {}),
  reject:     (id: number, reason: string) => _post<any>(`/v1/coach-push/${id}/reject`, { reason }),
}

// ============================================================
// 页面逻辑
// ============================================================
const SOURCE_LABEL: Record<string, string> = {
  ai_recommended:    'AI推荐',
  assessment_trigger: '评估触发',
  coach_manual:       '手动推送',
  system:             '系统',
  rx_push:            '行为处方',
  prescription:       '行为处方',
}

const activeTab      = ref<'pending' | 'history'>('pending')
const loading        = ref(false)
const historyLoading = ref(false)
const pendingList    = ref<any[]>([])
const historyList    = ref<any[]>([])

// 拒绝弹窗
const rejectTarget = ref<any>(null)
const rejectReason = ref('')

// 编辑弹窗
const editTarget  = ref<any>(null)
const editTitle   = ref('')
const editContent = ref('')

// 批量弹窗
const showBatchModal = ref(false)

// 统计
const approvedCount = computed(() => historyList.value.filter(i => i.status === 'approved').length)
const rejectedCount = computed(() => historyList.value.filter(i => i.status === 'rejected').length)

// ── 生命周期 ──
onMounted(() => {
  loadPending()
})

// ── 加载待审批 ──
async function loadPending() {
  loading.value = true
  try {
    const res = await api.getPending()
    pendingList.value = (res.items || []).map((item: any) => ({ ...item, _expanded: false }))
  } catch {
    pendingList.value = []
  } finally {
    loading.value = false
  }
}

// ── 加载已处理 ──
async function loadHistory() {
  // 历史记录由前端本地追踪（后端暂无 history 端点）
  // 已处理项在 approve/reject 时已 unshift 到 historyList
}

// ── 展开/收起 ──
function toggleExpand(item: any) {
  item._expanded = !item._expanded
}

// ── 直接通过 ──
async function handleApprove(item: any) {
  try {
    await api.approve(item.id)
    pendingList.value = pendingList.value.filter(i => i.id !== item.id)
    historyList.value.unshift({ ...item, status: 'approved', reviewed_at: new Date().toISOString() })
    uni.showToast({ title: '已通过', icon: 'success' })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
  }
}

// ── 拒绝弹窗 ──
function openRejectModal(item: any) {
  rejectTarget.value = item
  rejectReason.value = ''
}

async function confirmReject() {
  if (!rejectReason.value.trim()) {
    uni.showToast({ title: '请输入拒绝原因', icon: 'none' })
    return
  }
  const item = rejectTarget.value
  try {
    await api.reject(item.id, rejectReason.value.trim())
    pendingList.value = pendingList.value.filter(i => i.id !== item.id)
    historyList.value.unshift({ ...item, status: 'rejected', reject_reason: rejectReason.value.trim(), reviewed_at: new Date().toISOString() })
    rejectTarget.value = null
    uni.showToast({ title: '已拒绝', icon: 'none' })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
  }
}

// ── 编辑后通过 ──
function openEditModal(item: any) {
  editTarget.value = item
  editTitle.value = item.content_title || ''
  editContent.value = item.content_body || item.ai_summary || ''
}

async function confirmEditApprove() {
  if (!editContent.value.trim()) {
    uni.showToast({ title: '内容不能为空', icon: 'none' })
    return
  }
  const item = editTarget.value
  try {
    await api.approve(item.id, {
      edited_title: editTitle.value.trim(),
      edited_content: editContent.value.trim(),
    })
    pendingList.value = pendingList.value.filter(i => i.id !== item.id)
    historyList.value.unshift({ ...item, status: 'approved', content_title: editTitle.value.trim(), reviewed_at: new Date().toISOString() })
    editTarget.value = null
    uni.showToast({ title: '编辑并通过', icon: 'success' })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
  }
}

// ── 批量通过 ──
async function doBatchApprove() {
  showBatchModal.value = false
  const items = [...pendingList.value]
  let count = 0
  for (const item of items) {
    try {
      await api.approve(item.id)
      count++
      historyList.value.unshift({ ...item, status: 'approved', reviewed_at: new Date().toISOString() })
    } catch { /* skip failed */ }
  }
  pendingList.value = []
  uni.showToast({ title: `已通过 ${count} 条`, icon: 'success' })
}

// ── 工具函数 ──
function formatTime(dateStr: string): string {
  if (!dateStr) return ''
  const d = dateStr.slice(0, 16).replace('T', ' ')
  const today = new Date().toISOString().slice(0, 10)
  if (d.startsWith(today)) return '今天 ' + d.slice(11)
  return d
}

function goBack() {
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}
</script>

<style scoped>
.pq-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }

/* 导航栏 */
.pq-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; padding-top: calc(8rpx + env(safe-area-inset-top));
  background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.pq-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; }
.pq-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.pq-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.pq-navbar__action {
  background: var(--bhp-primary-500, #10b981); border-radius: var(--radius-full);
  padding: 8rpx 20rpx;
}
.pq-navbar__action:active { opacity: 0.85; }
.pq-navbar__action-text { font-size: 22rpx; font-weight: 600; color: #fff; }
.pq-navbar__placeholder { width: 120rpx; }

/* 统计栏 */
.pq-stats {
  display: flex; background: var(--surface); padding: 20rpx 32rpx;
  border-bottom: 1px solid var(--border-light); gap: 8rpx;
}
.pq-stat { flex: 1; text-align: center; }
.pq-stat__val { display: block; font-size: 36rpx; font-weight: 800; }
.pq-stat__val--orange { color: #f59e0b; }
.pq-stat__val--green { color: #10b981; }
.pq-stat__val--red { color: #ef4444; }
.pq-stat__label { display: block; font-size: 22rpx; color: var(--text-secondary); margin-top: 4rpx; }

/* Tab 栏 */
.pq-tabs {
  display: flex; background: var(--surface);
  border-bottom: 1px solid var(--border-light);
}
.pq-tab {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 8rpx;
  padding: 20rpx 0; font-size: 26rpx; font-weight: 500;
  color: var(--text-secondary); border-bottom: 3px solid transparent;
}
.pq-tab--active {
  color: var(--bhp-primary-500, #10b981); font-weight: 700;
  border-bottom-color: var(--bhp-primary-500, #10b981);
}
.pq-tab__badge {
  background: #ef4444; color: #fff; font-size: 20rpx; font-weight: 700;
  min-width: 32rpx; height: 32rpx; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; padding: 0 6rpx;
}

/* 列表区域 */
.pq-body { flex: 1; padding: 20rpx 32rpx; }

/* 卡片 */
.pq-card {
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 24rpx; margin-bottom: 16rpx; border: 1px solid var(--border-light);
}
.pq-card--done { opacity: 0.75; }

.pq-card__header { display: flex; align-items: center; gap: 10rpx; margin-bottom: 10rpx; flex-wrap: wrap; }
.pq-card__name { font-size: 28rpx; font-weight: 700; color: var(--text-primary); }
.pq-card__source {
  font-size: 20rpx; font-weight: 600; padding: 2rpx 12rpx; border-radius: var(--radius-full);
}
.pq-card__source--ai_recommended { color: #8b5cf6; background: rgba(139,92,246,0.1); }
.pq-card__source--assessment_trigger { color: #d97706; background: rgba(217,119,6,0.1); }
.pq-card__source--coach_manual { color: #2563eb; background: rgba(37,99,235,0.1); }
.pq-card__source--system { color: #6b7280; background: rgba(107,114,128,0.1); }
.pq-card__source--rx_push,
.pq-card__source--prescription { color: #059669; background: rgba(5,150,105,0.1); }
.pq-card__time { font-size: 22rpx; color: var(--text-tertiary); margin-left: auto; }
.pq-card__time-bottom { display: block; font-size: 22rpx; color: var(--text-tertiary); margin-top: 8rpx; }

.pq-card__status {
  font-size: 20rpx; font-weight: 700; padding: 2rpx 12rpx; border-radius: var(--radius-full);
}
.pq-card__status--green { background: #f0fdf4; color: #16a34a; }
.pq-card__status--red { background: #fef2f2; color: #dc2626; }

.pq-card__title { display: block; font-size: 26rpx; font-weight: 600; color: var(--text-primary); margin-bottom: 6rpx; }
.pq-card__summary { display: block; font-size: 24rpx; color: var(--text-tertiary); line-height: 1.5; margin-bottom: 8rpx; }

/* 内容预览 */
.pq-card__content {
  background: var(--surface-secondary); border-radius: var(--radius-md);
  padding: 16rpx 20rpx; margin-bottom: 12rpx;
}
.pq-card__content-label {
  display: block; font-size: 22rpx; font-weight: 600; color: var(--text-secondary); margin-bottom: 8rpx;
}
.pq-card__content-text {
  display: block; font-size: 24rpx; color: var(--text-primary); line-height: 1.6;
  white-space: pre-wrap; word-break: break-all;
}
.pq-card__content-text--collapsed {
  overflow: hidden; text-overflow: ellipsis;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  white-space: normal;
}

/* 操作按钮 */
.pq-card__actions { display: flex; gap: 12rpx; margin-top: 16rpx; }
.pq-btn {
  flex: 1; height: 68rpx; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 24rpx; font-weight: 600;
}
.pq-btn:active { opacity: 0.8; }
.pq-btn--approve { background: #10b981; color: #fff; }
.pq-btn--reject { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.pq-btn--edit { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }

/* 空状态 */
.pq-empty { display: flex; flex-direction: column; align-items: center; padding: 120rpx 0; gap: 12rpx; }
.pq-empty__icon { font-size: 80rpx; }
.pq-empty__text { font-size: 28rpx; font-weight: 600; color: var(--text-secondary); }
.pq-empty__sub { font-size: 24rpx; color: var(--text-tertiary); }

/* 弹窗 */
.pq-modal-mask {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 999;
}
.pq-modal {
  width: 85%; background: var(--surface); border-radius: var(--radius-xl); padding: 32rpx;
}
.pq-modal--large { width: 90%; }
.pq-modal__title { display: block; font-size: 30rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 8rpx; }
.pq-modal__subtitle { display: block; font-size: 24rpx; color: var(--text-secondary); margin-bottom: 20rpx; }

.pq-modal__textarea {
  width: 100%; height: 180rpx; padding: 16rpx 20rpx;
  background: var(--surface-secondary); border-radius: var(--radius-lg);
  border: 1px solid var(--border-light); font-size: 26rpx;
  color: var(--text-primary); box-sizing: border-box;
}
.pq-modal__textarea--tall { height: 300rpx; }

.pq-modal__hint {
  padding: 12rpx 16rpx; margin-top: 12rpx;
  background: rgba(245,158,11,0.08); border-radius: var(--radius-md);
}
.pq-modal__hint-text { font-size: 22rpx; color: #92400e; line-height: 1.5; }

.pq-modal__btns { display: flex; gap: 16rpx; margin-top: 20rpx; }
.pq-modal__btn {
  flex: 1; height: 80rpx; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 28rpx; font-weight: 600;
}
.pq-modal__btn:active { opacity: 0.8; }
.pq-modal__btn--primary { background: #10b981; color: #fff; }
.pq-modal__btn--secondary { background: var(--surface-secondary); color: var(--text-secondary); }
.pq-modal__btn--danger { background: #ef4444; color: #fff; }

/* 编辑弹窗 */
.pq-edit-label { display: block; font-size: 24rpx; font-weight: 600; color: var(--text-secondary); margin-bottom: 8rpx; margin-top: 16rpx; }
.pq-edit-input {
  width: 100%; height: 72rpx; padding: 0 20rpx;
  background: var(--surface-secondary); border-radius: var(--radius-lg);
  border: 1px solid var(--border-light); font-size: 26rpx;
  color: var(--text-primary); box-sizing: border-box;
}
</style>
