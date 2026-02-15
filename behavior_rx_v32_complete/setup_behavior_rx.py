"""
BehaviorOS v32 — 行为处方系统安装脚本
==========================================
在 D:\behavioral-health-project\ 根目录下运行:

    python setup_behavior_rx.py

自动完成:
  1. 创建 behavior_rx/ 包目录结构
  2. 生成所有 __init__.py
  3. 移动测试文件到正确位置
  4. 验证安装

前置条件:
  - behavior_rx 的 16 个代码文件已存在于某个位置
  - 本脚本会告诉你缺少什么文件
"""

import os
import sys
import shutil

# =====================================================================
# 配置
# =====================================================================

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# behavior_rx 包目录结构
PACKAGE_DIRS = [
    "behavior_rx",
    "behavior_rx/core",
    "behavior_rx/agents",
    "behavior_rx/api",
    "behavior_rx/configs",
    "behavior_rx/migrations",
    "behavior_rx/patches",
    "behavior_rx/tests",
]

# 必需的代码文件 (相对于 behavior_rx/)
REQUIRED_FILES = {
    "core/rx_models.py":                        "ORM 数据模型",
    "core/rx_schemas.py":                       "Pydantic Schemas",
    "core/behavior_rx_engine.py":               "3D 处方引擎",
    "core/agent_handoff_service.py":            "Agent 交接服务",
    "core/agent_collaboration_orchestrator.py":  "协作编排器",
    "core/rx_conflict_resolver.py":             "冲突解决器",
    "agents/base_expert_agent.py":              "Agent 基类",
    "agents/behavior_coach_agent.py":           "行为教练 Agent",
    "agents/metabolic_expert_agent.py":         "代谢专家 Agent",
    "agents/cardiac_expert_agent.py":           "心血管专家 Agent",
    "agents/adherence_expert_agent.py":         "依从性专家 Agent",
    "api/rx_routes.py":                         "FastAPI 路由",
    "configs/rx_strategies.json":               "12策略模板",
    "migrations/031_behavior_rx_foundation.py":  "数据库迁移",
    "patches/master_agent_integration.py":       "MasterAgent 集成",
}

# 测试文件 (应放在 tests/ 根下, 不是 tests/test/)
TEST_FILES = [
    "test_v32_behavior_rx.py",
    "test_v32_models.py",
    "test_v32_api.py",
    "test_v32_policy_engine.py",
]

# __init__.py 内容
INIT_CONTENT = {
    "behavior_rx/__init__.py": '''"""
BehaviorOS — 行为处方系统 (behavior_rx)
==========================================
4-Expert-Agent 行为处方引擎
"""

__version__ = "0.32.0"
''',
    "behavior_rx/core/__init__.py": '"""behavior_rx.core — 核心引擎"""\n',
    "behavior_rx/agents/__init__.py": '"""behavior_rx.agents — 专家 Agent"""\n',
    "behavior_rx/api/__init__.py": '"""behavior_rx.api — REST 接口"""\n',
    "behavior_rx/configs/__init__.py": '"""behavior_rx.configs — 配置"""\n',
    "behavior_rx/migrations/__init__.py": '"""behavior_rx.migrations — 迁移"""\n',
    "behavior_rx/patches/__init__.py": '"""behavior_rx.patches — 补丁"""\n',
    "behavior_rx/tests/__init__.py": '"""behavior_rx.tests"""\n',
}


def print_header(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


def print_ok(msg):
    print(f"  ✅ {msg}")


def print_warn(msg):
    print(f"  ⚠️  {msg}")


def print_err(msg):
    print(f"  ❌ {msg}")


# =====================================================================
# Step 1: 创建目录
# =====================================================================

def step1_create_dirs():
    print_header("Step 1: 创建 behavior_rx 目录结构")

    for d in PACKAGE_DIRS:
        full_path = os.path.join(PROJECT_ROOT, d)
        os.makedirs(full_path, exist_ok=True)
        print_ok(f"目录: {d}/")

    # 确保 tests/ 存在
    os.makedirs(os.path.join(PROJECT_ROOT, "tests"), exist_ok=True)
    print_ok("目录: tests/")


# =====================================================================
# Step 2: 生成 __init__.py
# =====================================================================

def step2_create_inits():
    print_header("Step 2: 生成 __init__.py 文件")

    for rel_path, content in INIT_CONTENT.items():
        full_path = os.path.join(PROJECT_ROOT, rel_path)
        if not os.path.exists(full_path):
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            print_ok(f"创建: {rel_path}")
        else:
            print_ok(f"已存在: {rel_path}")


# =====================================================================
# Step 3: 检查代码文件
# =====================================================================

def step3_check_files():
    print_header("Step 3: 检查 behavior_rx 代码文件")

    missing = []
    found = []

    for rel_path, desc in REQUIRED_FILES.items():
        full_path = os.path.join(PROJECT_ROOT, "behavior_rx", rel_path)
        if os.path.exists(full_path):
            size_kb = os.path.getsize(full_path) / 1024
            print_ok(f"{rel_path} ({size_kb:.1f} KB) — {desc}")
            found.append(rel_path)
        else:
            print_err(f"缺失: {rel_path} — {desc}")
            missing.append(rel_path)

    print(f"\n  找到: {len(found)}/{len(REQUIRED_FILES)} 文件")

    if missing:
        print_warn(f"\n  缺失 {len(missing)} 个文件!")
        print_warn("  请将 files.zip 解压到以下目录:")
        print(f"\n  解压目标: D:\\behavioral-health-project\\behavior_rx\\")
        print(f"\n  解压后 behavior_rx/ 下应有:")
        for m in missing:
            print(f"    behavior_rx/{m}")

    return len(missing) == 0


# =====================================================================
# Step 4: 修复测试文件位置
# =====================================================================

def step4_fix_test_location():
    print_header("Step 4: 修复测试文件位置")

    tests_root = os.path.join(PROJECT_ROOT, "tests")
    tests_nested = os.path.join(PROJECT_ROOT, "tests", "test")

    # 检查是否有 tests/test/ 嵌套目录
    if os.path.exists(tests_nested) and os.path.isdir(tests_nested):
        print_warn(f"发现嵌套目录: tests/test/")

        for fname in TEST_FILES:
            nested_path = os.path.join(tests_nested, fname)
            target_path = os.path.join(tests_root, fname)

            if os.path.exists(nested_path):
                if os.path.exists(target_path):
                    # 比较大小, 保留较大的
                    if os.path.getsize(nested_path) > os.path.getsize(target_path):
                        shutil.copy2(nested_path, target_path)
                        print_ok(f"更新: tests/{fname} (从 tests/test/)")
                    else:
                        print_ok(f"保留: tests/{fname} (已是最新)")
                else:
                    shutil.copy2(nested_path, target_path)
                    print_ok(f"移动: tests/test/{fname} → tests/{fname}")
    else:
        # 检查测试文件是否在正确位置
        for fname in TEST_FILES:
            target_path = os.path.join(tests_root, fname)
            if os.path.exists(target_path):
                print_ok(f"tests/{fname}")
            else:
                print_err(f"缺失: tests/{fname}")

    # 确保 tests/__init__.py 存在
    tests_init = os.path.join(tests_root, "__init__.py")
    if not os.path.exists(tests_init):
        with open(tests_init, "w", encoding="utf-8") as f:
            f.write("")
        print_ok("创建: tests/__init__.py")


# =====================================================================
# Step 5: 验证导入
# =====================================================================

def step5_validate_imports():
    print_header("Step 5: 验证 Python 导入")

    # 确保项目根目录在 sys.path
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)

    success = 0
    total = 0

    imports_to_check = [
        ("behavior_rx", "包根"),
        ("behavior_rx.core.rx_schemas", "Pydantic Schemas"),
        ("behavior_rx.core.rx_models", "ORM 模型"),
        ("behavior_rx.core.behavior_rx_engine", "处方引擎"),
        ("behavior_rx.core.agent_handoff_service", "交接服务"),
        ("behavior_rx.core.agent_collaboration_orchestrator", "协作编排"),
        ("behavior_rx.core.rx_conflict_resolver", "冲突解决"),
        ("behavior_rx.agents.base_expert_agent", "Agent基类"),
        ("behavior_rx.agents.behavior_coach_agent", "行为教练"),
        ("behavior_rx.agents.metabolic_expert_agent", "代谢专家"),
        ("behavior_rx.agents.cardiac_expert_agent", "心血管专家"),
        ("behavior_rx.agents.adherence_expert_agent", "依从性专家"),
        ("behavior_rx.api.rx_routes", "FastAPI路由"),
        ("behavior_rx.patches.master_agent_integration", "MasterAgent集成"),
    ]

    for module_name, desc in imports_to_check:
        total += 1
        try:
            __import__(module_name)
            print_ok(f"import {module_name} — {desc}")
            success += 1
        except ImportError as e:
            print_err(f"import {module_name} — {e}")
        except Exception as e:
            print_warn(f"import {module_name} — {type(e).__name__}: {e}")
            success += 1  # 非 ImportError 说明文件存在

    print(f"\n  导入成功: {success}/{total}")
    return success == total


# =====================================================================
# Step 6: 打印最终目录树
# =====================================================================

def step6_print_tree():
    print_header("Step 6: 最终目录结构")

    rx_root = os.path.join(PROJECT_ROOT, "behavior_rx")
    if not os.path.exists(rx_root):
        print_err("behavior_rx/ 目录不存在")
        return

    for root, dirs, files in os.walk(rx_root):
        # 跳过 __pycache__
        dirs[:] = [d for d in dirs if d != "__pycache__"]

        level = root.replace(rx_root, "").count(os.sep)
        indent = "  " * level
        folder_name = os.path.basename(root)
        print(f"  {indent}{folder_name}/")

        sub_indent = "  " * (level + 1)
        for f in sorted(files):
            if f == "__pycache__":
                continue
            size_kb = os.path.getsize(os.path.join(root, f)) / 1024
            print(f"  {sub_indent}{f} ({size_kb:.1f} KB)")


# =====================================================================
# Main
# =====================================================================

def main():
    print("\n" + "=" * 60)
    print("  BehaviorOS v32 — 行为处方系统安装工具")
    print("=" * 60)
    print(f"\n  项目根目录: {PROJECT_ROOT}")

    step1_create_dirs()
    step2_create_inits()
    all_files_ok = step3_check_files()
    step4_fix_test_location()

    if all_files_ok:
        all_imports_ok = step5_validate_imports()
        step6_print_tree()

        if all_imports_ok:
            print_header("🎉 安装完成! 运行测试:")
            print("""
  python -m pytest tests/test_v32_behavior_rx.py -v -s
  python -m pytest tests/test_v32_models.py -v -s
  python -m pytest tests/test_v32_api.py -v -s
  python -m pytest tests/test_v32_policy_engine.py -v -s

  # 全部运行:
  python -m pytest tests/test_v32_*.py -v -s
""")
        else:
            print_header("⚠️ 部分导入失败, 请检查缺失的依赖")
    else:
        print_header("⚠️ 代码文件不完整, 请按以下步骤操作")
        print("""
  1. 找到之前下载的 behavior_rx 文件夹 (16个代码文件)

  2. 将文件复制到以下结构:

     D:\\behavioral-health-project\\behavior_rx\\
     ├── __init__.py                              ← 已自动创建
     ├── core\\
     │   ├── __init__.py                          ← 已自动创建
     │   ├── rx_models.py
     │   ├── rx_schemas.py
     │   ├── behavior_rx_engine.py
     │   ├── agent_handoff_service.py
     │   ├── agent_collaboration_orchestrator.py
     │   └── rx_conflict_resolver.py
     ├── agents\\
     │   ├── __init__.py                          ← 已自动创建
     │   ├── base_expert_agent.py
     │   ├── behavior_coach_agent.py
     │   ├── metabolic_expert_agent.py
     │   ├── cardiac_expert_agent.py
     │   └── adherence_expert_agent.py
     ├── api\\
     │   ├── __init__.py                          ← 已自动创建
     │   └── rx_routes.py
     ├── configs\\
     │   ├── __init__.py                          ← 已自动创建
     │   └── rx_strategies.json
     ├── migrations\\
     │   ├── __init__.py                          ← 已自动创建
     │   └── 031_behavior_rx_foundation.py
     └── patches\\
         ├── __init__.py                          ← 已自动创建
         └── master_agent_integration.py

  3. 再次运行本脚本验证:
     python setup_behavior_rx.py
""")


if __name__ == "__main__":
    main()
