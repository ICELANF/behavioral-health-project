"""
Knowledge RAG API Router

提供知识库管理的 REST 端点:
  GET  /knowledge/docs           — 文档列表
  POST /knowledge/docs/upload    — 上传文档
  GET  /knowledge/docs/{id}      — 文档详情
  DELETE /knowledge/docs/{id}    — 删除文档
  GET  /knowledge/search         — 语义检索
  GET  /knowledge/domains        — 领域列表
  GET  /knowledge/stats          — 统计信息
"""
import sys, os
from typing import Optional

from fastapi import APIRouter, Query, UploadFile, File, HTTPException

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

router = APIRouter(tags=["knowledge"])


@router.get("/knowledge/docs")
async def list_documents(
    scope: Optional[str] = Query(None),
    domain_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """文档列表"""
    return {"docs": [], "total": 0, "skip": skip, "limit": limit}


@router.post("/knowledge/docs/upload")
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


@router.get("/knowledge/docs/{doc_id}")
async def get_document(doc_id: int):
    """文档详情"""
    raise HTTPException(404, f"文档 {doc_id} 不存在")


@router.delete("/knowledge/docs/{doc_id}")
async def delete_document(doc_id: int):
    """删除文档"""
    raise HTTPException(404, f"文档 {doc_id} 不存在")


@router.get("/knowledge/search")
async def search_knowledge(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    scope: Optional[str] = Query(None),
    domain_id: Optional[str] = Query(None),
    top_k: int = Query(5, ge=1, le=20),
):
    """语义检索"""
    return {"query": q, "results": [], "total": 0}


@router.get("/knowledge/domains")
async def list_domains():
    """领域列表"""
    from services.ingest import DOMAIN_SEEDS
    return [
        {"domain_id": k, "label": v["label"], "description": v["description"]}
        for k, v in DOMAIN_SEEDS.items()
    ]


@router.get("/knowledge/stats")
async def knowledge_stats():
    """知识库统计"""
    return {
        "total_documents": 0,
        "total_chunks": 0,
        "total_domains": 0,
        "scope_breakdown": {"platform": 0, "domain": 0, "tenant": 0},
    }


__all__ = ["router"]
