"""
Professional Agent 请求Schema
"""
from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    agent_name: str = Field(..., description="Agent名称")
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None
    context: Optional[dict] = None


class AgentListRequest(BaseModel):
    domain: Optional[str] = None
    page: int = 1
    page_size: int = 20
