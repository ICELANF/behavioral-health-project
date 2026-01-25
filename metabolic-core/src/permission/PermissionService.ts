/**
 * Permission Service - 四维权限服务
 * 实现 Role × Level × Certification × Status 权限判定
 */

import {
  SystemRole,
  UserStatus,
  PermissionAction,
  ResourceType,
  UserIdentity,
  PermissionRule,
  PermissionCheckRequest,
  PermissionCheckResult,
  PermissionCondition
} from './PermissionSchema';

/**
 * 预定义权限规则
 */
const PERMISSION_RULES: PermissionRule[] = [
  // ============ 用户档案权限 ============
  {
    id: 'profile_view_own',
    name: '查看自己的档案',
    description: '所有活跃用户可查看自己的档案',
    resource: 'user_profile',
    action: 'view',
    conditions: {
      required_status: ['active', 'training']
    }
  },
  {
    id: 'profile_view_student',
    name: '教练查看学员档案',
    description: '初级及以上教练可查看分配给自己的学员档案',
    resource: 'user_profile',
    action: 'view',
    conditions: {
      required_roles: ['COACH_JUNIOR', 'COACH_INTERMEDIATE', 'COACH_SENIOR', 'EXPERT', 'ADMIN'],
      min_level: 1,
      required_status: ['active']
    }
  },
  {
    id: 'profile_edit_student',
    name: '教练编辑学员档案',
    description: '中级及以上教练可编辑学员档案',
    resource: 'user_profile',
    action: 'edit',
    conditions: {
      required_roles: ['COACH_INTERMEDIATE', 'COACH_SENIOR', 'EXPERT', 'ADMIN'],
      min_level: 2,
      required_status: ['active']
    }
  },

  // ============ 健康数据权限 ============
  {
    id: 'health_data_view_own',
    name: '查看自己的健康数据',
    description: '用户可查看自己的健康数据',
    resource: 'health_data',
    action: 'view',
    conditions: {
      required_status: ['active']
    }
  },
  {
    id: 'health_data_view_student',
    name: '教练查看学员健康数据',
    description: '教练可查看学员健康数据',
    resource: 'health_data',
    action: 'view',
    conditions: {
      required_roles: ['COACH_JUNIOR', 'COACH_INTERMEDIATE', 'COACH_SENIOR', 'EXPERT'],
      min_level: 1,
      required_status: ['active']
    }
  },

  // ============ 干预计划权限 ============
  {
    id: 'intervention_view',
    name: '查看干预计划',
    description: '教练可查看干预计划',
    resource: 'intervention_plan',
    action: 'view',
    conditions: {
      required_roles: ['COACH_JUNIOR', 'COACH_INTERMEDIATE', 'COACH_SENIOR', 'EXPERT', 'ADMIN'],
      min_level: 1,
      required_status: ['active']
    }
  },
  {
    id: 'intervention_create_basic',
    name: '创建基础干预计划',
    description: '初级教练可创建低风险用户的基础干预计划',
    resource: 'intervention_plan',
    action: 'create',
    conditions: {
      required_roles: ['COACH_JUNIOR', 'COACH_INTERMEDIATE', 'COACH_SENIOR', 'EXPERT'],
      min_level: 1,
      required_certifications: ['L1_CERTIFIED'],
      required_status: ['active'],
      custom_check: 'checkLowRiskOnly'
    }
  },
  {
    id: 'intervention_create_advanced',
    name: '创建高级干预计划',
    description: '中级及以上教练可创建中高风险用户的干预计划',
    resource: 'intervention_plan',
    action: 'create',
    conditions: {
      required_roles: ['COACH_INTERMEDIATE', 'COACH_SENIOR', 'EXPERT'],
      min_level: 2,
      required_certifications: ['L2_CERTIFIED'],
      required_status: ['active']
    }
  },
  {
    id: 'intervention_approve',
    name: '审批干预计划',
    description: '专家可审批干预计划',
    resource: 'intervention_plan',
    action: 'approve',
    conditions: {
      required_roles: ['EXPERT', 'ADMIN'],
      min_level: 3,
      required_status: ['active']
    }
  },

  // ============ 教练学员权限 ============
  {
    id: 'coach_students_view',
    name: '查看学员列表',
    description: '教练可查看自己的学员',
    resource: 'coach_students',
    action: 'view',
    conditions: {
      required_roles: ['COACH_JUNIOR', 'COACH_INTERMEDIATE', 'COACH_SENIOR', 'EXPERT'],
      min_level: 1,
      required_status: ['active']
    }
  },
  {
    id: 'coach_students_manage',
    name: '管理学员分配',
    description: '高级教练可管理学员分配',
    resource: 'coach_students',
    action: 'edit',
    conditions: {
      required_roles: ['COACH_SENIOR', 'ADMIN'],
      min_level: 3,
      required_status: ['active']
    }
  },

  // ============ Agent权限 ============
  {
    id: 'agent_view_suggestions',
    name: '查看Agent建议',
    description: '教练可查看Agent建议',
    resource: 'agent_suggestion',
    action: 'view',
    conditions: {
      required_roles: ['COACH_JUNIOR', 'COACH_INTERMEDIATE', 'COACH_SENIOR', 'EXPERT'],
      min_level: 1,
      required_status: ['active']
    }
  },
  {
    id: 'agent_execute',
    name: '执行Agent任务',
    description: '中级及以上教练可执行Agent任务',
    resource: 'agent_suggestion',
    action: 'execute',
    conditions: {
      required_roles: ['COACH_INTERMEDIATE', 'COACH_SENIOR', 'EXPERT'],
      min_level: 2,
      required_certifications: ['L2_CERTIFIED'],
      required_status: ['active']
    }
  },
  {
    id: 'agent_configure',
    name: '配置Agent规则',
    description: '专家可配置Agent规则',
    resource: 'agent_suggestion',
    action: 'configure',
    conditions: {
      required_roles: ['EXPERT', 'ADMIN'],
      min_level: 4,
      required_certifications: ['L4_CERTIFIED'],
      required_status: ['active']
    }
  },

  // ============ 专家审核权限 ============
  {
    id: 'expert_review_view',
    name: '查看待审核列表',
    description: '专家可查看待审核内容',
    resource: 'expert_review',
    action: 'view',
    conditions: {
      required_roles: ['EXPERT', 'ADMIN'],
      min_level: 3,
      required_status: ['active']
    }
  },
  {
    id: 'expert_review_approve',
    name: '审批内容',
    description: '专家可审批方案',
    resource: 'expert_review',
    action: 'approve',
    conditions: {
      required_roles: ['EXPERT', 'ADMIN'],
      min_level: 3,
      required_certifications: ['L3_CERTIFIED'],
      required_status: ['active']
    }
  },

  // ============ 认证考试权限 ============
  {
    id: 'cert_view_own',
    name: '查看自己的认证',
    description: '所有用户可查看自己的认证状态',
    resource: 'certification',
    action: 'view',
    conditions: {
      required_status: ['active', 'training']
    }
  },
  {
    id: 'cert_take_exam',
    name: '参加考试',
    description: '活跃用户可参加考试',
    resource: 'certification',
    action: 'execute',
    conditions: {
      required_status: ['active']
    }
  },
  {
    id: 'cert_manage',
    name: '管理认证体系',
    description: '管理员可管理认证',
    resource: 'certification',
    action: 'configure',
    conditions: {
      required_roles: ['TRAINER', 'ADMIN'],
      min_level: 4,
      required_status: ['active']
    }
  },

  // ============ 培训内容权限 ============
  {
    id: 'training_view',
    name: '查看培训内容',
    description: '所有活跃用户可查看培训内容',
    resource: 'training_content',
    action: 'view',
    conditions: {
      required_status: ['active', 'training']
    }
  },
  {
    id: 'training_create',
    name: '创建培训内容',
    description: '讲师可创建培训内容',
    resource: 'training_content',
    action: 'create',
    conditions: {
      required_roles: ['TRAINER', 'EXPERT', 'ADMIN'],
      min_level: 3,
      required_status: ['active']
    }
  },

  // ============ 系统配置权限 ============
  {
    id: 'system_config',
    name: '系统配置',
    description: '管理员可配置系统',
    resource: 'system_config',
    action: 'configure',
    conditions: {
      required_roles: ['ADMIN'],
      required_status: ['active']
    }
  },

  // ============ 决策记录权限 ============
  {
    id: 'decision_view_own',
    name: '查看自己相关的决策记录',
    description: '用户可查看与自己相关的决策记录',
    resource: 'decision_record',
    action: 'view',
    conditions: {
      required_status: ['active']
    }
  },
  {
    id: 'decision_view_all',
    name: '查看所有决策记录',
    description: '专家可查看所有决策记录用于科研',
    resource: 'decision_record',
    action: 'view',
    conditions: {
      required_roles: ['EXPERT', 'ADMIN'],
      min_level: 3,
      required_status: ['active']
    }
  }
];

/**
 * 角色层级映射
 */
const ROLE_HIERARCHY: Record<SystemRole, number> = {
  'USER': 0,
  'STUDENT': 0,
  'COACH_JUNIOR': 1,
  'COACH_INTERMEDIATE': 2,
  'COACH_SENIOR': 3,
  'EXPERT': 4,
  'TRAINER': 3,
  'ADMIN': 5,
  'AGENT': 0
};

/**
 * 权限服务类
 */
export class PermissionService {
  private rules: Map<string, PermissionRule> = new Map();
  private customChecks: Map<string, (request: PermissionCheckRequest) => boolean> = new Map();

  constructor() {
    // 加载预定义规则
    PERMISSION_RULES.forEach(rule => {
      this.rules.set(rule.id, rule);
    });

    // 注册自定义检查函数
    this.registerCustomCheck('checkLowRiskOnly', (request) => {
      return request.context?.target_risk_level === 'low';
    });

    this.registerCustomCheck('checkOwnResource', (request) => {
      return request.user.user_id === request.context?.target_user_id;
    });

    this.registerCustomCheck('checkAssignedStudent', (request) => {
      // 实际应用中需要查询数据库验证教练-学员关系
      return true;
    });
  }

  /**
   * 注册自定义检查函数
   */
  registerCustomCheck(name: string, check: (request: PermissionCheckRequest) => boolean): void {
    this.customChecks.set(name, check);
  }

  /**
   * 检查权限
   */
  check(request: PermissionCheckRequest): PermissionCheckResult {
    const { user, resource, action } = request;

    // 状态检查
    if (user.status === 'suspended') {
      return {
        allowed: false,
        reason: '账户已暂停，无法执行任何操作'
      };
    }

    if (user.status === 'inactive') {
      return {
        allowed: false,
        reason: '账户未激活'
      };
    }

    // 查找匹配的规则
    const matchingRules = this.findMatchingRules(resource, action);

    if (matchingRules.length === 0) {
      return {
        allowed: false,
        reason: `未找到资源 ${resource} 的 ${action} 权限规则`
      };
    }

    // 逐一检查规则
    for (const rule of matchingRules) {
      const result = this.checkRule(request, rule);
      if (result.allowed) {
        return {
          ...result,
          matched_rule: rule.id
        };
      }
    }

    // 所有规则都不满足
    const firstRule = matchingRules[0];
    return {
      allowed: false,
      reason: '权限不足',
      required_level: firstRule.conditions.min_level,
      required_certifications: firstRule.conditions.required_certifications
    };
  }

  /**
   * 查找匹配资源和操作的规则
   */
  private findMatchingRules(resource: ResourceType, action: PermissionAction): PermissionRule[] {
    return Array.from(this.rules.values()).filter(
      rule => rule.resource === resource && rule.action === action
    );
  }

  /**
   * 检查单个规则
   */
  private checkRule(request: PermissionCheckRequest, rule: PermissionRule): PermissionCheckResult {
    const { user } = request;
    const { conditions } = rule;

    // 检查角色
    if (conditions.required_roles && conditions.required_roles.length > 0) {
      if (!conditions.required_roles.includes(user.role)) {
        return {
          allowed: false,
          reason: `需要角色: ${conditions.required_roles.join(' 或 ')}`
        };
      }
    }

    // 检查等级
    if (conditions.min_level !== undefined) {
      if (user.level < conditions.min_level) {
        return {
          allowed: false,
          reason: `需要等级 ${conditions.min_level}，当前等级 ${user.level}`,
          required_level: conditions.min_level
        };
      }
    }

    if (conditions.max_level !== undefined) {
      if (user.level > conditions.max_level) {
        return {
          allowed: false,
          reason: `等级超过上限 ${conditions.max_level}`
        };
      }
    }

    // 检查认证
    if (conditions.required_certifications && conditions.required_certifications.length > 0) {
      const hasCerts = conditions.required_certifications.every(
        cert => user.certifications.includes(cert)
      );
      if (!hasCerts) {
        return {
          allowed: false,
          reason: `需要认证: ${conditions.required_certifications.join(', ')}`,
          required_certifications: conditions.required_certifications
        };
      }
    }

    // 检查状态
    if (conditions.required_status && conditions.required_status.length > 0) {
      if (!conditions.required_status.includes(user.status)) {
        return {
          allowed: false,
          reason: `账户状态需要: ${conditions.required_status.join(' 或 ')}`
        };
      }
    }

    // 执行自定义检查
    if (conditions.custom_check) {
      const customCheck = this.customChecks.get(conditions.custom_check);
      if (customCheck && !customCheck(request)) {
        return {
          allowed: false,
          reason: `自定义检查失败: ${conditions.custom_check}`
        };
      }
    }

    return { allowed: true };
  }

  /**
   * 获取用户所有权限
   */
  getUserPermissions(user: UserIdentity): string[] {
    const permissions: string[] = [];
    const resources: ResourceType[] = [
      'user_profile', 'health_data', 'intervention_plan', 'coach_students',
      'certification', 'training_content', 'agent_suggestion', 'expert_review',
      'system_config', 'commercial_resource', 'decision_record'
    ];
    const actions: PermissionAction[] = ['view', 'create', 'edit', 'delete', 'approve', 'execute', 'configure'];

    for (const resource of resources) {
      for (const action of actions) {
        const result = this.check({ user, resource, action });
        if (result.allowed) {
          permissions.push(`${resource}:${action}`);
        }
      }
    }

    return permissions;
  }

  /**
   * 根据角色获取基础等级
   */
  getRoleBaseLevel(role: SystemRole): number {
    return ROLE_HIERARCHY[role] || 0;
  }

  /**
   * 检查是否可以服务指定风险等级的用户
   */
  canServeRiskLevel(user: UserIdentity, riskLevel: 'low' | 'medium' | 'high'): boolean {
    const riskLevelMap = { low: 1, medium: 2, high: 3 };
    const requiredLevel = riskLevelMap[riskLevel];

    // L1 只能服务 low
    // L2 可以服务 low, medium
    // L3+ 可以服务所有
    if (user.level >= 3) return true;
    if (user.level === 2) return requiredLevel <= 2;
    if (user.level === 1) return requiredLevel === 1;
    return false;
  }

  /**
   * 获取最大可服务学员数
   */
  getMaxStudentCount(user: UserIdentity): number {
    switch (user.level) {
      case 0: return 0;
      case 1: return 10;   // L1 初级教练最多10人
      case 2: return 30;   // L2 中级教练最多30人
      case 3: return 50;   // L3 高级教练最多50人
      case 4: return 100;  // L4 督导最多100人
      default: return 0;
    }
  }

  /**
   * 获取所有规则
   */
  getAllRules(): PermissionRule[] {
    return Array.from(this.rules.values());
  }

  /**
   * 添加自定义规则
   */
  addRule(rule: PermissionRule): void {
    this.rules.set(rule.id, rule);
  }
}

// 导出单例
export const permissionService = new PermissionService();
