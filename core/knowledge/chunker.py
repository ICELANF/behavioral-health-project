"""
Markdown 分块策略

将 Markdown 文本切分为带标题的文本块，供嵌入和检索使用。
从 scripts/ingest_knowledge.py 提取为独立模块，便于 Docker 镜像内复用。
"""

import re
from typing import List, Dict


def chunk_markdown(text: str, max_chars: int = 800, overlap: int = 100) -> List[Dict[str, str]]:
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


def _split_long(text: str, max_chars: int, overlap: int) -> List[str]:
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
