# -*- coding: utf-8 -*-
"""
BAPS 评分引擎
行健行为教练 - 行为评估系统核心计分模块

实现四大问卷的评分算法：
1. 大五人格计分（含反向计分）
2. BPT-6行为分型判定
3. CAPACITY潜力诊断
4. SPI成功可能性加权计算
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class DimensionScore:
    """维度得分"""
    dimension: str
    name: str
    raw_score: float
    normalized_score: float = 0.0
    level: str = ""
    label: str = ""
    description: str = ""
    stars: int = 0


@dataclass
class BigFiveResult:
    """大五人格评估结果"""
    user_id: str
    assessed_at: datetime
    dimension_scores: Dict[str, DimensionScore]
    personality_profile: str
    dominant_traits: List[str]
    recommendations: List[str]


@dataclass
class BPT6Result:
    """BPT-6行为分型结果"""
    user_id: str
    assessed_at: datetime
    type_scores: Dict[str, int]
    dominant_types: List[str]
    is_mixed: bool
    is_dispersed: bool
    primary_type: str
    type_profile: Dict[str, Any]
    intervention_strategies: List[str]
    strategies_to_avoid: List[str]


@dataclass
class CAPACITYResult:
    """CAPACITY改变潜力结果"""
    user_id: str
    assessed_at: datetime
    dimension_scores: Dict[str, DimensionScore]
    total_score: int
    potential_level: str
    potential_label: str
    strategy: str
    weak_dimensions: List[str]
    strong_dimensions: List[str]


@dataclass
class SPIResult:
    """SPI成功可能性结果"""
    user_id: str
    assessed_at: datetime
    dimension_scores: Dict[str, float]
    spi_score: float
    success_level: str
    success_label: str
    success_rate: str
    strategy: str
    dimension_analysis: Dict[str, str]


@dataclass
class TTM7Result:
    """TTM-7改变阶段评估结果"""
    user_id: str
    assessed_at: datetime
    stage_scores: Dict[str, int]           # {S0: 12, S1: 6, ...}
    current_stage: str                      # "S0"-"S6"
    stage_name: str                         # "勉强接受"
    ttm_mapping: str                        # "准备期"
    sub_scores: Dict[str, int]             # {AW: 觉察, WI: 意愿, AC: 行动}
    stage_confidence: float                 # 0.0-1.0 判定置信度
    friendly_name: str                      # 去诊断化的友好名称
    friendly_description: str               # 去诊断化的描述


class BAPSScoringEngine:
    """BAPS综合评分引擎"""

    def __init__(self):
        """初始化评分引擎"""
        # 大五人格解读标准
        self.big_five_levels = [
            {"range": (25, 40), "level": "very_high", "label": "很高", "description": "该特质非常显著"},
            {"range": (10, 24), "level": "high", "label": "偏高", "description": "该特质较为明显"},
            {"range": (-9, 9), "level": "medium", "label": "中等", "description": "该特质处于平均水平"},
            {"range": (-24, -10), "level": "low", "label": "偏低", "description": "该特质较不明显"},
            {"range": (-40, -25), "level": "very_low", "label": "很低", "description": "该特质很不明显"}
        ]

        # CAPACITY维度解读标准
        self.capacity_dimension_levels = [
            {"range": (16, 20), "level": "high", "stars": 5, "label": "高"},
            {"range": (12, 15), "level": "medium_high", "stars": 4, "label": "中高"},
            {"range": (8, 11), "level": "medium", "stars": 3, "label": "中等"},
            {"range": (4, 7), "level": "low", "stars": 2, "label": "较低"}
        ]

        # CAPACITY总分解读标准
        self.capacity_total_levels = [
            {"range": (128, 160), "level": "high", "label": "高潜力", "strategy": "可挑战高目标"},
            {"range": (96, 127), "level": "medium_high", "label": "中高潜力", "strategy": "稳步推进"},
            {"range": (64, 95), "level": "medium", "label": "中等潜力", "strategy": "降低难度，加强支持"},
            {"range": (32, 63), "level": "low", "label": "需要准备", "strategy": "先解决前置问题"}
        ]

        # SPI解读标准
        self.spi_levels = [
            {"range": (40, 50), "level": "very_high", "label": "很高", "success_rate": ">75%", "strategy": "可挑战高目标"},
            {"range": (30, 39.99), "level": "high", "label": "较高", "success_rate": "50-75%", "strategy": "稳步推进"},
            {"range": (20, 29.99), "level": "medium", "label": "中等", "success_rate": "30-50%", "strategy": "降低难度，加强支持"},
            {"range": (10, 19.99), "level": "low", "label": "较低", "success_rate": "15-30%", "strategy": "从微习惯起步"},
            {"range": (0, 9.99), "level": "very_low", "label": "很低", "success_rate": "<15%", "strategy": "暂缓，先解决前置问题"}
        ]

        # BPT-6类型配置
        self.bpt6_type_profiles = {
            "action": {
                "name": "行动型",
                "core_trait": "说干就干，执行力强",
                "personality_base": "高尽责+低神经质",
                "intervention_focus": "防止过度、增加反思",
                "strategies": ["执行意图", "数据追踪"],
                "avoid": ["过度分析"]
            },
            "knowledge": {
                "name": "知识型",
                "core_trait": "知识充分，行动不足",
                "personality_base": "高开放+低尽责",
                "intervention_focus": "启动行动、降低完美主义",
                "strategies": ["MVP启动", "实验心态"],
                "avoid": ["无限研究"]
            },
            "emotion": {
                "name": "情绪型",
                "core_trait": "情绪主导行为",
                "personality_base": "高神经质+高开放",
                "intervention_focus": "情绪管理、自我关怀",
                "strategies": ["情绪解耦", "自我关怀"],
                "avoid": ["刚性目标"]
            },
            "relation": {
                "name": "关系型",
                "core_trait": "需要关系支持",
                "personality_base": "高外向+高宜人",
                "intervention_focus": "培养独立性",
                "strategies": ["社交嵌入", "公开承诺"],
                "avoid": ["完全独立"]
            },
            "environment": {
                "name": "环境型",
                "core_trait": "环境驱动行为",
                "personality_base": "中等各维度",
                "intervention_focus": "培养内在动机",
                "strategies": ["环境工程", "默认选项"],
                "avoid": ["意志力依赖"]
            },
            "ambivalent": {
                "name": "矛盾型",
                "core_trait": "意愿与恐惧并存",
                "personality_base": "高神经质",
                "intervention_focus": "接纳矛盾、小步实验",
                "strategies": ["ACT技术", "小步实验"],
                "avoid": ["催促决定"]
            }
        }

        # 维度名称映射
        self.big_five_names = {
            "E": "外向性", "N": "神经质", "C": "尽责性", "A": "宜人性", "O": "开放性"
        }
        self.capacity_names = {
            "C1": "觉察力", "A1": "自主感", "P": "匹配度", "A2": "资源",
            "C2": "承诺", "I": "身份", "T": "时间", "Y": "期待"
        }
        self.spi_names = {
            "M": "动机", "A": "能力", "S": "支持", "E": "环境", "H": "历史"
        }

    # ============ 大五人格计分 ============

    def score_big_five(self, answers: Dict[str, int], user_id: str = "anonymous") -> BigFiveResult:
        """
        计算大五人格得分

        参数:
            answers: Dict[题号, 得分] - 得分范围 -4 到 +4
            user_id: 用户ID

        返回:
            BigFiveResult 对象
        """
        reverse_items = ["E3"]  # 反向计分题

        dimensions = {
            "E": [f"E{i}" for i in range(1, 11)],
            "N": [f"N{i}" for i in range(1, 11)],
            "C": [f"C{i}" for i in range(1, 11)],
            "A": [f"A{i}" for i in range(1, 11)],
            "O": [f"O{i}" for i in range(1, 11)]
        }

        dimension_scores = {}
        dominant_traits = []

        for dim, items in dimensions.items():
            total = 0
            for item in items:
                score = answers.get(item, 0)
                if item in reverse_items:
                    score = -score  # 反向计分
                total += score

            # 确定水平
            level_info = self._get_big_five_level(total)

            dimension_scores[dim] = DimensionScore(
                dimension=dim,
                name=self.big_five_names[dim],
                raw_score=total,
                level=level_info["level"],
                label=level_info["label"],
                description=level_info["description"]
            )

            # 记录显著特质
            if level_info["level"] in ["very_high", "high"]:
                dominant_traits.append(self.big_five_names[dim])

        # 生成人格画像描述
        personality_profile = self._generate_big_five_profile(dimension_scores)

        # 生成建议
        recommendations = self._generate_big_five_recommendations(dimension_scores)

        return BigFiveResult(
            user_id=user_id,
            assessed_at=datetime.now(),
            dimension_scores=dimension_scores,
            personality_profile=personality_profile,
            dominant_traits=dominant_traits,
            recommendations=recommendations
        )

    def _get_big_five_level(self, score: int) -> Dict[str, str]:
        """获取大五人格维度水平"""
        for level in self.big_five_levels:
            min_val, max_val = level["range"]
            if min_val <= score <= max_val:
                return level
        return {"level": "medium", "label": "中等", "description": "该特质处于平均水平"}

    def _generate_big_five_profile(self, scores: Dict[str, DimensionScore]) -> str:
        """生成大五人格画像描述"""
        profile_parts = []

        # 外向性
        e_score = scores["E"]
        if e_score.level in ["very_high", "high"]:
            profile_parts.append("社交活跃，喜欢与人互动")
        elif e_score.level in ["very_low", "low"]:
            profile_parts.append("内向沉稳，偏好独处")

        # 神经质
        n_score = scores["N"]
        if n_score.level in ["very_high", "high"]:
            profile_parts.append("情感敏感，需要情绪管理支持")
        elif n_score.level in ["very_low", "low"]:
            profile_parts.append("情绪稳定，心态平和")

        # 尽责性
        c_score = scores["C"]
        if c_score.level in ["very_high", "high"]:
            profile_parts.append("自律性强，做事有条理")
        elif c_score.level in ["very_low", "low"]:
            profile_parts.append("灵活随性，需要外部结构支持")

        # 宜人性
        a_score = scores["A"]
        if a_score.level in ["very_high", "high"]:
            profile_parts.append("友善合作，重视人际和谐")
        elif a_score.level in ["very_low", "low"]:
            profile_parts.append("独立直接，注重个人立场")

        # 开放性
        o_score = scores["O"]
        if o_score.level in ["very_high", "high"]:
            profile_parts.append("思维开放，喜欢创新探索")
        elif o_score.level in ["very_low", "low"]:
            profile_parts.append("务实传统，偏好熟悉事物")

        return "；".join(profile_parts) if profile_parts else "人格特质处于平均水平"

    def _generate_big_five_recommendations(self, scores: Dict[str, DimensionScore]) -> List[str]:
        """基于大五人格生成建议"""
        recommendations = []

        # 基于神经质给予情绪管理建议
        if scores["N"].level in ["very_high", "high"]:
            recommendations.append("建议学习情绪调节技巧，如正念冥想、深呼吸练习")
            recommendations.append("设定灵活目标，避免过度自我批评")

        # 基于尽责性给予执行力建议
        if scores["C"].level in ["very_low", "low"]:
            recommendations.append("使用外部提醒工具（日历、闹钟）辅助行动")
            recommendations.append("从小目标开始，逐步建立习惯")

        # 基于外向性给予社交支持建议
        if scores["E"].level in ["very_high", "high"]:
            recommendations.append("可考虑组建互助小组或寻找accountability partner")
        else:
            recommendations.append("独自行动可能更适合您，避免过多社交压力")

        return recommendations if recommendations else ["保持当前状态，继续观察"]

    # ============ BPT-6 行为分型 ============

    def score_bpt6(self, answers: Dict[str, int], user_id: str = "anonymous") -> BPT6Result:
        """
        计算BPT-6行为分型得分

        参数:
            answers: Dict[题号, 得分] - 得分范围 1-5
            user_id: 用户ID

        返回:
            BPT6Result 对象
        """
        type_items = {
            "action": ["BPT1", "BPT2", "BPT3"],
            "knowledge": ["BPT4", "BPT5", "BPT6"],
            "emotion": ["BPT7", "BPT8", "BPT9"],
            "relation": ["BPT10", "BPT11", "BPT12"],
            "environment": ["BPT13", "BPT14", "BPT15"],
            "ambivalent": ["BPT16", "BPT17", "BPT18"]
        }

        # 计算各类型得分
        type_scores = {}
        for type_name, items in type_items.items():
            type_scores[type_name] = sum(answers.get(item, 0) for item in items)

        # 确定主导类型
        dominant_types = [t for t, s in type_scores.items() if s >= 12]
        mixed_threshold_types = [t for t, s in type_scores.items() if s >= 10]

        # 判断分型
        is_mixed = len([t for t, s in type_scores.items() if s >= 10]) >= 2
        is_dispersed = all(7 <= s <= 9 for s in type_scores.values())

        # 确定主要类型
        if dominant_types:
            primary_type = max(dominant_types, key=lambda t: type_scores[t])
        elif mixed_threshold_types:
            primary_type = max(mixed_threshold_types, key=lambda t: type_scores[t])
        else:
            primary_type = max(type_scores, key=type_scores.get)

        # 获取类型配置
        type_profile = self.bpt6_type_profiles.get(primary_type, {})

        # 汇总干预策略
        strategies = []
        avoid = []
        for t in (dominant_types if dominant_types else [primary_type]):
            profile = self.bpt6_type_profiles.get(t, {})
            strategies.extend(profile.get("strategies", []))
            avoid.extend(profile.get("avoid", []))

        return BPT6Result(
            user_id=user_id,
            assessed_at=datetime.now(),
            type_scores=type_scores,
            dominant_types=dominant_types,
            is_mixed=is_mixed,
            is_dispersed=is_dispersed,
            primary_type=primary_type,
            type_profile=type_profile,
            intervention_strategies=list(set(strategies)),
            strategies_to_avoid=list(set(avoid))
        )

    # ============ CAPACITY 潜力诊断 ============

    def score_capacity(self, answers: Dict[str, int], user_id: str = "anonymous") -> CAPACITYResult:
        """
        计算CAPACITY改变潜力得分

        参数:
            answers: Dict[题号, 得分] - 得分范围 1-5
            user_id: 用户ID

        返回:
            CAPACITYResult 对象
        """
        dimension_items = {
            "C1": ["CAP1", "CAP2", "CAP3", "CAP4"],
            "A1": ["CAP5", "CAP6", "CAP7", "CAP8"],
            "P": ["CAP9", "CAP10", "CAP11", "CAP12"],
            "A2": ["CAP13", "CAP14", "CAP15", "CAP16"],
            "C2": ["CAP17", "CAP18", "CAP19", "CAP20"],
            "I": ["CAP21", "CAP22", "CAP23", "CAP24"],
            "T": ["CAP25", "CAP26", "CAP27", "CAP28"],
            "Y": ["CAP29", "CAP30", "CAP31", "CAP32"]
        }

        dimension_scores = {}
        total_score = 0
        weak_dimensions = []
        strong_dimensions = []

        for dim, items in dimension_items.items():
            score = sum(answers.get(item, 0) for item in items)
            total_score += score

            # 确定维度水平
            level_info = self._get_capacity_dimension_level(score)

            dimension_scores[dim] = DimensionScore(
                dimension=dim,
                name=self.capacity_names[dim],
                raw_score=score,
                level=level_info["level"],
                label=level_info["label"],
                stars=level_info["stars"]
            )

            # 记录强弱项
            if level_info["level"] == "low":
                weak_dimensions.append(self.capacity_names[dim])
            elif level_info["level"] == "high":
                strong_dimensions.append(self.capacity_names[dim])

        # 确定总体潜力水平
        total_level_info = self._get_capacity_total_level(total_score)

        return CAPACITYResult(
            user_id=user_id,
            assessed_at=datetime.now(),
            dimension_scores=dimension_scores,
            total_score=total_score,
            potential_level=total_level_info["level"],
            potential_label=total_level_info["label"],
            strategy=total_level_info["strategy"],
            weak_dimensions=weak_dimensions,
            strong_dimensions=strong_dimensions
        )

    def _get_capacity_dimension_level(self, score: int) -> Dict[str, Any]:
        """获取CAPACITY维度水平"""
        for level in self.capacity_dimension_levels:
            min_val, max_val = level["range"]
            if min_val <= score <= max_val:
                return level
        return {"level": "medium", "stars": 3, "label": "中等"}

    def _get_capacity_total_level(self, score: int) -> Dict[str, str]:
        """获取CAPACITY总体潜力水平"""
        for level in self.capacity_total_levels:
            min_val, max_val = level["range"]
            if min_val <= score <= max_val:
                return level
        return {"level": "medium", "label": "中等潜力", "strategy": "降低难度，加强支持"}

    # ============ SPI 成功可能性 ============

    def score_spi(self, answers: Dict[str, int], user_id: str = "anonymous") -> SPIResult:
        """
        计算SPI成功可能性指数

        参数:
            answers: Dict[题号, 得分] - 得分范围 1-5
            user_id: 用户ID

        返回:
            SPIResult 对象

        公式: SPI = M×0.30 + A×0.25 + S×0.20 + E×0.15 + H×0.10
        """
        dimension_items = {
            "M": [f"SPI{i}" for i in range(1, 11)],
            "A": [f"SPI{i}" for i in range(11, 21)],
            "S": [f"SPI{i}" for i in range(21, 31)],
            "E": [f"SPI{i}" for i in range(31, 41)],
            "H": [f"SPI{i}" for i in range(41, 51)]
        }

        weights = {"M": 0.30, "A": 0.25, "S": 0.20, "E": 0.15, "H": 0.10}

        # 计算各维度得分
        dimension_scores = {}
        for dim, items in dimension_items.items():
            dimension_scores[dim] = sum(answers.get(item, 0) for item in items)

        # 计算SPI加权得分
        spi_score = sum(dimension_scores[d] * weights[d] for d in dimension_items)
        spi_score = round(spi_score, 2)

        # 确定成功可能性水平
        level_info = self._get_spi_level(spi_score)

        # 维度分析
        dimension_analysis = {}
        for dim, score in dimension_scores.items():
            avg = score / 10  # 平均分
            if avg >= 4:
                dimension_analysis[self.spi_names[dim]] = "强项"
            elif avg >= 3:
                dimension_analysis[self.spi_names[dim]] = "一般"
            else:
                dimension_analysis[self.spi_names[dim]] = "需加强"

        return SPIResult(
            user_id=user_id,
            assessed_at=datetime.now(),
            dimension_scores=dimension_scores,
            spi_score=spi_score,
            success_level=level_info["level"],
            success_label=level_info["label"],
            success_rate=level_info["success_rate"],
            strategy=level_info["strategy"],
            dimension_analysis=dimension_analysis
        )

    def _get_spi_level(self, score: float) -> Dict[str, str]:
        """获取SPI成功可能性水平"""
        for level in self.spi_levels:
            min_val, max_val = level["range"]
            if min_val <= score <= max_val:
                return level
        return {"level": "medium", "label": "中等", "success_rate": "30-50%", "strategy": "降低难度，加强支持"}

    # ============ TTM-7 改变阶段评估 ============

    # 阶段友好名称映射 (去诊断化)
    STAGE_FRIENDLY_NAMES = {
        "S0": "探索期",
        "S1": "觉醒期",
        "S2": "思考期",
        "S3": "准备期",
        "S4": "行动期",
        "S5": "成长期",
        "S6": "收获期",
    }
    STAGE_FRIENDLY_DESC = {
        "S0": "你正处于对自身行为模式的探索阶段，这是一切改变的起点",
        "S1": "你已经开始意识到一些问题，内心正在觉醒中",
        "S2": "你正在思考改变的可能性，这说明你的内在力量在积蓄",
        "S3": "你已经准备好迎接改变，正在寻找合适的方式",
        "S4": "你已经迈出了行动的第一步，这是最了不起的跨越",
        "S5": "你正在持续成长，新的行为模式正在生根发芽",
        "S6": "健康行为已经成为你的一部分，这就是你",
    }

    def score_ttm7(self, answers: Dict[str, int], user_id: str = "anonymous") -> TTM7Result:
        """
        计算TTM-7改变阶段评估得分

        参数:
            answers: Dict[题号, 得分] - 得分范围 1-5
                     题号格式: TTM01-TTM21
            user_id: 用户ID

        返回:
            TTM7Result 对象

        判定逻辑:
            - 计算7个阶段各自得分(每阶段3题, 满分15)
            - S0-S2为早期阶段(高分=处于该阶段)
            - S3-S6为后期阶段(高分=处于该阶段)
            - 综合判定当前所处阶段
        """
        stages = {
            "S0": ["TTM01", "TTM02", "TTM03"],
            "S1": ["TTM04", "TTM05", "TTM06"],
            "S2": ["TTM07", "TTM08", "TTM09"],
            "S3": ["TTM10", "TTM11", "TTM12"],
            "S4": ["TTM13", "TTM14", "TTM15"],
            "S5": ["TTM16", "TTM17", "TTM18"],
            "S6": ["TTM19", "TTM20", "TTM21"],
        }

        stage_names = {
            "S0": "无知无觉", "S1": "强烈抗拒", "S2": "被动应对",
            "S3": "勉强接受", "S4": "尝试阶段", "S5": "主动实践", "S6": "内化习惯"
        }
        ttm_mapping = {
            "S0": "前意向期", "S1": "前意向期", "S2": "意向期",
            "S3": "准备期", "S4": "行动期(早期)", "S5": "行动期", "S6": "维持期"
        }

        # 计算各阶段得分
        stage_scores = {}
        for stage, items in stages.items():
            stage_scores[stage] = sum(answers.get(item, 0) for item in items)

        # 阶段判定逻辑
        early_stages = ["S0", "S1", "S2"]
        late_stages = ["S3", "S4", "S5", "S6"]

        early_max_score, early_max_stage = max(
            ((stage_scores[s], s) for s in early_stages), key=lambda x: x[0]
        )
        late_max_score, late_max_stage = max(
            ((stage_scores[s], s) for s in late_stages), key=lambda x: x[0]
        )

        # 判定: 如果早期阶段得分高且后期低 → 处于早期
        # 否则取后期阶段的最高分
        if early_max_score >= 10 and late_max_score < 10:
            current_stage = early_max_stage
        elif late_max_score >= 12 and late_max_stage == "S6":
            current_stage = "S6"  # S6需要更高门槛
        else:
            current_stage = late_max_stage

        # 计算置信度 (最高分与第二高分的差距)
        sorted_scores = sorted(stage_scores.values(), reverse=True)
        if sorted_scores[0] > 0:
            confidence = min(1.0, (sorted_scores[0] - sorted_scores[1]) / sorted_scores[0])
        else:
            confidence = 0.0

        # 计算子维度 (觉察AW / 意愿WI / 行动AC)
        aw_items = ["TTM01", "TTM04", "TTM07", "TTM10", "TTM13", "TTM16", "TTM19"]
        wi_items = ["TTM02", "TTM05", "TTM08", "TTM11", "TTM14", "TTM17", "TTM20"]
        ac_items = ["TTM03", "TTM06", "TTM09", "TTM12", "TTM15", "TTM18", "TTM21"]

        sub_scores = {
            "AW": sum(answers.get(item, 0) for item in aw_items),
            "WI": sum(answers.get(item, 0) for item in wi_items),
            "AC": sum(answers.get(item, 0) for item in ac_items),
        }

        return TTM7Result(
            user_id=user_id,
            assessed_at=datetime.now(),
            stage_scores=stage_scores,
            current_stage=current_stage,
            stage_name=stage_names[current_stage],
            ttm_mapping=ttm_mapping[current_stage],
            sub_scores=sub_scores,
            stage_confidence=round(confidence, 2),
            friendly_name=self.STAGE_FRIENDLY_NAMES[current_stage],
            friendly_description=self.STAGE_FRIENDLY_DESC[current_stage],
        )

    # ============ 综合评估 ============

    def comprehensive_assessment(
        self,
        big_five_answers: Dict[str, int],
        bpt6_answers: Dict[str, int],
        capacity_answers: Dict[str, int],
        spi_answers: Dict[str, int],
        ttm7_answers: Optional[Dict[str, int]] = None,
        user_id: str = "anonymous"
    ) -> Dict[str, Any]:
        """
        进行综合评估

        返回包含所有问卷结果的综合报告（TTM7选填）
        """
        big_five_result = self.score_big_five(big_five_answers, user_id)
        bpt6_result = self.score_bpt6(bpt6_answers, user_id)
        capacity_result = self.score_capacity(capacity_answers, user_id)
        spi_result = self.score_spi(spi_answers, user_id)

        ttm7_result = None
        if ttm7_answers:
            ttm7_result = self.score_ttm7(ttm7_answers, user_id)

        # 交叉分析
        cross_analysis = self._cross_analyze(big_five_result, bpt6_result, capacity_result, spi_result)

        report = {
            "user_id": user_id,
            "assessed_at": datetime.now().isoformat(),
            "big_five": self._result_to_dict(big_five_result),
            "bpt6": self._result_to_dict(bpt6_result),
            "capacity": self._result_to_dict(capacity_result),
            "spi": self._result_to_dict(spi_result),
            "cross_analysis": cross_analysis,
            "overall_recommendations": self._generate_overall_recommendations(
                big_five_result, bpt6_result, capacity_result, spi_result
            )
        }

        if ttm7_result:
            report["ttm7"] = self._result_to_dict(ttm7_result)
            # 基于阶段的额外交叉建议
            report["cross_analysis"]["current_stage"] = ttm7_result.current_stage
            report["cross_analysis"]["stage_name"] = ttm7_result.friendly_name

        return report

    def _cross_analyze(
        self,
        big_five: BigFiveResult,
        bpt6: BPT6Result,
        capacity: CAPACITYResult,
        spi: SPIResult
    ) -> Dict[str, Any]:
        """交叉分析四个评估结果"""
        analysis = {
            "personality_behavior_match": "",
            "change_readiness": "",
            "key_barriers": [],
            "key_strengths": []
        }

        # 人格-行为类型匹配度分析
        primary_type = bpt6.primary_type
        expected_type = self._infer_type_from_big_five(big_five)
        if primary_type == expected_type:
            analysis["personality_behavior_match"] = "高度匹配"
        else:
            analysis["personality_behavior_match"] = f"存在差异（人格倾向{expected_type}，实际表现{primary_type}）"

        # 改变准备度综合评估
        capacity_level = capacity.potential_level
        spi_level = spi.success_level
        if capacity_level in ["high", "medium_high"] and spi_level in ["very_high", "high"]:
            analysis["change_readiness"] = "高度就绪"
        elif capacity_level == "low" or spi_level in ["very_low", "low"]:
            analysis["change_readiness"] = "需要更多准备"
        else:
            analysis["change_readiness"] = "基本就绪"

        # 关键障碍识别
        analysis["key_barriers"] = capacity.weak_dimensions.copy()
        for dim, status in spi.dimension_analysis.items():
            if status == "需加强" and dim not in analysis["key_barriers"]:
                analysis["key_barriers"].append(dim)

        # 关键优势识别
        analysis["key_strengths"] = capacity.strong_dimensions.copy()
        for dim, status in spi.dimension_analysis.items():
            if status == "强项" and dim not in analysis["key_strengths"]:
                analysis["key_strengths"].append(dim)

        return analysis

    def _infer_type_from_big_five(self, big_five: BigFiveResult) -> str:
        """根据大五人格推断可能的行为类型"""
        scores = big_five.dimension_scores

        # 高尽责+低神经质 → 行动型
        if scores["C"].level in ["very_high", "high"] and scores["N"].level in ["very_low", "low"]:
            return "action"
        # 高开放+低尽责 → 知识型
        if scores["O"].level in ["very_high", "high"] and scores["C"].level in ["very_low", "low"]:
            return "knowledge"
        # 高神经质 → 情绪型或矛盾型
        if scores["N"].level in ["very_high", "high"]:
            return "emotion"
        # 高外向+高宜人 → 关系型
        if scores["E"].level in ["very_high", "high"] and scores["A"].level in ["very_high", "high"]:
            return "relation"
        # 默认
        return "environment"

    def _generate_overall_recommendations(
        self,
        big_five: BigFiveResult,
        bpt6: BPT6Result,
        capacity: CAPACITYResult,
        spi: SPIResult
    ) -> List[str]:
        """生成综合建议"""
        recommendations = []

        # 基于SPI策略
        recommendations.append(f"整体策略：{spi.strategy}")

        # 基于行为类型的干预建议
        if bpt6.intervention_strategies:
            recommendations.append(f"推荐干预方法：{', '.join(bpt6.intervention_strategies)}")

        # 基于弱项的改进建议
        if capacity.weak_dimensions:
            recommendations.append(f"需优先提升：{', '.join(capacity.weak_dimensions)}")

        # 基于人格的沟通建议
        recommendations.extend(big_five.recommendations[:2])

        return recommendations

    def _result_to_dict(self, result) -> Dict[str, Any]:
        """将结果对象转换为字典"""
        if hasattr(result, '__dict__'):
            d = {}
            for k, v in result.__dict__.items():
                if isinstance(v, datetime):
                    d[k] = v.isoformat()
                elif isinstance(v, dict):
                    d[k] = {
                        kk: self._result_to_dict(vv) if hasattr(vv, '__dict__') else vv
                        for kk, vv in v.items()
                    }
                elif hasattr(v, '__dict__'):
                    d[k] = self._result_to_dict(v)
                else:
                    d[k] = v
            return d
        return result
