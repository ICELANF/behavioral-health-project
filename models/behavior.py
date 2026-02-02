# models/behavior.py
# Pydantic schemas for behavior trace API validation
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class BehaviorTraceSchema(BaseModel):
    """行为长期记忆 — API 层 Pydantic 验证模型"""
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_ui: str = ""
    from_stage: str = "S0"
    to_stage: str = "S0"
    is_transition: bool = False
    belief: float = 0.0
    actions: int = 0
    narrative: str = ""

    def to_orm_dict(self) -> dict:
        """转换为 ORM 字段名（供写入 core.models.BehaviorTrace 使用）"""
        return {
            "user_id": self.user_id,
            "timestamp": self.timestamp,
            "source_ui": self.source_ui,
            "from_stage": self.from_stage,
            "to_stage": self.to_stage,
            "is_transition": self.is_transition,
            "belief_score": self.belief,
            "action_count": self.actions,
            "narrative_sent": self.narrative,
        }

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "U12345",
                "source_ui": "UI-3",
                "from_stage": "S2",
                "to_stage": "S3",
                "is_transition": True,
                "belief": 0.8,
                "actions": 2,
                "narrative": "你已经走过了准备期的考验...",
            }
        }


class WeeklyTrendResponse(BaseModel):
    """周报趋势分析响应"""
    user_id: str
    total_evaluations: int = 0
    transitions: list = []
    belief_trend: Optional[dict] = None
    summary: str = ""
