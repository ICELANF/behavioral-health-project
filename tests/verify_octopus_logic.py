"""
verify_octopus_logic.py
=======================
八爪鱼核心逻辑验证 — 3 个场景:
  1. SOP 6.2 公共防火墙 (UI-1 → SILENCE, 绕过大脑)
  2. S2 → S3 阶段跃迁 (UI-3, belief=0.8)
  3. L6 热重写 (英雄之旅叙事, 非原始 JSON)
"""
import sys, os, json, unittest

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from core.brain.decision_engine import BehavioralBrain

# 加载 spi_mapping 配置
CONFIG_PATH = os.path.join(PROJECT_ROOT, "configs", "spi_mapping.json")
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    SPI_CONFIG = json.load(f)


class TestOctopusLogic(unittest.TestCase):
    """八爪鱼核心逻辑验证"""

    def setUp(self):
        self.brain = BehavioralBrain(config=SPI_CONFIG)

    # ------------------------------------------------------------------ #
    # 场景 1: SOP 6.2 公共防火墙
    # ------------------------------------------------------------------ #
    def test_sop62_firewall_ui1_returns_silence(self):
        """UI-1 请求必须返回 SILENCE 并绕过大脑"""
        result = self.brain.process(
            source_ui="UI-1",
            current_state={"current_stage": "S2", "belief": 0.9, "action_count_3d": 5},
        )

        self.assertEqual(result["action"], "SILENCE", "UI-1 应返回 SILENCE")
        self.assertTrue(result["bypass_brain"], "UI-1 应绕过大脑判定")
        # 确保大脑判定字段不存在 (被完全跳过)
        self.assertNotIn("from_stage", result, "SILENCE 响应不应包含阶段判定字段")
        self.assertNotIn("is_transition", result, "SILENCE 响应不应包含跃迁字段")

    # ------------------------------------------------------------------ #
    # 场景 2: S2 → S3 阶段跃迁
    # ------------------------------------------------------------------ #
    def test_s2_to_s3_transition_via_ui3(self):
        """UI-3 + belief=0.8 + current_stage=S2 应触发 S3 跃迁"""
        result = self.brain.process(
            source_ui="UI-3",
            current_state={"current_stage": "S2", "belief": 0.8, "action_count_3d": 2},
        )

        self.assertEqual(result["from_stage"], "S2")
        self.assertEqual(result["to_stage"], "S3")
        self.assertTrue(result["is_transition"], "belief=0.8 应触发 S2→S3 跃迁")

    # ------------------------------------------------------------------ #
    # 场景 3: L6 热重写 — 英雄之旅叙事
    # ------------------------------------------------------------------ #
    def test_l6_hero_journey_rewrite(self):
        """跃迁响应必须包含英雄之旅风格叙事, 而非原始 JSON 数据"""
        result = self.brain.process(
            source_ui="UI-3",
            current_state={"current_stage": "S2", "belief": 0.8, "action_count_3d": 2},
        )

        # 必须有 narrative 字段
        self.assertIn("narrative", result, "跃迁响应必须包含 narrative 字段")

        narrative = result["narrative"]

        # 叙事文本应包含英雄之旅关键词
        self.assertIn("英雄之旅", narrative, "叙事文本应包含'英雄之旅'")
        self.assertIn("行动", narrative, "叙事文本应包含'行动'关键词")

        # 叙事文本不应是原始 JSON 数据
        self.assertNotIn('"from_stage"', narrative, "叙事不应包含原始 JSON 键")
        self.assertNotIn('"belief"', narrative, "叙事不应包含原始指标键")


if __name__ == "__main__":
    unittest.main(verbosity=2)
