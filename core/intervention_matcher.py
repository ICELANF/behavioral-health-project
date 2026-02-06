# -*- coding: utf-8 -*-
"""
InterventionMatcher - 领域干预匹配引擎

职责:
- 根据 BehavioralProfile (阶段+类型+心理层级+领域) 自动匹配干预策略
- 加载 rx_library.json (8类行为处方)
- 加载 prescription_strategy_library.json (L1-L5策略)
- 为每个需干预领域输出: 策略模板、语气、推荐行为、禁忌行为、建议列表
"""
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from loguru import logger


# 路径
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RX_PATH = os.path.join(_PROJECT_ROOT, "models", "rx_library.json")
_STRATEGY_PATH = os.path.join(_PROJECT_ROOT, "configs", "assessment", "prescription_strategy_library.json")
_SPI_MAPPING_PATH = os.path.join(_PROJECT_ROOT, "configs", "spi_mapping.json")

# 领域 → rx_library category 映射
DOMAIN_TO_CATEGORY = {
    "sleep": "sleep_regulation",
    "stress": "stress_management",
    "exercise": "exercise_habit",
    "nutrition": "nutrition_management",
    "emotion": "emotional_regulation",
    "tcm": "tcm_wellness",
    "social": "social_connection",
    "cognitive": "cognitive_improvement",
}

# 阶段 → stage_strategy 键映射
STAGE_TO_STRATEGY_KEY = {
    "S0": "intention",
    "S1": "intention",
    "S2": "preparation",
    "S3": "preparation",
    "S4": "action",
    "S5": "action",
    "S6": "action",
}


@dataclass
class DomainIntervention:
    """单个领域的干预方案"""
    domain: str                    # "nutrition" / "exercise" / "sleep" ...
    domain_name: str               # "营养管理"
    rx_id: str                     # "RX-SLEEP-001"
    rx_name: str                   # "睡眠质量改善基础方案"
    stage_strategy: str            # "intention" / "preparation" / "action"
    tone: str                      # "gentle_accepting" / "encouraging_practical" / ...
    core_goal: str                 # 核心目标
    scripts: Dict[str, str] = field(default_factory=dict)  # opening, motivation, closing
    do_list: List[str] = field(default_factory=list)
    dont_list: List[str] = field(default_factory=list)
    advice: List[Dict] = field(default_factory=list)
    knowledge: List[Dict] = field(default_factory=list)
    difficulty_level: str = "moderate"
    intensity_multiplier: float = 0.7


@dataclass
class InterventionPlan:
    """完整干预计划"""
    user_id: int
    stage: str
    psychological_level: str
    domain_interventions: List[DomainIntervention] = field(default_factory=list)
    policy_decision: str = "allow"
    generated_at: str = ""


class InterventionMatcher:
    """领域干预匹配引擎"""

    def __init__(self):
        self.rx_library = self._load_json(_RX_PATH)
        self.strategy_library = self._load_json(_STRATEGY_PATH)
        self.spi_mapping = self._load_json(_SPI_MAPPING_PATH)

        # 构建 category → prescription 索引
        self._rx_by_category: Dict[str, List[Dict]] = {}
        for rx in self.rx_library.get("prescriptions", []):
            cat = rx.get("category", "")
            if cat not in self._rx_by_category:
                self._rx_by_category[cat] = []
            self._rx_by_category[cat].append(rx)

    @staticmethod
    def _load_json(path: str) -> Dict:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load {path}: {e}")
            return {}

    def match(
        self,
        user_id: int,
        current_stage: str,
        psychological_level: str,
        bpt6_type: str,
        spi_score: float,
        target_domains: List[str],
        policy_decision: str = "allow",
    ) -> InterventionPlan:
        """
        核心匹配入口

        Args:
            user_id: 用户ID
            current_stage: 当前行为阶段 S0-S6
            psychological_level: 心理层级 L1-L5
            bpt6_type: 行为类型
            spi_score: SPI总分
            target_domains: 需干预领域列表 ["nutrition", "sleep", ...]
            policy_decision: PolicyGate 决定

        Returns:
            InterventionPlan
        """
        # 1. 确定难度等级
        difficulty_level, intensity_multiplier = self._get_difficulty(spi_score)

        # 2. 确定阶段策略键
        strategy_key = STAGE_TO_STRATEGY_KEY.get(current_stage, "intention")

        # 3. 为每个领域匹配干预
        domain_interventions = []
        for domain in target_domains:
            intervention = self._match_domain(
                domain=domain,
                strategy_key=strategy_key,
                difficulty_level=difficulty_level,
                intensity_multiplier=intensity_multiplier,
            )
            if intervention:
                domain_interventions.append(intervention)

        plan = InterventionPlan(
            user_id=user_id,
            stage=current_stage,
            psychological_level=psychological_level,
            domain_interventions=domain_interventions,
            policy_decision=policy_decision,
            generated_at=datetime.utcnow().isoformat(),
        )

        logger.info(
            f"InterventionPlan generated: user={user_id}, stage={current_stage}, "
            f"domains={[d.domain for d in domain_interventions]}"
        )
        return plan

    def _match_domain(
        self,
        domain: str,
        strategy_key: str,
        difficulty_level: str,
        intensity_multiplier: float,
    ) -> Optional[DomainIntervention]:
        """匹配单个领域的干预方案"""
        category = DOMAIN_TO_CATEGORY.get(domain)
        if not category:
            logger.warning(f"Unknown domain: {domain}")
            return None

        # 找到该类别的第一个处方 (后续可扩展选择逻辑)
        prescriptions = self._rx_by_category.get(category, [])
        if not prescriptions:
            logger.warning(f"No prescriptions for category: {category}")
            return None

        rx = prescriptions[0]
        rx_id = rx.get("rx_id", "")
        rx_name = rx.get("name", "")

        # 获取阶段策略
        stage_strategy = rx.get("stage_strategy", {}).get(strategy_key, {})
        if not stage_strategy:
            # 回退到 intention
            stage_strategy = rx.get("stage_strategy", {}).get("intention", {})

        # 获取内容
        content = rx.get("content", {})
        advice_list = content.get("constructive_advice", [])
        knowledge_list = content.get("knowledge_points", [])

        # 根据难度过滤建议 (仅保留难度 <= 当前级别的)
        difficulty_cap = {"challenging": 5, "moderate": 3, "easy": 2, "minimal": 1}
        cap = difficulty_cap.get(difficulty_level, 3)
        filtered_advice = [
            a for a in advice_list
            if a.get("difficulty", 3) <= cap
        ]

        domain_name = self.rx_library.get("categories", {}).get(category, domain)

        return DomainIntervention(
            domain=domain,
            domain_name=domain_name,
            rx_id=rx_id,
            rx_name=rx_name,
            stage_strategy=strategy_key,
            tone=stage_strategy.get("tone", "gentle_accepting"),
            core_goal=stage_strategy.get("core_goal", ""),
            scripts={
                "opening": stage_strategy.get("script_opening", ""),
                "motivation": stage_strategy.get("script_motivation", ""),
                "closing": stage_strategy.get("script_closing", ""),
            },
            do_list=stage_strategy.get("do", []),
            dont_list=stage_strategy.get("dont", []),
            advice=[
                {
                    "id": a.get("advice_id"),
                    "title": a.get("title"),
                    "description": a.get("description"),
                    "difficulty": a.get("difficulty"),
                    "priority": a.get("priority"),
                }
                for a in filtered_advice[:5]  # 最多5条
            ],
            knowledge=[
                {
                    "id": k.get("knowledge_id"),
                    "title": k.get("title"),
                    "content": k.get("content"),
                }
                for k in knowledge_list[:3]  # 最多3条
            ],
            difficulty_level=difficulty_level,
            intensity_multiplier=intensity_multiplier,
        )

    def _get_difficulty(self, spi_score: float) -> tuple:
        """根据 SPI 分数确定目标难度和强度系数"""
        spi_ranges = (
            self.strategy_library
            .get("prescription_framework", {})
            .get("smart_goal_rules", {})
            .get("spi_ranges", {})
        )

        if spi_score >= 70:
            cfg = spi_ranges.get(">=70", {})
            return cfg.get("level", "challenging"), cfg.get("intensity_multiplier", 1.0)
        elif spi_score >= 50:
            cfg = spi_ranges.get("50-69", {})
            return cfg.get("level", "moderate"), cfg.get("intensity_multiplier", 0.7)
        elif spi_score >= 30:
            cfg = spi_ranges.get("30-49", {})
            return cfg.get("level", "easy"), cfg.get("intensity_multiplier", 0.4)
        else:
            cfg = spi_ranges.get("<30", {})
            return cfg.get("level", "minimal"), cfg.get("intensity_multiplier", 0.2)

    def plan_to_dict(self, plan: InterventionPlan) -> Dict[str, Any]:
        """将干预计划转为可序列化字典"""
        return {
            "user_id": plan.user_id,
            "stage": plan.stage,
            "psychological_level": plan.psychological_level,
            "policy_decision": plan.policy_decision,
            "generated_at": plan.generated_at,
            "domain_interventions": [
                {
                    "domain": di.domain,
                    "domain_name": di.domain_name,
                    "rx_id": di.rx_id,
                    "rx_name": di.rx_name,
                    "stage_strategy": di.stage_strategy,
                    "tone": di.tone,
                    "core_goal": di.core_goal,
                    "scripts": di.scripts,
                    "do_list": di.do_list,
                    "dont_list": di.dont_list,
                    "advice": di.advice,
                    "knowledge": di.knowledge,
                    "difficulty_level": di.difficulty_level,
                    "intensity_multiplier": di.intensity_multiplier,
                }
                for di in plan.domain_interventions
            ],
        }
