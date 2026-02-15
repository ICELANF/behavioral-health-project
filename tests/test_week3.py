"""
Week 3 全量测试套件
覆盖:
  STG-01~10: S0-S5 阶段引擎 (10 cases)
  RSP-01~08: 责任追踪服务 (8 cases)
  GOV-01~06: 治理仪表盘 (6 cases)
  CEX-01~10: 约束退出机制 (10 cases)
"""

import pytest
import sys, os

# 路径设置
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stage_engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'responsibility_tracker'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'governance_dashboard'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'constraint_exit'))

from stage_engine import (
    Stage, StageConfig, StageEngine, UserStageState,
    STAGE_CONFIGS, TransitionResult,
)
from responsibility_tracker import (
    ResponsibilityTracker, HealthColor, RESPONSIBILITY_REGISTRY,
    ROLE_RESPONSIBILITIES, LEVEL_TO_ROLE,
)
from governance_dashboard import (
    GovernanceDashboard, COACH_KPI_DEFINITIONS,
)
from constraint_exit_engine import (
    ConstraintEngine, ViolationType, ExitType,
    VIOLATION_CONFIGS,
)

from datetime import datetime, timezone, timedelta


# ════════════════════════════════
# Helpers
# ════════════════════════════════

def make_stage_state(**kwargs) -> UserStageState:
    defaults = {
        "user_id": 1,
        "current_stage": Stage.S1_AWARENESS,
        "stage_entered_at": (datetime.now(timezone.utc) - timedelta(days=14)).isoformat(),
        "stage_history": [],
        "coach_id": 100,
    }
    defaults.update(kwargs)
    return UserStageState(**defaults)


# ════════════════════════════════
# STG-01~10: S0-S5 阶段引擎
# ════════════════════════════════

def test_stg01_six_stages_defined():
    """全部6个阶段配置存在"""
    assert len(STAGE_CONFIGS) == 6
    for stage in Stage:
        assert stage in STAGE_CONFIGS


def test_stg02_stage_display_permissions():
    """各阶段展示/禁止项正确 (Sheet⑪ RED-01~06)"""
    engine = StageEngine()
    
    # S1: 禁止风险等级、群体排名、预测结论
    perms = engine.get_display_permissions(Stage.S1_AWARENESS)
    assert "风险等级" in perms["forbidden"]
    assert "群体排名" in perms["forbidden"]
    assert "预测结论" in perms["forbidden"]
    assert "行为趋势" in perms["allowed"]
    
    # 全局禁止项
    assert "R0-R4风险标签" in perms["forbidden"]


@pytest.mark.asyncio
async def test_stg03_s0_to_s1_transition():
    """S0→S1: 授权完成+初始评估+教练绑定"""
    engine = StageEngine()
    state = make_stage_state(current_stage=Stage.S0_AUTHORIZATION)
    
    metrics = {
        "authorization_signed": True,
        "initial_assessment_done": True,
    }
    
    result, next_stage, reason = await engine.evaluate_transition(state, metrics)
    assert result == TransitionResult.ADVANCED
    assert next_stage == Stage.S1_AWARENESS


@pytest.mark.asyncio
async def test_stg04_s1_to_s2_needs_feedback():
    """S1→S2: 需要反馈习惯形成"""
    engine = StageEngine()
    state = make_stage_state(current_stage=Stage.S1_AWARENESS)
    
    # 反馈不足 → 留在S1
    metrics = {"feedback_frequency": 1.0, "has_identified_interruption_points": False}
    result, _, _ = await engine.evaluate_transition(state, metrics)
    assert result == TransitionResult.STAYED
    
    # 反馈达标 → 进入S2
    metrics = {"feedback_frequency": 4.0, "has_identified_interruption_points": True}
    result, next_stage, _ = await engine.evaluate_transition(state, metrics)
    assert result == TransitionResult.ADVANCED
    assert next_stage == Stage.S2_TRIAL


@pytest.mark.asyncio
async def test_stg05_s2_no_regression():
    """S2: 波动不降级 (核心规则)"""
    engine = StageEngine()
    state = make_stage_state(current_stage=Stage.S2_TRIAL)
    
    # 波动 → 留在S2, 不回S1
    metrics = {"behavior_attempts": 2, "volatility_decreasing": False}
    result, next_stage, reason = await engine.evaluate_transition(state, metrics)
    assert result == TransitionResult.STAYED
    assert next_stage is None
    assert "不降级" in reason


@pytest.mark.asyncio
async def test_stg06_s3_can_regress_to_s2():
    """S3→S2: S3是唯一允许回退的阶段"""
    engine = StageEngine()
    state = make_stage_state(
        current_stage=Stage.S3_PATHWAY,
        stage_entered_at=(datetime.now(timezone.utc) - timedelta(days=35)).isoformat(),
    )
    
    metrics = {"severe_regression": True, "pathway_score": 0.2}
    result, next_stage, _ = await engine.evaluate_transition(state, metrics)
    assert result == TransitionResult.REGRESSED_TO_S2
    assert next_stage == Stage.S2_TRIAL


@pytest.mark.asyncio
async def test_stg07_s4_90day_stability():
    """S4: 90天稳定验证"""
    engine = StageEngine()
    state = make_stage_state(
        current_stage=Stage.S4_INTERNALIZATION,
        stability_counter_days=89,
    )
    
    # 89天 → 未达标
    metrics = {"habit_retention_rate": 0.9, "max_consecutive_gap_days": 1,
               "coach_interventions_last_90d": 0, "consecutive_stable_days": 89}
    stable = await engine.check_90day_stability(state, metrics)
    assert stable is False
    
    # 90天 → 达标
    state.stability_counter_days = 90
    metrics["consecutive_stable_days"] = 90
    stable = await engine.check_90day_stability(state, metrics)
    assert stable is True


@pytest.mark.asyncio
async def test_stg08_s4_stability_reset():
    """S4: 稳定中断重置计数器 (不降级)"""
    engine = StageEngine()
    state = make_stage_state(
        current_stage=Stage.S4_INTERNALIZATION,
        stability_counter_days=60,
    )
    
    # 保持率低 → 重置
    metrics = {"habit_retention_rate": 0.5, "max_consecutive_gap_days": 5,
               "coach_interventions_last_90d": 0, "consecutive_stable_days": 0}
    await engine.check_90day_stability(state, metrics)
    assert state.stability_counter_days == 0


@pytest.mark.asyncio
async def test_stg09_graduation():
    """S5: 毕业机制"""
    engine = StageEngine()
    state = make_stage_state(
        current_stage=Stage.S5_GRADUATION,
        indicators_improved=3,
    )
    
    metrics = {"graduation_ceremony_complete": True}
    result, _, _ = await engine.evaluate_transition(state, metrics)
    assert result == TransitionResult.GRADUATED


def test_stg10_stage_summary():
    """阶段摘要数据完整性"""
    engine = StageEngine()
    state = make_stage_state(current_stage=Stage.S3_PATHWAY)
    
    summary = engine.get_stage_summary(state)
    assert summary["current_stage"] == "S3"
    assert summary["stage_name"] == "形成路径期"
    assert "stage_language" in summary
    assert "journey_timeline" in summary
    assert "display_permissions" in summary


# ════════════════════════════════
# RSP-01~08: 责任追踪服务
# ════════════════════════════════

def test_rsp01_registry_completeness():
    """34条责任项注册完整"""
    assert len(RESPONSIBILITY_REGISTRY) == 34
    
    role_counts = {"成长者": 6, "分享者": 5, "教练": 10, "促进师": 7, "大师": 6}
    for role, expected in role_counts.items():
        actual = len(ROLE_RESPONSIBILITIES[role])
        assert actual == expected, f"{role}: expected {expected}, got {actual}"


def test_rsp02_level_to_role_mapping():
    """层级→角色映射正确"""
    assert LEVEL_TO_ROLE["L0"] == "成长者"
    assert LEVEL_TO_ROLE["L2"] == "分享者"
    assert LEVEL_TO_ROLE["L3"] == "教练"
    assert LEVEL_TO_ROLE["L4"] == "促进师"
    assert LEVEL_TO_ROLE["L5"] == "大师"


@pytest.mark.asyncio
async def test_rsp03_health_report_green():
    """全绿健康报告"""
    tracker = ResponsibilityTracker()
    metrics = {
        "data_entry_frequency": 5,
        "program_interaction_rate": 0.8,
        "weekly_learning_minutes": 60,
        "safety_interception_rate": 0.01,
        "coach_message_reply_rate": 0.9,
        "crisis_keyword_triggers": True,
    }
    report = await tracker.generate_health_report(1, "L1", metrics)
    assert report.overall_color == HealthColor.GREEN
    assert report.green_count == 6
    assert report.health_score == 100.0


@pytest.mark.asyncio
async def test_rsp04_health_report_red():
    """包含红色告警的报告"""
    tracker = ResponsibilityTracker()
    metrics = {
        "data_entry_frequency": 0,      # RED: 无录入
        "program_interaction_rate": 0.8,
        "weekly_learning_minutes": 60,
        "safety_interception_rate": 0.01,
        "coach_message_reply_rate": 0.9,
        "crisis_keyword_triggers": True,
    }
    report = await tracker.generate_health_report(1, "L1", metrics)
    assert report.overall_color == HealthColor.RED
    assert report.red_count >= 1


@pytest.mark.asyncio
async def test_rsp05_coach_10_items():
    """教练10条责任全量评估"""
    tracker = ResponsibilityTracker()
    report = await tracker.generate_health_report(100, "L3")
    assert len(report.items) == 10
    assert report.role == "教练"


@pytest.mark.asyncio
async def test_rsp06_batch_check():
    """批量检查"""
    tracker = ResponsibilityTracker()
    users = [(1, "L1"), (2, "L3"), (3, "L4")]
    reports = await tracker.batch_check(users)
    assert len(reports) == 3


def test_rsp07_registry_stats():
    """注册表统计"""
    tracker = ResponsibilityTracker()
    stats = tracker.get_all_registry_stats()
    assert stats["total_items"] == 34
    assert stats["auto_count"] + stats["semi_auto_count"] == 34


def test_rsp08_role_query():
    """按角色查询责任项"""
    tracker = ResponsibilityTracker()
    items = tracker.get_responsibilities_for_role("教练")
    assert len(items) == 10
    assert all(i["code"].startswith("COA") for i in items)


# ════════════════════════════════
# GOV-01~06: 治理仪表盘
# ════════════════════════════════

def test_gov01_kpi_definitions():
    """教练10项KPI定义完整"""
    assert len(COACH_KPI_DEFINITIONS) == 10


@pytest.mark.asyncio
async def test_gov02_coach_kpi_all_green():
    """全绿KPI仪表盘"""
    dashboard = GovernanceDashboard()
    metrics = {
        "student_data_view_frequency": 3,
        "avg_response_time_hours": 12,
        "alert_response_time": 2,
        "safety_pipeline_interception_rate": 0.02,
        "quarterly_credits": 30,
        "assessment_review_days": 5,
        "monthly_complaint_count": 0,
        "out_of_scope_referral_rate": 1.0,
        "mentee_quality_score": 4.2,
        "unauthorized_access_count": 0,
    }
    result = await dashboard.get_coach_kpi_dashboard(100, metrics)
    assert result["summary"]["overall_color"] == "green"
    assert result["summary"]["green"] == 10
    assert result["summary"]["health_score"] == 100.0


@pytest.mark.asyncio
async def test_gov03_kpi_red_with_escalation():
    """红色KPI触发自动升级"""
    dashboard = GovernanceDashboard()
    metrics = {
        "student_data_view_frequency": 3,
        "avg_response_time_hours": 60,     # RED: >48h → 升级Admin
        "alert_response_time": 2,
        "safety_pipeline_interception_rate": 0.02,
        "quarterly_credits": 30,
        "assessment_review_days": 5,
        "monthly_complaint_count": 3,       # RED: ≥2 → 升级督导
        "out_of_scope_referral_rate": 1.0,
        "mentee_quality_score": 4.2,
        "unauthorized_access_count": 0,
    }
    result = await dashboard.get_coach_kpi_dashboard(100, metrics)
    assert result["summary"]["overall_color"] == "red"
    assert len(result["escalations"]) == 2
    escalation_targets = {e["target"] for e in result["escalations"]}
    assert "Admin" in escalation_targets
    assert "督导" in escalation_targets


@pytest.mark.asyncio
async def test_gov04_org_overview():
    """组织级聚合概览"""
    dashboard = GovernanceDashboard()
    tracker = ResponsibilityTracker()
    
    reports = []
    for uid, level in [(1, "L1"), (2, "L1"), (3, "L3")]:
        r = await tracker.generate_health_report(uid, level)
        reports.append(r)
    
    overview = await dashboard.get_org_overview(reports)
    assert overview["total_users"] == 3
    assert "role_breakdown" in overview


@pytest.mark.asyncio
async def test_gov05_alert_pipeline():
    """告警管道处理"""
    dashboard = GovernanceDashboard()
    tracker = ResponsibilityTracker()
    
    # 创建含红色告警的报告
    metrics = {"data_entry_frequency": 0}
    report = await tracker.generate_health_report(1, "L1", metrics)
    
    alerts = await dashboard.process_alerts([report])
    # 至少有1个红色告警
    red_items = [i for i in report.items if i.color == HealthColor.RED]
    if red_items:
        assert len(alerts) >= 1


@pytest.mark.asyncio
async def test_gov06_kpi_yellow_boundary():
    """KPI黄色边界值"""
    dashboard = GovernanceDashboard()
    metrics = {
        "student_data_view_frequency": 0.5,  # YELLOW
        "avg_response_time_hours": 36,        # YELLOW
        "alert_response_time": 6,             # YELLOW
        "safety_pipeline_interception_rate": 0.07,  # YELLOW
        "quarterly_credits": 22,              # YELLOW
        "assessment_review_days": 10,         # YELLOW
        "monthly_complaint_count": 1,         # YELLOW
        "out_of_scope_referral_rate": 0.85,   # YELLOW
        "mentee_quality_score": 3.2,          # YELLOW
        "unauthorized_access_count": 0,       # GREEN
    }
    result = await dashboard.get_coach_kpi_dashboard(100, metrics)
    assert result["summary"]["yellow"] >= 8


# ════════════════════════════════
# CEX-01~10: 约束退出机制
# ════════════════════════════════

def test_cex01_violation_configs():
    """5类违规配置完整"""
    assert len(VIOLATION_CONFIGS) == 5
    for vtype in ViolationType:
        assert vtype in VIOLATION_CONFIGS


@pytest.mark.asyncio
async def test_cex02_minor_complaint():
    """轻微投诉: -20积分+警告"""
    engine = ConstraintEngine()
    result = await engine.process_violation(
        user_id=1,
        violation_type=ViolationType.MINOR_COMPLAINT,
        description="学员反馈态度不佳",
        current_points=500,
    )
    assert result["record"]["points_deducted"] == 20
    assert "警告" in result["record"]["action_taken"]
    assert result["record"]["appeal_deadline"] != ""


@pytest.mark.asyncio
async def test_cex03_protection_period():
    """新晋级保护期: 首次免罚"""
    engine = ConstraintEngine()
    
    # 激活保护期
    engine.activate_protection(1, datetime.now(timezone.utc).isoformat())
    
    result = await engine.process_violation(
        user_id=1,
        violation_type=ViolationType.MINOR_COMPLAINT,
        current_points=500,
    )
    assert result["protection_applied"] is True
    assert result["record"]["points_deducted"] == 0


@pytest.mark.asyncio
async def test_cex04_ethics_redline_permanent():
    """伦理红线: 永久取消, 不可恢复"""
    engine = ConstraintEngine()
    result = await engine.process_violation(
        user_id=1,
        violation_type=ViolationType.ETHICS_REDLINE,
        description="严重伦理违规",
        current_level="L3",
        current_points=1500,
    )
    assert result["record"]["points_deducted"] == 1500  # 清零
    assert result["demotion"]["new_level"] == "TERMINATED"
    assert result["exit"] is not None
    assert result["exit"]["recovery_eligible"] is False


@pytest.mark.asyncio
async def test_cex05_second_overreach_demotion():
    """越权二次: 降级+观察期"""
    engine = ConstraintEngine()
    result = await engine.process_violation(
        user_id=1,
        violation_type=ViolationType.SECOND_OVERREACH,
        current_level="L3",
        current_points=800,
    )
    assert result["record"]["points_deducted"] == 300
    assert result["demotion"]["new_level"] == "L2"
    assert result["demotion"]["observation_days"] == 180


@pytest.mark.asyncio
async def test_cex06_kpi_no_penalty():
    """KPI不达标: 不扣积分"""
    engine = ConstraintEngine()
    result = await engine.process_violation(
        user_id=1,
        violation_type=ViolationType.KPI_UNDERPERFORM,
        current_points=1000,
    )
    assert result["record"]["points_deducted"] == 0


@pytest.mark.asyncio
async def test_cex07_voluntary_exit():
    """自愿退出: 积分冻结, 可恢复"""
    engine = ConstraintEngine()
    result = await engine.process_exit(
        user_id=1, exit_type=ExitType.VOLUNTARY,
        current_level="L2", current_points=500,
    )
    assert result["points_status"] == "frozen"
    assert result["points_frozen"] == 500
    assert result["recovery_eligible"] is True


@pytest.mark.asyncio
async def test_cex08_forced_exit():
    """强制退出: 不可恢复"""
    engine = ConstraintEngine()
    result = await engine.process_exit(
        user_id=1, exit_type=ExitType.FORCED,
        current_level="L3", current_points=1000,
        reason="伦理红线",
    )
    assert result["points_status"] == "cleared"
    assert result["recovery_eligible"] is False


@pytest.mark.asyncio
async def test_cex09_recovery_request():
    """恢复申请流程"""
    engine = ConstraintEngine()
    
    # 先退出
    await engine.process_exit(1, ExitType.VOLUNTARY, "L2", 500)
    
    # 申请恢复
    result = await engine.request_recovery(1)
    assert result["eligible"] is True
    assert result["previous_level"] == "L2"
    assert result["points_frozen"] == 500
    assert len(result["recovery_steps"]) == 4


@pytest.mark.asyncio
async def test_cex10_ethics_no_recovery():
    """伦理红线退出后无法恢复"""
    engine = ConstraintEngine()
    
    await engine.process_exit(1, ExitType.FORCED, "L3", 1000, "伦理红线")
    
    result = await engine.request_recovery(1)
    assert result["eligible"] is False
    assert "不可恢复" in result["reason"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
