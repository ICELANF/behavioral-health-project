import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  deviceAPI,
  type DeviceInfo,
  type GlucoseReading,
  type GlucoseStatistics,
  type WeightRecord,
  type BloodPressureRecord,
  type DashboardData
} from '@/api/device'
import { showToast } from 'vant'

export const useDeviceStore = defineStore('device', () => {
  // State
  const devices = ref<DeviceInfo[]>([])
  const glucoseReadings = ref<GlucoseReading[]>([])
  const glucoseStats = ref<GlucoseStatistics | null>(null)
  const currentGlucose = ref<{
    value?: number
    trend?: string
    trend_arrow?: string
    status?: string
    minutes_ago?: number
  } | null>(null)
  const weightRecords = ref<WeightRecord[]>([])
  const bpRecords = ref<BloodPressureRecord[]>([])
  const dashboard = ref<DashboardData | null>(null)
  const loading = ref(false)

  // Phase 2: 睡眠/活动/心率/HRV
  const lastNightSleep = ref<{
    date: string
    sleep_start?: string
    sleep_end?: string
    duration?: string
    score?: number
    stages?: {
      awake_min: number
      light_min: number
      deep_min: number
      rem_min: number
    }
    insights?: string[]
  } | null>(null)
  const todayActivity = ref<{
    steps: number
    distance_km: number
    calories_active: number
    active_minutes: number
  } | null>(null)
  const heartRateStats = ref<{
    resting_hr?: number
    avg_hr?: number
    max_hr?: number
    min_hr?: number
  } | null>(null)
  const hrvStats = ref<{
    avg_hrv?: number
    avg_stress?: number
    trend?: string
  } | null>(null)

  // Getters
  const hasDevices = computed(() => devices.value.length > 0)
  const latestWeight = computed(() => weightRecords.value[0] || null)
  const latestBP = computed(() => bpRecords.value[0] || null)
  const glucoseInRange = computed(() => {
    if (!currentGlucose.value?.value) return true
    const v = currentGlucose.value.value
    return v >= 3.9 && v <= 10.0
  })

  // Actions

  /**
   * 加载设备列表
   */
  const loadDevices = async () => {
    try {
      const res = await deviceAPI.getDevices()
      devices.value = res.devices || []
    } catch (error) {
      console.error('Load devices error:', error)
      devices.value = []
    }
  }

  /**
   * 绑定设备
   */
  const bindDevice = async (deviceType: string, manufacturer?: string, model?: string) => {
    loading.value = true
    try {
      const res = await deviceAPI.bindDevice({
        device_type: deviceType,
        manufacturer,
        model
      })
      if (res.success) {
        showToast('设备绑定成功')
        await loadDevices()
      }
      return res
    } catch (error) {
      showToast('绑定失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 解绑设备
   */
  const unbindDevice = async (deviceId: string) => {
    loading.value = true
    try {
      const res = await deviceAPI.unbindDevice(deviceId)
      if (res.success) {
        showToast('设备已解绑')
        await loadDevices()
      }
      return res
    } catch (error) {
      showToast('解绑失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 记录血糖
   */
  const recordGlucose = async (value: number, mealTag?: string, notes?: string) => {
    loading.value = true
    try {
      const res = await deviceAPI.recordGlucose({
        value,
        meal_tag: mealTag,
        notes
      })
      if (res.success) {
        showToast(`血糖已记录: ${value} mmol/L`)
        // 刷新数据
        await loadGlucoseData()
        await loadCurrentGlucose()
      }
      return res
    } catch (error) {
      showToast('记录失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 加载血糖数据
   */
  const loadGlucoseData = async (startDate?: string, endDate?: string) => {
    try {
      const res = await deviceAPI.getGlucoseReadings({
        start_date: startDate,
        end_date: endDate,
        limit: 100
      })
      glucoseReadings.value = res.readings || []
      glucoseStats.value = res.statistics || null
    } catch (error) {
      console.error('Load glucose error:', error)
      glucoseReadings.value = []
      glucoseStats.value = null
    }
  }

  /**
   * 加载当前血糖
   */
  const loadCurrentGlucose = async () => {
    try {
      const res = await deviceAPI.getCurrentGlucose()
      if (res.value) {
        currentGlucose.value = {
          value: res.value,
          trend: res.trend,
          trend_arrow: res.trend_arrow,
          status: res.status,
          minutes_ago: res.minutes_ago
        }
      } else {
        currentGlucose.value = null
      }
    } catch (error) {
      console.error('Load current glucose error:', error)
      currentGlucose.value = null
    }
  }

  /**
   * 记录体重
   */
  const recordWeight = async (weightKg: number, bodyFatPercent?: number) => {
    loading.value = true
    try {
      const res = await deviceAPI.recordWeight({
        weight_kg: weightKg,
        body_fat_percent: bodyFatPercent
      })
      if (res.success) {
        showToast(`体重已记录: ${weightKg} kg`)
        await loadWeightData()
      }
      return res
    } catch (error) {
      showToast('记录失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 加载体重数据
   */
  const loadWeightData = async (limit = 30) => {
    try {
      const res = await deviceAPI.getWeightRecords({ limit })
      weightRecords.value = res.records || []
    } catch (error) {
      console.error('Load weight error:', error)
      weightRecords.value = []
    }
  }

  /**
   * 记录血压
   */
  const recordBloodPressure = async (systolic: number, diastolic: number, pulse?: number) => {
    loading.value = true
    try {
      const res = await deviceAPI.recordBloodPressure({
        systolic,
        diastolic,
        pulse
      })
      if (res.success) {
        showToast(`血压已记录: ${systolic}/${diastolic}`)
        await loadBPData()
      }
      return res
    } catch (error) {
      showToast('记录失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 加载血压数据
   */
  const loadBPData = async (limit = 30) => {
    try {
      const res = await deviceAPI.getBloodPressureRecords(limit)
      bpRecords.value = res.records || []
    } catch (error) {
      console.error('Load BP error:', error)
      bpRecords.value = []
    }
  }

  /**
   * 加载今日仪表盘
   */
  const loadDashboard = async () => {
    try {
      dashboard.value = await deviceAPI.getTodayDashboard()
    } catch (error) {
      console.error('Load dashboard error:', error)
      dashboard.value = null
    }
  }

  // ============================================
  // Phase 2: 睡眠/活动/心率/HRV
  // ============================================

  /**
   * 加载昨晚睡眠
   */
  const loadLastNightSleep = async () => {
    try {
      const res = await deviceAPI.getLastNightSleep()
      if (res.score !== undefined) {
        lastNightSleep.value = {
          date: res.date,
          sleep_start: res.sleep_start,
          sleep_end: res.sleep_end,
          duration: res.duration,
          score: res.score,
          stages: res.stages,
          insights: res.insights
        }
      } else {
        lastNightSleep.value = null
      }
    } catch (error) {
      console.error('Load sleep error:', error)
      lastNightSleep.value = null
    }
  }

  /**
   * 加载今日活动
   */
  const loadTodayActivity = async () => {
    try {
      const today = new Date().toISOString().split('T')[0]
      const res = await deviceAPI.getActivityRecords({
        start_date: today,
        end_date: today
      })
      if (res.records?.length > 0) {
        const record = res.records[0]
        todayActivity.value = {
          steps: record.steps,
          distance_km: record.distance_km,
          calories_active: record.calories_active,
          active_minutes: record.active_minutes
        }
      } else {
        todayActivity.value = null
      }
    } catch (error) {
      console.error('Load activity error:', error)
      todayActivity.value = null
    }
  }

  /**
   * 加载心率统计
   */
  const loadHeartRateStats = async () => {
    try {
      const today = new Date().toISOString().split('T')[0]
      const res = await deviceAPI.getHeartRateData({
        start_date: today,
        end_date: today
      })
      if (res.statistics?.count > 0) {
        heartRateStats.value = {
          resting_hr: res.statistics.resting_hr,
          avg_hr: res.statistics.avg_hr,
          max_hr: res.statistics.max_hr,
          min_hr: res.statistics.min_hr
        }
      } else {
        heartRateStats.value = null
      }
    } catch (error) {
      console.error('Load heart rate error:', error)
      heartRateStats.value = null
    }
  }

  /**
   * 加载 HRV 统计
   */
  const loadHRVStats = async () => {
    try {
      const today = new Date().toISOString().split('T')[0]
      const res = await deviceAPI.getHRVData({
        start_date: today,
        end_date: today
      })
      if (res.statistics?.count > 0) {
        hrvStats.value = {
          avg_hrv: res.statistics.avg_hrv,
          avg_stress: res.statistics.avg_stress,
          trend: res.statistics.trend
        }
      } else {
        hrvStats.value = null
      }
    } catch (error) {
      console.error('Load HRV error:', error)
      hrvStats.value = null
    }
  }

  /**
   * 初始化加载
   */
  const init = async () => {
    loading.value = true
    try {
      await Promise.all([
        loadDevices(),
        loadDashboard(),
        loadCurrentGlucose(),
        // Phase 2
        loadLastNightSleep(),
        loadTodayActivity(),
        loadHeartRateStats(),
        loadHRVStats()
      ])
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    devices,
    glucoseReadings,
    glucoseStats,
    currentGlucose,
    weightRecords,
    bpRecords,
    dashboard,
    loading,
    // Phase 2
    lastNightSleep,
    todayActivity,
    heartRateStats,
    hrvStats,

    // Getters
    hasDevices,
    latestWeight,
    latestBP,
    glucoseInRange,

    // Actions
    loadDevices,
    bindDevice,
    unbindDevice,
    recordGlucose,
    loadGlucoseData,
    loadCurrentGlucose,
    recordWeight,
    loadWeightData,
    recordBloodPressure,
    loadBPData,
    loadDashboard,
    init,
    // Phase 2
    loadLastNightSleep,
    loadTodayActivity,
    loadHeartRateStats,
    loadHRVStats
  }
})
