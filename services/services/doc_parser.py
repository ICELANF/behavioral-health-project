"""
文档解析器 — 将 Markdown / TXT 文件解析为结构化数据

提供:
  DocumentParser  — 解析入口
  ParsedDocument  — 解析后的文档
  ParsedSection   — 解析后的章节
"""
import hashlib
import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ParsedSection:
    """解析后的一个章节"""
    heading: str = ""
    level: int = 0
    content: str = ""


@dataclass
class ParsedDocument:
    """解析后的完整文档"""
    title: str = ""
    raw_text: str = ""
    sections: List[ParsedSection] = field(default_factory=list)
    file_type: str = ""
    file_hash: str = ""
    total_chars: int = 0


class DocumentParser:
    """文档解析器 — 支持 .md / .txt"""

    SUPPORTED = {".md", ".txt"}

    def parse(self, file_path: str) -> ParsedDocument:
        import os
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.SUPPORTED:
            raise ValueError(f"不支持的文件格式: {ext} (仅支持 {self.SUPPORTED})")

        with open(file_path, "r", encoding="utf-8") as f:
            raw = f.read()

        file_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        if ext == ".md":
            return self._parse_markdown(raw, file_path, file_hash)
        else:
            return self._parse_txt(raw, file_path, file_hash)

    def _parse_markdown(self, raw: str, path: str, file_hash: str) -> ParsedDocument:
        import os
        title = os.path.splitext(os.path.basename(path))[0]
        sections: List[ParsedSection] = []
        current_heading = ""
        current_level = 0
        buffer = ""

        for line in raw.split("\n"):
            m = re.match(r'^(#{1,6})\s+(.*)', line)
            if m:
                if buffer.strip():
                    sections.append(ParsedSection(
                        heading=current_heading,
                        level=current_level,
                        content=buffer.strip(),
                    ))
                    buffer = ""
                current_level = len(m.group(1))
                current_heading = m.group(2).strip()
                if not title or title == os.path.splitext(os.path.basename(path))[0]:
                    if current_level == 1 and not sections:
                        title = current_heading
            else:
                buffer += line + "\n"

        if buffer.strip():
            sections.append(ParsedSection(
                heading=current_heading,
                level=current_level,
                content=buffer.strip(),
            ))

        return ParsedDocument(
            title=title,
            raw_text=raw,
            sections=sections,
            file_type=".md",
            file_hash=file_hash,
            total_chars=len(raw),
        )

    def _parse_txt(self, raw: str, path: str, file_hash: str) -> ParsedDocument:
        import os
        title = os.path.splitext(os.path.basename(path))[0]
        sections = [ParsedSection(heading="", content=raw.strip())]
        return ParsedDocument(
            title=title,
            raw_text=raw,
            sections=sections,
            file_type=".txt",
            file_hash=file_hash,
            total_chars=len(raw),
        )


__all__ = ["DocumentParser", "ParsedDocument", "ParsedSection"]
