#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX-09 补丁: 添加 check_user_data_access 导入到 learning_api.py

用法:
  python fix09_add_import.py [learning_api.py 路径]

默认: api/learning_api.py
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime

target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("api/learning_api.py")

if not target.exists():
    print(f"❌ 文件不存在: {target}")
    sys.exit(1)

content = target.read_text("utf-8")

# ── 检查是否已导入 ──
if "from core.access_control import check_user_data_access" in content:
    print(f"✅ {target} 已有 import, 无需修改")
    sys.exit(0)

# ── 检查函数调用是否存在 ──
call_count = content.count("check_user_data_access(")
if call_count == 0:
    print(f"⚠ {target} 中未发现 check_user_data_access() 调用, 跳过")
    sys.exit(0)

print(f"发现 {call_count} 处调用, 缺少 import → 添加中...")

# ── 备份 ──
bak = target.with_suffix(f".py.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}")
shutil.copy2(target, bak)
print(f"备份: {bak}")

# ── 注入 import ──
# 策略: 在 "from api.dependencies import get_current_user" 之后添加
import_line = "from core.access_control import check_user_data_access"

insertion_points = [
    "from api.dependencies import get_current_user",
    "from core.database import get_db",
    "from sqlalchemy import func",
]

inserted = False
for anchor in insertion_points:
    if anchor in content:
        content = content.replace(
            anchor,
            f"{anchor}\n{import_line}",
            1,
        )
        inserted = True
        print(f"✅ import 已添加 (在 '{anchor}' 之后)")
        break

if not inserted:
    # 降级: 添加到文件头部 import 区域
    lines = content.split("\n")
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("from ") or line.startswith("import "):
            insert_idx = i + 1
    lines.insert(insert_idx, import_line)
    content = "\n".join(lines)
    print(f"✅ import 已添加 (在第 {insert_idx+1} 行)")

target.write_text(content, "utf-8")

# ── 验证 ──
verify = target.read_text("utf-8")
has_import = import_line in verify
has_calls = verify.count("check_user_data_access(") == call_count

print()
print("═" * 50)
print(f"  import 存在: {'✅' if has_import else '❌'}")
print(f"  调用数量: {call_count} 处 {'✅' if has_calls else '❌'}")
print("═" * 50)

if has_import and has_calls:
    print("✅ FIX-09 补丁完成")
else:
    print("⚠ 请手动检查")
