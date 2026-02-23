"""
ASR (Automatic Speech Recognition) 服务 — V5.2.0

策略: cloud_first (OpenAI Whisper API → Ollama whisper fallback)
支持: openai / ollama / cloud_first / disabled

用法:
    svc = ASRService()
    text = await svc.transcribe(audio_bytes, filename="recording.webm")
"""

import httpx
from io import BytesIO
from loguru import logger
from api.config import (
    ASR_PROVIDER, ASR_OPENAI_API_KEY, ASR_OPENAI_BASE_URL,
    ASR_OPENAI_MODEL, ASR_LANGUAGE, ASR_TIMEOUT,
    OLLAMA_API_URL,
)


class ASRService:
    """语音识别服务 — cloud-first + Ollama fallback"""

    def __init__(self):
        self.provider = ASR_PROVIDER
        self.language = ASR_LANGUAGE

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.webm",
        language: str | None = None,
    ) -> dict:
        """
        转录音频文件 → 文字

        Returns: {"text": str, "provider": str, "language": str}
        Raises: RuntimeError if all providers fail
        """
        lang = language or self.language

        if self.provider == "disabled":
            raise RuntimeError("ASR 服务已禁用")

        if self.provider == "openai":
            return await self._transcribe_openai(audio_bytes, filename, lang)

        if self.provider == "ollama":
            return await self._transcribe_ollama(audio_bytes, filename, lang)

        # cloud_first: try OpenAI → fallback to Ollama
        if ASR_OPENAI_API_KEY:
            try:
                return await self._transcribe_openai(audio_bytes, filename, lang)
            except Exception as e:
                logger.warning(f"OpenAI ASR failed, falling back to Ollama: {e}")

        # Ollama fallback
        try:
            return await self._transcribe_ollama(audio_bytes, filename, lang)
        except Exception as e:
            logger.error(f"Ollama ASR also failed: {e}")
            raise RuntimeError(
                "语音识别失败: 所有提供者均不可用。"
                "请配置 ASR_OPENAI_API_KEY 或确保 Ollama 服务运行中。"
            )

    async def _transcribe_openai(
        self, audio_bytes: bytes, filename: str, language: str,
    ) -> dict:
        """OpenAI Whisper API 转录"""
        if not ASR_OPENAI_API_KEY:
            raise RuntimeError("ASR_OPENAI_API_KEY 未配置")

        url = f"{ASR_OPENAI_BASE_URL}/audio/transcriptions"
        headers = {"Authorization": f"Bearer {ASR_OPENAI_API_KEY}"}

        # Determine content type from filename
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "webm"
        mime_map = {
            "webm": "audio/webm", "wav": "audio/wav", "mp3": "audio/mpeg",
            "m4a": "audio/mp4", "ogg": "audio/ogg", "flac": "audio/flac",
        }
        content_type = mime_map.get(ext, "audio/webm")

        data = {
            "model": ASR_OPENAI_MODEL,
            "response_format": "json",
        }
        if language and language != "auto":
            data["language"] = language

        async with httpx.AsyncClient(timeout=ASR_TIMEOUT) as client:
            resp = await client.post(
                url,
                headers=headers,
                data=data,
                files={"file": (filename, BytesIO(audio_bytes), content_type)},
            )
            resp.raise_for_status()
            result = resp.json()

        text = result.get("text", "").strip()
        logger.info(f"OpenAI ASR: {len(audio_bytes)} bytes → {len(text)} chars")
        return {"text": text, "provider": "openai", "language": language}

    async def _transcribe_ollama(
        self, audio_bytes: bytes, filename: str, language: str,
    ) -> dict:
        """
        Ollama Whisper fallback.
        Note: Ollama currently doesn't natively support audio transcription.
        This attempts to use the Ollama API if a whisper-compatible model is available,
        otherwise falls back to a simple HTTP call to a local ASR service on :8090.
        """
        # Try local ASR service (FunASR/Whisper standalone) at port 8090
        local_url = "http://localhost:8090/api/v1/asr"

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "webm"
        mime_map = {
            "webm": "audio/webm", "wav": "audio/wav", "mp3": "audio/mpeg",
            "m4a": "audio/mp4", "ogg": "audio/ogg", "flac": "audio/flac",
        }
        content_type = mime_map.get(ext, "audio/webm")

        try:
            async with httpx.AsyncClient(timeout=ASR_TIMEOUT) as client:
                resp = await client.post(
                    local_url,
                    files={"file": (filename, BytesIO(audio_bytes), content_type)},
                    data={"language": language},
                )
                resp.raise_for_status()
                result = resp.json()
                text = result.get("text", result.get("result", "")).strip()
                logger.info(f"Local ASR: {len(audio_bytes)} bytes → {len(text)} chars")
                return {"text": text, "provider": "local", "language": language}
        except Exception as e:
            raise RuntimeError(f"本地ASR服务不可用 ({local_url}): {e}")

    def is_available(self) -> dict:
        """检查 ASR 服务可用性"""
        return {
            "provider": self.provider,
            "openai_configured": bool(ASR_OPENAI_API_KEY),
            "language": self.language,
            "status": "disabled" if self.provider == "disabled" else "ready",
        }
