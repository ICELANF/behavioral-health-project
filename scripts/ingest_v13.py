import os, json, uuid, urllib.request
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

QDRANT_HOST = "qdrant"
COLLECTION = "bhp_knowledge"
DASHSCOPE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"
DASHSCOPE_KEY = os.getenv("CLOUD_LLM_API_KEY", "")
MODEL = "text-embedding-v3"

def embed(text):
    text = text[:340].replace("\x00", "")
    if not text.strip():
        return None
    payload = json.dumps({"model": MODEL, "input": text}, ensure_ascii=False).encode()
    req = urllib.request.Request(DASHSCOPE_URL, data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {DASHSCOPE_KEY}"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())["data"][0]["embedding"]

client = QdrantClient(host=QDRANT_HOST, port=6333)
data = json.load(open('/app/knowledge/vector_chunks/bhp_vector_chunks_v1.3.json'))
chunks = data.get('chunks', [])
print(f"待入库: {len(chunks)} chunks")

points = []
skipped = 0
for c in chunks:
    content = c.get('content', '').strip()
    if not content or len(content) < 10:
        skipped += 1
        continue
    try:
        vec = embed(content)
        if not vec:
            skipped += 1
            continue
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload={
                "chunk_id": c.get("chunk_id"),
                "document_id": c.get("document_id"),
                "knowledge_id": c.get("knowledge_id"),
                "heading": c.get("heading"),
                "text": content[:200],
                "batch": "v1.3_recovery",
            }
        ))
    except Exception as e:
        print(f"  SKIP {c.get('chunk_id')}: {e}")
        skipped += 1

client.upsert(collection_name=COLLECTION, points=points)
print(f"入库: {len(points)}, 跳过: {skipped}")
print(f"集合总量: {client.get_collection(COLLECTION).points_count}")
