"""
Agent 启动注册 — 应用启动时执行

调用方式 (在 api/main.py startup):
    from core.agents.startup import create_registry
    registry = create_registry(db_session=db)
    # registry 已冻结, 传入 MasterAgent

注册顺序:
  1. Safety: CrisisAgent (priority=0, 最先注册)
  2. Specialist: 9 个专科 Agent
  3. Integrative: BehaviorRx, Weight, Cardiac, TrustGuide
  4. User: HealthAssistant, HabitTracker, OnboardingGuide (Phase 3 新增)
  5. Expert: Vision, XZB, BehaviorRx Experts
"""
from __future__ import annotations
import logging
from typing import Any, Optional

from .registry import AgentRegistry
from .agent_meta import AgentMeta, AgentTier

logger = logging.getLogger(__name__)


def register_all_agents(registry: AgentRegistry, db_session=None) -> None:
    """
    注册全部 Agent (不冻结, 允许外部追加)

    分层注册, 每层独立 try/except, 某层失败不阻断其他层。
    唯一硬约束: CrisisAgent 必须成功注册。
    """
    _register_safety(registry)
    _register_specialists(registry)
    _register_integrative(registry)
    _register_user_agents(registry)
    _register_experts(registry)
    _register_behavior_rx_experts(registry)
    _register_from_db_templates(registry, db_session)

    logger.info("Agent 注册完成: %d 个", registry.count())


def create_registry(db_session=None) -> AgentRegistry:
    """
    创建并冻结 AgentRegistry — 一站式入口

    Returns:
        已冻结的 AgentRegistry 实例
    """
    registry = AgentRegistry()
    register_all_agents(registry, db_session=db_session)
    registry.freeze()
    return registry


# ═══════════════════════════════════════════════
# 第一层: Safety
# ═══════════════════════════════════════════════

def _register_safety(registry: AgentRegistry) -> None:
    from .specialist_agents import CrisisAgent

    registry.register(
        CrisisAgent(),
        AgentMeta(
            domain="crisis",
            display_name="危机干预",
            tier=AgentTier.SAFETY,
            priority=0,
            keywords=("自杀", "自残", "不想活", "结束生命", "活着没意思",
                      "去死", "跳楼", "割腕", "安眠药", "遗书"),
            base_weight=1.0,
            enable_llm=False,
            description="危机检测与紧急响应, 优先级最高, 不走 LLM",
        ),
    )


# ═══════════════════════════════════════════════
# 第二层: Specialist (9 个专科)
# ═══════════════════════════════════════════════

def _register_specialists(registry: AgentRegistry) -> None:
    try:
        from .specialist_agents import (
            SleepAgent, GlucoseAgent, StressAgent,
            NutritionAgent, ExerciseAgent, MentalHealthAgent,
            TCMWellnessAgent, MotivationAgent,
        )

        specs = [
            (SleepAgent(), AgentMeta(
                domain="sleep", display_name="睡眠专家",
                tier=AgentTier.SPECIALIST, priority=2,
                keywords=("睡眠", "失眠", "早醒", "熬夜", "睡不着", "嗜睡", "打鼾", "午睡"),
                data_fields=("sleep",), base_weight=0.85,
            )),
            (GlucoseAgent(), AgentMeta(
                domain="glucose", display_name="血糖管理",
                tier=AgentTier.SPECIALIST, priority=1,
                keywords=("血糖", "糖尿病", "胰岛素", "低血糖", "高血糖", "糖化", "控糖"),
                data_fields=("cgm",), base_weight=0.9,
            )),
            (StressAgent(), AgentMeta(
                domain="stress", display_name="压力管理",
                tier=AgentTier.SPECIALIST, priority=2,
                keywords=("压力", "焦虑", "紧张", "烦躁", "崩溃", "喘不过气"),
                data_fields=("hrv",), base_weight=0.85,
            )),
            (NutritionAgent(), AgentMeta(
                domain="nutrition", display_name="营养指导",
                tier=AgentTier.SPECIALIST, priority=3,
                keywords=("饮食", "营养", "减肥", "热量", "碳水", "蛋白质",
                          "吃什么", "食谱", "代餐", "节食"),
                base_weight=0.8,
            )),
            (ExerciseAgent(), AgentMeta(
                domain="exercise", display_name="运动指导",
                tier=AgentTier.SPECIALIST, priority=3,
                keywords=("运动", "健身", "步数", "跑步", "散步", "力量训练", "瑜伽"),
                data_fields=("activity",), base_weight=0.8,
            )),
            (MentalHealthAgent(), AgentMeta(
                domain="mental", display_name="心理咨询",
                tier=AgentTier.SPECIALIST, priority=2,
                keywords=("情绪", "抑郁", "心情", "难过", "伤心", "郁闷", "无助"),
                base_weight=0.85,
            )),
            (TCMWellnessAgent(), AgentMeta(
                domain="tcm", display_name="中医养生",
                tier=AgentTier.SPECIALIST, priority=4,
                keywords=("中医", "体质", "穴位", "气血", "经络", "养生", "上火", "湿气"),
                base_weight=0.75,
            )),
            (MotivationAgent(), AgentMeta(
                domain="motivation", display_name="动机管理",
                tier=AgentTier.SPECIALIST, priority=3,
                keywords=("动力", "坚持", "放弃", "没意义", "为什么", "值不值"),
                base_weight=0.8,
            )),
        ]
        registry.register_batch(specs)
    except Exception as e:
        logger.error("专科 Agent 注册失败: %s", e, exc_info=True)
        raise


# ═══════════════════════════════════════════════
# 第三层: Integrative (整合型)
# ═══════════════════════════════════════════════

def _register_integrative(registry: AgentRegistry) -> None:
    try:
        from .integrative_agents import BehaviorRxAgent, WeightAgent, CardiacRehabAgent

        integ = [
            (BehaviorRxAgent(), AgentMeta(
                domain="behavior_rx", display_name="行为处方师",
                tier=AgentTier.INTEGRATIVE, priority=2,
                keywords=("行为处方", "习惯", "戒烟", "依从性", "打卡", "任务"),
                base_weight=0.9,
            )),
            (WeightAgent(), AgentMeta(
                domain="weight", display_name="体重管理师",
                tier=AgentTier.INTEGRATIVE, priority=2,
                keywords=("体重", "减重", "BMI", "脂肪", "腰围", "减肥"),
                base_weight=0.85,
            )),
            (CardiacRehabAgent(), AgentMeta(
                domain="cardiac_rehab", display_name="心脏康复师",
                tier=AgentTier.INTEGRATIVE, priority=1,
                keywords=("心脏", "心血管", "冠心病", "康复", "心梗", "支架"),
                base_weight=0.85,
            )),
        ]
        registry.register_batch(integ)
    except Exception as e:
        logger.error("整合型 Agent 注册失败: %s", e, exc_info=True)

    # TrustGuide (可选)
    try:
        from .trust_guide_agent import TrustGuideAgent
        registry.register(
            TrustGuideAgent(),
            AgentMeta(
                domain="trust_guide", display_name="信任引导",
                tier=AgentTier.INTEGRATIVE, priority=3,
                keywords=("信任", "首次", "新用户", "了解"),
                base_weight=0.7,
            ),
        )
    except ImportError:
        logger.info("TrustGuideAgent 不可用, 跳过")


# ═══════════════════════════════════════════════
# 第四层: User (用户层 — Phase 3 新增)
# ═══════════════════════════════════════════════

def _register_user_agents(registry: AgentRegistry) -> None:
    """注册 3 个用户层 Agent (Phase 3 激活)"""

    # 1. HealthAssistant — 健康知识科普
    try:
        from .user_agents.health_assistant import HealthAssistantAgent
        registry.register(
            HealthAssistantAgent(),
            AgentMeta(
                domain="health_assistant", display_name="健康知识助手",
                tier=AgentTier.USER, priority=4,
                keywords=("科普", "什么是", "怎么回事", "为什么会", "健康知识",
                          "原理", "原因", "怎么预防", "注意什么"),
                base_weight=0.65,
                enable_llm=True,
                description="健康知识科普 + RAG 知识库问答, 主动推送科普内容",
            ),
        )
    except ImportError:
        logger.info("HealthAssistantAgent 不可用, 跳过")

    # 2. HabitTracker — 习惯追踪
    try:
        from .user_agents.habit_tracker import HabitTrackerAgent
        registry.register(
            HabitTrackerAgent(),
            AgentMeta(
                domain="habit_tracker", display_name="习惯追踪",
                tier=AgentTier.USER, priority=4,
                keywords=("打卡", "习惯", "坚持了", "连续", "记录", "追踪",
                          "完成率", "趋势", "统计", "进步"),
                data_fields=("tasks",),
                base_weight=0.6,
                enable_llm=True,
                description="打卡趋势分析 + 智能反馈 + 成就激励",
            ),
        )
    except ImportError:
        logger.info("HabitTrackerAgent 不可用, 跳过")

    # 3. OnboardingGuide — 新手引导
    try:
        from .user_agents.onboarding_guide import OnboardingGuideAgent
        registry.register(
            OnboardingGuideAgent(),
            AgentMeta(
                domain="onboarding_guide", display_name="新手引导",
                tier=AgentTier.USER, priority=3,
                keywords=("怎么用", "第一次", "新手", "不会", "教我", "入门",
                          "开始", "指引", "帮助"),
                base_weight=0.7,
                enable_llm=True,
                description="新用户引导流程: 评估→推荐→首个任务",
                dependencies=("trust_guide",),
            ),
        )
    except ImportError:
        logger.info("OnboardingGuideAgent 不可用, 跳过")


# ═══════════════════════════════════════════════
# 第五层: Expert (动态专家)
# ═══════════════════════════════════════════════

def _register_experts(registry: AgentRegistry) -> None:
    # Vision Agent
    try:
        from .vision_agent import VisionGuideAgent
        registry.register(
            VisionGuideAgent(),
            AgentMeta(
                domain="vision", display_name="视力健康",
                tier=AgentTier.EXPERT, priority=3,
                keywords=("视力", "近视", "眼睛", "屏幕", "用眼", "护眼"),
                base_weight=0.8,
            ),
        )
    except ImportError:
        logger.info("VisionGuideAgent 不可用, 跳过")

    # XZB Expert Agent
    try:
        from .xzb_expert_agent import XZBExpertAgent
        registry.register(
            XZBExpertAgent(),
            AgentMeta(
                domain="xzb_expert", display_name="行诊智伴专家",
                tier=AgentTier.EXPERT, priority=1,
                keywords=(),  # XZB 路由由 tenant_ctx 控制, 不靠关键词
                base_weight=0.95,
                description="行诊智伴: 医疗专家 AI 分身, 由租户上下文激活",
            ),
        )
    except ImportError:
        logger.info("XZBExpertAgent 不可用, 跳过")


def _register_behavior_rx_experts(registry: AgentRegistry) -> None:
    """注册 behavior_rx 的 4 个专家 Agent (原猴子补丁注入)"""
    try:
        from behavior_rx.agents.behavior_coach_agent import BehaviorCoachExpertAgent
        from behavior_rx.agents.metabolic_expert_agent import MetabolicExpertAgent
        from behavior_rx.agents.cardiac_expert_agent import CardiacExpertAgent
        from behavior_rx.agents.adherence_expert_agent import AdherenceExpertAgent

        experts = [
            (BehaviorCoachExpertAgent(), AgentMeta(
                domain="brx_behavior_coach", display_name="行为教练专家",
                tier=AgentTier.EXPERT, priority=2,
                base_weight=0.85,
            )),
            (MetabolicExpertAgent(), AgentMeta(
                domain="brx_metabolic", display_name="代谢专家",
                tier=AgentTier.EXPERT, priority=2,
                base_weight=0.85,
            )),
            (CardiacExpertAgent(), AgentMeta(
                domain="brx_cardiac", display_name="心脏专家",
                tier=AgentTier.EXPERT, priority=2,
                base_weight=0.85,
            )),
            (AdherenceExpertAgent(), AgentMeta(
                domain="brx_adherence", display_name="依从性专家",
                tier=AgentTier.EXPERT, priority=3,
                base_weight=0.8,
            )),
        ]
        registry.register_batch(experts)
    except ImportError:
        logger.info("behavior_rx 专家 Agent 不可用, 跳过 (非阻断)")


# ═══════════════════════════════════════════════
# DB 模板动态注册
# ═══════════════════════════════════════════════

def _register_from_db_templates(registry: AgentRegistry, db_session) -> None:
    """从数据库模板动态注册 Agent (增量叠加, 不覆盖硬编码)"""
    if not db_session:
        return
    try:
        from core.agent_template_service import build_agents_from_templates
        agents_from_db = build_agents_from_templates(db_session)
        if not agents_from_db:
            return

        for domain, agent in agents_from_db.items():
            if registry.has(domain):
                logger.debug("DB 模板 '%s' 已被硬编码注册, 跳过", domain)
                continue
            registry.register(
                agent,
                AgentMeta(
                    domain=domain,
                    display_name=getattr(agent, "display_name", domain),
                    tier=AgentTier.EXPERT,
                    priority=getattr(agent, "priority", 5),
                    base_weight=getattr(agent, "base_weight", 0.7),
                    description=f"DB 模板动态 Agent: {domain}",
                ),
            )
        logger.info("DB 模板注册 %d 个新 Agent", len(agents_from_db))
    except Exception as e:
        logger.warning("DB 模板 Agent 注册失败 (non-blocking): %s", e)
