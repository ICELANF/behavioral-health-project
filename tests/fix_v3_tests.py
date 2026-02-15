"""
BHP v3 测试自动修复脚本
========================
在 D:\\behavioral-health-project 根目录运行：
    python tests/fix_v3_tests.py

功能：
1. 修复 test_00_preflight.py 的 sys.exit 崩溃
2. 探测 v3 模块实际路径
3. 生成适配版 test_v3_api.py
"""
import os
import sys
import re
from pathlib import Path

BASE = Path(__file__).parent.parent
TESTS = BASE / "tests"

print("=" * 60)
print("BHP v3 测试修复工具")
print(f"项目根目录: {BASE}")
print("=" * 60)

# ══════════════════════════════════════════════
# 1. 修复 test_00_preflight.py
# ══════════════════════════════════════════════

def fix_preflight():
    print("\n[1] 修复 test_00_preflight.py ...")
    pf = TESTS / "test_00_preflight.py"
    if not pf.exists():
        print("  ⚠️ 文件不存在，跳过")
        return

    content = pf.read_text(encoding="utf-8")

    # 查找模块级 sys.exit
    # 匹配行首的 sys.exit(...)，不在 def/if 缩进内
    pattern = r'^(sys\.exit\(\d*\))'
    lines = content.split('\n')
    fixed = False
    new_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('sys.exit(') and not line.startswith(' ') and not line.startswith('\t'):
            # 模块级 sys.exit → 包在 __main__ 保护中
            new_lines.append(f'if __name__ == "__main__":')
            new_lines.append(f'    {stripped}')
            fixed = True
            print(f"  ✅ 第 {i+1} 行: '{stripped}' → 已包在 __main__ 保护中")
        else:
            new_lines.append(line)

    if fixed:
        # 备份
        bak = pf.with_suffix('.py.bak')
        if not bak.exists():
            pf.rename(bak)
            print(f"  📁 原文件备份到: {bak.name}")
        pf.write_text('\n'.join(new_lines), encoding="utf-8")
        print("  ✅ test_00_preflight.py 已修复")
    else:
        print("  ℹ️ 未发现模块级 sys.exit()，无需修复")


# ══════════════════════════════════════════════
# 2. 探测 v3 模块路径
# ══════════════════════════════════════════════

def probe_v3_paths():
    """探测 v3 模块在基础项目中的实际位置"""
    print("\n[2] 探测 v3 模块路径 ...")

    results = {}

    # 探测 schemas
    schema_paths = [
        ("api.schemas", "APIResponse"),
        ("api.v3_schemas", "APIResponse"),
        ("v3.api.schemas", "APIResponse"),
        ("api.v3.schemas", "APIResponse"),
    ]
    results["schemas"] = None
    for mod, attr in schema_paths:
        try:
            m = __import__(mod, fromlist=[attr])
            if hasattr(m, attr):
                results["schemas"] = mod
                print(f"  ✅ Schemas: {mod}.{attr}")
                break
        except:
            pass
    if not results["schemas"]:
        print("  ❌ 未找到 v3 Schemas (APIResponse)")

    # 探测 routers
    router_paths = [
        "api.routers.diagnostic",
        "api.v3.routers.diagnostic",
        "v3.api.routers.diagnostic",
        "api.routers_v3.diagnostic",
    ]
    results["routers_prefix"] = None
    for mod in router_paths:
        try:
            m = __import__(mod, fromlist=["router"])
            if hasattr(m, "router"):
                # 提取前缀 (去掉 .diagnostic)
                results["routers_prefix"] = mod.rsplit(".", 1)[0]
                print(f"  ✅ Routers: {results['routers_prefix']}.*")
                break
        except:
            pass
    if not results["routers_prefix"]:
        print("  ❌ 未找到 v3 路由模块")

    # 探测 dependencies
    dep_paths = [
        ("api.dependencies", "get_llm_client"),
        ("api.v3_dependencies", "get_llm_client"),
        ("v3.api.dependencies", "get_llm_client"),
    ]
    results["dependencies"] = None
    for mod, attr in dep_paths:
        try:
            m = __import__(mod, fromlist=[attr])
            if hasattr(m, attr):
                results["dependencies"] = mod
                print(f"  ✅ Dependencies: {mod}")
                break
        except:
            pass
    if not results["dependencies"]:
        print("  ❌ 未找到 v3 依赖注入 (get_llm_client)")

    # 探测 database
    db_paths = [
        ("api.database", "get_db"),
        ("core.database", "get_db"),
        ("database", "get_db"),
    ]
    results["database"] = None
    for mod, attr in db_paths:
        try:
            m = __import__(mod, fromlist=[attr])
            if hasattr(m, attr):
                results["database"] = mod
                print(f"  ✅ Database: {mod}")
                break
        except:
            pass
    if not results["database"]:
        print("  ❌ 未找到 database 模块")

    # 探测 worker
    worker_paths = [
        ("api.worker", "celery_app"),
        ("worker", "celery_app"),
        ("core.worker", "celery_app"),
    ]
    results["worker"] = None
    for mod, attr in worker_paths:
        try:
            m = __import__(mod, fromlist=[attr])
            if hasattr(m, attr):
                results["worker"] = mod
                print(f"  ✅ Worker: {mod}")
                break
        except:
            pass
    if not results["worker"]:
        print("  ⚠️ 未找到 worker 模块 (非必需)")

    # 探测 main app
    app_paths = [
        ("api.main", "app"),
        ("main", "app"),
        ("app", "app"),
    ]
    results["app"] = None
    for mod, attr in app_paths:
        try:
            m = __import__(mod, fromlist=[attr])
            if hasattr(m, attr):
                results["app"] = mod
                app_obj = getattr(m, attr)
                print(f"  ✅ App: {mod} (title='{getattr(app_obj, 'title', '?')}', version='{getattr(app_obj, 'version', '?')}')")
                results["app_title"] = getattr(app_obj, "title", "")
                results["app_version"] = getattr(app_obj, "version", "")
                break
        except:
            pass

    return results


# ══════════════════════════════════════════════
# 3. 显示操作建议
# ══════════════════════════════════════════════

def show_recommendations(results):
    print("\n[3] 修复建议 ...")

    missing = []

    if not results.get("schemas"):
        missing.append("schemas")
        print("""
  📋 Schemas 缺失 — 需要将 v3 的 Schema 类合并到基础项目:
     方法: 将 bhp_v3/api/schemas.py 中的所有类定义追加到
           D:\\behavioral-health-project\\api\\schemas.py 末尾
     涉及 21 个 Pydantic 类 (APIResponse, DiagnosticMinimalRequest 等)""")

    if not results.get("routers_prefix"):
        missing.append("routers")
        print("""
  📋 Routers 缺失 — 需要创建 api/routers/ 目录:
     方法: mkdir api\\routers
           copy bhp_v3\\api\\routers\\*.py api\\routers\\""")

    if not results.get("dependencies"):
        missing.append("dependencies")
        print("""
  📋 Dependencies 缺失 — 需要追加 v3 依赖注入函数:
     方法: 将 bhp_v3/api/dependencies.py 中的函数追加到
           D:\\behavioral-health-project\\api\\dependencies.py 末尾""")

    if not results.get("database"):
        missing.append("database")
        print("""
  📋 Database 缺失 — 需要添加 api/database.py:
     方法: copy bhp_v3\\api\\database.py api\\database.py""")

    if not missing:
        print("  ✅ 所有 v3 模块路径已找到!")
    else:
        print(f"\n  ⚠️ 缺失模块: {', '.join(missing)}")
        print("  👉 请按上述建议合并文件后重新运行测试")


# ══════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════

if __name__ == "__main__":
    # 确保从项目根目录运行
    os.chdir(str(BASE))
    sys.path.insert(0, str(BASE))

    fix_preflight()
    results = probe_v3_paths()
    show_recommendations(results)

    print("\n" + "=" * 60)
    print("修复工具执行完毕")
    print("下一步: python -m pytest tests/test_00_preflight.py -v")
    print("=" * 60)
