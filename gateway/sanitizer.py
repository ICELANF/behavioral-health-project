"""
数据脱敏管道 — 跨层数据传输时的字段级脱敏

规则 (Sheet⑫ 数据隔离边界):
  - 心理评估原始数据: 教练只能看聚合统计，不能看原始答题
  - 对话日志: 教练可看，但脱敏敏感关键词
  - 行为处方: 制定教练可看完整版，其他教练看摘要版
"""
from typing import Any, Dict
import re


# 敏感关键词（脱敏为 [***]）
SENSITIVE_PATTERNS = [
    r"\b\d{11}\b",          # 手机号
    r"\b\d{17}[\dXx]\b",   # 身份证
    r"[\w.-]+@[\w.-]+",    # 邮箱
    r"(?:密码|password)\s*[:=]\s*\S+",  # 密码
]


def sanitize_for_coach(data: Dict[str, Any]) -> Dict[str, Any]:
    """教练视角脱敏"""
    result = {}
    for key, value in data.items():
        if key in ("raw_assessment_answers", "psychological_raw", "therapy_notes_raw"):
            # 原始评估数据 → 聚合统计
            result[key + "_summary"] = _aggregate(value)
        elif isinstance(value, str):
            result[key] = _redact_pii(value)
        else:
            result[key] = value
    return result


def _redact_pii(text: str) -> str:
    """去除PII"""
    for pattern in SENSITIVE_PATTERNS:
        text = re.sub(pattern, "[***]", text)
    return text


def _aggregate(raw_data) -> dict:
    """原始数据→聚合统计"""
    if isinstance(raw_data, list):
        return {
            "total_items": len(raw_data),
            "summary": "已脱敏，仅显示聚合统计",
        }
    return {"summary": "已脱敏"}
