"""
F-002: Contract Types Schema — 契约类型枚举与验证

Source: 契约注册表 ②③④ 各角色契约 Sheet
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ContractType(str, Enum):
    """契约类型"""
    observer_free = "observer_free"          # 免注册观察者协议
    observer_registered = "observer_reg"     # 注册观察者协议
    grower = "grower"                        # 成长者契约
    sharer = "sharer"                        # 分享者契约
    coach_l3 = "coach_l3"                    # 教练 L3 契约
    coach_l4 = "coach_l4"                    # 教练 L4 契约
    promoter = "promoter"                    # 推广者契约
    supervisor = "supervisor"                # 督导契约
    master = "master"                        # 大师契约
    renewal = "renewal"                      # 续期契约


class ContractStatus(str, Enum):
    active = "active"
    expired = "expired"
    revoked = "revoked"
    renewed = "renewed"


class EthicalClause(BaseModel):
    """伦理声明条款"""
    clause_id: str
    text_zh: str
    category: str  # boundary / disclosure / competency / emergency / supervision


COACH_5_CLAUSES: List[EthicalClause] = [
    EthicalClause(clause_id="C1", text_zh="我承诺不提供医疗诊断或处方建议", category="boundary"),
    EthicalClause(clause_id="C2", text_zh="我承诺保护学员隐私，不泄露个人健康数据", category="disclosure"),
    EthicalClause(clause_id="C3", text_zh="我承诺在能力范围内提供指导，超出时主动转介", category="competency"),
    EthicalClause(clause_id="C4", text_zh="我承诺在发现危机风险(R3+)时立即上报", category="emergency"),
    EthicalClause(clause_id="C5", text_zh="我承诺接受平台定期督导并配合质量审计", category="supervision"),
]

PROMOTER_7_CLAUSES: List[EthicalClause] = COACH_5_CLAUSES + [
    EthicalClause(clause_id="P6", text_zh="我承诺不以虚假案例或夸大效果进行推广", category="boundary"),
    EthicalClause(clause_id="P7", text_zh="我承诺对所辖教练的伦理行为承担连带督导责任", category="supervision"),
]


class ContractDefinition(BaseModel):
    """契约完整定义"""
    contract_type: ContractType
    role_required: str
    level_required: int = 0
    duration_days: Optional[int] = None  # None = permanent
    requires_ethical: bool = False
    ethical_type: Optional[str] = None
    renewal_allowed: bool = True
    key_obligations: List[str] = []
