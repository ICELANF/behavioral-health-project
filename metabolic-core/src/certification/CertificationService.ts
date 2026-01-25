/**
 * Certification Service - 认证服务
 * 管理教练档案、课程、考试、案例
 */

import { v4 as uuidv4 } from 'uuid';
import {
  CertificationLevel,
  SpecialtyTag,
  CoachProfile,
  CoachCompetencyModel,
  CoachCase,
  CourseDefinition,
  ExamDefinition,
  LevelRequirement,
  CompletedCourse,
  PassedExam,
  TrainingSession
} from './CertificationSchema';

/**
 * 预定义等级要求
 */
export const LEVEL_REQUIREMENTS: LevelRequirement[] = [
  {
    level: 'L0',
    name: '公众学习者',
    description: '免费入口层，建立行为健康基础认知',
    required_courses: [
      { module_type: 'knowledge', course_ids: ['CRS-L0-K01', 'CRS-L0-K02'] }
    ],
    required_exams: [
      { exam_type: 'theory', min_score: 80, weight_percent: 100 }
    ],
    practice_requirements: {
      min_cases: 0,
      min_completed_paths: 0
    },
    granted_permissions: [],
    serviceable_risk_levels: [],
    revenue_share_ratio: 0
  },
  {
    level: 'L1',
    name: '初级行为健康教练',
    description: '助理级，能辅助服务、能带基础人群、能执行标准路径',
    required_courses: [
      { module_type: 'knowledge', course_ids: ['CRS-L1-K01', 'CRS-L1-K02', 'CRS-L1-K03'] },
      { module_type: 'method', course_ids: ['CRS-L1-M01', 'CRS-L1-M02'] },
      { module_type: 'skill', course_ids: ['CRS-L1-S01', 'CRS-L1-S02'] }
    ],
    required_exams: [
      { exam_type: 'theory', min_score: 80, weight_percent: 40 },
      { exam_type: 'case_simulation', min_score: 70, weight_percent: 30 },
      { exam_type: 'dialogue_assessment', min_score: 70, weight_percent: 30 }
    ],
    practice_requirements: {
      min_cases: 3,
      min_completed_paths: 0
    },
    granted_permissions: [
      { agent_type: 'basic_assessment', permission_level: 'execute', granted_at: '' }
    ],
    serviceable_risk_levels: ['low'],
    revenue_share_ratio: 0.3
  },
  {
    level: 'L2',
    name: '中级行为健康教练',
    description: '独立上岗级，平台主力教练层，可独立带慢病/代谢异常客户',
    required_courses: [
      { module_type: 'knowledge', course_ids: ['CRS-L2-K01', 'CRS-L2-K02', 'CRS-L2-K03'] },
      { module_type: 'method', course_ids: ['CRS-L2-M01', 'CRS-L2-M02', 'CRS-L2-M03'] },
      { module_type: 'skill', course_ids: ['CRS-L2-S01', 'CRS-L2-S02', 'CRS-L2-S03'] }
    ],
    required_exams: [
      { exam_type: 'theory', min_score: 80, weight_percent: 30 },
      { exam_type: 'case_simulation', min_score: 75, weight_percent: 40 },
      { exam_type: 'dialogue_assessment', min_score: 75, weight_percent: 30 }
    ],
    practice_requirements: {
      min_cases: 5,
      min_completed_paths: 3,
      min_improved_cases: 1
    },
    min_platform_rating: 'A-',
    granted_permissions: [
      { agent_type: 'basic_assessment', permission_level: 'execute', granted_at: '' },
      { agent_type: 'metabolic_intervention', permission_level: 'execute', granted_at: '' },
      { agent_type: 'personalized_plan', permission_level: 'execute', granted_at: '' }
    ],
    serviceable_risk_levels: ['low', 'medium'],
    revenue_share_ratio: 0.5
  },
  {
    level: 'L3',
    name: '高级行为健康教练',
    description: '专项/慢病专家级，平台慢病主力+项目骨干+医疗协作层',
    required_courses: [
      { module_type: 'knowledge', course_ids: ['CRS-L3-K01', 'CRS-L3-K02'] },
      { module_type: 'method', course_ids: ['CRS-L3-M01', 'CRS-L3-M02'] },
      { module_type: 'skill', course_ids: ['CRS-L3-S01', 'CRS-L3-S02'] }
    ],
    required_exams: [
      { exam_type: 'specialty', min_score: 80, weight_percent: 40 },
      { exam_type: 'case_simulation', min_score: 80, weight_percent: 30 },
      { exam_type: 'dialogue_assessment', min_score: 80, weight_percent: 30 }
    ],
    practice_requirements: {
      min_cases: 20,
      min_completed_paths: 10,
      min_followup_months: 3,
      min_improved_cases: 5
    },
    min_platform_rating: 'A',
    granted_permissions: [
      { agent_type: 'basic_assessment', permission_level: 'configure', granted_at: '' },
      { agent_type: 'metabolic_intervention', permission_level: 'configure', granted_at: '' },
      { agent_type: 'personalized_plan', permission_level: 'configure', granted_at: '' },
      { agent_type: 'specialty_expert', permission_level: 'execute', granted_at: '' }
    ],
    serviceable_risk_levels: ['low', 'medium', 'high'],
    revenue_share_ratio: 0.65
  },
  {
    level: 'L4',
    name: '行为健康督导/讲师/专家',
    description: '平台方法论中枢+认证体系核心师资',
    required_courses: [],
    required_exams: [],
    practice_requirements: {
      min_cases: 100,
      min_completed_paths: 50,
      min_followup_months: 6,
      min_improved_cases: 30
    },
    min_platform_rating: 'A+',
    mentoring_requirements: {
      min_mentees: 10
    },
    granted_permissions: [
      { agent_type: 'basic_assessment', permission_level: 'configure', granted_at: '' },
      { agent_type: 'metabolic_intervention', permission_level: 'configure', granted_at: '' },
      { agent_type: 'personalized_plan', permission_level: 'configure', granted_at: '' },
      { agent_type: 'specialty_expert', permission_level: 'configure', granted_at: '' },
      { agent_type: 'strategy_supervisor', permission_level: 'execute', granted_at: '' },
      { agent_type: 'agent_rules', permission_level: 'configure', granted_at: '' }
    ],
    serviceable_risk_levels: ['low', 'medium', 'high'],
    revenue_share_ratio: 0.75
  }
];

/**
 * 预定义课程库
 */
export const PREDEFINED_COURSES: CourseDefinition[] = [
  // L0 课程
  {
    course_id: 'CRS-L0-K01',
    course_name: '行为健康入门',
    level: 'L0',
    module_type: 'knowledge',
    description: '6讲×15分钟，建立行为健康基础认知',
    duration_minutes: 90,
    content_format: 'video',
    prerequisites: [],
    learning_objectives: ['理解行为健康概念', '认识行为改变的重要性', '了解主动健康理念'],
    assessment_criteria: ['完成全部视频', '课后测验≥80%']
  },
  {
    course_id: 'CRS-L0-K02',
    course_name: '慢病与代谢基础认知',
    level: 'L0',
    module_type: 'knowledge',
    description: '血糖/血压/体重基础解读',
    duration_minutes: 60,
    content_format: 'video',
    prerequisites: ['CRS-L0-K01'],
    learning_objectives: ['理解代谢指标含义', '识别常见慢病风险', '了解行为与代谢关联'],
    assessment_criteria: ['完成全部视频', '完成1份个人行为画像']
  },
  // L1 课程
  {
    course_id: 'CRS-L1-K01',
    course_name: '行为健康基础理论',
    level: 'L1',
    module_type: 'knowledge',
    description: '系统学习行为科学理论基础',
    duration_minutes: 180,
    content_format: 'video',
    prerequisites: ['CRS-L0-K01', 'CRS-L0-K02'],
    learning_objectives: ['掌握TTM阶段模型', '理解COM-B模型', '了解自主性动机理论'],
    assessment_criteria: ['理论考试≥80分']
  },
  {
    course_id: 'CRS-L1-K02',
    course_name: '代谢与慢病风险入门',
    level: 'L1',
    module_type: 'knowledge',
    description: '深入学习代谢相关知识',
    duration_minutes: 120,
    content_format: 'video',
    prerequisites: ['CRS-L0-K02'],
    learning_objectives: ['理解代谢综合征', '掌握风险分层方法', '了解生活方式干预原理'],
    assessment_criteria: ['理论考试≥80分']
  },
  {
    course_id: 'CRS-L1-K03',
    course_name: '指标解读基础',
    level: 'L1',
    module_type: 'knowledge',
    description: 'CGM/血压/体脂数据解读',
    duration_minutes: 150,
    content_format: 'interactive',
    prerequisites: ['CRS-L1-K02'],
    learning_objectives: ['能解读CGM图谱', '能分析血压趋势', '能评估体成分数据'],
    assessment_criteria: ['数据解读实操≥70分']
  },
  {
    course_id: 'CRS-L1-M01',
    course_name: '标准评估流程',
    level: 'L1',
    module_type: 'method',
    description: '掌握标准化评估方法',
    duration_minutes: 90,
    content_format: 'video',
    prerequisites: ['CRS-L1-K01'],
    learning_objectives: ['掌握评估问卷使用', '学会阶段判定', '能完成基础画像'],
    assessment_criteria: ['完成3次模拟评估']
  },
  {
    course_id: 'CRS-L1-M02',
    course_name: '标准14天控糖路径',
    level: 'L1',
    module_type: 'method',
    description: '学习并掌握标准干预路径',
    duration_minutes: 120,
    content_format: 'case_study',
    prerequisites: ['CRS-L1-M01'],
    learning_objectives: ['理解14天路径设计', '掌握每日任务安排', '学会进度跟踪'],
    assessment_criteria: ['路径模拟通过']
  },
  {
    course_id: 'CRS-L1-S01',
    course_name: '基础教练对话',
    level: 'L1',
    module_type: 'skill',
    description: '教练式对话基础技能',
    duration_minutes: 180,
    content_format: 'simulation',
    prerequisites: ['CRS-L1-K01'],
    learning_objectives: ['掌握开放式提问', '学会积极倾听', '能给予有效反馈'],
    assessment_criteria: ['对话录音评估≥70分']
  },
  {
    course_id: 'CRS-L1-S02',
    course_name: '目标设定与简单阻抗处理',
    level: 'L1',
    module_type: 'skill',
    description: 'SMART目标设定和基础阻抗应对',
    duration_minutes: 120,
    content_format: 'simulation',
    prerequisites: ['CRS-L1-S01'],
    learning_objectives: ['掌握SMART目标法', '识别常见阻抗', '学会基础应对策略'],
    assessment_criteria: ['情景模拟≥70分']
  },
  // L2 课程
  {
    course_id: 'CRS-L2-K01',
    course_name: '代谢综合征系统课程',
    level: 'L2',
    module_type: 'knowledge',
    description: '深入学习代谢综合征机制与干预',
    duration_minutes: 300,
    content_format: 'video',
    prerequisites: ['CRS-L1-K02'],
    learning_objectives: ['深入理解代谢机制', '掌握多因素干预', '了解药物与生活方式协同'],
    assessment_criteria: ['理论考试≥80分', '案例分析报告']
  },
  {
    course_id: 'CRS-L2-K02',
    course_name: 'CGM深度解读',
    level: 'L2',
    module_type: 'knowledge',
    description: 'CGM高级数据分析与应用',
    duration_minutes: 180,
    content_format: 'interactive',
    prerequisites: ['CRS-L1-K03'],
    learning_objectives: ['掌握TIR/TAR/TBR分析', '能识别血糖模式', '学会基于CGM调整干预'],
    assessment_criteria: ['CGM解读实操≥75分']
  },
  {
    course_id: 'CRS-L2-K03',
    course_name: '行为-生理联动模型',
    level: 'L2',
    module_type: 'knowledge',
    description: '理解行为与生理指标的双向关系',
    duration_minutes: 150,
    content_format: 'video',
    prerequisites: ['CRS-L2-K01'],
    learning_objectives: ['理解心身联动', '掌握压力-代谢关联', '了解睡眠-代谢关系'],
    assessment_criteria: ['理论考试≥80分']
  },
  {
    course_id: 'CRS-L2-M01',
    course_name: '个性化干预路径设计',
    level: 'L2',
    module_type: 'method',
    description: '学习根据用户画像设计个性化方案',
    duration_minutes: 240,
    content_format: 'case_study',
    prerequisites: ['CRS-L1-M02', 'CRS-L2-K01'],
    learning_objectives: ['掌握画像分析', '能设计个性化路径', '学会方案调整'],
    assessment_criteria: ['个性化方案设计评审']
  },
  {
    course_id: 'CRS-L2-M02',
    course_name: '多指标联动处方',
    level: 'L2',
    module_type: 'method',
    description: '学习综合多个指标制定干预处方',
    duration_minutes: 180,
    content_format: 'case_study',
    prerequisites: ['CRS-L2-M01'],
    learning_objectives: ['理解指标关联', '能制定联动处方', '掌握优先级排序'],
    assessment_criteria: ['处方设计评审']
  },
  {
    course_id: 'CRS-L2-M03',
    course_name: '动态调整方法',
    level: 'L2',
    module_type: 'method',
    description: '学习根据反馈动态调整干预策略',
    duration_minutes: 150,
    content_format: 'simulation',
    prerequisites: ['CRS-L2-M02'],
    learning_objectives: ['掌握数据复盘', '能识别调整信号', '学会策略迭代'],
    assessment_criteria: ['动态调整模拟']
  },
  {
    course_id: 'CRS-L2-S01',
    course_name: '高级动机访谈',
    level: 'L2',
    module_type: 'skill',
    description: '深入学习动机访谈技术',
    duration_minutes: 300,
    content_format: 'simulation',
    prerequisites: ['CRS-L1-S01'],
    learning_objectives: ['掌握MI核心精神', '学会OARS技术', '能处理矛盾心理'],
    assessment_criteria: ['MI技能评估≥75分']
  },
  {
    course_id: 'CRS-L2-S02',
    course_name: '阻抗与失败复盘',
    level: 'L2',
    module_type: 'skill',
    description: '高级阻抗处理与失败案例复盘',
    duration_minutes: 180,
    content_format: 'simulation',
    prerequisites: ['CRS-L1-S02', 'CRS-L2-S01'],
    learning_objectives: ['深入理解阻抗', '掌握复盘方法', '能转化失败为学习'],
    assessment_criteria: ['复盘案例评审']
  },
  {
    course_id: 'CRS-L2-S03',
    course_name: '长程陪伴能力',
    level: 'L2',
    module_type: 'skill',
    description: '建立长期教练关系的能力培养',
    duration_minutes: 150,
    content_format: 'video',
    prerequisites: ['CRS-L2-S01'],
    learning_objectives: ['理解长程陪伴理念', '掌握关系维护技巧', '学会边界管理'],
    assessment_criteria: ['长程案例跟踪']
  }
];

/**
 * 预定义考试
 */
export const PREDEFINED_EXAMS: ExamDefinition[] = [
  // L0 考试
  {
    exam_id: 'EXM-L0-T01',
    exam_name: '入门知识测验',
    level: 'L0',
    exam_type: 'theory',
    passing_score: 80,
    weight_percent: 100,
    duration_minutes: 30,
    questions_count: 20
  },
  // L1 考试
  {
    exam_id: 'EXM-L1-T01',
    exam_name: 'L1理论机考',
    level: 'L1',
    exam_type: 'theory',
    passing_score: 80,
    weight_percent: 40,
    duration_minutes: 60,
    questions_count: 50
  },
  {
    exam_id: 'EXM-L1-C01',
    exam_name: 'L1标准案例模拟',
    level: 'L1',
    exam_type: 'case_simulation',
    passing_score: 70,
    weight_percent: 30,
    duration_minutes: 45,
    questions_count: 3
  },
  {
    exam_id: 'EXM-L1-D01',
    exam_name: 'L1对话录音评估',
    level: 'L1',
    exam_type: 'dialogue_assessment',
    passing_score: 70,
    weight_percent: 30,
    duration_minutes: 30
  },
  // L2 考试
  {
    exam_id: 'EXM-L2-T01',
    exam_name: 'L2理论考试',
    level: 'L2',
    exam_type: 'theory',
    passing_score: 80,
    weight_percent: 30,
    duration_minutes: 90,
    questions_count: 60
  },
  {
    exam_id: 'EXM-L2-C01',
    exam_name: 'L2实战案例评审',
    level: 'L2',
    exam_type: 'case_simulation',
    passing_score: 75,
    weight_percent: 40,
    duration_minutes: 60
  },
  {
    exam_id: 'EXM-L2-D01',
    exam_name: 'L2对话质控评分',
    level: 'L2',
    exam_type: 'dialogue_assessment',
    passing_score: 75,
    weight_percent: 30,
    duration_minutes: 45
  },
  // L3 专项考试
  {
    exam_id: 'EXM-L3-S01',
    exam_name: '糖尿病逆转专项笔试',
    level: 'L3',
    exam_type: 'specialty',
    passing_score: 80,
    weight_percent: 40,
    duration_minutes: 90,
    specialty: 'diabetes_reversal'
  },
  {
    exam_id: 'EXM-L3-S02',
    exam_name: '高血压专项笔试',
    level: 'L3',
    exam_type: 'specialty',
    passing_score: 80,
    weight_percent: 40,
    duration_minutes: 90,
    specialty: 'hypertension'
  },
  {
    exam_id: 'EXM-L3-S03',
    exam_name: '体重管理专项笔试',
    level: 'L3',
    exam_type: 'specialty',
    passing_score: 80,
    weight_percent: 40,
    duration_minutes: 90,
    specialty: 'weight_management'
  },
  {
    exam_id: 'EXM-L3-C01',
    exam_name: 'L3真实病例答辩',
    level: 'L3',
    exam_type: 'case_simulation',
    passing_score: 80,
    weight_percent: 30,
    duration_minutes: 60
  },
  {
    exam_id: 'EXM-L3-D01',
    exam_name: 'L3督导现场评估',
    level: 'L3',
    exam_type: 'dialogue_assessment',
    passing_score: 80,
    weight_percent: 30,
    duration_minutes: 60
  }
];

/**
 * 认证服务
 */
export class CertificationService {
  private coaches: Map<string, CoachProfile> = new Map();
  private cases: Map<string, CoachCase> = new Map();
  private courses: Map<string, CourseDefinition> = new Map();
  private exams: Map<string, ExamDefinition> = new Map();
  private trainingSessions: Map<string, TrainingSession> = new Map();

  constructor() {
    // 加载预定义课程
    PREDEFINED_COURSES.forEach(c => this.courses.set(c.course_id, c));
    // 加载预定义考试
    PREDEFINED_EXAMS.forEach(e => this.exams.set(e.exam_id, e));
  }

  /**
   * 创建教练档案
   */
  createCoachProfile(userId: string, name: string): CoachProfile {
    const profile: CoachProfile = {
      coach_id: uuidv4(),
      user_id: userId,
      name,
      level: 'L0',
      specialty_tags: [],
      competency: this.createEmptyCompetency(),
      completed_courses: [],
      passed_exams: [],
      real_cases: [],
      quality_score: 0,
      platform_rating: 'C',
      agent_permissions: [],
      serviceable_risk_levels: [],
      revenue_share_ratio: 0,
      mentoring_records: [],
      registered_at: new Date().toISOString(),
      level_achieved_at: new Date().toISOString(),
      status: 'active'
    };

    this.coaches.set(profile.coach_id, profile);
    return profile;
  }

  /**
   * 创建空能力模型
   */
  private createEmptyCompetency(): CoachCompetencyModel {
    return {
      knowledge: {
        behavioral_science: 0,
        metabolic_medicine: 0,
        lifestyle_medicine: 0,
        psychology_motivation: 0,
        data_interpretation: 0
      },
      method: {
        behavioral_assessment: 0,
        stage_models: 0,
        prescription_design: 0,
        intervention_planning: 0,
        review_adjustment: 0
      },
      skill: {
        motivational_interview: 0,
        coaching_dialogue: 0,
        resistance_handling: 0,
        goal_decomposition: 0,
        accompaniment_feedback: 0,
        platform_tools: 0
      },
      value: {
        proactive_health: 0,
        behavior_ethics: 0,
        boundary_awareness: 0,
        long_term_mindset: 0
      }
    };
  }

  /**
   * 完成课程
   */
  completeCourse(coachId: string, courseId: string, score?: number): boolean {
    const coach = this.coaches.get(coachId);
    const course = this.courses.get(courseId);

    if (!coach || !course) return false;

    // 检查前置条件
    for (const prereq of course.prerequisites) {
      if (!coach.completed_courses.some(c => c.course_id === prereq)) {
        return false;
      }
    }

    const completed: CompletedCourse = {
      course_id: courseId,
      course_name: course.course_name,
      level: course.level,
      module_type: course.module_type,
      completed_at: new Date().toISOString(),
      score
    };

    coach.completed_courses.push(completed);
    this.updateCompetencyFromCourse(coach, course);

    return true;
  }

  /**
   * 通过考试
   */
  passExam(coachId: string, examId: string, score: number): boolean {
    const coach = this.coaches.get(coachId);
    const exam = this.exams.get(examId);

    if (!coach || !exam) return false;
    if (score < exam.passing_score) return false;

    const passed: PassedExam = {
      exam_id: examId,
      exam_name: exam.exam_name,
      level: exam.level,
      exam_type: exam.exam_type,
      score,
      passed_at: new Date().toISOString()
    };

    coach.passed_exams.push(passed);
    return true;
  }

  /**
   * 创建案例
   */
  createCase(coachId: string, clientUserId: string, riskType: 'low' | 'medium' | 'high'): CoachCase | null {
    const coach = this.coaches.get(coachId);
    if (!coach) return null;

    // 检查权限
    if (!coach.serviceable_risk_levels.includes(riskType)) {
      return null;
    }

    const coachCase: CoachCase = {
      case_id: uuidv4(),
      coach_id: coachId,
      user_id: clientUserId,
      risk_type: riskType,
      primary_issues: [],
      intervention_path: {
        path_id: '',
        path_name: '',
        duration_days: 14,
        phases: []
      },
      outcome_metrics: [],
      status: 'ongoing',
      start_date: new Date().toISOString()
    };

    this.cases.set(coachCase.case_id, coachCase);
    coach.real_cases.push(coachCase.case_id);

    return coachCase;
  }

  /**
   * 完成案例
   */
  completeCase(caseId: string, outcomes: CoachCase['outcome_metrics']): boolean {
    const coachCase = this.cases.get(caseId);
    if (!coachCase) return false;

    coachCase.status = 'completed';
    coachCase.end_date = new Date().toISOString();
    coachCase.outcome_metrics = outcomes;

    return true;
  }

  /**
   * 更新能力模型
   */
  private updateCompetencyFromCourse(coach: CoachProfile, course: CourseDefinition): void {
    const increment = 10;

    switch (course.module_type) {
      case 'knowledge':
        coach.competency.knowledge.behavioral_science += increment;
        coach.competency.knowledge.metabolic_medicine += increment;
        break;
      case 'method':
        coach.competency.method.behavioral_assessment += increment;
        coach.competency.method.intervention_planning += increment;
        break;
      case 'skill':
        coach.competency.skill.coaching_dialogue += increment;
        coach.competency.skill.resistance_handling += increment;
        break;
      case 'value':
        coach.competency.value.proactive_health += increment;
        coach.competency.value.behavior_ethics += increment;
        break;
    }

    // 限制最大值100
    this.capCompetency(coach.competency);
  }

  /**
   * 限制能力值上限
   */
  private capCompetency(competency: CoachCompetencyModel): void {
    for (const category of Object.values(competency)) {
      for (const key of Object.keys(category)) {
        (category as any)[key] = Math.min(100, (category as any)[key]);
      }
    }
  }

  /**
   * 获取教练档案
   */
  getCoachProfile(coachId: string): CoachProfile | undefined {
    return this.coaches.get(coachId);
  }

  /**
   * 获取教练案例列表
   */
  getCoachCases(coachId: string): CoachCase[] {
    return Array.from(this.cases.values()).filter(c => c.coach_id === coachId);
  }

  /**
   * 获取等级要求
   */
  getLevelRequirement(level: CertificationLevel): LevelRequirement | undefined {
    return LEVEL_REQUIREMENTS.find(r => r.level === level);
  }

  /**
   * 获取所有课程
   */
  getAllCourses(): CourseDefinition[] {
    return Array.from(this.courses.values());
  }

  /**
   * 获取等级课程
   */
  getCoursesByLevel(level: CertificationLevel): CourseDefinition[] {
    return Array.from(this.courses.values()).filter(c => c.level === level);
  }

  /**
   * 获取所有考试
   */
  getAllExams(): ExamDefinition[] {
    return Array.from(this.exams.values());
  }

  /**
   * 获取等级考试
   */
  getExamsByLevel(level: CertificationLevel): ExamDefinition[] {
    return Array.from(this.exams.values()).filter(e => e.level === level);
  }

  /**
   * 创建训练会话
   */
  createTrainingSession(
    coachId: string,
    sessionType: TrainingSession['session_type'],
    scenario: TrainingSession['scenario']
  ): TrainingSession {
    const session: TrainingSession = {
      session_id: uuidv4(),
      coach_id: coachId,
      session_type: sessionType,
      scenario,
      dialogue_turns: []
    };

    this.trainingSessions.set(session.session_id, session);
    return session;
  }

  /**
   * 获取所有教练
   */
  getAllCoaches(): CoachProfile[] {
    return Array.from(this.coaches.values());
  }

  /**
   * 按等级获取教练
   */
  getCoachesByLevel(level: CertificationLevel): CoachProfile[] {
    return Array.from(this.coaches.values()).filter(c => c.level === level);
  }
}

// 导出单例
export const certificationService = new CertificationService();
