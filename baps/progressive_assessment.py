"""
#3 渐进式评估 — 171 题分批完成, 自适应推荐
放置: api/baps/progressive_assessment.py

核心问题: 171 题一次性完成导致用户放弃
解决方案:
  - 将 5 套问卷拆为多个 2-3 分钟的评估批次
  - 系统根据用户状态自适应推荐下一批
  - 随时可中断, 随时可恢复, 随时可触发完整评估
"""
from datetime import datetime, timedelta
from enum import Enum as PyEnum
from typing import Any, Optional
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, Boolean, JSON,
    ForeignKey, Index,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import Session

try:
    from database import Base
except ImportError:
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()


# ══════════════════════════════════════════════
# 评估批次定义
# ══════════════════════════════════════════════

class AssessmentStatus(str, PyEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"  # 超过30天未完成


# 5 套问卷拆批: 每批 ≤15 题, 2-3 分钟
ASSESSMENT_BATCHES: list[dict] = [
    # ── 第1轮: 必填 + 快速画像 (约 3 分钟) ──
    {
        "batch_id": "B1_TTM7_CORE",
        "questionnaire": "TTM7",
        "label": "行为阶段快速判定",
        "question_range": (1, 7),       # TTM7 核心 7 题 (每阶段 1 题)
        "question_count": 7,
        "priority": 1,                   # 最高优先
        "required": True,
        "estimated_minutes": 2,
        "unlocks": ["behavioral_stage"],
    },
    {
        "batch_id": "B2_SPI_QUICK",
        "questionnaire": "SPI",
        "label": "成功可能性快评",
        "question_range": "quick_5",     # SPI 快速版 5 题
        "question_count": 5,
        "priority": 2,
        "required": True,
        "estimated_minutes": 1,
        "unlocks": ["readiness_level", "spi_quick"],
    },
    # ── 第2轮: 动因+迫切度 (约 3 分钟) ──
    {
        "batch_id": "B3_SPI_TRIGGERS",
        "questionnaire": "SPI",
        "label": "改变动因评估",
        "question_range": (1, 13),       # SPI Part1 前 13 题: 内在+外部+情绪
        "question_count": 13,
        "priority": 3,
        "required": False,
        "estimated_minutes": 3,
        "unlocks": ["trigger_partial"],
    },
    {
        "batch_id": "B4_SPI_TRIGGERS2",
        "questionnaire": "SPI",
        "label": "改变动因(续)+迫切度",
        "question_range": (14, 25),      # SPI Part1 后 12 题: 认知+能力+社会 + C25
        "question_count": 12,
        "priority": 4,
        "required": False,
        "estimated_minutes": 3,
        "unlocks": ["trigger_full"],
        "depends_on": "B3_SPI_TRIGGERS",
    },
    # ── 第3轮: 心理层次深度 (约 3 分钟) ──
    {
        "batch_id": "B5_SPI_PSY",
        "questionnaire": "SPI",
        "label": "心理状态深度评估",
        "question_range": (26, 45),      # SPI Part2 心理层次 20 题
        "question_count": 20,
        "priority": 5,
        "required": False,
        "estimated_minutes": 3,
        "unlocks": ["readiness_deep", "spi_full_ready"],
        "depends_on": "B4_SPI_TRIGGERS2",
    },
    {
        "batch_id": "B6_SPI_URGENCY",
        "questionnaire": "SPI",
        "label": "迫切度评估",
        "question_range": (46, 50),      # SPI Part3 迫切度 5 题
        "question_count": 5,
        "priority": 6,
        "required": False,
        "estimated_minutes": 1,
        "unlocks": ["spi_full"],
        "depends_on": "B5_SPI_PSY",
    },
    # ── 第4轮: 人格+行为分型 (约 3 分钟) ──
    {
        "batch_id": "B7_BPT6",
        "questionnaire": "BPT6",
        "label": "行为模式分型",
        "question_range": (1, 18),
        "question_count": 18,
        "priority": 7,
        "required": False,
        "estimated_minutes": 3,
        "unlocks": ["behavior_type"],
    },
    # ── 第5轮: 大五人格 (分2批) ──
    {
        "batch_id": "B8_BIG5_PART1",
        "questionnaire": "BIG5",
        "label": "大五人格(上)",
        "question_range": (1, 25),
        "question_count": 25,
        "priority": 8,
        "required": False,
        "estimated_minutes": 3,
        "unlocks": ["big5_partial"],
    },
    {
        "batch_id": "B9_BIG5_PART2",
        "questionnaire": "BIG5",
        "label": "大五人格(下)",
        "question_range": (26, 50),
        "question_count": 25,
        "priority": 9,
        "required": False,
        "estimated_minutes": 3,
        "unlocks": ["big5_full"],
        "depends_on": "B8_BIG5_PART1",
    },
    # ── 第6轮: 改变潜力 (分2批) ──
    {
        "batch_id": "B10_CAPACITY_PART1",
        "questionnaire": "CAPACITY",
        "label": "改变潜力(上)",
        "question_range": (1, 16),
        "question_count": 16,
        "priority": 10,
        "required": False,
        "estimated_minutes": 3,
        "unlocks": ["capacity_partial"],
    },
    {
        "batch_id": "B11_CAPACITY_PART2",
        "questionnaire": "CAPACITY",
        "label": "改变潜力(下)",
        "question_range": (17, 32),
        "question_count": 16,
        "priority": 11,
        "required": False,
        "estimated_minutes": 3,
        "unlocks": ["capacity_full"],
        "depends_on": "B10_CAPACITY_PART1",
    },
    # ── 第7轮: TTM7 深度 ──
    {
        "batch_id": "B12_TTM7_DEEP",
        "questionnaire": "TTM7",
        "label": "行为阶段深度确认",
        "question_range": (8, 21),       # TTM7 剩余 14 题
        "question_count": 14,
        "priority": 12,
        "required": False,
        "estimated_minutes": 3,
        "unlocks": ["stage_deep"],
        "depends_on": "B1_TTM7_CORE",
    },
]

# batch_id → index 快查
_BATCH_MAP = {b["batch_id"]: i for i, b in enumerate(ASSESSMENT_BATCHES)}

# 总题数: 7+5+13+12+20+5+18+25+25+16+16+14 = 176 (含快速版5题重叠) → 实际 171 独立题


# ══════════════════════════════════════════════
# 数据表: 评估会话
# ══════════════════════════════════════════════

class AssessmentSession(Base):
    """用户评估会话 — 跨批次持久化"""
    __tablename__ = "assessment_sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(15), nullable=False, default="in_progress")
    # 进度
    completed_batches = Column(JSON, default=list)      # ["B1_TTM7_CORE", "B2_SPI_QUICK"]
    pending_batches = Column(JSON, default=list)
    total_questions_answered = Column(Integer, default=0)
    total_questions = Column(Integer, default=176)
    # 已累积的部分结果
    partial_results = Column(JSON, default=dict)         # {"behavioral_stage": "S3", "spi_quick": 63}
    # 时间
    started_at = Column(DateTime, server_default=func.now())
    last_activity = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
    expires_at = Column(DateTime)                        # started_at + 30 天
    __table_args__ = (
        Index("ix_assess_session_user", "user_id", "status"),
    )


class BatchAnswer(Base):
    """单批次答题记录"""
    __tablename__ = "batch_answers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("assessment_sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    batch_id = Column(String(30), nullable=False)
    questionnaire = Column(String(10), nullable=False)
    answers = Column(JSON, nullable=False)     # 原始答案
    scores = Column(JSON)                       # 即时评分
    duration_seconds = Column(Integer)          # 耗时
    created_at = Column(DateTime, server_default=func.now())
    __table_args__ = (
        Index("ix_batch_session", "session_id", "batch_id"),
    )


# ══════════════════════════════════════════════
# 自适应推荐引擎
# ══════════════════════════════════════════════

class AdaptiveRecommender:
    """根据用户当前状态推荐下一个最优评估批次"""

    @staticmethod
    def recommend_next(
        completed: list[str],
        partial_results: dict,
        user_stage: str | None = None,
    ) -> list[dict]:
        """
        返回推荐批次列表 (按优先级排序, 最多3个选项)

        自适应规则:
        1. 必填批次未完成 → 最高优先
        2. 依赖已满足的批次 → 按 priority 排序
        3. 根据已知阶段跳过不必要的深度评估:
           - S0-S1 用户: 优先完成 SPI (动因+迫切度重要)
           - S4-S6 用户: 可跳过深度 TTM7, 优先 BIG5+CAPACITY
        """
        completed_set = set(completed)
        candidates = []

        for batch in ASSESSMENT_BATCHES:
            bid = batch["batch_id"]
            if bid in completed_set:
                continue

            # 检查依赖
            dep = batch.get("depends_on")
            if dep and dep not in completed_set:
                continue

            # 计算自适应优先级调整
            adjusted_priority = batch["priority"]

            if user_stage:
                if user_stage in ("S0", "S1"):
                    # 早期阶段: SPI 动因更重要
                    if batch["questionnaire"] == "SPI":
                        adjusted_priority -= 2
                elif user_stage in ("S4", "S5", "S6"):
                    # 高阶用户: 人格和能力更重要
                    if batch["questionnaire"] in ("BIG5", "CAPACITY"):
                        adjusted_priority -= 2
                    if bid == "B12_TTM7_DEEP":
                        adjusted_priority += 5  # 降低优先级

            candidates.append({
                "batch_id": bid,
                "label": batch["label"],
                "questionnaire": batch["questionnaire"],
                "question_count": batch["question_count"],
                "estimated_minutes": batch["estimated_minutes"],
                "required": batch["required"],
                "priority": adjusted_priority,
            })

        candidates.sort(key=lambda x: x["priority"])
        return candidates[:3]

    @staticmethod
    def get_completion_summary(completed: list[str]) -> dict:
        """返回当前评估完成度"""
        answered = sum(
            ASSESSMENT_BATCHES[_BATCH_MAP[bid]]["question_count"]
            for bid in completed
            if bid in _BATCH_MAP
        )
        total = sum(b["question_count"] for b in ASSESSMENT_BATCHES)
        questionnaires_done = set()
        for bid in completed:
            if bid in _BATCH_MAP:
                questionnaires_done.add(ASSESSMENT_BATCHES[_BATCH_MAP[bid]]["questionnaire"])

        # 判断哪些问卷完整
        full = set()
        if {"B1_TTM7_CORE", "B12_TTM7_DEEP"}.issubset(completed):
            full.add("TTM7")
        if {"B3_SPI_TRIGGERS", "B4_SPI_TRIGGERS2", "B5_SPI_PSY", "B6_SPI_URGENCY"}.issubset(completed):
            full.add("SPI")
        if "B7_BPT6" in completed:
            full.add("BPT6")
        if {"B8_BIG5_PART1", "B9_BIG5_PART2"}.issubset(completed):
            full.add("BIG5")
        if {"B10_CAPACITY_PART1", "B11_CAPACITY_PART2"}.issubset(completed):
            full.add("CAPACITY")

        return {
            "questions_answered": answered,
            "questions_total": total,
            "progress_percent": round(answered / total * 100, 1),
            "batches_completed": len(completed),
            "batches_total": len(ASSESSMENT_BATCHES),
            "questionnaires_touched": sorted(questionnaires_done),
            "questionnaires_complete": sorted(full),
            "can_generate_profile": "B1_TTM7_CORE" in completed and "B2_SPI_QUICK" in completed,
            "full_assessment_complete": full == {"TTM7", "SPI", "BPT6", "BIG5", "CAPACITY"},
        }


# ══════════════════════════════════════════════
# 会话管理
# ══════════════════════════════════════════════

def get_or_create_session(db: Session, user_id: int) -> AssessmentSession:
    """获取活跃会话或创建新会话"""
    session = (
        db.query(AssessmentSession)
        .filter(
            AssessmentSession.user_id == user_id,
            AssessmentSession.status == "in_progress",
        )
        .first()
    )

    if session:
        # 检查过期
        if session.expires_at and datetime.now() > session.expires_at:
            session.status = "expired"
            db.commit()
        else:
            return session

    # 创建新会话
    now = datetime.now()
    session = AssessmentSession(
        user_id=user_id,
        status="in_progress",
        completed_batches=[],
        pending_batches=[b["batch_id"] for b in ASSESSMENT_BATCHES],
        total_questions_answered=0,
        partial_results={},
        started_at=now,
        last_activity=now,
        expires_at=now + timedelta(days=30),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def submit_batch(
    db: Session,
    user_id: int,
    batch_id: str,
    answers: dict | list,
    duration_seconds: int = 0,
    scores: dict | None = None,
) -> dict:
    """提交一个批次的答案"""
    session = get_or_create_session(db, user_id)

    if batch_id not in _BATCH_MAP:
        raise ValueError(f"Unknown batch: {batch_id}")

    batch_def = ASSESSMENT_BATCHES[_BATCH_MAP[batch_id]]

    # 保存答案
    ba = BatchAnswer(
        session_id=session.id,
        user_id=user_id,
        batch_id=batch_id,
        questionnaire=batch_def["questionnaire"],
        answers=answers,
        scores=scores,
        duration_seconds=duration_seconds,
    )
    db.add(ba)

    # 更新会话进度
    completed = list(session.completed_batches or [])
    if batch_id not in completed:
        completed.append(batch_id)
    session.completed_batches = completed

    pending = list(session.pending_batches or [])
    if batch_id in pending:
        pending.remove(batch_id)
    session.pending_batches = pending

    session.total_questions_answered = (session.total_questions_answered or 0) + batch_def["question_count"]
    session.last_activity = datetime.now()

    # 更新 partial_results
    pr = dict(session.partial_results or {})
    for unlock in batch_def.get("unlocks", []):
        pr[unlock] = True
    if scores:
        pr.update(scores)
    session.partial_results = pr

    # 检查完成
    summary = AdaptiveRecommender.get_completion_summary(completed)
    if summary["full_assessment_complete"]:
        session.status = "completed"
        session.completed_at = datetime.now()

    db.commit()

    # 推荐下一批
    user_stage = pr.get("behavioral_stage")
    recommendations = AdaptiveRecommender.recommend_next(completed, pr, user_stage)

    return {
        "batch_id": batch_id,
        "saved": True,
        "summary": summary,
        "next_recommended": recommendations,
    }
