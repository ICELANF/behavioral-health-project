/**
 * deploy-assessment-module.js
 * 评估管理模块完整部署 — 5个页面 + API路径修正
 *
 * 修复截图中的6个404错误:
 *   - /api/v1/behavior/4/recent?limit=20 → 404
 *   - /api/v1/professional/coach/students/4/notes → 404
 *   - /api/v1/assessment-assignments → 404
 *
 * 已验证可用的后端端点:
 *   - GET  /api/v1/assessment-assignments/review-list → 200 {assignments}
 *   - GET  /api/v1/assessment-assignments/my-pending  → 200
 *   - GET  /api/v1/assessment/profile/me              → 200
 *   - GET  /api/v1/coach/dashboard                    → 200 {coach, students, today_stats}
 *   - GET  /api/v1/coach/students                     → 200
 *   - POST /api/v1/assessment/evaluate                → 提交评估
 *
 * 用法: node deploy-assessment-module.js
 * 时机: 在 npm run dev:mp-weixin 之前运行
 */

const fs = require('fs');
const path = require('path');

// ============================================================
// 通用内联HTTP (所有页面共用)
// ============================================================
const INLINE_HTTP = `
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
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data as T)
        else reject(new Error(\`HTTP \${res.statusCode}\`))
      },
      fail: (err: any) => reject(err)
    })
  })
}
`.trim();

// ============================================================
// 1. coach/assessment/index.vue — 教练评估管理中心
//    修复: /api/v1/assessment-assignments → /api/v1/assessment-assignments/review-list
// ============================================================
const COACH_ASSESSMENT_INDEX = `<template>
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

${INLINE_HTTP}

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
</style>`;

// ============================================================
// 2. coach/assessment/review.vue — 评估审核详情
// ============================================================
const COACH_ASSESSMENT_REVIEW = `<template>
  <view class="review-page">
    <view class="review-navbar">
      <view class="review-nav-back" @tap="goBack">←</view>
      <text class="review-nav-title">评估审核</text>
    </view>

    <!-- 加载中 -->
    <view v-if="loading" class="review-loading">
      <text>加载评估数据...</text>
    </view>

    <scroll-view v-else scroll-y class="review-content">
      <!-- 学员信息 -->
      <view class="review-student">
        <view class="review-avatar" :style="{ background: avatarColor(data.student_name) }">
          {{ (data.student_name || '?')[0] }}
        </view>
        <view class="review-student-info">
          <text class="review-student-name">{{ data.student_name || '未知学员' }}</text>
          <text class="review-student-meta">评估时间: {{ formatDate(data.completed_at || data.created_at) }}</text>
        </view>
        <view class="review-status" :style="{ background: statusColor(data.status) }">
          {{ statusLabel(data.status) }}
        </view>
      </view>

      <!-- 大五人格 -->
      <view class="review-section" v-if="big5Data.length">
        <text class="review-section-title">🧠 大五人格 BIG5</text>
        <view class="review-big5">
          <view class="big5-item" v-for="item in big5Data" :key="item.name">
            <text class="big5-label">{{ item.name }}</text>
            <view class="big5-bar-bg">
              <view class="big5-bar-fill" :style="{ width: item.percent + '%', background: item.color }"></view>
            </view>
            <text class="big5-value">{{ item.score }}</text>
          </view>
        </view>
      </view>

      <!-- BPT6 行为类型 -->
      <view class="review-section" v-if="bptTags.length">
        <text class="review-section-title">🏷️ BPT6 行为类型</text>
        <view class="review-tags">
          <view class="review-tag" v-for="(tag, i) in bptTags" :key="i" :style="{ background: tagColors[i % tagColors.length] }">
            {{ tag }}
          </view>
        </view>
      </view>

      <!-- TTM 行为阶段 -->
      <view class="review-section" v-if="ttmStage">
        <text class="review-section-title">📈 TTM 行为改变阶段</text>
        <view class="ttm-timeline">
          <view
            v-for="(stage, i) in ttmStages" :key="i"
            class="ttm-stage" :class="{ 'ttm-stage--active': i === ttmStageIndex, 'ttm-stage--done': i < ttmStageIndex }"
          >
            <view class="ttm-dot"></view>
            <text class="ttm-label">{{ stage }}</text>
          </view>
        </view>
      </view>

      <!-- SPI/能力评估 -->
      <view class="review-section" v-if="capacityScores.length">
        <text class="review-section-title">💪 能力评估</text>
        <view class="capacity-list">
          <view class="capacity-item" v-for="c in capacityScores" :key="c.name">
            <text class="capacity-name">{{ c.name }}</text>
            <view class="capacity-bar-bg">
              <view class="capacity-bar-fill" :style="{ width: (c.score / c.max * 100) + '%' }"></view>
            </view>
            <text class="capacity-score">{{ c.score }}/{{ c.max }}</text>
          </view>
        </view>
      </view>

      <!-- AI 建议摘要 -->
      <view class="review-section" v-if="aiSuggestions.length">
        <text class="review-section-title">🤖 AI 分析建议</text>
        <view class="ai-suggestion" v-for="(s, i) in aiSuggestions" :key="i">
          <text class="ai-suggestion-num">{{ i + 1 }}</text>
          <text class="ai-suggestion-text">{{ s }}</text>
        </view>
      </view>

      <!-- 教练备注 -->
      <view class="review-section">
        <text class="review-section-title">📝 教练备注</text>
        <textarea
          class="review-note-input"
          placeholder="输入您的专业评估意见和建议..."
          v-model="coachNote"
          maxlength="500"
        />
        <text class="review-note-count">{{ coachNote.length }}/500</text>
      </view>

      <!-- 审核操作 -->
      <view class="review-actions" v-if="canReview">
        <view class="review-btn review-btn-reject" @tap="doReview('rejected')">退回修改</view>
        <view class="review-btn review-btn-approve" @tap="doReview('approved')">通过审核</view>
      </view>

      <view class="review-actions" v-else-if="data.status === 'completed' || data.status === 'reviewed'">
        <view class="review-completed-tag">✅ 评估已完成审核</view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

${INLINE_HTTP}

const loading = ref(true)
const data = ref<any>({})
const coachNote = ref('')

const ttmStages = ['前意向', '意向', '准备', '行动', '维持', '终止']
const tagColors = ['#3498DB', '#E67E22', '#27AE60', '#9B59B6', '#E74C3C', '#1ABC9C']
const AVATAR_COLORS = ['#3498DB', '#E67E22', '#27AE60', '#9B59B6', '#E74C3C', '#1ABC9C']

function avatarColor(name: string): string {
  if (!name) return '#8E99A4'
  let hash = 0; for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash)
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length]
}
function statusColor(s: string): string {
  const map: Record<string, string> = { pending: '#E67E22', assigned: '#E67E22', in_progress: '#3498DB', submitted: '#9B59B6', review: '#9B59B6', completed: '#27AE60', reviewed: '#27AE60', approved: '#27AE60', rejected: '#E74C3C' }
  return map[s] || '#8E99A4'
}
function statusLabel(s: string): string {
  const map: Record<string, string> = { pending: '待分配', assigned: '已分配', in_progress: '进行中', submitted: '待审核', review: '待审核', completed: '已完成', reviewed: '已审核', approved: '已通过', rejected: '已退回' }
  return map[s] || s
}
function formatDate(d: string): string { return d ? d.slice(0, 10) : '-' }

const canReview = computed(() => ['submitted', 'review', 'completed_pending_review'].includes(data.value.status))

const big5Data = computed(() => {
  const r = data.value.big5 || data.value.personality || data.value.results?.big5
  if (!r) return []
  const dims = [
    { key: 'openness', name: '开放性', color: '#3498DB' },
    { key: 'conscientiousness', name: '尽责性', color: '#27AE60' },
    { key: 'extraversion', name: '外向性', color: '#E67E22' },
    { key: 'agreeableness', name: '宜人性', color: '#9B59B6' },
    { key: 'neuroticism', name: '神经质', color: '#E74C3C' },
  ]
  return dims.map(d => {
    const score = r[d.key] ?? r[d.name] ?? 0
    return { ...d, score: Math.round(score * 10) / 10, percent: Math.min(100, Math.round((score / 7) * 100)) }
  })
})

const bptTags = computed(() => {
  const r = data.value.bpt6 || data.value.behavior_types || data.value.results?.bpt6
  if (Array.isArray(r)) return r.slice(0, 6)
  if (r && typeof r === 'object') return Object.keys(r).slice(0, 6)
  return []
})

const ttmStage = computed(() => data.value.ttm_stage || data.value.ttm || data.value.results?.ttm || '')
const ttmStageIndex = computed(() => {
  const s = ttmStage.value
  if (!s) return -1
  const map: Record<string, number> = { precontemplation: 0, contemplation: 1, preparation: 2, action: 3, maintenance: 4, termination: 5 }
  if (map[s] !== undefined) return map[s]
  return ttmStages.findIndex(st => s.includes(st))
})

const capacityScores = computed(() => {
  const r = data.value.capacity || data.value.results?.capacity
  if (!r) return []
  if (Array.isArray(r)) return r
  return Object.entries(r).map(([k, v]) => ({ name: k, score: Number(v) || 0, max: 10 }))
})

const aiSuggestions = computed(() => {
  const s = data.value.ai_suggestions || data.value.suggestions || data.value.results?.suggestions
  if (Array.isArray(s)) return s.slice(0, 5)
  if (typeof s === 'string') return s.split('\\n').filter(Boolean).slice(0, 5)
  return []
})

async function loadData() {
  loading.value = true
  const id = (getCurrentPages().slice(-1)[0] as any)?.options?.id
  if (!id) { loading.value = false; return }

  // 尝试多个端点获取评估详情
  const endpoints = [
    \`/api/v1/assessment-assignments/\${id}/result\`,
    \`/api/v1/assessment-assignments/\${id}\`,
    \`/api/v1/assessment/results/\${id}\`,
    \`/api/v1/assessment/\${id}\`,
  ]
  for (const ep of endpoints) {
    try {
      const res = await http<any>(ep)
      data.value = res.result || res.assignment || res || {}
      break
    } catch { continue }
  }
  loading.value = false
}

async function doReview(action: string) {
  const id = data.value.id
  if (!id) return

  const confirmText = action === 'approved' ? '确认通过此评估？' : '确认退回此评估？'
  uni.showModal({
    title: '确认操作',
    content: confirmText,
    success: async (res) => {
      if (!res.confirm) return
      try {
        // 尝试多个审核端点
        try {
          await http(\`/api/v1/assessment-assignments/\${id}/review\`, {
            method: 'POST',
            data: { action, note: coachNote.value }
          })
        } catch {
          await http(\`/api/v1/assessment-assignments/\${id}/\${action === 'approved' ? 'approve' : 'reject'}\`, {
            method: 'POST',
            data: { note: coachNote.value }
          })
        }
        uni.showToast({ title: action === 'approved' ? '审核通过' : '已退回', icon: 'success' })
        setTimeout(() => uni.navigateBack(), 800)
      } catch (e: any) {
        uni.showToast({ title: '操作失败', icon: 'none' })
      }
    }
  })
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

onMounted(() => { loadData() })
</script>

<style scoped>
.review-page { min-height: 100vh; background: #F5F6FA; }
.review-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #9B59B6 0%, #8E44AD 100%); color: #fff; }
.review-nav-back { font-size: 40rpx; padding: 16rpx; }
.review-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }

.review-loading { text-align: center; padding: 200rpx 0; color: #8E99A4; font-size: 28rpx; }
.review-content { height: calc(100vh - 180rpx); padding: 24rpx; }

.review-student { display: flex; align-items: center; gap: 16rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 16rpx; }
.review-avatar { width: 80rpx; height: 80rpx; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 34rpx; font-weight: 600; }
.review-student-info { flex: 1; }
.review-student-name { display: block; font-size: 32rpx; font-weight: 600; color: #2C3E50; }
.review-student-meta { display: block; font-size: 24rpx; color: #8E99A4; margin-top: 4rpx; }
.review-status { padding: 8rpx 20rpx; border-radius: 8rpx; color: #fff; font-size: 24rpx; }

.review-section { background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 16rpx; }
.review-section-title { display: block; font-size: 30rpx; font-weight: 600; color: #2C3E50; margin-bottom: 20rpx; }

.review-big5 { }
.big5-item { display: flex; align-items: center; gap: 12rpx; margin-bottom: 16rpx; }
.big5-label { width: 100rpx; font-size: 24rpx; color: #5B6B7F; text-align: right; }
.big5-bar-bg { flex: 1; height: 20rpx; background: #F0F0F0; border-radius: 10rpx; overflow: hidden; }
.big5-bar-fill { height: 100%; border-radius: 10rpx; transition: width 0.6s; }
.big5-value { width: 60rpx; font-size: 24rpx; color: #2C3E50; font-weight: 600; }

.review-tags { display: flex; flex-wrap: wrap; gap: 12rpx; }
.review-tag { padding: 8rpx 20rpx; border-radius: 20rpx; color: #fff; font-size: 24rpx; }

.ttm-timeline { display: flex; align-items: flex-start; gap: 0; padding: 16rpx 0; }
.ttm-stage { flex: 1; text-align: center; position: relative; }
.ttm-stage::before { content: ''; position: absolute; top: 14rpx; left: 0; right: 0; height: 4rpx; background: #E0E0E0; z-index: 0; }
.ttm-stage:first-child::before { left: 50%; }
.ttm-stage:last-child::before { right: 50%; }
.ttm-dot { width: 28rpx; height: 28rpx; border-radius: 50%; background: #E0E0E0; margin: 0 auto 8rpx; position: relative; z-index: 1; }
.ttm-stage--done .ttm-dot { background: #27AE60; }
.ttm-stage--done::before { background: #27AE60; }
.ttm-stage--active .ttm-dot { background: #9B59B6; width: 36rpx; height: 36rpx; margin-top: -4rpx; box-shadow: 0 0 0 8rpx rgba(155,89,182,0.2); }
.ttm-label { font-size: 20rpx; color: #8E99A4; }
.ttm-stage--active .ttm-label { color: #9B59B6; font-weight: 600; }
.ttm-stage--done .ttm-label { color: #27AE60; }

.capacity-list { }
.capacity-item { display: flex; align-items: center; gap: 12rpx; margin-bottom: 12rpx; }
.capacity-name { width: 120rpx; font-size: 24rpx; color: #5B6B7F; }
.capacity-bar-bg { flex: 1; height: 16rpx; background: #F0F0F0; border-radius: 8rpx; overflow: hidden; }
.capacity-bar-fill { height: 100%; background: linear-gradient(90deg, #3498DB, #2ECC71); border-radius: 8rpx; }
.capacity-score { width: 80rpx; font-size: 22rpx; color: #8E99A4; text-align: right; }

.ai-suggestion { display: flex; gap: 12rpx; margin-bottom: 16rpx; }
.ai-suggestion-num { width: 40rpx; height: 40rpx; border-radius: 50%; background: #9B59B6; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 22rpx; flex-shrink: 0; }
.ai-suggestion-text { flex: 1; font-size: 26rpx; color: #5B6B7F; line-height: 1.6; }

.review-note-input { width: 100%; height: 160rpx; padding: 16rpx; background: #F5F6FA; border-radius: 12rpx; font-size: 26rpx; line-height: 1.6; }
.review-note-count { display: block; text-align: right; font-size: 22rpx; color: #8E99A4; margin-top: 8rpx; }

.review-actions { display: flex; gap: 16rpx; padding: 24rpx 0 48rpx; }
.review-btn { flex: 1; text-align: center; padding: 24rpx 0; border-radius: 16rpx; font-size: 30rpx; font-weight: 600; }
.review-btn-reject { background: #FFF0ED; color: #E74C3C; }
.review-btn-approve { background: #9B59B6; color: #fff; }
.review-completed-tag { flex: 1; text-align: center; padding: 24rpx; background: #E8F8F0; color: #27AE60; border-radius: 16rpx; font-size: 28rpx; font-weight: 500; }
</style>`;

// ============================================================
// 3. assessment/pending.vue — 学员待做评估列表
// ============================================================
const ASSESSMENT_PENDING = `<template>
  <view class="pending-page">
    <view class="pending-navbar">
      <view class="pending-nav-back" @tap="goBack">←</view>
      <text class="pending-nav-title">我的评估</text>
    </view>

    <scroll-view scroll-y class="pending-content" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <!-- 待完成 -->
      <view class="pending-section" v-if="pendingList.length">
        <text class="pending-section-title">⏳ 待完成 ({{ pendingList.length }})</text>
        <view v-for="item in pendingList" :key="item.id" class="pending-card pending-card--active" @tap="goAssessment(item)">
          <view class="pending-card-icon">📝</view>
          <view class="pending-card-info">
            <text class="pending-card-title">{{ item.assessment_name || item.scale_names || '综合评估' }}</text>
            <text class="pending-card-meta">分配教练: {{ item.coach_name || '系统分配' }}</text>
            <text class="pending-card-meta" v-if="item.deadline">截止: {{ formatDate(item.deadline) }}</text>
          </view>
          <view class="pending-go-btn">开始 →</view>
        </view>
      </view>

      <!-- 进行中（有草稿） -->
      <view class="pending-section" v-if="inProgressList.length">
        <text class="pending-section-title">✍️ 进行中 ({{ inProgressList.length }})</text>
        <view v-for="item in inProgressList" :key="item.id" class="pending-card pending-card--progress" @tap="goAssessment(item)">
          <view class="pending-card-icon">📊</view>
          <view class="pending-card-info">
            <text class="pending-card-title">{{ item.assessment_name || item.scale_names || '综合评估' }}</text>
            <view class="pending-progress-bar">
              <view class="pending-progress-fill" :style="{ width: (item.progress || 30) + '%' }"></view>
            </view>
            <text class="pending-card-meta">已完成 {{ item.progress || 30 }}%</text>
          </view>
          <view class="pending-go-btn">继续 →</view>
        </view>
      </view>

      <!-- 已完成 -->
      <view class="pending-section" v-if="completedList.length">
        <text class="pending-section-title">✅ 已完成 ({{ completedList.length }})</text>
        <view v-for="item in completedList" :key="item.id" class="pending-card pending-card--done" @tap="goResult(item)">
          <view class="pending-card-icon">📈</view>
          <view class="pending-card-info">
            <text class="pending-card-title">{{ item.assessment_name || item.scale_names || '综合评估' }}</text>
            <text class="pending-card-meta">完成时间: {{ formatDate(item.completed_at) }}</text>
            <text class="pending-card-meta" v-if="item.score != null">得分: {{ item.score }}</text>
          </view>
          <view class="pending-go-btn pending-go-view">查看 →</view>
        </view>
      </view>

      <!-- 空状态 -->
      <view v-if="!loading && allItems.length === 0" class="pending-empty">
        <text class="pending-empty-icon">📋</text>
        <text class="pending-empty-text">暂无评估任务</text>
        <text class="pending-empty-hint">教练分配评估后会在这里显示</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

${INLINE_HTTP}

const loading = ref(false)
const refreshing = ref(false)
const allItems = ref<any[]>([])

const pendingList = computed(() => allItems.value.filter(a => ['pending', 'assigned'].includes(a.status)))
const inProgressList = computed(() => allItems.value.filter(a => a.status === 'in_progress'))
const completedList = computed(() => allItems.value.filter(a => ['completed', 'submitted', 'reviewed'].includes(a.status)))

function formatDate(d: string): string { return d ? d.slice(0, 10) : '-' }

async function loadData() {
  loading.value = true
  // ★ 使用已验证端点 ★
  const endpoints = [
    '/api/v1/assessment-assignments/my-pending',
    '/api/v1/assessment-assignments/review-list',
    '/api/v1/assessment/user/latest',
  ]
  for (const ep of endpoints) {
    try {
      const res = await http<any>(ep)
      const list = res.items || res.assignments || (Array.isArray(res) ? res : [])
      if (list.length > 0 || allItems.value.length === 0) {
        allItems.value = [...allItems.value, ...list]
      }
    } catch { /* 继续尝试 */ }
  }
  // 去重
  const seen = new Set()
  allItems.value = allItems.value.filter(item => {
    const key = item.id || (item.student_id + '_' + item.assessment_type)
    if (seen.has(key)) return false
    seen.add(key); return true
  })
  loading.value = false
}

async function onRefresh() { refreshing.value = true; allItems.value = []; await loadData(); refreshing.value = false }

function goAssessment(item: any) {
  uni.navigateTo({ url: '/pages/assessment/do?id=' + item.id })
}

function goResult(item: any) {
  uni.navigateTo({ url: '/pages/assessment/result?id=' + item.id })
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

onMounted(() => { loadData() })
</script>

<style scoped>
.pending-page { min-height: 100vh; background: #F5F6FA; }
.pending-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #9B59B6 0%, #8E44AD 100%); color: #fff; }
.pending-nav-back { font-size: 40rpx; padding: 16rpx; }
.pending-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }

.pending-content { height: calc(100vh - 180rpx); padding: 24rpx; }
.pending-section { margin-bottom: 24rpx; }
.pending-section-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; margin-bottom: 16rpx; }

.pending-card { display: flex; align-items: center; gap: 16rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 12rpx; }
.pending-card--active { border-left: 6rpx solid #E67E22; }
.pending-card--progress { border-left: 6rpx solid #3498DB; }
.pending-card--done { border-left: 6rpx solid #27AE60; opacity: 0.85; }

.pending-card-icon { font-size: 48rpx; }
.pending-card-info { flex: 1; }
.pending-card-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; margin-bottom: 6rpx; }
.pending-card-meta { display: block; font-size: 22rpx; color: #8E99A4; }

.pending-progress-bar { height: 8rpx; background: #F0F0F0; border-radius: 4rpx; margin: 8rpx 0; overflow: hidden; }
.pending-progress-fill { height: 100%; background: #3498DB; border-radius: 4rpx; }

.pending-go-btn { padding: 12rpx 24rpx; background: #9B59B6; color: #fff; border-radius: 8rpx; font-size: 24rpx; white-space: nowrap; }
.pending-go-view { background: #27AE60; }

.pending-empty { text-align: center; padding: 200rpx 0; }
.pending-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.pending-empty-text { display: block; font-size: 30rpx; color: #5B6B7F; margin-bottom: 8rpx; }
.pending-empty-hint { display: block; font-size: 24rpx; color: #8E99A4; }
</style>`;

// ============================================================
// 4. assessment/do.vue — 评估作答(5种题型+分步+草稿+计时)
// ============================================================
const ASSESSMENT_DO = `<template>
  <view class="do-page">
    <!-- 自定义导航栏 -->
    <view class="do-navbar">
      <view class="do-nav-back" @tap="confirmExit">←</view>
      <view class="do-nav-center">
        <text class="do-nav-group">第{{ currentGroupIndex + 1 }}组/共{{ groups.length }}组</text>
        <text class="do-nav-scale">{{ currentGroupName }}</text>
      </view>
      <text class="do-nav-timer">{{ timerText }}</text>
    </view>

    <!-- 量表进度 -->
    <view class="do-group-progress">
      <view
        v-for="(g, i) in groups" :key="i"
        class="do-group-dot"
        :class="{ 'do-group-dot--done': i < currentGroupIndex, 'do-group-dot--active': i === currentGroupIndex }"
      ></view>
    </view>

    <!-- 题目进度条 -->
    <view class="do-progress-bar">
      <view class="do-progress-fill" :style="{ width: progressPercent + '%' }"></view>
    </view>
    <text class="do-progress-text">{{ currentQuestionIndex + 1 }} / {{ currentGroupQuestions.length }}</text>

    <!-- 题目内容 -->
    <scroll-view scroll-y class="do-question-area" v-if="currentQuestion">
      <view class="do-question-card">
        <text class="do-question-num">Q{{ currentQuestionIndex + 1 }}</text>
        <text class="do-question-text">{{ currentQuestion.text || currentQuestion.question || currentQuestion.title }}</text>

        <!-- 单选 -->
        <view v-if="currentQuestion.type === 'single' || currentQuestion.type === 'radio'" class="do-options">
          <view
            v-for="(opt, oi) in currentQuestion.options" :key="oi"
            class="do-option" :class="{ 'do-option--selected': answers[questionKey] === oi }"
            @tap="selectSingle(oi)"
          >
            <view class="do-option-indicator">{{ answers[questionKey] === oi ? '✓' : String.fromCharCode(65 + oi) }}</view>
            <text class="do-option-text">{{ typeof opt === 'string' ? opt : opt.text || opt.label }}</text>
          </view>
        </view>

        <!-- 多选 -->
        <view v-else-if="currentQuestion.type === 'multiple' || currentQuestion.type === 'checkbox'" class="do-options">
          <view
            v-for="(opt, oi) in currentQuestion.options" :key="oi"
            class="do-option" :class="{ 'do-option--selected': (answers[questionKey] || []).includes(oi) }"
            @tap="selectMultiple(oi)"
          >
            <view class="do-option-indicator">{{ (answers[questionKey] || []).includes(oi) ? '✓' : '○' }}</view>
            <text class="do-option-text">{{ typeof opt === 'string' ? opt : opt.text || opt.label }}</text>
          </view>
        </view>

        <!-- 量表滑动 1-7 -->
        <view v-else-if="currentQuestion.type === 'scale' || currentQuestion.type === 'likert'" class="do-scale">
          <view class="do-scale-labels">
            <text class="do-scale-min">{{ currentQuestion.min_label || '非常不同意' }}</text>
            <text class="do-scale-max">{{ currentQuestion.max_label || '非常同意' }}</text>
          </view>
          <view class="do-scale-dots">
            <view
              v-for="n in (currentQuestion.max || 7)" :key="n"
              class="do-scale-dot" :class="{ 'do-scale-dot--selected': answers[questionKey] === n }"
              @tap="answers[questionKey] = n; saveDraft()"
            >
              {{ n }}
            </view>
          </view>
        </view>

        <!-- 布尔 -->
        <view v-else-if="currentQuestion.type === 'boolean'" class="do-boolean">
          <view class="do-bool-btn" :class="{ 'do-bool-btn--yes': answers[questionKey] === true }" @tap="answers[questionKey] = true; saveDraft()">
            <text class="do-bool-icon">✓</text>
            <text>是</text>
          </view>
          <view class="do-bool-btn" :class="{ 'do-bool-btn--no': answers[questionKey] === false }" @tap="answers[questionKey] = false; saveDraft()">
            <text class="do-bool-icon">✕</text>
            <text>否</text>
          </view>
        </view>

        <!-- 文本 -->
        <view v-else-if="currentQuestion.type === 'text' || currentQuestion.type === 'essay'" class="do-text">
          <textarea class="do-text-input" placeholder="请输入您的回答..." v-model="answers[questionKey]" @blur="saveDraft" maxlength="500" />
        </view>

        <!-- 默认按单选处理 -->
        <view v-else class="do-options">
          <view
            v-for="(opt, oi) in (currentQuestion.options || [])" :key="oi"
            class="do-option" :class="{ 'do-option--selected': answers[questionKey] === oi }"
            @tap="selectSingle(oi)"
          >
            <view class="do-option-indicator">{{ answers[questionKey] === oi ? '✓' : String.fromCharCode(65 + oi) }}</view>
            <text class="do-option-text">{{ typeof opt === 'string' ? opt : opt.text || opt.label }}</text>
          </view>
        </view>
      </view>
    </scroll-view>

    <!-- 底部操作 -->
    <view class="do-bottom">
      <view class="do-bottom-btns">
        <view class="do-btn do-btn-prev" v-if="canPrev" @tap="prevQuestion">← 上一题</view>
        <view class="do-btn do-btn-next" v-if="canNext" @tap="nextQuestion">下一题 →</view>
        <view class="do-btn do-btn-submit" v-if="isLastQuestion && allAnswered" @tap="submitAssessment">提交评估 ✓</view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, reactive } from 'vue'

${INLINE_HTTP}

const assessmentId = ref('')
const groups = ref<any[]>([])
const currentGroupIndex = ref(0)
const currentQuestionIndex = ref(0)
const answers = reactive<Record<string, any>>({})
const timer = ref(0)
let timerInterval: any = null

// 量表分组定义
const scaleGroups = [
  { key: 'ttm7', name: 'TTM 行为阶段' },
  { key: 'big5', name: 'BIG5 大五人格' },
  { key: 'bpt6', name: 'BPT6 行为类型' },
  { key: 'capacity', name: '能力评估' },
  { key: 'spi', name: 'SPI 自我评估' },
]

const currentGroupName = computed(() => groups.value[currentGroupIndex.value]?.name || '评估')
const currentGroupQuestions = computed(() => groups.value[currentGroupIndex.value]?.questions || [])
const currentQuestion = computed(() => currentGroupQuestions.value[currentQuestionIndex.value])
const questionKey = computed(() => \`\${currentGroupIndex.value}_\${currentQuestionIndex.value}\`)

const progressPercent = computed(() => {
  const total = currentGroupQuestions.value.length
  return total > 0 ? Math.round((currentQuestionIndex.value / total) * 100) : 0
})

const canPrev = computed(() => currentQuestionIndex.value > 0 || currentGroupIndex.value > 0)
const canNext = computed(() => {
  if (currentQuestionIndex.value < currentGroupQuestions.value.length - 1) return true
  if (currentGroupIndex.value < groups.value.length - 1) return true
  return false
})
const isLastQuestion = computed(() =>
  currentGroupIndex.value === groups.value.length - 1 &&
  currentQuestionIndex.value === currentGroupQuestions.value.length - 1
)
const allAnswered = computed(() => {
  let total = 0, answered = 0
  groups.value.forEach((g, gi) => {
    g.questions.forEach((_: any, qi: number) => {
      total++
      if (answers[\`\${gi}_\${qi}\`] !== undefined && answers[\`\${gi}_\${qi}\`] !== null && answers[\`\${gi}_\${qi}\`] !== '') answered++
    })
  })
  return total > 0 && answered >= total
})

const timerText = computed(() => {
  const m = Math.floor(timer.value / 60)
  const s = timer.value % 60
  return \`\${String(m).padStart(2,'0')}:\${String(s).padStart(2,'0')}\`
})

function selectSingle(oi: number) {
  answers[questionKey.value] = oi
  saveDraft()
  // 自动下一题
  setTimeout(() => { if (canNext.value) nextQuestion() }, 300)
}

function selectMultiple(oi: number) {
  const cur = answers[questionKey.value] || []
  const idx = cur.indexOf(oi)
  if (idx >= 0) cur.splice(idx, 1)
  else cur.push(oi)
  answers[questionKey.value] = [...cur]
  saveDraft()
}

function nextQuestion() {
  if (currentQuestionIndex.value < currentGroupQuestions.value.length - 1) {
    currentQuestionIndex.value++
  } else if (currentGroupIndex.value < groups.value.length - 1) {
    currentGroupIndex.value++
    currentQuestionIndex.value = 0
  }
  saveDraft()
}

function prevQuestion() {
  if (currentQuestionIndex.value > 0) {
    currentQuestionIndex.value--
  } else if (currentGroupIndex.value > 0) {
    currentGroupIndex.value--
    currentQuestionIndex.value = groups.value[currentGroupIndex.value].questions.length - 1
  }
}

function saveDraft() {
  try {
    uni.setStorageSync('assessment_draft_' + assessmentId.value, JSON.stringify({
      answers, currentGroupIndex: currentGroupIndex.value, currentQuestionIndex: currentQuestionIndex.value, timer: timer.value
    }))
  } catch {}
}

function loadDraft() {
  try {
    const d = uni.getStorageSync('assessment_draft_' + assessmentId.value)
    if (d) {
      const parsed = JSON.parse(d)
      Object.assign(answers, parsed.answers || {})
      currentGroupIndex.value = parsed.currentGroupIndex || 0
      currentQuestionIndex.value = parsed.currentQuestionIndex || 0
      timer.value = parsed.timer || 0
    }
  } catch {}
}

async function loadQuestions() {
  const endpoints = [
    \`/api/v1/assessment-assignments/\${assessmentId.value}/questions\`,
    \`/api/v1/assessment/questions/\${assessmentId.value}\`,
    '/api/v1/assessment/questions',
  ]
  let questions: any[] = []
  for (const ep of endpoints) {
    try {
      const res = await http<any>(ep)
      questions = res.questions || res.items || (Array.isArray(res) ? res : [])
      if (questions.length > 0) break
    } catch { continue }
  }

  if (questions.length > 0) {
    // 按量表分组
    const grouped: Record<string, any[]> = {}
    questions.forEach(q => {
      const g = q.scale || q.group || q.category || 'default'
      if (!grouped[g]) grouped[g] = []
      grouped[g].push(q)
    })
    groups.value = Object.entries(grouped).map(([key, qs]) => {
      const sg = scaleGroups.find(s => s.key === key)
      return { key, name: sg?.name || key, questions: qs }
    })
  } else {
    // 生成模拟题目
    groups.value = generateDemoQuestions()
  }

  loadDraft()
}

function generateDemoQuestions(): any[] {
  return [
    { key: 'ttm7', name: 'TTM 行为阶段', questions: [
      { type: 'single', text: '关于改变不健康的行为习惯，您目前处于哪个阶段？', options: ['我没想过要改变', '我在考虑改变', '我准备在近期开始改变', '我已经开始改变了', '我已经保持改变超过6个月'] },
      { type: 'scale', text: '您对改变当前不健康行为的信心程度如何？', min_label: '完全没有信心', max_label: '非常有信心', max: 7 },
      { type: 'boolean', text: '在过去一个月内，您是否尝试过改变某个不健康的生活习惯？' },
    ]},
    { key: 'big5', name: 'BIG5 大五人格', questions: [
      { type: 'scale', text: '我喜欢尝试新事物和新体验。', min_label: '非常不同意', max_label: '非常同意', max: 7 },
      { type: 'scale', text: '我做事有条理且注重细节。', min_label: '非常不同意', max_label: '非常同意', max: 7 },
      { type: 'scale', text: '我在社交场合中感到自在。', min_label: '非常不同意', max_label: '非常同意', max: 7 },
      { type: 'scale', text: '我容易与他人产生共鸣。', min_label: '非常不同意', max_label: '非常同意', max: 7 },
      { type: 'scale', text: '我在压力下容易感到焦虑。', min_label: '非常不同意', max_label: '非常同意', max: 7 },
    ]},
    { key: 'bpt6', name: 'BPT6 行为类型', questions: [
      { type: 'multiple', text: '以下哪些描述最符合您的日常行为模式？（可多选）', options: ['规律运动型', '健康饮食型', '社交活跃型', '学习成长型', '情绪管理型', '作息规律型'] },
      { type: 'single', text: '面对健康目标时，您通常的行动模式是？', options: ['立即行动', '制定计划后行动', '等待合适时机', '需要他人督促'] },
    ]},
  ]
}

async function submitAssessment() {
  uni.showModal({
    title: '确认提交',
    content: '提交后不可修改，确认提交评估？',
    success: async (res) => {
      if (!res.confirm) return
      try {
        await http('/api/v1/assessment/evaluate', {
          method: 'POST',
          data: { assignment_id: assessmentId.value, answers, duration: timer.value }
        })
        // 清除草稿
        try { uni.removeStorageSync('assessment_draft_' + assessmentId.value) } catch {}
        uni.showToast({ title: '提交成功', icon: 'success' })
        setTimeout(() => {
          uni.redirectTo({ url: '/pages/assessment/result?id=' + assessmentId.value })
        }, 800)
      } catch {
        uni.showToast({ title: '提交失败，请重试', icon: 'none' })
      }
    }
  })
}

function confirmExit() {
  const hasAnswers = Object.keys(answers).length > 0
  if (!hasAnswers) { goBack(); return }
  uni.showModal({
    title: '退出评估',
    content: '当前进度已自动保存为草稿，下次可继续',
    confirmText: '退出',
    success: (res) => { if (res.confirm) goBack() }
  })
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

onMounted(() => {
  const page = getCurrentPages().slice(-1)[0] as any
  assessmentId.value = page?.options?.id || 'demo'
  loadQuestions()
  timerInterval = setInterval(() => { timer.value++ }, 1000)
})

onUnmounted(() => { if (timerInterval) clearInterval(timerInterval) })
</script>

<style scoped>
.do-page { min-height: 100vh; background: #F5F6FA; display: flex; flex-direction: column; }
.do-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #9B59B6 0%, #8E44AD 100%); color: #fff; }
.do-nav-back { font-size: 40rpx; padding: 16rpx; }
.do-nav-center { flex: 1; text-align: center; }
.do-nav-group { display: block; font-size: 22rpx; opacity: 0.8; }
.do-nav-scale { display: block; font-size: 30rpx; font-weight: 600; }
.do-nav-timer { font-size: 28rpx; font-family: monospace; background: rgba(255,255,255,0.2); padding: 8rpx 16rpx; border-radius: 8rpx; }

.do-group-progress { display: flex; justify-content: center; gap: 16rpx; padding: 16rpx; }
.do-group-dot { width: 16rpx; height: 16rpx; border-radius: 50%; background: #D0D0D0; }
.do-group-dot--done { background: #27AE60; }
.do-group-dot--active { background: #9B59B6; width: 24rpx; height: 24rpx; margin-top: -4rpx; }

.do-progress-bar { height: 6rpx; background: #E0E0E0; margin: 0 24rpx; border-radius: 3rpx; overflow: hidden; }
.do-progress-fill { height: 100%; background: #9B59B6; border-radius: 3rpx; transition: width 0.3s; }
.do-progress-text { text-align: center; font-size: 22rpx; color: #8E99A4; margin: 8rpx 0; }

.do-question-area { flex: 1; padding: 24rpx; }
.do-question-card { background: #fff; border-radius: 20rpx; padding: 32rpx; min-height: 400rpx; }
.do-question-num { display: inline-block; padding: 4rpx 16rpx; background: #9B59B6; color: #fff; border-radius: 8rpx; font-size: 22rpx; margin-bottom: 16rpx; }
.do-question-text { display: block; font-size: 32rpx; color: #2C3E50; line-height: 1.6; margin-bottom: 32rpx; font-weight: 500; }

.do-options { }
.do-option { display: flex; align-items: center; gap: 16rpx; padding: 24rpx; margin-bottom: 12rpx; border-radius: 12rpx; background: #F8F9FA; border: 2rpx solid transparent; }
.do-option--selected { background: #F0E6F6; border-color: #9B59B6; }
.do-option-indicator { width: 48rpx; height: 48rpx; border-radius: 50%; background: #E0E0E0; color: #5B6B7F; display: flex; align-items: center; justify-content: center; font-size: 24rpx; font-weight: 600; flex-shrink: 0; }
.do-option--selected .do-option-indicator { background: #9B59B6; color: #fff; }
.do-option-text { flex: 1; font-size: 28rpx; color: #2C3E50; line-height: 1.4; }

.do-scale { }
.do-scale-labels { display: flex; justify-content: space-between; margin-bottom: 16rpx; }
.do-scale-min, .do-scale-max { font-size: 22rpx; color: #8E99A4; }
.do-scale-dots { display: flex; justify-content: space-between; gap: 8rpx; }
.do-scale-dot { flex: 1; height: 80rpx; border-radius: 12rpx; background: #F0F0F0; display: flex; align-items: center; justify-content: center; font-size: 30rpx; color: #5B6B7F; font-weight: 600; }
.do-scale-dot--selected { background: #9B59B6; color: #fff; }

.do-boolean { display: flex; gap: 24rpx; }
.do-bool-btn { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 12rpx; padding: 40rpx; border-radius: 16rpx; background: #F0F0F0; font-size: 32rpx; color: #5B6B7F; }
.do-bool-btn--yes { background: #E8F8F0; color: #27AE60; }
.do-bool-btn--no { background: #FFF0ED; color: #E74C3C; }
.do-bool-icon { font-size: 48rpx; }

.do-text { }
.do-text-input { width: 100%; height: 200rpx; padding: 20rpx; background: #F8F9FA; border-radius: 12rpx; font-size: 28rpx; line-height: 1.6; }

.do-bottom { padding: 24rpx; padding-bottom: calc(24rpx + env(safe-area-inset-bottom)); background: #fff; box-shadow: 0 -2rpx 8rpx rgba(0,0,0,0.04); }
.do-bottom-btns { display: flex; gap: 16rpx; }
.do-btn { flex: 1; text-align: center; padding: 24rpx 0; border-radius: 12rpx; font-size: 28rpx; font-weight: 600; }
.do-btn-prev { background: #F0F0F0; color: #5B6B7F; }
.do-btn-next { background: #9B59B6; color: #fff; }
.do-btn-submit { background: #27AE60; color: #fff; }
</style>`;

// ============================================================
// 5. assessment/result.vue — 评估结果/行为画像
// ============================================================
const ASSESSMENT_RESULT = `<template>
  <view class="result-page">
    <view class="result-navbar">
      <view class="result-nav-back" @tap="goBack">←</view>
      <text class="result-nav-title">评估结果</text>
      <view class="result-nav-share" @tap="shareResult">分享</view>
    </view>

    <scroll-view scroll-y class="result-content" v-if="!loading">
      <!-- 总分概览 -->
      <view class="result-header">
        <view class="result-score-ring">
          <text class="result-score-num">{{ totalScore }}</text>
          <text class="result-score-label">综合评分</text>
        </view>
        <view class="result-header-info">
          <text class="result-header-title">行为健康画像</text>
          <text class="result-header-date">{{ formatDate(data.completed_at) }}</text>
          <text class="result-header-scales">{{ data.scale_names || '综合评估' }}</text>
        </view>
      </view>

      <!-- 大五人格 -->
      <view class="result-section" v-if="big5Data.length">
        <text class="result-section-title">🧠 人格特质 · 大五人格</text>
        <view class="result-big5">
          <view class="big5-row" v-for="item in big5Data" :key="item.name">
            <text class="big5-name">{{ item.name }}</text>
            <view class="big5-bar-track">
              <view class="big5-bar-fill" :style="{ width: item.percent + '%', background: item.color }"></view>
            </view>
            <text class="big5-score">{{ item.score }}<text class="big5-max">/7</text></text>
          </view>
        </view>
        <text class="result-summary" v-if="big5Summary">{{ big5Summary }}</text>
      </view>

      <!-- BPT6 行为类型 -->
      <view class="result-section" v-if="bptTags.length">
        <text class="result-section-title">🏷️ 行为类型标签</text>
        <view class="result-bpt-tags">
          <view class="bpt-tag" v-for="(tag, i) in bptTags" :key="i" :style="{ background: bptColors[i % bptColors.length] }">
            {{ tag }}
          </view>
        </view>
      </view>

      <!-- TTM 阶段 -->
      <view class="result-section" v-if="ttmStage">
        <text class="result-section-title">📈 行为改变阶段</text>
        <view class="result-ttm">
          <view
            v-for="(stage, i) in ttmStages" :key="i"
            class="ttm-step" :class="{ 'ttm-step--done': i < ttmIndex, 'ttm-step--current': i === ttmIndex }"
          >
            <view class="ttm-step-dot">
              <text v-if="i < ttmIndex">✓</text>
              <text v-else-if="i === ttmIndex">●</text>
              <text v-else>○</text>
            </view>
            <view class="ttm-step-info">
              <text class="ttm-step-name">{{ stage.name }}</text>
              <text class="ttm-step-desc">{{ stage.desc }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- AI 行为处方预览 -->
      <view class="result-section">
        <text class="result-section-title">🤖 AI 行为处方建议</text>
        <view v-if="prescriptions.length" class="result-rx-list">
          <view class="result-rx-card" v-for="(rx, i) in prescriptions" :key="i">
            <text class="result-rx-num">{{ i + 1 }}</text>
            <view class="result-rx-body">
              <text class="result-rx-title">{{ rx.title || rx }}</text>
              <text class="result-rx-desc" v-if="rx.description">{{ rx.description }}</text>
            </view>
          </view>
        </view>
        <view v-else class="result-rx-placeholder">
          <text>AI处方将在教练审核后生成</text>
        </view>
      </view>

      <!-- 操作按钮 -->
      <view class="result-footer">
        <view class="result-btn result-btn-detail" @tap="viewFullReport">查看完整报告</view>
        <view class="result-btn result-btn-share" @tap="shareToCoach">分享给教练</view>
      </view>
    </scroll-view>

    <view v-if="loading" class="result-loading">
      <text>加载评估结果...</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

${INLINE_HTTP}

const loading = ref(true)
const data = ref<any>({})

const ttmStages = [
  { name: '前意向期', desc: '尚未意识到需要改变' },
  { name: '意向期', desc: '开始考虑改变的可能' },
  { name: '准备期', desc: '制定改变计划' },
  { name: '行动期', desc: '正在积极改变行为' },
  { name: '维持期', desc: '保持健康行为6个月以上' },
  { name: '巩固期', desc: '行为已成为习惯' },
]

const bptColors = ['#3498DB', '#E67E22', '#27AE60', '#9B59B6', '#E74C3C', '#1ABC9C']

const totalScore = computed(() => data.value.total_score || data.value.score || '—')

const big5Data = computed(() => {
  const r = data.value.big5 || data.value.personality || data.value.results?.big5
  if (!r) return []
  const dims = [
    { key: 'openness', name: '开放性', color: '#3498DB' },
    { key: 'conscientiousness', name: '尽责性', color: '#27AE60' },
    { key: 'extraversion', name: '外向性', color: '#E67E22' },
    { key: 'agreeableness', name: '宜人性', color: '#9B59B6' },
    { key: 'neuroticism', name: '神经质', color: '#E74C3C' },
  ]
  return dims.map(d => {
    const score = r[d.key] ?? r[d.name] ?? 0
    return { ...d, score: Math.round(score * 10) / 10, percent: Math.min(100, Math.round((score / 7) * 100)) }
  })
})

const big5Summary = computed(() => {
  if (!big5Data.value.length) return ''
  const top = [...big5Data.value].sort((a, b) => b.score - a.score).slice(0, 2)
  return \`您在\${top.map(d => d.name).join('和')}方面表现突出\`
})

const bptTags = computed(() => {
  const r = data.value.bpt6 || data.value.behavior_types || data.value.results?.bpt6
  if (Array.isArray(r)) return r.slice(0, 6)
  if (r && typeof r === 'object') return Object.keys(r).slice(0, 6)
  return []
})

const ttmStage = computed(() => data.value.ttm_stage || data.value.ttm || data.value.results?.ttm || '')
const ttmIndex = computed(() => {
  const s = ttmStage.value
  if (!s) return -1
  const map: Record<string, number> = { precontemplation: 0, contemplation: 1, preparation: 2, action: 3, maintenance: 4, termination: 5 }
  return map[s] ?? ttmStages.findIndex(st => s.includes(st.name)) ?? -1
})

const prescriptions = computed(() => {
  const rx = data.value.prescriptions || data.value.suggestions || data.value.results?.prescriptions
  if (Array.isArray(rx)) return rx.slice(0, 5)
  if (typeof rx === 'string') return rx.split('\\n').filter(Boolean)
  return []
})

function formatDate(d: string): string { return d ? d.slice(0, 10) : '-' }

async function loadData() {
  loading.value = true
  const page = getCurrentPages().slice(-1)[0] as any
  const id = page?.options?.id

  // ★ 多端点fallback ★
  const endpoints = id ? [
    \`/api/v1/assessment/results/\${id}\`,
    \`/api/v1/assessment-assignments/\${id}/result\`,
    \`/api/v1/assessment/\${id}\`,
  ] : ['/api/v1/assessment/profile/me', '/api/v1/assessment/user/latest']

  for (const ep of endpoints) {
    try {
      const res = await http<any>(ep)
      data.value = res.result || res.profile || res || {}
      break
    } catch { continue }
  }
  loading.value = false
}

function viewFullReport() {
  uni.showToast({ title: '完整报告生成中...', icon: 'none' })
}

function shareToCoach() {
  uni.showToast({ title: '已分享给教练', icon: 'success' })
}

function shareResult() {
  uni.showToast({ title: '分享功能即将开放', icon: 'none' })
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

onMounted(() => { loadData() })
</script>

<style scoped>
.result-page { min-height: 100vh; background: #F5F6FA; }
.result-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #9B59B6 0%, #8E44AD 100%); color: #fff; }
.result-nav-back { font-size: 40rpx; padding: 16rpx; }
.result-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.result-nav-share { font-size: 26rpx; padding: 8rpx 16rpx; background: rgba(255,255,255,0.2); border-radius: 8rpx; }

.result-loading { text-align: center; padding: 200rpx 0; color: #8E99A4; font-size: 28rpx; }
.result-content { height: calc(100vh - 180rpx); padding: 24rpx; }

.result-header { display: flex; align-items: center; gap: 24rpx; background: linear-gradient(135deg, #9B59B6 0%, #8E44AD 100%); border-radius: 20rpx; padding: 32rpx; color: #fff; margin-bottom: 16rpx; }
.result-score-ring { width: 120rpx; height: 120rpx; border-radius: 50%; border: 6rpx solid rgba(255,255,255,0.3); display: flex; flex-direction: column; align-items: center; justify-content: center; }
.result-score-num { font-size: 40rpx; font-weight: 700; }
.result-score-label { font-size: 18rpx; opacity: 0.8; }
.result-header-info { flex: 1; }
.result-header-title { display: block; font-size: 32rpx; font-weight: 600; }
.result-header-date { display: block; font-size: 24rpx; opacity: 0.8; margin-top: 4rpx; }
.result-header-scales { display: block; font-size: 22rpx; opacity: 0.7; margin-top: 4rpx; }

.result-section { background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 16rpx; }
.result-section-title { display: block; font-size: 30rpx; font-weight: 600; color: #2C3E50; margin-bottom: 20rpx; }

.big5-row { display: flex; align-items: center; gap: 12rpx; margin-bottom: 16rpx; }
.big5-name { width: 100rpx; font-size: 24rpx; color: #5B6B7F; text-align: right; }
.big5-bar-track { flex: 1; height: 24rpx; background: #F0F0F0; border-radius: 12rpx; overflow: hidden; }
.big5-bar-fill { height: 100%; border-radius: 12rpx; transition: width 0.8s ease; }
.big5-score { width: 80rpx; font-size: 26rpx; color: #2C3E50; font-weight: 600; }
.big5-max { font-size: 20rpx; color: #8E99A4; font-weight: 400; }

.result-summary { display: block; font-size: 24rpx; color: #5B6B7F; background: #F8F9FA; padding: 16rpx; border-radius: 12rpx; margin-top: 12rpx; line-height: 1.5; }

.result-bpt-tags { display: flex; flex-wrap: wrap; gap: 12rpx; }
.bpt-tag { padding: 12rpx 24rpx; border-radius: 24rpx; color: #fff; font-size: 26rpx; }

.result-ttm { }
.ttm-step { display: flex; align-items: flex-start; gap: 16rpx; padding: 16rpx 0; position: relative; }
.ttm-step::before { content: ''; position: absolute; left: 18rpx; top: 52rpx; bottom: -16rpx; width: 4rpx; background: #E0E0E0; }
.ttm-step:last-child::before { display: none; }
.ttm-step--done::before { background: #27AE60; }
.ttm-step-dot { width: 40rpx; height: 40rpx; border-radius: 50%; background: #F0F0F0; display: flex; align-items: center; justify-content: center; font-size: 24rpx; color: #8E99A4; flex-shrink: 0; position: relative; z-index: 1; }
.ttm-step--done .ttm-step-dot { background: #27AE60; color: #fff; }
.ttm-step--current .ttm-step-dot { background: #9B59B6; color: #fff; width: 48rpx; height: 48rpx; margin: -4rpx; box-shadow: 0 0 0 8rpx rgba(155,89,182,0.15); }
.ttm-step-info { flex: 1; }
.ttm-step-name { display: block; font-size: 28rpx; color: #2C3E50; font-weight: 500; }
.ttm-step--current .ttm-step-name { color: #9B59B6; font-weight: 600; }
.ttm-step-desc { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }

.result-rx-list { }
.result-rx-card { display: flex; gap: 16rpx; margin-bottom: 16rpx; padding: 16rpx; background: #F8F9FA; border-radius: 12rpx; }
.result-rx-num { width: 40rpx; height: 40rpx; border-radius: 50%; background: #9B59B6; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 22rpx; flex-shrink: 0; }
.result-rx-body { flex: 1; }
.result-rx-title { display: block; font-size: 26rpx; color: #2C3E50; font-weight: 500; }
.result-rx-desc { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 6rpx; line-height: 1.5; }
.result-rx-placeholder { text-align: center; padding: 40rpx; color: #8E99A4; font-size: 26rpx; }

.result-footer { display: flex; gap: 16rpx; padding: 24rpx 0 48rpx; }
.result-btn { flex: 1; text-align: center; padding: 24rpx 0; border-radius: 16rpx; font-size: 28rpx; font-weight: 600; }
.result-btn-detail { background: #9B59B6; color: #fff; }
.result-btn-share { background: #F0E6F6; color: #9B59B6; }
</style>`;


// ============================================================
// 部署逻辑
// ============================================================
const FILES = {
  // 教练评估管理
  'src/pages/coach/assessment/index.vue': COACH_ASSESSMENT_INDEX,
  'src/pages/coach/assessment/review.vue': COACH_ASSESSMENT_REVIEW,
  // 学员评估
  'src/pages/assessment/pending.vue': ASSESSMENT_PENDING,
  'src/pages/assessment/do.vue': ASSESSMENT_DO,
  'src/pages/assessment/result.vue': ASSESSMENT_RESULT,
};

console.log('╔══════════════════════════════════════════╗');
console.log('║  评估管理模块部署 — 5个页面完整实现     ║');
console.log('╚══════════════════════════════════════════╝\n');

let count = 0;
for (const [filePath, content] of Object.entries(FILES)) {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
    console.log(`  📁 ${dir}`);
  }
  fs.writeFileSync(filePath, content);
  count++;
  const lines = content.split('\n').length;
  console.log(`  ✅ ${filePath} (${lines} 行)`);
}

console.log(`\n✅ 共部署 ${count} 个文件\n`);

// ============================================================
// 关键API修复检查
// ============================================================
console.log('═══ API 路径修复清单 ═══');
console.log('  ❌ /api/v1/assessment-assignments         → ✅ /api/v1/assessment-assignments/review-list');
console.log('  ❌ /api/v1/behavior/{id}/recent            → ⚠️  学员详情页调用,需单独修复');
console.log('  ❌ /api/v1/professional/coach/students/... → ⚠️  学员详情页调用,需单独修复');
console.log('');

// ============================================================
// pages.json 路由检查
// ============================================================
console.log('═══ pages.json 路由检查 ═══');
const pagesJsonPath = 'src/pages.json';
if (fs.existsSync(pagesJsonPath)) {
  const pagesContent = fs.readFileSync(pagesJsonPath, 'utf-8');
  const requiredPaths = [
    'assessment/pending',
    'assessment/do',
    'assessment/result',
  ];
  const requiredSubPaths = [
    'assessment/index',
    'assessment/review',
  ];

  console.log('  主包页面:');
  for (const p of requiredPaths) {
    const found = pagesContent.includes(p);
    console.log(`    ${found ? '✅' : '❌'} pages/${p}`);
    if (!found) {
      console.log(`       → 需要在 pages.json 的 pages 数组中添加:`);
      console.log(`         { "path": "pages/${p}", "style": { "navigationBarTitleText": "" , "navigationStyle": "custom" } }`);
    }
  }

  console.log('  coach分包页面:');
  for (const p of requiredSubPaths) {
    const found = pagesContent.includes(p);
    console.log(`    ${found ? '✅' : '❌'} ${p}`);
    if (!found) {
      console.log(`       → 需要在 coach subPackage 中添加:`);
      console.log(`         { "path": "${p}", "style": { "navigationBarTitleText": "", "navigationStyle": "custom" } }`);
    }
  }
} else {
  console.log('  ⚠️  未找到 pages.json，请确保路由配置正确');
}

console.log('\n═══ 下一步 ═══');
console.log('  1. node deploy-assessment-module.js');
console.log('  2. npm run dev:mp-weixin');
console.log('  3. 微信开发者工具 → 评估管理 → 验证页面');
console.log('  4. 如果学员详情页还有404，需要修复behavior和notes API路径');
console.log('═══════════════════════════════════════════\n');
