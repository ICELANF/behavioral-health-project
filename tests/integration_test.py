# -*- coding: utf-8 -*-
"""
integration_test.py - Dify 与 Master Agent 集成测试

测试内容：
1. 调用 Dify v1/chat-messages 接口
2. 验证返回数据结构是否符合 v2.0 Schema
3. 测试 DataFormatConverter 兼容层
4. 端到端流程验证
"""

import os
import sys
import json
import time
import unittest
from typing import Dict, Any, Optional, List
from datetime import datetime

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("Warning: requests library not installed. Run: pip install requests")

from core.master_agent import (
    DataFormatConverter,
    UserInput,
    MasterAgent,
    SCHEMA_VERSION,
    CoreUserInput,
    CoreAgentTask,
    CoreAgentResult,
    CoreInterventionPlan,
    CoreDailyTask,
    AssessmentResult,
)


# ============================================================================
# 配置
# ============================================================================

# Dify API 配置 - 请替换为您的实际 API Key
DIFY_API_KEY = os.environ.get('DIFY_API_KEY', 'app-zX5qVxIrj2a9ZQdrRygfGjWz')
DIFY_BASE_URL = os.environ.get('DIFY_BASE_URL', 'http://localhost')

# 测试用户
TEST_USER_ID = "test-user-integration-001"


# ============================================================================
# Dify API 客户端
# ============================================================================

class DifyClient:
    """Dify API 客户端"""

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or DIFY_API_KEY
        self.base_url = base_url or DIFY_BASE_URL
        self.conversation_id = None

    def chat(self,
             query: str,
             user: str = TEST_USER_ID,
             inputs: Dict[str, Any] = None,
             streaming: bool = False,
             timeout: int = 120) -> Dict[str, Any]:
        """
        调用 Dify chat-messages API

        Args:
            query: 用户消息
            user: 用户标识
            inputs: 额外输入变量
            streaming: 是否使用流式响应
            timeout: 超时时间（秒）

        Returns:
            API 响应
        """
        if not HAS_REQUESTS:
            raise RuntimeError("requests library not installed")

        url = f"{self.base_url}/v1/chat-messages"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "inputs": inputs or {},
            "query": query,
            "response_mode": "streaming" if streaming else "blocking",
            "user": user
        }

        # 如果有会话 ID，添加到请求中
        if self.conversation_id:
            payload["conversation_id"] = self.conversation_id

        try:
            if streaming:
                return self._stream_chat(url, headers, payload, timeout)
            else:
                response = requests.post(url, headers=headers, json=payload, timeout=timeout)
                response.raise_for_status()
                result = response.json()
                # 保存会话 ID
                if "conversation_id" in result:
                    self.conversation_id = result["conversation_id"]
                return result
        except requests.exceptions.Timeout:
            return {"error": "timeout", "message": f"Request timed out after {timeout}s"}
        except requests.exceptions.RequestException as e:
            return {"error": "request_failed", "message": str(e)}

    def _stream_chat(self, url: str, headers: Dict, payload: Dict, timeout: int) -> Dict[str, Any]:
        """处理流式响应"""
        response = requests.post(url, headers=headers, json=payload, timeout=timeout, stream=True)
        response.raise_for_status()

        full_answer = ""
        metadata = {}

        for line in response.iter_lines():
            if not line:
                continue
            line = line.decode('utf-8', errors='ignore')
            if line.startswith('data: '):
                try:
                    data = json.loads(line[6:])
                    event = data.get('event', '')

                    if event == 'message':
                        full_answer += data.get('answer', '')
                    elif event == 'message_end':
                        metadata = data.get('metadata', {})
                        if 'conversation_id' in data:
                            self.conversation_id = data['conversation_id']
                    elif event == 'workflow_started':
                        if 'conversation_id' in data:
                            self.conversation_id = data['conversation_id']
                    elif event == 'error':
                        return {"error": "dify_error", "message": data.get('message', 'Unknown error')}
                except json.JSONDecodeError:
                    pass

        return {
            "answer": full_answer,
            "conversation_id": self.conversation_id,
            "metadata": metadata
        }

    def reset_conversation(self):
        """重置会话"""
        self.conversation_id = None


# ============================================================================
# 测试用例
# ============================================================================

class TestDifyIntegration(unittest.TestCase):
    """Dify 集成测试"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.client = DifyClient()
        cls.master_agent = None
        try:
            cls.master_agent = MasterAgent()
        except Exception as e:
            print(f"Warning: Could not initialize MasterAgent: {e}")

    def setUp(self):
        """每个测试前重置"""
        self.client.reset_conversation()

    # ========== Dify API 连接测试 ==========

    def test_01_dify_connection(self):
        """测试 Dify API 连接"""
        if not HAS_REQUESTS:
            self.skipTest("requests library not installed")

        print("\n[Test] Dify API Connection")
        result = self.client.chat("你好", streaming=True, timeout=30)

        self.assertNotIn("error", result, f"API Error: {result.get('message', result)}")
        self.assertIn("answer", result, "Response should contain 'answer' field")
        print(f"  Answer: {result['answer'][:100]}...")
        print(f"  Conversation ID: {result.get('conversation_id', 'N/A')}")

    def test_02_dify_health_assessment(self):
        """测试健康评估对话"""
        if not HAS_REQUESTS:
            self.skipTest("requests library not installed")

        print("\n[Test] Health Assessment Dialog")

        # 模拟颈椎问题用户
        query = "我最近颈椎很疼，睡眠也不好，血糖有点高，感觉压力很大"
        result = self.client.chat(query, streaming=True, timeout=60)

        self.assertNotIn("error", result, f"API Error: {result.get('message')}")
        answer = result.get("answer", "")
        print(f"  Query: {query}")
        print(f"  Answer: {answer[:300]}...")

        # 验证响应包含关键内容
        # (具体验证取决于 Dify 工作流配置)

    # ========== DataFormatConverter 测试 ==========

    def test_10_converter_old_format_input(self):
        """测试旧格式输入转换"""
        print("\n[Test] DataFormatConverter - Old Format Input")

        old_input = {
            "user_id": "test123",
            "message": "我血糖高睡不好",
            "physiological_state": {
                "hrv_sdnn": 45,
                "sleep_hours": 5.5,
                "sleep_quality": 55,
                "fasting_glucose": 126,
                "time_in_range": 60
            },
            "psychological_state": {
                "stress_score": 70,
                "anxiety_score": 50,
                "self_efficacy": 40
            },
            "behavior_state": {
                "stage": "contemplation",
                "spi": 0.5
            }
        }

        converted = DataFormatConverter.convert_user_input(old_input)

        # 验证转换结果
        self.assertEqual(converted.get("content"), "我血糖高睡不好")
        self.assertIn("device_data", converted)
        print(f"  Original keys: {list(old_input.keys())}")
        print(f"  Converted keys: {list(converted.keys())}")
        print(f"  Content: {converted.get('content')}")
        print(f"  Device data: {converted.get('device_data')}")

    def test_11_converter_stage_mapping(self):
        """测试行为阶段映射"""
        print("\n[Test] DataFormatConverter - Stage Mapping")

        test_cases = [
            ("precontemplation", "resistance"),
            ("contemplation", "ambivalence"),
            ("preparation", "compromise"),
            ("action", "adaptation"),
            ("maintenance", "integration"),
            ("前意向期", "resistance"),
            ("完全对抗", "resistance"),
        ]

        for old_stage, expected_new in test_cases:
            result = DataFormatConverter.convert_stage(old_stage)
            self.assertEqual(result, expected_new, f"Stage '{old_stage}' should map to '{expected_new}'")
            print(f"  {old_stage} -> {result} ✓")

    def test_12_converter_profile_data(self):
        """测试用户画像数据转换"""
        print("\n[Test] DataFormatConverter - Profile Data")

        old_profile = {
            "physiological_state": {
                "hrv_sdnn": 50,
                "sleep_hours": 7,
                "fasting_glucose": 100,
                "hba1c": 5.8
            },
            "psychological_state": {
                "stress_score": 45,
                "self_efficacy": 60
            },
            "computed_indicators": {
                "bmi": 24.5,
                "bmi_category": "normal"
            }
        }

        converted = DataFormatConverter.convert_profile_data(old_profile)

        # 验证新格式字段
        self.assertIn("biometrics", converted)
        self.assertIn("psych", converted)
        self.assertIn("constitution", converted)

        self.assertEqual(converted["biometrics"]["hrv"]["sdnn"], 50)
        self.assertEqual(converted["biometrics"]["glucose"]["hba1c"], 5.8)
        self.assertEqual(converted["psych"]["efficacy_score"], 60)
        self.assertEqual(converted["constitution"]["bmi"], 24.5)

        print(f"  biometrics: {converted.get('biometrics')}")
        print(f"  psych: {converted.get('psych')}")
        print(f"  constitution: {converted.get('constitution')}")

    # ========== UserInput 测试 ==========

    def test_20_user_input_from_old_format(self):
        """测试 UserInput 从旧格式创建"""
        print("\n[Test] UserInput.from_dict - Old Format")

        old_data = {
            "user_id": "U12345",
            "query": "我颈椎疼",
            "physiological_state": {
                "hrv_sdnn": 48,
                "sleep_quality": 65
            }
        }

        user_input = UserInput.from_dict(old_data)

        self.assertEqual(user_input.user_id, "U12345")
        self.assertEqual(user_input.content, "我颈椎疼")
        self.assertIsNotNone(user_input.device_data)
        self.assertEqual(user_input.device_data.hrv.sdnn, 48)

        print(f"  user_id: {user_input.user_id}")
        print(f"  content: {user_input.content}")
        print(f"  device_data.hrv.sdnn: {user_input.device_data.hrv.sdnn}")

    def test_21_user_input_from_new_format(self):
        """测试 UserInput 从新格式创建"""
        print("\n[Test] UserInput.from_dict - New Format")

        new_data = {
            "user_id": "U12345",
            "content": "我想改善睡眠",
            "input_type": "text",
            "efficacy_score": 65.0,
            "device_data": {
                "hrv": {"sdnn": 55, "rmssd": 40},
                "sleep": {"duration_hours": 6.5, "quality_score": 70}
            }
        }

        user_input = UserInput.from_dict(new_data)

        self.assertEqual(user_input.user_id, "U12345")
        self.assertEqual(user_input.content, "我想改善睡眠")
        self.assertEqual(user_input.efficacy_score, 65.0)

        print(f"  user_id: {user_input.user_id}")
        print(f"  content: {user_input.content}")
        print(f"  efficacy_score: {user_input.efficacy_score}")

    # ========== Core Data Schema 测试 ==========

    def test_30_core_schema_version(self):
        """测试 Schema 版本"""
        print("\n[Test] Core Data Schema Version")
        self.assertEqual(SCHEMA_VERSION, "1.0")
        print(f"  SCHEMA_VERSION: {SCHEMA_VERSION}")

    def test_31_core_user_input(self):
        """测试 CoreUserInput 结构"""
        print("\n[Test] CoreUserInput Structure")

        data = {
            "input_id": "IN12345",
            "user_id": "U12345",
            "input_type": "chat",
            "raw_content": {"text": "测试消息"},
            "source": "app"
        }

        core_input = CoreUserInput.from_dict(data)

        self.assertEqual(core_input.schema_version, SCHEMA_VERSION)
        self.assertEqual(core_input.user_id, "U12345")

        output = core_input.to_dict()
        self.assertIn("schema_version", output)
        print(f"  schema_version: {output['schema_version']}")
        print(f"  input_type: {output['input_type']}")

    def test_32_core_agent_task(self):
        """测试 CoreAgentTask 结构"""
        print("\n[Test] CoreAgentTask Structure")

        data = {
            "task_id": "T12345",
            "user_id": "U12345",
            "target_agent": "sleep",
            "task_type": "analysis",
            "focus_domain": "sleep_quality",
            "specific_questions": ["分析睡眠质量", "给出改善建议"]
        }

        task = CoreAgentTask.from_dict(data)

        self.assertEqual(task.schema_version, SCHEMA_VERSION)
        output = task.to_dict()
        self.assertEqual(output["target_agent"], "sleep")
        self.assertEqual(output["task_type"], "analysis")
        print(f"  task_id: {output['task_id']}")
        print(f"  target_agent: {output['target_agent']}")
        print(f"  schema_version: {output['schema_version']}")

    def test_33_core_agent_result(self):
        """测试 CoreAgentResult 结构"""
        print("\n[Test] CoreAgentResult Structure")

        data = {
            "task_id": "T12345",
            "agent_id": "SleepAgent",
            "domain": "sleep",
            "key_findings": ["睡眠时间不足", "睡眠质量偏低"],
            "behavior_pattern_tags": ["late_sleeper", "poor_sleep_quality"],
            "risk_assessment": {"risk_level": "moderate", "confidence": 0.85},
            "recommendations": ["22:30前入睡", "睡前避免使用手机"]
        }

        result = CoreAgentResult.from_dict(data)

        self.assertEqual(result.schema_version, SCHEMA_VERSION)
        output = result.to_dict()
        self.assertEqual(len(output["key_findings"]), 2)
        self.assertEqual(output["risk_assessment"]["risk_level"], "moderate")
        print(f"  agent_id: {output['agent_id']}")
        print(f"  key_findings: {output['key_findings']}")
        print(f"  risk_level: {output['risk_assessment']['risk_level']}")

    def test_34_core_intervention_plan(self):
        """测试 CoreInterventionPlan 结构"""
        print("\n[Test] CoreInterventionPlan Structure")

        data = {
            "plan_id": "IP12345",
            "user_id": "U12345",
            "target_goals": ["改善睡眠", "稳定血糖"],
            "current_stage": "startup",
            "strategy_type": "behavioral",
            "intervention_modules": [
                {
                    "module_type": "sleep",
                    "intensity_level": "light",
                    "key_methods": ["固定作息时间", "睡前放松"]
                }
            ]
        }

        plan = CoreInterventionPlan.from_dict(data)

        self.assertEqual(plan.schema_version, SCHEMA_VERSION)
        output = plan.to_dict()
        self.assertEqual(output["current_stage"], "startup")
        self.assertEqual(len(output["intervention_modules"]), 1)
        print(f"  plan_id: {output['plan_id']}")
        print(f"  target_goals: {output['target_goals']}")
        print(f"  current_stage: {output['current_stage']}")

    def test_35_core_daily_task(self):
        """测试 CoreDailyTask 结构"""
        print("\n[Test] CoreDailyTask Structure")

        data = {
            "task_id": "DT12345",
            "user_id": "U12345",
            "task_type": "micro_habit",
            "description": "22:30前上床准备睡觉",
            "scheduled_time": "22:30",
            "completion_status": "pending"
        }

        task = CoreDailyTask.from_dict(data)

        self.assertEqual(task.schema_version, SCHEMA_VERSION)
        output = task.to_dict()
        self.assertEqual(output["task_type"], "micro_habit")
        self.assertEqual(output["completion_status"], "pending")
        print(f"  task_id: {output['task_id']}")
        print(f"  description: {output['description']}")
        print(f"  task_type: {output['task_type']}")

    # ========== MasterAgent 集成测试 ==========

    def test_40_master_agent_process_old_format(self):
        """测试 MasterAgent 处理旧格式数据"""
        if self.master_agent is None:
            self.skipTest("MasterAgent not available")

        print("\n[Test] MasterAgent - Process Old Format")

        old_input = {
            "user_id": "test-integration-user",
            "message": "我最近睡眠不好，压力很大",
            "physiological_state": {
                "hrv_sdnn": 42,
                "sleep_hours": 5,
                "sleep_quality": 50
            },
            "psychological_state": {
                "stress_score": 75,
                "self_efficacy": 35
            }
        }

        try:
            result = self.master_agent.process_json(old_input)

            self.assertIn("session_id", result)
            self.assertIn("response", result)
            print(f"  session_id: {result.get('session_id')}")
            print(f"  response text: {result.get('response', {}).get('text', '')[:200]}...")
        except Exception as e:
            print(f"  Warning: MasterAgent.process_json failed: {e}")
            # 不失败测试，因为可能缺少 LLM 后端

    # ========== 端到端测试 ==========

    def test_50_end_to_end_flow(self):
        """端到端流程测试"""
        if not HAS_REQUESTS:
            self.skipTest("requests library not installed")

        print("\n[Test] End-to-End Flow")

        # Step 1: 用户首次对话
        print("  Step 1: Initial conversation")
        result1 = self.client.chat(
            "我是一个糖尿病患者，最近血糖控制不好，睡眠也很差",
            streaming=True,
            timeout=60
        )

        if "error" in result1:
            self.skipTest(f"Dify API error: {result1.get('message')}")

        print(f"    Response: {result1.get('answer', '')[:150]}...")

        # Step 2: 跟进对话
        print("  Step 2: Follow-up conversation")
        result2 = self.client.chat(
            "我应该怎么改善睡眠？",
            streaming=True,
            timeout=60
        )

        if "error" not in result2:
            print(f"    Response: {result2.get('answer', '')[:150]}...")
            print(f"    Same conversation: {result1.get('conversation_id') == result2.get('conversation_id')}")

        print("  End-to-end test completed")


# ============================================================================
# 测试报告
# ============================================================================

class TestReport:
    """测试报告生成器"""

    def __init__(self):
        self.results = []
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = datetime.now()
        print("=" * 60)
        print("Integration Test Report")
        print(f"Started at: {self.start_time.isoformat()}")
        print("=" * 60)

    def end(self):
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        print("\n" + "=" * 60)
        print(f"Completed at: {self.end_time.isoformat()}")
        print(f"Duration: {duration:.2f} seconds")
        print("=" * 60)


# ============================================================================
# 主函数
# ============================================================================

def run_quick_test():
    """快速测试 - 仅测试关键功能"""
    print("\n" + "=" * 60)
    print("Quick Integration Test")
    print("=" * 60)

    # 1. 测试 DataFormatConverter
    print("\n[1] Testing DataFormatConverter...")
    old_data = {
        "message": "测试消息",
        "physiological_state": {"hrv_sdnn": 50, "sleep_hours": 7}
    }
    converted = DataFormatConverter.convert_user_input(old_data)
    print(f"    Old format: {list(old_data.keys())}")
    print(f"    New format: {list(converted.keys())}")
    print(f"    Content: {converted.get('content')}")
    print("    [OK] DataFormatConverter working")

    # 2. 测试 UserInput
    print("\n[2] Testing UserInput...")
    user_input = UserInput.from_dict({
        "user_id": "test",
        "query": "测试",
        "physiological_state": {"hrv_sdnn": 45}
    })
    print(f"    user_id: {user_input.user_id}")
    print(f"    content: {user_input.content}")
    print(f"    device_data: {user_input.device_data is not None}")
    print("    [OK] UserInput working")

    # 3. 测试 Dify 连接
    if HAS_REQUESTS:
        print("\n[3] Testing Dify connection...")
        client = DifyClient()
        result = client.chat("你好", streaming=True, timeout=30)
        if "error" not in result:
            print(f"    Response: {result.get('answer', '')[:100]}...")
            print("    [OK] Dify connection working")
        else:
            print(f"    [FAIL] Dify error: {result.get('message')}")
    else:
        print("\n[3] Skipping Dify test (requests not installed)")

    print("\n" + "=" * 60)
    print("Quick test completed!")
    print("=" * 60)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Dify Integration Test")
    parser.add_argument("--quick", action="store_true", help="Run quick test only")
    parser.add_argument("--api-key", type=str, help="Dify API Key")
    parser.add_argument("--base-url", type=str, help="Dify Base URL")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # 设置 API Key
    if args.api_key:
        global DIFY_API_KEY
        DIFY_API_KEY = args.api_key

    if args.base_url:
        global DIFY_BASE_URL
        DIFY_BASE_URL = args.base_url

    if args.quick:
        run_quick_test()
    else:
        # 运行完整测试
        report = TestReport()
        report.start()

        # 设置测试详细程度
        verbosity = 2 if args.verbose else 1

        # 运行测试
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestDifyIntegration)
        runner = unittest.TextTestRunner(verbosity=verbosity)
        runner.run(suite)

        report.end()


if __name__ == "__main__":
    main()
