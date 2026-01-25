/**
 * Commercial Resource Library - 商业资源库
 * 管理产品、服务、合作伙伴等商业资源
 */

import { v4 as uuidv4 } from 'uuid';

/**
 * 资源类型
 */
export type ResourceType =
  | 'device'          // 设备
  | 'supplement'      // 补充剂
  | 'food'            // 食品
  | 'service'         // 服务
  | 'program'         // 课程/项目
  | 'app';            // 应用

/**
 * 资源类别
 */
export type ResourceCategory =
  | 'monitoring'      // 监测类
  | 'nutrition'       // 营养类
  | 'fitness'         // 健身类
  | 'mental_health'   // 心理健康
  | 'medical'         // 医疗类
  | 'education';      // 教育类

/**
 * 商业资源
 */
export interface CommercialResource {
  /** 资源ID */
  resource_id: string;
  /** 资源名称 */
  name: string;
  /** 资源类型 */
  type: ResourceType;
  /** 资源类别 */
  category: ResourceCategory;
  /** 品牌 */
  brand?: string;
  /** 描述 */
  description: string;
  /** 核心卖点 */
  key_benefits: string[];
  /** 适用人群 */
  target_audience: string[];
  /** 适用表型 */
  applicable_phenotypes?: string[];
  /** 价格信息 */
  pricing?: {
    price: number;
    currency: string;
    unit?: string;
    discount_available?: boolean;
  };
  /** 购买链接 */
  purchase_url?: string;
  /** 图片URL */
  image_url?: string;
  /** 评分 */
  rating?: {
    score: number;
    count: number;
  };
  /** 库存状态 */
  availability: 'in_stock' | 'low_stock' | 'out_of_stock' | 'pre_order';
  /** 推荐优先级 */
  priority: number;
  /** 佣金比例 */
  commission_rate?: number;
  /** 合作状态 */
  partnership_status: 'active' | 'pending' | 'expired';
  /** 创建时间 */
  created_at: string;
  /** 更新时间 */
  updated_at?: string;
}

/**
 * 合作伙伴
 */
export interface Partner {
  /** 合作伙伴ID */
  partner_id: string;
  /** 名称 */
  name: string;
  /** 类型 */
  type: 'manufacturer' | 'retailer' | 'service_provider' | 'content_creator' | 'healthcare';
  /** 描述 */
  description: string;
  /** 联系方式 */
  contact?: {
    email?: string;
    phone?: string;
    website?: string;
  };
  /** 合作资源 */
  resources: string[]; // resource_ids
  /** 合作协议 */
  agreement?: {
    start_date: string;
    end_date?: string;
    terms?: string;
  };
  /** 状态 */
  status: 'active' | 'inactive' | 'pending';
}

/**
 * 推荐记录
 */
export interface ResourceRecommendation {
  /** 推荐ID */
  recommendation_id: string;
  /** 用户ID */
  user_id: string;
  /** 资源ID */
  resource_id: string;
  /** 推荐理由 */
  reason: string;
  /** 推荐时间 */
  recommended_at: string;
  /** 用户反馈 */
  user_feedback?: {
    clicked: boolean;
    purchased: boolean;
    rating?: number;
    feedback?: string;
  };
}

/**
 * 预定义商业资源
 */
export const PREDEFINED_RESOURCES: CommercialResource[] = [
  {
    resource_id: 'RES-001',
    name: '连续血糖监测仪(CGM)',
    type: 'device',
    category: 'monitoring',
    brand: '通用型',
    description: '实时监测血糖变化，帮助了解饮食和生活方式对血糖的影响',
    key_benefits: [
      '实时血糖数据',
      '趋势预警功能',
      '无需频繁扎手指',
      '与APP联动分析'
    ],
    target_audience: ['糖尿病患者', '血糖管理需求者', '健康管理爱好者'],
    applicable_phenotypes: ['PHE-001', 'PHE-003', 'PHE-004'],
    availability: 'in_stock',
    priority: 100,
    partnership_status: 'active',
    created_at: new Date().toISOString()
  },
  {
    resource_id: 'RES-002',
    name: '智能血压计',
    type: 'device',
    category: 'monitoring',
    description: '蓝牙连接智能血压计，自动同步数据到APP',
    key_benefits: [
      '医疗级精准测量',
      '自动数据同步',
      '多用户管理',
      '心律不齐检测'
    ],
    target_audience: ['高血压患者', '心血管风险人群'],
    availability: 'in_stock',
    priority: 80,
    partnership_status: 'active',
    created_at: new Date().toISOString()
  },
  {
    resource_id: 'RES-003',
    name: 'HRV智能手环',
    type: 'device',
    category: 'monitoring',
    description: '监测心率变异性和睡眠质量',
    key_benefits: [
      'HRV实时监测',
      '睡眠分析',
      '压力评估',
      '运动追踪'
    ],
    target_audience: ['压力管理需求者', '睡眠问题人群'],
    applicable_phenotypes: ['PHE-005', 'PHE-007'],
    availability: 'in_stock',
    priority: 85,
    partnership_status: 'active',
    created_at: new Date().toISOString()
  },
  {
    resource_id: 'RES-004',
    name: '低GI代餐粉',
    type: 'food',
    category: 'nutrition',
    description: '专为血糖管理设计的低升糖指数营养代餐',
    key_benefits: [
      '低GI配方',
      '均衡营养',
      '延缓餐后血糖上升',
      '增强饱腹感'
    ],
    target_audience: ['糖尿病患者', '体重管理需求者'],
    applicable_phenotypes: ['PHE-001'],
    availability: 'in_stock',
    priority: 70,
    partnership_status: 'active',
    created_at: new Date().toISOString()
  },
  {
    resource_id: 'RES-005',
    name: '正念冥想课程',
    type: 'program',
    category: 'mental_health',
    description: '8周正念减压课程，专为慢病人群设计',
    key_benefits: [
      '专业导师指导',
      '渐进式学习',
      '社群支持',
      '科学验证有效'
    ],
    target_audience: ['压力大的慢病患者', '情绪管理需求者'],
    applicable_phenotypes: ['PHE-005'],
    pricing: {
      price: 299,
      currency: 'CNY',
      unit: '期'
    },
    availability: 'in_stock',
    priority: 75,
    partnership_status: 'active',
    created_at: new Date().toISOString()
  },
  {
    resource_id: 'RES-006',
    name: '睡眠改善APP会员',
    type: 'app',
    category: 'mental_health',
    description: '提供白噪音、冥想引导、睡眠追踪等功能',
    key_benefits: [
      '丰富的助眠内容',
      '睡眠数据分析',
      '个性化建议',
      '定时关闭功能'
    ],
    target_audience: ['睡眠困难人群', '作息不规律者'],
    applicable_phenotypes: ['PHE-007'],
    pricing: {
      price: 15,
      currency: 'CNY',
      unit: '月'
    },
    availability: 'in_stock',
    priority: 65,
    partnership_status: 'active',
    created_at: new Date().toISOString()
  },
  {
    resource_id: 'RES-007',
    name: '居家运动器材套装',
    type: 'device',
    category: 'fitness',
    description: '包含弹力带、瑜伽垫、哑铃的居家健身套装',
    key_benefits: [
      '无需健身房',
      '适合初学者',
      '占地小',
      '含教学视频'
    ],
    target_audience: ['久坐办公人群', '运动初学者'],
    applicable_phenotypes: ['PHE-006'],
    pricing: {
      price: 199,
      currency: 'CNY'
    },
    availability: 'in_stock',
    priority: 60,
    partnership_status: 'active',
    created_at: new Date().toISOString()
  },
  {
    resource_id: 'RES-008',
    name: '营养师1对1咨询',
    type: 'service',
    category: 'nutrition',
    description: '注册营养师提供个性化饮食方案制定',
    key_benefits: [
      '专业营养师',
      '个性化方案',
      '持续跟踪调整',
      '食谱定制'
    ],
    target_audience: ['需要专业饮食指导的患者'],
    pricing: {
      price: 399,
      currency: 'CNY',
      unit: '次'
    },
    availability: 'in_stock',
    priority: 90,
    partnership_status: 'active',
    created_at: new Date().toISOString()
  }
];

/**
 * 商业资源服务
 */
export class CommercialResourceService {
  private resources: Map<string, CommercialResource> = new Map();
  private partners: Map<string, Partner> = new Map();
  private recommendations: Map<string, ResourceRecommendation[]> = new Map();

  constructor() {
    // 加载预定义资源
    PREDEFINED_RESOURCES.forEach(r => {
      this.resources.set(r.resource_id, r);
    });
  }

  /**
   * 根据条件搜索资源
   */
  searchResources(criteria: {
    type?: ResourceType;
    category?: ResourceCategory;
    phenotype?: string;
    maxPrice?: number;
    availability?: CommercialResource['availability'];
  }): CommercialResource[] {
    let results = Array.from(this.resources.values())
      .filter(r => r.partnership_status === 'active');

    if (criteria.type) {
      results = results.filter(r => r.type === criteria.type);
    }
    if (criteria.category) {
      results = results.filter(r => r.category === criteria.category);
    }
    if (criteria.phenotype) {
      results = results.filter(r =>
        r.applicable_phenotypes?.includes(criteria.phenotype!) ?? false
      );
    }
    if (criteria.maxPrice !== undefined) {
      results = results.filter(r =>
        !r.pricing || r.pricing.price <= criteria.maxPrice!
      );
    }
    if (criteria.availability) {
      results = results.filter(r => r.availability === criteria.availability);
    }

    // 按优先级排序
    return results.sort((a, b) => b.priority - a.priority);
  }

  /**
   * 根据表型推荐资源
   */
  recommendByPhenotypes(
    phenotypeIds: string[],
    limit: number = 5
  ): CommercialResource[] {
    const results = Array.from(this.resources.values())
      .filter(r =>
        r.partnership_status === 'active' &&
        r.applicable_phenotypes?.some(p => phenotypeIds.includes(p))
      )
      .sort((a, b) => b.priority - a.priority);

    return results.slice(0, limit);
  }

  /**
   * 创建推荐记录
   */
  createRecommendation(
    userId: string,
    resourceId: string,
    reason: string
  ): ResourceRecommendation {
    const recommendation: ResourceRecommendation = {
      recommendation_id: uuidv4(),
      user_id: userId,
      resource_id: resourceId,
      reason,
      recommended_at: new Date().toISOString()
    };

    const userRecs = this.recommendations.get(userId) || [];
    userRecs.push(recommendation);
    this.recommendations.set(userId, userRecs);

    return recommendation;
  }

  /**
   * 记录用户反馈
   */
  recordFeedback(
    recommendationId: string,
    feedback: ResourceRecommendation['user_feedback']
  ): boolean {
    for (const [userId, recs] of this.recommendations.entries()) {
      const rec = recs.find(r => r.recommendation_id === recommendationId);
      if (rec) {
        rec.user_feedback = feedback;
        return true;
      }
    }
    return false;
  }

  /**
   * 获取用户推荐历史
   */
  getUserRecommendations(userId: string): ResourceRecommendation[] {
    return this.recommendations.get(userId) || [];
  }

  /**
   * 注册资源
   */
  registerResource(
    resource: Omit<CommercialResource, 'resource_id' | 'created_at'>
  ): CommercialResource {
    const newResource: CommercialResource = {
      resource_id: `RES-${uuidv4().slice(0, 8).toUpperCase()}`,
      ...resource,
      created_at: new Date().toISOString()
    };
    this.resources.set(newResource.resource_id, newResource);
    return newResource;
  }

  /**
   * 注册合作伙伴
   */
  registerPartner(partner: Omit<Partner, 'partner_id'>): Partner {
    const newPartner: Partner = {
      partner_id: `PTN-${uuidv4().slice(0, 8).toUpperCase()}`,
      ...partner
    };
    this.partners.set(newPartner.partner_id, newPartner);
    return newPartner;
  }

  /**
   * 获取资源
   */
  getResource(resourceId: string): CommercialResource | undefined {
    return this.resources.get(resourceId);
  }

  /**
   * 获取所有资源
   */
  getAllResources(): CommercialResource[] {
    return Array.from(this.resources.values());
  }

  /**
   * 获取所有合作伙伴
   */
  getAllPartners(): Partner[] {
    return Array.from(this.partners.values());
  }

  /**
   * 更新资源可用性
   */
  updateAvailability(
    resourceId: string,
    availability: CommercialResource['availability']
  ): boolean {
    const resource = this.resources.get(resourceId);
    if (!resource) return false;

    resource.availability = availability;
    resource.updated_at = new Date().toISOString();
    return true;
  }

  /**
   * 获取推荐转化统计
   */
  getConversionStats(resourceId?: string): {
    total_recommendations: number;
    clicked: number;
    purchased: number;
    click_rate: number;
    conversion_rate: number;
  } {
    let allRecs: ResourceRecommendation[] = [];
    for (const recs of this.recommendations.values()) {
      if (resourceId) {
        allRecs.push(...recs.filter(r => r.resource_id === resourceId));
      } else {
        allRecs.push(...recs);
      }
    }

    const total = allRecs.length;
    const clicked = allRecs.filter(r => r.user_feedback?.clicked).length;
    const purchased = allRecs.filter(r => r.user_feedback?.purchased).length;

    return {
      total_recommendations: total,
      clicked,
      purchased,
      click_rate: total > 0 ? (clicked / total) * 100 : 0,
      conversion_rate: clicked > 0 ? (purchased / clicked) * 100 : 0
    };
  }
}

// 导出单例
export const commercialResourceService = new CommercialResourceService();
