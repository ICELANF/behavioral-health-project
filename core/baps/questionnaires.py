# -*- coding: utf-8 -*-
"""
BAPS 问卷定义模块
行健行为教练 - 行为评估系统

包含四大核心问卷：
1. BigFiveQuestionnaire - 大五人格测评 (50题)
2. BPT6Questionnaire - 行为模式分型 (18题)
3. CAPACITYQuestionnaire - 改变潜力诊断 (32题)
4. SPIQuestionnaire - 成功可能性评估 (50题)
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class QuestionnaireType(Enum):
    """问卷类型枚举"""
    BIG_FIVE = "big_five"
    BPT6 = "bpt6"
    CAPACITY = "capacity"
    SPI = "spi"


@dataclass
class QuestionItem:
    """题目项"""
    id: str
    dimension: str
    text: str
    reverse: bool = False


@dataclass
class ScaleConfig:
    """量表配置"""
    type: str
    range: tuple
    labels: Dict[str, str]


@dataclass
class DimensionConfig:
    """维度配置"""
    name: str
    name_en: str = ""
    items: int = 0
    score_range: tuple = (0, 0)
    weight: float = 1.0
    threshold: int = 0


class BaseQuestionnaire:
    """问卷基类"""

    def __init__(self):
        self.id: str = ""
        self.name: str = ""
        self.description: str = ""
        self.total_items: int = 0
        self.estimated_minutes: int = 0
        self.scale: ScaleConfig = None
        self.dimensions: Dict[str, DimensionConfig] = {}
        self.items: List[QuestionItem] = []
        self.reverse_items: List[str] = []

    def load_from_bank(self, bank_data: Dict[str, Any]) -> None:
        """从题库加载问卷数据"""
        raise NotImplementedError

    def get_items(self) -> List[Dict[str, Any]]:
        """获取所有题目"""
        return [
            {
                "id": item.id,
                "dimension": item.dimension,
                "text": item.text,
                "reverse": item.reverse
            }
            for item in self.items
        ]

    def get_dimension_items(self, dimension: str) -> List[QuestionItem]:
        """获取特定维度的题目"""
        return [item for item in self.items if item.dimension == dimension]

    def validate_answers(self, answers: Dict[str, int]) -> bool:
        """验证答案完整性"""
        required_ids = {item.id for item in self.items}
        provided_ids = set(answers.keys())
        return required_ids == provided_ids


class BigFiveQuestionnaire(BaseQuestionnaire):
    """大五人格测评问卷 (50题)"""

    def __init__(self, question_bank_path: str = None):
        super().__init__()
        self.id = "BIG_FIVE_50"
        self.name = "大五人格测评"
        self.description = "基于大五人格理论的人格特质评估"
        self.total_items = 50
        self.estimated_minutes = 10

        # 量表配置: 双极量表 -4 到 +4
        self.scale = ScaleConfig(
            type="bipolar",
            range=(-4, 4),
            labels={
                "-4": "完全不符合", "-3": "很不符合", "-2": "比较不符合",
                "-1": "有些不符合", "0": "中立",
                "1": "有些符合", "2": "比较符合", "3": "很符合", "4": "完全符合"
            }
        )

        # 五大维度
        self.dimensions = {
            "E": DimensionConfig("外向性", "Extraversion", 10, (-40, 40)),
            "N": DimensionConfig("神经质", "Neuroticism", 10, (-40, 40)),
            "C": DimensionConfig("尽责性", "Conscientiousness", 10, (-40, 40)),
            "A": DimensionConfig("宜人性", "Agreeableness", 10, (-40, 40)),
            "O": DimensionConfig("开放性", "Openness", 10, (-40, 40))
        }

        self.reverse_items = ["E3"]

        # 加载题目
        if question_bank_path:
            self._load_items(question_bank_path)
        else:
            self._init_default_items()

    def _load_items(self, path: str):
        """从题库文件加载题目"""
        with open(path, 'r', encoding='utf-8') as f:
            bank = json.load(f)

        big_five_data = bank["questionnaires"]["big_five"]
        for item_data in big_five_data["items"]:
            self.items.append(QuestionItem(
                id=item_data["id"],
                dimension=item_data["dimension"],
                text=item_data["text"],
                reverse=item_data.get("reverse", False)
            ))

    def _init_default_items(self):
        """初始化默认题目"""
        # 外向性 E1-E10
        e_items = [
            ("E1", "我喜欢参加社交聚会和活动"),
            ("E2", "我很容易和陌生人开始交谈"),
            ("E3", "我更喜欢独处而不是和他人在一起"),
            ("E4", "在团队中我经常是话题的发起者"),
            ("E5", "我喜欢成为关注的焦点"),
            ("E6", "我精力充沛，充满活力"),
            ("E7", "我喜欢尝试新的社交活动"),
            ("E8", "我在人群中感到舒适自在"),
            ("E9", "我很容易表达自己的想法和感受"),
            ("E10", "我认为自己是一个外向的人"),
        ]
        for id_, text in e_items:
            self.items.append(QuestionItem(id_, "E", text, id_ == "E3"))

        # 神经质 N1-N10
        n_items = [
            ("N1", "我经常感到焦虑或担忧"),
            ("N2", "我的情绪容易波动"),
            ("N3", "我经常感到紧张或压力很大"),
            ("N4", "小事情也会让我感到烦躁"),
            ("N5", "我经常担心事情会出问题"),
            ("N6", "我容易感到沮丧或低落"),
            ("N7", "批评会让我感到非常不安"),
            ("N8", "我经常对自己的决定感到后悔"),
            ("N9", "我很难放松下来"),
            ("N10", "我经常感到不安全或缺乏自信"),
        ]
        for id_, text in n_items:
            self.items.append(QuestionItem(id_, "N", text))

        # 尽责性 C1-C10
        c_items = [
            ("C1", "我做事有计划、有条理"),
            ("C2", "我总是按时完成任务"),
            ("C3", "我注重细节，追求完美"),
            ("C4", "我对自己的承诺非常认真"),
            ("C5", "我有很强的自律能力"),
            ("C6", "我总是努力做到最好"),
            ("C7", "我喜欢把事情安排得井井有条"),
            ("C8", "我做决定前会仔细考虑"),
            ("C9", "我对工作和生活有明确的目标"),
            ("C10", "我很少拖延重要的事情"),
        ]
        for id_, text in c_items:
            self.items.append(QuestionItem(id_, "C", text))

        # 宜人性 A1-A10
        a_items = [
            ("A1", "我相信大多数人是善良的"),
            ("A2", "我愿意帮助需要帮助的人"),
            ("A3", "我很容易原谅别人的错误"),
            ("A4", "我在意他人的感受"),
            ("A5", "我尽量避免与他人发生冲突"),
            ("A6", "我喜欢与他人合作而非竞争"),
            ("A7", "我对他人的需求很敏感"),
            ("A8", "我很容易与他人建立信任"),
            ("A9", "我尊重他人的意见和观点"),
            ("A10", "我认为自己是一个友善的人"),
        ]
        for id_, text in a_items:
            self.items.append(QuestionItem(id_, "A", text))

        # 开放性 O1-O10
        o_items = [
            ("O1", "我喜欢尝试新事物和新体验"),
            ("O2", "我对艺术和美学很感兴趣"),
            ("O3", "我喜欢思考抽象的概念和问题"),
            ("O4", "我有丰富的想象力"),
            ("O5", "我对不同的文化和观念持开放态度"),
            ("O6", "我喜欢探索新的想法和理论"),
            ("O7", "我经常有创新的想法"),
            ("O8", "我喜欢挑战传统的做法"),
            ("O9", "我对学习新知识充满热情"),
            ("O10", "我认为自己是一个有创造力的人"),
        ]
        for id_, text in o_items:
            self.items.append(QuestionItem(id_, "O", text))


class BPT6Questionnaire(BaseQuestionnaire):
    """BPT-6行为模式分型问卷 (18题)"""

    def __init__(self, question_bank_path: str = None):
        super().__init__()
        self.id = "BPT6_18"
        self.name = "BPT-6行为模式分型"
        self.description = "识别个体主要的行为改变模式类型"
        self.total_items = 18
        self.estimated_minutes = 5

        # 量表配置: 李克特5点量表
        self.scale = ScaleConfig(
            type="likert",
            range=(1, 5),
            labels={
                "1": "完全不符合", "2": "基本不符合", "3": "不确定",
                "4": "基本符合", "5": "完全符合"
            }
        )

        # 六种行为类型
        self.dimensions = {
            "action": DimensionConfig("行动型", "Action", 3, (3, 15), threshold=12),
            "knowledge": DimensionConfig("知识型", "Knowledge", 3, (3, 15), threshold=12),
            "emotion": DimensionConfig("情绪型", "Emotion", 3, (3, 15), threshold=12),
            "relation": DimensionConfig("关系型", "Relation", 3, (3, 15), threshold=12),
            "environment": DimensionConfig("环境型", "Environment", 3, (3, 15), threshold=12),
            "ambivalent": DimensionConfig("矛盾型", "Ambivalent", 3, (3, 15), threshold=12)
        }

        # 类型特征配置
        self.type_profiles = {
            "action": {
                "core_trait": "说干就干，执行力强",
                "personality_base": "高尽责+低神经质",
                "intervention_focus": "防止过度、增加反思",
                "strategies": ["执行意图", "数据追踪"],
                "avoid": ["过度分析"]
            },
            "knowledge": {
                "core_trait": "知识充分，行动不足",
                "personality_base": "高开放+低尽责",
                "intervention_focus": "启动行动、降低完美主义",
                "strategies": ["MVP启动", "实验心态"],
                "avoid": ["无限研究"]
            },
            "emotion": {
                "core_trait": "情绪主导行为",
                "personality_base": "高神经质+高开放",
                "intervention_focus": "情绪管理、自我关怀",
                "strategies": ["情绪解耦", "自我关怀"],
                "avoid": ["刚性目标"]
            },
            "relation": {
                "core_trait": "需要关系支持",
                "personality_base": "高外向+高宜人",
                "intervention_focus": "培养独立性",
                "strategies": ["社交嵌入", "公开承诺"],
                "avoid": ["完全独立"]
            },
            "environment": {
                "core_trait": "环境驱动行为",
                "personality_base": "中等各维度",
                "intervention_focus": "培养内在动机",
                "strategies": ["环境工程", "默认选项"],
                "avoid": ["意志力依赖"]
            },
            "ambivalent": {
                "core_trait": "意愿与恐惧并存",
                "personality_base": "高神经质",
                "intervention_focus": "接纳矛盾、小步实验",
                "strategies": ["ACT技术", "小步实验"],
                "avoid": ["催促决定"]
            }
        }

        if question_bank_path:
            self._load_items(question_bank_path)
        else:
            self._init_default_items()

    def _load_items(self, path: str):
        """从题库文件加载题目"""
        with open(path, 'r', encoding='utf-8') as f:
            bank = json.load(f)

        bpt6_data = bank["questionnaires"]["bpt6"]
        for item_data in bpt6_data["items"]:
            self.items.append(QuestionItem(
                id=item_data["id"],
                dimension=item_data["dimension"],
                text=item_data["text"]
            ))

    def _init_default_items(self):
        """初始化默认题目"""
        items_data = [
            ("BPT1", "action", "当我决定做某事时，我会立即行动而不是过多思考"),
            ("BPT2", "action", "我更喜欢边做边学，而不是先学习再行动"),
            ("BPT3", "action", "我认为做比想更重要"),
            ("BPT4", "knowledge", "在开始任何新事物之前，我需要充分了解相关知识"),
            ("BPT5", "knowledge", "我喜欢收集信息和研究最佳方法"),
            ("BPT6", "knowledge", "知道为什么要做某事对我很重要"),
            ("BPT7", "emotion", "我的行为很大程度上受当时情绪的影响"),
            ("BPT8", "emotion", "当我感觉不好时，很难坚持计划"),
            ("BPT9", "emotion", "情绪状态决定了我是否能完成任务"),
            ("BPT10", "relation", "有人陪伴或支持时，我更容易坚持"),
            ("BPT11", "relation", "我需要他人的鼓励才能持续行动"),
            ("BPT12", "relation", "和他人一起做事比独自做更有动力"),
            ("BPT13", "environment", "我的行为很大程度上取决于周围环境"),
            ("BPT14", "environment", "改变环境对我改变行为很有帮助"),
            ("BPT15", "environment", "当环境不支持时，我很难保持行为"),
            ("BPT16", "ambivalent", "我经常在想要改变和害怕改变之间挣扎"),
            ("BPT17", "ambivalent", "我知道应该做什么，但总是犹豫不决"),
            ("BPT18", "ambivalent", "我对改变既期待又恐惧"),
        ]
        for id_, dim, text in items_data:
            self.items.append(QuestionItem(id_, dim, text))


class CAPACITYQuestionnaire(BaseQuestionnaire):
    """CAPACITY改变潜力诊断问卷 (32题)"""

    def __init__(self, question_bank_path: str = None):
        super().__init__()
        self.id = "CAPACITY_32"
        self.name = "CAPACITY改变潜力诊断"
        self.description = "评估个体的行为改变潜力与资源"
        self.total_items = 32
        self.estimated_minutes = 8

        self.scale = ScaleConfig(
            type="likert",
            range=(1, 5),
            labels={
                "1": "完全不符合", "2": "不太符合", "3": "不确定",
                "4": "比较符合", "5": "完全符合"
            }
        )

        # CAPACITY 8维度
        self.dimensions = {
            "C1": DimensionConfig("觉察力", "Consciousness", 4, (4, 20)),
            "A1": DimensionConfig("自主感", "Autonomy", 4, (4, 20)),
            "P": DimensionConfig("匹配度", "Personality Match", 4, (4, 20)),
            "A2": DimensionConfig("资源", "Action Resources", 4, (4, 20)),
            "C2": DimensionConfig("承诺", "Commitment", 4, (4, 20)),
            "I": DimensionConfig("身份", "Identity", 4, (4, 20)),
            "T": DimensionConfig("时间", "Timeline", 4, (4, 20)),
            "Y": DimensionConfig("期待", "Yield Expectation", 4, (4, 20))
        }

        if question_bank_path:
            self._load_items(question_bank_path)
        else:
            self._init_default_items()

    def _load_items(self, path: str):
        """从题库文件加载题目"""
        with open(path, 'r', encoding='utf-8') as f:
            bank = json.load(f)

        capacity_data = bank["questionnaires"]["capacity"]
        for item_data in capacity_data["items"]:
            self.items.append(QuestionItem(
                id=item_data["id"],
                dimension=item_data["dimension"],
                text=item_data["text"]
            ))

    def _init_default_items(self):
        """初始化默认题目"""
        items_data = [
            # C1 - 觉察力
            ("CAP1", "C1", "我清楚地知道自己当前行为存在什么问题"),
            ("CAP2", "C1", "我能觉察到自己的行为模式和习惯"),
            ("CAP3", "C1", "我了解这些行为对我生活的影响"),
            ("CAP4", "C1", "我能识别触发不良行为的情境和因素"),
            # A1 - 自主感
            ("CAP5", "A1", "改变是我自己的选择，不是被迫的"),
            ("CAP6", "A1", "我有权决定是否改变以及如何改变"),
            ("CAP7", "A1", "我觉得自己能掌控改变的过程"),
            ("CAP8", "A1", "改变的方向符合我内心真正的需要"),
            # P - 匹配度
            ("CAP9", "P", "这个改变目标与我的性格特点相匹配"),
            ("CAP10", "P", "我过去有过类似成功改变的经验"),
            ("CAP11", "P", "这个目标对我来说难度适中"),
            ("CAP12", "P", "我具备实现这个改变所需的基本能力"),
            # A2 - 资源
            ("CAP13", "A2", "我有足够的时间来实施改变计划"),
            ("CAP14", "A2", "我有必要的工具和资源支持改变"),
            ("CAP15", "A2", "我的生活环境有利于这个改变"),
            ("CAP16", "A2", "我能获得他人的支持和帮助"),
            # C2 - 承诺
            ("CAP17", "C2", "我已经下定决心要进行这个改变"),
            ("CAP18", "C2", "我愿意为这个改变付出努力"),
            ("CAP19", "C2", "即使遇到困难我也会坚持"),
            ("CAP20", "C2", "我已经向他人表达了我的改变意愿"),
            # I - 身份
            ("CAP21", "I", "这个改变符合我对自己的期望"),
            ("CAP22", "I", "改变后的我会更接近理想中的自己"),
            ("CAP23", "I", "我能想象自己改变后的样子"),
            ("CAP24", "I", "这个改变与我的核心价值观一致"),
            # T - 时间
            ("CAP25", "T", "我有明确的改变时间表"),
            ("CAP26", "T", "我知道什么时候开始第一步"),
            ("CAP27", "T", "我对改变需要的时间有合理的预期"),
            ("CAP28", "T", "我能接受改变是一个渐进的过程"),
            # Y - 期待
            ("CAP29", "Y", "我清楚改变会带来什么好处"),
            ("CAP30", "Y", "这些好处对我来说很重要"),
            ("CAP31", "Y", "我相信改变带来的收益大于付出"),
            ("CAP32", "Y", "我对改变的结果有积极的期待"),
        ]
        for id_, dim, text in items_data:
            self.items.append(QuestionItem(id_, dim, text))


class SPIQuestionnaire(BaseQuestionnaire):
    """SPI成功可能性评估问卷 (50题)"""

    def __init__(self, question_bank_path: str = None):
        super().__init__()
        self.id = "SPI_50"
        self.name = "SPI成功可能性评估"
        self.description = "评估行为改变的成功可能性指数"
        self.total_items = 50
        self.estimated_minutes = 12

        self.scale = ScaleConfig(
            type="likert",
            range=(1, 5),
            labels={
                "1": "完全不符合", "2": "不太符合", "3": "不确定",
                "4": "比较符合", "5": "完全符合"
            }
        )

        # SPI 5维度 (含权重)
        self.dimensions = {
            "M": DimensionConfig("动机", "Motivation", 10, (10, 50), weight=0.30),
            "A": DimensionConfig("能力", "Ability", 10, (10, 50), weight=0.25),
            "S": DimensionConfig("支持", "Support", 10, (10, 50), weight=0.20),
            "E": DimensionConfig("环境", "Environment", 10, (10, 50), weight=0.15),
            "H": DimensionConfig("历史", "History", 10, (10, 50), weight=0.10)
        }

        self.formula = "SPI = M×0.30 + A×0.25 + S×0.20 + E×0.15 + H×0.10"

        if question_bank_path:
            self._load_items(question_bank_path)
        else:
            self._init_default_items()

    def _load_items(self, path: str):
        """从题库文件加载题目"""
        with open(path, 'r', encoding='utf-8') as f:
            bank = json.load(f)

        spi_data = bank["questionnaires"]["spi"]
        for item_data in spi_data["items"]:
            self.items.append(QuestionItem(
                id=item_data["id"],
                dimension=item_data["dimension"],
                text=item_data["text"]
            ))

    def _init_default_items(self):
        """初始化默认题目"""
        items_data = [
            # M - 动机 (1-10)
            ("SPI1", "M", "改变这个行为对我来说非常重要"),
            ("SPI2", "M", "我有强烈的意愿想要改变"),
            ("SPI3", "M", "我已经厌倦了现在的状态"),
            ("SPI4", "M", "改变会让我的生活变得更好"),
            ("SPI5", "M", "不改变会给我带来严重的后果"),
            ("SPI6", "M", "我清楚知道为什么要改变"),
            ("SPI7", "M", "改变是我主动选择的，不是被迫的"),
            ("SPI8", "M", "我对改变充满期待"),
            ("SPI9", "M", "我愿意为改变付出代价"),
            ("SPI10", "M", "我已经准备好开始改变了"),
            # A - 能力 (11-20)
            ("SPI11", "A", "我知道如何进行这个改变"),
            ("SPI12", "A", "我具备改变所需的知识"),
            ("SPI13", "A", "我有足够的技能来执行改变计划"),
            ("SPI14", "A", "我能够制定合理的改变计划"),
            ("SPI15", "A", "我能够监控自己的进度"),
            ("SPI16", "A", "我知道如何应对可能遇到的困难"),
            ("SPI17", "A", "我有足够的自控能力"),
            ("SPI18", "A", "我能够在压力下保持行动"),
            ("SPI19", "A", "我能够调整策略应对变化"),
            ("SPI20", "A", "我相信自己有能力成功改变"),
            # S - 支持 (21-30)
            ("SPI21", "S", "我的家人支持我的改变"),
            ("SPI22", "S", "我的朋友会鼓励我"),
            ("SPI23", "S", "我有可以倾诉的对象"),
            ("SPI24", "S", "有人愿意和我一起改变"),
            ("SPI25", "S", "我能获得专业的指导和帮助"),
            ("SPI26", "S", "我的社交圈支持健康的生活方式"),
            ("SPI27", "S", "我有可以学习的榜样"),
            ("SPI28", "S", "我能加入支持性的社群或团体"),
            ("SPI29", "S", "我的工作环境支持我的改变"),
            ("SPI30", "S", "需要帮助时我知道可以找谁"),
            # E - 环境 (31-40)
            ("SPI31", "E", "我的生活环境有利于这个改变"),
            ("SPI32", "E", "我有足够的时间进行改变"),
            ("SPI33", "E", "我有必要的物质资源"),
            ("SPI34", "E", "我的日常安排允许我实施改变"),
            ("SPI35", "E", "我的居住环境支持健康行为"),
            ("SPI36", "E", "我能方便地获取所需的工具和设备"),
            ("SPI37", "E", "我的经济状况允许我进行这个改变"),
            ("SPI38", "E", "我的工作压力在可控范围内"),
            ("SPI39", "E", "我没有太多外部干扰"),
            ("SPI40", "E", "我的生活相对稳定"),
            # H - 历史 (41-50)
            ("SPI41", "H", "我过去成功改变过类似的行为"),
            ("SPI42", "H", "我有坚持完成目标的记录"),
            ("SPI43", "H", "我从过去的失败中学到了经验"),
            ("SPI44", "H", "我之前的尝试让我更了解自己"),
            ("SPI45", "H", "我知道什么方法对我有效"),
            ("SPI46", "H", "我克服过比这更大的困难"),
            ("SPI47", "H", "我在逆境中能够坚持"),
            ("SPI48", "H", "我的过往经历让我更有信心"),
            ("SPI49", "H", "我善于从经验中学习"),
            ("SPI50", "H", "我相信这次会比以前做得更好"),
        ]
        for id_, dim, text in items_data:
            self.items.append(QuestionItem(id_, dim, text))


# 便捷函数：获取所有问卷实例
def get_all_questionnaires(question_bank_path: str = None) -> Dict[str, BaseQuestionnaire]:
    """获取所有问卷实例"""
    return {
        "big_five": BigFiveQuestionnaire(question_bank_path),
        "bpt6": BPT6Questionnaire(question_bank_path),
        "capacity": CAPACITYQuestionnaire(question_bank_path),
        "spi": SPIQuestionnaire(question_bank_path)
    }
