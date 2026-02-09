"""
压缩包解压器
支持 ZIP / 7Z / RAR 格式

解压到临时目录，筛选支持的文件格式并返回文件列表。
"""
import os
import tempfile
import zipfile
from typing import List, Tuple
from loguru import logger

from core.knowledge.file_converter import SUPPORTED_EXTENSIONS


def extract_archive(file_path: str) -> Tuple[str, List[str]]:
    """
    解压压缩包到临时目录

    Args:
        file_path: 压缩包路径

    Returns:
        (临时目录路径, 支持格式的文件路径列表)

    Raises:
        ValueError: 不支持的压缩格式
    """
    ext = os.path.splitext(file_path)[1].lower()
    tmp_dir = tempfile.mkdtemp(prefix="bhp_ingest_")

    try:
        if ext == ".zip":
            _extract_zip(file_path, tmp_dir)
        elif ext == ".7z":
            _extract_7z(file_path, tmp_dir)
        elif ext == ".rar":
            _extract_rar(file_path, tmp_dir)
        else:
            raise ValueError(f"不支持的压缩格式: {ext}")
    except Exception as e:
        logger.error(f"解压失败 {file_path}: {e}")
        raise

    # 扫描解压目录，筛选支持的文件
    supported_files = []
    for root, _dirs, files in os.walk(tmp_dir):
        for fname in files:
            if fname.startswith(".") or fname.startswith("__"):
                continue
            fext = os.path.splitext(fname)[1].lower()
            if fext in SUPPORTED_EXTENSIONS:
                supported_files.append(os.path.join(root, fname))

    logger.info(f"解压完成: {len(supported_files)} 个支持格式文件 (来自 {file_path})")
    return tmp_dir, supported_files


def _extract_zip(file_path: str, target_dir: str):
    """解压 ZIP"""
    with zipfile.ZipFile(file_path, "r") as zf:
        zf.extractall(target_dir)


def _extract_7z(file_path: str, target_dir: str):
    """解压 7Z"""
    try:
        import py7zr
        with py7zr.SevenZipFile(file_path, mode="r") as archive:
            archive.extractall(path=target_dir)
    except ImportError:
        logger.warning("py7zr 未安装，7z 解压不可用")
        raise ValueError("py7zr 未安装，无法解压 .7z 文件")


def _extract_rar(file_path: str, target_dir: str):
    """解压 RAR"""
    try:
        import rarfile
        with rarfile.RarFile(file_path) as rf:
            rf.extractall(target_dir)
    except ImportError:
        logger.warning("rarfile 未安装，RAR 解压不可用")
        raise ValueError("rarfile 未安装，无法解压 .rar 文件")


# 支持的压缩格式
ARCHIVE_EXTENSIONS = {".zip", ".7z", ".rar"}


def is_archive(file_path: str) -> bool:
    """判断文件是否是压缩包"""
    ext = os.path.splitext(file_path)[1].lower()
    return ext in ARCHIVE_EXTENSIONS
