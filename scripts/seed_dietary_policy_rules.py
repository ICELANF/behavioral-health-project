#!/usr/bin/env python3
"""
饮食行为干预决策树10情境 — Policy Engine路由规则种子脚本

读取 configs/policy_dietary_scenarios.json → PolicyRule 逐条写入DB
支持 --dry-run 验证模式

Usage:
    python scripts/seed_dietary_policy_rules.py --dry-run   # 验证，不写入
    python scripts/seed_dietary_policy_rules.py              # 实际种子
    python scripts/seed_dietary_policy_rules.py --db postgresql://...  # 指定DB
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from loguru import logger


def load_rules_config() -> list:
    """Load and flatten rules from config JSON."""
    config_path = PROJECT_ROOT / "configs" / "policy_dietary_scenarios.json"
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rules = []
    for section in data.get("rules", []):
        for item in section.get("items", []):
            rules.append(item)

    logger.info(f"Loaded {len(rules)} rules from {config_path.name}")
    return rules


def validate_rule(rule: dict) -> list:
    """Validate a single rule structure. Returns list of errors."""
    errors = []
    required_fields = [
        "rule_name", "rule_type", "condition_expr",
        "action_type", "action_params", "priority"
    ]
    for field in required_fields:
        if field not in rule:
            errors.append(f"Missing required field: {field}")

    if "rule_name" in rule:
        name = rule["rule_name"]
        if not name.startswith("dietary_"):
            errors.append(f"Rule name should start with 'dietary_': {name}")

    if "priority" in rule:
        p = rule["priority"]
        if not (0 <= p <= 100):
            errors.append(f"Priority out of range [0,100]: {p}")

    if "condition_expr" in rule:
        expr = rule["condition_expr"]
        if not isinstance(expr, dict):
            errors.append("condition_expr must be a JSON object")

    if "action_params" in rule:
        params = rule["action_params"]
        if "agent" not in params:
            errors.append("action_params must contain 'agent' field")
        if "scenario_id" not in params:
            errors.append("action_params must contain 'scenario_id' field")

    return errors


def dry_run(rules: list) -> bool:
    """Validate all rules without writing to DB."""
    logger.info("=== DRY RUN MODE ===")
    all_valid = True
    names_seen = set()

    for i, rule in enumerate(rules):
        name = rule.get("rule_name", f"<unnamed-{i}>")
        errors = validate_rule(rule)

        # Check for duplicate names
        if name in names_seen:
            errors.append(f"Duplicate rule_name: {name}")
        names_seen.add(name)

        if errors:
            all_valid = False
            for err in errors:
                logger.error(f"  [{name}] {err}")
        else:
            agent = rule["action_params"]["agent"]
            scenario = rule["action_params"]["scenario_id"]
            logger.info(
                f"  OK: {name} → {agent} (scenario={scenario}, "
                f"priority={rule['priority']})"
            )

    if all_valid:
        logger.success(
            f"Dry run passed: {len(rules)} rules validated, "
            f"{len(names_seen)} unique names"
        )
    else:
        logger.error("Dry run FAILED: see errors above")

    return all_valid


def seed_rules(rules: list, db_url: str) -> dict:
    """Seed rules into the database."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from core.models import PolicyRule

    # Ensure sync driver
    engine_url = db_url.replace("+asyncpg", "")
    engine = create_engine(engine_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    stats = {"created": 0, "skipped": 0, "errors": 0}

    try:
        for rule_data in rules:
            name = rule_data["rule_name"]
            try:
                # Check if rule already exists (UNIQUE constraint on rule_name)
                existing = db.query(PolicyRule).filter(
                    PolicyRule.rule_name == name
                ).first()

                if existing:
                    logger.info(f"  SKIP (exists): {name} (id={existing.id})")
                    stats["skipped"] += 1
                    continue

                rule = PolicyRule(
                    rule_name=name,
                    rule_type=rule_data["rule_type"],
                    condition_expr=rule_data["condition_expr"],
                    action_type=rule_data["action_type"],
                    action_params=rule_data["action_params"],
                    priority=rule_data.get("priority", 50),
                    evidence_tier=rule_data.get("evidence_tier"),
                    description=rule_data.get("description"),
                    created_by="seed_dietary_policy_rules",
                )
                db.add(rule)
                db.commit()
                db.refresh(rule)

                logger.info(
                    f"  CREATED: {name} (id={rule.id}, "
                    f"priority={rule.priority})"
                )
                stats["created"] += 1

            except Exception as e:
                db.rollback()
                logger.error(f"  ERROR: {name} → {e}")
                stats["errors"] += 1

    finally:
        db.close()

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Seed dietary intervention policy rules"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Validate rules without writing to DB"
    )
    parser.add_argument(
        "--db", type=str, default=None,
        help="Database URL (default: DATABASE_URL env or project default)"
    )
    args = parser.parse_args()

    rules = load_rules_config()

    if args.dry_run:
        success = dry_run(rules)
        sys.exit(0 if success else 1)

    # Determine DB URL
    db_url = (
        args.db
        or os.environ.get("DATABASE_URL")
        or "postgresql://postgres:difyai123456@db:5432/health_platform"
    )

    logger.info(f"Seeding {len(rules)} dietary policy rules...")
    stats = seed_rules(rules, db_url)

    logger.info(
        f"Seed complete: {stats['created']} created, "
        f"{stats['skipped']} skipped, {stats['errors']} errors"
    )

    if stats["errors"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
