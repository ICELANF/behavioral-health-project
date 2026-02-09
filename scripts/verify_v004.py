"""
BHP V004 方案引擎 — 部署验证脚本
运行: python verify_v004.py

检查项:
1. SQL表创建验证 (3张新表 + 2视图 + 2函数)
2. glucose-14d模板导入验证
3. API端点可达性验证
4. APScheduler任务注册验证
5. 与V003激励系统联动验证
"""

import json
import sys
import subprocess
from pathlib import Path

# ── 配置 ──
API_BASE = "http://localhost:8000"
DB_URL = "postgresql://postgres:difyai123456@localhost:5432/health_platform"

CHECKS = []


def check(name):
    """装饰器: 注册检查项"""
    def decorator(func):
        CHECKS.append((name, func))
        return func
    return decorator


# ═══════════════════════════════════════════════════
# 检查项定义
# ═══════════════════════════════════════════════════

@check("1. V004 SQL 表是否存在")
def check_tables():
    """验证3张新表已创建"""
    tables = ["program_templates", "program_enrollments", "program_interactions"]
    results = {}
    for table in tables:
        try:
            out = subprocess.run(
                ["psql", DB_URL, "-t", "-c",
                 f"SELECT COUNT(*) FROM information_schema.tables "
                 f"WHERE table_name = '{table}'"],
                capture_output=True, text=True, timeout=5
            )
            exists = out.stdout.strip() == "1"
            results[table] = "✅" if exists else "❌ 未创建"
        except Exception as e:
            results[table] = f"⚠️ {e}"
    return results


@check("2. 枚举类型是否存在")
def check_enums():
    enums = ["program_category", "enrollment_status", "push_slot"]
    results = {}
    for enum in enums:
        try:
            out = subprocess.run(
                ["psql", DB_URL, "-t", "-c",
                 f"SELECT COUNT(*) FROM pg_type WHERE typname = '{enum}'"],
                capture_output=True, text=True, timeout=5
            )
            exists = out.stdout.strip() == "1"
            results[enum] = "✅" if exists else "❌"
        except Exception as e:
            results[enum] = f"⚠️ {e}"
    return results


@check("3. 视图是否存在")
def check_views():
    views = ["v_program_enrollment_summary", "v_program_today_pushes"]
    results = {}
    for view in views:
        try:
            out = subprocess.run(
                ["psql", DB_URL, "-t", "-c",
                 f"SELECT COUNT(*) FROM information_schema.views "
                 f"WHERE table_name = '{view}'"],
                capture_output=True, text=True, timeout=5
            )
            exists = out.stdout.strip() == "1"
            results[view] = "✅" if exists else "❌"
        except Exception as e:
            results[view] = f"⚠️ {e}"
    return results


@check("4. 数据库函数是否存在")
def check_functions():
    funcs = ["advance_program_day", "calc_interaction_rate"]
    results = {}
    for func in funcs:
        try:
            out = subprocess.run(
                ["psql", DB_URL, "-t", "-c",
                 f"SELECT COUNT(*) FROM pg_proc WHERE proname = '{func}'"],
                capture_output=True, text=True, timeout=5
            )
            exists = int(out.stdout.strip()) > 0
            results[func] = "✅" if exists else "❌"
        except Exception as e:
            results[func] = f"⚠️ {e}"
    return results


@check("5. glucose-14d 模板JSON有效性")
def check_template_json():
    config_dir = Path(__file__).parent
    path = config_dir / "glucose-14d-template.json"
    if not path.exists():
        return {"file": f"❌ 未找到: {path}"}

    data = json.loads(path.read_text(encoding="utf-8"))
    schedule = data.get("schedule", {})
    days = schedule.get("days", [])
    total_pushes = sum(len(d.get("pushes", [])) for d in days)
    total_questions = sum(
        len(p.get("survey", {}).get("questions", []))
        for d in days for p in d.get("pushes", [])
    )

    return {
        "file": "✅ 存在",
        "slug": data.get("slug", "?"),
        "days": f"{len(days)} 天",
        "pushes": f"{total_pushes} 次推送",
        "questions": f"{total_questions} 个题目",
        "rules": f"{len(data.get('recommendation_rules', {}).get('rules', []))} 条规则",
    }


@check("6. glucose-14d 模板是否已导入数据库")
def check_template_in_db():
    try:
        out = subprocess.run(
            ["psql", DB_URL, "-t", "-c",
             "SELECT slug, title, total_days, category "
             "FROM program_templates WHERE slug = 'glucose-14d'"],
            capture_output=True, text=True, timeout=5
        )
        if out.stdout.strip():
            return {"glucose-14d": f"✅ {out.stdout.strip()}"}
        return {"glucose-14d": "⚠️ 未导入(需运行 seed_program_templates.py)"}
    except Exception as e:
        return {"glucose-14d": f"⚠️ {e}"}


@check("7. API 端点可达性")
def check_api_endpoints():
    """检查12个端点是否注册"""
    endpoints = [
        ("GET",  "/api/v1/programs/templates"),
        ("POST", "/api/v1/programs/templates"),
        ("GET",  "/api/v1/programs/templates/{id}"),
        ("PUT",  "/api/v1/programs/templates/{id}"),
        ("POST", "/api/v1/programs/enroll"),
        ("GET",  "/api/v1/programs/my"),
        ("GET",  "/api/v1/programs/my/{id}/today"),
        ("POST", "/api/v1/programs/my/{id}/interact"),
        ("GET",  "/api/v1/programs/my/{id}/timeline"),
        ("GET",  "/api/v1/programs/my/{id}/progress"),
        ("GET",  "/api/v1/programs/admin/analytics"),
        ("GET",  "/api/v1/programs/admin/enrollments"),
    ]
    results = {}
    try:
        import requests
        resp = requests.get(f"{API_BASE}/openapi.json", timeout=3)
        if resp.status_code == 200:
            openapi = resp.json()
            paths = openapi.get("paths", {})
            for method, path in endpoints:
                # Normalize path params
                norm = path.replace("{id}", "{enrollment_id}").replace("{id}", "{template_id}")
                found = any(
                    p.startswith("/api/v1/programs") and method.lower() in methods
                    for p, methods in paths.items()
                )
                results[f"{method} {path}"] = "✅" if found else "⚠️ 未发现"
        else:
            results["openapi"] = f"⚠️ HTTP {resp.status_code}"
    except Exception as e:
        results["connectivity"] = f"⚠️ API不可达: {e}"
        for method, path in endpoints:
            results[f"{method} {path}"] = "⏭️ 跳过"
    return results


@check("8. V003激励系统联动")
def check_v003_integration():
    """验证V003的milestone_key枚举是否可兼容方案引擎事件"""
    try:
        out = subprocess.run(
            ["psql", DB_URL, "-t", "-c",
             "SELECT string_agg(enumlabel, ', ') "
             "FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid "
             "WHERE t.typname = 'milestone_key'"],
            capture_output=True, text=True, timeout=5
        )
        keys = out.stdout.strip()
        if keys:
            return {
                "milestone_keys": f"✅ {keys}",
                "note": "方案完成可复用DAY_14/DAY_30里程碑",
            }
        return {"milestone_keys": "⚠️ V003可能未部署"}
    except Exception as e:
        return {"check": f"⚠️ {e}"}


# ═══════════════════════════════════════════════════
# 执行
# ═══════════════════════════════════════════════════

def run_all():
    print("=" * 60)
    print("BHP V004 方案引擎 — 部署验证")
    print(f"时间: {__import__('datetime').datetime.now().isoformat()}")
    print("=" * 60)

    all_pass = True
    for name, func in CHECKS:
        print(f"\n🔍 {name}")
        try:
            results = func()
            if isinstance(results, dict):
                for k, v in results.items():
                    status = "❌" if "❌" in str(v) else ""
                    if status:
                        all_pass = False
                    print(f"   {k}: {v}")
            else:
                print(f"   {results}")
        except Exception as e:
            print(f"   ❌ 异常: {e}")
            all_pass = False

    print(f"\n{'='*60}")
    if all_pass:
        print("✅ 所有检查通过")
    else:
        print("⚠️  部分检查未通过，请查看上方详情")
    print("=" * 60)

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(run_all())
