#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行健平台最优架构手术 — 本地文件采集脚本
============================================================
执行位置: D:/behavioral-health-project/ （项目根目录）
执行方式: python collect_for_surgery.py
输出结果: surgery_pack_{时间戳}.zip

功能:
  1. 收集所有手术必需文件
  2. 执行 8 条诊断命令，输出保存为文本
  3. 全部打包为一个 zip，直接上传到新对话

Windows 执行方式:
  cd D:\behavioral-health-project
  python collect_for_surgery.py

  如果 python 命令不存在，改用:
  python3 collect_for_surgery.py

  或双击运行（会在当前目录生成 zip）
============================================================
"""

import os
import sys
import zipfile
import subprocess
import json
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# 配置：需要采集的文件
# ─────────────────────────────────────────────────────────────────────────────

# 已知存在的文件（V5.3.2 已核实）
CONFIRMED_FILES = [
    "main.py",
    "core/master_agent_v0.py",
    "api/r3_grower_flywheel_api_live.py",
]

# 第一批：MasterAgent 归一 + Agent 整合（出架构图用）
BATCH_1 = [
    "core/master_agent_unified.py",
    "core/agents/master_agent.py",
    "core/agents/__init__.py",
    "behavior_rx/master_agent_integration.py",
    "behavior_rx/behavior_rx_engine.py",
    "behavior_rx/agent_handoff_service.py",
]

# 第二批：v3 路由清退（端点 diff 用）
BATCH_2 = [
    "v3/routers/auth.py",
    "v3/routers/diagnostic.py",
    "v3/routers/chat.py",
    "v3/routers/assessment.py",
    "v3/routers/tracking.py",
    "v3/routers/incentive.py",
    "v3/routers/knowledge.py",
    "v3/routers/health.py",
    "api/chat_rest_api.py",
    "api/assessment_api.py",
    "api/assessment_assignment_api.py",
]

# 第三批：数据模型 + 迁移历史
BATCH_3 = [
    "core/models.py",
    "core/database.py",
]

# behavior_rx 补充文件（如存在）
BATCH_RX = [
    "behavior_rx/rx_routes.py",
    "behavior_rx/__init__.py",
    "behavior_rx/agent_orchestrator.py",
    "behavior_rx/expert_agent_router.py",
]

# 补充：其他可能包含 Agent 类的核心文件
BATCH_EXTRA = [
    "core/safety_agent.py",
    "core/crisis_agent.py",
    "core/chat_agent.py",
    "core/coaching_agent.py",
    "core/assessment_agent.py",
    "api/dependencies.py",
]

ALL_FILE_TARGETS = (
    CONFIRMED_FILES
    + BATCH_1
    + BATCH_2
    + BATCH_3
    + BATCH_RX
    + BATCH_EXTRA
)

# ─────────────────────────────────────────────────────────────────────────────
# 配置：诊断命令（跨平台，Windows/Linux/Mac 均可）
# ─────────────────────────────────────────────────────────────────────────────

# Windows 用 dir 替代 find，用 findstr 替代 grep
# 脚本会自动检测系统并选择合适命令

IS_WINDOWS = sys.platform.startswith("win")

COMMANDS = {
    "cmd1_agent_class_locations": {
        "desc": "所有含 Agent 类的文件位置",
        "win": 'findstr /s /m "class.*Agent" *.py',
        "unix": 'find . -name "*.py" -not -path "*/__pycache__/*" -not -path "*/.venv/*" -not -path "*/.git/*" | xargs grep -l "class.*Agent" 2>/dev/null | sort',
        "python_fallback": True,
    },
    "cmd2_registry_mechanism": {
        "desc": "现有注册机制",
        "win": 'findstr /s /r "class.*Registry AgentRegistry register_agent" *.py',
        "unix": 'grep -rn "class.*Registry\\|AgentRegistry\\|register_agent\\|@agent\\b" --include="*.py" --exclude-dir=.git --exclude-dir=.venv . 2>/dev/null',
        "python_fallback": True,
    },
    "cmd3_masteragent_signatures": {
        "desc": "三版本 MasterAgent 方法签名",
        "win": None,  # Python fallback only
        "unix": 'grep -n "^class \\|^    def \\|^def " core/master_agent_v0.py core/master_agent_unified.py core/agents/master_agent.py 2>/dev/null',
        "python_fallback": True,
    },
    "cmd4_router_registration": {
        "desc": "完整路由注册清单（含行号）",
        "win": 'findstr /n "include_router app.add_ @app." main.py',
        "unix": 'grep -n "include_router\\|app\\.add_\\|@app\\." main.py',
        "python_fallback": False,
    },
    "cmd5_agent_instantiation": {
        "desc": "Agent 实例化的全部位置",
        "win": None,
        "unix": 'grep -rn "MasterAgent()\\|UnifiedMasterAgent()\\|get_master_agent\\|get_agent_master" --include="*.py" --exclude-dir=.git --exclude-dir=.venv . 2>/dev/null | grep -v "def \\|test_\\|_DEPRECATED"',
        "python_fallback": True,
    },
    "cmd6_test_collection": {
        "desc": "测试现状",
        "win": "pytest tests/ --collect-only -q 2>nul",
        "unix": "pytest tests/ --collect-only -q 2>/dev/null | head -80",
        "python_fallback": False,
    },
    "cmd7_v3_routes": {
        "desc": "v3 路由冲突点",
        "win": 'findstr /n "prefix.*v3 /v3/ v3_" main.py',
        "unix": 'grep -n "prefix.*v3\\|/v3/\\|v3_" main.py | head -30',
        "python_fallback": False,
    },
    "cmd8_alembic_versions": {
        "desc": "Alembic 迁移文件完整列表",
        "win": "dir alembic\\versions\\*.py",
        "unix": "ls -lh alembic/versions/*.py 2>/dev/null | sort -k6,7",
        "python_fallback": False,
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Python fallback 实现（不依赖 shell 命令）
# ─────────────────────────────────────────────────────────────────────────────

def py_find_agent_classes(root: Path) -> str:
    """命令1 Python 实现"""
    results = []
    exclude = {"__pycache__", ".venv", ".git", "venv", "env", "node_modules"}
    for path in sorted(root.rglob("*.py")):
        if any(e in path.parts for e in exclude):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "class " in text and "Agent" in text:
                import re
                if re.search(r"class\s+\w*Agent\w*", text):
                    results.append(str(path.relative_to(root)))
        except OSError:
            continue
    return "\n".join(results)


def py_find_registry(root: Path) -> str:
    """命令2 Python 实现"""
    import re
    results = []
    exclude = {"__pycache__", ".venv", ".git", "venv", "env", "node_modules"}
    patterns = [
        re.compile(r"class\s+\w*Registry"),
        re.compile(r"AgentRegistry"),
        re.compile(r"register_agent"),
        re.compile(r"@agent\b"),
    ]
    for path in sorted(root.rglob("*.py")):
        if any(e in path.parts for e in exclude):
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            rel = str(path.relative_to(root))
            for i, line in enumerate(lines, 1):
                if any(p.search(line) for p in patterns):
                    results.append(f"{rel}:{i}:{line.rstrip()}")
        except OSError:
            continue
    return "\n".join(results)


def py_agent_signatures(root: Path) -> str:
    """命令3 Python 实现"""
    import re
    targets = [
        "core/master_agent_v0.py",
        "core/master_agent_unified.py",
        "core/agents/master_agent.py",
    ]
    results = []
    sig_pattern = re.compile(r"^(class |    def |def )")
    for rel_path in targets:
        full = root / rel_path
        if not full.exists():
            results.append(f"\n# ── {rel_path}: 文件不存在 ──")
            continue
        results.append(f"\n# ══════════ {rel_path} ══════════")
        try:
            lines = full.read_text(encoding="utf-8", errors="ignore").splitlines()
            for i, line in enumerate(lines, 1):
                if sig_pattern.match(line):
                    results.append(f"{i}: {line.rstrip()}")
        except OSError:
            results.append(f"# 读取失败")
    return "\n".join(results)


def py_agent_instantiation(root: Path) -> str:
    """命令5 Python 实现"""
    import re
    results = []
    exclude = {"__pycache__", ".venv", ".git", "venv", "env", "node_modules",
               "tests", "_DEPRECATED"}
    patterns = [
        re.compile(r"MasterAgent\(\)"),
        re.compile(r"UnifiedMasterAgent\(\)"),
        re.compile(r"get_master_agent\b"),
        re.compile(r"get_agent_master\b"),
    ]
    skip = re.compile(r"^\s*(def |#)")
    for path in sorted(root.rglob("*.py")):
        if any(e in str(path) for e in exclude):
            continue
        if "test_" in path.name:
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            rel = str(path.relative_to(root))
            for i, line in enumerate(lines, 1):
                if skip.match(line):
                    continue
                if any(p.search(line) for p in patterns):
                    results.append(f"{rel}:{i}:{line.rstrip()}")
        except OSError:
            continue
    return "\n".join(results)


# ─────────────────────────────────────────────────────────────────────────────
# 执行命令
# ─────────────────────────────────────────────────────────────────────────────

def run_command(name: str, config: dict, root: Path) -> str:
    """执行单条诊断命令，返回输出文本"""
    desc = config["desc"]
    print(f"  执行: {desc} ...", end=" ", flush=True)

    # 优先使用 Python fallback
    if config.get("python_fallback"):
        fallback_fn = {
            "cmd1_agent_class_locations": py_find_agent_classes,
            "cmd2_registry_mechanism":    py_find_registry,
            "cmd3_masteragent_signatures": py_agent_signatures,
            "cmd5_agent_instantiation":   py_agent_instantiation,
        }.get(name)
        if fallback_fn:
            try:
                result = fallback_fn(root)
                print("✅ (Python)")
                return result if result else "(空结果)"
            except Exception as e:
                print(f"⚠️  Python fallback 失败: {e}")

    # Shell 命令
    cmd = config["win"] if IS_WINDOWS else config["unix"]
    if not cmd:
        print("⏭️  跳过（无对应命令）")
        return "(跳过)"

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            cwd=str(root),
            timeout=30,
        )
        output = result.stdout + (result.stderr if result.returncode != 0 else "")
        print("✅")
        return output.strip() if output.strip() else "(空结果)"
    except subprocess.TimeoutExpired:
        print("⏱️  超时")
        return "(命令超时)"
    except Exception as e:
        print(f"❌ 失败: {e}")
        return f"(命令执行失败: {e})"


# ─────────────────────────────────────────────────────────────────────────────
# 采集额外 Agent 文件（自动扫描）
# ─────────────────────────────────────────────────────────────────────────────

def find_additional_agent_files(root: Path) -> list:
    """自动找出所有含 Agent 类的 .py 文件（已知清单之外的）"""
    import re
    agent_pattern = re.compile(r"class\s+\w*Agent\w*")
    exclude = {"__pycache__", ".venv", ".git", "venv", "env",
               "node_modules", "alembic", "migrations"}
    found = []
    known = set(ALL_FILE_TARGETS)
    for path in sorted(root.rglob("*.py")):
        if any(e in path.parts for e in exclude):
            continue
        rel = str(path.relative_to(root)).replace("\\", "/")
        if rel in known:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if agent_pattern.search(text):
                found.append(rel)
        except OSError:
            continue
    return found


def find_alembic_migrations(root: Path) -> list:
    """找出所有 alembic migration 文件"""
    alembic_dir = root / "alembic" / "versions"
    if not alembic_dir.exists():
        return []
    return sorted(
        str(p.relative_to(root)).replace("\\", "/")
        for p in alembic_dir.glob("*.py")
        if not p.name.startswith("__")
    )


# ─────────────────────────────────────────────────────────────────────────────
# 主程序
# ─────────────────────────────────────────────────────────────────────────────

def main():
    root = Path.cwd()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"surgery_pack_{ts}.zip"
    manifest = {
        "generated_at": datetime.now().isoformat(),
        "project_root": str(root),
        "files_collected": [],
        "files_missing": [],
        "auto_discovered": [],
        "commands": {},
    }

    print("=" * 60)
    print(" 行健平台最优架构手术 — 文件采集脚本")
    print(f" 项目根目录: {root}")
    print(f" 输出文件: {zip_name}")
    print("=" * 60)

    # ── 1. 执行诊断命令 ──────────────────────────────────────────
    print("\n📊 执行诊断命令 (共8条)...")
    cmd_outputs = {}
    for name, config in COMMANDS.items():
        output = run_command(name, config, root)
        cmd_outputs[name] = {
            "description": config["desc"],
            "output": output,
        }

    # ── 2. 自动发现额外 Agent 文件 ───────────────────────────────
    print("\n🔍 自动扫描额外 Agent 文件...")
    extra_agent_files = find_additional_agent_files(root)
    if extra_agent_files:
        print(f"  发现 {len(extra_agent_files)} 个额外文件:")
        for f in extra_agent_files:
            print(f"    {f}")
    else:
        print("  无额外文件")

    # ── 3. 找出所有 Alembic Migration ───────────────────────────
    print("\n📁 扫描 Alembic Migration 文件...")
    migration_files = find_alembic_migrations(root)
    if migration_files:
        print(f"  发现 {len(migration_files)} 个迁移文件")
        # 只包含关键迁移（054/058 及最近5个）
        key_migrations = []
        for f in migration_files:
            fname = Path(f).name
            if any(fname.startswith(n) for n in ["054", "055", "056", "057", "058", "059"]):
                key_migrations.append(f)
        # 最新的3个
        recent = migration_files[-3:] if len(migration_files) > 3 else migration_files
        key_migrations = list(set(key_migrations + recent))
        print(f"  关键迁移文件 ({len(key_migrations)} 个): {[Path(f).name for f in key_migrations]}")
    else:
        key_migrations = []
        print("  alembic/versions/ 目录未找到")

    # ── 4. 确定所有要打包的文件 ──────────────────────────────────
    all_targets = list(set(
        ALL_FILE_TARGETS
        + extra_agent_files
        + key_migrations
    ))

    # ── 5. 生成命令输出文本文件 ──────────────────────────────────
    cmd_output_text = []
    cmd_output_text.append("# 行健平台最优架构手术 — 诊断命令输出")
    cmd_output_text.append(f"# 生成时间: {datetime.now().isoformat()}")
    cmd_output_text.append(f"# 项目根: {root}")
    cmd_output_text.append("")

    for name, data in cmd_outputs.items():
        cmd_output_text.append(f"{'='*60}")
        cmd_output_text.append(f"## {name}: {data['description']}")
        cmd_output_text.append(f"{'='*60}")
        cmd_output_text.append(data["output"])
        cmd_output_text.append("")

    cmd_output_content = "\n".join(cmd_output_text)

    # 额外 Agent 文件清单
    extra_files_text = "\n".join([
        "# 自动发现的额外 Agent 文件",
        f"# 数量: {len(extra_agent_files)}",
        "",
    ] + extra_agent_files)

    # ── 6. 打包 ──────────────────────────────────────────────────
    print(f"\n📦 开始打包...")
    collected = []
    missing = []

    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zf:

        # 命令输出
        zf.writestr("_commands_output.txt", cmd_output_content)
        zf.writestr("_extra_agent_files.txt", extra_files_text)
        print(f"  ✅ 诊断命令输出 (_commands_output.txt)")

        # 所有目标文件
        for rel_path in sorted(set(all_targets)):
            full_path = root / rel_path.replace("/", os.sep)
            if full_path.exists():
                zf.write(full_path, rel_path)
                collected.append(rel_path)
                size = full_path.stat().st_size
                print(f"  ✅ {rel_path} ({size:,} bytes)")
            else:
                missing.append(rel_path)

        # Manifest
        manifest["files_collected"] = collected
        manifest["files_missing"] = missing
        manifest["auto_discovered"] = extra_agent_files
        manifest["migration_files_included"] = key_migrations
        zf.writestr("_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

    # ── 7. 汇总报告 ──────────────────────────────────────────────
    zip_size = Path(zip_name).stat().st_size / 1024
    print(f"\n{'='*60}")
    print(f" 打包完成: {zip_name} ({zip_size:.1f} KB)")
    print(f" 已收集: {len(collected)} 个文件")
    print(f" 缺失:   {len(missing)} 个文件")
    if missing:
        print(f"\n 缺失文件列表（可能路径不同，或尚未创建）:")
        for f in sorted(missing):
            print(f"   - {f}")
    print(f"\n 下一步: 将 {zip_name} 上传到新对话")
    print(f"         连同「新对话开场文档.md」一起发送")
    print("=" * 60)

    return zip_name


if __name__ == "__main__":
    main()
