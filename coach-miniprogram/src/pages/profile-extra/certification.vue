<template>
  <view class="cert-page">
    <view class="cert-header">
      <text class="cert-title">我的认证</text>
      <text class="cert-sub">教练培养体系认证记录</text>
    </view>

    <scroll-view scroll-y class="cert-scroll" refresher-enabled
      @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <!-- 当前级别 -->
      <view class="cert-level-card">
        <view class="cert-level-icon">{{ levelIcon(currentLevel) }}</view>
        <view class="cert-level-info">
          <text class="cert-level-name">{{ levelName(currentLevel) }}</text>
          <text class="cert-level-desc">当前平台角色</text>
        </view>
        <view class="cert-go-exam" @tap="goExam"><text>参加考试</text></view>
      </view>

      <!-- 认证历史 -->
      <view class="cert-section-title">认证记录</view>
      <view class="cert-list">
        <view v-for="c in certs" :key="c.id" class="cert-item">
          <view class="cert-item-icon">🏆</view>
          <view class="cert-item-body">
            <text class="cert-item-name">{{ c.name || c.cert_name }}</text>
            <text class="cert-item-date">{{ formatDate(c.issued_at || c.created_at) }}</text>
          </view>
          <view class="cert-item-badge" :class="c.valid ? 'cert-badge--valid' : 'cert-badge--exp'">
            {{ c.valid ? '有效' : '已过期' }}
          </view>
        </view>
      </view>

      <view v-if="certs.length === 0 && !loading" class="cert-empty">
        <text class="cert-empty-icon">🏆</text>
        <text class="cert-empty-text">还没有认证记录</text>
        <view class="cert-go-exam-btn" @tap="goExam"><text>去参加考试</text></view>
      </view>

      <view style="height:80rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const certs = ref<any[]>([])
const currentLevel = ref('observer')
const refreshing = ref(false)
const loading = ref(false)

const levelIcons: Record<string, string> = { observer:'👁', grower:'🌱', sharer:'🤝', guide:'🧭', master:'⭐' }
const levelNames: Record<string, string> = { observer:'观察者', grower:'成长者', sharer:'分享者', guide:'向导者', master:'大师' }
function levelIcon(k: string) { return levelIcons[k] || '🌱' }
function levelName(k: string) { return levelNames[k] || k }

function formatDate(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

async function loadData() {
  loading.value = true
  // 优先从本地缓存读取角色（避免额外请求）
  try {
    const stored = uni.getStorageSync('user_info')
    const u = stored ? (typeof stored === 'string' ? JSON.parse(stored) : stored) : null
    if (u?.role) currentLevel.value = u.role
  } catch {}

  try {
    const [meRes, certRes] = await Promise.allSettled([
      http<any>('/api/v1/auth/me'),
      http<any>('/api/v1/certification/sessions/my'),
    ])
    if (meRes.status === 'fulfilled' && meRes.value?.role) {
      currentLevel.value = meRes.value.role
    }
    if (certRes.status === 'fulfilled') {
      certs.value = (certRes.value?.items || []).filter((c: any) => c.passed)
    }
  } finally { loading.value = false }
}

function goExam() { uni.navigateTo({ url: '/pages/exam/index' }) }

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }
onMounted(() => { loadData() })
</script>

<style scoped>
.cert-page { min-height: 100vh; background: #F5F6FA; }
.cert-header { padding: 24rpx 32rpx; padding-top: calc(80rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); color: #fff; }
.cert-title { display: block; font-size: 38rpx; font-weight: 700; }
.cert-sub { display: block; font-size: 24rpx; opacity: 0.85; margin-top: 6rpx; }
.cert-scroll { height: calc(100vh - 200rpx); }
.cert-level-card { display: flex; align-items: center; gap: 16rpx; background: #fff; margin: 24rpx; border-radius: 16rpx; padding: 24rpx; box-shadow: 0 4rpx 16rpx rgba(45,142,105,0.1); }
.cert-level-icon { font-size: 56rpx; }
.cert-level-info { flex: 1; }
.cert-level-name { display: block; font-size: 32rpx; font-weight: 700; color: #2C3E50; }
.cert-level-desc { font-size: 22rpx; color: #8E99A4; }
.cert-go-exam { background: #2D8E69; color: #fff; border-radius: 12rpx; padding: 10rpx 20rpx; font-size: 24rpx; }
.cert-section-title { font-size: 22rpx; color: #8E99A4; padding: 0 32rpx 12rpx; }
.cert-list { background: #fff; margin: 0 24rpx 16rpx; border-radius: 16rpx; }
.cert-item { display: flex; align-items: center; gap: 16rpx; padding: 20rpx 24rpx; border-bottom: 1rpx solid #F8F8F8; }
.cert-item:last-child { border-bottom: none; }
.cert-item-icon { font-size: 36rpx; }
.cert-item-body { flex: 1; }
.cert-item-name { display: block; font-size: 26rpx; font-weight: 600; color: #2C3E50; }
.cert-item-date { font-size: 20rpx; color: #8E99A4; }
.cert-item-badge { font-size: 20rpx; padding: 4rpx 12rpx; border-radius: 8rpx; }
.cert-badge--valid { background: #E8F8F0; color: #2D8E69; }
.cert-badge--exp { background: #F5F5F5; color: #8E99A4; }
.cert-empty { text-align: center; padding: 80rpx 0; }
.cert-empty-icon { display: block; font-size: 64rpx; margin-bottom: 16rpx; }
.cert-empty-text { display: block; font-size: 26rpx; color: #8E99A4; margin-bottom: 32rpx; }
.cert-go-exam-btn { display: inline-block; padding: 16rpx 48rpx; background: #2D8E69; color: #fff; border-radius: 16rpx; font-size: 28rpx; }
</style>
