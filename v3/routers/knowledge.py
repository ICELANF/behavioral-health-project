"""
知识库管理路由 (Admin)
路径前缀: /api/v3/admin/knowledge
"""
from fastapi import APIRouter, Depends

from v3.schemas import APIResponse, KnowledgeLoadFileRequest, KnowledgeLoadDirRequest
from v3.dependencies import get_knowledge_loader, get_qdrant_store
from v3.auth import User, require_role
from core.rag.knowledge_loader import KnowledgeLoader
from core.rag.vector_store import QdrantStore

router = APIRouter(prefix="/api/v3/admin/knowledge", tags=["知识库管理 (Admin)"])

# 所有 Admin 路由需要 admin 或 bhp_master 角色
_admin_dep = require_role("admin", "bhp_master")


@router.get("/stats", response_model=APIResponse, summary="知识库统计")
def knowledge_stats(
    _admin: User = Depends(_admin_dep),
    store: QdrantStore = Depends(get_qdrant_store),
):
    """查看 Qdrant 集合统计: 文档数/向量数/状态"""
    try:
        info = store.collection_info()
        return APIResponse(data=info)
    except Exception as e:
        return APIResponse(ok=False, message=f"Qdrant 连接失败: {e}")


@router.post("/load-file", response_model=APIResponse, summary="加载单个知识文件")
def load_file(
    req: KnowledgeLoadFileRequest,
    _admin: User = Depends(_admin_dep),
    loader: KnowledgeLoader = Depends(get_knowledge_loader),
):
    """加载单个文件到知识库 (.md / .txt / .json)"""
    try:
        result = loader.load_file(
            filepath=req.filepath,
            doc_type=req.doc_type,
            replace=req.replace,
        )
        return APIResponse(data=result)
    except FileNotFoundError:
        return APIResponse(ok=False, message=f"文件不存在: {req.filepath}")
    except Exception as e:
        return APIResponse(ok=False, message=str(e))


@router.post("/load-dir", response_model=APIResponse, summary="加载知识目录")
def load_directory(
    req: KnowledgeLoadDirRequest,
    _admin: User = Depends(_admin_dep),
    loader: KnowledgeLoader = Depends(get_knowledge_loader),
):
    """批量加载目录下所有 .md/.txt/.json 文件"""
    try:
        result = loader.load_directory(
            dirpath=req.dirpath,
            doc_type_map=req.doc_type_map,
        )
        return APIResponse(data=result)
    except FileNotFoundError:
        return APIResponse(ok=False, message=f"目录不存在: {req.dirpath}")
    except Exception as e:
        return APIResponse(ok=False, message=str(e))


@router.post("/init", response_model=APIResponse, summary="初始化知识库集合")
def init_collection(
    _admin: User = Depends(_admin_dep),
    store: QdrantStore = Depends(get_qdrant_store),
):
    """创建 Qdrant 集合 (如不存在)"""
    created = store.ensure_collection()
    return APIResponse(
        data={"created": created},
        message="集合已创建" if created else "集合已存在",
    )


@router.delete("/reset", response_model=APIResponse, summary="重置知识库")
def reset_collection(
    _admin: User = Depends(_admin_dep),
    store: QdrantStore = Depends(get_qdrant_store),
):
    """删除并重建 Qdrant 集合 (危险操作!)"""
    store.delete_collection()
    store.ensure_collection()
    return APIResponse(message="知识库已重置")
