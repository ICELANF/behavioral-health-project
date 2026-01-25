/**
 * Agent Orchestrator - Agent编排器
 * 统一的Agent调度、输出标准化、人工审核、反馈收集
 */

import { v4 as uuidv4 } from 'uuid';
import {
  AgentType,
  AgentOutputType,
  AgentTask,
  AgentOutput,
  AgentFeedback,
  AgentRegistration,
  AgentExecutionHistory,
  AgentStats,
  AgentContext,
  AgentSuggestion
} from './AgentSchema';

/**
 * Agent处理器接口
 */
export interface AgentHandler {
  agent_id: string;
  agent_type: AgentType;
  process(task: AgentTask): Promise<AgentOutput>;
}

/**
 * Agent编排器
 */
export class AgentOrchestrator {
  private agents: Map<string, AgentRegistration> = new Map();
  private handlers: Map<string, AgentHandler> = new Map();
  private tasks: Map<string, AgentTask> = new Map();
  private executions: Map<string, AgentExecutionHistory> = new Map();
  private feedbacks: Map<string, AgentFeedback> = new Map();

  constructor() {
    this.initializeDefaultAgents();
  }

  /**
   * 初始化默认Agent
   */
  private initializeDefaultAgents(): void {
    const defaultAgents: AgentRegistration[] = [
      {
        agent_id: 'assessment_agent_v1',
        agent_type: 'assessment_agent',
        name: '评估Agent',
        description: '基于用户数据生成健康评估报告',
        version: '1.0.0',
        supported_outputs: ['assessment_result', 'risk_alert'],
        required_context: ['profile', 'device_data'],
        max_concurrent_tasks: 10,
        average_response_time_ms: 2000,
        status: 'active',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      {
        agent_id: 'intervention_agent_v1',
        agent_type: 'intervention_agent',
        name: '干预Agent',
        description: '基于用户画像生成个性化干预建议',
        version: '1.0.0',
        supported_outputs: ['intervention_plan', 'suggestion'],
        required_context: ['profile', 'behavior_stage', 'phenotype_tags'],
        max_concurrent_tasks: 10,
        average_response_time_ms: 3000,
        status: 'active',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      {
        agent_id: 'coaching_agent_v1',
        agent_type: 'coaching_agent',
        name: '教练陪伴Agent',
        description: '提供日常对话和行为指导',
        version: '1.0.0',
        supported_outputs: ['suggestion', 'recommendation'],
        required_context: ['profile', 'conversation_history'],
        max_concurrent_tasks: 20,
        average_response_time_ms: 1500,
        status: 'active',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      {
        agent_id: 'alert_agent_v1',
        agent_type: 'alert_agent',
        name: '预警Agent',
        description: '监测异常指标并发出预警',
        version: '1.0.0',
        supported_outputs: ['risk_alert'],
        required_context: ['profile', 'device_data'],
        max_concurrent_tasks: 50,
        average_response_time_ms: 500,
        status: 'active',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      {
        agent_id: 'training_agent_v1',
        agent_type: 'training_agent',
        name: '训练Agent',
        description: '生成模拟案例和训练场景',
        version: '1.0.0',
        supported_outputs: ['training_case'],
        required_context: ['profile'],
        max_concurrent_tasks: 5,
        average_response_time_ms: 5000,
        status: 'active',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      {
        agent_id: 'recommendation_agent_v1',
        agent_type: 'recommendation_agent',
        name: '推荐Agent',
        description: '推荐内容、资源和产品',
        version: '1.0.0',
        supported_outputs: ['recommendation'],
        required_context: ['profile', 'phenotype_tags'],
        max_concurrent_tasks: 20,
        average_response_time_ms: 1000,
        status: 'active',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    ];

    defaultAgents.forEach(agent => {
      this.agents.set(agent.agent_id, agent);
    });
  }

  /**
   * 注册Agent处理器
   */
  registerHandler(handler: AgentHandler): void {
    this.handlers.set(handler.agent_id, handler);
  }

  /**
   * 创建任务
   */
  createTask(
    agentType: AgentType,
    userId: string,
    context: AgentContext,
    expectedOutput: AgentOutputType,
    options?: {
      priority?: 'low' | 'normal' | 'high' | 'urgent';
      coachId?: string;
      expiresIn?: number;
      callbackUrl?: string;
    }
  ): AgentTask {
    const task: AgentTask = {
      task_id: uuidv4(),
      agent_type: agentType,
      user_id: userId,
      coach_id: options?.coachId,
      priority: options?.priority || 'normal',
      context,
      expected_output: expectedOutput,
      created_at: new Date().toISOString(),
      expires_at: options?.expiresIn
        ? new Date(Date.now() + options.expiresIn).toISOString()
        : undefined,
      callback_url: options?.callbackUrl
    };

    this.tasks.set(task.task_id, task);
    return task;
  }

  /**
   * 执行任务
   */
  async runTask(taskId: string): Promise<AgentOutput> {
    const task = this.tasks.get(taskId);
    if (!task) {
      throw new Error(`Task ${taskId} not found`);
    }

    // 找到对应的Agent
    const agent = this.findAgentByType(task.agent_type);
    if (!agent) {
      throw new Error(`No agent found for type ${task.agent_type}`);
    }

    // 创建执行记录
    const execution: AgentExecutionHistory = {
      execution_id: uuidv4(),
      task_id: taskId,
      agent_id: agent.agent_id,
      status: 'processing',
      input_snapshot: task,
      started_at: new Date().toISOString()
    };
    this.executions.set(execution.execution_id, execution);

    try {
      // 查找处理器
      const handler = this.handlers.get(agent.agent_id);
      let output: AgentOutput;

      if (handler) {
        // 使用注册的处理器
        output = await handler.process(task);
      } else {
        // 使用默认处理（模拟）
        output = await this.defaultProcess(task, agent);
      }

      // 更新执行记录
      execution.status = 'completed';
      execution.output_snapshot = output;
      execution.completed_at = new Date().toISOString();

      return output;
    } catch (error) {
      execution.status = 'failed';
      execution.error = String(error);
      execution.completed_at = new Date().toISOString();
      throw error;
    }
  }

  /**
   * 默认处理（模拟Agent输出）
   */
  private async defaultProcess(task: AgentTask, agent: AgentRegistration): Promise<AgentOutput> {
    // 模拟处理延迟
    await new Promise(resolve => setTimeout(resolve, 100));

    const suggestions = this.generateDefaultSuggestions(task);
    const riskFlags = this.detectRiskFlags(task);

    return {
      task_id: task.task_id,
      agent_id: agent.agent_id,
      agent_type: agent.agent_type,
      output_type: task.expected_output,
      confidence: 0.85,
      suggestions,
      risk_flags: riskFlags,
      need_human_review: riskFlags.length > 0 || task.context.profile.risk_level === 'high',
      review_reason: riskFlags.length > 0 ? '检测到风险标记' : undefined,
      metadata: {
        processing_time_ms: 100,
        model_version: agent.version
      },
      created_at: new Date().toISOString()
    };
  }

  /**
   * 生成默认建议
   */
  private generateDefaultSuggestions(task: AgentTask): AgentSuggestion[] {
    const suggestions: AgentSuggestion[] = [];
    const { profile, behavior_stage } = task.context;

    // 基于行为阶段生成建议
    switch (behavior_stage) {
      case 'precontemplation':
        suggestions.push({
          id: uuidv4(),
          type: 'content',
          priority: 8,
          text: '推荐阅读：了解血糖管理的重要性',
          rationale: '用户处于前意向阶段，需要提升健康意识'
        });
        break;
      case 'contemplation':
        suggestions.push({
          id: uuidv4(),
          type: 'action',
          priority: 7,
          text: '设定一个简单的健康目标',
          rationale: '用户已有改变意愿，需要明确方向'
        });
        break;
      case 'preparation':
        suggestions.push({
          id: uuidv4(),
          type: 'task',
          priority: 8,
          text: '制定本周的饮食计划',
          rationale: '用户准备行动，需要具体计划'
        });
        break;
      case 'action':
        suggestions.push({
          id: uuidv4(),
          type: 'task',
          priority: 9,
          text: '记录今日三餐内容',
          rationale: '用户正在行动，需要跟踪执行'
        });
        suggestions.push({
          id: uuidv4(),
          type: 'action',
          priority: 7,
          text: '餐后步行15分钟',
          rationale: '帮助控制餐后血糖'
        });
        break;
      case 'maintenance':
        suggestions.push({
          id: uuidv4(),
          type: 'content',
          priority: 6,
          text: '分享您的成功经验',
          rationale: '维持阶段强化成就感'
        });
        break;
      default:
        suggestions.push({
          id: uuidv4(),
          type: 'action',
          priority: 5,
          text: '完成今日健康任务',
          rationale: '保持健康习惯'
        });
    }

    // 基于风险等级添加建议
    if (profile.risk_level === 'high') {
      suggestions.push({
        id: uuidv4(),
        type: 'alert',
        priority: 10,
        text: '建议尽快与教练沟通当前状况',
        rationale: '高风险用户需要更多关注'
      });
    }

    return suggestions;
  }

  /**
   * 检测风险标记
   */
  private detectRiskFlags(task: AgentTask): string[] {
    const flags: string[] = [];
    const { profile, device_data } = task.context;

    // 检查设备数据中的异常
    if (device_data) {
      for (const data of device_data) {
        if (data.metric === 'glucose' && data.value > 10) {
          flags.push('high_glucose');
        }
        if (data.metric === 'blood_pressure_systolic' && data.value > 140) {
          flags.push('high_blood_pressure');
        }
        if (data.metric === 'heart_rate' && (data.value < 50 || data.value > 100)) {
          flags.push('abnormal_heart_rate');
        }
      }
    }

    // 检查风险等级
    if (profile.risk_level === 'high') {
      flags.push('high_risk_user');
    }

    return flags;
  }

  /**
   * 查找Agent
   */
  private findAgentByType(agentType: AgentType): AgentRegistration | undefined {
    return Array.from(this.agents.values()).find(
      a => a.agent_type === agentType && a.status === 'active'
    );
  }

  /**
   * 提交反馈
   */
  submitFeedback(
    taskId: string,
    reviewerId: string,
    reviewerRole: string,
    feedbackType: 'accept' | 'reject' | 'modify' | 'rate',
    options?: {
      rating?: number;
      comment?: string;
      modifications?: { original: any; modified: any };
    }
  ): AgentFeedback {
    const task = this.tasks.get(taskId);
    const execution = Array.from(this.executions.values()).find(e => e.task_id === taskId);

    if (!task || !execution) {
      throw new Error(`Task ${taskId} not found`);
    }

    const feedback: AgentFeedback = {
      feedback_id: uuidv4(),
      task_id: taskId,
      agent_id: execution.agent_id,
      user_id: task.user_id,
      reviewer_id: reviewerId,
      reviewer_role: reviewerRole,
      feedback_type: feedbackType,
      rating: options?.rating,
      comment: options?.comment,
      modifications: options?.modifications,
      applied: feedbackType === 'accept',
      timestamp: new Date().toISOString()
    };

    this.feedbacks.set(feedback.feedback_id, feedback);
    execution.feedback = feedback;

    return feedback;
  }

  /**
   * 获取Agent列表
   */
  getAgents(): AgentRegistration[] {
    return Array.from(this.agents.values());
  }

  /**
   * 获取Agent统计
   */
  getAgentStats(agentId: string): AgentStats {
    const executions = Array.from(this.executions.values()).filter(e => e.agent_id === agentId);
    const feedbacks = Array.from(this.feedbacks.values()).filter(f => f.agent_id === agentId);

    const successful = executions.filter(e => e.status === 'completed').length;
    const failed = executions.filter(e => e.status === 'failed').length;
    const ratings = feedbacks.filter(f => f.rating).map(f => f.rating!);
    const acceptCount = feedbacks.filter(f => f.feedback_type === 'accept').length;

    const confidences = executions
      .filter(e => e.output_snapshot)
      .map(e => e.output_snapshot!.confidence);

    const responseTimes = executions
      .filter(e => e.completed_at && e.started_at)
      .map(e => new Date(e.completed_at!).getTime() - new Date(e.started_at).getTime());

    return {
      agent_id: agentId,
      total_tasks: executions.length,
      successful_tasks: successful,
      failed_tasks: failed,
      average_confidence: confidences.length > 0
        ? confidences.reduce((a, b) => a + b, 0) / confidences.length
        : 0,
      average_response_time_ms: responseTimes.length > 0
        ? responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length
        : 0,
      acceptance_rate: feedbacks.length > 0 ? acceptCount / feedbacks.length : 0,
      average_rating: ratings.length > 0
        ? ratings.reduce((a, b) => a + b, 0) / ratings.length
        : 0,
      last_active_at: executions.length > 0
        ? executions.sort((a, b) =>
            new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
          )[0].started_at
        : ''
    };
  }

  /**
   * 获取执行历史
   */
  getExecutionHistory(options?: {
    agentId?: string;
    userId?: string;
    status?: string;
    limit?: number;
  }): AgentExecutionHistory[] {
    let results = Array.from(this.executions.values());

    if (options?.agentId) {
      results = results.filter(e => e.agent_id === options.agentId);
    }
    if (options?.userId) {
      results = results.filter(e => {
        const task = this.tasks.get(e.task_id);
        return task?.user_id === options.userId;
      });
    }
    if (options?.status) {
      results = results.filter(e => e.status === options.status);
    }

    // 按时间倒序
    results.sort((a, b) =>
      new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
    );

    if (options?.limit) {
      results = results.slice(0, options.limit);
    }

    return results;
  }

  /**
   * 获取待审核任务
   */
  getPendingReviews(): AgentExecutionHistory[] {
    return Array.from(this.executions.values()).filter(
      e => e.status === 'completed' &&
           e.output_snapshot?.need_human_review &&
           !e.feedback
    );
  }

  /**
   * 获取任务
   */
  getTask(taskId: string): AgentTask | undefined {
    return this.tasks.get(taskId);
  }

  /**
   * 获取执行结果
   */
  getExecution(executionId: string): AgentExecutionHistory | undefined {
    return this.executions.get(executionId);
  }
}

// 导出单例
export const agentOrchestrator = new AgentOrchestrator();
