/**
 * Trajectory Schema - 生命线轨迹数据结构定义
 * 连续轨迹建模：代谢 × 行为 × 干预 × 阶段迁移
 */

/**
 * 时间窗口类型
 */
export type TimeWindow =
  | 'last_24_hours'
  | 'last_7_days'
  | 'last_14_days'
  | 'last_30_days'
  | 'last_90_days'
  | 'custom';

/**
 * 趋势方向
 */
export type TrendDirection = 'up' | 'down' | 'stable' | 'volatile';

/**
 * 行为阶段 (TTM + 五层次心理准备度)
 */
export type BehaviorStage =
  | 'precontemplation'  // 前意向期 / 完全对抗
  | 'contemplation'     // 意向期 / 抗拒与反思
  | 'preparation'       // 准备期 / 妥协与接受
  | 'action'            // 行动期 / 顺应与调整
  | 'maintenance';      // 维持期 / 全面臣服

/**
 * 信号摘要 - 时间窗口内的统计数据
 */
export interface SignalsSummary {
  // CGM 相关
  fasting_glucose_mean?: number;
  fasting_glucose_std?: number;
  postprandial_peak?: number;
  postprandial_mean?: number;
  time_in_range?: number;  // TIR: 3.9-10.0 mmol/L
  time_below_range?: number;  // TBR: <3.9 mmol/L
  time_above_range?: number;  // TAR: >10.0 mmol/L
  variability_cv?: number;  // 变异系数
  night_hypo_count?: number;  // 夜间低血糖次数
  dawn_phenomenon?: boolean;  // 黎明现象

  // BP 相关
  systolic_mean?: number;
  diastolic_mean?: number;
  bp_variability?: number;

  // HRV 相关
  rmssd_mean?: number;
  sdnn_mean?: number;
  hrv_trend?: TrendDirection;
  stress_index?: number;

  // 活动相关
  daily_steps_mean?: number;
  active_minutes_mean?: number;
  sleep_duration_mean?: number;
  deep_sleep_ratio_mean?: number;

  // 体重相关
  weight_change?: number;
  fat_percent_change?: number;
}

/**
 * 代谢特征集 - 用于表型匹配和风险预测
 * Metabolic Feature Set for phenotype matching and risk prediction
 */
export interface MetabolicFeatureSet {
  feature_id: string;
  time_window: '24h' | '3d' | '7d' | '14d';
  glucose_features: {
    fasting_mean: number;
    postprandial_peak: number;
    time_to_peak: number;
    variability_cv: number;
    night_hypo_count: number;
  };
  hrv_features?: {
    rmssd_mean: number;
    lf_hf_ratio: number;
    recovery_score: number;
  };
  activity_features?: {
    steps_mean: number;
    sedentary_ratio: number;
  };
}

/**
 * 行为事件
 */
export interface BehaviorEvent {
  event_id: string;
  time: string;
  event_type:
    | 'meal'
    | 'exercise'
    | 'medication'
    | 'sleep'
    | 'stress'
    | 'task_completion'
    | 'task_skip'
    | 'coach_interaction';
  event: string;
  details?: Record<string, any>;
  impact?: {
    metric: string;
    direction: TrendDirection;
    magnitude: 'low' | 'medium' | 'high';
  };
}

/**
 * 阶段迁移记录
 */
export interface StageTransition {
  transition_id: string;
  from: BehaviorStage;
  to: BehaviorStage;
  date: string;
  trigger?: string;
  confidence: number;
  supporting_evidence?: string[];
}

/**
 * 干预记录
 */
export interface InterventionApplied {
  intervention_id: string;
  name: string;
  domain: 'diet' | 'exercise' | 'sleep' | 'emotion' | 'medication';
  start_date: string;
  end_date?: string;
  adherence_rate?: number;
  outcome?: {
    effective: boolean;
    metrics_improved?: string[];
    notes?: string;
  };
}

/**
 * 结果指标
 */
export interface TrajectoryOutcomes {
  // 血糖改善
  fasting_glucose_reduction?: number;
  ppg_reduction?: number;  // 餐后血糖降低
  tir_improvement?: number;  // TIR提升

  // 行为改善
  adherence_score?: number;  // 依从性评分 (0-100)
  task_completion_rate?: number;
  habit_strength_index?: number;

  // 健康改善
  weight_loss?: number;
  bp_reduction?: { systolic: number; diastolic: number };
  hrv_improvement?: number;

  // 心理改善
  stress_reduction?: number;
  efficacy_improvement?: number;
}

/**
 * 轨迹记录 - 核心资产
 */
export interface TrajectoryRecord {
  /** 轨迹唯一ID */
  trajectory_id: string;
  /** 用户ID */
  user_id: string;
  /** 时间窗口 */
  time_window: TimeWindow;
  /** 时间范围 */
  time_range?: {
    start: string;
    end: string;
  };
  /** 信号摘要 */
  signals_summary: SignalsSummary;
  /** 行为事件列表 */
  behavior_events: BehaviorEvent[];
  /** 阶段迁移历史 */
  stage_transitions: StageTransition[];
  /** 当前阶段 */
  current_stage?: BehaviorStage;
  /** 已应用的干预 */
  interventions_applied: InterventionApplied[];
  /** 结果指标 */
  outcomes: TrajectoryOutcomes;
  /** 风险标记 */
  risk_flags?: string[];
  /** 洞察要点 */
  insights?: string[];
  /** 下一步建议 */
  next_actions?: string[];
  /** 版本 */
  version: string;
  /** 创建时间 */
  created_at: string;
  /** 更新时间 */
  updated_at?: string;
}

/**
 * 轨迹快照 - 用于教练回放
 */
export interface TrajectorySnapshot {
  snapshot_id: string;
  trajectory_id: string;
  snapshot_date: string;
  stage: BehaviorStage;
  key_metrics: Record<string, number>;
  key_events: string[];
  coach_notes?: string;
}

/**
 * 用户潜在画像 - 综合用户状态评估
 * User Latent Profile for personalized intervention matching
 */
export interface UserLatentProfile {
  /** 用户ID */
  user_id: string;
  /** 代谢风险等级 */
  metabolic_risk_level: 'low' | 'medium' | 'high';
  /** 主导表型列表 */
  dominant_phenotypes: string[];
  /** 行为改变阶段 */
  behavior_stage: BehaviorStage;
  /** 动机水平 (0-100) */
  motivation_level: number;
  /** 依从倾向 */
  adherence_tendency: 'strong' | 'medium' | 'weak';
  /** 压力负荷 */
  stress_load: 'low' | 'medium' | 'high';
  /** 更新日志 */
  update_log: {
    timestamp: string;
    field: string;
    old_value: any;
    new_value: any;
    reason?: string;
  }[];
}
