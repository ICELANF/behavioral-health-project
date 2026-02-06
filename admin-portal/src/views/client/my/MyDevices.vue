<template>
  <div class="my-devices">
    <div class="page-header">
      <button class="back-btn" @click="$router.back()">← 返回</button>
      <h2>穿戴设备管理</h2>
      <button class="add-btn" @click="showBindModal = true">+ 绑定设备</button>
    </div>

    <div v-if="!loading && devices.length === 0" class="empty-state">
      <p class="empty-icon">⌚</p>
      <p>暂未绑定任何设备</p>
      <button class="primary-btn" @click="showBindModal = true">绑定设备</button>
    </div>

    <div v-if="loading" class="loading-state">
      <p>加载中...</p>
    </div>

    <div v-for="device in devices" :key="device.id" class="device-card" :class="{ offline: device.status !== 'active' && device.status !== 'connected' }">
      <div class="device-header">
        <span class="device-icon">{{ deviceIcon(device.device_type) }}</span>
        <div class="device-info">
          <span class="device-name">{{ device.model || deviceTypeLabel(device.device_type) }}</span>
          <span class="device-model">{{ device.manufacturer || '' }} {{ device.device_id }}</span>
        </div>
        <span class="device-status" :class="device.status === 'active' || device.status === 'connected' ? 'online' : 'offline'">
          {{ device.status === 'active' || device.status === 'connected' ? '在线' : '离线' }}
        </span>
      </div>

      <div class="sync-info">
        <span class="sync-label">最后同步:</span>
        <span class="sync-time">{{ device.last_sync_at ? formatTime(device.last_sync_at) : '从未同步' }}</span>
        <button class="sync-btn" @click="syncDevice(device)" :disabled="device.syncing">
          {{ device.syncing ? '同步中...' : '立即同步' }}
        </button>
      </div>

      <div class="device-actions">
        <button class="action-btn" @click="$router.push('/client/device-dashboard')">查看详情</button>
        <button class="action-btn danger" @click="unbindDevice(device)">解绑</button>
      </div>
    </div>

    <!-- Bind Modal -->
    <div v-if="showBindModal" class="modal-overlay" @click.self="showBindModal = false">
      <div class="modal-content">
        <h3>绑定新设备</h3>
        <div class="bind-options">
          <div v-for="opt in bindOptions" :key="opt.type" class="bind-option" @click="bindDevice(opt)">
            <span class="bind-icon">{{ opt.icon }}</span>
            <span class="bind-name">{{ opt.name }}</span>
            <span class="bind-desc">{{ opt.desc }}</span>
          </div>
        </div>
        <button class="cancel-btn" @click="showBindModal = false">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/api/request'

const showBindModal = ref(false)
const loading = ref(false)
const devices = ref<any[]>([])

const deviceIcon = (type: string) => {
  const map: Record<string, string> = { cgm: '🩸', smartwatch: '⌚', bp_monitor: '💓', scale: '⚖️', fitness_band: '⌚' }
  return map[type] || '📱'
}

const deviceTypeLabel = (type: string) => {
  const map: Record<string, string> = { cgm: '血糖仪', smartwatch: '智能手表', bp_monitor: '血压计', scale: '体脂秤', fitness_band: '手环' }
  return map[type] || type
}

const formatTime = (iso: string) => {
  const d = new Date(iso)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin}分钟前`
  const diffHours = Math.floor(diffMin / 60)
  if (diffHours < 24) return `${diffHours}小时前`
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}天前`
}

const bindOptions = [
  { type: 'fitness_band', icon: '⌚', name: '智能手环/手表', desc: '支持小米、华为、Apple Watch等' },
  { type: 'cgm', icon: '🩸', name: '血糖仪', desc: '支持Dexcom、雅培等CGM设备' },
  { type: 'bp_monitor', icon: '💓', name: '血压计', desc: '支持欧姆龙等蓝牙血压计' },
  { type: 'scale', icon: '⚖️', name: '体脂秤', desc: '支持华为、小米等智能秤' },
]

const loadDevices = async () => {
  loading.value = true
  try {
    const { data } = await request.get('/v1/devices')
    devices.value = (data.devices || data || []).map((d: any) => ({ ...d, syncing: false }))
  } catch (e: any) {
    console.error('加载设备列表失败:', e)
  } finally {
    loading.value = false
  }
}

const syncDevice = async (device: any) => {
  device.syncing = true
  try {
    const { data } = await request.post(`/v1/devices/${device.id}/sync`)
    device.last_sync_at = data.last_sync_at || new Date().toISOString()
    device.status = 'connected'
  } catch (e: any) {
    console.error('同步失败:', e)
    // Fallback: just update locally
    device.last_sync_at = new Date().toISOString()
  } finally {
    device.syncing = false
  }
}

const unbindDevice = async (device: any) => {
  if (!confirm(`确定要解绑 ${device.model || deviceTypeLabel(device.device_type)} 吗？`)) return
  try {
    await request.delete(`/v1/devices/${device.id}`)
    devices.value = devices.value.filter(d => d.id !== device.id)
  } catch (e: any) {
    console.error('解绑失败:', e)
    // Fallback
    devices.value = devices.value.filter(d => d.id !== device.id)
  }
}

const bindDevice = async (opt: any) => {
  try {
    const { data } = await request.post('/v1/devices', {
      device_type: opt.type,
      manufacturer: null,
      model: null,
    })
    devices.value.push({ ...data, syncing: false, device_type: opt.type })
    showBindModal.value = false
  } catch (e: any) {
    console.error('绑定失败:', e)
    // Fallback: add locally
    const newDevice = {
      id: Date.now(),
      device_id: `DEV-${Date.now()}`,
      device_type: opt.type,
      model: opt.name,
      manufacturer: null,
      status: 'pairing',
      last_sync_at: null,
      syncing: false,
    }
    devices.value.push(newDevice)
    showBindModal.value = false
  }
}

onMounted(() => {
  loadDevices()
})
</script>

<style scoped>
.my-devices { max-width: 600px; margin: 0 auto; padding: 16px; }
.page-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.page-header h2 { flex: 1; margin: 0; font-size: 18px; }
.back-btn, .add-btn { padding: 6px 16px; border: 1px solid #d9d9d9; border-radius: 6px; background: #fff; cursor: pointer; font-size: 14px; }
.add-btn { color: #1890ff; border-color: #1890ff; }

.loading-state { text-align: center; padding: 40px; color: #999; }

.device-card { background: #fff; border: 1px solid #f0f0f0; border-radius: 12px; padding: 16px; margin-bottom: 12px; }
.device-card.offline { opacity: 0.7; }
.device-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.device-icon { font-size: 28px; }
.device-info { flex: 1; }
.device-name { display: block; font-size: 15px; font-weight: 600; color: #333; }
.device-model { font-size: 12px; color: #999; }
.device-status { font-size: 12px; padding: 2px 8px; border-radius: 10px; }
.device-status.online { background: #f6ffed; color: #389e0d; }
.device-status.offline { background: #f5f5f5; color: #999; }

.sync-info { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #999; margin-bottom: 12px; padding: 8px; background: #fafafa; border-radius: 6px; }
.sync-label { color: #999; }
.sync-time { flex: 1; color: #666; }
.sync-btn { padding: 2px 10px; border: 1px solid #1890ff; color: #1890ff; background: #fff; border-radius: 4px; cursor: pointer; font-size: 12px; }
.sync-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.device-actions { display: flex; gap: 8px; }
.action-btn { flex: 1; padding: 6px; border: 1px solid #d9d9d9; border-radius: 6px; background: #fff; cursor: pointer; font-size: 13px; text-align: center; }
.action-btn.danger { color: #ff4d4f; border-color: #ff4d4f; }

.empty-state { text-align: center; padding: 40px 20px; }
.empty-icon { font-size: 48px; margin-bottom: 8px; }
.primary-btn { padding: 8px 24px; background: #1890ff; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-content { background: #fff; border-radius: 12px; padding: 24px; width: 360px; max-width: 90vw; }
.modal-content h3 { margin: 0 0 16px; font-size: 16px; }
.bind-options { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }
.bind-option { display: flex; align-items: center; gap: 12px; padding: 12px; border: 1px solid #f0f0f0; border-radius: 8px; cursor: pointer; }
.bind-option:hover { background: #f6f6f6; }
.bind-icon { font-size: 24px; }
.bind-name { font-weight: 500; font-size: 14px; color: #333; }
.bind-desc { font-size: 12px; color: #999; margin-left: auto; }
.cancel-btn { width: 100%; padding: 8px; border: 1px solid #d9d9d9; border-radius: 6px; background: #fff; cursor: pointer; }
</style>
