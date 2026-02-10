"""
Coach Agent — 将诊断管道 + RAG + LLM 整合为统一对话代理
放置: api/core/llm/coach_agent.py

职责:
  1. 接收用户消息, 判断意图
  2. 查 RAG 知识库获取参考
  3. 结合用户画像 (DiagnosticPipeline 输出) 生成回复
  4. 记录对话日志供效果追踪使用

与现有模块的关系:
  - 读取: DiagnosticPipeline.PipelineResult (用户画像)
  - 读取: InterventionStrategyEngine.match()  (策略话术)
  - 读取: IncentiveIntegration (成长等级/处方模式)
  - 写入: llm_call_logs 表 (调用日志)
  - 调用: RAGPipeline (知识检索+生成)
  - 调用: LLMRouter (三级路由)
"""
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from core.llm.client import LLMClient, LLMResponse
from core.llm.router import LLMRouter, TaskComplexity, INTENT_COMPLEXITY
from core.rag.pipeline import RAGPipeline, RAGResult, RAGConfig
from core.rag.vector_store import QdrantStore

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════
# 意图识别 Prompt
# ══════════════════════════════════════════════

INTENT_CLASSIFY_PROMPT = """你是 BHP 行为健康平台的意图分类器。
请判断用户消息的意图类别, 仅输出一个标签。

可选标签:
- greeting: 打招呼/问候
- checkin_confirm: 打卡/签到确认
- mood_tag: 表达情绪/心情
- knowledge_qa: 知识/概念类提问
- task_reminder: 询问任务/进度
- progress_summary: 查看汇总/报告
- strategy_explain: 询问干预策略的原因
- coach_dialogue: 寻求深度指导/困惑
- stage_assessment: 要求评估/测评
- crisis_support: 表达严重困扰/危机
- general_chat: 闲聊/其他

用户消息: {message}
意图标签:"""


# ══════════════════════════════════════════════
# 对话上下文
# ══════════════════════════════════════════════

@dataclass
class UserContext:
    """用户上下文 (从 PipelineResult 提取)"""
    user_id: int
    behavioral_stage: str = "S0"
    readiness_level: str = "L1"
    spi_score: float = 0.0
    bpt_type: str = "mixed"
    cultivation_stage: str = "startup"
    growth_level: str = "G0"
    streak_days: int = 0
    health_competency: str = "Lv0"
    top_obstacles: list = field(default_factory=list)
    dominant_causes: list = field(default_factory=list)
    strengths: list = field(default_factory=list)
    weaknesses: list = field(default_factory=list)
    support_level: str = "moderate"

    def to_profile_dict(self) -> dict:
        """转为 RAGPipeline 需要的 profile 字典"""
        return {
            "behavioral_stage": self.behavioral_stage,
            "readiness_level": self.readiness_level,
            "spi_score": self.spi_score,
            "behavior_type": self.bpt_type,
            "cultivation_stage": self.cultivation_stage,
            "growth_level": self.growth_level,
            "health_competency": self.health_competency,
            "top_obstacles": self.top_obstacles,
            "dominant_causes": self.dominant_causes,
            "support_level": self.support_level,
        }

    @classmethod
    def from_pipeline_result(cls, pr) -> "UserContext":
        """从 DiagnosticPipeline.PipelineResult 构建"""
        ctx = cls(user_id=pr.user_id)
        ctx.behavioral_stage = pr.layer1.behavioral_stage
        ctx.bpt_type = pr.layer1.bpt_type
        ctx.spi_score = pr.layer2.spi_score
        ctx.readiness_level = pr.layer2.readiness_level

        if pr.layer3:
            ctx.strengths = pr.layer3.strengths
            ctx.weaknesses = pr.layer3.weaknesses
            ctx.top_obstacles = [
                o.get("category", "unknown")
                for o in pr.layer3.obstacles.get("top_obstacles", [])[:3]
            ] if pr.layer3.obstacles else []
            if pr.layer3.support:
                ctx.support_level = pr.layer3.support.get("support_level", "moderate")

        if pr.layer2.cause_analysis:
            sorted_causes = sorted(
                pr.layer2.cause_analysis.get("scores", {}).items(),
                key=lambda x: x[1], reverse=True,
            )
            ctx.dominant_causes = [c[0] for c in sorted_causes[:3]]

        ctx.cultivation_stage = pr.layer4.cultivation_stage
        ctx.growth_level = pr.layer4.incentive_context.get("growth_level", "G0")

        return ctx


# ══════════════════════════════════════════════
# 对话日志 (内存缓存, 可定期写入数据库)
# ══════════════════════════════════════════════

@dataclass
class ConversationTurn:
    """单轮对话记录"""
    turn_id: int
    user_id: int
    timestamp: datetime
    user_message: str
    intent: str
    assistant_message: str
    model_used: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_yuan: float = 0.0
    latency_ms: int = 0
    rag_sources: list = field(default_factory=list)
    used_rag: bool = False

    def to_db_dict(self) -> dict:
        """转为数据库写入格式"""
        return {
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "user_message": self.user_message[:500],
            "intent": self.intent,
            "assistant_message": self.assistant_message[:2000],
            "model_used": self.model_used,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_yuan": self.cost_yuan,
            "latency_ms": self.latency_ms,
            "rag_source_count": len(self.rag_sources),
            "used_rag": self.used_rag,
        }


# ══════════════════════════════════════════════
# Coach Agent
# ══════════════════════════════════════════════

# 需要 RAG 的意图
RAG_INTENTS = {
    "knowledge_qa", "strategy_explain", "coach_dialogue",
    "stage_assessment", "crisis_support", "progress_summary",
}

# 简单回复 (不调 LLM)
QUICK_REPLIES: dict[str, str] = {
    "checkin_confirm": "打卡成功！今天的任务完成得很好 💪 继续保持！",
}


class CoachAgent:
    """
    BHP 对话代理 — 统一入口

    用法:
        agent = CoachAgent()
        reply = agent.chat(
            user_id=123,
            message="SPI评分低于30是不是说明我没救了？",
            user_context=ctx,       # 从 DiagnosticPipeline 获取
            history=prev_messages,  # 可选: 多轮对话历史
        )
        print(reply["answer"])
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        router: LLMRouter | None = None,
        rag_pipeline: RAGPipeline | None = None,
        qdrant_url: str | None = None,
    ):
        self.llm = llm_client or LLMClient()
        self.router = router or LLMRouter(self.llm)

        if rag_pipeline:
            self.rag = rag_pipeline
        else:
            store = QdrantStore(base_url=qdrant_url)
            self.rag = RAGPipeline(self.llm, self.router, store)

        self._turn_counter = 0
        self._conversation_log: list[ConversationTurn] = []

    def chat(
        self,
        user_id: int,
        message: str,
        user_context: UserContext | None = None,
        history: list[dict] | None = None,
        force_intent: str | None = None,
    ) -> dict:
        """
        主对话接口

        Args:
            user_id: 用户ID
            message: 用户消息
            user_context: 用户上下文 (画像)
            history: 多轮对话历史 [{"role":"user","content":"..."},...]
            force_intent: 强制指定意图 (跳过分类)

        Returns:
            {
                "answer": str,
                "intent": str,
                "model": str,
                "sources": list,
                "latency_ms": int,
                "tokens": int,
                "cost_yuan": float,
            }
        """
        t0 = time.time()

        # Step 1: 意图识别
        intent = force_intent or self._classify_intent(message)

        # Step 2: 快捷回复检查
        if intent in QUICK_REPLIES and not history:
            answer = QUICK_REPLIES[intent]
            latency = int((time.time() - t0) * 1000)
            self._log_turn(user_id, message, intent, answer, "", 0, 0, 0, latency, [])
            return {
                "answer": answer,
                "intent": intent,
                "model": "builtin",
                "sources": [],
                "latency_ms": latency,
                "tokens": 0,
                "cost_yuan": 0,
            }

        # Step 3: 判断是否需要 RAG
        use_rag = intent in RAG_INTENTS

        # Step 4: 生成回复
        if use_rag and intent == "coach_dialogue" and user_context:
            # Coach 对话: RAG + 画像
            result = self.rag.coach_query(
                question=message,
                user_profile=user_context.to_profile_dict(),
                history=history,
            )
        elif use_rag:
            # 知识问答: 纯 RAG
            result = self.rag.query(
                question=message,
                history=history,
            )
        else:
            # 简单对话: 直接 LLM
            system = self._build_simple_system(user_context)
            messages = list(history or [])
            messages.append({"role": "user", "content": message})

            llm_resp = self.router.route(
                messages=messages,
                system=system,
                intent=intent,
            )
            result = RAGResult(
                answer=llm_resp.content,
                sources=[],
                llm_response=llm_resp,
                query=message,
                latency_ms=int((time.time() - t0) * 1000),
            )

        latency = int((time.time() - t0) * 1000)

        # Step 5: 记录日志
        llm_resp = result.llm_response
        self._log_turn(
            user_id, message, intent, result.answer,
            llm_resp.model if llm_resp else "",
            llm_resp.input_tokens if llm_resp else 0,
            llm_resp.output_tokens if llm_resp else 0,
            llm_resp.cost_yuan if llm_resp else 0,
            latency, result.sources, use_rag,
        )

        return {
            "answer": result.answer,
            "intent": intent,
            "model": llm_resp.model if llm_resp else "builtin",
            "sources": result.sources,
            "latency_ms": latency,
            "tokens": llm_resp.total_tokens if llm_resp else 0,
            "cost_yuan": llm_resp.cost_yuan if llm_resp else 0,
        }

    def generate_prescription(
        self,
        user_context: UserContext,
        layer3_report: dict | None = None,
    ) -> dict:
        """
        RAG 增强处方生成

        将已有的规则引擎处方 (DiagnosticPipeline.Layer4)
        与 LLM 生成的个性化话术/任务名称结合
        """
        result = self.rag.prescription_query(
            user_profile=user_context.to_profile_dict(),
            layer3_report=layer3_report,
        )

        return {
            "prescription_text": result.answer,
            "sources": result.sources,
            "model": result.llm_response.model if result.llm_response else "",
            "cost_yuan": result.llm_response.cost_yuan if result.llm_response else 0,
        }

    def get_conversation_log(self, user_id: int | None = None) -> list[dict]:
        """获取对话日志"""
        logs = self._conversation_log
        if user_id:
            logs = [l for l in logs if l.user_id == user_id]
        return [l.to_db_dict() for l in logs]

    def get_stats(self) -> dict:
        """汇总统计"""
        router_stats = self.router.get_stats()
        return {
            "total_turns": len(self._conversation_log),
            "router": router_stats,
        }

    # ── 内部方法 ──

    def _classify_intent(self, message: str) -> str:
        """用轻量模型分类意图"""
        try:
            prompt = INTENT_CLASSIFY_PROMPT.format(message=message)
            resp = self.router.route(
                messages=[{"role": "user", "content": prompt}],
                complexity=TaskComplexity.SIMPLE,
                max_tokens=20,
                temperature=0.1,
            )
            intent = resp.content.strip().lower().replace('"', "").replace("'", "")
            # 验证是否在已知意图列表中
            if intent in INTENT_COMPLEXITY:
                return intent
            return "general_chat"
        except Exception as e:
            logger.warning(f"Intent classification failed: {e}")
            return "general_chat"

    def _build_simple_system(self, ctx: UserContext | None) -> str:
        """构建简单对话的 system prompt"""
        base = (
            "你是 BHP 行为健康促进平台的AI助手。\n"
            "请用温暖、鼓励的语气与用户交流。\n"
            "回复简洁, 控制在100字以内。"
        )
        if ctx:
            base += f"\n\n用户当前行为阶段: {ctx.behavioral_stage}"
            if ctx.spi_score:
                base += f", SPI评分: {ctx.spi_score}"
        return base

    def _log_turn(
        self,
        user_id: int,
        message: str,
        intent: str,
        answer: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        latency: int,
        sources: list,
        used_rag: bool = False,
    ):
        self._turn_counter += 1
        turn = ConversationTurn(
            turn_id=self._turn_counter,
            user_id=user_id,
            timestamp=datetime.now(),
            user_message=message,
            intent=intent,
            assistant_message=answer,
            model_used=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_yuan=cost,
            latency_ms=latency,
            rag_sources=sources,
            used_rag=used_rag,
        )
        self._conversation_log.append(turn)

        # 只保留最近 1000 条 (内存保护)
        if len(self._conversation_log) > 1000:
            self._conversation_log = self._conversation_log[-500:]


# ══════════════════════════════════════════════
# 便捷工厂
# ══════════════════════════════════════════════

def create_coach_agent(qdrant_url: str | None = None) -> CoachAgent:
    """一站式创建 CoachAgent"""
    return CoachAgent(qdrant_url=qdrant_url)
