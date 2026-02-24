"""
XZBStyleAdapter — 专家风格转换层
将 LLM 原始输出转换为专家特有语言风格

风格维度: conclusion_first / certainty_level / emotional_warmth / tcm_weight / analogy_density
"""
from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class StyleProfile:
    expert_id: str
    vocabulary_profile: Dict[str, float] = field(default_factory=dict)
    conclusion_first: bool = True
    certainty_level: str = "medium"
    emotional_warmth: float = 0.5
    tcm_weight: float = 0.5
    analogy_density: str = "occasional"


# 预设风格模板 (5种)
PRESET_PROFILES: Dict[str, StyleProfile] = {
    "rigorous": StyleProfile(
        expert_id="preset_rigorous", conclusion_first=True,
        certainty_level="high", emotional_warmth=0.1, tcm_weight=0.1, analogy_density="none",
    ),
    "warm_guide": StyleProfile(
        expert_id="preset_warm_guide", conclusion_first=False,
        certainty_level="medium", emotional_warmth=0.9, tcm_weight=0.3, analogy_density="frequent",
    ),
    "tcm_master": StyleProfile(
        expert_id="preset_tcm_master", conclusion_first=False,
        certainty_level="medium", emotional_warmth=0.7, tcm_weight=0.9, analogy_density="occasional",
    ),
    "evidence_based": StyleProfile(
        expert_id="preset_evidence_based", conclusion_first=True,
        certainty_level="high", emotional_warmth=0.3, tcm_weight=0.2, analogy_density="none",
    ),
    "lifestyle_coach": StyleProfile(
        expert_id="preset_lifestyle_coach", conclusion_first=False,
        certainty_level="medium", emotional_warmth=0.8, tcm_weight=0.2, analogy_density="frequent",
    ),
}

CERTAINTY_REPLACEMENTS = {
    "low":    {"建议": "可以考虑", "应该": "可以尝试", "必须": "可以考虑"},
    "medium": {"应当": "建议", "必须": "建议"},
    "high":   {"可以考虑": "建议", "不妨": "建议"},
}


class XZBStyleAdapter:
    """风格转换主类 (同步版)"""

    def __init__(self, llm_service=None):
        self.llm_service = llm_service
        self._profile_cache: Dict[str, StyleProfile] = {}

    def transform_sync(
        self, raw_text: str, expert_id: str,
        evidence_tier: Optional[str] = None, db: Session = None,
    ) -> str:
        profile = self._get_profile(expert_id, db)
        return self._apply_style(raw_text, profile, evidence_tier)

    def invalidate_cache(self, expert_id: str):
        self._profile_cache.pop(expert_id, None)

    def _apply_style(self, text: str, profile: StyleProfile, evidence_tier: str = None) -> str:
        result = text
        if profile.conclusion_first:
            result = self._reorder_conclusion_first(result)
        result = self._apply_certainty(result, profile.certainty_level)
        result = self._apply_warmth(result, profile)
        if profile.tcm_weight > 0.6:
            result = self._add_tcm_flavor(result, profile.tcm_weight)
        return result

    def _reorder_conclusion_first(self, text: str) -> str:
        sentences = re.split(r'[。！？]', text)
        if len(sentences) <= 2:
            return text
        conclusion = sentences[-2].strip()
        rest = '。'.join(sentences[:-2])
        return f"{conclusion}。{rest}。" if conclusion else text

    def _apply_certainty(self, text: str, level: str) -> str:
        for old, new in CERTAINTY_REPLACEMENTS.get(level, {}).items():
            text = text.replace(old, new)
        return text

    def _apply_warmth(self, text: str, profile: StyleProfile) -> str:
        if profile.emotional_warmth > 0.6:
            text = text.replace("患者", "你").replace("受益者", "你")
            text = text.replace("执行", "试试").replace("遵医嘱", "记得")
        elif profile.emotional_warmth < 0.3:
            text = text.replace("你", "患者")
        return text

    def _add_tcm_flavor(self, text: str, tcm_weight: float) -> str:
        # stub — 实际需对接 TCMWellnessAgent
        return text

    def _get_profile(self, expert_id: str, db: Session = None) -> StyleProfile:
        if expert_id in self._profile_cache:
            return self._profile_cache[expert_id]
        if expert_id in PRESET_PROFILES:
            return PRESET_PROFILES[expert_id]
        if db:
            try:
                from core.xzb.xzb_models import XZBExpertProfile
                from sqlalchemy import select
                expert = db.execute(
                    select(XZBExpertProfile).where(XZBExpertProfile.id == expert_id)
                ).scalar_one_or_none()
                if expert and expert.style_profile:
                    sp = expert.style_profile
                    profile = StyleProfile(
                        expert_id=str(expert_id),
                        conclusion_first=sp.get("conclusion_first", True),
                        certainty_level=sp.get("certainty_level", "medium"),
                        emotional_warmth=sp.get("emotional_warmth", 0.5),
                        tcm_weight=expert.tcm_weight or 0.5,
                        analogy_density=sp.get("analogy_density", "occasional"),
                    )
                    self._profile_cache[expert_id] = profile
                    return profile
            except Exception:
                pass
        return PRESET_PROFILES["evidence_based"]
