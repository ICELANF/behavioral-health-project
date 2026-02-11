# -*- coding: utf-8 -*-
"""
SafetyPipeline — 4 层安全管线编排器

编排 L1→L2→L3→L4 四层安全检查.
"""
from __future__ import annotations

import logging
from typing import Optional

from .input_filter import InputFilter, InputFilterResult
from .rag_safety import RAGSafety, RAGSafetyResult
from .generation_guard import GenerationGuard, GuardedPrompt, CRISIS_RESPONSE_TEMPLATE
from .output_filter import OutputFilter, OutputFilterResult

logger = logging.getLogger(__name__)


def _safety_enabled() -> bool:
    """检查安全模块是否启用"""
    try:
        import api.config as cfg
        return getattr(cfg, "SAFETY_ENABLED", True)
    except ImportError:
        import os
        return os.getenv("SAFETY_ENABLED", "true").lower() in ("true", "1", "yes")


class SafetyPipeline:
    """
    4 层安全管线编排器

    用法:
        pipeline = get_safety_pipeline()

        # L1: 输入过滤
        input_result = pipeline.process_input(user_message)

        # L2: RAG 安全增强
        rag_result = pipeline.enhance_retrieval(query, rag_results)

        # L3: 生成约束
        guarded = pipeline.guard_generation(system_prompt, input_result.category)

        # L4: 输出过滤
        output_result = pipeline.filter_output(llm_output, input_result.category)
    """

    def __init__(self):
        self.input_filter = InputFilter()
        self.rag_safety = RAGSafety()
        self.generation_guard = GenerationGuard()
        self.output_filter = OutputFilter()
        self.enabled = _safety_enabled()
        logger.info("SafetyPipeline initialized (enabled=%s)", self.enabled)

    # ── L1: 输入过滤 ──

    def process_input(self, user_message: str) -> InputFilterResult:
        """L1 输入安全检查"""
        if not self.enabled:
            return InputFilterResult(safe=True)
        return self.input_filter.check(user_message)

    # ── L2: RAG 安全增强 ──

    def enhance_retrieval(self, query: str,
                          rag_results: list[dict]) -> RAGSafetyResult:
        """L2 RAG 检索结果安全增强"""
        if not self.enabled:
            return RAGSafetyResult(references=rag_results,
                                   total_count=len(rag_results))
        return self.rag_safety.enhance(query, rag_results)

    # ── L3: 生成约束 ──

    def guard_generation(self,
                         system_prompt: str,
                         input_category: str = "normal",
                         agent_domain: str = "",
                         user_message: str = "") -> GuardedPrompt:
        """L3 为 LLM 生成注入安全约束"""
        if not self.enabled:
            return GuardedPrompt(system_prompt=system_prompt)
        return self.generation_guard.guard(
            system_prompt=system_prompt,
            input_category=input_category,
            agent_domain=agent_domain,
            user_message=user_message,
        )

    # ── L4: 输出过滤 ──

    def filter_output(self, text: str,
                      input_category: str = "normal") -> OutputFilterResult:
        """L4 输出安全过滤"""
        if not self.enabled:
            return OutputFilterResult(text=text, grade="safe")
        return self.output_filter.filter(text, input_category)

    # ── 便捷: 获取危机回复 ──

    @staticmethod
    def get_crisis_response() -> str:
        """获取标准危机回复模板"""
        return CRISIS_RESPONSE_TEMPLATE


# ── 单例 ──────────────────────────────────────────────────

_instance: Optional[SafetyPipeline] = None


def get_safety_pipeline() -> SafetyPipeline:
    """获取全局安全管线单例"""
    global _instance
    if _instance is None:
        _instance = SafetyPipeline()
    return _instance
