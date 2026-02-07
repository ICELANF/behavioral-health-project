#!/usr/bin/env python3
"""
知识库入库脚本

读取 knowledge/ 下的 Markdown 文件 → 分块 → Ollama 嵌入 → 写入 DB

目录约定:
  knowledge/kb_theory/*.md     → scope=platform, domain=general
  knowledge/kb_case_studies/*.md → scope=platform, domain=按文件名推断
  knowledge/kb_domain/<domain>/*.md → scope=domain, domain_id=<domain>

用法:
  python scripts/ingest_knowledge.py
  python scripts/ingest_knowledge.py --dir knowledge/kb_theory --scope platform --domain general
"""

import os
import sys
import re
import json
import argparse
from datetime import datetime

# 添加项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from core.database import SessionLocal, engine
from core.models import Base, KnowledgeDocument, KnowledgeChunk
from core.knowledge.embedding_service import EmbeddingService


# ──────────────────────────────────────────
# 分块策略
# ──────────────────────────────────────────

def chunk_markdown(text: str, max_chars: int = 800, overlap: int = 100):
    """
    Markdown 分块策略:
      1. 先按 ## 标题分割成逻辑段
      2. 段内如果超长，再按段落分割
      3. 每块保留所属标题 (heading)
    """
    chunks = []
    current_heading = ""

    # 按 ## 标题分割
    sections = re.split(r'^(#{1,3}\s+.+)$', text, flags=re.MULTILINE)

    buffer = ""
    for section in sections:
        section = section.strip()
        if not section:
            continue

        # 检测标题
        if re.match(r'^#{1,3}\s+', section):
            # 先保存之前的 buffer
            if buffer.strip():
                for sub in _split_long(buffer.strip(), max_chars, overlap):
                    chunks.append({"heading": current_heading, "content": sub})
                buffer = ""
            current_heading = re.sub(r'^#{1,3}\s+', '', section).strip()
            continue

        buffer += "\n\n" + section

    # 收尾
    if buffer.strip():
        for sub in _split_long(buffer.strip(), max_chars, overlap):
            chunks.append({"heading": current_heading, "content": sub})

    return chunks


def _split_long(text: str, max_chars: int, overlap: int):
    """超长文本按段落切分"""
    if len(text) <= max_chars:
        return [text]

    paragraphs = text.split("\n\n")
    result = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 > max_chars and current:
            result.append(current.strip())
            # 保留尾部 overlap 字符
            current = current[-overlap:] + "\n\n" + para if overlap else para
        else:
            current = (current + "\n\n" + para) if current else para

    if current.strip():
        result.append(current.strip())

    return result


# ──────────────────────────────────────────
# 文件元数据推断
# ──────────────────────────────────────────

DOMAIN_KEYWORDS = {
    "nutrition": ["营养", "饮食", "膳食", "nutrition", "diet", "食物"],
    "exercise": ["运动", "锻炼", "exercise", "fitness", "康复"],
    "sleep": ["睡眠", "sleep", "失眠", "作息"],
    "mental": ["心理", "情绪", "mental", "焦虑", "抑郁", "压力"],
    "glucose": ["血糖", "糖尿", "glucose", "insulin", "胰岛素"],
    "tcm": ["中医", "体质", "经络", "tcm", "养生"],
    "cardiac": ["心脏", "心血管", "cardiac", "冠心"],
    "metabolism": ["代谢", "metabol", "内分泌"],
    "behavior": ["行为", "习惯", "behavior", "动机"],
}


def infer_domain(filename: str, content: str) -> str:
    """从文件名和内容推断领域"""
    text = (filename + " " + content[:500]).lower()
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text)
        if score > 0:
            scores[domain] = score
    if scores:
        return max(scores, key=scores.get)
    return "general"


def extract_metadata(content: str, filename: str):
    """从 Markdown 文件提取元数据"""
    title = filename.replace(".md", "").replace("_", " ").strip()
    author = ""
    source = ""

    # 尝试从 YAML frontmatter 提取
    fm_match = re.match(r'^---\s*\n(.+?)\n---', content, re.DOTALL)
    if fm_match:
        fm = fm_match.group(1)
        title_m = re.search(r'title:\s*(.+)', fm)
        author_m = re.search(r'author:\s*(.+)', fm)
        source_m = re.search(r'source:\s*(.+)', fm)
        if title_m:
            title = title_m.group(1).strip().strip('"').strip("'")
        if author_m:
            author = author_m.group(1).strip().strip('"').strip("'")
        if source_m:
            source = source_m.group(1).strip().strip('"').strip("'")

    # 从第一个 # 标题提取
    if not title or title == filename.replace(".md", ""):
        h1 = re.search(r'^#\s+(.+)', content, re.MULTILINE)
        if h1:
            title = h1.group(1).strip()

    return title, author, source


# ──────────────────────────────────────────
# 主入库逻辑
# ──────────────────────────────────────────

def ingest_directory(
    directory: str,
    scope: str = "platform",
    domain_id: str = None,
    tenant_id: str = None,
    priority: int = 5,
):
    """入库一个目录下的所有 Markdown 文件"""
    if not os.path.isdir(directory):
        print(f"❌ 目录不存在: {directory}")
        return

    md_files = [f for f in os.listdir(directory) if f.endswith(".md")]
    if not md_files:
        print(f"⚠️ 目录下无 .md 文件: {directory}")
        return

    print(f"\n📂 入库目录: {directory}")
    print(f"   scope={scope}, domain={domain_id or 'auto'}, files={len(md_files)}")

    embedder = EmbeddingService()
    db = SessionLocal()

    total_chunks = 0

    try:
        for filename in sorted(md_files):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            if not content.strip():
                print(f"  ⏭ 跳过空文件: {filename}")
                continue

            # 元数据
            title, author, source = extract_metadata(content, filename)
            file_domain = domain_id or infer_domain(filename, content)

            # 检查是否已入库
            existing = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.title == title,
                KnowledgeDocument.scope == scope,
            ).first()
            if existing:
                print(f"  ⏭ 已入库: {title} (id={existing.id})")
                continue

            # 分块
            chunks = chunk_markdown(content)
            if not chunks:
                print(f"  ⏭ 无有效内容: {filename}")
                continue

            # 创建文档
            doc = KnowledgeDocument(
                title=title,
                author=author,
                source=source,
                domain_id=file_domain,
                scope=scope,
                tenant_id=tenant_id,
                priority=priority,
                is_active=True,
                status="processing",
                file_path=filepath,
                chunk_count=len(chunks),
                created_at=datetime.utcnow(),
            )
            db.add(doc)
            db.flush()  # 获取 doc.id

            # 嵌入 & 创建 chunks
            texts = [c["content"] for c in chunks]
            print(f"  📄 {title} → {len(chunks)} 块, 嵌入中...")
            embeddings = embedder.embed_batch(texts)

            for i, (chunk_data, embedding) in enumerate(zip(chunks, embeddings)):
                chunk = KnowledgeChunk(
                    document_id=doc.id,
                    content=chunk_data["content"],
                    heading=chunk_data.get("heading", ""),
                    chunk_index=i,
                    doc_title=title,
                    doc_author=author,
                    doc_source=source,
                    scope=scope,
                    domain_id=file_domain,
                    tenant_id=tenant_id,
                    embedding=json.dumps(embedding) if embedding else None,
                    created_at=datetime.utcnow(),
                )
                db.add(chunk)

            doc.status = "ready"
            db.commit()
            total_chunks += len(chunks)
            print(f"  ✅ {title}: {len(chunks)} 块已入库 (domain={file_domain})")

        print(f"\n✅ 完成! 共入库 {total_chunks} 个文本块")

    except Exception as e:
        db.rollback()
        print(f"❌ 入库失败: {e}")
        raise
    finally:
        embedder.close()
        db.close()


def main():
    parser = argparse.ArgumentParser(description="知识库入库脚本")
    parser.add_argument("--dir", type=str, help="指定入库目录")
    parser.add_argument("--scope", type=str, default="platform", choices=["platform", "domain", "tenant"])
    parser.add_argument("--domain", type=str, default=None, help="领域ID (不指定则自动推断)")
    parser.add_argument("--tenant", type=str, default=None, help="租户ID (scope=tenant 时必须)")
    parser.add_argument("--priority", type=int, default=5, help="文档优先级 1-10")
    parser.add_argument("--init-db", action="store_true", help="初始化数据库表")
    args = parser.parse_args()

    if args.init_db:
        print("🔧 初始化数据库表...")
        Base.metadata.create_all(engine)
        print("✅ 数据库表已创建")

    if args.dir:
        ingest_directory(
            directory=args.dir,
            scope=args.scope,
            domain_id=args.domain,
            tenant_id=args.tenant,
            priority=args.priority,
        )
    else:
        # 默认: 入库所有 knowledge 子目录
        kb_root = os.path.join(PROJECT_ROOT, "knowledge")

        if not os.path.isdir(kb_root):
            print(f"⚠️ knowledge/ 目录不存在, 创建示例目录...")
            os.makedirs(os.path.join(kb_root, "kb_theory"), exist_ok=True)
            os.makedirs(os.path.join(kb_root, "kb_case_studies"), exist_ok=True)
            print(f"请将 Markdown 文件放入 {kb_root} 后重新运行")
            return

        # 先初始化表
        Base.metadata.create_all(engine)

        # 入库理论库
        theory_dir = os.path.join(kb_root, "kb_theory")
        if os.path.isdir(theory_dir):
            ingest_directory(theory_dir, scope="platform", domain_id="general")

        # 入库案例库
        case_dir = os.path.join(kb_root, "kb_case_studies")
        if os.path.isdir(case_dir):
            ingest_directory(case_dir, scope="platform")

        # 入库领域库 (按子目录名作为 domain_id)
        domain_dir = os.path.join(kb_root, "kb_domain")
        if os.path.isdir(domain_dir):
            for sub in sorted(os.listdir(domain_dir)):
                sub_path = os.path.join(domain_dir, sub)
                if os.path.isdir(sub_path):
                    ingest_directory(sub_path, scope="domain", domain_id=sub)


if __name__ == "__main__":
    main()
