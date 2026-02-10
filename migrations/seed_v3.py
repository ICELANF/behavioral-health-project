"""
v3.1 种子数据加载器 — 运行一次即可
用法: python -m migrations.seed_v3
"""
import json
import os
from pathlib import Path
from sqlalchemy.orm import Session

# 导入项目数据库和v3模型
from v3.database import SessionLocal, engine
from v3.models import ChangeCause, InterventionStrategy, Base

CONFIGS_DIR = Path(__file__).parent.parent / "configs"


def seed_change_causes(db: Session) -> int:
    """加载 24 条改变动因"""
    fp = CONFIGS_DIR / "change_causes.json"
    with open(fp, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    for item in data:
        exists = db.query(ChangeCause).filter_by(id=item["id"]).first()
        if not exists:
            db.add(ChangeCause(
                id=item["id"],
                category=item["category"],
                name_zh=item["name_zh"],
                name_en=item["name_en"],
                assessment_question=item["question"],
                weight=item.get("weight", 1.0),
            ))
            count += 1

    db.commit()
    return count


def backfill_readiness_level(db: Session) -> int:
    """为 intervention_strategies 表补填 readiness_level (P→L)"""
    from core.stage_mapping import P_TO_L_MAP

    rows = db.query(InterventionStrategy).filter(
        InterventionStrategy.readiness_level.is_(None)
    ).all()

    for row in rows:
        row.readiness_level = P_TO_L_MAP.get(row.stage_code, "L1")

    db.commit()
    return len(rows)


def seed_intervention_strategies(db: Session) -> int:
    """加载干预策略种子数据 (L1-L5 × C1-C24 代表性条目)"""
    fp = CONFIGS_DIR / "intervention_strategies.json"
    with open(fp, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    for item in data:
        exists = db.query(InterventionStrategy).filter_by(
            stage_code=item["stage_code"],
            cause_code=item["cause_code"],
        ).first()
        if not exists:
            db.add(InterventionStrategy(
                stage_code=item["stage_code"],
                readiness_level=item.get("readiness_level", item["stage_code"]),
                stage_name=item["stage_name"],
                cause_code=item["cause_code"],
                cause_category=item["cause_category"],
                cause_name=item["cause_name"],
                strategy_type=item["strategy_type"],
                coach_script=item["coach_script"],
            ))
            count += 1

    db.commit()
    return count


def run_all():
    db = SessionLocal()
    try:
        n1 = seed_change_causes(db)
        print(f"[seed] change_causes: {n1} rows inserted")

        n2 = seed_intervention_strategies(db)
        print(f"[seed] intervention_strategies: {n2} rows inserted")

        n3 = backfill_readiness_level(db)
        print(f"[seed] readiness_level backfill: {n3} rows updated")

    finally:
        db.close()


if __name__ == "__main__":
    run_all()
