# -*- coding: utf-8 -*-
"""
五大人格测评程序 (Big Five Personality Assessment)
包含：问卷模块、评分算法、结果报告
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple
import json


# ==================== 问卷模块 ====================

@dataclass
class Question:
    """问卷题目"""
    id: int
    text: str
    trait: str  # O/C/E/A/N
    reverse: bool = False  # 是否反向计分


class Questionnaire:
    """五大人格问卷 (基于 BFI-44 简化版)"""

    TRAITS = {
        'O': '开放性 (Openness)',
        'C': '尽责性 (Conscientiousness)',
        'E': '外向性 (Extraversion)',
        'A': '宜人性 (Agreeableness)',
        'N': '神经质 (Neuroticism)'
    }

    def __init__(self):
        self.questions = self._init_questions()

    def _init_questions(self) -> List[Question]:
        """初始化问卷题目"""
        items = [
            # 外向性 (E)
            (1, "我喜欢与人交往，善于社交", "E", False),
            (2, "我在聚会中通常比较安静", "E", True),
            (3, "我精力充沛，充满活力", "E", False),
            (4, "我喜欢成为众人关注的焦点", "E", False),
            (5, "我更喜欢独处而非参加社交活动", "E", True),

            # 宜人性 (A)
            (6, "我愿意帮助他人，为人慷慨", "A", False),
            (7, "我有时会对别人挑剔", "A", True),
            (8, "我信任他人，相信人性本善", "A", False),
            (9, "我容易与他人产生争执", "A", True),
            (10, "我善于体谅他人的感受", "A", False),

            # 尽责性 (C)
            (11, "我做事有计划，井井有条", "C", False),
            (12, "我有时会粗心大意", "C", True),
            (13, "我是一个可靠的工作者", "C", False),
            (14, "我倾向于拖延，效率不高", "C", True),
            (15, "我会坚持完成任务直到结束", "C", False),

            # 神经质 (N)
            (16, "我容易感到焦虑或担忧", "N", False),
            (17, "我情绪稳定，不容易沮丧", "N", True),
            (18, "我有时会感到情绪低落", "N", False),
            (19, "我能很好地应对压力", "N", True),
            (20, "我容易紧张", "N", False),

            # 开放性 (O)
            (21, "我对新事物充满好奇", "O", False),
            (22, "我更喜欢常规和熟悉的事物", "O", True),
            (23, "我富有想象力和创造力", "O", False),
            (24, "我喜欢思考抽象的概念", "O", False),
            (25, "我对艺术和美有较高的敏感度", "O", False),
        ]
        return [Question(id=i[0], text=i[1], trait=i[2], reverse=i[3]) for i in items]

    def get_questions(self) -> List[Question]:
        """获取所有问题"""
        return self.questions

    def get_scale_description(self) -> str:
        """获取量表说明"""
        return """
评分标准 (1-5分):
  1 = 非常不同意
  2 = 不同意
  3 = 中立
  4 = 同意
  5 = 非常同意
"""


# ==================== 评分算法 ====================

class ScoringEngine:
    """评分引擎"""

    def __init__(self, questionnaire: Questionnaire):
        self.questionnaire = questionnaire
        self.questions_by_trait = self._group_by_trait()

    def _group_by_trait(self) -> Dict[str, List[Question]]:
        """按特质分组问题"""
        grouped = {'O': [], 'C': [], 'E': [], 'A': [], 'N': []}
        for q in self.questionnaire.get_questions():
            grouped[q.trait].append(q)
        return grouped

    def calculate_scores(self, answers: Dict[int, int]) -> Dict[str, float]:
        """
        计算各维度得分

        Args:
            answers: {题目ID: 答案(1-5)}

        Returns:
            各维度原始分和百分比分数
        """
        trait_scores = {}

        for trait, questions in self.questions_by_trait.items():
            total = 0
            for q in questions:
                raw_score = answers.get(q.id, 3)  # 默认中立分
                # 反向计分
                if q.reverse:
                    raw_score = 6 - raw_score
                total += raw_score

            # 计算平均分 (1-5) 和百分比 (0-100)
            avg_score = total / len(questions)
            percentage = (avg_score - 1) / 4 * 100

            trait_scores[trait] = {
                'raw': total,
                'average': round(avg_score, 2),
                'percentage': round(percentage, 1)
            }

        return trait_scores

    def get_level(self, percentage: float) -> str:
        """根据百分比判断水平"""
        if percentage >= 80:
            return "很高"
        elif percentage >= 60:
            return "较高"
        elif percentage >= 40:
            return "中等"
        elif percentage >= 20:
            return "较低"
        else:
            return "很低"


# ==================== 结果报告 ====================

class ReportGenerator:
    """报告生成器"""

    TRAIT_DESCRIPTIONS = {
        'O': {
            'name': '开放性 (Openness)',
            'high': '你富有想象力和创造力，喜欢探索新事物和新观点。你对艺术、美学有较高的敏感度，思维活跃，乐于接受挑战。',
            'mid': '你在接受新事物方面持平衡态度，既能欣赏创新，也重视传统经验。',
            'low': '你更偏好实际和具体的事物，喜欢熟悉的环境和常规。你务实稳重，注重实际效果。'
        },
        'C': {
            'name': '尽责性 (Conscientiousness)',
            'high': '你做事有条理，自律性强，目标明确。你可靠、勤奋，善于规划和执行任务。',
            'mid': '你在工作和生活中保持适度的组织性，能在灵活性和纪律性之间取得平衡。',
            'low': '你更喜欢灵活自由的方式，不喜欢过多的规则约束。你可能更注重当下而非长期计划。'
        },
        'E': {
            'name': '外向性 (Extraversion)',
            'high': '你热情开朗，喜欢社交活动，善于表达自己。你精力充沛，乐于成为焦点。',
            'mid': '你在社交和独处之间保持平衡，能根据情境调整自己的社交风格。',
            'low': '你更喜欢安静的环境和深度的人际关系。你善于倾听和思考，独立性强。'
        },
        'A': {
            'name': '宜人性 (Agreeableness)',
            'high': '你善解人意，乐于助人，与人相处融洽。你富有同情心，重视和谐的人际关系。',
            'mid': '你在合作与竞争之间保持平衡，既能体谅他人，也能坚持自己的立场。',
            'low': '你更注重客观和理性，不会轻易被情感左右。你独立思考，敢于表达不同意见。'
        },
        'N': {
            'name': '神经质 (Neuroticism)',
            'high': '你情感丰富，对环境变化敏感。你可能需要更多的支持来应对压力和焦虑。',
            'mid': '你的情绪稳定性处于中等水平，能够应对大多数日常压力。',
            'low': '你情绪稳定，心态平和，能够从容应对压力和挫折。你很少感到焦虑或沮丧。'
        }
    }

    def __init__(self, questionnaire: Questionnaire, scoring_engine: ScoringEngine):
        self.questionnaire = questionnaire
        self.scoring_engine = scoring_engine

    def generate_report(self, scores: Dict[str, dict]) -> str:
        """生成文字报告"""
        report_lines = [
            "=" * 60,
            "          五大人格测评结果报告",
            "=" * 60,
            "",
            "【各维度得分】",
            ""
        ]

        # 得分表格
        for trait in ['O', 'C', 'E', 'A', 'N']:
            score_data = scores[trait]
            trait_name = self.TRAIT_DESCRIPTIONS[trait]['name']
            level = self.scoring_engine.get_level(score_data['percentage'])
            bar = self._create_bar(score_data['percentage'])

            report_lines.append(f"{trait_name}")
            report_lines.append(f"  得分: {score_data['average']}/5.0 ({score_data['percentage']}%)  [{level}]")
            report_lines.append(f"  {bar}")
            report_lines.append("")

        # 详细解读
        report_lines.extend([
            "-" * 60,
            "【详细解读】",
            ""
        ])

        for trait in ['O', 'C', 'E', 'A', 'N']:
            score_data = scores[trait]
            desc = self.TRAIT_DESCRIPTIONS[trait]
            percentage = score_data['percentage']

            if percentage >= 60:
                interpretation = desc['high']
            elif percentage >= 40:
                interpretation = desc['mid']
            else:
                interpretation = desc['low']

            report_lines.append(f"* {desc['name']}")
            report_lines.append(f"  {interpretation}")
            report_lines.append("")

        # 人格画像
        report_lines.extend([
            "-" * 60,
            "【人格画像】",
            ""
        ])

        profile = self._generate_profile(scores)
        report_lines.append(profile)

        report_lines.extend([
            "",
            "=" * 60,
            "注：本测评仅供参考，不作为专业心理诊断依据。",
            "=" * 60
        ])

        return "\n".join(report_lines)

    def _create_bar(self, percentage: float, width: int = 30) -> str:
        """创建进度条"""
        filled = int(percentage / 100 * width)
        bar = "#" * filled + "-" * (width - filled)
        return f"[{bar}]"

    def _generate_profile(self, scores: Dict[str, dict]) -> str:
        """生成人格画像描述"""
        # 找出最高和最低的两个维度
        sorted_traits = sorted(scores.items(), key=lambda x: x[1]['percentage'], reverse=True)
        top_traits = sorted_traits[:2]
        low_traits = sorted_traits[-2:]

        trait_names = {
            'O': '开放', 'C': '尽责', 'E': '外向', 'A': '亲和', 'N': '敏感'
        }

        high_desc = "、".join([trait_names[t[0]] for t in top_traits])

        profile = f"你的突出特质是: {high_desc}。"

        # 根据组合给出建议
        if scores['E']['percentage'] >= 60 and scores['A']['percentage'] >= 60:
            profile += "\n  你适合从事需要人际沟通的工作，如销售、公关、教育等。"
        elif scores['C']['percentage'] >= 60 and scores['O']['percentage'] >= 60:
            profile += "\n  你适合从事需要创造力和执行力的工作，如产品设计、项目管理等。"
        elif scores['O']['percentage'] >= 60 and scores['N']['percentage'] <= 40:
            profile += "\n  你适合从事需要创新和抗压能力的工作，如创业、研发等。"
        elif scores['C']['percentage'] >= 60:
            profile += "\n  你适合从事需要细致和责任心的工作，如财务、质量管理等。"

        return profile

    def export_json(self, scores: Dict[str, dict]) -> str:
        """导出JSON格式结果"""
        result = {
            'scores': scores,
            'interpretations': {}
        }

        for trait in scores:
            percentage = scores[trait]['percentage']
            desc = self.TRAIT_DESCRIPTIONS[trait]
            if percentage >= 60:
                interpretation = desc['high']
            elif percentage >= 40:
                interpretation = desc['mid']
            else:
                interpretation = desc['low']

            result['interpretations'][trait] = {
                'name': desc['name'],
                'level': self.scoring_engine.get_level(percentage),
                'description': interpretation
            }

        return json.dumps(result, ensure_ascii=False, indent=2)


# ==================== 主程序 ====================

def run_assessment():
    """运行测评程序"""
    questionnaire = Questionnaire()
    scoring_engine = ScoringEngine(questionnaire)
    report_generator = ReportGenerator(questionnaire, scoring_engine)

    print("=" * 60)
    print("          欢迎参加五大人格测评")
    print("=" * 60)
    print(questionnaire.get_scale_description())
    print("-" * 60)

    answers = {}
    questions = questionnaire.get_questions()

    for i, q in enumerate(questions, 1):
        while True:
            try:
                print(f"\n[{i}/{len(questions)}] {q.text}")
                score = input("请输入分数 (1-5): ").strip()
                score = int(score)
                if 1 <= score <= 5:
                    answers[q.id] = score
                    break
                else:
                    print("请输入1-5之间的数字!")
            except ValueError:
                print("输入无效，请输入数字!")
            except KeyboardInterrupt:
                print("\n\n测评已取消。")
                return

    # 计算得分
    scores = scoring_engine.calculate_scores(answers)

    # 生成报告
    print("\n")
    report = report_generator.generate_report(scores)
    print(report)

    # 询问是否保存
    save = input("\n是否保存结果到文件? (y/n): ").strip().lower()
    if save == 'y':
        with open("personality_report.txt", "w", encoding="utf-8") as f:
            f.write(report)
        with open("personality_result.json", "w", encoding="utf-8") as f:
            f.write(report_generator.export_json(scores))
        print("结果已保存到 personality_report.txt 和 personality_result.json")


def demo_mode():
    """演示模式 - 使用随机答案"""
    import random

    questionnaire = Questionnaire()
    scoring_engine = ScoringEngine(questionnaire)
    report_generator = ReportGenerator(questionnaire, scoring_engine)

    # 生成模拟答案
    answers = {q.id: random.randint(1, 5) for q in questionnaire.get_questions()}

    # 计算得分并生成报告
    scores = scoring_engine.calculate_scores(answers)
    report = report_generator.generate_report(scores)
    print(report)

    return scores, report


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo_mode()
    else:
        run_assessment()
