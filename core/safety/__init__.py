# -*- coding: utf-8 -*-
"""
安全模块 — 4 层安全管线

L1: InputFilter   — 输入过滤 (敏感词 + 正则 + 意图分类)
L2: RAGSafety     — RAG 安全增强 (evidence tier 排序 + 过期过滤)
L3: GenerationGuard — 生成约束 (system prompt 注入 + 领域边界)
L4: OutputFilter  — 输出过滤 (医疗声明检测 + 合规标注)
"""
from .pipeline import SafetyPipeline
from .input_filter import InputFilter, InputFilterResult
from .rag_safety import RAGSafety, RAGSafetyResult
from .generation_guard import GenerationGuard, GuardedPrompt
from .output_filter import OutputFilter, OutputFilterResult

__all__ = [
    "SafetyPipeline",
    "InputFilter", "InputFilterResult",
    "RAGSafety", "RAGSafetyResult",
    "GenerationGuard", "GuardedPrompt",
    "OutputFilter", "OutputFilterResult",
]
