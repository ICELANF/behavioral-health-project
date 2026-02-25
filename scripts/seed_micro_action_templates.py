#!/usr/bin/env python3
"""
饮食行为干预决策树10情境 — 微行动模板验证+种子脚本

50条模板 (10情境 × 5优先级)
支持 --validate / --seed-test-tasks --user-id N

Usage:
    python scripts/seed_micro_action_templates.py --validate
    python scripts/seed_micro_action_templates.py --seed-test-tasks --user-id 2
    python scripts/seed_micro_action_templates.py --seed-test-tasks --user-id 2 --db postgresql://...
"""

import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from loguru import logger

VALID_DOMAINS = {
    "nutrition", "exercise", "sleep", "emotion",
    "stress", "cognitive", "social"
}
VALID_DIFFICULTIES = {"easy", "moderate", "challenging"}
VALID_TTM_STAGES = {"S0", "S1", "S2", "S3", "S4", "S5"}
EXPECTED_SCENARIOS = {
    "S01", "S02", "S03", "S04", "S05",
    "S06", "S07", "S08", "S09", "S10"
}


def load_templates() -> list:
    """Load and flatten templates from config JSON."""
    config_path = PROJECT_ROOT / "configs" / "micro_action_dietary_templates.json"
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    templates = []
    for section in data.get("templates", []):
        for item in section.get("items", []):
            templates.append(item)

    logger.info(f"Loaded {len(templates)} templates from {config_path.name}")
    return templates


def validate_template(t: dict) -> list:
    """Validate a single template. Returns list of errors."""
    errors = []

    required_fields = [
        "template_id", "scenario_id", "priority", "domain",
        "title", "description", "metabolic_mechanism",
        "difficulty", "compliance_tip", "ttm_stages", "duration_minutes"
    ]
    for field in required_fields:
        if field not in t:
            errors.append(f"Missing field: {field}")

    if "template_id" in t:
        tid = t["template_id"]
        if not tid.startswith("MA-DS"):
            errors.append(f"template_id should start with 'MA-DS': {tid}")

    if "scenario_id" in t:
        sid = t["scenario_id"]
        if sid not in EXPECTED_SCENARIOS:
            errors.append(f"Unknown scenario_id: {sid}")

    if "priority" in t:
        p = t["priority"]
        if not (1 <= p <= 5):
            errors.append(f"Priority out of range [1,5]: {p}")

    if "domain" in t:
        d = t["domain"]
        if d not in VALID_DOMAINS:
            errors.append(f"Invalid domain '{d}', expected one of {VALID_DOMAINS}")

    if "difficulty" in t:
        diff = t["difficulty"]
        if diff not in VALID_DIFFICULTIES:
            errors.append(
                f"Invalid difficulty '{diff}', "
                f"expected one of {VALID_DIFFICULTIES}"
            )

    if "ttm_stages" in t:
        stages = t["ttm_stages"]
        if not isinstance(stages, list) or len(stages) == 0:
            errors.append("ttm_stages must be a non-empty list")
        else:
            for s in stages:
                if s not in VALID_TTM_STAGES:
                    errors.append(f"Invalid TTM stage: {s}")

    if "duration_minutes" in t:
        dm = t["duration_minutes"]
        if not isinstance(dm, (int, float)) or dm < 0:
            errors.append(f"duration_minutes must be >= 0: {dm}")

    return errors


def validate_all(templates: list) -> bool:
    """Validate all 50 templates. Returns True if all pass."""
    logger.info("=== VALIDATION MODE ===")
    all_valid = True
    ids_seen = set()
    scenarios_seen = set()
    scenario_priority_combos = set()

    for i, t in enumerate(templates):
        tid = t.get("template_id", f"<unnamed-{i}>")
        errors = validate_template(t)

        # Check for duplicate template_id
        if tid in ids_seen:
            errors.append(f"Duplicate template_id: {tid}")
        ids_seen.add(tid)

        # Track scenario coverage
        sid = t.get("scenario_id", "")
        scenarios_seen.add(sid)

        # Check unique scenario+priority
        combo = (sid, t.get("priority", 0))
        if combo in scenario_priority_combos:
            errors.append(
                f"Duplicate scenario+priority: {sid} P{t.get('priority')}"
            )
        scenario_priority_combos.add(combo)

        if errors:
            all_valid = False
            for err in errors:
                logger.error(f"  [{tid}] {err}")

    # Coverage checks
    missing = EXPECTED_SCENARIOS - scenarios_seen
    if missing:
        all_valid = False
        logger.error(f"Missing scenarios: {missing}")

    if all_valid:
        logger.success(
            f"Validation passed: {len(templates)} templates, "
            f"{len(scenarios_seen)} scenarios, all fields present"
        )
    else:
        logger.error("Validation FAILED: see errors above")

    return all_valid


def seed_test_tasks(templates: list, user_id: int, db_url: str) -> dict:
    """Create P1-P3 tasks for a test user from templates."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from core.models import MicroActionTask

    engine_url = db_url.replace("+asyncpg", "")
    engine = create_engine(engine_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    stats = {"created": 0, "skipped": 0, "errors": 0}
    today = date.today()

    try:
        # Filter P1-P3 templates
        p1_p3 = [t for t in templates if t.get("priority", 99) <= 3]
        logger.info(
            f"Creating {len(p1_p3)} tasks (P1-P3) for user_id={user_id}"
        )

        for i, t in enumerate(p1_p3):
            tid = t["template_id"]
            scheduled = (today + timedelta(days=i // 5)).isoformat()

            try:
                # Check if already exists
                existing = db.query(MicroActionTask).filter(
                    MicroActionTask.user_id == user_id,
                    MicroActionTask.title == t["title"],
                    MicroActionTask.scheduled_date == scheduled,
                ).first()

                if existing:
                    logger.info(f"  SKIP (exists): {tid}")
                    stats["skipped"] += 1
                    continue

                task = MicroActionTask(
                    user_id=user_id,
                    domain=t["domain"],
                    title=t["title"],
                    description=t["description"],
                    difficulty=t["difficulty"],
                    source="dietary_template",
                    source_id=tid,
                    status="pending",
                    scheduled_date=scheduled,
                )
                db.add(task)
                db.commit()
                db.refresh(task)

                logger.info(
                    f"  CREATED: {tid} → task_id={task.id} "
                    f"(date={scheduled})"
                )
                stats["created"] += 1

            except Exception as e:
                db.rollback()
                logger.error(f"  ERROR: {tid} → {e}")
                stats["errors"] += 1

    finally:
        db.close()

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Validate and seed dietary micro-action templates"
    )
    parser.add_argument(
        "--validate", action="store_true",
        help="Validate all 50 templates structure"
    )
    parser.add_argument(
        "--seed-test-tasks", action="store_true",
        help="Create P1-P3 tasks for a test user"
    )
    parser.add_argument(
        "--user-id", type=int, default=None,
        help="User ID for test task creation (required with --seed-test-tasks)"
    )
    parser.add_argument(
        "--db", type=str, default=None,
        help="Database URL (default: DATABASE_URL env or project default)"
    )
    args = parser.parse_args()

    templates = load_templates()

    if args.validate:
        success = validate_all(templates)
        sys.exit(0 if success else 1)

    if args.seed_test_tasks:
        if not args.user_id:
            logger.error("--user-id is required with --seed-test-tasks")
            sys.exit(1)

        # Always validate first
        if not validate_all(templates):
            logger.error("Templates validation failed, aborting seed")
            sys.exit(1)

        db_url = (
            args.db
            or os.environ.get("DATABASE_URL")
            or "postgresql://postgres:difyai123456@db:5432/health_platform"
        )

        stats = seed_test_tasks(templates, args.user_id, db_url)
        logger.info(
            f"Seed complete: {stats['created']} created, "
            f"{stats['skipped']} skipped, {stats['errors']} errors"
        )

        if stats["errors"] > 0:
            sys.exit(1)
        return

    # Default: just validate
    logger.info("No action specified, running validation...")
    success = validate_all(templates)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
