"""
BHP知识库向量化脚本
读取 bhp_vector_chunks JSON，调用 Ollama mxbai-embed-large 生成 1024 维向量，
输出带 embedding 的新 JSON 文件。

用法:
    python scripts/embed_chunks.py \
        --input knowledge/vector_chunks/bhp_vector_chunks_v1.3.json \
        --model mxbai-embed-large \
        --output knowledge/vector_chunks/bhp_vector_chunks_v1.3_1024d.json
"""
import argparse
import json
import sys
import time
import urllib.request
import urllib.error

OLLAMA_URL = "http://localhost:11434/api/embed"


def get_embedding(text: str, model: str, retries: int = 3) -> list[float]:
    # mxbai-embed-large context = 512 tokens; Chinese ≈ 1.5 tokens/char
    text = text[:340].replace("\x00", "")
    payload = json.dumps({"model": model, "input": text}, ensure_ascii=False).encode("utf-8")
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                OLLAMA_URL,
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            return result["embeddings"][0]
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            if attempt < retries - 1:
                try:
                    err_body = e.read().decode("utf-8", errors="replace")[:200]
                except Exception:
                    err_body = ""
                print(f"    Retry {attempt+1}/{retries}: {e} | {err_body}")
                time.sleep(3)
            else:
                raise


def main():
    parser = argparse.ArgumentParser(description="Embed BHP knowledge chunks via Ollama")
    parser.add_argument("--input", required=True, help="Input JSON file path")
    parser.add_argument("--model", default="mxbai-embed-large:latest", help="Ollama model name")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    chunks = data.get("chunks", data if isinstance(data, list) else [])
    total = len(chunks)
    print(f"Loaded {total} chunks from {args.input}")
    print(f"Model: {args.model}")

    # Verify model produces expected dimension
    test_emb = get_embedding("test", args.model)
    dim = len(test_emb)
    print(f"Verified embedding dimension: {dim}")
    if dim != 1024:
        print(f"WARNING: Expected 1024, got {dim}")
    time.sleep(1)  # Let Ollama cool down after test

    t0 = time.time()
    for i, chunk in enumerate(chunks):
        text = chunk.get("content", "")
        if not text.strip():
            chunk["embedding"] = [0.0] * dim
            continue
        # Prepend heading for better context
        heading = chunk.get("heading", "")
        embed_text = f"{heading}\n{text}" if heading else text
        chunk["embedding"] = get_embedding(embed_text, args.model)
        chunk["embedding_dim"] = dim
        chunk["embedding_model"] = args.model

        if (i + 1) % 10 == 0 or i == total - 1:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (total - i - 1) / rate if rate > 0 else 0
            print(f"  [{i+1}/{total}] {rate:.1f} chunks/s, ETA {eta:.0f}s")

    # Update metadata
    if isinstance(data, dict):
        data["embedding_model"] = args.model
        data["embedding_dim"] = dim
        data["chunks"] = chunks

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    elapsed = time.time() - t0
    print(f"\nDone! {total} chunks embedded in {elapsed:.1f}s")
    print(f"Output: {args.output}")
    # File size
    import os
    size_mb = os.path.getsize(args.output) / (1024 * 1024)
    print(f"File size: {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
