"""
单元测试 — 教练快捷操作写入验证
验证目标: 本 Session 的核心修复 (detail.vue 内联 Modal)
  1. 发消息  → POST /api/v1/coach/students/{id}/notes  [消息]前缀  → 200
  2. 开处方  → POST /api/v1/coach/students/{id}/notes  [行为处方]前缀 → 200
  3. 写后可读 → GET  /api/v1/coach/students/{id}/notes → 200 + list
  4. 健康审核退回无 body → POST /api/v1/health-review/{id}/reject → 非422

运行方式:
  cd D:\\behavioral-health-project
  pytest "C:\\Users\\Administrator\\Desktop\\test\\单元imya.py" -v
  # 或直接:
  python "C:\\Users\\Administrator\\Desktop\\test\\单元imya.py"
"""

import sys
import os
import json

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import requests

BASE = "http://localhost:8000"

# ─── DB 自植入（保证队列非空）────────────────────────────────────────────────
try:
    import psycopg2
    _DB = dict(host="localhost", port=5432, dbname="bhp_db",
               user="bhp_user", password="bhp_password")
    HAS_DB = True
except Exception:
    HAS_DB = False

def seed_health_review_item(user_id=4, reviewer_role="coach", risk_level="medium"):
    if not HAS_DB:
        return None
    try:
        conn = psycopg2.connect(**_DB)
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO health_review_queue
              (user_id, reviewer_role, risk_level, status, ai_summary, created_at)
            VALUES (%s, %s, %s, 'pending', '单元测试植入条目', NOW())
            RETURNING id
        """, (user_id, reviewer_role, risk_level))
        row = cur.fetchone()
        conn.commit(); conn.close()
        return row[0] if row else None
    except Exception:
        return None
COACH_USER = {"username": "coach", "password": "Coach@2026"}

# ─── 颜色输出 ─────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"

_pass = _fail = _skip = 0

def ok(name):
    global _pass; _pass += 1
    print(f"  {GREEN}[PASS]{RESET} {name}")

def fail(name, detail=""):
    global _fail; _fail += 1
    print(f"  {RED}[FAIL]{RESET} {name}" + (f": {detail}" if detail else ""))

def skip(name, reason=""):
    global _skip; _skip += 1
    print(f"  {YELLOW}[SKIP]{RESET} {name}" + (f": {reason}" if reason else ""))

# ─── 公共登录 ─────────────────────────────────────────────────────────────────
def login(creds):
    r = requests.post(f"{BASE}/api/v1/auth/login", json=creds, timeout=8)
    if r.status_code != 200:
        return None
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ─── 测试块 ───────────────────────────────────────────────────────────────────

def test_coach_auth():
    print("\n─── 1. 教练登录 ───")
    h = login(COACH_USER)
    if h:
        ok("POST /api/v1/auth/login → 200")
    else:
        fail("POST /api/v1/auth/login", "无法获取 token")
    return h


def test_get_students(h):
    print("\n─── 2. 获取绑定学员 ───")
    r = requests.get(f"{BASE}/api/v1/coach/dashboard", headers=h, timeout=8)
    if r.status_code == 200:
        ok(f"GET /api/v1/coach/dashboard → 200")
    else:
        fail("GET /api/v1/coach/dashboard", r.status_code)
        return None

    students = r.json().get("students") or r.json().get("data", {}).get("students", [])
    if students:
        sid = students[0].get("id") or students[0].get("user_id")
        ok(f"学员列表非空，使用 student_id={sid}")
        return sid
    else:
        skip("获取学员 id", "dashboard 无绑定学员，跳过后续写入测试")
        return None


def test_send_message(h, sid):
    print("\n─── 3. 发消息 (内联Modal → notes) ───")
    payload = {"content": "[消息] 单元测试-验证内联发消息功能", "note_type": "supervision"}
    r = requests.post(f"{BASE}/api/v1/coach/students/{sid}/notes", json=payload, headers=h, timeout=8)
    if r.status_code == 200:
        ok(f"POST /api/v1/coach/students/{sid}/notes [消息] → 200")
    else:
        fail(f"POST notes [消息]", f"HTTP {r.status_code}: {r.text[:120]}")


def test_create_prescription(h, sid):
    print("\n─── 4. 开处方 (内联Modal → notes) ───")
    payload = {"content": "[行为处方] 单元测试-每日步行6000步", "note_type": "supervision"}
    r = requests.post(f"{BASE}/api/v1/coach/students/{sid}/notes", json=payload, headers=h, timeout=8)
    if r.status_code == 200:
        ok(f"POST /api/v1/coach/students/{sid}/notes [行为处方] → 200")
    else:
        fail(f"POST notes [行为处方]", f"HTTP {r.status_code}: {r.text[:120]}")


def test_read_notes(h, sid):
    print("\n─── 5. 督导笔记可读取 ───")
    r = requests.get(f"{BASE}/api/v1/coach/students/{sid}/notes", headers=h, timeout=8)
    if r.status_code != 200:
        fail(f"GET /api/v1/coach/students/{sid}/notes", f"HTTP {r.status_code}")
        return
    data = r.json()
    notes = data if isinstance(data, list) else data.get("items", data.get("notes", []))
    ok(f"GET notes → 200，共 {len(notes)} 条记录")


def test_health_review_reject_no_body(h):
    print("\n─── 6. 健康审核退回不发 body (422修复验证) ───")
    seed_health_review_item()   # ← 加这一行
    # 先获取队列中的一条记录
    r = requests.get(
        f"{BASE}/api/v1/health-review/queue?reviewer_role=coach&risk_level=medium",
        headers=h, timeout=8
    )
    if r.status_code != 200:
        skip("health-review 退回测试", f"队列获取失败 HTTP {r.status_code}")
        return

    items = r.json()
    items = items if isinstance(items, list) else items.get("items", [])
    if not items:
        skip("health-review 退回测试", "队列为空（所有记录已处理）")
        return

    item_id = items[0]["id"]
    # 关键：不发 data body，验证不会 422
    r2 = requests.post(
        f"{BASE}/api/v1/health-review/{item_id}/reject",
        headers=h,
        timeout=8
        # 注意: 不传 json/data 参数
    )
    if r2.status_code == 422:
        fail(f"POST /api/v1/health-review/{item_id}/reject 无body", "仍然 422！修复未生效")
    elif r2.status_code in (200, 201, 204):
        ok(f"POST /api/v1/health-review/{item_id}/reject 无body → {r2.status_code} (非422)")
    else:
        ok(f"POST /api/v1/health-review/{item_id}/reject 无body → {r2.status_code} (非422，可能已处理)")


# ─── 主入口 ───────────────────────────────────────────────────────────────────

def run():
    print("=" * 60)
    print("  BehaviorOS 单元测试 — 教练快捷操作")
    print("  Target: http://localhost:8000")
    print("=" * 60)

    h = test_coach_auth()
    if not h:
        print(f"\n{RED}无法登录，终止测试{RESET}")
        sys.exit(1)

    sid = test_get_students(h)
    if sid:
        test_send_message(h, sid)
        test_create_prescription(h, sid)
        test_read_notes(h, sid)

    test_health_review_reject_no_body(h)

    print("\n" + "=" * 60)
    print(f"  结果: {GREEN}{_pass} PASS{RESET}  {RED}{_fail} FAIL{RESET}  {YELLOW}{_skip} SKIP{RESET}")
    print("=" * 60)

    if _fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    run()


# ─── pytest 兼容入口 ──────────────────────────────────────────────────────────

import pytest

@pytest.fixture(scope="module")
def auth_h():
    h = login(COACH_USER)
    if not h:
        pytest.skip("coach 登录失败，跳过全部用例")
    return h


@pytest.fixture(scope="module")
def sid(auth_h):
    r = requests.get(f"{BASE}/api/v1/coach/dashboard", headers=auth_h, timeout=8)
    students = r.json().get("students", []) if r.status_code == 200 else []
    if not students:
        pytest.skip("无绑定学员")
    return students[0].get("id") or students[0].get("user_id")


def test_login_ok():
    h = login(COACH_USER)
    assert h is not None, "coach 登录失败"


def test_dashboard_ok(auth_h):
    r = requests.get(f"{BASE}/api/v1/coach/dashboard", headers=auth_h, timeout=8)
    assert r.status_code == 200


def test_notes_post_message(auth_h, sid):
    payload = {"content": "[消息] pytest-发消息测试", "note_type": "supervision"}
    r = requests.post(f"{BASE}/api/v1/coach/students/{sid}/notes", json=payload, headers=auth_h, timeout=8)
    assert r.status_code == 200, f"发消息 422/404: {r.text[:200]}"


def test_notes_post_prescription(auth_h, sid):
    payload = {"content": "[行为处方] pytest-处方测试", "note_type": "supervision"}
    r = requests.post(f"{BASE}/api/v1/coach/students/{sid}/notes", json=payload, headers=auth_h, timeout=8)
    assert r.status_code == 200, f"开处方失败: {r.text[:200]}"


def test_notes_get(auth_h, sid):
    r = requests.get(f"{BASE}/api/v1/coach/students/{sid}/notes", headers=auth_h, timeout=8)
    assert r.status_code == 200


def test_health_review_reject_not_422(auth_h):
    r = requests.get(
        f"{BASE}/api/v1/health-review/queue?reviewer_role=coach&risk_level=medium",
        headers=auth_h, timeout=8
    )
    if r.status_code != 200:
        pytest.skip("队列接口不可用")
    items = r.json()
    items = items if isinstance(items, list) else items.get("items", [])
    if not items:
        pytest.skip("队列为空")
    item_id = items[0]["id"]
    r2 = requests.post(f"{BASE}/api/v1/health-review/{item_id}/reject", headers=auth_h, timeout=8)
    assert r2.status_code != 422, f"422 未修复: {r2.text[:200]}"
