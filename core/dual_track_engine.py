"""
双轨晋级校验引擎
契约来源: Sheet④ 晋级契约 + Sheet⑩ 技术实施映射 (P0, 1.5周)

公式: 晋级 = 积分轨达标(门槛) ∧ 成长轨验证通过(判定)

核心组件:
  1. PromotionThresholds — L0~L5 积分阈值 + 成长轨条件配置
  2. DualTrackChecker  — 双轨校验主逻辑 (积分轨 + 成长轨)
  3. PromotionStateManager — 4种状态管理 (正常成长/等待验证/成长先到/晋级就绪)
  4. GapAnalyzer — 差距分析报告生成
  5. PromotionOrchestrator — 晋级流程编排 (触发→校验→仪式)
"""

from __future__ import annotations
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field, asdict


# ══════════════════════════════════════════
# 1. 晋级阈值配置 (对齐 Sheet④ 第4节)
# ══════════════════════════════════════════

class PromotionLevel(str, Enum):
    L0_OBSERVER = "L0"
    L1_GROWER = "L1"
    L2_SHARER = "L2"
    L3_COACH = "L3"
    L4_SENIOR_COACH = "L4"
    L5_MASTER = "L5"


class PromotionState(int, Enum):
    """双轨状态 (Sheet④ 双轨状态×用户引导话术)"""
    NORMAL_GROWTH = 1       # 状态1: 正常成长 — 积分未达标, 成长未验证
    AWAITING_VERIFY = 2     # 状态2: 等待验证 — 积分达标, 成长未过 ⚠️关键
    GROWTH_FIRST = 3        # 状态3: 成长先到 — 成长通过, 积分未达 (罕见)
    READY_TO_PROMOTE = 4    # 状态4: 晋级就绪 — 双轨均达标


@dataclass
class PointsThreshold:
    """积分轨阈值"""
    growth: int = 0
    contribution: int = 0
    influence: int = 0
    is_hard_gate: bool = True  # True=硬性门槛, False=参考值(如L1→L2)


@dataclass
class PeerRequirement:
    """同道者要求 (Sheet④ 四同道者裂变)"""
    total_required: int = 4
    min_progressed: int = 2            # 至少X人达到指定阶段
    progress_target: str = ""          # 进度目标描述
    min_advanced: int = 1              # 至少X人达到高级阶段
    advanced_target: str = ""          # 高级目标描述


@dataclass
class GrowthTrackRequirement:
    """成长轨要求 (Sheet④ 核心判定)"""
    peer_req: PeerRequirement
    capability_requirements: List[str] = field(default_factory=list)
    exam_requirements: List[str] = field(default_factory=list)
    behavior_requirements: List[str] = field(default_factory=list)
    ethics_requirements: List[str] = field(default_factory=list)
    min_period_months: int = 0
    ceremony_name: str = ""
    ceremony_emoji: str = ""


@dataclass
class LevelThreshold:
    """单层级完整晋级条件"""
    from_level: PromotionLevel
    to_level: PromotionLevel
    points: PointsThreshold
    growth: GrowthTrackRequirement
    anti_cheat_strategies: List[str] = field(default_factory=list)


# ── L0→L5 全量配置 ──

PROMOTION_THRESHOLDS: Dict[str, LevelThreshold] = {
    
    "L0_TO_L1": LevelThreshold(
        from_level=PromotionLevel.L0_OBSERVER,
        to_level=PromotionLevel.L1_GROWER,
        points=PointsThreshold(growth=100, contribution=0, influence=0),
        growth=GrowthTrackRequirement(
            peer_req=PeerRequirement(
                total_required=4,
                min_progressed=2, progress_target="开始行为尝试",
                min_advanced=0, advanced_target="",
            ),
            capability_requirements=[
                "S0-S4全阶段完成",
                "≥1项核心行为稳定90天",
                "生物学指标好转≥2项",
            ],
            exam_requirements=[
                "基础课程20学时完成",
                "行为链基础测评通过",
            ],
            behavior_requirements=[
                "贡献≥3条可复用行为路径/中断模式/认知-行为差距数据",
            ],
            ethics_requirements=["社区规范遵守"],
            min_period_months=3,
            ceremony_name="破壳者", ceremony_emoji="🐣",
        ),
        anti_cheat_strategies=["AS-01"],
    ),
    
    "L1_TO_L2": LevelThreshold(
        from_level=PromotionLevel.L1_GROWER,
        to_level=PromotionLevel.L2_SHARER,
        points=PointsThreshold(
            growth=300, contribution=50, influence=0,
            is_hard_gate=False,  # ⚠️ L1→L2 积分为活跃度参考, 非硬性门槛
        ),
        growth=GrowthTrackRequirement(
            peer_req=PeerRequirement(
                total_required=4,
                min_progressed=2, progress_target="完成S0-S3",
                min_advanced=1, advanced_target="达到S4内化",
            ),
            capability_requirements=[
                "累计陪伴时长≥50h",
                "单人陪伴≥10次",
                "正确转介≥3个",
            ],
            exam_requirements=[
                "分享者培训40学时完成",
                "同伴支持技能考核通过",
                "伦理边界测试100%",
            ],
            behavior_requirements=[
                "自身行为持续稳定",
                "自愿意愿+贡献行为证明",
            ],
            ethics_requirements=["伦理边界测试100%", "不给建议/不诊断/不承诺效果"],
            min_period_months=6,
            ceremony_name="传灯者", ceremony_emoji="🕯️",
        ),
        anti_cheat_strategies=["AS-02", "AS-03"],
    ),
    
    "L2_TO_L3": LevelThreshold(
        from_level=PromotionLevel.L2_SHARER,
        to_level=PromotionLevel.L3_COACH,
        points=PointsThreshold(growth=800, contribution=100, influence=0),
        growth=GrowthTrackRequirement(
            peer_req=PeerRequirement(
                total_required=4,
                min_progressed=2, progress_target="通过分享者考核",
                min_advanced=1, advanced_target="具备教练潜力",
            ),
            capability_requirements=[
                "独立完成≥10案例",
                "≥3人实现S0-S4跃迁",
                "可解释性评分≥0.8",
            ],
            exam_requirements=[
                "400分制考核≥240分",
                "理论150分(≥90)",
                "技能150分(≥90)",
                "综合100分(≥60)",
                "伦理100%(一票否决)",
            ],
            behavior_requirements=["自身行为持续稳定"],
            ethics_requirements=["伦理测试100%", "5条伦理宣言签署"],
            min_period_months=10,
            ceremony_name="持杖者", ceremony_emoji="🪄",
        ),
        anti_cheat_strategies=["AS-04", "AS-06"],
    ),
    
    "L3_TO_L4": LevelThreshold(
        from_level=PromotionLevel.L3_COACH,
        to_level=PromotionLevel.L4_SENIOR_COACH,
        points=PointsThreshold(growth=1500, contribution=500, influence=200),
        growth=GrowthTrackRequirement(
            peer_req=PeerRequirement(
                total_required=4,
                min_progressed=2, progress_target="独立执业",
                min_advanced=1, advanced_target="成为项目负责人",
            ),
            capability_requirements=[
                "独立设计执行≥2个组织级项目",
                "累计服务≥100人",
                "带教≥5名L3(≥2人通过)",
                "≥2个模板被采纳+≥1门课程开发",
            ],
            exam_requirements=[
                "促进师认证考试",
                "高级伦理测试",
                "方案设计答辩",
                "14天专家认证",
            ],
            behavior_requirements=["项目管理经验"],
            ethics_requirements=["利益冲突披露", "14天认证全程"],
            min_period_months=12,
            ceremony_name="立柱者", ceremony_emoji="🏛️",
        ),
        anti_cheat_strategies=["AS-06", "AS-05"],
    ),
    
    "L4_TO_L5": LevelThreshold(
        from_level=PromotionLevel.L4_SENIOR_COACH,
        to_level=PromotionLevel.L5_MASTER,
        points=PointsThreshold(growth=3000, contribution=1500, influence=800),
        growth=GrowthTrackRequirement(
            peer_req=PeerRequirement(
                total_required=4,
                min_progressed=2, progress_target="成为区域/行业标杆",
                min_advanced=1, advanced_target="具备大师潜力",
            ),
            capability_requirements=[
                "促进师≥24月",
                "带教≥15名L3+≥4名L4",
                "原创方法论",
                "≥3高风险案例成功",
                "行业标准制定参与",
            ],
            exam_requirements=[
                "大师认证考试",
                "方法论同行评审",
                "专家委员会全票通过(一票否决)",
            ],
            behavior_requirements=["行业标杆级"],
            ethics_requirements=["零重大伦理事件", "终身合规"],
            min_period_months=24,
            ceremony_name="归源者", ceremony_emoji="🌊",
        ),
        anti_cheat_strategies=["AS-01", "AS-02", "AS-03", "AS-04", "AS-05", "AS-06"],
    ),
}


# ══════════════════════════════════════════
# 2. 双轨校验器
# ══════════════════════════════════════════

@dataclass
class PointsCheckResult:
    """积分轨校验结果"""
    passed: bool
    growth_current: int = 0
    growth_required: int = 0
    contribution_current: int = 0
    contribution_required: int = 0
    influence_current: int = 0
    influence_required: int = 0
    is_soft_gate: bool = False  # L1→L2 非硬性门槛


@dataclass
class GrowthCheckResult:
    """成长轨校验结果"""
    passed: bool
    peer_check: Dict[str, Any] = field(default_factory=dict)
    capability_check: Dict[str, bool] = field(default_factory=dict)
    exam_check: Dict[str, bool] = field(default_factory=dict)
    behavior_check: Dict[str, bool] = field(default_factory=dict)
    ethics_check: Dict[str, bool] = field(default_factory=dict)
    stability_90day: bool = False
    period_met: bool = False


@dataclass
class DualTrackResult:
    """双轨校验综合结果"""
    state: PromotionState
    points_result: PointsCheckResult
    growth_result: GrowthCheckResult
    promotion_key: str = ""
    ceremony_name: str = ""
    ceremony_emoji: str = ""
    guidance_message: str = ""


class DualTrackChecker:
    """
    双轨晋级校验器。
    
    集成点:
      - IncentiveEngine → 积分查询
      - StageEngine     → S0-S5 阶段查询 + 90天稳定验证
      - PeerTracking    → 同道者质量查询
      - ExamSystem      → 考核成绩查询
      - CompanionRelation → 陪伴关系查询
    """
    
    def __init__(
        self,
        points_service=None,
        stage_service=None,
        peer_service=None,
        exam_service=None,
        companion_service=None,
    ):
        self.points_svc = points_service
        self.stage_svc = stage_service
        self.peer_svc = peer_service
        self.exam_svc = exam_service
        self.companion_svc = companion_service
    
    async def check(self, user_id: int, promotion_key: str) -> DualTrackResult:
        """
        执行双轨校验。
        
        Args:
            user_id: 用户 ID
            promotion_key: 晋级键 (如 "L0_TO_L1")
        
        Returns:
            DualTrackResult 含状态+详细结果+引导话术
        """
        threshold = PROMOTION_THRESHOLDS.get(promotion_key)
        if not threshold:
            raise ValueError(f"Unknown promotion key: {promotion_key}")
        
        # 并行校验两轨
        points_result = await self._check_points_track(user_id, threshold)
        growth_result = await self._check_growth_track(user_id, threshold)
        
        # 确定状态 (Sheet④ 四种状态)
        state = self._determine_state(points_result, growth_result)
        guidance = self._get_guidance_message(state, threshold)
        
        return DualTrackResult(
            state=state,
            points_result=points_result,
            growth_result=growth_result,
            promotion_key=promotion_key,
            ceremony_name=threshold.growth.ceremony_name,
            ceremony_emoji=threshold.growth.ceremony_emoji,
            guidance_message=guidance,
        )
    
    async def _check_points_track(
        self, user_id: int, threshold: LevelThreshold
    ) -> PointsCheckResult:
        """积分轨校验"""
        pts = threshold.points
        
        # 从积分服务获取当前积分
        current = await self._get_user_points(user_id)
        
        growth_ok = current.get("growth", 0) >= pts.growth
        contrib_ok = current.get("contribution", 0) >= pts.contribution
        influence_ok = current.get("influence", 0) >= pts.influence
        
        # 综合判定
        if pts.is_hard_gate:
            passed = growth_ok and contrib_ok and influence_ok
        else:
            # L1→L2: 非硬性门槛, 作为参考值
            passed = True  # 积分不阻断, 只做参考
        
        return PointsCheckResult(
            passed=passed,
            growth_current=current.get("growth", 0),
            growth_required=pts.growth,
            contribution_current=current.get("contribution", 0),
            contribution_required=pts.contribution,
            influence_current=current.get("influence", 0),
            influence_required=pts.influence,
            is_soft_gate=not pts.is_hard_gate,
        )
    
    async def _check_growth_track(
        self, user_id: int, threshold: LevelThreshold
    ) -> GrowthCheckResult:
        """成长轨校验 (核心判定, 不可伪造)"""
        gt = threshold.growth
        
        # 1. 同道者质量校验
        peer_check = await self._check_peers(user_id, gt.peer_req)
        
        # 2. 能力/案例校验
        cap_check = await self._check_capabilities(user_id, gt.capability_requirements)
        
        # 3. 考核/认证校验
        exam_check = await self._check_exams(user_id, gt.exam_requirements)
        
        # 4. 行为要求校验
        behavior_check = await self._check_behaviors(user_id, gt.behavior_requirements)
        
        # 5. 伦理要求校验 (一票否决)
        ethics_check = await self._check_ethics(user_id, gt.ethics_requirements)
        
        # 6. 90天稳定性校验
        stability_90 = await self._check_90day_stability(user_id)
        
        # 7. 最低周期校验
        period_met = await self._check_min_period(user_id, gt.min_period_months)
        
        # 综合判定: 全部通过才算成长轨通过
        all_peers = peer_check.get("passed", False)
        all_caps = all(cap_check.values()) if cap_check else True
        all_exams = all(exam_check.values()) if exam_check else True
        all_behaviors = all(behavior_check.values()) if behavior_check else True
        all_ethics = all(ethics_check.values()) if ethics_check else True
        
        passed = all([
            all_peers, all_caps, all_exams,
            all_behaviors, all_ethics,
            stability_90, period_met,
        ])
        
        return GrowthCheckResult(
            passed=passed,
            peer_check=peer_check,
            capability_check=cap_check,
            exam_check=exam_check,
            behavior_check=behavior_check,
            ethics_check=ethics_check,
            stability_90day=stability_90,
            period_met=period_met,
        )
    
    def _determine_state(
        self, pts: PointsCheckResult, grw: GrowthCheckResult
    ) -> PromotionState:
        """确定双轨状态 (Sheet④ 4种状态)"""
        if pts.passed and grw.passed:
            return PromotionState.READY_TO_PROMOTE     # 状态4: 双轨达标
        elif pts.passed and not grw.passed:
            return PromotionState.AWAITING_VERIFY       # 状态2: 等待验证 ⚠️关键
        elif not pts.passed and grw.passed:
            return PromotionState.GROWTH_FIRST          # 状态3: 成长先到 (罕见)
        else:
            return PromotionState.NORMAL_GROWTH         # 状态1: 正常成长
    
    def _get_guidance_message(
        self, state: PromotionState, threshold: LevelThreshold
    ) -> str:
        """获取固化引导话术 (Sheet④ 双轨状态×引导话术)"""
        ceremony = threshold.growth.ceremony_name
        messages = {
            PromotionState.NORMAL_GROWTH:
                "你正在成长的路上,每一步都有价值。继续保持!",
            PromotionState.AWAITING_VERIFY:
                f"您的活跃度已经达标!接下来需要完成以下成长验证——"
                f"这些验证确保您不仅做了很多,而且真正成长为"
                f"下一级所需要的人。",
            PromotionState.GROWTH_FIRST:
                "太棒了!您的能力已经得到验证。"
                "积分只是确保您有足够的平台参与度,"
                "继续日常活动很快就能达到。",
            PromotionState.READY_TO_PROMOTE:
                f"恭喜您!积分达标+成长验证全部通过!"
                f"您已经准备好成为{ceremony}了。"
                f"点击开始晋级仪式。",
        }
        return messages.get(state, "")
    
    # ── 子服务查询 (对接现有服务) ──
    
    async def _get_user_points(self, user_id: int) -> Dict[str, int]:
        if self.points_svc:
            return await self.points_svc.get_points_summary(user_id)
        return {"growth": 0, "contribution": 0, "influence": 0}
    
    async def _check_peers(self, user_id: int, req: PeerRequirement) -> dict:
        if self.peer_svc:
            return await self.peer_svc.validate_peers(user_id, req)
        return {
            "passed": False,
            "total_count": 0,
            "total_required": req.total_required,
            "progressed_count": 0,
            "progressed_required": req.min_progressed,
            "advanced_count": 0,
            "advanced_required": req.min_advanced,
        }
    
    async def _check_capabilities(self, user_id: int, reqs: List[str]) -> Dict[str, bool]:
        if self.companion_svc and reqs:
            return await self.companion_svc.check_capability_requirements(user_id, reqs)
        return {req: False for req in reqs}
    
    async def _check_exams(self, user_id: int, reqs: List[str]) -> Dict[str, bool]:
        if self.exam_svc and reqs:
            return await self.exam_svc.check_exam_requirements(user_id, reqs)
        return {req: False for req in reqs}
    
    async def _check_behaviors(self, user_id: int, reqs: List[str]) -> Dict[str, bool]:
        if self.stage_svc and reqs:
            return await self.stage_svc.check_behavior_requirements(user_id, reqs)
        return {req: False for req in reqs}
    
    async def _check_ethics(self, user_id: int, reqs: List[str]) -> Dict[str, bool]:
        if self.exam_svc and reqs:
            return await self.exam_svc.check_ethics_requirements(user_id, reqs)
        return {req: False for req in reqs}
    
    async def _check_90day_stability(self, user_id: int) -> bool:
        if self.stage_svc:
            return await self.stage_svc.check_90day_stability(user_id)
        return False
    
    async def _check_min_period(self, user_id: int, months: int) -> bool:
        if self.stage_svc:
            return await self.stage_svc.check_min_period(user_id, months)
        return False


# ══════════════════════════════════════════
# 3. 差距分析器 (GapAnalysis API)
# ══════════════════════════════════════════

@dataclass
class GapItem:
    """差距项"""
    category: str          # points | peer | capability | exam | behavior | ethics | stability | period
    requirement: str       # 要求描述
    current: str           # 当前状态
    gap: str               # 差距描述
    actionable: bool       # 用户是否可主动解决
    estimated_days: int = 0


@dataclass
class GapReport:
    """差距分析报告"""
    user_id: int
    promotion_key: str
    state: PromotionState
    total_gaps: int
    gaps: List[GapItem]
    estimated_total_days: int
    ceremony_name: str
    ceremony_emoji: str
    generated_at: str = ""


class GapAnalyzer:
    """
    差距分析报告生成器。
    Sheet④ 状态2(等待验证)时自动触发, 生成具体差距清单。
    """
    
    def analyze(self, result: DualTrackResult) -> GapReport:
        """从双轨校验结果生成差距报告"""
        gaps: List[GapItem] = []
        
        # 积分差距
        pts = result.points_result
        if not pts.passed and not pts.is_soft_gate:
            if pts.growth_current < pts.growth_required:
                gap_val = pts.growth_required - pts.growth_current
                gaps.append(GapItem(
                    category="points",
                    requirement=f"成长积分 ≥{pts.growth_required}",
                    current=f"当前 {pts.growth_current}",
                    gap=f"差 {gap_val} 分",
                    actionable=True,
                    estimated_days=max(1, gap_val // 20),  # ~20分/天
                ))
            if pts.contribution_current < pts.contribution_required:
                gap_val = pts.contribution_required - pts.contribution_current
                gaps.append(GapItem(
                    category="points",
                    requirement=f"贡献积分 ≥{pts.contribution_required}",
                    current=f"当前 {pts.contribution_current}",
                    gap=f"差 {gap_val} 分",
                    actionable=True,
                    estimated_days=max(1, gap_val // 10),
                ))
            if pts.influence_current < pts.influence_required:
                gap_val = pts.influence_required - pts.influence_current
                gaps.append(GapItem(
                    category="points",
                    requirement=f"影响力积分 ≥{pts.influence_required}",
                    current=f"当前 {pts.influence_current}",
                    gap=f"差 {gap_val} 分",
                    actionable=True,
                    estimated_days=max(1, gap_val // 5),
                ))
        
        # 同道者差距
        grw = result.growth_result
        peer = grw.peer_check
        if not peer.get("passed", True):
            tc = peer.get("total_count", 0)
            tr = peer.get("total_required", 4)
            if tc < tr:
                gaps.append(GapItem(
                    category="peer",
                    requirement=f"同道者总数 ≥{tr} 人",
                    current=f"当前 {tc} 人",
                    gap=f"差 {tr - tc} 人",
                    actionable=True,
                    estimated_days=(tr - tc) * 30,
                ))
            pc = peer.get("progressed_count", 0)
            pr = peer.get("progressed_required", 2)
            if pc < pr:
                gaps.append(GapItem(
                    category="peer",
                    requirement=f"≥{pr} 人达到进度目标",
                    current=f"当前 {pc} 人达标",
                    gap=f"差 {pr - pc} 人",
                    actionable=False,
                    estimated_days=(pr - pc) * 60,
                ))
        
        # 能力/案例差距
        for req, passed in grw.capability_check.items():
            if not passed:
                gaps.append(GapItem(
                    category="capability",
                    requirement=req,
                    current="未完成",
                    gap="需完成",
                    actionable=True,
                    estimated_days=30,
                ))
        
        # 考核差距
        for req, passed in grw.exam_check.items():
            if not passed:
                gaps.append(GapItem(
                    category="exam",
                    requirement=req,
                    current="未通过",
                    gap="需考核",
                    actionable=True,
                    estimated_days=14,
                ))
        
        # 伦理差距 (一票否决)
        for req, passed in grw.ethics_check.items():
            if not passed:
                gaps.append(GapItem(
                    category="ethics",
                    requirement=req,
                    current="未通过",
                    gap="必须通过 (一票否决)",
                    actionable=True,
                    estimated_days=7,
                ))
        
        # 90天稳定性
        if not grw.stability_90day:
            gaps.append(GapItem(
                category="stability",
                requirement="≥1项核心行为稳定90天",
                current="未达到",
                gap="需持续行为记录",
                actionable=True,
                estimated_days=90,
            ))
        
        # 最低周期
        if not grw.period_met:
            gaps.append(GapItem(
                category="period",
                requirement="达到最低成长周期",
                current="周期不足",
                gap="需时间积累",
                actionable=False,
            ))
        
        total_est = sum(g.estimated_days for g in gaps)
        
        return GapReport(
            user_id=0,  # 由调用方填充
            promotion_key=result.promotion_key,
            state=result.state,
            total_gaps=len(gaps),
            gaps=gaps,
            estimated_total_days=total_est,
            ceremony_name=result.ceremony_name,
            ceremony_emoji=result.ceremony_emoji,
            generated_at=datetime.utcnow().isoformat(),
        )


# ══════════════════════════════════════════
# 4. 晋级状态管理器
# ══════════════════════════════════════════

class PromotionStateManager:
    """
    管理用户晋级状态持久化和状态转换。
    
    状态转换规则:
      1 → 2: 积分达标触发
      1 → 3: 成长轨通过 + 积分未达 (罕见)
      2 → 4: 成长轨全部验证通过
      3 → 4: 积分达标
      4 → 仪式: 用户点击「开始晋级仪式」
    """
    
    def __init__(self, db_session_factory=None, audit_logger=None):
        self.db_factory = db_session_factory
        self.audit = audit_logger
    
    async def get_state(self, user_id: int) -> Optional[Dict]:
        """获取用户当前晋级状态"""
        if self.db_factory:
            async with self.db_factory() as session:
                from app.models.promotion import PromotionProgress
                from sqlalchemy import select
                stmt = select(PromotionProgress).where(
                    PromotionProgress.user_id == user_id
                ).order_by(PromotionProgress.updated_at.desc())
                result = await session.execute(stmt)
                record = result.scalar_one_or_none()
                if record:
                    return {
                        "user_id": record.user_id,
                        "current_level": record.current_level,
                        "target_level": record.target_level,
                        "state": record.state,
                        "gap_report_json": record.gap_report_json,
                        "updated_at": record.updated_at.isoformat(),
                    }
        return None
    
    async def update_state(
        self,
        user_id: int,
        result: DualTrackResult,
        gap_report: Optional[GapReport] = None,
    ) -> Dict:
        """更新晋级状态"""
        state_data = {
            "user_id": user_id,
            "state": result.state.value,
            "promotion_key": result.promotion_key,
            "ceremony_name": result.ceremony_name,
            "guidance_message": result.guidance_message,
            "gap_report": asdict(gap_report) if gap_report else None,
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        # 持久化 (实际项目写DB)
        if self.db_factory:
            await self._persist_state(user_id, state_data)
        
        # 审计
        if self.audit:
            await self.audit.log(
                user_id=user_id,
                action="promotion_state_changed",
                resource_type="promotion",
                details={
                    "new_state": result.state.name,
                    "promotion_key": result.promotion_key,
                },
            )
        
        return state_data
    
    async def _persist_state(self, user_id: int, data: dict) -> None:
        """写入数据库"""
        try:
            async with self.db_factory() as session:
                from app.models.promotion import PromotionProgress
                from sqlalchemy import select
                stmt = select(PromotionProgress).where(
                    PromotionProgress.user_id == user_id
                )
                result = await session.execute(stmt)
                record = result.scalar_one_or_none()
                if record:
                    record.state = data["state"]
                    record.gap_report_json = json.dumps(
                        data.get("gap_report"), ensure_ascii=False
                    ) if data.get("gap_report") else None
                    record.updated_at = datetime.utcnow()
                else:
                    session.add(PromotionProgress(
                        user_id=user_id,
                        current_level=data["promotion_key"].split("_TO_")[0],
                        target_level=data["promotion_key"].split("_TO_")[1],
                        state=data["state"],
                        gap_report_json=json.dumps(
                            data.get("gap_report"), ensure_ascii=False
                        ) if data.get("gap_report") else None,
                    ))
                await session.commit()
        except Exception:
            pass


# ══════════════════════════════════════════
# 5. 晋级编排器 (Orchestrator)
# ══════════════════════════════════════════

class PromotionOrchestrator:
    """
    晋级流程编排器 — 核心入口。
    
    调用流程:
      1. 积分变动触发 → check_promotion_eligibility()
      2. 用户主动查询 → get_promotion_status()
      3. 晋级仪式启动 → initiate_ceremony()
    """
    
    def __init__(
        self,
        checker: DualTrackChecker,
        gap_analyzer: GapAnalyzer,
        state_manager: PromotionStateManager,
        notification_service=None,
    ):
        self.checker = checker
        self.gap_analyzer = gap_analyzer
        self.state_mgr = state_manager
        self.notifier = notification_service
    
    def get_promotion_key(self, current_level: str) -> Optional[str]:
        """根据当前等级获取晋级键"""
        level_map = {
            "L0": "L0_TO_L1", "L1": "L1_TO_L2", "L2": "L2_TO_L3",
            "L3": "L3_TO_L4", "L4": "L4_TO_L5",
        }
        return level_map.get(current_level)
    
    async def check_promotion_eligibility(
        self, user_id: int, current_level: str
    ) -> Dict:
        """
        检查晋级资格 (积分变动后自动调用)。
        
        Returns:
            {
                "state": PromotionState,
                "state_name": str,
                "guidance_message": str,
                "gap_report": GapReport | None,
                "ceremony_ready": bool,
            }
        """
        promo_key = self.get_promotion_key(current_level)
        if not promo_key:
            return {"state": None, "state_name": "max_level", "ceremony_ready": False}
        
        # 双轨校验
        result = await self.checker.check(user_id, promo_key)
        
        # 差距分析 (状态2/3时生成)
        gap_report = None
        if result.state in (PromotionState.AWAITING_VERIFY, PromotionState.GROWTH_FIRST):
            gap_report = self.gap_analyzer.analyze(result)
            gap_report.user_id = user_id
        
        # 更新状态
        await self.state_mgr.update_state(user_id, result, gap_report)
        
        # 状态2通知 (积分达标但成长未过)
        if result.state == PromotionState.AWAITING_VERIFY and self.notifier:
            await self.notifier.send(
                user_id=user_id,
                notification_type="promotion_awaiting_verify",
                data={
                    "ceremony_name": result.ceremony_name,
                    "gap_count": gap_report.total_gaps if gap_report else 0,
                    "message": result.guidance_message,
                },
            )
        
        # 状态4通知 (晋级就绪)
        if result.state == PromotionState.READY_TO_PROMOTE and self.notifier:
            await self.notifier.send(
                user_id=user_id,
                notification_type="promotion_ready",
                data={
                    "ceremony_name": result.ceremony_name,
                    "ceremony_emoji": result.ceremony_emoji,
                    "message": result.guidance_message,
                },
            )
        
        return {
            "state": result.state.value,
            "state_name": result.state.name,
            "guidance_message": result.guidance_message,
            "gap_report": asdict(gap_report) if gap_report else None,
            "ceremony_ready": result.state == PromotionState.READY_TO_PROMOTE,
            "ceremony_name": result.ceremony_name,
            "ceremony_emoji": result.ceremony_emoji,
        }
    
    async def initiate_ceremony(self, user_id: int, current_level: str) -> Dict:
        """
        启动晋级仪式 (状态4时用户点击触发)。
        
        Returns:
            {"success": bool, "new_level": str, "ceremony": dict}
        """
        promo_key = self.get_promotion_key(current_level)
        if not promo_key:
            return {"success": False, "reason": "已达最高等级"}
        
        # 最终二次校验 (防止状态不一致)
        result = await self.checker.check(user_id, promo_key)
        if result.state != PromotionState.READY_TO_PROMOTE:
            return {
                "success": False,
                "reason": "晋级条件尚未满足",
                "state": result.state.name,
            }
        
        threshold = PROMOTION_THRESHOLDS[promo_key]
        new_level = threshold.to_level.value
        
        return {
            "success": True,
            "new_level": new_level,
            "ceremony": {
                "name": threshold.growth.ceremony_name,
                "emoji": threshold.growth.ceremony_emoji,
                "from_level": current_level,
                "to_level": new_level,
                "contracts_to_sign": self._get_ceremony_contracts(promo_key),
            },
        }
    
    def _get_ceremony_contracts(self, promo_key: str) -> List[str]:
        """获取晋级仪式需签署的契约"""
        contracts = {
            "L0_TO_L1": ["数据诚实承诺", "成长契约"],
            "L1_TO_L2": ["分享诚信承诺", "共创契约", "自愿申请表"],
            "L2_TO_L3": ["教练伦理宣言5条", "专业服务契约"],
            "L3_TO_L4": ["专家责任宣言7条", "高级服务契约"],
            "L4_TO_L5": ["行业引领宣言", "引领契约"],
        }
        return contracts.get(promo_key, [])
