"""
OnboardingGuideAgent — 新手引导

功能:
  - 新用户首次进入 → 欢迎 + 平台介绍
  - 引导完成首次评估 (阶段判定 + 体质辨识)
  - 推荐首个行为处方
  - 设置个人目标

路由触发:
  关键词: 怎么用/第一次/新手/不会/教我/入门/开始/指引/帮助
  条件触发: 用户 growth_level == "G0" 且无历史对话

与 TrustGuideAgent 的分工:
  - TrustGuide: 评估信任度, 决定是否下发干预
  - Onboarding: 编排引导流程, 推荐评估和首个任务

来源: 合并 assistant_agents/onboarding_guide.py 设计
"""
from __future__ import annotations
import logging
from typing import Any, Dict

from ..base import BaseAgent, AgentDomain, AgentInput, AgentResult, RiskLevel

logger = logging.getLogger(__name__)

# 引导步骤定义
ONBOARDING_STEPS = [
    {
        "step": 1,
        "name": "welcome",
        "description": "欢迎 + 平台介绍",
        "trigger": "首次登录或请求帮助",
    },
    {
        "step": 2,
        "name": "initial_assessment",
        "description": "快速评估 (12题最小启动)",
        "trigger": "欢迎完成后",
    },
    {
        "step": 3,
        "name": "profile_setup",
        "description": "个人目标设定",
        "trigger": "评估完成后",
    },
    {
        "step": 4,
        "name": "first_task",
        "description": "领取首个任务",
        "trigger": "目标设定后",
    },
]

# 阶段化欢迎语
WELCOME_MESSAGES = {
    "default": (
        "欢迎来到行健平台！我是你的健康伙伴。\n\n"
        "这里的一切都围绕「你」展开 — 不是告诉你必须做什么，"
        "而是帮你发现适合自己的健康方式。\n\n"
        "我们先花2分钟做个快速了解，帮我更好地陪伴你，好吗？"
    ),
    "returning": (
        "欢迎回来！看起来你之前的引导没有完成。\n\n"
        "没关系，我们可以从上次的地方继续，"
        "也可以重新开始。你想怎么做？"
    ),
}


class OnboardingGuideAgent(BaseAgent):
    """
    新手引导 Agent — 用户层

    核心职责:
      1. 检测用户是否为新手 (G0 + 无完成评估)
      2. 根据引导阶段返回对应内容
      3. 推荐下一步行动
    """
    domain = AgentDomain.MOTIVATION  # 归属动机领域
    display_name = "新手引导"
    keywords = ["怎么用", "第一次", "新手", "不会", "教我", "入门",
                "开始", "指引", "帮助"]
    priority = 3
    base_weight = 0.7
    enable_llm = True
    evidence_tier = "T3"

    def process(self, inp: AgentInput) -> AgentResult:
        profile = inp.profile
        context = inp.context
        message = inp.message

        growth_level = profile.get("growth_level", "G0")
        has_assessment = profile.get("has_initial_assessment", False)
        onboarding_step = context.get("onboarding_step", 0)

        findings = []
        recommendations = []
        tasks = []

        # 判断引导阶段
        if growth_level == "G0" and not has_assessment:
            # 全新用户 → 从 Step 1 开始
            current_step = max(onboarding_step, 1)
        elif growth_level == "G0" and has_assessment:
            # 已评估但未完成引导
            current_step = 3
        else:
            # 非新手但请求帮助
            current_step = 0

        if current_step == 0:
            # 非新手的帮助请求
            findings.append("用户非新手, 提供使用指南")
            recommendations.append(self._generate_help_guide(profile))
            return AgentResult(
                agent_domain="onboarding_guide",
                confidence=0.6, risk_level=RiskLevel.LOW,
                findings=findings, recommendations=recommendations,
                metadata={"onboarding_phase": "help", "is_new_user": False},
            )

        elif current_step == 1:
            # Step 1: 欢迎
            findings.append("新用户首次进入, 启动引导流程")
            recommendations.append(WELCOME_MESSAGES["default"])
            tasks.append({
                "type": "onboarding_assessment",
                "description": "完成2分钟快速评估",
                "difficulty": "minimal",
                "metadata": {"step": "initial_assessment", "estimated_time": "2min"},
            })

        elif current_step == 2:
            # Step 2: 引导评估
            findings.append("引导阶段: 快速评估")
            recommendations.append(
                "让我们快速了解你的现状。\n"
                "只需回答12个简单问题，不需要翻查任何资料。\n"
                "你的回答没有对错之分，真实感受最重要。"
            )
            tasks.append({
                "type": "start_minimal_diagnostic",
                "description": "开始12题最小启动评估",
                "difficulty": "minimal",
                "metadata": {"assessment_type": "minimal_12"},
            })

        elif current_step == 3:
            # Step 3: 目标设定
            findings.append("评估已完成, 引导目标设定")
            stage = profile.get("current_stage", "S0")
            recommendations.append(self._stage_goal_suggestion(stage))
            tasks.append({
                "type": "set_initial_goal",
                "description": "设定你的第一个健康小目标",
                "difficulty": "easy",
                "metadata": {"suggested_stage": stage},
            })

        elif current_step >= 4:
            # Step 4: 首个任务
            findings.append("引导流程即将完成, 推荐首个任务")
            recommendations.append(
                "太好了！一切准备就绪。\n"
                "这是为你量身定制的第一个任务 — 很简单，试试看？"
            )
            tasks.append({
                "type": "first_micro_action",
                "description": "完成你的第一个微行动",
                "difficulty": "minimal",
                "metadata": {"onboarding_final": True},
            })

        result = AgentResult(
            agent_domain="onboarding_guide",
            confidence=0.8,
            risk_level=RiskLevel.LOW,
            findings=findings,
            recommendations=recommendations,
            tasks=tasks,
            metadata={
                "onboarding_phase": f"step_{current_step}",
                "is_new_user": growth_level == "G0",
                "next_step": min(current_step + 1, 4),
            },
        )

        return self._enhance_with_llm(result, inp)

    def _stage_goal_suggestion(self, stage: str) -> str:
        suggestions = {
            "S0": "目前不用想太多, 你的第一个目标就是: 每天记录一件和健康有关的事。",
            "S1": "你已经开始关注健康了！设一个小目标: 这周了解一个健康知识。",
            "S2": "你在考虑改变, 很好！目标建议: 这周尝试一个你感兴趣的健康习惯。",
            "S3": "你已经准备好了！目标: 本周完成3个微行动任务。",
        }
        return suggestions.get(stage, suggestions["S0"])

    def _generate_help_guide(self, profile: dict) -> str:
        stage = profile.get("current_stage", "S0")
        return (
            f"以下是你当前阶段({stage})的使用指南：\n\n"
            "• 聊天: 随时和我聊健康话题\n"
            "• 任务: 查看和完成每日微行动\n"
            "• 数据: 同步设备数据查看趋势\n"
            "• 评估: 定期做评估了解变化\n\n"
            "有什么具体想了解的吗？"
        )
