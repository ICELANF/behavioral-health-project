<template>
  <view class="ex-page">
    <view class="ex-navbar">
      <view class="ex-back" @tap="goBack">←</view>
      <text class="ex-title">运动记录</text>
      <view style="width:80rpx;"></view>
    </view>

    <scroll-view scroll-y class="ex-scroll">
      <!-- 今日概览 -->
      <view class="ex-today-card">
        <view class="ex-today-row">
          <view class="ex-today-item">
            <text class="ex-today-val" :style="{ color: stepsColor }">{{ todaySteps ?? '—' }}</text>
            <text class="ex-today-label">今日步数</text>
          </view>
          <view class="ex-today-item">
            <text class="ex-today-val" style="color:#E67E22;">{{ todayCalories ?? '—' }}</text>
            <text class="ex-today-label">消耗(kcal)</text>
          </view>
          <view class="ex-today-item">
            <text class="ex-today-val" style="color:#9B59B6;">{{ todayMinutes ?? '—' }}</text>
            <text class="ex-today-label">运动(分钟)</text>
          </view>
        </view>
        <!-- 步数进度环 -->
        <view class="ex-steps-bar">
          <view class="ex-steps-fill" :style="{ width: Math.min((todaySteps || 0) / 100, 100) + '%' }"></view>
        </view>
        <text class="ex-steps-hint">{{ stepsHint }}</text>
      </view>

      <!-- 微信步数授权 -->
      <view class="ex-werun-card" v-if="!werunAuthed">
        <text class="ex-werun-icon">👟</text>
        <text class="ex-werun-title">授权微信运动</text>
        <text class="ex-werun-desc">同步微信运动步数，无需额外设备，作为基础运动数据来源</text>
        <view class="ex-werun-btn" @tap="authorizeWeRun">授权微信步数</view>
      </view>
      <view class="ex-werun-synced" v-else @tap="syncWeRun">
        <text>✅ 已授权微信步数 · </text>
        <text style="color:#27AE60;">点击同步</text>
      </view>

      <!-- 穿戴设备（手表/手环）同步 -->
      <view class="ex-device-card">
        <text class="ex-device-title">📡 穿戴设备</text>
        <view v-if="watchDevice" class="ex-device-row" @tap="syncFromWatch">
          <text class="ex-device-icon-text">{{ watchDevice.device_type === 'smartwatch' ? '⌚' : '📿' }}</text>
          <view class="ex-device-info-col">
            <text class="ex-device-name">{{ watchDevice.manufacturer || '智能手表/手环' }}</text>
            <text class="ex-device-hint">{{ syncingWatch ? '同步中…' : '点击同步运动·心率·睡眠数据' }}</text>
          </view>
          <text class="ex-device-arrow">{{ syncingWatch ? '…' : '同步 ›' }}</text>
        </view>
        <view v-else class="ex-device-row ex-device-row--add" @tap="goDeviceBind">
          <text class="ex-device-icon-text">＋</text>
          <view class="ex-device-info-col">
            <text class="ex-device-name">绑定智能手表 / 手环</text>
            <text class="ex-device-hint">支持 Apple Watch、华为、小米手环、Fitbit 等</text>
          </view>
          <text class="ex-device-arrow">›</text>
        </view>
      </view>

      <!-- 手动录入运动 -->
      <view class="ex-entry-card">
        <text class="ex-entry-title">🏃 手动录入运动</text>
        <view class="ex-entry-row">
          <view class="ex-entry-field">
            <text class="ex-field-label">运动类型</text>
            <picker :range="exerciseTypes" :range-key="'name'" :value="typeIdx" @change="typeIdx = $event.detail.value">
              <view class="ex-field-picker">{{ exerciseTypes[typeIdx].name }}</view>
            </picker>
          </view>
          <view class="ex-entry-field">
            <text class="ex-field-label">时长(分钟)</text>
            <input class="ex-field-input" type="number" v-model="form.duration" placeholder="30" maxlength="3" />
          </view>
        </view>
        <view class="ex-entry-row">
          <view class="ex-entry-field">
            <text class="ex-field-label">消耗卡路里(选填)</text>
            <input class="ex-field-input" type="number" v-model="form.calories" placeholder="如: 200" maxlength="4" />
          </view>
          <view class="ex-entry-field">
            <text class="ex-field-label">心率峰值(选填)</text>
            <input class="ex-field-input" type="number" v-model="form.heart_rate_peak" placeholder="如: 145" maxlength="3" />
          </view>
        </view>
        <view class="ex-submit-btn" :class="{ 'ex-submit-btn--loading': submitting }" @tap="submitExercise">
          {{ submitting ? '保存中…' : '保存运动记录' }}
        </view>
      </view>

      <!-- 历史记录 -->
      <view class="ex-history-card">
        <text class="ex-history-title">📋 近期运动</text>
        <view v-if="history.length > 0">
          <view v-for="item in history" :key="item.id" class="ex-hist-item">
            <text class="ex-hist-icon">{{ typeIcon(item.activity_type || item.exercise_type) }}</text>
            <view class="ex-hist-body">
              <text class="ex-hist-name">{{ item.activity_type || item.exercise_type || '运动' }}</text>
              <text class="ex-hist-meta">{{ item.duration_minutes || item.duration }}分钟 · {{ item.calories_burned || item.calories || 0 }}kcal · {{ formatDate(item.start_time || item.recorded_at) }}</text>
            </view>
            <text class="ex-hist-dur">{{ item.duration_minutes || item.duration }}min</text>
          </view>
        </view>
        <view v-else class="ex-empty"><text>暂无运动记录</text></view>
      </view>

      <view style="height:120rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const exerciseTypes = [
  { name: '快走', type: 'walking' }, { name: '跑步', type: 'running' },
  { name: '骑行', type: 'cycling' }, { name: '游泳', type: 'swimming' },
  { name: '力量训练', type: 'strength' }, { name: '瑜伽', type: 'yoga' },
  { name: '广场舞', type: 'dance' }, { name: '爬楼', type: 'stairs' }, { name: '其他', type: 'other' },
]
const typeIdx = ref(0)
const form = ref({ duration: '', calories: '', heart_rate_peak: '' })
const submitting = ref(false)
const todaySteps = ref<number|null>(null)
const todayCalories = ref<number|null>(null)
const todayMinutes = ref<number|null>(null)
const history = ref<any[]>([])
const werunAuthed = ref(false)
const watchDevice = ref<any>(null)
const syncingWatch = ref(false)

const stepsColor = computed(() => {
  const v = todaySteps.value
  if (!v) return '#8E99A4'
  return v >= 8000 ? '#27AE60' : v >= 5000 ? '#E67E22' : '#E74C3C'
})
const stepsHint = computed(() => {
  const v = todaySteps.value
  if (!v) return '未获取步数'
  if (v >= 10000) return `🎉 已达10000步目标！还差${Math.max(0, 10000-v)}步`
  return `距目标10000步还差 ${Math.max(0, 10000-v)} 步`
})

function typeIcon(type: string): string {
  const m: Record<string,string> = { walking:'🚶', running:'🏃', cycling:'🚴', swimming:'🏊', strength:'💪', yoga:'🧘', dance:'💃', stairs:'🪜' }
  return m[type] || '🏋️'
}

function formatDate(t: string): string {
  if (!t) return ''
  return new Date(t).toLocaleDateString('zh-CN', { month:'numeric', day:'numeric' })
}

async function loadData() {
  try {
    const today = new Date().toISOString().slice(0, 10)
    const res = await http<any>(`/api/v1/health-data/activity?date=${today}`)
    const items = res.records || res.items || (Array.isArray(res) ? res : [])
    if (items.length > 0) {
      todaySteps.value = items.reduce((sum: number, i: any) => sum + (i.steps || 0), 0)
      todayCalories.value = Math.round(items.reduce((sum: number, i: any) => sum + (i.calories_burned || 0), 0))
      todayMinutes.value = items.reduce((sum: number, i: any) => sum + (i.duration_minutes || 0), 0)
    }
  } catch (e) { console.warn('[health/exercise] loadData:', e) }
  try {
    const res = await http<any>('/api/v1/health-data/activity?limit=20')
    history.value = res.records || res.items || (Array.isArray(res) ? res : [])
  } catch (e) { console.warn('[health/exercise] activity?limit=20:', e) }
  // 检查 WeRun 授权状态
  werunAuthed.value = !!uni.getStorageSync('werun_authed')
  // 加载穿戴设备
  try {
    const res = await http<any>('/api/v1/devices')
    const devs: any[] = res.devices || res.items || (Array.isArray(res) ? res : [])
    watchDevice.value = devs.find(d => ['smartwatch','fitness_band'].includes(d.device_type) && d.status === 'active')
      ?? devs.find(d => ['smartwatch','fitness_band'].includes(d.device_type))
      ?? null
  } catch { /* silent */ }
}

async function syncFromWatch() {
  if (!watchDevice.value || syncingWatch.value) return
  syncingWatch.value = true
  try {
    await http(`/api/v1/devices/${watchDevice.value.device_id}/sync`, { method: 'PUT', data: {} })
    uni.showToast({ title: '同步成功', icon: 'success' })
    await loadData()
  } catch {
    uni.showToast({ title: '同步失败，请检查设备连接', icon: 'none' })
  } finally {
    syncingWatch.value = false
  }
}

function goDeviceBind() {
  uni.navigateTo({ url: '/pages/health/device-bind' })
}

function authorizeWeRun() {
  uni.showModal({
    title: '授权微信步数',
    content: '需要您授权"微信运动"数据，用于健康分析。是否授权？',
    success: (modalRes) => {
      if (!modalRes.confirm) return
      // 微信 API: getWeRunData 需要先通过 scope.werun 授权
      uni.authorize({
        scope: 'scope.weRunData',
        success: () => {
          werunAuthed.value = true
          uni.setStorageSync('werun_authed', true)
          syncWeRun()
        },
        fail: () => {
          uni.showModal({
            title: '授权失败',
            content: '请在设置中开启"微信运动"权限',
            showCancel: false,
          })
        },
      })
    },
  })
}

async function syncWeRun() {
  uni.showLoading({ title: '同步中…' })
  // 获取加密步数数据
  uni.getWeRunData({
    success: async (res: any) => {
      try {
        await http('/api/v1/health-data/werun/sync', {
          method: 'POST',
          data: {
            encrypted_data: res.encryptedData,
            iv: res.iv,
            step_info_list: res.stepInfoList, // 非加密备用
          },
        })
        uni.showToast({ title: '同步成功', icon: 'success' })
        await loadData()
      } catch {
        // 降级：用明文步数（非加密）
        const steps = res.stepInfoList?.[0]?.step || 0
        if (steps > 0) {
          todaySteps.value = steps
          uni.showToast({ title: `今日步数: ${steps}步`, icon: 'none' })
        }
      }
    },
    fail: () => {
      uni.showToast({ title: '获取步数失败', icon: 'none' })
    },
    complete: () => uni.hideLoading(),
  })
}

async function submitExercise() {
  const dur = parseInt(form.value.duration)
  if (!dur || dur < 1 || dur > 600) {
    uni.showToast({ title: '请输入有效运动时长(1-600分钟)', icon: 'none' }); return
  }
  if (submitting.value) return
  submitting.value = true
  try {
    const et = exerciseTypes[typeIdx.value]
    const payload: any = {
      activity_type: et.type,
      duration_minutes: dur,
      start_time: new Date().toISOString(),
    }
    if (form.value.calories) payload.calories_burned = parseInt(form.value.calories)
    if (form.value.heart_rate_peak) payload.heart_rate_peak = parseInt(form.value.heart_rate_peak)
    await http('/api/v1/health-data/activity', { method: 'POST', data: payload })
    form.value = { duration: '', calories: '', heart_rate_peak: '' }
    uni.showToast({ title: '运动记录保存成功', icon: 'success' })
    await loadData()
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

onMounted(() => loadData())
</script>

<style scoped>
.ex-page { min-height: 100vh; background: #F5F6FA; }
.ex-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #1E8449 0%, #27AE60 100%); color: #fff; }
.ex-back  { font-size: 40rpx; padding: 16rpx; }
.ex-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.ex-scroll { height: calc(100vh - 180rpx); }

.ex-today-card { margin: 24rpx; background: linear-gradient(135deg, #1E8449, #27AE60); border-radius: 20rpx; padding: 32rpx; color: #fff; }
.ex-today-row  { display: flex; justify-content: space-around; margin-bottom: 20rpx; }
.ex-today-item { text-align: center; }
.ex-today-val  { display: block; font-size: 48rpx; font-weight: 700; }
.ex-today-label { display: block; font-size: 22rpx; opacity: 0.8; margin-top: 4rpx; }
.ex-steps-bar  { height: 12rpx; background: rgba(255,255,255,0.3); border-radius: 6rpx; overflow: hidden; }
.ex-steps-fill { height: 100%; background: #fff; border-radius: 6rpx; transition: width 0.5s; }
.ex-steps-hint { display: block; font-size: 22rpx; opacity: 0.85; margin-top: 10rpx; }

.ex-werun-card { margin: 0 24rpx 24rpx; background: #fff; border-radius: 16rpx; padding: 32rpx; text-align: center; }
.ex-werun-icon  { display: block; font-size: 60rpx; margin-bottom: 12rpx; }
.ex-werun-title { display: block; font-size: 30rpx; font-weight: 600; color: #2C3E50; margin-bottom: 8rpx; }
.ex-werun-desc  { display: block; font-size: 24rpx; color: #8E99A4; margin-bottom: 24rpx; line-height: 1.6; }
.ex-werun-btn   { background: #27AE60; color: #fff; padding: 20rpx 48rpx; border-radius: 50rpx; font-size: 28rpx; font-weight: 600; display: inline-block; }
.ex-werun-synced { margin: 0 24rpx 24rpx; background: #E8F8F0; border-radius: 12rpx; padding: 20rpx 24rpx; font-size: 26rpx; color: #5B6B7F; text-align: center; }

.ex-entry-card { margin: 0 24rpx 24rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
.ex-entry-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; margin-bottom: 20rpx; }
.ex-entry-row  { display: flex; gap: 16rpx; margin-bottom: 16rpx; }
.ex-entry-field { flex: 1; }
.ex-field-label  { display: block; font-size: 22rpx; color: #8E99A4; margin-bottom: 8rpx; }
.ex-field-input  { width: 100%; background: #F5F6FA; border-radius: 12rpx; padding: 16rpx 20rpx; font-size: 26rpx; box-sizing: border-box; }
.ex-field-picker { background: #F5F6FA; border-radius: 12rpx; padding: 16rpx 20rpx; font-size: 26rpx; color: #2C3E50; }
.ex-submit-btn { background: #E65100; color: #fff; text-align: center; padding: 26rpx 0; border-radius: 16rpx; font-size: 30rpx; font-weight: 600; }
.ex-submit-btn--loading { background: #FFCC80; color: #E65100; }

/* 穿戴设备区 */
.ex-device-card { margin: 0 24rpx 24rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
.ex-device-title { display: block; font-size: 26rpx; font-weight: 600; color: #2C3E50; margin-bottom: 16rpx; }
.ex-device-row { display: flex; align-items: center; gap: 16rpx; background: #E3F2FD; border-radius: 12rpx; padding: 20rpx; }
.ex-device-row--add { background: #FFF3E0; }
.ex-device-icon-text { font-size: 40rpx; flex-shrink: 0; }
.ex-device-info-col { flex: 1; }
.ex-device-name { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.ex-device-hint { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.ex-device-arrow { font-size: 28rpx; color: #E65100; font-weight: 700; flex-shrink: 0; }

.ex-history-card { margin: 0 24rpx 24rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
.ex-history-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; margin-bottom: 16rpx; }
.ex-hist-item { display: flex; align-items: center; gap: 16rpx; padding: 14rpx 0; border-bottom: 1rpx solid #F8F8F8; }
.ex-hist-item:last-child { border-bottom: none; }
.ex-hist-icon { font-size: 36rpx; flex-shrink: 0; }
.ex-hist-body { flex: 1; }
.ex-hist-name { display: block; font-size: 28rpx; color: #2C3E50; font-weight: 500; }
.ex-hist-meta { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.ex-hist-dur  { font-size: 26rpx; color: #27AE60; font-weight: 600; }

.ex-empty { text-align: center; padding: 48rpx; font-size: 26rpx; color: #8E99A4; }
</style>
