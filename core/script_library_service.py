"""
V4.0 Script Library Service — 话术库 (MEU-32)

ScriptLibrary: Curated conversation scripts for coaches
  - Organized by stage (S0-S5) + domain + scenario
  - Used by CoachCopilot Agent for evidence-based dialogue
  - CRUD + search + domain tagging
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_

from core.models import Base, User
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON, Boolean

logger = logging.getLogger(__name__)


class ScriptTemplate(Base):
    """话术模板"""
    __tablename__ = "script_templates"

    id = Column(Integer, primary_key=True, index=True)

    # Classification
    title = Column(String(200), nullable=False)
    domain = Column(String(30), nullable=False, index=True)   # nutrition/sleep/emotion/...
    stage = Column(String(30), nullable=False, index=True)     # s0-s5 or "any"
    scenario = Column(String(50), nullable=False, index=True)  # e.g., "resistance", "relapse", "motivation"
    agency_mode = Column(String(20), default="any")            # passive/transitional/active/any

    # Content
    opening_line = Column(Text, nullable=False)       # 开场白
    key_questions = Column(JSON, default=[])           # 关键提问列表
    response_templates = Column(JSON, default=[])      # 回应模板
    closing_line = Column(Text, nullable=True)        # 结束语
    notes = Column(Text, nullable=True)                # 使用注意事项

    # Metadata
    tags = Column(JSON, default=[])
    difficulty = Column(String(20), default="basic")   # basic/intermediate/advanced
    evidence_source = Column(String(200), nullable=True)  # 证据来源
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)

    # Author
    created_by = Column(Integer, nullable=True)        # user_id of author
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.utcnow)


# ── Built-in Script Seeds ───────────────────────

SCRIPT_SEEDS = [
    {
        "title": "S0 首次对话 — 建立安全感",
        "domain": "general",
        "stage": "s0_authorization",
        "scenario": "first_meeting",
        "agency_mode": "passive",
        "opening_line": "你好, 我是你的健康伙伴。在我们开始之前, 我想先听听你——是什么让你来到这里?",
        "key_questions": [
            "你现在最关心的健康问题是什么?",
            "你之前有没有尝试过改变? 那次经历如何?",
            "你希望我们的对话是什么样的?",
        ],
        "response_templates": [
            "谢谢你愿意分享。我听到了..., 这很重要。",
            "你的感受完全可以理解。很多人在这个阶段也有类似的想法。",
        ],
        "closing_line": "今天我们先到这里。我会在这里, 随时可以聊。",
        "difficulty": "basic",
        "evidence_source": "MI (Motivational Interviewing)",
        "tags": ["MI", "rapport", "safety"],
    },
    {
        "title": "S1 行为觉察 — 引导数据观察",
        "domain": "general",
        "stage": "s1_awareness",
        "scenario": "data_awareness",
        "agency_mode": "passive",
        "opening_line": "你这周的健康数据我看到了一些有趣的地方。你想不想一起看看?",
        "key_questions": [
            "你觉得哪个数据最让你意外?",
            "你注意到了什么模式或规律吗?",
            "如果这个数据是一个故事, 它在告诉你什么?",
        ],
        "response_templates": [
            "你观察得很仔细! 这个模式确实值得关注。",
            "每个人的数据都有自己的'语言', 你正在学会听懂它。",
        ],
        "closing_line": "这周试着留意一下这个模式, 下次我们再聊聊你的发现。",
        "difficulty": "basic",
        "evidence_source": "Health Coaching (CHES Framework)",
        "tags": ["data", "awareness", "observation"],
    },
    {
        "title": "S2 抗拒处理 — 动机式访谈",
        "domain": "general",
        "stage": "s2_trial",
        "scenario": "resistance",
        "agency_mode": "passive",
        "opening_line": "我感觉到你现在可能有些犹豫。这完全正常, 我们可以慢慢来。",
        "key_questions": [
            "如果改变的好处有10分, 你觉得现在能打几分?",
            "什么在阻碍你迈出下一步?",
            "如果不做任何改变, 半年后你觉得会怎样?",
        ],
        "response_templates": [
            "你说到了一个很关键的点。改变确实不容易, 但你已经在思考了。",
            "我听到你说'但是...'——这个'但是'后面通常藏着很重要的东西。",
        ],
        "closing_line": "没有人能代替你做决定。当你准备好了, 我在这里。",
        "difficulty": "intermediate",
        "evidence_source": "MI - Rolling with Resistance",
        "tags": ["MI", "resistance", "ambivalence"],
    },
    {
        "title": "S3 行为巩固 — 成功回顾",
        "domain": "general",
        "stage": "s3_pathway",
        "scenario": "success_review",
        "agency_mode": "transitional",
        "opening_line": "恭喜你! 你已经坚持了一段时间了。让我们一起回顾一下你的成功经验。",
        "key_questions": [
            "这段时间你做了什么不同的事?",
            "什么帮助你坚持下来了?",
            "你觉得自己和开始时有什么不一样了?",
        ],
        "response_templates": [
            "你总结得很好。这些'成功因素'就是你的独特配方。",
            "每个人的改变之路都不一样, 你找到了属于自己的方式。",
        ],
        "closing_line": "接下来, 我们可以一起看看怎样让这些好习惯变得更'自动'。",
        "difficulty": "intermediate",
        "evidence_source": "Solution-Focused Brief Therapy",
        "tags": ["consolidation", "strengths", "SFBT"],
    },
    {
        "title": "S4 复发预防 — 预案制定",
        "domain": "general",
        "stage": "s4_internalization",
        "scenario": "relapse_prevention",
        "agency_mode": "transitional",
        "opening_line": "你已经走得很远了。现在让我们一起为可能的挑战做些准备。",
        "key_questions": [
            "你觉得什么情况最可能让你'退回'以前的习惯?",
            "如果真的发生了, 你打算怎么处理?",
            "你身边谁可以在那个时候支持你?",
        ],
        "response_templates": [
            "有预案不是因为你会失败, 而是因为你已经足够成熟来面对挑战了。",
            "偶尔的波动不是失败, 而是成长过程的一部分。",
        ],
        "closing_line": "记住, 即使有波动, 你已经拥有了很多内在资源。你比你想象的更有能力。",
        "difficulty": "advanced",
        "evidence_source": "Relapse Prevention Model (Marlatt & Gordon)",
        "tags": ["relapse", "prevention", "coping"],
    },
]


class ScriptLibraryService:
    """话术库服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_script(self, data: dict, created_by: int = None) -> dict:
        """创建话术模板"""
        script = ScriptTemplate(
            title=data["title"],
            domain=data.get("domain", "general"),
            stage=data.get("stage", "any"),
            scenario=data.get("scenario", "general"),
            agency_mode=data.get("agency_mode", "any"),
            opening_line=data["opening_line"],
            key_questions=data.get("key_questions", []),
            response_templates=data.get("response_templates", []),
            closing_line=data.get("closing_line"),
            notes=data.get("notes"),
            tags=data.get("tags", []),
            difficulty=data.get("difficulty", "basic"),
            evidence_source=data.get("evidence_source"),
            created_by=created_by,
        )
        self.db.add(script)
        self.db.flush()
        return self._to_dict(script)

    def list_scripts(
        self,
        domain: str = None,
        stage: str = None,
        scenario: str = None,
        agency_mode: str = None,
        search: str = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """搜索话术"""
        q = self.db.query(ScriptTemplate).filter(ScriptTemplate.is_active == True)
        if domain:
            q = q.filter(ScriptTemplate.domain == domain)
        if stage:
            q = q.filter(or_(ScriptTemplate.stage == stage, ScriptTemplate.stage == "any"))
        if scenario:
            q = q.filter(ScriptTemplate.scenario == scenario)
        if agency_mode:
            q = q.filter(or_(
                ScriptTemplate.agency_mode == agency_mode,
                ScriptTemplate.agency_mode == "any",
            ))
        if search:
            q = q.filter(or_(
                ScriptTemplate.title.ilike(f"%{search}%"),
                ScriptTemplate.opening_line.ilike(f"%{search}%"),
            ))

        total = q.count()
        scripts = q.order_by(desc(ScriptTemplate.usage_count)).offset(offset).limit(limit).all()

        return {
            "total": total,
            "scripts": [self._to_dict(s) for s in scripts],
        }

    def get_script(self, script_id: int) -> dict:
        """获取单条话术"""
        s = self.db.query(ScriptTemplate).filter(ScriptTemplate.id == script_id).first()
        if not s:
            return {"error": "话术不存在"}
        # Increment usage
        s.usage_count = (s.usage_count or 0) + 1
        self.db.flush()
        return self._to_dict(s)

    def get_domains(self) -> List[str]:
        """获取所有领域"""
        results = self.db.query(ScriptTemplate.domain).distinct().all()
        return [r[0] for r in results]

    def get_scenarios(self) -> List[str]:
        """获取所有场景"""
        results = self.db.query(ScriptTemplate.scenario).distinct().all()
        return [r[0] for r in results]

    def seed_scripts(self) -> int:
        """种子话术初始化"""
        count = 0
        for seed in SCRIPT_SEEDS:
            existing = self.db.query(ScriptTemplate).filter(
                ScriptTemplate.title == seed["title"]
            ).first()
            if not existing:
                self.create_script(seed)
                count += 1
        self.db.flush()
        return count

    def _to_dict(self, s: ScriptTemplate) -> dict:
        return {
            "id": s.id,
            "title": s.title,
            "domain": s.domain,
            "stage": s.stage,
            "scenario": s.scenario,
            "agency_mode": s.agency_mode,
            "opening_line": s.opening_line,
            "key_questions": s.key_questions or [],
            "response_templates": s.response_templates or [],
            "closing_line": s.closing_line,
            "notes": s.notes,
            "tags": s.tags or [],
            "difficulty": s.difficulty,
            "evidence_source": s.evidence_source,
            "usage_count": s.usage_count or 0,
            "is_active": s.is_active,
            "created_at": str(s.created_at) if s.created_at else None,
        }
