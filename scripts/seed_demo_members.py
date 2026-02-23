# -*- coding: utf-8 -*-
"""
生成模拟成员数据
Seed Demo Members for Supervisor Workbench

为促进师以下角色(教练/分享者/成长者/观察员)各创建3个模拟用户，
用于督导工作台展示。

用法:
    docker exec -it bhp-api python scripts/seed_demo_members.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from core.database import SessionLocal, engine
from core.models import User, UserRole, Base
from core.auth import hash_password
from loguru import logger

DEMO_MEMBERS = [
    # 教练 (L3)
    {"username": "coach_zhang", "email": "coach_zhang@demo.local", "password": "Demo@2026",
     "role": UserRole.COACH, "full_name": "张教练"},
    {"username": "coach_li", "email": "coach_li@demo.local", "password": "Demo@2026",
     "role": UserRole.COACH, "full_name": "李教练"},
    {"username": "coach_wang", "email": "coach_wang@demo.local", "password": "Demo@2026",
     "role": UserRole.COACH, "full_name": "王教练"},
    # 分享者 (L2)
    {"username": "sharer_liu", "email": "sharer_liu@demo.local", "password": "Demo@2026",
     "role": UserRole.SHARER, "full_name": "刘分享"},
    {"username": "sharer_chen", "email": "sharer_chen@demo.local", "password": "Demo@2026",
     "role": UserRole.SHARER, "full_name": "陈分享"},
    {"username": "sharer_yang", "email": "sharer_yang@demo.local", "password": "Demo@2026",
     "role": UserRole.SHARER, "full_name": "杨分享"},
    # 成长者 (L1)
    {"username": "grower_zhao", "email": "grower_zhao@demo.local", "password": "Demo@2026",
     "role": UserRole.GROWER, "full_name": "赵成长"},
    {"username": "grower_huang", "email": "grower_huang@demo.local", "password": "Demo@2026",
     "role": UserRole.GROWER, "full_name": "黄成长"},
    {"username": "grower_wu", "email": "grower_wu@demo.local", "password": "Demo@2026",
     "role": UserRole.GROWER, "full_name": "吴成长"},
    # 观察员 (L0)
    {"username": "observer_sun", "email": "observer_sun@demo.local", "password": "Demo@2026",
     "role": UserRole.OBSERVER, "full_name": "孙观察"},
    {"username": "observer_zhou", "email": "observer_zhou@demo.local", "password": "Demo@2026",
     "role": UserRole.OBSERVER, "full_name": "周观察"},
    {"username": "observer_xu", "email": "observer_xu@demo.local", "password": "Demo@2026",
     "role": UserRole.OBSERVER, "full_name": "徐观察"},
]


def seed_demo_members():
    db: Session = SessionLocal()
    created = 0
    skipped = 0

    try:
        for member in DEMO_MEMBERS:
            existing = db.query(User).filter(User.username == member["username"]).first()
            if existing:
                logger.info(f"  跳过已存在: {member['username']} ({member['full_name']})")
                skipped += 1
                continue

            user = User(
                username=member["username"],
                email=member["email"],
                password_hash=hash_password(member["password"]),
                role=member["role"],
                full_name=member["full_name"],
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            created += 1
            logger.info(f"  创建: {member['username']} ({member['full_name']}) - {member['role'].value}")

        db.commit()
        logger.info(f"\n完成: 创建 {created} 个, 跳过 {skipped} 个")
    except Exception as e:
        db.rollback()
        logger.error(f"失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("=== 生成模拟成员 ===")
    seed_demo_members()
