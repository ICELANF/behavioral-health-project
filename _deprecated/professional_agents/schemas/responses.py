"""
Professional Agent 响应Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, Any


class ChatResponse(BaseModel):
    agent: str
    domain: str
    content: str
    layer: str = "professional"
    safety_intercepted: bool = False
    coach_reviewed: bool = Field(False, description="教练是否已审核")
    review_note: Optional[str] = None
    metadata: Optional[dict] = None
