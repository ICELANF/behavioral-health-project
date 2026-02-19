<template>
  <div class="page-container">
    <van-nav-bar title="数据同步" left-arrow @click-left="$router.back()" />

    <div class="page-content">
      <!-- 设备列表 -->
      <div class="card">
        <div class="section-header">
          <h3>我的设备</h3>
          <van-button size="small" type="primary" plain @click="showBindDialog = true">绑定设备</van-button>
        </div>

        <van-loading v-if="loadingDevices" class="loading" />

        <template v-else-if="devices.length">
          <div class="device-item" v-for="device in devices" :key="device.device_id">
            <div class="device-info">
              <van-icon :name="deviceIcon(device.device_type)" size="32" color="#1989fa" />
              <div class="device-detail">
                <div class="device-name">{{ DEVICE_NAMES[device.device_type] || device.device_type }}</div>
                <div class="device-meta">
                  <van-tag :type="device.status === 'connected' ? 'success' : 'default'" size="small">
                    {{ device.status === 'connected' ? '已连接' : '离线' }}
                  </van-tag>
                  <span v-if="device.battery_level">电量 {{ device.battery_level }}%</span>
                  <span v-if="device.last_sync_at">上次同步: {{ formatTime(device.last_sync_at) }}</span>
                </div>
              </div>
            </div>
            <div class="device-actions">
              <van-button
                size="small"
                type="primary"
                :loading="syncingId === device.device_id"
                @click="syncDevice(device)"
              >
                同步
              </van-button>
            </div>
          </div>
        </template>

        <van-empty v-else description="暂无绑定设备" />
      </div>

      <!-- 同步日志 -->
      <div class="card">
        <h3>最近同步记录</h3>
        <template v-if="syncLogs.length">
          <div class="sync-log" v-for="(log, idx) in syncLogs" :key="idx">
            <van-icon :name="log.success ? 'checked' : 'warning-o'" :color="log.success ? '#07c160' : '#ee0a24'" />
            <div class="log-content">
              <div class="log-text">{{ log.message }}</div>
              <div class="log-time">{{ log.time }}</div>
            </div>
          </div>
        </template>
        <van-empty v-else description="暂无同步记录" image-size="60" />
      </div>

      <!-- 批量同步 -->
      <van-button
        type="primary"
        block
        round
        class="sync-all-btn"
        :loading="syncingAll"
        :disabled="!devices.length"
        @click="syncAll"
      >
        一键同步所有设备
      </van-button>
    </div>

    <!-- 绑定设备弹窗 -->
    <van-dialog
      v-model:show="showBindDialog"
      title="绑定新设备"
      show-cancel-button
      @confirm="bindDevice"
    >
      <div class="bind-form">
        <van-field name="type" label="设备类型">
          <template #input>
            <van-radio-group v-model="bindForm.device_type" direction="horizontal">
              <van-radio name="smartwatch">手表</van-radio>
              <van-radio name="smartband">手环</van-radio>
              <van-radio name="cgm">血糖仪</van-radio>
              <van-radio name="glucometer">指血仪</van-radio>
              <van-radio name="scale">体脂秤</van-radio>
              <van-radio name="bp_monitor">血压计</van-radio>
            </van-radio-group>
          </template>
        </van-field>
        <van-field v-model="bindForm.manufacturer" label="厂商" placeholder="如: 华为、小米 (选填)" />
        <van-field v-model="bindForm.model" label="型号" placeholder="如: GT4、Band 8 (选填)" />
      </div>
    </van-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { showToast } from 'vant'
import api from '@/api/index'

const devices = ref<any[]>([])
const syncLogs = ref<any[]>([])
const loadingDevices = ref(false)
const syncingId = ref<string | null>(null)
const syncingAll = ref(false)
const showBindDialog = ref(false)

const bindForm = reactive({
  device_type: 'smartwatch',
  manufacturer: '',
  model: ''
})

const DEVICE_ICONS: Record<string, string> = {
  smartwatch: 'clock-o',
  smartband: 'bar-chart-o',
  cgm: 'column',
  glucometer: 'column',
  scale: 'balance-o',
  bp_monitor: 'like-o'
}

const DEVICE_NAMES: Record<string, string> = {
  smartwatch: '智能手表',
  smartband: '智能手环',
  cgm: '动态血糖仪',
  glucometer: '血糖仪',
  scale: '体脂秤',
  bp_monitor: '血压计'
}

function deviceIcon(type: string) {
  return DEVICE_ICONS[type] || 'setting-o'
}

function formatTime(str: string) {
  if (!str) return '--'
  return str.replace('T', ' ').slice(0, 16)
}

function addLog(success: boolean, message: string) {
  syncLogs.value.unshift({
    success,
    message,
    time: new Date().toLocaleString('zh-CN')
  })
}

async function loadDevices() {
  loadingDevices.value = true
  try {
    const res: any = await api.get('/api/v1/mp/device/devices')
    devices.value = res.devices || res.data || res || []
  } catch {
    devices.value = []
  } finally {
    loadingDevices.value = false
  }
}

async function syncDevice(device: any) {
  const deviceId = device.device_id
  const deviceName = DEVICE_NAMES[device.device_type] || device.device_type
  syncingId.value = deviceId
  try {
    // 后端 sync 接口: device_id 为 query 参数, data 为 body
    const res: any = await api.post(`/api/v1/mp/device/sync?device_id=${encodeURIComponent(deviceId)}`, {})
    addLog(true, `${deviceName} 同步成功，处理 ${res.records_processed || 0} 条记录`)
    showToast({ message: '同步成功', type: 'success' })
    if (res.task_completed) {
      setTimeout(() => showToast({ message: '监测任务已自动完成 +10积分', type: 'success' }), 1500)
    }
    await loadDevices()
  } catch (e: any) {
    addLog(false, `${deviceName} 同步失败: ${e.response?.data?.detail || '未知错误'}`)
    showToast('同步失败')
  } finally {
    syncingId.value = null
  }
}

async function syncAll() {
  if (!devices.value.length) return
  syncingAll.value = true
  let successCount = 0
  let failCount = 0

  for (const device of devices.value) {
    const deviceName = DEVICE_NAMES[device.device_type] || device.device_type
    try {
      const res: any = await api.post(`/api/v1/mp/device/sync?device_id=${encodeURIComponent(device.device_id)}`, {})
      addLog(true, `${deviceName} 同步成功`)
      successCount++
    } catch {
      addLog(false, `${deviceName} 同步失败`)
      failCount++
    }
  }

  await loadDevices()
  const msg = failCount === 0
    ? `全部 ${successCount} 台设备同步成功`
    : `${successCount} 台成功，${failCount} 台失败`
  showToast({ message: msg, type: failCount === 0 ? 'success' : 'fail' })
  syncingAll.value = false
}

async function bindDevice() {
  try {
    await api.post('/api/v1/mp/device/devices/bind', {
      device_type: bindForm.device_type,
      manufacturer: bindForm.manufacturer || undefined,
      model: bindForm.model || undefined
    })
    showToast({ message: '绑定成功', type: 'success' })
    bindForm.manufacturer = ''
    bindForm.model = ''
    await loadDevices()
  } catch (e: any) {
    showToast(e.response?.data?.detail || '绑定失败')
  }
}

onMounted(loadDevices)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.loading { text-align: center; padding: $spacing-lg 0; }

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $spacing-sm;

  h3 { font-size: $font-size-lg; margin: 0; }
}

.card h3 {
  font-size: $font-size-lg;
  margin-bottom: $spacing-sm;
}

.device-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-md 0;
  border-bottom: 1px solid #f5f5f5;

  &:last-child { border-bottom: none; }

  .device-info {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
  }

  .device-detail {
    .device-name {
      font-size: $font-size-md;
      font-weight: 500;
    }

    .device-meta {
      display: flex;
      align-items: center;
      gap: $spacing-xs;
      margin-top: 4px;
      font-size: $font-size-xs;
      color: $text-color-secondary;
    }
  }
}

.sync-log {
  display: flex;
  align-items: flex-start;
  gap: $spacing-sm;
  padding: $spacing-xs 0;

  .log-text {
    font-size: $font-size-sm;
  }

  .log-time {
    font-size: $font-size-xs;
    color: $text-color-secondary;
  }
}

.sync-all-btn {
  margin-top: $spacing-md;
}

.bind-form {
  padding: $spacing-sm 0;
}
</style>
