/**
 * Phenotype Mapping Library - 表型映射库
 * 基于信号模式识别行为表型和潜在需求
 */

import { v4 as uuidv4 } from 'uuid';
import { SignalsSummary } from '../trajectory/TrajectorySchema';

/**
 * 风险等级
 */
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

/**
 * 表型映射记录
 */
export interface PhenotypeMapping {
  /** 映射ID */
  mapping_id: string;
  /** 表型名称 */
  phenotype_name: string;
  /** 表型类别 */
  category: 'metabolic' | 'behavioral' | 'psychological' | 'composite';
  /** 输入信号模式 */
  input_signals: {
    required: string[];
    optional?: string[];
    thresholds?: Record<string, { min?: number; max?: number }>;
  };
  /** 检测到的模式 */
  detected_patterns: string[];
  /** 可能的行为 */
  probable_behaviors: string[];
  /** 潜在需求 */
  latent_needs: string[];
  /** 推荐的干预杠杆 */
  recommended_levers: string[];
  /** 风险等级 */
  risk_level: RiskLevel;
  /** 轨迹条件 */
  trajectory_conditions?: {
    requires_trend?: string[];
    min_days?: number;
    stage_prerequisite?: string[];
  };
  /** 置信度 */
  confidence_score?: number;
  /** 版本 */
  version: string;
  /** 描述 */
  description?: string;
}

/**
 * 表型匹配结果
 */
export interface PhenotypeMatchResult {
  phenotype: PhenotypeMapping;
  match_score: number;
  matched_patterns: string[];
  missing_signals?: string[];
}

/**
 * 预定义表型库
 */
export const PREDEFINED_PHENOTYPES: PhenotypeMapping[] = [
  {
    mapping_id: 'PHE-001',
    phenotype_name: '餐后高血糖型',
    category: 'metabolic',
    input_signals: {
      required: ['glucose'],
      thresholds: {
        postprandial_peak: { min: 10 }
      }
    },
    detected_patterns: ['餐后血糖飙升', '进餐速度快', '碳水为主'],
    probable_behaviors: ['快速进食', '主食优先', '缺乏餐后活动'],
    latent_needs: ['即时满足', '压力释放', '时间紧迫'],
    recommended_levers: ['进餐顺序调整', '餐后散步', '慢食训练'],
    risk_level: 'medium',
    trajectory_conditions: {
      min_days: 3
    },
    confidence_score: 0.85,
    version: '1.0',
    description: '餐后2小时血糖峰值持续高于10 mmol/L'
  },
  {
    mapping_id: 'PHE-002',
    phenotype_name: '黎明现象型',
    category: 'metabolic',
    input_signals: {
      required: ['glucose'],
      thresholds: {
        dawn_glucose_rise: { min: 1.5 }
      }
    },
    detected_patterns: ['清晨血糖升高', '空腹高于睡前', '激素波动'],
    probable_behaviors: ['晚餐过晚', '睡眠不规律', '早餐延迟'],
    latent_needs: ['睡眠改善', '作息规律', '晚餐时间调整'],
    recommended_levers: ['睡前轻食', '定时早餐', '睡眠卫生'],
    risk_level: 'medium',
    trajectory_conditions: {
      min_days: 7,
      requires_trend: ['dawn_glucose_pattern']
    },
    confidence_score: 0.75,
    version: '1.0',
    description: '凌晨4-8点血糖自动升高超过1.5 mmol/L'
  },
  {
    mapping_id: 'PHE-003',
    phenotype_name: '血糖波动敏感型',
    category: 'metabolic',
    input_signals: {
      required: ['glucose'],
      thresholds: {
        variability_cv: { min: 36 }
      }
    },
    detected_patterns: ['血糖大幅波动', '情绪影响大', '饮食不规律'],
    probable_behaviors: ['不定时进餐', '情绪化饮食', '运动不规律'],
    latent_needs: ['情绪管理', '规律作息', '预判能力'],
    recommended_levers: ['定时定量', '情绪觉察', 'CGM实时反馈'],
    risk_level: 'high',
    confidence_score: 0.9,
    version: '1.0',
    description: '血糖变异系数CV超过36%'
  },
  {
    mapping_id: 'PHE-004',
    phenotype_name: '夜间低血糖型',
    category: 'metabolic',
    input_signals: {
      required: ['glucose'],
      thresholds: {
        night_hypo_count: { min: 1 }
      }
    },
    detected_patterns: ['夜间血糖过低', '晚餐碳水不足', '运动过量'],
    probable_behaviors: ['晚餐控制过严', '睡前运动', '药物调整需求'],
    latent_needs: ['安全感', '睡眠质量', '能量平衡'],
    recommended_levers: ['睡前加餐', '晚餐调整', '药物复核'],
    risk_level: 'high',
    trajectory_conditions: {
      min_days: 3
    },
    confidence_score: 0.95,
    version: '1.0',
    description: '夜间(0-6点)出现低血糖(<3.9 mmol/L)'
  },
  {
    mapping_id: 'PHE-005',
    phenotype_name: '压力应激型',
    category: 'psychological',
    input_signals: {
      required: ['hrv', 'glucose'],
      thresholds: {
        rmssd: { max: 20 },
        glucose_spike_stress: { min: 2 }
      }
    },
    detected_patterns: ['HRV降低', '应激性血糖升高', '睡眠质量差'],
    probable_behaviors: ['高压工作', '缺乏放松', '情绪压抑'],
    latent_needs: ['压力释放', '情绪表达', '社会支持'],
    recommended_levers: ['呼吸练习', '正念冥想', '社交连接'],
    risk_level: 'medium',
    confidence_score: 0.8,
    version: '1.0',
    description: 'HRV持续偏低伴随应激性血糖升高'
  },
  {
    mapping_id: 'PHE-006',
    phenotype_name: '久坐代谢型',
    category: 'behavioral',
    input_signals: {
      required: ['steps', 'glucose'],
      thresholds: {
        daily_steps: { max: 5000 },
        sedentary_hours: { min: 8 }
      }
    },
    detected_patterns: ['日均步数低', '长时间静坐', '胰岛素抵抗趋势'],
    probable_behaviors: ['办公室工作', '缺乏运动习惯', '交通依赖'],
    latent_needs: ['时间管理', '运动启动', '工作整合'],
    recommended_levers: ['番茄钟站立', '步行会议', '通勤运动'],
    risk_level: 'medium',
    confidence_score: 0.85,
    version: '1.0',
    description: '日均步数低于5000且久坐时间超过8小时'
  },
  {
    mapping_id: 'PHE-007',
    phenotype_name: '睡眠-代谢失调型',
    category: 'composite',
    input_signals: {
      required: ['sleep', 'glucose', 'hrv'],
      thresholds: {
        sleep_duration: { max: 6 },
        deep_sleep_ratio: { max: 15 }
      }
    },
    detected_patterns: ['睡眠不足', '深睡比例低', '次日血糖波动大'],
    probable_behaviors: ['熬夜', '电子设备依赖', '咖啡因依赖'],
    latent_needs: ['睡眠卫生', '压力管理', '昼夜节律重建'],
    recommended_levers: ['睡眠时间锚定', '蓝光过滤', '咖啡因断点'],
    risk_level: 'high',
    trajectory_conditions: {
      min_days: 7,
      requires_trend: ['sleep_glucose_correlation']
    },
    confidence_score: 0.85,
    version: '1.0',
    description: '睡眠时长<6小时或深睡比例<15%，伴随代谢指标异常'
  }
];

/**
 * 表型映射服务
 */
export class PhenotypeMappingService {
  private phenotypes: Map<string, PhenotypeMapping> = new Map();

  constructor() {
    // 加载预定义表型
    PREDEFINED_PHENOTYPES.forEach(p => {
      this.phenotypes.set(p.mapping_id, p);
    });
  }

  /**
   * 匹配表型
   */
  matchPhenotypes(signalsSummary: SignalsSummary): PhenotypeMatchResult[] {
    const results: PhenotypeMatchResult[] = [];

    for (const phenotype of this.phenotypes.values()) {
      const matchResult = this.evaluateMatch(phenotype, signalsSummary);
      if (matchResult.match_score > 0.5) {
        results.push(matchResult);
      }
    }

    // 按匹配分数排序
    return results.sort((a, b) => b.match_score - a.match_score);
  }

  /**
   * 评估单个表型匹配
   */
  private evaluateMatch(
    phenotype: PhenotypeMapping,
    summary: SignalsSummary
  ): PhenotypeMatchResult {
    let matchedPatterns: string[] = [];
    let totalScore = 0;
    let maxScore = 0;

    // 检查阈值条件
    const thresholds = phenotype.input_signals.thresholds || {};

    for (const [metric, threshold] of Object.entries(thresholds)) {
      maxScore += 1;
      const value = this.getMetricValue(summary, metric);

      if (value !== undefined) {
        let matches = true;
        if (threshold.min !== undefined && value < threshold.min) matches = false;
        if (threshold.max !== undefined && value > threshold.max) matches = false;

        if (matches) {
          totalScore += 1;
          matchedPatterns.push(`${metric}: ${value}`);
        }
      }
    }

    const matchScore = maxScore > 0 ? totalScore / maxScore : 0;

    return {
      phenotype,
      match_score: matchScore * (phenotype.confidence_score || 1),
      matched_patterns: matchedPatterns
    };
  }

  /**
   * 获取指标值
   */
  private getMetricValue(summary: SignalsSummary, metric: string): number | undefined {
    const metricMap: Record<string, number | undefined> = {
      postprandial_peak: summary.postprandial_peak,
      variability_cv: summary.variability_cv,
      night_hypo_count: summary.night_hypo_count,
      rmssd: summary.rmssd_mean,
      daily_steps: summary.daily_steps_mean,
      sleep_duration: summary.sleep_duration_mean,
      deep_sleep_ratio: summary.deep_sleep_ratio_mean,
      time_in_range: summary.time_in_range
    };
    return metricMap[metric];
  }

  /**
   * 注册新表型
   */
  registerPhenotype(phenotype: Omit<PhenotypeMapping, 'mapping_id'>): PhenotypeMapping {
    const newPhenotype: PhenotypeMapping = {
      mapping_id: `PHE-${uuidv4().slice(0, 8).toUpperCase()}`,
      ...phenotype
    };
    this.phenotypes.set(newPhenotype.mapping_id, newPhenotype);
    return newPhenotype;
  }

  /**
   * 获取所有表型
   */
  getAllPhenotypes(): PhenotypeMapping[] {
    return Array.from(this.phenotypes.values());
  }

  /**
   * 根据ID获取表型
   */
  getPhenotypeById(id: string): PhenotypeMapping | undefined {
    return this.phenotypes.get(id);
  }

  /**
   * 按类别获取表型
   */
  getPhenotypesByCategory(category: PhenotypeMapping['category']): PhenotypeMapping[] {
    return Array.from(this.phenotypes.values()).filter(p => p.category === category);
  }
}

// 导出单例
export const phenotypeMappingService = new PhenotypeMappingService();
