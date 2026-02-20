#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CI Seed Demo Accounts — creates test users for CI environment.

Usage:
    python scripts/seed_demo_accounts.py --db postgresql://user:pass@host:5432/dbname
    python scripts/seed_demo_accounts.py  # uses DATABASE_URL env var
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.models import User, UserRole, Base
from core.auth import hash_password

TEST_USERS = [
    {"username": "admin", "email": "admin@test.local", "password": "Admin@2026", "role": UserRole.ADMIN, "full_name": "Test Admin"},
    {"username": "observer", "email": "observer@test.local", "password": "Observer@2026", "role": UserRole.OBSERVER, "full_name": "Test Observer"},
    {"username": "grower", "email": "grower@test.local", "password": "Grower@2026", "role": UserRole.GROWER, "full_name": "Test Grower"},
    {"username": "sharer", "email": "sharer@test.local", "password": "Sharer@2026", "role": UserRole.SHARER, "full_name": "Test Sharer"},
    {"username": "coach", "email": "coach@test.local", "password": "Coach@2026", "role": UserRole.COACH, "full_name": "Test Coach"},
    {"username": "promoter", "email": "promoter@test.local", "password": "Promoter@2026", "role": UserRole.PROMOTER, "full_name": "Test Promoter"},
    {"username": "supervisor", "email": "supervisor@test.local", "password": "Supervisor@2026", "role": UserRole.SUPERVISOR, "full_name": "Test Supervisor"},
    {"username": "master", "email": "master@test.local", "password": "Master@2026", "role": UserRole.MASTER, "full_name": "Test Master"},
]


def main():
    parser = argparse.ArgumentParser(description="Seed demo accounts for CI")
    parser.add_argument("--db", default=os.environ.get("DATABASE_URL", ""), help="Database URL")
    args = parser.parse_args()

    db_url = args.db or os.environ.get("DATABASE_URL", "")
    if not db_url:
        print("ERROR: No database URL provided. Use --db or set DATABASE_URL.")
        sys.exit(1)

    # Ensure sync driver
    if "+asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg", "postgresql")

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    created = 0
    skipped = 0

    try:
        for u in TEST_USERS:
            existing = db.query(User).filter(User.username == u["username"]).first()
            if existing:
                skipped += 1
                continue
            user = User(
                username=u["username"],
                email=u["email"],
                password_hash=hash_password(u["password"]),
                role=u["role"],
                full_name=u["full_name"],
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            db.commit()
            created += 1
        print(f"Seed complete: {created} created, {skipped} skipped")
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
