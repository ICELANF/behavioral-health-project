import request from './request'

/**
 * 设备信息
 */
export interface DeviceInfo {
  device_id: string
  device_type: string
  manufacturer?: string
  model?: string
  status: string
  battery_level?: number
  last_sync_at?: string
}

/**
 * 血糖读数
 */
export interface GlucoseReading {
  id: number
  value: number
  value_mgdl: number
  unit: string
  trend?: string
  trend_arrow?: string
  source: string
  meal_tag?: string
  recorded_at: string
  notes?: string
}

/**
 * 血糖统计
 */
export interface GlucoseStatistics {
  avg_glucose?: number
  min_glucose?: number
  max_glucose?: number
  std_glucose?: number
  cv?: number
  time_in_range?: number
  time_below_range?: number
  time_above_range?: number
  readings_count: number
}

/**
 * 体重记录
 */
export interface WeightRecord {
  id: number
  weight_kg: number
  bmi?: number
  body_fat_percent?: number
  muscle_mass_kg?: number
  recorded_at: string
}

/**
 * 血压记录
 */
export interface BloodPressureRecord {
  id: number
  systolic: number
  diastolic: number
  pulse?: number
  recorded_at: string
}

/**
 * 今日仪表盘
 */
export interface DashboardData {
  date: string
  glucose?: {
    current: number
    current_mgdl: number
    trend?: string
    trend_arrow?: string
    avg_today?: number
    tir_today?: number
    readings_count: number
    status: string
    last_reading_at: string
  }
  activity?: {
    steps: number
    steps_goal: number
    progress_percent: number
    distance_km: number
    calories_active: number
    active_minutes: number
  }
  sleep?: {
    duration_hours?: number
    score?: number
    deep_percent?: number
    status: string
  }
  weight?: {
    weight_kg: number
    bmi?: number
    recorded_at: string
  }
  alerts: Array<{
    type: string
    message: string
    severity: string
  }>
}

/**
 * 设备数据 API
 */
export const deviceAPI = {
  /**
   * 获取设备列表
   */
  getDevices(): Promise<{ devices: DeviceInfo[]; total: number }> {
    return request.get('/api/v1/mp/device/devices')
  },

  /**
   * 绑定设备
   */
  bindDevice(data: {
    device_type: string
    manufacturer?: string
    model?: string
    serial_number?: string
  }): Promise<{ success: boolean; device_id: string; message: string }> {
    return request.post('/api/v1/mp/device/devices/bind', data)
  },

  /**
   * 解绑设备
   */
  unbindDevice(deviceId: string): Promise<{ success: boolean; message: string }> {
    return request.delete(`/api/v1/mp/device/devices/${deviceId}`)
  },

  /**
   * 手动记录血糖
   */
  recordGlucose(data: {
    value: number
    meal_tag?: string
    timestamp?: string
    notes?: string
  }): Promise<{
    success: boolean
    reading_id: number
    value: number
    value_mgdl: number
    recorded_at: string
  }> {
    return request.post('/api/v1/mp/device/glucose/manual', data)
  },

  /**
   * 获取血糖数据
   */
  getGlucoseReadings(params?: {
    start_date?: string
    end_date?: string
    limit?: number
  }): Promise<{
    readings: GlucoseReading[]
    statistics: GlucoseStatistics
    period: { start?: string; end?: string; count: number }
  }> {
    return request.get('/api/v1/mp/device/glucose', { params, silentError: true })
  },

  /**
   * 获取当前血糖
   */
  getCurrentGlucose(): Promise<{
    value?: number
    value_mgdl?: number
    trend?: string
    trend_arrow?: string
    timestamp?: string
    source?: string
    minutes_ago?: number
    in_range?: boolean
    status?: string
    message?: string
  }> {
    return request.get('/api/v1/mp/device/glucose/current', { silentError: true })
  },

  /**
   * 获取血糖日图表数据
   */
  getGlucoseDailyChart(date: string): Promise<{
    date: string
    chart_data: {
      timestamps: string[]
      values: number[]
      target_low: number
      target_high: number
    }
    daily_stats?: {
      avg: number
      min: number
      max: number
      tir: number
      count: number
    }
    message?: string
  }> {
    return request.get('/api/v1/mp/device/glucose/chart/daily', { params: { date }, silentError: true })
  },

  /**
   * 记录体重
   */
  recordWeight(data: {
    weight_kg: number
    body_fat_percent?: number
    muscle_mass_kg?: number
    timestamp?: string
  }): Promise<{
    success: boolean
    record_id: number
    weight_kg: number
    recorded_at: string
  }> {
    return request.post('/api/v1/mp/device/weight', data)
  },

  /**
   * 获取体重记录
   */
  getWeightRecords(params?: {
    start_date?: string
    end_date?: string
    limit?: number
  }): Promise<{
    records: WeightRecord[]
    trend?: {
      direction: string
      period_days: number
      weight_change_kg: number
    }
    total: number
  }> {
    return request.get('/api/v1/mp/device/weight', { params, silentError: true })
  },

  /**
   * 记录血压
   */
  recordBloodPressure(data: {
    systolic: number
    diastolic: number
    pulse?: number
    timestamp?: string
  }): Promise<{
    success: boolean
    record_id: number
    systolic: number
    diastolic: number
    classification: string
    recorded_at: string
  }> {
    return request.post('/api/v1/mp/device/blood-pressure', data)
  },

  /**
   * 获取血压记录
   */
  getBloodPressureRecords(limit?: number): Promise<{
    records: BloodPressureRecord[]
    statistics: {
      avg_systolic?: number
      avg_diastolic?: number
      count: number
    }
    total: number
  }> {
    return request.get('/api/v1/mp/device/blood-pressure', { params: { limit }, silentError: true })
  },

  /**
   * 获取今日仪表盘
   */
  getTodayDashboard(): Promise<DashboardData> {
    return request.get('/api/v1/mp/device/dashboard/today', { silentError: true })
  },

  /**
   * 同步设备数据
   */
  syncDeviceData(deviceId: string, data: any): Promise<{
    success: boolean
    device_id: string
    records_processed: number
    synced_at: string
  }> {
    return request.post('/api/v1/mp/device/sync', { device_id: deviceId, data })
  },

  // ============================================
  // Phase 2: 睡眠/活动/心率/HRV
  // ============================================

  /**
   * 获取昨晚睡眠数据
   */
  getLastNightSleep(): Promise<{
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
    message?: string
  }> {
    return request.get('/api/v1/mp/device/sleep/last-night', { silentError: true })
  },

  /**
   * 获取睡眠记录
   */
  getSleepRecords(params?: {
    start_date?: string
    end_date?: string
  }): Promise<{
    records: Array<{
      date: string
      duration_min: number
      score?: number
      deep_min: number
      light_min: number
      rem_min: number
      awake_min: number
    }>
    weekly_avg: {
      duration_min: number
      sleep_score: number
    }
    total: number
  }> {
    return request.get('/api/v1/mp/device/sleep', { params, silentError: true })
  },

  /**
   * 获取活动数据
   */
  getActivityRecords(params?: {
    start_date?: string
    end_date?: string
  }): Promise<{
    records: Array<{
      date: string
      steps: number
      distance_km: number
      calories_active: number
      active_minutes: number
    }>
    total: number
  }> {
    return request.get('/api/v1/mp/device/activity', { params, silentError: true })
  },

  /**
   * 获取心率数据
   */
  getHeartRateData(params?: {
    start_date?: string
    end_date?: string
  }): Promise<{
    date: string | null
    readings: Array<{
      hr: number
      activity_type?: string
      timestamp: string
    }>
    statistics: {
      resting_hr?: number
      avg_hr?: number
      max_hr?: number
      min_hr?: number
      count: number
    }
  }> {
    return request.get('/api/v1/mp/device/heart-rate', { params, silentError: true })
  },

  /**
   * 获取 HRV 数据
   */
  getHRVData(params?: {
    start_date?: string
    end_date?: string
  }): Promise<{
    readings: Array<{
      sdnn: number
      rmssd: number
      lf_hf_ratio?: number
      stress_score?: number
      recovery_score?: number
      timestamp: string
    }>
    statistics: {
      avg_hrv?: number
      avg_stress?: number
      trend?: string
      count: number
    }
  }> {
    return request.get('/api/v1/mp/device/hrv', { params, silentError: true })
  }
}
