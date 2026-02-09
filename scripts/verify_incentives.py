"""
BHP 激励体系一致性校验 (V003)
运行: python3 verify_incentives.py
校验: milestones.json + badges.json + point_events.json 交叉一致性
"""

import json
from pathlib import Path

PASS = "✅"
FAIL = "❌"
errors = []

def check(cond, msg):
    if cond:
        print(f"  {PASS} {msg}")
    else:
        print(f"  {FAIL} {msg}")
        errors.append(msg)

base = Path(__file__).parent.parent / "configs"
milestones = json.loads((base / "milestones.json").read_text())
badges_data = json.loads((base / "badges.json").read_text())
events_data = json.loads((base / "point_events.json").read_text())

ms_list = milestones["milestones"]
pools = milestones["flip_card_pools"]
badge_cats = badges_data["badge_categories"]

# 收集所有已定义的badge_id
all_badge_ids = set()
for cat_key, cat in badge_cats.items():
    for b in cat.get("badges", []):
        all_badge_ids.add(b["id"])
    for b in cat.get("combo_badges", []):
        all_badge_ids.add(b["id"])

# 收集所有已定义的point action
all_actions = set()
for section in events_data["events"]:
    for item in section["items"]:
        all_actions.add(item["action"])

print("=" * 60)
print("BHP 激励体系一致性校验 (V003)")
print("=" * 60)

# ═══ 1. 里程碑完整性 ═══
print("\n📋 1. 里程碑链完整性")
expected = ["FIRST_LOGIN", "DAY_3", "DAY_7", "DAY_14", "DAY_21", "DAY_30"]
actual = [m["key"] for m in ms_list]
for key in expected:
    check(key in actual, f"里程碑 {key} 存在")

# ═══ 2. 积分递增 ═══
print("\n📋 2. 里程碑积分/学分递增")
for i in range(len(ms_list) - 1):
    m1, m2 = ms_list[i], ms_list[i+1]
    p1 = sum(p["amount"] for p in m1["rewards"]["points"])
    p2 = sum(p["amount"] for p in m2["rewards"]["points"])
    check(p2 >= p1, f"{m1['key']}({p1}) → {m2['key']}({p2}) 积分递增")
    c1 = m1["rewards"]["credits"]
    c2 = m2["rewards"]["credits"]
    check(c2 >= c1, f"{m1['key']}({c1}) → {m2['key']}({c2}) 学分递增")

# ═══ 3. 徽章引用一致性 ═══
print("\n📋 3. 里程碑引用的徽章都已定义")
for m in ms_list:
    for badge_id in m["rewards"].get("badges", []):
        check(badge_id in all_badge_ids, f"{m['key']} → {badge_id} 存在于badges.json")

# ═══ 4. 积分action引用 ═══
print("\n📋 4. 里程碑积分action检查")
milestone_actions = set()
for m in ms_list:
    for pt in m["rewards"]["points"]:
        milestone_actions.add(pt["action"])

# 里程碑的action是特有的(milestone_前缀),不需要在point_events.json中
for action in milestone_actions:
    if action.startswith("milestone_") or action.startswith("streak_bonus"):
        # 这些是里程碑专有action,不在常规事件表中
        check(True, f"{action} 是里程碑专有action(OK)")
    else:
        check(action in all_actions, f"{action} 存在于point_events.json")

# ═══ 5. 翻牌池一致性 ═══
print("\n📋 5. 翻牌池引用一致性")
for m in ms_list:
    for item in m["rewards"].get("items", []):
        if item["type"] == "flip_card_reward":
            pool_id = item["pool"]
            check(pool_id in pools, f"{m['key']} 翻牌池 {pool_id} 已定义")
            if pool_id in pools:
                pool = pools[pool_id]
                show = item.get("show", 3)
                check(len(pool["items"]) >= show,
                      f"  池 {pool_id} 有{len(pool['items'])}项 ≥ 展示{show}项")

# ═══ 6. 学时徽章递增 ═══
print("\n📋 6. 学时徽章递增")
hour_badges = badge_cats["learning_hours"]["badges"]
for i in range(len(hour_badges) - 1):
    b1, b2 = hour_badges[i], hour_badges[i+1]
    h1 = b1["condition"]["training_hours_gte"]
    h2 = b2["condition"]["training_hours_gte"]
    check(h2 > h1, f"{b1['name']}({h1}h) < {b2['name']}({h2}h)")

# ═══ 7. 模块徽章tier递增 ═══
print("\n📋 7. 模块徽章tier一致性")
mod_badges = badge_cats["module_mastery"]["badges"]
for module in ["M1_BEHAVIOR", "M2_LIFESTYLE", "M3_MINDSET", "M4_COACHING"]:
    mb = [b for b in mod_badges if b.get("module") == module]
    mb.sort(key=lambda x: x.get("tier", 0))
    for i in range(len(mb) - 1):
        t1_credits = mb[i]["condition"]["module_credits_gte"]
        t2_credits = mb[i+1]["condition"]["module_credits_gte"]
        check(t2_credits > t1_credits,
              f"{module} tier{mb[i].get('tier')}({t1_credits}) < tier{mb[i+1].get('tier')}({t2_credits})")

# ═══ 8. 晋级仪式完整性 ═══
print("\n📋 8. 晋级仪式完整性")
ceremony_configs = badge_cats["promotion_ceremony"]["ceremony_configs"]
expected_transitions = [
    ("observer", "grower"), ("grower", "sharer"), ("sharer", "coach"),
    ("coach", "promoter"), ("promoter", "master")
]
for fr, to in expected_transitions:
    found = any(c["from_role"] == fr and c["to_role"] == to for c in ceremony_configs)
    check(found, f"{fr}→{to} 晋级仪式配置存在")

# ═══ 9. 仪式都有对应徽章 ═══
print("\n📋 9. 每个晋级仪式有对应徽章")
promo_badges = badge_cats["promotion_ceremony"]["badges"]
for cc in ceremony_configs:
    to_role = cc["to_role"]
    has_badge = any(b["condition"]["role"] == to_role for b in promo_badges)
    check(has_badge, f"{cc['ceremony_name']} ({to_role}) 有对应徽章")

# ═══ 10. 稀有度分布 ═══
print("\n📋 10. 徽章稀有度分布合理性")
rarity_count = {"common": 0, "uncommon": 0, "rare": 0, "epic": 0, "legendary": 0}
for cat_key, cat in badge_cats.items():
    for b in cat.get("badges", []):
        r = b.get("rarity", "common")
        rarity_count[r] = rarity_count.get(r, 0) + 1
    for b in cat.get("combo_badges", []):
        r = b.get("rarity", "common")
        rarity_count[r] = rarity_count.get(r, 0) + 1

total_badges = sum(rarity_count.values())
print(f"  总徽章数: {total_badges}")
for r, c in rarity_count.items():
    pct = (c / total_badges * 100) if total_badges > 0 else 0
    print(f"  {r}: {c} ({pct:.0f}%)")

# 稀有度应该是金字塔形
check(rarity_count["common"] >= rarity_count["uncommon"],
      "common ≥ uncommon (金字塔底)")
check(rarity_count["legendary"] <= rarity_count["epic"],
      "legendary ≤ epic (金字塔尖)")

# ═══ 汇总 ═══
print("\n" + "=" * 60)
if errors:
    print(f"❌ 发现 {len(errors)} 个错误:")
    for e in errors:
        print(f"   - {e}")
else:
    print("✅ 所有激励体系一致性检查通过!")
print("=" * 60)

import sys
sys.exit(1 if errors else 0)
