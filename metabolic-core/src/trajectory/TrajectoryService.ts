/**
 * Trajectory Service - 生命线轨迹服务
 * 构建、更新、分析用户行为轨迹
 */

import { v4 as uuidv4 } from 'uuid';
import { SignalRecord, SignalBatch } from '../signal/SignalSchema';
import {
  TrajectoryRecord,
  TrajectorySnapshot,
  SignalsSummary,
  BehaviorEvent,
  StageTransition,
  InterventionApplied,
  TrajectoryOutcomes,
  TimeWindow,
  BehaviorStage,
  TrendDirection
} from './TrajectorySchema';

/**
 * 轨迹构建选项
 */
export interface TrajectoryBuildOptions {
  timeWindow: TimeWindow;
  includeEvents?: boolean;
  calculateOutcomes?: boolean;
  detectStageTransition?: boolean;
}

/**
 * 轨迹服务类
 */
export class TrajectoryService {
  private trajectories: Map<string, TrajectoryRecord[]> = new Map();

  /**
   * 构建新轨迹
   */
  buildTrajectory(
    userId: string,
    signals: SignalRecord[],
    options: TrajectoryBuildOptions = { timeWindow: 'last_7_days' }
  ): TrajectoryRecord {
    const trajectoryId = uuidv4();
    const now = new Date().toISOString();

    // 计算信号摘要
    const signalsSummary = this.calculateSignalsSummary(signals);

    // 确定时间范围
    const timeRange = this.getTimeRange(signals);

    // 构建轨迹记录
    const trajectory: TrajectoryRecord = {
      trajectory_id: trajectoryId,
      user_id: userId,
      time_window: options.timeWindow,
      time_range: timeRange,
      signals_summary: signalsSummary,
      behavior_events: [],
      stage_transitions: [],
      current_stage: this.inferCurrentStage(signalsSummary),
      interventions_applied: [],
      outcomes: {},
      risk_flags: this.detectRiskFlags(signalsSummary),
      insights: this.generateInsights(signalsSummary),
      next_actions: [],
      version: '1.0',
      created_at: now
    };

    // 保存轨迹
    this.saveTrajectory(userId, trajectory);

    return trajectory;
  }

  /**
   * 更新轨迹
   */
  updateTrajectory(
    trajectoryId: string,
    updates: Partial<TrajectoryRecord>
  ): TrajectoryRecord | null {
    for (const [userId, trajectories] of this.trajectories.entries()) {
      const index = trajectories.findIndex(t => t.trajectory_id === trajectoryId);
      if (index !== -1) {
        const updated = {
          ...trajectories[index],
          ...updates,
          updated_at: new Date().toISOString()
        };
        trajectories[index] = updated;
        return updated;
      }
    }
    return null;
  }

  /**
   * 添加行为事件
   */
  addBehaviorEvent(
    trajectoryId: string,
    event: Omit<BehaviorEvent, 'event_id'>
  ): BehaviorEvent | null {
    for (const [userId, trajectories] of this.trajectories.entries()) {
      const trajectory = trajectories.find(t => t.trajectory_id === trajectoryId);
      if (trajectory) {
        const behaviorEvent: BehaviorEvent = {
          event_id: uuidv4(),
          ...event
        };
        trajectory.behavior_events.push(behaviorEvent);
        trajectory.updated_at = new Date().toISOString();
        return behaviorEvent;
      }
    }
    return null;
  }

  /**
   * 记录阶段迁移
   */
  recordStageTransition(
    trajectoryId: string,
    from: BehaviorStage,
    to: BehaviorStage,
    trigger?: string
  ): StageTransition | null {
    for (const [userId, trajectories] of this.trajectories.entries()) {
      const trajectory = trajectories.find(t => t.trajectory_id === trajectoryId);
      if (trajectory) {
        const transition: StageTransition = {
          transition_id: uuidv4(),
          from,
          to,
          date: new Date().toISOString(),
          trigger,
          confidence: 0.8
        };
        trajectory.stage_transitions.push(transition);
        trajectory.current_stage = to;
        trajectory.updated_at = new Date().toISOString();
        return transition;
      }
    }
    return null;
  }

  /**
   * 应用干预
   */
  applyIntervention(
    trajectoryId: string,
    intervention: Omit<InterventionApplied, 'intervention_id'>
  ): InterventionApplied | null {
    for (const [userId, trajectories] of this.trajectories.entries()) {
      const trajectory = trajectories.find(t => t.trajectory_id === trajectoryId);
      if (trajectory) {
        const applied: InterventionApplied = {
          intervention_id: uuidv4(),
          ...intervention
        };
        trajectory.interventions_applied.push(applied);
        trajectory.updated_at = new Date().toISOString();
        return applied;
      }
    }
    return null;
  }

  /**
   * 获取用户轨迹
   */
  getUserTrajectories(userId: string): TrajectoryRecord[] {
    return this.trajectories.get(userId) || [];
  }

  /**
   * 获取最新轨迹
   */
  getLatestTrajectory(userId: string): TrajectoryRecord | null {
    const trajectories = this.getUserTrajectories(userId);
    if (trajectories.length === 0) return null;
    return trajectories.sort((a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )[0];
  }

  /**
   * 创建轨迹快照
   */
  createSnapshot(trajectoryId: string, coachNotes?: string): TrajectorySnapshot | null {
    for (const [userId, trajectories] of this.trajectories.entries()) {
      const trajectory = trajectories.find(t => t.trajectory_id === trajectoryId);
      if (trajectory) {
        return {
          snapshot_id: uuidv4(),
          trajectory_id: trajectoryId,
          snapshot_date: new Date().toISOString(),
          stage: trajectory.current_stage || 'precontemplation',
          key_metrics: this.extractKeyMetrics(trajectory.signals_summary),
          key_events: trajectory.behavior_events.slice(-5).map(e => e.event),
          coach_notes: coachNotes
        };
      }
    }
    return null;
  }

  /**
   * 计算信号摘要
   */
  private calculateSignalsSummary(signals: SignalRecord[]): SignalsSummary {
    const summary: SignalsSummary = {};

    // 按指标分组
    const byMetric = new Map<string, SignalRecord[]>();
    signals.forEach(s => {
      const existing = byMetric.get(s.metric) || [];
      existing.push(s);
      byMetric.set(s.metric, existing);
    });

    // 计算血糖指标
    const glucoseSignals = byMetric.get('glucose') || [];
    if (glucoseSignals.length > 0) {
      const values = glucoseSignals.map(s => s.value);
      const mean = values.reduce((a, b) => a + b, 0) / values.length;
      const std = this.calculateStd(values);

      summary.fasting_glucose_mean = mean;
      summary.fasting_glucose_std = std;
      summary.variability_cv = (std / mean) * 100;

      // TIR 计算
      const inRange = values.filter(v => v >= 3.9 && v <= 10.0).length;
      summary.time_in_range = (inRange / values.length) * 100;

      // 餐后峰值
      const postprandial = glucoseSignals.filter(
        s => s.context.post_meal_minutes && s.context.post_meal_minutes <= 120
      );
      if (postprandial.length > 0) {
        summary.postprandial_peak = Math.max(...postprandial.map(s => s.value));
        summary.postprandial_mean = postprandial.reduce((a, b) => a + b.value, 0) / postprandial.length;
      }

      // 夜间低血糖
      const nightHypo = glucoseSignals.filter(s => {
        const hour = new Date(s.timestamp).getHours();
        return hour >= 0 && hour < 6 && s.value < 3.9;
      });
      summary.night_hypo_count = nightHypo.length;
    }

    // HRV 指标
    const rmssdSignals = byMetric.get('rmssd') || [];
    if (rmssdSignals.length > 0) {
      summary.rmssd_mean = rmssdSignals.reduce((a, b) => a + b.value, 0) / rmssdSignals.length;
      summary.hrv_trend = this.detectTrend(rmssdSignals.map(s => s.value));
    }

    // 活动指标
    const stepsSignals = byMetric.get('steps') || [];
    if (stepsSignals.length > 0) {
      summary.daily_steps_mean = stepsSignals.reduce((a, b) => a + b.value, 0) / stepsSignals.length;
    }

    return summary;
  }

  /**
   * 检测趋势
   */
  private detectTrend(values: number[]): TrendDirection {
    if (values.length < 2) return 'stable';

    const firstHalf = values.slice(0, Math.floor(values.length / 2));
    const secondHalf = values.slice(Math.floor(values.length / 2));

    const firstMean = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
    const secondMean = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;

    const change = (secondMean - firstMean) / firstMean;

    if (change > 0.1) return 'up';
    if (change < -0.1) return 'down';
    return 'stable';
  }

  /**
   * 推断当前阶段
   */
  private inferCurrentStage(summary: SignalsSummary): BehaviorStage {
    // 简化的阶段推断逻辑
    if (summary.time_in_range && summary.time_in_range >= 70) {
      return 'maintenance';
    }
    if (summary.daily_steps_mean && summary.daily_steps_mean >= 8000) {
      return 'action';
    }
    if (summary.variability_cv && summary.variability_cv < 30) {
      return 'preparation';
    }
    return 'contemplation';
  }

  /**
   * 检测风险标记
   */
  private detectRiskFlags(summary: SignalsSummary): string[] {
    const flags: string[] = [];

    if (summary.night_hypo_count && summary.night_hypo_count > 0) {
      flags.push('night_hypoglycemia');
    }
    if (summary.variability_cv && summary.variability_cv > 36) {
      flags.push('high_glucose_variability');
    }
    if (summary.time_below_range && summary.time_below_range > 4) {
      flags.push('frequent_hypoglycemia');
    }
    if (summary.postprandial_peak && summary.postprandial_peak > 14) {
      flags.push('high_postprandial_spike');
    }

    return flags;
  }

  /**
   * 生成洞察
   */
  private generateInsights(summary: SignalsSummary): string[] {
    const insights: string[] = [];

    if (summary.time_in_range) {
      if (summary.time_in_range >= 70) {
        insights.push('血糖控制良好，TIR达标');
      } else if (summary.time_in_range >= 50) {
        insights.push('血糖控制中等，仍有改善空间');
      } else {
        insights.push('血糖波动较大，需加强管理');
      }
    }

    if (summary.hrv_trend === 'up') {
      insights.push('HRV呈上升趋势，压力管理有效');
    } else if (summary.hrv_trend === 'down') {
      insights.push('HRV呈下降趋势，建议关注压力和睡眠');
    }

    if (summary.daily_steps_mean) {
      if (summary.daily_steps_mean >= 10000) {
        insights.push('运动量充足，保持良好习惯');
      } else if (summary.daily_steps_mean < 5000) {
        insights.push('日均步数偏低，建议增加日常活动');
      }
    }

    return insights;
  }

  /**
   * 提取关键指标
   */
  private extractKeyMetrics(summary: SignalsSummary): Record<string, number> {
    const metrics: Record<string, number> = {};

    if (summary.fasting_glucose_mean !== undefined) {
      metrics.fasting_glucose = summary.fasting_glucose_mean;
    }
    if (summary.time_in_range !== undefined) {
      metrics.time_in_range = summary.time_in_range;
    }
    if (summary.rmssd_mean !== undefined) {
      metrics.rmssd = summary.rmssd_mean;
    }
    if (summary.daily_steps_mean !== undefined) {
      metrics.daily_steps = summary.daily_steps_mean;
    }

    return metrics;
  }

  /**
   * 获取时间范围
   */
  private getTimeRange(signals: SignalRecord[]): { start: string; end: string } {
    if (signals.length === 0) {
      const now = new Date().toISOString();
      return { start: now, end: now };
    }

    const timestamps = signals.map(s => s.timestamp).sort();
    return {
      start: timestamps[0],
      end: timestamps[timestamps.length - 1]
    };
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
   * 保存轨迹
   */
  private saveTrajectory(userId: string, trajectory: TrajectoryRecord): void {
    const existing = this.trajectories.get(userId) || [];
    existing.push(trajectory);
    this.trajectories.set(userId, existing);
  }
}

// 导出单例
export const trajectoryService = new TrajectoryService();
