# -*- coding: utf-8 -*-
"""
初始化测试用户脚本
Seed Test Users Script

为每个角色创建一个测试用户，用于开发和测试。

用法:
    python scripts/seed_test_users.py
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from core.database import SessionLocal, engine
from core.models import User, UserRole, Base
from core.auth import hash_password
from loguru import logger

# 测试用户配置（与前端 LoginPage.tsx 一致）
TEST_USERS = [
    {
        "username": "observer",
        "email": "observer@test.local",
        "password": "Observer@2026",
        "role": UserRole.OBSERVER,
        "full_name": "测试观察员",
    },
    {
        "username": "grower",
        "email": "grower@test.local",
        "password": "Grower@2026",
        "role": UserRole.GROWER,
        "full_name": "测试成长者",
    },
    {
        "username": "sharer",
        "email": "sharer@test.local",
        "password": "Sharer@2026",
        "role": UserRole.SHARER,
        "full_name": "测试分享者",
    },
    {
        "username": "coach",
        "email": "coach@test.local",
        "password": "Coach@2026",
        "role": UserRole.COACH,
        "full_name": "测试健康教练",
    },
    {
        "username": "promoter",
        "email": "promoter@test.local",
        "password": "Promoter@2026",
        "role": UserRole.PROMOTER,
        "full_name": "测试促进师",
    },
    {
        "username": "supervisor",
        "email": "supervisor@test.local",
        "password": "Supervisor@2026",
        "role": UserRole.SUPERVISOR,
        "full_name": "测试督导专家",
    },
    {
        "username": "master",
        "email": "master@test.local",
        "password": "Master@2026",
        "role": UserRole.MASTER,
        "full_name": "测试大师",
    },
    {
        "username": "admin",
        "email": "admin@test.local",
        "password": "Admin@2026",
        "role": UserRole.ADMIN,
        "full_name": "测试管理员",
    },
]


def seed_test_users(db: Session) -> dict:
    """
    初始化测试用户

    返回创建/跳过的用户统计
    """
    stats = {"created": 0, "skipped": 0, "errors": 0}

    for user_data in TEST_USERS:
        try:
            # 检查用户是否已存在
            existing = db.query(User).filter(
                (User.username == user_data["username"]) |
                (User.email == user_data["email"])
            ).first()

            if existing:
                logger.info(f"用户已存在，跳过: {user_data['username']}")
                stats["skipped"] += 1
                continue

            # 创建新用户
            new_user = User(
                username=user_data["username"],
                email=user_data["email"],
                password_hash=hash_password(user_data["password"]),
                role=user_data["role"],
                full_name=user_data["full_name"],
                is_active=True,
                is_verified=True,  # 测试用户默认已验证
            )

            db.add(new_user)
            db.commit()

            logger.info(f"创建用户成功: {user_data['username']} ({user_data['role'].value})")
            stats["created"] += 1

        except Exception as e:
            logger.error(f"创建用户失败 {user_data['username']}: {e}")
            db.rollback()
            stats["errors"] += 1

    return stats


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("开始初始化测试用户...")
    logger.info("=" * 50)

    # 确保表存在
    Base.metadata.create_all(bind=engine)

    # 创建数据库会话
    db = SessionLocal()

    try:
        stats = seed_test_users(db)

        logger.info("=" * 50)
        logger.info("测试用户初始化完成!")
        logger.info(f"  - 创建: {stats['created']} 个")
        logger.info(f"  - 跳过: {stats['skipped']} 个（已存在）")
        logger.info(f"  - 错误: {stats['errors']} 个")
        logger.info("=" * 50)

        # 打印测试账号信息
        print("\n测试账号信息：")
        print("-" * 60)
        print(f"{'角色':<15} {'用户名':<15} {'密码':<20}")
        print("-" * 60)
        for user in TEST_USERS:
            role_label = user["role"].value
            print(f"{role_label:<15} {user['username']:<15} {user['password']:<20}")
        print("-" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    main()
