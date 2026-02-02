"""
行为健康数字平台 - 四级权限管理模块
Four-Level Permission Management

[v14.1-NEW] 权限管理模块

四级权限架构：
┌─────────────────────────────────────────────────────────────┐
│  第一层：患者端 — 只参与，不知晓                              │
│  - 做：完成问卷、日常打卡、健康数据采集                        │
│  - 看：正向激励信息，不出现分类标签                           │
│  - 不看：行为阶段、风险等级、人格分型等敏感评估结果             │
├─────────────────────────────────────────────────────────────┤
│  第二层：教练端 — 看到结果，执行干预                          │
│  - 看：学员的行为阶段、风险等级、评估报告摘要                  │
│  - 做：根据评估结果选择干预策略，审核AI建议后推送               │
│  - 不能做：不能修改评估结果本身，只能标注观察备注               │
├─────────────────────────────────────────────────────────────┤
│  第三层：专家/督导端 — 审核确认                               │
│  - 看：完整评估报告（含量表原始分、AI分析）                    │
│  - 做：审核评估结果、标注是否可向患者披露、处理敏感案例上报      │
│  - 权限：可以覆盖/修正系统自动评估的阶段判定                   │
├─────────────────────────────────────────────────────────────┤
│  第四层：管理员端 — 系统配置                                  │
│  - 做：配置评估量表、设置披露规则、查看整体统计                 │
│  - 不看：个人敏感数据（脱敏后的统计数据除外）                  │
└─────────────────────────────────────────────────────────────┘
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
from loguru import logger


class PermissionLevel(int, Enum):
    """权限等级"""
    PATIENT = 1      # 患者端
    COACH = 2        # 教练端
    EXPERT = 3       # 专家/督导端
    ADMIN = 4        # 管理员端


class DataCategory(str, Enum):
    """数据类别"""
    # 基础信息
    BASIC_PROFILE = "basic_profile"              # 基础档案
    HEALTH_GOALS = "health_goals"                # 健康目标
    
    # 评估数据
    QUESTIONNAIRE_ANSWERS = "questionnaire_answers"  # 问卷答案
    BIG5_SCORES = "big5_scores"                  # 大五人格分数
    BIG5_INTERPRETATION = "big5_interpretation"  # 大五人格解读
    BPT6_TYPE = "bpt6_type"                      # 行为模式分型
    TTM_STAGE = "ttm_stage"                      # 改变阶段
    TTM_STAGE_LABEL = "ttm_stage_label"          # 阶段标签名称
    CAPACITY_SCORE = "capacity_score"            # 改变力得分
    SPI_SCORE = "spi_score"                      # 成功可能性指数
    RISK_LEVEL = "risk_level"                    # 风险等级
    
    # 健康数据
    DAILY_CHECKIN = "daily_checkin"              # 日常打卡
    DEVICE_DATA = "device_data"                  # 设备数据
    CGM_DATA = "cgm_data"                        # 血糖数据
    
    # 干预数据
    INTERVENTION_PLAN = "intervention_plan"      # 干预计划
    AI_RECOMMENDATIONS = "ai_recommendations"    # AI建议
    COACH_NOTES = "coach_notes"                  # 教练备注
    
    # 敏感数据
    MENTAL_HEALTH_RISK = "mental_health_risk"    # 心理健康风险
    RAW_ASSESSMENT = "raw_assessment"            # 原始评估数据
    EXPERT_NOTES = "expert_notes"                # 专家备注
    AUDIT_LOG = "audit_log"                      # 审计日志


class ActionType(str, Enum):
    """操作类型"""
    VIEW = "view"                # 查看
    CREATE = "create"            # 创建
    EDIT = "edit"                # 编辑
    DELETE = "delete"            # 删除
    APPROVE = "approve"          # 审批
    OVERRIDE = "override"        # 覆盖/修正
    EXPORT = "export"            # 导出
    SHARE = "share"              # 分享/披露


# ============================================
# 权限矩阵定义
# ============================================

# 数据查看权限矩阵
VIEW_PERMISSIONS: Dict[DataCategory, Set[PermissionLevel]] = {
    # 基础信息 - 所有人可见
    DataCategory.BASIC_PROFILE: {PermissionLevel.PATIENT, PermissionLevel.COACH, 
                                  PermissionLevel.EXPERT, PermissionLevel.ADMIN},
    DataCategory.HEALTH_GOALS: {PermissionLevel.PATIENT, PermissionLevel.COACH,
                                 PermissionLevel.EXPERT, PermissionLevel.ADMIN},
    
    # 问卷答案 - 患者可见自己的
    DataCategory.QUESTIONNAIRE_ANSWERS: {PermissionLevel.PATIENT, PermissionLevel.COACH,
                                          PermissionLevel.EXPERT, PermissionLevel.ADMIN},
    
    # 评估结果 - 患者不可见
    DataCategory.BIG5_SCORES: {PermissionLevel.COACH, PermissionLevel.EXPERT, PermissionLevel.ADMIN},
    DataCategory.BIG5_INTERPRETATION: {PermissionLevel.COACH, PermissionLevel.EXPERT, PermissionLevel.ADMIN},
    DataCategory.BPT6_TYPE: {PermissionLevel.COACH, PermissionLevel.EXPERT, PermissionLevel.ADMIN},
    DataCategory.TTM_STAGE: {PermissionLevel.COACH, PermissionLevel.EXPERT, PermissionLevel.ADMIN},
    DataCategory.TTM_STAGE_LABEL: {PermissionLevel.COACH, PermissionLevel.EXPERT, PermissionLevel.ADMIN},
    DataCategory.CAPACITY_SCORE: {PermissionLevel.COACH, PermissionLevel.EXPERT, PermissionLevel.ADMIN},
    DataCategory.SPI_SCORE: {PermissionLevel.COACH, PermissionLevel.EXPERT, PermissionLevel.ADMIN},
    DataCategory.RISK_LEVEL: {PermissionLevel.COACH, PermissionLevel.EXPERT, PermissionLevel.ADMIN},
    
    # 健康数据 - 患者可见自己的
    DataCategory.DAILY_CHECKIN: {PermissionLevel.PATIENT, PermissionLevel.COACH,
                                  PermissionLevel.EXPERT, PermissionLevel.ADMIN},
    DataCategory.DEVICE_DATA: {PermissionLevel.PATIENT, PermissionLevel.COACH,
                                PermissionLevel.EXPERT, PermissionLevel.ADMIN},
    DataCategory.CGM_DATA: {PermissionLevel.PATIENT, PermissionLevel.COACH,
                            PermissionLevel.EXPERT, PermissionLevel.ADMIN},
    
    # 干预数据
    DataCategory.INTERVENTION_PLAN: {PermissionLevel.PATIENT, PermissionLevel.COACH,
                                      PermissionLevel.EXPERT, PermissionLevel.ADMIN},
    DataCategory.AI_RECOMMENDATIONS: {PermissionLevel.COACH, PermissionLevel.EXPERT, PermissionLevel.ADMIN},
    DataCategory.COACH_NOTES: {PermissionLevel.COACH, PermissionLevel.EXPERT, PermissionLevel.ADMIN},
    
    # 敏感数据 - 仅专家/管理员
    DataCategory.MENTAL_HEALTH_RISK: {PermissionLevel.EXPERT, PermissionLevel.ADMIN},
    DataCategory.RAW_ASSESSMENT: {PermissionLevel.EXPERT, PermissionLevel.ADMIN},
    DataCategory.EXPERT_NOTES: {PermissionLevel.EXPERT, PermissionLevel.ADMIN},
    DataCategory.AUDIT_LOG: {PermissionLevel.ADMIN},
}

# 数据操作权限矩阵
ACTION_PERMISSIONS: Dict[ActionType, Dict[DataCategory, Set[PermissionLevel]]] = {
    ActionType.VIEW: VIEW_PERMISSIONS,
    
    ActionType.CREATE: {
        DataCategory.QUESTIONNAIRE_ANSWERS: {PermissionLevel.PATIENT},
        DataCategory.DAILY_CHECKIN: {PermissionLevel.PATIENT},
        DataCategory.COACH_NOTES: {PermissionLevel.COACH, PermissionLevel.EXPERT},
        DataCategory.EXPERT_NOTES: {PermissionLevel.EXPERT},
        DataCategory.INTERVENTION_PLAN: {PermissionLevel.COACH, PermissionLevel.EXPERT},
    },
    
    ActionType.EDIT: {
        DataCategory.BASIC_PROFILE: {PermissionLevel.PATIENT, PermissionLevel.COACH, PermissionLevel.EXPERT},
        DataCategory.HEALTH_GOALS: {PermissionLevel.PATIENT, PermissionLevel.COACH},
        DataCategory.COACH_NOTES: {PermissionLevel.COACH, PermissionLevel.EXPERT},
        DataCategory.EXPERT_NOTES: {PermissionLevel.EXPERT},
        DataCategory.INTERVENTION_PLAN: {PermissionLevel.COACH, PermissionLevel.EXPERT},
    },
    
    ActionType.APPROVE: {
        DataCategory.TTM_STAGE: {PermissionLevel.EXPERT},
        DataCategory.RISK_LEVEL: {PermissionLevel.EXPERT},
        DataCategory.MENTAL_HEALTH_RISK: {PermissionLevel.EXPERT},
    },
    
    ActionType.OVERRIDE: {
        DataCategory.TTM_STAGE: {PermissionLevel.EXPERT},
        DataCategory.BPT6_TYPE: {PermissionLevel.EXPERT},
        DataCategory.RISK_LEVEL: {PermissionLevel.EXPERT},
    },
    
    ActionType.SHARE: {
        # 向患者披露需要专家批准
        DataCategory.BIG5_INTERPRETATION: {PermissionLevel.EXPERT},
        DataCategory.TTM_STAGE_LABEL: {PermissionLevel.EXPERT},
        DataCategory.RISK_LEVEL: {PermissionLevel.EXPERT},
    },
}


@dataclass
class UserPermission:
    """用户权限"""
    user_id: int
    level: PermissionLevel
    
    # 额外权限（可选）
    extra_view: Set[DataCategory] = field(default_factory=set)
    extra_actions: Dict[ActionType, Set[DataCategory]] = field(default_factory=dict)
    
    # 限制（可选）
    restricted_categories: Set[DataCategory] = field(default_factory=set)
    
    def can_view(self, category: DataCategory) -> bool:
        """检查是否可以查看"""
        if category in self.restricted_categories:
            return False
        if category in self.extra_view:
            return True
        allowed_levels = VIEW_PERMISSIONS.get(category, set())
        return self.level in allowed_levels
    
    def can_action(self, action: ActionType, category: DataCategory) -> bool:
        """检查是否可以执行操作"""
        if category in self.restricted_categories:
            return False
        
        # 检查额外权限
        if action in self.extra_actions and category in self.extra_actions[action]:
            return True
        
        # 检查标准权限
        action_perms = ACTION_PERMISSIONS.get(action, {})
        allowed_levels = action_perms.get(category, set())
        return self.level in allowed_levels


class PermissionManager:
    """
    权限管理器
    
    管理四级权限的检查和授权
    """
    
    def __init__(self):
        self._user_permissions: Dict[int, UserPermission] = {}
        logger.info("[Permission] 权限管理器初始化")
    
    def register_user(self, user_id: int, level: PermissionLevel) -> UserPermission:
        """注册用户权限"""
        perm = UserPermission(user_id=user_id, level=level)
        self._user_permissions[user_id] = perm
        logger.info(f"[Permission] 用户注册: {user_id} level={level.name}")
        return perm
    
    def get_user_permission(self, user_id: int) -> Optional[UserPermission]:
        """获取用户权限"""
        return self._user_permissions.get(user_id)
    
    def check_view(self, user_id: int, category: DataCategory) -> bool:
        """检查查看权限"""
        perm = self._user_permissions.get(user_id)
        if not perm:
            logger.warning(f"[Permission] 用户未注册: {user_id}")
            return False
        return perm.can_view(category)
    
    def check_action(self, user_id: int, action: ActionType, category: DataCategory) -> bool:
        """检查操作权限"""
        perm = self._user_permissions.get(user_id)
        if not perm:
            return False
        return perm.can_action(action, category)
    
    def get_viewable_categories(self, user_id: int) -> List[DataCategory]:
        """获取用户可查看的数据类别"""
        perm = self._user_permissions.get(user_id)
        if not perm:
            return []
        
        viewable = []
        for category in DataCategory:
            if perm.can_view(category):
                viewable.append(category)
        return viewable
    
    def grant_extra_view(self, user_id: int, category: DataCategory):
        """授予额外查看权限"""
        perm = self._user_permissions.get(user_id)
        if perm:
            perm.extra_view.add(category)
            logger.info(f"[Permission] 授予额外查看权限: {user_id} -> {category.value}")
    
    def restrict_category(self, user_id: int, category: DataCategory):
        """限制某个类别的访问"""
        perm = self._user_permissions.get(user_id)
        if perm:
            perm.restricted_categories.add(category)
            logger.info(f"[Permission] 限制类别访问: {user_id} -> {category.value}")


# ============================================
# 患者端数据过滤器
# ============================================

class PatientDataFilter:
    """
    患者端数据过滤器
    
    将评估结果转换为患者友好的展示
    """
    
    # 阶段标签映射（患者端不显示原始标签）
    STAGE_DISPLAY_MAP = {
        "前意向期": "健康旅程即将开始",
        "意向期": "健康意识觉醒中",
        "准备期": "准备踏上健康之路",
        "行动期": "健康习惯养成中",
        "维持期": "健康生活进行中",
        "终结期": "健康达人",
        
        # 简化版标签
        "觉察者": "健康意识觉醒中",
        "行动者": "健康习惯养成中",
        "稳定者": "健康生活进行中",
        "调整者": "健康节奏调整中",
    }
    
    # 风险等级映射
    RISK_DISPLAY_MAP = {
        "critical": "需要特别关注",
        "high": "需要持续关注",
        "moderate": "状态良好",
        "low": "非常棒",
    }
    
    @classmethod
    def filter_for_patient(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        过滤数据用于患者端显示
        
        移除敏感字段，转换标签
        """
        filtered = {}
        
        # 保留基础信息
        for key in ["user_id", "name", "avatar", "health_goals"]:
            if key in data:
                filtered[key] = data[key]
        
        # 转换阶段显示
        if "ttm_stage" in data:
            stage = data["ttm_stage"]
            filtered["status_message"] = cls.STAGE_DISPLAY_MAP.get(
                stage, "健康旅程进行中"
            )
            # 不暴露原始阶段名
        
        # 转换风险等级
        if "risk_level" in data:
            risk = data["risk_level"]
            filtered["encouragement"] = cls.RISK_DISPLAY_MAP.get(
                risk, "继续保持"
            )
            # 不暴露原始风险等级
        
        # 保留进度信息（正向）
        if "progress" in data:
            filtered["progress"] = data["progress"]
        
        # 保留任务信息
        if "tasks" in data:
            filtered["tasks"] = data["tasks"]
        
        # 添加正向激励
        filtered["motivational_message"] = cls._get_motivational_message(data)
        
        return filtered
    
    @classmethod
    def _get_motivational_message(cls, data: Dict) -> str:
        """生成激励消息"""
        messages = [
            "每一小步都是进步，继续加油！",
            "你的坚持让人敬佩，保持这个节奏！",
            "健康是最好的投资，你做得很好！",
            "今天的你比昨天更好，明天会更棒！",
        ]
        
        # 根据数据选择合适的消息
        import random
        return random.choice(messages)
    
    @classmethod
    def should_hide_from_patient(cls, field_name: str) -> bool:
        """判断字段是否应对患者隐藏"""
        hidden_fields = {
            "ttm_stage", "ttm_stage_label", "bpt6_type",
            "big5_scores", "big5_interpretation",
            "risk_level", "risk_assessment",
            "capacity_score", "spi_score",
            "mental_health_risk", "expert_notes",
            "raw_assessment", "coach_notes"
        }
        return field_name in hidden_fields


# ============================================
# 教练端数据视图
# ============================================

class CoachDataView:
    """
    教练端数据视图
    
    为教练提供评估结果摘要
    """
    
    @classmethod
    def build_student_summary(cls, assessment_data: Dict) -> Dict:
        """构建学员摘要（教练视角）"""
        return {
            "user_id": assessment_data.get("user_id"),
            "name": assessment_data.get("name"),
            
            # 阶段信息（教练可见）
            "ttm_stage": assessment_data.get("ttm_stage"),
            "stage_description": cls._get_stage_description(assessment_data.get("ttm_stage")),
            
            # 行为模式（教练可见）
            "bpt6_type": assessment_data.get("bpt6_type"),
            "type_description": cls._get_type_description(assessment_data.get("bpt6_type")),
            
            # 风险等级（教练可见）
            "risk_level": assessment_data.get("risk_level"),
            "risk_alert": assessment_data.get("risk_level") in ("critical", "high"),
            
            # 干预建议
            "intervention_suggestions": cls._get_intervention_suggestions(assessment_data),
            
            # 教练可执行操作
            "allowed_actions": ["view_detail", "add_note", "send_message", "assign_task"]
        }
    
    @classmethod
    def _get_stage_description(cls, stage: str) -> str:
        """获取阶段描述"""
        descriptions = {
            "前意向期": "用户尚未意识到需要改变，需要温和引导",
            "意向期": "用户开始考虑改变，可以提供信息支持",
            "准备期": "用户准备采取行动，可以提供具体计划",
            "行动期": "用户正在改变，需要持续鼓励和支持",
            "维持期": "用户已维持一段时间，防止复发是关键",
        }
        return descriptions.get(stage, "请关注用户状态")
    
    @classmethod
    def _get_type_description(cls, bpt_type: str) -> str:
        """获取行为模式描述"""
        descriptions = {
            "执行型": "行动导向，给具体任务效果好",
            "知识型": "理性思考，提供科学依据更有说服力",
            "情绪型": "感性驱动，共情和情感支持很重要",
            "关系型": "人际导向，社群支持效果好",
            "环境型": "情境敏感，环境改造是关键",
            "矛盾型": "需要更多耐心和个性化策略",
        }
        return descriptions.get(bpt_type, "请了解用户特点")
    
    @classmethod
    def _get_intervention_suggestions(cls, data: Dict) -> List[str]:
        """获取干预建议"""
        suggestions = []
        
        stage = data.get("ttm_stage")
        bpt_type = data.get("bpt6_type")
        risk = data.get("risk_level")
        
        # 根据阶段建议
        if stage == "前意向期":
            suggestions.append("推送健康科普内容，不要强推行动计划")
        elif stage == "行动期":
            suggestions.append("持续鼓励，关注执行情况")
        
        # 根据类型建议
        if bpt_type == "情绪型":
            suggestions.append("先共情再建议，关注情绪状态")
        elif bpt_type == "知识型":
            suggestions.append("提供数据和原理支持")
        
        # 根据风险建议
        if risk in ("critical", "high"):
            suggestions.append("⚠️ 高风险，请及时关注并上报专家")
        
        return suggestions


# ============================================
# 全局单例
# ============================================

_permission_manager: Optional[PermissionManager] = None


def get_permission_manager() -> PermissionManager:
    """获取权限管理器"""
    global _permission_manager
    if _permission_manager is None:
        _permission_manager = PermissionManager()
    return _permission_manager
