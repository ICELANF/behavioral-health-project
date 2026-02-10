"""
知识库管理 CLI — 加载/检索/统计
放置: api/scripts/load_knowledge.py

用法:
    # 加载整个知识目录
    python scripts/load_knowledge.py load --dir ./knowledge/

    # 加载单个文件
    python scripts/load_knowledge.py load --file ./knowledge/spec.md --type spec

    # 测试检索
    python scripts/load_knowledge.py search "SPI评分低于30"

    # 查看统计
    python scripts/load_knowledge.py stats

    # 重置知识库
    python scripts/load_knowledge.py reset
"""
import argparse
import json
import os
import sys

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm.client import LLMClient
from core.rag.vector_store import QdrantStore
from core.rag.knowledge_loader import KnowledgeLoader
from core.rag.pipeline import create_rag_pipeline


def cmd_load(args):
    """加载知识库"""
    client = LLMClient()
    store = QdrantStore(base_url=args.qdrant_url)
    loader = KnowledgeLoader(client, store)

    if args.file:
        print(f"📄 Loading file: {args.file} (type={args.type})")
        result = loader.load_file(args.file, doc_type=args.type)
        print(f"   ✅ {result['source']}: {result['chunks']} chunks, {result['vectors']} vectors")
    elif args.dir:
        print(f"📁 Loading directory: {args.dir}")
        doc_type_map = None
        if args.type_map:
            doc_type_map = json.loads(args.type_map)
        result = loader.load_directory(args.dir, doc_type_map=doc_type_map)
        print(f"   ✅ {result['files']} files, {result['total_chunks']} chunks, {result['total_vectors']} vectors")
        for d in result["details"]:
            print(f"      - {d['source']}: {d['chunks']} chunks")
    else:
        print("❌ Please specify --file or --dir")
        return

    print("\n📊 Collection info:")
    info = store.collection_info()
    print(f"   Points: {info['points_count']}, Status: {info['status']}")


def cmd_search(args):
    """测试检索"""
    pipeline = create_rag_pipeline(qdrant_url=args.qdrant_url)
    query = " ".join(args.query)

    if args.rag:
        # 完整 RAG (检索 + LLM 生成)
        print(f"🔍 RAG query: {query}")
        print("-" * 60)
        result = pipeline.query(query, doc_type=args.doc_type)
        print(f"\n💬 Answer:\n{result.answer}")
        print(f"\n📎 Sources ({len(result.sources)}):")
        for s in result.sources:
            print(f"   [{s['score']}] {s['source']} / {s.get('section', '')}")
        if result.llm_response:
            print(f"\n⚙️  Model: {result.llm_response.model}, "
                  f"Tokens: {result.llm_response.total_tokens}, "
                  f"Cost: ¥{result.llm_response.cost_yuan}")
    else:
        # 仅检索 (不调 LLM)
        print(f"🔍 Search only: {query}")
        print("-" * 60)
        results = pipeline.search_only(query, doc_type=args.doc_type, top_k=args.top_k)
        for i, r in enumerate(results):
            print(f"\n  [{i+1}] Score: {r['score']}  Source: {r['source']}")
            if r.get("section"):
                print(f"      Section: {r['section']}")
            print(f"      Type: {r['doc_type']}")
            print(f"      Text: {r['text'][:150]}...")


def cmd_stats(args):
    """查看知识库统计"""
    store = QdrantStore(base_url=args.qdrant_url)
    try:
        info = store.collection_info()
        print(f"📊 Collection: {info['name']}")
        print(f"   Points:  {info['points_count']}")
        print(f"   Vectors: {info['vectors_count']}")
        print(f"   Status:  {info['status']}")
    except Exception as e:
        print(f"❌ Cannot connect to Qdrant: {e}")
        print(f"   URL: {args.qdrant_url}")


def cmd_reset(args):
    """重置知识库"""
    store = QdrantStore(base_url=args.qdrant_url)
    confirm = input(f"⚠️  Delete collection '{store.collection}'? [y/N]: ")
    if confirm.lower() == "y":
        store.delete_collection()
        print("✅ Collection deleted")
    else:
        print("Cancelled")


def main():
    parser = argparse.ArgumentParser(description="BHP Knowledge Base Manager")
    parser.add_argument(
        "--qdrant-url", default=os.environ.get("QDRANT_URL", "http://localhost:6333"),
        help="Qdrant server URL",
    )

    sub = parser.add_subparsers(dest="command")

    # load
    p_load = sub.add_parser("load", help="Load documents into knowledge base")
    p_load.add_argument("--file", help="Single file path")
    p_load.add_argument("--dir", help="Directory path")
    p_load.add_argument("--type", default="spec", help="Document type (spec/strategy/tcm/clinical/course/faq)")
    p_load.add_argument("--type-map", help='JSON map: {"filename": "doc_type"}')

    # search
    p_search = sub.add_parser("search", help="Search knowledge base")
    p_search.add_argument("query", nargs="+", help="Search query")
    p_search.add_argument("--doc-type", help="Filter by doc type")
    p_search.add_argument("--top-k", type=int, default=5, help="Number of results")
    p_search.add_argument("--rag", action="store_true", help="Use full RAG (search + LLM)")

    # stats
    sub.add_parser("stats", help="Show knowledge base statistics")

    # reset
    sub.add_parser("reset", help="Reset (delete) knowledge base")

    args = parser.parse_args()

    if args.command == "load":
        cmd_load(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "reset":
        cmd_reset(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
