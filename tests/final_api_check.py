"""
final_api_check.py
==================
端到端 API 验证 — 直接调用运行中的 /api/v1/brain/evaluate 端点
  1. UI-1 被 SOP 6.2 防火墙拦截 → SILENCE
  2. UI-3 触发 S2→S3 跃迁
  3. 英雄之旅叙事内容正确返回
  4. 跃迁事件持久化到 behavior_audit_logs 表
"""
import sys, os, unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

try:
    import httpx
    CLIENT_CLS = "httpx"
except ImportError:
    import requests
    CLIENT_CLS = "requests"

BASE_URL = "http://127.0.0.1:8000"
ENDPOINT = f"{BASE_URL}/api/v1/brain/evaluate"

TEST_USER_ID = "test_user_e2e"


def _post(headers, payload):
    if CLIENT_CLS == "httpx":
        with httpx.Client(timeout=10) as c:
            return c.post(ENDPOINT, headers=headers, json=payload).json()
    else:
        return requests.post(ENDPOINT, headers=headers, json=payload, timeout=10).json()


class TestFinalAPICheck(unittest.TestCase):
    """端到端 API 验证"""

    @classmethod
    def setUpClass(cls):
        """确认服务可达"""
        try:
            if CLIENT_CLS == "httpx":
                with httpx.Client(timeout=5) as c:
                    r = c.get(f"{BASE_URL}/health")
                    assert r.status_code == 200
            else:
                r = requests.get(f"{BASE_URL}/health", timeout=5)
                assert r.status_code == 200
        except Exception:
            raise RuntimeError(
                "后端未启动，请先运行 start_all.bat 或 "
                "uvicorn api.main:app --port 8000"
            )

    # ------------------------------------------------------------------ #
    # 场景 1: SOP 6.2 — UI-1 被拦截
    # ------------------------------------------------------------------ #
    def test_ui1_blocked_by_firewall(self):
        """UI-1 请求必须返回 SILENCE 且绕过大脑"""
        data = _post(
            headers={"X-Source-UI": "UI-1"},
            payload={"user_id": TEST_USER_ID, "current_stage": "S2", "belief": 0.9, "action_count_3d": 5},
        )
        self.assertEqual(data["action"], "SILENCE")
        self.assertTrue(data["bypass_brain"])
        self.assertNotIn("from_stage", data)
        self.assertNotIn("narrative", data)

    # ------------------------------------------------------------------ #
    # 场景 2: UI-3 触发 S2→S3 跃迁
    # ------------------------------------------------------------------ #
    def test_ui3_triggers_s2_to_s3(self):
        """UI-3 + belief=0.8 + stage=S2 应返回 S3 跃迁"""
        data = _post(
            headers={"X-Source-UI": "UI-3"},
            payload={"user_id": TEST_USER_ID, "current_stage": "S2", "belief": 0.8, "action_count_3d": 2},
        )
        self.assertEqual(data["from_stage"], "S2")
        self.assertEqual(data["to_stage"], "S3")
        self.assertTrue(data["is_transition"])

    # ------------------------------------------------------------------ #
    # 场景 3: 英雄之旅叙事正确返回
    # ------------------------------------------------------------------ #
    def test_hero_journey_narrative_in_response(self):
        """跃迁响应中 narrative 字段包含英雄之旅中文叙事"""
        data = _post(
            headers={"X-Source-UI": "UI-3"},
            payload={"user_id": TEST_USER_ID, "current_stage": "S2", "belief": 0.8, "action_count_3d": 2},
        )
        self.assertIn("narrative", data)
        narrative = data["narrative"]
        self.assertIsInstance(narrative, str)
        self.assertGreater(len(narrative), 10, "叙事文本不应为空或过短")
        self.assertIn("英雄之旅", narrative)
        self.assertIn("行动", narrative)
        # 确认不是原始 JSON 字符串
        self.assertNotIn("{", narrative)
        self.assertNotIn("from_stage", narrative)

    # ------------------------------------------------------------------ #
    # 场景 4: 跃迁事件持久化到 behavior_audit_logs
    # ------------------------------------------------------------------ #
    def test_transition_persisted_to_db(self):
        """跃迁发生后 behavior_audit_logs 表中应有对应记录"""
        import time

        # 先触发一次跃迁
        _post(
            headers={"X-Source-UI": "UI-3"},
            payload={"user_id": TEST_USER_ID, "current_stage": "S2", "belief": 0.8, "action_count_3d": 2},
        )

        # BackgroundTasks 异步写入，等待完成
        time.sleep(1)

        # 直接查询数据库验证
        from core.database import get_db_session
        from core.models import BehaviorAuditLog

        with get_db_session() as db:
            logs = (
                db.query(BehaviorAuditLog)
                .filter(BehaviorAuditLog.user_id == TEST_USER_ID)
                .order_by(BehaviorAuditLog.created_at.desc())
                .all()
            )

        self.assertGreater(len(logs), 0, "数据库中应至少有一条审计记录")
        latest = logs[0]
        self.assertEqual(latest.from_stage, "S2")
        self.assertEqual(latest.to_stage, "S3")
        self.assertEqual(latest.source_ui, "UI-3")
        self.assertIsNotNone(latest.narrative)
        self.assertIn("英雄之旅", latest.narrative)


if __name__ == "__main__":
    unittest.main(verbosity=2)
