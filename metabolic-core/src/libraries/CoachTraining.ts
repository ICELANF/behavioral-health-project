/**
 * Coach Training Library - 教练训练库
 * 管理AI教练和人类教练的训练素材与能力模型
 */

import { v4 as uuidv4 } from 'uuid';
import { BehaviorStage } from '../trajectory/TrajectorySchema';

/**
 * 教练类型
 */
export type CoachType = 'ai' | 'human' | 'hybrid';

/**
 * 技能领域
 */
export type SkillDomain =
  | 'motivational_interviewing'  // 动机访谈
  | 'behavior_change'            // 行为改变
  | 'nutrition_counseling'       // 营养咨询
  | 'exercise_prescription'      // 运动处方
  | 'stress_management'          // 压力管理
  | 'sleep_hygiene'              // 睡眠卫生
  | 'medication_adherence'       // 用药依从
  | 'crisis_intervention'        // 危机干预
  | 'group_facilitation'         // 团体辅导
  | 'data_interpretation';       // 数据解读

/**
 * 技能等级
 */
export type SkillLevel = 'novice' | 'intermediate' | 'advanced' | 'expert';

/**
 * 训练模块
 */
export interface TrainingModule {
  /** 模块ID */
  module_id: string;
  /** 模块名称 */
  name: string;
  /** 技能领域 */
  domain: SkillDomain;
  /** 难度等级 */
  difficulty: SkillLevel;
  /** 描述 */
  description: string;
  /** 学习目标 */
  learning_objectives: string[];
  /** 前置模块 */
  prerequisites?: string[];
  /** 内容单元 */
  units: TrainingUnit[];
  /** 评估方式 */
  assessment: {
    type: 'quiz' | 'case_study' | 'role_play' | 'practical';
    passing_score: number;
    max_attempts?: number;
  };
  /** 预计时长(分钟) */
  duration_minutes: number;
  /** 适用教练类型 */
  applicable_to: CoachType[];
  /** 版本 */
  version: string;
  /** 创建时间 */
  created_at: string;
}

/**
 * 训练单元
 */
export interface TrainingUnit {
  /** 单元ID */
  unit_id: string;
  /** 单元名称 */
  name: string;
  /** 内容类型 */
  content_type: 'text' | 'video' | 'audio' | 'interactive';
  /** 内容 */
  content: string;
  /** 时长(分钟) */
  duration_minutes: number;
  /** 关键要点 */
  key_points: string[];
  /** 练习题 */
  exercises?: {
    question: string;
    type: 'single_choice' | 'multiple_choice' | 'text';
    options?: string[];
    correct_answer: string | string[];
    explanation?: string;
  }[];
}

/**
 * 案例库条目
 */
export interface CaseStudy {
  /** 案例ID */
  case_id: string;
  /** 案例名称 */
  name: string;
  /** 案例类型 */
  type: 'success' | 'challenge' | 'failure';
  /** 相关表型 */
  phenotypes: string[];
  /** 用户阶段 */
  stage: BehaviorStage;
  /** 背景描述 */
  background: string;
  /** 用户画像 */
  user_profile: {
    age_range: string;
    condition: string;
    challenges: string[];
    goals: string[];
  };
  /** 教练行动 */
  coach_actions: {
    action: string;
    rationale: string;
    outcome: string;
  }[];
  /** 结果 */
  outcome: {
    success: boolean;
    metrics_change?: Record<string, number>;
    user_feedback?: string;
    coach_reflection?: string;
  };
  /** 学习要点 */
  learning_points: string[];
  /** 讨论问题 */
  discussion_questions?: string[];
  /** 创建时间 */
  created_at: string;
}

/**
 * AI Prompt模板
 */
export interface AIPromptTemplate {
  /** 模板ID */
  template_id: string;
  /** 模板名称 */
  name: string;
  /** 场景 */
  scenario: string;
  /** 适用阶段 */
  stage?: BehaviorStage;
  /** 系统提示 */
  system_prompt: string;
  /** 用户提示模板 */
  user_prompt_template: string;
  /** 变量 */
  variables: string[];
  /** 输出格式 */
  output_format?: string;
  /** 示例 */
  examples?: {
    input: Record<string, string>;
    output: string;
  }[];
  /** 约束条件 */
  constraints?: string[];
  /** 版本 */
  version: string;
}

/**
 * 教练能力模型
 */
export interface CoachCompetencyModel {
  /** 能力域 */
  domain: SkillDomain;
  /** 能力名称 */
  name: string;
  /** 描述 */
  description: string;
  /** 各等级行为指标 */
  level_indicators: {
    level: SkillLevel;
    behaviors: string[];
    criteria: string[];
  }[];
  /** 评估方法 */
  assessment_methods: string[];
}

/**
 * 预定义训练模块
 */
export const PREDEFINED_MODULES: TrainingModule[] = [
  {
    module_id: 'TRN-001',
    name: '动机访谈基础',
    domain: 'motivational_interviewing',
    difficulty: 'novice',
    description: '学习动机访谈的核心原则和基本技巧',
    learning_objectives: [
      '理解动机访谈的四个原则(RULE)',
      '掌握开放式提问技巧',
      '学会反映式倾听',
      '识别和应对抵触'
    ],
    units: [
      {
        unit_id: 'TRN-001-U1',
        name: '什么是动机访谈',
        content_type: 'text',
        content: `
# 动机访谈概述

动机访谈(Motivational Interviewing, MI)是一种以人为中心的咨询方法，旨在通过探索和解决矛盾心理来增强改变的内在动机。

## 四大原则(RULE)

1. **抵抗反射(Resist the Righting Reflex)**: 避免直接纠正或说教
2. **理解动机(Understand Motivation)**: 探索用户自己的改变理由
3. **倾听(Listen)**: 用反映式倾听表达理解
4. **赋能(Empower)**: 支持用户的自主性和自我效能

## 核心精神

- 合作(Partnership)
- 接纳(Acceptance)
- 同理心(Compassion)
- 唤起(Evocation)
        `,
        duration_minutes: 15,
        key_points: [
          'MI是合作式而非对抗式的',
          '改变的动机来自用户内部',
          '教练的角色是引导而非指导'
        ],
        exercises: [
          {
            question: '动机访谈的四大原则中，"R"代表什么？',
            type: 'single_choice',
            options: [
              '反思(Reflect)',
              '抵抗纠正反射(Resist the Righting Reflex)',
              '重复(Repeat)',
              '回应(Respond)'
            ],
            correct_answer: '抵抗纠正反射(Resist the Righting Reflex)',
            explanation: 'R代表抵抗纠正反射，即避免直接告诉用户该怎么做'
          }
        ]
      },
      {
        unit_id: 'TRN-001-U2',
        name: '开放式提问',
        content_type: 'text',
        content: `
# 开放式提问技巧

开放式问题是动机访谈的核心工具，能够引导用户深入思考。

## 封闭式 vs 开放式

| 封闭式 | 开放式 |
|--------|--------|
| 你吃早餐了吗？ | 跟我说说你的早餐情况？ |
| 你想减肥吗？ | 关于体重，你有什么想法？ |

## 开放式问题的作用

- 鼓励用户表达
- 探索用户的想法和感受
- 避免是/否的简单回答

## 实用句式

- "跟我说说..."
- "帮我理解一下..."
- "你是怎么看待...的？"
- "什么让你...？"
        `,
        duration_minutes: 10,
        key_points: [
          '开放式问题以"什么"、"如何"、"怎样"开头',
          '避免以"是否"、"有没有"开头的封闭式问题',
          '开放式问题能引出更多信息'
        ]
      }
    ],
    assessment: {
      type: 'quiz',
      passing_score: 80,
      max_attempts: 3
    },
    duration_minutes: 45,
    applicable_to: ['ai', 'human', 'hybrid'],
    version: '1.0',
    created_at: new Date().toISOString()
  },
  {
    module_id: 'TRN-002',
    name: '行为改变阶段识别',
    domain: 'behavior_change',
    difficulty: 'intermediate',
    description: '学习识别用户所处的行为改变阶段并采取相应策略',
    learning_objectives: [
      '理解TTM模型的五个阶段',
      '识别各阶段的特征信号',
      '掌握阶段匹配的干预策略',
      '避免阶段不匹配的常见错误'
    ],
    prerequisites: ['TRN-001'],
    units: [
      {
        unit_id: 'TRN-002-U1',
        name: 'TTM模型详解',
        content_type: 'text',
        content: `
# 跨理论模型(TTM)

TTM模型描述了人们改变行为时经历的五个阶段。

## 五个阶段

### 1. 前意向期(Precontemplation)
- 不认为有问题或无意改变
- "我没觉得有什么问题"

### 2. 意向期(Contemplation)
- 意识到问题，考虑改变但存在矛盾
- "我知道应该改变，但是..."

### 3. 准备期(Preparation)
- 决定改变，准备行动
- "我打算从下周开始..."

### 4. 行动期(Action)
- 正在执行改变
- "我已经开始每天散步了"

### 5. 维持期(Maintenance)
- 新行为已稳定(>6个月)
- "这已经成为我的习惯了"
        `,
        duration_minutes: 20,
        key_points: [
          '阶段不是线性的，可能反复',
          '大多数人不在行动期',
          '阶段识别决定干预策略'
        ]
      }
    ],
    assessment: {
      type: 'case_study',
      passing_score: 75
    },
    duration_minutes: 60,
    applicable_to: ['ai', 'human', 'hybrid'],
    version: '1.0',
    created_at: new Date().toISOString()
  }
];

/**
 * 预定义案例
 */
export const PREDEFINED_CASES: CaseStudy[] = [
  {
    case_id: 'CASE-001',
    name: '从抵触到主动：一位2型糖尿病患者的转变',
    type: 'success',
    phenotypes: ['PHE-001', 'PHE-006'],
    stage: 'precontemplation',
    background: '张先生，52岁，确诊2型糖尿病2年，因家人要求使用健康管理APP。初始态度抵触，认为"吃药就行了"。',
    user_profile: {
      age_range: '50-55',
      condition: '2型糖尿病，HbA1c 8.2%',
      challenges: ['否认问题严重性', '久坐办公', '饮食不规律'],
      goals: ['家人希望他改善生活方式']
    },
    coach_actions: [
      {
        action: '不急于给建议，先建立信任关系',
        rationale: '用户处于前意向期，说教会增加抵触',
        outcome: '用户愿意继续对话'
      },
      {
        action: '分享CGM数据，让用户自己发现问题',
        rationale: '客观数据比主观说教更有说服力',
        outcome: '用户首次表达担忧："原来吃完饭血糖会这么高"'
      },
      {
        action: '询问用户最看重什么',
        rationale: '寻找内在动机',
        outcome: '用户提到想看到孙子结婚'
      },
      {
        action: '将目标与健康管理联系起来',
        rationale: '连接内在价值与行为改变',
        outcome: '用户开始主动问"我该怎么做"'
      }
    ],
    outcome: {
      success: true,
      metrics_change: {
        'HbA1c': -0.8,
        'daily_steps': 4000,
        'TIR': 15
      },
      user_feedback: '原来控制血糖不只是吃药，生活方式真的很重要',
      coach_reflection: '前意向期用户需要时间，不能急于求成'
    },
    learning_points: [
      '前意向期用户需要意识唤醒而非行动建议',
      '利用数据让用户自己发现问题',
      '挖掘内在动机是关键',
      '信任关系是一切的基础'
    ],
    discussion_questions: [
      '如果用户始终不承认问题，你会怎么做？',
      '如何在不说教的情况下分享健康知识？'
    ],
    created_at: new Date().toISOString()
  }
];

/**
 * 预定义AI Prompt模板
 */
export const PREDEFINED_PROMPTS: AIPromptTemplate[] = [
  {
    template_id: 'PRM-001',
    name: '动机访谈式回应',
    scenario: '用户表达对改变的矛盾心理',
    system_prompt: `你是一位专业的健康教练，擅长动机访谈技术。
你的回应应该：
1. 表达理解和接纳
2. 使用反映式倾听
3. 探索矛盾而非解决矛盾
4. 避免说教和直接建议
5. 引出用户自己的改变理由`,
    user_prompt_template: `用户说："{user_message}"

当前用户处于{stage}阶段。

请用动机访谈的方式回应，注意：
- 先反映用户的感受和想法
- 使用开放式问题探索
- 不要急于给解决方案`,
    variables: ['user_message', 'stage'],
    output_format: '简洁的对话回应，100字以内',
    examples: [
      {
        input: {
          user_message: '我知道应该控制饮食，但是真的很难做到',
          stage: '意向期'
        },
        output: '听起来您已经意识到饮食控制的重要性，同时也感受到改变的挑战。能跟我说说，是什么让您觉得特别难吗？'
      }
    ],
    constraints: [
      '不使用"你应该"、"你必须"等词汇',
      '不给出具体的饮食建议',
      '保持温和、非评判的语气'
    ],
    version: '1.0'
  },
  {
    template_id: 'PRM-002',
    name: '数据洞察解读',
    scenario: '向用户解释健康数据趋势',
    system_prompt: `你是一位健康数据分析师，需要将复杂的健康数据转化为用户能理解的洞察。
你的解读应该：
1. 使用简单易懂的语言
2. 关联日常生活行为
3. 提供可操作的观察点
4. 避免医学术语
5. 保持积极但诚实的态度`,
    user_prompt_template: `用户的健康数据摘要：
{data_summary}

请为用户生成一段数据解读，包括：
1. 关键发现（正面和需要关注的）
2. 可能的原因分析
3. 建议的观察方向`,
    variables: ['data_summary'],
    output_format: '分段落的解读报告，200字左右',
    version: '1.0'
  }
];

/**
 * 预定义能力模型
 */
export const COMPETENCY_MODELS: CoachCompetencyModel[] = [
  {
    domain: 'motivational_interviewing',
    name: '动机访谈能力',
    description: '运用动机访谈技术促进用户行为改变的能力',
    level_indicators: [
      {
        level: 'novice',
        behaviors: [
          '能够区分开放式和封闭式问题',
          '理解MI的基本原则'
        ],
        criteria: [
          '完成MI基础培训',
          '通过基础测试'
        ]
      },
      {
        level: 'intermediate',
        behaviors: [
          '能够使用反映式倾听',
          '能够识别和处理抵触',
          '能够引出改变谈话'
        ],
        criteria: [
          '完成至少20个案例练习',
          '通过角色扮演评估'
        ]
      },
      {
        level: 'advanced',
        behaviors: [
          '能够灵活运用MI技巧',
          '能够处理复杂的矛盾心理',
          '能够培训他人'
        ],
        criteria: [
          '完成100+案例',
          '用户满意度>90%',
          '完成督导培训'
        ]
      },
      {
        level: 'expert',
        behaviors: [
          '能够创新MI应用场景',
          '能够进行MI研究和发表',
          '能够培训高级教练'
        ],
        criteria: [
          '完成500+案例',
          '发表相关研究/文章',
          '培养出高级教练'
        ]
      }
    ],
    assessment_methods: [
      '知识测试',
      '角色扮演评估',
      '实际案例督导',
      '用户反馈评估'
    ]
  }
];

/**
 * 教练训练服务
 */
export class CoachTrainingService {
  private modules: Map<string, TrainingModule> = new Map();
  private cases: Map<string, CaseStudy> = new Map();
  private prompts: Map<string, AIPromptTemplate> = new Map();
  private competencyModels: Map<SkillDomain, CoachCompetencyModel> = new Map();
  private trainingRecords: Map<string, TrainingRecord[]> = new Map();

  constructor() {
    // 加载预定义数据
    PREDEFINED_MODULES.forEach(m => {
      this.modules.set(m.module_id, m);
    });
    PREDEFINED_CASES.forEach(c => {
      this.cases.set(c.case_id, c);
    });
    PREDEFINED_PROMPTS.forEach(p => {
      this.prompts.set(p.template_id, p);
    });
    COMPETENCY_MODELS.forEach(cm => {
      this.competencyModels.set(cm.domain, cm);
    });
  }

  /**
   * 获取推荐的训练路径
   */
  getRecommendedPath(
    coachType: CoachType,
    currentLevel: SkillLevel,
    targetDomain: SkillDomain
  ): TrainingModule[] {
    const levelOrder: SkillLevel[] = ['novice', 'intermediate', 'advanced', 'expert'];
    const currentIndex = levelOrder.indexOf(currentLevel);

    return Array.from(this.modules.values())
      .filter(m =>
        m.domain === targetDomain &&
        m.applicable_to.includes(coachType) &&
        levelOrder.indexOf(m.difficulty) >= currentIndex
      )
      .sort((a, b) =>
        levelOrder.indexOf(a.difficulty) - levelOrder.indexOf(b.difficulty)
      );
  }

  /**
   * 获取相关案例
   */
  getRelatedCases(
    phenotypes?: string[],
    stage?: BehaviorStage,
    limit: number = 5
  ): CaseStudy[] {
    let results = Array.from(this.cases.values());

    if (phenotypes && phenotypes.length > 0) {
      results = results.filter(c =>
        c.phenotypes.some(p => phenotypes.includes(p))
      );
    }

    if (stage) {
      results = results.filter(c => c.stage === stage);
    }

    return results.slice(0, limit);
  }

  /**
   * 获取AI提示模板
   */
  getPromptTemplate(scenario: string, stage?: BehaviorStage): AIPromptTemplate | undefined {
    for (const prompt of this.prompts.values()) {
      if (prompt.scenario.includes(scenario)) {
        if (!stage || !prompt.stage || prompt.stage === stage) {
          return prompt;
        }
      }
    }
    return undefined;
  }

  /**
   * 填充提示模板
   */
  fillPromptTemplate(
    templateId: string,
    variables: Record<string, string>
  ): { system_prompt: string; user_prompt: string } | null {
    const template = this.prompts.get(templateId);
    if (!template) return null;

    let userPrompt = template.user_prompt_template;
    for (const [key, value] of Object.entries(variables)) {
      userPrompt = userPrompt.replace(`{${key}}`, value);
    }

    return {
      system_prompt: template.system_prompt,
      user_prompt: userPrompt
    };
  }

  /**
   * 记录训练进度
   */
  recordTrainingProgress(
    coachId: string,
    moduleId: string,
    unitId: string,
    score?: number
  ): TrainingRecord {
    const record: TrainingRecord = {
      record_id: uuidv4(),
      coach_id: coachId,
      module_id: moduleId,
      unit_id: unitId,
      completed_at: new Date().toISOString(),
      score
    };

    const coachRecords = this.trainingRecords.get(coachId) || [];
    coachRecords.push(record);
    this.trainingRecords.set(coachId, coachRecords);

    return record;
  }

  /**
   * 获取教练训练记录
   */
  getCoachTrainingRecords(coachId: string): TrainingRecord[] {
    return this.trainingRecords.get(coachId) || [];
  }

  /**
   * 评估教练能力等级
   */
  assessCompetencyLevel(
    coachId: string,
    domain: SkillDomain
  ): SkillLevel {
    const records = this.trainingRecords.get(coachId) || [];
    const domainModules = Array.from(this.modules.values())
      .filter(m => m.domain === domain);

    const completedModules = domainModules.filter(m =>
      records.some(r =>
        r.module_id === m.module_id &&
        (r.score === undefined || r.score >= 70)
      )
    );

    if (completedModules.length === 0) return 'novice';

    const highestLevel = completedModules.reduce((highest, m) => {
      const levelOrder: SkillLevel[] = ['novice', 'intermediate', 'advanced', 'expert'];
      if (levelOrder.indexOf(m.difficulty) > levelOrder.indexOf(highest)) {
        return m.difficulty;
      }
      return highest;
    }, 'novice' as SkillLevel);

    return highestLevel;
  }

  /**
   * 获取所有训练模块
   */
  getAllModules(): TrainingModule[] {
    return Array.from(this.modules.values());
  }

  /**
   * 获取所有案例
   */
  getAllCases(): CaseStudy[] {
    return Array.from(this.cases.values());
  }

  /**
   * 获取所有提示模板
   */
  getAllPromptTemplates(): AIPromptTemplate[] {
    return Array.from(this.prompts.values());
  }
}

/**
 * 训练记录
 */
interface TrainingRecord {
  record_id: string;
  coach_id: string;
  module_id: string;
  unit_id: string;
  completed_at: string;
  score?: number;
}

// 导出单例
export const coachTrainingService = new CoachTrainingService();
