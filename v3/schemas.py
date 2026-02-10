"""
Pydantic 请求/响应模型
放置: api/schemas.py
"""
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


# ══════════════════════════════════════════════
# 通用
# ══════════════════════════════════════════════

class APIResponse(BaseModel):
    """统一响应包装"""
    ok: bool = True
    data: Any = None
    message: str = ""


class ErrorResponse(BaseModel):
    ok: bool = False
    message: str
    detail: str = ""


# ══════════════════════════════════════════════
# 诊断管道
# ══════════════════════════════════════════════

class DiagnosticMinimalRequest(BaseModel):
    """最小启动 (12 题)"""
    user_id: int
    behavioral_stage: str = Field(..., pattern=r"^S[0-6]$", description="TTM 行为阶段 S0-S6")
    trigger_strength: int = Field(5, ge=1, le=10)
    psychological_level: int = Field(3, ge=1, le=5)
    capability_resource: int = Field(5, ge=1, le=10)
    social_support: int = Field(5, ge=1, le=10)
    urgency_val: int = Field(5, ge=1, le=10)


class Layer1Input(BaseModel):
    behavioral_stage: str = Field(..., pattern=r"^S[0-6]$")
    bpt_type: str = "mixed"
    big5_profile: dict | None = None
    capacity_scores: dict | None = None
    health_competency_answers: dict | None = None


class Layer2Input(BaseModel):
    # 完整版
    part1_scores: dict[str, int] | None = None
    part2_scores: list[int] | None = None
    part3_scores: dict[str, int] | None = None
    # 快速版
    trigger_strength: int | None = None
    psychological_level: int | None = None
    capability_resource: int | None = None
    social_support: int | None = None
    urgency_val: int | None = None


class Layer3Input(BaseModel):
    hbm_answers: dict[str, list[int]] | None = None
    attribution: str = "behavioral"
    time_orient: str = "future"
    comb_answers: dict | None = None
    se_answers: dict[str, int] | None = None
    support_answers: dict | None = None
    obstacle_answers: dict | None = None
    obstacle_version: str = "v2"


class DiagnosticFullRequest(BaseModel):
    """完整管道"""
    user_id: int
    layer1: Layer1Input
    layer2: Layer2Input
    layer3: Layer3Input | None = None
    growth_level: str = "G0"
    streak_days: int = 0
    cultivation_stage: str = "startup"


# ══════════════════════════════════════════════
# Coach 对话
# ══════════════════════════════════════════════

class ChatMessage(BaseModel):
    role: str = Field(..., pattern=r"^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    user_id: int
    message: str = Field(..., min_length=1, max_length=2000)
    history: list[ChatMessage] | None = None
    force_intent: str | None = None
    # 用户上下文 (可选, 优先从 DB 读取)
    behavioral_stage: str | None = None
    readiness_level: str | None = None
    spi_score: float | None = None


class ChatResponse(BaseModel):
    answer: str
    intent: str
    model: str
    sources: list[dict] = []
    latency_ms: int = 0
    tokens: int = 0
    cost_yuan: float = 0.0


# ══════════════════════════════════════════════
# RAG 知识问答
# ══════════════════════════════════════════════

class KnowledgeQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    doc_type: str | None = None
    top_k: int = Field(5, ge=1, le=20)


class KnowledgeSearchResult(BaseModel):
    chunk_id: str
    text: str
    score: float
    source: str
    section: str = ""
    doc_type: str = ""


class PrescriptionRequest(BaseModel):
    """RAG 增强处方生成"""
    user_id: int
    behavioral_stage: str
    readiness_level: str = "L1"
    spi_score: float = 0.0
    bpt_type: str = "mixed"
    top_obstacles: list[str] = []
    dominant_causes: list[str] = []


# ══════════════════════════════════════════════
# 渐进式评估
# ══════════════════════════════════════════════

class BatchSubmitRequest(BaseModel):
    user_id: int
    batch_id: str
    answers: dict | list
    duration_seconds: int = 0
    scores: dict | None = None


class BatchRecommendRequest(BaseModel):
    user_id: int


# ══════════════════════════════════════════════
# 效果追踪
# ══════════════════════════════════════════════

class DailyOutcomeRequest(BaseModel):
    user_id: int
    date: datetime | None = None
    tasks_assigned: int = Field(..., ge=0)
    tasks_completed: int = Field(..., ge=0)
    tasks_skipped: int = Field(0, ge=0)
    streak_days: int = Field(0, ge=0)
    user_mood: int | None = Field(None, ge=1, le=5)
    user_difficulty: int | None = Field(None, ge=1, le=5)
    user_notes: str = ""
    cultivation_stage: str = "startup"
    spi_before: float | None = None
    spi_after: float | None = None


class WeeklyReviewRequest(BaseModel):
    user_id: int
    end_date: datetime | None = None


# ══════════════════════════════════════════════
# 积分激励
# ══════════════════════════════════════════════

class CheckinRequest(BaseModel):
    user_id: int


class TaskCompleteRequest(BaseModel):
    user_id: int
    task_id: str


# ══════════════════════════════════════════════
# 知识库管理 (Admin)
# ══════════════════════════════════════════════

class KnowledgeLoadFileRequest(BaseModel):
    filepath: str
    doc_type: str = "spec"
    replace: bool = True


class KnowledgeLoadDirRequest(BaseModel):
    dirpath: str
    doc_type_map: dict[str, str] | None = None
