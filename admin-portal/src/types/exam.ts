/**
 * 考试系统类型定义
 */

// 认证等级（六级体系）
export type CertificationLevel = 'L0' | 'L1' | 'L2' | 'L3' | 'L4' | 'L5';

// 考试类型
export type ExamType = 'theory' | 'case_simulation' | 'dialogue_assessment' | 'specialty';

// 专项方向
export type SpecialtyTag =
  | 'diabetes_reversal'
  | 'hypertension'
  | 'weight_management'
  | 'stress_psychology'
  | 'metabolic_syndrome'
  | 'sleep_optimization';

// 题目类型
export type QuestionType = 'single' | 'multiple' | 'truefalse' | 'short_answer';

// 题目接口
export interface Question {
  question_id: string;
  content: string;
  type: QuestionType;
  level: CertificationLevel;
  difficulty: 1 | 2 | 3 | 4 | 5;
  options?: string[];
  answer?: number | boolean | number[];
  explanation?: string;
  tags?: string[];
  category?: string;
  use_count: number;
  default_score: number;
  status: 'active' | 'inactive';
  created_at: string;
  updated_at: string;
}

// 考试定义
export interface ExamDefinition {
  exam_id: string;
  exam_name: string;
  level: CertificationLevel;
  exam_type: ExamType;
  passing_score: number;
  weight_percent: number;
  duration_minutes: number | null;
  questions_count: number | null;
  specialty?: SpecialtyTag;
  description?: string;
  instructions?: string;
  question_ids: string[];
  status: 'draft' | 'published' | 'archived';
  max_attempts: number;
  allow_retry: boolean;
  created_at: string;
  updated_at: string;
}

// 考试结果
export interface ExamResult {
  id: string;
  coach_id: string;
  exam_id: string;
  exam_name: string;
  attempt_number: number;
  score: number;
  passing_score: number;
  status: 'passed' | 'failed';
  answers: ExamAnswer[];
  duration_seconds: number;
  started_at: string;
  submitted_at: string;
  violation_count: number;
  integrity_score: number;
  review_status: 'valid' | 'flagged' | 'invalidated';
}

// 单题答案
export interface ExamAnswer {
  question_id: string;
  user_answer: number | number[] | boolean | string;
  correct_answer: number | number[] | boolean | string;
  is_correct: boolean;
  score_earned: number;
  max_score: number;
}

// 考试统计
export interface ExamStatistics {
  exam_id: string;
  totalAttempts: number;
  passCount: number;
  failCount: number;
  passRate: number;
  averageScore: number;
  highestScore: number;
  lowestScore: number;
  averageDurationMinutes?: number;
}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// 考试列表查询参数
export interface ExamListParams {
  level?: CertificationLevel;
  exam_type?: ExamType;
  status?: 'draft' | 'published' | 'archived';
  keyword?: string;
  page?: number;
  page_size?: number;
}

// 题目列表查询参数
export interface QuestionListParams {
  type?: QuestionType;
  level?: CertificationLevel;
  difficulty?: number;
  keyword?: string;
  status?: 'active' | 'inactive';
  exclude_ids?: string[];
  page?: number;
  page_size?: number;
}

// 结果列表查询参数
export interface ResultListParams {
  exam_id: string;
  passed?: boolean;
  date_from?: string;
  date_to?: string;
  keyword?: string;
  page?: number;
  page_size?: number;
}

// UI 显示常量
export const levelLabels: Record<CertificationLevel, string> = {
  L0: 'L0 观察员',
  L1: 'L1 成长者',
  L2: 'L2 分享者',
  L3: 'L3 教练',
  L4: 'L4 促进师',
  L5: 'L5 大师',
};

export const levelColors: Record<CertificationLevel, string> = {
  L0: 'default',
  L1: 'blue',
  L2: 'green',
  L3: 'orange',
  L4: 'purple',
  L5: 'magenta',
};

export const examTypeLabels: Record<ExamType, string> = {
  theory: '理论考试',
  case_simulation: '案例模拟',
  dialogue_assessment: '对话评估',
  specialty: '专项考试',
};

export const examTypeColors: Record<ExamType, string> = {
  theory: 'blue',
  case_simulation: 'green',
  dialogue_assessment: 'orange',
  specialty: 'purple',
};

export const questionTypeLabels: Record<QuestionType, string> = {
  single: '单选题',
  multiple: '多选题',
  truefalse: '判断题',
  short_answer: '简答题',
};

export const questionTypeColors: Record<QuestionType, string> = {
  single: 'blue',
  multiple: 'green',
  truefalse: 'orange',
  short_answer: 'purple',
};

export const statusLabels: Record<string, string> = {
  draft: '草稿',
  published: '已发布',
  archived: '已归档',
};

export const statusBadges: Record<string, string> = {
  draft: 'default',
  published: 'success',
  archived: 'error',
};

export const specialtyLabels: Record<SpecialtyTag, string> = {
  diabetes_reversal: '糖尿病逆转',
  hypertension: '高血压',
  weight_management: '体重管理',
  stress_psychology: '心理压力',
  metabolic_syndrome: '代谢综合征',
  sleep_optimization: '睡眠优化',
};
