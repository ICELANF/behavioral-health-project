"""
向量数据库操作层 — Qdrant
放置: api/core/rag/vector_store.py

封装 Qdrant REST API, 不依赖 qdrant-client SDK (减少依赖)。
使用 httpx 直接调用 Qdrant HTTP 接口。
"""
import logging
import os
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")

# BHP 知识库集合名
COLLECTION_NAME = "bhp_knowledge"
EMBEDDING_DIM = 1024  # text-embedding-v3 维度


@dataclass
class SearchResult:
    """单条检索结果"""
    chunk_id: str
    score: float
    text: str
    metadata: dict


class QdrantStore:
    """Qdrant 向量存储操作"""

    def __init__(self, base_url: str | None = None, collection: str | None = None):
        self.base_url = (base_url or QDRANT_URL).rstrip("/")
        self.collection = collection or COLLECTION_NAME

    def _request(self, method: str, path: str, json: dict | None = None) -> dict:
        import httpx
        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=30) as client:
            resp = client.request(method, url, json=json)
            resp.raise_for_status()
            return resp.json()

    # ── 集合管理 ──

    def ensure_collection(self, dim: int = EMBEDDING_DIM) -> bool:
        """创建集合 (如不存在)"""
        try:
            resp = self._request("GET", f"/collections/{self.collection}")
            if resp.get("result"):
                logger.info(f"Collection '{self.collection}' exists")
                return False
        except Exception:
            pass

        self._request("PUT", f"/collections/{self.collection}", json={
            "vectors": {
                "size": dim,
                "distance": "Cosine",
            },
            "optimizers_config": {
                "indexing_threshold": 1000,
            },
        })
        logger.info(f"Collection '{self.collection}' created (dim={dim})")
        return True

    def delete_collection(self) -> bool:
        try:
            self._request("DELETE", f"/collections/{self.collection}")
            return True
        except Exception:
            return False

    def collection_info(self) -> dict:
        resp = self._request("GET", f"/collections/{self.collection}")
        result = resp.get("result", {})
        return {
            "name": self.collection,
            "points_count": result.get("points_count", 0),
            "vectors_count": result.get("vectors_count", 0),
            "status": result.get("status", "unknown"),
        }

    # ── 写入 ──

    def upsert(
        self,
        points: list[dict],
    ) -> int:
        """
        批量写入向量

        points 格式:
        [
            {
                "id": "doc_001_chunk_003",
                "vector": [0.1, 0.2, ...],
                "payload": {"text": "...", "source": "...", "doc_type": "..."}
            }
        ]
        """
        # Qdrant 要求 ID 为整数或 UUID, 这里用 hash
        formatted = []
        for p in points:
            pid = p["id"]
            if isinstance(pid, str):
                pid = abs(hash(pid)) % (2**63)  # 转为正整数
            formatted.append({
                "id": pid,
                "vector": p["vector"],
                "payload": {
                    **p.get("payload", {}),
                    "chunk_id": p["id"],  # 保留原始 string ID
                },
            })

        # 分批写入 (每批100条)
        total = 0
        for i in range(0, len(formatted), 100):
            batch = formatted[i:i+100]
            self._request("PUT", f"/collections/{self.collection}/points", json={
                "points": batch,
            })
            total += len(batch)

        logger.info(f"Upserted {total} points to '{self.collection}'")
        return total

    # ── 检索 ──

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        score_threshold: float = 0.3,
        filter_conditions: dict | None = None,
    ) -> list[SearchResult]:
        """
        向量相似度检索

        Args:
            query_vector: 查询向量
            top_k: 返回条数
            score_threshold: 最低相似度 (0-1)
            filter_conditions: Qdrant 过滤条件

        Returns:
            排序后的 SearchResult 列表
        """
        payload: dict = {
            "vector": query_vector,
            "top": top_k,
            "with_payload": True,
            "score_threshold": score_threshold,
        }
        if filter_conditions:
            payload["filter"] = filter_conditions

        resp = self._request(
            "POST",
            f"/collections/{self.collection}/points/search",
            json=payload,
        )

        results = []
        for hit in resp.get("result", []):
            pl = hit.get("payload", {})
            results.append(SearchResult(
                chunk_id=pl.get("chunk_id", str(hit.get("id", ""))),
                score=hit.get("score", 0.0),
                text=pl.get("text", ""),
                metadata={k: v for k, v in pl.items() if k not in ("text", "chunk_id")},
            ))

        return results

    def search_with_filter(
        self,
        query_vector: list[float],
        doc_type: str | None = None,
        source: str | None = None,
        top_k: int = 5,
    ) -> list[SearchResult]:
        """按文档类型/来源过滤检索"""
        conditions = []
        if doc_type:
            conditions.append({
                "key": "doc_type",
                "match": {"value": doc_type},
            })
        if source:
            conditions.append({
                "key": "source",
                "match": {"value": source},
            })

        filt = {"must": conditions} if conditions else None
        return self.search(query_vector, top_k=top_k, filter_conditions=filt)

    # ── 删除 ──

    def delete_by_source(self, source: str) -> bool:
        """按来源删除所有 chunk (用于重新导入)"""
        try:
            self._request(
                "POST",
                f"/collections/{self.collection}/points/delete",
                json={
                    "filter": {
                        "must": [{"key": "source", "match": {"value": source}}],
                    },
                },
            )
            logger.info(f"Deleted points with source='{source}'")
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False
