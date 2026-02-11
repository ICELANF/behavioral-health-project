# -*- coding: utf-8 -*-
"""
Pydantic 数据模型定义

包含 API 请求/响应模型、任务分解模型、效能评分模型
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
import uuid


# =============================================================================
# 枚举类型
# =============================================================================

class TaskPriority(str, Enum):
    """任务优先级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskCategory(str, Enum):
    """任务类别"""
    MENTAL_HEALTH = "mental_health"      # 心理健康
    NUTRITION = "nutrition"               # 营养饮食
    EXERCISE = "exercise"                 # 运动锻炼
    TCM_WELLNESS = "tcm_wellness"         # 中医养生
    LIFESTYLE = "lifestyle"               # 生活方式
    MEDICAL = "medical"                   # 就医建议


class DifficultyLevel(str, Enum):
    """难度等级"""
    EASY = "easy"           # 简单，无需准备
    MODERATE = "moderate"   # 中等，需要一定准备
    HARD = "hard"           # 困难，需要专业指导或设备


# =============================================================================
# 效能评分模型
# =============================================================================

class EfficacyScore(BaseModel):
    """效能评分模型

    评估每个建议/任务的预期效果
    """
    effectiveness: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="有效性评分 (0-1)，基于循证依据"
    )
    feasibility: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="可行性评分 (0-1)，考虑用户执行难度"
    )
    immediacy: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="即时性评分 (0-1)，见效速度"
    )
    sustainability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="可持续性评分 (0-1)，长期坚持的可能性"
    )
    overall: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="综合评分 (自动计算)"
    )

    def __init__(self, **data):
        super().__init__(**data)
        # 计算综合评分（加权平均）
        if self.overall == 0.0:
            self.overall = round(
                self.effectiveness * 0.35 +
                self.feasibility * 0.30 +
                self.immediacy * 0.15 +
                self.sustainability * 0.20,
                2
            )

    class Config:
        json_schema_extra = {
            "example": {
                "effectiveness": 0.85,
                "feasibility": 0.90,
                "immediacy": 0.60,
                "sustainability": 0.75,
                "overall": 0.80
            }
        }


# =============================================================================
# 原子任务模型
# =============================================================================

class AtomicTask(BaseModel):
    """原子任务模型

    将专家建议拆解为可执行的最小行动单元
    """
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4())[:8],
        description="任务唯一标识"
    )
    title: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="任务标题（简洁动词短语）"
    )
    description: str = Field(
        ...,
        min_length=5,
        max_length=200,
        description="任务详细描述"
    )
    category: TaskCategory = Field(
        ...,
        description="任务所属类别"
    )
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM,
        description="任务优先级"
    )
    difficulty: DifficultyLevel = Field(
        default=DifficultyLevel.EASY,
        description="执行难度"
    )
    duration_minutes: int = Field(
        default=15,
        ge=1,
        le=480,
        description="预计耗时（分钟）"
    )
    frequency: str = Field(
        default="每日一次",
        description="建议执行频率"
    )
    prerequisites: List[str] = Field(
        default_factory=list,
        description="前置条件或准备事项"
    )
    efficacy: Optional[EfficacyScore] = Field(
        default=None,
        description="效能评分"
    )
    expert_source: str = Field(
        default="",
        description="建议来源专家"
    )
    notes: str = Field(
        default="",
        max_length=200,
        description="补充说明或注意事项"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "task001",
                "title": "睡前腹式呼吸练习",
                "description": "躺在床上，将手放在腹部，缓慢吸气4秒让腹部隆起，屏息2秒，缓慢呼气6秒让腹部下沉，重复10次",
                "category": "mental_health",
                "priority": "high",
                "difficulty": "easy",
                "duration_minutes": 10,
                "frequency": "每晚睡前",
                "prerequisites": ["安静的卧室环境"],
                "efficacy": {
                    "effectiveness": 0.80,
                    "feasibility": 0.95,
                    "immediacy": 0.70,
                    "sustainability": 0.85,
                    "overall": 0.83
                },
                "expert_source": "心理咨询师",
                "notes": "如感到头晕请恢复正常呼吸"
            }
        }


# =============================================================================
# 专家信息模型
# =============================================================================

class ExpertInfo(BaseModel):
    """专家信息"""
    id: str = Field(..., description="专家ID")
    name: str = Field(..., description="专家名称")
    description: str = Field(default="", description="专家简介")


# =============================================================================
# Chat API 模型
# =============================================================================

class ChatRequest(BaseModel):
    """聊天请求"""
    session_id: Optional[str] = Field(
        default=None,
        description="会话ID，为空则创建新会话"
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="用户消息"
    )
    expert_id: Optional[str] = Field(
        default=None,
        description="指定专家ID（可选），为空则自动路由"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123",
                "message": "我最近压力很大，晚上总是睡不好",
                "expert_id": None
            }
        }


class ChatResponse(BaseModel):
    """聊天响应"""
    session_id: str = Field(..., description="会话ID")
    response: str = Field(..., description="AI回复内容")
    primary_expert: str = Field(..., description="主要处理专家")
    primary_expert_id: str = Field(..., description="主要专家ID")
    consulted_experts: List[str] = Field(
        default_factory=list,
        description="咨询过的其他专家"
    )
    routing_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="路由置信度"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="响应时间戳"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123",
                "response": "我理解你正在经历压力和睡眠困扰...",
                "primary_expert": "心理咨询师",
                "primary_expert_id": "mental_health",
                "consulted_experts": ["中医养生师"],
                "routing_confidence": 0.85,
                "timestamp": "2024-01-15T10:30:00"
            }
        }


# =============================================================================
# Decompose API 模型
# =============================================================================

class DecomposeRequest(BaseModel):
    """任务分解请求"""
    advice_text: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="需要拆解的建议文本（通常来自专家回复）"
    )
    max_tasks: int = Field(
        default=10,
        ge=1,
        le=20,
        description="最大任务数量"
    )
    include_efficacy: bool = Field(
        default=True,
        description="是否包含效能评分"
    )
    user_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="用户上下文信息（用于个性化拆解）"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "advice_text": "建议您每天进行30分钟的有氧运动，如快走或游泳。同时注意饮食均衡，减少咖啡因摄入，睡前可以做一些放松练习，如深呼吸或冥想。",
                "max_tasks": 5,
                "include_efficacy": True,
                "user_context": {
                    "age": 35,
                    "fitness_level": "beginner"
                }
            }
        }


class DecomposeResponse(BaseModel):
    """任务分解响应"""
    original_advice: str = Field(..., description="原始建议文本")
    tasks: List[AtomicTask] = Field(
        default_factory=list,
        description="拆解后的原子任务列表"
    )
    task_count: int = Field(default=0, description="任务总数")
    categories_summary: Dict[str, int] = Field(
        default_factory=dict,
        description="各类别任务数量统计"
    )
    average_efficacy: Optional[float] = Field(
        default=None,
        description="平均效能评分"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="处理时间戳"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "original_advice": "建议您每天进行30分钟有氧运动...",
                "tasks": [],
                "task_count": 3,
                "categories_summary": {
                    "exercise": 1,
                    "nutrition": 1,
                    "mental_health": 1
                },
                "average_efficacy": 0.78,
                "timestamp": "2024-01-15T10:30:00"
            }
        }


# =============================================================================
# 通用响应模型
# =============================================================================

class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(default="healthy", description="服务状态")
    version: str = Field(default="1.0.0", description="API版本")
    experts_loaded: int = Field(default=0, description="已加载专家数量")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="检查时间"
    )


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(default=None, description="详细信息")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="错误时间"
    )


class ExpertsListResponse(BaseModel):
    """专家列表响应"""
    experts: List[ExpertInfo] = Field(
        default_factory=list,
        description="可用专家列表"
    )
    count: int = Field(default=0, description="专家数量")


# =============================================================================
# 八爪鱼限幅引擎模型 (Octopus Clamping)
# =============================================================================

class WearableData(BaseModel):
    """穿戴设备数据模型"""
    hr: Optional[int] = Field(
        default=None,
        ge=30,
        le=220,
        description="心率 (bpm)"
    )
    steps: Optional[int] = Field(
        default=None,
        ge=0,
        description="今日步数"
    )
    sleep_hours: Optional[float] = Field(
        default=None,
        ge=0,
        le=24,
        description="昨晚睡眠时长 (小时)"
    )
    hrv: Optional[int] = Field(
        default=None,
        ge=0,
        description="心率变异性 (ms)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "hr": 85,
                "steps": 3200,
                "sleep_hours": 6.5,
                "hrv": 45
            }
        }


class ReasoningStepModel(BaseModel):
    """推理步骤模型"""
    phase: str = Field(..., description="阶段名称")
    input: Dict[str, Any] = Field(..., description="输入数据")
    output: Dict[str, Any] = Field(..., description="输出数据")
    decision: str = Field(..., description="决策说明")
    timestamp: str = Field(..., description="时间戳")


class ClampedTask(BaseModel):
    """限幅后的任务"""
    id: int = Field(..., description="任务ID")
    content: str = Field(..., description="任务内容")
    difficulty: int = Field(..., ge=1, le=5, description="难度等级 (1-5)")
    type: str = Field(default="general", description="任务类型")


class OctopusChatRequest(BaseModel):
    """八爪鱼智能对话请求"""
    session_id: Optional[str] = Field(
        default=None,
        description="会话ID，为空则创建新会话"
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="用户消息"
    )
    efficacy_score: int = Field(
        default=50,
        ge=0,
        le=100,
        description="用户效能感分值 (0-100)"
    )
    wearable_data: Optional[WearableData] = Field(
        default=None,
        description="穿戴设备数据（心率、步数等）"
    )
    expert_id: Optional[str] = Field(
        default=None,
        description="指定专家ID（可选），为空则自动路由"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": None,
                "message": "我压力很大",
                "efficacy_score": 10,
                "wearable_data": {"hr": 95},
                "expert_id": None
            }
        }


class OctopusChatResponse(BaseModel):
    """八爪鱼智能对话响应（结构化）"""
    session_id: str = Field(..., description="会话ID")
    status: str = Field(default="success", description="处理状态")

    # 核心输出
    response: str = Field(..., description="AI回复内容（原始专家建议）")
    clamped_tasks: List[ClampedTask] = Field(
        default_factory=list,
        description="限幅后的可执行任务列表"
    )

    # 推理路径
    reasoning_path: List[ReasoningStepModel] = Field(
        default_factory=list,
        description="八爪鱼限幅推理路径"
    )

    # 效能相关
    input_efficacy: int = Field(..., description="输入效能分")
    final_efficacy: int = Field(..., description="调节后效能分")
    clamping_level: str = Field(..., description="限幅等级 (minimal/moderate/full)")

    # 专家信息
    primary_expert: str = Field(..., description="主要处理专家")
    primary_expert_id: str = Field(..., description="主要专家ID")
    consulted_experts: List[str] = Field(
        default_factory=list,
        description="咨询过的其他专家"
    )

    # 外部钩子
    external_hooks: Dict[str, Any] = Field(
        default_factory=dict,
        description="外部触发器（如视频播放、临床警报）"
    )

    # 元数据
    wearable_impact: Optional[Dict[str, Any]] = Field(
        default=None,
        description="穿戴数据影响详情"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="响应时间戳"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123",
                "status": "success",
                "response": "我理解你正在经历压力...",
                "clamped_tasks": [
                    {"id": 1, "content": "进行3次深呼吸", "difficulty": 1, "type": "mental"}
                ],
                "reasoning_path": [
                    {
                        "phase": "WEARABLE_AUDIT",
                        "input": {"hr": 95},
                        "output": {"adjustment": -10},
                        "decision": "心率偏高，轻度降档",
                        "timestamp": "2024-01-15T10:30:00"
                    }
                ],
                "input_efficacy": 10,
                "final_efficacy": 0,
                "clamping_level": "minimal",
                "primary_expert": "心理咨询师",
                "primary_expert_id": "mental_health",
                "consulted_experts": [],
                "external_hooks": {"show_video": True, "clinical_alert": True},
                "wearable_impact": {"applied": True, "adjustment": -10},
                "timestamp": "2024-01-15T10:30:00"
            }
        }


# ══════════════════════════════════════════════
# V3 Schemas (merged from bhp_v3)
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


class ChatMessage(BaseModel):
    role: str = Field(..., pattern=r"^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    user_id: int
    message: str = Field(..., min_length=1, max_length=2000)
    history: list[ChatMessage] | None = None
    force_intent: str | None = None
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


class BatchSubmitRequest(BaseModel):
    user_id: int
    batch_id: str
    answers: dict | list
    duration_seconds: int = 0
    scores: dict | None = None


class BatchRecommendRequest(BaseModel):
    user_id: int


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


class CheckinRequest(BaseModel):
    user_id: int


class TaskCompleteRequest(BaseModel):
    user_id: int
    task_id: str


class KnowledgeLoadFileRequest(BaseModel):
    filepath: str
    doc_type: str = "spec"
    replace: bool = True


class KnowledgeLoadDirRequest(BaseModel):
    dirpath: str
    doc_type_map: dict[str, str] | None = None
