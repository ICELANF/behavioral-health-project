<template>
  <view class="bg-page">
    <view class="bg-navbar">
      <view class="bg-back" @tap="goBack">←</view>
      <text class="bg-title">血糖记录</text>
      <view style="width:80rpx;"></view>
    </view>

    <scroll-view scroll-y class="bg-scroll">
      <!-- 最新血糖 -->
      <view class="bg-latest-card">
        <text class="bg-latest-label">最新血糖值</text>
        <text class="bg-latest-val" :style="{ color: latestColor }">{{ latestGlucose ?? '—' }}</text>
        <text class="bg-latest-unit">mmol/L</text>
        <text class="bg-latest-status" :style="{ color: latestColor }">{{ latestStatus }}</text>
        <text class="bg-latest-time">{{ latestTime }}</text>
      </view>

      <!-- 手动录入 -->
      <view class="bg-entry-card">
        <text class="bg-entry-title">📝 手动录入</text>
        <view class="bg-entry-row">
          <view class="bg-entry-field">
            <text class="bg-field-label">血糖值 (mmol/L)</text>
            <input class="bg-field-input" type="digit" v-model="form.value" placeholder="如: 5.6" maxlength="5" />
          </view>
          <view class="bg-entry-field">
            <text class="bg-field-label">测量时机</text>
            <picker :range="mealTimes" :value="mealTimeIdx" @change="mealTimeIdx = $event.detail.value">
              <view class="bg-field-picker">{{ mealTimes[mealTimeIdx] }}</view>
            </picker>
          </view>
        </view>
        <view class="bg-entry-row">
          <view class="bg-entry-field" style="flex:1;">
            <text class="bg-field-label">备注（选填）</text>
            <input class="bg-field-input" v-model="form.note" placeholder="如: 饭后2小时" maxlength="50" />
          </view>
        </view>
        <view class="bg-submit-btn" :class="{ 'bg-submit-btn--loading': submitting }" @tap="submitReading">
          {{ submitting ? '保存中…' : '保存记录' }}
        </view>
      </view>

      <!-- 历史趋势 -->
      <view class="bg-history-card">
        <view class="bg-history-header">
          <text class="bg-history-title">📊 近7天记录</text>
          <view class="bg-tab-row">
            <view v-for="r in rangeOpts" :key="r.key" class="bg-tab" :class="{ 'bg-tab--active': range === r.key }" @tap="range = r.key; loadHistory()">{{ r.label }}</view>
          </view>
        </view>
        <view v-if="history.length > 0">
          <view v-for="item in history" :key="item.id" class="bg-hist-item">
            <view class="bg-hist-dot" :style="{ background: glucoseColor(item.value) }"></view>
            <view class="bg-hist-body">
              <text class="bg-hist-val" :style="{ color: glucoseColor(item.value) }">{{ item.value?.toFixed(1) }} mmol/L</text>
              <text class="bg-hist-meta">{{ item.meal_context || '未知时机' }} · {{ formatTime(item.measured_at || item.recorded_at) }}</text>
            </view>
            <text class="bg-hist-status" :style="{ color: glucoseColor(item.value) }">{{ glucoseLabel(item.value) }}</text>
          </view>
        </view>
        <view v-else class="bg-empty">
          <text>暂无血糖记录</text>
        </view>
      </view>

      <!-- 参考范围说明 -->
      <view class="bg-ref-card">
        <text class="bg-ref-title">📋 参考范围</text>
        <view class="bg-ref-row"><view class="bg-ref-dot" style="background:#27AE60;"></view><text>空腹正常: 3.9 — 6.1 mmol/L</text></view>
        <view class="bg-ref-row"><view class="bg-ref-dot" style="background:#3498DB;"></view><text>餐后2h正常: ≤ 7.8 mmol/L</text></view>
        <view class="bg-ref-row"><view class="bg-ref-dot" style="background:#E67E22;"></view><text>餐后2h偏高: 7.8 — 10.0</text></view>
        <view class="bg-ref-row"><view class="bg-ref-dot" style="background:#E74C3C;"></view><text>高血糖: > 10.0 mmol/L</text></view>
      </view>

      <view style="height:120rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const mealTimes = ['空腹', '早餐前', '早餐后2h', '午餐前', '午餐后2h', '晚餐前', '晚餐后2h', '睡前', '随机']
const mealTimeIdx = ref(0)
const rangeOpts = [{ key:'7d', label:'7天' }, { key:'30d', label:'30天' }]
const range = ref('7d')
const form = ref({ value: '', note: '' })
const submitting = ref(false)
const history = ref<any[]>([])
const latestGlucose = ref<number|null>(null)
const latestTime = ref('')

const latestColor = computed(() => glucoseColor(latestGlucose.value ?? 0))
const latestStatus = computed(() => glucoseLabel(latestGlucose.value ?? 0))

function glucoseColor(v: number): string {
  if (!v) return '#8E99A4'
  if (v < 3.9 || v > 10) return '#E74C3C'
  if (v > 7.8) return '#E67E22'
  return '#27AE60'
}
function glucoseLabel(v: number): string {
  if (!v) return '—'
  if (v < 3.9) return '低血糖'
  if (v > 10) return '高血糖'
  if (v > 7.8) return '偏高'
  return '正常'
}
function formatTime(t: string): string {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN', { month:'numeric', day:'numeric', hour:'2-digit', minute:'2-digit' })
}

async function loadHistory() {
  try {
    const days = range.value === '30d' ? 30 : 7
    const res = await http<any>(`/api/v1/health-data/glucose?days=${days}&limit=50`)
    const items = res.readings || res.items || (Array.isArray(res) ? res : [])
    history.value = items
    if (items.length > 0) {
      latestGlucose.value = items[0].value
      latestTime.value = formatTime(items[0].measured_at || items[0].recorded_at)
    }
  } catch {}
}

async function submitReading() {
  const v = parseFloat(form.value.value)
  if (!v || v < 1 || v > 30) {
    uni.showToast({ title: '请输入有效血糖值(1-30)', icon: 'none' }); return
  }
  if (submitting.value) return
  submitting.value = true
  try {
    await http('/api/v1/health-data/glucose', {
      method: 'POST',
      data: {
        value: v,
        unit: 'mmol/L',
        meal_context: mealTimes[mealTimeIdx.value],
        notes: form.value.note || null,
        measured_at: new Date().toISOString(),
      },
    })
    form.value = { value: '', note: '' }
    mealTimeIdx.value = 0
    uni.showToast({ title: '记录成功', icon: 'success' })
    await loadHistory()
  } catch {
    uni.showToast({ title: '保存失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.navigateTo({ url: '/pages/health/index' })
}

onMounted(() => loadHistory())
</script>

<style scoped>
.bg-page { min-height: 100vh; background: #F5F6FA; }
.bg-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #C0392B 0%, #E74C3C 100%); color: #fff; }
.bg-back  { font-size: 40rpx; padding: 16rpx; }
.bg-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.bg-scroll { height: calc(100vh - 180rpx); }

.bg-latest-card { margin: 24rpx; background: linear-gradient(135deg, #C0392B, #E74C3C); border-radius: 20rpx; padding: 40rpx; text-align: center; color: #fff; }
.bg-latest-label { display: block; font-size: 24rpx; opacity: 0.8; margin-bottom: 12rpx; }
.bg-latest-val   { display: block; font-size: 80rpx; font-weight: 800; }
.bg-latest-unit  { display: block; font-size: 24rpx; opacity: 0.7; }
.bg-latest-status { display: block; font-size: 28rpx; font-weight: 600; margin-top: 8rpx; }
.bg-latest-time  { display: block; font-size: 22rpx; opacity: 0.7; margin-top: 8rpx; }

.bg-entry-card { margin: 0 24rpx 24rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
.bg-entry-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; margin-bottom: 20rpx; }
.bg-entry-row { display: flex; gap: 16rpx; margin-bottom: 16rpx; }
.bg-entry-field { flex: 1; }
.bg-field-label  { display: block; font-size: 22rpx; color: #8E99A4; margin-bottom: 8rpx; }
.bg-field-input  { width: 100%; background: #F5F6FA; border-radius: 12rpx; padding: 18rpx 20rpx; font-size: 28rpx; box-sizing: border-box; }
.bg-field-picker { background: #F5F6FA; border-radius: 12rpx; padding: 18rpx 20rpx; font-size: 28rpx; color: #2C3E50; }
.bg-submit-btn { margin-top: 8rpx; background: #E74C3C; color: #fff; text-align: center; padding: 26rpx 0; border-radius: 16rpx; font-size: 30rpx; font-weight: 600; }
.bg-submit-btn--loading { background: #F9A8A8; }

.bg-history-card { margin: 0 24rpx 24rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
.bg-history-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20rpx; }
.bg-history-title { font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.bg-tab-row { display: flex; gap: 8rpx; }
.bg-tab { padding: 8rpx 20rpx; border-radius: 20rpx; font-size: 22rpx; color: #8E99A4; background: #F5F6FA; }
.bg-tab--active { background: #E74C3C; color: #fff; }

.bg-hist-item { display: flex; align-items: center; gap: 16rpx; padding: 16rpx 0; border-bottom: 1rpx solid #F8F8F8; }
.bg-hist-item:last-child { border-bottom: none; }
.bg-hist-dot  { width: 16rpx; height: 16rpx; border-radius: 50%; flex-shrink: 0; }
.bg-hist-body { flex: 1; }
.bg-hist-val  { display: block; font-size: 30rpx; font-weight: 600; }
.bg-hist-meta { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.bg-hist-status { font-size: 22rpx; font-weight: 600; }

.bg-ref-card { margin: 0 24rpx 24rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
.bg-ref-title { display: block; font-size: 26rpx; font-weight: 600; color: #2C3E50; margin-bottom: 16rpx; }
.bg-ref-row   { display: flex; align-items: center; gap: 12rpx; margin-bottom: 10rpx; font-size: 24rpx; color: #5B6B7F; }
.bg-ref-dot   { width: 16rpx; height: 16rpx; border-radius: 50%; flex-shrink: 0; }

.bg-empty { text-align: center; padding: 48rpx; font-size: 26rpx; color: #8E99A4; }
</style>
