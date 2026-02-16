"""
疼痛与中医骨科评估引擎

4个评估引擎:
  1. PainScaleEngine — NRS/VAS/BPI 疼痛量化评分
  2. PainAssessEngine — 多维疼痛综合评估(性质分类+灾难化+自效能)
  3. TCMSyndromeEngine — 中医骨伤辨证分型 → 穴位/外用方映射
  4. RehabStageEngine — 康复分期评估(5阶段) → 阶段匹配方案

设计原则:
  - 复用现有 assessment_engine 框架的存储接口
  - 评估结果统一存入 assessment_results 表
  - 引擎间可组合调用 (如 PainAssess 调用 PainScale 的评分)
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ================================================================
# 通用数据结构
# ================================================================

@dataclass
class AssessmentResult:
    """统一评估结果, 可序列化存入 assessment_results 表"""
    assessment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    engine_name: str = ""
    user_id: Optional[int] = None
    assessed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    scores: dict[str, Any] = field(default_factory=dict)
    classification: str = ""
    recommendations: list[str] = field(default_factory=list)
    raw_answers: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# ================================================================
# 1. PainScaleEngine — 疼痛量化评分
# ================================================================

class PainIntensity(str, Enum):
    NONE = "无痛"
    MILD = "轻度"
    MODERATE = "中度"
    SEVERE = "重度"
    EXTREME = "极重度"


@dataclass
class PainScaleResult:
    """疼痛评分结果"""
    nrs_score: int = 0          # 数字评分 0-10
    intensity: PainIntensity = PainIntensity.NONE
    location: str = ""           # 疼痛部位
    duration_days: int = 0       # 持续天数
    is_chronic: bool = False     # ≥90天为慢性
    functional_impact: dict[str, int] = field(default_factory=dict)
    # BPI简版: 对日常活动的影响 0-10
    # keys: general_activity, mood, walking, work, relations, sleep, enjoyment


class PainScaleEngine:
    """
    NRS数字评分引擎 + BPI简版功能影响

    用法:
        engine = PainScaleEngine()
        result = engine.evaluate(nrs=7, location="腰部", duration_days=95,
                                 functional_impact={"sleep": 8, "walking": 6})
    """
    ENGINE_NAME = "PainScaleEngine"

    @staticmethod
    def classify_intensity(nrs: int) -> PainIntensity:
        if nrs == 0:
            return PainIntensity.NONE
        elif nrs <= 3:
            return PainIntensity.MILD
        elif nrs <= 6:
            return PainIntensity.MODERATE
        elif nrs <= 8:
            return PainIntensity.SEVERE
        else:
            return PainIntensity.EXTREME

    def evaluate(
        self,
        nrs: int,
        location: str,
        duration_days: int = 0,
        functional_impact: Optional[dict[str, int]] = None,
        user_id: Optional[int] = None,
    ) -> AssessmentResult:
        nrs = max(0, min(10, nrs))
        intensity = self.classify_intensity(nrs)
        is_chronic = duration_days >= 90

        pain_result = PainScaleResult(
            nrs_score=nrs,
            intensity=intensity,
            location=location,
            duration_days=duration_days,
            is_chronic=is_chronic,
            functional_impact=functional_impact or {},
        )

        # 生成建议
        recommendations = []
        if nrs >= 8:
            recommendations.append("疼痛评分≥8, 建议尽快就诊疼痛科/骨科")
        if is_chronic:
            recommendations.append("疼痛超过3个月, 建议进行慢性疼痛综合评估")
        if functional_impact:
            high_impact = [k for k, v in functional_impact.items() if v >= 7]
            if high_impact:
                recommendations.append(
                    f"功能影响严重的领域: {', '.join(high_impact)}, 建议重点关注"
                )

        # 功能障碍均分
        fi_avg = 0.0
        if functional_impact:
            fi_avg = sum(functional_impact.values()) / len(functional_impact)

        return AssessmentResult(
            engine_name=self.ENGINE_NAME,
            user_id=user_id,
            scores={
                "nrs": nrs,
                "intensity": intensity.value,
                "functional_impact_avg": round(fi_avg, 1),
                "is_chronic": is_chronic,
                "duration_days": duration_days,
            },
            classification=intensity.value,
            recommendations=recommendations,
            raw_answers={
                "nrs": nrs,
                "location": location,
                "duration_days": duration_days,
                "functional_impact": functional_impact or {},
            },
            metadata={"pain_result": asdict(pain_result)},
        )


# ================================================================
# 2. PainAssessEngine — 多维疼痛综合评估
# ================================================================

class PainType(str, Enum):
    NOCICEPTIVE = "伤害性疼痛"        # 组织损伤
    NEUROPATHIC = "神经病理性疼痛"     # 神经损伤
    NOCIPLASTIC = "伤害可塑性疼痛"     # 中枢敏化
    MIXED = "混合性疼痛"


@dataclass
class PainCatastrophizingScore:
    """疼痛灾难化量表 PCS 简版 (6题)"""
    rumination: int = 0       # 反刍 (0-8)
    magnification: int = 0    # 放大 (0-8)
    helplessness: int = 0     # 无助 (0-8)
    total: int = 0            # 总分 (0-24)
    level: str = "正常"        # 正常/临界/临床显著

    @classmethod
    def from_answers(cls, answers: dict[str, int]) -> PainCatastrophizingScore:
        """从6题答案计算 (每题0-4分)"""
        rum = answers.get("rum1", 0) + answers.get("rum2", 0)
        mag = answers.get("mag1", 0) + answers.get("mag2", 0)
        hlp = answers.get("hlp1", 0) + answers.get("hlp2", 0)
        total = rum + mag + hlp
        if total <= 8:
            level = "正常"
        elif total <= 14:
            level = "临界"
        else:
            level = "临床显著"
        return cls(rumination=rum, magnification=mag,
                   helplessness=hlp, total=total, level=level)


@dataclass
class PainSelfEfficacyScore:
    """疼痛自效能量表 PSEQ 简版 (4题, 每题0-6)"""
    total: int = 0          # 总分 (0-24)
    level: str = "高"       # 高/中/低

    @classmethod
    def from_answers(cls, answers: list[int]) -> PainSelfEfficacyScore:
        total = sum(answers[:4])
        if total >= 17:
            level = "高"
        elif total >= 10:
            level = "中"
        else:
            level = "低"
        return cls(total=total, level=level)


class PainAssessEngine:
    """
    多维疼痛综合评估引擎

    组合评估:
      1. 疼痛性质分类 (基于症状描述, LLM辅助)
      2. 疼痛灾难化 PCS
      3. 疼痛自效能 PSEQ
      4. 综合分级 → 干预策略推荐
    """
    ENGINE_NAME = "PainAssessEngine"

    # 神经病理性疼痛特征词
    NEUROPATHIC_KEYWORDS = [
        "放射", "串痛", "触电", "烧灼", "蚁走感",
        "麻木", "针刺感", "过敏", "异常感觉", "电击样"
    ]

    def classify_pain_type(self, description: str) -> PainType:
        """基于描述初步判断疼痛性质 (可被LLM结果覆盖)"""
        neuro_count = sum(
            1 for kw in self.NEUROPATHIC_KEYWORDS if kw in description
        )
        has_tissue = any(
            kw in description
            for kw in ["酸痛", "胀痛", "刺痛", "钝痛", "压痛", "活动痛"]
        )
        if neuro_count >= 2 and has_tissue:
            return PainType.MIXED
        elif neuro_count >= 2:
            return PainType.NEUROPATHIC
        elif has_tissue:
            return PainType.NOCICEPTIVE
        return PainType.NOCICEPTIVE  # 默认

    def evaluate(
        self,
        pain_description: str,
        nrs_score: int,
        pcs_answers: Optional[dict[str, int]] = None,
        pseq_answers: Optional[list[int]] = None,
        pain_type_override: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> AssessmentResult:
        """
        综合评估

        Args:
            pain_description: 疼痛描述文本
            nrs_score: NRS评分 0-10
            pcs_answers: PCS 6题答案 {"rum1":x,"rum2":x,"mag1":x,...}
            pseq_answers: PSEQ 4题答案 [x, x, x, x]
            pain_type_override: LLM判断的疼痛类型覆盖
        """
        # 疼痛分类
        if pain_type_override and pain_type_override in PainType.__members__:
            pain_type = PainType[pain_type_override]
        else:
            pain_type = self.classify_pain_type(pain_description)

        # PCS
        pcs = PainCatastrophizingScore()
        if pcs_answers:
            pcs = PainCatastrophizingScore.from_answers(pcs_answers)

        # PSEQ
        pseq = PainSelfEfficacyScore()
        if pseq_answers:
            pseq = PainSelfEfficacyScore.from_answers(pseq_answers)

        # 综合分级和策略
        recommendations = self._generate_recommendations(
            nrs_score, pain_type, pcs, pseq
        )

        # 综合风险等级
        risk_factors = 0
        if nrs_score >= 7:
            risk_factors += 1
        if pcs.level == "临床显著":
            risk_factors += 1
        if pseq.level == "低":
            risk_factors += 1
        if pain_type == PainType.NEUROPATHIC:
            risk_factors += 1

        risk_level = "低" if risk_factors <= 1 else ("中" if risk_factors <= 2 else "高")

        return AssessmentResult(
            engine_name=self.ENGINE_NAME,
            user_id=user_id,
            scores={
                "nrs": nrs_score,
                "pain_type": pain_type.value,
                "pcs_total": pcs.total,
                "pcs_level": pcs.level,
                "pseq_total": pseq.total,
                "pseq_level": pseq.level,
                "risk_level": risk_level,
            },
            classification=f"{pain_type.value} / 风险{risk_level}",
            recommendations=recommendations,
            raw_answers={
                "description": pain_description,
                "nrs": nrs_score,
                "pcs_answers": pcs_answers,
                "pseq_answers": pseq_answers,
            },
            metadata={
                "pcs_detail": asdict(pcs),
                "pseq_detail": asdict(pseq),
            },
        )

    def _generate_recommendations(
        self,
        nrs: int,
        pain_type: PainType,
        pcs: PainCatastrophizingScore,
        pseq: PainSelfEfficacyScore,
    ) -> list[str]:
        recs = []

        # 基于疼痛类型
        if pain_type == PainType.NEUROPATHIC:
            recs.append("神经病理性疼痛特征明显, 建议神经内科/疼痛科评估")
        elif pain_type == PainType.MIXED:
            recs.append("混合性疼痛, 建议多学科联合评估(骨科+疼痛科+康复科)")

        # 基于灾难化
        if pcs.level == "临床显著":
            recs.append("疼痛灾难化程度高, 建议加入认知行为干预(CBT)")
            recs.append("转介心理专家(mental_expert)进行情绪评估")
        elif pcs.level == "临界":
            recs.append("疼痛灾难化倾向, 建议关注疼痛认知教育")

        # 基于自效能
        if pseq.level == "低":
            recs.append("疼痛自效能低, 建议小步渐进式康复 + 成功体验积累")
            recs.append("转介行为教练(behavior_coach)制定个性化激励策略")
        elif pseq.level == "中":
            recs.append("可适度自主康复, 配合教练定期跟进")

        # 基于NRS
        if nrs >= 8:
            recs.append("疼痛剧烈(NRS≥8), 优先控制疼痛后再开始康复训练")
        elif nrs >= 5:
            recs.append("中度疼痛, 康复运动强度需控制在疼痛不加重为度")

        return recs


# ================================================================
# 3. TCMSyndromeEngine — 中医骨伤辨证分型
# ================================================================

class TCMOrthoSyndrome(str, Enum):
    """骨伤科常见证型"""
    QI_ZHI_XUE_YU = "气滞血瘀"
    FENG_HAN_SHI_BI = "风寒湿痹"
    SHI_RE_YU_ZU = "湿热瘀阻"
    GAN_SHEN_KUI_XU = "肝肾亏虚"
    QI_XUE_LIANG_XU = "气血两虚"
    TAN_YU_HU_JIE = "痰瘀互结"


# 证型 → 推荐穴位
SYNDROME_ACUPOINT_MAP: dict[str, list[dict[str, str]]] = {
    "气滞血瘀": [
        {"name": "合谷", "method": "泻法", "note": "行气止痛"},
        {"name": "血海", "method": "泻法", "note": "活血化瘀"},
        {"name": "膈俞", "method": "泻法", "note": "血会, 活血要穴"},
        {"name": "太冲", "method": "泻法", "note": "疏肝理气"},
        {"name": "阿是穴", "method": "围刺", "note": "局部通经活络"},
    ],
    "风寒湿痹": [
        {"name": "风池", "method": "泻法+灸", "note": "祛风"},
        {"name": "风市", "method": "泻法", "note": "祛风止痛(下肢)"},
        {"name": "阳陵泉", "method": "平补平泻", "note": "筋会"},
        {"name": "足三里", "method": "补法+灸", "note": "健脾祛湿"},
        {"name": "关元", "method": "灸法", "note": "温阳散寒"},
    ],
    "湿热瘀阻": [
        {"name": "阴陵泉", "method": "泻法", "note": "利湿"},
        {"name": "曲池", "method": "泻法", "note": "清热"},
        {"name": "血海", "method": "泻法", "note": "凉血活血"},
        {"name": "三阴交", "method": "泻法", "note": "利湿活血"},
        {"name": "委中", "method": "刺络放血", "note": "清热活血(腰背)"},
    ],
    "肝肾亏虚": [
        {"name": "肾俞", "method": "补法+灸", "note": "补肾强腰"},
        {"name": "太溪", "method": "补法", "note": "补肾阴"},
        {"name": "肝俞", "method": "补法", "note": "养肝血"},
        {"name": "三阴交", "method": "补法", "note": "滋阴补肝肾"},
        {"name": "悬钟(绝骨)", "method": "补法", "note": "髓会, 强筋骨"},
    ],
    "气血两虚": [
        {"name": "气海", "method": "补法+灸", "note": "补气"},
        {"name": "血海", "method": "补法", "note": "养血"},
        {"name": "足三里", "method": "补法+灸", "note": "健脾益气"},
        {"name": "脾俞", "method": "补法+灸", "note": "健脾生血"},
        {"name": "关元", "method": "补法+灸", "note": "培元固本"},
    ],
    "痰瘀互结": [
        {"name": "丰隆", "method": "泻法", "note": "化痰要穴"},
        {"name": "血海", "method": "泻法", "note": "活血"},
        {"name": "中脘", "method": "平补平泻", "note": "运化痰湿"},
        {"name": "膈俞", "method": "泻法", "note": "活血化瘀"},
        {"name": "阿是穴", "method": "围刺", "note": "散结通络"},
    ],
}

# 证型 → 外用方推荐
SYNDROME_EXTERNAL_MAP: dict[str, list[dict[str, str]]] = {
    "气滞血瘀": [
        {"type": "贴敷", "formula": "活血止痛膏/云南白药膏", "usage": "日1次, 4-6h/次"},
        {"type": "熏洗", "formula": "伸筋草30g+透骨草30g+红花15g+乳香10g+没药10g",
         "usage": "水煎外洗, 温度38-42°C, 20min/次, 日1-2次"},
    ],
    "风寒湿痹": [
        {"type": "贴敷", "formula": "狗皮膏/追风膏", "usage": "日1次, 温热时贴敷效佳"},
        {"type": "熏蒸", "formula": "威灵仙30g+独活20g+羌活20g+桂枝15g+细辛5g",
         "usage": "蒸汽熏蒸, 注意温度勿烫伤, 15-20min/次"},
        {"type": "艾灸", "formula": "温和灸/隔姜灸", "usage": "每穴15-20min, 以皮肤红润为度"},
    ],
    "湿热瘀阻": [
        {"type": "贴敷", "formula": "如意金黄散调敷", "usage": "日1次, 6-8h/次, 忌热敷"},
        {"type": "熏洗", "formula": "黄柏30g+苍术20g+牛膝15g+薏苡仁30g+忍冬藤30g",
         "usage": "水煎温洗(勿过热), 20min/次, 日1次"},
    ],
    "肝肾亏虚": [
        {"type": "贴敷", "formula": "杜仲壮骨膏/肾骨宁膏", "usage": "日1次, 长期使用"},
        {"type": "熏洗", "formula": "杜仲30g+续断20g+桑寄生30g+牛膝15g+鸡血藤30g",
         "usage": "温洗腰膝, 40-42°C, 20min/次"},
        {"type": "足浴", "formula": "补肾强骨足浴方: 仙灵脾20g+肉桂10g+艾叶15g",
         "usage": "泡脚, 40°C, 20-30min/次, 睡前"},
    ],
    "气血两虚": [
        {"type": "贴敷", "formula": "温经通络膏/十全大补膏(外用)", "usage": "日1次"},
        {"type": "艾灸", "formula": "温和灸关元+气海+足三里",
         "usage": "每穴15min, 以温热舒适为度, 日1次"},
    ],
    "痰瘀互结": [
        {"type": "贴敷", "formula": "消瘀散结膏", "usage": "日1次, 局部有硬结处"},
        {"type": "熏洗", "formula": "半夏15g+陈皮15g+红花10g+桃仁10g+丹参20g",
         "usage": "温洗局部, 20min/次, 日1次"},
    ],
}


class TCMSyndromeEngine:
    """
    中医骨伤辨证引擎

    基于症状组合判断证型, 映射穴位处方和外用方
    完整辨证需LLM辅助, 此引擎提供规则框架
    """
    ENGINE_NAME = "TCMSyndromeEngine"

    # 证型特征词 (用于初步筛选, LLM做最终判断)
    SYNDROME_FEATURES: dict[str, list[str]] = {
        "气滞血瘀": ["刺痛", "固定", "拒按", "夜间加重", "舌暗", "瘀斑", "外伤后"],
        "风寒湿痹": ["遇冷加重", "游走性", "沉重", "阴雨加重", "畏寒", "关节僵硬"],
        "湿热瘀阻": ["红肿热痛", "口渴", "小便黄", "舌红苔黄腻", "灼热感"],
        "肝肾亏虚": ["酸软", "乏力", "腰膝酸软", "绵绵作痛", "久病", "老年"],
        "气血两虚": ["面色苍白", "疲倦", "头晕", "术后", "产后", "食欲差"],
        "痰瘀互结": ["包块", "结节", "关节变形", "肢体麻木", "皮下硬结"],
    }

    def preliminary_classify(self, symptoms: list[str]) -> list[tuple[str, float]]:
        """
        根据症状列表初步判断可能的证型 (返回匹配度排序)

        Returns: [(证型, 匹配度0-1), ...]
        """
        results = []
        symptom_text = " ".join(symptoms)
        for syndrome, features in self.SYNDROME_FEATURES.items():
            matches = sum(1 for f in features if f in symptom_text)
            if matches > 0:
                score = matches / len(features)
                results.append((syndrome, round(score, 2)))
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def get_acupoint_prescription(self, syndrome: str) -> list[dict[str, str]]:
        """获取证型对应的穴位处方"""
        return SYNDROME_ACUPOINT_MAP.get(syndrome, [])

    def get_external_prescription(self, syndrome: str) -> list[dict[str, str]]:
        """获取证型对应的外用方"""
        return SYNDROME_EXTERNAL_MAP.get(syndrome, [])

    def evaluate(
        self,
        symptoms: list[str],
        primary_syndrome: Optional[str] = None,
        location: str = "",
        user_id: Optional[int] = None,
    ) -> AssessmentResult:
        """
        辨证评估

        Args:
            symptoms: 症状列表 ["刺痛", "固定", "夜间加重", ...]
            primary_syndrome: LLM判断的主要证型 (覆盖规则判断)
            location: 疼痛部位
        """
        # 初步分类
        candidates = self.preliminary_classify(symptoms)

        if primary_syndrome and primary_syndrome in [s.value for s in TCMOrthoSyndrome]:
            final_syndrome = primary_syndrome
        elif candidates:
            final_syndrome = candidates[0][0]
        else:
            final_syndrome = "气滞血瘀"  # 默认

        acupoints = self.get_acupoint_prescription(final_syndrome)
        externals = self.get_external_prescription(final_syndrome)

        # 加入局部取穴 (基于部位)
        local_acupoints = self._get_local_acupoints(location)

        recommendations = [
            f"主要证型: {final_syndrome}",
            f"取穴方案: {len(acupoints)}个基础穴 + {len(local_acupoints)}个局部穴",
            f"外用方案: {len(externals)}种",
        ]
        if len(candidates) > 1:
            recommendations.append(
                f"兼证考虑: {candidates[1][0]}(匹配度{candidates[1][1]})"
            )

        return AssessmentResult(
            engine_name=self.ENGINE_NAME,
            user_id=user_id,
            scores={
                "primary_syndrome": final_syndrome,
                "candidates": candidates[:3],
                "acupoint_count": len(acupoints) + len(local_acupoints),
                "external_count": len(externals),
            },
            classification=final_syndrome,
            recommendations=recommendations,
            raw_answers={"symptoms": symptoms, "location": location},
            metadata={
                "acupoints": acupoints,
                "local_acupoints": local_acupoints,
                "external_prescriptions": externals,
            },
        )

    def _get_local_acupoints(self, location: str) -> list[dict[str, str]]:
        """根据部位返回局部取穴"""
        location_map = {
            "颈": [
                {"name": "风池", "note": "颈项要穴"},
                {"name": "天柱", "note": "颈部局部"},
                {"name": "颈夹脊", "note": "颈椎旁"},
            ],
            "肩": [
                {"name": "肩髃", "note": "肩关节前"},
                {"name": "肩髎", "note": "肩关节后"},
                {"name": "臂臑", "note": "肩臂痛"},
            ],
            "腰": [
                {"name": "肾俞", "note": "腰部要穴"},
                {"name": "大肠俞", "note": "腰痛常用"},
                {"name": "腰阳关", "note": "腰部正中"},
                {"name": "委中", "note": "'腰背委中求'"},
            ],
            "膝": [
                {"name": "内膝眼", "note": "膝关节局部"},
                {"name": "外膝眼(犊鼻)", "note": "膝关节局部"},
                {"name": "阳陵泉", "note": "筋会"},
                {"name": "梁丘", "note": "膝痛要穴"},
            ],
            "踝": [
                {"name": "解溪", "note": "踝关节前"},
                {"name": "昆仑", "note": "踝关节后外"},
                {"name": "太溪", "note": "踝关节后内"},
            ],
            "髋": [
                {"name": "环跳", "note": "髋关节要穴"},
                {"name": "居髎", "note": "髋部局部"},
                {"name": "秩边", "note": "臀部深层"},
            ],
        }
        for key, acupoints in location_map.items():
            if key in location:
                return acupoints
        return [{"name": "阿是穴", "note": "压痛点局部取穴"}]


# ================================================================
# 4. RehabStageEngine — 康复分期评估
# ================================================================

class RehabStage(str, Enum):
    ACUTE = "急性期"            # 0-3天 / 术后0-1周
    SUBACUTE = "亚急性期"       # 3-14天 / 术后1-2周
    RECOVERY = "恢复期"         # 2-6周 / 术后2-6周
    STRENGTHENING = "强化期"    # 6-12周 / 术后6-12周
    MAINTENANCE = "维持期"      # >12周 / 术后>12周


@dataclass
class RehabStageResult:
    """康复分期评估结果"""
    stage: RehabStage
    week_number: int
    progress_pct: float
    allowed_activities: list[str]
    prohibited_activities: list[str]
    functional_goals: list[str]
    tcm_methods: list[str]  # 本期适用的中医方法


# 各期允许/禁止的活动和中医方法
STAGE_PROTOCOLS: dict[str, dict] = {
    "急性期": {
        "allowed": [
            "静卧休息", "冰敷(24-48h内)", "等长收缩训练",
            "呼吸训练", "远端关节主动活动"
        ],
        "prohibited": [
            "局部热敷(48h内)", "被动牵拉", "负重活动",
            "高强度运动", "推拿(损伤局部)"
        ],
        "goals": ["控制炎症和肿胀", "减轻疼痛", "保护受伤结构"],
        "tcm_methods": [
            "远端取穴(非局部)", "中药冷敷(芒硝+大黄)",
            "呼吸导引(卧式八段锦第一式)"
        ],
    },
    "亚急性期": {
        "allowed": [
            "温热敷", "轻柔被动活动(ROM)", "主动辅助活动",
            "渐进等张训练", "水中运动"
        ],
        "prohibited": [
            "暴力手法", "高冲击运动", "完全负重(视情况)",
            "过度牵拉"
        ],
        "goals": ["恢复关节活动度", "减轻粘连", "轻度力量训练启动"],
        "tcm_methods": [
            "局部轻柔推拿", "温针灸", "中药熏洗",
            "坐式八段锦(简化版)"
        ],
    },
    "恢复期": {
        "allowed": [
            "主动全范围活动", "渐进抗阻训练", "本体感觉训练",
            "功能性活动训练", "步行训练"
        ],
        "prohibited": [
            "极限负重", "高强度对抗运动", "突然爆发力动作"
        ],
        "goals": ["恢复80%关节活动度", "肌力达到健侧70%", "日常生活自理"],
        "tcm_methods": [
            "推拿(中等力度)", "针灸(局部+远端)", "中药外洗(活血通络方)",
            "太极拳(简化24式)", "八段锦(立式简化版)"
        ],
    },
    "强化期": {
        "allowed": [
            "全范围抗阻训练", "专项功能训练", "平衡协调训练",
            "有氧耐力训练", "工作模拟训练"
        ],
        "prohibited": [
            "超极限对抗", "疼痛下强行训练"
        ],
        "goals": ["肌力达到健侧90%", "恢复工作/运动能力", "预防再伤"],
        "tcm_methods": [
            "推拿(正常力度)", "针灸巩固", "中药内服(补益肝肾方)",
            "太极拳(完整套路)", "八段锦(完整版)", "易筋经(选段)"
        ],
    },
    "维持期": {
        "allowed": [
            "自主运动计划", "全功能活动", "体育运动(渐进)",
            "力量维持训练", "柔韧性训练"
        ],
        "prohibited": [
            "突然增量", "忽视热身"
        ],
        "goals": ["功能完全恢复", "建立长期运动习惯", "预防复发"],
        "tcm_methods": [
            "自我保健推拿", "穴位按压", "季节性调理",
            "太极拳/八段锦/易筋经(日常练习)", "五禽戏"
        ],
    },
}


class RehabStageEngine:
    """
    康复分期评估引擎

    基于时间线 + 功能恢复指标 判断当前所处康复阶段,
    并匹配对应的活动处方和中医方法
    """
    ENGINE_NAME = "RehabStageEngine"

    def determine_stage(
        self,
        onset_days: int,
        is_postop: bool = False,
        nrs_current: int = 5,
        rom_pct: float = 50.0,
        strength_pct: float = 50.0,
    ) -> RehabStage:
        """
        综合判断康复阶段

        Args:
            onset_days: 发病/术后天数
            is_postop: 是否术后
            nrs_current: 当前NRS评分
            rom_pct: 关节活动度恢复百分比 (vs 正常)
            strength_pct: 肌力恢复百分比 (vs 健侧)
        """
        # 基于时间的初步判断
        if onset_days <= 3 or (is_postop and onset_days <= 7):
            time_stage = RehabStage.ACUTE
        elif onset_days <= 14:
            time_stage = RehabStage.SUBACUTE
        elif onset_days <= 42:  # 6周
            time_stage = RehabStage.RECOVERY
        elif onset_days <= 84:  # 12周
            time_stage = RehabStage.STRENGTHENING
        else:
            time_stage = RehabStage.MAINTENANCE

        # 基于功能指标的调整 (不能跳级, 只能降级)
        functional_stage = time_stage
        if nrs_current >= 7:
            # 疼痛仍重, 不应进入恢复期以上
            if time_stage.value in ["恢复期", "强化期", "维持期"]:
                functional_stage = RehabStage.SUBACUTE
        elif rom_pct < 30 and strength_pct < 30:
            if time_stage.value in ["强化期", "维持期"]:
                functional_stage = RehabStage.RECOVERY
        elif rom_pct < 70 or strength_pct < 60:
            if time_stage == RehabStage.MAINTENANCE:
                functional_stage = RehabStage.STRENGTHENING

        # 取更保守的阶段
        stages_order = list(RehabStage)
        time_idx = stages_order.index(time_stage)
        func_idx = stages_order.index(functional_stage)
        return stages_order[min(time_idx, func_idx)]

    def evaluate(
        self,
        onset_days: int,
        diagnosis: str = "",
        is_postop: bool = False,
        nrs_current: int = 5,
        rom_pct: float = 50.0,
        strength_pct: float = 50.0,
        user_id: Optional[int] = None,
    ) -> AssessmentResult:
        stage = self.determine_stage(
            onset_days, is_postop, nrs_current, rom_pct, strength_pct
        )
        protocol = STAGE_PROTOCOLS.get(stage.value, {})
        week = max(1, onset_days // 7)

        # 进度估算
        progress_map = {
            RehabStage.ACUTE: 0.1,
            RehabStage.SUBACUTE: 0.25,
            RehabStage.RECOVERY: 0.5,
            RehabStage.STRENGTHENING: 0.75,
            RehabStage.MAINTENANCE: 0.95,
        }
        base_progress = progress_map[stage]
        # 微调: ROM和力量加权
        progress = base_progress * 0.4 + (rom_pct / 100) * 0.3 + (strength_pct / 100) * 0.3
        progress = min(1.0, max(0.0, progress))

        rehab_result = RehabStageResult(
            stage=stage,
            week_number=week,
            progress_pct=round(progress * 100, 1),
            allowed_activities=protocol.get("allowed", []),
            prohibited_activities=protocol.get("prohibited", []),
            functional_goals=protocol.get("goals", []),
            tcm_methods=protocol.get("tcm_methods", []),
        )

        recommendations = [
            f"当前处于 {stage.value} (第{week}周)",
            f"康复进度约 {rehab_result.progress_pct}%",
        ]
        recommendations.extend(
            f"本期目标: {g}" for g in rehab_result.functional_goals
        )
        if nrs_current >= 5:
            recommendations.append(
                "疼痛仍较明显, 活动以不加重疼痛为原则"
            )

        return AssessmentResult(
            engine_name=self.ENGINE_NAME,
            user_id=user_id,
            scores={
                "stage": stage.value,
                "week": week,
                "progress_pct": rehab_result.progress_pct,
                "nrs_current": nrs_current,
                "rom_pct": rom_pct,
                "strength_pct": strength_pct,
            },
            classification=stage.value,
            recommendations=recommendations,
            raw_answers={
                "onset_days": onset_days,
                "diagnosis": diagnosis,
                "is_postop": is_postop,
                "nrs_current": nrs_current,
                "rom_pct": rom_pct,
                "strength_pct": strength_pct,
            },
            metadata={"rehab_detail": asdict(rehab_result)},
        )
