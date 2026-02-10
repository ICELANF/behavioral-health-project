"""
鉴权模块测试 — JWT + 密码 + 角色 + 端点集成
运行: python tests/test_auth.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DATABASE_URL"] = "sqlite:///test_auth.db"
os.environ["QDRANT_URL"] = "http://localhost:6333"
os.environ["DASHSCOPE_API_KEY"] = "test-key"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-unit-tests-only"

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}: {detail}")


# ══════════════════════════════════════════════
# 1. 密码工具
# ══════════════════════════════════════════════

def test_password():
    print("\n━━━ 1. Password Hashing ━━━")
    from api.auth import hash_password, verify_password

    plain = "myP@ssw0rd"
    hashed = hash_password(plain)

    check("hash not plaintext", hashed != plain)
    check("hash starts with $2b$", hashed.startswith("$2b$"))
    check("verify correct password", verify_password(plain, hashed))
    check("reject wrong password", not verify_password("wrong", hashed))

    # 不同密码 → 不同 hash (salt)
    hashed2 = hash_password(plain)
    check("different salts", hashed != hashed2)
    check("both verify", verify_password(plain, hashed2))


# ══════════════════════════════════════════════
# 2. JWT Token
# ══════════════════════════════════════════════

def test_jwt():
    print("\n━━━ 2. JWT Token ━━━")
    from api.auth import (
        create_access_token, create_refresh_token,
        create_token_pair, decode_token, TokenPayload,
    )

    # Access token
    at = create_access_token(user_id=42, role="user")
    check("access token is string", isinstance(at, str))
    check("access token has 3 parts", len(at.split(".")) == 3)

    payload = decode_token(at)
    check("decode user_id=42", payload.user_id == 42)
    check("decode role=user", payload.role == "user")
    check("decode type=access", payload.token_type == "access")
    check("decode exp > now", payload.exp > time.time())

    # Refresh token
    rt = create_refresh_token(user_id=42, role="admin")
    payload_r = decode_token(rt)
    check("refresh type=refresh", payload_r.token_type == "refresh")
    check("refresh role=admin", payload_r.role == "admin")

    # Token pair
    pair = create_token_pair(user_id=99, role="bhp_coach")
    check("pair has access_token", len(pair.access_token) > 20)
    check("pair has refresh_token", len(pair.refresh_token) > 20)
    check("pair token_type=bearer", pair.token_type == "bearer")
    check("pair expires_in=7200", pair.expires_in == 120 * 60)
    check("access != refresh", pair.access_token != pair.refresh_token)

    # Invalid token
    from fastapi import HTTPException
    try:
        decode_token("invalid.token.here")
        check("reject invalid token", False, "should have raised")
    except HTTPException as e:
        check("reject invalid token", e.status_code == 401)

    # Expired token (manual)
    from jose import jwt as jose_jwt
    from datetime import datetime, timezone, timedelta
    expired = jose_jwt.encode(
        {"sub": "1", "role": "user", "exp": datetime.now(timezone.utc) - timedelta(hours=1), "type": "access"},
        os.environ["JWT_SECRET_KEY"], algorithm="HS256",
    )
    try:
        decode_token(expired)
        check("reject expired token", False, "should have raised")
    except HTTPException as e:
        check("reject expired token", e.status_code == 401)


# ══════════════════════════════════════════════
# 3. User Model
# ══════════════════════════════════════════════

def test_user_model():
    print("\n━━━ 3. User Model ━━━")
    from api.auth import User

    check("User tablename=users", User.__tablename__ == "users")

    cols = {c.name for c in User.__table__.columns}
    expected_cols = {
        "id", "phone", "password_hash", "nickname", "avatar_url",
        "role", "is_active", "health_competency_level",
        "current_stage", "growth_level",
        "created_at", "updated_at", "last_login_at",
    }
    for c in expected_cols:
        check(f"User has column '{c}'", c in cols, f"missing from {cols}")


# ══════════════════════════════════════════════
# 4. Request/Response Schemas
# ══════════════════════════════════════════════

def test_schemas():
    print("\n━━━ 4. Auth Schemas ━━━")
    from api.auth import (
        RegisterRequest, LoginRequest, RefreshRequest,
        UserProfile, ChangePasswordRequest, TokenPair,
    )

    # RegisterRequest 验证
    reg = RegisterRequest(phone="13800138000", password="123456")
    check("register phone", reg.phone == "13800138000")

    try:
        RegisterRequest(phone="123", password="123456")
        check("reject short phone", False)
    except Exception:
        check("reject short phone", True)

    try:
        RegisterRequest(phone="13800138000", password="12345")
        check("reject short password", False)
    except Exception:
        check("reject short password", True)

    # LoginRequest
    login = LoginRequest(phone="13800138000", password="test")
    check("login request", login.phone == "13800138000")

    # RefreshRequest
    rf = RefreshRequest(refresh_token="some-token")
    check("refresh request", rf.refresh_token == "some-token")

    # ChangePasswordRequest
    cp = ChangePasswordRequest(old_password="old", new_password="newpass")
    check("change password", cp.new_password == "newpass")

    # UserProfile (from_attributes)
    check("UserProfile has from_attributes", UserProfile.model_config.get("from_attributes"))


# ══════════════════════════════════════════════
# 5. FastAPI TestClient — 端到端
# ══════════════════════════════════════════════

def test_e2e_auth():
    print("\n━━━ 5. End-to-End Auth Flow ━━━")
    from fastapi.testclient import TestClient
    from api.main import app
    from api.database import engine, Base

    # 建表 (先清理确保干净状态)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    client = TestClient(app)

    # 5.1 注册
    resp = client.post("/api/v3/auth/register", json={
        "phone": "13800138001",
        "password": "testpass123",
        "nickname": "测试用户",
    })
    check("register 200", resp.status_code == 200)
    data = resp.json()
    check("register ok=True", data["ok"] is True)
    check("register has tokens", "tokens" in data["data"])
    access_token = data["data"]["tokens"]["access_token"]
    refresh_token = data["data"]["tokens"]["refresh_token"]
    check("register returns user", data["data"]["user"]["phone"] == "13800138001")
    check("register user nickname", data["data"]["user"]["nickname"] == "测试用户")

    # 5.2 重复注册
    resp2 = client.post("/api/v3/auth/register", json={
        "phone": "13800138001",
        "password": "anotherpass",
    })
    check("duplicate register 409", resp2.status_code == 409)

    # 5.3 登录
    resp3 = client.post("/api/v3/auth/login", json={
        "phone": "13800138001",
        "password": "testpass123",
    })
    check("login 200", resp3.status_code == 200)
    check("login ok=True", resp3.json()["ok"] is True)

    # 5.4 错误密码
    resp4 = client.post("/api/v3/auth/login", json={
        "phone": "13800138001",
        "password": "wrong",
    })
    check("wrong password 401", resp4.status_code == 401)

    # 5.5 获取当前用户 (带 Token)
    headers = {"Authorization": f"Bearer {access_token}"}
    resp5 = client.get("/api/v3/auth/me", headers=headers)
    check("me 200 with token", resp5.status_code == 200)
    check("me returns phone", resp5.json()["data"]["phone"] == "13800138001")

    # 5.6 无 Token → 401
    resp6 = client.get("/api/v3/auth/me")
    check("me without token 401", resp6.status_code == 401)

    # 5.7 Token 刷新
    resp7 = client.post("/api/v3/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    check("refresh 200", resp7.status_code == 200)
    new_access = resp7.json()["data"]["access_token"]
    check("refresh returns valid token", len(new_access) > 20)

    # 5.8 用 refresh_token 当 access_token → 401
    resp8 = client.get("/api/v3/auth/me", headers={
        "Authorization": f"Bearer {refresh_token}",
    })
    check("refresh as access → 401", resp8.status_code == 401)

    # 5.9 修改密码
    resp9 = client.put("/api/v3/auth/password", headers=headers, json={
        "old_password": "testpass123",
        "new_password": "newpass456",
    })
    check("change password 200", resp9.status_code == 200)

    # 用新密码登录
    resp10 = client.post("/api/v3/auth/login", json={
        "phone": "13800138001",
        "password": "newpass456",
    })
    check("login with new password", resp10.status_code == 200)

    return access_token, headers


# ══════════════════════════════════════════════
# 6. 业务端点鉴权集成
# ══════════════════════════════════════════════

def test_endpoint_auth():
    print("\n━━━ 6. Endpoint Auth Integration ━━━")
    from fastapi.testclient import TestClient
    from api.main import app

    client = TestClient(app)

    # 无 Token 访问业务端点 → 401
    protected_endpoints = [
        ("POST", "/api/v3/diagnostic/minimal"),
        ("POST", "/api/v3/chat/message"),
        ("GET", "/api/v3/assessment/session"),
        ("POST", "/api/v3/tracking/daily"),
        ("POST", "/api/v3/incentive/checkin"),
        ("GET", "/api/v3/incentive/balance"),
        ("GET", "/api/v3/admin/knowledge/stats"),
    ]

    for method, path in protected_endpoints:
        if method == "GET":
            resp = client.get(path)
        else:
            resp = client.request(method, path, json={})
        check(f"{method} {path} → 401 without token",
              resp.status_code == 401,
              f"got {resp.status_code}")

    # 公开端点不需要 Token
    public_endpoints = [
        ("GET", "/health"),
        ("GET", "/"),
        ("GET", "/api/v3/assessment/batches"),
    ]
    for method, path in public_endpoints:
        resp = client.get(path)
        check(f"GET {path} → 200 without token",
              resp.status_code == 200,
              f"got {resp.status_code}")

    # 带 Token 访问
    from api.auth import create_access_token
    token = create_access_token(user_id=1, role="user")
    headers = {"Authorization": f"Bearer {token}"}

    # 诊断端点 (会因为缺少 body 返回 422, 但不是 401)
    resp = client.post("/api/v3/diagnostic/minimal", headers=headers, json={
        "behavioral_stage": "S3",
    })
    check("diagnostic with token ≠ 401",
          resp.status_code != 401,
          f"got {resp.status_code}")


# ══════════════════════════════════════════════
# 7. 角色权限
# ══════════════════════════════════════════════

def test_role_guards():
    print("\n━━━ 7. Role Guards ━━━")
    from fastapi.testclient import TestClient
    from api.main import app
    from api.database import SessionLocal
    from api.auth import create_access_token, User, hash_password

    client = TestClient(app)
    db = SessionLocal()

    # 创建 admin 用户和 master 用户
    admin_user = User(phone="13900000001", password_hash=hash_password("admin"), role="admin", nickname="admin")
    master_user = User(phone="13900000002", password_hash=hash_password("master"), role="bhp_master", nickname="master")
    db.add_all([admin_user, master_user])
    db.commit()
    db.refresh(admin_user)
    db.refresh(master_user)

    # 普通用户访问 Admin 端点 → 403 (user_id=1 from e2e test has role=user)
    user_token = create_access_token(user_id=1, role="user")
    user_headers = {"Authorization": f"Bearer {user_token}"}

    resp = client.get("/api/v3/admin/knowledge/stats", headers=user_headers)
    check("user → admin endpoint → 403", resp.status_code == 403)

    # Admin 访问 Admin 端点 → 不是 401/403
    admin_token = create_access_token(user_id=admin_user.id, role="admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    resp2 = client.get("/api/v3/admin/knowledge/stats", headers=admin_headers)
    check("admin → admin endpoint ≠ 403",
          resp2.status_code not in (401, 403),
          f"got {resp2.status_code}")

    # bhp_master 也可以访问
    master_token = create_access_token(user_id=master_user.id, role="bhp_master")
    master_headers = {"Authorization": f"Bearer {master_token}"}

    resp3 = client.get("/api/v3/admin/knowledge/stats", headers=master_headers)
    check("bhp_master → admin endpoint ≠ 403",
          resp3.status_code not in (401, 403),
          f"got {resp3.status_code}")

    db.close()


# ══════════════════════════════════════════════
# 8. Auth Router 端点完整性
# ══════════════════════════════════════════════

def test_auth_router():
    print("\n━━━ 8. Auth Router Endpoints ━━━")
    from api.main import app

    routes = {r.path: r.methods for r in app.routes if hasattr(r, "methods")}

    expected = {
        "/api/v3/auth/register": {"POST"},
        "/api/v3/auth/login": {"POST"},
        "/api/v3/auth/refresh": {"POST"},
        "/api/v3/auth/me": {"GET"},
        "/api/v3/auth/password": {"PUT"},
        "/api/v3/auth/profile": {"PUT"},
        "/api/v3/auth/users": {"GET"},
        "/api/v3/auth/users/{user_id}/role": {"PUT"},
    }
    for path, methods in expected.items():
        check(f"auth {list(methods)[0]} {path}",
              path in routes,
              f"not found")


# ══════════════════════════════════════════════
# 9. Migration v3_004
# ══════════════════════════════════════════════

def test_migration():
    print("\n━━━ 9. Migration v3_004 ━━━")
    import sqlite3
    import tempfile
    from migrations.v3_004_auth import upgrade, _OpHelper

    tmp = tempfile.mktemp(suffix=".db")
    conn = sqlite3.connect(tmp)
    op = _OpHelper(conn)

    upgrade(op)
    conn.commit()

    # 验证表
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    check("users table created", "users" in tables)

    # 验证字段
    cursor = conn.execute("PRAGMA table_info(users)")
    cols = {r[1] for r in cursor.fetchall()}
    for expected in ["phone", "password_hash", "role", "current_stage", "growth_level"]:
        check(f"users has '{expected}'", expected in cols, f"cols: {cols}")

    # 幂等: 再次执行不报错
    try:
        upgrade(op)
        conn.commit()
        check("migration idempotent", True)
    except Exception as e:
        check("migration idempotent", False, str(e))

    conn.close()
    os.unlink(tmp)


# ══════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("BHP v3 Auth Module Tests")
    print("=" * 60)

    t0 = time.time()

    test_password()
    test_jwt()
    test_user_model()
    test_schemas()
    test_e2e_auth()
    test_endpoint_auth()
    test_role_guards()
    test_auth_router()
    test_migration()

    elapsed = time.time() - t0

    print("\n" + "=" * 60)
    print(f"Results: {PASS} passed, {FAIL} failed ({elapsed:.2f}s)")
    print("=" * 60)

    # 清理
    import pathlib
    for f in ["test_auth.db"]:
        p = pathlib.Path(f)
        if p.exists():
            p.unlink()

    if FAIL > 0:
        sys.exit(1)
