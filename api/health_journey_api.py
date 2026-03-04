# -*- coding: utf-8 -*-
"""
健康之路 API (案例分享 v2)

路由前缀: /api/v1/health-journey
content_type: health_journey  (兼容旧数据: case_share)
"""
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text as sa_text

from core.database import get_db
from core.models import ContentItem, ContentLike, ContentBookmark, UserActivityLog, User
from api.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/health-journey", tags=["健康之路"])

CONTENT_TYPES = ("health_journey", "case_share")  # 兼容旧数据

DOMAIN_LABELS = {
    "blood_glucose": "血糖管理",
    "weight":        "体重控制",
    "exercise":      "运动康复",
    "diet":          "饮食调整",
    "sleep":         "睡眠改善",
    "stress":        "压力管理",
    "medication":    "合理用药",
    "mental":        "心态调整",
    "general":       "综合健康",
}


class StoryCreate(BaseModel):
    title:       str            = Field(..., min_length=2, max_length=80)
    domain:      str            = Field(...)
    challenge:   str            = Field(..., min_length=5, max_length=1000)
    approach:    str            = Field(..., min_length=5, max_length=1000)
    outcome:     str            = Field(..., min_length=5, max_length=1000)
    reflection:  Optional[str]  = Field(None, max_length=800)
    is_anonymous: bool          = False
    media_urls:  Optional[List[str]] = []


def _author(db: Session, author_id: int) -> dict:
    row = db.execute(
        sa_text("SELECT full_name, username FROM users WHERE id=:id"),
        {"id": author_id}
    ).mappings().first()
    if not row:
        return {"name": "匿名", "id": 0}
    return {"name": row["full_name"] or row["username"] or "用户", "id": author_id}


def _to_card(item: ContentItem, author: dict) -> dict:
    preview = (item.body[:120] + "…") if item.body and len(item.body) > 120 else (item.body or "")
    return {
        "id":           item.id,
        "title":        item.title or "",
        "domain":       item.domain,
        "domain_label": DOMAIN_LABELS.get(item.domain or "", item.domain or ""),
        "preview":      preview,
        "author_name":  author["name"],
        "author_id":    author["id"],
        "like_count":   item.like_count or 0,
        "collect_count": item.collect_count or 0,
        "view_count":   item.view_count or 0,
        "created_at":   item.created_at.isoformat() if item.created_at else None,
    }


@router.get("")
def list_stories(
    page:      int            = Query(1, ge=1),
    page_size: int            = Query(20, ge=1, le=100),
    skip:      int            = Query(0, ge=0),
    limit:     int            = Query(0, ge=0),
    domain:    Optional[str]  = None,
    keyword:   Optional[str]  = None,
    db: Session = Depends(get_db),
):
    """列出健康之路故事（兼容 skip/limit 和 page/page_size 两种分页方式）"""
    if limit > 0:
        page_size = limit
        page = (skip // limit) + 1
    query = db.query(ContentItem).filter(
        ContentItem.content_type.in_(list(CONTENT_TYPES)),
        ContentItem.status == "published",
    )
    if domain:
        query = query.filter(ContentItem.domain == domain)
    if keyword:
        query = query.filter(ContentItem.title.ilike(f"%{keyword}%"))
    query = query.order_by(ContentItem.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    result = [_to_card(it, _author(db, it.author_id)) for it in items]
    return {"items": result, "total": total, "page": page, "page_size": page_size}


@router.get("/{story_id}")
def get_story(story_id: int, db: Session = Depends(get_db)):
    """获取故事详情"""
    item = db.query(ContentItem).filter(
        ContentItem.id == story_id,
        ContentItem.content_type.in_(list(CONTENT_TYPES)),
    ).first()
    if not item:
        raise HTTPException(404, "故事不存在")
    item.view_count = (item.view_count or 0) + 1
    db.commit()
    card = _to_card(item, _author(db, item.author_id))
    card["body"] = item.body or ""
    return card


@router.post("")
def create_story(
    story: StoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交健康故事"""
    body = (
        f"**挑战：**\n{story.challenge}\n\n"
        f"**方法：**\n{story.approach}\n\n"
        f"**成果：**\n{story.outcome}"
    )
    if story.reflection:
        body += f"\n\n**感悟：**\n{story.reflection}"
    if story.media_urls:
        body += "\n\n**媒体：**\n" + "\n".join(story.media_urls)

    item = ContentItem(
        content_type="health_journey",
        title=story.title,
        body=body,
        domain=story.domain,
        author_id=current_user.id,
        status="draft",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(item)
    db.add(UserActivityLog(
        user_id=current_user.id,
        activity_type="share",
        detail={"title": story.title, "domain": story.domain},
        created_at=datetime.utcnow(),
    ))
    db.commit()
    db.refresh(item)
    return {"success": True, "id": item.id, "message": "提交成功，审核后公开分享"}


@router.post("/{story_id}/like")
def like_story(
    story_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(ContentItem).filter(ContentItem.id == story_id).first()
    if not item:
        raise HTTPException(404, "故事不存在")
    existing = db.query(ContentLike).filter(
        ContentLike.user_id == current_user.id, ContentLike.content_id == story_id,
    ).first()
    if existing:
        db.delete(existing)
        item.like_count = max(0, (item.like_count or 0) - 1)
        db.commit()
        return {"liked": False, "like_count": item.like_count}
    db.add(ContentLike(user_id=current_user.id, content_id=story_id, created_at=datetime.utcnow()))
    item.like_count = (item.like_count or 0) + 1
    db.commit()
    return {"liked": True, "like_count": item.like_count}


@router.post("/{story_id}/helpful")
def helpful_story(
    story_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(ContentItem).filter(ContentItem.id == story_id).first()
    if not item:
        raise HTTPException(404, "故事不存在")
    existing = db.query(ContentBookmark).filter(
        ContentBookmark.user_id == current_user.id, ContentBookmark.content_id == story_id,
    ).first()
    if existing:
        db.delete(existing)
        item.collect_count = max(0, (item.collect_count or 0) - 1)
        db.commit()
        return {"marked": False, "helpful_count": item.collect_count}
    db.add(ContentBookmark(user_id=current_user.id, content_id=story_id, created_at=datetime.utcnow()))
    item.collect_count = (item.collect_count or 0) + 1
    db.commit()
    return {"marked": True, "helpful_count": item.collect_count}
