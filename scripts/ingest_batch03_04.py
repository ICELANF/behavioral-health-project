"""
BHP知识库 Batch03+04 向量入库脚本
34个KI文件 → chunk → mxbai-embed-large 1024dim → Qdrant bhp_knowledge

用法: python scripts/ingest_batch03_04.py
"""
import json
import os
import re
import sys
import time
import hashlib
import urllib.request
import urllib.error

# ── 配置 ──
QDRANT_URL = "http://localhost:6333"
COLLECTION = "bhp_knowledge"
OLLAMA_URL = "http://localhost:11434/api/embed"
EMBED_MODEL = "mxbai-embed-large"
VECTOR_DIM = 1024
CHUNK_SIZE = 512       # v4.0: ~512字符
CHUNK_OVERLAP = 50
MAX_EMBED_CHARS = 340  # mxbai context=512 tokens, Chinese≈1.5 tok/char

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge")

# ── 34个待入库文件 ──
FILES = [
    # Batch03
    ("kb_clinical/KI-CGM-AACE-CONSENSUS-2024.md", "CGM", "T1", "batch03"),
    ("kb_clinical/KI-DM-ACLM-LIFESTYLE-CPG-2025.md", "DM", "T1", "batch03"),
    ("kb_clinical/KI-DM-CGM-2021-blood-glucose-monitoring.md", "DM", "T1", "batch03"),
    ("kb_clinical/KI-GUT-MICROBIOME-2024.md", "NUTR", "T2", "batch03"),
    ("kb_tcm/KI-TCM-NEIJING-BH-CORE-2024.md", "TCM", "T1", "batch03"),
    ("kb_tcm/KI-TCM-CONSTITUTION-chapters1-6.md", "TCM", "T1", "batch03"),
    ("kb_theory/KI-COACH-ICF-COMPETENCY-2024.md", "COACHING", "T2", "batch03"),
    ("kb_theory/KI-NEURO-BRAIN-BODY-AMEN-2024.md", "NEURO", "T2", "batch03"),
    ("kb_theory/KI-PHIL-ELEMENT-ROBINSON-2024.md", "PHIL", "T2", "batch03"),
    ("kb_theory/psychology/KI-ADDIC-PSYCHOLOGY-SHEN-2024.md", "PSYCH", "T2", "batch03"),
    ("kb_theory/behavioral/KI-BCT-NCDS-CONSENSUS-2024.md", "BCT", "T1", "batch03"),
    ("kb_ops/KI-OPS-IMMERSIVE-PROGRAM-2024.md", "OPS", "T3", "batch03"),
    ("kb_ops/KI-OPS-INSTITUTIONAL-POLICE-2025.md", "OPS", "T3", "batch03"),
    # Batch04
    ("kb_clinical/KI-DM-ACLM-001_生活方式干预T2D缓解指南.md", "DM", "T1", "batch04"),
    ("kb_clinical/KI-DM-ACLM-002_T2D运动处方FITT框架.md", "DM", "T1", "batch04"),
    ("kb_clinical/KI-DM-ACLM-003-004_营养处方与行为改变.md", "DM", "T1", "batch04"),
    ("kb_clinical/KI-DM-VADOD-001-003_诊断标准与管理.md", "DM", "T1", "batch04"),
    ("kb_clinical/KI-DM-BLI-糖尿病行为生活方式干预指南2024.md", "DM", "T1", "batch04"),
    ("kb_clinical/KI-DM-CGM-持续血糖监测作为行为改变工具系统综述2024.md", "DM", "T2", "batch04"),
    ("kb_clinical/KI-DM-REV8-逆转糖尿病8个策略-乔斯林.md", "DM", "T1", "batch04"),
    ("kb_clinical/KI-CD-LIFESTYLE-逆转慢性病-生活方式医学.md", "CD", "T1", "batch04"),
    ("kb_clinical/KI-CD-SELFHEAL-自愈力的真相-心身医学.md", "CD", "T3", "batch04"),
    ("kb_theory/behavioral/KI-BCT-FOGG-001-002_福格行为模型.md", "BCT", "T2", "batch04"),
    ("kb_theory/behavioral/KI-BT-BCW-行为改变轮干预设计框架.md", "BCT", "T2", "batch04"),
    ("kb_tcm/KI-TCM-NEIJING-001_黄帝内经系统思维.md", "TCM", "T2", "batch04"),
    ("kb_theory/psychology/KI-PSYCH-BURG-001-002_人格心理学.md", "PSYCH", "T2", "batch04"),
    ("kb_theory/psychology/KI-BIO-KAL-001-002_生物心理学.md", "PSYCH", "T2", "batch04"),
    ("kb_theory/psychology/KI-NUTR-EMO-001-002_食物与情绪.md", "NUTR", "T2", "batch04"),
    ("kb_theory/KI-LM-COMP-001-002_生活方式医学能力框架.md", "COACHING", "T2", "batch04"),
    ("kb_theory/KI-RES-ERICK-001-002_韧性成长.md", "PSYCH", "T2", "batch04"),
    ("kb_theory/KI-LEARN-ILL-001-002_学习理论上.md", "LEARN", "T2", "batch04"),
    ("kb_theory/KI-LEARN-ILL-003-004_学习理论下.md", "LEARN", "T2", "batch04"),
    ("kb_theory/KI-CULT-HUM-001_文化人文因素与健康.md", "CULT", "T2", "batch04"),
    ("kb_theory/KI-CM-MHWC-精通健康与健康教练进阶框架.md", "COACHING", "T3", "batch04"),
]


def get_embedding(text: str, retries: int = 3) -> list:
    text = text[:MAX_EMBED_CHARS].replace("\x00", "")
    payload = json.dumps({"model": EMBED_MODEL, "input": text}, ensure_ascii=False).encode("utf-8")
    for attempt in range(retries):
        try:
            req = urllib.request.Request(OLLAMA_URL, data=payload,
                                        headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            return result["embeddings"][0]
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            if attempt < retries - 1:
                print(f"    Retry {attempt+1}: {e}")
                time.sleep(3)
            else:
                raise


def chunk_text(text: str) -> list:
    """按v4.0规范切片: ~512字符, 50字符重叠, 优先在句末切割"""
    if len(text) <= CHUNK_SIZE:
        return [text.strip()] if text.strip() else []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        # 在70%位置之后找句末切割点
        if end < len(text):
            segment = text[start:end]
            for sep in ['\n\n', '。\n', '。', '\n', '；']:
                pos = segment.rfind(sep, int(CHUNK_SIZE * 0.7))
                if pos > 0:
                    end = start + pos + len(sep)
                    break
        chunk = text[start:end].strip()
        if len(chunk) >= 20:
            chunks.append(chunk)
        # 确保至少前进 CHUNK_SIZE - CHUNK_OVERLAP 个字符
        next_start = end - CHUNK_OVERLAP
        if next_start <= start:
            next_start = start + CHUNK_SIZE // 2
        start = next_start
    return chunks


def extract_ki_ids(text: str) -> list:
    """提取文档中的 KI-xxx-nnn ID"""
    return list(set(re.findall(r'KI-[A-Z]+-(?:[A-Z]+-)?(?:\d{3}(?:-\d{3})?)', text)))


def extract_heading(text: str) -> str:
    """提取第一个标题行"""
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('#'):
            return line.lstrip('#').strip()
    return ""


def stable_id(file_path: str, chunk_idx: int) -> int:
    """生成稳定的point ID (基于文件路径+chunk序号的hash)"""
    key = f"{file_path}::{chunk_idx}"
    h = int(hashlib.md5(key.encode()).hexdigest()[:15], 16)
    return h


def qdrant_upsert(points: list):
    """批量写入Qdrant"""
    payload = json.dumps({"points": points}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"{QDRANT_URL}/collections/{COLLECTION}/points?wait=true",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="PUT"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result.get("status") == "ok" or result.get("result", {}).get("status") == "completed"


def main():
    print(f"{'='*60}")
    print(f"BHP Batch03+04 向量入库")
    print(f"Qdrant: {QDRANT_URL}/{COLLECTION}")
    print(f"Model: {EMBED_MODEL} ({VECTOR_DIM}dim)")
    print(f"Files: {len(FILES)}")
    print(f"{'='*60}")

    # 验证embedding
    test_vec = get_embedding("测试")
    assert len(test_vec) == VECTOR_DIM, f"维度错误: {len(test_vec)} != {VECTOR_DIM}"
    print(f"Embedding验证: {VECTOR_DIM}dim OK\n")

    total_chunks = 0
    total_points = 0
    t0 = time.time()

    for idx, (rel_path, domain, tier, batch) in enumerate(FILES):
        fpath = os.path.normpath(os.path.join(KNOWLEDGE_DIR, rel_path))
        fname = os.path.basename(rel_path)

        if not os.path.exists(fpath):
            print(f"[{idx+1}/{len(FILES)}] SKIP (不存在): {rel_path}")
            continue

        with open(fpath, encoding="utf-8") as f:
            content = f.read()

        ki_ids = extract_ki_ids(content)
        doc_heading = extract_heading(content)
        chunks = chunk_text(content)
        total_chunks += len(chunks)

        print(f"[{idx+1}/{len(FILES)}] {fname}: {len(chunks)} chunks, KIs={ki_ids[:3]}")

        # Embed + build points
        points = []
        for ci, chunk in enumerate(chunks):
            # 提取该chunk最近的标题
            heading = ""
            for line in chunk.split('\n'):
                if line.strip().startswith('#'):
                    heading = line.strip().lstrip('#').strip()
                    break
            embed_text = f"{heading}\n{chunk}" if heading else chunk

            vec = get_embedding(embed_text)

            point = {
                "id": stable_id(rel_path, ci),
                "vector": vec,
                "payload": {
                    "text": chunk,
                    "file": rel_path,
                    "filename": fname,
                    "domain": domain,
                    "evidence_tier": tier,
                    "batch": batch,
                    "ki_ids": ki_ids,
                    "doc_heading": doc_heading,
                    "chunk_heading": heading,
                    "chunk_index": ci,
                    "chunk_total": len(chunks),
                    "char_count": len(chunk),
                    "embedding_model": EMBED_MODEL,
                    "embedding_dim": VECTOR_DIM,
                    "ingest_date": "2026-03-05",
                    "rule_version": "v4.0",
                }
            }
            points.append(point)

        # 批量写入 (每50个一批)
        for i in range(0, len(points), 50):
            batch_pts = points[i:i+50]
            ok = qdrant_upsert(batch_pts)
            if not ok:
                print(f"  WARNING: upsert可能失败 (batch {i}-{i+len(batch_pts)})")
        total_points += len(points)

        # 进度
        elapsed = time.time() - t0
        rate = total_chunks / elapsed if elapsed > 0 else 0
        print(f"  → 累计 {total_points} points, {rate:.1f} chunks/s")

    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print(f"完成! {len(FILES)} 文件, {total_chunks} chunks, {total_points} points")
    print(f"耗时: {elapsed:.0f}s ({total_chunks/elapsed:.1f} chunks/s)")

    # 验证Qdrant总量
    try:
        req = urllib.request.Request(f"{QDRANT_URL}/collections/{COLLECTION}")
        with urllib.request.urlopen(req) as resp:
            info = json.loads(resp.read().decode("utf-8"))
        count = info["result"]["points_count"]
        print(f"Qdrant总量: {count} points")
    except Exception as e:
        print(f"验证失败: {e}")


if __name__ == "__main__":
    main()
