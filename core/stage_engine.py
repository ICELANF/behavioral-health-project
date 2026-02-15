"""
S0-S5 阶段引擎 — 成长者行为改变六阶段状态机
契约来源: Sheet⑪ 第3节「成长者S0-S5阶段化执行结构」

六阶段:
  S0 授权进入     — 同意陪伴·绑定教练·初始评估 (第1天)
  S1 觉察与稳定期 — 低压力任务·反馈习惯·中断点识别 (1-2周)
  S2 尝试与波动期 — 行为尝试·波动正常·不追求完成率 (2-4周)
  S3 形成路径期   — 主动调整·减少干预·路径形成 (4-8周)
  S4 内化期       — 行为成为习惯·自主应对波动·90天稳定 (8-16周)
  S5 转出期       — 毕业不是结束·周期性自检·贡献数据入库 (16-24周)

核心规则:
  - S2 波动不降级 (反复→留S2, 不回S1)
  - S4 需90天连续稳定验证
  - S5 强制毕业/转出机制
  - 伦理: 禁止展示风险等级/群体排名/预测结论

积分事件:
  授权完成 +20, 阶段进入 +10, 行为尝试 +10/次,
  路径形成 +20, 阶段跃迁 +30, 90天稳定 +50, 毕业 +100, 指标好转 +20/项
"""

from __future__ import annotations
import time
from datetime import datetime, date, timedelta, timezone
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field, asdict


# ══════════════════════════════════════════
# 0. 阶段定义
# ══════════════════════════════════════════

class Stage(str, Enum):
    S0_AUTHORIZATION = "S0"
    S1_AWARENESS = "S1"
    S2_TRIAL = "S2"
    S3_PATHWAY = "S3"
    S4_INTERNALIZATION = "S4"
    S5_GRADUATION = "S5"


class TransitionResult(str, Enum):
    ADVANCED = "advanced"           # 正常推进
    STAYED = "stayed"               # 留在当前阶段
    REGRESSED_TO_S2 = "regressed"   # 回到S2 (仅S3可回)
    GRADUATED = "graduated"         # 毕业
    BLOCKED = "blocked"             # 条件不满足


# ══════════════════════════════════════════
# 1. 阶段配置 (Sheet⑪ 第3节)
# ══════════════════════════════════════════

@dataclass
class StageConfig:
    stage: Stage
    name: str
    description: str
    estimated_weeks: Tuple[int, int]  # (min, max)
    points_on_enter: int
    allowed_display: List[str]       # ✅允许展示
    forbidden_display: List[str]     # ❌禁止展示
    data_collected: List[str]
    coach_focus: str
    exit_rules: Dict[str, str]       # {condition: next_stage}


STAGE_CONFIGS: Dict[Stage, StageConfig] = {
    Stage.S0_AUTHORIZATION: StageConfig(
        stage=Stage.S0_AUTHORIZATION,
        name="授权进入",
        description="明确同意被陪伴·理解非医疗非诊断·确认数据采集与隐私",
        estimated_weeks=(0, 0),
        points_on_enter=20,
        allowed_display=[],
        forbidden_display=[],
        data_collected=["授权同意", "初始评估数据", "教练绑定关系"],
        coach_focus="确认理解·建立信任",
        exit_rules={"authorization_complete": "S1"},
    ),
    Stage.S1_AWARENESS: StageConfig(
        stage=Stage.S1_AWARENESS,
        name="觉察与稳定期",
        description="接受节奏温和的任务·学会反馈·不追求完成率",
        estimated_weeks=(1, 2),
        points_on_enter=10,
        allowed_display=["行为趋势", "稳定性变化"],
        forbidden_display=["风险等级", "群体排名", "预测结论"],
        data_collected=["任务完成率", "反馈频率", "中断点模式"],
        coach_focus="反馈习惯建立·中断点识别",
        exit_rules={"feedback_habit_formed": "S2", "not_adapted": "adjust_S1"},
    ),
    Stage.S2_TRIAL: StageConfig(
        stage=Stage.S2_TRIAL,
        name="尝试与波动期",
        description="行为开始尝试但不稳定·波动正常·不追求完成率",
        estimated_weeks=(2, 4),
        points_on_enter=10,
        allowed_display=["行为趋势", "阶段语言(正在尝试)"],
        forbidden_display=["风险等级", "群体排名"],
        data_collected=["中断模式", "波动周期", "认知-行为差距"],
        coach_focus="中断模式分析·情绪支持·不批评不加压",
        exit_rules={"behavior_stabilizing": "S3", "relapse": "stay_S2"},
    ),
    Stage.S3_PATHWAY: StageConfig(
        stage=Stage.S3_PATHWAY,
        name="形成路径期",
        description="用户开始主动调整·不再完全依赖提醒",
        estimated_weeks=(4, 8),
        points_on_enter=20,
        allowed_display=["阶段语言(正在形成习惯)", "行为趋势"],
        forbidden_display=["风险等级", "预测结论"],
        data_collected=["路径形成模式", "自主决策数据", "干预频率下降"],
        coach_focus="路径模式记录·逐步放手",
        exit_rules={"pathway_formed": "S4", "regression": "S2"},
    ),
    Stage.S4_INTERNALIZATION: StageConfig(
        stage=Stage.S4_INTERNALIZATION,
        name="内化期",
        description="行为成为习惯·能自主应对波动·不再需要持续提醒",
        estimated_weeks=(8, 16),
        points_on_enter=30,
        allowed_display=["阶段语言(已形成习惯)", "稳定性数据"],
        forbidden_display=["风险等级"],
        data_collected=["习惯稳定数据", "自我觉察能力", "波动自处能力"],
        coach_focus="习惯验证·波动应对·转出准备",
        exit_rules={"90day_stable": "S5"},
    ),
    Stage.S5_GRADUATION: StageConfig(
        stage=Stage.S5_GRADUATION,
        name="转出期",
        description="退出陪伴·转为周期性自检·毕业而非结束",
        estimated_weeks=(16, 24),
        points_on_enter=100,
        allowed_display=["毕业证明", "成长轨迹回顾"],
        forbidden_display=[],
        data_collected=["毕业评估", "全流程数据", "系统沉淀"],
        coach_focus="毕业仪式·后续跟踪计划·贡献数据入库",
        exit_rules={"graduated": "complete"},
    ),
}


# ══════════════════════════════════════════
# 2. 用户阶段状态
# ══════════════════════════════════════════

@dataclass
class UserStageState:
    user_id: int
    current_stage: Stage
    stage_entered_at: str            # ISO datetime
    stage_history: List[Dict]        # [{stage, entered_at, exited_at, duration_days}]
    stability_counter_days: int = 0  # S4 90天稳定计数器
    stability_start_date: str = ""   # 稳定期开始日期
    is_graduated: bool = False
    graduation_date: str = ""
    coach_id: int = 0
    indicators_improved: int = 0     # 好转指标数
    total_duration_days: int = 0     # 总陪伴天数
    behavior_attempts: int = 0       # 行为尝试次数
    interruption_count: int = 0      # 中断次数
    feedback_frequency: float = 0.0  # 反馈频率 (次/周)
    pathway_score: float = 0.0       # 路径形成评分
    self_regulation_score: float = 0.0  # 自主调节评分

    def days_in_current_stage(self) -> int:
        entered = datetime.fromisoformat(self.stage_entered_at)
        now = datetime.now(timezone.utc)
        return (now - entered).days


# ══════════════════════════════════════════
# 3. 阶段引擎核心
# ══════════════════════════════════════════

class StageEngine:
    """
    S0-S5 阶段引擎。
    
    职责:
      1. 阶段转换判定 (advance/stay/regress)
      2. 90天稳定验证 (S4)
      3. 毕业机制 (S5)
      4. 展示权限校验 (禁止展示项)
      5. 积分事件触发
    
    关键规则:
      - S2 波动不降级: relapse → stay_S2
      - S3→S2 是唯一允许的回退
      - S4 必须连续90天稳定
      - S5 是强制设计的毕业机制
    """
    
    VALID_TRANSITIONS = {
        Stage.S0_AUTHORIZATION: [Stage.S1_AWARENESS],
        Stage.S1_AWARENESS: [Stage.S2_TRIAL],
        Stage.S2_TRIAL: [Stage.S3_PATHWAY],              # S2只能前进, 不能后退
        Stage.S3_PATHWAY: [Stage.S4_INTERNALIZATION, Stage.S2_TRIAL],  # S3可回S2
        Stage.S4_INTERNALIZATION: [Stage.S5_GRADUATION],
        Stage.S5_GRADUATION: [],                          # 终态
    }
    
    STABILITY_REQUIRED_DAYS = 90
    
    def __init__(self, points_service=None, notification_service=None):
        self.points = points_service
        self.notifications = notification_service
    
    # ── 3.1 阶段转换 ──
    
    async def evaluate_transition(
        self, state: UserStageState, metrics: Dict[str, Any]
    ) -> Tuple[TransitionResult, Optional[Stage], str]:
        """
        评估是否应推进/留存/回退阶段。
        
        Args:
            state: 当前用户阶段状态
            metrics: 行为指标数据
        
        Returns:
            (result, next_stage, reason)
        """
        current = state.current_stage
        
        if state.is_graduated:
            return TransitionResult.STAYED, None, "已毕业"
        
        evaluator = {
            Stage.S0_AUTHORIZATION: self._eval_s0,
            Stage.S1_AWARENESS: self._eval_s1,
            Stage.S2_TRIAL: self._eval_s2,
            Stage.S3_PATHWAY: self._eval_s3,
            Stage.S4_INTERNALIZATION: self._eval_s4,
            Stage.S5_GRADUATION: self._eval_s5,
        }.get(current)
        
        if not evaluator:
            return TransitionResult.BLOCKED, None, f"未知阶段: {current}"
        
        return await evaluator(state, metrics)
    
    async def _eval_s0(self, state, metrics) -> Tuple[TransitionResult, Optional[Stage], str]:
        """S0→S1: 授权完成+初始评估+教练绑定"""
        if (
            metrics.get("authorization_signed") and
            metrics.get("initial_assessment_done") and
            state.coach_id > 0
        ):
            return TransitionResult.ADVANCED, Stage.S1_AWARENESS, "授权流程完成, 进入觉察期"
        return TransitionResult.STAYED, None, "等待完成授权流程"
    
    async def _eval_s1(self, state, metrics) -> Tuple[TransitionResult, Optional[Stage], str]:
        """S1→S2: 反馈习惯形成 (反馈频率≥3次/周, 至少7天)"""
        min_days = 7
        if state.days_in_current_stage() < min_days:
            return TransitionResult.STAYED, None, f"需在S1至少{min_days}天"
        
        if (
            metrics.get("feedback_frequency", 0) >= 3.0 and
            metrics.get("has_identified_interruption_points", False)
        ):
            return TransitionResult.ADVANCED, Stage.S2_TRIAL, "反馈习惯已建立, 进入尝试期"
        return TransitionResult.STAYED, None, "反馈习惯仍在培养中"
    
    async def _eval_s2(self, state, metrics) -> Tuple[TransitionResult, Optional[Stage], str]:
        """S2→S3: 行为开始稳定 (波动减少, 尝试≥5次)"""
        # ⚠️ S2 波动不降级, 只能前进或留存
        min_days = 14
        if state.days_in_current_stage() < min_days:
            return TransitionResult.STAYED, None, f"需在S2至少{min_days}天"
        
        if (
            metrics.get("behavior_attempts", 0) >= 5 and
            metrics.get("volatility_decreasing", False) and
            metrics.get("cognitive_behavior_gap_narrowing", False)
        ):
            return TransitionResult.ADVANCED, Stage.S3_PATHWAY, "行为趋于稳定, 进入路径形成期"
        
        # 波动→留S2 (关键: 不降级)
        return TransitionResult.STAYED, None, "波动正常, 继续尝试 (波动不降级)"
    
    async def _eval_s3(self, state, metrics) -> Tuple[TransitionResult, Optional[Stage], str]:
        """S3→S4 或 S3→S2: 路径形成 或 回退"""
        min_days = 28
        if state.days_in_current_stage() < min_days:
            return TransitionResult.STAYED, None, f"需在S3至少{min_days}天"
        
        # 路径形成: 自主决策增加, 干预频率下降
        if (
            metrics.get("pathway_score", 0) >= 0.7 and
            metrics.get("intervention_frequency_decreased", False) and
            metrics.get("autonomous_decisions", 0) >= 10
        ):
            return TransitionResult.ADVANCED, Stage.S4_INTERNALIZATION, "路径已形成, 进入内化期"
        
        # 严重波动 → 回退S2 (S3是唯一允许回退的阶段)
        if metrics.get("severe_regression", False):
            return TransitionResult.REGRESSED_TO_S2, Stage.S2_TRIAL, "行为出现较大波动, 回到尝试期 (这是正常的)"
        
        return TransitionResult.STAYED, None, "路径仍在形成中"
    
    async def _eval_s4(self, state, metrics) -> Tuple[TransitionResult, Optional[Stage], str]:
        """S4→S5: 90天连续稳定 (核心防刷机制)"""
        # 90天稳定验证
        stability_ok = await self.check_90day_stability(state, metrics)
        
        if stability_ok:
            return TransitionResult.ADVANCED, Stage.S5_GRADUATION, "90天稳定验证通过! 准备毕业"
        
        # 中断 → 重置计数器 (但不回退阶段)
        if metrics.get("stability_broken", False):
            return TransitionResult.STAYED, None, "稳定期中断, 重新开始计数 (不降级)"
        
        return TransitionResult.STAYED, None, f"稳定验证中 ({state.stability_counter_days}/90天)"
    
    async def _eval_s5(self, state, metrics) -> Tuple[TransitionResult, Optional[Stage], str]:
        """S5: 毕业/转出"""
        if metrics.get("graduation_ceremony_complete", False):
            return TransitionResult.GRADUATED, None, "毕业! 转为周期性自检"
        return TransitionResult.STAYED, None, "准备毕业仪式中"
    
    # ── 3.2 执行转换 ──
    
    async def execute_transition(
        self, state: UserStageState, metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行阶段转换并触发副作用 (积分/通知)"""
        result, next_stage, reason = await self.evaluate_transition(state, metrics)
        
        response = {
            "result": result.value,
            "current_stage": state.current_stage.value,
            "next_stage": next_stage.value if next_stage else None,
            "reason": reason,
            "points_awarded": 0,
            "notifications": [],
        }
        
        if result in (TransitionResult.ADVANCED, TransitionResult.REGRESSED_TO_S2, TransitionResult.GRADUATED):
            # 记录离开旧阶段
            old_stage = state.current_stage
            state.stage_history.append({
                "stage": old_stage.value,
                "entered_at": state.stage_entered_at,
                "exited_at": datetime.now(timezone.utc).isoformat(),
                "duration_days": state.days_in_current_stage(),
            })
            
            if result == TransitionResult.GRADUATED:
                state.is_graduated = True
                state.graduation_date = datetime.now(timezone.utc).isoformat()
                response["points_awarded"] = 100  # 毕业+100
                
                # 指标好转积分
                indicator_bonus = state.indicators_improved * 20
                response["points_awarded"] += indicator_bonus
                response["indicator_bonus"] = indicator_bonus
            else:
                # 进入新阶段
                state.current_stage = next_stage
                state.stage_entered_at = datetime.now(timezone.utc).isoformat()
                
                config = STAGE_CONFIGS[next_stage]
                response["points_awarded"] = config.points_on_enter
                
                if next_stage == Stage.S4_INTERNALIZATION:
                    # 启动90天稳定计数器
                    state.stability_counter_days = 0
                    state.stability_start_date = date.today().isoformat()
            
            # 通知
            response["notifications"].append({
                "type": "stage_transition",
                "from": old_stage.value,
                "to": next_stage.value if next_stage else "graduated",
                "message": reason,
            })
        
        return response
    
    # ── 3.3 90天稳定验证 ──
    
    async def check_90day_stability(
        self, state: UserStageState, metrics: Dict[str, Any]
    ) -> bool:
        """
        S4 核心: 90天连续稳定验证。
        
        稳定条件:
          - 行为习惯保持率 ≥ 80%
          - 无连续3天以上中断
          - 自主应对波动 (无教练干预)
        """
        if state.current_stage != Stage.S4_INTERNALIZATION:
            return False
        
        habit_retention = metrics.get("habit_retention_rate", 0)
        max_gap_days = metrics.get("max_consecutive_gap_days", 999)
        coach_interventions = metrics.get("coach_interventions_last_90d", 999)
        
        daily_stable = (
            habit_retention >= 0.8 and
            max_gap_days <= 3 and
            coach_interventions <= 2
        )
        
        if daily_stable:
            state.stability_counter_days = metrics.get("consecutive_stable_days", 0)
        else:
            # 中断 → 重置
            state.stability_counter_days = 0
            state.stability_start_date = date.today().isoformat()
        
        return state.stability_counter_days >= self.STABILITY_REQUIRED_DAYS
    
    # ── 3.4 展示权限 ──
    
    def get_display_permissions(self, stage: Stage) -> Dict[str, List[str]]:
        """返回指定阶段的展示/禁止项 (Sheet⑪ 红线 RED-01~06)"""
        config = STAGE_CONFIGS.get(stage)
        if not config:
            return {"allowed": [], "forbidden": []}
        
        return {
            "allowed": config.allowed_display,
            "forbidden": config.forbidden_display + [
                # 全局禁止 (RED-01~06)
                "R0-R4风险标签",
                "BPT类型判断",
                "用户归因评价",
                "强制转化话术",
                "制造焦虑内容",
            ],
        }
    
    def is_display_allowed(self, stage: Stage, display_item: str) -> bool:
        """校验某展示项在当前阶段是否允许"""
        perms = self.get_display_permissions(stage)
        if display_item in perms["forbidden"]:
            return False
        return True
    
    # ── 3.5 阶段摘要 (前端可视化数据源) ──
    
    def get_stage_summary(self, state: UserStageState) -> Dict[str, Any]:
        """生成前端可视化所需的阶段摘要数据"""
        config = STAGE_CONFIGS[state.current_stage]
        
        # 阶段语言 (Sheet⑪: 不同阶段不同话术)
        stage_language = {
            Stage.S0_AUTHORIZATION: "准备开始你的成长之旅",
            Stage.S1_AWARENESS: "正在培养觉察习惯",
            Stage.S2_TRIAL: "正在尝试新行为 — 波动是正常的",
            Stage.S3_PATHWAY: "正在形成自己的习惯路径",
            Stage.S4_INTERNALIZATION: "行为已开始内化为习惯",
            Stage.S5_GRADUATION: "即将毕业 — 这是新的开始",
        }
        
        progress_pct = self._calculate_progress(state)
        
        return {
            "user_id": state.user_id,
            "current_stage": state.current_stage.value,
            "stage_name": config.name,
            "stage_language": stage_language[state.current_stage],
            "description": config.description,
            "days_in_stage": state.days_in_current_stage(),
            "estimated_weeks": config.estimated_weeks,
            "progress_percent": progress_pct,
            "display_permissions": self.get_display_permissions(state.current_stage),
            "coach_focus": config.coach_focus,
            "data_collected": config.data_collected,
            "is_graduated": state.is_graduated,
            "stability_progress": {
                "days": state.stability_counter_days,
                "required": self.STABILITY_REQUIRED_DAYS,
                "percent": round(state.stability_counter_days / self.STABILITY_REQUIRED_DAYS * 100, 1),
            } if state.current_stage == Stage.S4_INTERNALIZATION else None,
            "journey_timeline": self._build_timeline(state),
        }
    
    def _calculate_progress(self, state: UserStageState) -> float:
        """计算当前阶段内进度百分比"""
        config = STAGE_CONFIGS[state.current_stage]
        min_weeks, max_weeks = config.estimated_weeks
        if max_weeks == 0:
            return 100.0 if state.is_graduated else 50.0
        
        days = state.days_in_current_stage()
        mid_weeks = (min_weeks + max_weeks) / 2
        expected_days = mid_weeks * 7
        
        if expected_days == 0:
            return 100.0
        
        return min(100.0, round(days / expected_days * 100, 1))
    
    def _build_timeline(self, state: UserStageState) -> List[Dict]:
        """构建成长轨迹时间线"""
        timeline = []
        
        for record in state.stage_history:
            stage_val = record["stage"]
            config = STAGE_CONFIGS.get(Stage(stage_val))
            timeline.append({
                "stage": stage_val,
                "name": config.name if config else stage_val,
                "entered_at": record["entered_at"],
                "exited_at": record["exited_at"],
                "duration_days": record["duration_days"],
                "status": "completed",
            })
        
        # 当前阶段
        config = STAGE_CONFIGS[state.current_stage]
        timeline.append({
            "stage": state.current_stage.value,
            "name": config.name,
            "entered_at": state.stage_entered_at,
            "exited_at": None,
            "duration_days": state.days_in_current_stage(),
            "status": "graduated" if state.is_graduated else "current",
        })
        
        # 未来阶段 (灰色占位)
        stage_order = [s for s in Stage]
        current_idx = stage_order.index(state.current_stage)
        for future_stage in stage_order[current_idx + 1:]:
            config = STAGE_CONFIGS[future_stage]
            timeline.append({
                "stage": future_stage.value,
                "name": config.name,
                "entered_at": None,
                "exited_at": None,
                "duration_days": 0,
                "status": "upcoming",
            })
        
        return timeline
    
    # ── 3.6 批量状态查询 (教练视角) ──
    
    async def get_coach_overview(
        self, coach_id: int, student_states: List[UserStageState]
    ) -> Dict[str, Any]:
        """教练视角: 所有学员阶段分布概览"""
        distribution = {s.value: 0 for s in Stage}
        graduated_count = 0
        alerts = []
        
        for state in student_states:
            if state.coach_id != coach_id:
                continue
            
            if state.is_graduated:
                graduated_count += 1
            else:
                distribution[state.current_stage.value] += 1
            
            # 检查需关注的学员
            days = state.days_in_current_stage()
            config = STAGE_CONFIGS[state.current_stage]
            _, max_weeks = config.estimated_weeks
            
            if max_weeks > 0 and days > max_weeks * 7 * 1.5:
                alerts.append({
                    "user_id": state.user_id,
                    "stage": state.current_stage.value,
                    "days_in_stage": days,
                    "expected_max_days": max_weeks * 7,
                    "alert_type": "extended_stay",
                    "message": f"学员在{config.name}已停留{days}天, 超过预期",
                })
        
        return {
            "coach_id": coach_id,
            "stage_distribution": distribution,
            "graduated_count": graduated_count,
            "total_students": sum(distribution.values()) + graduated_count,
            "alerts": alerts,
        }
