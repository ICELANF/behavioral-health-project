#!/usr/bin/env python3
"""
蓝绿迁移: 768维 → 1024维 全量重嵌入脚本

将 knowledge_chunks 和 xzb_knowledge 中的内容用新模型 (mxbai-embed-large, 1024维)
重新嵌入，写入新列 (embedding_1024 / vector_embedding_1024)，旧列不动。

Usage:
    python scripts/migrate_embeddings_1024.py                    # 执行重嵌入
    python scripts/migrate_embeddings_1024.py --dry-run          # 只统计，不写入
    python scripts/migrate_embeddings_1024.py --validate         # 验证迁移质量
    python scripts/migrate_embeddings_1024.py --db postgresql://...
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from loguru import logger


def get_db_session(db_url: str):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine_url = db_url.replace("+asyncpg", "")
    engine = create_engine(engine_url)
    Session = sessionmaker(bind=engine)
    return Session()


def get_embedder():
    """创建 1024 维嵌入服务 (mxbai-embed-large)"""
    from core.knowledge.embedding_service import EmbeddingService
    svc = EmbeddingService()
    # 验证维度
    test_vec = svc.embed_query("维度测试")
    if not test_vec:
        logger.error("嵌入服务不可用，请确认 Ollama 运行中且 mxbai-embed-large 已拉取")
        sys.exit(1)
    dim = len(test_vec)
    if dim != 1024:
        logger.error(f"模型输出 {dim} 维，期望 1024 维。请检查 OLLAMA_EMBED_MODEL 环境变量")
        sys.exit(1)
    logger.info(f"嵌入服务就绪: model={svc.model}, dim={dim}")
    return svc


def migrate_knowledge_chunks(db, embedder, dry_run=False):
    """重嵌入 knowledge_chunks → embedding_1024"""
    from sqlalchemy import text

    # 统计
    total = db.execute(text(
        "SELECT COUNT(*) FROM knowledge_chunks WHERE embedding IS NOT NULL"
    )).scalar()
    already = db.execute(text(
        "SELECT COUNT(*) FROM knowledge_chunks WHERE embedding_1024 IS NOT NULL"
    )).scalar()

    logger.info(f"knowledge_chunks: 总计 {total} 条有旧向量, {already} 条已有新向量")

    if dry_run:
        logger.info(f"[DRY RUN] 需重嵌入: {total - already} 条")
        return {"total": total, "already": already, "embedded": 0, "errors": 0}

    # 批量处理
    rows = db.execute(text("""
        SELECT id, content FROM knowledge_chunks
        WHERE embedding IS NOT NULL AND embedding_1024 IS NULL
        ORDER BY id
    """)).fetchall()

    logger.info(f"待重嵌入: {len(rows)} 条")

    embedded = 0
    errors = 0
    batch_size = 20
    start = time.time()

    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        texts = [r[1] for r in batch]
        ids = [r[0] for r in batch]

        vectors = embedder.embed_batch(texts)

        for row_id, vec in zip(ids, vectors):
            if not vec or len(vec) != 1024:
                errors += 1
                continue
            db.execute(text(
                "UPDATE knowledge_chunks SET embedding_1024 = :vec WHERE id = :id"
            ), {"vec": json.dumps(vec), "id": row_id})
            embedded += 1

        db.commit()
        elapsed = time.time() - start
        rate = embedded / elapsed if elapsed > 0 else 0
        logger.info(f"  进度: {embedded}/{len(rows)} ({rate:.1f} chunks/s)")

    logger.info(f"knowledge_chunks 完成: {embedded} 嵌入, {errors} 失败")
    return {"total": total, "already": already, "embedded": embedded, "errors": errors}


def migrate_xzb_knowledge(db, embedder, dry_run=False):
    """重嵌入 xzb_knowledge → vector_embedding_1024"""
    from sqlalchemy import text

    # 检查表是否存在
    exists = db.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_name = 'xzb_knowledge'
        )
    """)).scalar()
    if not exists:
        logger.info("xzb_knowledge 表不存在，跳过")
        return {"total": 0, "embedded": 0, "errors": 0}

    # 检查新列是否存在
    col_exists = db.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'xzb_knowledge'
            AND column_name = 'vector_embedding_1024'
        )
    """)).scalar()
    if not col_exists:
        logger.warning("xzb_knowledge.vector_embedding_1024 列不存在，跳过")
        return {"total": 0, "embedded": 0, "errors": 0}

    total = db.execute(text(
        "SELECT COUNT(*) FROM xzb_knowledge WHERE vector_embedding IS NOT NULL"
    )).scalar()

    if dry_run:
        logger.info(f"[DRY RUN] xzb_knowledge: {total} 条待重嵌入")
        return {"total": total, "embedded": 0, "errors": 0}

    rows = db.execute(text("""
        SELECT id, content FROM xzb_knowledge
        WHERE vector_embedding IS NOT NULL AND vector_embedding_1024 IS NULL
        ORDER BY id
    """)).fetchall()

    logger.info(f"xzb_knowledge 待重嵌入: {len(rows)} 条")
    embedded = 0
    errors = 0

    for r in rows:
        vec = embedder.embed_query(r[1])
        if not vec or len(vec) != 1024:
            errors += 1
            continue
        db.execute(text(
            "UPDATE xzb_knowledge SET vector_embedding_1024 = CAST(:vec AS vector) WHERE id = :id"
        ), {"vec": str(vec), "id": str(r[0])})
        embedded += 1
        if embedded % 20 == 0:
            db.commit()
            logger.info(f"  xzb 进度: {embedded}/{len(rows)}")

    db.commit()
    logger.info(f"xzb_knowledge 完成: {embedded} 嵌入, {errors} 失败")
    return {"total": total, "embedded": embedded, "errors": errors}


def validate_migration(db):
    """Phase 3: 验证迁移质量"""
    from sqlalchemy import text
    import numpy as np

    logger.info("=== 迁移质量验证 ===")

    # 1. 完整性检查
    old_count = db.execute(text(
        "SELECT COUNT(*) FROM knowledge_chunks WHERE embedding IS NOT NULL"
    )).scalar()
    new_count = db.execute(text(
        "SELECT COUNT(*) FROM knowledge_chunks WHERE embedding_1024 IS NOT NULL"
    )).scalar()

    logger.info(f"完整性: 旧列 {old_count} 行, 新列 {new_count} 行")
    if old_count != new_count:
        logger.error(f"完整性不通过! 差异 {old_count - new_count} 行")
        return False

    # 2. 维度检查 (采样 10 条)
    samples = db.execute(text("""
        SELECT id, embedding_1024 FROM knowledge_chunks
        WHERE embedding_1024 IS NOT NULL LIMIT 10
    """)).fetchall()

    dim_ok = True
    for s in samples:
        vec = json.loads(s[1])
        if len(vec) != 1024:
            logger.error(f"维度错误: chunk id={s[0]}, dim={len(vec)}")
            dim_ok = False

    if dim_ok:
        logger.info(f"维度检查: 采样 {len(samples)} 条, 全部 1024 维 ✅")
    else:
        return False

    # 3. 语义检查 — 测试查询的 top-5 对比
    test_queries = [
        "情绪进食 压力大想喝奶茶",
        "血糖焦虑 指标没达标",
        "运动恐惧 害怕健身房",
        "家庭饮食冲突 油盐重",
        "习得性无助 天生没救",
    ]

    from core.knowledge.embedding_service import EmbeddingService
    embedder = EmbeddingService()

    def cosine_sim(a, b):
        a, b = np.array(a), np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))

    all_chunks_new = db.execute(text(
        "SELECT id, content, embedding_1024 FROM knowledge_chunks WHERE embedding_1024 IS NOT NULL"
    )).fetchall()

    logger.info(f"语义检查: {len(test_queries)} 条测试查询, {len(all_chunks_new)} 候选")

    for query in test_queries:
        qvec = embedder.embed_query(query)
        if not qvec:
            logger.warning(f"查询嵌入失败: {query}")
            continue

        scored = []
        for chunk in all_chunks_new:
            cvec = json.loads(chunk[2])
            score = cosine_sim(qvec, cvec)
            scored.append((chunk[0], chunk[1][:40], score))

        scored.sort(key=lambda x: x[2], reverse=True)
        top3 = scored[:3]
        logger.info(f"  Query: '{query[:20]}...'")
        for rank, (cid, content, score) in enumerate(top3, 1):
            logger.info(f"    #{rank}: score={score:.4f} | {content}...")

    logger.info("=== 验证完成 ===")
    return True


def main():
    parser = argparse.ArgumentParser(description="768→1024维 蓝绿迁移重嵌入脚本")
    parser.add_argument("--dry-run", action="store_true", help="只统计，不写入")
    parser.add_argument("--validate", action="store_true", help="验证迁移质量")
    parser.add_argument("--db", type=str, default=None, help="Database URL")
    args = parser.parse_args()

    db_url = (
        args.db
        or os.environ.get("DATABASE_URL")
        or "postgresql://postgres:difyai123456@localhost:5432/health_platform"
    )

    db = get_db_session(db_url)

    try:
        if args.validate:
            success = validate_migration(db)
            sys.exit(0 if success else 1)

        embedder = get_embedder()

        logger.info("=" * 50)
        logger.info("蓝绿迁移: 768维 → 1024维 全量重嵌入")
        logger.info(f"模型: {embedder.model}")
        logger.info(f"Dry run: {args.dry_run}")
        logger.info("=" * 50)

        # knowledge_chunks
        kc_stats = migrate_knowledge_chunks(db, embedder, args.dry_run)

        # xzb_knowledge
        xzb_stats = migrate_xzb_knowledge(db, embedder, args.dry_run)

        # 汇总
        logger.info("=" * 50)
        logger.info("迁移汇总:")
        logger.info(f"  knowledge_chunks: {kc_stats}")
        logger.info(f"  xzb_knowledge:    {xzb_stats}")

        total_errors = kc_stats["errors"] + xzb_stats["errors"]
        if total_errors > 0:
            logger.warning(f"共 {total_errors} 条嵌入失败")
            sys.exit(1)

        if not args.dry_run:
            logger.info("重嵌入完成! 下一步: python scripts/migrate_embeddings_1024.py --validate")

        embedder.close()

    finally:
        db.close()


if __name__ == "__main__":
    main()
