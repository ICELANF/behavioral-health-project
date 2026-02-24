# -*- coding: utf-8 -*-
"""
supervisor_credential_service.py — 督导资质生命周期服务 (I-07)

提供:
- grant_credential()   — 授予资质 + 触发角色升级 + 写 RoleChangeLog
- review_credential()  — 年审续期 next_review_at
- revoke_credential()  — 吊销 + 若无其他有效资质则降级为 COACH
- check_expired_credentials() — 调度器调用: 自动过期 + 降级
"""
import json
import os
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from core.models import (
    SupervisorCredential, RoleChangeLog, User, UserRole, ROLE_LEVEL,
    Notification,
)

import logging
logger = logging.getLogger(__name__)

# 加载配置
_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "configs", "supervisor_credential_config.json",
)
try:
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        _CONFIG = json.load(f)
except Exception:
    _CONFIG = {"credential_types": {}}

_CREDENTIAL_TYPES = _CONFIG.get("credential_types", {})


class SupervisorCredentialService:

    def grant_credential(
        self,
        db: Session,
        user_id: int,
        credential_type: str,
        granted_by: int,
        credential_number: Optional[str] = None,
        issuing_authority: Optional[str] = None,
        issued_at: Optional[datetime] = None,
    ) -> dict:
        """授予资质 + 触发角色升级"""
        cfg = _CREDENTIAL_TYPES.get(credential_type)
        if not cfg:
            raise ValueError(f"未知资质类型: {credential_type}")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"用户不存在: {user_id}")

        review_days = cfg.get("review_interval_days", 365)
        now = datetime.utcnow()

        cred = SupervisorCredential(
            user_id=user_id,
            credential_type=credential_type,
            credential_number=credential_number,
            issuing_authority=issuing_authority,
            issued_at=issued_at or now,
            status="active",
            granted_by=granted_by,
            granted_at=now,
            last_review_at=now,
            next_review_at=now + timedelta(days=review_days),
        )
        db.add(cred)

        # 角色升级
        target_role_str = cfg.get("target_role", "coach")
        target_role = UserRole.SUPERVISOR if target_role_str == "supervisor" else UserRole.COACH
        target_level = ROLE_LEVEL.get(target_role, 4)
        user_level = ROLE_LEVEL.get(user.role, 0)

        role_changed = False
        if user_level < target_level:
            old_role = user.role.value if user.role else "observer"
            user.role = target_role
            role_changed = True
            db.add(RoleChangeLog(
                user_id=user_id,
                old_role=old_role,
                new_role=target_role.value,
                reason="credential_granted",
                changed_by=granted_by,
                detail={"credential_type": credential_type, "credential_id": cred.id},
            ))

        db.commit()
        db.refresh(cred)
        return {
            "credential_id": cred.id,
            "role_changed": role_changed,
            "new_role": user.role.value,
        }

    def review_credential(
        self,
        db: Session,
        credential_id: int,
        reviewer_id: int,
        notes: Optional[str] = None,
    ) -> dict:
        """年审续期"""
        cred = db.query(SupervisorCredential).filter(
            SupervisorCredential.id == credential_id,
        ).first()
        if not cred:
            raise ValueError(f"资质不存在: {credential_id}")
        if cred.status != "active":
            raise ValueError(f"资质状态 {cred.status} 不可年审")

        cfg = _CREDENTIAL_TYPES.get(cred.credential_type, {})
        review_days = cfg.get("review_interval_days", 365)
        now = datetime.utcnow()

        cred.last_review_at = now
        cred.next_review_at = now + timedelta(days=review_days)
        cred.review_notes = notes
        db.commit()

        return {
            "credential_id": cred.id,
            "next_review_at": cred.next_review_at.isoformat(),
        }

    def revoke_credential(
        self,
        db: Session,
        credential_id: int,
        revoked_by: int,
        reason: str = "",
    ) -> dict:
        """吊销资质 + 若无其他有效资质则降级"""
        cred = db.query(SupervisorCredential).filter(
            SupervisorCredential.id == credential_id,
        ).first()
        if not cred:
            raise ValueError(f"资质不存在: {credential_id}")

        now = datetime.utcnow()
        cred.status = "revoked"
        cred.revoked_by = revoked_by
        cred.revoked_at = now
        cred.revoke_reason = reason

        # 检查是否还有其他有效资质
        other_active = db.query(SupervisorCredential).filter(
            SupervisorCredential.user_id == cred.user_id,
            SupervisorCredential.id != credential_id,
            SupervisorCredential.status == "active",
        ).count()

        role_changed = False
        user = db.query(User).filter(User.id == cred.user_id).first()
        if user and other_active == 0 and user.role == UserRole.SUPERVISOR:
            old_role = user.role.value
            user.role = UserRole.COACH
            role_changed = True
            db.add(RoleChangeLog(
                user_id=user.id,
                old_role=old_role,
                new_role="coach",
                reason="credential_revoked",
                changed_by=revoked_by,
                detail={"credential_id": credential_id, "revoke_reason": reason},
            ))

        db.commit()
        return {
            "credential_id": credential_id,
            "status": "revoked",
            "role_changed": role_changed,
            "new_role": user.role.value if user else None,
        }

    def check_expired_credentials(self, db: Session) -> dict:
        """调度器调用: 自动过期 + 降级"""
        now = datetime.utcnow()
        expired_creds = db.query(SupervisorCredential).filter(
            SupervisorCredential.status == "active",
            SupervisorCredential.next_review_at < now,
        ).all()

        expired_count = 0
        downgraded = 0
        for cred in expired_creds:
            cfg = _CREDENTIAL_TYPES.get(cred.credential_type, {})
            if not cfg.get("auto_expire", True):
                continue

            cred.status = "expired"
            expired_count += 1

            # 发送通知
            db.add(Notification(
                user_id=cred.user_id,
                title="资质已过期",
                body=f"您的{cfg.get('display_name', cred.credential_type)}资质已过期，请联系管理员进行年审续期。",
                type="credential_expired",
                priority="high",
            ))

            # 检查是否需要降级
            other_active = db.query(SupervisorCredential).filter(
                SupervisorCredential.user_id == cred.user_id,
                SupervisorCredential.id != cred.id,
                SupervisorCredential.status == "active",
            ).count()

            if other_active == 0:
                user = db.query(User).filter(User.id == cred.user_id).first()
                if user and user.role == UserRole.SUPERVISOR:
                    old_role = user.role.value
                    user.role = UserRole.COACH
                    downgraded += 1
                    db.add(RoleChangeLog(
                        user_id=user.id,
                        old_role=old_role,
                        new_role="coach",
                        reason="credential_expired",
                        changed_by=0,
                        detail={"credential_id": cred.id, "expired_at": now.isoformat()},
                    ))

        if expired_count:
            db.commit()

        return {"expired": expired_count, "downgraded": downgraded}


    def get_user_credentials(self, db: Session, user_id: int) -> list:
        """查询用户所有资质"""
        creds = db.query(SupervisorCredential).filter(
            SupervisorCredential.user_id == user_id,
        ).order_by(SupervisorCredential.granted_at.desc()).all()

        return [
            {
                "id": c.id,
                "credential_type": c.credential_type,
                "credential_number": c.credential_number,
                "issuing_authority": c.issuing_authority,
                "issued_at": c.issued_at.isoformat() if c.issued_at else None,
                "status": c.status,
                "granted_at": c.granted_at.isoformat() if c.granted_at else None,
                "last_review_at": c.last_review_at.isoformat() if c.last_review_at else None,
                "next_review_at": c.next_review_at.isoformat() if c.next_review_at else None,
                "display_name": _CREDENTIAL_TYPES.get(c.credential_type, {}).get("display_name", c.credential_type),
            }
            for c in creds
        ]
