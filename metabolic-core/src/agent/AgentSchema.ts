/**
 * Agent Schema - Agent系统类型定义
 * 统一的Agent插槽架构
 */

/**
 * Agent类型
 */
export type AgentType =
  | 'assessment_agent'        // 评估Agent
  | 'intervention_agent'      // 干预Agent
  | 'coaching_agent'          // 教练陪伴Agent
  | 'training_agent'          // 训练Agent
  | 'review_agent'            // 审核Agent
  | 'alert_agent'             // 预警Agent
  | 'recommendation_agent';   // 推荐Agent

/**
 * Agent输出类型
 */
export type AgentOutputType =
  | 'suggestion'              // 建议
  | 'risk_alert'              // 风险预警
  | 'intervention_plan'       // 干预计划
  | 'training_case'           // 训练案例
  | 'assessment_result'       // 评估结果
  | 'recommendation';         // 推荐内容

/**
 * Agent任务
 */
export interface AgentTask {
  task_id: string;
  agent_type: AgentType;
  user_id: string;
  coach_id?: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  context: AgentContext;
  expected_output: AgentOutputType;
  created_at: string;
  expires_at?: string;
  callback_url?: string;
}

/**
 * Agent上下文
 */
export interface AgentContext {
  profile: UserProfileSnapshot;
  device_data?: DeviceDataSnapshot[];
  behavior_stage?: string;
  phenotype_tags?: string[];
  recent_interventions?: InterventionSnapshot[];
  conversation_history?: ConversationMessage[];
  custom_data?: Record<string, any>;
}

/**
 * 用户档案快照
 */
export interface UserProfileSnapshot {
  user_id: string;
  age?: number;
  gender?: 'male' | 'female' | 'other';
  primary_conditions?: string[];
  risk_level: 'low' | 'medium' | 'high';
  behavior_stage: string;
  current_goals?: string[];
  preferences?: Record<string, any>;
}

/**
 * 设备数据快照
 */
export interface DeviceDataSnapshot {
  device_type: string;
  metric: string;
  value: number;
  unit: string;
  timestamp: string;
}

/**
 * 干预快照
 */
export interface InterventionSnapshot {
  intervention_id: string;
  type: string;
  status: 'active' | 'completed' | 'paused';
  progress: number;
  outcome?: string;
}

/**
 * 对话消息
 */
export interface ConversationMessage {
  role: 'user' | 'coach' | 'agent';
  content: string;
  timestamp: string;
}

/**
 * Agent输出（强约束格式）
 */
export interface AgentOutput {
  task_id: string;
  agent_id: string;
  agent_type: AgentType;
  output_type: AgentOutputType;
  confidence: number;          // 0-1 置信度
  suggestions: AgentSuggestion[];
  risk_flags: string[];
  need_human_review: boolean;
  review_reason?: string;
  metadata: {
    processing_time_ms: number;
    model_version: string;
    token_usage?: number;
  };
  created_at: string;
}

/**
 * Agent建议
 */
export interface AgentSuggestion {
  id: string;
  type: 'action' | 'task' | 'alert' | 'content' | 'resource';
  priority: number;          // 1-10
  text: string;
  rationale?: string;        // 建议理由
  evidence?: string[];       // 支持证据
  action_url?: string;
  expires_at?: string;
}

/**
 * Agent反馈
 */
export interface AgentFeedback {
  feedback_id: string;
  task_id: string;
  agent_id: string;
  user_id: string;
  reviewer_id: string;
  reviewer_role: string;
  feedback_type: 'accept' | 'reject' | 'modify' | 'rate';
  rating?: number;           // 1-5
  comment?: string;
  modifications?: {
    original: any;
    modified: any;
  };
  applied: boolean;
  timestamp: string;
}

/**
 * Agent注册信息
 */
export interface AgentRegistration {
  agent_id: string;
  agent_type: AgentType;
  name: string;
  description: string;
  version: string;
  supported_outputs: AgentOutputType[];
  required_context: string[];
  max_concurrent_tasks: number;
  average_response_time_ms: number;
  status: 'active' | 'inactive' | 'maintenance';
  created_at: string;
  updated_at: string;
}

/**
 * Agent执行历史
 */
export interface AgentExecutionHistory {
  execution_id: string;
  task_id: string;
  agent_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'timeout';
  input_snapshot: AgentTask;
  output_snapshot?: AgentOutput;
  error?: string;
  feedback?: AgentFeedback;
  started_at: string;
  completed_at?: string;
}

/**
 * Agent统计
 */
export interface AgentStats {
  agent_id: string;
  total_tasks: number;
  successful_tasks: number;
  failed_tasks: number;
  average_confidence: number;
  average_response_time_ms: number;
  acceptance_rate: number;
  average_rating: number;
  last_active_at: string;
}
