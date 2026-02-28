<template>
  <view class="cam-page">

    <!-- 导航栏 -->
    <view class="cam-navbar">
      <view class="cam-navbar__back" @tap="goBack"><text class="cam-navbar__arrow">&#8249;</text></view>
      <text class="cam-navbar__title">评估管理</text>
      <view class="cam-navbar__placeholder"></view>
    </view>

    <!-- 搜索栏 -->
    <view class="cam-search">
      <input class="cam-search__input" v-model="searchKey" placeholder="搜索学员姓名..." :adjust-position="true" />
    </view>

    <!-- Tab -->
    <view class="cam-tabs">
      <view
        v-for="tab in TABS"
        :key="tab.key"
        class="cam-tab"
        :class="{ 'cam-tab--active': activeTab === tab.key }"
        @tap="switchTab(tab.key)"
      >
        <text>{{ tab.label }}</text>
        <view class="cam-tab__badge" v-if="tabCounts[tab.key] > 0">
          <text>{{ tabCounts[tab.key] }}</text>
        </view>
      </view>
    </view>

    <!-- 列表 -->
    <scroll-view
      scroll-y class="cam-body"
      refresher-enabled :refresher-triggered="refreshing"
      @refresherrefresh="onRefresh"
    >
      <template v-if="loading">
        <view class="bhp-skeleton" v-for="i in 3" :key="i" style="height: 160rpx; border-radius: var(--radius-lg); margin-bottom: 16rpx;"></view>
      </template>

      <view v-else-if="filteredList.length" class="cam-list">
        <view v-for="item in filteredList" :key="item.id" class="cam-card" @tap="goDetail(item)">
          <view class="cam-card__header">
            <text class="cam-card__name">{{ item.student_name || '学员#' + item.student_id }}</text>
            <view class="cam-card__status" :class="`cam-card__status--${item.status}`">
              <text>{{ STATUS_LABEL[item.status] || item.status }}</text>
            </view>
          </view>
          <view class="cam-card__info">
            <text class="cam-card__scales">{{ item.scales?.join(' + ') || '综合评估' }}</text>
          </view>
          <!-- 评估结果预览（已完成/待审核） -->
          <view class="cam-card__preview" v-if="item.score_summary || item.ttm_stage">
            <view class="cam-card__score" v-if="item.score_summary">
              <text class="cam-card__score-label">综合得分</text>
              <text class="cam-card__score-val">{{ item.score_summary }}</text>
            </view>
            <view class="cam-card__stage" v-if="item.ttm_stage">
              <text>{{ TTM_LABEL[item.ttm_stage] || item.ttm_stage }}</text>
            </view>
          </view>
          <view class="cam-card__footer">
            <text class="cam-card__date">{{ formatDate(item.created_at) }}</text>
            <text class="cam-card__action-hint" v-if="item.status === 'pending_review'">点击审核 →</text>
          </view>
        </view>
      </view>

      <view v-else class="cam-empty">
        <text class="cam-empty__icon">📋</text>
        <text class="cam-empty__text">{{ searchKey ? '未找到匹配的评估' : '暂无评估' }}</text>
      </view>
    </scroll-view>

    <!-- 分配新评估按钮 -->
    <view class="cam-fab" @tap="openAssignModal">
      <text class="cam-fab__text">+ 分配评估</text>
    </view>

    <!-- 分配弹窗 -->
    <view class="cam-modal-mask" v-if="showAssignModal" @tap="showAssignModal = false">
      <view class="cam-modal" @tap.stop>
        <text class="cam-modal__title">分配新评估</text>

        <view class="cam-modal__field">
          <text class="cam-modal__label">选择学员</text>
          <picker :range="studentNames" @change="onStudentPick">
            <view class="cam-modal__picker">
              <text>{{ selectedStudent ? selectedStudent.full_name || selectedStudent.username : '请选择学员' }}</text>
              <text class="cam-modal__picker-arrow">▼</text>
            </view>
          </picker>
        </view>

        <view class="cam-modal__field">
          <text class="cam-modal__label">量表组合（可多选）</text>
          <view class="cam-modal__scale-list">
            <view
              v-for="s in SCALE_OPTIONS"
              :key="s.key"
              class="cam-modal__scale"
              :class="{ 'cam-modal__scale--active': selectedScales.includes(s.key) }"
              @tap="toggleScale(s.key)"
            >
              <text class="cam-modal__scale-icon">{{ s.icon }}</text>
              <text>{{ s.label }}</text>
            </view>
          </view>
        </view>

        <!-- 快捷全选 -->
        <view class="cam-modal__quick">
          <view class="cam-modal__quick-btn" @tap="selectAllScales">
            <text>全选</text>
          </view>
          <view class="cam-modal__quick-btn" @tap="selectedScales = []">
            <text>清空</text>
          </view>
        </view>

        <view class="cam-modal__actions">
          <view class="cam-modal__btn cam-modal__btn--cancel" @tap="showAssignModal = false">
            <text>取消</text>
          </view>
          <view class="cam-modal__btn cam-modal__btn--ok" @tap="submitAssign">
            <text>{{ submitting ? '分配中...' : '确认分配' }}</text>
          </view>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

// ============================================================
// 内联 HTTP — 完全自包含
// ============================================================
const BASE_URL = 'http://localhost:8000/api'

function _request<T = any>(method: 'GET' | 'POST' | 'PUT', path: string, data?: any): Promise<T> {
  return new Promise((resolve, reject) => {
    const token = uni.getStorageSync('access_token') || ''
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (token) headers['Authorization'] = `Bearer ${token}`
    const url = `${BASE_URL}/${path.replace(/^\//, '')}`
    uni.request({
      url, method, data, header: headers,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data as T)
        else if (res.statusCode === 401) {
          uni.removeStorageSync('access_token'); uni.removeStorageSync('refresh_token'); uni.removeStorageSync('user_info')
          uni.reLaunch({ url: '/pages/auth/login' }); reject(new Error('Session expired'))
        } else {
          const e = res.data as any
          uni.showToast({ title: String(e?.detail || e?.message || `请求失败 (${res.statusCode})`).slice(0, 30), icon: 'none' })
          reject({ statusCode: res.statusCode, data: e })
        }
      },
      fail(err) { uni.showToast({ title: '网络异常', icon: 'none' }); reject(err) },
    })
  })
}

function _get<T = any>(path: string, params?: Record<string, any>): Promise<T> {
  if (params && Object.keys(params).length) {
    const qs = Object.entries(params).filter(([, v]) => v != null).map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`).join('&')
    path = `${path}?${qs}`
  }
  return _request<T>('GET', path)
}

function _post<T = any>(path: string, data?: any): Promise<T> { return _request<T>('POST', path, data) }

// ============================================================
// 常量
// ============================================================
const TABS = [
  { key: 'all',            label: '全部' },
  { key: 'assigned',       label: '待完成' },
  { key: 'in_progress',    label: '进行中' },
  { key: 'pending_review', label: '待审核' },
  { key: 'completed',      label: '已完成' },
]

const STATUS_LABEL: Record<string, string> = {
  assigned: '待完成', in_progress: '进行中', pending_review: '待审核',
  completed: '已完成', reviewed: '已完成',
}

const TTM_LABEL: Record<string, string> = {
  precontemplation: '前意向期', contemplation: '意向期',
  preparation: '准备期', action: '行动期',
  maintenance: '维持期', termination: '终止期',
}

const SCALE_OPTIONS = [
  { key: 'ttm7',     label: 'TTM行为阶段',  icon: '🔄' },
  { key: 'big5',     label: '大五人格',       icon: '🧠' },
  { key: 'bpt6',     label: '行为类型BPT6',   icon: '🏷' },
  { key: 'capacity', label: '能力评估',       icon: '💪' },
  { key: 'spi',      label: '健康行为指数',   icon: '📊' },
]

// ============================================================
// 状态
// ============================================================
const activeTab       = ref('all')
const list            = ref<any[]>([])
const loading         = ref(false)
const refreshing      = ref(false)
const searchKey       = ref('')
const showAssignModal = ref(false)
const submitting      = ref(false)
const students        = ref<any[]>([])
const selectedStudent = ref<any>(null)
const selectedScales  = ref<string[]>([])

const tabCounts = computed(() => {
  const counts: Record<string, number> = { all: list.value.length }
  for (const item of list.value) {
    counts[item.status] = (counts[item.status] || 0) + 1
  }
  return counts
})

const filteredList = computed(() => {
  let items = list.value
  if (activeTab.value !== 'all') {
    items = items.filter(i => i.status === activeTab.value)
  }
  if (searchKey.value.trim()) {
    const q = searchKey.value.trim().toLowerCase()
    items = items.filter(i => (i.student_name || '').toLowerCase().includes(q))
  }
  return items
})

const studentNames = computed(() => students.value.map(s => s.full_name || s.username || s.name))

// ============================================================
// 生命周期
// ============================================================
onMounted(() => { loadList(); loadStudents() })

async function loadList() {
  loading.value = true
  try {
    const [reviewRes, pushedRes, pendingRes] = await Promise.allSettled([
      _get<any>('/v1/assessment-assignments/review-list'),
      _get<any>('/v1/assessment-assignments/pushed-list'),
      _get<any>('/v1/assessment-assignments/my-pending'),
    ])
    const all: any[] = []
    const extract = (r: PromiseSettledResult<any>) => {
      if (r.status === 'fulfilled') {
        const d = r.value as any
        return d.assignments || d.items || (Array.isArray(d) ? d : [])
      }
      return []
    }
    const seen = new Set<string>()
    for (const items of [extract(reviewRes), extract(pushedRes), extract(pendingRes)]) {
      for (const item of items) {
        const key = String(item.id || item.assignment_id || Math.random())
        if (!seen.has(key)) { seen.add(key); all.push(item) }
      }
    }
    // 按时间倒序
    all.sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime())
    list.value = all
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

async function loadStudents() {
  try {
    const res = await _get<any>('/v1/coach/students')
    students.value = res.students || res.items || []
  } catch {}
}

// ============================================================
// 交互
// ============================================================
function switchTab(key: string) { activeTab.value = key }

async function onRefresh() {
  refreshing.value = true
  await loadList()
  refreshing.value = false
}

function openAssignModal() {
  selectedStudent.value = null
  selectedScales.value = []
  showAssignModal.value = true
}

function onStudentPick(e: any) {
  const idx = Number(e.detail.value)
  selectedStudent.value = students.value[idx] || null
}

function toggleScale(s: string) {
  const idx = selectedScales.value.indexOf(s)
  if (idx >= 0) selectedScales.value.splice(idx, 1)
  else selectedScales.value.push(s)
}

function selectAllScales() {
  selectedScales.value = SCALE_OPTIONS.map(s => s.key)
}

async function submitAssign() {
  if (!selectedStudent.value || !selectedScales.value.length) {
    uni.showToast({ title: '请选择学员和量表', icon: 'none' })
    return
  }
  submitting.value = true
  try {
    await _post('/v1/assessment-assignments/assign', {
      student_id: Number(selectedStudent.value.id),
      scales: selectedScales.value,
    })
    uni.showToast({ title: '分配成功', icon: 'success' })
    showAssignModal.value = false
    loadList()
  } catch (e: any) {
    const msg = e?.data?.detail || e?.message || '分配失败'
    uni.showToast({ title: msg, icon: 'none' })
  } finally {
    submitting.value = false
  }
}

function goDetail(item: any) {
  if (item.status === 'pending_review' || item.status === 'completed' || item.status === 'reviewed') {
    uni.navigateTo({ url: `/pages/coach/assessment/review?id=${item.id}` })
  } else {
    uni.showToast({ title: '学员尚未完成评估', icon: 'none' })
  }
}

function formatDate(dt: string): string {
  if (!dt) return ''
  const d = new Date(dt)
  const today = new Date().toDateString()
  const prefix = d.toDateString() === today ? '今天' : `${d.getMonth() + 1}/${d.getDate()}`
  return `${prefix} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

function goBack() {
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}
</script>

<style scoped>
.cam-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }

/* 导航 */
.cam-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top));
  background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.cam-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; }
.cam-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.cam-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.cam-navbar__placeholder { width: 64rpx; }

/* 搜索 */
.cam-search { padding: 12rpx 32rpx; background: var(--surface); }
.cam-search__input {
  height: 64rpx; padding: 0 24rpx; background: var(--surface-secondary);
  border-radius: var(--radius-full); font-size: 26rpx; color: var(--text-primary);
  border: 1px solid var(--border-light);
}

/* Tab */
.cam-tabs {
  display: flex; background: var(--surface); padding: 12rpx 24rpx 16rpx;
  gap: 12rpx; border-bottom: 1px solid var(--border-light); overflow-x: auto;
}
.cam-tab {
  position: relative; display: flex; align-items: center; gap: 6rpx;
  padding: 10rpx 20rpx; border-radius: var(--radius-full);
  font-size: 22rpx; font-weight: 600; color: var(--text-secondary);
  background: var(--surface-secondary); flex-shrink: 0;
}
.cam-tab--active { background: var(--bhp-primary-500, #10b981); color: #fff; }
.cam-tab__badge {
  min-width: 28rpx; height: 28rpx; border-radius: var(--radius-full);
  background: #ef4444; color: #fff; font-size: 18rpx; font-weight: 700;
  display: flex; align-items: center; justify-content: center; padding: 0 6rpx;
}
.cam-tab--active .cam-tab__badge { background: rgba(255,255,255,0.3); }

/* 列表 */
.cam-body { flex: 1; padding: 20rpx 32rpx 120rpx; }
.cam-list { display: flex; flex-direction: column; gap: 16rpx; }

/* 卡片 */
.cam-card {
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 24rpx; border: 1px solid var(--border-light);
}
.cam-card:active { opacity: 0.85; }
.cam-card__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10rpx; }
.cam-card__name { font-size: 28rpx; font-weight: 700; color: var(--text-primary); }
.cam-card__status { font-size: 20rpx; font-weight: 600; padding: 4rpx 14rpx; border-radius: var(--radius-full); }
.cam-card__status--assigned { background: #fff7ed; color: #ea580c; }
.cam-card__status--in_progress { background: #eff6ff; color: #2563eb; }
.cam-card__status--pending_review { background: #fefce8; color: #ca8a04; }
.cam-card__status--completed,
.cam-card__status--reviewed { background: #f0fdf4; color: #16a34a; }
.cam-card__info { margin-bottom: 8rpx; }
.cam-card__scales { font-size: 24rpx; color: var(--text-secondary); }

/* 评估预览 */
.cam-card__preview { display: flex; align-items: center; gap: 16rpx; margin-bottom: 8rpx; }
.cam-card__score { display: flex; align-items: center; gap: 6rpx; }
.cam-card__score-label { font-size: 22rpx; color: var(--text-tertiary); }
.cam-card__score-val { font-size: 26rpx; font-weight: 800; color: var(--bhp-primary-500, #10b981); }
.cam-card__stage {
  font-size: 20rpx; font-weight: 600; padding: 2rpx 12rpx;
  border-radius: var(--radius-full); background: rgba(16,185,129,0.1); color: #059669;
}

.cam-card__footer { display: flex; justify-content: space-between; align-items: center; }
.cam-card__date { font-size: 22rpx; color: var(--text-tertiary); }
.cam-card__action-hint { font-size: 22rpx; font-weight: 600; color: #ca8a04; }

/* 空 */
.cam-empty { display: flex; flex-direction: column; align-items: center; padding: 120rpx 0; gap: 16rpx; }
.cam-empty__icon { font-size: 64rpx; }
.cam-empty__text { font-size: 26rpx; color: var(--text-tertiary); }

/* FAB */
.cam-fab {
  position: fixed; bottom: 60rpx; right: 32rpx;
  background: var(--bhp-primary-500, #10b981); color: #fff;
  padding: 16rpx 32rpx; border-radius: var(--radius-full);
  box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.15);
}
.cam-fab:active { opacity: 0.85; }
.cam-fab__text { font-size: 26rpx; font-weight: 700; }

/* 弹窗 */
.cam-modal-mask {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 999;
}
.cam-modal {
  width: 88%; background: var(--surface); border-radius: var(--radius-xl);
  padding: 32rpx; max-height: 80vh; overflow-y: auto;
}
.cam-modal__title { display: block; font-size: 30rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 28rpx; }
.cam-modal__field { margin-bottom: 24rpx; }
.cam-modal__label { display: block; font-size: 24rpx; font-weight: 600; color: var(--text-secondary); margin-bottom: 10rpx; }
.cam-modal__picker {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16rpx 20rpx; background: var(--surface-secondary); border-radius: var(--radius-lg);
  font-size: 26rpx; color: var(--text-primary); border: 1px solid var(--border-light);
}
.cam-modal__picker-arrow { font-size: 20rpx; color: var(--text-tertiary); }

.cam-modal__scale-list { display: flex; flex-wrap: wrap; gap: 12rpx; }
.cam-modal__scale {
  display: flex; align-items: center; gap: 6rpx;
  padding: 10rpx 20rpx; border-radius: var(--radius-full);
  border: 1px solid var(--border-light); font-size: 22rpx; color: var(--text-secondary);
}
.cam-modal__scale--active { border-color: var(--bhp-primary-500, #10b981); background: rgba(16,185,129,0.08); color: #059669; font-weight: 600; }
.cam-modal__scale-icon { font-size: 20rpx; }

.cam-modal__quick { display: flex; gap: 12rpx; margin-bottom: 20rpx; }
.cam-modal__quick-btn {
  font-size: 22rpx; font-weight: 600; color: var(--bhp-primary-500, #10b981);
  padding: 6rpx 16rpx; border-radius: var(--radius-full);
  background: rgba(16,185,129,0.08);
}

.cam-modal__actions { display: flex; gap: 16rpx; }
.cam-modal__btn {
  flex: 1; height: 80rpx; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 28rpx; font-weight: 600;
}
.cam-modal__btn--cancel { background: var(--surface-secondary); color: var(--text-secondary); }
.cam-modal__btn--ok { background: var(--bhp-primary-500, #10b981); color: #fff; }
.cam-modal__btn:active { opacity: 0.85; }
</style>
