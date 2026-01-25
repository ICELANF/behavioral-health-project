/**
 * Intervention Playbook - 干预策略剧本库
 * 基于表型匹配推荐干预杠杆与实施路径
 */

import { v4 as uuidv4 } from 'uuid';
import { RiskLevel } from './PhenotypeMapping';
import { BehaviorStage } from '../trajectory/TrajectorySchema';

/**
 * 干预领域
 */
export type InterventionDomain =
  | 'diet'           // 饮食
  | 'exercise'       // 运动
  | 'sleep'          // 睡眠
  | 'emotion'        // 情绪
  | 'medication'     // 用药
  | 'monitoring'     // 监测
  | 'education';     // 教育

/**
 * 干预强度
 */
export type InterventionIntensity = 'light' | 'moderate' | 'intensive';

/**
 * 干预频率
 */
export type InterventionFrequency =
  | 'once'
  | 'daily'
  | 'weekly'
  | 'biweekly'
  | 'monthly'
  | 'as_needed';

/**
 * 干预杠杆
 */
export interface InterventionLever {
  /** 杠杆ID */
  lever_id: string;
  /** 杠杆名称 */
  name: string;
  /** 描述 */
  description: string;
  /** 领域 */
  domain: InterventionDomain;
  /** 强度 */
  intensity: InterventionIntensity;
  /** 预期效果 */
  expected_outcomes: string[];
  /** 所需资源 */
  required_resources?: string[];
  /** 禁忌条件 */
  contraindications?: string[];
}

/**
 * 干预剧本
 */
export interface InterventionPlaybook {
  /** 剧本ID */
  playbook_id: string;
  /** 剧本名称 */
  name: string;
  /** 目标表型ID列表 */
  target_phenotypes: string[];
  /** 适用阶段 */
  applicable_stages: BehaviorStage[];
  /** 干预杠杆序列 */
  levers: {
    lever: InterventionLever;
    sequence: number;
    duration_days: number;
    frequency: InterventionFrequency;
    success_criteria?: string[];
    fallback_lever_id?: string;
  }[];
  /** 预期周期(天) */
  expected_duration_days: number;
  /** 成功指标 */
  success_metrics: {
    metric: string;
    target_value: number;
    comparison: 'gt' | 'lt' | 'eq' | 'gte' | 'lte';
  }[];
  /** 风险等级要求 */
  min_risk_level?: RiskLevel;
  /** 版本 */
  version: string;
  /** 创建时间 */
  created_at: string;
}

/**
 * 干预计划
 */
export interface InterventionPlan {
  /** 计划ID */
  plan_id: string;
  /** 用户ID */
  user_id: string;
  /** 来源剧本ID */
  playbook_id: string;
  /** 当前阶段 */
  current_phase: number;
  /** 开始日期 */
  start_date: string;
  /** 预计结束日期 */
  expected_end_date: string;
  /** 实际结束日期 */
  actual_end_date?: string;
  /** 每日任务列表 */
  daily_tasks: DailyTask[];
  /** 进度 */
  progress: {
    completed_tasks: number;
    total_tasks: number;
    adherence_rate: number;
  };
  /** 状态 */
  status: 'active' | 'paused' | 'completed' | 'abandoned';
}

/**
 * 每日任务
 */
export interface DailyTask {
  task_id: string;
  date: string;
  lever_id: string;
  task_name: string;
  task_description: string;
  scheduled_time?: string;
  completed: boolean;
  completed_at?: string;
  notes?: string;
}

/**
 * 项目协议 - 结构化干预项目定义
 * Program Protocol for structured intervention programs
 */
export interface ProgramProtocol {
  /** 协议ID */
  protocol_id: 'glucose_14d_basic' | 'glucose_14d_advanced' | 'stress_7d' | 'sleep_14d' | string;
  /** 目标人群画像 */
  target_profile: string[];
  /** 项目持续天数 */
  duration_days: number;
  /** 每日计划 */
  daily_plan: {
    /** 第几天 */
    day: number;
    /** 评估触发点 */
    assessment_hooks: string[];
    /** 干预措施 */
    interventions: string[];
    /** 教练对话模板 */
    coach_dialogue_templates: string[];
    /** 预期指标 */
    expected_metrics: string[];
  }[];
  /** 毕业规则 */
  graduation_rules: {
    /** 必须达成的指标 */
    required_metrics?: { metric: string; target: number; comparison: 'gt' | 'lt' | 'eq' | 'gte' | 'lte' }[];
    /** 最低依从率 */
    min_adherence_rate?: number;
    /** 阶段要求 */
    stage_requirement?: BehaviorStage;
  };
}

/**
 * 预定义干预杠杆库
 */
export const PREDEFINED_LEVERS: InterventionLever[] = [
  // 饮食类
  {
    lever_id: 'LEV-DIET-001',
    name: '进餐顺序调整',
    description: '先吃蔬菜和蛋白质，最后吃主食',
    domain: 'diet',
    intensity: 'light',
    expected_outcomes: ['餐后血糖峰值降低', 'GI负荷减少'],
    required_resources: ['饮食记录工具']
  },
  {
    lever_id: 'LEV-DIET-002',
    name: '慢食训练',
    description: '每餐进食时间延长至20分钟以上',
    domain: 'diet',
    intensity: 'light',
    expected_outcomes: ['餐后血糖平稳', '饱腹感增强'],
    required_resources: ['进餐计时器']
  },
  {
    lever_id: 'LEV-DIET-003',
    name: '碳水配额制',
    description: '每餐碳水化合物控制在特定份量内',
    domain: 'diet',
    intensity: 'moderate',
    expected_outcomes: ['血糖波动减少', '体重控制'],
    required_resources: ['食物秤', '碳水计算工具']
  },
  {
    lever_id: 'LEV-DIET-004',
    name: '睡前加餐策略',
    description: '睡前补充少量蛋白质和复合碳水',
    domain: 'diet',
    intensity: 'light',
    expected_outcomes: ['夜间低血糖减少', '睡眠质量改善'],
    contraindications: ['重度肥胖', '胃食管反流']
  },

  // 运动类
  {
    lever_id: 'LEV-EXE-001',
    name: '餐后散步',
    description: '餐后15-30分钟进行10-15分钟轻度步行',
    domain: 'exercise',
    intensity: 'light',
    expected_outcomes: ['餐后血糖下降', '胰岛素敏感性提升']
  },
  {
    lever_id: 'LEV-EXE-002',
    name: '番茄钟站立',
    description: '每工作25分钟站立活动5分钟',
    domain: 'exercise',
    intensity: 'light',
    expected_outcomes: ['久坐时间减少', '代谢改善'],
    required_resources: ['番茄钟APP']
  },
  {
    lever_id: 'LEV-EXE-003',
    name: '抗阻力训练',
    description: '每周2-3次力量训练，每次20-30分钟',
    domain: 'exercise',
    intensity: 'moderate',
    expected_outcomes: ['肌肉量增加', '基础代谢提升', '胰岛素敏感性改善'],
    contraindications: ['急性损伤', '未控制的高血压']
  },

  // 睡眠类
  {
    lever_id: 'LEV-SLP-001',
    name: '睡眠时间锚定',
    description: '固定就寝和起床时间，误差不超过30分钟',
    domain: 'sleep',
    intensity: 'moderate',
    expected_outcomes: ['昼夜节律稳定', '睡眠质量改善']
  },
  {
    lever_id: 'LEV-SLP-002',
    name: '蓝光过滤',
    description: '睡前1小时避免电子屏幕或使用蓝光滤镜',
    domain: 'sleep',
    intensity: 'light',
    expected_outcomes: ['入睡潜伏期缩短', '褪黑素分泌正常化'],
    required_resources: ['蓝光滤镜眼镜或软件']
  },
  {
    lever_id: 'LEV-SLP-003',
    name: '咖啡因断点',
    description: '下午2点后不摄入咖啡因',
    domain: 'sleep',
    intensity: 'light',
    expected_outcomes: ['睡眠质量改善', '深睡比例增加']
  },

  // 情绪类
  {
    lever_id: 'LEV-EMO-001',
    name: '呼吸练习',
    description: '4-7-8呼吸法，每日2-3次',
    domain: 'emotion',
    intensity: 'light',
    expected_outcomes: ['HRV提升', '压力降低', '血糖稳定']
  },
  {
    lever_id: 'LEV-EMO-002',
    name: '正念冥想',
    description: '每日10-20分钟正念练习',
    domain: 'emotion',
    intensity: 'moderate',
    expected_outcomes: ['压力管理', '情绪调节', '应激反应改善'],
    required_resources: ['冥想APP']
  },
  {
    lever_id: 'LEV-EMO-003',
    name: '情绪觉察日记',
    description: '每日记录情绪状态与血糖关联',
    domain: 'emotion',
    intensity: 'light',
    expected_outcomes: ['情绪模式识别', '触发因素认知'],
    required_resources: ['情绪日记模板']
  },

  // 监测类
  {
    lever_id: 'LEV-MON-001',
    name: 'CGM实时反馈',
    description: '利用CGM数据进行即时行为调整',
    domain: 'monitoring',
    intensity: 'moderate',
    expected_outcomes: ['血糖波动减少', '自我管理能力提升'],
    required_resources: ['CGM设备']
  },
  {
    lever_id: 'LEV-MON-002',
    name: '血压自测规律',
    description: '每日定时测量血压并记录',
    domain: 'monitoring',
    intensity: 'light',
    expected_outcomes: ['血压趋势掌握', '用药调整依据'],
    required_resources: ['家用血压计']
  }
];

/**
 * 预定义干预剧本
 */
export const PREDEFINED_PLAYBOOKS: InterventionPlaybook[] = [
  {
    playbook_id: 'PLB-001',
    name: '餐后高血糖管理剧本',
    target_phenotypes: ['PHE-001'],
    applicable_stages: ['preparation', 'action'],
    levers: [
      {
        lever: PREDEFINED_LEVERS.find(l => l.lever_id === 'LEV-DIET-001')!,
        sequence: 1,
        duration_days: 7,
        frequency: 'daily',
        success_criteria: ['餐后血糖峰值<11']
      },
      {
        lever: PREDEFINED_LEVERS.find(l => l.lever_id === 'LEV-EXE-001')!,
        sequence: 2,
        duration_days: 14,
        frequency: 'daily',
        success_criteria: ['餐后血糖峰值<10']
      },
      {
        lever: PREDEFINED_LEVERS.find(l => l.lever_id === 'LEV-DIET-002')!,
        sequence: 3,
        duration_days: 14,
        frequency: 'daily',
        success_criteria: ['餐后血糖峰值<9']
      }
    ],
    expected_duration_days: 35,
    success_metrics: [
      { metric: 'postprandial_peak', target_value: 10, comparison: 'lt' }
    ],
    version: '1.0',
    created_at: new Date().toISOString()
  },
  {
    playbook_id: 'PLB-002',
    name: '夜间低血糖预防剧本',
    target_phenotypes: ['PHE-004'],
    applicable_stages: ['contemplation', 'preparation', 'action'],
    levers: [
      {
        lever: PREDEFINED_LEVERS.find(l => l.lever_id === 'LEV-DIET-004')!,
        sequence: 1,
        duration_days: 7,
        frequency: 'daily',
        success_criteria: ['夜间低血糖次数=0']
      },
      {
        lever: PREDEFINED_LEVERS.find(l => l.lever_id === 'LEV-MON-001')!,
        sequence: 1,
        duration_days: 14,
        frequency: 'daily'
      }
    ],
    expected_duration_days: 14,
    success_metrics: [
      { metric: 'night_hypo_count', target_value: 0, comparison: 'eq' }
    ],
    min_risk_level: 'high',
    version: '1.0',
    created_at: new Date().toISOString()
  },
  {
    playbook_id: 'PLB-003',
    name: '压力应激管理剧本',
    target_phenotypes: ['PHE-005'],
    applicable_stages: ['contemplation', 'preparation', 'action'],
    levers: [
      {
        lever: PREDEFINED_LEVERS.find(l => l.lever_id === 'LEV-EMO-001')!,
        sequence: 1,
        duration_days: 7,
        frequency: 'daily',
        success_criteria: ['能够完成每日呼吸练习']
      },
      {
        lever: PREDEFINED_LEVERS.find(l => l.lever_id === 'LEV-EMO-002')!,
        sequence: 2,
        duration_days: 21,
        frequency: 'daily',
        success_criteria: ['RMSSD提升10%']
      },
      {
        lever: PREDEFINED_LEVERS.find(l => l.lever_id === 'LEV-EMO-003')!,
        sequence: 1,
        duration_days: 21,
        frequency: 'daily'
      }
    ],
    expected_duration_days: 28,
    success_metrics: [
      { metric: 'rmssd_mean', target_value: 25, comparison: 'gte' }
    ],
    version: '1.0',
    created_at: new Date().toISOString()
  },
  {
    playbook_id: 'PLB-004',
    name: '久坐代谢改善剧本',
    target_phenotypes: ['PHE-006'],
    applicable_stages: ['preparation', 'action'],
    levers: [
      {
        lever: PREDEFINED_LEVERS.find(l => l.lever_id === 'LEV-EXE-002')!,
        sequence: 1,
        duration_days: 14,
        frequency: 'daily',
        success_criteria: ['久坐时间<6小时']
      },
      {
        lever: PREDEFINED_LEVERS.find(l => l.lever_id === 'LEV-EXE-001')!,
        sequence: 2,
        duration_days: 14,
        frequency: 'daily',
        success_criteria: ['日均步数>6000']
      },
      {
        lever: PREDEFINED_LEVERS.find(l => l.lever_id === 'LEV-EXE-003')!,
        sequence: 3,
        duration_days: 28,
        frequency: 'biweekly',
        success_criteria: ['日均步数>8000']
      }
    ],
    expected_duration_days: 56,
    success_metrics: [
      { metric: 'daily_steps_mean', target_value: 8000, comparison: 'gte' }
    ],
    version: '1.0',
    created_at: new Date().toISOString()
  },
  {
    playbook_id: 'PLB-005',
    name: '睡眠-代谢联合干预剧本',
    target_phenotypes: ['PHE-007'],
    applicable_stages: ['preparation', 'action'],
    levers: [
      {
        lever: PREDEFINED_LEVERS.find(l => l.lever_id === 'LEV-SLP-001')!,
        sequence: 1,
        duration_days: 14,
        frequency: 'daily',
        success_criteria: ['入睡时间固定']
      },
      {
        lever: PREDEFINED_LEVERS.find(l => l.lever_id === 'LEV-SLP-002')!,
        sequence: 1,
        duration_days: 14,
        frequency: 'daily'
      },
      {
        lever: PREDEFINED_LEVERS.find(l => l.lever_id === 'LEV-SLP-003')!,
        sequence: 1,
        duration_days: 14,
        frequency: 'daily'
      },
      {
        lever: PREDEFINED_LEVERS.find(l => l.lever_id === 'LEV-MON-001')!,
        sequence: 2,
        duration_days: 14,
        frequency: 'daily'
      }
    ],
    expected_duration_days: 28,
    success_metrics: [
      { metric: 'sleep_duration_mean', target_value: 7, comparison: 'gte' },
      { metric: 'deep_sleep_ratio_mean', target_value: 20, comparison: 'gte' }
    ],
    version: '1.0',
    created_at: new Date().toISOString()
  }
];

/**
 * 干预剧本服务
 */
export class InterventionPlaybookService {
  private playbooks: Map<string, InterventionPlaybook> = new Map();
  private levers: Map<string, InterventionLever> = new Map();
  private plans: Map<string, InterventionPlan> = new Map();

  constructor() {
    // 加载预定义剧本
    PREDEFINED_PLAYBOOKS.forEach(p => {
      this.playbooks.set(p.playbook_id, p);
    });
    // 加载预定义杠杆
    PREDEFINED_LEVERS.forEach(l => {
      this.levers.set(l.lever_id, l);
    });
  }

  /**
   * 根据表型匹配剧本
   */
  matchPlaybooks(phenotypeIds: string[], stage: BehaviorStage): InterventionPlaybook[] {
    const matched: InterventionPlaybook[] = [];

    for (const playbook of this.playbooks.values()) {
      // 检查表型匹配
      const phenotypeMatch = phenotypeIds.some(id =>
        playbook.target_phenotypes.includes(id)
      );
      // 检查阶段匹配
      const stageMatch = playbook.applicable_stages.includes(stage);

      if (phenotypeMatch && stageMatch) {
        matched.push(playbook);
      }
    }

    return matched;
  }

  /**
   * 创建干预计划
   */
  createPlan(
    userId: string,
    playbookId: string
  ): InterventionPlan | null {
    const playbook = this.playbooks.get(playbookId);
    if (!playbook) return null;

    const startDate = new Date();
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + playbook.expected_duration_days);

    // 生成每日任务
    const dailyTasks: DailyTask[] = [];
    let currentDate = new Date(startDate);

    for (const leverConfig of playbook.levers) {
      const leverEndDate = new Date(currentDate);
      leverEndDate.setDate(leverEndDate.getDate() + leverConfig.duration_days);

      while (currentDate < leverEndDate) {
        if (this.shouldScheduleTask(leverConfig.frequency, currentDate, startDate)) {
          dailyTasks.push({
            task_id: uuidv4(),
            date: currentDate.toISOString().split('T')[0],
            lever_id: leverConfig.lever.lever_id,
            task_name: leverConfig.lever.name,
            task_description: leverConfig.lever.description,
            completed: false
          });
        }
        currentDate.setDate(currentDate.getDate() + 1);
      }
    }

    const plan: InterventionPlan = {
      plan_id: uuidv4(),
      user_id: userId,
      playbook_id: playbookId,
      current_phase: 1,
      start_date: startDate.toISOString(),
      expected_end_date: endDate.toISOString(),
      daily_tasks: dailyTasks,
      progress: {
        completed_tasks: 0,
        total_tasks: dailyTasks.length,
        adherence_rate: 0
      },
      status: 'active'
    };

    this.plans.set(plan.plan_id, plan);
    return plan;
  }

  /**
   * 判断是否应该安排任务
   */
  private shouldScheduleTask(
    frequency: InterventionFrequency,
    date: Date,
    startDate: Date
  ): boolean {
    const daysDiff = Math.floor(
      (date.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)
    );

    switch (frequency) {
      case 'once':
        return daysDiff === 0;
      case 'daily':
        return true;
      case 'weekly':
        return daysDiff % 7 === 0;
      case 'biweekly':
        return daysDiff % 14 === 0;
      case 'monthly':
        return daysDiff % 30 === 0;
      default:
        return false;
    }
  }

  /**
   * 完成任务
   */
  completeTask(planId: string, taskId: string, notes?: string): boolean {
    const plan = this.plans.get(planId);
    if (!plan) return false;

    const task = plan.daily_tasks.find(t => t.task_id === taskId);
    if (!task) return false;

    task.completed = true;
    task.completed_at = new Date().toISOString();
    task.notes = notes;

    // 更新进度
    plan.progress.completed_tasks = plan.daily_tasks.filter(t => t.completed).length;
    plan.progress.adherence_rate =
      (plan.progress.completed_tasks / plan.progress.total_tasks) * 100;

    return true;
  }

  /**
   * 获取今日任务
   */
  getTodayTasks(planId: string): DailyTask[] {
    const plan = this.plans.get(planId);
    if (!plan) return [];

    const today = new Date().toISOString().split('T')[0];
    return plan.daily_tasks.filter(t => t.date === today);
  }

  /**
   * 获取用户所有计划
   */
  getUserPlans(userId: string): InterventionPlan[] {
    return Array.from(this.plans.values()).filter(p => p.user_id === userId);
  }

  /**
   * 获取所有剧本
   */
  getAllPlaybooks(): InterventionPlaybook[] {
    return Array.from(this.playbooks.values());
  }

  /**
   * 获取所有杠杆
   */
  getAllLevers(): InterventionLever[] {
    return Array.from(this.levers.values());
  }
}

// 导出单例
export const interventionPlaybookService = new InterventionPlaybookService();
