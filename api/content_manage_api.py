"""
内容管理 API (需求3: 批量图文内容发布)

提供 ContentItem 的 CRUD 和批量发布功能。
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from loguru import logger

from core.database import get_db
from core.models import ContentItem, User, UserActivityLog
from api.dependencies import get_current_user, require_coach_or_admin

router = APIRouter(prefix="/api/v1/content-manage", tags=["内容管理"])


class ContentCreateRequest(BaseModel):
    content_type: str = "article"  # article/video/course/card/case
    title: str
    body: Optional[str] = None
    cover_url: Optional[str] = None
    media_url: Optional[str] = None
    domain: Optional[str] = None
    level: Optional[str] = None
    tenant_id: Optional[str] = None
    has_quiz: bool = False


class ContentUpdateRequest(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    cover_url: Optional[str] = None
    media_url: Optional[str] = None
    domain: Optional[str] = None
    level: Optional[str] = None
    has_quiz: Optional[bool] = None


def _item_to_dict(item: ContentItem) -> dict:
    return {
        "id": item.id,
        "content_type": item.content_type,
        "title": item.title,
        "body": item.body[:200] + "..." if item.body and len(item.body) > 200 else item.body,
        "cover_url": item.cover_url,
        "media_url": item.media_url,
        "domain": item.domain,
        "level": item.level,
        "author_id": item.author_id,
        "tenant_id": item.tenant_id,
        "status": item.status,
        "view_count": item.view_count,
        "like_count": item.like_count,
        "comment_count": item.comment_count,
        "collect_count": item.collect_count,
        "has_quiz": item.has_quiz,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


@router.post("/create")
def create_content(
    req: ContentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """创建内容条目"""
    item = ContentItem(
        content_type=req.content_type,
        title=req.title,
        body=req.body,
        cover_url=req.cover_url,
        media_url=req.media_url,
        domain=req.domain,
        level=req.level,
        author_id=current_user.id,
        tenant_id=req.tenant_id,
        has_quiz=req.has_quiz,
        status="draft",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(item)
    db.flush()
    try:
        db.add(UserActivityLog(
            user_id=current_user.id,
            activity_type="content.create",
            detail={"content_id": item.id, "title": req.title, "type": req.content_type},
            created_at=datetime.utcnow(),
        ))
        db.flush()
    except Exception:
        logger.warning("审计日志写入失败")
    db.commit()
    db.refresh(item)
    return _item_to_dict(item)


@router.post("/batch-create")
def batch_create_content(
    items: List[ContentCreateRequest],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """批量创建内容 (JSON数组)"""
    created = []
    for req in items[:50]:  # 最多50条
        item = ContentItem(
            content_type=req.content_type,
            title=req.title,
            body=req.body,
            cover_url=req.cover_url,
            media_url=req.media_url,
            domain=req.domain,
            level=req.level,
            author_id=current_user.id,
            tenant_id=req.tenant_id,
            has_quiz=req.has_quiz,
            status="draft",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(item)
        created.append(item)
    try:
        db.add(UserActivityLog(
            user_id=current_user.id,
            activity_type="content.batch_create",
            detail={"count": len(created), "titles": [r.title for r in items[:5]]},
            created_at=datetime.utcnow(),
        ))
        db.flush()
    except Exception:
        logger.warning("审计日志写入失败")
    db.commit()
    return {"created": len(created), "items": [_item_to_dict(i) for i in created]}


@router.get("/list")
def list_content(
    content_type: Optional[str] = None,
    status: Optional[str] = None,
    domain: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """列出内容"""
    query = db.query(ContentItem)
    if content_type:
        query = query.filter(ContentItem.content_type == content_type)
    if status:
        query = query.filter(ContentItem.status == status)
    if domain:
        query = query.filter(ContentItem.domain == domain)
    query = query.order_by(ContentItem.created_at.desc())
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return {"total": total, "items": [_item_to_dict(i) for i in items]}


@router.put("/{item_id}")
def update_content(
    item_id: int,
    req: ContentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """编辑内容"""
    item = db.query(ContentItem).filter(ContentItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "内容不存在")

    if req.title is not None:
        item.title = req.title
    if req.body is not None:
        item.body = req.body
    if req.cover_url is not None:
        item.cover_url = req.cover_url
    if req.media_url is not None:
        item.media_url = req.media_url
    if req.domain is not None:
        item.domain = req.domain
    if req.level is not None:
        item.level = req.level
    if req.has_quiz is not None:
        item.has_quiz = req.has_quiz

    item.updated_at = datetime.utcnow()
    try:
        db.add(UserActivityLog(
            user_id=current_user.id,
            activity_type="content.update",
            detail={"content_id": item_id, "fields": list(req.dict(exclude_unset=True).keys())},
            created_at=datetime.utcnow(),
        ))
        db.flush()
    except Exception:
        logger.warning("审计日志写入失败")
    db.commit()
    db.refresh(item)
    return _item_to_dict(item)


@router.post("/{item_id}/publish")
def publish_content(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """发布单个内容"""
    item = db.query(ContentItem).filter(ContentItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "内容不存在")

    item.status = "published"
    item.updated_at = datetime.utcnow()
    try:
        db.add(UserActivityLog(
            user_id=current_user.id,
            activity_type="content.publish",
            detail={"content_id": item_id},
            created_at=datetime.utcnow(),
        ))
        db.flush()
    except Exception:
        logger.warning("审计日志写入失败")
    db.commit()
    return {"message": "发布成功", "id": item.id}


@router.post("/batch-publish")
def batch_publish(
    item_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """批量发布"""
    count = 0
    for iid in item_ids[:100]:
        item = db.query(ContentItem).filter(ContentItem.id == iid).first()
        if item and item.status != "published":
            item.status = "published"
            item.updated_at = datetime.utcnow()
            count += 1
    try:
        db.add(UserActivityLog(
            user_id=current_user.id,
            activity_type="content.batch_publish",
            detail={"item_ids": item_ids[:10], "count": count},
            created_at=datetime.utcnow(),
        ))
        db.flush()
    except Exception:
        logger.warning("审计日志写入失败")
    db.commit()
    return {"published": count}


@router.delete("/{item_id}")
def delete_content(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """删除内容（标记归档）"""
    item = db.query(ContentItem).filter(ContentItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "内容不存在")

    item.status = "archived"
    item.updated_at = datetime.utcnow()
    try:
        db.add(UserActivityLog(
            user_id=current_user.id,
            activity_type="content.delete",
            detail={"content_id": item_id, "title": item.title},
            created_at=datetime.utcnow(),
        ))
        db.flush()
    except Exception:
        logger.warning("审计日志写入失败")
    db.commit()
    return {"message": "已归档"}
