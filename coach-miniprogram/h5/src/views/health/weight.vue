<template>
  <view class="wt-page">
    <view class="wt-navbar">
      <view class="wt-back" @tap="goBack">←</view>
      <text class="wt-title">体重·体成分</text>
      <view style="width:80rpx;"></view>
    </view>

    <scroll-view scroll-y class="wt-scroll">
      <!-- 当前体重 -->
      <view class="wt-current-card">
        <view class="wt-current-row">
          <view class="wt-current-item">
            <text class="wt-current-val">{{ latest.weight ?? '—' }}</text>
            <text class="wt-current-unit">kg 体重</text>
          </view>
          <view class="wt-current-item">
            <text class="wt-current-val" :style="{ color: bmiColor }">{{ latest.bmi ?? '—' }}</text>
            <text class="wt-current-unit">BMI</text>
          </view>
          <view class="wt-current-item">
            <text class="wt-current-val" style="color:#FFF8E1;">{{ latest.body_fat ?? '—' }}</text>
            <text class="wt-current-unit">% 体脂</text>
          </view>
        </view>
        <text class="wt-current-status" :style="{ color: bmiColor }">{{ bmiLabel }}</text>
      </view>

      <!-- 穿戴设备同步（智能秤） -->
      <view class="wt-device-card">
        <text class="wt-device-title">📡 穿戴设备</text>
        <view v-if="scaleDevice" class="wt-device-row" @tap="syncFromScale">
          <text class="wt-device-icon-text">⚖️</text>
          <view class="wt-device-info-col">
            <text class="wt-device-name">{{ scaleDevice.manufacturer || '智能体重秤' }}</text>
            <text class="wt-device-hint">{{ syncing ? '同步中…' : '点击同步体重·体成分数据' }}</text>
          </view>
          <text class="wt-device-arrow">{{ syncing ? '…' : '同步 ›' }}</text>
        </view>
        <view v-else class="wt-device-row wt-device-row--add" @tap="goDeviceBind">
          <text class="wt-device-icon-text">＋</text>
          <view class="wt-device-info-col">
            <text class="wt-device-name">绑定智能体重秤</text>
            <text class="wt-device-hint">支持小米体脂秤、PICOOC、Withings 等</text>
          </view>
          <text class="wt-device-arrow">›</text>
        </view>
      </view>

      <!-- 录入 -->
      <view class="wt-entry-card">
        <text class="wt-entry-title">📝 手动录入</text>
        <view class="wt-fields">
          <view class="wt-field">
            <text class="wt-field-label">体重 (kg) *</text>
            <input class="wt-field-input" type="digit" v-model="form.weight" placeholder="如: 65.5" maxlength="5" />
          </view>
          <view class="wt-field">
            <text class="wt-field-label">身高 (cm, 初次填写)</text>
            <input class="wt-field-input" type="digit" v-model="form.height" placeholder="如: 170" maxlength="3" />
          </view>
          <view class="wt-field">
            <text class="wt-field-label">体脂率 (%, 选填)</text>
            <input class="wt-field-input" type="digit" v-model="form.body_fat" placeholder="如: 22.5" maxlength="4" />
          </view>
          <view class="wt-field">
            <text class="wt-field-label">肌肉量 (kg, 选填)</text>
            <input class="wt-field-input" type="digit" v-model="form.muscle_mass" placeholder="如: 45.0" maxlength="4" />
          </view>
          <view class="wt-field">
            <text class="wt-field-label">内脏脂肪等级 (选填)</text>
            <input class="wt-field-input" type="number" v-model="form.visceral_fat" placeholder="1-20" maxlength="2" />
          </view>
        </view>
        <view class="wt-submit-btn" :class="{ 'wt-submit-btn--loading': submitting }" @tap="submitWeight">
          {{ submitting ? '保存中…' : '保存记录' }}
        </view>
      </view>

      <!-- 历史记录 -->
      <view class="wt-history-card">
        <text class="wt-history-title">📊 历史记录</text>
        <view v-if="history.length > 0">
          <view v-for="item in history" :key="item.id" class="wt-hist-item">
            <view class="wt-hist-left">
              <text class="wt-hist-val">{{ item.weight?.toFixed(1) }} kg</text>
              <text class="wt-hist-date">{{ formatDate(item.recorded_at || item.measured_at) }}</text>
            </view>
            <view class="wt-hist-right">
              <text v-if="item.bmi" class="wt-hist-tag" :style="{ background: bmiBg(item.bmi), color: bmiTagColor(item.bmi) }">BMI {{ item.bmi?.toFixed(1) }}</text>
              <text v-if="item.body_fat_percentage" class="wt-hist-tag" style="background:#E3F2FD; color:#1565C0;">体脂 {{ item.body_fat_percentage?.toFixed(1) }}%</text>
            </view>
          </view>
        </view>
        <view v-else class="wt-empty"><text>暂无记录，录入第一条数据吧</text></view>
      </view>

      <!-- 体成分指标说明 -->
      <view class="wt-ref-card">
        <text class="wt-ref-title">📋 BMI 参考</text>
        <view class="wt-ref-row"><view class="wt-ref-dot" style="background:#1E88E5;"></view><text>&lt; 18.5 偏瘦</text></view>
        <view class="wt-ref-row"><view class="wt-ref-dot" style="background:#27AE60;"></view><text>18.5 — 23.9 正常</text></view>
        <view class="wt-ref-row"><view class="wt-ref-dot" style="background:#E65100;"></view><text>24.0 — 27.9 超重</text></view>
        <view class="wt-ref-row"><view class="wt-ref-dot" style="background:#B71C1C;"></view><text>≥ 28.0 肥胖</text></view>
      </view>

      <view style="height:120rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const form = ref({ weight: '', height: '', body_fat: '', muscle_mass: '', visceral_fat: '' })
const submitting = ref(false)
const syncing = ref(false)
const latest = ref<any>({})
const history = ref<any[]>([])
const scaleDevice = ref<any>(null)

const bmiColor = computed(() => {
  const b = latest.value.bmi
  if (!b) return '#fff'
  if (b < 18.5) return '#90CAF9'
  if (b < 24)  return '#A5D6A7'
  if (b < 28)  return '#FFCC80'
  return '#EF9A9A'
})
const bmiLabel = computed(() => {
  const b = latest.value.bmi
  if (!b) return '—'
  if (b < 18.5) return '偏瘦'
  if (b < 24)   return '正常体重'
  if (b < 28)   return '超重'
  return '肥胖'
})

function bmiBg(bmi: number): string {
  if (!bmi)    return '#F5F6FA'
  if (bmi < 18.5) return '#E3F2FD'
  if (bmi < 24)   return '#E8F5E9'
  if (bmi < 28)   return '#FFF3E0'
  return '#FFEBEE'
}
function bmiTagColor(bmi: number): string {
  if (!bmi)    return '#8E99A4'
  if (bmi < 18.5) return '#1565C0'
  if (bmi < 24)   return '#2E7D32'
  if (bmi < 28)   return '#E65100'
  return '#B71C1C'
}

function formatDate(t: string): string {
  if (!t) return ''
  return new Date(t).toLocaleDateString('zh-CN', { month:'numeric', day:'numeric' })
}

async function loadDevices() {
  try {
    const res = await http<any>('/api/v1/devices')
    const devs: any[] = res.devices || res.items || (Array.isArray(res) ? res : [])
    scaleDevice.value = devs.find(d => d.device_type === 'smart_scale' && d.status === 'active')
      ?? devs.find(d => d.device_type === 'smart_scale')
      ?? null
  } catch { /* silent */ }
}

async function syncFromScale() {
  if (!scaleDevice.value || syncing.value) return
  syncing.value = true
  try {
    await http(`/api/v1/devices/${scaleDevice.value.device_id}/sync`, { method: 'PUT', data: {} })
    uni.showToast({ title: '同步成功', icon: 'success' })
    await loadData()
  } catch {
    uni.showToast({ title: '同步失败，请检查设备连接', icon: 'none' })
  } finally {
    syncing.value = false
  }
}

function goDeviceBind() {
  uni.navigateTo({ url: '/health/device-bind' })
}

async function loadData() {
  try {
    const res = await http<any>('/api/v1/health-data/vitals?limit=20&type=weight')
    const items = res.readings || res.items || (Array.isArray(res) ? res : [])
    history.value = items
    if (items.length > 0) {
      const l = items[0]
      latest.value = {
        weight: l.weight?.toFixed(1),
        bmi:    l.bmi?.toFixed(1),
        body_fat: l.body_fat_percentage?.toFixed(1),
      }
    }
  } catch (e) { console.warn('[health/weight] vitals?limit=20&type=weight:', e) }
}

async function submitWeight() {
  const w = parseFloat(form.value.weight)
  if (!w || w < 20 || w > 300) {
    uni.showToast({ title: '请输入有效体重(20-300kg)', icon: 'none' }); return
  }
  if (submitting.value) return
  submitting.value = true
  try {
    const payload: any = { weight: w, recorded_at: new Date().toISOString() }
    if (form.value.height)       payload.height = parseFloat(form.value.height)
    if (form.value.body_fat)     payload.body_fat_percentage = parseFloat(form.value.body_fat)
    if (form.value.muscle_mass)  payload.muscle_mass = parseFloat(form.value.muscle_mass)
    if (form.value.visceral_fat) payload.visceral_fat_level = parseInt(form.value.visceral_fat)
    await http('/api/v1/health-data/vitals', { method: 'POST', data: payload })
    form.value = { weight: '', height: '', body_fat: '', muscle_mass: '', visceral_fat: '' }
    uni.showToast({ title: '记录成功', icon: 'success' })
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
  else uni.navigateTo({ url: '/health/index' })
}

onMounted(() => { loadData(); loadDevices() })
</script>

<style scoped>
.wt-page { min-height: 100vh; background: #F0F7FF; }
.wt-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #1565C0 0%, #1E88E5 100%); color: #fff; }
.wt-back  { font-size: 40rpx; padding: 16rpx; }
.wt-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.wt-scroll { height: calc(100vh - 180rpx); }

.wt-current-card { margin: 24rpx; background: linear-gradient(135deg, #1565C0, #1E88E5); border-radius: 20rpx; padding: 32rpx; color: #fff; }
.wt-current-row  { display: flex; justify-content: space-around; margin-bottom: 16rpx; }
.wt-current-item { text-align: center; }
.wt-current-val  { display: block; font-size: 48rpx; font-weight: 700; }
.wt-current-unit { display: block; font-size: 20rpx; opacity: 0.8; margin-top: 4rpx; }
.wt-current-status { display: block; text-align: center; font-size: 26rpx; font-weight: 600; }

/* 穿戴设备区 */
.wt-device-card { margin: 0 24rpx 24rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
.wt-device-title { display: block; font-size: 26rpx; font-weight: 600; color: #2C3E50; margin-bottom: 16rpx; }
.wt-device-row { display: flex; align-items: center; gap: 16rpx; background: #E3F2FD; border-radius: 12rpx; padding: 20rpx; }
.wt-device-row--add { background: #FFF3E0; }
.wt-device-icon-text { font-size: 40rpx; flex-shrink: 0; }
.wt-device-info-col { flex: 1; }
.wt-device-name { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.wt-device-hint { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.wt-device-arrow { font-size: 28rpx; color: #E65100; font-weight: 700; flex-shrink: 0; }

.wt-entry-card { margin: 0 24rpx 24rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
.wt-entry-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; margin-bottom: 20rpx; }
.wt-fields { display: flex; flex-wrap: wrap; gap: 16rpx; }
.wt-field { width: calc(50% - 8rpx); }
.wt-field-label { display: block; font-size: 22rpx; color: #8E99A4; margin-bottom: 8rpx; }
.wt-field-input { width: 100%; background: #F5F6FA; border-radius: 12rpx; padding: 16rpx 20rpx; font-size: 26rpx; box-sizing: border-box; }
.wt-submit-btn { margin-top: 20rpx; background: #E65100; color: #fff; text-align: center; padding: 26rpx 0; border-radius: 16rpx; font-size: 30rpx; font-weight: 600; }
.wt-submit-btn--loading { background: #FFCC80; color: #E65100; }

.wt-history-card { margin: 0 24rpx 24rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
.wt-history-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; margin-bottom: 16rpx; }
.wt-hist-item { display: flex; justify-content: space-between; align-items: center; padding: 14rpx 0; border-bottom: 1rpx solid #F8F8F8; }
.wt-hist-item:last-child { border-bottom: none; }
.wt-hist-val  { display: block; font-size: 30rpx; font-weight: 600; color: #2C3E50; }
.wt-hist-date { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.wt-hist-right { display: flex; gap: 8rpx; flex-wrap: wrap; }
.wt-hist-tag  { padding: 4rpx 12rpx; border-radius: 20rpx; font-size: 20rpx; }

.wt-ref-card { margin: 0 24rpx 24rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
.wt-ref-title { display: block; font-size: 26rpx; font-weight: 600; color: #2C3E50; margin-bottom: 16rpx; }
.wt-ref-row   { display: flex; align-items: center; gap: 12rpx; margin-bottom: 10rpx; font-size: 24rpx; color: #5B6B7F; }
.wt-ref-dot   { width: 16rpx; height: 16rpx; border-radius: 50%; flex-shrink: 0; }

.wt-empty { text-align: center; padding: 48rpx; font-size: 26rpx; color: #8E99A4; }
</style>
