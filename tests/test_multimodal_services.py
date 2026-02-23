# -*- coding: utf-8 -*-
"""
测试 — 多模态服务 (ASR / VLM / Audio API / Food Recognition 解析器)
运行: python -m pytest tests/test_multimodal_services.py -v

覆盖:
  1. ASRService: 配置读取、disabled 拒绝、OpenAI 转录 mock、cloud_first fallback
  2. VLMService: 配置读取、disabled 拒绝、Ollama 分析 mock、ollama_first fallback
  3. audio_api: 文件验证 (空文件/超大/格式)、asr-status 响应结构
  4. food_recognition _parse_llm_response: JSON 直接解析、markdown 包裹、正则 fallback、完全失败
"""

import sys
import os
import json
import asyncio
import unittest
from unittest.mock import patch, AsyncMock, MagicMock

# 确保项目根目录在 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ══════════════════════════════════════════════════
# 1. ASRService 单元测试
# ══════════════════════════════════════════════════

class TestASRService(unittest.TestCase):
    """core/asr_service.py ASRService 测试"""

    def _run(self, coro):
        """Helper to run async in sync test"""
        return asyncio.run(coro)

    @patch("core.asr_service.ASR_PROVIDER", "cloud_first")
    @patch("core.asr_service.ASR_OPENAI_API_KEY", "test-key-123")
    @patch("core.asr_service.ASR_LANGUAGE", "zh")
    def test_init_reads_config(self):
        """ASRService 正确读取配置"""
        from core.asr_service import ASRService
        svc = ASRService()
        self.assertEqual(svc.provider, "cloud_first")
        self.assertEqual(svc.language, "zh")

    @patch("core.asr_service.ASR_PROVIDER", "disabled")
    def test_disabled_raises(self):
        """provider=disabled 时 transcribe 抛出 RuntimeError"""
        from core.asr_service import ASRService
        svc = ASRService()
        with self.assertRaises(RuntimeError) as ctx:
            self._run(svc.transcribe(b"fake-audio"))
        self.assertIn("禁用", str(ctx.exception))

    @patch("core.asr_service.ASR_PROVIDER", "openai")
    @patch("core.asr_service.ASR_OPENAI_API_KEY", "sk-test")
    @patch("core.asr_service.ASR_OPENAI_BASE_URL", "https://api.test.com/v1")
    @patch("core.asr_service.ASR_OPENAI_MODEL", "whisper-1")
    @patch("core.asr_service.ASR_TIMEOUT", 30.0)
    def test_openai_transcribe_success(self):
        """OpenAI 转录: mock httpx → 返回正确结构"""
        from core.asr_service import ASRService

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"text": "你好世界"}
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("core.asr_service.httpx.AsyncClient", return_value=mock_client):
            svc = ASRService()
            result = self._run(svc.transcribe(b"audio-bytes", "test.wav", "zh"))

        self.assertEqual(result["text"], "你好世界")
        self.assertEqual(result["provider"], "openai")
        self.assertEqual(result["language"], "zh")

    @patch("core.asr_service.ASR_PROVIDER", "openai")
    @patch("core.asr_service.ASR_OPENAI_API_KEY", "")
    def test_openai_no_key_raises(self):
        """OpenAI provider 无 API key → RuntimeError"""
        from core.asr_service import ASRService
        svc = ASRService()
        with self.assertRaises(RuntimeError) as ctx:
            self._run(svc.transcribe(b"audio", "test.wav"))
        self.assertIn("ASR_OPENAI_API_KEY", str(ctx.exception))

    @patch("core.asr_service.ASR_PROVIDER", "cloud_first")
    @patch("core.asr_service.ASR_OPENAI_API_KEY", "sk-test")
    @patch("core.asr_service.ASR_TIMEOUT", 10.0)
    def test_cloud_first_fallback(self):
        """cloud_first: OpenAI 失败 → 回退 Ollama/local"""
        from core.asr_service import ASRService

        # OpenAI mock: 抛异常
        openai_mock = AsyncMock(side_effect=Exception("OpenAI down"))
        # Local ASR mock: 成功
        local_resp = MagicMock()
        local_resp.json.return_value = {"text": "本地识别结果"}
        local_resp.raise_for_status = MagicMock()
        local_mock = AsyncMock(return_value=local_resp)

        call_count = {"n": 0}
        original_post = None

        async def mock_post(url, **kwargs):
            call_count["n"] += 1
            if "audio/transcriptions" in url:
                raise Exception("OpenAI down")
            return local_resp

        mock_client = AsyncMock()
        mock_client.post = mock_post
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("core.asr_service.httpx.AsyncClient", return_value=mock_client):
            svc = ASRService()
            result = self._run(svc.transcribe(b"audio", "test.webm"))

        self.assertEqual(result["text"], "本地识别结果")
        self.assertEqual(result["provider"], "local")

    @patch("core.asr_service.ASR_PROVIDER", "cloud_first")
    @patch("core.asr_service.ASR_OPENAI_API_KEY", "")
    def test_is_available_structure(self):
        """is_available 返回正确结构"""
        from core.asr_service import ASRService
        svc = ASRService()
        info = svc.is_available()
        self.assertIn("provider", info)
        self.assertIn("openai_configured", info)
        self.assertIn("status", info)
        self.assertEqual(info["provider"], "cloud_first")
        self.assertFalse(info["openai_configured"])
        self.assertEqual(info["status"], "ready")

    @patch("core.asr_service.ASR_PROVIDER", "disabled")
    def test_is_available_disabled(self):
        """disabled 时 status=disabled"""
        from core.asr_service import ASRService
        svc = ASRService()
        info = svc.is_available()
        self.assertEqual(info["status"], "disabled")


# ══════════════════════════════════════════════════
# 2. VLMService 单元测试
# ══════════════════════════════════════════════════

class TestVLMService(unittest.TestCase):
    """core/vlm_service.py VLMService 测试"""

    def _run(self, coro):
        return asyncio.run(coro)

    @patch("core.vlm_service.VLM_PROVIDER", "ollama_first")
    def test_init_reads_config(self):
        """VLMService 正确读取 provider"""
        from core.vlm_service import VLMService
        svc = VLMService()
        self.assertEqual(svc.provider, "ollama_first")

    @patch("core.vlm_service.VLM_PROVIDER", "disabled")
    def test_disabled_raises(self):
        """provider=disabled 时 analyze_image 抛出 RuntimeError"""
        from core.vlm_service import VLMService
        svc = VLMService()
        with self.assertRaises(RuntimeError) as ctx:
            self._run(svc.analyze_image("base64data", "analyze this"))
        self.assertIn("禁用", str(ctx.exception))

    @patch("core.vlm_service.VLM_PROVIDER", "ollama")
    @patch("core.vlm_service.VLM_OLLAMA_MODEL", "qwen2.5vl:7b")
    @patch("core.vlm_service.OLLAMA_API_URL", "http://localhost:11434")
    @patch("core.vlm_service.VLM_TIMEOUT", 30.0)
    def test_ollama_analyze_success(self):
        """Ollama VLM: mock httpx → 返回正确结构"""
        from core.vlm_service import VLMService

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "message": {"content": '{"food_name": "米饭", "calories": 200}'}
        }
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("core.vlm_service.httpx.AsyncClient", return_value=mock_client):
            svc = VLMService()
            result = self._run(svc.analyze_image("b64img", "分析食物"))

        self.assertEqual(result["provider"], "ollama")
        self.assertIn("food_name", result["text"])

    @patch("core.vlm_service.VLM_PROVIDER", "cloud")
    @patch("core.vlm_service.VLM_CLOUD_API_KEY", "")
    def test_cloud_no_key_raises(self):
        """Cloud provider 无 API key → RuntimeError"""
        from core.vlm_service import VLMService
        svc = VLMService()
        with self.assertRaises(RuntimeError) as ctx:
            self._run(svc.analyze_image("b64img", "prompt"))
        self.assertIn("VLM_CLOUD_API_KEY", str(ctx.exception))

    @patch("core.vlm_service.VLM_PROVIDER", "cloud")
    @patch("core.vlm_service.VLM_CLOUD_API_KEY", "sk-test")
    @patch("core.vlm_service.VLM_CLOUD_BASE_URL", "https://api.test.com/v1")
    @patch("core.vlm_service.VLM_CLOUD_MODEL", "qwen-vl-plus")
    @patch("core.vlm_service.VLM_TIMEOUT", 30.0)
    def test_cloud_analyze_success(self):
        """Cloud VLM: mock httpx → OpenAI-compatible 结构"""
        from core.vlm_service import VLMService

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "分析结果: 鸡蛋炒饭"}}]
        }
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("core.vlm_service.httpx.AsyncClient", return_value=mock_client):
            svc = VLMService()
            result = self._run(svc.analyze_image("b64img", "分析食物"))

        self.assertEqual(result["provider"], "cloud")
        self.assertEqual(result["text"], "分析结果: 鸡蛋炒饭")

    @patch("core.vlm_service.VLM_PROVIDER", "ollama_first")
    @patch("core.vlm_service.VLM_CLOUD_API_KEY", "sk-test")
    @patch("core.vlm_service.VLM_CLOUD_BASE_URL", "https://api.test.com/v1")
    @patch("core.vlm_service.VLM_CLOUD_MODEL", "qwen-vl-plus")
    @patch("core.vlm_service.VLM_TIMEOUT", 30.0)
    @patch("core.vlm_service.OLLAMA_API_URL", "http://localhost:11434")
    @patch("core.vlm_service.VLM_OLLAMA_MODEL", "qwen2.5vl:7b")
    def test_ollama_first_fallback_to_cloud(self):
        """ollama_first: Ollama 失败 → 回退 Cloud"""
        from core.vlm_service import VLMService

        call_urls = []

        cloud_resp = MagicMock()
        cloud_resp.json.return_value = {
            "choices": [{"message": {"content": "cloud结果"}}]
        }
        cloud_resp.raise_for_status = MagicMock()

        async def mock_post(url, **kwargs):
            call_urls.append(url)
            if "/api/chat" in url:
                raise ConnectionError("Ollama not running")
            return cloud_resp

        mock_client = AsyncMock()
        mock_client.post = mock_post
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("core.vlm_service.httpx.AsyncClient", return_value=mock_client):
            svc = VLMService()
            result = self._run(svc.analyze_image("b64img", "分析"))

        self.assertEqual(result["provider"], "cloud")
        self.assertEqual(result["text"], "cloud结果")
        # 确认先尝试 Ollama 再尝试 Cloud
        self.assertTrue(any("/api/chat" in u for u in call_urls))
        self.assertTrue(any("/chat/completions" in u for u in call_urls))

    @patch("core.vlm_service.VLM_PROVIDER", "ollama_first")
    @patch("core.vlm_service.VLM_CLOUD_API_KEY", "")
    @patch("core.vlm_service.OLLAMA_API_URL", "http://localhost:11434")
    @patch("core.vlm_service.VLM_OLLAMA_MODEL", "qwen2.5vl:7b")
    @patch("core.vlm_service.VLM_TIMEOUT", 5.0)
    def test_all_providers_fail_raises(self):
        """ollama_first + 无 cloud key: 所有提供者失败 → RuntimeError"""
        from core.vlm_service import VLMService

        async def mock_post(url, **kwargs):
            raise ConnectionError("Ollama not running")

        mock_client = AsyncMock()
        mock_client.post = mock_post
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("core.vlm_service.httpx.AsyncClient", return_value=mock_client):
            svc = VLMService()
            with self.assertRaises(RuntimeError) as ctx:
                self._run(svc.analyze_image("b64img", "分析"))
            self.assertIn("所有提供者均不可用", str(ctx.exception))

    @patch("core.vlm_service.VLM_PROVIDER", "ollama_first")
    @patch("core.vlm_service.VLM_CLOUD_API_KEY", "sk-test")
    @patch("core.vlm_service.OLLAMA_API_URL", "http://localhost:11434")
    @patch("core.vlm_service.VLM_OLLAMA_MODEL", "qwen2.5vl:7b")
    def test_is_available_structure(self):
        """is_available 返回正确字段"""
        from core.vlm_service import VLMService
        svc = VLMService()
        info = svc.is_available()
        self.assertIn("provider", info)
        self.assertIn("ollama_model", info)
        self.assertIn("cloud_configured", info)
        self.assertIn("status", info)
        self.assertEqual(info["provider"], "ollama_first")
        self.assertTrue(info["cloud_configured"])
        self.assertEqual(info["status"], "ready")


# ══════════════════════════════════════════════════
# 3. _parse_llm_response 单元测试
# ══════════════════════════════════════════════════

class TestParseLlmResponse(unittest.TestCase):
    """food_recognition_api._parse_llm_response 解析测试"""

    @classmethod
    def setUpClass(cls):
        from api.food_recognition_api import _parse_llm_response
        cls.parse = staticmethod(_parse_llm_response)

    def test_direct_json(self):
        """直接 JSON 字符串"""
        text = '{"food_name": "白米饭", "calories": 200, "protein": 4.0, "fat": 0.5, "carbs": 45, "fiber": 0.3, "advice": "建议搭配蔬菜"}'
        result = self.parse(text)
        self.assertEqual(result["food_name"], "白米饭")
        self.assertEqual(result["calories"], 200)
        self.assertEqual(result["protein"], 4.0)

    def test_markdown_wrapped_json(self):
        """```json 代码块包裹"""
        text = '```json\n{"food_name": "鸡蛋炒饭", "calories": 350, "advice": "热量适中"}\n```'
        result = self.parse(text)
        self.assertEqual(result["food_name"], "鸡蛋炒饭")
        self.assertEqual(result["calories"], 350)

    def test_markdown_no_lang_tag(self):
        """``` 无语言标签包裹"""
        text = '```\n{"food_name": "面条", "calories": 280}\n```'
        result = self.parse(text)
        self.assertEqual(result["food_name"], "面条")

    def test_json_embedded_in_text(self):
        """JSON 嵌入文字中"""
        text = '分析结果如下:\n{"food_name": "沙拉", "calories": 150, "protein": 5, "advice": "低热量"}\n以上是分析。'
        result = self.parse(text)
        self.assertEqual(result["food_name"], "沙拉")
        self.assertEqual(result["calories"], 150)

    def test_regex_fallback(self):
        """JSON 格式错误 → 正则 fallback"""
        text = '{"food_name": "红烧肉", "calories": 500, broken syntax here'
        result = self.parse(text)
        # 正则应能提取 food_name 和 calories
        self.assertEqual(result.get("food_name"), "红烧肉")
        self.assertEqual(result.get("calories"), 500.0)

    def test_complete_failure(self):
        """完全无法解析 → 返回默认"""
        text = "这张图片看不清楚，无法识别。"
        result = self.parse(text)
        self.assertEqual(result["food_name"], "未能识别")
        self.assertIn("请尝试", result["advice"])

    def test_whitespace_handling(self):
        """前后空白处理"""
        text = '   \n  {"food_name": "豆浆", "calories": 80}  \n  '
        result = self.parse(text)
        self.assertEqual(result["food_name"], "豆浆")

    def test_nested_foods_array(self):
        """包含 foods 数组的完整响应"""
        text = json.dumps({
            "food_name": "快餐套餐",
            "calories": 800,
            "protein": 30,
            "fat": 40,
            "carbs": 80,
            "fiber": 3,
            "foods": [
                {"name": "汉堡", "portion": "1个", "calories": 500},
                {"name": "薯条", "portion": "中份", "calories": 300},
            ],
            "advice": "热量较高，建议减少油炸食品",
        }, ensure_ascii=False)
        result = self.parse(text)
        self.assertEqual(result["food_name"], "快餐套餐")
        self.assertEqual(len(result["foods"]), 2)
        self.assertEqual(result["foods"][0]["name"], "汉堡")


# ══════════════════════════════════════════════════
# 4. Audio API 端点验证
# ══════════════════════════════════════════════════

class TestAudioAPIValidation(unittest.TestCase):
    """audio_api 端点输入验证测试 (使用 FastAPI TestClient)"""

    @classmethod
    def setUpClass(cls):
        """构建最小 FastAPI app 挂载 audio_api router"""
        try:
            from fastapi import FastAPI
            from fastapi.testclient import TestClient

            app = FastAPI()

            # Mock get_current_user 依赖
            mock_user = MagicMock()
            mock_user.id = 1

            from api.audio_api import router
            from api.dependencies import get_current_user

            app.include_router(router)
            app.dependency_overrides[get_current_user] = lambda: mock_user
            cls.client = TestClient(app)
            cls.available = True
        except Exception as e:
            cls.available = False
            cls.skip_reason = str(e)

    def setUp(self):
        if not self.available:
            self.skipTest(f"TestClient setup failed: {self.skip_reason}")

    def test_transcribe_empty_file(self):
        """空文件 → 400"""
        resp = self.client.post(
            "/api/v1/audio/transcribe",
            files={"file": ("test.wav", b"", "audio/wav")},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("空", resp.json()["detail"])

    def test_transcribe_unsupported_format(self):
        """不支持的格式 → 400"""
        resp = self.client.post(
            "/api/v1/audio/transcribe",
            files={"file": ("test.txt", b"not audio", "text/plain")},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("不支持", resp.json()["detail"])

    def test_transcribe_oversized_file(self):
        """超大文件 → 400"""
        # 26MB 的假数据
        big_data = b"x" * (26 * 1024 * 1024)
        resp = self.client.post(
            "/api/v1/audio/transcribe",
            files={"file": ("big.wav", big_data, "audio/wav")},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("过大", resp.json()["detail"])

    def test_asr_status_endpoint(self):
        """GET asr-status 返回正确结构"""
        resp = self.client.get("/api/v1/audio/asr-status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["code"], 0)
        self.assertIn("provider", data["data"])
        self.assertIn("status", data["data"])


# ══════════════════════════════════════════════════
# 5. Food Recognition VLM-Status 端点
# ══════════════════════════════════════════════════

class TestFoodRecognitionEndpoints(unittest.TestCase):
    """food_recognition_api vlm-status 端点测试"""

    @classmethod
    def setUpClass(cls):
        try:
            from fastapi import FastAPI
            from fastapi.testclient import TestClient

            app = FastAPI()

            mock_user = MagicMock()
            mock_user.id = 1

            from api.food_recognition_api import router
            from api.dependencies import get_current_user

            app.include_router(router)
            app.dependency_overrides[get_current_user] = lambda: mock_user
            cls.client = TestClient(app)
            cls.available = True
        except Exception as e:
            cls.available = False
            cls.skip_reason = str(e)

    def setUp(self):
        if not self.available:
            self.skipTest(f"TestClient setup failed: {self.skip_reason}")

    def test_vlm_status_endpoint(self):
        """GET vlm-status 返回正确结构"""
        resp = self.client.get("/api/v1/food/vlm-status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["code"], 0)
        self.assertIn("provider", data["data"])
        self.assertIn("ollama_model", data["data"])
        self.assertIn("cloud_configured", data["data"])
        self.assertIn("status", data["data"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
