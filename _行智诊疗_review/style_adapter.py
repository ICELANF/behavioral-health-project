"""
XZBStyleAdapter — 专家风格转换层（文档 §6.1）
将 LLM 原始输出转换为专家特有语言风格

风格维度：
  - vocabulary_profile: 词汇倾向向量
  - conclusion_first: 结论先/论据先
  - certainty_level: 确定性表达偏好 (low/medium/high)
  - emotional_warmth: 情感温度 0.0冷静 ~ 1.0温暖
  - tcm_weight: 中医/西医权重 0.0纯西医 ~ 1.0纯中医
  - analogy_density: 类比使用频率 (none/occasional/frequent)
"""
from __future__ import annotations
import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Style Profile
# ─────────────────────────────────────────────

@dataclass
class StyleProfile:
    expert_id: str
    vocabulary_profile: Dict[str, float] = field(default_factory=dict)
    conclusion_first: bool = True       # True=结论优先, False=铺垫优先
    certainty_level: str = "medium"     # "low" | "medium" | "high"
    emotional_warmth: float = 0.5       # 0.0冷静 ~ 1.0温暖
    tcm_weight: float = 0.5             # 0.0纯西医 ~ 1.0纯中医
    analogy_density: str = "occasional" # "none" | "occasional" | "frequent"

    # 各级别的表达模板池
    CERTAINTY_TEMPLATES = {
        "high": {
            "prefix": ["根据{evidence}，", "研究证实，", "数据显示，"],
            "modal": ["应当", "必须", "建议"],
        },
        "medium": {
            "prefix": ["综合来看，", "从现有证据看，", ""],
            "modal": ["建议", "可以考虑", "推荐"],
        },
        "low": {
            "prefix": ["目前的证据提示，", "个人经验来看，", ""],
            "modal": ["可能适合", "不妨试试", "可以尝试"],
        },
    }

    WARMTH_PHRASES = {
        "cold":  {"you": "患者", "do": "执行", "good": "达标"},
        "warm":  {"you": "你", "do": "试试", "good": "很好"},
    }


# ─────────────────────────────────────────────
# Prescription Card Transformer (文档 §6.3)
# ─────────────────────────────────────────────

@dataclass
class RxCard:
    """处方详情页的5张卡片"""
    goal: str       # 目标卡
    action: str     # 行动卡
    rationale: str  # 原理卡
    tracking: str   # 追踪卡
    reminder: str   # 提醒卡


class XZBStyleAdapter:
    """
    风格转换主类
    在 LLM 生成的原始输出和最终呈现之间执行风格转换
    """

    # 预设风格模板（Phase 1 基础版 5种预设）
    PRESET_PROFILES: Dict[str, StyleProfile] = {
        "rigorous": StyleProfile(
            expert_id="preset_rigorous",
            conclusion_first=True,
            certainty_level="high",
            emotional_warmth=0.1,
            tcm_weight=0.1,
            analogy_density="none",
        ),
        "warm_guide": StyleProfile(
            expert_id="preset_warm_guide",
            conclusion_first=False,
            certainty_level="medium",
            emotional_warmth=0.9,
            tcm_weight=0.3,
            analogy_density="frequent",
        ),
        "tcm_master": StyleProfile(
            expert_id="preset_tcm_master",
            conclusion_first=False,
            certainty_level="medium",
            emotional_warmth=0.7,
            tcm_weight=0.9,
            analogy_density="occasional",
        ),
        "evidence_based": StyleProfile(
            expert_id="preset_evidence_based",
            conclusion_first=True,
            certainty_level="high",
            emotional_warmth=0.3,
            tcm_weight=0.2,
            analogy_density="none",
        ),
        "lifestyle_coach": StyleProfile(
            expert_id="preset_lifestyle_coach",
            conclusion_first=False,
            certainty_level="medium",
            emotional_warmth=0.8,
            tcm_weight=0.2,
            analogy_density="frequent",
        ),
    }

    def __init__(self, llm_service=None):
        self.llm_service = llm_service  # 用于复杂风格转换
        self._profile_cache: Dict[str, StyleProfile] = {}

    async def transform(
        self,
        raw_text: str,
        expert_id: str,
        evidence_tier: Optional[str] = None,
        db=None,
    ) -> str:
        """
        单段文本风格转换入口
        """
        profile = await self._get_profile(expert_id, db)
        return self._apply_style(raw_text, profile, evidence_tier)

    async def transform_rx_cards(
        self,
        raw_cards: RxCard,
        expert_id: str,
        db=None,
    ) -> RxCard:
        """
        处方5张卡片批量风格转换（文档 §6.3）
        """
        profile = await self._get_profile(expert_id, db)

        return RxCard(
            goal=self._transform_goal(raw_cards.goal, profile),
            action=self._transform_action(raw_cards.action, profile),
            rationale=self._transform_rationale(raw_cards.rationale, profile),
            tracking=self._apply_style(raw_cards.tracking, profile),
            reminder=self._apply_warmth(raw_cards.reminder, profile),
        )

    # ── 内部转换方法 ────────────────────────────────────────────

    def _apply_style(self, text: str, profile: StyleProfile, evidence_tier: str = None) -> str:
        """综合应用风格参数"""
        result = text

        # 1. 结构调整：结论先/论据先
        if profile.conclusion_first:
            result = self._reorder_conclusion_first(result)

        # 2. 确定性语气转换
        result = self._apply_certainty(result, profile.certainty_level, evidence_tier)

        # 3. 情感温度（人称/措辞替换）
        result = self._apply_warmth(result, profile)

        # 4. 中医/西医权重（追加或省略中医表述）
        if profile.tcm_weight > 0.6:
            result = self._add_tcm_flavor(result, profile.tcm_weight)

        return result

    def _transform_goal(self, text: str, profile: StyleProfile) -> str:
        """目标卡风格转换（文档 §6.3 示例）"""
        if profile.emotional_warmth < 0.3:
            # 严谨型：精确数值 + 标准来源
            return self._add_clinical_precision(text)
        else:
            # 温暖型：口语化表达
            return self._apply_warmth(text, profile)

    def _transform_action(self, text: str, profile: StyleProfile) -> str:
        """行动卡风格转换"""
        if profile.emotional_warmth < 0.3:
            return self._add_precise_timing(text)
        return self._apply_warmth(text, profile)

    def _transform_rationale(self, text: str, profile: StyleProfile) -> str:
        """原理卡风格转换"""
        if profile.analogy_density == "frequent":
            text = self._add_analogy(text)
        if profile.tcm_weight > 0.6:
            text = self._add_tcm_flavor(text, profile.tcm_weight)
        return text

    def _reorder_conclusion_first(self, text: str) -> str:
        """提取结论句移到句首（简单规则实现）"""
        sentences = re.split(r'[。！？]', text)
        if len(sentences) <= 2:
            return text
        # 将最后一句（通常是结论）移到开头
        conclusion = sentences[-2].strip()
        rest = '。'.join(sentences[:-2])
        return f"{conclusion}。{rest}。" if conclusion else text

    def _apply_certainty(self, text: str, level: str, evidence_tier: str = None) -> str:
        """应用确定性语气"""
        templates = StyleProfile.CERTAINTY_TEMPLATES.get(level, {})
        modals = templates.get("modal", ["建议"])

        # 替换模糊语气词
        replacements = {
            "low":    {"建议": "可以考虑", "应该": "可以尝试", "必须": "可以考虑"},
            "medium": {"应当": "建议", "必须": "建议"},
            "high":   {"可以考虑": "建议", "不妨": "建议"},
        }
        for old, new in replacements.get(level, {}).items():
            text = text.replace(old, new)
        return text

    def _apply_warmth(self, text: str, profile: StyleProfile) -> str:
        """应用情感温度（人称替换）"""
        warmth = profile.emotional_warmth
        if warmth > 0.6:
            text = text.replace("患者", "你").replace("受益者", "你")
            text = text.replace("执行", "试试").replace("遵医嘱", "记得")
        else:
            text = text.replace("你", "患者")
        return text

    def _add_clinical_precision(self, text: str) -> str:
        """严谨风格：尝试添加精确指标说明（stub，实际需结合知识库）"""
        return text   # 实际实现需匹配领域知识

    def _add_precise_timing(self, text: str) -> str:
        """精确时间节点"""
        return text

    def _add_analogy(self, text: str) -> str:
        """添加类比（stub）"""
        return text

    def _add_tcm_flavor(self, text: str, tcm_weight: float) -> str:
        """追加中医表述（stub，需对接 TCMWellnessAgent）"""
        return text

    async def _get_profile(self, expert_id: str, db=None) -> StyleProfile:
        """获取专家风格配置（缓存 → DB → 预设）"""
        if expert_id in self._profile_cache:
            return self._profile_cache[expert_id]

        if expert_id in self.PRESET_PROFILES:
            return self.PRESET_PROFILES[expert_id]

        if db:
            from xzb.models.xzb_models import XZBExpertProfile as ExpertModel
            from sqlalchemy import select
            result = await db.execute(
                select(ExpertModel).where(ExpertModel.id == expert_id)
            )
            expert = result.scalar_one_or_none()
            if expert and expert.style_profile:
                sp = expert.style_profile
                profile = StyleProfile(
                    expert_id=str(expert_id),
                    conclusion_first=sp.get("conclusion_first", True),
                    certainty_level=sp.get("certainty_level", "medium"),
                    emotional_warmth=sp.get("emotional_warmth", 0.5),
                    tcm_weight=expert.tcm_weight,
                    analogy_density=sp.get("analogy_density", "occasional"),
                )
                self._profile_cache[expert_id] = profile
                return profile

        # 默认返回中性预设
        return self.PRESET_PROFILES["evidence_based"]

    def invalidate_cache(self, expert_id: str):
        """专家修改风格配置后主动失效缓存"""
        self._profile_cache.pop(expert_id, None)


# ─────────────────────────────────────────────
# 风格校准工具（文档 §7.1 /calibrate 端点使用）
# ─────────────────────────────────────────────

class StyleCalibrator:
    """
    通过30轮对话校准专家风格参数
    """
    CALIBRATION_SCENARIOS = [
        {"id": 1, "prompt": "请用您的方式解释：为什么餐后血糖会升高？"},
        {"id": 2, "prompt": "一位患者问：我需要戒糖吗？请回答。"},
        {"id": 3, "prompt": "对于不太愿意运动的患者，您通常怎么劝说？"},
        # ... 30个场景
    ]

    def analyze_responses(self, responses: List[Dict]) -> StyleProfile:
        """
        分析校准对话，提取风格参数
        这里实现基本的规则分析，完整版需要 LLM 分析
        """
        if not responses:
            return StyleProfile(expert_id="calibrated")

        texts = [r.get("text", "") for r in responses]
        combined = " ".join(texts)

        # 情感温度：检测人称代词
        warmth = 0.5
        if combined.count("你") > combined.count("患者"):
            warmth = 0.8
        elif combined.count("患者") > combined.count("你") * 2:
            warmth = 0.2

        # 结论优先：检测是否首句包含结论词
        conclusion_markers = ["所以", "因此", "总之", "结论是"]
        conclusion_in_end = sum(
            1 for t in texts if any(t.rstrip().endswith(m) or m in t[-30:] for m in conclusion_markers)
        )
        conclusion_first = conclusion_in_end < len(texts) / 2

        # 中医权重：检测中医术语频率
        tcm_terms = ["气虚", "阴虚", "阳虚", "湿热", "痰湿", "肝气", "脾胃", "经络"]
        tcm_count = sum(combined.count(term) for term in tcm_terms)
        tcm_weight = min(tcm_count / (len(texts) * 2), 1.0)

        return StyleProfile(
            expert_id="calibrated",
            conclusion_first=conclusion_first,
            certainty_level="medium",
            emotional_warmth=warmth,
            tcm_weight=tcm_weight,
            analogy_density="occasional",
        )
