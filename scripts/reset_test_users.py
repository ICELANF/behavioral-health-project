# -*- coding: utf-8 -*-
"""
重置测试用户脚本
Reset Test Users Script

清除测试用户的关联数据并重置 User 列为初始值，用于测试前环境准备。

用法:
    python scripts/reset_test_users.py                       # 重置全部8个测试用户
    python scripts/reset_test_users.py --users coach grower  # 只重置指定用户
    python scripts/reset_test_users.py --dry-run             # 只显示将清除的数据量
"""

import argparse
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import SessionLocal, engine
from core.models import User
from loguru import logger

# ── 8 个测试用户名 ──────────────────────────────────────────
ALL_TEST_USERNAMES = [
    "observer", "grower", "sharer", "coach",
    "promoter", "supervisor", "master", "admin",
]

# ── User 列重置值 ──────────────────────────────────────────
RESET_FIELDS = {
    "health_competency_level": "Lv0",
    "current_stage": "S0",
    "growth_level": "G0",
    "agency_mode": "passive",
    "agency_score": 0.0,
    "trust_score": 0.0,
    "coach_intent": False,
    "conversion_type": None,
    "conversion_source": None,
    "adherence_rate": 0.0,
    "last_assessment_date": None,
    "profile": "{}",  # JSON 字面量, 通过 raw SQL 写入
}

# ── 要清除的子表 (分组) ────────────────────────────────────
# 格式: (table_name, fk_column)
# 默认 fk_column = "user_id", 特殊表另行指定

SUB_TABLES = [
    # A 组 — 学习/积分 (测试最常 "变脏")
    ("learning_time_logs", "user_id"),
    ("learning_points_logs", "user_id"),
    ("learning_progress", "user_id"),
    ("user_credits", "user_id"),
    ("point_transactions", "user_id"),
    ("user_points", "user_id"),
    ("user_point_balances", "user_id"),
    ("user_badges", "user_id"),
    ("user_milestones", "user_id"),
    ("user_streaks", "user_id"),
    ("user_memorials", "user_id"),
    ("user_rewards", "user_id"),

    # B 组 — 评估/任务
    ("assessment_sessions", "user_id"),
    ("assessments", "user_id"),
    ("micro_action_logs", "user_id"),
    ("micro_action_tasks", "user_id"),
    ("daily_tasks", "user_id"),

    # C 组 — 对话/消息
    # chat_messages 通过 session_id→chat_sessions 关联, 单独处理
    ("chat_sessions", "user_id"),
    ("reminders", "user_id"),

    # D 组 — 设备数据
    ("glucose_readings", "user_id"),
    ("heart_rate_readings", "user_id"),
    ("hrv_readings", "user_id"),
    ("sleep_records", "user_id"),
    ("activity_records", "user_id"),
    ("workout_records", "user_id"),
    ("vital_signs", "user_id"),
    ("device_alerts", "user_id"),
    ("user_devices", "user_id"),

    # E 组 — V4.0 旅程
    ("journey_states", "user_id"),
    ("trust_score_logs", "user_id"),
    ("agency_score_logs", "user_id"),
    ("observer_quota_logs", "user_id"),

    # F 组 — 社交/晋级
    ("challenge_enrollments", "user_id"),
]

# 特殊表: 使用非 user_id 外键, 单独处理
COMPANION_TABLE = "companion_relations"  # mentor_id OR mentee_id
COACH_MESSAGES_TABLE = "coach_schema.coach_messages"  # coach_id OR student_id


def _get_user_columns(db):
    """查询 users 表实际存在的列名"""
    rows = db.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'users' AND table_schema = 'public'"
    )).fetchall()
    return {r[0] for r in rows}


def _resolve_user_ids(db, usernames):
    """查询用户名 → id 映射"""
    rows = db.execute(
        text("SELECT id, username FROM users WHERE username = ANY(:names)"),
        {"names": usernames},
    ).fetchall()
    return {r.username: r.id for r in rows}


def _count_rows(db, table, fk_col, uid):
    """统计某表中指定用户的行数"""
    try:
        row = db.execute(
            text(f"SELECT count(*) AS cnt FROM {table} WHERE {fk_col} = :uid"),
            {"uid": uid},
        ).fetchone()
        return row.cnt
    except Exception:
        return -1  # 表不存在


def _count_dual_fk(db, table, fk_a, fk_b, uid):
    """统计双外键表中涉及该用户的行数"""
    try:
        row = db.execute(
            text(f"SELECT count(*) AS cnt FROM {table} "
                 f"WHERE {fk_a} = :uid OR {fk_b} = :uid"),
            {"uid": uid},
        ).fetchone()
        return row.cnt
    except Exception:
        return -1


def dry_run(db, user_map):
    """只显示将要清除的数据量，不实际删除"""
    logger.info("[DRY-RUN] 以下为将要清除的数据量:")
    total = 0
    for uname, uid in sorted(user_map.items(), key=lambda x: x[1]):
        user_total = 0
        logger.info(f"\n  === {uname} (id={uid}) ===")
        # chat_messages (via session_id)
        try:
            row = db.execute(
                text("SELECT count(*) AS cnt FROM chat_messages WHERE session_id IN "
                     "(SELECT id FROM chat_sessions WHERE user_id = :uid)"),
                {"uid": uid},
            ).fetchone()
            if row.cnt > 0:
                logger.info(f"    chat_messages: {row.cnt} 行")
                user_total += row.cnt
        except Exception:
            logger.warning(f"    chat_messages: (表不存在)")
        for tbl, fk in SUB_TABLES:
            cnt = _count_rows(db, tbl, fk, uid)
            if cnt > 0:
                logger.info(f"    {tbl}: {cnt} 行")
                user_total += cnt
            elif cnt == -1:
                logger.warning(f"    {tbl}: (表不存在)")
        # 特殊双外键表
        for tbl, fk_a, fk_b in [
            (COACH_MESSAGES_TABLE, "coach_id", "student_id"),
            (COMPANION_TABLE, "mentor_id", "mentee_id"),
        ]:
            cnt = _count_dual_fk(db, tbl, fk_a, fk_b, uid)
            if cnt > 0:
                logger.info(f"    {tbl}: {cnt} 行")
                user_total += cnt
            elif cnt == -1:
                logger.warning(f"    {tbl}: (表不存在)")
        logger.info(f"    小计: {user_total} 行")
        total += user_total
    logger.info(f"\n  总计将清除: {total} 行")
    return total


def reset_users(db, user_map):
    """执行重置：清除子表 + 重置 User 列"""
    grand_total = 0

    for uname, uid in sorted(user_map.items(), key=lambda x: x[1]):
        user_total = 0
        logger.info(f"\n{'='*50}")
        logger.info(f"重置用户: {uname} (id={uid})")
        logger.info(f"{'='*50}")

        def _safe_delete(sql_str, params, label):
            """Execute DELETE inside a SAVEPOINT so failures don't roll back prior work."""
            nonlocal user_total
            try:
                nested = db.begin_nested()
                result = db.execute(text(sql_str), params)
                deleted = result.rowcount
                nested.commit()
                if deleted > 0:
                    logger.info(f"  {label}: 删除 {deleted} 行")
                    user_total += deleted
            except Exception as e:
                nested.rollback()
                logger.warning(f"  {label}: 跳过 ({e})")

        # 1a) chat_messages (FK via session_id → chat_sessions.user_id)
        _safe_delete(
            "DELETE FROM chat_messages WHERE session_id IN "
            "(SELECT id FROM chat_sessions WHERE user_id = :uid)",
            {"uid": uid}, "chat_messages",
        )

        # 1b) 清除子表
        for tbl, fk in SUB_TABLES:
            _safe_delete(
                f"DELETE FROM {tbl} WHERE {fk} = :uid",
                {"uid": uid}, tbl,
            )

        # 特殊双外键表
        for tbl, fk_a, fk_b in [
            (COACH_MESSAGES_TABLE, "coach_id", "student_id"),
            (COMPANION_TABLE, "mentor_id", "mentee_id"),
        ]:
            _safe_delete(
                f"DELETE FROM {tbl} WHERE {fk_a} = :uid OR {fk_b} = :uid",
                {"uid": uid}, tbl,
            )

        # 2) 重置 User 列 (只更新实际存在的列)
        actual_cols = _get_user_columns(db)
        set_clauses = []
        params = {"uid": uid}
        skipped = []
        for col, val in RESET_FIELDS.items():
            if col not in actual_cols:
                skipped.append(col)
                continue
            param_name = f"v_{col}"
            if val is None:
                set_clauses.append(f"{col} = NULL")
            elif col == "profile":
                set_clauses.append(f"{col} = '{{}}'::jsonb")
            else:
                set_clauses.append(f"{col} = :{param_name}")
                params[param_name] = val

        if set_clauses:
            sql = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = :uid"
            db.execute(text(sql), params)
        reset_count = len(RESET_FIELDS) - len(skipped)
        logger.info(f"  users: 重置 {reset_count} 个字段")
        if skipped:
            logger.warning(f"  users: 跳过不存在的列: {skipped}")

        db.commit()
        logger.info(f"  小计清除: {user_total} 行")
        grand_total += user_total

    return grand_total


def main():
    parser = argparse.ArgumentParser(
        description="重置测试用户状态 (清除关联数据 + 重置 User 列)"
    )
    parser.add_argument(
        "--users", nargs="+", default=None,
        help=f"只重置指定用户 (可选: {', '.join(ALL_TEST_USERNAMES)})"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="只显示将清除的数据量，不实际删除"
    )
    args = parser.parse_args()

    target_usernames = args.users or ALL_TEST_USERNAMES

    # 验证用户名
    invalid = [u for u in target_usernames if u not in ALL_TEST_USERNAMES]
    if invalid:
        logger.error(f"无效的用户名: {invalid}")
        logger.info(f"可选用户: {ALL_TEST_USERNAMES}")
        sys.exit(1)

    logger.info("=" * 50)
    logger.info("测试用户重置脚本")
    logger.info(f"目标用户: {target_usernames}")
    logger.info(f"模式: {'DRY-RUN (只查看)' if args.dry_run else 'EXECUTE (实际删除)'}")
    logger.info("=" * 50)

    db = SessionLocal()
    try:
        # 查询用户 ID
        user_map = _resolve_user_ids(db, target_usernames)
        found = list(user_map.keys())
        missing = [u for u in target_usernames if u not in user_map]
        if missing:
            logger.warning(f"以下用户在数据库中不存在，跳过: {missing}")
        if not user_map:
            logger.error("没有找到任何目标用户，退出")
            sys.exit(1)

        logger.info(f"找到 {len(user_map)} 个用户: "
                     + ", ".join(f"{u}(id={uid})" for u, uid in user_map.items()))

        if args.dry_run:
            dry_run(db, user_map)
        else:
            total = reset_users(db, user_map)
            logger.info("\n" + "=" * 50)
            logger.info(f"重置完成! 共清除 {total} 行关联数据")
            logger.info(f"已重置 {len(user_map)} 个用户的 {len(RESET_FIELDS)} 个字段")
            logger.info("=" * 50)
    finally:
        db.close()


if __name__ == "__main__":
    main()
