"""
BHP KMS - 大五人格类型标签库批量导入脚本
BATCH-BIG5-001 | 20个典型人格类型 -> Qdrant 1024维向量库

复用平台 EmbeddingService (自动按 EMBEDDING_PROVIDER 选择 ollama/dashscope)

使用方法:
    # 容器内执行
    docker compose exec app python kms/import_big5_ki.py

    # 本地执行 (需 Ollama 运行中)
    python kms/import_big5_ki.py
"""

import os
import sys
import json
import time
from pathlib import Path

# 确保项目根目录在 path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue
)

# ── 配置 ──────────────────────────────────────────────
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = os.getenv("KMS_COLLECTION", "bhp_knowledge")
EMBEDDING_DIM = 1024
BATCH_SIZE = 5

KI_FILE = Path(__file__).parent / "big5_ki_items.json"


def get_embedder():
    """复用平台 EmbeddingService (自动按 EMBEDDING_PROVIDER 路由)"""
    from core.knowledge.embedding_service import EmbeddingService
    svc = EmbeddingService()
    print(f"  Embedding: provider={svc.provider}, model={svc.model}, dim={svc.expected_dim}")
    return svc


def ensure_collection(client: QdrantClient):
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        print(f"  创建集合: {COLLECTION_NAME}")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
    else:
        print(f"  集合已存在: {COLLECTION_NAME}")


def check_existing(client: QdrantClient, ki_id: str) -> bool:
    results = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(
            must=[FieldCondition(key="ki_id", match=MatchValue(value=ki_id))]
        ),
        limit=1,
    )
    return len(results[0]) > 0


def import_batch(client: QdrantClient, items: list, embedder, start_id: int):
    texts = [item["text_for_embedding"] for item in items]
    embeddings = embedder.embed_batch(texts)

    points = []
    for i, (item, embedding) in enumerate(zip(items, embeddings)):
        if not embedding:
            print(f"    SKIP {item['ki_id']}: embedding failed")
            continue
        payload = {k: v for k, v in item.items() if k != "text_for_embedding"}
        payload["import_time"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        payload["batch"] = "BATCH-BIG5-001"
        points.append(PointStruct(id=start_id + i, vector=embedding, payload=payload))

    if points:
        client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)


def main():
    print("=" * 60)
    print("BHP KMS - 大五人格类型标签库导入")
    print("BATCH-BIG5-001 | 20个典型人格类型")
    print("=" * 60)

    if not KI_FILE.exists():
        print(f"  找不到: {KI_FILE}")
        sys.exit(1)

    with open(KI_FILE, encoding="utf-8") as f:
        ki_items = json.load(f)
    print(f"  KI条目: {len(ki_items)} 个")

    embedder = get_embedder()

    print(f"\n  Qdrant: {QDRANT_HOST}:{QDRANT_PORT}")
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        client.get_collections()
    except Exception as e:
        print(f"  连接失败: {e}")
        sys.exit(1)

    ensure_collection(client)

    # 去重
    print("\n  检查重复...")
    new_items, skip_ids = [], []
    for item in ki_items:
        if check_existing(client, item["ki_id"]):
            skip_ids.append(item["ki_id"])
        else:
            new_items.append(item)

    if skip_ids:
        print(f"  跳过已存在: {len(skip_ids)} 个")
    print(f"  待导入: {len(new_items)} 个")

    if not new_items:
        print("\n  所有条目已存在，无需导入")
        embedder.close()
        return

    # 分批导入
    print(f"\n  开始导入 (batch_size={BATCH_SIZE})...")
    total = 0
    start_id = 10000

    for i in range(0, len(new_items), BATCH_SIZE):
        batch = new_items[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(new_items) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"\n  batch {batch_num}/{total_batches}: {[b['ki_id'] for b in batch]}")

        try:
            count = import_batch(client, batch, embedder, start_id=start_id + i)
            total += count
            print(f"    imported {count}")
        except Exception as e:
            print(f"    FAILED: {e}")

        if i + BATCH_SIZE < len(new_items):
            time.sleep(0.5)

    # 验证
    try:
        info = client.get_collection(COLLECTION_NAME)
        print(f"\n  集合总向量数: {info.vectors_count}")
    except Exception:
        pass

    print(f"\n{'=' * 60}")
    print(f"  导入完成: {total} 个大五人格类型 KI")
    print(f"  集合: {COLLECTION_NAME} | 批次: BATCH-BIG5-001")
    print(f"{'=' * 60}")

    embedder.close()


if __name__ == "__main__":
    main()
