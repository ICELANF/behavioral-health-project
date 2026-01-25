/**
 * Signal Normalization Service - 设备信号标准化服务
 * 将不同设备的原始数据转换为统一的 SignalRecord 格式
 */

import { v4 as uuidv4 } from 'uuid';
import {
  SignalRecord,
  SignalBatch,
  DeviceType,
  MetricType,
  QualityFlag,
  SignalContext,
  DEFAULT_DEVICE_CONFIGS,
  DeviceConfig
} from './SignalSchema';

/**
 * 原始信号数据输入格式
 */
export interface RawSignalInput {
  user_id: string;
  device_type: DeviceType;
  device_id?: string;
  metric: MetricType;
  value: number | string;
  unit?: string;
  timestamp: string | Date;
  context?: Partial<SignalContext>;
  raw_data?: any;
  source?: string;
}

/**
 * 标准化结果
 */
export interface NormalizationResult {
  success: boolean;
  record?: SignalRecord;
  error?: string;
  warnings?: string[];
}

/**
 * 信号标准化服务
 */
export class SignalNormalizationService {
  private deviceConfigs: Map<DeviceType, DeviceConfig>;

  constructor() {
    this.deviceConfigs = new Map();
    DEFAULT_DEVICE_CONFIGS.forEach(config => {
      this.deviceConfigs.set(config.device_type, config);
    });
  }

  /**
   * 标准化单条信号
   */
  normalize(raw: RawSignalInput): NormalizationResult {
    const warnings: string[] = [];

    try {
      // 验证必填字段
      if (!raw.user_id || !raw.device_type || !raw.metric || raw.value === undefined) {
        return {
          success: false,
          error: 'Missing required fields: user_id, device_type, metric, value'
        };
      }

      // 解析数值
      const numericValue = typeof raw.value === 'string' ? parseFloat(raw.value) : raw.value;
      if (isNaN(numericValue)) {
        return {
          success: false,
          error: `Invalid numeric value: ${raw.value}`
        };
      }

      // 获取设备配置
      const config = this.deviceConfigs.get(raw.device_type);

      // 验证指标是否支持
      if (config && !config.supported_metrics.includes(raw.metric)) {
        warnings.push(`Metric ${raw.metric} not in standard list for ${raw.device_type}`);
      }

      // 数据质量检查
      let qualityFlag: QualityFlag = 'valid';
      if (config) {
        const rule = config.normalization_rules?.find(r => r.metric === raw.metric);
        if (rule) {
          if (numericValue < rule.min_valid || numericValue > rule.max_valid) {
            qualityFlag = 'noise';
            warnings.push(`Value ${numericValue} outside valid range [${rule.min_valid}, ${rule.max_valid}]`);
          }
        }
      }

      // 标准化时间戳
      const timestamp = this.normalizeTimestamp(raw.timestamp);

      // 推断单位
      const unit = raw.unit || this.inferUnit(raw.metric);

      // 构建标准记录
      const record: SignalRecord = {
        signal_id: uuidv4(),
        user_id: raw.user_id,
        device_type: raw.device_type,
        device_id: raw.device_id,
        metric: raw.metric,
        value: numericValue,
        unit,
        timestamp,
        context: this.normalizeContext(raw.context || {}),
        quality_flag: qualityFlag,
        raw_data: raw.raw_data,
        source: raw.source,
        created_at: new Date().toISOString()
      };

      return {
        success: true,
        record,
        warnings: warnings.length > 0 ? warnings : undefined
      };

    } catch (error) {
      return {
        success: false,
        error: `Normalization error: ${error}`
      };
    }
  }

  /**
   * 批量标准化
   */
  normalizeBatch(rawSignals: RawSignalInput[]): SignalBatch {
    const validRecords: SignalRecord[] = [];
    const errors: string[] = [];

    rawSignals.forEach((raw, index) => {
      const result = this.normalize(raw);
      if (result.success && result.record) {
        validRecords.push(result.record);
      } else {
        errors.push(`Signal ${index}: ${result.error}`);
      }
    });

    // 确定时间范围
    let startTime = '';
    let endTime = '';
    if (validRecords.length > 0) {
      const timestamps = validRecords.map(r => r.timestamp).sort();
      startTime = timestamps[0];
      endTime = timestamps[timestamps.length - 1];
    }

    // 计算统计摘要
    const values = validRecords.map(r => r.value);
    const summary = values.length > 0 ? {
      count: rawSignals.length,
      valid_count: validRecords.length,
      mean: values.reduce((a, b) => a + b, 0) / values.length,
      min: Math.min(...values),
      max: Math.max(...values),
      std: this.calculateStd(values)
    } : {
      count: rawSignals.length,
      valid_count: 0
    };

    return {
      batch_id: uuidv4(),
      user_id: rawSignals[0]?.user_id || 'unknown',
      device_type: rawSignals[0]?.device_type || 'cgm',
      signals: validRecords,
      time_range: {
        start: startTime,
        end: endTime
      },
      summary
    };
  }

  /**
   * 标准化时间戳
   */
  private normalizeTimestamp(input: string | Date): string {
    if (input instanceof Date) {
      return input.toISOString();
    }
    // 尝试解析各种格式
    const date = new Date(input);
    if (isNaN(date.getTime())) {
      // 如果无法解析，使用当前时间
      return new Date().toISOString();
    }
    return date.toISOString();
  }

  /**
   * 标准化上下文
   */
  private normalizeContext(context: Partial<SignalContext>): SignalContext {
    return {
      fasting: context.fasting,
      post_meal_minutes: context.post_meal_minutes,
      meal_type: context.meal_type,
      sleep_state: context.sleep_state,
      activity_state: context.activity_state || 'rest',
      mood_score: context.mood_score,
      stress_level: context.stress_level,
      medication: context.medication
    };
  }

  /**
   * 推断单位
   */
  private inferUnit(metric: MetricType): string {
    const unitMap: Record<MetricType, string> = {
      glucose: 'mmol/L',
      systolic_bp: 'mmHg',
      diastolic_bp: 'mmHg',
      rmssd: 'ms',
      sdnn: 'ms',
      fat_percent: '%',
      weight: 'kg',
      steps: 'steps',
      heart_rate: 'bpm',
      sleep_duration: 'hours',
      deep_sleep_ratio: '%'
    };
    return unitMap[metric] || 'unknown';
  }

  /**
   * 计算标准差
   */
  private calculateStd(values: number[]): number {
    if (values.length === 0) return 0;
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const squaredDiffs = values.map(v => Math.pow(v - mean, 2));
    return Math.sqrt(squaredDiffs.reduce((a, b) => a + b, 0) / values.length);
  }

  /**
   * 注册自定义设备配置
   */
  registerDeviceConfig(config: DeviceConfig): void {
    this.deviceConfigs.set(config.device_type, config);
  }

  /**
   * 获取设备配置
   */
  getDeviceConfig(deviceType: DeviceType): DeviceConfig | undefined {
    return this.deviceConfigs.get(deviceType);
  }
}

// 导出单例
export const signalNormalizationService = new SignalNormalizationService();
