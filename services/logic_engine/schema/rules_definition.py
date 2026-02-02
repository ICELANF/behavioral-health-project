"""
行为健康数字平台 - 行为母库规范定义
Behavior Library Schema Definition

[v15-NEW] 逻辑引擎模块

核心设计理念：
- 将业务逻辑从Python硬编码中剥离
- 转化为可动态加载的JSON配置
- 支持专家无代码修改行为规则

母库结构：
1. stages: TTM阶段定义
2. trigger_tags: 触发标签规则
3. action_packages: 干预动作包
4. policy_gates: 策略门控
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Literal
from enum import Enum
from datetime import datetime


# ============================================
# 枚举定义
# ============================================

class RiskLevel(str, Enum):
    """风险等级"""
    L1 = "L1"  # 低风险 - 自动处理
    L2 = "L2"  # 中低风险 - 记录日志
    L3 = "L3"  # 中高风险 - 通知教练
    L4 = "L4"  # 高风险 - 紧急升级


class TriggerPriority(str, Enum):
    """触发优先级"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class RenderType(str, Enum):
    """UI渲染类型"""
    INTERACTIVE_CARD = "INTERACTIVE_CARD"
    QUICK_REPLY = "QUICK_REPLY"
    SURVEY_MINI = "SURVEY_MINI"
    NOTIFICATION = "NOTIFICATION"
    COMPANION_MESSAGE = "COMPANION_MESSAGE"
    TASK_CARD = "TASK_CARD"
    PROGRESS_TRACKER = "PROGRESS_TRACKER"


class ComponentType(str, Enum):
    """UI组件类型"""
    TEXT = "TEXT"
    BUTTON = "BUTTON"
    SLIDER = "SLIDER"
    CHECKBOX = "CHECKBOX"
    RADIO = "RADIO"
    INPUT = "INPUT"
    TEXTAREA = "TEXTAREA"
    IMAGE = "IMAGE"
    EMOJI_PICKER = "EMOJI_PICKER"
    DATE_PICKER = "DATE_PICKER"
    TIME_PICKER = "TIME_PICKER"


class Visibility(str, Enum):
    """可见性"""
    CLIENT_ONLY = "client_only"      # 仅患者可见
    COACH_ONLY = "coach_only"        # 仅教练可见
    EXPERT_ONLY = "expert_only"      # 仅专家可见
    ALL = "all"                      # 所有人可见


class AuditLevel(str, Enum):
    """审计等级"""
    L0 = "L0"  # 无需审计
    L1 = "L1"  # 记录日志
    L2 = "L2"  # 需要复核
    L3 = "L3"  # 需要双重审核


# ============================================
# 阶段定义 (TTM Stages)
# ============================================

class StageDefinition(BaseModel):
    """阶段定义"""
    id: str = Field(..., description="阶段ID，如 S0, S1")
    name: str = Field(..., description="阶段名称")
    name_display: str = Field(..., description="面向用户的显示名称（脱敏）")
    description: str = Field(..., description="阶段描述")
    next_possible: List[str] = Field(default_factory=list, description="可能的下一阶段")
    
    # 阶段特性
    intervention_intensity: Literal["minimal", "moderate", "active", "intensive"] = "moderate"
    allow_action_push: bool = Field(True, description="是否允许主动推送行动")
    
    # 教练端描述
    coach_guidance: Optional[str] = Field(None, description="给教练的指导建议")


# ============================================
# 触发规则定义 (Trigger Rules)
# ============================================

class ConditionExpression(BaseModel):
    """条件表达式"""
    field: str = Field(..., description="字段名，如 user.age, snippet.sentiment")
    operator: Literal["==", "!=", ">", "<", ">=", "<=", "in", "not_in", "contains", "matches"] = "=="
    value: Any = Field(..., description="比较值")
    
    def to_python_expr(self) -> str:
        """转换为Python表达式"""
        if self.operator == "in":
            return f"{self.field} in {self.value}"
        elif self.operator == "not_in":
            return f"{self.field} not in {self.value}"
        elif self.operator == "contains":
            return f"'{self.value}' in {self.field}"
        elif self.operator == "matches":
            return f"re.match(r'{self.value}', {self.field})"
        else:
            if isinstance(self.value, str):
                return f"{self.field} {self.operator} '{self.value}'"
            return f"{self.field} {self.operator} {self.value}"


class TriggerRule(BaseModel):
    """触发规则"""
    id: str = Field(..., description="规则ID")
    name: str = Field(..., description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    
    # 条件定义
    condition: str = Field(..., description="条件表达式，如 snippet.sentiment == 'negative'")
    conditions_advanced: Optional[List[ConditionExpression]] = Field(
        None, description="结构化条件（用于可视化编辑）"
    )
    keyword_match: Optional[List[str]] = Field(None, description="关键词匹配列表")
    
    # 触发特性
    risk_level: RiskLevel = Field(RiskLevel.L1, description="风险等级")
    priority: TriggerPriority = Field(TriggerPriority.MEDIUM, description="优先级")
    
    # 关联动作
    action_ref: str = Field(..., description="对应动作包ID")
    
    # 适用范围
    applicable_stages: Optional[List[str]] = Field(None, description="适用的TTM阶段")
    applicable_bpt_types: Optional[List[str]] = Field(None, description="适用的BPT行为类型")
    
    # 冷却控制
    cooldown_minutes: int = Field(0, description="触发后冷却时间（分钟）")
    max_daily_triggers: int = Field(10, description="每日最大触发次数")
    
    # 启用状态
    enabled: bool = Field(True, description="是否启用")
    
    @validator('condition')
    def validate_condition(cls, v):
        """验证条件表达式安全性"""
        # 禁止危险操作
        dangerous_keywords = ['import', 'exec', 'eval', 'open', 'os.', 'sys.', '__']
        for keyword in dangerous_keywords:
            if keyword in v:
                raise ValueError(f"条件表达式包含不安全的关键词: {keyword}")
        return v


# ============================================
# 动作包定义 (Action Packages)
# ============================================

class UIComponent(BaseModel):
    """UI组件定义"""
    type: ComponentType
    id: str = Field(..., description="组件ID")
    label: Optional[str] = None
    text: Optional[str] = None
    placeholder: Optional[str] = None
    
    # 组件特定属性
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    options: Optional[List[Dict[str, str]]] = None
    
    # 动作
    action: Optional[str] = Field(None, description="点击动作，如 SUBMIT_DATA, DISMISS")
    
    # 样式
    style: Optional[Dict[str, str]] = None


class PolicyGate(BaseModel):
    """策略门控"""
    visibility: Visibility = Visibility.CLIENT_ONLY
    audit_level: AuditLevel = AuditLevel.L1
    require_expert_approval: bool = False
    disclosure_level: Literal["full", "partial", "none"] = "partial"


class ActionPayload(BaseModel):
    """动作负载"""
    title: Optional[str] = None
    content: Optional[str] = None
    subtitle: Optional[str] = None
    image_url: Optional[str] = None
    
    # UI组件
    components: List[UIComponent] = Field(default_factory=list)
    
    # 快捷回复选项
    quick_replies: Optional[List[Dict[str, str]]] = None
    
    # 扩展数据
    extra_data: Optional[Dict[str, Any]] = None


class ActionPackage(BaseModel):
    """干预动作包 - Action-to-UI 协议"""
    action_id: str = Field(..., description="动作包ID")
    name: str = Field(..., description="动作包名称")
    description: Optional[str] = None
    
    # 渲染配置
    render_type: RenderType = RenderType.COMPANION_MESSAGE
    payload: ActionPayload
    
    # 策略门控
    policy_gate: PolicyGate = Field(default_factory=PolicyGate)
    
    # 分发配置
    target_roles: List[Visibility] = Field(
        default_factory=lambda: [Visibility.CLIENT_ONLY]
    )
    
    # 触发后动作
    on_complete_action: Optional[str] = Field(None, description="完成后触发的动作")
    on_dismiss_action: Optional[str] = Field(None, description="取消后触发的动作")
    
    # 有效期
    expires_in_hours: Optional[int] = Field(None, description="有效期（小时）")
    
    # 版本控制
    version: str = "1.0"
    enabled: bool = True


# ============================================
# 行为母库完整定义
# ============================================

class BehaviorLibrary(BaseModel):
    """行为母库"""
    version: str = Field(..., description="母库版本")
    name: str = Field("default", description="母库名称")
    description: Optional[str] = None
    
    # 阶段定义
    stages: Dict[str, StageDefinition] = Field(default_factory=dict)
    
    # 触发规则
    triggers: List[TriggerRule] = Field(default_factory=list)
    
    # 动作包
    action_packages: Dict[str, ActionPackage] = Field(default_factory=dict)
    
    # 元信息
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    author: Optional[str] = None
    
    def get_trigger_by_id(self, trigger_id: str) -> Optional[TriggerRule]:
        """根据ID获取触发规则"""
        for trigger in self.triggers:
            if trigger.id == trigger_id:
                return trigger
        return None
    
    def get_action_by_id(self, action_id: str) -> Optional[ActionPackage]:
        """根据ID获取动作包"""
        return self.action_packages.get(action_id)
    
    def get_triggers_by_risk_level(self, level: RiskLevel) -> List[TriggerRule]:
        """按风险等级获取触发规则"""
        return [t for t in self.triggers if t.risk_level == level]
    
    def get_triggers_for_stage(self, stage_id: str) -> List[TriggerRule]:
        """获取适用于特定阶段的触发规则"""
        return [
            t for t in self.triggers 
            if t.applicable_stages is None or stage_id in t.applicable_stages
        ]


# ============================================
# 验证工具
# ============================================

class RuleValidator:
    """规则验证器"""
    
    @staticmethod
    def validate_condition(condition: str) -> tuple[bool, Optional[str]]:
        """验证条件表达式"""
        # 禁止危险操作
        dangerous = ['import', 'exec', 'eval', 'open', 'os.', 'sys.', '__', 'lambda']
        for keyword in dangerous:
            if keyword in condition:
                return False, f"包含不安全的关键词: {keyword}"
        
        # 检查语法
        try:
            compile(condition, '<string>', 'eval')
            return True, None
        except SyntaxError as e:
            return False, f"语法错误: {str(e)}"
    
    @staticmethod
    def validate_library(library: BehaviorLibrary) -> tuple[bool, List[str]]:
        """验证整个母库"""
        errors = []
        
        # 验证阶段转换
        all_stage_ids = set(library.stages.keys())
        for stage_id, stage in library.stages.items():
            for next_id in stage.next_possible:
                if next_id not in all_stage_ids:
                    errors.append(f"阶段 {stage_id} 引用了不存在的下一阶段: {next_id}")
        
        # 验证触发规则引用的动作包
        all_action_ids = set(library.action_packages.keys())
        for trigger in library.triggers:
            if trigger.action_ref not in all_action_ids:
                errors.append(f"触发规则 {trigger.id} 引用了不存在的动作包: {trigger.action_ref}")
            
            # 验证条件表达式
            valid, error = RuleValidator.validate_condition(trigger.condition)
            if not valid:
                errors.append(f"触发规则 {trigger.id} 的条件表达式无效: {error}")
        
        return len(errors) == 0, errors
