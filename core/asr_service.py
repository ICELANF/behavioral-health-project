"""
ASR (Automatic Speech Recognition) 服务 — V5.3.0

策略: 本地 ASR 服务 (FunASR / Whisper standalone) 运行在 :8090
支持: ollama / disabled

用法:
    svc = ASRService()
    text = await svc.transcribe(audio_bytes, filename="recording.webm")
"""

import httpx
from io import BytesIO
from loguru import logger
from api.config import (
    ASR_PROVIDER, ASR_LANGUAGE, ASR_TIMEOUT,
)


class ASRService:
    """语音识别服务 — 本地 ASR"""

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

        return await self._transcribe_ollama(audio_bytes, filename, lang)

    async def _transcribe_ollama(
        self, audio_bytes: bytes, filename: str, language: str,
    ) -> dict:
        """
        本地 ASR 服务 (FunASR/Whisper standalone) at port 8090.
        """
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
            "language": self.language,
            "status": "disabled" if self.provider == "disabled" else "ready",
        }
