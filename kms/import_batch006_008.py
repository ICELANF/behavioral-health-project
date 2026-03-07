"""
BHP KMS - BATCH-006/007/008 知识项批量导入脚本
22个成长类KI -> Qdrant 1024维向量库

来源:
  BATCH-006: HBR《自我发现与重塑》(9 KI)
  BATCH-007: 萨提亚模式 + 行为健康培训 (7 KI)
  BATCH-008: 李中莹 NLP《重塑心灵》(7 KI)

使用方法:
    python kms/import_batch006_008.py
"""

import os
import re
import sys
import time
import hashlib
from pathlib import Path

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
BATCH_SIZE = 3

# 源文件
CHUNK_FILES = [
    ("BATCH-006", "KI-GROWTH-HBR_自我发现与重塑_向量chunks.md"),
    ("BATCH-007", "KI-GROWTH-SATIR_萨提亚模式_行为健康培训_向量chunks.md"),
    ("BATCH-008", "KI-GROWTH-NLP_重塑心灵_李中莹NLP_向量chunks.md"),
]

# 源文件目录 (优先项目kms目录, 其次临时解压目录)
IMPORT_DIR = Path(__file__).parent
TEMP_DIR = Path(os.getenv("TEMP", "/tmp")) / "vector_import"


class DirectOllamaEmbedder:
    """直接调用 Ollama REST API, 绕过 EmbeddingService httpx 兼容性问题"""
    def __init__(self):
        import httpx
        self.model = os.getenv("OLLAMA_EMBED_MODEL", "mxbai-embed-large:latest")
        self.base_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
        self.expected_dim = EMBEDDING_DIM
        self.provider = "ollama-direct"
        self._client = httpx.Client(timeout=120.0)

    def embed_batch(self, texts: list) -> list:
        results = []
        for text in texts:
            try:
                resp = self._client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": text},
                )
                resp.raise_for_status()
                vec = resp.json().get("embedding", [])
                results.append(vec if len(vec) == self.expected_dim else [])
            except Exception as e:
                print(f"      Embed error: {e}")
                results.append([])
        return results

    def close(self):
        self._client.close()


def get_embedder():
    embedder = DirectOllamaEmbedder()
    # 验证连接
    import httpx
    try:
        resp = httpx.post(
            f"{embedder.base_url}/api/embeddings",
            json={"model": embedder.model, "prompt": "test"},
            timeout=30,
        )
        resp.raise_for_status()
        dim = len(resp.json().get("embedding", []))
        print(f"  Embedding: {embedder.model} @ {embedder.base_url}, dim={dim}")
    except Exception as e:
        print(f"  Embedding test failed: {e}")
        sys.exit(1)
    return embedder


def stable_id(ki_id: str) -> int:
    """生成稳定的数字ID (基于ki_id哈希)"""
    return int(hashlib.md5(ki_id.encode()).hexdigest()[:8], 16)


def detect_batch(ki_id: str) -> str:
    if "HBR" in ki_id:
        return "BATCH-006"
    if "SATIR" in ki_id or "COACH-BH" in ki_id:
        return "BATCH-007"
    if "NLP" in ki_id:
        return "BATCH-008"
    return "UNKNOWN"


def parse_ki_chunks(md_file: Path, batch_name: str) -> list:
    """解析MD文件, 按 ## KI- 分块"""
    content = md_file.read_text(encoding="utf-8")
    chunks = re.split(r'\n(?=## KI-)', content)

    results = []
    for chunk in chunks:
        if not chunk.startswith("## KI-"):
            continue

        header = chunk.split("\n")[0]
        ki_id_match = re.search(r'(KI-[\w-]+)', header)
        if not ki_id_match:
            continue
        ki_id = ki_id_match.group(1)
        title = header.replace("## ", "").strip()

        # 提取元数据
        meta_line = ""
        for line in chunk.split("\n"):
            if line.startswith("<!-- 领域:") or line.startswith("<!-- 类型:"):
                meta_line = line
                break

        stages = re.findall(r'S[0-6]', meta_line)
        growth_dim = ""
        gd_match = re.search(r'成长维度:([\w,_+]+)', meta_line)
        if gd_match:
            growth_dim = gd_match.group(1)

        evidence = "T2"
        ev_match = re.search(r'证据:(T\d)', meta_line)
        if ev_match:
            evidence = ev_match.group(1)

        domain = "growth"
        if "IDENT" in ki_id:
            domain = "identity"
        elif "MEANING" in ki_id:
            domain = "meaning"
        elif "COACH" in ki_id:
            domain = "coach"

        # 构建嵌入文本 (标题 + 核心内容)
        # mxbai-embed-large 上下文约512 tokens, 中文约300字
        text_for_embedding = f"{title}\n\n{chunk[:300]}"

        results.append({
            "ki_id": ki_id,
            "title": title,
            "text_for_embedding": text_for_embedding,
            "content_preview": chunk[:1500],
            "full_length": len(chunk),
            "batch": batch_name,
            "domain": domain,
            "applicable_stages": stages,
            "growth_dimension": growth_dim,
            "evidence_level": evidence,
            "source": "BHP_KMS_v4.0",
            "category": "knowledge_item",
            "subcategory": domain,
        })

    return results


def check_existing(client: QdrantClient, ki_id: str) -> bool:
    results = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(
            must=[FieldCondition(key="ki_id", match=MatchValue(value=ki_id))]
        ),
        limit=1,
    )
    return len(results[0]) > 0


def import_batch_items(client: QdrantClient, items: list, embedder):
    texts = [item["text_for_embedding"] for item in items]
    embeddings = embedder.embed_batch(texts)

    points = []
    for item, embedding in zip(items, embeddings):
        if not embedding:
            print(f"    SKIP {item['ki_id']}: embedding failed")
            continue
        payload = {k: v for k, v in item.items() if k != "text_for_embedding"}
        payload["import_time"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        point_id = stable_id(item["ki_id"])
        points.append(PointStruct(id=point_id, vector=embedding, payload=payload))

    if points:
        client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)


def find_file(filename: str) -> Path:
    """查找源文件: 优先kms目录, 其次临时目录"""
    for d in [IMPORT_DIR, TEMP_DIR]:
        p = d / filename
        if p.exists():
            return p
    return None


def main():
    print("=" * 60)
    print("BHP KMS - BATCH-006/007/008 成长类知识项导入")
    print("22个KI: HBR + 萨提亚 + NLP")
    print("=" * 60)

    # 解析所有文件
    all_items = []
    for batch_name, filename in CHUNK_FILES:
        fpath = find_file(filename)
        if not fpath:
            print(f"  [WARN] 找不到: {filename}")
            continue
        items = parse_ki_chunks(fpath, batch_name)
        print(f"  {batch_name}: {len(items)} KI from {fpath.name}")
        all_items.extend(items)

    if not all_items:
        print("  没有找到任何KI, 退出")
        sys.exit(1)

    print(f"\n  总计: {len(all_items)} KI")

    embedder = get_embedder()

    print(f"\n  Qdrant: {QDRANT_HOST}:{QDRANT_PORT}")
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        client.get_collections()
    except Exception as e:
        print(f"  连接失败: {e}")
        sys.exit(1)

    # 去重
    print("\n  检查重复...")
    new_items, skip_ids = [], []
    for item in all_items:
        if check_existing(client, item["ki_id"]):
            skip_ids.append(item["ki_id"])
        else:
            new_items.append(item)

    if skip_ids:
        print(f"  跳过已存在: {len(skip_ids)} ({', '.join(skip_ids[:5])}...)")
    print(f"  待导入: {len(new_items)}")

    if not new_items:
        print("\n  所有KI已存在, 无需导入")
        embedder.close()
        return

    # 分批导入
    print(f"\n  开始导入 (batch_size={BATCH_SIZE})...")
    total = 0
    for i in range(0, len(new_items), BATCH_SIZE):
        batch = new_items[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(new_items) + BATCH_SIZE - 1) // BATCH_SIZE
        ki_ids = [b["ki_id"] for b in batch]
        print(f"\n  batch {batch_num}/{total_batches}: {ki_ids}")

        try:
            count = import_batch_items(client, batch, embedder)
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

    # 按批次统计
    for batch_name, _ in CHUNK_FILES:
        try:
            res = client.scroll(
                collection_name=COLLECTION_NAME,
                scroll_filter=Filter(
                    must=[FieldCondition(key="batch", match=MatchValue(value=batch_name))]
                ),
                limit=100,
            )
            print(f"  {batch_name}: {len(res[0])} vectors")
        except Exception:
            pass

    print(f"\n{'=' * 60}")
    print(f"  导入完成: {total} 个成长类 KI")
    print(f"  集合: {COLLECTION_NAME}")
    print(f"  批次: BATCH-006 / BATCH-007 / BATCH-008")
    print(f"{'=' * 60}")

    embedder.close()


if __name__ == "__main__":
    main()
