/**
 * Intervention Planner - 干预规划器
 * 基于表型和轨迹生成个性化干预计划
 */

import { v4 as uuidv4 } from 'uuid';
import { TrajectoryRecord, BehaviorStage, SignalsSummary } from '../trajectory/TrajectorySchema';
import { PhenotypeMatchResult, phenotypeMappingService } from '../libraries/PhenotypeMapping';
import {
  InterventionPlaybook,
  InterventionPlan,
  InterventionLever,
  interventionPlaybookService
} from '../libraries/InterventionPlaybook';
import { behaviorChangeEngineService, StageAssessment } from '../libraries/BehaviorChangeEngine';
import { ContentMaterial, contentMaterialService } from '../libraries/ContentMaterial';
import { CommercialResource, commercialResourceService } from '../libraries/CommercialResource';

/**
 * 干预优先级
 */
export type InterventionPriority = 'immediate' | 'short_term' | 'long_term';

/**
 * 干预建议
 */
export interface InterventionRecommendation {
  /** 建议ID */
  recommendation_id: string;
  /** 匹配的表型 */
  matched_phenotype: PhenotypeMatchResult;
  /** 推荐的剧本 */
  recommended_playbook?: InterventionPlaybook;
  /** 推荐的杠杆 */
  recommended_levers: InterventionLever[];
  /** 优先级 */
  priority: InterventionPriority;
  /** 理由 */
  rationale: string;
  /** 预期效果 */
  expected_outcomes: string[];
  /** 相关内容 */
  related_content: ContentMaterial[];
  /** 相关资源 */
  related_resources: CommercialResource[];
  /** 置信度 */
  confidence: number;
}

/**
 * 干预计划摘要
 */
export interface InterventionPlanSummary {
  /** 用户ID */
  user_id: string;
  /** 当前阶段评估 */
  stage_assessment: StageAssessment;
  /** 识别的表型 */
  identified_phenotypes: PhenotypeMatchResult[];
  /** 干预建议列表 */
  recommendations: InterventionRecommendation[];
  /** 总体策略 */
  overall_strategy: string;
  /** 立即行动项 */
  immediate_actions: string[];
  /** 注意事项 */
  cautions: string[];
  /** 生成时间 */
  generated_at: string;
}

/**
 * 干预规划器
 */
export class InterventionPlanner {
  /**
   * 生成干预计划
   */
  generatePlan(
    userId: string,
    trajectory: TrajectoryRecord,
    stageIndicators?: {
      awareness_score: number;
      motivation_score: number;
      self_efficacy_score: number;
      action_frequency: number;
      days_maintained: number;
    }
  ): InterventionPlanSummary {
    // 1. 评估行为阶段
    const stageAssessment = stageIndicators
      ? behaviorChangeEngineService.assessStage(userId, stageIndicators)
      : this.inferStageAssessment(trajectory);

    // 2. 匹配表型
    const phenotypeMatches = phenotypeMappingService.matchPhenotypes(trajectory.signals_summary);

    // 3. 生成干预建议
    const recommendations = this.generateRecommendations(
      phenotypeMatches,
      stageAssessment.current_stage,
      trajectory
    );

    // 4. 生成总体策略
    const overallStrategy = this.generateOverallStrategy(
      stageAssessment,
      phenotypeMatches,
      recommendations
    );

    // 5. 提取立即行动项
    const immediateActions = this.extractImmediateActions(recommendations, stageAssessment);

    // 6. 识别注意事项
    const cautions = this.identifyCautions(phenotypeMatches, trajectory);

    return {
      user_id: userId,
      stage_assessment: stageAssessment,
      identified_phenotypes: phenotypeMatches,
      recommendations,
      overall_strategy: overallStrategy,
      immediate_actions: immediateActions,
      cautions,
      generated_at: new Date().toISOString()
    };
  }

  /**
   * 从轨迹推断阶段评估
   */
  private inferStageAssessment(trajectory: TrajectoryRecord): StageAssessment {
    const summary = trajectory.signals_summary;

    // 简化的推断逻辑
    const awareness = summary.time_in_range !== undefined ? 60 : 30;
    const motivation = trajectory.behavior_events.length > 0 ? 50 : 30;
    const selfEfficacy = summary.time_in_range && summary.time_in_range > 50 ? 60 : 40;
    const actionFrequency = trajectory.interventions_applied.length;
    const daysMaintained = trajectory.stage_transitions.length > 0 ? 30 : 0;

    return behaviorChangeEngineService.assessStage('inferred', {
      awareness_score: awareness,
      motivation_score: motivation,
      self_efficacy_score: selfEfficacy,
      action_frequency: actionFrequency,
      days_maintained: daysMaintained
    });
  }

  /**
   * 生成干预建议
   */
  private generateRecommendations(
    phenotypeMatches: PhenotypeMatchResult[],
    currentStage: BehaviorStage,
    trajectory: TrajectoryRecord
  ): InterventionRecommendation[] {
    const recommendations: InterventionRecommendation[] = [];

    for (const match of phenotypeMatches.slice(0, 3)) { // 最多处理前3个匹配
      const phenotype = match.phenotype;

      // 匹配剧本
      const matchedPlaybooks = interventionPlaybookService.matchPlaybooks(
        [phenotype.mapping_id],
        currentStage
      );

      // 获取相关内容
      const relatedContent = contentMaterialService.recommendContents(
        currentStage,
        [phenotype.mapping_id],
        3
      );

      // 获取相关资源
      const relatedResources = commercialResourceService.recommendByPhenotypes(
        [phenotype.mapping_id],
        3
      );

      // 确定优先级
      const priority = this.determinePriority(phenotype.risk_level, match.match_score);

      // 生成理由
      const rationale = this.generateRationale(match, currentStage);

      // 获取推荐杠杆
      const recommendedLevers = phenotype.recommended_levers
        .slice(0, 3)
        .map(leverName => {
          return interventionPlaybookService.getAllLevers()
            .find(l => l.name === leverName);
        })
        .filter((l): l is InterventionLever => l !== undefined);

      recommendations.push({
        recommendation_id: uuidv4(),
        matched_phenotype: match,
        recommended_playbook: matchedPlaybooks[0],
        recommended_levers: recommendedLevers,
        priority,
        rationale,
        expected_outcomes: phenotype.recommended_levers.slice(0, 3),
        related_content: relatedContent,
        related_resources: relatedResources,
        confidence: match.match_score * (phenotype.confidence_score || 1)
      });
    }

    // 按优先级排序
    const priorityOrder: Record<InterventionPriority, number> = {
      immediate: 0,
      short_term: 1,
      long_term: 2
    };
    recommendations.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);

    return recommendations;
  }

  /**
   * 确定优先级
   */
  private determinePriority(
    riskLevel: string,
    matchScore: number
  ): InterventionPriority {
    if (riskLevel === 'critical' || riskLevel === 'high') {
      return 'immediate';
    }
    if (riskLevel === 'medium' || matchScore > 0.8) {
      return 'short_term';
    }
    return 'long_term';
  }

  /**
   * 生成理由
   */
  private generateRationale(
    match: PhenotypeMatchResult,
    stage: BehaviorStage
  ): string {
    const phenotype = match.phenotype;
    const patterns = match.matched_patterns.slice(0, 2).join('、');

    const stageNames: Record<BehaviorStage, string> = {
      precontemplation: '前意向期',
      contemplation: '意向期',
      preparation: '准备期',
      action: '行动期',
      maintenance: '维持期'
    };

    return `检测到${phenotype.phenotype_name}特征(${patterns})，` +
      `当前处于${stageNames[stage]}，建议采用阶段匹配的干预策略。`;
  }

  /**
   * 生成总体策略
   */
  private generateOverallStrategy(
    stageAssessment: StageAssessment,
    phenotypes: PhenotypeMatchResult[],
    recommendations: InterventionRecommendation[]
  ): string {
    const stageNames: Record<BehaviorStage, string> = {
      precontemplation: '前意向期',
      contemplation: '意向期',
      preparation: '准备期',
      action: '行动期',
      maintenance: '维持期'
    };

    const stage = stageNames[stageAssessment.current_stage];
    const phenotypeCount = phenotypes.length;
    const topPhenotype = phenotypes[0]?.phenotype.phenotype_name || '未识别';
    const advancementProb = stageAssessment.advancement_probability;

    let strategy = `用户当前处于${stage}，识别到${phenotypeCount}个表型特征，主要为${topPhenotype}。`;

    if (stageAssessment.regression_risk > 50) {
      strategy += `退行风险较高(${stageAssessment.regression_risk}%)，需重点关注稳定性。`;
    } else if (advancementProb > 60) {
      strategy += `进阶可能性良好(${advancementProb}%)，可适度提升干预强度。`;
    }

    const immediateCount = recommendations.filter(r => r.priority === 'immediate').length;
    if (immediateCount > 0) {
      strategy += `有${immediateCount}项需要立即关注的干预建议。`;
    }

    return strategy;
  }

  /**
   * 提取立即行动项
   */
  private extractImmediateActions(
    recommendations: InterventionRecommendation[],
    stageAssessment: StageAssessment
  ): string[] {
    const actions: string[] = [];

    // 添加阶段相关的推荐行动
    actions.push(...stageAssessment.recommended_actions.slice(0, 2));

    // 添加高优先级干预的杠杆
    for (const rec of recommendations.filter(r => r.priority === 'immediate')) {
      for (const lever of rec.recommended_levers.slice(0, 1)) {
        actions.push(`${lever.name}：${lever.description}`);
      }
    }

    return actions.slice(0, 5); // 最多5项
  }

  /**
   * 识别注意事项
   */
  private identifyCautions(
    phenotypes: PhenotypeMatchResult[],
    trajectory: TrajectoryRecord
  ): string[] {
    const cautions: string[] = [];

    // 从风险标记提取
    if (trajectory.risk_flags) {
      for (const flag of trajectory.risk_flags) {
        switch (flag) {
          case 'night_hypoglycemia':
            cautions.push('存在夜间低血糖风险，注意睡前血糖监测');
            break;
          case 'high_glucose_variability':
            cautions.push('血糖波动较大，避免剧烈运动');
            break;
          case 'frequent_hypoglycemia':
            cautions.push('低血糖频繁，随身携带糖果');
            break;
          case 'high_postprandial_spike':
            cautions.push('餐后血糖峰值高，注意进餐顺序');
            break;
        }
      }
    }

    // 从表型提取禁忌
    for (const match of phenotypes) {
      const phenotype = match.phenotype;
      if (phenotype.risk_level === 'high' || phenotype.risk_level === 'critical') {
        cautions.push(`${phenotype.phenotype_name}风险等级较高，建议医生指导下调整方案`);
      }
    }

    return cautions;
  }

  /**
   * 创建执行计划
   */
  createExecutionPlan(
    userId: string,
    recommendation: InterventionRecommendation
  ): InterventionPlan | null {
    if (!recommendation.recommended_playbook) {
      return null;
    }

    return interventionPlaybookService.createPlan(
      userId,
      recommendation.recommended_playbook.playbook_id
    );
  }

  /**
   * 获取今日建议
   */
  getTodayRecommendations(
    userId: string,
    currentPlan?: InterventionPlan
  ): {
    tasks: Array<{
      task_id: string;
      task_name: string;
      task_description: string;
    }>;
    tips: string[];
    content: ContentMaterial[];
  } {
    const result: {
      tasks: Array<{ task_id: string; task_name: string; task_description: string }>;
      tips: string[];
      content: ContentMaterial[];
    } = {
      tasks: [],
      tips: [],
      content: []
    };

    // 获取今日任务
    if (currentPlan) {
      const todayTasks = interventionPlaybookService.getTodayTasks(currentPlan.plan_id);
      result.tasks = todayTasks.map(t => ({
        task_id: t.task_id,
        task_name: t.task_name,
        task_description: t.task_description
      }));
    }

    // 获取每日小贴士
    result.tips = [
      '记得在餐前喝杯水，有助于控制食量',
      '餐后15分钟是散步的最佳时机',
      '保持规律作息对血糖控制很有帮助'
    ];

    // 获取推荐内容
    result.content = contentMaterialService.searchContents({
      domain: 'nutrition',
      difficulty: 'beginner'
    }).slice(0, 2);

    return result;
  }
}

// 导出单例
export const interventionPlanner = new InterventionPlanner();
