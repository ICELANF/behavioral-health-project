"""
BehaviorOS — 行为处方基座 (Behavior Rx)
=========================================
4 款专家 Agent + 行为处方引擎 + Agent 协作编排

组件:
  - BehaviorRxEngine: 三维处方计算 (TTM × BigFive × CAPACITY)
  - BaseExpertAgent: 专家 Agent 抽象基类 (Template Method)
  - 4 Expert Agents: BehaviorCoach, Metabolic, Cardiac, Adherence
  - AgentHandoffService: Agent 交接管理
  - AgentCollaborationOrchestrator: 多 Agent 协作编排
  - RxConflictResolver: 处方冲突消解
  - ExpertAgentRouter: 专家 Agent 路由器
"""
