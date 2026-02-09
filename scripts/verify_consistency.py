"""
BHP平台 规则一致性校验脚本
运行方式: python3 verify_consistency.py
作用: 校验 promotion_rules.json / point_events.json / course_modules.json 三套配置的内部一致性
"""

import json
import sys
from pathlib import Path

PASS = "✅"
FAIL = "❌"
WARN = "⚠️"
errors = []
warnings = []

def check(condition, msg):
    if condition:
        print(f"  {PASS} {msg}")
    else:
        print(f"  {FAIL} {msg}")
        errors.append(msg)

def warn(condition, msg):
    if condition:
        print(f"  {PASS} {msg}")
    else:
        print(f"  {WARN} {msg}")
        warnings.append(msg)

# ── 加载配置 ──

base = Path(__file__).parent.parent / "configs"
rules = json.loads((base / "promotion_rules.json").read_text())["rules"]
events_data = json.loads((base / "point_events.json").read_text())["events"]
modules_data = json.loads((base / "course_modules.json").read_text())

all_events = []
for section in events_data:
    all_events.extend(section["items"])

mandatory = modules_data["mandatory_modules"]

# 角色晋升链
ROLE_CHAIN = ["observer", "grower", "sharer", "coach", "promoter", "master"]
ROLE_LEVEL = {r: i for i, r in enumerate(ROLE_CHAIN)}

print("=" * 60)
print("BHP 规则一致性校验")
print("=" * 60)

# ═══════════════════════════════════════
# 1. 晋级规则内部一致性
# ═══════════════════════════════════════
print("\n📋 1. 晋级规则链完整性")

rule_map = {r["from_role"]: r for r in rules}
for i in range(len(ROLE_CHAIN) - 1):
    fr, to = ROLE_CHAIN[i], ROLE_CHAIN[i + 1]
    check(fr in rule_map, f"{fr}→{to} 晋级规则存在")
    if fr in rule_map:
        check(rule_map[fr]["to_role"] == to, f"{fr}→{to} 目标角色正确")

print("\n📋 2. 学分递增检查")
for i in range(len(rules) - 1):
    r1, r2 = rules[i], rules[i + 1]
    check(r2["credits"]["total_min"] > r1["credits"]["total_min"],
          f"{r1['display']}({r1['credits']['total_min']}) < {r2['display']}({r2['credits']['total_min']}) 总学分递增")
    for m in ["m1_min", "m2_min", "m3_min", "m4_min"]:
        check(r2["credits"][m] >= r1["credits"][m],
              f"  {m}: {r1['credits'][m]} → {r2['credits'][m]} 递增")

print("\n📋 3. 积分递增检查")
for i in range(len(rules) - 1):
    r1, r2 = rules[i], rules[i + 1]
    for p in ["growth_min", "contribution_min", "influence_min"]:
        check(r2["points"][p] >= r1["points"][p],
              f"{r1['display']}→{r2['display']} {p}: {r1['points'][p]} → {r2['points'][p]}")

# ═══════════════════════════════════════
# 2. 学分 = 必修 + 选修 一致性
# ═══════════════════════════════════════
print("\n📋 4. 必修学分 + 选修 = 总学分 一致性")

for r in rules:
    c = r["credits"]
    mandatory_sum = c["m1_min"] + c["m2_min"] + c["m3_min"] + c["m4_min"]
    check(mandatory_sum == c["mandatory_min"],
          f"{r['display']} 必修分项之和({mandatory_sum}) = mandatory_min({c['mandatory_min']})")
    check(c["total_min"] == c["mandatory_min"] + c["elective_min"],
          f"{r['display']} total({c['total_min']}) = mandatory({c['mandatory_min']}) + elective({c['elective_min']})")

# ═══════════════════════════════════════
# 3. 课程模块学分 ≥ 必修要求
# ═══════════════════════════════════════
print("\n📋 5. 模块种子学分 ≥ 层级必修要求 (累计制)")

# 学分是累计的: L2→L3的要求 = L0 + L1 + L2 模块之和
cumulative = {}
for role in ROLE_CHAIN:
    if role not in mandatory:
        break
    mods = mandatory[role]
    for mt in ["M1_BEHAVIOR", "M2_LIFESTYLE", "M3_MINDSET", "M4_COACHING"]:
        key = mt
        prev = cumulative.get(key, 0)
        add = sum(m["credit_value"] for m in mods if m["module_type"] == mt)
        cumulative[key] = prev + add

    total_cum = sum(cumulative.values())
    # find the promotion rule FROM this role
    if role in rule_map:
        r = rule_map[role]
        check(cumulative.get("M1_BEHAVIOR", 0) >= r["credits"]["m1_min"],
              f"{r['display']} M1 累计({cumulative.get('M1_BEHAVIOR',0)}) ≥ 要求({r['credits']['m1_min']})")
        check(cumulative.get("M2_LIFESTYLE", 0) >= r["credits"]["m2_min"],
              f"{r['display']} M2 累计({cumulative.get('M2_LIFESTYLE',0)}) ≥ 要求({r['credits']['m2_min']})")
        check(cumulative.get("M3_MINDSET", 0) >= r["credits"]["m3_min"],
              f"{r['display']} M3 累计({cumulative.get('M3_MINDSET',0)}) ≥ 要求({r['credits']['m3_min']})")
        check(cumulative.get("M4_COACHING", 0) >= r["credits"]["m4_min"],
              f"{r['display']} M4 累计({cumulative.get('M4_COACHING',0)}) ≥ 要求({r['credits']['m4_min']})")
        total_mandatory = sum(cumulative.values())
        check(total_mandatory >= r["credits"]["mandatory_min"],
              f"{r['display']} 必修累计({total_mandatory}) ≥ 要求({r['credits']['mandatory_min']})")

# ═══════════════════════════════════════
# 4. 积分事件角色权限一致性
# ═══════════════════════════════════════
print("\n📋 6. 积分事件角色权限检查")

for evt in all_events:
    roles = evt["eligible_roles"]
    if "all" in roles:
        continue
    for role_str in roles:
        clean = role_str.replace("+", "")
        check(clean in ROLE_CHAIN or clean in ["all"],
              f"事件 {evt['action']} 角色 '{role_str}' 在有效角色列表中")

print("\n📋 7. 积分-学分联动事件检查")
dual_write = [e for e in all_events if e.get("triggers_credit")]
for evt in dual_write:
    check(evt["point_type"] == "growth",
          f"联动事件 {evt['action']} 是成长积分(不应联动贡献/影响力)")

non_dual = [e for e in all_events if not e.get("triggers_credit")]
for evt in non_dual:
    check("credit_note" not in evt,
          f"非联动事件 {evt['action']} 不应有 credit_note 字段")

# ═══════════════════════════════════════
# 5. 同道者规则一致性
# ═══════════════════════════════════════
print("\n📋 8. 四同道者规则一致性")

for r in rules:
    comp = r["companions"]
    check(comp["graduated_min"] == 4,
          f"{r['display']} 四同道者要求 = {comp['graduated_min']}")
    mentee_role = comp["mentee_role"]
    from_role = r["from_role"]
    from_idx = ROLE_LEVEL.get(from_role, -1)
    mentee_idx = ROLE_LEVEL.get(mentee_role, -1)
    # L0特殊: invite模式,mentee也是observer
    if comp.get("mode") == "invite":
        check(mentee_role == from_role,
              f"{r['display']} 邀请模式: mentee({mentee_role}) = 同级(invite)")
    else:
        check(mentee_idx == from_idx - 1,
              f"{r['display']} 带教角色({mentee_role},L{mentee_idx}) = 自身({from_role},L{from_idx})的下一级")

# ═══════════════════════════════════════
# 6. 模块编码唯一性
# ═══════════════════════════════════════
print("\n📋 9. 模块编码唯一性")

all_codes = []
for role, mods in mandatory.items():
    for m in mods:
        all_codes.append(m["code"])

check(len(all_codes) == len(set(all_codes)),
      f"所有模块编码唯一 ({len(all_codes)} 个模块, {len(set(all_codes))} 个唯一编码)")

dups = [c for c in all_codes if all_codes.count(c) > 1]
if dups:
    print(f"    重复编码: {set(dups)}")

# ═══════════════════════════════════════
# 7. tier 分配逻辑检查
# ═══════════════════════════════════════
print("\n📋 10. 干预层(tier)分配逻辑")

for role, mods in mandatory.items():
    for m in mods:
        mt = m["module_type"]
        tier = m["tier"]
        if mt == "M1_BEHAVIOR":
            check(tier == "T1_PRESCRIPTION",
                  f"{m['code']} M1模块 → T1_PRESCRIPTION")
        elif mt == "M3_MINDSET":
            check(tier == "T3_GROWTH",
                  f"{m['code']} M3模块 → T3_GROWTH")

# ═══════════════════════════════════════
# 汇总
# ═══════════════════════════════════════
print("\n" + "=" * 60)
if errors:
    print(f"❌ 发现 {len(errors)} 个错误:")
    for e in errors:
        print(f"   - {e}")
else:
    print("✅ 所有一致性检查通过!")

if warnings:
    print(f"⚠️  {len(warnings)} 个警告:")
    for w in warnings:
        print(f"   - {w}")

print("=" * 60)
sys.exit(1 if errors else 0)
