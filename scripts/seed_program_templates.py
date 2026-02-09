"""
BHP 方案引擎 — 种子数据导入脚本
运行方式: python -m scripts.seed_program_templates

功能:
1. 从 config/glucose-14d-template.json 导入血糖14天方案模板
2. 验证schedule_json结构完整性
3. 输出导入结果统计
"""

import json
import sys
from pathlib import Path

# ── 根据项目实际路径调整 ──
# from app.database import SessionLocal
# from app.services.program_service import ProgramService

CONFIG_DIR = Path(__file__).parent.parent / "configs"


def validate_schedule(schedule: dict) -> list:
    """验证schedule_json结构"""
    errors = []
    days = schedule.get("days", [])

    if not days:
        errors.append("schedule.days is empty")
        return errors

    day_numbers = set()
    for day in days:
        d = day.get("day")
        if d is None:
            errors.append("day.day is missing")
            continue
        if d in day_numbers:
            errors.append(f"Duplicate day number: {d}")
        day_numbers.add(d)

        pushes = day.get("pushes", [])
        if not pushes:
            errors.append(f"Day {d}: no pushes")
            continue

        slots_seen = set()
        for i, push in enumerate(pushes):
            slot = push.get("slot")
            if not slot:
                errors.append(f"Day {d} push {i}: missing slot")
            if slot in slots_seen:
                errors.append(f"Day {d}: duplicate slot '{slot}'")
            slots_seen.add(slot)

            content = push.get("content", {})
            if not content.get("knowledge") and not content.get("behavior_guide"):
                errors.append(f"Day {d} {slot}: empty content")

            # 验证survey结构
            survey = push.get("survey")
            if survey:
                questions = survey.get("questions", [])
                qids = set()
                for q in questions:
                    qid = q.get("id")
                    if not qid:
                        errors.append(f"Day {d} {slot}: question missing id")
                    if qid in qids:
                        errors.append(f"Day {d} {slot}: duplicate question id '{qid}'")
                    qids.add(qid)
                    if not q.get("type"):
                        errors.append(f"Day {d} {slot}: question '{qid}' missing type")
                    if not q.get("text"):
                        errors.append(f"Day {d} {slot}: question '{qid}' missing text")

    return errors


def validate_recommendation_rules(rules: dict) -> list:
    """验证推荐规则结构"""
    errors = []
    for i, rule in enumerate(rules.get("rules", [])):
        if not rule.get("condition"):
            errors.append(f"Rule {i}: missing condition")
        if not rule.get("action"):
            errors.append(f"Rule {i}: missing action")
        cond = rule.get("condition", {})
        if not cond.get("metric"):
            errors.append(f"Rule {i}: condition missing metric")
        if not cond.get("op"):
            errors.append(f"Rule {i}: condition missing op")
    return errors


def load_and_validate(slug: str) -> dict:
    """加载并验证模板JSON"""
    path = CONFIG_DIR / f"{slug}-template.json"
    if not path.exists():
        print(f"❌ File not found: {path}")
        sys.exit(1)

    data = json.loads(path.read_text(encoding="utf-8"))
    print(f"📄 Loaded: {path.name}")
    print(f"   Title: {data['title']}")
    print(f"   Category: {data['category']}")
    print(f"   Total days: {data['total_days']}")

    schedule = data.get("schedule", {})
    days = schedule.get("days", [])
    total_pushes = sum(len(d.get("pushes", [])) for d in days)
    total_surveys = sum(
        1 for d in days for p in d.get("pushes", []) if p.get("survey")
    )
    total_questions = sum(
        len(p.get("survey", {}).get("questions", []))
        for d in days for p in d.get("pushes", [])
    )
    print(f"   Days: {len(days)}, Pushes: {total_pushes}, "
          f"Surveys: {total_surveys}, Questions: {total_questions}")

    # Validate
    errors = validate_schedule(schedule)
    rule_errors = validate_recommendation_rules(
        data.get("recommendation_rules", {"rules": []})
    )
    errors.extend(rule_errors)

    if errors:
        print(f"\n⚠️  Validation warnings ({len(errors)}):")
        for e in errors[:10]:
            print(f"   - {e}")
        if len(errors) > 10:
            print(f"   ... and {len(errors) - 10} more")
    else:
        print("   ✅ Validation passed")

    return data


def seed_to_database(data: dict):
    """导入到数据库"""
    # db = SessionLocal()
    # try:
    #     service = ProgramService(db)
    #     result = service.seed_template_from_json(data["slug"])
    #     if result:
    #         print(f"\n✅ Seeded: {result}")
    #     else:
    #         print(f"\n⚠️  Template already exists or seed failed")
    # finally:
    #     db.close()
    print("\n💡 Database seed skipped (uncomment above code to run)")


def generate_sql_insert(data: dict) -> str:
    """生成SQL INSERT语句(可直接在psql中执行)"""
    schedule_json = json.dumps(data["schedule"], ensure_ascii=False)
    rules_json = json.dumps(
        data.get("recommendation_rules", {"rules": []}), ensure_ascii=False
    )
    tags_json = json.dumps(data.get("tags", []))

    sql = f"""
-- 导入方案模板: {data['slug']}
INSERT INTO program_templates
  (slug, title, description, category, total_days, pushes_per_day,
   schedule_json, recommendation_rules, tags,
   is_active, is_public, created_by)
VALUES
  ('{data["slug"]}',
   '{data["title"]}',
   '{data.get("description", "").replace("'", "''")}',
   '{data.get("category", "custom")}',
   {data["total_days"]},
   {data.get("pushes_per_day", 3)},
   '{schedule_json.replace("'", "''")}',
   '{rules_json.replace("'", "''")}',
   '{tags_json}',
   true, true, 1)
ON CONFLICT (slug) DO UPDATE SET
  title = EXCLUDED.title,
  description = EXCLUDED.description,
  schedule_json = EXCLUDED.schedule_json,
  recommendation_rules = EXCLUDED.recommendation_rules,
  tags = EXCLUDED.tags,
  updated_at = NOW();
"""
    return sql


if __name__ == "__main__":
    templates_to_seed = ["glucose-14d"]

    for slug in templates_to_seed:
        print(f"\n{'='*50}")
        print(f"Processing: {slug}")
        print('='*50)

        data = load_and_validate(slug)
        seed_to_database(data)

        # 生成SQL INSERT
        sql = generate_sql_insert(data)
        sql_path = CONFIG_DIR.parent / f"scripts/seed_{slug.replace('-', '_')}.sql"
        sql_path.parent.mkdir(parents=True, exist_ok=True)
        sql_path.write_text(sql, encoding="utf-8")
        print(f"📝 SQL INSERT saved to: {sql_path}")

    print(f"\n{'='*50}")
    print("Seed complete!")
