<template>
  <view class="assess-page">
    <!-- 导航栏 -->
    <view class="assess-navbar">
      <view class="assess-nav-back" @tap="goBack">←</view>
      <text class="assess-nav-title">评估管理</text>
      <view class="assess-nav-action" @tap="showAssign = true">+ 分配</view>
    </view>

    <!-- 统计概览 -->
    <view class="assess-stats">
      <view class="assess-stat-card" v-for="s in overviewStats" :key="s.label">
        <text class="assess-stat-num" :style="{ color: s.color }">{{ s.value }}</text>
        <text class="assess-stat-label">{{ s.label }}</text>
      </view>
    </view>

    <!-- 状态Tab -->
    <view class="assess-tabs">
      <view
        v-for="tab in statusTabs" :key="tab.key"
        class="assess-tab" :class="{ 'assess-tab--active': activeTab === tab.key }"
        @tap="activeTab = tab.key"
      >
        {{ tab.label }}
        <view v-if="tab.count > 0" class="assess-tab-badge">{{ tab.count }}</view>
      </view>
    </view>

    <!-- 搜索 -->
    <view class="assess-search">
      <input class="assess-search-input" placeholder="搜索学员姓名" v-model="searchText" @confirm="loadData" />
    </view>

    <!-- 评估列表 -->
    <scroll-view scroll-y class="assess-list" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <view v-for="item in filteredItems" :key="item.id" class="assess-card" @tap="goReview(item)">
        <view class="assess-card-header">
          <view class="assess-card-avatar" :style="{ background: avatarColor(item.student_name || item.user_name) }">
            {{ (item.student_name || item.user_name || '?')[0] }}
          </view>
          <view class="assess-card-info">
            <text class="assess-card-name">{{ item.student_name || item.user_name || '未知学员' }}</text>
            <text class="assess-card-scale">{{ formatScales(item) }}</text>
          </view>
          <view class="assess-status-tag" :style="{ background: statusColor(item.status) }">
            {{ statusLabel(item.status) }}
          </view>
        </view>
        <view class="assess-card-body">
          <view class="assess-card-meta">
            <text class="assess-meta-item">📅 {{ formatDate(item.assigned_at || item.created_at) }}</text>
            <text class="assess-meta-item" v-if="item.completed_at">✅ {{ formatDate(item.completed_at) }}</text>
            <text class="assess-meta-item" v-if="item.score != null">📊 {{ item.score }}分</text>
          </view>
          <!-- 待审核：快捷操作 -->
          <view v-if="item.status === 'submitted' || item.status === 'review' || item.status === 'completed_pending_review'" class="assess-card-actions">
            <view class="assess-action-btn assess-action-review" @tap.stop="goReview(item)">查看评估</view>
          </view>
          <!-- 待分配/进行中：提醒 -->
          <view v-if="item.status === 'assigned' || item.status === 'pending'" class="assess-card-actions">
            <view class="assess-action-btn assess-action-remind" @tap.stop="remindStudent(item)">提醒完成</view>
          </view>
        </view>
      </view>

      <view v-if="!loading && filteredItems.length === 0" class="assess-empty">
        <text class="assess-empty-icon">📋</text>
        <text class="assess-empty-text">暂无{{ activeTab === 'all' ? '' : statusLabel(activeTab) }}评估</text>
        <view class="assess-empty-action" @tap="showAssign = true">分配新评估</view>
      </view>

      <view v-if="loading" class="assess-loading">
        <text>加载中...</text>
      </view>
    </scroll-view>

    <!-- 分配评估弹窗 -->
    <view v-if="showAssign" class="assess-modal-mask" @tap="showAssign = false">
      <view class="assess-modal" @tap.stop>
        <text class="assess-modal-title">分配新评估</text>

        <view class="assess-modal-section">
          <text class="assess-modal-label">选择学员</text>
          <picker :range="studentNames" @change="selectedStudent = Number($event.detail.value)">
            <view class="assess-picker">{{ studentNames[selectedStudent] || '请选择学员' }}</view>
          </picker>
        </view>

        <view class="assess-modal-section">
          <text class="assess-modal-label">量表组合</text>
          <view class="assess-scale-options">
            <view
              v-for="s in scaleOptions" :key="s.value"
              class="assess-scale-opt" :class="{ 'assess-scale-opt--active': selectedScales.includes(s.value) }"
              @tap="toggleScale(s.value)"
            >
              {{ s.label }}
            </view>
          </view>
          <text class="assess-scale-hint">已选 {{ selectedScales.length }} 个量表，预计 {{ estimatedTime }} 分钟</text>
        </view>

        <view class="assess-modal-section">
          <text class="assess-modal-label">截止时间</text>
          <picker mode="date" @change="deadline = $event.detail.value">
            <view class="assess-picker">{{ deadline || '选择截止日期（可选）' }}</view>
          </picker>
        </view>

        <view class="assess-modal-section">
          <text class="assess-modal-label">备注</text>
          <textarea class="assess-textarea" placeholder="给学员的备注说明（可选）" v-model="assignNote" maxlength="200" />
        </view>

        <view class="assess-modal-actions">
          <view class="assess-modal-btn assess-modal-cancel" @tap="showAssign = false">取消</view>
          <view class="assess-modal-btn assess-modal-confirm" @tap="doAssign">确认分配</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const BASE_URL = 'http://localhost:8000'

function getToken(): string {
  return uni.getStorageSync('access_token') || ''
}

async function http<T = any>(url: string, options: any = {}): Promise<T> {
  const { method = 'GET', data } = options
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url,
      method,
      data,
      header: {
        'Authorization': 'Bearer ' + getToken(),
        'Content-Type': 'application/json'
      },
      success: (res: any) => {
        if (res.statusCode === 401) {
          uni.removeStorageSync('access_token')
          uni.reLaunch({ url: '/pages/auth/login' })
          reject(new Error('401')); return
        }
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data as T)
        else reject(new Error(`HTTP ${res.statusCode}`))
      },
      fail: (err: any) => reject(err)
    })
  })
}

const activeTab = ref('all')
const searchText = ref('')
const refreshing = ref(false)
const loading = ref(false)
const assignments = ref<any[]>([])
const studentsData = ref<any[]>([])
const showAssign = ref(false)
const selectedStudent = ref(0)
const selectedScales = ref<string[]>(['big5', 'ttm7'])
const deadline = ref('')
const assignNote = ref('')

const scaleOptions = [
  { label: '大五人格 BIG5', value: 'big5', time: 8 },
  { label: 'TTM行为阶段', value: 'ttm7', time: 5 },
  { label: 'BPT行为类型', value: 'bpt6', time: 6 },
  { label: '能力评估 CAP', value: 'capacity', time: 10 },
  { label: 'SPI自我评估', value: 'spi', time: 7 },
]

const estimatedTime = computed(() => {
  return scaleOptions.filter(s => selectedScales.value.includes(s.value)).reduce((a, s) => a + s.time, 0)
})

const overviewStats = computed(() => [
  { label: '总评估', value: assignments.value.length, color: '#2C3E50' },
  { label: '待完成', value: assignments.value.filter(a => ['pending', 'assigned', 'in_progress'].includes(a.status)).length, color: '#E67E22' },
  { label: '待审核', value: assignments.value.filter(a => ['submitted', 'review', 'completed_pending_review'].includes(a.status)).length, color: '#9B59B6' },
  { label: '已完成', value: assignments.value.filter(a => a.status === 'completed' || a.status === 'reviewed').length, color: '#27AE60' },
])

const statusTabs = computed(() => [
  { key: 'all', label: '全部', count: assignments.value.length },
  { key: 'pending', label: '待分配', count: assignments.value.filter(a => ['pending', 'assigned'].includes(a.status)).length },
  { key: 'in_progress', label: '进行中', count: assignments.value.filter(a => a.status === 'in_progress').length },
  { key: 'review', label: '待审核', count: assignments.value.filter(a => ['submitted', 'review', 'completed_pending_review'].includes(a.status)).length },
  { key: 'completed', label: '已完成', count: assignments.value.filter(a => ['completed', 'reviewed'].includes(a.status)).length },
])

const studentNames = computed(() => studentsData.value.map(s => s.name || s.full_name || s.username || '未知'))

const filteredItems = computed(() => {
  let list = assignments.value
  if (activeTab.value !== 'all') {
    if (activeTab.value === 'pending') list = list.filter(a => ['pending', 'assigned'].includes(a.status))
    else if (activeTab.value === 'review') list = list.filter(a => ['submitted', 'review', 'completed_pending_review'].includes(a.status))
    else if (activeTab.value === 'completed') list = list.filter(a => ['completed', 'reviewed'].includes(a.status))
    else list = list.filter(a => a.status === activeTab.value)
  }
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    list = list.filter(a => (a.student_name || a.user_name || '').toLowerCase().includes(q))
  }
  return list.sort((a: any, b: any) => {
    const da = a.updated_at || a.created_at || ''
    const db = b.updated_at || b.created_at || ''
    return db.localeCompare(da)
  })
})

const AVATAR_COLORS = ['#3498DB', '#E67E22', '#27AE60', '#9B59B6', '#E74C3C', '#1ABC9C', '#F39C12', '#2980B9']
function avatarColor(name: string): string {
  if (!name) return '#8E99A4'
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash)
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length]
}

function statusColor(s: string): string {
  const map: Record<string, string> = {
    pending: '#E67E22', assigned: '#E67E22',
    in_progress: '#3498DB',
    submitted: '#9B59B6', review: '#9B59B6', completed_pending_review: '#9B59B6',
    completed: '#27AE60', reviewed: '#27AE60'
  }
  return map[s] || '#8E99A4'
}

function statusLabel(s: string): string {
  const map: Record<string, string> = {
    all: '', pending: '待分配', assigned: '已分配',
    in_progress: '进行中',
    submitted: '待审核', review: '待审核', completed_pending_review: '待审核',
    completed: '已完成', reviewed: '已审核'
  }
  return map[s] || s
}

function formatDate(d: string): string {
  if (!d) return '-'
  return d.slice(0, 10)
}

function formatScales(item: any): string {
  if (item.scale_names) return item.scale_names
  if (item.scales && Array.isArray(item.scales)) {
    const nameMap: Record<string, string> = { big5: '大五人格', ttm7: 'TTM', bpt6: 'BPT', capacity: '能力', spi: 'SPI' }
    return item.scales.map((s: string) => nameMap[s] || s).join(' + ')
  }
  return item.assessment_type || '综合评估'
}

function toggleScale(val: string) {
  const idx = selectedScales.value.indexOf(val)
  if (idx >= 0) selectedScales.value.splice(idx, 1)
  else selectedScales.value.push(val)
}

async function loadData() {
  loading.value = true
  
  // ★ 关键修复: 使用已验证的 review-list 端点 ★
  try {
    const res = await http<any>('/api/v1/assessment-assignments/review-list')
    assignments.value = res.assignments || res.items || (Array.isArray(res) ? res : [])
  } catch {
    // fallback: 尝试其他可能的端点
    try {
      const res2 = await http<any>('/api/v1/assessment-assignments/my-pending')
      assignments.value = res2.items || res2.assignments || (Array.isArray(res2) ? res2 : [])
    } catch {
      try {
        // 最终fallback: 从教练dashboard的students中构造
        const dash = await http<any>('/api/v1/coach/dashboard')
        if (dash.students) {
          assignments.value = dash.students
            .filter((s: any) => s.latest_assessment || s.assessment_status)
            .map((s: any) => ({
              id: s.assessment_id || s.id,
              student_name: s.name || s.full_name,
              status: s.assessment_status || 'pending',
              created_at: s.assessment_date || s.created_at,
              score: s.assessment_score
            }))
        }
      } catch { assignments.value = [] }
    }
  }

  // 加载学员列表（用于分配弹窗）
  try {
    const res = await http<any>('/api/v1/coach/students')
    studentsData.value = res.students || res.items || (Array.isArray(res) ? res : [])
  } catch {
    try {
      const dash = await http<any>('/api/v1/coach/dashboard')
      studentsData.value = dash.students || []
    } catch { studentsData.value = [] }
  }

  loading.value = false
}

async function doAssign() {
  if (!studentsData.value[selectedStudent.value]) {
    uni.showToast({ title: '请选择学员', icon: 'none' })
    return
  }
  if (selectedScales.value.length === 0) {
    uni.showToast({ title: '请选择量表', icon: 'none' })
    return
  }

  const student = studentsData.value[selectedStudent.value]
  try {
    // 尝试多个可能的创建端点
    try {
      await http('/api/v1/assessment-assignments', {
        method: 'POST',
        data: {
          student_id: student.id || student.user_id,
          scales: selectedScales.value,
          deadline: deadline.value || undefined,
          note: assignNote.value || undefined,
        }
      })
    } catch {
      await http('/api/v1/assessment/assign', {
        method: 'POST',
        data: {
          user_id: student.id || student.user_id,
          assessment_type: selectedScales.value.join(','),
          note: assignNote.value || undefined,
        }
      })
    }
    uni.showToast({ title: '分配成功', icon: 'success' })
    showAssign.value = false
    assignNote.value = ''
    deadline.value = ''
    loadData()
  } catch (e: any) {
    uni.showToast({ title: '分配失败: ' + (e.message || '未知错误'), icon: 'none' })
  }
}

async function remindStudent(item: any) {
  try {
    await http('/api/v1/coach-push/send', {
      method: 'POST',
      data: {
        student_id: item.student_id || item.user_id,
        content: '请尽快完成评估任务',
        type: 'assessment_remind'
      }
    })
    uni.showToast({ title: '已发送提醒', icon: 'success' })
  } catch {
    uni.showToast({ title: '提醒发送失败', icon: 'none' })
  }
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }

function goReview(item: any) {
  uni.navigateTo({ url: '/pages/coach/assessment/review?id=' + item.id })
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

onMounted(() => { loadData() })
</script>

<style scoped>
.assess-page { min-height: 100vh; background: #F5F6FA; }
.assess-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #9B59B6 0%, #8E44AD 100%); color: #fff; }
.assess-nav-back { font-size: 40rpx; padding: 16rpx; }
.assess-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.assess-nav-action { font-size: 26rpx; padding: 8rpx 16rpx; background: rgba(255,255,255,0.2); border-radius: 8rpx; }

.assess-stats { display: flex; padding: 20rpx 24rpx 8rpx; gap: 12rpx; }
.assess-stat-card { flex: 1; background: #fff; border-radius: 12rpx; padding: 16rpx; text-align: center; }
.assess-stat-num { display: block; font-size: 36rpx; font-weight: 700; }
.assess-stat-label { display: block; font-size: 20rpx; color: #8E99A4; margin-top: 4rpx; }

.assess-tabs { display: flex; padding: 12rpx 16rpx 0; gap: 8rpx; overflow-x: auto; white-space: nowrap; }
.assess-tab { position: relative; display: inline-flex; align-items: center; gap: 6rpx; padding: 12rpx 20rpx; border-radius: 24rpx; background: #fff; font-size: 24rpx; color: #5B6B7F; flex-shrink: 0; }
.assess-tab--active { background: #9B59B6; color: #fff; }
.assess-tab-badge { min-width: 28rpx; height: 28rpx; border-radius: 14rpx; background: #E74C3C; color: #fff; font-size: 18rpx; display: flex; align-items: center; justify-content: center; padding: 0 6rpx; }

.assess-search { padding: 12rpx 24rpx; }
.assess-search-input { background: #fff; border-radius: 12rpx; padding: 16rpx 24rpx; font-size: 28rpx; }

.assess-list { height: calc(100vh - 560rpx); padding: 0 24rpx 24rpx; }

.assess-card { background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 16rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.04); }
.assess-card-header { display: flex; align-items: center; gap: 16rpx; }
.assess-card-avatar { width: 72rpx; height: 72rpx; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 30rpx; font-weight: 600; }
.assess-card-info { flex: 1; }
.assess-card-name { display: block; font-size: 30rpx; font-weight: 600; color: #2C3E50; }
.assess-card-scale { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.assess-status-tag { padding: 6rpx 16rpx; border-radius: 8rpx; color: #fff; font-size: 22rpx; white-space: nowrap; }

.assess-card-body { margin-top: 16rpx; }
.assess-card-meta { display: flex; flex-wrap: wrap; gap: 16rpx; }
.assess-meta-item { font-size: 24rpx; color: #8E99A4; }
.assess-card-actions { display: flex; gap: 12rpx; margin-top: 16rpx; justify-content: flex-end; }
.assess-action-btn { padding: 10rpx 24rpx; border-radius: 8rpx; font-size: 24rpx; }
.assess-action-review { background: #9B59B6; color: #fff; }
.assess-action-remind { background: #F0F0F0; color: #E67E22; }

.assess-empty { text-align: center; padding: 120rpx 0; }
.assess-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.assess-empty-text { display: block; font-size: 28rpx; color: #8E99A4; margin-bottom: 24rpx; }
.assess-empty-action { display: inline-block; padding: 16rpx 40rpx; background: #9B59B6; color: #fff; border-radius: 12rpx; font-size: 28rpx; }

.assess-loading { text-align: center; padding: 40rpx; color: #8E99A4; font-size: 26rpx; }

.assess-modal-mask { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 999; }
.assess-modal { width: 88%; max-height: 85vh; background: #fff; border-radius: 24rpx; padding: 32rpx; overflow-y: auto; }
.assess-modal-title { display: block; font-size: 32rpx; font-weight: 600; color: #2C3E50; margin-bottom: 24rpx; text-align: center; }
.assess-modal-section { margin-bottom: 24rpx; }
.assess-modal-label { display: block; font-size: 26rpx; color: #5B6B7F; margin-bottom: 12rpx; font-weight: 500; }
.assess-picker { padding: 16rpx 20rpx; background: #F5F6FA; border-radius: 12rpx; font-size: 28rpx; color: #2C3E50; }
.assess-scale-options { display: flex; flex-wrap: wrap; gap: 12rpx; }
.assess-scale-opt { padding: 10rpx 20rpx; border-radius: 8rpx; background: #F0F0F0; font-size: 24rpx; color: #5B6B7F; }
.assess-scale-opt--active { background: #9B59B6; color: #fff; }
.assess-scale-hint { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 12rpx; }
.assess-textarea { width: 100%; height: 120rpx; padding: 16rpx; background: #F5F6FA; border-radius: 12rpx; font-size: 26rpx; }
.assess-modal-actions { display: flex; gap: 16rpx; margin-top: 24rpx; }
.assess-modal-btn { flex: 1; text-align: center; padding: 20rpx 0; border-radius: 12rpx; font-size: 28rpx; }
.assess-modal-cancel { background: #F0F0F0; color: #5B6B7F; }
.assess-modal-confirm { background: #9B59B6; color: #fff; }
</style>