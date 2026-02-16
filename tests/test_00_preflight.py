"""
预飞检查 — 验证所有基础依赖是否就绪
运行: python tests/test_00_preflight.py

这是第一个该跑的测试: 如果这里不过，后面全不用试。
"""
import sys
import subprocess
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PASS = "✅"
FAIL = "❌"
WARN = "⚠️"
results = []       # (name, ok, msg, mandatory)
soft_results = []  # non-fatal checks (PostgreSQL/pgvector)


def check(name, ok, msg="", mandatory=True):
    status = PASS if ok else FAIL
    if mandatory:
        results.append((name, ok, msg))
    else:
        soft_results.append((name, ok, msg))
        if not ok:
            status = WARN
    print(f"  {status} {name}" + (f"  ({msg})" if msg else ""))
    return ok


def section(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")


# ──────────────────────────────────────────
# 1. Python 版本
# ──────────────────────────────────────────
section("1. Python 环境")
v = sys.version_info
check("Python >= 3.10", v >= (3, 10), f"当前: {v.major}.{v.minor}.{v.micro}")


# ──────────────────────────────────────────
# 2. 核心依赖
# ──────────────────────────────────────────
section("2. Python 核心依赖")

REQUIRED_PACKAGES = [
    ("sqlalchemy", "2.0", "ORM + async"),
    ("asyncpg", None, "PostgreSQL async driver"),
    ("alembic", None, "数据库迁移"),
    ("pydantic", "2.0", "数据验证"),
    ("fastapi", None, "Web框架"),
    ("uvicorn", None, "ASGI服务器"),
    ("yaml", None, "YAML解析 (pyyaml)"),
]

for pkg_name, min_ver, desc in REQUIRED_PACKAGES:
    try:
        mod = __import__(pkg_name)
        ver = getattr(mod, "__version__", "?")
        if min_ver and ver != "?" and ver < min_ver:
            check(f"{pkg_name} >= {min_ver}", False, f"当前: {ver}")
        else:
            check(f"{pkg_name}", True, f"v{ver}")
    except ImportError:
        check(f"{pkg_name}", False, f"未安装 — pip install {pkg_name}")


# ──────────────────────────────────────────
# 3. 知识库专用依赖
# ──────────────────────────────────────────
section("3. 知识库 RAG 依赖")

RAG_PACKAGES = [
    ("sentence_transformers", None, "Embedding模型 (sentence-transformers)", True),
    ("hashlib", None, "文件哈希 (内置)", True),
]

RAG_OPTIONAL = [
    ("pgvector", None, "pgvector Python 绑定 (仅PostgreSQL层需要)"),
]

for pkg_name, min_ver, desc, *_ in RAG_PACKAGES:
    try:
        mod = __import__(pkg_name)
        ver = getattr(mod, "__version__", "内置")
        check(f"{pkg_name}", True, f"{desc} v{ver}")
    except ImportError:
        check(f"{pkg_name}", False, f"未安装 — {desc}")

for pkg_name, min_ver, desc in RAG_OPTIONAL:
    try:
        mod = __import__(pkg_name)
        ver = getattr(mod, "__version__", "内置")
        check(f"{pkg_name}", True, f"{desc} v{ver}", mandatory=False)
    except ImportError:
        check(f"{pkg_name}", False, f"未安装 — {desc}", mandatory=False)

# 文档解析可选依赖
section("3b. 文档解析可选依赖")
OPTIONAL = [
    ("docx", "python-docx", "DOCX解析"),
    ("pypdf", "pypdf", "PDF解析 (推荐)"),
    ("PyPDF2", "PyPDF2", "PDF解析 (备选)"),
]
for import_name, pip_name, desc in OPTIONAL:
    try:
        __import__(import_name)
        check(f"{import_name}", True, desc)
    except ImportError:
        print(f"  {WARN} {import_name} 未安装 (可选, 仅 {desc} 时需要)")


# ──────────────────────────────────────────
# 4. PostgreSQL + pgvector
# ──────────────────────────────────────────
section("4. PostgreSQL 连接")

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    # 尝试常见默认值
    DATABASE_URL = "postgresql://bhp_user:bhp_password@host.docker.internal:5432/bhp_db"
    print(f"  {WARN} DATABASE_URL 未设置, 尝试默认: {DATABASE_URL}")

try:
    import asyncio
    import asyncpg

    async def check_pg():
        # 从 SQLAlchemy URL 提取 asyncpg URL
        pg_url = DATABASE_URL.replace("postgresql://", "").replace("postgresql+asyncpg://", "")
        parts = pg_url.split("@")
        if len(parts) == 2:
            user_pass = parts[0]
            host_db = parts[1]
        else:
            return False, "URL格式错误"

        try:
            conn = await asyncpg.connect(DATABASE_URL.replace("postgresql://", "postgresql://").replace("+asyncpg", ""))

            # PostgreSQL 版本
            ver = await conn.fetchval("SELECT version()")
            check("PostgreSQL 连接", True, ver.split(",")[0] if ver else "?", mandatory=False)

            # pgvector 扩展
            ext = await conn.fetchval("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            if ext:
                check("pgvector 扩展", True, f"v{ext}", mandatory=False)
            else:
                check("pgvector 扩展", False, "未安装 — 运行: CREATE EXTENSION vector;", mandatory=False)

            # 检查知识库表是否存在
            tables = await conn.fetch("""
                SELECT tablename FROM pg_tables
                WHERE tablename IN ('knowledge_documents', 'knowledge_chunks', 'knowledge_domains', 'knowledge_citations')
            """)
            table_names = [r['tablename'] for r in tables]
            if len(table_names) == 4:
                check("知识库4张表", True, ", ".join(table_names), mandatory=False)
            elif len(table_names) > 0:
                check("知识库表 (部分)", False, f"仅有: {', '.join(table_names)}", mandatory=False)
            else:
                check("知识库表", False, "未创建 — 运行 Alembic 迁移", mandatory=False)

            # 检查租户表
            tenant_tables = await conn.fetch("""
                SELECT tablename FROM pg_tables
                WHERE tablename IN ('expert_tenants', 'tenant_clients', 'tenant_agent_mappings', 'tenant_audit_logs')
            """)
            t_names = [r['tablename'] for r in tenant_tables]
            if len(t_names) == 4:
                check("租户4张表", True, ", ".join(t_names), mandatory=False)
            else:
                check("租户表", False, f"仅有: {', '.join(t_names) if t_names else '无'} (需要: expert_tenants, tenant_clients, tenant_agent_mappings, tenant_audit_logs)", mandatory=False)

            await conn.close()
            return True, ""
        except Exception as e:
            check("PostgreSQL 连接", False, str(e)[:100], mandatory=False)
            return False, str(e)

    asyncio.run(check_pg())
except ImportError:
    check("PostgreSQL 检查", False, "asyncpg 未安装", mandatory=False)
except Exception as e:
    check("PostgreSQL 检查", False, str(e)[:100], mandatory=False)


# ──────────────────────────────────────────
# 5. Embedding 模型
# ──────────────────────────────────────────
section("5. Embedding 模型可用性")

try:
    from sentence_transformers import SentenceTransformer
    import torch

    check("PyTorch", True, f"v{torch.__version__}")

    # 检查模型是否已缓存
    from pathlib import Path
    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
    cached_models = list(cache_dir.glob("models--*")) if cache_dir.exists() else []

    chinese_models = [
        "shibing624/text2vec-base-chinese",
        "BAAI/bge-base-zh-v1.5",
    ]

    found = False
    for m in chinese_models:
        safe_name = "models--" + m.replace("/", "--")
        if any(safe_name in str(p) for p in cached_models):
            check(f"模型已缓存: {m}", True)
            found = True
            break

    if not found:
        print(f"  {WARN} 中文 Embedding 模型未缓存，首次运行将自动下载 (~400MB)")
        print(f"       预下载: python -c \"from sentence_transformers import SentenceTransformer; SentenceTransformer('shibing624/text2vec-base-chinese')\"")

except ImportError:
    check("sentence-transformers", False, "未安装")


# ──────────────────────────────────────────
# 汇总
# ──────────────────────────────────────────
section("汇总")
total = len(results)
passed = sum(1 for _, ok, _ in results if ok)
failed = total - passed

soft_total = len(soft_results)
soft_passed = sum(1 for _, ok, _ in soft_results if ok)
soft_failed = soft_total - soft_passed

print(f"\n  必需检查: {passed}/{total} 通过")
if soft_total > 0:
    print(f"  可选检查: {soft_passed}/{soft_total} 通过 (PostgreSQL/pgvector, 不阻塞)")
if failed > 0:
    print(f"\n  {FAIL} 以下必需项需要修复后再继续:")
    for name, ok, msg in results:
        if not ok:
            print(f"     → {name}: {msg}")
    if __name__ == "__main__":
        sys.exit(1)
else:
    if soft_failed > 0:
        print(f"\n  {WARN} 以下可选项未通过 (Layer 2/5 数据库测试将跳过):")
        for name, ok, msg in soft_results:
            if not ok:
                print(f"     → {name}: {msg}")
    print(f"\n  {PASS} 所有必需预飞检查通过! 可以继续后续测试。")
    if __name__ == "__main__":
        sys.exit(0)
