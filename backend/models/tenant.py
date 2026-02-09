"""
Bridge: models.tenant → core.models (Tenant* 模型)

  from models.tenant import ExpertTenant, TenantClient, ...
"""
import sys, os

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from core.models import (
    ExpertTenant,
    TenantClient,
    TenantAgentMapping,
    TenantAuditLog,
)

__all__ = [
    "ExpertTenant",
    "TenantClient",
    "TenantAgentMapping",
    "TenantAuditLog",
]
