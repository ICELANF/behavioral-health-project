/**
 * 干预包 API 和匹配逻辑
 * 模拟 GET /api/interventions/match 接口
 */
import type { InterventionPack, TTMStage, RiskLevel, TriggerDomain, CoachLevel } from '@/types'

// 模拟干预包数据（包含完整字段）
const mockInterventionPacks: InterventionPack[] = [
  {
    pack_id: 'IP001',
    name: '高血糖紧急干预包',
    description: '针对血糖严重超标（>13.9mmol/L）的紧急干预方案，需要高级教练介入',
    trigger_tags: ['high_glucose', 'glucose_spike'],
    applicable_stages: ['action', 'maintenance'],
    behavior_stage: 'action',
    risk_levels: ['high'],
    trigger_domain: 'glucose',
    coach_level_min: 'L2',
    tasks: [
      {
        task_id: 't001',
        title: '血糖监测强化',
        description: '增加血糖监测频率至每日4次（早餐前、午餐后2h、晚餐前、睡前）',
        type: 'monitoring',
        category: 'self_monitoring',
        priority: 1,
        duration_minutes: 5,
        behavior_stage: ['action', 'maintenance']
      },
      {
        task_id: 't002',
        title: '饮食记录与分析',
        description: '详细记录每餐食物种类、份量和进餐时间，分析血糖波动原因',
        type: 'action',
        category: 'behavior_experiment',
        priority: 2,
        duration_minutes: 10,
        behavior_stage: ['action']
      },
      {
        task_id: 't003',
        title: '紧急用药确认',
        description: '确认是否按医嘱服药，必要时联系医生调整方案',
        type: 'action',
        category: 'activation',
        priority: 1,
        behavior_stage: ['action', 'maintenance']
      }
    ],
    coach_actions: [
      {
        action_id: 'ca001',
        title: '紧急电话随访',
        description: '24小时内完成电话随访，了解血糖异常原因和用户状态',
        category: 'coaching',
        script: '您好，我是您的健康教练。我注意到您最近的血糖读数偏高，想关心一下您的情况。能告诉我最近的饮食、作息和用药情况吗？',
        tips: ['保持关心但不要引起恐慌', '询问近期饮食和用药情况', '评估是否需要就医'],
        required_level: 'L2',
        behavior_stage: ['action', 'maintenance']
      },
      {
        action_id: 'ca002',
        title: '血糖管理教育',
        description: '讲解高血糖的危害和紧急处理方法',
        category: 'education',
        tips: ['使用通俗易懂的语言', '强调及时干预的重要性'],
        required_level: 'L1',
        behavior_stage: ['action']
      }
    ],
    priority: 1,
    is_active: true,
    created_at: '2024-01-10',
    updated_at: '2024-01-15'
  },
  {
    pack_id: 'IP002',
    name: '血糖波动管理包',
    description: '针对血糖波动较大但未达危险水平的管理方案',
    trigger_tags: ['glucose_fluctuation', 'high_glucose'],
    applicable_stages: ['contemplation', 'preparation', 'action'],
    behavior_stage: 'preparation',
    risk_levels: ['mid'],
    trigger_domain: 'glucose',
    coach_level_min: 'L1',
    tasks: [
      {
        task_id: 't004',
        title: '血糖模式分析',
        description: '分析一周血糖数据，识别波动规律和触发因素',
        type: 'monitoring',
        category: 'self_monitoring',
        priority: 1,
        behavior_stage: ['preparation', 'action']
      },
      {
        task_id: 't005',
        title: '血糖影响因素学习',
        description: '学习影响血糖的主要因素：饮食、运动、情绪、睡眠',
        type: 'education',
        category: 'skill_training',
        priority: 2,
        duration_minutes: 20,
        resources: ['video_glucose_factors', 'article_diet_impact'],
        behavior_stage: ['contemplation', 'preparation']
      },
      {
        task_id: 't006',
        title: '餐后散步实验',
        description: '连续3天尝试餐后15分钟散步，记录血糖变化',
        type: 'action',
        category: 'behavior_experiment',
        priority: 3,
        duration_minutes: 15,
        behavior_stage: ['preparation', 'action']
      }
    ],
    coach_actions: [
      {
        action_id: 'ca003',
        title: '血糖管理指导',
        description: '帮助用户理解血糖波动原因并制定个性化改善计划',
        category: 'guidance',
        tips: ['使用动机访谈技巧', '设定SMART目标', '关注用户的准备程度'],
        required_level: 'L1',
        behavior_stage: ['preparation', 'action']
      },
      {
        action_id: 'ca004',
        title: '目标设定辅导',
        description: '与用户一起设定具体、可衡量的血糖控制目标',
        category: 'coaching',
        script: '根据您目前的情况，我们可以先设定一个小目标。您觉得把餐后血糖控制在10以下，一周内达成3次，这个目标怎么样？',
        tips: ['目标要具体可衡量', '从小目标开始建立信心'],
        required_level: 'L1',
        behavior_stage: ['preparation']
      }
    ],
    priority: 2,
    is_active: true,
    created_at: '2024-01-08',
    updated_at: '2024-01-12'
  },
  {
    pack_id: 'IP003',
    name: '运动启动包',
    description: '帮助久坐或活动量不足的用户开始规律运动',
    trigger_tags: ['low_activity', 'sedentary'],
    applicable_stages: ['contemplation', 'preparation'],
    behavior_stage: 'contemplation',
    risk_levels: ['low', 'mid'],
    trigger_domain: 'exercise',
    coach_level_min: 'L1',
    tasks: [
      {
        task_id: 't007',
        title: '运动能力自评',
        description: '完成简单的体能自评问卷，了解当前运动能力',
        type: 'monitoring',
        category: 'self_monitoring',
        priority: 1,
        duration_minutes: 10,
        behavior_stage: ['contemplation']
      },
      {
        task_id: 't008',
        title: '运动益处探索',
        description: '了解运动对血糖控制、心情、睡眠的好处',
        type: 'education',
        category: 'skill_training',
        priority: 2,
        duration_minutes: 15,
        resources: ['video_exercise_benefits'],
        behavior_stage: ['contemplation', 'preparation']
      },
      {
        task_id: 't009',
        title: '5分钟运动挑战',
        description: '尝试每天5分钟的简单运动（如原地踏步、伸展），持续一周',
        type: 'action',
        category: 'behavior_experiment',
        priority: 3,
        duration_minutes: 5,
        behavior_stage: ['preparation']
      }
    ],
    coach_actions: [
      {
        action_id: 'ca005',
        title: '运动动机探索',
        description: '了解用户对运动的看法、障碍和内在动机',
        category: 'coaching',
        script: '我想了解一下，您平时有运动的习惯吗？是什么原因让您觉得运动比较困难呢？',
        tips: ['探索内在动机而非外在压力', '不要急于给建议，先倾听'],
        required_level: 'L1',
        behavior_stage: ['contemplation']
      },
      {
        action_id: 'ca006',
        title: '运动计划制定',
        description: '根据用户情况制定切实可行的运动启动计划',
        category: 'guidance',
        tips: ['从最小可行动作开始', '考虑用户的时间和环境限制'],
        required_level: 'L1',
        behavior_stage: ['preparation']
      }
    ],
    priority: 3,
    is_active: true,
    created_at: '2024-01-05',
    updated_at: '2024-01-10'
  },
  {
    pack_id: 'IP004',
    name: '饮食控制强化包',
    description: '针对饮食控制不佳、暴饮暴食或高碳水摄入的干预方案',
    trigger_tags: ['overeating', 'high_carb', 'irregular_meals'],
    applicable_stages: ['action', 'maintenance'],
    behavior_stage: 'action',
    risk_levels: ['mid', 'high'],
    trigger_domain: 'diet',
    coach_level_min: 'L1',
    tasks: [
      {
        task_id: 't010',
        title: '7天饮食日记',
        description: '连续7天详细记录所有饮食，包括时间、种类、份量、进餐情绪',
        type: 'monitoring',
        category: 'self_monitoring',
        priority: 1,
        behavior_stage: ['action']
      },
      {
        task_id: 't011',
        title: '糖尿病饮食原则学习',
        description: '学习低GI饮食、食物交换份、餐盘法则等',
        type: 'education',
        category: 'skill_training',
        priority: 2,
        duration_minutes: 30,
        resources: ['course_diabetes_diet', 'tool_food_exchange'],
        behavior_stage: ['action']
      },
      {
        task_id: 't012',
        title: '健康替代实验',
        description: '选择一种常吃的高GI食物，尝试用低GI替代品替换，观察血糖变化',
        type: 'action',
        category: 'behavior_experiment',
        priority: 3,
        behavior_stage: ['action', 'maintenance']
      }
    ],
    coach_actions: [
      {
        action_id: 'ca007',
        title: '饮食习惯分析',
        description: '分析用户饮食日记，找出问题模式和改善机会',
        category: 'guidance',
        tips: ['关注进餐规律而非单纯限制', '识别情绪性进食'],
        required_level: 'L1',
        behavior_stage: ['action']
      },
      {
        action_id: 'ca008',
        title: '个性化饮食计划',
        description: '与用户一起制定符合其口味和生活习惯的饮食计划',
        category: 'coaching',
        script: '看了您的饮食记录，我注意到...... 我们可以从调整...开始，您觉得这样的改变可以接受吗？',
        tips: ['尊重用户饮食偏好', '循序渐进，不要一次改变太多'],
        required_level: 'L1',
        behavior_stage: ['action', 'maintenance']
      }
    ],
    priority: 2,
    is_active: true,
    created_at: '2024-01-03',
    updated_at: '2024-01-08'
  },
  {
    pack_id: 'IP005',
    name: '用药依从性提升包',
    description: '针对漏服药物或用药不规律的干预方案',
    trigger_tags: ['missed_medication', 'irregular_medication'],
    applicable_stages: ['precontemplation', 'contemplation', 'action'],
    behavior_stage: 'contemplation',
    risk_levels: ['mid', 'high'],
    trigger_domain: 'medication',
    coach_level_min: 'L1',
    tasks: [
      {
        task_id: 't013',
        title: '用药提醒设置',
        description: '在手机上设置用药提醒闹钟，与日常活动绑定',
        type: 'action',
        category: 'activation',
        priority: 1,
        duration_minutes: 10,
        behavior_stage: ['action']
      },
      {
        task_id: 't014',
        title: '药物知识学习',
        description: '了解所服药物的作用机制、正确服用方法和注意事项',
        type: 'education',
        category: 'skill_training',
        priority: 2,
        duration_minutes: 15,
        behavior_stage: ['contemplation', 'action']
      },
      {
        task_id: 't015',
        title: '服药障碍记录',
        description: '记录每次漏服或延迟服药的原因，找出规律',
        type: 'monitoring',
        category: 'self_monitoring',
        priority: 2,
        behavior_stage: ['contemplation']
      }
    ],
    coach_actions: [
      {
        action_id: 'ca009',
        title: '用药障碍探索',
        description: '了解用户不按时服药的真实原因（忘记、副作用、认知等）',
        category: 'coaching',
        script: '我注意到您有时会忘记服药，能告诉我是什么情况吗？是单纯忘记了，还是有其他原因呢？',
        tips: ['不要责备用户', '区分能力问题和意愿问题', '关注副作用顾虑'],
        required_level: 'L1',
        behavior_stage: ['precontemplation', 'contemplation']
      },
      {
        action_id: 'ca010',
        title: '用药重要性教育',
        description: '帮助用户理解规律用药的重要性',
        category: 'education',
        tips: ['用数据说话', '关联用户关心的健康目标'],
        required_level: 'L1',
        behavior_stage: ['precontemplation', 'contemplation']
      }
    ],
    priority: 1,
    is_active: true,
    created_at: '2024-01-02',
    updated_at: '2024-01-06'
  },
  {
    pack_id: 'IP006',
    name: '睡眠质量改善包',
    description: '针对睡眠质量差影响血糖控制的干预方案',
    trigger_tags: ['poor_sleep', 'insomnia'],
    applicable_stages: ['contemplation', 'preparation', 'action'],
    behavior_stage: 'preparation',
    risk_levels: ['low', 'mid'],
    trigger_domain: 'sleep',
    coach_level_min: 'L1',
    tasks: [
      {
        task_id: 't016',
        title: '睡眠日记',
        description: '记录入睡时间、起床时间、夜醒次数、睡眠质量评分',
        type: 'monitoring',
        category: 'self_monitoring',
        priority: 1,
        behavior_stage: ['contemplation', 'preparation']
      },
      {
        task_id: 't017',
        title: '睡眠卫生知识',
        description: '学习良好睡眠习惯：固定作息、睡前放松、环境优化',
        type: 'education',
        category: 'skill_training',
        priority: 2,
        duration_minutes: 20,
        behavior_stage: ['preparation']
      },
      {
        task_id: 't018',
        title: '睡前放松练习',
        description: '尝试睡前10分钟的呼吸放松或冥想',
        type: 'action',
        category: 'behavior_experiment',
        priority: 3,
        duration_minutes: 10,
        resources: ['audio_sleep_meditation'],
        behavior_stage: ['action']
      }
    ],
    coach_actions: [
      {
        action_id: 'ca011',
        title: '睡眠问题评估',
        description: '了解用户睡眠问题的类型和可能原因',
        category: 'guidance',
        tips: ['排除需要医疗干预的情况', '关注血糖与睡眠的双向影响'],
        required_level: 'L1',
        behavior_stage: ['contemplation']
      },
      {
        action_id: 'ca012',
        title: '睡眠改善计划',
        description: '制定个性化的睡眠改善计划',
        category: 'coaching',
        script: '根据您的睡眠日记，我们可以先从调整就寝时间开始。您觉得每晚11点上床，这个目标可以做到吗？',
        tips: ['从最容易的改变开始', '一次只改变一个习惯'],
        required_level: 'L1',
        behavior_stage: ['preparation', 'action']
      }
    ],
    priority: 3,
    is_active: true,
    created_at: '2024-01-01',
    updated_at: '2024-01-05'
  },
  {
    pack_id: 'IP007',
    name: '压力管理包',
    description: '针对压力过大影响血糖和健康行为的干预方案',
    trigger_tags: ['high_stress', 'anxiety'],
    applicable_stages: ['contemplation', 'preparation', 'action'],
    behavior_stage: 'contemplation',
    risk_levels: ['mid'],
    trigger_domain: 'stress',
    coach_level_min: 'L2',
    tasks: [
      {
        task_id: 't019',
        title: '压力源识别',
        description: '列出主要压力来源，评估压力程度',
        type: 'monitoring',
        category: 'self_monitoring',
        priority: 1,
        behavior_stage: ['contemplation']
      },
      {
        task_id: 't020',
        title: '压力应对技巧学习',
        description: '学习呼吸放松、正念、时间管理等压力应对技巧',
        type: 'education',
        category: 'skill_training',
        priority: 2,
        duration_minutes: 25,
        resources: ['video_stress_management', 'audio_breathing_exercise'],
        behavior_stage: ['preparation']
      },
      {
        task_id: 't021',
        title: '每日放松练习',
        description: '每天进行5分钟的呼吸放松练习',
        type: 'action',
        category: 'behavior_experiment',
        priority: 3,
        duration_minutes: 5,
        behavior_stage: ['action']
      }
    ],
    coach_actions: [
      {
        action_id: 'ca013',
        title: '压力评估与支持',
        description: '评估用户压力水平，提供情感支持',
        category: 'support',
        tips: ['先倾听，再建议', '评估是否需要转介心理咨询', '关注压力与血糖的关系'],
        required_level: 'L2',
        behavior_stage: ['contemplation']
      },
      {
        action_id: 'ca014',
        title: '压力管理指导',
        description: '帮助用户识别压力触发因素并制定应对策略',
        category: 'guidance',
        script: '您提到工作压力比较大，能具体说说是什么情况让您感到压力呢？我们一起想想有什么方法可以帮助您。',
        tips: ['关注可改变的因素', '教授具体可操作的技巧'],
        required_level: 'L2',
        behavior_stage: ['preparation', 'action']
      }
    ],
    priority: 2,
    is_active: true,
    created_at: '2024-01-04',
    updated_at: '2024-01-09'
  }
]

// 触发标签定义
export const TRIGGER_TAGS = [
  { tag: 'high_glucose', label: '高血糖', domain: 'glucose' as TriggerDomain },
  { tag: 'low_glucose', label: '低血糖', domain: 'glucose' as TriggerDomain },
  { tag: 'glucose_spike', label: '血糖骤升', domain: 'glucose' as TriggerDomain },
  { tag: 'glucose_fluctuation', label: '血糖波动', domain: 'glucose' as TriggerDomain },
  { tag: 'overeating', label: '暴饮暴食', domain: 'diet' as TriggerDomain },
  { tag: 'high_carb', label: '高碳水摄入', domain: 'diet' as TriggerDomain },
  { tag: 'irregular_meals', label: '饮食不规律', domain: 'diet' as TriggerDomain },
  { tag: 'low_activity', label: '活动量不足', domain: 'exercise' as TriggerDomain },
  { tag: 'sedentary', label: '久坐', domain: 'exercise' as TriggerDomain },
  { tag: 'missed_medication', label: '漏服药物', domain: 'medication' as TriggerDomain },
  { tag: 'irregular_medication', label: '用药不规律', domain: 'medication' as TriggerDomain },
  { tag: 'poor_sleep', label: '睡眠质量差', domain: 'sleep' as TriggerDomain },
  { tag: 'insomnia', label: '失眠', domain: 'sleep' as TriggerDomain },
  { tag: 'high_stress', label: '压力过大', domain: 'stress' as TriggerDomain },
  { tag: 'anxiety', label: '焦虑', domain: 'stress' as TriggerDomain }
]

// 任务类型标签映射
export const TASK_CATEGORY_MAP = {
  behavior_experiment: { label: '行为实验', color: '#52c41a' },
  activation: { label: '行为激活', color: '#1890ff' },
  self_monitoring: { label: '自我监测', color: '#faad14' },
  skill_training: { label: '技能训练', color: '#722ed1' }
}

// 教练动作类型映射
export const ACTION_CATEGORY_MAP = {
  education: { label: '健康教育', color: '#1890ff' },
  guidance: { label: '行为指导', color: '#52c41a' },
  coaching: { label: '教练辅导', color: '#722ed1' },
  support: { label: '情感支持', color: '#eb2f96' }
}

/**
 * 获取所有干预包
 */
export function getAllInterventionPacks(): InterventionPack[] {
  return mockInterventionPacks
}

// 教练等级顺序（用于比较）
const COACH_LEVEL_ORDER = ['L0', 'L1', 'L2', 'L3', 'L4']

/**
 * 比较教练等级是否满足要求
 * @param userLevel 用户等级
 * @param requiredLevel 要求的最低等级
 * @returns 用户等级是否 >= 要求等级
 */
export function isCoachLevelSufficient(userLevel: CoachLevel, requiredLevel: CoachLevel): boolean {
  const userIndex = COACH_LEVEL_ORDER.indexOf(userLevel)
  const requiredIndex = COACH_LEVEL_ORDER.indexOf(requiredLevel)
  return userIndex >= requiredIndex
}

/**
 * 匹配结果接口
 */
export interface MatchResult {
  pack: InterventionPack
  matchedActions: typeof mockInterventionPacks[0]['coach_actions']
  canExecute: boolean
  reason?: string
}

/**
 * 模拟 GET /api/interventions/match 接口
 * 根据触发标签、行为阶段和教练等级匹配干预包
 * @param trigger_tag 触发标签（必填）
 * @param behavior_stage 行为阶段（必填）
 * @param coach_level 当前教练等级（可选，用于筛选可执行的干预包）
 * @returns 匹配结果列表，包含干预包和推荐的教练动作
 */
export function matchInterventionPack(
  trigger_tag: string,
  behavior_stage: TTMStage,
  coach_level?: CoachLevel
): MatchResult[] {
  const results: MatchResult[] = []

  mockInterventionPacks.forEach(pack => {
    // 必须匹配触发标签
    if (!pack.trigger_tags.includes(trigger_tag)) {
      return
    }
    // 必须匹配行为阶段
    if (!pack.applicable_stages.includes(behavior_stage)) {
      return
    }
    // 必须是激活状态
    if (!pack.is_active) {
      return
    }

    // 筛选该阶段适用的教练动作
    const matchedActions = pack.coach_actions.filter(action => {
      // 如果动作有指定行为阶段，检查是否匹配
      if (action.behavior_stage && action.behavior_stage.length > 0) {
        return action.behavior_stage.includes(behavior_stage)
      }
      return true
    })

    // 检查教练等级是否满足要求
    let canExecute = true
    let reason: string | undefined

    if (coach_level) {
      if (!isCoachLevelSufficient(coach_level, pack.coach_level_min)) {
        canExecute = false
        reason = '需要 ' + pack.coach_level_min + ' 及以上等级教练'
      }
    }

    results.push({
      pack,
      matchedActions,
      canExecute,
      reason
    })
  })

  // 按优先级排序，可执行的排在前面
  return results.sort((a, b) => {
    // 先按是否可执行排序
    if (a.canExecute !== b.canExecute) {
      return a.canExecute ? -1 : 1
    }
    // 再按优先级排序
    return a.pack.priority - b.pack.priority
  })
}

/**
 * 根据触发标签和行为阶段匹配干预包（支持可选参数）
 * @param triggerTag 触发标签
 * @param behaviorStage 行为阶段（可选）
 * @param riskLevel 风险等级（可选）
 * @returns 匹配的干预包列表，按优先级排序
 */
export function matchInterventionPacks(
  triggerTag: string,
  behaviorStage?: TTMStage,
  riskLevel?: RiskLevel
): InterventionPack[] {
  let matched = mockInterventionPacks.filter(pack => {
    // 必须匹配触发标签
    if (!pack.trigger_tags.includes(triggerTag)) {
      return false
    }
    // 必须是激活状态
    if (!pack.is_active) {
      return false
    }
    return true
  })

  // 如果指定了行为阶段，进一步筛选
  if (behaviorStage) {
    matched = matched.filter(pack =>
      pack.applicable_stages.includes(behaviorStage)
    )
  }

  // 如果指定了风险等级，进一步筛选
  if (riskLevel) {
    matched = matched.filter(pack =>
      pack.risk_levels.includes(riskLevel)
    )
  }

  // 按优先级排序（数字越小优先级越高）
  return matched.sort((a, b) => a.priority - b.priority)
}

/**
 * 根据 ID 获取干预包
 */
export function getInterventionPackById(packId: string): InterventionPack | undefined {
  return mockInterventionPacks.find(pack => pack.pack_id === packId)
}

/**
 * 根据触发域获取干预包
 */
export function getInterventionPacksByDomain(domain: TriggerDomain): InterventionPack[] {
  return mockInterventionPacks.filter(pack => pack.trigger_domain === domain)
}

/**
 * 根据教练等级筛选可执行的干预包
 */
export function getInterventionPacksByCoachLevel(level: CoachLevel): InterventionPack[] {
  const levelOrder = ['L0', 'L1', 'L2', 'L3', 'L4']
  const levelIndex = levelOrder.indexOf(level)

  return mockInterventionPacks.filter(pack => {
    const packLevelIndex = levelOrder.indexOf(pack.coach_level_min)
    return packLevelIndex <= levelIndex && pack.is_active
  })
}
