"""Structured logging configuration using loguru"""
import os
import sys
import json
from loguru import logger


def setup_logging():
    """Configure production logging"""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_format = os.getenv("LOG_FORMAT", "text")  # text or json
    log_dir = os.getenv("LOG_DIR", "logs")

    # Remove default handler
    logger.remove()

    if log_format == "json":
        def json_formatter(record):
            log_record = {
                "timestamp": record["time"].isoformat(),
                "level": record["level"].name,
                "message": record["message"],
                "module": record["module"],
                "function": record["function"],
                "line": record["line"],
            }
            if record["exception"]:
                log_record["exception"] = str(record["exception"])
            record["extra"]["serialized"] = json.dumps(log_record, ensure_ascii=False)
            return "{extra[serialized]}\n"

        logger.add(sys.stderr, format=json_formatter, level=log_level)
    else:
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=log_level,
            colorize=True,
        )

    # File rotation
    os.makedirs(log_dir, exist_ok=True)
    logger.add(
        os.path.join(log_dir, "app_{time:YYYY-MM-DD}.log"),
        rotation="00:00",
        retention="30 days",
        compression="gz",
        level=log_level,
        encoding="utf-8",
    )

    # Error-only file
    logger.add(
        os.path.join(log_dir, "error_{time:YYYY-MM-DD}.log"),
        rotation="00:00",
        retention="90 days",
        compression="gz",
        level="ERROR",
        encoding="utf-8",
    )

    logger.info(f"Logging configured: level={log_level} format={log_format}")
