# -*- coding: utf-8 -*-
"""
图片上传 API
Survey Image Upload API
"""
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from api.dependencies import get_current_user
from core.database import get_db
from core.models import User

router = APIRouter(prefix="/api/v1/upload", tags=["Upload"])

UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static", "uploads", "survey_images",
)
MAX_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@router.post("/survey-image")
async def upload_survey_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    上传问卷图片

    - 限制: 5MB, image/jpeg|png|webp|gif
    - 存储: static/uploads/survey_images/{userId}_{timestamp}_{uuid8}.{ext}
    - 返回: { url: "/api/static/uploads/survey_images/xxx.jpg" }
    """
    # Validate content type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file.content_type}，仅支持 JPEG/PNG/WebP/GIF",
        )

    # Read and validate size
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制 (最大 5MB，当前 {len(content) / 1024 / 1024:.1f}MB)",
        )

    # Build filename
    ext_map = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/gif": "gif",
    }
    ext = ext_map.get(file.content_type, "jpg")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    short_uuid = uuid.uuid4().hex[:8]
    filename = f"{current_user.id}_{timestamp}_{short_uuid}.{ext}"

    # Ensure directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Write file
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    url = f"/api/static/uploads/survey_images/{filename}"
    return {"url": url, "filename": filename}


# ── 头像上传 ──────────────────────────────────────────

AVATAR_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static", "uploads", "avatars",
)
AVATAR_MAX_SIZE = 2 * 1024 * 1024  # 2MB
AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    上传用户头像

    - 限制: 2MB, image/jpeg|png|webp
    - 存储: static/uploads/avatars/{userId}_{timestamp}_{uuid8}.{ext}
    - 自动更新 User.avatar_url, 删除旧文件
    - 返回: { url, filename }
    """
    if file.content_type not in AVATAR_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file.content_type}，仅支持 JPG/PNG/WebP",
        )

    content = await file.read()
    if len(content) > AVATAR_MAX_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件过大 (最大 2MB，当前 {len(content) / 1024 / 1024:.1f}MB)",
        )

    ext_map = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
    ext = ext_map.get(file.content_type, "jpg")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    short_uuid = uuid.uuid4().hex[:8]
    filename = f"{current_user.id}_{timestamp}_{short_uuid}.{ext}"

    os.makedirs(AVATAR_DIR, exist_ok=True)

    # Delete old avatar file if exists
    old_url = getattr(current_user, "avatar_url", None) or ""
    if old_url and "/avatars/" in old_url:
        old_filename = old_url.rsplit("/", 1)[-1]
        old_path = os.path.join(AVATAR_DIR, old_filename)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass

    # Write new file
    filepath = os.path.join(AVATAR_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    # Update DB
    url = f"/api/static/uploads/avatars/{filename}"
    current_user.avatar_url = url
    db.commit()

    return {"url": url, "filename": filename}
