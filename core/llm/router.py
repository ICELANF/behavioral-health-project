"""
LLM 三级路由器 — 按复杂度分流 + 故障自动降级
放置: api/core/llm/router.py

路由策略:
  simple  → qwen-turbo    (意图分类/情绪标签/简单确认)
  medium  → qwen-plus     (日常问答/任务提醒/知识检索)
  complex → qwen3-max     (诊断报告/处方生成/Coach深度对话)

降级链:
  qwen3-max → qwen-plus → deepseek-v3-bailian → deepseek-v3
"""
import logging
import time
from dataclasses import dataclass
from typing import Any

from core.llm.client import (
    LLMClient, LLMResponse, LLMTimeoutError, LLMAPIError,
    MODEL_REGISTRY,
)

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════
# 复杂度分级
# ══════════════════════════════════════════════

class TaskComplexity:
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


# 复杂度 → 模型映射 + 降级链
ROUTING_TABLE: dict[str, list[str]] = {
    TaskComplexity.SIMPLE: [
        "qwen-turbo",
        "qwen-plus",          # 降级1
    ],
    TaskComplexity.MEDIUM: [
        "qwen-plus",
        "qwen-turbo",         # 降级1 (损失质量换可用)
        "deepseek-v3-bailian",  # 降级2
    ],
    TaskComplexity.COMPLEX: [
        "qwen3-max",
        "qwen-plus",          # 降级1
        "deepseek-v3-bailian",  # 降级2
        "deepseek-v3",         # 降级3 (独立API)
    ],
}

# 意图 → 复杂度映射 (用于自动分级)
INTENT_COMPLEXITY: dict[str, str] = {
    # simple
    "greeting": TaskComplexity.SIMPLE,
    "checkin_confirm": TaskComplexity.SIMPLE,
    "mood_tag": TaskComplexity.SIMPLE,
    "intent_classify": TaskComplexity.SIMPLE,
    "yes_no_question": TaskComplexity.SIMPLE,
    # medium
    "knowledge_qa": TaskComplexity.MEDIUM,
    "task_reminder": TaskComplexity.MEDIUM,
    "progress_summary": TaskComplexity.MEDIUM,
    "general_chat": TaskComplexity.MEDIUM,
    "strategy_explain": TaskComplexity.MEDIUM,
    # complex
    "diagnostic_report": TaskComplexity.COMPLEX,
    "prescription_generate": TaskComplexity.COMPLEX,
    "coach_dialogue": TaskComplexity.COMPLEX,
    "stage_assessment": TaskComplexity.COMPLEX,
    "crisis_support": TaskComplexity.COMPLEX,
    "behavior_analysis": TaskComplexity.COMPLEX,
}


# ══════════════════════════════════════════════
# 使用量追踪
# ══════════════════════════════════════════════

@dataclass
class UsageStats:
    """路由级使用统计 (内存, 可定期持久化)"""
    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_yuan: float = 0.0
    total_latency_ms: int = 0
    fallback_count: int = 0
    error_count: int = 0
    model_calls: dict = None

    def __post_init__(self):
        if self.model_calls is None:
            self.model_calls = {}

    def record(self, resp: LLMResponse, fell_back: bool = False):
        self.total_calls += 1
        self.total_input_tokens += resp.input_tokens
        self.total_output_tokens += resp.output_tokens
        self.total_cost_yuan += resp.cost_yuan
        self.total_latency_ms += resp.latency_ms
        if fell_back:
            self.fallback_count += 1
        model = resp.model
        if model not in self.model_calls:
            self.model_calls[model] = {"count": 0, "cost": 0.0}
        self.model_calls[model]["count"] += 1
        self.model_calls[model]["cost"] += resp.cost_yuan

    def summary(self) -> dict:
        avg_latency = self.total_latency_ms / self.total_calls if self.total_calls else 0
        return {
            "total_calls": self.total_calls,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost_yuan": round(self.total_cost_yuan, 4),
            "avg_latency_ms": round(avg_latency),
            "fallback_rate": round(self.fallback_count / max(self.total_calls, 1), 4),
            "model_breakdown": self.model_calls,
        }


# ══════════════════════════════════════════════
# 路由器
# ══════════════════════════════════════════════

class LLMRouter:
    """
    BHP LLM 路由器

    用法:
        router = LLMRouter()
        resp = router.route(
            messages=[{"role":"user","content":"我今天完成打卡了"}],
            intent="checkin_confirm",
        )
    """

    def __init__(self, client: LLMClient | None = None):
        self.client = client or LLMClient()
        self.stats = UsageStats()

    def classify_complexity(
        self,
        intent: str | None = None,
        message: str | None = None,
    ) -> str:
        """
        判定任务复杂度

        优先用 intent (精确), 否则用启发式规则 (粗略)
        """
        if intent and intent in INTENT_COMPLEXITY:
            return INTENT_COMPLEXITY[intent]

        # 启发式: 根据消息长度和关键词
        if message:
            msg = message.lower()
            complex_keywords = [
                "诊断", "评估", "处方", "报告", "分析",
                "为什么", "怎么办", "制定计划", "行为改变",
                "心理", "情绪困扰", "焦虑", "抑郁",
            ]
            simple_keywords = [
                "好的", "谢谢", "打卡", "签到", "是的", "不是",
                "你好", "早上好", "晚安",
            ]
            if any(kw in msg for kw in complex_keywords):
                return TaskComplexity.COMPLEX
            if any(kw in msg for kw in simple_keywords) or len(msg) < 10:
                return TaskComplexity.SIMPLE
        return TaskComplexity.MEDIUM

    def route(
        self,
        messages: list[dict],
        system: str | None = None,
        intent: str | None = None,
        complexity: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        force_model: str | None = None,
    ) -> LLMResponse:
        """
        智能路由 + 降级调用

        Args:
            messages: 对话消息列表
            system: 系统提示词
            intent: 意图标签 (如 "coach_dialogue")
            complexity: 直接指定复杂度 (跳过分类)
            force_model: 强制使用指定模型 (跳过路由)

        Returns:
            LLMResponse
        """
        # 确定复杂度
        if force_model:
            chain = [force_model]
            level = "forced"
        else:
            level = complexity or self.classify_complexity(
                intent=intent,
                message=messages[-1]["content"] if messages else None,
            )
            chain = ROUTING_TABLE.get(level, ROUTING_TABLE[TaskComplexity.MEDIUM])

        # 按降级链逐个尝试
        last_error = None
        for i, model_key in enumerate(chain):
            if model_key not in MODEL_REGISTRY:
                continue
            try:
                resp = self.client.chat(
                    model_key=model_key,
                    messages=messages,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                fell_back = i > 0
                if fell_back:
                    logger.warning(
                        f"Fallback: {chain[0]} → {model_key} "
                        f"(reason: {last_error})"
                    )
                self.stats.record(resp, fell_back=fell_back)
                return resp

            except (LLMTimeoutError, LLMAPIError) as e:
                last_error = str(e)
                logger.warning(f"Model {model_key} failed: {e}, trying next...")
                self.stats.error_count += 1
                continue

        # 全部失败
        raise LLMAPIError(
            "all_models",
            503,
            f"All models in chain failed: {chain}. Last error: {last_error}",
        )

    def route_with_rag(
        self,
        query: str,
        rag_context: str,
        system: str | None = None,
        intent: str = "knowledge_qa",
        extra_messages: list[dict] | None = None,
    ) -> LLMResponse:
        """
        RAG 增强路由: 将检索结果注入 prompt

        Args:
            query: 用户问题
            rag_context: RAG 检索到的上下文 (已拼接)
            system: 额外系统提示词
            extra_messages: 历史对话消息
        """
        rag_system = (
            "你是 BHP (行为健康促进) 平台的专业健康顾问。\n"
            "请根据以下知识库内容回答用户问题。如果知识库中没有相关信息，"
            "请诚实说明，不要编造。\n\n"
            "【知识库参考】\n"
            f"{rag_context}\n\n"
            "【回答要求】\n"
            "- 准确引用知识库内容\n"
            "- 使用通俗易懂的中文\n"
            "- 如涉及具体数值/阈值，请精确引用\n"
            "- 如果用户问题超出知识库范围，建议咨询专业人士"
        )
        if system:
            rag_system = f"{system}\n\n{rag_system}"

        messages = list(extra_messages or [])
        messages.append({"role": "user", "content": query})

        return self.route(
            messages=messages,
            system=rag_system,
            intent=intent,
        )

    def get_stats(self) -> dict:
        return self.stats.summary()
