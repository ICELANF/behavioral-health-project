/**
 * 行为健康平台常量配置
 */

// 风险等级配置
export const RISK_LEVELS = {
  high: { label: '高风险', color: '#ff4d4f', bgColor: '#fff2f0' },
  mid: { label: '中风险', color: '#faad14', bgColor: '#fffbe6' },
  low: { label: '低风险', color: '#52c41a', bgColor: '#f6ffed' },
  normal: { label: '正常', color: '#1890ff', bgColor: '#e6f7ff' }
} as const

// 教练等级配置
export const COACH_LEVELS = {
  L0: { label: '见习教练', color: '#8c8c8c', description: '新入职，学习阶段' },
  L1: { label: '初级教练', color: '#52c41a', description: '独立处理低风险案例' },
  L2: { label: '中级教练', color: '#1890ff', description: '独立处理中风险案例' },
  L3: { label: '高级教练', color: '#722ed1', description: '处理高风险案例，可带教' },
  L4: { label: '专家教练', color: '#eb2f96', description: '督导级别，培训讲师' }
} as const

// TTM 行为阶段
export const TTM_STAGES = {
  precontemplation: { label: '前意向期', color: '#ff7a45', order: 1 },
  contemplation: { label: '意向期', color: '#ffa940', order: 2 },
  preparation: { label: '准备期', color: '#fadb14', order: 3 },
  action: { label: '行动期', color: '#52c41a', order: 4 },
  maintenance: { label: '维持期', color: '#13c2c2', order: 5 },
  termination: { label: '终止期', color: '#1890ff', order: 6 }
} as const

// 触发域配置
export const TRIGGER_DOMAINS = {
  glucose: { label: '血糖管理', color: '#ff4d4f', icon: 'experiment' },
  diet: { label: '饮食控制', color: '#52c41a', icon: 'coffee' },
  exercise: { label: '运动锻炼', color: '#1890ff', icon: 'thunderbolt' },
  medication: { label: '用药依从', color: '#722ed1', icon: 'medicine-box' },
  sleep: { label: '睡眠质量', color: '#13c2c2', icon: 'rest' },
  stress: { label: '压力管理', color: '#eb2f96', icon: 'heart' },
  weight: { label: '体重控制', color: '#faad14', icon: 'dashboard' }
} as const

// 干预类型
export const INTERVENTION_TYPES = {
  education: { label: '健康教育', color: '#1890ff' },
  motivation: { label: '动机激励', color: '#52c41a' },
  skill_building: { label: '技能培训', color: '#722ed1' },
  problem_solving: { label: '问题解决', color: '#faad14' },
  social_support: { label: '社会支持', color: '#eb2f96' },
  relapse_prevention: { label: '复发预防', color: '#ff4d4f' }
} as const

// 专业方向
export const SPECIALTIES = [
  { value: 'diabetes', label: '糖尿病管理' },
  { value: 'hypertension', label: '高血压管理' },
  { value: 'obesity', label: '体重管理' },
  { value: 'smoking', label: '戒烟指导' },
  { value: 'mental_health', label: '心理健康' },
  { value: 'chronic_disease', label: '慢病综合' }
]

// 用户状态
export const USER_STATUS = {
  active: { label: '正常', color: '#52c41a' },
  inactive: { label: '未激活', color: '#8c8c8c' },
  suspended: { label: '已停用', color: '#ff4d4f' }
} as const

// 考试状态
export const EXAM_STATUS = {
  draft: { label: '草稿', color: '#8c8c8c' },
  published: { label: '已发布', color: '#52c41a' },
  ongoing: { label: '进行中', color: '#1890ff' },
  ended: { label: '已结束', color: '#ff4d4f' }
} as const

// 直播状态
export const LIVE_STATUS = {
  scheduled: { label: '未开始', color: '#8c8c8c' },
  live: { label: '直播中', color: '#52c41a' },
  ended: { label: '已结束', color: '#1890ff' },
  cancelled: { label: '已取消', color: '#ff4d4f' }
} as const

// 晋级申请状态
export const PROMOTION_STATUS = {
  pending: { label: '待审核', color: '#faad14' },
  approved: { label: '已通过', color: '#52c41a' },
  rejected: { label: '已拒绝', color: '#ff4d4f' }
} as const

// 题目类型
export const QUESTION_TYPES = {
  single: { label: '单选题', color: '#1890ff' },
  multiple: { label: '多选题', color: '#52c41a' },
  judge: { label: '判断题', color: '#722ed1' },
  essay: { label: '简答题', color: '#faad14' }
} as const

// 难度等级
export const DIFFICULTY_LEVELS = [
  { value: 1, label: '简单', color: '#52c41a' },
  { value: 2, label: '较易', color: '#73d13d' },
  { value: 3, label: '中等', color: '#faad14' },
  { value: 4, label: '较难', color: '#fa8c16' },
  { value: 5, label: '困难', color: '#ff4d4f' }
]

// C端行为阶段映射 (用于患者端展示)
export const BEHAVIOR_STAGE_MAP = {
  precontemplation: {
    name: '前意向期',
    description: '尚未意识到需要改变',
    color: 'orange',
    icon: 'QuestionCircleOutlined',
    progress: 10
  },
  contemplation: {
    name: '意向期',
    description: '开始思考改变的可能',
    color: 'gold',
    icon: 'BulbOutlined',
    progress: 25
  },
  preparation: {
    name: '准备期',
    description: '正在为改变做准备',
    color: 'blue',
    icon: 'ToolOutlined',
    progress: 45
  },
  action: {
    name: '行动期',
    description: '正在积极实施改变',
    color: 'green',
    icon: 'ThunderboltOutlined',
    progress: 70
  },
  maintenance: {
    name: '维持期',
    description: '保持健康行为习惯',
    color: 'cyan',
    icon: 'SafetyOutlined',
    progress: 90
  },
  termination: {
    name: '终止期',
    description: '健康行为已成为习惯',
    color: 'purple',
    icon: 'TrophyOutlined',
    progress: 100
  }
} as const

// Agent 类型映射 (用于 AI 对话)
export const AGENT_TYPE_MAP = {
  A1: {
    name: '基础健康咨询',
    description: '解答日常健康问题',
    icon: 'RobotOutlined',
    color: '#1890ff'
  },
  A2: {
    name: '运动指导专家',
    description: '提供运动计划和建议',
    icon: 'ThunderboltOutlined',
    color: '#52c41a'
  },
  A3: {
    name: '饮食专家',
    description: '个性化饮食方案指导',
    icon: 'CoffeeOutlined',
    color: '#faad14'
  },
  A4: {
    name: '心理支持',
    description: '情绪管理和心理疏导',
    icon: 'HeartOutlined',
    color: '#eb2f96'
  },
  A5: {
    name: '用药提醒',
    description: '用药指导和提醒服务',
    icon: 'MedicineBoxOutlined',
    color: '#722ed1'
  }
} as const
