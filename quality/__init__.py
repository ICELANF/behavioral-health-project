"""
行为健康数字平台 - 质量审计模块
Quality Audit Module

[v14-NEW] 全新模块

功能：
- 对AI陪伴响应进行质量评估
- 评分维度：服从度、安全性、共情度、一致性
- 与Trace系统关联，支持全链路追溯
- 异步后台审计，不阻塞前端

与v14关系：
- 与 SafetyAgent 互补：实时检测 vs 事后审计
- 与 TriggerEngine 协同：审计时参考Trigger Tags
- 与 RhythmEngine 协同：考虑节律相位

使用方式：
    from quality import LLMJudge, AuditRequest, get_llm_judge
    
    judge = get_llm_judge()
    result = await judge.evaluate(snapshot_data, response_text, trace_id)
"""

from quality.schema import (
    QualityScore,
    QualityAuditResult,
    AuditGrade,
    AuditRequest,
    BatchAuditRequest,
    determine_grade,
    SAFETY_THRESHOLD,
    CONSISTENCY_THRESHOLD,
    ADHERENCE_THRESHOLD
)

from quality.judge_prompt import (
    build_judge_prompt,
    build_batch_judge_prompt,
    build_safety_focused_prompt,
    build_empathy_focused_prompt,
    TTM_STAGE_DESCRIPTIONS,
    AGENT_ROLE_DESCRIPTIONS
)

from quality.llm_judge import (
    LLMJudge,
    BatchLLMJudge,
    get_llm_judge
)

__all__ = [
    # Schema
    'QualityScore',
    'QualityAuditResult',
    'AuditGrade',
    'AuditRequest',
    'BatchAuditRequest',
    'determine_grade',
    'SAFETY_THRESHOLD',
    'CONSISTENCY_THRESHOLD',
    'ADHERENCE_THRESHOLD',
    
    # Prompt
    'build_judge_prompt',
    'build_batch_judge_prompt',
    'build_safety_focused_prompt',
    'build_empathy_focused_prompt',
    'TTM_STAGE_DESCRIPTIONS',
    'AGENT_ROLE_DESCRIPTIONS',
    
    # Judge
    'LLMJudge',
    'BatchLLMJudge',
    'get_llm_judge',
]

__version__ = "14.0.0"
