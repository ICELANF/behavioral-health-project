"""
Layer3 综合诊断报告生成器
放置: api/core/diagnostics/layer3_report_generator.py
"""
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from core.diagnostics.cognitive_assessment import score_hbm
from core.diagnostics.capability_assessment import score_comb, score_self_efficacy
from core.diagnostics.support_assessment import score_support_system


class Layer3DiagnosticReport(BaseModel):
    user_id: int
    assessment_date: datetime

    hbm_scores: dict[str, int]
    attribution_type: str
    time_orientation: str

    comb_scores: dict
    comb_bottleneck: str
    self_efficacy_level: str

    support_total: float
    support_level: str
    weakest_layer: str

    strengths: list[str]
    weaknesses: list[str]
    priority_interventions: list[dict]

    def to_behavioral_profile_patch(self) -> dict:
        return {
            "cognitive_structure": {
                "hbm": self.hbm_scores,
                "attribution": self.attribution_type,
                "time_orientation": self.time_orientation,
            },
            "support_network": {
                "total_score": self.support_total,
                "level": self.support_level,
            },
            "capability": {
                "comb_bottleneck": self.comb_bottleneck,
                "self_efficacy": self.self_efficacy_level,
            },
        }


def generate_layer3_report(
    user_id: int,
    hbm_answers: dict[str, list[int]],
    attribution: str,
    time_orient: str,
    comb_answers: dict[str, dict[str, list[int]]],
    se_answers: dict[str, int],
    support_answers: dict[str, dict[str, list[int]]],
) -> Layer3DiagnosticReport:
    """一站式生成 Layer3 诊断报告"""
    hbm = score_hbm(hbm_answers)
    comb = score_comb(comb_answers)
    se = score_self_efficacy(se_answers)
    support = score_support_system(support_answers)

    # 归纳优劣势
    strengths = []
    weaknesses = []

    if hbm["total_score"] >= 54:
        strengths.append("健康信念认知较好")
    for w in hbm["weak_dimensions"]:
        weaknesses.append(f"HBM-{w}维度偏弱")

    if se["level"] == "strong":
        strengths.append("自我效能较强")
    elif se["level"] == "low":
        weaknesses.append("自我效能偏低")

    if support["support_level"] == "strong":
        strengths.append("支持体系充足")
    elif support["support_level"] == "weak":
        weaknesses.append(f"支持体系薄弱(最弱: {support['weakest_layer']})")

    if comb["bottleneck"]:
        weaknesses.append(f"COM-B瓶颈: {comb['bottleneck']}")

    # 优先干预
    priorities = hbm["intervention_priorities"][:3]
    if se["level"] != "strong":
        priorities.append({"dimension": "self_efficacy", "strategy": "微目标+成功体验"})
    for layer in support.get("build_priorities", []):
        priorities.append({"dimension": f"support_{layer}", "strategy": f"加强{layer}圈支持"})

    return Layer3DiagnosticReport(
        user_id=user_id,
        assessment_date=datetime.now(),
        hbm_scores=hbm["dimension_scores"],
        attribution_type=attribution,
        time_orientation=time_orient,
        comb_scores=comb["dimension_scores"],
        comb_bottleneck=comb["bottleneck"],
        self_efficacy_level=se["level"],
        support_total=support["total_score"],
        support_level=support["support_level"],
        weakest_layer=support["weakest_layer"],
        strengths=strengths,
        weaknesses=weaknesses,
        priority_interventions=priorities,
    )
