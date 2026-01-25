# -*- coding: utf-8 -*-
"""
真实数据处理脚本

功能:
1. 从 data/raw/ 读取 Excel 生理/心理测评数据
2. 运行八爪鱼归因模型
3. 生成个体诊断看板
4. 输出 JSON 格式诊断报告（含商城产品推荐）
"""

import os
import sys
import json
import glob
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

import pandas as pd
import numpy as np

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from health_engine import (
    HealthReport, HRVMetrics, ANSBalance, PsychMetrics,
    OctopusAttributionModel, HealthDashboard, AttributionResult
)


# =============================================================================
# 商城产品推荐引擎
# =============================================================================

@dataclass
class ProductRecommendation:
    """商城产品推荐"""
    product_id: str
    name: str
    category: str
    price: float
    description: str
    relevance_score: float      # 相关性分数 (0-100)
    target_dimension: str       # 针对的健康维度
    expected_benefit: str       # 预期效果


class ProductRecommendationEngine:
    """
    商城产品推荐引擎

    根据八爪鱼归因结果推荐相关产品
    """

    # 产品目录
    PRODUCT_CATALOG = [
        # 助眠类
        {
            "product_id": "SLEEP_001",
            "name": "智能助眠仪 SleepWave Pro",
            "category": "助眠硬件",
            "price": 1299.00,
            "description": "采用脑波诱导技术，通过特定频率声光刺激帮助快速入睡",
            "target_dimensions": ["生理韧性", "应激状态"],
            "efficacy_threshold": 40,
            "benefit": "改善睡眠质量，提升 HRV 指标"
        },
        {
            "product_id": "SLEEP_002",
            "name": "舒眠精油香薰套装",
            "category": "助眠用品",
            "price": 168.00,
            "description": "薰衣草+洋甘菊精油组合，促进副交感神经活性",
            "target_dimensions": ["应激状态"],
            "efficacy_threshold": 50,
            "benefit": "降低交感神经兴奋，促进放松"
        },
        {
            "product_id": "SLEEP_003",
            "name": "加权重力毯 8kg",
            "category": "助眠用品",
            "price": 599.00,
            "description": "深度压力刺激，模拟拥抱感，减少焦虑",
            "target_dimensions": ["心理健康", "应激状态"],
            "efficacy_threshold": 45,
            "benefit": "减轻焦虑感，提升安全感"
        },

        # 呼吸训练类
        {
            "product_id": "BREATH_001",
            "name": "呼吸训练仪 BreathCoach",
            "category": "呼吸训练硬件",
            "price": 899.00,
            "description": "实时监测呼吸模式，引导腹式呼吸训练，提升 HRV",
            "target_dimensions": ["生理韧性", "应激状态"],
            "efficacy_threshold": 35,
            "benefit": "提升 SDNN，增强自主神经调节能力"
        },
        {
            "product_id": "BREATH_002",
            "name": "正念呼吸课程（21天）",
            "category": "呼吸训练课程",
            "price": 299.00,
            "description": "专业心理咨询师录制，包含 4-7-8 呼吸法、方块呼吸等技巧",
            "target_dimensions": ["生理韧性", "心理健康"],
            "efficacy_threshold": 40,
            "benefit": "系统学习呼吸调节技巧"
        },
        {
            "product_id": "BREATH_003",
            "name": "便携式生物反馈仪",
            "category": "呼吸训练硬件",
            "price": 1599.00,
            "description": "实时显示 HRV 变化，游戏化呼吸训练",
            "target_dimensions": ["生理韧性"],
            "efficacy_threshold": 30,
            "benefit": "可视化训练效果，提升训练动力"
        },

        # 心理健康类
        {
            "product_id": "PSYCH_001",
            "name": "在线心理咨询（单次）",
            "category": "心理服务",
            "price": 399.00,
            "description": "持证心理咨询师一对一视频咨询，50分钟",
            "target_dimensions": ["心理健康"],
            "efficacy_threshold": 35,
            "benefit": "专业心理支持与指导"
        },
        {
            "product_id": "PSYCH_002",
            "name": "认知行为疗法课程（8周）",
            "category": "心理课程",
            "price": 699.00,
            "description": "基于 CBT 理论的系统课程，包含练习手册",
            "target_dimensions": ["心理健康", "应激状态"],
            "efficacy_threshold": 40,
            "benefit": "学习情绪管理技巧，改变负面思维模式"
        },
        {
            "product_id": "PSYCH_003",
            "name": "压力管理工作坊（线上）",
            "category": "心理课程",
            "price": 199.00,
            "description": "3小时互动工作坊，学习压力识别与应对策略",
            "target_dimensions": ["心理健康", "应激状态"],
            "efficacy_threshold": 50,
            "benefit": "掌握实用减压技巧"
        },

        # 运动健康类
        {
            "product_id": "SPORT_001",
            "name": "瑜伽入门套装",
            "category": "运动装备",
            "price": 259.00,
            "description": "瑜伽垫+瑜伽砖+伸展带，适合初学者",
            "target_dimensions": ["生理韧性", "应激状态"],
            "efficacy_threshold": 55,
            "benefit": "通过瑜伽提升身心平衡"
        },
        {
            "product_id": "SPORT_002",
            "name": "智能跳绳（计数版）",
            "category": "运动装备",
            "price": 129.00,
            "description": "自动计数，App 记录运动数据",
            "target_dimensions": ["生理韧性"],
            "efficacy_threshold": 60,
            "benefit": "有氧运动提升心肺功能和 HRV"
        },

        # 营养补充类
        {
            "product_id": "NUTR_001",
            "name": "镁元素补充剂（90天装）",
            "category": "营养补充",
            "price": 168.00,
            "description": "甘氨酸镁，支持神经系统健康",
            "target_dimensions": ["生理韧性", "心理健康"],
            "efficacy_threshold": 45,
            "benefit": "改善睡眠质量，减轻焦虑"
        },
        {
            "product_id": "NUTR_002",
            "name": "Omega-3 鱼油（EPA/DHA）",
            "category": "营养补充",
            "price": 229.00,
            "description": "高纯度深海鱼油，支持心脑血管健康",
            "target_dimensions": ["生理韧性"],
            "efficacy_threshold": 50,
            "benefit": "支持心血管健康，可能改善 HRV"
        }
    ]

    def __init__(self, attributions: List[AttributionResult], overall_score: float):
        self.attributions = attributions
        self.overall_score = overall_score

    def _calculate_relevance(self, product: Dict, attribution: AttributionResult) -> float:
        """计算产品与健康维度的相关性分数"""
        if attribution.dimension not in product["target_dimensions"]:
            return 0.0

        # 基础相关性
        base_relevance = 60.0

        # 根据状态严重程度调整
        status_bonus = {
            "critical": 40,
            "warning": 25,
            "mild": 10,
            "normal": 0
        }
        base_relevance += status_bonus.get(attribution.status, 0)

        # 根据效能阈值调整（分数越低越需要该产品）
        if attribution.score <= product["efficacy_threshold"]:
            base_relevance += 15

        return min(100, base_relevance)

    def recommend(self, max_products: int = 5) -> List[ProductRecommendation]:
        """根据归因结果推荐产品"""
        recommendations = []

        for product in self.PRODUCT_CATALOG:
            max_relevance = 0
            target_dim = ""

            # 计算与所有相关维度的最高相关性
            for attr in self.attributions:
                relevance = self._calculate_relevance(product, attr)
                if relevance > max_relevance:
                    max_relevance = relevance
                    target_dim = attr.dimension

            if max_relevance > 50:  # 只推荐相关性超过 50 的产品
                recommendations.append(ProductRecommendation(
                    product_id=product["product_id"],
                    name=product["name"],
                    category=product["category"],
                    price=product["price"],
                    description=product["description"],
                    relevance_score=max_relevance,
                    target_dimension=target_dim,
                    expected_benefit=product["benefit"]
                ))

        # 按相关性排序，取前 N 个
        recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
        return recommendations[:max_products]


# =============================================================================
# Excel 数据解析器
# =============================================================================

class ExcelDataParser:
    """
    Excel 测评数据解析器

    支持解析生理测评和心理测评 Excel 文件
    """

    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    def find_user_files(self, user_id: str) -> Tuple[Optional[str], Optional[str]]:
        """查找用户的生理和心理数据文件"""
        physio_pattern = os.path.join(self.data_dir, f"*{user_id}*生理*.xlsx")
        psych_pattern = os.path.join(self.data_dir, f"*{user_id}*心理*.xlsx")

        physio_files = glob.glob(physio_pattern)
        psych_files = glob.glob(psych_pattern)

        physio_file = physio_files[0] if physio_files else None
        psych_file = psych_files[0] if psych_files else None

        return physio_file, psych_file

    def parse_physio_data(self, file_path: str) -> HRVMetrics:
        """解析生理测评数据"""
        df = pd.read_excel(file_path)

        # 列名映射（处理可能的编码问题）
        col_mapping = {}
        for col in df.columns:
            col_lower = col.lower()
            if 'sdnn' in col_lower:
                col_mapping['sdnn'] = col
            elif 'rmssd' in col_lower:
                col_mapping['rmssd'] = col
            elif 'pnn50' in col_lower:
                col_mapping['pnn50'] = col
            elif col_lower == 'lf':
                col_mapping['lf'] = col
            elif col_lower == 'hf':
                col_mapping['hf'] = col
            elif '心率' in col or '平均' in col:
                col_mapping['hr'] = col

        # 提取非零数据的平均值
        hrv = HRVMetrics()

        if 'sdnn' in col_mapping:
            values = df[col_mapping['sdnn']].replace(0, np.nan).dropna()
            if len(values) > 0:
                hrv.sdnn = float(values.mean())

        if 'rmssd' in col_mapping:
            values = df[col_mapping['rmssd']].replace(0, np.nan).dropna()
            if len(values) > 0:
                hrv.rmssd = float(values.mean())

        if 'pnn50' in col_mapping:
            values = df[col_mapping['pnn50']].replace(0, np.nan).dropna()
            if len(values) > 0:
                hrv.pnn50 = float(values.mean())

        if 'lf' in col_mapping:
            values = df[col_mapping['lf']].replace(0, np.nan).dropna()
            if len(values) > 0:
                hrv.lf_power = float(values.mean())

        if 'hf' in col_mapping:
            values = df[col_mapping['hf']].replace(0, np.nan).dropna()
            if len(values) > 0:
                hrv.hf_power = float(values.mean())

        # 计算 LF/HF 比值
        if hrv.lf_power and hrv.hf_power and hrv.hf_power > 0:
            hrv.lf_hf_ratio = hrv.lf_power / hrv.hf_power

        return hrv

    def parse_psych_data(self, file_path: str) -> Tuple[PsychMetrics, ANSBalance]:
        """解析心理测评数据"""
        df = pd.read_excel(file_path)

        psych = PsychMetrics()
        ans = ANSBalance()

        # 列名映射
        col_mapping = {}
        for col in df.columns:
            col_str = str(col)
            if '压力' in col_str:
                col_mapping['stress'] = col
            elif '疲劳' in col_str:
                col_mapping['fatigue'] = col
            elif '焦虑' in col_str:
                col_mapping['anxiety'] = col
            elif '活力' in col_str:
                col_mapping['vitality'] = col

        # 提取平均值
        if 'stress' in col_mapping:
            psych.stress_score = float(df[col_mapping['stress']].mean())
            # 压力分数也可以作为应激指数的参考
            ans.stress_index = psych.stress_score

        if 'anxiety' in col_mapping:
            psych.anxiety_score = float(df[col_mapping['anxiety']].mean())

        if 'fatigue' in col_mapping:
            # 疲劳度可以反推效能感（疲劳越高，效能感越低）
            fatigue = float(df[col_mapping['fatigue']].mean())
            psych.efficacy_score = max(0, 100 - fatigue)

        if 'vitality' in col_mapping:
            vitality = float(df[col_mapping['vitality']].mean())
            # 活力可以作为副交感活性的参考
            ans.parasympathetic = vitality
            ans.sympathetic = 100 - vitality
            ans.balance_index = vitality - (100 - vitality)

        return psych, ans

    def parse_user_data(self, user_id: str) -> Optional[HealthReport]:
        """解析指定用户的完整数据"""
        physio_file, psych_file = self.find_user_files(user_id)

        if not physio_file and not psych_file:
            print(f"[WARN] 未找到用户 {user_id} 的数据文件")
            return None

        report = HealthReport(
            report_id=f"RPT_{user_id}_{datetime.now().strftime('%Y%m%d')}",
            user_id=user_id,
            report_date=datetime.now().strftime("%Y-%m-%d")
        )

        if physio_file:
            print(f"  解析生理数据: {os.path.basename(physio_file)}")
            report.hrv = self.parse_physio_data(physio_file)

        if psych_file:
            print(f"  解析心理数据: {os.path.basename(psych_file)}")
            report.psych, report.ans = self.parse_psych_data(psych_file)

        return report


# =============================================================================
# JSON 报告生成器
# =============================================================================

class DiagnosticReportGenerator:
    """诊断报告生成器"""

    def __init__(
        self,
        report: HealthReport,
        attributions: List[AttributionResult],
        overall_score: float,
        recommendations: List[ProductRecommendation],
        dashboard_path: str
    ):
        self.report = report
        self.attributions = attributions
        self.overall_score = overall_score
        self.recommendations = recommendations
        self.dashboard_path = dashboard_path

    def _get_risk_level(self, score: float) -> str:
        """根据综合分数确定风险等级"""
        if score < 30:
            return "高风险"
        elif score < 50:
            return "中高风险"
        elif score < 70:
            return "中等风险"
        elif score < 85:
            return "低风险"
        else:
            return "健康"

    def _get_urgency(self, score: float) -> str:
        """确定干预紧迫性"""
        if score < 30:
            return "立即干预"
        elif score < 50:
            return "尽快干预"
        elif score < 70:
            return "建议干预"
        else:
            return "常规维护"

    def generate(self) -> Dict[str, Any]:
        """生成完整的诊断报告"""
        report_data = {
            "report_meta": {
                "report_id": self.report.report_id,
                "user_id": self.report.user_id,
                "generated_at": datetime.now().isoformat(),
                "report_date": self.report.report_date,
                "model_version": "OctopusHealth v1.0"
            },

            "summary": {
                "overall_score": round(self.overall_score, 1),
                "risk_level": self._get_risk_level(self.overall_score),
                "urgency": self._get_urgency(self.overall_score),
                "dashboard_path": self.dashboard_path
            },

            "raw_metrics": {
                "hrv": {
                    "sdnn_ms": self.report.hrv.sdnn,
                    "rmssd_ms": self.report.hrv.rmssd,
                    "pnn50_percent": self.report.hrv.pnn50,
                    "lf_power": self.report.hrv.lf_power,
                    "hf_power": self.report.hrv.hf_power,
                    "lf_hf_ratio": self.report.hrv.lf_hf_ratio
                },
                "autonomic_nervous_system": {
                    "sympathetic_percent": self.report.ans.sympathetic,
                    "parasympathetic_percent": self.report.ans.parasympathetic,
                    "balance_index": self.report.ans.balance_index,
                    "stress_index": self.report.ans.stress_index
                },
                "psychological": {
                    "anxiety_score": self.report.psych.anxiety_score,
                    "depression_score": self.report.psych.depression_score,
                    "stress_score": self.report.psych.stress_score,
                    "efficacy_score": self.report.psych.efficacy_score
                }
            },

            "octopus_attribution": [
                {
                    "dimension": attr.dimension,
                    "status": attr.status,
                    "score": round(attr.score, 1),
                    "reason": attr.reason,
                    "recommendation": attr.recommendation
                }
                for attr in self.attributions
            ],

            "product_recommendations": [
                {
                    "product_id": rec.product_id,
                    "name": rec.name,
                    "category": rec.category,
                    "price": rec.price,
                    "description": rec.description,
                    "relevance_score": round(rec.relevance_score, 1),
                    "target_dimension": rec.target_dimension,
                    "expected_benefit": rec.expected_benefit
                }
                for rec in self.recommendations
            ],

            "action_plan": self._generate_action_plan()
        }

        return report_data

    def _generate_action_plan(self) -> Dict[str, Any]:
        """生成行动计划"""
        # 找到最需要关注的维度
        critical_dims = [a for a in self.attributions if a.status in ["critical", "warning"]]
        critical_dims.sort(key=lambda x: x.score)

        immediate_actions = []
        short_term_actions = []
        long_term_actions = []

        for attr in critical_dims:
            if attr.status == "critical":
                immediate_actions.append({
                    "dimension": attr.dimension,
                    "action": attr.recommendation,
                    "priority": "高"
                })
            elif attr.status == "warning":
                short_term_actions.append({
                    "dimension": attr.dimension,
                    "action": attr.recommendation,
                    "priority": "中"
                })

        # 添加长期行动
        long_term_actions = [
            {"action": "建立规律的作息时间", "benefit": "改善整体 HRV"},
            {"action": "每周 3 次有氧运动（30分钟以上）", "benefit": "增强心肺功能"},
            {"action": "定期进行 HRV 监测", "benefit": "追踪健康改善进度"}
        ]

        return {
            "immediate": immediate_actions,
            "short_term": short_term_actions,
            "long_term": long_term_actions,
            "follow_up_date": (datetime.now().replace(day=1) +
                              pd.DateOffset(months=1)).strftime("%Y-%m-%d")
        }


# =============================================================================
# 主处理流程
# =============================================================================

def process_user(user_id: str, data_dir: str, output_dir: str) -> Dict[str, Any]:
    """处理单个用户的完整流程"""
    print(f"\n{'='*60}")
    print(f"八爪鱼健康引擎 - 处理用户: {user_id}")
    print(f"{'='*60}")

    # 1. 解析数据
    print("\n[1/4] 解析测评数据...")
    parser = ExcelDataParser(data_dir)
    report = parser.parse_user_data(user_id)

    if not report:
        return {"error": f"未找到用户 {user_id} 的数据"}

    print(f"  - SDNN: {report.hrv.sdnn:.2f} ms" if report.hrv.sdnn else "  - SDNN: 无数据")
    print(f"  - LF/HF: {report.hrv.lf_hf_ratio:.2f}" if report.hrv.lf_hf_ratio else "  - LF/HF: 无数据")
    print(f"  - 焦虑分数: {report.psych.anxiety_score:.1f}" if report.psych.anxiety_score else "  - 焦虑分数: 无数据")
    print(f"  - 压力分数: {report.psych.stress_score:.1f}" if report.psych.stress_score else "  - 压力分数: 无数据")

    # 2. 归因分析
    print("\n[2/4] 运行八爪鱼归因分析...")
    model = OctopusAttributionModel(report)
    attributions = model.run_attribution()
    overall_score = model.get_overall_score()

    for attr in attributions:
        status_mark = {"critical": "[!]", "warning": "[*]", "mild": "[~]", "normal": "[v]", "unknown": "[?]"}
        print(f"  {status_mark.get(attr.status, '[?]')} {attr.dimension}: {attr.status} ({attr.score:.0f})")

    print(f"\n  综合健康分数: {overall_score:.1f}/100")

    # 3. 生成看板
    print("\n[3/4] 生成诊断看板...")
    dashboard_dir = os.path.join(output_dir, "dashboards")
    os.makedirs(dashboard_dir, exist_ok=True)

    dashboard = HealthDashboard(report, attributions, dashboard_dir)
    dashboard_filename = f"dashboard_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    dashboard_path = dashboard.generate_dashboard(dashboard_filename)

    # 4. 生成产品推荐
    print("\n[4/4] 生成产品推荐...")
    recommender = ProductRecommendationEngine(attributions, overall_score)
    recommendations = recommender.recommend(max_products=5)

    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec.name} (RMB {rec.price}) - relevance: {rec.relevance_score:.0f}")

    # 5. 生成 JSON 报告
    report_generator = DiagnosticReportGenerator(
        report, attributions, overall_score, recommendations, dashboard_path
    )
    report_data = report_generator.generate()

    # 保存 JSON 报告
    reports_dir = os.path.join(output_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    json_filename = f"diagnosis_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    json_path = os.path.join(reports_dir, json_filename)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print("处理完成!")
    print(f"  看板: {dashboard_path}")
    print(f"  报告: {json_path}")
    print(f"{'='*60}\n")

    return {
        "user_id": user_id,
        "dashboard_path": dashboard_path,
        "report_path": json_path,
        "overall_score": overall_score,
        "report_data": report_data
    }


def list_available_users(data_dir: str) -> List[str]:
    """列出所有可用的用户 ID"""
    import re

    files = glob.glob(os.path.join(data_dir, "*.xlsx"))
    user_ids = set()

    for f in files:
        basename = os.path.basename(f)
        # 提取 [XXXX] 或 【XXXX】格式的用户 ID
        match = re.search(r'[\[【]([A-F0-9]+)[\]】]', basename)
        if match:
            user_ids.add(match.group(1))

    return sorted(list(user_ids))


# =============================================================================
# 入口点
# =============================================================================

if __name__ == "__main__":
    # 配置路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, "data", "raw")
    output_dir = os.path.join(project_root, "output")

    print("\n" + "=" * 60)
    print("八爪鱼健康引擎 - 真实数据处理")
    print("=" * 60)

    # 列出可用用户
    users = list_available_users(data_dir)
    print(f"\n发现 {len(users)} 个用户数据:")
    for i, uid in enumerate(users[:5], 1):
        print(f"  {i}. {uid}")
    if len(users) > 5:
        print(f"  ... 及其他 {len(users) - 5} 个用户")

    # 处理第一个用户作为演示
    if users:
        target_user = users[0]
        print(f"\n选择处理用户: {target_user}")
        result = process_user(target_user, data_dir, output_dir)

        # 打印 JSON 报告摘要
        if "report_data" in result:
            print("\n" + "=" * 60)
            print("JSON 报告摘要:")
            print("=" * 60)
            rd = result["report_data"]
            print(f"用户ID: {rd['report_meta']['user_id']}")
            print(f"综合分数: {rd['summary']['overall_score']}")
            print(f"风险等级: {rd['summary']['risk_level']}")
            print(f"干预紧迫性: {rd['summary']['urgency']}")
            print(f"\nTop 3 Recommended Products:")
            for p in rd["product_recommendations"][:3]:
                print(f"  - {p['name']} (RMB {p['price']}) -> {p['expected_benefit']}")
    else:
        print("\n[ERROR] 未找到任何用户数据")
