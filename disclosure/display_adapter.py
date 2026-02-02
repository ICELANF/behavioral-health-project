"""
行为健康数字平台 - 评估结果展示适配器
Assessment Result Display Adapter

[v14.1-NEW] 披露控制模块

根据四级权限架构，将评估结果适配为不同角色的展示格式：
- 患者端：正向激励，隐藏标签
- 教练端：结果摘要，干预建议
- 专家端：完整报告，审核工具
- 管理端：脱敏统计，配置界面

核心原则：
1. 患者非要求不展示评估结果
2. 敏感信息需专家审核后才能披露
3. 避免标签效应带来的心理暗示
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

from disclosure.permissions import (
    PermissionLevel,
    DataCategory,
    PatientDataFilter,
    CoachDataView,
    get_permission_manager
)
from disclosure.rewriter import get_ai_rewriter
from disclosure.blacklist import get_blacklist_manager


@dataclass
class AssessmentDisplay:
    """评估结果展示"""
    user_id: int
    viewer_level: PermissionLevel
    
    # 展示内容
    content: Dict[str, Any]
    
    # 元信息
    generated_at: datetime
    is_filtered: bool
    hidden_fields: List[str]


class AssessmentDisplayAdapter:
    """
    评估结果展示适配器
    
    根据查看者权限生成适合的展示内容
    """
    
    def __init__(self):
        self.permission_mgr = get_permission_manager()
        self.rewriter = get_ai_rewriter()
        self.blacklist = get_blacklist_manager()
        logger.info("[Display] 评估展示适配器初始化")
    
    def adapt(
        self,
        assessment_data: Dict[str, Any],
        viewer_id: int,
        viewer_level: PermissionLevel
    ) -> AssessmentDisplay:
        """
        适配评估结果用于展示
        
        Args:
            assessment_data: 原始评估数据
            viewer_id: 查看者ID
            viewer_level: 查看者权限等级
        
        Returns:
            AssessmentDisplay: 适配后的展示内容
        """
        user_id = assessment_data.get("user_id", 0)
        hidden_fields = []
        
        if viewer_level == PermissionLevel.PATIENT:
            content = self._adapt_for_patient(assessment_data)
            hidden_fields = self._get_hidden_fields_for_patient()
            
        elif viewer_level == PermissionLevel.COACH:
            content = self._adapt_for_coach(assessment_data)
            hidden_fields = self._get_hidden_fields_for_coach()
            
        elif viewer_level == PermissionLevel.EXPERT:
            content = self._adapt_for_expert(assessment_data)
            hidden_fields = []  # 专家可见全部
            
        elif viewer_level == PermissionLevel.ADMIN:
            content = self._adapt_for_admin(assessment_data)
            hidden_fields = self._get_hidden_fields_for_admin()
            
        else:
            content = {"error": "Unknown permission level"}
            hidden_fields = list(assessment_data.keys())
        
        return AssessmentDisplay(
            user_id=user_id,
            viewer_level=viewer_level,
            content=content,
            generated_at=datetime.now(),
            is_filtered=viewer_level != PermissionLevel.EXPERT,
            hidden_fields=hidden_fields
        )
    
    def _adapt_for_patient(self, data: Dict) -> Dict:
        """
        适配患者端展示
        
        原则：只参与，不知晓
        - 移除所有评估标签
        - 转换为正向激励内容
        - 保留任务和进度
        """
        result = {
            "user_id": data.get("user_id"),
            "name": data.get("name"),
            
            # 正向状态消息（替代阶段标签）
            "status": self._get_patient_status_message(data),
            
            # 激励消息
            "encouragement": self._get_encouragement_message(data),
            
            # 今日任务（可见）
            "today_tasks": data.get("today_tasks", []),
            
            # 进度追踪（正向展示）
            "progress": self._format_progress_for_patient(data.get("progress", {})),
            
            # 健康小贴士
            "health_tip": self._get_health_tip(data),
            
            # 可用功能
            "available_actions": [
                "complete_questionnaire",
                "daily_checkin",
                "view_tasks",
                "chat_with_coach"
            ]
        }
        
        # 确保没有敏感信息泄露
        self._verify_patient_safe(result)
        
        return result
    
    def _adapt_for_coach(self, data: Dict) -> Dict:
        """
        适配教练端展示
        
        原则：看到结果，执行干预
        - 展示评估结果摘要
        - 提供干预建议
        - 不展示原始分数
        """
        return {
            "user_id": data.get("user_id"),
            "name": data.get("name"),
            
            # 学员画像（教练可见）
            "profile": {
                "ttm_stage": data.get("ttm_stage"),
                "stage_label": self._get_stage_label(data.get("ttm_stage")),
                "bpt6_type": data.get("bpt6_type"),
                "type_label": self._get_type_label(data.get("bpt6_type")),
            },
            
            # 风险提示
            "risk_alert": {
                "level": data.get("risk_level", "low"),
                "needs_attention": data.get("risk_level") in ("critical", "high"),
                "alert_message": self._get_risk_alert_for_coach(data.get("risk_level"))
            },
            
            # 评估摘要（不含原始分数）
            "assessment_summary": self._build_coach_summary(data),
            
            # 干预建议
            "intervention_suggestions": CoachDataView._get_intervention_suggestions(data),
            
            # AI推荐的干预话术
            "recommended_scripts": self._get_intervention_scripts(data),
            
            # 可执行操作
            "allowed_actions": [
                "view_detail",
                "add_observation_note",
                "send_intervention",
                "assign_task",
                "escalate_to_expert"
            ],
            
            # 最近动态
            "recent_activities": data.get("recent_activities", [])
        }
    
    def _adapt_for_expert(self, data: Dict) -> Dict:
        """
        适配专家端展示
        
        原则：完整可见，审核确认
        - 展示完整评估报告
        - 提供审核工具
        - 可覆盖系统判定
        """
        return {
            "user_id": data.get("user_id"),
            "name": data.get("name"),
            
            # 完整评估数据
            "full_assessment": {
                # 大五人格
                "big5": {
                    "scores": data.get("big5_scores", {}),
                    "interpretation": data.get("big5_interpretation", ""),
                    "profile_chart": data.get("big5_profile", {})
                },
                
                # 行为模式
                "bpt6": {
                    "type": data.get("bpt6_type"),
                    "scores": data.get("bpt6_scores", {}),
                    "analysis": data.get("bpt6_analysis", "")
                },
                
                # 改变阶段
                "ttm": {
                    "stage": data.get("ttm_stage"),
                    "history": data.get("ttm_history", []),
                    "transition_probability": data.get("ttm_transition", {})
                },
                
                # 改变力
                "capacity": {
                    "score": data.get("capacity_score"),
                    "dimensions": data.get("capacity_dimensions", {})
                },
                
                # 成功预测
                "spi": {
                    "score": data.get("spi_score"),
                    "factors": data.get("spi_factors", {})
                }
            },
            
            # 风险评估
            "risk_assessment": {
                "level": data.get("risk_level"),
                "factors": data.get("risk_factors", []),
                "mental_health_flags": data.get("mental_health_flags", [])
            },
            
            # 原始问卷答案
            "raw_questionnaire": data.get("questionnaire_answers", {}),
            
            # 审核工具
            "review_tools": {
                "can_override_stage": True,
                "can_override_type": True,
                "can_override_risk": True,
                "can_approve_disclosure": True,
                "can_add_expert_notes": True
            },
            
            # 披露状态
            "disclosure_status": data.get("disclosure_status", "pending"),
            
            # 可执行操作
            "allowed_actions": [
                "view_full_report",
                "override_assessment",
                "approve_disclosure",
                "reject_disclosure",
                "add_expert_notes",
                "refer_to_specialist"
            ]
        }
    
    def _adapt_for_admin(self, data: Dict) -> Dict:
        """
        适配管理端展示
        
        原则：脱敏统计，系统配置
        - 脱敏个人信息
        - 提供统计视图
        - 系统配置入口
        """
        return {
            # 脱敏用户标识
            "user_hash": f"USER_{hash(data.get('user_id', 0)) % 10000:04d}",
            
            # 统计分类
            "statistics": {
                "stage_category": data.get("ttm_stage"),
                "type_category": data.get("bpt6_type"),
                "risk_category": data.get("risk_level"),
            },
            
            # 审计信息
            "audit_info": {
                "assessment_date": data.get("assessment_date"),
                "last_updated": data.get("last_updated"),
                "reviewed_by": data.get("reviewed_by"),
            },
            
            # 可执行操作
            "allowed_actions": [
                "view_aggregate_stats",
                "configure_rules",
                "export_anonymized_data"
            ]
        }
    
    # ============================================
    # 辅助方法
    # ============================================
    
    def _get_patient_status_message(self, data: Dict) -> str:
        """生成患者状态消息（正向）"""
        stage = data.get("ttm_stage", "")
        
        messages = {
            "前意向期": "健康意识正在觉醒，每一步都很重要",
            "意向期": "你已经开始关注健康了，这是很棒的开始",
            "准备期": "你已经准备好迈出第一步，让我们一起",
            "行动期": "你正在积极行动，为你感到骄傲",
            "维持期": "你已经养成了好习惯，继续保持",
            "终结期": "你是健康达人，你的坚持令人敬佩",
        }
        
        return messages.get(stage, "健康旅程进行中，加油！")
    
    def _get_encouragement_message(self, data: Dict) -> str:
        """生成激励消息"""
        risk = data.get("risk_level", "low")
        
        if risk == "low":
            return "你的状态非常棒，继续保持！💪"
        elif risk == "moderate":
            return "你做得很好，让我们一起更进一步！"
        else:
            return "每一小步都是进步，我们陪着你！"
    
    def _format_progress_for_patient(self, progress: Dict) -> Dict:
        """格式化进度信息（正向）"""
        return {
            "completion_rate": progress.get("completion_rate", 0),
            "streak_days": progress.get("streak_days", 0),
            "achievements": progress.get("achievements", []),
            "message": f"已坚持 {progress.get('streak_days', 0)} 天，继续加油！"
        }
    
    def _get_health_tip(self, data: Dict) -> str:
        """获取健康小贴士"""
        tips = [
            "今天记得多喝水哦 💧",
            "饭后百步走，活到九十九 🚶",
            "深呼吸，放松心情 🧘",
            "早睡早起身体好 😴",
        ]
        import random
        return random.choice(tips)
    
    def _verify_patient_safe(self, result: Dict):
        """验证患者数据安全（无敏感信息泄露）"""
        dangerous_keys = {
            "ttm_stage", "bpt6_type", "big5", "risk_level",
            "capacity_score", "spi_score", "assessment"
        }
        
        for key in list(result.keys()):
            if key in dangerous_keys:
                logger.warning(f"[Display] 患者数据中发现敏感字段: {key}")
                del result[key]
    
    def _get_stage_label(self, stage: str) -> str:
        """获取阶段标签（教练可见版本）"""
        labels = {
            "前意向期": "觉察期 - 尚未意识到需要改变",
            "意向期": "考虑期 - 开始思考改变",
            "准备期": "准备期 - 准备采取行动",
            "行动期": "行动期 - 正在实施改变",
            "维持期": "维持期 - 保持改变成果",
        }
        return labels.get(stage, stage)
    
    def _get_type_label(self, bpt_type: str) -> str:
        """获取行为模式标签"""
        labels = {
            "执行型": "执行型 - 行动导向",
            "知识型": "知识型 - 理性思考",
            "情绪型": "情绪型 - 感性驱动",
            "关系型": "关系型 - 人际导向",
            "环境型": "环境型 - 情境敏感",
            "矛盾型": "矛盾型 - 需个性化策略",
        }
        return labels.get(bpt_type, bpt_type)
    
    def _get_risk_alert_for_coach(self, risk: str) -> str:
        """获取教练风险提示"""
        alerts = {
            "critical": "⚠️ 高风险：请立即关注并上报专家",
            "high": "⚠️ 较高风险：需要密切关注",
            "moderate": "注意：需要持续关注",
            "low": "状态良好",
        }
        return alerts.get(risk, "请关注")
    
    def _build_coach_summary(self, data: Dict) -> str:
        """构建教练摘要"""
        stage = data.get("ttm_stage", "未知")
        bpt_type = data.get("bpt6_type", "未知")
        
        summary = f"该学员目前处于{stage}，行为模式为{bpt_type}。"
        
        if data.get("risk_level") in ("critical", "high"):
            summary += "⚠️ 风险等级较高，请优先关注。"
        
        return summary
    
    def _get_intervention_scripts(self, data: Dict) -> List[Dict]:
        """获取干预话术"""
        stage = data.get("ttm_stage", "")
        bpt_type = data.get("bpt6_type", "")
        
        scripts = []
        
        # 根据阶段+类型组合推荐话术
        if stage == "前意向期" and bpt_type == "情绪型":
            scripts.append({
                "scenario": "首次接触",
                "script": "最近感觉怎么样？有什么困扰想聊聊吗？",
                "note": "先共情，不急于推行动"
            })
        elif stage == "行动期" and bpt_type == "执行型":
            scripts.append({
                "scenario": "执行跟进",
                "script": "今天的任务完成得怎么样？遇到什么困难了吗？",
                "note": "直接询问执行情况"
            })
        
        # 通用脚本
        scripts.append({
            "scenario": "日常问候",
            "script": "今天状态如何？有什么我可以帮助的吗？",
            "note": "温和开场"
        })
        
        return scripts
    
    def _get_hidden_fields_for_patient(self) -> List[str]:
        """患者隐藏字段"""
        return [
            "ttm_stage", "ttm_stage_label", "bpt6_type",
            "big5_scores", "big5_interpretation",
            "risk_level", "risk_assessment",
            "capacity_score", "spi_score",
            "mental_health_risk", "expert_notes",
            "raw_assessment", "coach_notes"
        ]
    
    def _get_hidden_fields_for_coach(self) -> List[str]:
        """教练隐藏字段"""
        return [
            "big5_scores", "raw_assessment",
            "mental_health_risk", "expert_notes"
        ]
    
    def _get_hidden_fields_for_admin(self) -> List[str]:
        """管理员隐藏字段（个人敏感）"""
        return [
            "name", "phone", "id_number",
            "questionnaire_answers"
        ]


# ============================================
# 全局单例
# ============================================

_display_adapter: Optional[AssessmentDisplayAdapter] = None


def get_display_adapter() -> AssessmentDisplayAdapter:
    """获取展示适配器"""
    global _display_adapter
    if _display_adapter is None:
        _display_adapter = AssessmentDisplayAdapter()
    return _display_adapter
