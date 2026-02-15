"""
V4.1 数据脱敏管道 — 跨层数据传输时的字段级脱敏

基于实际数据库PII字段分布:
  users: email, phone, password_hash
  user_sessions: token, refresh_token, ip_address
  user_devices: auth_token
  ethical_declarations: ip_address

脱敏规则 (Sheet⑫ 数据隔离边界):
  Level 0 (完全脱敏): password_hash, token, refresh_token, auth_token → 永远不跨层
  Level 1 (部分脱敏): email, phone, ip_address → 教练可见掩码版
  Level 2 (聚合脱敏): 评估原始答题 → 教练只见统计摘要
  Level 3 (对话脱敏): 对话日志 → 教练可见但去除PII
"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from copy import deepcopy


# ═══════════════════════════════════════════════════════════
# 脱敏规则配置
# ═══════════════════════════════════════════════════════════

# Level 0: 永远不跨层的字段（直接删除）
BLACKLIST_FIELDS = {
    "password_hash", "password", "pwd",
    "token", "access_token", "refresh_token", "auth_token",
    "secret", "api_key", "private_key",
}

# Level 1: 部分脱敏（掩码）
MASK_FIELDS = {
    "email": "_mask_email",
    "phone": "_mask_phone",
    "mobile": "_mask_phone",
    "ip_address": "_mask_ip",
    "id_card": "_mask_id_card",
    "address": "_mask_address",
}

# Level 2: 聚合脱敏的字段（原始数据→统计摘要）
AGGREGATE_FIELDS = {
    "raw_assessment_answers",
    "psychological_raw",
    "therapy_notes_raw",
    "raw_responses",
    "answer_details",
}

# PII正则模式（用于对话日志中的PII检测）
PII_PATTERNS = [
    (r'(?<!\d)1[3-9]\d{9}(?!\d)', '[手机号已脱敏]'),       # 手机号（不依赖\b）
    (r'(?<!\d)\d{17}[\dXx](?!\d)', '[身份证已脱敏]'),       # 身份证
    (r'[\w.-]+@[\w.-]+\.\w+', '[邮箱已脱敏]'),             # 邮箱
    (r'(?<!\d)\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?!\d)', '[IP已脱敏]'),  # IP
    (r'(?:密码|口令|password)\s*[:=：]\s*\S+', '[密码已脱敏]'),   # 密码明文
]


# ═══════════════════════════════════════════════════════════
# 掩码函数
# ═══════════════════════════════════════════════════════════

def _mask_email(email: str) -> str:
    """user@example.com → u***@example.com"""
    if not email or '@' not in email:
        return '[邮箱已脱敏]'
    local, domain = email.rsplit('@', 1)
    masked = local[0] + '***' if local else '***'
    return f"{masked}@{domain}"


def _mask_phone(phone: str) -> str:
    """13812345678 → 138****5678"""
    phone = str(phone).strip()
    if len(phone) >= 11:
        return phone[:3] + '****' + phone[-4:]
    return '[手机号已脱敏]'


def _mask_ip(ip: str) -> str:
    """192.168.1.100 → 192.168.*.*"""
    parts = str(ip).split('.')
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.*.*"
    return '[IP已脱敏]'


def _mask_id_card(id_card: str) -> str:
    """110101199001011234 → 1101***********1234"""
    s = str(id_card)
    if len(s) >= 18:
        return s[:4] + '***********' + s[-4:]
    return '[证件号已脱敏]'


def _mask_address(address: str) -> str:
    """北京市朝阳区xxx路xxx号 → 北京市朝阳区****"""
    s = str(address)
    if len(s) > 6:
        return s[:6] + '****'
    return '[地址已脱敏]'


MASK_FUNCS = {
    "_mask_email": _mask_email,
    "_mask_phone": _mask_phone,
    "_mask_ip": _mask_ip,
    "_mask_id_card": _mask_id_card,
    "_mask_address": _mask_address,
}


# ═══════════════════════════════════════════════════════════
# 核心脱敏器
# ═══════════════════════════════════════════════════════════

class DataSanitizer:
    """
    跨层数据脱敏器

    用法:
        sanitizer = DataSanitizer(viewer_role="coach")
        safe_data = sanitizer.sanitize(raw_user_data)
        redacted_fields = sanitizer.get_redacted_fields()
    """

    def __init__(self, viewer_role: str = "coach"):
        self.viewer_role = viewer_role
        self._redacted_fields: List[str] = []

    def sanitize(self, data: Any, field_name: str = "") -> Any:
        """递归脱敏数据结构"""
        if data is None:
            return None

        if isinstance(data, dict):
            return self._sanitize_dict(data)
        elif isinstance(data, list):
            return [self.sanitize(item) for item in data]
        elif isinstance(data, str) and field_name:
            return self._sanitize_field(field_name, data)
        return data

    def _sanitize_dict(self, d: Dict[str, Any]) -> Dict[str, Any]:
        result = {}
        for key, value in d.items():
            key_lower = key.lower()

            # Level 0: 黑名单字段 → 删除
            if key_lower in BLACKLIST_FIELDS:
                self._redacted_fields.append(key)
                continue  # 完全不输出

            # Level 2: 聚合脱敏
            if key_lower in AGGREGATE_FIELDS:
                self._redacted_fields.append(key)
                result[key + "_summary"] = self._aggregate(value)
                continue

            # Level 1: 掩码脱敏
            if key_lower in MASK_FIELDS:
                mask_func_name = MASK_FIELDS[key_lower]
                mask_func = MASK_FUNCS[mask_func_name]
                if isinstance(value, str):
                    self._redacted_fields.append(key)
                    result[key] = mask_func(value)
                    continue

            # 递归处理嵌套
            if isinstance(value, dict):
                result[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                result[key] = [self.sanitize(item) for item in value]
            elif isinstance(value, str):
                result[key] = self._sanitize_text(value, key)
            elif isinstance(value, (int, float, bool)):
                result[key] = value
            else:
                result[key] = value

        return result

    def _sanitize_field(self, field_name: str, value: str) -> str:
        """对单个字段值脱敏"""
        fl = field_name.lower()
        if fl in BLACKLIST_FIELDS:
            return "[已脱敏]"
        if fl in MASK_FIELDS:
            func = MASK_FUNCS[MASK_FIELDS[fl]]
            return func(value)
        return self._sanitize_text(value, field_name)

    def _sanitize_text(self, text: str, field_name: str = "") -> str:
        """Level 3: 文本中的PII检测和替换"""
        # 对话日志类字段做PII扫描
        if any(kw in field_name.lower() for kw in
               ["message", "content", "text", "note", "log", "chat", "reply"]):
            for pattern, replacement in PII_PATTERNS:
                if re.search(pattern, text):
                    self._redacted_fields.append(f"{field_name}:pii_redacted")
                    text = re.sub(pattern, replacement, text)
        return text

    def _aggregate(self, raw_data: Any) -> Dict[str, Any]:
        """Level 2: 原始数据→聚合统计"""
        if isinstance(raw_data, list):
            return {
                "total_items": len(raw_data),
                "data_type": "aggregated",
                "note": "原始数据已脱敏，仅显示统计摘要",
            }
        elif isinstance(raw_data, dict):
            return {
                "total_fields": len(raw_data),
                "keys": list(raw_data.keys())[:10],
                "data_type": "aggregated",
                "note": "原始数据已脱敏，仅显示字段列表",
            }
        return {"data_type": "aggregated", "note": "已脱敏"}

    def get_redacted_fields(self) -> List[str]:
        """返回被脱敏的字段列表（用于审计日志）"""
        return list(set(self._redacted_fields))

    def reset(self):
        self._redacted_fields = []


# ═══════════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════════

def sanitize_for_coach(data: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
    """教练视角脱敏 — 返回 (脱敏数据, 被脱敏字段列表)"""
    s = DataSanitizer(viewer_role="coach")
    result = s.sanitize(data)
    return result, s.get_redacted_fields()


def sanitize_for_supervisor(data: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
    """督导视角脱敏 — 同教练（督导不应看到更多PII）"""
    return sanitize_for_coach(data)


def sanitize_for_admin(data: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
    """Admin视角 — 仅删除密码/token，保留其他"""
    s = DataSanitizer(viewer_role="admin")
    result = {}
    redacted = []
    for key, value in data.items():
        if key.lower() in BLACKLIST_FIELDS:
            redacted.append(key)
            continue
        result[key] = value
    return result, redacted


# ═══════════════════════════════════════════════════════════
# 测试用例
# ═══════════════════════════════════════════════════════════

def _self_test():
    """运行自测"""
    test_data = {
        "id": "abc-123",
        "username": "张三",
        "email": "zhangsan@example.com",
        "phone": "13812345678",
        "password_hash": "$2b$12$xxx",
        "ip_address": "192.168.1.100",
        "token": "eyJhbGc...",
        "role": "grower",
        "behavioral_profile": {
            "agency_mode": "active",
            "trust_score": 0.72,
        },
        "raw_assessment_answers": [
            {"q": 1, "a": 3}, {"q": 2, "a": 5}
        ],
        "chat_history": [
            {"content": "我的手机号是13912345678，帮我查一下"},
            {"content": "正常对话内容"},
        ],
    }

    result, fields = sanitize_for_coach(test_data)

    print("原始字段:", list(test_data.keys()))
    print("脱敏字段:", fields)
    print()
    print("脱敏结果:")
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

    # 验证
    assert "password_hash" not in result, "密码应被删除"
    assert "token" not in result, "token应被删除"
    assert result["email"] == "z***@example.com", f"邮箱脱敏错误: {result['email']}"
    assert result["phone"] == "138****5678", f"手机脱敏错误: {result['phone']}"
    assert "raw_assessment_answers_summary" in result, "评估应被聚合"
    assert "raw_assessment_answers" not in result, "评估原始数据应删除"

    # 对话中的PII
    chat = result.get("chat_history", [])
    if chat:
        assert "13912345678" not in str(chat), "对话中的手机号应被脱敏"

    print("\n✅ 所有脱敏测试通过")


if __name__ == "__main__":
    _self_test()
