# -*- coding: utf-8 -*-
"""
音频处理 API — V5.2.0

端点:
  POST /api/v1/audio/transcribe  — 语音转文字 (ASR)
  GET  /api/v1/audio/asr-status  — ASR 服务状态
"""

from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from api.dependencies import get_current_user
from loguru import logger

router = APIRouter(prefix="/api/v1/audio", tags=["音频处理"])


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(..., description="音频文件 (webm/wav/mp3/m4a/ogg/flac)"),
    language: Optional[str] = Form(None, description="语言代码: zh/en/auto"),
    current_user=Depends(get_current_user),
):
    """
    语音转文字 (ASR)

    - 支持 webm, wav, mp3, m4a, ogg, flac 格式
    - 策略: cloud_first (OpenAI Whisper → 本地 ASR fallback)
    - Returns: {"text": str, "provider": str, "language": str}
    """
    from core.asr_service import ASRService

    # 验证文件类型
    allowed_extensions = {"webm", "wav", "mp3", "m4a", "ogg", "flac", "mp4", "mpeg"}
    filename = file.filename or "audio.webm"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的音频格式: .{ext}，支持: webm/wav/mp3/m4a/ogg/flac",
        )

    # 读取音频数据
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="音频文件为空")

    # 限制文件大小 (25MB — OpenAI Whisper 限制)
    max_size = 25 * 1024 * 1024
    if len(audio_bytes) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"音频文件过大: {len(audio_bytes) / 1024 / 1024:.1f}MB，最大 25MB",
        )

    user_id = current_user.id if hasattr(current_user, "id") else "unknown"
    logger.info(f"ASR request: user={user_id}, file={filename}, size={len(audio_bytes)} bytes")

    try:
        svc = ASRService()
        result = await svc.transcribe(audio_bytes, filename=filename, language=language)
        return {
            "code": 0,
            "message": "success",
            "data": result,
        }
    except RuntimeError as e:
        logger.error(f"ASR failed for user {user_id}: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/asr-status")
async def asr_status(current_user=Depends(get_current_user)):
    """检查 ASR 服务可用性"""
    from core.asr_service import ASRService
    svc = ASRService()
    return {
        "code": 0,
        "message": "success",
        "data": svc.is_available(),
    }
