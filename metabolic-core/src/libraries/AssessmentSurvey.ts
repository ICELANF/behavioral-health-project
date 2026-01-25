/**
 * Assessment Survey Library - 评估问卷库
 * 集成BAPS及其他评估工具
 */

import { v4 as uuidv4 } from 'uuid';

/**
 * 问卷类型
 */
export type SurveyType =
  | 'big_five'        // 大五人格
  | 'bpt6'            // 行为模式类型
  | 'capacity'        // 改变能力评估
  | 'spi'             // 成功可能性指数
  | 'phq9'            // 抑郁筛查
  | 'gad7'            // 焦虑筛查
  | 'dsm_screening'   // 糖尿病自我管理
  | 'health_literacy' // 健康素养
  | 'custom';         // 自定义

/**
 * 问题类型
 */
export type QuestionType =
  | 'likert_5'        // 5点量表
  | 'likert_7'        // 7点量表
  | 'bipolar'         // 双极量表
  | 'single_choice'   // 单选
  | 'multiple_choice' // 多选
  | 'text'            // 文本
  | 'number';         // 数字

/**
 * 问题定义
 */
export interface SurveyQuestion {
  /** 问题ID */
  question_id: string;
  /** 问题序号 */
  order: number;
  /** 问题文本 */
  text: string;
  /** 问题类型 */
  type: QuestionType;
  /** 选项 */
  options?: {
    value: number | string;
    label: string;
  }[];
  /** 是否反向计分 */
  reverse_scored?: boolean;
  /** 所属维度 */
  dimension?: string;
  /** 必答 */
  required: boolean;
}

/**
 * 问卷定义
 */
export interface SurveyDefinition {
  /** 问卷ID */
  survey_id: string;
  /** 问卷类型 */
  type: SurveyType;
  /** 问卷名称 */
  name: string;
  /** 问卷描述 */
  description: string;
  /** 问题列表 */
  questions: SurveyQuestion[];
  /** 维度列表 */
  dimensions?: {
    id: string;
    name: string;
    description: string;
    questions: string[]; // question_ids
  }[];
  /** 计分规则 */
  scoring_rules?: {
    type: 'sum' | 'average' | 'weighted' | 'custom';
    weights?: Record<string, number>;
    custom_formula?: string;
  };
  /** 结果解释 */
  result_interpretation?: {
    ranges: {
      min: number;
      max: number;
      level: string;
      description: string;
    }[];
  };
  /** 完成时间(分钟) */
  estimated_minutes: number;
  /** 版本 */
  version: string;
}

/**
 * 问卷回答
 */
export interface SurveyResponse {
  /** 回答ID */
  response_id: string;
  /** 用户ID */
  user_id: string;
  /** 问卷ID */
  survey_id: string;
  /** 回答内容 */
  answers: Record<string, number | string | string[]>;
  /** 开始时间 */
  started_at: string;
  /** 完成时间 */
  completed_at?: string;
  /** 状态 */
  status: 'in_progress' | 'completed' | 'abandoned';
}

/**
 * 评估结果
 */
export interface SurveyResult {
  /** 结果ID */
  result_id: string;
  /** 回答ID */
  response_id: string;
  /** 用户ID */
  user_id: string;
  /** 问卷类型 */
  survey_type: SurveyType;
  /** 总分 */
  total_score?: number;
  /** 维度得分 */
  dimension_scores?: Record<string, number>;
  /** 结果级别 */
  result_level?: string;
  /** 结果解释 */
  interpretation?: string;
  /** 建议 */
  recommendations?: string[];
  /** 计算时间 */
  calculated_at: string;
}

/**
 * PHQ-9抑郁筛查问卷
 */
const PHQ9_SURVEY: SurveyDefinition = {
  survey_id: 'SURVEY-PHQ9',
  type: 'phq9',
  name: 'PHQ-9 抑郁症筛查量表',
  description: '过去2周内，您有多少时候受到以下问题困扰？',
  questions: [
    {
      question_id: 'PHQ9-1',
      order: 1,
      text: '做事时提不起劲或没有兴趣',
      type: 'likert_5',
      options: [
        { value: 0, label: '完全不会' },
        { value: 1, label: '好几天' },
        { value: 2, label: '一半以上的天数' },
        { value: 3, label: '几乎每天' }
      ],
      dimension: 'depression',
      required: true
    },
    {
      question_id: 'PHQ9-2',
      order: 2,
      text: '感到心情低落、沮丧或绝望',
      type: 'likert_5',
      options: [
        { value: 0, label: '完全不会' },
        { value: 1, label: '好几天' },
        { value: 2, label: '一半以上的天数' },
        { value: 3, label: '几乎每天' }
      ],
      dimension: 'depression',
      required: true
    },
    {
      question_id: 'PHQ9-3',
      order: 3,
      text: '入睡困难、睡不安稳或睡眠过多',
      type: 'likert_5',
      options: [
        { value: 0, label: '完全不会' },
        { value: 1, label: '好几天' },
        { value: 2, label: '一半以上的天数' },
        { value: 3, label: '几乎每天' }
      ],
      dimension: 'depression',
      required: true
    },
    {
      question_id: 'PHQ9-4',
      order: 4,
      text: '感觉疲倦或没有活力',
      type: 'likert_5',
      options: [
        { value: 0, label: '完全不会' },
        { value: 1, label: '好几天' },
        { value: 2, label: '一半以上的天数' },
        { value: 3, label: '几乎每天' }
      ],
      dimension: 'depression',
      required: true
    },
    {
      question_id: 'PHQ9-5',
      order: 5,
      text: '食欲不振或吃太多',
      type: 'likert_5',
      options: [
        { value: 0, label: '完全不会' },
        { value: 1, label: '好几天' },
        { value: 2, label: '一半以上的天数' },
        { value: 3, label: '几乎每天' }
      ],
      dimension: 'depression',
      required: true
    },
    {
      question_id: 'PHQ9-6',
      order: 6,
      text: '觉得自己很糟，或觉得自己很失败，或让自己或家人失望',
      type: 'likert_5',
      options: [
        { value: 0, label: '完全不会' },
        { value: 1, label: '好几天' },
        { value: 2, label: '一半以上的天数' },
        { value: 3, label: '几乎每天' }
      ],
      dimension: 'depression',
      required: true
    },
    {
      question_id: 'PHQ9-7',
      order: 7,
      text: '对事物专注有困难，例如阅读报纸或看电视时',
      type: 'likert_5',
      options: [
        { value: 0, label: '完全不会' },
        { value: 1, label: '好几天' },
        { value: 2, label: '一半以上的天数' },
        { value: 3, label: '几乎每天' }
      ],
      dimension: 'depression',
      required: true
    },
    {
      question_id: 'PHQ9-8',
      order: 8,
      text: '动作或说话速度缓慢到别人已经察觉？或正好相反——Loss躁动或坐立不安',
      type: 'likert_5',
      options: [
        { value: 0, label: '完全不会' },
        { value: 1, label: '好几天' },
        { value: 2, label: '一半以上的天数' },
        { value: 3, label: '几乎每天' }
      ],
      dimension: 'depression',
      required: true
    },
    {
      question_id: 'PHQ9-9',
      order: 9,
      text: '有不如死掉或用某种方式伤害自己的念头',
      type: 'likert_5',
      options: [
        { value: 0, label: '完全不会' },
        { value: 1, label: '好几天' },
        { value: 2, label: '一半以上的天数' },
        { value: 3, label: '几乎每天' }
      ],
      dimension: 'depression',
      required: true
    }
  ],
  dimensions: [
    {
      id: 'depression',
      name: '抑郁症状',
      description: 'PHQ-9总分反映抑郁症状严重程度',
      questions: ['PHQ9-1', 'PHQ9-2', 'PHQ9-3', 'PHQ9-4', 'PHQ9-5', 'PHQ9-6', 'PHQ9-7', 'PHQ9-8', 'PHQ9-9']
    }
  ],
  scoring_rules: {
    type: 'sum'
  },
  result_interpretation: {
    ranges: [
      { min: 0, max: 4, level: '正常', description: '无明显抑郁症状' },
      { min: 5, max: 9, level: '轻度', description: '轻度抑郁症状，建议关注' },
      { min: 10, max: 14, level: '中度', description: '中度抑郁症状，建议就医' },
      { min: 15, max: 19, level: '中重度', description: '中重度抑郁症状，需要治疗' },
      { min: 20, max: 27, level: '重度', description: '重度抑郁症状，需紧急干预' }
    ]
  },
  estimated_minutes: 5,
  version: '1.0'
};

/**
 * GAD-7焦虑筛查问卷
 */
const GAD7_SURVEY: SurveyDefinition = {
  survey_id: 'SURVEY-GAD7',
  type: 'gad7',
  name: 'GAD-7 广泛性焦虑障碍量表',
  description: '过去2周内，您有多少时候受到以下问题困扰？',
  questions: [
    {
      question_id: 'GAD7-1',
      order: 1,
      text: '感觉紧张、焦虑或急切',
      type: 'likert_5',
      options: [
        { value: 0, label: '完全不会' },
        { value: 1, label: '好几天' },
        { value: 2, label: '一半以上的天数' },
        { value: 3, label: '几乎每天' }
      ],
      dimension: 'anxiety',
      required: true
    },
    {
      question_id: 'GAD7-2',
      order: 2,
      text: '不能够停止或控制担忧',
      type: 'likert_5',
      options: [
        { value: 0, label: '完全不会' },
        { value: 1, label: '好几天' },
        { value: 2, label: '一半以上的天数' },
        { value: 3, label: '几乎每天' }
      ],
      dimension: 'anxiety',
      required: true
    },
    {
      question_id: 'GAD7-3',
      order: 3,
      text: '对各种各样的事情担忧过多',
      type: 'likert_5',
      options: [
        { value: 0, label: '完全不会' },
        { value: 1, label: '好几天' },
        { value: 2, label: '一半以上的天数' },
        { value: 3, label: '几乎每天' }
      ],
      dimension: 'anxiety',
      required: true
    },
    {
      question_id: 'GAD7-4',
      order: 4,
      text: '很难放松下来',
      type: 'likert_5',
      options: [
        { value: 0, label: '完全不会' },
        { value: 1, label: '好几天' },
        { value: 2, label: '一半以上的天数' },
        { value: 3, label: '几乎每天' }
      ],
      dimension: 'anxiety',
      required: true
    },
    {
      question_id: 'GAD7-5',
      order: 5,
      text: '由于不安而无法静坐',
      type: 'likert_5',
      options: [
        { value: 0, label: '完全不会' },
        { value: 1, label: '好几天' },
        { value: 2, label: '一半以上的天数' },
        { value: 3, label: '几乎每天' }
      ],
      dimension: 'anxiety',
      required: true
    },
    {
      question_id: 'GAD7-6',
      order: 6,
      text: '变得容易烦恼或急躁',
      type: 'likert_5',
      options: [
        { value: 0, label: '完全不会' },
        { value: 1, label: '好几天' },
        { value: 2, label: '一半以上的天数' },
        { value: 3, label: '几乎每天' }
      ],
      dimension: 'anxiety',
      required: true
    },
    {
      question_id: 'GAD7-7',
      order: 7,
      text: '感到似乎将有可怕的事情发生而害怕',
      type: 'likert_5',
      options: [
        { value: 0, label: '完全不会' },
        { value: 1, label: '好几天' },
        { value: 2, label: '一半以上的天数' },
        { value: 3, label: '几乎每天' }
      ],
      dimension: 'anxiety',
      required: true
    }
  ],
  dimensions: [
    {
      id: 'anxiety',
      name: '焦虑症状',
      description: 'GAD-7总分反映焦虑症状严重程度',
      questions: ['GAD7-1', 'GAD7-2', 'GAD7-3', 'GAD7-4', 'GAD7-5', 'GAD7-6', 'GAD7-7']
    }
  ],
  scoring_rules: {
    type: 'sum'
  },
  result_interpretation: {
    ranges: [
      { min: 0, max: 4, level: '正常', description: '无明显焦虑症状' },
      { min: 5, max: 9, level: '轻度', description: '轻度焦虑症状' },
      { min: 10, max: 14, level: '中度', description: '中度焦虑症状，建议就医' },
      { min: 15, max: 21, level: '重度', description: '重度焦虑症状，需要治疗' }
    ]
  },
  estimated_minutes: 3,
  version: '1.0'
};

/**
 * 糖尿病自我管理评估
 */
const DSM_SCREENING_SURVEY: SurveyDefinition = {
  survey_id: 'SURVEY-DSM',
  type: 'dsm_screening',
  name: '糖尿病自我管理评估',
  description: '评估您过去一周的糖尿病自我管理情况',
  questions: [
    {
      question_id: 'DSM-1',
      order: 1,
      text: '过去7天中，您有几天遵循了健康饮食计划？',
      type: 'number',
      dimension: 'diet',
      required: true
    },
    {
      question_id: 'DSM-2',
      order: 2,
      text: '过去7天中，您有几天每天吃了5份或更多的水果和蔬菜？',
      type: 'number',
      dimension: 'diet',
      required: true
    },
    {
      question_id: 'DSM-3',
      order: 3,
      text: '过去7天中，您有几天进行了至少30分钟的体力活动？',
      type: 'number',
      dimension: 'exercise',
      required: true
    },
    {
      question_id: 'DSM-4',
      order: 4,
      text: '过去7天中，您有几天进行了特定的运动（如游泳、步行、骑自行车）？',
      type: 'number',
      dimension: 'exercise',
      required: true
    },
    {
      question_id: 'DSM-5',
      order: 5,
      text: '过去7天中，您有几天测量了血糖？',
      type: 'number',
      dimension: 'monitoring',
      required: true
    },
    {
      question_id: 'DSM-6',
      order: 6,
      text: '过去7天中，您有几天按照医嘱服用了糖尿病药物或注射了胰岛素？',
      type: 'number',
      dimension: 'medication',
      required: true
    },
    {
      question_id: 'DSM-7',
      order: 7,
      text: '过去7天中，您有几天检查了脚？',
      type: 'number',
      dimension: 'foot_care',
      required: true
    }
  ],
  dimensions: [
    { id: 'diet', name: '饮食管理', description: '饮食计划遵从情况', questions: ['DSM-1', 'DSM-2'] },
    { id: 'exercise', name: '运动管理', description: '体力活动情况', questions: ['DSM-3', 'DSM-4'] },
    { id: 'monitoring', name: '血糖监测', description: '血糖自我监测频率', questions: ['DSM-5'] },
    { id: 'medication', name: '药物依从', description: '药物/胰岛素使用依从性', questions: ['DSM-6'] },
    { id: 'foot_care', name: '足部护理', description: '足部自检情况', questions: ['DSM-7'] }
  ],
  scoring_rules: {
    type: 'average'
  },
  estimated_minutes: 5,
  version: '1.0'
};

/**
 * 预定义问卷库
 */
export const PREDEFINED_SURVEYS: SurveyDefinition[] = [
  PHQ9_SURVEY,
  GAD7_SURVEY,
  DSM_SCREENING_SURVEY
];

/**
 * 评估问卷服务
 */
export class AssessmentSurveyService {
  private surveys: Map<string, SurveyDefinition> = new Map();
  private responses: Map<string, SurveyResponse> = new Map();
  private results: Map<string, SurveyResult> = new Map();

  constructor() {
    // 加载预定义问卷
    PREDEFINED_SURVEYS.forEach(s => {
      this.surveys.set(s.survey_id, s);
    });
  }

  /**
   * 获取问卷
   */
  getSurvey(surveyId: string): SurveyDefinition | undefined {
    return this.surveys.get(surveyId);
  }

  /**
   * 按类型获取问卷
   */
  getSurveyByType(type: SurveyType): SurveyDefinition | undefined {
    for (const survey of this.surveys.values()) {
      if (survey.type === type) return survey;
    }
    return undefined;
  }

  /**
   * 开始问卷
   */
  startSurvey(userId: string, surveyId: string): SurveyResponse | null {
    const survey = this.surveys.get(surveyId);
    if (!survey) return null;

    const response: SurveyResponse = {
      response_id: uuidv4(),
      user_id: userId,
      survey_id: surveyId,
      answers: {},
      started_at: new Date().toISOString(),
      status: 'in_progress'
    };

    this.responses.set(response.response_id, response);
    return response;
  }

  /**
   * 提交答案
   */
  submitAnswer(
    responseId: string,
    questionId: string,
    answer: number | string | string[]
  ): boolean {
    const response = this.responses.get(responseId);
    if (!response || response.status !== 'in_progress') return false;

    response.answers[questionId] = answer;
    return true;
  }

  /**
   * 完成问卷并计分
   */
  completeSurvey(responseId: string): SurveyResult | null {
    const response = this.responses.get(responseId);
    if (!response) return null;

    const survey = this.surveys.get(response.survey_id);
    if (!survey) return null;

    // 检查必答题
    for (const question of survey.questions) {
      if (question.required && !(question.question_id in response.answers)) {
        return null; // 有必答题未完成
      }
    }

    response.status = 'completed';
    response.completed_at = new Date().toISOString();

    // 计算得分
    const result = this.calculateScore(response, survey);
    this.results.set(result.result_id, result);

    return result;
  }

  /**
   * 计算得分
   */
  private calculateScore(response: SurveyResponse, survey: SurveyDefinition): SurveyResult {
    const dimensionScores: Record<string, number> = {};
    let totalScore = 0;

    // 计算各维度得分
    if (survey.dimensions) {
      for (const dimension of survey.dimensions) {
        let dimScore = 0;
        let count = 0;

        for (const qId of dimension.questions) {
          const answer = response.answers[qId];
          if (typeof answer === 'number') {
            const question = survey.questions.find(q => q.question_id === qId);
            const score = question?.reverse_scored ? (3 - answer) : answer; // 假设最大值为3
            dimScore += score;
            count++;
          }
        }

        if (count > 0) {
          if (survey.scoring_rules?.type === 'average') {
            dimensionScores[dimension.id] = dimScore / count;
          } else {
            dimensionScores[dimension.id] = dimScore;
          }
          totalScore += dimScore;
        }
      }
    } else {
      // 无维度时直接累加
      for (const answer of Object.values(response.answers)) {
        if (typeof answer === 'number') {
          totalScore += answer;
        }
      }
    }

    // 确定结果级别
    let resultLevel: string | undefined;
    let interpretation: string | undefined;

    if (survey.result_interpretation) {
      for (const range of survey.result_interpretation.ranges) {
        if (totalScore >= range.min && totalScore <= range.max) {
          resultLevel = range.level;
          interpretation = range.description;
          break;
        }
      }
    }

    // 生成建议
    const recommendations = this.generateRecommendations(survey.type, totalScore, dimensionScores);

    return {
      result_id: uuidv4(),
      response_id: response.response_id,
      user_id: response.user_id,
      survey_type: survey.type,
      total_score: totalScore,
      dimension_scores: Object.keys(dimensionScores).length > 0 ? dimensionScores : undefined,
      result_level: resultLevel,
      interpretation,
      recommendations,
      calculated_at: new Date().toISOString()
    };
  }

  /**
   * 生成建议
   */
  private generateRecommendations(
    type: SurveyType,
    totalScore: number,
    dimensionScores: Record<string, number>
  ): string[] {
    const recommendations: string[] = [];

    switch (type) {
      case 'phq9':
        if (totalScore >= 10) {
          recommendations.push('建议寻求专业心理健康评估');
          recommendations.push('考虑与医生讨论治疗方案');
        }
        if (totalScore >= 5) {
          recommendations.push('保持规律作息和适度运动');
          recommendations.push('维护社交联系，寻求支持');
        }
        break;

      case 'gad7':
        if (totalScore >= 10) {
          recommendations.push('建议进行专业焦虑评估');
        }
        if (totalScore >= 5) {
          recommendations.push('练习放松技巧如深呼吸');
          recommendations.push('减少咖啡因摄入');
        }
        break;

      case 'dsm_screening':
        if (dimensionScores.diet < 4) {
          recommendations.push('加强饮食计划执行');
        }
        if (dimensionScores.exercise < 3) {
          recommendations.push('增加日常体力活动');
        }
        if (dimensionScores.monitoring < 5) {
          recommendations.push('提高血糖监测频率');
        }
        break;
    }

    return recommendations;
  }

  /**
   * 获取用户历史结果
   */
  getUserResults(userId: string): SurveyResult[] {
    return Array.from(this.results.values()).filter(r => r.user_id === userId);
  }

  /**
   * 注册自定义问卷
   */
  registerSurvey(survey: SurveyDefinition): void {
    this.surveys.set(survey.survey_id, survey);
  }

  /**
   * 获取所有问卷
   */
  getAllSurveys(): SurveyDefinition[] {
    return Array.from(this.surveys.values());
  }
}

// 导出单例
export const assessmentSurveyService = new AssessmentSurveyService();
