"""
文件格式转换器
PDF/DOCX/TXT → Markdown

将不同格式的文件统一转换为 Markdown 文本，
复用现有 chunk_markdown() 进行分块。
"""
import os
from loguru import logger


def convert_pdf_to_markdown(file_path: str) -> str:
    """PDF → Markdown"""
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(f"## 第 {i + 1} 页\n\n{text.strip()}")
        return "\n\n".join(pages)
    except ImportError:
        logger.warning("pypdf 未安装，PDF 转换不可用")
        raise
    except Exception as e:
        logger.error(f"PDF 转换失败 {file_path}: {e}")
        raise


def convert_docx_to_markdown(file_path: str) -> str:
    """DOCX → Markdown"""
    try:
        from docx import Document
        doc = Document(file_path)
        lines = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            style = para.style.name.lower() if para.style else ""
            if "heading 1" in style:
                lines.append(f"# {text}")
            elif "heading 2" in style:
                lines.append(f"## {text}")
            elif "heading 3" in style:
                lines.append(f"### {text}")
            elif "heading" in style:
                lines.append(f"#### {text}")
            elif "list" in style:
                lines.append(f"- {text}")
            else:
                lines.append(text)
            lines.append("")  # blank line between paragraphs
        return "\n".join(lines)
    except ImportError:
        logger.warning("python-docx 未安装，DOCX 转换不可用")
        raise
    except Exception as e:
        logger.error(f"DOCX 转换失败 {file_path}: {e}")
        raise


def convert_txt_to_markdown(file_path: str) -> str:
    """TXT → Markdown (直接读取)"""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        logger.error(f"TXT 读取失败 {file_path}: {e}")
        raise


def convert_md_to_markdown(file_path: str) -> str:
    """Markdown 直接读取"""
    return convert_txt_to_markdown(file_path)


# 格式 → 转换函数映射
CONVERTERS = {
    ".pdf": convert_pdf_to_markdown,
    ".docx": convert_docx_to_markdown,
    ".txt": convert_txt_to_markdown,
    ".md": convert_md_to_markdown,
}

# 支持的文件扩展名
SUPPORTED_EXTENSIONS = set(CONVERTERS.keys())


def convert_file_to_markdown(file_path: str) -> str:
    """
    根据文件扩展名自动选择转换器

    Args:
        file_path: 文件路径

    Returns:
        Markdown 文本

    Raises:
        ValueError: 不支持的文件格式
    """
    ext = os.path.splitext(file_path)[1].lower()
    converter = CONVERTERS.get(ext)
    if not converter:
        raise ValueError(f"不支持的文件格式: {ext}，支持: {', '.join(SUPPORTED_EXTENSIONS)}")
    return converter(file_path)
