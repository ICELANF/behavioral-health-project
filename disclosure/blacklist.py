"""
行为健康数字平台 - 披露控制：禁词库
Disclosure Control: Blacklist Configuration

[v14-NEW] 披露控制模块

核心原则："黑盒评估，白盒干预"
- 专业术语不应直接暴露给用户
- 避免"标签效应"带来的心理暗示
- 敏感信息需专家审核后才能披露

禁词分类：
- clinical: 临床诊断词（绝对禁止）
- personality: 人格标签词（需转换）
- ttm: 阶段术语（需语境化）
- risk: 风险描述词（需脱敏）
"""
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import re


class BlacklistCategory(str, Enum):
    """禁词类别"""
    CLINICAL = "clinical"          # 临床诊断词
    PERSONALITY = "personality"    # 人格标签词
    TTM_STAGE = "ttm_stage"        # 阶段术语
    RISK = "risk"                  # 风险描述词
    BEHAVIOR = "behavior"          # 行为缺陷词


class SensitivityLevel(str, Enum):
    """敏感度等级"""
    CRITICAL = "critical"    # 绝对禁止（红色）
    HIGH = "high"            # 高度敏感（橙色）
    MODERATE = "moderate"    # 中度敏感（黄色）
    LOW = "low"              # 轻度敏感（灰色）


@dataclass
class BlacklistWord:
    """禁词定义"""
    word: str
    category: BlacklistCategory
    level: SensitivityLevel
    suggested_replacement: Optional[str] = None
    context_hint: Optional[str] = None


# ============================================
# 默认禁词库
# ============================================

DEFAULT_BLACKLIST: List[BlacklistWord] = [
    # === 临床诊断词 (CRITICAL - 绝对禁止) ===
    BlacklistWord("抑郁症", BlacklistCategory.CLINICAL, SensitivityLevel.CRITICAL,
                  "情绪低落倾向", "请勿诊断，建议就医"),
    BlacklistWord("焦虑症", BlacklistCategory.CLINICAL, SensitivityLevel.CRITICAL,
                  "压力感知敏感", "请勿诊断，建议就医"),
    BlacklistWord("人格障碍", BlacklistCategory.CLINICAL, SensitivityLevel.CRITICAL,
                  None, "严禁使用"),
    BlacklistWord("神经症", BlacklistCategory.CLINICAL, SensitivityLevel.CRITICAL,
                  None, "严禁使用"),
    BlacklistWord("精神分裂", BlacklistCategory.CLINICAL, SensitivityLevel.CRITICAL,
                  None, "严禁使用"),
    BlacklistWord("双相情感障碍", BlacklistCategory.CLINICAL, SensitivityLevel.CRITICAL,
                  None, "严禁使用"),
    BlacklistWord("病症", BlacklistCategory.CLINICAL, SensitivityLevel.CRITICAL,
                  "健康状况", "避免病理化"),
    BlacklistWord("疾病", BlacklistCategory.CLINICAL, SensitivityLevel.CRITICAL,
                  "健康挑战", "避免病理化"),
    BlacklistWord("诊断", BlacklistCategory.CLINICAL, SensitivityLevel.CRITICAL,
                  "评估", "非医疗场景"),
    BlacklistWord("治疗", BlacklistCategory.CLINICAL, SensitivityLevel.CRITICAL,
                  "健康管理", "非医疗场景"),
    
    # === 人格标签词 (HIGH - 需转换) ===
    BlacklistWord("神经质", BlacklistCategory.PERSONALITY, SensitivityLevel.HIGH,
                  "情感敏锐", "BIG5-N维度"),
    BlacklistWord("高神经质", BlacklistCategory.PERSONALITY, SensitivityLevel.HIGH,
                  "情感细腻且敏锐", "BIG5-N高分"),
    BlacklistWord("低尽责性", BlacklistCategory.PERSONALITY, SensitivityLevel.HIGH,
                  "灵活自由型", "BIG5-C低分"),
    BlacklistWord("低外向性", BlacklistCategory.PERSONALITY, SensitivityLevel.HIGH,
                  "独立思考型", "BIG5-E低分"),
    BlacklistWord("低宜人性", BlacklistCategory.PERSONALITY, SensitivityLevel.HIGH,
                  "独立主见型", "BIG5-A低分"),
    BlacklistWord("情绪不稳", BlacklistCategory.PERSONALITY, SensitivityLevel.HIGH,
                  "情绪丰富", "避免负面标签"),
    BlacklistWord("缺陷", BlacklistCategory.PERSONALITY, SensitivityLevel.HIGH,
                  "成长空间", "积极重构"),
    BlacklistWord("问题人格", BlacklistCategory.PERSONALITY, SensitivityLevel.HIGH,
                  None, "严禁使用"),
    
    # === 阶段术语 (MODERATE - 需语境化) ===
    BlacklistWord("无知无觉", BlacklistCategory.TTM_STAGE, SensitivityLevel.MODERATE,
                  "探索期", "TTM前意向阶段"),
    BlacklistWord("前意向期", BlacklistCategory.TTM_STAGE, SensitivityLevel.MODERATE,
                  "启程准备中", "TTM专业术语"),
    BlacklistWord("强烈抗拒", BlacklistCategory.TTM_STAGE, SensitivityLevel.MODERATE,
                  "审慎观望中", "避免对抗感"),
    BlacklistWord("抗拒阶段", BlacklistCategory.TTM_STAGE, SensitivityLevel.MODERATE,
                  "思考期", "避免负面标签"),
    BlacklistWord("复发", BlacklistCategory.TTM_STAGE, SensitivityLevel.MODERATE,
                  "调整期", "避免失败感"),
    BlacklistWord("失败风险", BlacklistCategory.TTM_STAGE, SensitivityLevel.MODERATE,
                  "需要更多支持", "积极重构"),
    
    # === 风险描述词 (HIGH - 需脱敏) ===
    BlacklistWord("高风险", BlacklistCategory.RISK, SensitivityLevel.HIGH,
                  "需要关注", "脱敏处理"),
    BlacklistWord("危险", BlacklistCategory.RISK, SensitivityLevel.HIGH,
                  "需要注意", "脱敏处理"),
    BlacklistWord("自伤", BlacklistCategory.RISK, SensitivityLevel.CRITICAL,
                  None, "需专家介入"),
    BlacklistWord("自杀", BlacklistCategory.RISK, SensitivityLevel.CRITICAL,
                  None, "需专家介入"),
    BlacklistWord("死亡", BlacklistCategory.RISK, SensitivityLevel.CRITICAL,
                  None, "敏感话题"),
    
    # === 行为缺陷词 (MODERATE - 需重构) ===
    BlacklistWord("执行力差", BlacklistCategory.BEHAVIOR, SensitivityLevel.MODERATE,
                  "执行力有提升空间", "积极重构"),
    BlacklistWord("意志力薄弱", BlacklistCategory.BEHAVIOR, SensitivityLevel.MODERATE,
                  "需要更多支持", "积极重构"),
    BlacklistWord("懒惰", BlacklistCategory.BEHAVIOR, SensitivityLevel.MODERATE,
                  "能量管理中", "避免道德评判"),
    BlacklistWord("拖延", BlacklistCategory.BEHAVIOR, SensitivityLevel.LOW,
                  "时间管理习惯", "中性描述"),
]


class BlacklistManager:
    """
    禁词库管理器
    
    功能：
    - 检测文本中的敏感词
    - 提供替换建议
    - 支持波浪线标记
    """
    
    def __init__(self, words: Optional[List[BlacklistWord]] = None):
        self.words = words or DEFAULT_BLACKLIST
        self._build_index()
        logger.info(f"[Disclosure] 禁词库加载完成: {len(self.words)} 个词条")
    
    def _build_index(self):
        """构建索引"""
        self._word_map: Dict[str, BlacklistWord] = {w.word: w for w in self.words}
        self._by_category: Dict[BlacklistCategory, List[BlacklistWord]] = {}
        self._by_level: Dict[SensitivityLevel, List[BlacklistWord]] = {}
        
        for w in self.words:
            self._by_category.setdefault(w.category, []).append(w)
            self._by_level.setdefault(w.level, []).append(w)
    
    def detect(self, text: str) -> List[Tuple[BlacklistWord, int, int]]:
        """
        检测文本中的敏感词
        
        Returns:
            [(禁词对象, 起始位置, 结束位置), ...]
        """
        results = []
        for word, bw in self._word_map.items():
            start = 0
            while True:
                pos = text.find(word, start)
                if pos == -1:
                    break
                results.append((bw, pos, pos + len(word)))
                start = pos + 1
        
        # 按位置排序
        results.sort(key=lambda x: x[1])
        return results
    
    def contains_sensitive(self, text: str, min_level: SensitivityLevel = SensitivityLevel.LOW) -> bool:
        """检查是否包含敏感词"""
        level_order = [SensitivityLevel.LOW, SensitivityLevel.MODERATE, 
                       SensitivityLevel.HIGH, SensitivityLevel.CRITICAL]
        min_idx = level_order.index(min_level)
        
        detections = self.detect(text)
        for bw, _, _ in detections:
            if level_order.index(bw.level) >= min_idx:
                return True
        return False
    
    def highlight_html(self, text: str) -> str:
        """
        生成带波浪线标记的HTML
        
        用于专家工作台实时预览
        """
        detections = self.detect(text)
        if not detections:
            return text
        
        # 从后往前替换，避免位置偏移
        result = text
        for bw, start, end in reversed(detections):
            word = text[start:end]
            color = {
                SensitivityLevel.CRITICAL: "red",
                SensitivityLevel.HIGH: "orange",
                SensitivityLevel.MODERATE: "#DAA520",
                SensitivityLevel.LOW: "gray"
            }.get(bw.level, "red")
            
            replacement = bw.suggested_replacement or "需替换"
            html = (f'<span style="text-decoration: underline wavy {color}; color: {color};" '
                   f'title="禁词: {word} | 建议替换: {replacement}">{word}</span>')
            result = result[:start] + html + result[end:]
        
        return result
    
    def auto_replace(self, text: str, level: SensitivityLevel = SensitivityLevel.MODERATE) -> str:
        """
        自动替换敏感词
        
        只替换有suggested_replacement的词
        """
        level_order = [SensitivityLevel.LOW, SensitivityLevel.MODERATE, 
                       SensitivityLevel.HIGH, SensitivityLevel.CRITICAL]
        min_idx = level_order.index(level)
        
        result = text
        for word, bw in self._word_map.items():
            if level_order.index(bw.level) >= min_idx and bw.suggested_replacement:
                result = result.replace(word, bw.suggested_replacement)
        
        return result
    
    def get_replacement_suggestions(self, text: str) -> Dict[str, str]:
        """获取替换建议"""
        detections = self.detect(text)
        suggestions = {}
        for bw, start, end in detections:
            word = text[start:end]
            if bw.suggested_replacement:
                suggestions[word] = bw.suggested_replacement
        return suggestions
    
    def get_by_category(self, category: BlacklistCategory) -> List[BlacklistWord]:
        """按类别获取禁词"""
        return self._by_category.get(category, [])
    
    def get_critical_words(self) -> List[str]:
        """获取绝对禁止词列表"""
        return [w.word for w in self._by_level.get(SensitivityLevel.CRITICAL, [])]
    
    def add_word(self, word: BlacklistWord):
        """添加禁词"""
        self.words.append(word)
        self._build_index()
    
    def to_dict(self) -> Dict:
        """导出为字典"""
        return {
            cat.value: [w.word for w in words]
            for cat, words in self._by_category.items()
        }


# ============================================
# 全局单例
# ============================================

_blacklist_manager: Optional[BlacklistManager] = None


def get_blacklist_manager() -> BlacklistManager:
    """获取禁词库管理器"""
    global _blacklist_manager
    if _blacklist_manager is None:
        _blacklist_manager = BlacklistManager()
    return _blacklist_manager
