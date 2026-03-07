#!/usr/bin/env python3
"""
一次性回填脚本：为已有 big5_scores 的 behavioral_profiles 填充 personality_archetype
运行：docker compose exec app python scripts/backfill_archetype.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://bhp_user:bhp_pass@localhost:5432/bhp_v3"
)

engine = create_engine(DATABASE_URL)


def classify_personality(scores: dict) -> str:
    E = scores.get("E", 0)
    N = scores.get("N", 0)
    C = scores.get("C", 0)
    A = scores.get("A", 0)
    O = scores.get("O", 0)

    if N >= 8 and (C >= 15 or A >= 30):
        return "P3"
    if N <= -15 and C >= 15:
        return "P1"
    if E >= 15 and N <= -5:
        return "P4"
    if O >= 15 and N <= -10:
        return "P2"
    if E <= -10:
        return "P5"
    if C >= 15:
        return "P1"
    if O >= 15:
        return "P2"
    if E >= 15:
        return "P4"
    return "P5"


def main():
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT id, user_id, big5_scores FROM behavioral_profiles "
            "WHERE big5_scores IS NOT NULL AND personality_archetype IS NULL"
        )).fetchall()

        print(f"Found {len(rows)} profiles to backfill")
        updated = 0

        for row in rows:
            bp_id, user_id, big5 = row
            if not big5 or not isinstance(big5, dict):
                continue

            raw = {}
            for dim in ("E", "N", "C", "A", "O"):
                val = big5.get(dim, {})
                raw[dim] = val.get("score", 0) if isinstance(val, dict) else 0

            p_type = classify_personality(raw)
            conn.execute(text(
                "UPDATE behavioral_profiles SET personality_archetype = :p WHERE id = :id"
            ), {"p": p_type, "id": bp_id})
            updated += 1
            print(f"  user={user_id}: big5={raw} -> {p_type}")

        conn.commit()
        print(f"\nDone: {updated}/{len(rows)} profiles updated")


if __name__ == "__main__":
    main()
