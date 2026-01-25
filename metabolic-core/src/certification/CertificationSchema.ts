/**
 * Certification Schema - 教练认证体系数据结构
 * 行为健康教练认证体系 · 五级制认证系统
 */

/**
 * 认证等级 (L0-L4)
 */
export type CertificationLevel =
  | 'L0'  // 公众学习者（免费）
  | 'L1'  // 初级行为健康教练（助理级）
  | 'L2'  // 中级行为健康教练（独立上岗）
  | 'L3'  // 高级行为健康教练（慢病/专项）
  | 'L4'; // 行为健康督导/讲师/专家

/**
 * 专项方向
 */
export type SpecialtyTag =
  | 'diabetes_reversal'    // 糖尿病逆转专项
  | 'hypertension'         // 高血压专项
  | 'weight_management'    // 体重管理专项
  | 'stress_psychology'    // 心理压力专项
  | 'metabolic_syndrome'   // 代谢综合征专项
  | 'sleep_optimization';  // 睡眠优化专项

/**
 * K-M-S-V 四维能力模型
 */
export interface CoachCompetencyModel {
  /** Knowledge - 知识体系 */
  knowledge: {
    behavioral_science: number;      // 行为科学基础 (0-100)
    metabolic_medicine: number;      // 慢病与代谢医学基础
    lifestyle_medicine: number;      // 生活方式医学
    psychology_motivation: number;   // 心理与动机理论
    data_interpretation: number;     // 数据与指标解读
  };
  /** Method - 方法体系 */
  method: {
    behavioral_assessment: number;   // 行为评估方法
    stage_models: number;            // 阶段模型（TTM/COM-B/自主性模型）
    prescription_design: number;     // 行为处方设计
    intervention_planning: number;   // 干预路径拆解
    review_adjustment: number;       // 复盘与调整方法
  };
  /** Skill - 核心技能 */
  skill: {
    motivational_interview: number;  // 动机访谈（MI）
    coaching_dialogue: number;       // 教练式对话
    resistance_handling: number;     // 阻抗处理
    goal_decomposition: number;      // 目标拆解
    accompaniment_feedback: number;  // 陪伴与反馈
    platform_tools: number;          // 平台工具使用能力
  };
  /** Value/View - 观念与职业心智 */
  value: {
    proactive_health: number;        // 主动健康观
    behavior_ethics: number;         // 行为改变伦理
    boundary_awareness: number;      // 边界与角色认知
    long_term_mindset: number;       // 长程陪伴理念
  };
}

/**
 * 教练档案
 */
export interface CoachProfile {
  /** 教练ID */
  coach_id: string;
  /** 用户ID（关联账户） */
  user_id: string;
  /** 姓名 */
  name: string;
  /** 当前等级 */
  level: CertificationLevel;
  /** 专项标签 */
  specialty_tags: SpecialtyTag[];
  /** 能力模型评分 */
  competency: CoachCompetencyModel;
  /** 已完成课程 */
  completed_courses: CompletedCourse[];
  /** 已通过考试 */
  passed_exams: PassedExam[];
  /** 真实案例列表 */
  real_cases: string[];  // CoachCase IDs
  /** 质量评分 (0-100) */
  quality_score: number;
  /** 平台评分等级 */
  platform_rating: 'S' | 'A+' | 'A' | 'A-' | 'B+' | 'B' | 'B-' | 'C' | 'D';
  /** Agent权限 */
  agent_permissions: AgentPermission[];
  /** 可服务人群类型 */
  serviceable_risk_levels: ('low' | 'medium' | 'high')[];
  /** 收益分成比例 */
  revenue_share_ratio: number;
  /** 带教记录 */
  mentoring_records: MentoringRecord[];
  /** 注册时间 */
  registered_at: string;
  /** 当前等级获得时间 */
  level_achieved_at: string;
  /** 状态 */
  status: 'active' | 'inactive' | 'suspended' | 'pending_review';
}

/**
 * 已完成课程
 */
export interface CompletedCourse {
  course_id: string;
  course_name: string;
  level: CertificationLevel;
  module_type: 'knowledge' | 'method' | 'skill' | 'value';
  completed_at: string;
  score?: number;
}

/**
 * 已通过考试
 */
export interface PassedExam {
  exam_id: string;
  exam_name: string;
  level: CertificationLevel;
  exam_type: 'theory' | 'case_simulation' | 'dialogue_assessment' | 'specialty';
  score: number;
  passed_at: string;
}

/**
 * Agent权限
 */
export interface AgentPermission {
  agent_type: string;
  permission_level: 'read' | 'execute' | 'configure';
  granted_at: string;
}

/**
 * 带教记录
 */
export interface MentoringRecord {
  mentee_id: string;
  mentee_name: string;
  start_date: string;
  end_date?: string;
  outcome?: 'promoted' | 'ongoing' | 'dropped';
  supervisor_notes?: string;
}

/**
 * 教练案例
 */
export interface CoachCase {
  /** 案例ID */
  case_id: string;
  /** 教练ID */
  coach_id: string;
  /** 用户ID（客户） */
  user_id: string;
  /** 风险类型 */
  risk_type: 'low' | 'medium' | 'high';
  /** 主要问题 */
  primary_issues: string[];
  /** 干预路径 */
  intervention_path: {
    path_id: string;
    path_name: string;
    duration_days: number;
    phases: {
      phase: number;
      description: string;
      interventions: string[];
    }[];
  };
  /** 结果指标 */
  outcome_metrics: {
    metric: string;
    baseline: number;
    final: number;
    improvement_percent: number;
  }[];
  /** 督导评分 */
  supervisor_score?: number;
  /** 督导评语 */
  supervisor_comments?: string;
  /** 案例状态 */
  status: 'ongoing' | 'completed' | 'abandoned';
  /** 开始日期 */
  start_date: string;
  /** 结束日期 */
  end_date?: string;
  /** 随访时长(月) */
  followup_months?: number;
  /** 对话质控评分 */
  dialogue_quality_score?: number;
  /** 客户满意度 */
  client_satisfaction?: number;
}

/**
 * 课程定义
 */
export interface CourseDefinition {
  course_id: string;
  course_name: string;
  level: CertificationLevel;
  module_type: 'knowledge' | 'method' | 'skill' | 'value';
  description: string;
  duration_minutes: number;
  content_format: 'video' | 'interactive' | 'case_study' | 'simulation';
  prerequisites: string[];
  learning_objectives: string[];
  assessment_criteria: string[];
}

/**
 * 考试定义
 */
export interface ExamDefinition {
  exam_id: string;
  exam_name: string;
  level: CertificationLevel;
  exam_type: 'theory' | 'case_simulation' | 'dialogue_assessment' | 'specialty';
  passing_score: number;
  weight_percent: number;
  duration_minutes: number;
  questions_count?: number;
  specialty?: SpecialtyTag;
}

/**
 * 等级要求定义
 */
export interface LevelRequirement {
  level: CertificationLevel;
  name: string;
  description: string;
  /** 课程要求 */
  required_courses: {
    module_type: 'knowledge' | 'method' | 'skill' | 'value';
    course_ids: string[];
  }[];
  /** 考试要求 */
  required_exams: {
    exam_type: 'theory' | 'case_simulation' | 'dialogue_assessment' | 'specialty';
    min_score: number;
    weight_percent: number;
  }[];
  /** 实战要求 */
  practice_requirements: {
    min_cases: number;
    min_completed_paths: number;
    min_followup_months?: number;
    min_improved_cases?: number;
  };
  /** 平台评分要求 */
  min_platform_rating?: 'S' | 'A+' | 'A' | 'A-' | 'B+' | 'B' | 'B-' | 'C' | 'D';
  /** 带教要求 */
  mentoring_requirements?: {
    min_mentees: number;
  };
  /** 授予的Agent权限 */
  granted_permissions: AgentPermission[];
  /** 可服务人群 */
  serviceable_risk_levels: ('low' | 'medium' | 'high')[];
  /** 收益分成比例 */
  revenue_share_ratio: number;
}

/**
 * 晋级申请
 */
export interface PromotionApplication {
  application_id: string;
  coach_id: string;
  current_level: CertificationLevel;
  target_level: CertificationLevel;
  submitted_at: string;
  status: 'pending' | 'under_review' | 'approved' | 'rejected' | 'need_supplement';
  review_result?: {
    reviewer_id: string;
    reviewed_at: string;
    decision: 'approved' | 'rejected' | 'need_supplement';
    comments: string;
    recommended_modules?: string[];
  };
  evidence: {
    theory_scores: { exam_id: string; score: number }[];
    skill_scores: { exam_id: string; score: number }[];
    case_ids: string[];
    platform_rating: string;
    additional_documents?: string[];
  };
}

/**
 * 智能陪练会话
 */
export interface TrainingSession {
  session_id: string;
  coach_id: string;
  session_type: 'ai_simulation' | 'resistance_scenario' | 'dialogue_practice' | 'path_review';
  scenario: {
    scenario_id: string;
    scenario_name: string;
    difficulty: 'beginner' | 'intermediate' | 'advanced';
    client_profile: string;
    presenting_issue: string;
    expected_approach: string[];
  };
  dialogue_turns: {
    turn: number;
    speaker: 'coach' | 'client';
    content: string;
    timestamp: string;
  }[];
  ai_feedback?: {
    overall_score: number;
    strengths: string[];
    improvements: string[];
    specific_feedback: {
      turn: number;
      feedback: string;
      suggestion: string;
    }[];
  };
  completed_at?: string;
}
