"""
行为健康数字平台 - v14 Agent 增强模块
Enhanced Agent Framework for v14

[v14-NEW] 全新模块

在v11 Agent编排器基础上增加三类专用Agent：
1. ExplainAgent - 行为解释Agent
2. ResistanceAgent - 阻抗识别Agent  
3. SafetyAgent - 安全兜底Agent（始终启用）

设计原则：
- 不替代现有Agent系统，只是增强
- 通过装饰器模式包装原有Agent输出
- SafetyAgent始终优先执行

使用方式：
    from core.v14.agents import get_agent_enhancer
    
    enhancer = get_agent_enhancer()
    result = enhancer.process(user_id, message, original_response)
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from loguru import logger
import re


class AgentAction(str, Enum):
    """Agent动作"""
    CONTINUE = "continue"      # 继续执行
    MODIFY = "modify"          # 修改响应
    DOWNGRADE = "downgrade"    # 降级干预
    PAUSE = "pause"            # 暂停等待
    ESCALATE = "escalate"      # 升级到人工


class ResistanceType(str, Enum):
    """阻抗类型"""
    PROCRASTINATION = "procrastination"   # 拖延
    AVOIDANCE = "avoidance"               # 回避
    EMOTIONAL = "emotional"               # 情绪波动
    CAPABILITY = "capability"             # 能力不足
    ENVIRONMENTAL = "environmental"       # 环境阻碍


@dataclass
class AgentOutput:
    """Agent输出"""
    agent_name: str
    action: AgentAction
    confidence: float
    content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "agent_name": self.agent_name,
            "action": self.action.value,
            "confidence": self.confidence,
            "content": self.content,
            "metadata": self.metadata
        }


# ============================================
# 安全关键词（SafetyAgent使用）
# ============================================

SAFETY_KEYWORDS = [
    # 自伤相关
    "自杀", "自残", "不想活", "死了算了", "活着没意思",
    "结束生命", "一了百了", "解脱", "跳楼", "割腕",
    # 危险行为
    "伤害自己", "伤害别人", "报复", "杀",
    # 严重情绪
    "绝望", "崩溃了", "受不了了", "撑不下去"
]

# 阻抗信号词
RESISTANCE_KEYWORDS = {
    ResistanceType.PROCRASTINATION: [
        "明天再说", "等会儿", "下次吧", "改天", "没时间",
        "太忙了", "懒得", "不想动"
    ],
    ResistanceType.AVOIDANCE: [
        "不想做", "做不到", "算了", "放弃", "不管了",
        "随便", "无所谓"
    ],
    ResistanceType.EMOTIONAL: [
        "烦死了", "累死了", "郁闷", "焦虑", "压力大",
        "心烦", "难受", "不开心"
    ],
    ResistanceType.CAPABILITY: [
        "不会", "不懂", "太难了", "学不会", "做不好",
        "没能力"
    ],
    ResistanceType.ENVIRONMENTAL: [
        "条件不允许", "没有设备", "家人不支持", "工作太忙",
        "没钱", "没地方"
    ]
}


# ============================================
# Agent 基类
# ============================================

class BaseV14Agent:
    """v14 Agent基类"""
    
    def __init__(self, name: str):
        self.name = name
        logger.info(f"[v14] {name} 初始化完成")
    
    def process(
        self,
        user_id: int,
        message: str,
        context: Dict[str, Any]
    ) -> AgentOutput:
        """处理消息（子类实现）"""
        raise NotImplementedError


# ============================================
# SafetyAgent - 安全兜底Agent
# ============================================

class SafetyAgent(BaseV14Agent):
    """
    安全兜底Agent [v14-NEW]
    
    检测危急关键词，立即升级到人工
    这个Agent始终启用，专家不可配置
    """
    
    def __init__(self):
        super().__init__("SafetyAgent")
        self.keywords = SAFETY_KEYWORDS
    
    def process(
        self,
        user_id: int,
        message: str,
        context: Dict[str, Any]
    ) -> AgentOutput:
        """检测安全风险"""
        message_lower = message.lower()
        
        detected = []
        for keyword in self.keywords:
            if keyword in message_lower:
                detected.append(keyword)
        
        if detected:
            logger.warning(f"[v14] SafetyAgent 检测到风险: user={user_id} keywords={detected}")
            
            return AgentOutput(
                agent_name=self.name,
                action=AgentAction.ESCALATE,
                confidence=0.95,
                content="我注意到你可能正在经历一些困难。你的感受很重要，我建议你和专业人士谈谈。需要我帮你联系健康管理师吗？",
                metadata={
                    "risk_level": "high",
                    "detected_keywords": detected,
                    "escalate_to": "human_coach",
                    "reason": "safety_concern"
                }
            )
        
        return AgentOutput(
            agent_name=self.name,
            action=AgentAction.CONTINUE,
            confidence=1.0,
            metadata={"risk_level": "none"}
        )


# ============================================
# ResistanceAgent - 阻抗识别Agent
# ============================================

class ResistanceAgent(BaseV14Agent):
    """
    阻抗识别Agent [v14-NEW]
    
    识别用户的拖延、抗拒、情绪波动等阻抗信号
    判断是阶段问题、能力问题还是情绪问题
    """
    
    def __init__(self):
        super().__init__("ResistanceAgent")
        self.keywords = RESISTANCE_KEYWORDS
    
    def process(
        self,
        user_id: int,
        message: str,
        context: Dict[str, Any]
    ) -> AgentOutput:
        """识别阻抗信号"""
        message_lower = message.lower()
        
        detected_types: Dict[ResistanceType, List[str]] = {}
        
        for resistance_type, keywords in self.keywords.items():
            matches = [kw for kw in keywords if kw in message_lower]
            if matches:
                detected_types[resistance_type] = matches
        
        if not detected_types:
            return AgentOutput(
                agent_name=self.name,
                action=AgentAction.CONTINUE,
                confidence=1.0,
                metadata={"resistance_detected": False}
            )
        
        # 分析主要阻抗类型
        primary_type = max(detected_types.keys(), 
                          key=lambda t: len(detected_types[t]))
        
        # 根据阻抗类型决定动作
        action = AgentAction.MODIFY
        confidence = 0.75
        
        if primary_type == ResistanceType.EMOTIONAL:
            # 情绪问题 - 可能需要降级
            action = AgentAction.DOWNGRADE
            confidence = 0.8
        elif primary_type == ResistanceType.CAPABILITY:
            # 能力问题 - 可能需要调整任务
            action = AgentAction.MODIFY
            confidence = 0.7
        
        # 多种阻抗同时出现，考虑暂停
        if len(detected_types) >= 3:
            action = AgentAction.PAUSE
            confidence = 0.85
        
        logger.info(f"[v14] ResistanceAgent 识别到阻抗: user={user_id} "
                   f"types={list(detected_types.keys())}")
        
        return AgentOutput(
            agent_name=self.name,
            action=action,
            confidence=confidence,
            metadata={
                "resistance_detected": True,
                "primary_type": primary_type.value,
                "all_types": {t.value: kws for t, kws in detected_types.items()},
                "suggestion": self._get_suggestion(primary_type)
            }
        )
    
    def _get_suggestion(self, resistance_type: ResistanceType) -> str:
        """根据阻抗类型给出建议"""
        suggestions = {
            ResistanceType.PROCRASTINATION: "考虑降低任务难度，设置更小的目标",
            ResistanceType.AVOIDANCE: "表达理解，询问具体困难",
            ResistanceType.EMOTIONAL: "先关注情绪支持，暂缓任务要求",
            ResistanceType.CAPABILITY: "提供更详细的指导或示范",
            ResistanceType.ENVIRONMENTAL: "帮助寻找替代方案或资源"
        }
        return suggestions.get(resistance_type, "进一步了解情况")


# ============================================
# ExplainAgent - 行为解释Agent
# ============================================

class ExplainAgent(BaseV14Agent):
    """
    行为解释Agent [v14-NEW]
    
    把"为什么是这个任务"讲成"符合你现阶段的理由"
    原则：不暴露评估，但让人被理解
    """
    
    def __init__(self):
        super().__init__("ExplainAgent")
        
        # 阶段-解释模板映射
        self.stage_templates = {
            "S0": "现在最重要的是让你感受到被支持，所以{task_hint}",
            "S1": "我注意到你开始有了一些改变的想法，{task_hint}可以帮助你更清晰地了解自己",
            "S2": "你已经准备好迈出第一步了，{task_hint}是一个很好的开始",
            "S3": "你正在养成新习惯，{task_hint}可以帮你巩固这个进展",
            "S4": "你已经做得很好了，{task_hint}可以帮你保持这个状态",
            "S5": "为了让你的进步更持久，{task_hint}是很有帮助的",
            "S6": "你已经形成了很好的健康习惯，{task_hint}可以让你的生活更健康"
        }
    
    def process(
        self,
        user_id: int,
        message: str,
        context: Dict[str, Any]
    ) -> AgentOutput:
        """生成行为解释"""
        # 获取用户阶段（从context中）
        user_stage = context.get("behavior_stage", "S2")
        task_hint = context.get("task_hint", "这个小任务")
        
        # 检测是否是询问原因的消息
        why_patterns = ["为什么", "为啥", "原因", "有什么用", "干嘛"]
        is_asking_why = any(p in message for p in why_patterns)
        
        if not is_asking_why:
            return AgentOutput(
                agent_name=self.name,
                action=AgentAction.CONTINUE,
                confidence=1.0,
                metadata={"explain_needed": False}
            )
        
        # 生成解释
        template = self.stage_templates.get(user_stage, self.stage_templates["S2"])
        explanation = template.format(task_hint=task_hint)
        
        logger.info(f"[v14] ExplainAgent 生成解释: user={user_id} stage={user_stage}")
        
        return AgentOutput(
            agent_name=self.name,
            action=AgentAction.MODIFY,
            confidence=0.8,
            content=explanation,
            metadata={
                "explain_needed": True,
                "user_stage": user_stage,
                "template_used": user_stage
            }
        )


# ============================================
# Agent 增强器（编排器）
# ============================================

class AgentEnhancer:
    """
    Agent增强器 [v14-NEW]
    
    编排v14新增Agent，增强原有响应
    执行顺序：SafetyAgent → ResistanceAgent → ExplainAgent
    """
    
    def __init__(self):
        from core.v14.config import feature_flags
        
        self.agents: List[BaseV14Agent] = []
        
        # SafetyAgent始终启用
        self.agents.append(SafetyAgent())
        
        # 根据配置启用其他Agent
        if feature_flags.ENABLE_RESISTANCE_AGENT:
            self.agents.append(ResistanceAgent())
        
        if feature_flags.ENABLE_EXPLAIN_AGENT:
            self.agents.append(ExplainAgent())
        
        logger.info(f"[v14] AgentEnhancer 初始化完成, 已加载Agent: "
                   f"{[a.name for a in self.agents]}")
    
    def process(
        self,
        user_id: int,
        message: str,
        original_response: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        处理消息，增强原有响应
        
        Args:
            user_id: 用户ID
            message: 用户消息
            original_response: 原有响应
            context: 上下文信息
        
        Returns:
            增强后的响应
        """
        context = context or {}
        outputs: List[AgentOutput] = []
        
        final_response = original_response
        final_action = AgentAction.CONTINUE
        
        # 按顺序执行Agent
        for agent in self.agents:
            try:
                output = agent.process(user_id, message, context)
                outputs.append(output)
                
                # 如果是ESCALATE或PAUSE，立即终止
                if output.action in (AgentAction.ESCALATE, AgentAction.PAUSE):
                    final_action = output.action
                    if output.content:
                        final_response = output.content
                    break
                
                # 如果是MODIFY且有内容，追加到响应
                if output.action == AgentAction.MODIFY and output.content:
                    final_response = f"{original_response}\n\n{output.content}"
                
                # 如果是DOWNGRADE，记录需要降级
                if output.action == AgentAction.DOWNGRADE:
                    final_action = AgentAction.DOWNGRADE
                    
            except Exception as e:
                logger.error(f"[v14] Agent {agent.name} 执行失败: {e}")
                continue
        
        result = {
            "user_id": user_id,
            "original_response": original_response,
            "enhanced_response": final_response,
            "final_action": final_action.value,
            "agent_outputs": [o.to_dict() for o in outputs],
            "modified": final_response != original_response
        }
        
        if final_action == AgentAction.ESCALATE:
            logger.warning(f"[v14] 消息需要升级到人工: user={user_id}")
        
        return result


# ============================================
# 全局单例
# ============================================

_agent_enhancer: Optional[AgentEnhancer] = None


def get_agent_enhancer() -> Optional[AgentEnhancer]:
    """获取Agent增强器单例"""
    global _agent_enhancer
    
    from core.v14.config import is_feature_enabled
    
    if not is_feature_enabled("ENABLE_V14_AGENTS"):
        # 即使v14 Agent未启用，SafetyAgent仍然工作
        if is_feature_enabled("ENABLE_SAFETY_AGENT"):
            if _agent_enhancer is None:
                _agent_enhancer = AgentEnhancer()
            return _agent_enhancer
        return None
    
    if _agent_enhancer is None:
        _agent_enhancer = AgentEnhancer()
    
    return _agent_enhancer
