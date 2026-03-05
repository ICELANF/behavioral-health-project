<template>
  <view class="bs-page">
    <!-- 自定义导航 -->
    <view class="bs-nav">
      <view class="bs-nav-back" @tap="goBack">‹</view>
      <text class="bs-nav-title">成为分享者</text>
    </view>

    <scroll-view scroll-y class="bs-scroll">
      <view v-if="loading" class="bs-loading"><text>加载中…</text></view>

      <template v-else>
        <!-- Hero -->
        <view class="bs-hero">
          <text class="bs-hero-icon">🌟</text>
          <text class="bs-hero-title">申请成为分享者</text>
          <text class="bs-hero-desc">分享者是平台成长社区的核心力量。你的亲身经历、收获与洞见，将照亮更多同道者的成长之路。</text>
        </view>

        <!-- 四维资质 -->
        <view class="section-card">
          <text class="section-title">资质检验</text>
          <view class="dim-list">
            <view v-for="dim in dims" :key="dim.key" class="dim-item">
              <view class="dim-check" :class="{ 'dim-check--done': dim.done }">
                <text>{{ dim.done ? '✓' : '○' }}</text>
              </view>
              <view class="dim-body">
                <text class="dim-name">{{ dim.name }}</text>
                <text class="dim-desc">{{ dim.desc }}</text>
                <text v-if="!dim.done" class="dim-action" @tap="goPage(dim.route)">→ {{ dim.actionLabel }}</text>
              </view>
              <view class="dim-status" :class="dim.done ? 'status-done' : 'status-pending'">
                <text>{{ dim.done ? '达标' : '进行中' }}</text>
              </view>
            </view>
          </view>
        </view>

        <!-- 申请陈述 -->
        <view class="section-card">
          <text class="section-title">申请陈述</text>
          <view class="stmt-guide">
            <text class="stmt-guide-item">📝 我的主要收获：我在健康管理上得到了什么？</text>
            <text class="stmt-guide-item">🌱 我的成长证明：有哪些具体改变？</text>
            <text class="stmt-guide-item">🤝 我的贡献意愿：我能为其他人提供什么？</text>
          </view>
          <textarea
            v-model="statement"
            placeholder="写下你的申请陈述（至少50字）…"
            :maxlength="800"
            class="stmt-textarea"
            :auto-height="true"
            :show-confirm-bar="false"
          />
          <text class="stmt-count">{{ statement.length }}/800</text>
        </view>

        <!-- 申请历史 -->
        <view class="section-card" v-if="history.length">
          <text class="section-title">申请记录</text>
          <view v-for="h in history" :key="h.id" class="hist-item">
            <text class="hist-date">{{ formatDate(h.applied_at || h.created_at) }}</text>
            <view class="hist-status" :class="'hist-status--' + h.status">
              <text>{{ statusLabel(h.status) }}</text>
            </view>
          </view>
        </view>

        <!-- 底部占位 -->
        <view style="height:200rpx;"></view>
      </template>
    </scroll-view>

    <!-- 固定底部 -->
    <view class="bs-footer" v-if="!loading">
      <view class="dim-summary">
        <text>{{ readyCount }}/4 维度达标</text>
        <text v-if="readyCount < 4" class="dim-hint">（未达标维度继续积累，可先提交申请）</text>
      </view>
      <view
        class="submit-btn"
        :class="{ 'submit-btn--disabled': statement.trim().length < 50 || submitting }"
        @tap="submitApplication"
      >
        <text>{{ submitting ? '提交中…' : '提交申请' }}</text>
      </view>
      <text class="submit-hint">提交后教练将在3个工作日内审核</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

interface DimStatus {
  reflection: boolean
  growth: boolean
  caseStory: boolean
  trajectory: boolean
}

interface HistoryItem {
  id: number
  applied_at?: string
  created_at?: string
  status: string
}

const loading = ref(true)
const submitting = ref(false)
const statement = ref('')
const history = ref<HistoryItem[]>([])

const dimStatus = ref<DimStatus>({
  reflection: false,
  growth: false,
  caseStory: false,
  trajectory: false,
})

const dims = computed(() => [
  {
    key: 'reflection',
    name: '自我收获',
    desc: '已写下至少1篇成长感悟，记录你的收获与洞见',
    done: dimStatus.value.reflection,
    route: '/pages/reflection/index',
    actionLabel: '去写成长感悟',
  },
  {
    key: 'growth',
    name: '在途成长',
    desc: 'TTM行为改变阶段处于S2(沉思)或以上，正在积极改变',
    done: dimStatus.value.growth,
    route: '/pages/assessment/pending',
    actionLabel: '完成行为评估',
  },
  {
    key: 'caseStory',
    name: '持续感悟',
    desc: '至少写过3篇成长感悟，展示持续记录与分享的意愿',
    done: dimStatus.value.caseStory,
    route: '/pages/reflection/index',
    actionLabel: '去写成长感悟',
  },
  {
    key: 'trajectory',
    name: '行为轨迹',
    desc: '综合成长分≥60，依从率≥50%，连续打卡≥3天',
    done: dimStatus.value.trajectory,
    route: '/pages/trajectory/index',
    actionLabel: '查看行为轨迹',
  },
])

const readyCount = computed(() => dims.value.filter(d => d.done).length)

function formatDate(iso?: string) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('zh-CN')
}

function statusLabel(s: string) {
  return ({ pending: '审核中', approved: '已通过', rejected: '未通过' } as Record<string, string>)[s] || s
}

function goPage(url: string) {
  uni.navigateTo({ url })
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) {
    uni.navigateBack()
  } else {
    uni.reLaunch({ url: '/home/index' })
  }
}

async function loadData() {
  loading.value = true
  const [reflectRes, journeyRes, trajRes, histRes] = await Promise.allSettled([
    http<any>('/api/v1/reflection/stats'),
    http<any>('/api/v1/journey/overview'),
    http<any>('/api/v1/learning/trajectory?days=30'),
    http<any>('/api/v1/promotion/my-history'),
  ])

  if (reflectRes.status === 'fulfilled') {
    const r = reflectRes.value as any
    const total = r.total_entries ?? r.count ?? 0
    dimStatus.value.reflection = total >= 1
    dimStatus.value.caseStory  = total >= 3   // 持续感悟：至少3篇
  }
  if (journeyRes.status === 'fulfilled') {
    const j = journeyRes.value as any
    const stage = j.current_level ?? j.ttm_stage ?? j.stage ?? 0
    dimStatus.value.growth = typeof stage === 'number'
      ? stage >= 2
      : parseInt(String(stage).replace(/\D/g, '') || '0') >= 2
  }
  if (trajRes.status === 'fulfilled') {
    const t = trajRes.value as any
    dimStatus.value.trajectory = t.qualifies_for_sharer === true
  }
  if (histRes.status === 'fulfilled') {
    const h = histRes.value as any
    history.value = Array.isArray(h) ? h : (h?.items || h?.history || [])
  }

  loading.value = false
}

async function submitApplication() {
  if (statement.value.trim().length < 50 || submitting.value) return
  submitting.value = true
  try {
    await http<any>('/api/v1/promotion/sharer-apply', {
      method: 'POST',
      data: {
        statement: statement.value.trim(),
        target_role: 'sharer',
        dim_ready: readyCount.value,
      },
    })
    uni.showToast({ title: '申请已提交，等待审核', icon: 'success' })
    statement.value = ''
    loadData()
  } catch {
    uni.showToast({ title: '提交失败，请稍后重试', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

onMounted(() => loadData())
</script>

<style scoped>
.bs-page { min-height: 100vh; background: #f7f8fa; }

.bs-nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  height: 88rpx; padding-top: env(safe-area-inset-top);
  background: linear-gradient(135deg, #ede9fe 0%, #dbeafe 100%);
  display: flex; align-items: center; padding-left: 28rpx;
}
.bs-nav-back { color: #5b21b6; font-size: 48rpx; padding-right: 16rpx; line-height: 1; }
.bs-nav-title { color: #1e1b4b; font-size: 32rpx; font-weight: 700; }
.bs-scroll {
  position: fixed; top: calc(88rpx + env(safe-area-inset-top));
  bottom: 0; left: 0; right: 0;
}
.bs-loading { text-align: center; padding: 80rpx 0; color: #999; font-size: 28rpx; }

/* Hero */
.bs-hero {
  background: linear-gradient(135deg, #ede9fe 0%, #dbeafe 100%);
  padding: 40rpx 32rpx 32rpx;
  text-align: center;
}
.bs-hero-icon { font-size: 80rpx; display: block; margin-bottom: 12rpx; }
.bs-hero-title { font-size: 40rpx; font-weight: 800; color: #1e1b4b; display: block; margin-bottom: 12rpx; }
.bs-hero-desc { font-size: 26rpx; color: #5b21b6; line-height: 1.6; display: block; }

/* 通用卡片 */
.section-card {
  background: #fff; margin: 20rpx 24rpx 0;
  padding: 28rpx 24rpx; border-radius: 20rpx;
  box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.05);
}
.section-title { font-size: 28rpx; font-weight: 700; color: #111; display: block; margin-bottom: 24rpx; }

/* 维度列表 */
.dim-list { display: flex; flex-direction: column; gap: 24rpx; }
.dim-item { display: flex; gap: 20rpx; align-items: flex-start; }
.dim-check {
  width: 48rpx; height: 48rpx; border-radius: 50%;
  border: 4rpx solid #d1d5db;
  display: flex; align-items: center; justify-content: center;
  font-size: 24rpx; color: #9ca3af; flex-shrink: 0;
}
.dim-check--done { background: #16a34a; border-color: #16a34a; color: #fff; font-weight: 700; }
.dim-body { flex: 1; }
.dim-name { font-size: 28rpx; font-weight: 700; color: #111; display: block; margin-bottom: 4rpx; }
.dim-desc { font-size: 24rpx; color: #6b7280; line-height: 1.4; display: block; }
.dim-action { font-size: 24rpx; color: #1565c0; display: block; margin-top: 8rpx; }
.dim-status {
  font-size: 22rpx; padding: 6rpx 16rpx; border-radius: 20rpx;
  flex-shrink: 0; font-weight: 600; margin-top: 4rpx;
}
.status-done { background: #dcfce7; color: #16a34a; }
.status-pending { background: #f3f4f6; color: #9ca3af; }

/* 申请陈述 */
.stmt-guide { margin-bottom: 20rpx; }
.stmt-guide-item { font-size: 24rpx; color: #6b7280; display: block; padding: 4rpx 0; }
.stmt-textarea {
  width: 100%; min-height: 200rpx; background: #f9fafb;
  border-radius: 16rpx; padding: 20rpx; font-size: 26rpx;
  color: #374151; line-height: 1.6; border: 2rpx solid #e5e7eb;
  box-sizing: border-box;
}
.stmt-count { font-size: 22rpx; color: #9ca3af; display: block; text-align: right; margin-top: 8rpx; }

/* 历史记录 */
.hist-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16rpx 0; border-bottom: 2rpx solid #f5f5f5;
}
.hist-item:last-child { border-bottom: none; }
.hist-date { font-size: 26rpx; color: #6b7280; }
.hist-status { font-size: 24rpx; padding: 4rpx 16rpx; border-radius: 20rpx; font-weight: 600; }
.hist-status--approved { background: #dcfce7; color: #16a34a; }
.hist-status--pending  { background: #fef3c7; color: #d97706; }
.hist-status--rejected { background: #fee2e2; color: #dc2626; }

/* 底部 */
.bs-footer {
  position: fixed; bottom: 0; left: 0; right: 0;
  background: #fff; padding: 20rpx 32rpx 40rpx;
  border-top: 2rpx solid #f0f0f0;
  box-shadow: 0 -4rpx 16rpx rgba(0,0,0,0.06);
}
.dim-summary { text-align: center; font-size: 26rpx; color: #6b7280; margin-bottom: 16rpx; }
.dim-hint { color: #9ca3af; }
.submit-btn {
  background: linear-gradient(135deg, #7c3aed, #1565c0);
  color: #fff; text-align: center; padding: 24rpx;
  border-radius: 50rpx; font-size: 30rpx; font-weight: 700;
}
.submit-btn--disabled { opacity: 0.4; }
.submit-hint { text-align: center; font-size: 22rpx; color: #9ca3af; display: block; margin-top: 12rpx; }
</style>
