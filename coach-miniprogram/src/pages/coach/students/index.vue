<template>
  <view class="stu-page">
    <view class="stu-navbar">
      <view class="stu-nav-back" @tap="goBack">←</view>
      <text class="stu-nav-title">我的学员</text>
      <text class="stu-nav-count">{{ students.length }}人</text>
    </view>

    <!-- 搜索 + 筛选 -->
    <view class="stu-filter-bar">
      <input class="stu-search" placeholder="搜索学员姓名" v-model="searchText" />
      <view class="stu-sort" @tap="toggleSort">
        {{ sortLabel }} ▾
      </view>
    </view>

    <!-- 阶段筛选 -->
    <scroll-view scroll-x class="stu-stage-bar">
      <view v-for="s in stageTabs" :key="s.key" class="stu-stage-tag" :class="{ 'stu-stage-tag--active': activeStage === s.key }" @tap="activeStage = s.key">
        {{ s.label }} ({{ s.count }})
      </view>
    </scroll-view>

    <!-- 学员列表 -->
    <scroll-view scroll-y class="stu-list" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <view v-for="s in filteredStudents" :key="s.id" class="stu-card" @tap="goDetail(s.id)">
        <view class="stu-card-left">
          <view class="stu-avatar" :style="{ background: avatarColor(s.name) }">{{ (s.name||'?')[0] }}</view>
          <view class="stu-card-info">
            <text class="stu-card-name">{{ s.name }}</text>
            <text class="stu-card-meta">{{ s.stage || '未评估' }} · Day {{ s.day_index || '—' }}</text>
          </view>
        </view>
        <view class="stu-card-right">
          <view class="stu-risk-tag" :style="{ background: riskBg(s.risk_level), color: riskColor(s.risk_level) }">
            R{{ s.risk_level }}
          </view>
          <text class="stu-card-active">{{ s.active_text }}</text>
        </view>
      </view>

      <view v-if="filteredStudents.length === 0" class="stu-empty">
        <text class="stu-empty-icon">👥</text>
        <text class="stu-empty-text">{{ searchText ? '未找到匹配学员' : '暂无学员' }}</text>
      </view>
    </scroll-view>
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
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data as T)
        else reject(new Error(`HTTP ${res.statusCode}`))
      },
      fail: (err: any) => reject(err)
    })
  })
}

interface Student {
  id: number
  name: string
  stage: string
  risk_level: number
  day_index: number
  active_text: string
  micro_action_count: number
  last_contact_days: number
}

const searchText = ref('')
const activeStage = ref('all')
const sortBy = ref<'risk'|'name'|'active'>('risk')
const refreshing = ref(false)
const students = ref<Student[]>([])

const sortLabel = computed(() => {
  const m: Record<string, string> = { risk: '风险↓', name: '姓名', active: '活跃↓' }
  return m[sortBy.value]
})

const stageTabs = computed(() => {
  const all = students.value
  const stages = [
    { key: 'all', label: '全部', count: all.length },
    { key: 'precontemplation', label: '前意向', count: all.filter(s => s.stage?.includes('前意向') || s.stage === 'precontemplation').length },
    { key: 'contemplation', label: '意向', count: all.filter(s => s.stage?.includes('意向') || s.stage === 'contemplation').length },
    { key: 'preparation', label: '准备', count: all.filter(s => s.stage?.includes('准备') || s.stage === 'preparation').length },
    { key: 'action', label: '行动', count: all.filter(s => s.stage?.includes('行动') || s.stage === 'action').length },
    { key: 'maintenance', label: '维持', count: all.filter(s => s.stage?.includes('维持') || s.stage === 'maintenance').length },
  ]
  return stages.filter(s => s.key === 'all' || s.count > 0)
})

const filteredStudents = computed(() => {
  let list = students.value
  // stage filter
  if (activeStage.value !== 'all') {
    list = list.filter(s => (s.stage || '').toLowerCase().includes(activeStage.value))
  }
  // search
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    list = list.filter(s => (s.name || '').toLowerCase().includes(q))
  }
  // sort
  if (sortBy.value === 'risk') list = [...list].sort((a, b) => (b.risk_level || 0) - (a.risk_level || 0))
  else if (sortBy.value === 'name') list = [...list].sort((a, b) => (a.name || '').localeCompare(b.name || ''))
  else if (sortBy.value === 'active') list = [...list].sort((a, b) => (a.last_contact_days || 999) - (b.last_contact_days || 999))
  return list
})

function toggleSort() {
  const order: Array<'risk'|'name'|'active'> = ['risk', 'name', 'active']
  const idx = order.indexOf(sortBy.value)
  sortBy.value = order[(idx + 1) % order.length]
}

const colorPool = ['#3498DB','#E74C3C','#27AE60','#9B59B6','#E67E22','#1ABC9C','#34495E']
function avatarColor(name: string): string {
  if (!name) return '#8E99A4'
  let h = 0; for (let i = 0; i < name.length; i++) h = name.charCodeAt(i) + ((h << 5) - h)
  return colorPool[Math.abs(h) % colorPool.length]
}

// Parse risk level from string ("R3") or number (3) → number
function parseRisk(v: any): number {
  if (typeof v === 'number') return v
  if (typeof v === 'string') { const n = parseInt(v.replace(/\D/g, '')); return isNaN(n) ? 0 : n }
  return 0
}

function riskColor(level: number): string {
  if (level >= 3) return '#C0392B'
  if (level >= 2) return '#E67E22'
  if (level >= 1) return '#F39C12'
  return '#27AE60'
}
function riskBg(level: number): string {
  if (level >= 3) return '#FDEDEC'
  if (level >= 2) return '#FEF5E7'
  if (level >= 1) return '#FEFCE8'
  return '#E8F8F0'
}

async function loadStudents() {
  try {
    const res = await http<any>('/api/v1/coach/dashboard')
    const raw = res.students || res.data?.students || []
    students.value = (Array.isArray(raw) ? raw : []).map((s: any) => ({
      id: s.id || s.user_id,
      name: s.name || s.full_name || s.username || '未知',
      stage: s.ttm_stage || s.stage || '未评估',
      risk_level: parseRisk(s.risk_level ?? s.risk_score),
      day_index: s.day_index ?? s.journey_day ?? 0,
      micro_action_count: s.micro_action_count ?? 0,
      last_contact_days: s.days_since_last_contact ?? 999,
      active_text: s.days_since_last_contact != null
        ? (s.days_since_last_contact === 0 ? '今天' : s.days_since_last_contact + '天前')
        : '—',
    }))
  } catch {
    // fallback
    try {
      const res2 = await http<any>('/api/v1/coach/students')
      const raw2 = res2.items || res2.students || (Array.isArray(res2) ? res2 : [])
      students.value = raw2.map((s: any) => ({
        id: s.id || s.user_id,
        name: s.name || s.full_name || '未知',
        stage: s.ttm_stage || s.current_stage || '未评估',
        risk_level: parseRisk(s.risk_level ?? s.latest_risk),
        day_index: 0,
        micro_action_count: 0,
        last_contact_days: 999,
        active_text: '—',
      }))
    } catch { students.value = [] }
  }
}

async function onRefresh() { refreshing.value = true; await loadStudents(); refreshing.value = false }

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

function goDetail(id: number) {
  uni.navigateTo({ url: '/pages/coach/students/detail?id=' + id })
}

onMounted(() => { loadStudents() })
</script>

<style scoped>
.stu-page { min-height: 100vh; background: #F5F6FA; }
.stu-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); color: #fff; }
.stu-nav-back { font-size: 40rpx; padding: 16rpx; }
.stu-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.stu-nav-count { font-size: 24rpx; opacity: 0.8; padding: 16rpx; }

.stu-filter-bar { display: flex; padding: 16rpx 24rpx; gap: 12rpx; }
.stu-search { flex: 1; background: #fff; border-radius: 12rpx; padding: 14rpx 20rpx; font-size: 28rpx; }
.stu-sort { background: #fff; border-radius: 12rpx; padding: 14rpx 20rpx; font-size: 26rpx; color: #3498DB; white-space: nowrap; }

.stu-stage-bar { white-space: nowrap; padding: 0 24rpx 16rpx; }
.stu-stage-tag { display: inline-block; padding: 10rpx 24rpx; border-radius: 24rpx; background: #fff; font-size: 24rpx; color: #5B6B7F; margin-right: 12rpx; }
.stu-stage-tag--active { background: #2D8E69; color: #fff; }

.stu-list { height: calc(100vh - 420rpx); padding: 0 24rpx; }
.stu-card { display: flex; align-items: center; justify-content: space-between; background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 12rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.03); }
.stu-card-left { display: flex; align-items: center; gap: 16rpx; flex: 1; }
.stu-avatar { width: 72rpx; height: 72rpx; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 28rpx; font-weight: 600; flex-shrink: 0; }
.stu-card-info { flex: 1; }
.stu-card-name { display: block; font-size: 30rpx; font-weight: 600; color: #2C3E50; }
.stu-card-meta { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.stu-card-right { display: flex; flex-direction: column; align-items: flex-end; gap: 8rpx; }
.stu-risk-tag { padding: 4rpx 16rpx; border-radius: 8rpx; font-size: 22rpx; font-weight: 700; }
.stu-card-active { font-size: 22rpx; color: #8E99A4; }

.stu-empty { text-align: center; padding: 120rpx 0; }
.stu-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.stu-empty-text { font-size: 28rpx; color: #8E99A4; }
</style>