/**
 * Orchestrator - 决策编排器
 * 系统核心，协调信号处理、轨迹分析、干预规划的完整流程
 */

import { v4 as uuidv4 } from 'uuid';
import { SignalRecord } from '../signal/SignalSchema';
import {
  signalNormalizationService,
  RawSignalInput,
  NormalizationResult
} from '../signal/SignalNormalizationService';
import {
  trajectoryService,
  TrajectoryBuildOptions
} from '../trajectory/TrajectoryService';
import { TrajectoryRecord, BehaviorStage } from '../trajectory/TrajectorySchema';
import { phenotypeMappingService, PhenotypeMatchResult } from '../libraries/PhenotypeMapping';
import { interventionPlaybookService, InterventionPlan } from '../libraries/InterventionPlaybook';
import { behaviorChangeEngineService, StageAssessment, BehaviorLock } from '../libraries/BehaviorChangeEngine';
import { contentMaterialService } from '../libraries/ContentMaterial';
import { commercialResourceService } from '../libraries/CommercialResource';
import { interventionPlanner, InterventionPlanSummary } from './InterventionPlanner';
import { libraryManager } from '../registry/LibraryManager';

/**
 * 用户会话
 */
export interface UserSession {
  /** 会话ID */
  session_id: string;
  /** 用户ID */
  user_id: string;
  /** 当前轨迹 */
  current_trajectory?: TrajectoryRecord;
  /** 当前干预计划 */
  current_plan?: InterventionPlan;
  /** 识别的表型 */
  phenotypes: PhenotypeMatchResult[];
  /** 阶段评估 */
  stage_assessment?: StageAssessment;
  /** 行为锁定 */
  behavior_locks: BehaviorLock[];
  /** 会话开始时间 */
  started_at: string;
  /** 最后活动时间 */
  last_activity: string;
}

/**
 * 处理结果
 */
export interface ProcessingResult {
  /** 成功 */
  success: boolean;
  /** 消息 */
  message: string;
  /** 信号处理结果 */
  signal_results?: NormalizationResult[];
  /** 轨迹 */
  trajectory?: TrajectoryRecord;
  /** 表型匹配 */
  phenotypes?: PhenotypeMatchResult[];
  /** 干预计划摘要 */
  intervention_summary?: InterventionPlanSummary;
  /** 错误 */
  errors?: string[];
}

/**
 * 用户反馈
 */
export interface UserFeedback {
  /** 反馈类型 */
  type: 'task_completed' | 'task_skipped' | 'content_viewed' | 'resource_clicked' | 'rating';
  /** 相关ID */
  related_id: string;
  /** 评分 */
  rating?: number;
  /** 评论 */
  comment?: string;
  /** 时间 */
  timestamp: string;
}

/**
 * 决策编排器
 */
export class Orchestrator {
  private sessions: Map<string, UserSession> = new Map();
  private initialized: boolean = false;

  /**
   * 初始化编排器
   */
  async initialize(): Promise<void> {
    if (this.initialized) return;

    console.log('Initializing Orchestrator...');

    // 初始化库管理器
    await libraryManager.initialize();

    this.initialized = true;
    console.log('Orchestrator initialized.');
  }

  /**
   * 创建用户会话
   */
  createSession(userId: string): UserSession {
    const session: UserSession = {
      session_id: uuidv4(),
      user_id: userId,
      phenotypes: [],
      behavior_locks: [],
      started_at: new Date().toISOString(),
      last_activity: new Date().toISOString()
    };

    this.sessions.set(session.session_id, session);
    return session;
  }

  /**
   * 获取或创建会话
   */
  getOrCreateSession(userId: string): UserSession {
    // 查找现有会话
    for (const session of this.sessions.values()) {
      if (session.user_id === userId) {
        session.last_activity = new Date().toISOString();
        return session;
      }
    }

    // 创建新会话
    return this.createSession(userId);
  }

  /**
   * 处理信号数据
   */
  processSignals(
    userId: string,
    rawSignals: RawSignalInput[]
  ): ProcessingResult {
    if (!this.initialized) {
      return {
        success: false,
        message: 'Orchestrator not initialized',
        errors: ['Please call initialize() first']
      };
    }

    const session = this.getOrCreateSession(userId);
    const results: NormalizationResult[] = [];
    const validSignals: SignalRecord[] = [];
    const errors: string[] = [];

    // 标准化信号
    for (const raw of rawSignals) {
      const result = signalNormalizationService.normalize(raw);
      results.push(result);

      if (result.success && result.record) {
        validSignals.push(result.record);
      } else if (result.error) {
        errors.push(result.error);
      }
    }

    if (validSignals.length === 0) {
      return {
        success: false,
        message: 'No valid signals processed',
        signal_results: results,
        errors
      };
    }

    // 构建/更新轨迹
    const trajectory = trajectoryService.buildTrajectory(userId, validSignals, {
      timeWindow: 'last_7_days'
    });
    session.current_trajectory = trajectory;

    // 匹配表型
    const phenotypes = phenotypeMappingService.matchPhenotypes(trajectory.signals_summary);
    session.phenotypes = phenotypes;

    // 更新会话
    session.last_activity = new Date().toISOString();

    return {
      success: true,
      message: `Processed ${validSignals.length} signals successfully`,
      signal_results: results,
      trajectory,
      phenotypes,
      errors: errors.length > 0 ? errors : undefined
    };
  }

  /**
   * 生成干预计划
   */
  generateIntervention(
    userId: string,
    stageIndicators?: {
      awareness_score: number;
      motivation_score: number;
      self_efficacy_score: number;
      action_frequency: number;
      days_maintained: number;
    }
  ): InterventionPlanSummary | null {
    const session = this.getOrCreateSession(userId);

    if (!session.current_trajectory) {
      return null;
    }

    const planSummary = interventionPlanner.generatePlan(
      userId,
      session.current_trajectory,
      stageIndicators
    );

    session.stage_assessment = planSummary.stage_assessment;
    session.last_activity = new Date().toISOString();

    return planSummary;
  }

  /**
   * 激活干预计划
   */
  activateInterventionPlan(
    userId: string,
    playbookId: string
  ): InterventionPlan | null {
    const session = this.getOrCreateSession(userId);

    const plan = interventionPlaybookService.createPlan(userId, playbookId);
    if (plan) {
      session.current_plan = plan;
      session.last_activity = new Date().toISOString();
    }

    return plan;
  }

  /**
   * 处理用户反馈
   */
  processFeedback(
    userId: string,
    feedback: UserFeedback
  ): boolean {
    const session = this.getOrCreateSession(userId);

    switch (feedback.type) {
      case 'task_completed':
        if (session.current_plan) {
          interventionPlaybookService.completeTask(
            session.current_plan.plan_id,
            feedback.related_id,
            feedback.comment
          );

          // 更新行为锁定
          for (const lock of session.behavior_locks) {
            behaviorChangeEngineService.updateLockStatus(lock.lock_id, true);
          }
        }
        break;

      case 'task_skipped':
        // 更新行为锁定（中断）
        for (const lock of session.behavior_locks) {
          behaviorChangeEngineService.updateLockStatus(lock.lock_id, false);
        }
        break;

      case 'content_viewed':
        contentMaterialService.recordInteraction(feedback.related_id, 'view');
        break;

      case 'resource_clicked':
        commercialResourceService.recordFeedback(feedback.related_id, {
          clicked: true,
          purchased: false
        });
        break;

      case 'rating':
        if (feedback.rating !== undefined) {
          contentMaterialService.recordInteraction(feedback.related_id, 'like');
        }
        break;
    }

    session.last_activity = new Date().toISOString();
    return true;
  }

  /**
   * 创建行为锁定
   */
  createBehaviorLock(
    userId: string,
    behaviorName: string,
    category: 'diet' | 'exercise' | 'sleep' | 'emotion' | 'monitoring',
    triggerCue: string,
    executionTime?: string,
    reward?: string
  ): BehaviorLock {
    const session = this.getOrCreateSession(userId);

    const lock = behaviorChangeEngineService.createBehaviorLock(
      userId,
      behaviorName,
      category,
      triggerCue,
      executionTime,
      reward
    );

    session.behavior_locks.push(lock);
    session.last_activity = new Date().toISOString();

    return lock;
  }

  /**
   * 获取用户仪表盘数据
   */
  getDashboard(userId: string): {
    session: UserSession | null;
    todayTasks: Array<{ task_id: string; task_name: string; completed: boolean }>;
    recentInsights: string[];
    metrics: Record<string, number>;
    recommendations: string[];
  } {
    const session = Array.from(this.sessions.values())
      .find(s => s.user_id === userId);

    if (!session) {
      return {
        session: null,
        todayTasks: [],
        recentInsights: [],
        metrics: {},
        recommendations: []
      };
    }

    // 获取今日任务
    const todayTasks = session.current_plan
      ? interventionPlaybookService.getTodayTasks(session.current_plan.plan_id)
          .map(t => ({
            task_id: t.task_id,
            task_name: t.task_name,
            completed: t.completed
          }))
      : [];

    // 获取洞察
    const recentInsights = session.current_trajectory?.insights || [];

    // 获取关键指标
    const metrics: Record<string, number> = {};
    if (session.current_trajectory?.signals_summary) {
      const summary = session.current_trajectory.signals_summary;
      if (summary.time_in_range !== undefined) metrics.time_in_range = summary.time_in_range;
      if (summary.fasting_glucose_mean !== undefined) metrics.fasting_glucose = summary.fasting_glucose_mean;
      if (summary.daily_steps_mean !== undefined) metrics.daily_steps = summary.daily_steps_mean;
    }

    // 获取推荐
    const recommendations = session.phenotypes
      .slice(0, 2)
      .flatMap(p => p.phenotype.recommended_levers.slice(0, 2));

    return {
      session,
      todayTasks,
      recentInsights,
      metrics,
      recommendations
    };
  }

  /**
   * 获取对话上下文
   */
  getConversationContext(userId: string): {
    stage: BehaviorStage;
    phenotypes: string[];
    riskFlags: string[];
    currentFocus: string;
    suggestedTopics: string[];
  } {
    const session = Array.from(this.sessions.values())
      .find(s => s.user_id === userId);

    const defaultContext = {
      stage: 'contemplation' as BehaviorStage,
      phenotypes: [],
      riskFlags: [],
      currentFocus: '建立信任关系',
      suggestedTopics: ['了解用户需求', '解释血糖监测的意义']
    };

    if (!session) return defaultContext;

    const stage = session.stage_assessment?.current_stage || 'contemplation';
    const phenotypes = session.phenotypes.map(p => p.phenotype.phenotype_name);
    const riskFlags = session.current_trajectory?.risk_flags || [];

    // 根据阶段确定当前焦点
    const focusMap: Record<BehaviorStage, string> = {
      precontemplation: '意识唤醒',
      contemplation: '动机强化',
      preparation: '行动规划',
      action: '习惯养成',
      maintenance: '巩固维持'
    };

    // 根据阶段和表型生成建议话题
    const suggestedTopics: string[] = [];
    if (stage === 'precontemplation') {
      suggestedTopics.push('分享CGM数据发现', '探索健康目标');
    } else if (stage === 'contemplation') {
      suggestedTopics.push('讨论改变的好处', '识别潜在障碍');
    } else if (stage === 'preparation') {
      suggestedTopics.push('制定具体计划', '设置小目标');
    } else if (stage === 'action') {
      suggestedTopics.push('回顾今日任务', '解决执行困难');
    } else {
      suggestedTopics.push('庆祝进步', '预防复发');
    }

    // 根据表型添加话题
    if (phenotypes.some(p => p.includes('餐后'))) {
      suggestedTopics.push('讨论进餐习惯');
    }
    if (phenotypes.some(p => p.includes('压力'))) {
      suggestedTopics.push('了解压力来源');
    }

    return {
      stage,
      phenotypes,
      riskFlags,
      currentFocus: focusMap[stage],
      suggestedTopics: suggestedTopics.slice(0, 4)
    };
  }

  /**
   * 获取系统状态
   */
  getSystemStatus(): {
    initialized: boolean;
    activeSessions: number;
    libraryStatus: ReturnType<typeof libraryManager.getLibraryStatus>;
    overallStats: ReturnType<typeof libraryManager.getOverallStats>;
  } {
    return {
      initialized: this.initialized,
      activeSessions: this.sessions.size,
      libraryStatus: libraryManager.getLibraryStatus(),
      overallStats: libraryManager.getOverallStats()
    };
  }

  /**
   * 清理过期会话
   */
  cleanupSessions(maxAgeHours: number = 24): number {
    const now = new Date().getTime();
    const maxAge = maxAgeHours * 60 * 60 * 1000;
    let cleaned = 0;

    for (const [sessionId, session] of this.sessions.entries()) {
      const lastActivity = new Date(session.last_activity).getTime();
      if (now - lastActivity > maxAge) {
        this.sessions.delete(sessionId);
        cleaned++;
      }
    }

    return cleaned;
  }
}

// 导出单例
export const orchestrator = new Orchestrator();
