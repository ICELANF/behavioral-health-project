<template>
  <view class="jh-page">
    <scroll-view scroll-y class="jh-scroll" refresher-enabled
      @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <view class="jh-list">
        <view v-for="item in records" :key="item.id" class="jh-card">
          <view class="jh-card-header">
            <view class="jh-status-dot" :class="'jh-dot--' + item.status" />
            <text class="jh-card-target">{{ levelName(item.target_level) }}</text>
            <view class="jh-status-badge" :class="'jh-badge--' + item.status">
              {{ statusLabel(item.status) }}
            </view>
          </view>
          <text class="jh-card-reason">{{ item.reason }}</text>
          <text class="jh-card-time">{{ formatDate(item.created_at) }}</text>
          <text v-if="item.review_comment" class="jh-card-comment">审核意见：{{ item.review_comment }}</text>
        </view>
      </view>

      <view v-if="records.length === 0 && !loading" class="jh-empty">
        <text class="jh-empty-icon">📜</text>
        <text class="jh-empty-text">暂无申请记录</text>
        <view class="jh-go-apply" @tap="goApply"><text>申请晋级</text></view>
      </view>

      <view style="height:80rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const BASE_URL = 'http://localhost:8000'
function getToken() { return uni.getStorageSync('access_token') || '' }

async function http<T = any>(url: string): Promise<T> {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url, method: 'GET',
      header: { 'Authorization': 'Bearer ' + getToken(), 'Content-Type': 'application/json' },
      success: (res: any) => {
        if (res.statusCode === 401) { uni.removeStorageSync('access_token'); uni.reLaunch({ url: '/pages/auth/login' }); reject(new Error('401')); return }
        res.statusCode < 300 ? resolve(res.data as T) : reject(new Error(`${res.statusCode}`))
      },
      fail: (e: any) => reject(e),
    })
  })
}

const records = ref<any[]>([])
const refreshing = ref(false)
const loading = ref(false)

const levels: Record<string, string> = { observer:'观察者', grower:'成长者', sharer:'分享者', guide:'向导者', master:'大师' }
function levelName(k: string) { return levels[k] || k }
function statusLabel(s: string) { return { pending:'审核中', approved:'已批准', rejected:'已驳回' }[s] || s }

async function loadData() {
  loading.value = true
  try {
    const res = await http<any>('/api/v1/journey/promotion/history')
    records.value = res?.items || []
  } catch { records.value = [] } finally { loading.value = false }
}

function formatDate(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}
function goApply() { uni.navigateTo({ url: '/pages/journey/promotion' }) }

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }
onMounted(() => { loadData() })
</script>

<style scoped>
.jh-page { min-height: 100vh; background: #F5F6FA; }
.jh-scroll { height: 100vh; }
.jh-list { padding: 16rpx 24rpx; }
.jh-card { background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 16rpx; }
.jh-card-header { display: flex; align-items: center; gap: 12rpx; margin-bottom: 12rpx; }
.jh-status-dot { width: 14rpx; height: 14rpx; border-radius: 50%; }
.jh-dot--pending { background: #E67E22; }
.jh-dot--approved { background: #2D8E69; }
.jh-dot--rejected { background: #E74C3C; }
.jh-card-target { flex: 1; font-size: 28rpx; font-weight: 700; color: #2C3E50; }
.jh-status-badge { font-size: 20rpx; padding: 4rpx 12rpx; border-radius: 8rpx; }
.jh-badge--pending { background: #FEF5E7; color: #E67E22; }
.jh-badge--approved { background: #E8F8F0; color: #2D8E69; }
.jh-badge--rejected { background: #FDEDEC; color: #E74C3C; }
.jh-card-reason { display: block; font-size: 24rpx; color: #5B6B7F; line-height: 1.6; margin-bottom: 8rpx; }
.jh-card-time { display: block; font-size: 20rpx; color: #8E99A4; }
.jh-card-comment { display: block; font-size: 22rpx; color: #E67E22; margin-top: 8rpx; padding: 8rpx; background: #FFF8E7; border-radius: 8rpx; }
.jh-empty { text-align: center; padding: 100rpx 0; }
.jh-empty-icon { display: block; font-size: 64rpx; margin-bottom: 16rpx; }
.jh-empty-text { display: block; font-size: 26rpx; color: #8E99A4; margin-bottom: 32rpx; }
.jh-go-apply { display: inline-block; padding: 16rpx 48rpx; background: #2D8E69; color: #fff; border-radius: 16rpx; font-size: 28rpx; }
</style>
