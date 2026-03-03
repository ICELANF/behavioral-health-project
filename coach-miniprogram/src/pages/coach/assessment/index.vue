<template>
  <view class="assess-page">
    <!-- 导航栏 -->
    <view class="assess-navbar">
      <view class="assess-nav-back" @tap="goBack">←</view>
      <text class="assess-nav-title">评估管理</text>
      <view class="assess-nav-action" @tap="showAssign = true">+ 分配</view>
    </view>

    <!-- 统计 + Tab 合并单排 -->
    <view class="assess-stattabs">
      <view
        v-for="t in statTabs" :key="t.key"
        class="assess-st" :class="{ 'assess-st--active': activeTab === t.key }"
        @tap="activeTab = t.key"
      >
        <text class="assess-st-num" :style="activeTab === t.key ? {} : { color: t.color }">{{ t.count }}</text>
        <text class="assess-st-label">{{ t.label }}</text>
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
          <view v-if="['submitted','review','completed','completed_pending_review'].includes(item.status)" class="assess-card-actions">
            <view class="assess-action-btn assess-action-review" @tap.stop="goReview(item)">查看评估</view>
          </view>
          <!-- 待完成：提醒学员 -->
          <view v-if="item.status === 'pending'" class="assess-card-actions">
            <view class="assess-action-btn assess-action-remind" @tap.stop="remindStudent(item)">提醒完成</view>
          </view>
        </view>
      </view>

      <view v-if="!loading && filteredItems.length === 0" class="assess-empty">
        <text class="assess-empty-icon">📋</text>
        <text class="assess-empty-text">暂无{{ statTabs.find(t => t.key === activeTab)?.label || '' }}评估</text>
        <view class="assess-empty-action" @tap="showAssign = true">分配新评估</view>
      </view>

      <view v-if="loading" class="assess-loading">
        <text>加载中...</text>
      </view>
    </scroll-view>

    <!-- 分配评估弹窗 -->
    <view v-if="showAssign" class="assess-modal-mask" @tap="closeAssign">
      <view class="assess-modal" @tap.stop>
        <text class="assess-modal-title">分配新评估</text>

        <!-- ① 学员选择面板（未选时显示） -->
        <view v-if="!selectedStudentObj" class="assess-modal-section">
          <view class="assess-modal-hrow">
            <text class="assess-modal-label">选择学员</text>
            <view class="assess-search-toggle" @tap="modalSearchMode = !modalSearchMode">
              {{ modalSearchMode ? '📋 推荐' : '🔍 搜索' }}
            </view>
          </view>

          <!-- 搜索框 -->
          <view v-if="modalSearchMode" class="assess-modal-searchbox">
            <input class="assess-modal-sinput" v-model="modalSearchQuery" placeholder="输入姓名搜索..." focus />
          </view>

          <!-- 学员卡片列表 -->
          <view class="assess-student-cards">
            <view
              v-for="s in currentBatchStudents" :key="s.id"
              class="assess-sc-card"
              @tap="selectStudentObj(s)"
            >
              <view class="assess-sc-avatar" :style="{ background: avatarColor(s.name) }">{{ (s.name||'?')[0] }}</view>
              <view class="assess-sc-info">
                <text class="assess-sc-name">{{ s.name }}</text>
                <text class="assess-sc-sub">{{ formatStudentSub(s) }}</text>
              </view>
              <view class="assess-sc-risk" :style="{ background: riskBg(s.risk_level) }">R{{ parseRisk(s.risk_level) }}</view>
            </view>
            <view v-if="currentBatchStudents.length === 0" class="assess-sc-empty">
              {{ modalSearchMode ? '未找到匹配学员' : '暂无学员数据' }}
            </view>
          </view>

          <!-- 批次导航（仅推荐模式） -->
          <view v-if="!modalSearchMode && prioritizedStudents.length > BATCH_SIZE" class="assess-batch-nav">
            <view class="assess-batch-btn" :class="{ 'assess-batch-btn--off': batchIndex === 0 }" @tap="prevBatch">‹ 上一批</view>
            <text class="assess-batch-info">{{ Math.floor(batchIndex / BATCH_SIZE) + 1 }} / {{ Math.ceil(prioritizedStudents.length / BATCH_SIZE) }}</text>
            <view class="assess-batch-btn" :class="{ 'assess-batch-btn--off': !hasNextBatch }" @tap="nextBatch">下一批 ›</view>
          </view>
        </view>

        <!-- ② 已选学员展示（已选时显示） -->
        <view v-else class="assess-modal-section">
          <view class="assess-modal-hrow">
            <text class="assess-modal-label">已选学员</text>
            <view class="assess-reselect" @tap="selectedStudentObj = null">↩ 重新选择</view>
          </view>
          <view class="assess-selected-card">
            <view class="assess-sc-avatar" :style="{ background: avatarColor(selectedStudentObj.name) }">{{ (selectedStudentObj.name||'?')[0] }}</view>
            <view class="assess-sc-info">
              <text class="assess-sc-name">{{ selectedStudentObj.name }}</text>
              <text class="assess-sc-sub">{{ formatStudentSub(selectedStudentObj) }}</text>
            </view>
            <view class="assess-sc-risk" :style="{ background: riskBg(selectedStudentObj.risk_level) }">R{{ parseRisk(selectedStudentObj.risk_level) }}</view>
          </view>
        </view>

        <!-- ③ 量表/时间/备注（仅已选学员后展示） -->
        <template v-if="selectedStudentObj">
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
        </template>

        <view class="assess-modal-actions">
          <view class="assess-modal-btn assess-modal-cancel" @tap="closeAssign">取消</view>
          <view
            class="assess-modal-btn assess-modal-confirm"
            :class="{ 'assess-modal-confirm--off': !selectedStudentObj }"
            @tap="doAssign"
          >确认分配</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const activeTab = ref('all')
const searchText = ref('')
const refreshing = ref(false)
const loading = ref(false)
const assignments = ref<any[]>([])
const studentsData = ref<any[]>([])
const showAssign = ref(false)
const selectedStudentObj = ref<any>(null)
const selectedScales = ref<string[]>(['big5', 'ttm7'])
const BATCH_SIZE = 5
const batchIndex = ref(0)
const modalSearchMode = ref(false)
const modalSearchQuery = ref('')
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

// 统计 + Tab 合并：单排四格，既是数字展示又是筛选器
const statTabs = computed(() => [
  { key: 'all',       label: '全部', color: '#9B59B6', count: assignments.value.filter(a => a.status !== 'cancelled').length },
  { key: 'pending',   label: '待完成', color: '#E67E22', count: assignments.value.filter(a => a.status === 'pending').length },
  { key: 'review',    label: '待审核', color: '#9B59B6', count: assignments.value.filter(a => a.status === 'completed').length },
  { key: 'completed', label: '已完成', color: '#27AE60', count: assignments.value.filter(a => ['reviewed', 'pushed'].includes(a.status)).length },
])

function parseRisk(r: any): number {
  return parseInt(String(r ?? '0').replace(/\D/g, '') || '0')
}
function riskBg(r: any): string {
  const n = parseRisk(r)
  if (n >= 4) return '#E74C3C'
  if (n === 3) return '#E67E22'
  if (n === 2) return '#F39C12'
  return '#27AE60'
}
function formatStudentSub(s: any): string {
  const days = s.days_since_last_contact ?? s.days_no_contact ?? null
  const stage = s.stage_label || s.stage || ''
  if (days === null) return stage || '从未联系'
  if (days > 30) return `${stage} · ${days}天未联系`
  return `${stage} · ${days}天前联系`
}
function selectStudentObj(s: any) {
  selectedStudentObj.value = s
  modalSearchMode.value = false
  modalSearchQuery.value = ''
}
function nextBatch() {
  if (hasNextBatch.value) batchIndex.value += BATCH_SIZE
}
function prevBatch() {
  if (batchIndex.value >= BATCH_SIZE) batchIndex.value -= BATCH_SIZE
}
function closeAssign() {
  showAssign.value = false
  selectedStudentObj.value = null
  batchIndex.value = 0
  modalSearchMode.value = false
  modalSearchQuery.value = ''
}

const prioritizedStudents = computed(() => {
  return [...studentsData.value].sort((a: any, b: any) => {
    const ra = parseRisk(a.risk_level), rb = parseRisk(b.risk_level)
    if (rb !== ra) return rb - ra
    const da = a.days_since_last_contact ?? a.days_no_contact ?? 999
    const db = b.days_since_last_contact ?? b.days_no_contact ?? 999
    return db - da
  })
})
const currentBatchStudents = computed(() => {
  if (modalSearchMode.value) {
    const q = modalSearchQuery.value.toLowerCase()
    if (!q) return prioritizedStudents.value.slice(0, BATCH_SIZE)
    return studentsData.value.filter((s: any) =>
      (s.name || s.full_name || '').toLowerCase().includes(q)
    ).slice(0, BATCH_SIZE)
  }
  return prioritizedStudents.value.slice(batchIndex.value, batchIndex.value + BATCH_SIZE)
})
const hasNextBatch = computed(() => batchIndex.value + BATCH_SIZE < prioritizedStudents.value.length)

const filteredItems = computed(() => {
  // 全部Tab不显示已取消，保持列表干净
  let list = assignments.value.filter(a => a.status !== 'cancelled')
  if (activeTab.value !== 'all') {
    if (activeTab.value === 'pending') list = list.filter(a => a.status === 'pending')
    else if (activeTab.value === 'review') list = list.filter(a => a.status === 'completed')
    else if (activeTab.value === 'completed') list = list.filter(a => ['reviewed', 'pushed'].includes(a.status))
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
    pending: '#E67E22',
    completed: '#9B59B6',
    reviewed: '#27AE60', pushed: '#27AE60',
    cancelled: '#BDC3C7'
  }
  return map[s] || '#8E99A4'
}

function statusLabel(s: string): string {
  const map: Record<string, string> = {
    pending: '待完成', completed: '待审核',
    reviewed: '已审核', pushed: '已推送', cancelled: '已取消'
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

  // 主数据源: /coach-list 返回教练所有状态的评估任务
  try {
    const res = await http<any>('/api/v1/assessment-assignments/coach-list')
    assignments.value = res.assignments || (Array.isArray(res) ? res : [])
  } catch (e) {
    console.warn('[assessment/index] coach-list:', e)
    // fallback: review-list 只含 completed/reviewed
    try {
      const res2 = await http<any>('/api/v1/assessment-assignments/review-list')
      assignments.value = res2.assignments || res2.items || (Array.isArray(res2) ? res2 : [])
    } catch (e2) { console.warn('[assessment/index] review-list:', e2); assignments.value = [] }
  }

  // 加载学员列表（用于分配弹窗）
  try {
    const res = await http<any>('/api/v1/coach/students')
    studentsData.value = res.students || res.items || (Array.isArray(res) ? res : [])
  } catch (e) {
    console.warn('[assessment/index] students:', e)
    try {
      const dash = await http<any>('/api/v1/coach/dashboard')
      studentsData.value = dash.students || []
    } catch (e2) { console.warn('[assessment/index] dashboard students:', e2); studentsData.value = [] }
  }

  loading.value = false
}

async function doAssign() {
  if (!selectedStudentObj.value) {
    uni.showToast({ title: '请选择学员', icon: 'none' })
    return
  }
  if (selectedScales.value.length === 0) {
    uni.showToast({ title: '请选择量表', icon: 'none' })
    return
  }

  const student = selectedStudentObj.value
  try {
    await http('/api/v1/assessment-assignments/assign', {
      method: 'POST',
      data: {
        user_id: student.id || student.user_id,
        student_id: student.id || student.user_id,
        scales: selectedScales.value,
        assessment_type: selectedScales.value.join(','),
        deadline: deadline.value || undefined,
        note: assignNote.value || undefined,
      }
    })
    uni.showToast({ title: '分配成功', icon: 'success' })
    closeAssign()
    assignNote.value = ''
    deadline.value = ''
    loadData()
  } catch (e: any) {
    const detail = e?.data?.detail || e?.detail || e?.message || '未知错误'
    uni.showToast({ title: detail.length > 20 ? detail.slice(0, 20) + '…' : detail, icon: 'none' })
  }
}

async function remindStudent(item: any) {
  const sid = item.student_id || item.user_id || item.id
  try {
    await http(`/api/v1/coach/students/${sid}/remind`, {
      method: 'POST',
      data: {
        title: '评估提醒',
        message: '请尽快完成评估任务',
        type: 'assessment_remind',
      }
    })
    uni.showToast({ title: '已发送提醒', icon: 'success' })
  } catch (e) {
    console.warn('[assessment/index] remind:', e)
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

/* ── 统计+Tab 合并单排 ── */
.assess-stattabs { display: flex; padding: 16rpx 24rpx 12rpx; gap: 12rpx; }
.assess-st { flex: 1; background: #fff; border-radius: 14rpx; padding: 18rpx 8rpx 14rpx; text-align: center; }
.assess-st--active { background: #9B59B6; }
.assess-st-num { display: block; font-size: 36rpx; font-weight: 700; color: #2C3E50; }
.assess-st--active .assess-st-num { color: #fff; }
.assess-st-label { display: block; font-size: 20rpx; color: #8E99A4; margin-top: 4rpx; }
.assess-st--active .assess-st-label { color: rgba(255,255,255,0.85); }

.assess-search { padding: 12rpx 24rpx; }
.assess-search-input { background: #fff; border-radius: 12rpx; padding: 16rpx 24rpx; font-size: 28rpx; }

.assess-list { height: calc(100vh - 480rpx); padding: 0 24rpx 24rpx; }

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
.assess-modal-confirm--off { background: #C0C0C0; pointer-events: none; }

/* ── 学员选择器 ── */
.assess-modal-hrow { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12rpx; }
.assess-search-toggle { font-size: 24rpx; color: #9B59B6; padding: 6rpx 16rpx; background: #F5F0FF; border-radius: 8rpx; }
.assess-modal-searchbox { margin-bottom: 12rpx; }
.assess-modal-sinput { width: 100%; padding: 14rpx 20rpx; background: #F5F6FA; border-radius: 12rpx; font-size: 28rpx; box-sizing: border-box; }

.assess-student-cards { display: flex; flex-direction: column; gap: 10rpx; }
.assess-sc-card { display: flex; align-items: center; gap: 16rpx; padding: 16rpx; background: #F8F9FA; border-radius: 14rpx; border: 2rpx solid transparent; }
.assess-sc-card:active { border-color: #9B59B6; background: #F5F0FF; }
.assess-sc-avatar { width: 64rpx; height: 64rpx; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 26rpx; font-weight: 600; flex-shrink: 0; }
.assess-sc-info { flex: 1; }
.assess-sc-name { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.assess-sc-sub { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.assess-sc-risk { padding: 4rpx 12rpx; border-radius: 6rpx; color: #fff; font-size: 22rpx; font-weight: 600; flex-shrink: 0; }
.assess-sc-empty { text-align: center; padding: 40rpx 0; font-size: 26rpx; color: #8E99A4; }

/* ── 批次导航 ── */
.assess-batch-nav { display: flex; align-items: center; justify-content: space-between; padding: 12rpx 0; margin-top: 8rpx; }
.assess-batch-btn { font-size: 24rpx; color: #9B59B6; padding: 8rpx 20rpx; background: #F5F0FF; border-radius: 8rpx; }
.assess-batch-btn--off { color: #C0C0C0; background: #F5F5F5; pointer-events: none; }
.assess-batch-info { font-size: 24rpx; color: #8E99A4; }

/* ── 已选学员卡片 ── */
.assess-selected-card { display: flex; align-items: center; gap: 16rpx; padding: 16rpx; background: #F5F0FF; border-radius: 14rpx; border: 2rpx solid #9B59B6; }
.assess-reselect { font-size: 24rpx; color: #9B59B6; }
</style>