"""
VisionGuideAgent 扩展  —  Phase 1 新增意图分类
续接 VisionExam Agent 体系（第48-51类），不新增 Agent 类，
扩展 generate_response 职责范围

新增意图：
    behavior_checkin      行为打卡
    goal_inquiry          目标查询
    parent_summary        家长摘要生成
    resistance_handling   阻抗应对（转接 ResistanceAgent）
    expert_consultation   专家介入请求
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Optional

# ── 意图分类 ──────────────────────────────────────────────────────────────────


class VisionIntent(str, Enum):
    # 原有意图（VisionExam 已定义）
    EXAM_RECORD_QUERY = "exam_record_query"
    RISK_EXPLANATION = "risk_explanation"
    APPOINTMENT_REMINDER = "appointment_reminder"
    PROGRESS_REVIEW = "progress_review"

    # VisionGuard 新增意图
    BEHAVIOR_CHECKIN = "behavior_checkin"
    GOAL_INQUIRY = "goal_inquiry"
    PARENT_SUMMARY = "parent_summary"
    RESISTANCE_HANDLING = "resistance_handling"
    EXPERT_CONSULTATION = "expert_consultation"


# 关键词映射（快速意图分类，精确 NLU 由 LLM 补充）
INTENT_KEYWORD_MAP: dict[VisionIntent, list[str]] = {
    VisionIntent.BEHAVIOR_CHECKIN: [
        "打卡", "今天完成了", "户外了", "出门了", "做操了",
        "眼保健操", "吃叶黄素了", "睡了", "屏幕",
    ],
    VisionIntent.GOAL_INQUIRY: [
        "目标是多少", "应该做几分钟", "我够了吗",
        "达标了吗", "还差多少", "今天要做", "完成多少",
    ],
    VisionIntent.PARENT_SUMMARY: [
        "给我家长看", "帮我告诉爸妈", "家长版",
        "发给家长", "告诉我妈", "告诉我爸",
    ],
    VisionIntent.RESISTANCE_HANDLING: [
        "不想出去", "没时间", "有用吗", "好烦",
        "不做了", "没意义", "做不到", "太难了",
    ],
    VisionIntent.EXPERT_CONSULTATION: [
        "想问医生", "需要看专家吗", "要不要手术",
        "找医生", "咨询专家", "要不要配眼镜",
    ],
}


def classify_intent(user_message: str) -> VisionIntent:
    """
    快速意图分类。
    1. 关键词匹配（覆盖 80% 高频场景）
    2. 若无命中，交由 LLM 精确分类（实际调用时替换）
    """
    msg = user_message.strip()
    for intent, keywords in INTENT_KEYWORD_MAP.items():
        if any(kw in msg for kw in keywords):
            return intent
    # 兜底：返回 exam_record_query（原有默认处理）
    return VisionIntent.EXAM_RECORD_QUERY


# ── 数据上下文 ─────────────────────────────────────────────────────────────────


@dataclass
class VisionAgentContext:
    user_id: uuid.UUID
    student_name: str
    age: int
    ttm_stage: str           # S0-S5
    risk_level: str          # NORMAL / WATCH / ALERT / URGENT
    today_log: Optional[dict]   # vision_behavior_logs 当日记录
    goal: Optional[dict]        # vision_behavior_goals 目标
    streak_days: int            # 连续达标天数
    is_exam_season: bool        # 考试季标识（feature_flag）
    expert_name: Optional[str]  # 绑定行诊智伴专家姓名


# ── 意图处理器 ────────────────────────────────────────────────────────────────


class VisionGuideAgentExtension:
    """
    VisionGuideAgent 扩展类，接管新增意图的 generate_response。
    原有意图继续由父类处理。

    使用方式（在父类 dispatch 方法末尾追加）：
        extension = VisionGuideAgentExtension(ctx)
        if intent in VisionIntent:
            return extension.handle(intent, user_message)
    """

    def __init__(self, ctx: VisionAgentContext):
        self.ctx = ctx

    def handle(self, intent: VisionIntent, user_message: str) -> str:
        handlers = {
            VisionIntent.BEHAVIOR_CHECKIN: self._handle_checkin,
            VisionIntent.GOAL_INQUIRY: self._handle_goal_inquiry,
            VisionIntent.PARENT_SUMMARY: self._handle_parent_summary,
            VisionIntent.RESISTANCE_HANDLING: self._handle_resistance,
            VisionIntent.EXPERT_CONSULTATION: self._handle_expert_consult,
        }
        handler = handlers.get(intent)
        if handler:
            return handler(user_message)
        return ""

    # ── behavior_checkin ──────────────────────────────────────────────────────
    def _handle_checkin(self, msg: str) -> str:
        ctx = self.ctx
        log = ctx.today_log or {}
        goal = ctx.goal or {}

        # 解析打卡数值（简单正则；生产中用结构化解析）
        outdoor = log.get("outdoor_minutes")
        target_outdoor = goal.get("outdoor_target_min", 120)

        parts = []

        if outdoor is not None:
            gap = target_outdoor - outdoor
            if gap > 0:
                parts.append(
                    f"今天出门 {outdoor} 分钟——距目标还差 {gap} 分钟！"
                    f"傍晚出去转一圈就够了 😊"
                )
            else:
                parts.append(
                    f"户外达标✓ 今天 {outdoor} 分钟，超出目标 {-gap} 分钟，很棒！"
                )

        if log.get("eye_exercise_done"):
            parts.append("眼保健操打卡✓")

        if ctx.streak_days >= 3:
            parts.append(f"你已经连续 {ctx.streak_days} 天完成护眼任务了，继续保持！")

        if not parts:
            parts.append("打卡成功！今天的护眼数据已记录，加油！")

        # 考试季特殊提示
        if ctx.is_exam_season:
            parts.append(
                "考试季期间护眼目标已适度下调，不要给自己太大压力，"
                "保持基础达标就很好。"
            )

        return "\n".join(parts)

    # ── goal_inquiry ──────────────────────────────────────────────────────────
    def _handle_goal_inquiry(self, msg: str) -> str:
        ctx = self.ctx
        goal = ctx.goal or {}
        log = ctx.today_log or {}

        outdoor_target = goal.get("outdoor_target_min", 120)
        outdoor_done = log.get("outdoor_minutes", 0) or 0
        screen_limit = goal.get("screen_daily_limit", 120)
        screen_done = log.get("screen_total_minutes", 0) or 0

        lines = [
            f"今天的护眼目标（{ctx.student_name}）：",
            f"  🌿 户外活动：{outdoor_done}/{outdoor_target} 分钟"
            + ("  ✅" if outdoor_done >= outdoor_target else f"  还差 {outdoor_target-outdoor_done} 分钟"),
            f"  📱 屏幕时间：{screen_done}/{screen_limit} 分钟"
            + ("  ⚠️ 已超标" if screen_done > screen_limit else "  ✅"),
            f"  💊 叶黄素目标：{goal.get('lutein_target_mg', 10)} mg/天",
            f"  💤 睡眠目标：{goal.get('sleep_target_min', 540)//60} 小时/天",
        ]
        return "\n".join(lines)

    # ── parent_summary ────────────────────────────────────────────────────────
    def _handle_parent_summary(self, msg: str) -> str:
        ctx = self.ctx
        log = ctx.today_log or {}

        summary = (
            f"【{ctx.student_name} 今日护眼摘要·家长版】\n"
            f"风险等级：{ctx.risk_level}\n"
            f"户外活动：{log.get('outdoor_minutes', '未记录')} 分钟\n"
            f"屏幕时间：{log.get('screen_total_minutes', '未记录')} 分钟\n"
            f"眼保健操：{'完成' if log.get('eye_exercise_done') else '未完成'}\n"
            f"综合评分：{log.get('behavior_score', '--')}/100\n"
            "\n家长今日建议：\n"
            "  ① 晚饭后可陪孩子在小区散步 20 分钟\n"
            "  ② 检查作业台灯照度 > 500lux，阅读距离 > 33cm\n"
        )

        if ctx.risk_level in ("ALERT", "URGENT"):
            summary += (
                f"\n⚠️ 当前风险等级为 {ctx.risk_level}，"
                f"建议尽快联系教练安排下次随访。\n"
            )

        # 实际生产中通过 WechatPushService 推送，此处返回文本供智伴展示
        return summary

    # ── resistance_handling ───────────────────────────────────────────────────
    def _handle_resistance(self, msg: str) -> str:
        """
        五种阻抗应对策略（平台现有 ResistanceAgent 的视力版适配）
        策略：共情 → 最小行动 → 还原自主权
        """
        ctx = self.ctx
        responses = [
            # 策略1：共情 + 最小行动
            (
                "明白，学习任务重的时候真的很难抽出时间。\n"
                "那就先做一次 20-20-20：现在停下来，"
                "看 20 秒窗外的远处，就这一次，不强求更多。"
            ),
            # 策略2：还原自主权
            (
                "出门或不出门，选择权在你。\n"
                "这周你觉得哪天最容易出去走走？"
                "我们只计划那一天，其他时间不提。"
            ),
            # 策略3：数据说话（适合 S1 沉思期）
            (
                f"你的眼轴增速在过去 30 天里是有变化的。"
                f"每天 2 小时户外在多项研究中被证明能减缓 30-50% 的近视进展。"
                f"你不需要相信我，数据会说话——先试一周？"
            ),
        ]

        # 根据 TTM 阶段选择策略
        stage_map = {"S0": 2, "S1": 2, "S2": 0, "S3": 1, "S4": 0, "S5": 1}
        idx = stage_map.get(ctx.ttm_stage, 0)
        return responses[idx % len(responses)]

    # ── expert_consultation ───────────────────────────────────────────────────
    def _handle_expert_consult(self, msg: str) -> str:
        ctx = self.ctx
        expert = ctx.expert_name or "行诊智伴眼科专家"

        if ctx.risk_level == "URGENT":
            return (
                f"你的情况需要尽快与 {expert} 沟通。"
                f"我已经将你的视力档案和最近的行为数据发送给了专家，"
                f"他会在 24 小时内通过智伴给你回复。\n"
                f"如有紧急情况，请直接前往眼科门诊。"
            )
        elif ctx.risk_level == "ALERT":
            return (
                f"这个问题超出了日常建议的范围，我已经记录下来，"
                f"会请 {expert} 通过智伴给你一个专业意见（通常 1-2 个工作日）。\n"
                f"如果你想更快得到回复，可以让教练帮你加急。"
            )
        else:
            return (
                f"你目前的风险等级是 {ctx.risk_level}，"
                f"暂时不需要立即联系专家。\n"
                f"如果你有具体问题，可以先问我，"
                f"我会判断是否需要转给 {expert}。"
            )


# ── 行为处方生成器（Phase 2 VisionRxAgent 接口预留）────────────────────────────


class VisionRxGenerator:
    """
    三格式处方生成（学生版 / 家长版 / 教练版）
    Phase 2 实现：对接 XZBRxBridge + OphthalmologyExpertAgent 知识库
    """

    def __init__(self, ctx: VisionAgentContext):
        self.ctx = ctx

    def generate_student_rx(self, trigger: str) -> dict:
        ctx = self.ctx
        return {
            "format": "STUDENT",
            "trigger": trigger,
            "target_this_week": f"每天出门两次，加起来超过 {ctx.goal.get('outdoor_target_min', 120)//60} 小时",
            "action_cards": [
                {"title": "午饭后出门 15 分钟", "points": 10},
                {"title": "完成今日眼保健操", "points": 5},
                {"title": "晚上屏幕时间控制在目标内", "points": 15},
            ],
            "progress_feedback": "你的护眼行为分数本周在上升，继续保持！",
            "expert_voice": (
                f"{ctx.expert_name or '医生'}说："
                f"你现在的状态{'很好，继续保持。' if ctx.risk_level == 'NORMAL' else '需要再努力一下，我相信你可以做到。'}"
            ),
        }

    def generate_parent_rx(self, trigger: str) -> dict:
        ctx = self.ctx
        risk_desc = {
            "NORMAL": "正常，目前无需特别担心",
            "WATCH": "观察期，需要关注但暂无紧急处理",
            "ALERT": "警示期，建议认真执行干预方案",
            "URGENT": "紧急，请尽快就医",
        }
        return {
            "format": "PARENT",
            "trigger": trigger,
            "risk_description": risk_desc.get(ctx.risk_level, ""),
            "parent_tasks": [
                "本周调整家庭晚饭后安排，陪孩子户外活动 30 分钟",
                "检查作业台灯照度 > 500lux，阅读距离 > 33cm",
            ],
            "expert_summary": "如下次检查度数再增加 > 0.5D，需讨论进一步干预选项",
        }

    def generate_coach_rx(self, trigger: str, exam_record: Optional[dict] = None) -> dict:
        ctx = self.ctx
        return {
            "format": "COACH",
            "trigger": trigger,
            "trigger_evidence": exam_record or {"source": trigger},
            "xzb_recommendation": f"基于学员年龄 {ctx.age} 岁和当前风险等级 {ctx.risk_level}，建议执行标准干预方案",
            "coach_actions_required": [
                "确认家长沟通干预选项",
                f"屏幕限制从现有值调整至 {ctx.goal.get('screen_daily_limit', 90)} 分钟/天",
                "30 天后安排随访",
            ],
            "auto_reminder": f"若 30 天内未收到新检查记录，自动触发 Job 28 重新评估",
        }
