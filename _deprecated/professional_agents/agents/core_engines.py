"""
评估引擎 + 处方组合器 — 教练层核心双引擎

assessment_engine: 评估量表执行 + 结果解读 + BPT-6分型
rx_composer: 多源处方合成 + 模板渲染 + 教练审核前格式化

对接:
  - BPT6RxEngine → BPT-6六域评估
  - BehaviorRxEngine → 行为处方计算
  - core/stage_engine → TTM阶段
  - UnifiedLLMClient → 自然语言增强
"""
from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional

from ..base import BaseProfessionalAgent

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# assessment_engine — 评估引擎
# ═══════════════════════════════════════════════════════════

class AssessmentEngineAgent(BaseProfessionalAgent):
    """评估引擎 — 量表执行 + BPT-6分型"""

    @property
    def name(self) -> str:
        return "assessment_engine"

    @property
    def domain(self) -> str:
        return "assessment"

    def _get_bpt6_engine(self):
        try:
            from core.bpt6_rx_engine import BPT6RxEngine
            return BPT6RxEngine()
        except ImportError:
            return None

    def _get_llm_client(self):
        try:
            from core.llm_client import get_llm_client
            return get_llm_client()
        except ImportError:
            return None

    async def run(self, message: str, **kwargs) -> Dict[str, Any]:
        """
        kwargs:
            action: str — "compute_bpt6" | "interpret_result" | "recommend_scale"
            assessment_data: dict — 评估原始数据
            user_profile: dict
        """
        if not await self.safety_check(message):
            return self._format_response(content="安全拦截", safety_intercepted=True)

        action = kwargs.get("action", "interpret_result")

        if action == "compute_bpt6":
            return await self._compute_bpt6(kwargs.get("assessment_data", {}), kwargs.get("user_profile", {}))
        elif action == "recommend_scale":
            return await self._recommend_scale(kwargs.get("user_profile", {}), message)
        else:
            return await self._interpret_result(kwargs.get("assessment_data", {}), message)

    async def _compute_bpt6(self, data: dict, profile: dict) -> dict:
        """执行BPT-6六域评估"""
        bpt6 = self._get_bpt6_engine()
        if not bpt6:
            return self._format_response(
                content="BPT-6引擎不可用，请检查配置。",
                engine_status="unavailable",
                review_required=True,
            )

        try:
            # BPT-6六域: 行为、认知、情感、社会、身体、精神
            result = bpt6.compute(data) if hasattr(bpt6, 'compute') else {}
            if hasattr(bpt6, 'assess'):
                result = bpt6.assess(data)

            bpt6_type = result.get("type") or result.get("bpt6_type", "未分类")
            domain_scores = result.get("domain_scores", {})
            strengths = result.get("strengths", [])
            growth_areas = result.get("growth_areas", [])

            # LLM增强解读
            interpretation = await self._llm_interpret_bpt6(bpt6_type, domain_scores, profile)

            return self._format_response(
                content=interpretation,
                bpt6_type=bpt6_type,
                domain_scores=domain_scores,
                strengths=strengths,
                growth_areas=growth_areas,
                engine="bpt6",
                review_required=True,
                confidence=0.8,
            )
        except Exception as e:
            logger.error(f"BPT-6计算失败: {e}")
            return self._format_response(
                content=f"BPT-6计算异常: {str(e)[:100]}",
                engine_status="error",
                review_required=True,
            )

    async def _interpret_result(self, data: dict, message: str) -> dict:
        """通用评估结果解读"""
        llm = self._get_llm_client()
        if not llm:
            return self._format_response(
                content=self._structured_interpretation(data),
                review_required=True,
                confidence=0.5,
            )

        prompt = f"""作为行为健康评估专家，请解读以下评估结果：

评估数据: {str(data)[:500]}
教练的问题: {message}

请提供：
1. 关键发现（2-3条）
2. 风险提示（如有）
3. 建议下一步评估或干预方向

注意：这是给教练看的专业解读，不是给用户的。"""

        try:
            response = await llm.achat(prompt) if hasattr(llm, 'achat') else llm.chat(prompt)
            text = response if isinstance(response, str) else getattr(response, 'content', str(response))
            return self._format_response(
                content=text,
                review_required=True,
                confidence=0.7,
            )
        except Exception as e:
            return self._format_response(
                content=self._structured_interpretation(data),
                review_required=True,
                confidence=0.5,
            )

    async def _recommend_scale(self, profile: dict, message: str) -> dict:
        """根据用户画像推荐评估量表"""
        stage = profile.get("ttm_stage", "S0")
        agency = profile.get("agency_mode", "unknown")

        # 规则推荐
        recommendations = []
        if stage in ("S0", "S1"):
            recommendations.extend(["动机准备度量表", "健康信念量表", "自我效能量表"])
        elif stage in ("S2", "S3"):
            recommendations.extend(["行为改变阶段量表", "社会支持量表", "自我调节量表"])
        elif stage in ("S4", "S5"):
            recommendations.extend(["维持自信量表", "生活质量量表", "复发预防量表"])

        # 通用推荐
        if not profile.get("bpt6_type"):
            recommendations.insert(0, "BPT-6行为分型评估")

        return self._format_response(
            content=f"基于用户当前阶段({stage})，推荐评估: {', '.join(recommendations[:5])}",
            recommendations=recommendations[:5],
            review_required=True,
        )

    async def _llm_interpret_bpt6(self, bpt6_type, domain_scores, profile) -> str:
        llm = self._get_llm_client()
        if not llm:
            return f"BPT-6分型: {bpt6_type}\n六域得分: {domain_scores}"
        try:
            prompt = f"简要解读BPT-6结果。分型: {bpt6_type}, 六域: {domain_scores}。给教练的2-3条要点。"
            response = await llm.achat(prompt) if hasattr(llm, 'achat') else llm.chat(prompt)
            return response if isinstance(response, str) else getattr(response, 'content', str(response))
        except Exception:
            return f"BPT-6分型: {bpt6_type}\n六域得分: {domain_scores}"

    def _structured_interpretation(self, data: dict) -> str:
        lines = ["【评估结果结构化解读】\n"]
        for key, value in list(data.items())[:10]:
            lines.append(f"  {key}: {value}")
        lines.append("\n（LLM不可用，请教练自行判读）")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# rx_composer — 处方组合器
# ═══════════════════════════════════════════════════════════

class RxComposerAgent(BaseProfessionalAgent):
    """处方组合器 — 多源合成 + 审核格式化"""

    @property
    def name(self) -> str:
        return "rx_composer"

    @property
    def domain(self) -> str:
        return "prescription"

    def _get_rx_engine(self):
        try:
            from behavior_rx.behavior_rx_engine import BehaviorRxEngine
            return BehaviorRxEngine()
        except ImportError:
            return None

    def _get_bpt6_engine(self):
        try:
            from core.bpt6_rx_engine import BPT6RxEngine
            return BPT6RxEngine()
        except ImportError:
            return None

    def _get_stage_config(self):
        try:
            from core.stage_personalization import get_stage_config
            return get_stage_config
        except ImportError:
            return None

    def _get_llm_client(self):
        try:
            from core.llm_client import get_llm_client
            return get_llm_client()
        except ImportError:
            return None

    async def run(self, message: str, **kwargs) -> Dict[str, Any]:
        """
        kwargs:
            action: "compose" | "preview" | "format_for_review"
            rx_sources: list — 各Agent提供的Rx片段
            user_profile: dict
            db: AsyncSession
        """
        if not await self.safety_check(message):
            return self._format_response(content="安全拦截", safety_intercepted=True)

        action = kwargs.get("action", "compose")
        profile = kwargs.get("user_profile", {})
        rx_sources = kwargs.get("rx_sources", [])

        if action == "compose":
            return await self._compose_rx(profile, rx_sources, message)
        elif action == "preview":
            return await self._preview_rx(profile, rx_sources)
        elif action == "format_for_review":
            return await self._format_for_review(rx_sources, profile)
        else:
            return await self._compose_rx(profile, rx_sources, message)

    async def _compose_rx(self, profile: dict, sources: list, message: str) -> dict:
        """从多个Agent的建议中合成统一处方"""
        stage = profile.get("ttm_stage", "S0")

        # 1. 收集各引擎的Rx
        rx_fragments = list(sources)  # 已有的外部来源

        # 2. 补充BPT6处方
        bpt6 = self._get_bpt6_engine()
        if bpt6:
            try:
                bpt6_rx = bpt6.compute({
                    "ttm_stage": stage,
                    "bpt6_type": profile.get("bpt6_type"),
                }) or {}
                if bpt6_rx:
                    rx_fragments.append({
                        "source": "bpt6",
                        "strategies": bpt6_rx.get("strategies", []),
                        "priority": 1,
                    })
            except Exception as e:
                logger.warning(f"BPT6 Rx获取失败: {e}")

        # 3. 补充BehaviorRx
        rx_engine = self._get_rx_engine()
        if rx_engine:
            try:
                rx = rx_engine.compute_rx({
                    "stage": stage,
                    "personality": profile.get("big_five_scores", {}),
                    "capacity": profile.get("capacity", 0.5),
                }) or {}
                if rx:
                    rx_fragments.append({
                        "source": "behavior_rx",
                        "strategies": rx.get("strategies", []),
                        "priority": 2,
                    })
            except Exception as e:
                logger.warning(f"BehaviorRx获取失败: {e}")

        # 4. 阶段个性化
        stage_config_fn = self._get_stage_config()
        stage_config = {}
        if stage_config_fn:
            try:
                stage_config = stage_config_fn(stage) or {}
            except Exception:
                pass

        # 5. 合并去重
        composed = self._merge_rx(rx_fragments, stage_config)

        # 6. LLM美化
        formatted = await self._llm_format_rx(composed, profile, message)

        return self._format_response(
            content=formatted["text"],
            rx_composed=composed,
            sources_used=[f.get("source", "unknown") for f in rx_fragments],
            stage=stage,
            review_required=True,
            confidence=formatted.get("confidence", 0.7),
        )

    def _merge_rx(self, fragments: list, stage_config: dict) -> dict:
        """合并多源Rx，去重+排序"""
        all_strategies = []
        seen = set()
        for frag in sorted(fragments, key=lambda x: x.get("priority", 99)):
            for s in frag.get("strategies", []):
                s_key = s if isinstance(s, str) else str(s)
                if s_key not in seen:
                    seen.add(s_key)
                    all_strategies.append(s_key)

        # 限制策略数量（避免处方过载）
        max_strategies = stage_config.get("max_rx_strategies", 5)

        return {
            "strategies": all_strategies[:max_strategies],
            "total_sources": len(fragments),
            "intensity": stage_config.get("intensity", "moderate"),
            "communication_style": stage_config.get("style", "supportive"),
            "duration_weeks": stage_config.get("rx_duration_weeks", 4),
        }

    async def _preview_rx(self, profile: dict, sources: list) -> dict:
        """预览模式 — 不写入数据库"""
        composed = self._merge_rx(sources, {})
        return self._format_response(
            content=f"预览处方: {', '.join(composed['strategies'][:5])}",
            rx_preview=composed,
            review_required=False,
        )

    async def _format_for_review(self, sources: list, profile: dict) -> dict:
        """格式化为教练审核格式"""
        composed = self._merge_rx(sources, {})
        review_doc = {
            "patient_stage": profile.get("ttm_stage", "未知"),
            "patient_type": profile.get("bpt6_type", "未分类"),
            "strategies": composed["strategies"],
            "intensity": composed["intensity"],
            "duration": f"{composed['duration_weeks']}周",
            "sources": [s.get("source", "") for s in sources],
            "requires_approval": True,
        }
        return self._format_response(
            content="处方已格式化，待教练审核。",
            review_document=review_doc,
            review_required=True,
        )

    async def _llm_format_rx(self, composed: dict, profile: dict, message: str) -> dict:
        llm = self._get_llm_client()
        if not llm:
            strategies = composed.get("strategies", [])
            text = f"【行为处方】\n\n干预策略:\n" + "\n".join(f"  {i}. {s}" for i, s in enumerate(strategies, 1))
            text += f"\n\n强度: {composed.get('intensity')}"
            text += f"\n周期: {composed.get('duration_weeks')}周"
            text += f"\n\n（待教练审核）"
            return {"text": text, "confidence": 0.5}

        prompt = f"""将以下结构化行为处方转化为教练可读的格式：

策略: {', '.join(composed.get('strategies', []))}
强度: {composed.get('intensity')}
周期: {composed.get('duration_weeks')}周
沟通风格: {composed.get('communication_style')}
教练备注: {message}

请输出包含：每条策略的执行要点、频次建议、效果观察指标。"""

        try:
            response = await llm.achat(prompt) if hasattr(llm, 'achat') else llm.chat(prompt)
            text = response if isinstance(response, str) else getattr(response, 'content', str(response))
            return {"text": text, "confidence": 0.8}
        except Exception:
            strategies = composed.get("strategies", [])
            text = f"【行为处方】\n策略: {', '.join(strategies)}\n（LLM不可用，待教练审核）"
            return {"text": text, "confidence": 0.5}
