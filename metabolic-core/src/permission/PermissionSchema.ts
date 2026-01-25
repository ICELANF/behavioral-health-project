/**
 * Permission Schema - 权限系统类型定义
 * 四维权限模型：Role × Level × Certification × Status
 */

/**
 * 系统角色
 */
export type SystemRole =
  | 'USER'           // 普通用户
  | 'STUDENT'        // 学习型用户
  | 'COACH_JUNIOR'   // 初级教练
  | 'COACH_INTERMEDIATE' // 中级教练
  | 'COACH_SENIOR'   // 高级教练
  | 'EXPERT'         // 专家
  | 'TRAINER'        // 培训讲师
  | 'ADMIN'          // 管理员
  | 'AGENT';         // 系统Agent

/**
 * 用户状态
 */
export type UserStatus =
  | 'active'         // 正常
  | 'suspended'      // 暂停
  | 'training'       // 培训中
  | 'pending'        // 待审核
  | 'inactive';      // 未激活

/**
 * 权限操作类型
 */
export type PermissionAction =
  | 'view'           // 查看
  | 'create'         // 创建
  | 'edit'           // 编辑
  | 'delete'         // 删除
  | 'approve'        // 审批
  | 'execute'        // 执行
  | 'configure';     // 配置

/**
 * 资源类型
 */
export type ResourceType =
  | 'user_profile'           // 用户档案
  | 'health_data'            // 健康数据
  | 'intervention_plan'      // 干预计划
  | 'coach_students'         // 教练学员
  | 'certification'          // 认证考试
  | 'training_content'       // 培训内容
  | 'agent_suggestion'       // Agent建议
  | 'expert_review'          // 专家审核
  | 'system_config'          // 系统配置
  | 'commercial_resource'    // 商业资源
  | 'decision_record';       // 决策记录

/**
 * 用户身份
 */
export interface UserIdentity {
  user_id: string;
  role: SystemRole;
  level: number;              // 成长等级 0-4
  certifications: string[];   // 已获认证
  status: UserStatus;
  permissions: string[];      // 动态计算的权限列表
  specialty_tags?: string[];  // 专项标签
  coach_id?: string;          // 所属教练ID
  team_id?: string;           // 所属团队ID
}

/**
 * 权限规则
 */
export interface PermissionRule {
  id: string;
  name: string;
  description: string;
  resource: ResourceType;
  action: PermissionAction;
  conditions: PermissionCondition;
}

/**
 * 权限条件 - 四维判定
 */
export interface PermissionCondition {
  required_roles?: SystemRole[];
  min_level?: number;
  max_level?: number;
  required_certifications?: string[];
  required_status?: UserStatus[];
  custom_check?: string;      // 自定义检查函数名
}

/**
 * 权限检查请求
 */
export interface PermissionCheckRequest {
  user: UserIdentity;
  resource: ResourceType;
  action: PermissionAction;
  context?: {
    target_user_id?: string;
    target_risk_level?: 'low' | 'medium' | 'high';
    resource_id?: string;
    [key: string]: any;
  };
}

/**
 * 权限检查结果
 */
export interface PermissionCheckResult {
  allowed: boolean;
  reason?: string;
  matched_rule?: string;
  required_level?: number;
  required_certifications?: string[];
}

/**
 * Agent权限
 */
export interface AgentPermission {
  agent_type: string;
  permission_level: 'view' | 'execute' | 'configure';
  granted_at: string;
  expires_at?: string;
}

/**
 * 决策记录（科研级资产）
 */
export interface DecisionRecord {
  record_id: string;
  user_id: string;
  agent_id: string;
  input_snapshot: any;
  output_snapshot: any;
  human_review: boolean;
  reviewer_id?: string;
  final_decision: any;
  feedback?: {
    rating: number;
    comment: string;
    applied: boolean;
  };
  timestamp: string;
}

/**
 * 用户成长档案
 */
export interface UserGrowthProfile {
  user_id: string;
  phenotype_tags: string[];
  behavior_stage: string;
  risk_level: 'low' | 'medium' | 'high';
  coach_id?: string;
  trajectory_summary: {
    total_days: number;
    active_days: number;
    completed_tasks: number;
    improvement_rate: number;
  };
  created_at: string;
  updated_at: string;
}
