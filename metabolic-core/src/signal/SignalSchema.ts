/**
 * Signal Schema - 设备信号数据结构定义
 * 支持: CGM / BP / HRV / Scale / Watch
 */

export type DeviceType = 'cgm' | 'bp' | 'hrv' | 'scale' | 'watch';

export type MetricType =
  | 'glucose'
  | 'systolic_bp'
  | 'diastolic_bp'
  | 'rmssd'
  | 'sdnn'
  | 'fat_percent'
  | 'weight'
  | 'steps'
  | 'heart_rate'
  | 'sleep_duration'
  | 'deep_sleep_ratio';

export type QualityFlag = 'valid' | 'noise' | 'missing' | 'calibrating';

export type SleepState = 'awake' | 'light_sleep' | 'deep_sleep' | 'rem';

export type ActivityState = 'rest' | 'walk' | 'exercise' | 'sedentary';

/**
 * 信号上下文 - 记录采集时的场景信息
 */
export interface SignalContext {
  /** 是否空腹 */
  fasting?: boolean;
  /** 餐后分钟数 */
  post_meal_minutes?: number;
  /** 餐食类型 */
  meal_type?: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  /** 睡眠状态 */
  sleep_state?: SleepState;
  /** 活动状态 */
  activity_state?: ActivityState;
  /** 情绪状态 (1-10) */
  mood_score?: number;
  /** 压力水平 (1-10) */
  stress_level?: number;
  /** 用药情况 */
  medication?: string[];
}

/**
 * 信号记录 - 单条设备数据
 */
export interface SignalRecord {
  /** 信号唯一ID */
  signal_id: string;
  /** 用户ID */
  user_id: string;
  /** 设备类型 */
  device_type: DeviceType;
  /** 设备ID (可选) */
  device_id?: string;
  /** 指标类型 */
  metric: MetricType;
  /** 数值 */
  value: number;
  /** 单位 */
  unit: string;
  /** 采集时间 (ISO 8601) */
  timestamp: string;
  /** 上下文信息 */
  context: SignalContext;
  /** 数据质量标记 */
  quality_flag: QualityFlag;
  /** 原始数据 (可选，用于调试) */
  raw_data?: any;
  /** 数据来源 */
  source?: string;
  /** 创建时间 */
  created_at?: string;
}

/**
 * 信号批次 - 批量信号数据
 */
export interface SignalBatch {
  batch_id: string;
  user_id: string;
  device_type: DeviceType;
  signals: SignalRecord[];
  time_range: {
    start: string;
    end: string;
  };
  summary?: {
    count: number;
    valid_count: number;
    mean?: number;
    min?: number;
    max?: number;
    std?: number;
  };
}

/**
 * 设备配置
 */
export interface DeviceConfig {
  device_type: DeviceType;
  supported_metrics: MetricType[];
  sampling_interval_seconds: number;
  data_format: 'json' | 'csv' | 'binary';
  normalization_rules?: {
    metric: MetricType;
    min_valid: number;
    max_valid: number;
    unit_conversion?: { from: string; to: string; factor: number };
  }[];
}

/**
 * 默认设备配置
 */
export const DEFAULT_DEVICE_CONFIGS: DeviceConfig[] = [
  {
    device_type: 'cgm',
    supported_metrics: ['glucose'],
    sampling_interval_seconds: 300, // 5分钟
    data_format: 'json',
    normalization_rules: [
      { metric: 'glucose', min_valid: 2.0, max_valid: 25.0 }
    ]
  },
  {
    device_type: 'bp',
    supported_metrics: ['systolic_bp', 'diastolic_bp', 'heart_rate'],
    sampling_interval_seconds: 0, // 手动测量
    data_format: 'json',
    normalization_rules: [
      { metric: 'systolic_bp', min_valid: 60, max_valid: 250 },
      { metric: 'diastolic_bp', min_valid: 40, max_valid: 150 }
    ]
  },
  {
    device_type: 'hrv',
    supported_metrics: ['rmssd', 'sdnn', 'heart_rate'],
    sampling_interval_seconds: 60,
    data_format: 'json',
    normalization_rules: [
      { metric: 'rmssd', min_valid: 5, max_valid: 200 },
      { metric: 'sdnn', min_valid: 10, max_valid: 250 }
    ]
  },
  {
    device_type: 'scale',
    supported_metrics: ['weight', 'fat_percent'],
    sampling_interval_seconds: 0,
    data_format: 'json',
    normalization_rules: [
      { metric: 'weight', min_valid: 20, max_valid: 300 },
      { metric: 'fat_percent', min_valid: 3, max_valid: 60 }
    ]
  },
  {
    device_type: 'watch',
    supported_metrics: ['steps', 'heart_rate', 'sleep_duration', 'deep_sleep_ratio'],
    sampling_interval_seconds: 60,
    data_format: 'json',
    normalization_rules: [
      { metric: 'steps', min_valid: 0, max_valid: 100000 },
      { metric: 'sleep_duration', min_valid: 0, max_valid: 24 }
    ]
  }
];
