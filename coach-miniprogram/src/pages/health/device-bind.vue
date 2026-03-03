<template>
  <view class="db-page">
    <view class="db-navbar">
      <view class="db-back" @tap="goBack">←</view>
      <text class="db-title">设备管理</text>
      <view style="width:80rpx;"></view>
    </view>

    <scroll-view scroll-y class="db-scroll">
      <!-- 已绑定设备 -->
      <view class="db-section-title">📡 已绑定设备 ({{ myDevices.length }})</view>
      <view class="db-devices" v-if="myDevices.length > 0">
        <view v-for="d in myDevices" :key="d.id" class="db-device-card">
          <view class="db-device-header">
            <text class="db-device-icon">{{ deviceTypeIcon(d.device_type) }}</text>
            <view class="db-device-info">
              <text class="db-device-name">{{ d.manufacturer || '' }} {{ d.model || d.device_type }}</text>
              <text class="db-device-sn" v-if="d.serial_number">SN: {{ d.serial_number }}</text>
              <view class="db-device-status-row">
                <view class="db-status-dot" :style="{ background: d.status === 'active' ? '#27AE60' : '#BDC3C7' }"></view>
                <text class="db-status-text">{{ d.status === 'active' ? '已连接' : '未连接' }}</text>
                <text class="db-last-sync">上次同步 {{ formatTime(d.last_sync_at) }}</text>
              </view>
            </view>
          </view>
          <view class="db-device-actions">
            <view class="db-btn db-btn--sync" @tap="syncDevice(d)">同步数据</view>
            <view class="db-btn db-btn--unbind" @tap="unbindDevice(d)">解绑</view>
          </view>
        </view>
      </view>
      <view class="db-no-device" v-else>
        <text>暂未绑定任何设备</text>
      </view>

      <!-- 添加设备 -->
      <view class="db-section-title">➕ 添加设备</view>
      <view class="db-catalog">
        <view v-for="cat in deviceCatalog" :key="cat.type" class="db-cat-card" @tap="showBindModal(cat)">
          <text class="db-cat-icon">{{ cat.icon }}</text>
          <view class="db-cat-info">
            <text class="db-cat-name">{{ cat.name }}</text>
            <text class="db-cat-desc">{{ cat.desc }}</text>
          </view>
          <text class="db-cat-arrow">›</text>
        </view>
      </view>

      <view style="height:120rpx;"></view>
    </scroll-view>

    <!-- 绑定 Modal -->
    <view v-if="bindModal.show" class="db-mask" @tap.self="bindModal.show = false">
      <view class="db-modal">
        <text class="db-modal-title">绑定 {{ bindModal.device?.name }}</text>
        <view class="db-modal-field">
          <text class="db-modal-label">品牌/厂商</text>
          <picker :range="bindModal.device?.brands || []" :value="bindModal.brandIdx" @change="bindModal.brandIdx = $event.detail.value">
            <view class="db-modal-picker">{{ (bindModal.device?.brands || [])[bindModal.brandIdx] || '请选择' }}</view>
          </picker>
        </view>
        <view class="db-modal-field">
          <text class="db-modal-label">型号（选填）</text>
          <input class="db-modal-input" v-model="bindModal.model" placeholder="如: Libre 2" maxlength="50" />
        </view>
        <view class="db-modal-field">
          <text class="db-modal-label">序列号（选填）</text>
          <input class="db-modal-input" v-model="bindModal.sn" placeholder="设备底部序列号" maxlength="100" />
        </view>
        <view class="db-modal-actions">
          <view class="db-modal-btn db-modal-btn--cancel" @tap="bindModal.show = false">取消</view>
          <view class="db-modal-btn db-modal-btn--confirm" :class="{ 'db-modal-btn--loading': binding }" @tap="confirmBind">
            {{ binding ? '绑定中…' : '确认绑定' }}
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'

const BASE_URL = 'http://localhost:8000'
function getToken() { return uni.getStorageSync('access_token') || '' }
async function http<T = any>(url: string, opts: any = {}): Promise<T> {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url, method: opts.method || 'GET', data: opts.data,
      header: { 'Authorization': 'Bearer ' + getToken(), 'Content-Type': 'application/json' },
      success: (res: any) => {
        if (res.statusCode === 401) { uni.removeStorageSync('access_token'); uni.reLaunch({ url: '/pages/auth/login' }); reject(new Error('401')); return }
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data as T)
        else reject(new Error(`HTTP ${res.statusCode}`))
      },
      fail: reject,
    })
  })
}

const deviceCatalog = [
  { type: 'cgm', icon: '🩸', name: '动态血糖仪(CGM)', desc: 'Abbott/Dexcom/Medtronic等', brands: ['Abbott Libre', 'Dexcom G6', 'Medtronic', '其他'] },
  { type: 'glucometer', icon: '🔬', name: '血糖仪', desc: '家用手指血糖检测仪', brands: ['鱼跃', '罗氏', '拜安进', '强生', '其他'] },
  { type: 'smart_scale', icon: '⚖️', name: '智能体重秤(含体成分)', desc: '测体重、体脂率、肌肉量等', brands: ['小米/华米', 'PICOOC', 'Withings', '其他'] },
  { type: 'smartwatch', icon: '⌚', name: '智能手表', desc: '心率、运动、睡眠监测', brands: ['Apple Watch', 'Huawei', '小米手环', 'Fitbit', '其他'] },
  { type: 'sleep_tracker', icon: '😴', name: '睡眠监测仪', desc: '专业睡眠质量分析', brands: ['Withings Sleep', '华为睡眠宝', '其他'] },
  { type: 'blood_pressure_monitor', icon: '💓', name: '血压计', desc: '上臂式电子血压计', brands: ['欧姆龙', '鱼跃', '迈克大夫', '其他'] },
  { type: 'pulse_oximeter', icon: '🫁', name: '血氧仪', desc: '指夹式血氧饱和度检测', brands: ['迈瑞', '乐普', '其他'] },
  { type: 'fitness_band', icon: '📿', name: '运动手环', desc: '步数、心率基础监测', brands: ['小米手环', 'Huawei Band', 'Fitbit', '其他'] },
]

const bindModal = reactive({ show: false, device: null as any, brandIdx: 0, model: '', sn: '' })
const binding = ref(false)
const myDevices = ref<any[]>([])

function deviceTypeIcon(type: string): string {
  const m: Record<string,string> = { cgm:'🩸', glucometer:'🔬', smart_scale:'⚖️', smartwatch:'⌚', sleep_tracker:'😴', blood_pressure_monitor:'💓', pulse_oximeter:'🫁', fitness_band:'📿' }
  return m[type] || '📱'
}

function formatTime(t: string): string {
  if (!t) return '从未'
  const d = new Date(t), diff = (Date.now() - d.getTime()) / 60000
  if (diff < 60) return `${Math.round(diff)}分钟前`
  if (diff < 1440) return `${Math.round(diff/60)}小时前`
  return `${Math.round(diff/1440)}天前`
}

async function loadDevices() {
  try {
    const res = await http<any>('/api/v1/devices')
    myDevices.value = res.devices || res.items || (Array.isArray(res) ? res : [])
  } catch {}
}

function showBindModal(cat: any) {
  bindModal.device = cat
  bindModal.brandIdx = 0
  bindModal.model = ''
  bindModal.sn = ''
  bindModal.show = true
}

async function confirmBind() {
  if (binding.value) return
  binding.value = true
  try {
    const brands: string[] = bindModal.device?.brands || []
    await http('/api/v1/devices/bind', {
      method: 'POST',
      data: {
        device_type: bindModal.device.type,
        manufacturer: brands[bindModal.brandIdx] || '',
        model: bindModal.model || null,
        serial_number: bindModal.sn || null,
      },
    })
    bindModal.show = false
    uni.showToast({ title: '设备绑定成功', icon: 'success' })
    await loadDevices()
  } catch {
    uni.showToast({ title: '绑定失败，请重试', icon: 'none' })
  } finally {
    binding.value = false
  }
}

async function syncDevice(d: any) {
  uni.showLoading({ title: '同步中…' })
  try {
    await http(`/api/v1/devices/${d.device_id}/sync`, { method: 'PUT', data: {} })
    uni.showToast({ title: '同步完成', icon: 'success' })
    await loadDevices()
  } catch {
    uni.showToast({ title: '同步失败', icon: 'none' })
  } finally {
    uni.hideLoading()
  }
}

function unbindDevice(d: any) {
  uni.showModal({
    title: '解绑设备',
    content: `确认解绑 ${d.manufacturer || ''} ${d.model || d.device_type}？`,
    success: async (res) => {
      if (!res.confirm) return
      try {
        await http(`/api/v1/devices/${d.device_id}`, { method: 'DELETE', data: {} })
        uni.showToast({ title: '已解绑', icon: 'success' })
        await loadDevices()
      } catch {
        uni.showToast({ title: '操作失败', icon: 'none' })
      }
    },
  })
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.navigateTo({ url: '/pages/health/index' })
}

onMounted(() => loadDevices())
</script>

<style scoped>
.db-page { min-height: 100vh; background: #F5F6FA; }
.db-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #1B2631 0%, #2C3E50 100%); color: #fff; }
.db-back  { font-size: 40rpx; padding: 16rpx; }
.db-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.db-scroll { height: calc(100vh - 180rpx); }

.db-section-title { font-size: 28rpx; font-weight: 700; color: #2C3E50; margin: 24rpx 24rpx 16rpx; }

.db-device-card { margin: 0 24rpx 16rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
.db-device-header { display: flex; gap: 16rpx; margin-bottom: 16rpx; }
.db-device-icon { font-size: 48rpx; }
.db-device-info { flex: 1; }
.db-device-name { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.db-device-sn   { display: block; font-size: 20rpx; color: #BDC3C7; margin-top: 4rpx; }
.db-device-status-row { display: flex; align-items: center; gap: 8rpx; margin-top: 8rpx; }
.db-status-dot  { width: 12rpx; height: 12rpx; border-radius: 50%; }
.db-status-text { font-size: 22rpx; color: #5B6B7F; }
.db-last-sync   { font-size: 20rpx; color: #BDC3C7; margin-left: 8rpx; }
.db-device-actions { display: flex; gap: 12rpx; }
.db-btn { flex: 1; text-align: center; padding: 16rpx 0; border-radius: 12rpx; font-size: 26rpx; font-weight: 600; }
.db-btn--sync   { background: #EEF6FF; color: #3498DB; }
.db-btn--unbind { background: #FFF0ED; color: #E74C3C; }
.db-no-device { margin: 0 24rpx 24rpx; background: #fff; border-radius: 16rpx; padding: 48rpx; text-align: center; font-size: 26rpx; color: #8E99A4; }

.db-cat-card { margin: 0 24rpx 12rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; display: flex; align-items: center; gap: 16rpx; }
.db-cat-icon  { font-size: 44rpx; flex-shrink: 0; }
.db-cat-info  { flex: 1; }
.db-cat-name  { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.db-cat-desc  { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.db-cat-arrow { font-size: 32rpx; color: #CCC; }

/* Modal */
.db-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 100; display: flex; align-items: flex-end; }
.db-modal { width: 100%; background: #fff; border-radius: 32rpx 32rpx 0 0; padding: 40rpx 32rpx calc(48rpx + env(safe-area-inset-bottom)); }
.db-modal-title { display: block; font-size: 34rpx; font-weight: 700; color: #2C3E50; text-align: center; margin-bottom: 32rpx; }
.db-modal-field { margin-bottom: 24rpx; }
.db-modal-label { display: block; font-size: 24rpx; color: #8E99A4; margin-bottom: 10rpx; }
.db-modal-input  { width: 100%; background: #F5F6FA; border-radius: 12rpx; padding: 18rpx 20rpx; font-size: 28rpx; box-sizing: border-box; }
.db-modal-picker { background: #F5F6FA; border-radius: 12rpx; padding: 18rpx 20rpx; font-size: 28rpx; color: #2C3E50; }
.db-modal-actions { display: flex; gap: 20rpx; margin-top: 32rpx; }
.db-modal-btn { flex: 1; text-align: center; padding: 26rpx 0; border-radius: 16rpx; font-size: 30rpx; font-weight: 600; }
.db-modal-btn--cancel  { background: #F0F0F0; color: #5B6B7F; }
.db-modal-btn--confirm { background: #2C3E50; color: #fff; }
.db-modal-btn--loading { background: #8E99A4; }
</style>
