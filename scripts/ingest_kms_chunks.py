import os, json, uuid, urllib.request, re
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

QDRANT_HOST = "qdrant"
COLLECTION = "bhp_knowledge"
DASHSCOPE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"
DASHSCOPE_KEY = os.getenv("CLOUD_LLM_API_KEY", "")
MODEL = "text-embedding-v3"

def embed(text):
    text = text[:340].replace("\x00", "")
    if not text.strip(): return None
    payload = json.dumps({"model": MODEL, "input": text}, ensure_ascii=False).encode()
    req = urllib.request.Request(DASHSCOPE_URL, data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {DASHSCOPE_KEY}"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())["data"][0]["embedding"]

files = [
    "/app/kms/KI-GROWTH-HBR_\u81ea\u6211\u53d1\u73b0\u4e0e\u91cd\u5851_\u5411\u91cf chunks.md",
    "/app/kms/KI-GROWTH-SATIR_\u8428\u63d0\u4e9a\u6a21\u5f0f_\u884c\u4e3a\u5065\u5eb7\u57f9\u8bad_\u5411\u91cf chunks.md",
    "/app/kms/KI-GROWTH-NLP_\u91cd\u5851\u5fc3\u7075_\u674e\u4e2d\u83b9NLP_\u5411\u91cf chunks.md",
]

import glob
actual_files = glob.glob("/app/kms/*chunks.md")
print(f"找到文件: {actual_files}")

client = QdrantClient(host=QDRANT_HOST, port=6333)
total = 0
for fpath in actual_files:
    text = open(fpath, encoding="utf-8", errors="ignore").read()
    # 按 --- 分割chunk
    sections = re.split(r'\n---+\n', text)
    fname = os.path.basename(fpath)
    points = []
    for i, sec in enumerate(sections):
        sec = sec.strip()
        if len(sec) < 20: continue
        try:
            vec = embed(sec)
            if not vec: continue
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=vec,
                payload={"source_file": fname, "chunk_index": i,
                         "batch": "kms_chunks_recovery", "text": sec[:200]}
            ))
        except Exception as e:
            print(f"  SKIP {fname}[{i}]: {e}")
    if points:
        client.upsert(collection_name=COLLECTION, points=points)
        total += len(points)
        print(f"  {fname}: {len(points)} chunks")

print(f"\n完成: {total} 向量")
print(f"集合总量: {client.get_collection(COLLECTION).points_count}")
