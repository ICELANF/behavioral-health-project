"""
API 层测试 — 路由注册 + Schema 验证 + 端点结构
运行: python tests/test_api.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置测试环境变量
os.environ.setdefault("DATABASE_URL", "sqlite:///test_api.db")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("DASHSCOPE_API_KEY", "test-key")

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
# 1. Schema 验证
# ══════════════════════════════════════════════

def test_schemas():
    print("\n━━━ 1. Pydantic Schemas ━━━")
    from api.schemas import (
        APIResponse, DiagnosticMinimalRequest, DiagnosticFullRequest,
        ChatRequest, ChatMessage, ChatResponse,
        KnowledgeQueryRequest, PrescriptionRequest,
        BatchSubmitRequest, DailyOutcomeRequest,
        CheckinRequest, TaskCompleteRequest,
        Layer1Input, Layer2Input, Layer3Input,
    )

    # APIResponse
    resp = APIResponse(ok=True, data={"test": 1}, message="ok")
    check("APIResponse serializes", resp.model_dump()["ok"] is True)

    # DiagnosticMinimalRequest 验证
    req = DiagnosticMinimalRequest(user_id=1, behavioral_stage="S3")
    check("minimal request defaults", req.trigger_strength == 5)

    try:
        DiagnosticMinimalRequest(user_id=1, behavioral_stage="X9")
        check("minimal rejects invalid stage", False, "should have raised")
    except Exception:
        check("minimal rejects invalid stage", True)

    # ChatRequest
    chat = ChatRequest(user_id=1, message="你好")
    check("chat request ok", chat.message == "你好")

    chat_with_history = ChatRequest(
        user_id=1,
        message="继续",
        history=[
            ChatMessage(role="user", content="你好"),
            ChatMessage(role="assistant", content="你好！"),
        ],
    )
    check("chat with history", len(chat_with_history.history) == 2)

    # ChatResponse
    cr = ChatResponse(answer="test", intent="greeting", model="qwen-plus")
    check("chat response defaults", cr.tokens == 0)

    # Layer inputs
    l1 = Layer1Input(behavioral_stage="S2", bpt_type="approach")
    check("layer1 input", l1.bpt_type == "approach")

    l2 = Layer2Input(trigger_strength=7, psychological_level=4)
    check("layer2 quick input", l2.part1_scores is None)

    l2_full = Layer2Input(
        part1_scores={"health_event": 8, "family_concern": 6},
        part2_scores=[3, 4, 5, 4, 3],
        part3_scores={"time_pressure": 7},
    )
    check("layer2 full input", l2_full.part1_scores is not None)

    # Prescription
    rx = PrescriptionRequest(
        user_id=1,
        behavioral_stage="S3",
        top_obstacles=["time_pressure"],
        dominant_causes=["health_event"],
    )
    check("prescription request", len(rx.top_obstacles) == 1)

    # DailyOutcome
    do = DailyOutcomeRequest(user_id=1, tasks_assigned=5, tasks_completed=3)
    check("daily outcome defaults", do.streak_days == 0)


# ══════════════════════════════════════════════
# 2. FastAPI App 构建
# ══════════════════════════════════════════════

def test_app_creation():
    print("\n━━━ 2. FastAPI App Creation ━━━")
    from api.main import app

    check("app instance created", app is not None)
    check("app title", "BHP" in app.title)
    check("app version", app.version == "3.1.0")

    # 收集所有路由
    routes = []
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            routes.append((route.path, route.methods))

    route_paths = [r[0] for r in routes]
    check(f"total routes: {len(routes)}", len(routes) >= 15)

    # 核心端点存在
    expected_paths = [
        "/health",
        "/api/v3/diagnostic/minimal",
        "/api/v3/diagnostic/full",
        "/api/v3/chat/message",
        "/api/v3/chat/knowledge",
        "/api/v3/chat/knowledge/search",
        "/api/v3/chat/prescription",
        "/api/v3/chat/stats",
        "/api/v3/assessment/batches",
        "/api/v3/assessment/submit",
        "/api/v3/tracking/daily",
        "/api/v3/tracking/weekly-review",
        "/api/v3/incentive/checkin",
        "/api/v3/incentive/task-complete",
        "/api/v3/admin/knowledge/stats",
        "/api/v3/admin/knowledge/init",
        "/api/v3/status",
        "/api/v3/auth/register",
        "/api/v3/auth/login",
        "/api/v3/auth/me",
    ]
    for path in expected_paths:
        check(f"route {path}", path in route_paths, f"not found in {route_paths[:5]}...")


# ══════════════════════════════════════════════
# 3. 路由模块导入
# ══════════════════════════════════════════════

def test_router_imports():
    print("\n━━━ 3. Router Module Imports ━━━")
    modules = [
        ("api.routers.diagnostic", "router"),
        ("api.routers.chat", "router"),
        ("api.routers.assessment", "router"),
        ("api.routers.tracking", "router"),
        ("api.routers.incentive", "router"),
        ("api.routers.knowledge", "router"),
        ("api.routers.health", "router"),
    ]
    for mod_name, attr in modules:
        try:
            mod = __import__(mod_name, fromlist=[attr])
            r = getattr(mod, attr)
            check(f"{mod_name}", r is not None)
        except Exception as e:
            check(f"{mod_name}", False, str(e))


# ══════════════════════════════════════════════
# 4. 依赖注入
# ══════════════════════════════════════════════

def test_dependencies():
    print("\n━━━ 4. Dependencies ━━━")
    from api.dependencies import (
        get_llm_client, get_llm_router, get_qdrant_store,
        get_rag_pipeline, get_coach_agent, get_knowledge_loader,
        get_diagnostic_pipeline,
    )

    client = get_llm_client()
    check("llm_client singleton", client is get_llm_client())

    router = get_llm_router()
    check("llm_router singleton", router is get_llm_router())

    store = get_qdrant_store()
    check("qdrant_store singleton", store is get_qdrant_store())

    rag = get_rag_pipeline()
    check("rag_pipeline singleton", rag is get_rag_pipeline())

    agent = get_coach_agent()
    check("coach_agent singleton", agent is get_coach_agent())

    loader = get_knowledge_loader()
    check("knowledge_loader singleton", loader is get_knowledge_loader())

    pipeline = get_diagnostic_pipeline()
    check("diagnostic_pipeline new each time", pipeline is not get_diagnostic_pipeline())


# ══════════════════════════════════════════════
# 5. Database 模块
# ══════════════════════════════════════════════

def test_database():
    print("\n━━━ 5. Database Module ━━━")
    from api.database import engine, SessionLocal, get_db, Base

    check("engine created", engine is not None)
    check("session factory", SessionLocal is not None)

    # 测试 get_db generator
    gen = get_db()
    db = next(gen)
    check("get_db yields session", db is not None)
    try:
        next(gen)
    except StopIteration:
        check("get_db closes properly", True)


# ══════════════════════════════════════════════
# 6. Worker 模块
# ══════════════════════════════════════════════

def test_worker():
    print("\n━━━ 6. Celery Worker ━━━")
    from api.worker import celery_app, flush_llm_logs, generate_weekly_reviews

    check("celery app", celery_app is not None)
    check("celery timezone", celery_app.conf.timezone == "Asia/Shanghai")

    # Beat schedule
    schedule = celery_app.conf.beat_schedule
    check("flush-llm-logs scheduled", "flush-llm-logs" in schedule)
    check("weekly-reviews scheduled", "weekly-reviews" in schedule)

    # Task callable
    check("flush task exists", flush_llm_logs is not None)
    check("weekly task exists", generate_weekly_reviews is not None)


# ══════════════════════════════════════════════
# 7. Docker 配置文件
# ══════════════════════════════════════════════

def test_docker_files():
    print("\n━━━ 7. Docker Files ━━━")
    import pathlib
    base = pathlib.Path(__file__).parent.parent

    dockerfile = base / "Dockerfile"
    check("Dockerfile exists", dockerfile.exists())
    content = dockerfile.read_text()
    check("Dockerfile has python 3.12", "python:3.12" in content)
    check("Dockerfile has healthcheck", "HEALTHCHECK" in content)
    check("Dockerfile has non-root user", "useradd" in content)

    compose = base / "docker-compose.yml"
    check("docker-compose.yml exists", compose.exists())
    cc = compose.read_text()
    check("compose has postgres", "postgres:" in cc)
    check("compose has redis", "redis:" in cc)
    check("compose has qdrant", "qdrant:" in cc)
    check("compose has nginx", "nginx:" in cc)
    check("compose has bhp-api", "bhp-api:" in cc)
    check("compose has bhp-worker", "bhp-worker:" in cc)
    check("compose has health depends", "service_healthy" in cc)

    env_example = base / ".env.example"
    check(".env.example exists", env_example.exists())
    ec = env_example.read_text()
    check("env has DASHSCOPE_API_KEY", "DASHSCOPE_API_KEY" in ec)
    check("env has DEEPSEEK_API_KEY", "DEEPSEEK_API_KEY" in ec)
    check("env has DB_PASSWORD", "DB_PASSWORD" in ec)

    nginx_conf = base / "nginx" / "conf.d" / "default.conf"
    check("nginx config exists", nginx_conf.exists())
    nc = nginx_conf.read_text()
    check("nginx has rate limiting", "limit_req_zone" in nc)
    check("nginx has SSL config", "ssl_certificate" in nc)
    check("nginx has SPA fallback", "try_files" in nc)

    requirements = base / "requirements.txt"
    check("requirements.txt exists", requirements.exists())
    rc = requirements.read_text()
    check("requires fastapi", "fastapi" in rc)
    check("requires httpx", "httpx" in rc)
    check("requires sqlalchemy", "sqlalchemy" in rc)

    deploy = base / "deploy.sh"
    check("deploy.sh exists", deploy.exists())

    dockerignore = base / ".dockerignore"
    check(".dockerignore exists", dockerignore.exists())


# ══════════════════════════════════════════════
# 8. OpenAPI 结构
# ══════════════════════════════════════════════

def test_openapi():
    print("\n━━━ 8. OpenAPI Schema ━━━")
    from api.main import app

    schema = app.openapi()
    check("openapi version", schema["openapi"].startswith("3."))
    check("info title", "BHP" in schema["info"]["title"])

    paths = schema.get("paths", {})
    check(f"openapi paths count: {len(paths)}", len(paths) >= 15)

    # 检查 tag 分组
    tags_in_paths = set()
    for path_data in paths.values():
        for method_data in path_data.values():
            if isinstance(method_data, dict) and "tags" in method_data:
                tags_in_paths.update(method_data["tags"])

    expected_tags = ["诊断管道", "对话 & 知识", "渐进式评估", "效果追踪", "积分激励", "鉴权"]
    for tag in expected_tags:
        check(f"tag '{tag}' in openapi", tag in tags_in_paths,
              f"found: {tags_in_paths}")


# ══════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("BHP v3 API Layer Tests")
    print("=" * 60)

    t0 = time.time()

    test_schemas()
    test_app_creation()
    test_router_imports()
    test_dependencies()
    test_database()
    test_worker()
    test_docker_files()
    test_openapi()

    elapsed = time.time() - t0

    print("\n" + "=" * 60)
    print(f"Results: {PASS} passed, {FAIL} failed ({elapsed:.2f}s)")
    print("=" * 60)

    # 清理测试 DB
    import pathlib
    test_db = pathlib.Path("test_api.db")
    if test_db.exists():
        test_db.unlink()

    if FAIL > 0:
        sys.exit(1)
