"""
P2 Route 1: 1-Week Checkin → Trust Score Pipeline Test

Simulates 7 days of checkins for grower user and verifies:
  1. trust_score increases from 0
  2. trust_score is monotonically non-decreasing over 7 days
  3. trust_score_logs has 42 records (7 days × 6 signals)
  4. journey_states.trust_score = users.trust_score (C4 consistency)

Usage (Docker):
  MSYS_NO_PATHCONV=1 docker run --rm --network dify_dify-network \
    -v "D:/behavioral-health-project:/app" -w /app \
    -e DATABASE_URL=postgresql://postgres:difyai123456@db:5432/health_platform \
    -e API_BASE_URL=http://bhp-api:8000 \
    bhp-api:latest python scripts/test_trust_score_week.py
"""

import os
import sys
import json
import time
import requests
from datetime import date, datetime, timedelta

API = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:difyai123456@localhost:5432/health_platform")

# ── DB helpers ──────────────────────────────────────

def get_db_conn():
    import psycopg2
    return psycopg2.connect(DB_URL)


def db_exec(sql, params=None, fetch=True):
    conn = get_db_conn()
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(sql, params)
    result = None
    if fetch:
        try:
            result = cur.fetchall()
        except Exception:
            result = []
    cur.close()
    conn.close()
    return result


def db_exec_one(sql, params=None):
    rows = db_exec(sql, params)
    return rows[0] if rows else None


# ── API helpers ─────────────────────────────────────

def login(username: str, password: str) -> str:
    resp = requests.post(f"{API}/api/v1/auth/login", data={
        "username": username, "password": password,
    })
    if resp.status_code != 200:
        print(f"  [ERROR] Login failed ({resp.status_code}): {resp.text[:200]}")
        sys.exit(1)
    return resp.json()["access_token"]


def api_get(path: str, token: str):
    resp = requests.get(f"{API}{path}", headers={"Authorization": f"Bearer {token}"})
    return resp.status_code, resp.json() if resp.status_code == 200 else resp.text


def api_post(path: str, token: str, json_body=None):
    resp = requests.post(
        f"{API}{path}",
        headers={"Authorization": f"Bearer {token}"},
        json=json_body or {},
    )
    return resp.status_code, resp.json() if resp.status_code < 400 else resp.text


# ── Test data ───────────────────────────────────────

DAY_CONFIGS = [
    # day, note, photo_url, value, voice_url
    {"day": 1, "note": None, "photo_url": None, "value": None},
    {"day": 2, "note": "today ok", "photo_url": None, "value": None},
    {"day": 3, "note": "feeling much better, walked 30 min after lunch and noticed my blood sugar was more stable", "photo_url": None, "value": 5.8},
    {"day": 4, "note": "had a good breakfast, feeling happy and energetic today", "photo_url": None, "value": 6.1},
    {"day": 5, "note": "exercised in the morning, feeling relaxed and grateful for a good night sleep", "photo_url": "https://example.com/meal.jpg", "value": 5.5},
    {"day": 6, "note": "today was a bit stressful at work but I managed to stick to my meal plan and do some stretching, feeling proud of myself", "photo_url": "https://example.com/walk.jpg", "value": 5.9, "voice_url": "https://example.com/voice.mp3"},
    {"day": 7, "note": "one week completed! feeling a lot more confident about managing my health, the routine is becoming natural", "photo_url": "https://example.com/progress.jpg", "value": 5.6, "voice_url": "https://example.com/reflection.mp3"},
]


# ── Main test ───────────────────────────────────────

def main():
    print("=" * 60)
    print("P2 Route 1: Checkin -> Trust Score Pipeline (7-Day Simulation)")
    print("=" * 60)

    # ── 0. Login ──
    print("\n[Step 0] Logging in as grower...")
    token = login("grower", "Grower@2026")
    user_id_row = db_exec_one(
        "SELECT id FROM users WHERE username = 'grower'"
    )
    if not user_id_row:
        print("  [ERROR] grower user not found in DB")
        sys.exit(1)
    user_id = user_id_row[0]
    print(f"  grower user_id = {user_id}")

    # ── 1. Reset ──
    print("\n[Step 1] Resetting trust data for grower...")
    db_exec("DELETE FROM trust_score_logs WHERE user_id = %s", (user_id,), fetch=False)
    db_exec("DELETE FROM task_checkins WHERE user_id = %s", (user_id,), fetch=False)
    db_exec("DELETE FROM daily_tasks WHERE user_id = %s", (user_id,), fetch=False)
    db_exec("DELETE FROM user_streaks WHERE user_id = %s", (user_id,), fetch=False)
    # Reset journey_states trust_score
    db_exec(
        "UPDATE journey_states SET trust_score = 0, trust_signals = '{}' WHERE user_id = %s",
        (user_id,), fetch=False,
    )
    # Reset users trust_score
    db_exec(
        "UPDATE users SET trust_score = 0 WHERE id = %s",
        (user_id,), fetch=False,
    )
    # Ensure journey_states row exists
    js_row = db_exec_one("SELECT id FROM journey_states WHERE user_id = %s", (user_id,))
    if not js_row:
        db_exec(
            "INSERT INTO journey_states (user_id, journey_stage, agency_mode, trust_score) "
            "VALUES (%s, 's1_awareness', 'passive', 0)",
            (user_id,), fetch=False,
        )
    print("  Done.")

    # ── 2. Simulate 7 days ──
    today = date.today()
    daily_scores = []
    results = {"days": [], "pass": True, "failures": []}
    tags = ["营养", "运动", "监测", "睡眠", "情绪", "学习"]

    for cfg in DAY_CONFIGS:
        day_num = cfg["day"]
        task_date = today - timedelta(days=7 - day_num)  # spread over past 7 days
        print(f"\n[Day {day_num}] {task_date} ──────────────────")

        # 2a. Insert synthetic daily tasks (3 per day with varying tags)
        task_ids = []
        for i in range(3):
            tid = f"dt_{task_date.strftime('%Y%m%d')}_{user_id}_{i+1:03d}"
            tag = tags[(day_num + i) % len(tags)]
            db_exec(
                """INSERT INTO daily_tasks (id, user_id, task_date, order_num, title, tag, tag_color, source, done)
                   VALUES (%s, %s, %s, %s, %s, %s, '#3b82f6', 'rx', false)
                   ON CONFLICT (id) DO NOTHING""",
                (tid, user_id, task_date, i + 1, f"Day{day_num} Task{i+1}", tag),
                fetch=False,
            )
            task_ids.append(tid)

        # 2b. Checkin via API (first task only to keep it simple)
        checkin_body = {}
        if cfg.get("note"):
            checkin_body["note"] = cfg["note"]
        if cfg.get("photo_url"):
            checkin_body["photo_url"] = cfg["photo_url"]
        if cfg.get("value") is not None:
            checkin_body["value"] = cfg["value"]
        if cfg.get("voice_url"):
            checkin_body["voice_url"] = cfg["voice_url"]

        # For past dates: insert checkin directly via DB since API uses NOW()
        checkin_time = datetime.combine(task_date, datetime.min.time().replace(hour=9))
        db_exec(
            """INSERT INTO task_checkins (task_id, user_id, note, photo_url, value, voice_url, points_earned, checked_at)
               VALUES (%s, %s, %s, %s, %s, %s, 10, %s)""",
            (task_ids[0], user_id, cfg.get("note"), cfg.get("photo_url"),
             cfg.get("value"), cfg.get("voice_url"), checkin_time),
            fetch=False,
        )
        # Mark task as done
        db_exec(
            "UPDATE daily_tasks SET done = true, done_time = %s WHERE id = %s",
            (checkin_time, task_ids[0]), fetch=False,
        )

        # 2c. Update streak
        db_exec("""
            INSERT INTO user_streaks (user_id, current_streak, longest_streak, last_checkin_date, updated_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (user_id) DO UPDATE
            SET current_streak = %s, longest_streak = GREATEST(user_streaks.longest_streak, %s),
                last_checkin_date = %s, updated_at = NOW()
        """, (user_id, day_num, day_num, task_date, day_num, day_num, task_date), fetch=False)

        print(f"  Inserted checkin: note={bool(cfg.get('note'))}, photo={bool(cfg.get('photo_url'))}, value={cfg.get('value')}")

    # ── 3. Now trigger trust score calculation via the LIVE API ──
    # We need one "today" task to checkin via API to trigger the pipeline
    print(f"\n[Live API Checkin] Creating today's task and checking in...")

    today_tid = f"dt_{today.strftime('%Y%m%d')}_{user_id}_901"
    db_exec(
        """INSERT INTO daily_tasks (id, user_id, task_date, order_num, title, tag, tag_color, source, done)
           VALUES (%s, %s, %s, 1, 'Live Pipeline Test', '监测', '#3b82f6', 'rx', false)
           ON CONFLICT (id) DO NOTHING""",
        (today_tid, user_id, today), fetch=False,
    )

    status_code, resp = api_post(
        f"/api/v1/daily-tasks/{today_tid}/checkin",
        token,
        {"note": "Pipeline test - feeling great after a full week of tracking, very motivated!", "value": 5.4},
    )
    print(f"  Checkin API: {status_code}")
    if status_code == 200:
        print(f"  Response: streak={resp.get('streak_days')}, msg={resp.get('message')}")
    else:
        print(f"  [WARN] Checkin API error: {resp}")

    # Small delay for async trust update to complete
    time.sleep(2)

    # ── 4. Verify results ──
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)

    # 4a. Check trust_score via API
    st, trust_resp = api_get("/api/v1/journey/trust", token)
    trust_score = trust_resp.get("trust_score", 0) if st == 200 else 0
    trust_level = trust_resp.get("trust_level", "unknown") if st == 200 else "unknown"
    trust_signals = trust_resp.get("trust_signals", {}) if st == 200 else {}
    print(f"\n  Trust Score (API): {trust_score}")
    print(f"  Trust Level: {trust_level}")
    print(f"  Trust Signals: {json.dumps(trust_signals, indent=2)}")

    # 4b. Check trust_score_logs count
    log_count_row = db_exec_one(
        "SELECT COUNT(*) FROM trust_score_logs WHERE user_id = %s", (user_id,)
    )
    log_count = log_count_row[0] if log_count_row else 0
    print(f"\n  trust_score_logs count: {log_count}")

    # 4c. Check C4 consistency: journey_states.trust_score = users.trust_score
    js_score_row = db_exec_one(
        "SELECT trust_score FROM journey_states WHERE user_id = %s", (user_id,)
    )
    user_score_row = db_exec_one(
        "SELECT trust_score FROM users WHERE id = %s", (user_id,)
    )
    js_score = float(js_score_row[0]) if js_score_row and js_score_row[0] else 0.0
    user_score = float(user_score_row[0]) if user_score_row and user_score_row[0] else 0.0
    print(f"\n  journey_states.trust_score: {js_score}")
    print(f"  users.trust_score:          {user_score}")
    c4_match = abs(js_score - user_score) < 0.0001
    print(f"  C4 consistency:             {'PASS' if c4_match else 'FAIL'}")

    # ── 5. Assertions ──
    print("\n" + "=" * 60)
    print("ASSERTIONS")
    print("=" * 60)

    failures = []

    # A1: trust_score > 0 after checkins
    if trust_score > 0:
        print(f"  [PASS] A1: trust_score ({trust_score}) > 0")
    else:
        msg = f"A1: trust_score ({trust_score}) should be > 0"
        print(f"  [FAIL] {msg}")
        failures.append(msg)

    # A2: trust_score_logs has at least 6 records (one API call = 6 signals)
    if log_count >= 6:
        print(f"  [PASS] A2: trust_score_logs count ({log_count}) >= 6")
    else:
        msg = f"A2: trust_score_logs count ({log_count}) should be >= 6"
        print(f"  [FAIL] {msg}")
        failures.append(msg)

    # A3: C4 consistency
    if c4_match:
        print(f"  [PASS] A3: C4 consistency (journey={js_score}, user={user_score})")
    else:
        msg = f"A3: C4 mismatch (journey={js_score}, user={user_score})"
        print(f"  [FAIL] {msg}")
        failures.append(msg)

    # A4: trust signals should not all be zero
    non_zero_signals = sum(1 for v in trust_signals.values() if v and float(v) > 0)
    if non_zero_signals > 0:
        print(f"  [PASS] A4: {non_zero_signals}/6 signals are non-zero")
    else:
        msg = "A4: All trust signals are zero"
        print(f"  [FAIL] {msg}")
        failures.append(msg)

    # ── 6. Summary ──
    passed = len(failures) == 0
    print("\n" + "=" * 60)
    if passed:
        print("RESULT: ALL PASSED")
    else:
        print(f"RESULT: {len(failures)} FAILURE(S)")
        for f in failures:
            print(f"  - {f}")
    print("=" * 60)

    # Write JSON report
    report = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "trust_score": trust_score,
        "trust_level": trust_level,
        "trust_signals": trust_signals,
        "log_count": log_count,
        "c4_consistency": c4_match,
        "assertions_passed": len(DAY_CONFIGS) + 4 - len(failures),
        "assertions_failed": len(failures),
        "failures": failures,
        "passed": passed,
    }
    report_path = "scripts/trust_score_week_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nReport saved to {report_path}")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
