"""
行为健康数字平台 - 披露控制：AI文案重写器
Disclosure Control: AI Content Rewriter

[v14-NEW] 披露控制模块

将专业评估结论转换为用户友好的正向表达：
- "高神经质" → "你是一个情感敏锐且富有创意的人"
- "强烈抗拒阶段" → "正在审视改变的意义"
- "执行力差" → "执行力有提升空间，我们一起来提升"

重写原则：
1. 避免标签化
2. 强调成长空间而非缺陷
3. 使用积极正向的语言
4. 保持专业性但增加温度
"""
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from loguru import logger
import os


# ============================================
# 预置话术库
# ============================================

# BIG5 人格特质转换
BIG5_REWRITES = {
    # 神经质(N) 高分
    "高神经质": "你是一个情感细腻、感受力强的人",
    "高N": "你的情感敏锐度很高，这让你更能共情他人",
    "神经质得分高": "你对情绪的感知非常敏锐，这是一种独特的能力",
    "情绪不稳定": "你的情绪世界丰富多彩",
    
    # 神经质(N) 低分
    "低神经质": "你是一个情绪稳定、心态平和的人",
    
    # 外向性(E) 高分
    "高外向性": "你是一个热情开朗、善于社交的人",
    
    # 外向性(E) 低分
    "低外向性": "你是一个独立思考、享受内心世界的人",
    "内向": "你擅长深度思考，享受独处的时光",
    
    # 开放性(O) 高分
    "高开放性": "你是一个富有创意、思维活跃的人",
    
    # 开放性(O) 低分
    "低开放性": "你是一个务实稳重、脚踏实地的人",
    
    # 宜人性(A) 高分
    "高宜人性": "你是一个善解人意、乐于助人的人",
    
    # 宜人性(A) 低分
    "低宜人性": "你是一个有独立主见、坚持原则的人",
    
    # 尽责性(C) 高分
    "高尽责性": "你是一个有条理、自律性强的人",
    
    # 尽责性(C) 低分
    "低尽责性": "你是一个灵活自由、不拘小节的人",
    "执行力差": "执行力有提升空间，我们可以一起来提高",
    "自律性差": "自我管理是可以培养的能力，让我们慢慢来",
}

# TTM 阶段转换
TTM_REWRITES = {
    "前意向期": "启程准备中",
    "无知无觉": "探索期",
    "意向期": "思考期",
    "准备期": "规划期",
    "行动期": "成长期",
    "维持期": "巩固期",
    "复发": "调整期",
    "终结期": "收获期",
    
    # 负面阶段描述
    "强烈抗拒": "正在审视改变的意义",
    "抗拒阶段": "正在思考中",
    "抵触情绪": "对改变有一些疑虑，这很正常",
    "不愿改变": "目前还在观望中",
}

# BPT-6 行为模式转换
BPT6_REWRITES = {
    "矛盾型": "多元思考型",
    "情绪型": "感性驱动型",
    "环境型": "情境敏感型",
    "执行型": "行动导向型",
    "知识型": "理性思考型",
    "关系型": "人际导向型",
}

# 风险描述转换
RISK_REWRITES = {
    "高风险": "需要特别关注",
    "中风险": "需要持续关注",
    "低风险": "状态良好",
    "危险": "需要注意",
    "失败风险高": "需要更多支持",
    "预后不良": "需要更多时间和耐心",
}

# 通用负面词转换
GENERAL_REWRITES = {
    "缺陷": "成长空间",
    "问题": "关注点",
    "障碍": "挑战",
    "困难": "成长机会",
    "失败": "学习经验",
    "弱点": "可提升领域",
    "不足": "可优化之处",
    "差": "有提升空间",
}


@dataclass
class RewriteResult:
    """重写结果"""
    original: str
    rewritten: str
    changes: List[Tuple[str, str]]  # [(原词, 替换词), ...]
    confidence: float


class AIRewriter:
    """
    AI文案重写器
    
    将专业评估文案转换为用户友好的表达
    """
    
    def __init__(self):
        # 合并所有转换规则
        self.rewrites: Dict[str, str] = {}
        self.rewrites.update(BIG5_REWRITES)
        self.rewrites.update(TTM_REWRITES)
        self.rewrites.update(BPT6_REWRITES)
        self.rewrites.update(RISK_REWRITES)
        self.rewrites.update(GENERAL_REWRITES)
        
        logger.info(f"[Disclosure] AI重写器初始化: {len(self.rewrites)} 条规则")
    
    def rewrite(self, text: str, context: Optional[Dict] = None) -> RewriteResult:
        """
        重写文本
        
        Args:
            text: 原始文本
            context: 上下文（可包含ttm_stage等信息）
        
        Returns:
            RewriteResult
        """
        result = text
        changes = []
        
        # 应用预置规则
        for original, replacement in self.rewrites.items():
            if original in result:
                result = result.replace(original, replacement)
                changes.append((original, replacement))
        
        # 计算置信度（基于替换数量和文本长度）
        if changes:
            confidence = min(0.95, 0.7 + len(changes) * 0.05)
        else:
            confidence = 1.0  # 无需修改
        
        return RewriteResult(
            original=text,
            rewritten=result,
            changes=changes,
            confidence=confidence
        )
    
    def rewrite_assessment_summary(
        self,
        big5_summary: str,
        ttm_stage: str,
        bpt6_type: str,
        risk_level: str
    ) -> str:
        """
        重写评估摘要
        
        生成用户友好的综合描述
        """
        # 获取转换后的描述
        stage_desc = TTM_REWRITES.get(ttm_stage, ttm_stage)
        type_desc = BPT6_REWRITES.get(bpt6_type, bpt6_type)
        
        # 构建正向摘要
        summary = f"""
你是一个{type_desc}的人，目前正处于{stage_desc}。

{self.rewrite(big5_summary).rewritten}

我们会根据你的特点，为你定制专属的健康计划。接下来，让我们从一些小事开始，好吗？
""".strip()
        
        return summary
    
    def generate_stage_message(self, ttm_stage: str) -> str:
        """
        根据TTM阶段生成鼓励消息
        
        不暴露具体阶段名称
        """
        messages = {
            "前意向期": "最近你可能感觉到一些压力，没关系，我们先从了解开始，不急着改变。",
            "意向期": "你开始思考健康的重要性了，这是很棒的第一步！",
            "准备期": "你已经准备好迈出第一步了，我们一起来规划吧！",
            "行动期": "你正在积极行动，太棒了！保持这个节奏。",
            "维持期": "你已经坚持了一段时间，为你感到骄傲！",
            "复发": "调整期是正常的，我们一起重新找回节奏。",
            "终结期": "你已经建立了很好的健康习惯，继续保持！"
        }
        
        return messages.get(ttm_stage, "让我们一起开始健康旅程吧！")
    
    def add_custom_rule(self, original: str, replacement: str):
        """添加自定义规则"""
        self.rewrites[original] = replacement
        logger.info(f"[Disclosure] 添加重写规则: '{original}' -> '{replacement}'")
    
    async def llm_rewrite(
        self,
        text: str,
        style: str = "warm_coach"
    ) -> str:
        """
        使用LLM进行高级重写
        
        当预置规则不足时，调用LLM
        
        Args:
            text: 原始文本
            style: 风格 (warm_coach/professional/casual)
        
        Returns:
            重写后的文本
        """
        # 先尝试规则重写
        rule_result = self.rewrite(text)
        if rule_result.changes:
            return rule_result.rewritten
        
        # 如果没有匹配规则，尝试LLM重写
        try:
            from quality.llm_judge import get_llm_judge
            
            judge = get_llm_judge()
            
            prompt = f"""请将以下专业评估文本重写为用户友好的表达。

要求：
1. 移除所有专业术语和负面标签
2. 使用温暖、鼓励的语气
3. 强调成长空间而非缺陷
4. 保持原意但更加正向

原文：
"{text}"

风格：{style}

请直接输出重写后的文本，不要任何解释。"""
            
            result = await judge._call_llm(prompt)
            return result.strip() if result else text
            
        except Exception as e:
            logger.warning(f"[Disclosure] LLM重写失败: {e}")
            return rule_result.rewritten


# ============================================
# 预置正向反馈模板
# ============================================

POSITIVE_FEEDBACK_TEMPLATES = {
    # 进度反馈
    "progress_good": "你最近的状态不错，继续保持！",
    "progress_improving": "你正在进步，每一小步都很重要。",
    "progress_needs_attention": "最近可能遇到了一些挑战，没关系，我们一起面对。",
    
    # 任务反馈
    "task_completed": "太棒了！你完成了今天的任务。",
    "task_partial": "完成了一部分，已经很好了！",
    "task_missed": "今天有点忙？没关系，明天继续。",
    
    # 鼓励消息
    "encouragement_start": "每一次尝试都是进步的开始。",
    "encouragement_persist": "坚持下去，你比想象中更强大。",
    "encouragement_setback": "遇到困难是正常的，重要的是我们不放弃。",
}


def get_positive_feedback(feedback_type: str, context: Optional[Dict] = None) -> str:
    """获取正向反馈文案"""
    template = POSITIVE_FEEDBACK_TEMPLATES.get(feedback_type, "")
    
    if context and template:
        try:
            return template.format(**context)
        except KeyError:
            pass
    
    return template


# ============================================
# 全局单例
# ============================================

_ai_rewriter: Optional[AIRewriter] = None


def get_ai_rewriter() -> AIRewriter:
    """获取AI重写器"""
    global _ai_rewriter
    if _ai_rewriter is None:
        _ai_rewriter = AIRewriter()
    return _ai_rewriter
