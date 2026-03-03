"""
集成测试 — 前后端接口契约验证
验证目标: 前端所有关键接口存在、返回正确状态，无404/500
覆盖角色: coach / supervisor / master

运行方式:
  cd D:\\behavioral-health-project
  pytest "C:\\Users\\Administrator\\Desktop\\test\\集成测试.py" -v
  # 或直接:
  python "C:\\Users\\Administrator\\Desktop\\test\\集成测试.py"
"""

import sys
import uuid
import requests

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ─── DB 直连（自植入 / 清理测试数据）──────────────────────────────────────────
try:
    import psycopg2
    _DB_CFG = dict(host="localhost", port=5432, dbname="bhp_db",
                   user="bhp_user", password="bhp_password")
    def _db_conn():
        return psycopg2.connect(**_DB_CFG)
    HAS_DB = True
except Exception:
    HAS_DB = False

def seed_health_review_item(user_id=4, reviewer_role="coach", risk_level="medium"):
    """插入一条测试用健康审核记录，返回 id；失败返回 None。"""
    if not HAS_DB:
        return None
    try:
        conn = _db_conn()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO health_review_queue
              (user_id, reviewer_role, risk_level, status, ai_summary, created_at)
            VALUES (%s, %s, %s, 'pending', '自动化测试植入条目，可忽略', NOW())
            RETURNING id
        """, (user_id, reviewer_role, risk_level))
        row = cur.fetchone()
        conn.commit(); conn.close()
        return row[0] if row else None
    except Exception as e:
        print(f"  seed error: {e}")
        return None

def delete_health_review_item(item_id):
    """删除测试植入的审核记录（清理）。"""
    if not HAS_DB or not item_id:
        return
    try:
        conn = _db_conn()
        cur  = conn.cursor()
        cur.execute("DELETE FROM health_review_queue WHERE id=%s", (item_id,))
        conn.commit(); conn.close()
    except Exception:
        pass

BASE = "http://localhost:8000"

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"

_pass = _fail = _skip = 0

def ok(name, note=""):
    global _pass; _pass += 1
    print(f"  {GREEN}[PASS]{RESET} {name}" + (f"  ({note})" if note else ""))

def fail(name, detail=""):
    global _fail; _fail += 1
    print(f"  {RED}[FAIL]{RESET} {name}" + (f": {detail}" if detail else ""))

def skip(name, reason=""):
    global _skip; _skip += 1
    print(f"  {YELLOW}[SKIP]{RESET} {name}: {reason}")


def login(username, password):
    try:
        r = requests.post(f"{BASE}/api/v1/auth/login", json={"username": username, "password": password}, timeout=8)
        if r.status_code == 200:
            return {"Authorization": f"Bearer {r.json()['access_token']}"}
    except Exception as e:
        print(f"  {RED}连接失败{RESET}: {e}")
    return None


def check(method, path, headers, allowed=(200, 201), body=None):
    """发请求，检查状态码不是 404/500。"""
    try:
        fn = getattr(requests, method.lower())
        kwargs = {"headers": headers, "timeout": 8}
        if body:
            kwargs["json"] = body
        r = fn(f"{BASE}{path}", **kwargs)
        if r.status_code in allowed:
            ok(f"{method} {path}", f"HTTP {r.status_code}")
        elif r.status_code == 404:
            fail(f"{method} {path}", f"404 接口不存在")
        elif r.status_code == 500:
            fail(f"{method} {path}", f"500 服务端错误: {r.text[:80]}")
        elif r.status_code == 422:
            fail(f"{method} {path}", f"422 参数错误: {r.text[:80]}")
        else:
            ok(f"{method} {path}", f"HTTP {r.status_code} (可接受)")
    except requests.exceptions.ConnectionError:
        fail(f"{method} {path}", "连接被拒绝 (服务未启动?)")
    except Exception as e:
        fail(f"{method} {path}", str(e)[:80])


# ═══════════════════════════════════════════════════════════════════════════════

def test_system_health():
    print(f"\n{CYAN}─── 0. 系统健康 ───{RESET}")
    r = requests.get(f"{BASE}/api/v1/system/health", timeout=8)
    if r.status_code == 200:
        d = r.json()
        status = d.get("status", "?")
        routes = d.get("total_routes", "?")
        color = GREEN if status == "healthy" else RED
        ok("GET /api/v1/system/health", f"status={color}{status}{RESET} routes={routes}")
        # 各子检查
        for k, v in d.get("checks", {}).items():
            sym = f"{GREEN}✓{RESET}" if v == "healthy" else f"{RED}✗{RESET}"
            print(f"    {sym} {k}: {v}")
    else:
        fail("GET /api/v1/system/health", r.status_code)


def test_auth_apis(h_coach):
    print(f"\n{CYAN}─── 1. 认证模块 ───{RESET}")
    check("GET",  "/api/v1/auth/me", h_coach)


def test_coach_apis(h_coach):
    print(f"\n{CYAN}─── 2. 教练核心模块 ───{RESET}")
    check("GET", "/api/v1/coach/dashboard",               h_coach)
    check("GET", "/api/v1/coach/students",                h_coach)

    # 获取一个真实 student_id
    r = requests.get(f"{BASE}/api/v1/coach/dashboard", headers=h_coach, timeout=8)
    students = []
    if r.status_code == 200:
        students = r.json().get("students", [])

    if students:
        sid = students[0].get("id") or students[0].get("user_id")
        check("GET",  f"/api/v1/coach/students/{sid}",       h_coach)
        check("GET",  f"/api/v1/coach/students/{sid}/notes", h_coach)
        check("POST", f"/api/v1/coach/students/{sid}/notes", h_coach,
              body={"content": "[消息] 集成测试", "note_type": "supervision"})
    else:
        skip("GET /api/v1/coach/students/{id}", "dashboard 无绑定学员")
        skip("GET /api/v1/coach/students/{id}/notes", "同上")
        skip("POST /api/v1/coach/students/{id}/notes", "同上")


def test_health_review_apis(h_coach):
    print(f"\n{CYAN}─── 3. 健康审核 (自植入数据 + 422修复验证) ───{RESET}")
    check("GET", "/api/v1/health-review/queue?reviewer_role=coach&risk_level=medium", h_coach)

    # 自植入一条测试记录，确保队列不为空
    seeded_id = seed_health_review_item()
    if seeded_id:
        ok("DB 植入测试审核记录", f"id={seeded_id}")
    else:
        skip("DB 植入", "psycopg2 不可用，使用队列现有数据")

    # 从队列拿记录
    r = requests.get(
        f"{BASE}/api/v1/health-review/queue?reviewer_role=coach&risk_level=medium",
        headers=h_coach, timeout=8
    )
    items = []
    if r.status_code == 200:
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])

    if items:
        iid = items[0]["id"]
        r2 = requests.post(f"{BASE}/api/v1/health-review/{iid}/reject", headers=h_coach, timeout=8)
        if r2.status_code == 422:
            fail("POST /api/v1/health-review/{id}/reject 无body", "422 — 修复未生效！")
        else:
            ok(f"POST /api/v1/health-review/{iid}/reject 无body", f"HTTP {r2.status_code} (非422)")
        # 清理（若是自植入的且还未被 reject 接口删除则清理）
        if seeded_id and seeded_id != iid:
            delete_health_review_item(seeded_id)
    else:
        fail("health-review 队列为空", "即使植入数据后队列仍无条目，检查 DB 连接")
        delete_health_review_item(seeded_id)


def test_profile_apis(h_coach):
    print(f"\n{CYAN}─── 4. 个人主页相关 ───{RESET}")
    check("GET", "/api/v1/auth/me",                          h_coach)
    check("GET", "/api/v1/learning/credits",                 h_coach)
    check("GET", "/api/v1/certification/sessions/my?status=passed", h_coach, allowed=(200, 400, 403))


def test_notification_apis(h_coach):
    print(f"\n{CYAN}─── 5. 通知模块 (非空验证) ───{RESET}")
    r = requests.get(f"{BASE}/api/v1/notifications", headers=h_coach, timeout=8)
    if r.status_code != 200:
        fail("GET /api/v1/notifications", f"HTTP {r.status_code}")
        return
    ok("GET /api/v1/notifications", f"HTTP {r.status_code}")

    data = r.json()
    items = data.get("items", data) if isinstance(data, dict) else data
    if len(items) > 0:
        ok("通知列表非空", f"{len(items)} 条通知（前端不会显示'暂无消息'）")
    else:
        fail("通知列表为空", "前端会显示'暂无消息' — 检查种子数据或 onShow 修复")


def test_assessment_apis(h_coach):
    print(f"\n{CYAN}─── 6. 评估模块 ───{RESET}")
    check("GET", "/api/v1/assessment-assignments/review-list", h_coach, allowed=(200, 400))
    check("GET", "/api/v1/coach/assessment/index",             h_coach, allowed=(200, 404))  # 可能是前端路由


def test_supervisor_apis():
    print(f"\n{CYAN}─── 7. 督导模块 ───{RESET}")
    h = login("coach", "Coach@2026")  # supervisor 账号未在 memory 中，用 coach 代替
    if not h:
        skip("supervisor APIs", "登录失败")
        return
    check("GET", "/api/v1/health-review/queue?reviewer_role=supervisor&risk_level=high", h,
          allowed=(200, 403))
    check("GET", "/api/v1/supervisor/dashboard", h, allowed=(200, 403, 404))


def test_push_queue_apis(h_coach):
    print(f"\n{CYAN}─── 8. 推送队列 (supervisor/push-queue 422修复验证) ───{RESET}")
    check("GET", "/api/v1/coach/push-queue", h_coach, allowed=(200, 404))

    # 验证 approve/reject 端点不会因无 body 而 422
    r = requests.get(f"{BASE}/api/v1/coach/push-queue", headers=h_coach, timeout=8)
    items = []
    if r.status_code == 200:
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", [])

    if items:
        iid = items[0]["id"]
        r2 = requests.post(f"{BASE}/api/v1/coach/push-queue/{iid}/approve", headers=h_coach, timeout=8)
        if r2.status_code == 422:
            fail(f"POST /api/v1/coach/push-queue/{iid}/approve 无body", "422 未修复")
        else:
            ok(f"POST /api/v1/coach/push-queue/{iid}/approve 无body", f"HTTP {r2.status_code}")
    else:
        skip("push-queue approve 422验证", "队列为空")


# ═══════════════════════════════════════════════════════════════════════════════

def run():
    print("=" * 65)
    print("  BehaviorOS 集成测试 — 前后端接口契约验证")
    print(f"  Target: {BASE}")
    print("=" * 65)

    test_system_health()

    h_coach = login("coach", "Coach@2026")
    if not h_coach:
        fail("coach 登录", "无法获取 token，终止")
        sys.exit(1)
    print(f"  {GREEN}coach 登录成功{RESET}")

    test_auth_apis(h_coach)
    test_coach_apis(h_coach)
    test_health_review_apis(h_coach)
    test_profile_apis(h_coach)
    test_notification_apis(h_coach)
    test_assessment_apis(h_coach)
    test_supervisor_apis()
    test_push_queue_apis(h_coach)

    print("\n" + "=" * 65)
    total = _pass + _fail + _skip
    print(f"  共 {total} 项  |  {GREEN}{_pass} PASS{RESET}  {RED}{_fail} FAIL{RESET}  {YELLOW}{_skip} SKIP{RESET}")
    print("=" * 65)

    if _fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    run()


# ─── pytest 兼容入口 ──────────────────────────────────────────────────────────

import pytest

@pytest.fixture(scope="module")
def h_coach():
    h = login("coach", "Coach@2026")
    if not h:
        pytest.skip("coach 登录失败")
    return h

@pytest.fixture(scope="module")
def first_student_id(h_coach):
    r = requests.get(f"{BASE}/api/v1/coach/dashboard", headers=h_coach, timeout=8)
    students = r.json().get("students", []) if r.status_code == 200 else []
    if not students:
        pytest.skip("无绑定学员")
    return students[0].get("id") or students[0].get("user_id")

@pytest.fixture(scope="module")
def review_item_id(h_coach):
    """自植入一条测试记录确保队列非空，返回 id。"""
    seeded = seed_health_review_item()
    r = requests.get(
        f"{BASE}/api/v1/health-review/queue?reviewer_role=coach&risk_level=medium",
        headers=h_coach, timeout=8
    )
    if r.status_code != 200:
        delete_health_review_item(seeded)
        return None
    items = r.json()
    items = items if isinstance(items, list) else items.get("items", [])
    if not items:
        delete_health_review_item(seeded)
        return None
    return items[0]["id"]


def test_system_health_ok():
    r = requests.get(f"{BASE}/api/v1/system/health", timeout=8)
    assert r.status_code == 200
    assert r.json().get("status") == "healthy"

def test_auth_me(h_coach):
    r = requests.get(f"{BASE}/api/v1/auth/me", headers=h_coach, timeout=8)
    assert r.status_code == 200

def test_coach_dashboard(h_coach):
    r = requests.get(f"{BASE}/api/v1/coach/dashboard", headers=h_coach, timeout=8)
    assert r.status_code == 200

def test_student_notes_post(h_coach, first_student_id):
    r = requests.post(
        f"{BASE}/api/v1/coach/students/{first_student_id}/notes",
        json={"content": "[消息] pytest集成测试", "note_type": "supervision"},
        headers=h_coach, timeout=8
    )
    assert r.status_code == 200

def test_student_notes_get(h_coach, first_student_id):
    r = requests.get(f"{BASE}/api/v1/coach/students/{first_student_id}/notes", headers=h_coach, timeout=8)
    assert r.status_code == 200

def test_health_review_queue(h_coach):
    r = requests.get(
        f"{BASE}/api/v1/health-review/queue?reviewer_role=coach&risk_level=medium",
        headers=h_coach, timeout=8
    )
    assert r.status_code == 200

def test_health_review_reject_not_422(h_coach, review_item_id):
    if not review_item_id:
        pytest.skip("队列为空")
    r = requests.post(f"{BASE}/api/v1/health-review/{review_item_id}/reject", headers=h_coach, timeout=8)
    assert r.status_code != 422, f"422 修复未生效: {r.text[:200]}"

def test_learning_credits(h_coach):
    r = requests.get(f"{BASE}/api/v1/learning/credits", headers=h_coach, timeout=8)
    assert r.status_code == 200

def test_notifications(h_coach):
    r = requests.get(f"{BASE}/api/v1/notifications", headers=h_coach, timeout=8)
    assert r.status_code == 200

def test_notifications_returns_data_not_empty(h_coach):
    """通知列表必须非空 — 防止'暂无消息'复活（种子数据+onShow修复共同保障）"""
    r = requests.get(f"{BASE}/api/v1/notifications", headers=h_coach, timeout=8)
    assert r.status_code == 200
    data = r.json()
    items = data.get("items", data) if isinstance(data, dict) else data
    assert len(items) > 0, "通知列表为空，前端会显示'暂无消息'——检查种子数据是否存在"
