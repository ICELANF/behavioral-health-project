"""
Assistant Agent 响应Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, Any


class ChatResponse(BaseModel):
    agent: str
    domain: str
    content: str
    layer: str = "assistant"
    safety_intercepted: bool = False
    metadata: Optional[dict] = None
