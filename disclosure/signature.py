"""
行为健康数字平台 - 披露控制：双重签名机制
Disclosure Control: Dual Signature System

[v14-NEW] 披露控制模块

高风险报告必须经过双重签名确认：
1. 第一负责人（主审专家）签名
2. 第二负责人（督导专家）签名

签名规则：
- CRITICAL 风险：必须双重签名
- HIGH 风险：必须双重签名
- MODERATE 风险：单签名即可
- LOW 风险：可自动批准
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger
import hashlib
import json


class SignatureRole(str, Enum):
    """签名角色"""
    PRIMARY = "primary"        # 第一负责人（主审专家）
    SECONDARY = "secondary"    # 第二负责人（督导专家）
    SYSTEM = "system"          # 系统自动


class SignatureStatus(str, Enum):
    """签名状态"""
    PENDING = "pending"          # 待签名
    SIGNED = "signed"            # 已签名
    REJECTED = "rejected"        # 已驳回
    EXPIRED = "expired"          # 已过期


class RiskLevel(str, Enum):
    """风险等级"""
    CRITICAL = "critical"    # 危急 - 必须双签
    HIGH = "high"            # 高风险 - 必须双签
    MODERATE = "moderate"    # 中风险 - 单签
    LOW = "low"              # 低风险 - 可自动


@dataclass
class Signature:
    """签名记录"""
    role: SignatureRole
    signer_id: str
    signer_name: str
    status: SignatureStatus = SignatureStatus.PENDING
    signed_at: Optional[datetime] = None
    comment: Optional[str] = None
    ip_address: Optional[str] = None
    
    # 签名哈希（防篡改）
    signature_hash: Optional[str] = None
    
    def sign(self, content_hash: str, comment: Optional[str] = None):
        """执行签名"""
        self.status = SignatureStatus.SIGNED
        self.signed_at = datetime.now()
        self.comment = comment
        
        # 生成签名哈希
        sign_data = f"{self.signer_id}:{content_hash}:{self.signed_at.isoformat()}"
        self.signature_hash = hashlib.sha256(sign_data.encode()).hexdigest()[:16]
        
        logger.info(f"[Disclosure] 签名完成: {self.role.value} by {self.signer_name}")
    
    def reject(self, reason: str):
        """驳回"""
        self.status = SignatureStatus.REJECTED
        self.signed_at = datetime.now()
        self.comment = reason
        
        logger.warning(f"[Disclosure] 签名驳回: {self.role.value} by {self.signer_name}: {reason}")
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role.value,
            "signer_id": self.signer_id,
            "signer_name": self.signer_name,
            "status": self.status.value,
            "signed_at": self.signed_at.isoformat() if self.signed_at else None,
            "comment": self.comment,
            "signature_hash": self.signature_hash
        }


@dataclass
class DualSignatureRequest:
    """双重签名请求"""
    request_id: str
    report_id: str
    user_id: int
    risk_level: RiskLevel
    
    # 签名
    primary_signature: Optional[Signature] = None
    secondary_signature: Optional[Signature] = None
    
    # 内容哈希（确保签名内容不变）
    content_hash: str = ""
    
    # 状态
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 披露内容摘要
    disclosure_summary: Optional[str] = None
    
    @property
    def requires_dual_signature(self) -> bool:
        """是否需要双重签名"""
        return self.risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH)
    
    @property
    def is_complete(self) -> bool:
        """签名是否完成"""
        if not self.requires_dual_signature:
            # 单签名场景
            return (self.primary_signature and 
                    self.primary_signature.status == SignatureStatus.SIGNED)
        
        # 双签名场景
        return (
            self.primary_signature and 
            self.primary_signature.status == SignatureStatus.SIGNED and
            self.secondary_signature and 
            self.secondary_signature.status == SignatureStatus.SIGNED
        )
    
    @property
    def is_rejected(self) -> bool:
        """是否被驳回"""
        if self.primary_signature and self.primary_signature.status == SignatureStatus.REJECTED:
            return True
        if self.secondary_signature and self.secondary_signature.status == SignatureStatus.REJECTED:
            return True
        return False
    
    @property
    def pending_role(self) -> Optional[SignatureRole]:
        """当前待签名角色"""
        if not self.primary_signature or self.primary_signature.status == SignatureStatus.PENDING:
            return SignatureRole.PRIMARY
        
        if self.requires_dual_signature:
            if not self.secondary_signature or self.secondary_signature.status == SignatureStatus.PENDING:
                return SignatureRole.SECONDARY
        
        return None
    
    def to_dict(self) -> Dict:
        return {
            "request_id": self.request_id,
            "report_id": self.report_id,
            "user_id": self.user_id,
            "risk_level": self.risk_level.value,
            "requires_dual_signature": self.requires_dual_signature,
            "is_complete": self.is_complete,
            "is_rejected": self.is_rejected,
            "pending_role": self.pending_role.value if self.pending_role else None,
            "primary_signature": self.primary_signature.to_dict() if self.primary_signature else None,
            "secondary_signature": self.secondary_signature.to_dict() if self.secondary_signature else None,
            "content_hash": self.content_hash,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class DualSignatureManager:
    """
    双重签名管理器
    
    管理披露报告的签名流程
    """
    
    def __init__(self):
        self._requests: Dict[str, DualSignatureRequest] = {}
        self._counter = 0
        logger.info("[Disclosure] 双重签名管理器初始化")
    
    def create_request(
        self,
        report_id: str,
        user_id: int,
        risk_level: RiskLevel,
        content: str,
        disclosure_summary: Optional[str] = None
    ) -> DualSignatureRequest:
        """
        创建签名请求
        
        Args:
            report_id: 报告ID
            user_id: 用户ID
            risk_level: 风险等级
            content: 待签名内容
            disclosure_summary: 披露摘要
        
        Returns:
            DualSignatureRequest
        """
        self._counter += 1
        request_id = f"sig_{report_id}_{self._counter}"
        
        # 计算内容哈希
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        request = DualSignatureRequest(
            request_id=request_id,
            report_id=report_id,
            user_id=user_id,
            risk_level=risk_level,
            content_hash=content_hash,
            disclosure_summary=disclosure_summary
        )
        
        # 初始化签名槽
        request.primary_signature = Signature(
            role=SignatureRole.PRIMARY,
            signer_id="",
            signer_name=""
        )
        
        if request.requires_dual_signature:
            request.secondary_signature = Signature(
                role=SignatureRole.SECONDARY,
                signer_id="",
                signer_name=""
            )
        
        self._requests[request_id] = request
        
        logger.info(f"[Disclosure] 创建签名请求: {request_id} risk={risk_level.value} "
                   f"dual={request.requires_dual_signature}")
        
        return request
    
    def sign(
        self,
        request_id: str,
        signer_id: str,
        signer_name: str,
        role: SignatureRole,
        comment: Optional[str] = None
    ) -> DualSignatureRequest:
        """
        执行签名
        
        Args:
            request_id: 请求ID
            signer_id: 签名人ID
            signer_name: 签名人姓名
            role: 签名角色
            comment: 备注
        
        Returns:
            更新后的请求
        """
        request = self._requests.get(request_id)
        if not request:
            raise ValueError(f"签名请求不存在: {request_id}")
        
        if request.is_complete:
            raise ValueError("签名已完成，无法重复签名")
        
        if request.is_rejected:
            raise ValueError("签名已被驳回")
        
        # 检查签名顺序
        if role == SignatureRole.SECONDARY and request.pending_role == SignatureRole.PRIMARY:
            raise ValueError("请先完成第一负责人签名")
        
        # 执行签名
        signature = None
        if role == SignatureRole.PRIMARY:
            signature = request.primary_signature
        elif role == SignatureRole.SECONDARY:
            signature = request.secondary_signature
        
        if not signature:
            raise ValueError(f"无效的签名角色: {role}")
        
        signature.signer_id = signer_id
        signature.signer_name = signer_name
        signature.sign(request.content_hash, comment)
        
        # 检查是否完成
        if request.is_complete:
            request.completed_at = datetime.now()
            logger.info(f"[Disclosure] 签名完成: {request_id}")
        
        return request
    
    def reject(
        self,
        request_id: str,
        signer_id: str,
        signer_name: str,
        role: SignatureRole,
        reason: str
    ) -> DualSignatureRequest:
        """
        驳回签名
        
        Args:
            request_id: 请求ID
            signer_id: 驳回人ID
            signer_name: 驳回人姓名
            role: 驳回角色
            reason: 驳回原因
        
        Returns:
            更新后的请求
        """
        request = self._requests.get(request_id)
        if not request:
            raise ValueError(f"签名请求不存在: {request_id}")
        
        signature = None
        if role == SignatureRole.PRIMARY:
            signature = request.primary_signature
        elif role == SignatureRole.SECONDARY:
            signature = request.secondary_signature
        
        if not signature:
            raise ValueError(f"无效的签名角色: {role}")
        
        signature.signer_id = signer_id
        signature.signer_name = signer_name
        signature.reject(reason)
        
        return request
    
    def get_request(self, request_id: str) -> Optional[DualSignatureRequest]:
        """获取签名请求"""
        return self._requests.get(request_id)
    
    def get_pending_requests(self, role: Optional[SignatureRole] = None) -> List[DualSignatureRequest]:
        """获取待签名请求"""
        requests = [r for r in self._requests.values() 
                   if not r.is_complete and not r.is_rejected]
        
        if role:
            requests = [r for r in requests if r.pending_role == role]
        
        return requests
    
    def can_disclose(self, request_id: str) -> bool:
        """检查是否可以披露"""
        request = self._requests.get(request_id)
        if not request:
            return False
        return request.is_complete


# ============================================
# 签名规则配置
# ============================================

SIGNATURE_RULES = {
    RiskLevel.CRITICAL: {
        "requires_dual": True,
        "timeout_hours": 24,
        "notify_supervisor": True,
        "description": "危急风险，必须双重签名，24小时内处理"
    },
    RiskLevel.HIGH: {
        "requires_dual": True,
        "timeout_hours": 48,
        "notify_supervisor": True,
        "description": "高风险，必须双重签名，48小时内处理"
    },
    RiskLevel.MODERATE: {
        "requires_dual": False,
        "timeout_hours": 72,
        "notify_supervisor": False,
        "description": "中风险，单签名即可，72小时内处理"
    },
    RiskLevel.LOW: {
        "requires_dual": False,
        "timeout_hours": None,
        "notify_supervisor": False,
        "auto_approve": True,
        "description": "低风险，可自动批准"
    }
}


def get_signature_rule(risk_level: RiskLevel) -> Dict:
    """获取签名规则"""
    return SIGNATURE_RULES.get(risk_level, SIGNATURE_RULES[RiskLevel.MODERATE])


# ============================================
# 全局单例
# ============================================

_signature_manager: Optional[DualSignatureManager] = None


def get_signature_manager() -> DualSignatureManager:
    """获取签名管理器"""
    global _signature_manager
    if _signature_manager is None:
        _signature_manager = DualSignatureManager()
    return _signature_manager
