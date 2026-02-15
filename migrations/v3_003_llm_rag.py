"""
数据库迁移 v3_003 — LLM 调用日志 + RAG 查询日志
放置: api/migrations/v3_003_llm_rag.py

新增表:
  - llm_call_logs:  每次 LLM API 调用记录 (成本追踪/质量监控)
  - rag_query_logs: RAG 检索+生成记录 (检索质量追踪)
  - knowledge_chunks: 知识库 chunk 元数据 (同步 Qdrant 的索引)
"""

revision = "v3_003"
down_revision = "v3_002"


def upgrade(op):
    """正向迁移"""

    # ── 1. LLM 调用日志 ──
    op.create_table(
        "llm_call_logs",
        {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "user_id": "INTEGER",
            "session_id": "VARCHAR(64)",         # 对话会话ID
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "intent": "VARCHAR(32)",             # 意图标签
            "complexity": "VARCHAR(16)",          # simple/medium/complex
            "model_requested": "VARCHAR(64)",     # 路由请求的模型
            "model_actual": "VARCHAR(64)",        # 实际执行的模型 (可能降级)
            "provider": "VARCHAR(32)",            # dashscope/deepseek
            "fell_back": "BOOLEAN DEFAULT FALSE", # 是否经历降级
            "input_tokens": "INTEGER DEFAULT 0",
            "output_tokens": "INTEGER DEFAULT 0",
            "cost_yuan": "REAL DEFAULT 0",
            "latency_ms": "INTEGER DEFAULT 0",
            "finish_reason": "VARCHAR(32)",
            "user_message_preview": "TEXT",       # 用户消息前200字
            "assistant_message_preview": "TEXT",  # 回复前200字
            "error_message": "TEXT",              # 如有错误
        },
    )
    op.create_index(
        "ix_llm_call_logs_user_date",
        "llm_call_logs",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_llm_call_logs_model",
        "llm_call_logs",
        ["model_actual", "created_at"],
    )

    # ── 2. RAG 查询日志 ──
    op.create_table(
        "rag_query_logs",
        {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "user_id": "INTEGER",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "query_text": "TEXT",                 # 原始查询
            "query_type": "VARCHAR(32)",           # knowledge_qa/coach/prescription
            "doc_type_filter": "VARCHAR(32)",      # 文档类型过滤
            "top_k": "INTEGER DEFAULT 5",
            "results_count": "INTEGER DEFAULT 0",  # 实际返回条数
            "top_score": "REAL DEFAULT 0",         # 最高相似度
            "avg_score": "REAL DEFAULT 0",         # 平均相似度
            "sources_json": "TEXT",                # 来源列表 JSON
            "embedding_latency_ms": "INTEGER DEFAULT 0",
            "search_latency_ms": "INTEGER DEFAULT 0",
            "total_latency_ms": "INTEGER DEFAULT 0",
            "llm_call_log_id": "INTEGER",          # 关联的 LLM 日志ID
        },
    )
    op.create_index(
        "ix_rag_query_logs_user_date",
        "rag_query_logs",
        ["user_id", "created_at"],
    )

    # ── 3. 知识库 chunk 元数据 ──
    op.create_table(
        "knowledge_chunks",
        {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "chunk_id": "VARCHAR(128) UNIQUE NOT NULL",  # 与 Qdrant 同步
            "source": "VARCHAR(256) NOT NULL",            # 文件名
            "doc_type": "VARCHAR(32) NOT NULL",           # spec/strategy/tcm/...
            "section": "VARCHAR(256)",                     # 章节标题
            "seq": "INTEGER DEFAULT 0",
            "char_count": "INTEGER DEFAULT 0",
            "text_preview": "TEXT",                        # 前200字
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        },
    )
    op.create_index(
        "ix_knowledge_chunks_source",
        "knowledge_chunks",
        ["source", "doc_type"],
    )


def downgrade(op):
    """回滚"""
    op.drop_table("knowledge_chunks")
    op.drop_table("rag_query_logs")
    op.drop_table("llm_call_logs")


# ══════════════════════════════════════════════
# Alembic 兼容 + 独立执行
# ══════════════════════════════════════════════

class _OpHelper:
    """最小化 op 模拟, 用于 SQLite/PostgreSQL 直接执行"""

    def __init__(self, conn):
        self.conn = conn

    def create_table(self, name: str, columns: dict):
        cols = ", ".join(f"{k} {v}" for k, v in columns.items())
        self.conn.execute(f"CREATE TABLE IF NOT EXISTS {name} ({cols})")

    def create_index(self, name: str, table: str, columns: list):
        cols = ", ".join(columns)
        self.conn.execute(
            f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({cols})"
        )

    def drop_table(self, name: str):
        self.conn.execute(f"DROP TABLE IF EXISTS {name}")


def run_standalone(db_url: str = "sqlite:///bhp_v3.db"):
    """独立执行迁移 (不依赖 Alembic)"""
    import sqlite3
    conn = sqlite3.connect(db_url.replace("sqlite:///", ""))
    op = _OpHelper(conn)
    upgrade(op)
    conn.commit()
    conn.close()
    print(f"Migration v3_003 applied to {db_url}")


if __name__ == "__main__":
    run_standalone()
