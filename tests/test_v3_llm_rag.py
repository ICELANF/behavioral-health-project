"""
综合测试 — LLM/RAG 新模块 + 全量兼容性验证
运行: python tests/test_llm_rag.py

测试策略:
  - LLM/RAG 模块: Mock HTTP 调用, 验证逻辑正确性
  - 现有模块: 直接执行, 验证导入和核心函数无冲突
"""
import json
import os
import sys
import time

# 项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}: {detail}")


# ══════════════════════════════════════════════
# 1. LLM Client — 配置与结构
# ══════════════════════════════════════════════

def test_llm_client():
    print("\n━━━ 1. LLM Client ━━━")
    from core.llm.client import (
        LLMClient, LLMResponse, MODEL_REGISTRY,
        LLMProvider, ModelConfig, LLMTimeoutError, LLMAPIError,
    )

    # 模型注册表完整性
    check("registry has 6 models", len(MODEL_REGISTRY) == 6,
          f"got {len(MODEL_REGISTRY)}: {list(MODEL_REGISTRY.keys())}")

    expected = ["qwen3-max", "qwen-plus", "qwen-turbo",
                "text-embedding-v3", "deepseek-v3", "deepseek-v3-bailian"]
    for m in expected:
        check(f"model '{m}' registered", m in MODEL_REGISTRY)

    # 配置正确性
    cfg = MODEL_REGISTRY["qwen3-max"]
    check("qwen3-max provider=dashscope", cfg.provider == LLMProvider.DASHSCOPE)
    check("qwen3-max cost_input=2.5", cfg.cost_per_1m_input == 2.5)
    check("qwen3-max cost_output=10.0", cfg.cost_per_1m_output == 10.0)
    check("qwen3-max timeout=30", cfg.timeout == 30)

    cfg_ds = MODEL_REGISTRY["deepseek-v3"]
    check("deepseek-v3 provider=deepseek", cfg_ds.provider == LLMProvider.DEEPSEEK)
    check("deepseek-v3 base_url has deepseek.com",
          "deepseek.com" in cfg_ds.base_url)

    # LLMResponse 结构
    resp = LLMResponse(
        content="测试回复",
        model="qwen-plus",
        provider="dashscope",
        input_tokens=100,
        output_tokens=50,
        latency_ms=500,
        cost_yuan=0.003,
    )
    check("response total_tokens=150", resp.total_tokens == 150)
    check("response content correct", resp.content == "测试回复")

    # 异常类
    err = LLMTimeoutError("qwen-plus", 15)
    check("timeout error message", "qwen-plus" in str(err))

    err2 = LLMAPIError("deepseek-v3", 429, "rate limited")
    check("api error has status", err2.status_code == 429)

    # Client 实例化
    client = LLMClient()
    check("client instantiation ok", client is not None)


# ══════════════════════════════════════════════
# 2. LLM Router — 路由逻辑
# ══════════════════════════════════════════════

def test_llm_router():
    print("\n━━━ 2. LLM Router ━━━")
    from core.llm.router import (
        LLMRouter, TaskComplexity, ROUTING_TABLE,
        INTENT_COMPLEXITY, UsageStats,
    )
    from core.llm.client import LLMClient

    # 路由表完整性
    check("3 complexity levels",
          set(ROUTING_TABLE.keys()) == {"simple", "medium", "complex"})

    check("simple chain starts with qwen-turbo",
          ROUTING_TABLE["simple"][0] == "qwen-turbo")
    check("complex chain starts with qwen3-max",
          ROUTING_TABLE["complex"][0] == "qwen3-max")
    check("complex has 4 fallback models",
          len(ROUTING_TABLE["complex"]) == 4)

    # 意图映射
    check("greeting → simple",
          INTENT_COMPLEXITY["greeting"] == TaskComplexity.SIMPLE)
    check("coach_dialogue → complex",
          INTENT_COMPLEXITY["coach_dialogue"] == TaskComplexity.COMPLEX)
    check("knowledge_qa → medium",
          INTENT_COMPLEXITY["knowledge_qa"] == TaskComplexity.MEDIUM)

    total_intents = len(INTENT_COMPLEXITY)
    check(f"total {total_intents} intents mapped", total_intents >= 11)

    # Router 分类逻辑
    router = LLMRouter(LLMClient())

    check("intent=greeting → simple",
          router.classify_complexity(intent="greeting") == "simple")
    check("intent=diagnostic_report → complex",
          router.classify_complexity(intent="diagnostic_report") == "complex")
    check("message='好的' → simple",
          router.classify_complexity(message="好的") == "simple")
    check("message='请帮我诊断行为阶段' → complex",
          router.classify_complexity(message="请帮我诊断一下我的行为阶段") == "complex")
    check("message='今天天气不错' → medium",
          router.classify_complexity(message="今天天气不错,我想聊聊天") == "medium")

    # UsageStats
    from core.llm.client import LLMResponse
    stats = UsageStats()
    mock_resp = LLMResponse(
        content="test", model="qwen-plus", provider="dashscope",
        input_tokens=100, output_tokens=50, cost_yuan=0.003, latency_ms=200,
    )
    stats.record(mock_resp, fell_back=False)
    stats.record(mock_resp, fell_back=True)

    summary = stats.summary()
    check("stats total_calls=2", summary["total_calls"] == 2)
    check("stats fallback_rate=0.5", summary["fallback_rate"] == 0.5)
    check("stats cost tracked", summary["total_cost_yuan"] == 0.006)


# ══════════════════════════════════════════════
# 3. Vector Store — Qdrant 操作 (Mock)
# ══════════════════════════════════════════════

def test_vector_store():
    print("\n━━━ 3. Vector Store ━━━")
    from core.rag.vector_store import QdrantStore, SearchResult, EMBEDDING_DIM

    check("default embedding dim=1024", EMBEDDING_DIM == 1024)

    store = QdrantStore(base_url="http://localhost:6333")
    check("store instantiation ok", store.collection == "bhp_knowledge")
    check("custom collection",
          QdrantStore(collection="test").collection == "test")

    # SearchResult
    sr = SearchResult(
        chunk_id="spec_0001",
        score=0.87,
        text="SPI是行为准备度指数",
        metadata={"source": "spec.md", "doc_type": "spec"},
    )
    check("search result score", sr.score == 0.87)
    check("search result metadata", sr.metadata["source"] == "spec.md")


# ══════════════════════════════════════════════
# 4. Knowledge Loader — 文本切分
# ══════════════════════════════════════════════

def test_knowledge_loader():
    print("\n━━━ 4. Knowledge Loader ━━━")
    from core.rag.knowledge_loader import TextChunker, KnowledgeLoader, TextChunk

    chunker = TextChunker(chunk_size=200, chunk_overlap=30, min_chunk_size=20)

    # Markdown 切分
    md_text = """# 第一章 概述
这是概述内容。BHP 系统是行为健康促进平台。

## 1.1 SPI 评分
SPI (Success Prediction Index) 是衡量行为改变成功可能性的综合指标。
分值范围 0-100, 越高越好。

低于 30 分说明准备度极低, 需要从动机激发开始。

## 1.2 行为阶段
TTM 模型将行为改变分为 S0-S6 七个阶段。

S0: 前意识期, 尚未意识到问题。
S1: 意识期, 开始思考改变。
"""
    chunks = chunker.chunk_markdown(md_text, "spec.md", "spec")
    check(f"markdown → {len(chunks)} chunks", len(chunks) >= 2)
    check("first chunk source=spec.md", chunks[0].source == "spec.md")
    check("chunks have section titles",
          any(c.section for c in chunks))
    check("chunk IDs are unique",
          len(set(c.chunk_id for c in chunks)) == len(chunks))

    # 策略 JSON 切分
    strategies = [
        {"readiness_level": "L1", "category": "intrinsic", "technique": "动机式访谈",
         "script_zh": "我注意到你开始思考健康问题了,这很好。能跟我说说是什么让你开始想这个的吗?"},
        {"readiness_level": "L3", "category": "capability", "technique": "目标设定",
         "script_zh": "你已经准备好行动了!我们来一起设定一个小目标。"},
    ]
    strategy_chunks = chunker.chunk_strategies(strategies, "strategies.json")
    check("strategies → 2 chunks", len(strategy_chunks) == 2)
    check("strategy chunk has readiness",
          "L1" in strategy_chunks[0].text)
    check("strategy doc_type=strategy",
          strategy_chunks[0].doc_type == "strategy")

    # 纯文本切分
    plain = "短文本。" * 5
    plain_chunks = chunker.chunk_plain_text(plain, "test.txt", "faq")
    check("plain text chunked", len(plain_chunks) >= 1)

    # TextChunk.to_payload
    payload = chunks[0].to_payload()
    check("payload has text", "text" in payload)
    check("payload has source", payload["source"] == "spec.md")
    check("payload has doc_type", payload["doc_type"] == "spec")

    # doc type guessing
    loader_cls = KnowledgeLoader.__new__(KnowledgeLoader)
    check("guess strategy file",
          loader_cls._guess_doc_type("intervention_strategies.json") == "strategy")
    check("guess tcm file",
          loader_cls._guess_doc_type("中医体质.md") == "tcm")
    check("guess clinical file",
          loader_cls._guess_doc_type("代谢管理指南.md") == "clinical")
    check("guess default=spec",
          loader_cls._guess_doc_type("unknown.md") == "spec")


# ══════════════════════════════════════════════
# 5. RAG Pipeline — 结构 & 上下文构建
# ══════════════════════════════════════════════

def test_rag_pipeline():
    print("\n━━━ 5. RAG Pipeline ━━━")
    from core.rag.pipeline import (
        RAGPipeline, RAGConfig, RAGResult,
        SYSTEM_KNOWLEDGE_QA, SYSTEM_COACH_WITH_PROFILE, SYSTEM_PRESCRIPTION,
    )
    from core.rag.vector_store import SearchResult

    # Prompt 模板
    check("knowledge_qa prompt exists", len(SYSTEM_KNOWLEDGE_QA) > 50)
    check("coach prompt has {user_profile}",
          "{user_profile}" in SYSTEM_COACH_WITH_PROFILE)
    check("prescription prompt has {rag_context}",
          "{rag_context}" in SYSTEM_PRESCRIPTION)

    # RAGConfig
    config = RAGConfig()
    check("default top_k=5", config.top_k == 5)
    check("default score_threshold=0.35", config.score_threshold == 0.35)
    check("default max_context_chars=3000", config.max_context_chars == 3000)

    # _build_context (无需 API)
    from core.llm.client import LLMClient
    from core.llm.router import LLMRouter
    from core.rag.vector_store import QdrantStore

    pipeline = RAGPipeline(LLMClient(), LLMRouter(), QdrantStore(), config)

    mock_results = [
        SearchResult("c1", 0.9, "SPI是行为准备度指数, 范围0-100",
                     {"source": "spec.md", "section": "SPI评分"}),
        SearchResult("c2", 0.8, "低于30分需要从动机激发开始",
                     {"source": "spec.md", "section": "SPI评分"}),
        SearchResult("c3", 0.6, "TTM模型有7个阶段",
                     {"source": "spec.md", "section": "行为阶段"}),
    ]
    context = pipeline._build_context(mock_results)
    check("context contains SPI", "SPI" in context)
    check("context contains source ref", "spec.md" in context)
    check("context within char limit", len(context) <= config.max_context_chars + 200)

    # 空结果
    empty_ctx = pipeline._build_context([])
    check("empty context has fallback message", "未找到" in empty_ctx)

    # _format_profile
    profile = {
        "behavioral_stage": "S3",
        "readiness_level": "L3",
        "spi_score": 65.0,
        "behavior_type": "approach",
        "top_obstacles": ["time", "motivation"],
    }
    fmt = pipeline._format_profile(profile)
    check("profile format has stage", "S3" in fmt)
    check("profile format has SPI", "65" in fmt)
    check("profile format has obstacles", "time" in fmt)

    # RAGResult
    result = RAGResult(
        answer="SPI 是衡量行为改变可能性的指标",
        sources=[{"chunk_id": "c1", "source": "spec.md", "score": 0.9}],
        query="什么是SPI",
        latency_ms=350,
    )
    d = result.to_dict()
    check("result.to_dict has answer", d["answer"] == result.answer)
    check("result.to_dict has latency", d["latency_ms"] == 350)


# ══════════════════════════════════════════════
# 6. Coach Agent — 集成逻辑
# ══════════════════════════════════════════════

def test_coach_agent():
    print("\n━━━ 6. Coach Agent ━━━")
    from core.llm.coach_agent import (
        CoachAgent, UserContext, ConversationTurn,
        RAG_INTENTS, QUICK_REPLIES, INTENT_CLASSIFY_PROMPT,
    )

    # RAG 意图集
    check("knowledge_qa is RAG intent", "knowledge_qa" in RAG_INTENTS)
    check("coach_dialogue is RAG intent", "coach_dialogue" in RAG_INTENTS)
    check("greeting is NOT RAG intent", "greeting" not in RAG_INTENTS)

    # Quick replies
    check("checkin has quick reply", "checkin_confirm" in QUICK_REPLIES)

    # Intent prompt
    check("classify prompt has {message}", "{message}" in INTENT_CLASSIFY_PROMPT)

    # UserContext
    ctx = UserContext(
        user_id=1,
        behavioral_stage="S3",
        readiness_level="L3",
        spi_score=65.0,
        bpt_type="approach",
        cultivation_stage="adaptation",
        growth_level="G2",
        streak_days=14,
        top_obstacles=["time_pressure", "low_motivation"],
        dominant_causes=["health_event", "family_concern"],
    )
    profile = ctx.to_profile_dict()
    check("profile dict has stage", profile["behavioral_stage"] == "S3")
    check("profile dict has obstacles", len(profile["top_obstacles"]) == 2)
    check("profile dict has growth_level", profile["growth_level"] == "G2")

    # from_pipeline_result (mock)
    from core.diagnostic_pipeline import DiagnosticPipeline
    pipeline = DiagnosticPipeline()
    pr = pipeline.run_minimal(user_id=42, behavioral_stage="S2",
                              trigger_strength=6, psychological_level=4)
    ctx2 = UserContext.from_pipeline_result(pr)
    check("ctx from pipeline: user_id=42", ctx2.user_id == 42)
    check("ctx from pipeline: stage=S2", ctx2.behavioral_stage == "S2")
    check("ctx from pipeline: spi > 0", ctx2.spi_score > 0)

    # ConversationTurn
    turn = ConversationTurn(
        turn_id=1, user_id=1, timestamp=__import__("datetime").datetime.now(),
        user_message="测试", intent="general_chat", assistant_message="回复",
        model_used="qwen-plus", input_tokens=50, output_tokens=30,
        cost_yuan=0.001, latency_ms=200,
    )
    db_dict = turn.to_db_dict()
    check("turn to_db_dict has model", db_dict["model_used"] == "qwen-plus")
    check("turn to_db_dict has cost", db_dict["cost_yuan"] == 0.001)


# ══════════════════════════════════════════════
# 7. Database Migration — 结构验证
# ══════════════════════════════════════════════

def test_migration():
    print("\n━━━ 7. Migration v3_003 ━━━")
    import sqlite3
    import tempfile, os
    from migrations.v3_003_llm_rag import upgrade, downgrade, _OpHelper

    # 在临时 DB 上执行迁移
    tmp = tempfile.mktemp(suffix=".db")
    conn = sqlite3.connect(tmp)
    op = _OpHelper(conn)

    upgrade(op)
    conn.commit()

    # 验证表存在
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [r[0] for r in cursor.fetchall()]
    check("llm_call_logs created", "llm_call_logs" in tables)
    check("rag_query_logs created", "rag_query_logs" in tables)
    check("knowledge_chunks created", "knowledge_chunks" in tables)

    # 验证字段 (通过 INSERT 测试)
    conn.execute("""
        INSERT INTO llm_call_logs
            (user_id, intent, complexity, model_requested, model_actual,
             provider, fell_back, input_tokens, output_tokens, cost_yuan, latency_ms)
        VALUES (1, 'knowledge_qa', 'medium', 'qwen3-max', 'qwen-plus',
                'dashscope', 1, 500, 200, 0.005, 1200)
    """)
    check("llm_call_logs insert ok", True)

    conn.execute("""
        INSERT INTO rag_query_logs
            (user_id, query_text, query_type, results_count, top_score, avg_score)
        VALUES (1, 'SPI评分', 'knowledge_qa', 5, 0.92, 0.75)
    """)
    check("rag_query_logs insert ok", True)

    conn.execute("""
        INSERT INTO knowledge_chunks
            (chunk_id, source, doc_type, section, seq, char_count, text_preview)
        VALUES ('spec_0001', 'spec.md', 'spec', 'SPI评分', 0, 200, 'SPI是...')
    """)
    check("knowledge_chunks insert ok", True)

    # 回滚
    downgrade(op)
    conn.commit()
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    tables_after = [r[0] for r in cursor.fetchall()]
    check("downgrade removes all 3 tables",
          "llm_call_logs" not in tables_after
          and "rag_query_logs" not in tables_after
          and "knowledge_chunks" not in tables_after)

    conn.close()
    os.unlink(tmp)


# ══════════════════════════════════════════════
# 8. 现有 15 模块兼容性 — 全量导入
# ══════════════════════════════════════════════

def test_existing_compatibility():
    print("\n━━━ 8. Existing Modules Compatibility ━━━")

    modules = [
        ("models_v3", "ChangeCauseCategory"),
        ("core.stage_mapping", "stage_resolver"),
        ("core.intervention_strategy_engine", "InterventionStrategyEngine"),
        ("core.intervention_tracker", "EffectivenessEvaluator"),
        ("core.incentive_integration", "PointEngine"),
        ("core.intervention_combinations", "EnhancedInterventionMatcher"),
        ("core.diagnostic_pipeline", "DiagnosticPipeline"),
        ("core.diagnostics.cognitive_assessment", "score_hbm"),
        ("core.diagnostics.capability_assessment", "score_comb"),
        ("core.diagnostics.support_assessment", "score_support_system"),
        ("core.diagnostics.layer3_report_generator", "Layer3DiagnosticReport"),
        ("baps.spi_calculator", "calculate_spi_full"),
        ("baps.cause_scoring", "score_change_causes"),
        ("baps.health_competency_assessment", "assess_health_competency"),
        ("baps.obstacle_assessment", "score_obstacles"),
        ("baps.progressive_assessment", "AdaptiveRecommender"),
        ("baps.urgency_assessment", "score_urgency"),
    ]

    for mod_name, attr_name in modules:
        try:
            mod = __import__(mod_name, fromlist=[attr_name])
            obj = getattr(mod, attr_name)
            check(f"{mod_name}.{attr_name}", obj is not None)
        except Exception as e:
            check(f"{mod_name}.{attr_name}", False, str(e))

    # 新模块也能正常导入
    new_modules = [
        ("core.llm.client", "LLMClient"),
        ("core.llm.router", "LLMRouter"),
        ("core.llm.coach_agent", "CoachAgent"),
        ("core.rag.vector_store", "QdrantStore"),
        ("core.rag.knowledge_loader", "KnowledgeLoader"),
        ("core.rag.pipeline", "RAGPipeline"),
    ]
    for mod_name, attr_name in new_modules:
        try:
            mod = __import__(mod_name, fromlist=[attr_name])
            obj = getattr(mod, attr_name)
            check(f"NEW {mod_name}.{attr_name}", obj is not None)
        except Exception as e:
            check(f"NEW {mod_name}.{attr_name}", False, str(e))


# ══════════════════════════════════════════════
# 9. 端到端集成 — DiagnosticPipeline → CoachAgent
# ══════════════════════════════════════════════

def test_e2e_integration():
    print("\n━━━ 9. End-to-End Integration ━━━")
    from core.diagnostic_pipeline import DiagnosticPipeline
    from core.llm.coach_agent import UserContext

    # 完整管道 → 用户上下文
    pipeline = DiagnosticPipeline()
    pr = pipeline.run_full(
        user_id=100,
        layer1_input={
            "behavioral_stage": "S3",
            "bpt_type": "approach",
        },
        layer2_input={
            "trigger_strength": 7,
            "psychological_level": 4,
            "capability_resource": 6,
            "social_support": 7,
            "urgency_val": 6,
        },
        growth_level="G2",
        streak_days=21,
        cultivation_stage="adaptation",
    )

    ctx = UserContext.from_pipeline_result(pr)
    check("e2e: stage=S3", ctx.behavioral_stage == "S3")
    check("e2e: spi > 0", ctx.spi_score > 0)
    check("e2e: cultivation=adaptation", ctx.cultivation_stage == "adaptation")

    # profile dict → RAG pipeline 可接受
    profile = ctx.to_profile_dict()
    check("e2e: profile has 10 keys", len(profile) >= 10)
    check("e2e: profile behavioral_stage=S3",
          profile["behavioral_stage"] == "S3")

    # 验证 incentive 集成未被破坏
    from core.incentive_integration import get_rx_context_from_incentive
    rx_ctx = get_rx_context_from_incentive("G2", 21, {})
    check("e2e: G2 available modes include challenge",
          "challenge" in rx_ctx["available_rx_modes"])
    check("e2e: G2+21days boost > 1.0",
          rx_ctx["rx_intensity_boost"] > 1.0)


# ══════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("BHP v3 LLM/RAG Module Tests")
    print("=" * 60)

    t0 = time.time()

    test_llm_client()
    test_llm_router()
    test_vector_store()
    test_knowledge_loader()
    test_rag_pipeline()
    test_coach_agent()
    test_migration()
    test_existing_compatibility()
    test_e2e_integration()

    elapsed = time.time() - t0

    print("\n" + "=" * 60)
    print(f"Results: {PASS} passed, {FAIL} failed ({elapsed:.2f}s)")
    print("=" * 60)

    if FAIL > 0:
        sys.exit(1)
