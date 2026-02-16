"""
C3 修复: Stage/阶段逻辑主从治理
冲突: 4处实现 — stage_engine, stage_mapping, stage_runtime, octopus_fsm
策略: stage_engine.py 为权威判定, 其余通过代理调用

文件:
  core/stage_engine.py — 标记为权威源(已存在, 加注释)
  core/stage_authority.py — 新建, 统一调用入口
  core/stage_mapping.py — 改为调用代理
  core/brain/stage_runtime.py — 改为调用代理
  agents/octopus_fsm.py — 改为调用代理
"""


# ═══════════════════════════════════════════════════════
# 新建: core/stage_authority.py — 统一入口
# ═══════════════════════════════════════════════════════

"""
core/stage_authority.py
C3 治理: 阶段逻辑统一入口

所有需要判定/流转阶段的模块统一通过此模块调用,
内部委托给 stage_engine.py (权威源)

禁止直接调用:
  - core/brain/stage_runtime.py (已降级为内部辅助)
  - agents/octopus_fsm.py (已降级为FSM状态展示)
"""

from typing import Optional
from datetime import datetime


class StageAuthority:
    """
    C3: 阶段权威判定统一入口

    架构层级:
    ┌─────────────────────────┐
    │   StageAuthority        │  ← 外部统一入口
    │   (core/stage_authority) │
    └────────┬────────────────┘
             │ 委托
    ┌────────▼────────────────┐
    │   StageEngine           │  ← 权威判定(SOURCE OF TRUTH)
    │   (core/stage_engine)   │
    └────────┬────────────────┘
             │ 辅助
    ┌────────▼────────────────┐
    │   stage_mapping         │  ← 辅助映射(只读)
    │   stage_runtime         │  ← 运行时缓存(只读)
    │   octopus_fsm           │  ← FSM展示层(只读)
    └─────────────────────────┘
    """

    def __init__(self, db):
        self.db = db
        # 延迟导入避免循环依赖
        self._engine = None

    @property
    def engine(self):
        if self._engine is None:
            from core.stage_engine import StageEngine
            self._engine = StageEngine(self.db)
        return self._engine

    def get_current_stage(self, user_id: int) -> Optional[str]:
        """获取用户当前阶段 (S0-S5) — 委托 stage_engine"""
        return self.engine.get_current_stage(user_id)

    def evaluate_transition(self, user_id: int) -> dict:
        """评估阶段流转条件 — 委托 stage_engine"""
        return self.engine.evaluate_transition(user_id)

    def execute_transition(
        self, user_id: int, target_stage: str, reason: str = ""
    ) -> dict:
        """执行阶段流转 — 委托 stage_engine + 同步缓存"""
        result = self.engine.execute_transition(
            user_id, target_stage, reason
        )
        # C4联动: 同步User缓存
        from core.field_sync_guard import FieldSyncGuard
        guard = FieldSyncGuard(self.db)
        guard.sync_user_cache(user_id)
        return result

    def check_90day_stability(self, user_id: int) -> dict:
        """90天稳定验证 — 委托 stage_engine"""
        return self.engine.check_stability(user_id)

    def get_stage_mapping(self, stage: str) -> dict:
        """获取阶段配置映射(权益/限制) — 委托 stage_mapping"""
        from core.stage_mapping import get_stage_config
        return get_stage_config(stage)


# ═══════════════════════════════════════════════════════
# PATCH: core/stage_engine.py 头部注释
# ═══════════════════════════════════════════════════════

STAGE_ENGINE_HEADER = '''
"""
core/stage_engine.py
═══════════════════════════════════════════════════
C3 权威源: S0-S5 阶段判定与流转引擎

⚠️ 这是阶段逻辑的 SOURCE OF TRUTH
  所有阶段判定、流转、验证必须通过此模块
  外部调用请使用 StageAuthority (core/stage_authority.py)

相关模块(辅助, 非权威):
  - core/stage_mapping.py — 阶段配置映射(只读辅助)
  - core/brain/stage_runtime.py — 运行时阶段缓存(只读)
  - agents/octopus_fsm.py — FSM状态展示层(只读)
═══════════════════════════════════════════════════
"""
'''


# ═══════════════════════════════════════════════════════
# PATCH: core/brain/stage_runtime.py — 降级为代理
# ═══════════════════════════════════════════════════════

STAGE_RUNTIME_PATCH = '''
"""
core/brain/stage_runtime.py
═══════════════════════════════════════════════════
C3 降级: 运行时阶段缓存 (DELEGATE → stage_engine)

⚠️ 此模块不再独立判定阶段
  所有判定逻辑已委托给 core/stage_engine.py
  本模块仅保留: 运行时缓存读取 + 性能优化
═══════════════════════════════════════════════════
"""

# 原有的独立判定方法改为代理:
def get_stage(self, user_id: int) -> str:
    """C3: 委托给权威源"""
    from core.stage_authority import StageAuthority
    authority = StageAuthority(self.db)
    return authority.get_current_stage(user_id)

# ⚠️ 以下方法已废弃, 保留兼容性但标记deprecated
# def _compute_stage(self, ...) → 使用 stage_engine.evaluate_transition
# def _transition(self, ...) → 使用 stage_engine.execute_transition
'''


# ═══════════════════════════════════════════════════════
# PATCH: core/stage_mapping.py — 标记为只读辅助
# ═══════════════════════════════════════════════════════

STAGE_MAPPING_PATCH = '''
"""
core/stage_mapping.py
═══════════════════════════════════════════════════
C3 辅助层: 阶段配置映射 (READ-ONLY)

⚠️ 此模块只提供阶段→配置的静态映射
  不包含任何判定或流转逻辑
  判定请使用 StageAuthority (core/stage_authority.py)
═══════════════════════════════════════════════════
"""
'''


# ═══════════════════════════════════════════════════════
# PATCH: agents/octopus_fsm.py — 标记为展示层
# ═══════════════════════════════════════════════════════

OCTOPUS_FSM_PATCH = '''
"""
agents/octopus_fsm.py
═══════════════════════════════════════════════════
C3 展示层: FSM 状态展示 (READ-ONLY, DELEGATE)

⚠️ 此模块仅用于 Agent 对话中展示阶段状态
  不执行阶段判定或流转
  阶段数据从 StageAuthority 获取
═══════════════════════════════════════════════════
"""

# 改为代理调用:
def get_user_stage_display(self, user_id: int) -> dict:
    """C3: 从权威源获取阶段, 仅用于展示"""
    from core.stage_authority import StageAuthority
    authority = StageAuthority(self.db)
    stage = authority.get_current_stage(user_id)
    mapping = authority.get_stage_mapping(stage)
    return {"stage": stage, "display": mapping}
'''
