#!/usr/bin/env python3
"""CI 静态安全检查 — 支持 static_checks_config.yaml 排除规则"""
import os, re, sys, yaml

# --------------- 参数解析 ---------------
fast_mode = "--fast" in sys.argv
count_only = "--count-only" in sys.argv

# --------------- 加载排除配置 ---------------
EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
                "alembic", "migrations", "dify", "_archived_temp_code",
                ".egg-info", "tcm_ortho_package", "cicd_staging"}
EXCLUDE_FILES = set()

config_path = "static_checks_config.yaml"
if os.path.exists(config_path):
    try:
        with open(config_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        for p in cfg.get("exclude_patterns", []):
            EXCLUDE_DIRS.add(p.rstrip("/"))
        for p in cfg.get("exclude_files", []):
            EXCLUDE_FILES.add(p)
    except Exception:
        pass  # config parse failure — use defaults

errors = []

# --------------- Check 1: No f-string SQL (injection risk) ---------------
for root, dirs, files in os.walk("."):
    # Prune excluded directories in-place
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
    for f in files:
        if not f.endswith(".py") or f in EXCLUDE_FILES:
            continue
        path = os.path.join(root, f)
        try:
            for i, line in enumerate(open(path, encoding="utf-8", errors="ignore"), 1):
                if re.search(r'\.execute\(f["\']', line):
                    errors.append(f"  {path}:{i}: f-string SQL (use parameterized queries)")
        except Exception:
            pass

# --------------- Check 2: RBAC role list consistency ---------------
# Detect role lists containing "promoter" but missing "supervisor" (or vice versa)
# These are always L4 peers and should appear together.
if not fast_mode:
    _rbac_pattern = re.compile(
        r'(?:role\.in_\(|\.role\.value\s+(?:not\s+)?in\s+|"role"\s*:\s*)\[([^\]]+)\]'
    )
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if not f.endswith(".py") or f in EXCLUDE_FILES:
                continue
            path = os.path.join(root, f)
            try:
                for i, line in enumerate(open(path, encoding="utf-8", errors="ignore"), 1):
                    m = _rbac_pattern.search(line)
                    if not m:
                        continue
                    content = m.group(1).lower()
                    has_promoter = "promoter" in content
                    has_supervisor = "supervisor" in content
                    if has_promoter and not has_supervisor:
                        errors.append(f"  {path}:{i}: Role list has 'promoter' but missing 'supervisor' (L4 peers)")
                    elif has_supervisor and not has_promoter:
                        errors.append(f"  {path}:{i}: Role list has 'supervisor' but missing 'promoter' (L4 peers)")
            except Exception:
                pass

# --------------- Check 3: CORS wildcard ---------------
if not fast_mode:
    for f in ["api/main.py", "main.py"]:
        if os.path.exists(f):
            content = open(f, encoding="utf-8", errors="ignore").read()
            if 'allow_origins=["*"]' in content or "allow_origins=['*']" in content:
                errors.append(f"  {f}: CORS allow_origins=[\"*\"] detected")

# --------------- Output ---------------
if count_only:
    print(len(errors))
    sys.exit(1 if errors else 0)

if errors:
    print(f"FAIL: {len(errors)} issues found:")
    for e in errors:
        print(e)
    sys.exit(1)

print("PASS: Static checks clean")
