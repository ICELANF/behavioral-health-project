"""
BHP知识库向量入库脚本 · v1.0
适配: Qdrant + 1024dim embedding + 本地运行
知识规则: BHP知识库建设规则 v4.0
入库批次: DM糖尿病批次 · 2026-03-04

使用方式:
  1. 将本脚本和5个KI文档放在同一目录
  2. 确认 Qdrant 服务已启动（Docker Compose）
  3. 确认 Ollama 已启动，embedding模型已拉取
  4. 运行: python ingest_ki_dm.py

依赖:
  pip install qdrant-client ollama langchain-text-splitters
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────
# 配置区 · 按实际环境修改
# ─────────────────────────────────────────────

QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = 6333
COLLECTION_NAME = "bhp_knowledge"  # 与平台contract registry一致

# Embedding模型（1024dim）
# 选项1: Ollama本地模型（推荐：bge-m3 输出1024dim）
EMBEDDING_PROVIDER = "dashscope"
DASHSCOPE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"
DASHSCOPE_KEY = os.getenv("CLOUD_LLM_API_KEY", "")
DASHSCOPE_MODEL = "text-embedding-v3"  # 项目标准: 1024dim

# 选项2: 若使用其他embedding服务，在此切换
# EMBEDDING_PROVIDER = "openai"  # 需要设置 OPENAI_API_KEY

VECTOR_SIZE = 1024  # 与平台Qdrant配置一致

# 切片参数 · v4.0规范：512字符/50字符重叠
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

# 知识文件目录（默认当前目录）
KI_DIR = Path(__file__).parent

# ─────────────────────────────────────────────
# 待入库文件列表
# ─────────────────────────────────────────────

KI_FILES = [
    {
        "file": "KI-DM-ACLM-001_生活方式干预T2D缓解指南.md",
        "domain": "DM",
        "source": "ACLM_CPG_2025",
        "evidence_tier": "T1",
        "source_grade": "C",
        "scope": "domain",
        "knowledge_layer": "L2",
        "ttm_stages": ["S0", "S1", "S2", "S3", "S4", "S5"],
        "agents": ["MetabolicAgent", "CoachAgent"],
        "ki_prefix": "KI-DM-ACLM-001",
    },
    {
        "file": "KI-DM-ACLM-002_T2D运动处方FITT框架.md",
        "domain": "DM_CEP",
        "source": "ACLM_CPG_2025_KAS4_5",
        "evidence_tier": "T1",
        "source_grade": "C",
        "scope": "domain",
        "knowledge_layer": "L2",
        "ttm_stages": ["S1", "S2", "S3", "S4"],
        "agents": ["ExerciseAgent", "MetabolicAgent"],
        "ki_prefix": "KI-DM-ACLM-002",
    },
    {
        "file": "KI-DM-ACLM-003-004_营养处方与行为改变.md",
        "domain": "DM_BCT_COACH",
        "source": "ACLM_CPG_2025_KAS7_8_12",
        "evidence_tier": "T1",
        "source_grade": "C",
        "scope": "domain",
        "knowledge_layer": "L2",
        "ttm_stages": ["S0", "S1", "S2", "S3", "S4", "S5"],
        "agents": ["NutritionAgent", "CoachAgent"],
        "ki_prefix": "KI-DM-ACLM-003",
    },
    {
        "file": "KI-DM-VADOD-001-003_诊断标准与管理.md",
        "domain": "DM_CGM",
        "source": "VA_DoD_DM_CPG_V6_2023",
        "evidence_tier": "T1",
        "source_grade": "C",
        "scope": "domain",
        "knowledge_layer": "L2",
        "ttm_stages": ["S0", "S1", "S2", "S3", "S4", "S5"],
        "agents": ["MetabolicAgent", "CoachAgent"],
        "ki_prefix": "KI-DM-VADOD-001",
    },
]

# ─────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────

def extract_ki_metadata(text: str, file_meta: dict) -> dict:
    """从文档头部YAML注释提取元数据，与file_meta合并"""
    meta = dict(file_meta)  # 基础元数据

    # 尝试提取第一个KI头部注释
    ki_id_match = re.search(r'##\s+(KI-[\w-]+)', text)
    if ki_id_match:
        meta["ki_id"] = ki_id_match.group(1)

    # 提取来源
    source_match = re.search(r'来源:\s*(.+?)(?:\n|-->)', text)
    if source_match:
        meta["source_full"] = source_match.group(1).strip()

    meta["ingest_date"] = datetime.now().isoformat()
    meta["ingest_batch"] = "DM_20260304"
    meta["rule_version"] = "v4.0"

    return meta


def split_by_ki_sections(content: str) -> list[dict]:
    """
    按 ## KI-xxx 标题分割文档为独立知识条目
    每个KI作为独立语义单元，再进行二次切片
    """
    # 按 ## KI- 标题分割
    pattern = r'(?=^## KI-)'
    sections = re.split(pattern, content, flags=re.MULTILINE)
    sections = [s.strip() for s in sections if s.strip() and 'KI-' in s]
    return sections


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    简单字符级切片（中文场景下字符切片比token切片更准确）
    v4.0规范：512字符 / 50字符重叠
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # 尽量在句末切割（避免切断句子）
        if end < len(text):
            # 向后找最近的句末符号
            for sep in ['。', '\n\n', '\n', '；', '。\n']:
                last_sep = chunk.rfind(sep)
                if last_sep > chunk_size * 0.7:  # 在70%以后找到分隔符
                    end = start + last_sep + len(sep)
                    chunk = text[start:end]
                    break

        chunks.append(chunk.strip())
        start = end - overlap

    return [c for c in chunks if c.strip()]



def get_embedding(text: str) -> list[float]:
    """DashScope text-embedding-v3 1024dim"""
    import urllib.request
    text = text[:340].replace("\x00", "")
    payload = json.dumps({"model": DASHSCOPE_MODEL, "input": text}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        DASHSCOPE_URL,
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {DASHSCOPE_KEY}"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result["data"][0]["embedding"]



# ─────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────

def setup_collection(client):
    """确保Qdrant集合存在且配置正确"""
    from qdrant_client.models import Distance, VectorParams

    collections = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME not in collections:
        print(f"[创建集合] {COLLECTION_NAME} (dim={VECTOR_SIZE})")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            )
        )
    else:
        print(f"[已存在] 集合 {COLLECTION_NAME}，追加入库")


def ingest_file(client, file_meta: dict) -> int:
    """处理单个KI文件，切片并入库"""
    from qdrant_client.models import PointStruct

    filepath = KI_DIR / file_meta["file"]
    if not filepath.exists():
        print(f"[跳过] 文件不存在: {filepath}")
        return 0

    print(f"\n[处理] {file_meta['file']}")
    content = filepath.read_text(encoding="utf-8")

    # 按KI条目分割
    ki_sections = split_by_ki_sections(content)
    if not ki_sections:
        # 无法分割则整体处理
        ki_sections = [content]

    print(f"  发现 {len(ki_sections)} 个KI条目")

    points = []
    total_chunks = 0
    point_id_base = abs(hash(file_meta["file"])) % (10**9)  # 文件级唯一基础ID

    for ki_idx, ki_text in enumerate(ki_sections):
        # 提取该KI的元数据
        meta = extract_ki_metadata(ki_text, file_meta)

        # 切片
        chunks = chunk_text(ki_text, CHUNK_SIZE, CHUNK_OVERLAP)
        print(f"  KI-{ki_idx+1}: {len(chunks)} 个切片")

        for chunk_idx, chunk in enumerate(chunks):
            if len(chunk.strip()) < 20:  # 跳过太短的片段
                continue

            # 生成embedding
            try:
                vector = get_embedding(chunk)
            except Exception as e:
                print(f"  [错误] embedding失败 (KI-{ki_idx+1}/chunk-{chunk_idx}): {e}")
                continue

            # 验证维度
            if len(vector) != VECTOR_SIZE:
                print(f"  [警告] 向量维度不匹配: 期望{VECTOR_SIZE}, 实际{len(vector)}")
                # 若模型输出不是1024dim，给出提示
                if len(vector) == 768:
                    print(f"  [提示] 检测到768dim输出，请确认DASHSCOPE_MODEL配置")

            # 构建payload
            payload = {
                **meta,
                "text": chunk,
                "ki_index": ki_idx,
                "chunk_index": chunk_idx,
                "chunk_total": len(chunks),
                "char_count": len(chunk),
            }

            # 生成稳定的point ID
            point_id = point_id_base + ki_idx * 1000 + chunk_idx

            points.append(PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            ))
            total_chunks += 1

    # 批量写入（每批100个）
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i+batch_size]
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=batch
        )
        print(f"  [写入] {i+len(batch)}/{len(points)} 个向量点")

    print(f"  [完成] {total_chunks} 个切片入库")
    return total_chunks


def verify_ingestion(client) -> None:
    """验证入库结果：执行测试查询"""
    print("\n" + "="*50)
    print("[验证] 执行测试查询...")

    test_queries = [
        "糖尿病患者每天应该运动多少分钟",
        "T2D缓解需要满足什么条件",
        "血糖低于多少需要立即处理",
        "SMART目标如何设定",
    ]

    for query in test_queries:
        try:
            vector = get_embedding(query)
            results = client.search(
                collection_name=COLLECTION_NAME,
                query_vector=vector,
                limit=2,
                score_threshold=0.5
            )
            if results:
                print(f"\n  查询: {query}")
                for r in results:
                    ki_id = r.payload.get('ki_prefix', 'N/A')
                    score = round(r.score, 3)
                    preview = r.payload.get('text', '')[:60].replace('\n', ' ')
                    print(f"    [{score}] {ki_id} | {preview}...")
            else:
                print(f"\n  查询: {query} → 无结果（score_threshold可能过高）")
        except Exception as e:
            print(f"\n  查询失败: {e}")


def generate_ingestion_report(total_points: int) -> None:
    """生成入库报告"""
    report = {
        "batch_id": "DM_20260304",
        "ingest_time": datetime.now().isoformat(),
        "collection": COLLECTION_NAME,
        "vector_dim": VECTOR_SIZE,
        "embed_model": DASHSCOPE_MODEL,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "files_processed": len(KI_FILES),
        "total_vectors": total_points,
        "rule_version": "v4.0",
        "ki_ids": [
            "KI-DM-ACLM-001", "KI-DM-ACLM-002",
            "KI-DM-ACLM-003", "KI-DM-ACLM-004",
            "KI-DM-VADOD-001", "KI-DM-VADOD-002", "KI-DM-VADOD-003"
        ]
    }

    report_path = KI_DIR / f"ingest_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[报告] 已保存至: {report_path}")


def main():
    print("=" * 60)
    print("BHP知识库向量入库脚本 v1.0")
    print(f"集合: {COLLECTION_NAME} | 维度: {VECTOR_SIZE}dim")
    print(f"切片: {CHUNK_SIZE}字符 / 重叠: {CHUNK_OVERLAP}字符")
    print(f"Embedding: {EMBEDDING_PROVIDER} / {DASHSCOPE_MODEL}")
    print("=" * 60)

    # 连接Qdrant
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        client.get_collections()  # 测试连接
        print(f"[连接] Qdrant {QDRANT_HOST}:{QDRANT_PORT} ✓")
    except Exception as e:
        print(f"[错误] 无法连接Qdrant: {e}")
        print("请确认 Docker Compose 已启动，Qdrant服务运行中")
        return

    # 确保集合存在
    setup_collection(client)

    # 逐文件入库
    total = 0
    for file_meta in KI_FILES:
        total += ingest_file(client, file_meta)

    print(f"\n{'='*60}")
    print(f"[汇总] 共入库 {total} 个向量点")

    # 验证查询
    verify_ingestion(client)

    # 生成报告
    generate_ingestion_report(total)

    print("\n[完成] 入库任务结束")


if __name__ == "__main__":
    main()
