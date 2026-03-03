<template>
  <view class="wd-page">
    <!-- 顶部 -->
    <view class="wd-hero">
      <view class="wd-hero-left">
        <text class="wd-hero-title">教练工作台</text>
        <text class="wd-hero-date">{{ todayStr }}</text>
      </view>
      <view class="wd-hero-avatar" :style="{ background: avatarBg }">
        {{ coachInitial }}
      </view>
    </view>

    <scroll-view scroll-y class="wd-scroll" refresher-enabled
      @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <!-- 核心数值行 -->
      <view class="wd-kpi-row">
        <view class="wd-kpi" @tap="nav('/pages/coach/students/index')">
          <text class="wd-kpi-n">{{ ts.total_students || students.length || 0 }}</text>
          <text class="wd-kpi-l">学员</text>
        </view>
        <view class="wd-kpi wd-kpi--warn" @tap="nav('/pages/coach/risk/index')">
          <text class="wd-kpi-n">{{ ts.alert_students || 0 }}</text>
          <text class="wd-kpi-l">高风险</text>
        </view>
        <view class="wd-kpi wd-kpi--blue" @tap="nav('/pages/coach/assessment/index')">
          <text class="wd-kpi-n">{{ ts.pending_followups || 0 }}</text>
          <text class="wd-kpi-l">待跟进</text>
        </view>
        <view class="wd-kpi wd-kpi--purple" @tap="nav('/pages/coach/push-queue/index')">
          <text class="wd-kpi-n">{{ ts.messages_sent || 0 }}</text>
          <text class="wd-kpi-l">今日消息</text>
        </view>
      </view>

      <!-- 工具快捷入口 -->
      <view class="wd-section">
        <text class="wd-section-title">工具入口</text>
        <view class="wd-tools">
          <view v-for="t in tools" :key="t.url" class="wd-tool" @tap="nav(t.url)">
            <view class="wd-tool-icon" :style="{ background: t.bg }">{{ t.icon }}</view>
            <text class="wd-tool-label">{{ t.label }}</text>
          </view>
        </view>
      </view>

      <!-- 学员列表快览 -->
      <view class="wd-section">
        <view class="wd-section-head">
          <text class="wd-section-title">学员概况</text>
          <text class="wd-section-more" @tap="nav('/pages/coach/students/index')">全部 ›</text>
        </view>
        <view class="wd-student-list">
          <view v-for="s in students.slice(0, 6)" :key="s.id" class="wd-student-row"
            @tap="nav('/pages/coach/students/detail?id=' + s.id)">
            <view class="wd-s-avatar" :style="{ background: avatarColor(s.name || s.full_name) }">
              {{ (s.name || s.full_name || '?')[0] }}
            </view>
            <view class="wd-s-info">
              <text class="wd-s-name">{{ s.name || s.full_name || s.username || '学员' }}</text>
              <text class="wd-s-sub">{{ stageName(s.stage || s.current_stage) }} · {{ s.days_since_last_contact != null ? s.days_since_last_contact + '天未联系' : '活跃中' }}</text>
            </view>
            <view class="wd-s-risk" :class="riskClass(s.risk_level || s.latest_risk)">
              {{ riskLabel(s.risk_level || s.latest_risk) }}
            </view>
          </view>
          <view v-if="students.length === 0 && !loading" class="wd-empty">
            <text>暂无学员数据</text>
          </view>
        </view>
      </view>

      <!-- 干预统计 -->
      <view class="wd-section">
        <text class="wd-section-title">服务数据</text>
        <view class="wd-stats-grid">
          <view class="wd-stat-cell">
            <text class="wd-stat-n">{{ coach.total_days || 0 }}</text>
            <text class="wd-stat-l">服务天数</text>
          </view>
          <view class="wd-stat-cell">
            <text class="wd-stat-n">{{ ts.total_interventions || 0 }}</text>
            <text class="wd-stat-l">干预次数</text>
          </view>
          <view class="wd-stat-cell">
            <text class="wd-stat-n">{{ ts.assessments_reviewed || 0 }}</text>
            <text class="wd-stat-l">评审完成</text>
          </view>
          <view class="wd-stat-cell">
            <text class="wd-stat-n">{{ ts.pending_followups || 0 }}</text>
            <text class="wd-stat-l">待跟进</text>
          </view>
        </view>
      </view>

      <view style="height:80rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const coach = ref<any>({})
const ts = ref<any>({})
const students = ref<any[]>([])
const refreshing = ref(false)
const loading = ref(false)
const coachName = ref('教练')

const coachInitial = computed(() => (coachName.value || '教')[0])
const avatarBg = computed(() => {
  const colors = ['#2D8E69','#3498DB','#9B59B6','#E67E22']
  let h = 0; for (const c of coachName.value) h = c.charCodeAt(0) + ((h << 5) - h)
  return colors[Math.abs(h) % colors.length]
})

const todayStr = computed(() => {
  const d = new Date()
  const w = ['日','一','二','三','四','五','六'][d.getDay()]
  return `${d.getMonth()+1}月${d.getDate()}日 周${w}`
})

const tools = [
  { icon: '👥', label: '我的学员', url: '/pages/coach/students/index', bg: '#EEF6FF' },
  { icon: '📊', label: '评估管理', url: '/pages/coach/assessment/index', bg: '#F0FBF6' },
  { icon: '🔄', label: 'AI飞轮', url: '/pages/coach/flywheel/index', bg: '#FFF8EE' },
  { icon: '📈', label: '数据分析', url: '/pages/coach/analytics/index', bg: '#EEF6FF' },
  { icon: '📤', label: '推送队列', url: '/pages/coach/push-queue/index', bg: '#F0FBF6' },
  { icon: '🛡️', label: '风险管理', url: '/pages/coach/risk/index', bg: '#FFF2F2' },
  { icon: '📡', label: '直播中心', url: '/pages/coach/live/index', bg: '#FFF8EE' },
  { icon: '💬', label: '消息', url: '/pages/coach/messages/index', bg: '#F5F0FF' },
]

const colorPool = ['#3498DB','#E74C3C','#27AE60','#9B59B6','#E67E22','#1ABC9C']
function avatarColor(name: string): string {
  if (!name) return '#8E99A4'
  let h = 0; for (const c of name) h = c.charCodeAt(0) + ((h << 5) - h)
  return colorPool[Math.abs(h) % colorPool.length]
}

function stageName(s: string): string {
  const m: Record<string,string> = { S1:'准备期', S2:'行动期', S3:'维持期', S4:'深化期', contemplation:'沉思期', preparation:'准备期', action:'行动期', maintenance:'维持期' }
  return m[s] || s || '—'
}

function riskLabel(r: string): string {
  const m: Record<string,string> = { high:'高', moderate:'中', low:'低', R1:'R1', R2:'R2', R3:'R3', R4:'R4' }
  return m[r] || r || '—'
}

function riskClass(r: string): string {
  if (r === 'high' || r === 'R3' || r === 'R4') return 'wd-s-risk--high'
  if (r === 'moderate' || r === 'R2') return 'wd-s-risk--mid'
  return 'wd-s-risk--low'
}

async function loadData() {
  loading.value = true
  try {
    const raw = uni.getStorageSync('user_info')
    if (raw) {
      const u = typeof raw === 'string' ? JSON.parse(raw) : raw
      coachName.value = u.full_name || u.username || '教练'
    }
  } catch (e) { console.warn('[coach/dashboard/index] loadData:', e) }
  try {
    const dash = await http<any>('/api/v1/coach/dashboard')
    coach.value = dash?.coach || {}
    ts.value = dash?.today_stats || {}
    students.value = dash?.students || []
  } catch (e) { console.warn('[coach/dashboard/index] dashboard:', e) } finally { loading.value = false }
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }
function nav(url: string) { uni.navigateTo({ url }) }
onMounted(() => { loadData() })
</script>

<style scoped>
.wd-page { min-height: 100vh; background: #F5F6FA; }

.wd-hero { display: flex; justify-content: space-between; align-items: flex-end; padding: 24rpx 32rpx; padding-top: calc(60rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); color: #fff; }
.wd-hero-title { display: block; font-size: 38rpx; font-weight: 700; }
.wd-hero-date { display: block; font-size: 24rpx; opacity: 0.85; margin-top: 4rpx; }
.wd-hero-avatar { width: 80rpx; height: 80rpx; border-radius: 50%; color: #fff; font-size: 32rpx; font-weight: 700; display: flex; align-items: center; justify-content: center; border: 4rpx solid rgba(255,255,255,0.5); }

.wd-scroll { height: calc(100vh - 180rpx); }

/* KPI row */
.wd-kpi-row { display: flex; background: #fff; margin: 20rpx 24rpx; border-radius: 20rpx; box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.05); overflow: hidden; }
.wd-kpi { flex: 1; padding: 24rpx 0; text-align: center; border-right: 1rpx solid #F0F0F0; position: relative; }
.wd-kpi:last-child { border-right: none; }
.wd-kpi::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 6rpx; background: #2D8E69; }
.wd-kpi--warn::before { background: #E74C3C; }
.wd-kpi--blue::before { background: #3498DB; }
.wd-kpi--purple::before { background: #9B59B6; }
.wd-kpi-n { display: block; font-size: 44rpx; font-weight: 800; color: #2C3E50; }
.wd-kpi-l { display: block; font-size: 20rpx; color: #8E99A4; margin-top: 4rpx; }

/* Section */
.wd-section { background: #fff; margin: 0 24rpx 20rpx; border-radius: 20rpx; padding: 24rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.03); }
.wd-section-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20rpx; }
.wd-section-title { font-size: 30rpx; font-weight: 700; color: #2C3E50; margin-bottom: 16rpx; display: block; }
.wd-section-more { font-size: 24rpx; color: #3498DB; }

/* Tools */
.wd-tools { display: flex; flex-wrap: wrap; gap: 20rpx; }
.wd-tool { width: calc(25% - 15rpx); display: flex; flex-direction: column; align-items: center; gap: 8rpx; }
.wd-tool-icon { width: 88rpx; height: 88rpx; border-radius: 20rpx; display: flex; align-items: center; justify-content: center; font-size: 36rpx; }
.wd-tool-label { font-size: 20rpx; color: #5B6B7F; text-align: center; }

/* Student list */
.wd-student-list { }
.wd-student-row { display: flex; align-items: center; gap: 16rpx; padding: 16rpx 0; border-bottom: 1rpx solid #F8F8F8; }
.wd-student-row:last-child { border-bottom: none; }
.wd-s-avatar { width: 72rpx; height: 72rpx; border-radius: 50%; color: #fff; font-size: 28rpx; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.wd-s-info { flex: 1; }
.wd-s-name { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.wd-s-sub { font-size: 20rpx; color: #8E99A4; margin-top: 4rpx; }
.wd-s-risk { font-size: 20rpx; padding: 4rpx 12rpx; border-radius: 8rpx; font-weight: 600; }
.wd-s-risk--high { background: #FDF0F0; color: #E74C3C; }
.wd-s-risk--mid { background: #FFF8EE; color: #E67E22; }
.wd-s-risk--low { background: #EFF9F4; color: #27AE60; }

/* Stats grid */
.wd-stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16rpx; }
.wd-stat-cell { background: #F8F9FA; border-radius: 16rpx; padding: 20rpx; text-align: center; }
.wd-stat-n { display: block; font-size: 44rpx; font-weight: 800; color: #2D8E69; }
.wd-stat-l { font-size: 22rpx; color: #8E99A4; margin-top: 6rpx; }

.wd-empty { text-align: center; padding: 40rpx 0; font-size: 26rpx; color: #8E99A4; }
</style>
