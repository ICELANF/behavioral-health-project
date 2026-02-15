# -*- coding: utf-8 -*-
"""
音频服务 — TTS 音频生成 + 管理

支持:
- edge-tts (免费, 离线可用, 默认)
- 云 TTS API (可配置)
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import time
from typing import Optional

logger = logging.getLogger(__name__)

# 音频存储目录
_AUDIO_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static", "audio",
)

# voice 映射
VOICE_MAP = {
    "tts_female": "zh-CN-XiaoxiaoNeural",
    "tts_male": "zh-CN-YunxiNeural",
}


class AudioService:
    """音频服务"""

    def __init__(self):
        os.makedirs(_AUDIO_DIR, exist_ok=True)
        self._edge_tts_available: Optional[bool] = None

    def _check_edge_tts(self) -> bool:
        if self._edge_tts_available is None:
            try:
                import edge_tts  # noqa: F401
                self._edge_tts_available = True
            except ImportError:
                self._edge_tts_available = False
                logger.warning("edge-tts not installed, TTS disabled")
        return self._edge_tts_available

    async def generate_tts(self, text: str,
                           voice: str = "tts_female") -> Optional[str]:
        """
        生成 TTS 音频文件.

        Args:
            text: 要转换的文本
            voice: 语音类型 (tts_female / tts_male)

        Returns:
            音频文件 URL 路径 (相对于 /api/static/), 或 None
        """
        if not text or not text.strip():
            return None

        if not self._check_edge_tts():
            return None

        try:
            import edge_tts

            # 生成文件名 (基于内容hash, 避免重复)
            text_hash = hashlib.sha256(f"{text}:{voice}".encode()).hexdigest()[:12]
            filename = f"tts_{text_hash}.mp3"
            filepath = os.path.join(_AUDIO_DIR, filename)

            # 如果已存在则直接返回
            if os.path.exists(filepath):
                return f"/api/static/audio/{filename}"

            # 生成音频
            voice_name = VOICE_MAP.get(voice, VOICE_MAP["tts_female"])
            communicate = edge_tts.Communicate(text[:3000], voice_name)
            await communicate.save(filepath)

            logger.info("TTS generated: %s (%d chars)", filename, len(text))
            return f"/api/static/audio/{filename}"

        except Exception as e:
            logger.error("TTS generation failed: %s", e)
            return None

    async def get_audio_for_content(self, content_id: int,
                                    db=None) -> Optional[dict]:
        """
        获取内容的音频附件信息.

        Args:
            content_id: 内容 ID
            db: 数据库 session

        Returns:
            音频信息 dict 或 None
        """
        if db is None:
            return None

        try:
            from core.models import ContentAudio
            audio = db.query(ContentAudio).filter(
                ContentAudio.content_item_id == content_id
            ).order_by(ContentAudio.created_at.desc()).first()

            if audio:
                return {
                    "id": audio.id,
                    "audio_url": audio.audio_url,
                    "duration_seconds": audio.duration_seconds,
                    "voice_type": audio.voice_type,
                }
            return None
        except Exception as e:
            logger.warning("Failed to get audio for content %d: %s", content_id, e)
            return None

    async def create_audio_for_content(self, content_id: int,
                                       text: str,
                                       voice: str = "tts_female",
                                       db=None) -> Optional[dict]:
        """
        为内容生成 TTS 音频并保存记录.

        Args:
            content_id: 内容 ID
            text: 内容文本
            voice: 语音类型
            db: 数据库 session

        Returns:
            音频记录 dict 或 None
        """
        audio_url = await self.generate_tts(text, voice)
        if not audio_url or db is None:
            return None

        try:
            from core.models import ContentAudio

            # 估算时长 (中文约 4 字/秒)
            duration = max(1, len(text.strip()) // 4)

            audio_record = ContentAudio(
                content_item_id=content_id,
                audio_url=audio_url,
                duration_seconds=duration,
                voice_type=voice,
                transcript=text[:5000] if text else None,
            )
            db.add(audio_record)
            db.commit()
            db.refresh(audio_record)

            return {
                "id": audio_record.id,
                "audio_url": audio_record.audio_url,
                "duration_seconds": audio_record.duration_seconds,
                "voice_type": audio_record.voice_type,
            }
        except Exception as e:
            logger.error("Failed to save audio record: %s", e)
            db.rollback()
            return None


# ── 单例 ──

_instance: Optional[AudioService] = None


def get_audio_service() -> AudioService:
    global _instance
    if _instance is None:
        _instance = AudioService()
    return _instance
