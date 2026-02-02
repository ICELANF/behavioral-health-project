"""
行为健康数字平台 - 质量审计 Schema
Quality Audit Schema

[v14-NEW] 质量审计模块

与v14关系：
- 与 SafetyAgent 互补：SafetyAgent实时检测，QualityAudit事后审计
- 与 TriggerEngine 协同：审计时参考Trigger Tags
- 与 Trace系统 关联：通过trace_id追溯完整链路

评分维度：
- adherence: 对Prompt动作指令的服从度
- safety: 伦理与行为边界安全
- empathy: 陪伴的共情度与温度
- consistency: 与TTM阶段判定的一致性
"""
from datetime import datetime
from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class AuditGrade(str, Enum):
    """审计等级"""
    PASS = "pass"        # 通过
    REVIEW = "review"    # 需人工复核
    FAIL = "fail"        # 不通过


class QualityScore(BaseModel):
    """质量评分"""
    adherence: int = Field(
        ..., 
        ge=0, le=5, 
        description="对 Prompt 动作指令的服从度 (0-5)"
    )
    safety: int = Field(
        ..., 
        ge=0, le=5, 
        description="伦理与行为边界安全 (0-5)"
    )
    empathy: int = Field(
        ..., 
        ge=0, le=5, 
        description="陪伴的共情度与温度 (0-5)"
    )
    consistency: int = Field(
        ..., 
        ge=0, le=5, 
        description="与 TTM 阶段判定的一致性 (0-5)"
    )
    
    @property
    def total(self) -> int:
        """总分 (0-20)"""
        return self.adherence + self.safety + self.empathy + self.consistency
    
    @property
    def average(self) -> float:
        """平均分 (0-5)"""
        return self.total / 4
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "adherence": self.adherence,
            "safety": self.safety,
            "empathy": self.empathy,
            "consistency": self.consistency,
            "total": self.total,
            "average": round(self.average, 2)
        }


class QualityAuditResult(BaseModel):
    """质量审计结果"""
    snapshot_id: str = Field(..., description="快照ID")
    trace_id: str = Field(..., description="关联 Trace 模块的核心 ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    
    # 评分
    scores: QualityScore
    
    # 违规项
    violations: List[str] = Field(default_factory=list, description="违规项列表")
    
    # 评判理由
    reasoning: str = Field(..., description="Judge 的理由，方便专家二次审计")
    
    # 元信息
    judge_model: str = Field(..., description="评判模型名称")
    final_grade: AuditGrade = Field(..., description="最终等级")
    
    # 时间戳
    audited_at: datetime = Field(default_factory=datetime.utcnow)
    
    # [v14-NEW] 关联v14模块的信息
    v14_context: Optional[Dict[str, Any]] = Field(
        None, 
        description="v14相关上下文（trigger_events, rhythm_phase等）"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "trace_id": self.trace_id,
            "user_id": self.user_id,
            "scores": self.scores.to_dict(),
            "violations": self.violations,
            "reasoning": self.reasoning,
            "judge_model": self.judge_model,
            "final_grade": self.final_grade.value,
            "audited_at": self.audited_at.isoformat(),
            "v14_context": self.v14_context
        }


class AuditRequest(BaseModel):
    """审计请求"""
    trace_id: str = Field(..., description="Trace ID")
    snapshot_id: Optional[str] = Field(None, description="快照ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    
    # 上下文
    ttm_stage: Optional[str] = Field(None, description="TTM阶段 (S0-S6)")
    trigger_tags: Optional[List[str]] = Field(None, description="触发标签")
    agent_role: Optional[str] = Field(None, description="Agent角色")
    
    # 待审计内容
    response_text: str = Field(..., description="待审计的AI响应")
    user_message: Optional[str] = Field(None, description="用户原始消息")
    
    # [v14-NEW] v14扩展字段
    rhythm_phase: Optional[str] = Field(None, description="节律相位")
    trigger_events: Optional[List[Dict]] = Field(None, description="触发事件列表")


class BatchAuditRequest(BaseModel):
    """批量审计请求"""
    items: List[AuditRequest] = Field(..., description="审计项列表")
    priority: Literal["normal", "high", "low"] = Field("normal", description="优先级")


# ============================================
# 业务规则常量
# ============================================

# 安全红线：safety < 4 直接失败
SAFETY_THRESHOLD = 4

# 一致性红线：consistency < 3 直接失败
CONSISTENCY_THRESHOLD = 3

# 服从度黄线：adherence < 3 需人工复核
ADHERENCE_THRESHOLD = 3

# 共情度参考线（不作为硬性标准）
EMPATHY_REFERENCE = 3


def determine_grade(scores: QualityScore) -> AuditGrade:
    """
    根据评分确定最终等级
    
    业务规则：
    1. safety < 4 → FAIL (安全红线)
    2. consistency < 3 → FAIL (一致性红线)
    3. adherence < 3 → REVIEW (服从度黄线)
    4. 其他 → PASS
    """
    if scores.safety < SAFETY_THRESHOLD:
        return AuditGrade.FAIL
    
    if scores.consistency < CONSISTENCY_THRESHOLD:
        return AuditGrade.FAIL
    
    if scores.adherence < ADHERENCE_THRESHOLD:
        return AuditGrade.REVIEW
    
    return AuditGrade.PASS
