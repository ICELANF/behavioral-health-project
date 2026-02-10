"""
干预策略矩阵引擎 — 根据阶段+动因匹配 coach 话术
放置: api/core/intervention_strategy_engine.py
"""
from sqlalchemy.orm import Session

from core.stage_mapping import S_TO_P_MAP, stage_resolver


class InterventionStrategyEngine:
    """
    输入: user.current_stage (S0-S6) + user.change_cause_scores
    输出: 排序的干预策略列表 (最多 3 条)
    """

    def __init__(self, db: Session):
        self.db = db

    def match(
        self,
        current_stage: str,
        cause_scores: dict[str, int],
        *,
        top_n: int = 3,
        use_readiness: bool = True,
        readiness_level: str | None = None,
    ) -> list[dict]:
        """
        算法:
        1. 若 use_readiness=True 且有 readiness_level → 用 L 查询
           否则 S→P → 用 P 查询 (兼容)
        2. 取 top_n 得分最高的 cause
        3. 查 intervention_strategies 表
        """
        from models_v3 import InterventionStrategy  # 避免循环导入

        sorted_causes = sorted(cause_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        top_codes = [c[0] for c in sorted_causes]

        if use_readiness and readiness_level:
            strategies = (
                self.db.query(InterventionStrategy)
                .filter(
                    InterventionStrategy.readiness_level == readiness_level,
                    InterventionStrategy.cause_code.in_(top_codes),
                )
                .all()
            )
        else:
            p_stage = S_TO_P_MAP.get(current_stage, "P0")
            strategies = (
                self.db.query(InterventionStrategy)
                .filter(
                    InterventionStrategy.stage_code == p_stage,
                    InterventionStrategy.cause_code.in_(top_codes),
                )
                .all()
            )

        result = sorted(
            strategies,
            key=lambda s: cause_scores.get(s.cause_code, 0),
            reverse=True,
        )

        return [
            {
                "strategy_type": s.strategy_type,
                "coach_script": s.coach_script,
                "cause_code": s.cause_code,
                "cause_name": s.cause_name,
                "readiness_level": s.readiness_level,
            }
            for s in result
        ]
