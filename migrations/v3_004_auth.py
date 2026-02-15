"""
数据库迁移 v3_004 — 用户表 + JWT 鉴权字段
放置: api/migrations/v3_004_auth.py

说明:
  - 如果 users 表不存在 → 全量创建
  - 如果 users 表已存在 → 添加缺失列 (current_stage, growth_level 等)
"""

revision = "v3_004"
down_revision = "v3_003"


def upgrade(op):
    """正向迁移"""

    # 完整用户表 (幂等: IF NOT EXISTS)
    op.create_table(
        "users",
        {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "phone": "VARCHAR(20) UNIQUE NOT NULL",
            "password_hash": "VARCHAR(128) NOT NULL",
            "nickname": "VARCHAR(64) DEFAULT ''",
            "avatar_url": "VARCHAR(256) DEFAULT ''",
            "role": "VARCHAR(32) DEFAULT 'user'",
            "is_active": "BOOLEAN DEFAULT TRUE",
            "health_competency_level": "VARCHAR(4) DEFAULT 'Lv0'",
            "current_stage": "VARCHAR(4) DEFAULT 'S0'",
            "growth_level": "VARCHAR(4) DEFAULT 'G0'",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "last_login_at": "DATETIME",
        },
    )
    op.create_index("ix_users_phone", "users", ["phone"])
    op.create_index("ix_users_role", "users", ["role"])

    # 尝试添加 v3.1 扩展字段 (已有则跳过)
    for col_name, col_def in [
        ("current_stage", "VARCHAR(4) DEFAULT 'S0'"),
        ("growth_level", "VARCHAR(4) DEFAULT 'G0'"),
    ]:
        op.add_column_safe("users", col_name, col_def)


def downgrade(op):
    """回滚: 不删用户表 (数据重要), 只删扩展列"""
    for col in ["current_stage", "growth_level"]:
        op.drop_column_safe("users", col)


# ══════════════════════════════════════════════
# 独立执行
# ══════════════════════════════════════════════

class _OpHelper:
    """最小化 op 模拟"""

    def __init__(self, conn):
        self.conn = conn

    def create_table(self, name: str, columns: dict):
        cols = ", ".join(f"{k} {v}" for k, v in columns.items())
        self.conn.execute(f"CREATE TABLE IF NOT EXISTS {name} ({cols})")

    def create_index(self, name: str, table: str, columns: list):
        cols = ", ".join(columns)
        self.conn.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({cols})")

    def add_column_safe(self, table: str, column: str, definition: str):
        """添加列, 已存在则跳过"""
        try:
            self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        except Exception:
            pass  # 已存在

    def drop_column_safe(self, table: str, column: str):
        """SQLite 不支持 DROP COLUMN, 此处仅标记"""
        pass

    def drop_table(self, name: str):
        self.conn.execute(f"DROP TABLE IF EXISTS {name}")


def run_standalone(db_url: str = "sqlite:///bhp_v3.db"):
    import sqlite3
    conn = sqlite3.connect(db_url.replace("sqlite:///", ""))
    op = _OpHelper(conn)
    upgrade(op)
    conn.commit()
    conn.close()
    print(f"Migration v3_004 applied to {db_url}")


if __name__ == "__main__":
    run_standalone()
