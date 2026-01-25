/**
 * Behavior Change Engine - 行为改变引擎
 * 基于TTM模型驱动阶段迁移与行为锁定
 */

import { v4 as uuidv4 } from 'uuid';
import { BehaviorStage, TrendDirection } from '../trajectory/TrajectorySchema';

/**
 * 阶段特征描述
 */
export interface StageProfile {
  /** 阶段 */
  stage: BehaviorStage;
  /** 中文名称 */
  name_zh: string;
  /** 英文名称 */
  name_en: string;
  /** 描述 */
  description: string;
  /** 心理准备度 */
  readiness_level: number; // 1-5
  /** 典型特征 */
  characteristics: string[];
  /** 推荐策略 */
  recommended_strategies: string[];
  /** 退行风险因素 */
  regression_risks: string[];
  /** 进阶条件 */
  advancement_criteria: string[];
}

/**
 * 行为锁定记录
 */
export interface BehaviorLock {
  /** 锁定ID */
  lock_id: string;
  /** 用户ID */
  user_id: string;
  /** 行为名称 */
  behavior_name: string;
  /** 行为类别 */
  category: 'diet' | 'exercise' | 'sleep' | 'emotion' | 'monitoring';
  /** 锁定日期 */
  lock_date: string;
  /** 连续天数 */
  consecutive_days: number;
  /** 锁定强度 */
  lock_strength: 'forming' | 'stable' | 'automatic';
  /** 触发条件 */
  trigger_cue: string;
  /** 执行时机 */
  execution_time?: string;
  /** 奖励机制 */
  reward?: string;
  /** 最后执行 */
  last_executed?: string;
  /** 中断次数 */
  break_count: number;
}

/**
 * 阶段迁移评估
 */
export interface StageAssessment {
  /** 当前阶段 */
  current_stage: BehaviorStage;
  /** 阶段得分 */
  stage_score: number;
  /** 各维度得分 */
  dimension_scores: {
    awareness: number;      // 意识觉醒
    motivation: number;     // 动机强度
    self_efficacy: number;  // 自我效能
    action_taking: number;  // 行动执行
    maintenance: number;    // 维持能力
  };
  /** 进阶可能性 */
  advancement_probability: number;
  /** 退行风险 */
  regression_risk: number;
  /** 推荐行动 */
  recommended_actions: string[];
  /** 评估时间 */
  assessed_at: string;
}

/**
 * 习惯循环
 */
export interface HabitLoop {
  /** 循环ID */
  loop_id: string;
  /** 提示(Cue) */
  cue: {
    type: 'time' | 'location' | 'emotion' | 'action' | 'person';
    description: string;
  };
  /** 惯例(Routine) */
  routine: {
    behavior: string;
    duration_minutes?: number;
    steps?: string[];
  };
  /** 奖励(Reward) */
  reward: {
    type: 'intrinsic' | 'extrinsic';
    description: string;
    delay_minutes?: number;
  };
  /** 渴望(Craving) - 驱动力 */
  craving?: string;
}

/**
 * 阶段特征库
 */
export const STAGE_PROFILES: StageProfile[] = [
  {
    stage: 'precontemplation',
    name_zh: '前意向期',
    name_en: 'Precontemplation',
    description: '尚未意识到问题或无改变意愿',
    readiness_level: 1,
    characteristics: [
      '否认存在问题',
      '认为改变无必要',
      '对信息抵触',
      '归因于外部因素'
    ],
    recommended_strategies: [
      '意识唤醒',
      '提供客观数据反馈',
      '建立信任关系',
      '避免说教'
    ],
    regression_risks: [],
    advancement_criteria: [
      '开始承认问题存在',
      '表达对健康的担忧',
      '愿意了解更多信息'
    ]
  },
  {
    stage: 'contemplation',
    name_zh: '意向期',
    name_en: 'Contemplation',
    description: '意识到问题，考虑改变但存在矛盾',
    readiness_level: 2,
    characteristics: [
      '承认问题存在',
      '权衡利弊',
      '存在矛盾心理',
      '可能拖延行动'
    ],
    recommended_strategies: [
      '动机强化',
      '探索改变的好处',
      '识别障碍并规划应对',
      '提升自我效能'
    ],
    regression_risks: [
      '负面反馈过多',
      '缺乏支持',
      '目标过高'
    ],
    advancement_criteria: [
      '表达明确的改变意愿',
      '开始制定计划',
      '寻求支持和资源'
    ]
  },
  {
    stage: 'preparation',
    name_zh: '准备期',
    name_en: 'Preparation',
    description: '决心改变，准备采取行动',
    readiness_level: 3,
    characteristics: [
      '有明确改变意向',
      '开始小步尝试',
      '收集信息和资源',
      '设定具体目标'
    ],
    recommended_strategies: [
      '具体行动规划',
      '微习惯启动',
      '环境设计',
      '社会支持动员'
    ],
    regression_risks: [
      '计划过于复杂',
      '缺乏具体步骤',
      '外部干扰'
    ],
    advancement_criteria: [
      '开始规律执行行为',
      '能够应对简单障碍',
      '初见积极变化'
    ]
  },
  {
    stage: 'action',
    name_zh: '行动期',
    name_en: 'Action',
    description: '积极执行新行为，但尚未稳定',
    readiness_level: 4,
    characteristics: [
      '积极改变行为',
      '投入时间和精力',
      '面临诸多挑战',
      '需要持续努力'
    ],
    recommended_strategies: [
      '正向强化',
      '障碍预防',
      '进展追踪',
      '灵活调整策略'
    ],
    regression_risks: [
      '意外事件',
      '压力增加',
      '进展停滞',
      '奖励减少'
    ],
    advancement_criteria: [
      '行为持续6个月以上',
      '能自主应对障碍',
      '内化为身份认同'
    ]
  },
  {
    stage: 'maintenance',
    name_zh: '维持期',
    name_en: 'Maintenance',
    description: '新行为已稳定，成为生活方式',
    readiness_level: 5,
    characteristics: [
      '行为已自动化',
      '自我效能高',
      '能够自我调节',
      '身份认同转变'
    ],
    recommended_strategies: [
      '防止复发',
      '持续优化',
      '扩展健康行为',
      '成为榜样支持他人'
    ],
    regression_risks: [
      '重大生活变故',
      '过度自信',
      '环境剧变'
    ],
    advancement_criteria: [
      '持续维持新行为',
      '成功应对高风险情境',
      '帮助他人改变'
    ]
  }
];

/**
 * 行为改变引擎服务
 */
export class BehaviorChangeEngineService {
  private stageProfiles: Map<BehaviorStage, StageProfile> = new Map();
  private behaviorLocks: Map<string, BehaviorLock[]> = new Map();
  private habitLoops: Map<string, HabitLoop[]> = new Map();

  constructor() {
    // 加载阶段特征
    STAGE_PROFILES.forEach(p => {
      this.stageProfiles.set(p.stage, p);
    });
  }

  /**
   * 评估用户当前阶段
   */
  assessStage(
    userId: string,
    indicators: {
      awareness_score: number;
      motivation_score: number;
      self_efficacy_score: number;
      action_frequency: number;
      days_maintained: number;
    }
  ): StageAssessment {
    const { awareness_score, motivation_score, self_efficacy_score, action_frequency, days_maintained } = indicators;

    // 计算各维度得分 (0-100)
    const dimension_scores = {
      awareness: awareness_score,
      motivation: motivation_score,
      self_efficacy: self_efficacy_score,
      action_taking: Math.min(action_frequency * 10, 100),
      maintenance: Math.min(days_maintained / 180 * 100, 100)
    };

    // 计算综合阶段得分
    const stage_score = (
      dimension_scores.awareness * 0.15 +
      dimension_scores.motivation * 0.2 +
      dimension_scores.self_efficacy * 0.2 +
      dimension_scores.action_taking * 0.25 +
      dimension_scores.maintenance * 0.2
    );

    // 确定当前阶段
    let current_stage: BehaviorStage;
    if (stage_score < 20) {
      current_stage = 'precontemplation';
    } else if (stage_score < 40) {
      current_stage = 'contemplation';
    } else if (stage_score < 60) {
      current_stage = 'preparation';
    } else if (stage_score < 80) {
      current_stage = 'action';
    } else {
      current_stage = 'maintenance';
    }

    // 计算进阶可能性和退行风险
    const advancement_probability = this.calculateAdvancementProbability(dimension_scores, current_stage);
    const regression_risk = this.calculateRegressionRisk(dimension_scores, current_stage);

    // 生成推荐行动
    const profile = this.stageProfiles.get(current_stage)!;
    const recommended_actions = this.generateRecommendedActions(profile, dimension_scores);

    return {
      current_stage,
      stage_score,
      dimension_scores,
      advancement_probability,
      regression_risk,
      recommended_actions,
      assessed_at: new Date().toISOString()
    };
  }

  /**
   * 计算进阶可能性
   */
  private calculateAdvancementProbability(
    scores: StageAssessment['dimension_scores'],
    stage: BehaviorStage
  ): number {
    const weights: Record<BehaviorStage, Record<string, number>> = {
      precontemplation: { awareness: 0.5, motivation: 0.3, self_efficacy: 0.2 },
      contemplation: { motivation: 0.4, self_efficacy: 0.35, action_taking: 0.25 },
      preparation: { self_efficacy: 0.3, action_taking: 0.5, maintenance: 0.2 },
      action: { action_taking: 0.3, maintenance: 0.5, self_efficacy: 0.2 },
      maintenance: { maintenance: 0.6, self_efficacy: 0.2, action_taking: 0.2 }
    };

    const stageWeights = weights[stage];
    let probability = 0;
    for (const [dim, weight] of Object.entries(stageWeights)) {
      probability += (scores[dim as keyof typeof scores] / 100) * weight;
    }

    return Math.round(probability * 100);
  }

  /**
   * 计算退行风险
   */
  private calculateRegressionRisk(
    scores: StageAssessment['dimension_scores'],
    stage: BehaviorStage
  ): number {
    if (stage === 'precontemplation') return 0;

    // 关键维度低于阈值时增加风险
    let risk = 0;
    if (scores.motivation < 40) risk += 25;
    if (scores.self_efficacy < 40) risk += 25;
    if (scores.action_taking < 30) risk += 20;
    if (scores.maintenance < 20) risk += 15;

    // 阶段越高，退行风险权重越大
    const stageMultiplier: Record<BehaviorStage, number> = {
      precontemplation: 0,
      contemplation: 0.8,
      preparation: 1.0,
      action: 1.2,
      maintenance: 0.6
    };

    return Math.min(Math.round(risk * stageMultiplier[stage]), 100);
  }

  /**
   * 生成推荐行动
   */
  private generateRecommendedActions(
    profile: StageProfile,
    scores: StageAssessment['dimension_scores']
  ): string[] {
    const actions: string[] = [...profile.recommended_strategies.slice(0, 2)];

    // 根据薄弱维度补充建议
    if (scores.awareness < 50) {
      actions.push('增强问题意识：记录当前健康状况');
    }
    if (scores.motivation < 50) {
      actions.push('强化动机：明确改变带来的好处');
    }
    if (scores.self_efficacy < 50) {
      actions.push('提升信心：从小目标开始积累成功经验');
    }
    if (scores.action_taking < 50) {
      actions.push('促进行动：设定具体可执行的每日任务');
    }

    return actions.slice(0, 5);
  }

  /**
   * 创建行为锁定
   */
  createBehaviorLock(
    userId: string,
    behaviorName: string,
    category: BehaviorLock['category'],
    triggerCue: string,
    executionTime?: string,
    reward?: string
  ): BehaviorLock {
    const lock: BehaviorLock = {
      lock_id: uuidv4(),
      user_id: userId,
      behavior_name: behaviorName,
      category,
      lock_date: new Date().toISOString(),
      consecutive_days: 0,
      lock_strength: 'forming',
      trigger_cue: triggerCue,
      execution_time: executionTime,
      reward,
      break_count: 0
    };

    const userLocks = this.behaviorLocks.get(userId) || [];
    userLocks.push(lock);
    this.behaviorLocks.set(userId, userLocks);

    return lock;
  }

  /**
   * 更新行为锁定状态
   */
  updateLockStatus(lockId: string, executed: boolean): BehaviorLock | null {
    for (const [userId, locks] of this.behaviorLocks.entries()) {
      const lock = locks.find(l => l.lock_id === lockId);
      if (lock) {
        if (executed) {
          lock.consecutive_days += 1;
          lock.last_executed = new Date().toISOString();

          // 更新锁定强度
          if (lock.consecutive_days >= 66) {
            lock.lock_strength = 'automatic';
          } else if (lock.consecutive_days >= 21) {
            lock.lock_strength = 'stable';
          }
        } else {
          lock.break_count += 1;
          // 连续中断会降低锁定强度
          if (lock.lock_strength === 'automatic' && lock.break_count >= 3) {
            lock.lock_strength = 'stable';
          } else if (lock.lock_strength === 'stable' && lock.break_count >= 2) {
            lock.lock_strength = 'forming';
          }
          lock.consecutive_days = 0;
        }
        return lock;
      }
    }
    return null;
  }

  /**
   * 创建习惯循环
   */
  createHabitLoop(
    userId: string,
    cue: HabitLoop['cue'],
    routine: HabitLoop['routine'],
    reward: HabitLoop['reward'],
    craving?: string
  ): HabitLoop {
    const loop: HabitLoop = {
      loop_id: uuidv4(),
      cue,
      routine,
      reward,
      craving
    };

    const userLoops = this.habitLoops.get(userId) || [];
    userLoops.push(loop);
    this.habitLoops.set(userId, userLoops);

    return loop;
  }

  /**
   * 获取用户行为锁定
   */
  getUserBehaviorLocks(userId: string): BehaviorLock[] {
    return this.behaviorLocks.get(userId) || [];
  }

  /**
   * 获取用户习惯循环
   */
  getUserHabitLoops(userId: string): HabitLoop[] {
    return this.habitLoops.get(userId) || [];
  }

  /**
   * 获取阶段特征
   */
  getStageProfile(stage: BehaviorStage): StageProfile | undefined {
    return this.stageProfiles.get(stage);
  }

  /**
   * 获取所有阶段特征
   */
  getAllStageProfiles(): StageProfile[] {
    return STAGE_PROFILES;
  }

  /**
   * 计算习惯强度指数
   */
  calculateHabitStrengthIndex(userId: string): number {
    const locks = this.behaviorLocks.get(userId) || [];
    if (locks.length === 0) return 0;

    const strengthScores: Record<BehaviorLock['lock_strength'], number> = {
      forming: 1,
      stable: 2,
      automatic: 3
    };

    const totalScore = locks.reduce((sum, lock) => {
      return sum + strengthScores[lock.lock_strength] * (1 - lock.break_count * 0.1);
    }, 0);

    return Math.round((totalScore / (locks.length * 3)) * 100);
  }
}

// 导出单例
export const behaviorChangeEngineService = new BehaviorChangeEngineService();
