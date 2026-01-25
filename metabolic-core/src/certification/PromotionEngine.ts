/**
 * Promotion Engine - 晋级判定引擎
 * 评估教练是否满足晋级条件，输出晋级决策
 */

import {
  CertificationLevel,
  CoachProfile,
  CoachCase,
  LevelRequirement,
  PromotionApplication
} from './CertificationSchema';
import { LEVEL_REQUIREMENTS, certificationService } from './CertificationService';
import { v4 as uuidv4 } from 'uuid';

/**
 * 晋级评估结果
 */
export interface PromotionEvaluation {
  /** 是否允许晋级 */
  eligible: boolean;
  /** 当前等级 */
  current_level: CertificationLevel;
  /** 目标等级 */
  target_level: CertificationLevel;
  /** 各项评估详情 */
  evaluation_details: {
    /** 理论成绩评估 */
    theory: {
      required_score: number;
      actual_score: number;
      passed: boolean;
    };
    /** 技能评分评估 */
    skills: {
      required_score: number;
      actual_score: number;
      passed: boolean;
    };
    /** 实战案例评估 */
    cases: {
      required_count: number;
      actual_count: number;
      completed_paths: number;
      improved_cases: number;
      passed: boolean;
    };
    /** 平台评分评估 */
    platform_rating: {
      required: string;
      actual: string;
      passed: boolean;
    };
    /** 督导评分评估 */
    supervisor?: {
      average_score: number;
      passed: boolean;
    };
    /** 带教评估 */
    mentoring?: {
      required_mentees: number;
      actual_mentees: number;
      passed: boolean;
    };
  };
  /** 推荐补修模块 */
  recommended_modules: string[];
  /** 缺失条件 */
  missing_requirements: string[];
  /** 授权新权限（如果晋级成功） */
  new_permissions: string[];
  /** 评估时间 */
  evaluated_at: string;
}

/**
 * 等级顺序映射
 */
const LEVEL_ORDER: Record<CertificationLevel, number> = {
  'L0': 0,
  'L1': 1,
  'L2': 2,
  'L3': 3,
  'L4': 4
};

/**
 * 平台评分顺序
 */
const RATING_ORDER: Record<string, number> = {
  'D': 0,
  'C': 1,
  'B-': 2,
  'B': 3,
  'B+': 4,
  'A-': 5,
  'A': 6,
  'A+': 7,
  'S': 8
};

/**
 * 晋级判定引擎
 */
export class PromotionEngine {
  /**
   * 获取下一等级
   */
  private getNextLevel(current: CertificationLevel): CertificationLevel | null {
    const levels: CertificationLevel[] = ['L0', 'L1', 'L2', 'L3', 'L4'];
    const currentIndex = levels.indexOf(current);
    if (currentIndex === -1 || currentIndex === levels.length - 1) {
      return null;
    }
    return levels[currentIndex + 1];
  }

  /**
   * 评估教练是否可以晋级
   */
  evaluate(coach: CoachProfile): PromotionEvaluation {
    const targetLevel = this.getNextLevel(coach.level);

    if (!targetLevel) {
      return this.createMaxLevelResult(coach);
    }

    const requirement = LEVEL_REQUIREMENTS.find(r => r.level === targetLevel);
    if (!requirement) {
      return this.createMaxLevelResult(coach);
    }

    const cases = certificationService.getCoachCases(coach.coach_id);
    const completedCases = cases.filter(c => c.status === 'completed');
    const improvedCases = completedCases.filter(c =>
      c.outcome_metrics.some(m => m.improvement_percent > 0)
    );

    // 评估各项条件
    const theoryEval = this.evaluateTheory(coach, requirement);
    const skillsEval = this.evaluateSkills(coach, requirement);
    const casesEval = this.evaluateCases(coach, cases, requirement);
    const ratingEval = this.evaluateRating(coach, requirement);
    const mentoringEval = this.evaluateMentoring(coach, requirement);

    const allPassed =
      theoryEval.passed &&
      skillsEval.passed &&
      casesEval.passed &&
      ratingEval.passed &&
      (mentoringEval ? mentoringEval.passed : true);

    const missingRequirements: string[] = [];
    const recommendedModules: string[] = [];

    if (!theoryEval.passed) {
      missingRequirements.push(`理论成绩需达到${theoryEval.required_score}分，当前${theoryEval.actual_score}分`);
      recommendedModules.push(...this.getRecommendedTheoryModules(coach, requirement));
    }

    if (!skillsEval.passed) {
      missingRequirements.push(`技能评分需达到${skillsEval.required_score}分，当前${skillsEval.actual_score}分`);
      recommendedModules.push(...this.getRecommendedSkillModules(coach, requirement));
    }

    if (!casesEval.passed) {
      if (casesEval.actual_count < casesEval.required_count) {
        missingRequirements.push(`需完成${casesEval.required_count}个案例，当前${casesEval.actual_count}个`);
      }
      if (requirement.practice_requirements.min_completed_paths &&
          casesEval.completed_paths < requirement.practice_requirements.min_completed_paths) {
        missingRequirements.push(`需完成${requirement.practice_requirements.min_completed_paths}个完整路径`);
      }
      if (requirement.practice_requirements.min_improved_cases &&
          casesEval.improved_cases < requirement.practice_requirements.min_improved_cases) {
        missingRequirements.push(`需有${requirement.practice_requirements.min_improved_cases}例指标改善案例`);
      }
    }

    if (!ratingEval.passed) {
      missingRequirements.push(`平台评分需达到${ratingEval.required}，当前${ratingEval.actual}`);
    }

    if (mentoringEval && !mentoringEval.passed) {
      missingRequirements.push(`需带教${mentoringEval.required_mentees}名教练，当前${mentoringEval.actual_mentees}名`);
    }

    return {
      eligible: allPassed,
      current_level: coach.level,
      target_level: targetLevel,
      evaluation_details: {
        theory: theoryEval,
        skills: skillsEval,
        cases: casesEval,
        platform_rating: ratingEval,
        mentoring: mentoringEval
      },
      recommended_modules: [...new Set(recommendedModules)],
      missing_requirements: missingRequirements,
      new_permissions: allPassed
        ? requirement.granted_permissions.map(p => p.agent_type)
        : [],
      evaluated_at: new Date().toISOString()
    };
  }

  /**
   * 评估理论成绩
   */
  private evaluateTheory(coach: CoachProfile, requirement: LevelRequirement): {
    required_score: number;
    actual_score: number;
    passed: boolean;
  } {
    const theoryExams = requirement.required_exams.filter(e => e.exam_type === 'theory');
    if (theoryExams.length === 0) {
      return { required_score: 0, actual_score: 100, passed: true };
    }

    const requiredScore = theoryExams[0].min_score;
    const passedTheoryExams = coach.passed_exams.filter(e =>
      e.exam_type === 'theory' && e.level === requirement.level
    );

    const actualScore = passedTheoryExams.length > 0
      ? Math.max(...passedTheoryExams.map(e => e.score))
      : 0;

    return {
      required_score: requiredScore,
      actual_score: actualScore,
      passed: actualScore >= requiredScore
    };
  }

  /**
   * 评估技能评分
   */
  private evaluateSkills(coach: CoachProfile, requirement: LevelRequirement): {
    required_score: number;
    actual_score: number;
    passed: boolean;
  } {
    const skillExams = requirement.required_exams.filter(e =>
      e.exam_type === 'case_simulation' || e.exam_type === 'dialogue_assessment'
    );

    if (skillExams.length === 0) {
      return { required_score: 0, actual_score: 100, passed: true };
    }

    let totalWeight = 0;
    let weightedScore = 0;
    let allPassed = true;

    for (const examReq of skillExams) {
      const passedExam = coach.passed_exams.find(e =>
        e.exam_type === examReq.exam_type && e.level === requirement.level
      );

      if (passedExam) {
        weightedScore += passedExam.score * examReq.weight_percent;
        totalWeight += examReq.weight_percent;
        if (passedExam.score < examReq.min_score) {
          allPassed = false;
        }
      } else {
        allPassed = false;
        totalWeight += examReq.weight_percent;
      }
    }

    const averageRequired = skillExams.reduce((sum, e) => sum + e.min_score, 0) / skillExams.length;
    const actualScore = totalWeight > 0 ? weightedScore / totalWeight : 0;

    return {
      required_score: Math.round(averageRequired),
      actual_score: Math.round(actualScore),
      passed: allPassed
    };
  }

  /**
   * 评估案例数量
   */
  private evaluateCases(coach: CoachProfile, cases: CoachCase[], requirement: LevelRequirement): {
    required_count: number;
    actual_count: number;
    completed_paths: number;
    improved_cases: number;
    passed: boolean;
  } {
    const completedCases = cases.filter(c => c.status === 'completed');
    const casesWithPaths = completedCases.filter(c => c.intervention_path.path_id);
    const improvedCases = completedCases.filter(c =>
      c.outcome_metrics.some(m => m.improvement_percent > 0)
    );

    const reqCases = requirement.practice_requirements.min_cases;
    const reqPaths = requirement.practice_requirements.min_completed_paths || 0;
    const reqImproved = requirement.practice_requirements.min_improved_cases || 0;

    const passed =
      completedCases.length >= reqCases &&
      casesWithPaths.length >= reqPaths &&
      improvedCases.length >= reqImproved;

    return {
      required_count: reqCases,
      actual_count: completedCases.length,
      completed_paths: casesWithPaths.length,
      improved_cases: improvedCases.length,
      passed
    };
  }

  /**
   * 评估平台评分
   */
  private evaluateRating(coach: CoachProfile, requirement: LevelRequirement): {
    required: string;
    actual: string;
    passed: boolean;
  } {
    if (!requirement.min_platform_rating) {
      return { required: 'N/A', actual: coach.platform_rating, passed: true };
    }

    const requiredOrder = RATING_ORDER[requirement.min_platform_rating] || 0;
    const actualOrder = RATING_ORDER[coach.platform_rating] || 0;

    return {
      required: requirement.min_platform_rating,
      actual: coach.platform_rating,
      passed: actualOrder >= requiredOrder
    };
  }

  /**
   * 评估带教记录
   */
  private evaluateMentoring(coach: CoachProfile, requirement: LevelRequirement): {
    required_mentees: number;
    actual_mentees: number;
    passed: boolean;
  } | undefined {
    if (!requirement.mentoring_requirements) {
      return undefined;
    }

    const successfulMentees = coach.mentoring_records.filter(m => m.outcome === 'promoted').length;

    return {
      required_mentees: requirement.mentoring_requirements.min_mentees,
      actual_mentees: successfulMentees,
      passed: successfulMentees >= requirement.mentoring_requirements.min_mentees
    };
  }

  /**
   * 获取推荐的理论模块
   */
  private getRecommendedTheoryModules(coach: CoachProfile, requirement: LevelRequirement): string[] {
    const modules: string[] = [];

    for (const courseReq of requirement.required_courses) {
      if (courseReq.module_type === 'knowledge') {
        for (const courseId of courseReq.course_ids) {
          if (!coach.completed_courses.some(c => c.course_id === courseId)) {
            modules.push(courseId);
          }
        }
      }
    }

    return modules;
  }

  /**
   * 获取推荐的技能模块
   */
  private getRecommendedSkillModules(coach: CoachProfile, requirement: LevelRequirement): string[] {
    const modules: string[] = [];

    for (const courseReq of requirement.required_courses) {
      if (courseReq.module_type === 'skill' || courseReq.module_type === 'method') {
        for (const courseId of courseReq.course_ids) {
          if (!coach.completed_courses.some(c => c.course_id === courseId)) {
            modules.push(courseId);
          }
        }
      }
    }

    return modules;
  }

  /**
   * 创建已达最高等级的结果
   */
  private createMaxLevelResult(coach: CoachProfile): PromotionEvaluation {
    return {
      eligible: false,
      current_level: coach.level,
      target_level: coach.level,
      evaluation_details: {
        theory: { required_score: 0, actual_score: 100, passed: true },
        skills: { required_score: 0, actual_score: 100, passed: true },
        cases: { required_count: 0, actual_count: 0, completed_paths: 0, improved_cases: 0, passed: true },
        platform_rating: { required: 'N/A', actual: coach.platform_rating, passed: true }
      },
      recommended_modules: [],
      missing_requirements: ['已达到最高等级'],
      new_permissions: [],
      evaluated_at: new Date().toISOString()
    };
  }

  /**
   * 执行晋级
   */
  promote(coachId: string): { success: boolean; message: string; new_level?: CertificationLevel } {
    const coach = certificationService.getCoachProfile(coachId);
    if (!coach) {
      return { success: false, message: '教练档案不存在' };
    }

    const evaluation = this.evaluate(coach);
    if (!evaluation.eligible) {
      return {
        success: false,
        message: `不满足晋级条件: ${evaluation.missing_requirements.join('; ')}`
      };
    }

    const targetLevel = evaluation.target_level;
    const requirement = LEVEL_REQUIREMENTS.find(r => r.level === targetLevel);

    if (!requirement) {
      return { success: false, message: '目标等级配置不存在' };
    }

    // 更新教练档案
    coach.level = targetLevel;
    coach.level_achieved_at = new Date().toISOString();
    coach.serviceable_risk_levels = requirement.serviceable_risk_levels;
    coach.revenue_share_ratio = requirement.revenue_share_ratio;

    // 授予新权限
    for (const perm of requirement.granted_permissions) {
      if (!coach.agent_permissions.some(p => p.agent_type === perm.agent_type)) {
        coach.agent_permissions.push({
          ...perm,
          granted_at: new Date().toISOString()
        });
      }
    }

    return {
      success: true,
      message: `成功晋级到${requirement.name}`,
      new_level: targetLevel
    };
  }

  /**
   * 创建晋级申请
   */
  createApplication(coachId: string): PromotionApplication | null {
    const coach = certificationService.getCoachProfile(coachId);
    if (!coach) return null;

    const targetLevel = this.getNextLevel(coach.level);
    if (!targetLevel) return null;

    const application: PromotionApplication = {
      application_id: uuidv4(),
      coach_id: coachId,
      current_level: coach.level,
      target_level: targetLevel,
      submitted_at: new Date().toISOString(),
      status: 'pending',
      evidence: {
        theory_scores: coach.passed_exams
          .filter(e => e.exam_type === 'theory')
          .map(e => ({ exam_id: e.exam_id, score: e.score })),
        skill_scores: coach.passed_exams
          .filter(e => e.exam_type !== 'theory')
          .map(e => ({ exam_id: e.exam_id, score: e.score })),
        case_ids: coach.real_cases,
        platform_rating: coach.platform_rating
      }
    };

    return application;
  }
}

// 导出单例
export const promotionEngine = new PromotionEngine();
