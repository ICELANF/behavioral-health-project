from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class BloodGlucoseData(BaseModel):
    """血糖数据模型"""
    value: float
    unit: str = "mmol/L"
    timestamp: datetime = Field(default_factory=datetime.now)
    meal_relation: str = "before_meal"

class DecisionContext(BaseModel):
    """决策上下文"""
    user_id: int
    user_name: str
    current_glucose: Optional[BloodGlucoseData] = None
    recent_triggers: List[Any] = []
    behavioral_tags: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.now)

class DecisionOutput(BaseModel):
    """决策输出结果 (对应之前的 InterventionResponse)"""
    strategy_name: str
    content: str
    priority: int
    triggers_addressed: List[str]
    agent_route: str = "default" # 路由信息