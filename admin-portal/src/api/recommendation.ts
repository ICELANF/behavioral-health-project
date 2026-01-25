/**
 * 推荐系统 API - 基于用户状态的个性化推荐
 */
import { BEHAVIOR_STAGE_MAP, TRIGGER_DOMAINS } from '@/constants/index'

// ============ 类型定义 ============

// 用户关注的问题领域
export type FocusArea = keyof typeof TRIGGER_DOMAINS

// 推荐视频
export interface RecommendedVideo {
  id: string
  title: string
  description: string
  thumbnail: string
  duration: number // 秒
  category: FocusArea
  stage: keyof typeof BEHAVIOR_STAGE_MAP
  views: number
  likes: number
  instructor: string
}

// 推荐产品
export interface RecommendedProduct {
  id: string
  name: string
  description: string
  image: string
  price: number
  originalPrice?: number
  category: FocusArea
  rating: number
  salesCount: number
  tags: string[]
}

// 推荐课程
export interface RecommendedCourse {
  id: string
  title: string
  description: string
  cover: string
  instructor: string
  instructorAvatar: string
  duration: number // 分钟
  lessonCount: number
  category: FocusArea
  stage: keyof typeof BEHAVIOR_STAGE_MAP
  level: 'beginner' | 'intermediate' | 'advanced'
  enrollCount: number
  rating: number
  price: number
  isFree: boolean
}

// 教练行为推荐
export interface RecommendedCoachAction {
  id: string
  title: string
  description: string
  category: 'education' | 'guidance' | 'coaching' | 'support'
  script: string
  tips: string[]
  stage: keyof typeof BEHAVIOR_STAGE_MAP
  focusArea: FocusArea
  difficulty: 'easy' | 'medium' | 'hard'
  expectedDuration: number // 分钟
}

// 综合推荐结果
export interface RecommendationResult {
  userStage: keyof typeof BEHAVIOR_STAGE_MAP
  focusAreas: FocusArea[]
  videos: RecommendedVideo[]
  products: RecommendedProduct[]
  courses: RecommendedCourse[]
  coachActions: RecommendedCoachAction[]
  dailyTip: {
    icon: string
    title: string
    content: string
  }
}

// ============ 模拟数据 ============

const mockVideos: RecommendedVideo[] = [
  {
    id: 'v001',
    title: '餐后血糖控制的5个黄金法则',
    description: '学习如何通过简单的生活方式调整，有效控制餐后血糖峰值',
    thumbnail: 'https://images.unsplash.com/photo-1505576399279-565b52d4ac71?w=400',
    duration: 480,
    category: 'glucose',
    stage: 'preparation',
    views: 12580,
    likes: 892,
    instructor: '李医生'
  },
  {
    id: 'v002',
    title: '糖尿病友好食谱：低GI早餐',
    description: '营养师教你制作美味又健康的低升糖早餐',
    thumbnail: 'https://images.unsplash.com/photo-1525351484163-7529414344d8?w=400',
    duration: 600,
    category: 'diet',
    stage: 'action',
    views: 8920,
    likes: 756,
    instructor: '王营养师'
  },
  {
    id: 'v003',
    title: '办公室10分钟降糖操',
    description: '适合上班族的简单运动，随时随地都能做',
    thumbnail: 'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400',
    duration: 720,
    category: 'exercise',
    stage: 'preparation',
    views: 15230,
    likes: 1203,
    instructor: '张教练'
  },
  {
    id: 'v004',
    title: '正确服用二甲双胍的注意事项',
    description: '药师详解二甲双胍的服用时间、剂量和常见问题',
    thumbnail: 'https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400',
    duration: 540,
    category: 'medication',
    stage: 'action',
    views: 6780,
    likes: 432,
    instructor: '陈药师'
  },
  {
    id: 'v005',
    title: '睡眠质量如何影响血糖',
    description: '揭秘睡眠与血糖的密切关系，改善睡眠的实用技巧',
    thumbnail: 'https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?w=400',
    duration: 420,
    category: 'sleep',
    stage: 'contemplation',
    views: 9450,
    likes: 678,
    instructor: '刘医生'
  }
]

const mockProducts: RecommendedProduct[] = [
  {
    id: 'p001',
    name: '智能血糖仪套装',
    description: '蓝牙连接，自动记录，生成趋势报告',
    image: 'https://images.unsplash.com/photo-1631549916768-4119b2e5f926?w=400',
    price: 299,
    originalPrice: 399,
    category: 'glucose',
    rating: 4.8,
    salesCount: 5620,
    tags: ['热销', '医院同款']
  },
  {
    id: 'p002',
    name: '低GI代餐粉（30日装）',
    description: '专为糖尿病人设计，营养均衡，控糖饱腹',
    image: 'https://images.unsplash.com/photo-1622485831930-8b8888e5b42a?w=400',
    price: 198,
    originalPrice: 268,
    category: 'diet',
    rating: 4.6,
    salesCount: 3280,
    tags: ['营养师推荐']
  },
  {
    id: 'p003',
    name: '智能运动手环',
    description: '心率监测+运动追踪+久坐提醒',
    image: 'https://images.unsplash.com/photo-1575311373937-040b8e1fd5b6?w=400',
    price: 159,
    originalPrice: 199,
    category: 'exercise',
    rating: 4.7,
    salesCount: 8920,
    tags: ['性价比之选']
  },
  {
    id: 'p004',
    name: '7天药盒提醒器',
    description: '智能提醒，分格存放，不再漏服',
    image: 'https://images.unsplash.com/photo-1550572017-edd951b55104?w=400',
    price: 68,
    category: 'medication',
    rating: 4.5,
    salesCount: 2150,
    tags: ['实用']
  }
]

const mockCourses: RecommendedCourse[] = [
  {
    id: 'c001',
    title: '糖尿病自我管理21天训练营',
    description: '系统学习血糖管理、饮食控制、运动处方，建立健康习惯',
    cover: 'https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=400',
    instructor: '李明教授',
    instructorAvatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=instructor1',
    duration: 630,
    lessonCount: 21,
    category: 'glucose',
    stage: 'preparation',
    level: 'beginner',
    enrollCount: 12580,
    rating: 4.9,
    price: 0,
    isFree: true
  },
  {
    id: 'c002',
    title: '糖友饮食全攻略',
    description: '从食材选择到烹饪技巧，打造适合糖尿病人的美味餐桌',
    cover: 'https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=400',
    instructor: '王芳营养师',
    instructorAvatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=instructor2',
    duration: 480,
    lessonCount: 16,
    category: 'diet',
    stage: 'action',
    level: 'intermediate',
    enrollCount: 8920,
    rating: 4.8,
    price: 99,
    isFree: false
  },
  {
    id: 'c003',
    title: '降糖运动处方',
    description: '针对不同体质定制的运动方案，安全有效降血糖',
    cover: 'https://images.unsplash.com/photo-1518611012118-696072aa579a?w=400',
    instructor: '张强教练',
    instructorAvatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=instructor3',
    duration: 360,
    lessonCount: 12,
    category: 'exercise',
    stage: 'preparation',
    level: 'beginner',
    enrollCount: 6780,
    rating: 4.7,
    price: 0,
    isFree: true
  }
]

const mockCoachActions: RecommendedCoachAction[] = [
  {
    id: 'ca001',
    title: '饮食日记回顾',
    description: '与教练一起分析您的饮食记录，找出改进空间',
    category: 'coaching',
    script: '让我们一起看看您这周的饮食记录。我注意到您在午餐时间经常...',
    tips: ['关注用餐时间规律性', '识别高GI食物', '建议替代方案'],
    stage: 'action',
    focusArea: 'diet',
    difficulty: 'easy',
    expectedDuration: 15
  },
  {
    id: 'ca002',
    title: '运动计划制定',
    description: '根据您的身体状况，制定个性化运动方案',
    category: 'guidance',
    script: '根据您目前的情况，我建议我们从每天15分钟的散步开始...',
    tips: ['循序渐进', '避免空腹运动', '注意运动后血糖变化'],
    stage: 'preparation',
    focusArea: 'exercise',
    difficulty: 'medium',
    expectedDuration: 20
  },
  {
    id: 'ca003',
    title: '血糖波动分析',
    description: '分析血糖数据，找出波动原因和改进方法',
    category: 'education',
    script: '我看到您最近的血糖有些波动，让我们一起分析一下可能的原因...',
    tips: ['关联饮食记录', '考虑压力因素', '检查用药依从性'],
    stage: 'action',
    focusArea: 'glucose',
    difficulty: 'medium',
    expectedDuration: 25
  },
  {
    id: 'ca004',
    title: '情绪支持对话',
    description: '倾听您的困扰，提供情绪支持和应对策略',
    category: 'support',
    script: '管理慢性病确实不容易，您现在感觉怎么样？有什么想和我分享的吗？',
    tips: ['积极倾听', '共情回应', '提供实际建议'],
    stage: 'contemplation',
    focusArea: 'stress',
    difficulty: 'easy',
    expectedDuration: 30
  }
]

// ============ API 函数 ============

/**
 * 获取用户关注的问题领域
 */
export async function getUserFocusAreas(): Promise<FocusArea[]> {
  return new Promise(resolve => {
    setTimeout(() => {
      // 模拟：根据用户数据返回关注领域
      resolve(['glucose', 'diet', 'exercise'])
    }, 300)
  })
}

/**
 * 获取个性化推荐
 */
export async function getRecommendations(
  stage: keyof typeof BEHAVIOR_STAGE_MAP,
  focusAreas: FocusArea[]
): Promise<RecommendationResult> {
  return new Promise(resolve => {
    setTimeout(() => {
      // 根据阶段和关注领域过滤推荐
      const filteredVideos = mockVideos.filter(
        v => focusAreas.includes(v.category)
      ).slice(0, 4)

      const filteredProducts = mockProducts.filter(
        p => focusAreas.includes(p.category)
      ).slice(0, 4)

      const filteredCourses = mockCourses.filter(
        c => focusAreas.includes(c.category)
      ).slice(0, 3)

      const filteredActions = mockCoachActions.filter(
        a => focusAreas.includes(a.focusArea)
      ).slice(0, 3)

      // 根据阶段生成每日提示
      const dailyTips: Record<string, { icon: string; title: string; content: string }> = {
        precontemplation: {
          icon: '🌱',
          title: '认识是改变的第一步',
          content: '了解自己的身体状况，是迈向健康的起点。今天花5分钟了解一下血糖管理吧！'
        },
        contemplation: {
          icon: '💭',
          title: '改变从想法开始',
          content: '您正在思考改变，这很棒！小小的改变也能带来大大的不同。'
        },
        preparation: {
          icon: '📝',
          title: '准备就绪，蓄势待发',
          content: '制定一个小目标，比如今天多走1000步，让改变自然发生。'
        },
        action: {
          icon: '🚀',
          title: '行动中的你最闪亮',
          content: '坚持得很好！每一天的努力都在为健康加分。'
        },
        maintenance: {
          icon: '🏆',
          title: '习惯已经养成',
          content: '健康管理已经成为您生活的一部分，继续保持！'
        },
        termination: {
          icon: '🌟',
          title: '健康达人就是你',
          content: '您已经成为健康管理的专家，可以帮助更多人！'
        }
      }

      resolve({
        userStage: stage,
        focusAreas,
        videos: filteredVideos,
        products: filteredProducts,
        courses: filteredCourses,
        coachActions: filteredActions,
        dailyTip: dailyTips[stage] || dailyTips.preparation
      })
    }, 500)
  })
}

/**
 * 记录用户点击行为（用于优化推荐）
 */
export async function trackRecommendationClick(
  type: 'video' | 'product' | 'course' | 'coachAction',
  itemId: string
): Promise<void> {
  console.log(`[推荐追踪] 用户点击了 ${type}: ${itemId}`)
  // 实际应用中会发送到后端记录
}

/**
 * 更新用户关注领域
 */
export async function updateUserFocusAreas(areas: FocusArea[]): Promise<boolean> {
  return new Promise(resolve => {
    setTimeout(() => {
      console.log('[用户偏好] 更新关注领域:', areas)
      resolve(true)
    }, 300)
  })
}
