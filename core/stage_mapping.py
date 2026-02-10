"""
统一阶段解析器 — 消除 P/S/L 三套编码歧义
放置: api/core/stage_mapping.py
"""

S_TO_L_FALLBACK: dict[str, str] = {
    "S0": "L1", "S1": "L1", "S2": "L2",
    "S3": "L3", "S4": "L4", "S5": "L4", "S6": "L5",
}

P_TO_S_MAP: dict[str, list[str]] = {
    "P0": ["S0"], "P1": ["S1"], "P2": ["S2"],
    "P3": ["S3"], "P4": ["S4"], "P5": ["S5", "S6"],
}

S_TO_P_MAP: dict[str, str] = {
    "S0": "P0", "S1": "P1", "S2": "P2",
    "S3": "P3", "S4": "P4", "S5": "P5", "S6": "P5",
}

P_TO_L_MAP: dict[str, str] = {
    "P0": "L1", "P1": "L1", "P2": "L2",
    "P3": "L3", "P4": "L4", "P5": "L5",
}

READINESS_DISPLAY_NAMES: dict[str, str] = {
    "L1": "完全对抗", "L2": "抗拒与反思", "L3": "妥协与接受",
    "L4": "顺应与调整", "L5": "全面臣服",
}


class UnifiedStageResolver:
    """
    统一阶段解析:
    - S 和 L 独立存储
    - 策略矩阵查询统一用 L 编码 (替代废弃的 P 编码)
    - 无 SPI 数据时从 S 降级推断 L
    """

    def resolve(
        self,
        behavioral_stage: str,
        readiness_level: str | None = None,
    ) -> dict:
        if readiness_level:
            strategy_key, source = readiness_level, "spi"
        else:
            strategy_key = S_TO_L_FALLBACK.get(behavioral_stage, "L1")
            source = "inferred"

        return {
            "behavioral_stage": behavioral_stage,
            "readiness_level": readiness_level or strategy_key,
            "readiness_source": source,
            "strategy_key": strategy_key,
            "display_label": READINESS_DISPLAY_NAMES.get(strategy_key, "未知"),
        }

    def s_to_p(self, s: str) -> str:
        """兼容旧逻辑: S→P"""
        return S_TO_P_MAP.get(s, "P0")

    def p_to_l(self, p: str) -> str:
        """P→L (迁移用)"""
        return P_TO_L_MAP.get(p, "L1")


# 单例
stage_resolver = UnifiedStageResolver()
