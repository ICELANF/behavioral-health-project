"""
知识库 API 路由

端点:
  GET    /knowledge/docs           — 文档列表
  POST   /knowledge/docs/upload    — 上传文档
  GET    /knowledge/docs/{doc_id}  — 文档详情
  DELETE /knowledge/docs/{doc_id}  — 删除文档
  GET    /knowledge/search         — 语义检索
  GET    /knowledge/domains        — 领域列表
  GET    /knowledge/stats          — 统计信息
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class SearchResult(BaseModel):
    content: str
    source: str
    scope: str
    score: float
    chunk_id: Optional[int] = None


class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    total: int


@router.get("/docs")
async def list_documents(
    scope: Optional[str] = Query(None),
    domain_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """文档列表"""
    return {"docs": [], "total": 0, "skip": skip, "limit": limit}


@router.post("/docs/upload")
async def upload_document(
    file: UploadFile = File(...),
    scope: str = Query("platform"),
    domain_id: str = Query("general"),
    tenant_id: Optional[str] = Query(None),
):
    """上传并入库文档"""
    if not file:
        raise HTTPException(400, "文件不能为空")
    return {"doc_id": None, "filename": file.filename, "status": "queued"}


@router.get("/docs/{doc_id}")
async def get_document(doc_id: int):
    """文档详情"""
    raise HTTPException(404, f"文档 {doc_id} 不存在")


@router.delete("/docs/{doc_id}")
async def delete_document(doc_id: int):
    """删除文档"""
    raise HTTPException(404, f"文档 {doc_id} 不存在")


@router.get("/search", response_model=SearchResponse)
async def search_knowledge(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    scope: Optional[str] = Query(None),
    domain_id: Optional[str] = Query(None),
    top_k: int = Query(5, ge=1, le=20),
):
    """语义检索"""
    return SearchResponse(results=[], query=q, total=0)


@router.get("/domains")
async def list_domains():
    """领域列表"""
    try:
        from backend.services.ingest import DOMAIN_SEEDS
        return [
            {"domain_id": k, "label": v["label"], "description": v["description"]}
            for k, v in DOMAIN_SEEDS.items()
        ]
    except ImportError:
        return []


@router.get("/stats")
async def knowledge_stats():
    """知识库统计"""
    return {
        "total_documents": 0,
        "total_chunks": 0,
        "total_domains": 0,
        "scope_breakdown": {"platform": 0, "domain": 0, "tenant": 0},
    }


__all__ = ["router"]
