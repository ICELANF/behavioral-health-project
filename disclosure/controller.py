"""
行为健康数字平台 - 披露控制：报告披露控制器
Disclosure Control: Report Disclosure Controller

[v14-NEW] 披露控制模块

核心功能：
1. 章节级别的可见性控制
2. AI辅助文案重写
3. 披露等级管理
4. 四级权限适配

报告章节（17章）：
1. core_profile - 核心画像
2. big5_summary - 大五人格摘要
3. big5_detail - 大五人格详情
4. bpt6_type - 行为模式分型
5. ttm_stage - 改变阶段
6. capacity_score - 改变力得分
7. spi_prediction - 成功率预测
8. trigger_factors - 触发因子
9. risk_assessment - 风险评估
10. mental_health - 心理健康风险
11. behavior_pattern - 行为模式分析
12. intervention_plan - 干预建议
13. coach_guidance - 教练指导
14. action_tasks - 行动任务
15. progress_tracking - 进度追踪
16. expert_notes - 专家备注
17. raw_data - 原始数据
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from loguru import logger

from disclosure.blacklist import get_blacklist_manager, SensitivityLevel
from disclosure.signature import (
    get_signature_manager, 
    RiskLevel, 
    DualSignatureRequest,
    SignatureRole
)


class DisclosureLevel(str, Enum):
    """披露等级"""
    FULL = "full"                    # 全量披露
    CONDITIONAL = "conditional"      # 有条件披露
    MINIMAL = "minimal"              # 最小披露
    NONE = "none"                    # 暂不披露


class ViewerRole(str, Enum):
    """查看者角色（四级权限）"""
    PATIENT = "patient"      # 患者端（C端）
    COACH = "coach"          # 教练端（B端）
    EXPERT = "expert"        # 专家/督导端
    ADMIN = "admin"          # 管理端


# ============================================
# 报告章节定义
# ============================================

@dataclass
class ReportChapter:
    """报告章节"""
    chapter_id: str
    name: str
    description: str
    
    # 默认可见性
    default_visibility: Dict[ViewerRole, bool] = field(default_factory=dict)
    
    # 敏感度
    sensitivity: SensitivityLevel = SensitivityLevel.LOW
    
    # 是否需要专家审核才能向患者披露
    requires_expert_approval: bool = False


# 默认章节配置
DEFAULT_CHAPTERS: List[ReportChapter] = [
    ReportChapter(
        "core_profile", "核心画像", "用户基础画像和健康目标",
        {ViewerRole.PATIENT: True, ViewerRole.COACH: True, ViewerRole.EXPERT: True, ViewerRole.ADMIN: True},
        SensitivityLevel.LOW, False
    ),
    ReportChapter(
        "big5_summary", "人格特质摘要", "大五人格正向解读",
        {ViewerRole.PATIENT: False, ViewerRole.COACH: True, ViewerRole.EXPERT: True, ViewerRole.ADMIN: True},
        SensitivityLevel.MODERATE, True
    ),
    ReportChapter(
        "big5_detail", "人格特质详情", "大五人格各维度详细分析",
        {ViewerRole.PATIENT: False, ViewerRole.COACH: False, ViewerRole.EXPERT: True, ViewerRole.ADMIN: False},
        SensitivityLevel.HIGH, True
    ),
    ReportChapter(
        "bpt6_type", "行为模式分型", "BPT-6行为模式分类",
        {ViewerRole.PATIENT: False, ViewerRole.COACH: True, ViewerRole.EXPERT: True, ViewerRole.ADMIN: True},
        SensitivityLevel.MODERATE, True
    ),
    ReportChapter(
        "ttm_stage", "改变阶段", "TTM改变阶段判定",
        {ViewerRole.PATIENT: False, ViewerRole.COACH: True, ViewerRole.EXPERT: True, ViewerRole.ADMIN: True},
        SensitivityLevel.MODERATE, True
    ),
    ReportChapter(
        "capacity_score", "改变力评估", "CAPACITY改变力得分",
        {ViewerRole.PATIENT: False, ViewerRole.COACH: True, ViewerRole.EXPERT: True, ViewerRole.ADMIN: True},
        SensitivityLevel.MODERATE, False
    ),
    ReportChapter(
        "spi_prediction", "成功率预测", "SPI成功可能性指数",
        {ViewerRole.PATIENT: False, ViewerRole.COACH: True, ViewerRole.EXPERT: True, ViewerRole.ADMIN: True},
        SensitivityLevel.MODERATE, False
    ),
    ReportChapter(
        "trigger_factors", "触发因子", "行为触发因子分析",
        {ViewerRole.PATIENT: False, ViewerRole.COACH: True, ViewerRole.EXPERT: True, ViewerRole.ADMIN: True},
        SensitivityLevel.LOW, False
    ),
    ReportChapter(
        "risk_assessment", "风险评估", "综合风险等级评估",
        {ViewerRole.PATIENT: False, ViewerRole.COACH: True, ViewerRole.EXPERT: True, ViewerRole.ADMIN: True},
        SensitivityLevel.HIGH, True
    ),
    ReportChapter(
        "mental_health", "心理健康风险", "心理健康风险筛查",
        {ViewerRole.PATIENT: False, ViewerRole.COACH: False, ViewerRole.EXPERT: True, ViewerRole.ADMIN: False},
        SensitivityLevel.CRITICAL, True
    ),
    ReportChapter(
        "behavior_pattern", "行为模式分析", "行为习惯和模式分析",
        {ViewerRole.PATIENT: False, ViewerRole.COACH: True, ViewerRole.EXPERT: True, ViewerRole.ADMIN: True},
        SensitivityLevel.MODERATE, False
    ),
    ReportChapter(
        "intervention_plan", "干预建议", "AI生成的干预建议",
        {ViewerRole.PATIENT: False, ViewerRole.COACH: True, ViewerRole.EXPERT: True, ViewerRole.ADMIN: True},
        SensitivityLevel.LOW, False
    ),
    ReportChapter(
        "coach_guidance", "教练指导", "面向教练的指导建议",
        {ViewerRole.PATIENT: False, ViewerRole.COACH: True, ViewerRole.EXPERT: True, ViewerRole.ADMIN: False},
        SensitivityLevel.LOW, False
    ),
    ReportChapter(
        "action_tasks", "行动任务", "推荐的行动任务清单",
        {ViewerRole.PATIENT: True, ViewerRole.COACH: True, ViewerRole.EXPERT: True, ViewerRole.ADMIN: True},
        SensitivityLevel.LOW, False
    ),
    ReportChapter(
        "progress_tracking", "进度追踪", "健康进度追踪",
        {ViewerRole.PATIENT: True, ViewerRole.COACH: True, ViewerRole.EXPERT: True, ViewerRole.ADMIN: True},
        SensitivityLevel.LOW, False
    ),
    ReportChapter(
        "expert_notes", "专家备注", "专家内部备注（不对外）",
        {ViewerRole.PATIENT: False, ViewerRole.COACH: False, ViewerRole.EXPERT: True, ViewerRole.ADMIN: False},
        SensitivityLevel.HIGH, False
    ),
    ReportChapter(
        "raw_data", "原始数据", "评估原始数据",
        {ViewerRole.PATIENT: False, ViewerRole.COACH: False, ViewerRole.EXPERT: True, ViewerRole.ADMIN: False},
        SensitivityLevel.HIGH, False
    ),
]


@dataclass
class DisclosureDecision:
    """披露决策"""
    report_id: str
    user_id: int
    
    # 披露等级
    disclosure_level: DisclosureLevel = DisclosureLevel.CONDITIONAL
    
    # 章节可见性覆盖（True=可见，False=隐藏）
    chapter_overrides: Dict[str, bool] = field(default_factory=dict)
    
    # 文案重写记录
    content_rewrites: Dict[str, str] = field(default_factory=dict)
    
    # 风险等级
    risk_level: RiskLevel = RiskLevel.MODERATE
    
    # 审核状态
    status: str = "pending"  # pending, reviewing, approved, rejected
    
    # 签名请求ID
    signature_request_id: Optional[str] = None
    
    # 审核记录
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "report_id": self.report_id,
            "user_id": self.user_id,
            "disclosure_level": self.disclosure_level.value,
            "chapter_overrides": self.chapter_overrides,
            "content_rewrites": self.content_rewrites,
            "risk_level": self.risk_level.value,
            "status": self.status,
            "signature_request_id": self.signature_request_id,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "review_notes": self.review_notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class DisclosureController:
    """
    披露控制器
    
    管理报告内容的披露策略
    """
    
    def __init__(self):
        self.chapters = {c.chapter_id: c for c in DEFAULT_CHAPTERS}
        self._decisions: Dict[str, DisclosureDecision] = {}
        self.blacklist = get_blacklist_manager()
        self.signature_mgr = get_signature_manager()
        
        logger.info(f"[Disclosure] 控制器初始化: {len(self.chapters)} 个章节")
    
    def create_decision(
        self,
        report_id: str,
        user_id: int,
        risk_level: RiskLevel = RiskLevel.MODERATE,
        initial_content: Optional[str] = None
    ) -> DisclosureDecision:
        """
        创建披露决策
        
        Args:
            report_id: 报告ID
            user_id: 用户ID
            risk_level: 风险等级
            initial_content: 初始内容（用于创建签名请求）
        
        Returns:
            DisclosureDecision
        """
        decision = DisclosureDecision(
            report_id=report_id,
            user_id=user_id,
            risk_level=risk_level
        )
        
        # 根据风险等级设置默认披露等级
        if risk_level == RiskLevel.CRITICAL:
            decision.disclosure_level = DisclosureLevel.NONE
        elif risk_level == RiskLevel.HIGH:
            decision.disclosure_level = DisclosureLevel.MINIMAL
        elif risk_level == RiskLevel.MODERATE:
            decision.disclosure_level = DisclosureLevel.CONDITIONAL
        else:
            decision.disclosure_level = DisclosureLevel.FULL
        
        # 创建签名请求
        if initial_content:
            sig_request = self.signature_mgr.create_request(
                report_id=report_id,
                user_id=user_id,
                risk_level=risk_level,
                content=initial_content
            )
            decision.signature_request_id = sig_request.request_id
        
        self._decisions[report_id] = decision
        
        logger.info(f"[Disclosure] 创建披露决策: report={report_id} risk={risk_level.value}")
        
        return decision
    
    def get_visible_chapters(
        self,
        report_id: str,
        viewer_role: ViewerRole
    ) -> List[str]:
        """
        获取指定角色可见的章节
        
        Args:
            report_id: 报告ID
            viewer_role: 查看者角色
        
        Returns:
            可见章节ID列表
        """
        decision = self._decisions.get(report_id)
        visible = []
        
        for chapter_id, chapter in self.chapters.items():
            # 默认可见性
            is_visible = chapter.default_visibility.get(viewer_role, False)
            
            # 如果有决策覆盖
            if decision and chapter_id in decision.chapter_overrides:
                # 专家可以覆盖
                if viewer_role in (ViewerRole.EXPERT, ViewerRole.ADMIN):
                    is_visible = decision.chapter_overrides[chapter_id]
                # 对患者的覆盖需要审核通过
                elif viewer_role == ViewerRole.PATIENT:
                    if decision.status == "approved":
                        is_visible = decision.chapter_overrides[chapter_id]
            
            # 暂不披露 = 患者什么都看不到
            if decision and decision.disclosure_level == DisclosureLevel.NONE:
                if viewer_role == ViewerRole.PATIENT:
                    is_visible = False
            
            if is_visible:
                visible.append(chapter_id)
        
        return visible
    
    def filter_content_for_viewer(
        self,
        content: str,
        viewer_role: ViewerRole,
        report_id: Optional[str] = None
    ) -> str:
        """
        根据角色过滤内容
        
        - 专家/管理员：原始内容
        - 教练：轻度脱敏
        - 患者：重度脱敏 + 正向重构
        """
        if viewer_role in (ViewerRole.EXPERT, ViewerRole.ADMIN):
            return content
        
        # 获取决策中的重写内容
        if report_id:
            decision = self._decisions.get(report_id)
            if decision and decision.content_rewrites:
                # 如果有专家编辑的版本，使用它
                for original, rewritten in decision.content_rewrites.items():
                    content = content.replace(original, rewritten)
        
        # 教练端：中度脱敏
        if viewer_role == ViewerRole.COACH:
            return self.blacklist.auto_replace(content, SensitivityLevel.HIGH)
        
        # 患者端：重度脱敏
        if viewer_role == ViewerRole.PATIENT:
            return self.blacklist.auto_replace(content, SensitivityLevel.MODERATE)
        
        return content
    
    def set_chapter_visibility(
        self,
        report_id: str,
        chapter_id: str,
        visible: bool,
        expert_id: str
    ) -> DisclosureDecision:
        """
        设置章节可见性
        
        Args:
            report_id: 报告ID
            chapter_id: 章节ID
            visible: 是否可见
            expert_id: 操作专家ID
        
        Returns:
            更新后的决策
        """
        decision = self._decisions.get(report_id)
        if not decision:
            raise ValueError(f"披露决策不存在: {report_id}")
        
        chapter = self.chapters.get(chapter_id)
        if not chapter:
            raise ValueError(f"章节不存在: {chapter_id}")
        
        # 高敏感章节向患者披露需要特别确认
        if visible and chapter.sensitivity == SensitivityLevel.CRITICAL:
            logger.warning(f"[Disclosure] 高敏感章节披露: {chapter_id} by {expert_id}")
        
        decision.chapter_overrides[chapter_id] = visible
        decision.updated_at = datetime.now()
        
        logger.info(f"[Disclosure] 章节可见性更新: {chapter_id}={visible} by {expert_id}")
        
        return decision
    
    def add_content_rewrite(
        self,
        report_id: str,
        original: str,
        rewritten: str,
        expert_id: str
    ) -> DisclosureDecision:
        """
        添加内容重写
        
        Args:
            report_id: 报告ID
            original: 原始文本
            rewritten: 重写文本
            expert_id: 操作专家ID
        
        Returns:
            更新后的决策
        """
        decision = self._decisions.get(report_id)
        if not decision:
            raise ValueError(f"披露决策不存在: {report_id}")
        
        # 检查重写后是否仍有敏感词
        if self.blacklist.contains_sensitive(rewritten, SensitivityLevel.HIGH):
            logger.warning(f"[Disclosure] 重写内容仍含敏感词: {rewritten[:50]}...")
        
        decision.content_rewrites[original] = rewritten
        decision.updated_at = datetime.now()
        
        logger.info(f"[Disclosure] 内容重写: '{original[:20]}...' -> '{rewritten[:20]}...' by {expert_id}")
        
        return decision
    
    def approve_disclosure(
        self,
        report_id: str,
        expert_id: str,
        expert_name: str,
        role: SignatureRole,
        notes: Optional[str] = None
    ) -> DisclosureDecision:
        """
        批准披露
        
        Args:
            report_id: 报告ID
            expert_id: 专家ID
            expert_name: 专家姓名
            role: 签名角色
            notes: 备注
        
        Returns:
            更新后的决策
        """
        decision = self._decisions.get(report_id)
        if not decision:
            raise ValueError(f"披露决策不存在: {report_id}")
        
        # 执行签名
        if decision.signature_request_id:
            self.signature_mgr.sign(
                request_id=decision.signature_request_id,
                signer_id=expert_id,
                signer_name=expert_name,
                role=role,
                comment=notes
            )
            
            # 检查签名是否完成
            sig_request = self.signature_mgr.get_request(decision.signature_request_id)
            if sig_request and sig_request.is_complete:
                decision.status = "approved"
                decision.reviewed_by = expert_id
                decision.reviewed_at = datetime.now()
                decision.review_notes = notes
                
                logger.info(f"[Disclosure] 披露已批准: {report_id}")
        else:
            # 无签名流程，直接批准
            decision.status = "approved"
            decision.reviewed_by = expert_id
            decision.reviewed_at = datetime.now()
            decision.review_notes = notes
        
        decision.updated_at = datetime.now()
        
        return decision
    
    def reject_disclosure(
        self,
        report_id: str,
        expert_id: str,
        expert_name: str,
        reason: str
    ) -> DisclosureDecision:
        """
        驳回披露
        """
        decision = self._decisions.get(report_id)
        if not decision:
            raise ValueError(f"披露决策不存在: {report_id}")
        
        if decision.signature_request_id:
            self.signature_mgr.reject(
                request_id=decision.signature_request_id,
                signer_id=expert_id,
                signer_name=expert_name,
                role=SignatureRole.PRIMARY,
                reason=reason
            )
        
        decision.status = "rejected"
        decision.reviewed_by = expert_id
        decision.reviewed_at = datetime.now()
        decision.review_notes = reason
        decision.updated_at = datetime.now()
        
        logger.warning(f"[Disclosure] 披露已驳回: {report_id} reason={reason}")
        
        return decision
    
    def can_patient_view(self, report_id: str) -> bool:
        """患者是否可以查看报告"""
        decision = self._decisions.get(report_id)
        if not decision:
            return False
        
        # 暂不披露
        if decision.disclosure_level == DisclosureLevel.NONE:
            return False
        
        # 需要审核通过
        if decision.risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH):
            return decision.status == "approved"
        
        return True
    
    def get_patient_view_message(self, report_id: str) -> str:
        """获取患者端显示消息"""
        decision = self._decisions.get(report_id)
        
        if not decision:
            return "报告正在生成中..."
        
        if decision.disclosure_level == DisclosureLevel.NONE:
            return "您的报告正在由专业团队审核中，请耐心等待。"
        
        if decision.status == "pending":
            return "报告正在由专家深度分析中，完成后将为您推送个性化建议。"
        
        if decision.status == "reviewing":
            return "报告正在由专家审核中，很快就会准备好。"
        
        if decision.status == "rejected":
            return "报告需要进一步完善，专家正在为您重新评估。"
        
        if decision.status == "approved":
            return "您的个性化成长路径已更新，快来查看吧！"
        
        return "报告处理中..."
    
    def get_decision(self, report_id: str) -> Optional[DisclosureDecision]:
        """获取披露决策"""
        return self._decisions.get(report_id)
    
    def list_pending_reviews(self) -> List[DisclosureDecision]:
        """获取待审核列表"""
        return [d for d in self._decisions.values() 
               if d.status in ("pending", "reviewing")]


# ============================================
# 全局单例
# ============================================

_disclosure_controller: Optional[DisclosureController] = None


def get_disclosure_controller() -> DisclosureController:
    """获取披露控制器"""
    global _disclosure_controller
    if _disclosure_controller is None:
        _disclosure_controller = DisclosureController()
    return _disclosure_controller
