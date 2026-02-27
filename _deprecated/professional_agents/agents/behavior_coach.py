"""
行为教练Agent — 教练层核心 (上游前置)

职责:
  1. 基于用户TTM阶段+BPT-6画像生成行为处方
  2. 选择合适的干预策略（12模板×领域变体）
  3. 输出必须经教练审核后才能触达用户

对接:
  - BehaviorRxEngine.compute_rx() → 核心Rx计算
  - BPT6RxEngine → V4.0 6域×6阶段=36模板
  - core/stage_engine → TTM阶段判断
  - UnifiedLLMClient → LLM增强输出
"""
from __future__ import annotations
import logging
from typing import Any, Dict, Optional

from ..base import BaseProfessionalAgent

logger = logging.getLogger(__name__)


class Agent(BaseProfessionalAgent):
    """行为教练 — 教练层上游前置Agent"""

    @property
    def name(self) -> str:
        return "behavior_coach"

    @property
    def domain(self) -> str:
        return "behavior"

    # ── 依赖注入（延迟加载避免循环import）──

    def _get_rx_engine(self):
        try:
            from behavior_rx.behavior_rx_engine import BehaviorRxEngine
            return BehaviorRxEngine()
        except ImportError:
            logger.warning("BehaviorRxEngine不可用，降级为规则模式")
            return None

    def _get_bpt6_engine(self):
        try:
            from core.bpt6_rx_engine import BPT6RxEngine
            return BPT6RxEngine()
        except ImportError:
            logger.warning("BPT6RxEngine不可用")
            return None

    def _get_stage_engine(self):
        try:
            from core.stage_engine import get_stage_summary
            return get_stage_summary
        except ImportError:
            logger.warning("stage_engine不可用")
            return None

    def _get_llm_client(self):
        try:
            from core.llm_client import get_llm_client
            return get_llm_client()
        except ImportError:
            logger.warning("LLM client不可用")
            return None

    # ── 核心逻辑 ──

    async def run(self, message: str, **kwargs) -> Dict[str, Any]:
        """
        处理教练的输入，生成行为处方建议

        kwargs:
            user_id: str        — 目标用户ID
            user_profile: dict  — 用户画像（含TTM stage, BPT-6, agency_mode等）
            session_context: dict — 会话上下文
            db: AsyncSession    — 数据库会话
        """
        # 0. 安全检查
        if not await self.safety_check(message):
            return self._format_response(
                "检测到安全风险内容，已转介危机响应通道。",
                safety_intercepted=True,
                action="crisis_referral",
            )

        user_id = kwargs.get("user_id")
        user_profile = kwargs.get("user_profile", {})
        db = kwargs.get("db")

        # 1. 获取用户阶段信息
        stage_info = await self._get_user_stage(user_id, user_profile, db)

        # 2. 计算行为处方
        rx_result = await self._compute_behavior_rx(user_profile, stage_info)

        # 3. LLM增强：将结构化Rx转化为教练可读的建议
        enhanced = await self._enhance_with_coaching_language(
            message, rx_result, stage_info, user_profile
        )

        # 4. 组装响应
        return self._format_response(
            content=enhanced["coaching_text"],
            rx_data=rx_result,
            stage_info=stage_info,
            strategies=enhanced.get("strategies", []),
            review_required=True,
            confidence=enhanced.get("confidence", 0.7),
        )

    async def _get_user_stage(
        self, user_id: Optional[str], profile: dict, db=None
    ) -> dict:
        """获取用户TTM阶段信息"""
        # 优先从profile中取
        stage = profile.get("ttm_stage") or profile.get("current_stage", "S0")
        agency = profile.get("agency_mode", "unknown")

        # 尝试从stage_engine获取详细信息
        get_summary = self._get_stage_engine()
        if get_summary and user_id:
            try:
                summary = get_summary(user_id) if not callable(getattr(get_summary, '__await__', None)) else await get_summary(user_id)
                if summary:
                    return {
                        "stage": summary.get("stage", stage),
                        "stage_name": summary.get("stage_name", self._stage_name(stage)),
                        "readiness": summary.get("readiness", 0.5),
                        "agency_mode": agency,
                        "days_in_stage": summary.get("days_in_stage", 0),
                        "source": "stage_engine",
                    }
            except Exception as e:
                logger.warning(f"stage_engine调用失败: {e}")

        return {
            "stage": stage,
            "stage_name": self._stage_name(stage),
            "readiness": profile.get("readiness", 0.5),
            "agency_mode": agency,
            "days_in_stage": 0,
            "source": "profile_fallback",
        }

    async def _compute_behavior_rx(self, profile: dict, stage_info: dict) -> dict:
        """计算行为处方 — 优先BPT6，降级BehaviorRx，兜底规则"""

        # 策略1: BPT6RxEngine (V4.0, 6域×6阶段)
        bpt6 = self._get_bpt6_engine()
        if bpt6:
            try:
                bpt6_input = {
                    "ttm_stage": stage_info["stage"],
                    "bpt6_type": profile.get("bpt6_type") or profile.get("personality_type"),
                    "big_five": profile.get("big_five_scores", {}),
                    "agency_mode": stage_info.get("agency_mode"),
                    "capacity": profile.get("capacity", 0.5),
                }
                result = bpt6.compute(bpt6_input) if hasattr(bpt6, 'compute') else {}
                if result:
                    return {
                        "engine": "bpt6",
                        "strategies": result.get("strategies", []),
                        "communication_style": result.get("communication_style", "supportive"),
                        "intensity": result.get("intensity", "moderate"),
                        "template_id": result.get("template_id"),
                        "raw": result,
                    }
            except Exception as e:
                logger.warning(f"BPT6计算失败: {e}")

        # 策略2: BehaviorRxEngine (传统3维)
        rx_engine = self._get_rx_engine()
        if rx_engine:
            try:
                rx_input = {
                    "stage": stage_info["stage"],
                    "personality": profile.get("big_five_scores", {}),
                    "capacity": profile.get("capacity", 0.5),
                }
                result = rx_engine.compute_rx(rx_input)
                if result:
                    return {
                        "engine": "behavior_rx",
                        "strategies": result.get("strategies", []),
                        "communication_style": result.get("style", "supportive"),
                        "intensity": result.get("intensity", "moderate"),
                        "raw": result,
                    }
            except Exception as e:
                logger.warning(f"BehaviorRx计算失败: {e}")

        # 策略3: 规则兜底
        return self._rule_based_rx(stage_info)

    def _rule_based_rx(self, stage_info: dict) -> dict:
        """基于规则的Rx兜底策略"""
        stage = stage_info.get("stage", "S0")
        STAGE_STRATEGIES = {
            "S0": {"strategies": ["意识提升", "风险感知"], "style": "empathetic", "intensity": "minimal"},
            "S1": {"strategies": ["动机访谈", "自我效能评估"], "style": "exploratory", "intensity": "low"},
            "S2": {"strategies": ["目标设定", "行动计划", "资源匹配"], "style": "collaborative", "intensity": "moderate"},
            "S3": {"strategies": ["行为替代", "刺激控制", "社会支持"], "style": "directive", "intensity": "moderate"},
            "S4": {"strategies": ["自我监控", "复发预防", "奖励管理"], "style": "supportive", "intensity": "low"},
            "S5": {"strategies": ["身份巩固", "价值整合", "环境优化"], "style": "affirming", "intensity": "minimal"},
        }
        config = STAGE_STRATEGIES.get(stage, STAGE_STRATEGIES["S0"])
        return {
            "engine": "rule_fallback",
            "strategies": config["strategies"],
            "communication_style": config["style"],
            "intensity": config["intensity"],
            "raw": config,
        }

    async def _enhance_with_coaching_language(
        self, message: str, rx: dict, stage: dict, profile: dict
    ) -> dict:
        """用LLM将结构化Rx转化为教练语言"""
        llm = self._get_llm_client()
        if not llm:
            # LLM不可用时返回结构化文本
            strategies = rx.get("strategies", [])
            return {
                "coaching_text": self._format_fallback_text(rx, stage),
                "strategies": strategies,
                "confidence": 0.5,
            }

        prompt = f"""你是一位行为健康教练的AI助手。根据以下信息，为教练生成针对该用户的干预建议。

用户阶段: {stage.get('stage_name')} ({stage.get('stage')})
阶段停留: {stage.get('days_in_stage', '未知')}天
自主模式: {stage.get('agency_mode', '未知')}
推荐策略: {', '.join(rx.get('strategies', []))}
沟通风格: {rx.get('communication_style', '支持性')}
干预强度: {rx.get('intensity', '中等')}

教练的问题/关注: {message}

请生成:
1. 针对该用户当前阶段的2-3条具体干预建议
2. 每条建议包含：做什么、为什么、怎么说
3. 注意匹配推荐的沟通风格

要求：语言专业但温暖，给教练看的（不是直接给用户的）。"""

        try:
            response = await llm.achat(prompt) if hasattr(llm, 'achat') else llm.chat(prompt)
            text = response if isinstance(response, str) else getattr(response, 'content', str(response))
            return {
                "coaching_text": text,
                "strategies": rx.get("strategies", []),
                "confidence": 0.8,
            }
        except Exception as e:
            logger.warning(f"LLM增强失败: {e}")
            return {
                "coaching_text": self._format_fallback_text(rx, stage),
                "strategies": rx.get("strategies", []),
                "confidence": 0.5,
            }

    def _format_fallback_text(self, rx: dict, stage: dict) -> str:
        """LLM不可用时的结构化文本输出"""
        strategies = rx.get("strategies", ["通用支持"])
        style = rx.get("communication_style", "supportive")
        intensity = rx.get("intensity", "moderate")
        stage_name = stage.get("stage_name", "未知阶段")

        lines = [
            f"【行为教练建议 — {stage_name}】",
            f"",
            f"推荐干预策略: {', '.join(strategies)}",
            f"沟通风格: {style}",
            f"干预强度: {intensity}",
            f"引擎: {rx.get('engine', 'unknown')}",
            f"",
            f"说明: LLM服务暂不可用，以上为结构化Rx输出。",
            f"教练可根据推荐策略自行制定具体干预方案。",
        ]
        return "\n".join(lines)

    @staticmethod
    def _stage_name(stage: str) -> str:
        NAMES = {
            "S0": "前意识期", "S1": "意识期", "S2": "准备期",
            "S3": "行动期", "S4": "维持期", "S5": "终止期",
        }
        return NAMES.get(stage, f"未知({stage})")

    # ── Rx引擎调用 (Sheet⑬ 要求) ──

    async def compute_rx(self, profile: dict) -> dict:
        """直接调用Rx引擎 — 供其他Agent或路由使用"""
        stage_info = {
            "stage": profile.get("ttm_stage", "S0"),
            "stage_name": self._stage_name(profile.get("ttm_stage", "S0")),
            "agency_mode": profile.get("agency_mode", "unknown"),
        }
        return await self._compute_behavior_rx(profile, stage_info)
