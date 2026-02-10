# -*- coding: utf-8 -*-
"""
BAPS 报告生成器
行健行为教练 - 行为评估系统报告模块

生成结构化评估报告，支持多种输出格式
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from .scoring_engine import (
    BAPSScoringEngine,
    BigFiveResult,
    BPT6Result,
    CAPACITYResult,
    SPIResult
)


class BAPSReportGenerator:
    """BAPS报告生成器"""

    def __init__(self):
        self.engine = BAPSScoringEngine()

    def generate_big_five_report(self, result: BigFiveResult) -> Dict[str, Any]:
        """生成大五人格评估报告"""
        report = {
            "report_type": "big_five",
            "title": "大五人格评估报告",
            "user_id": result.user_id,
            "assessed_at": result.assessed_at.isoformat(),
            "summary": {
                "personality_profile": result.personality_profile,
                "dominant_traits": result.dominant_traits
            },
            "dimensions": {},
            "recommendations": result.recommendations,
            "visualization_data": {
                "type": "radar",
                "labels": [],
                "values": []
            }
        }

        # 维度详情
        dim_order = ["E", "N", "C", "A", "O"]
        for dim in dim_order:
            score = result.dimension_scores[dim]
            report["dimensions"][dim] = {
                "name": score.name,
                "raw_score": score.raw_score,
                "level": score.level,
                "label": score.label,
                "description": score.description
            }
            # 雷达图数据（归一化到0-100）
            normalized = (score.raw_score + 40) / 80 * 100
            report["visualization_data"]["labels"].append(score.name)
            report["visualization_data"]["values"].append(round(normalized, 1))

        return report

    def generate_bpt6_report(self, result: BPT6Result) -> Dict[str, Any]:
        """生成BPT-6行为分型报告"""
        report = {
            "report_type": "bpt6",
            "title": "BPT-6行为模式分型报告",
            "user_id": result.user_id,
            "assessed_at": result.assessed_at.isoformat(),
            "summary": {
                "primary_type": result.primary_type,
                "primary_type_name": result.type_profile.get("name", ""),
                "is_mixed": result.is_mixed,
                "is_dispersed": result.is_dispersed,
                "dominant_types": result.dominant_types
            },
            "type_scores": result.type_scores,
            "type_profile": result.type_profile,
            "intervention": {
                "recommended_strategies": result.intervention_strategies,
                "strategies_to_avoid": result.strategies_to_avoid
            },
            "visualization_data": {
                "type": "bar",
                "labels": [],
                "values": []
            }
        }

        # 图表数据
        type_names = {
            "action": "行动型", "knowledge": "知识型", "emotion": "情绪型",
            "relation": "关系型", "environment": "环境型", "ambivalent": "矛盾型"
        }
        for type_key, score in result.type_scores.items():
            report["visualization_data"]["labels"].append(type_names.get(type_key, type_key))
            report["visualization_data"]["values"].append(score)

        return report

    def generate_capacity_report(self, result: CAPACITYResult) -> Dict[str, Any]:
        """生成CAPACITY改变潜力报告"""
        report = {
            "report_type": "capacity",
            "title": "CAPACITY改变潜力诊断报告",
            "user_id": result.user_id,
            "assessed_at": result.assessed_at.isoformat(),
            "summary": {
                "total_score": result.total_score,
                "max_score": 160,
                "potential_level": result.potential_level,
                "potential_label": result.potential_label,
                "strategy": result.strategy
            },
            "dimensions": {},
            "strengths": result.strong_dimensions,
            "weaknesses": result.weak_dimensions,
            "visualization_data": {
                "type": "radar",
                "labels": [],
                "values": []
            }
        }

        # 维度详情
        dim_order = ["C1", "A1", "P", "A2", "C2", "I", "T", "Y"]
        for dim in dim_order:
            score = result.dimension_scores[dim]
            report["dimensions"][dim] = {
                "name": score.name,
                "raw_score": score.raw_score,
                "max_score": 20,
                "level": score.level,
                "label": score.label,
                "stars": score.stars
            }
            report["visualization_data"]["labels"].append(score.name)
            report["visualization_data"]["values"].append(score.raw_score)

        return report

    def generate_spi_report(self, result: SPIResult) -> Dict[str, Any]:
        """生成SPI成功可能性报告"""
        report = {
            "report_type": "spi",
            "title": "SPI成功可能性评估报告",
            "user_id": result.user_id,
            "assessed_at": result.assessed_at.isoformat(),
            "summary": {
                "spi_score": result.spi_score,
                "max_score": 50,
                "success_level": result.success_level,
                "success_label": result.success_label,
                "success_rate": result.success_rate,
                "strategy": result.strategy
            },
            "dimensions": {},
            "dimension_analysis": result.dimension_analysis,
            "formula": "SPI = M×0.30 + A×0.25 + S×0.20 + E×0.15 + H×0.10",
            "visualization_data": {
                "type": "bar",
                "labels": [],
                "values": [],
                "weights": []
            }
        }

        # 维度详情
        dim_names = {"M": "动机", "A": "能力", "S": "支持", "E": "环境", "H": "历史"}
        weights = {"M": 0.30, "A": 0.25, "S": 0.20, "E": 0.15, "H": 0.10}

        for dim in ["M", "A", "S", "E", "H"]:
            score = result.dimension_scores[dim]
            report["dimensions"][dim] = {
                "name": dim_names[dim],
                "raw_score": score,
                "max_score": 50,
                "weight": weights[dim],
                "weighted_score": round(score * weights[dim], 2),
                "analysis": result.dimension_analysis.get(dim_names[dim], "")
            }
            report["visualization_data"]["labels"].append(dim_names[dim])
            report["visualization_data"]["values"].append(score)
            report["visualization_data"]["weights"].append(weights[dim])

        return report

    def generate_comprehensive_report(
        self,
        big_five_answers: Dict[str, int],
        bpt6_answers: Dict[str, int],
        capacity_answers: Dict[str, int],
        spi_answers: Dict[str, int],
        user_id: str = "anonymous"
    ) -> Dict[str, Any]:
        """生成综合评估报告"""
        # 计算各问卷得分
        big_five_result = self.engine.score_big_five(big_five_answers, user_id)
        bpt6_result = self.engine.score_bpt6(bpt6_answers, user_id)
        capacity_result = self.engine.score_capacity(capacity_answers, user_id)
        spi_result = self.engine.score_spi(spi_answers, user_id)

        # 生成各问卷报告
        big_five_report = self.generate_big_five_report(big_five_result)
        bpt6_report = self.generate_bpt6_report(bpt6_result)
        capacity_report = self.generate_capacity_report(capacity_result)
        spi_report = self.generate_spi_report(spi_result)

        # 综合分析
        comprehensive = self.engine.comprehensive_assessment(
            big_five_answers, bpt6_answers, capacity_answers, spi_answers, user_id=user_id
        )

        return {
            "report_type": "comprehensive",
            "title": "行为评估综合报告",
            "user_id": user_id,
            "assessed_at": datetime.now().isoformat(),
            "executive_summary": self._generate_executive_summary(
                big_five_result, bpt6_result, capacity_result, spi_result
            ),
            "sections": {
                "personality": big_five_report,
                "behavior_type": bpt6_report,
                "change_potential": capacity_report,
                "success_possibility": spi_report
            },
            "cross_analysis": comprehensive["cross_analysis"],
            "overall_recommendations": comprehensive["overall_recommendations"],
            "action_plan": self._generate_action_plan(
                big_five_result, bpt6_result, capacity_result, spi_result
            )
        }

    def _generate_executive_summary(
        self,
        big_five: BigFiveResult,
        bpt6: BPT6Result,
        capacity: CAPACITYResult,
        spi: SPIResult
    ) -> str:
        """生成执行摘要"""
        type_name = self.engine.bpt6_type_profiles.get(bpt6.primary_type, {}).get("name", bpt6.primary_type)

        summary = f"""
您的行为评估已完成。以下是核心发现：

【人格画像】{big_five.personality_profile}

【行为类型】您属于{type_name}，{self.engine.bpt6_type_profiles.get(bpt6.primary_type, {}).get('core_trait', '')}

【改变潜力】{capacity.potential_label}（总分{capacity.total_score}/160）

【成功预测】SPI指数{spi.spi_score}分，成功可能性{spi.success_label}（预期成功率{spi.success_rate}）

【核心建议】{spi.strategy}
""".strip()

        return summary

    def _generate_action_plan(
        self,
        big_five: BigFiveResult,
        bpt6: BPT6Result,
        capacity: CAPACITYResult,
        spi: SPIResult
    ) -> Dict[str, Any]:
        """生成行动计划"""
        plan = {
            "phase_1": {
                "name": "启动期（1-2周）",
                "focus": "建立行为",
                "tasks": []
            },
            "phase_2": {
                "name": "适应期（3-4周）",
                "focus": "形成规律",
                "tasks": []
            },
            "phase_3": {
                "name": "稳定期（5-8周）",
                "focus": "自动化",
                "tasks": []
            },
            "phase_4": {
                "name": "内化期（9-12周）",
                "focus": "身份整合",
                "tasks": []
            }
        }

        # 根据行为类型定制任务
        if bpt6.primary_type == "action":
            plan["phase_1"]["tasks"] = ["设定数据追踪机制", "建立反思日志"]
            plan["phase_2"]["tasks"] = ["每周复盘进度", "调整执行节奏"]
        elif bpt6.primary_type == "knowledge":
            plan["phase_1"]["tasks"] = ["选择最小可行行动", "设定实验周期"]
            plan["phase_2"]["tasks"] = ["记录实验结果", "迭代优化方案"]
        elif bpt6.primary_type == "emotion":
            plan["phase_1"]["tasks"] = ["建立情绪觉察习惯", "学习自我关怀技巧"]
            plan["phase_2"]["tasks"] = ["情绪-行为解耦练习", "弹性目标设定"]
        elif bpt6.primary_type == "relation":
            plan["phase_1"]["tasks"] = ["寻找accountability partner", "加入支持社群"]
            plan["phase_2"]["tasks"] = ["定期互助交流", "公开承诺机制"]
        elif bpt6.primary_type == "environment":
            plan["phase_1"]["tasks"] = ["环境审计与优化", "设置默认选项"]
            plan["phase_2"]["tasks"] = ["减少决策点", "培养内在动机"]
        else:  # ambivalent
            plan["phase_1"]["tasks"] = ["接纳矛盾情绪", "尝试微小实验"]
            plan["phase_2"]["tasks"] = ["记录成功体验", "渐进扩大舒适区"]

        # 通用任务
        plan["phase_3"]["tasks"] = ["减少外部提醒依赖", "建立自动触发机制"]
        plan["phase_4"]["tasks"] = ["将行为融入身份认同", "分享经验帮助他人"]

        return plan

    def generate_markdown_report(
        self,
        comprehensive_report: Dict[str, Any]
    ) -> str:
        """生成Markdown格式报告"""
        r = comprehensive_report
        md = f"""# {r['title']}

**用户ID**: {r['user_id']}
**评估时间**: {r['assessed_at']}

---

## 执行摘要

{r['executive_summary']}

---

## 一、人格画像（大五人格）

"""
        # 大五人格部分
        bf = r['sections']['personality']
        for dim, data in bf['dimensions'].items():
            md += f"- **{data['name']}**: {data['raw_score']}分 ({data['label']})\n"

        md += f"\n**人格描述**: {bf['summary']['personality_profile']}\n"

        # BPT-6部分
        md += f"""
---

## 二、行为模式分型（BPT-6）

"""
        bt = r['sections']['behavior_type']
        md += f"**主导类型**: {bt['summary']['primary_type_name']}\n\n"
        md += "各类型得分：\n"
        for label, value in zip(bt['visualization_data']['labels'], bt['visualization_data']['values']):
            md += f"- {label}: {value}分\n"

        if bt['intervention']['recommended_strategies']:
            md += f"\n**推荐策略**: {', '.join(bt['intervention']['recommended_strategies'])}\n"
        if bt['intervention']['strategies_to_avoid']:
            md += f"\n**避免策略**: {', '.join(bt['intervention']['strategies_to_avoid'])}\n"

        # CAPACITY部分
        md += f"""
---

## 三、改变潜力诊断（CAPACITY）

"""
        cap = r['sections']['change_potential']
        md += f"**总分**: {cap['summary']['total_score']}/{cap['summary']['max_score']}\n"
        md += f"**潜力水平**: {cap['summary']['potential_label']}\n"
        md += f"**建议策略**: {cap['summary']['strategy']}\n\n"

        md += "各维度详情：\n"
        for dim, data in cap['dimensions'].items():
            stars = "★" * data['stars'] + "☆" * (5 - data['stars'])
            md += f"- {data['name']}: {data['raw_score']}/{data['max_score']} {stars}\n"

        # SPI部分
        md += f"""
---

## 四、成功可能性预测（SPI）

"""
        spi = r['sections']['success_possibility']
        md += f"**SPI指数**: {spi['summary']['spi_score']}\n"
        md += f"**成功水平**: {spi['summary']['success_label']}（{spi['summary']['success_rate']}）\n"
        md += f"**建议策略**: {spi['summary']['strategy']}\n\n"

        md += f"计算公式: `{spi['formula']}`\n\n"
        md += "各维度分析：\n"
        for dim, data in spi['dimensions'].items():
            md += f"- {data['name']}: {data['raw_score']}分 × {data['weight']} = {data['weighted_score']} ({data['analysis']})\n"

        # 综合建议
        md += f"""
---

## 五、综合分析

**人格-行为匹配**: {r['cross_analysis']['personality_behavior_match']}

**改变准备度**: {r['cross_analysis']['change_readiness']}

**关键优势**: {', '.join(r['cross_analysis']['key_strengths']) if r['cross_analysis']['key_strengths'] else '暂无'}

**关键障碍**: {', '.join(r['cross_analysis']['key_barriers']) if r['cross_analysis']['key_barriers'] else '暂无'}

---

## 六、行动计划

"""
        for phase_key, phase in r['action_plan'].items():
            md += f"### {phase['name']}\n"
            md += f"**重点**: {phase['focus']}\n"
            for task in phase['tasks']:
                md += f"- [ ] {task}\n"
            md += "\n"

        md += f"""
---

## 七、核心建议

"""
        for i, rec in enumerate(r['overall_recommendations'], 1):
            md += f"{i}. {rec}\n"

        md += f"""
---

*报告由 行健行为教练 BAPS系统 自动生成*
*本报告仅供参考，如有健康问题请咨询专业人员*
"""

        return md
