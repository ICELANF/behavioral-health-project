"""
HabitTrackerAgent — 习惯追踪 + 趋势分析

功能:
  - 读取用户打卡/任务完成数据 → 趋势分析
  - 智能反馈: 连续天数激励 / 中断预警 / 完成率评估
  - 成就系统触发 (与积分激励协同)

路由触发:
  关键词: 打卡/习惯/坚持了/连续/记录/追踪/完成率/趋势/统计/进步

数据源:
  - micro_action_tasks 表 (通过 context 传入摘要)
  - device_data.tasks (设备同步的任务数据)

来源: 合并 assistant_agents/remaining_agents.py::HabitTrackerAgent 设计
      + daily_tasks_api.py 的数据逻辑
"""
from __future__ import annotations
import logging
from typing import Any, Dict

from ..base import BaseAgent, AgentDomain, AgentInput, AgentResult, RiskLevel

logger = logging.getLogger(__name__)

# 连续天数激励模板
STREAK_MILESTONES = {
    3: "连续3天！好的开始是成功的一半 💪",
    7: "一周了！习惯正在形成中 🌱",
    14: "两周坚持！你已经超过了大多数人 🎯",
    21: "21天！习惯的种子已经发芽了 🌿",
    30: "一个月！你正在改变自己的生活方式 🌟",
    60: "两个月！这已经不只是习惯，而是你的一部分了 ⭐",
    90: "90天！你是真正的行动者 🏆",
    180: "半年坚持！你的毅力令人敬佩 🎖️",
    365: "一整年！你已经是健康生活的榜样了 👑",
}


class HabitTrackerAgent(BaseAgent):
    """
    习惯追踪 Agent — 用户层

    区别于 daily_tasks_api (CRUD):
      - 这个 Agent 做"分析+反馈", 不做"增删改查"
      - 趋势分析: 完成率变化、最佳/最差时段、中断风险
      - 智能激励: 基于连续天数+阶段的个性化反馈
    """
    domain = AgentDomain.BEHAVIOR_RX  # 归属行为处方领域
    display_name = "习惯追踪"
    keywords = ["打卡", "习惯", "坚持了", "连续", "记录", "追踪",
                "完成率", "趋势", "统计", "进步"]
    data_fields = ["tasks"]
    priority = 4
    base_weight = 0.6
    enable_llm = True
    evidence_tier = "T3"

    def process(self, inp: AgentInput) -> AgentResult:
        profile = inp.profile
        context = inp.context
        stage = profile.get("current_stage", "S0")

        # 提取习惯追踪数据 — 优先从 context 读取, 否则从 DB 查询
        stats = self._load_task_stats(inp.user_id, context)
        streak_days = stats["streak_days"]
        completion_rate = stats["completion_rate"]
        tasks_today = stats["tasks_today"]
        tasks_done_today = stats["tasks_done_today"]
        recent_trend = stats["trend"]

        findings = []
        recommendations = []
        tasks = []

        # 1. 连续天数分析
        if streak_days > 0:
            findings.append(f"已连续打卡 {streak_days} 天")
            # 里程碑检测
            milestone_msg = self._check_milestone(streak_days)
            if milestone_msg:
                recommendations.append(milestone_msg)
            else:
                recommendations.append(f"继续保持！距离下一个里程碑还有 "
                                       f"{self._next_milestone(streak_days) - streak_days} 天")
        else:
            findings.append("尚未开始连续打卡")
            if stage in ("S0", "S1"):
                recommendations.append("不用急，从记录一次开始就好")
            else:
                recommendations.append("今天是重新开始的好时候，完成一个小任务试试？")
                tasks.append({"type": "restart_streak",
                              "description": "完成今天的第一个任务, 重启连续记录",
                              "difficulty": "minimal"})

        # 2. 完成率分析
        if completion_rate is not None:
            if completion_rate >= 0.8:
                findings.append(f"近期完成率 {completion_rate:.0%}, 表现优秀")
                recommendations.append("完成率很高！可以考虑尝试一个进阶任务")
            elif completion_rate >= 0.5:
                findings.append(f"近期完成率 {completion_rate:.0%}")
                recommendations.append("稳步前进中，保持现在的节奏就好")
            else:
                findings.append(f"近期完成率 {completion_rate:.0%}, 需要关注")
                recommendations.append("完成率有些低，我们来看看哪些任务可以调整难度")
                tasks.append({"type": "review_tasks",
                              "description": "回顾本周任务, 标记太难的部分",
                              "difficulty": "easy"})

        # 3. 趋势分析
        if recent_trend == "declining":
            findings.append("近期完成趋势下降")
            recommendations.append("最近是不是遇到了什么困难？可以和我聊聊")
        elif recent_trend == "improving":
            findings.append("近期完成趋势上升")
            recommendations.append("趋势很好！你的努力正在产生效果")

        # 4. 今日任务提醒
        if tasks_today > 0 and tasks_done_today < tasks_today:
            remaining = tasks_today - tasks_done_today
            findings.append(f"今日还有 {remaining} 个任务待完成")
            tasks.append({"type": "daily_reminder",
                          "description": f"完成今日剩余 {remaining} 个任务",
                          "difficulty": "easy"})

        # 确定风险等级
        risk = RiskLevel.LOW
        if streak_days == 0 and (completion_rate or 0) < 0.3:
            risk = RiskLevel.MODERATE  # 可能有脱落风险

        result = AgentResult(
            agent_domain="habit_tracker",
            confidence=0.75 if findings else 0.5,
            risk_level=risk,
            findings=findings,
            recommendations=recommendations,
            tasks=tasks,
            metadata={
                "streak_days": streak_days,
                "completion_rate": completion_rate,
                "trend": recent_trend,
            },
        )

        return self._enhance_with_llm(result, inp)

    def _load_task_stats(self, user_id: int, context: dict) -> dict:
        """
        加载任务统计 — 优先从 context 读取, 否则从 DB 查询

        兼容两种调用方式:
          1. 已有统计 (如 API 层预计算后传入 context)
          2. 无统计 (Agent 直接被调用, 自行查 DB)

        查询的数据源: MicroActionTask 表
        字段对齐: micro_action_service.py 的 MicroActionTask 模型
          - scheduled_date: str (YYYY-MM-DD)
          - status: "pending" / "completed" / "skipped" / "expired"
          - source: "coach_assigned" / "ai_recommended" / "user_selected" / "intervention_plan" / "system"
          - domain: "nutrition" / "exercise" / "sleep" / ...
        """
        # 快速路径: context 已有数据
        if context.get("task_completion_rate") is not None:
            return {
                "streak_days": context.get("streak_days", 0),
                "completion_rate": context["task_completion_rate"],
                "tasks_today": context.get("tasks_assigned_today", 0),
                "tasks_done_today": context.get("tasks_completed_today", 0),
                "trend": context.get("completion_trend", "stable"),
            }

        # DB 查询路径
        try:
            from datetime import date, timedelta
            from sqlalchemy import func
            from core.models import MicroActionTask
            from core.database import SessionLocal

            db = SessionLocal()
            try:
                today_str = date.today().isoformat()

                # 今日任务
                today_tasks = (
                    db.query(MicroActionTask)
                    .filter(
                        MicroActionTask.user_id == user_id,
                        MicroActionTask.scheduled_date == today_str,
                    )
                    .all()
                )
                tasks_today = len(today_tasks)
                tasks_done_today = sum(1 for t in today_tasks if t.status == "completed")

                # 近7天完成率
                seven_days_ago = (date.today() - timedelta(days=7)).isoformat()
                recent_total = (
                    db.query(func.count(MicroActionTask.id))
                    .filter(
                        MicroActionTask.user_id == user_id,
                        MicroActionTask.scheduled_date >= seven_days_ago,
                        MicroActionTask.status.notin_(["expired"]),
                    )
                    .scalar() or 0
                )
                recent_completed = (
                    db.query(func.count(MicroActionTask.id))
                    .filter(
                        MicroActionTask.user_id == user_id,
                        MicroActionTask.scheduled_date >= seven_days_ago,
                        MicroActionTask.status == "completed",
                    )
                    .scalar() or 0
                )
                completion_rate = (recent_completed / recent_total) if recent_total > 0 else None

                # 趋势: 比较前7天 vs 前14-7天
                fourteen_days_ago = (date.today() - timedelta(days=14)).isoformat()
                prev_total = (
                    db.query(func.count(MicroActionTask.id))
                    .filter(
                        MicroActionTask.user_id == user_id,
                        MicroActionTask.scheduled_date >= fourteen_days_ago,
                        MicroActionTask.scheduled_date < seven_days_ago,
                        MicroActionTask.status.notin_(["expired"]),
                    )
                    .scalar() or 0
                )
                prev_completed = (
                    db.query(func.count(MicroActionTask.id))
                    .filter(
                        MicroActionTask.user_id == user_id,
                        MicroActionTask.scheduled_date >= fourteen_days_ago,
                        MicroActionTask.scheduled_date < seven_days_ago,
                        MicroActionTask.status == "completed",
                    )
                    .scalar() or 0
                )
                prev_rate = (prev_completed / prev_total) if prev_total > 0 else 0
                current_rate = completion_rate or 0

                if current_rate > prev_rate + 0.1:
                    trend = "improving"
                elif current_rate < prev_rate - 0.1:
                    trend = "declining"
                else:
                    trend = "stable"

                # 连续天数: 从今天往前数, 每天都有 completed 的连续天数
                streak_days = 0
                check_date = date.today()
                for _ in range(365):
                    day_str = check_date.isoformat()
                    has_completed = (
                        db.query(func.count(MicroActionTask.id))
                        .filter(
                            MicroActionTask.user_id == user_id,
                            MicroActionTask.scheduled_date == day_str,
                            MicroActionTask.status == "completed",
                        )
                        .scalar() or 0
                    )
                    if has_completed > 0:
                        streak_days += 1
                        check_date -= timedelta(days=1)
                    else:
                        break

                return {
                    "streak_days": streak_days,
                    "completion_rate": completion_rate,
                    "tasks_today": tasks_today,
                    "tasks_done_today": tasks_done_today,
                    "trend": trend,
                }
            finally:
                db.close()

        except Exception as e:
            logger.warning("HabitTracker DB 查询失败 (降级到 context): %s", e)
            return {
                "streak_days": context.get("streak_days", 0),
                "completion_rate": None,
                "tasks_today": 0,
                "tasks_done_today": 0,
                "trend": "stable",
            }

    def _check_milestone(self, days: int) -> str | None:
        """检查是否达到里程碑"""
        return STREAK_MILESTONES.get(days)

    def _next_milestone(self, days: int) -> int:
        """找到下一个里程碑天数"""
        for milestone in sorted(STREAK_MILESTONES.keys()):
            if milestone > days:
                return milestone
        return days + 30  # 超过365天后每30天一个里程碑
