#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_journey_null.py — 容器内定位并修复 journey/stage/transitions 500

用法 (宿主机执行):

  # 1. 先定位 BUG 位置
  docker exec bhp-api python /app/fix_journey_null.py --locate

  # 2. 查看修复方案
  docker exec bhp-api python /app/fix_journey_null.py --preview

  # 3. 执行修复
  docker exec bhp-api python /app/fix_journey_null.py --fix

  # 4. 验证
  curl -s -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/journey/stage/transitions | python -m json.tool

或者直接把此脚本 cp 进容器:
  docker cp fix_journey_null.py bhp-api:/app/fix_journey_null.py
  docker exec bhp-api python /app/fix_journey_null.py --locate
"""

import argparse
import ast
import os
import re
import sys
import glob


def find_journey_file():
    """在容器 /app 中找到 journey 相关 API 文件"""
    candidates = []
    for root, dirs, files in os.walk("/app"):
        # 跳过虚拟环境和缓存
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".venv", "venv", "node_modules", ".git")]
        for f in files:
            if f.endswith(".py"):
                fpath = os.path.join(root, f)
                try:
                    with open(fpath, "r", encoding="utf-8") as fh:
                        content = fh.read()
                        if "stage/transitions" in content or "stage_transitions" in content:
                            candidates.append(fpath)
                except Exception:
                    pass
    return candidates


def locate_bug(filepath):
    """定位 .first() 后未做空值检查的代码"""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 找到 transitions 端点
    in_transitions = False
    endpoint_start = -1
    endpoint_end = -1
    first_calls = []  # (line_no, line_content)
    attr_accesses = []  # .first() 返回值后的属性访问

    for i, line in enumerate(lines):
        # 找到路由装饰器
        if "transitions" in line and ("@router" in line or "def " in line):
            in_transitions = True
            endpoint_start = i
        elif in_transitions:
            # 找到下一个路由装饰器 = 当前端点结束
            if line.strip().startswith("@router.") and i > endpoint_start + 2:
                endpoint_end = i
                break
            # 找 .first() 调用
            if ".first()" in line:
                first_calls.append((i + 1, line.rstrip()))
            # 找属性访问 (variable.attribute)
            if first_calls and "." in line and "=" not in line.split(".")[0]:
                attr_accesses.append((i + 1, line.rstrip()))

    if endpoint_end == -1:
        endpoint_end = len(lines)

    return {
        "file": filepath,
        "endpoint_range": (endpoint_start + 1, endpoint_end + 1),
        "first_calls": first_calls,
        "code": lines[endpoint_start:endpoint_end],
    }


def find_null_unsafe_pattern(code_lines, start_line):
    """分析代码找出 .first() → 直接访问属性 的不安全模式"""
    results = []
    var_from_first = None

    for i, line in enumerate(code_lines):
        stripped = line.strip()
        line_no = start_line + i

        # 检测: variable = query.first()
        m = re.match(r"(\w+)\s*=\s*.*\.first\(\)", stripped)
        if m:
            var_from_first = m.group(1)
            results.append({
                "line": line_no,
                "type": "first_call",
                "var": var_from_first,
                "code": stripped,
            })
            continue

        # 检测: 是否在 .first() 之后有 if not var / if var is None 保护
        if var_from_first:
            if f"if not {var_from_first}" in stripped or f"if {var_from_first} is None" in stripped:
                results.append({
                    "line": line_no,
                    "type": "null_check",
                    "var": var_from_first,
                    "code": stripped,
                    "safe": True,
                })
                var_from_first = None  # 已保护
                continue

            # 检测: 直接使用 var.attribute (未保护)
            if f"{var_from_first}." in stripped and "=" not in stripped.split(f"{var_from_first}.")[0]:
                results.append({
                    "line": line_no,
                    "type": "unsafe_access",
                    "var": var_from_first,
                    "code": stripped,
                    "safe": False,
                })

    return results


def generate_fix(filepath, info):
    """生成修复后的代码"""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    start = info["endpoint_range"][0] - 1
    end = info["endpoint_range"][1] - 1
    code = lines[start:end]

    # 找到 .first() 行
    fixed_code = []
    skip_next_attr = False

    for i, line in enumerate(code):
        stripped = line.strip()

        # 在 .first() 行之后插入空值保护
        m = re.match(r"(\s*)(\w+)\s*=\s*.*\.first\(\)", line.rstrip())
        if m:
            indent = m.group(1)
            var = m.group(2)
            fixed_code.append(line)
            # 插入空值检查
            fixed_code.append(f"{indent}if not {var}:\n")
            fixed_code.append(f'{indent}    return {{"transitions": [], "current_stage": None, "message": "用户尚未开始旅程"}}\n')
            fixed_code.append(f"{indent}\n")
            continue

        fixed_code.append(line)

    return start, end, fixed_code


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--locate", action="store_true", help="定位 BUG")
    parser.add_argument("--preview", action="store_true", help="预览修复")
    parser.add_argument("--fix", action="store_true", help="执行修复")
    args = parser.parse_args()

    if not any([args.locate, args.preview, args.fix]):
        args.locate = True

    # 找文件
    files = find_journey_file()
    if not files:
        print("❌ 未找到包含 stage/transitions 的 Python 文件")
        print("   尝试手动查找: grep -rn 'transitions' /app/api/")
        sys.exit(1)

    print(f"📂 找到 {len(files)} 个相关文件:")
    for f in files:
        print(f"   {f}")

    for filepath in files:
        info = locate_bug(filepath)
        if not info["code"]:
            continue

        print(f"\n{'='*60}")
        print(f"📍 {filepath}")
        print(f"   端点范围: L{info['endpoint_range'][0]}-L{info['endpoint_range'][1]}")
        print(f"   .first() 调用: {len(info['first_calls'])}个")
        for ln, code in info["first_calls"]:
            print(f"     L{ln}: {code.strip()}")

        # 分析安全性
        analysis = find_null_unsafe_pattern(info["code"], info["endpoint_range"][0])
        unsafe = [a for a in analysis if a.get("safe") == False]
        if unsafe:
            print(f"\n   🔴 不安全访问 ({len(unsafe)}个):")
            for u in unsafe:
                print(f"     L{u['line']}: {u['code']}  ← {u['var']} 可能为 None!")
        else:
            safe_checks = [a for a in analysis if a.get("safe") == True]
            if safe_checks:
                print(f"\n   ✅ 已有空值保护")
            else:
                print(f"\n   ⚠️ 需要人工检查 .first() 后的代码")

        if args.locate:
            # 打印端点代码
            print(f"\n   端点代码:")
            for i, line in enumerate(info["code"]):
                ln = info["endpoint_range"][0] + i
                print(f"   {ln:4d} | {line.rstrip()}")

        if args.preview or args.fix:
            start, end, fixed = generate_fix(filepath, info)
            print(f"\n   修复预览:")
            for line in fixed:
                print(f"   + {line.rstrip()}")

            if args.fix:
                # 写入修复
                with open(filepath, "r", encoding="utf-8") as f:
                    all_lines = f.readlines()
                all_lines[start:end] = fixed
                with open(filepath, "w", encoding="utf-8") as f:
                    f.writelines(all_lines)
                print(f"\n   ✅ 已写入修复到 {filepath}")
                print(f"   ⚠️ 需要重启服务: kill -HUP 1 或重启容器")


if __name__ == "__main__":
    main()
