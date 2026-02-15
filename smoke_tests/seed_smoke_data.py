"""
冒烟测试种子数据 — 预置多角色测试账号
在运行冒烟测试前执行: python seed_smoke_data.py

前置: 服务已启动，数据库已迁移到最新版本
"""
import httpx
import sys

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
API = f"{BASE_URL}/api/v1"

DEFAULT_PASSWORD = "Test@Smoke2026!"

# ============================================================
# 测试账号定义
# ============================================================

SEED_ACCOUNTS = [
    {
        "username": "smoke_observer",
        "email": "smoke_observer@test.xingjian.com",
        "password": DEFAULT_PASSWORD,
        "target_role": None,  # 保持Observer
        "description": "Observer角色 — 注册但不转化",
    },
    {
        "username": "smoke_grower",
        "email": "smoke_grower@test.xingjian.com",
        "password": DEFAULT_PASSWORD,
        "target_role": "grower",
        "description": "Grower角色 — 注册+转化+S0",
    },
    {
        "username": "smoke_coach",
        "email": "smoke_coach@test.xingjian.com",
        "password": DEFAULT_PASSWORD,
        "target_role": "coach",
        "description": "Coach角色 — 需手动/SQL提权",
    },
    {
        "username": "smoke_sharer",
        "email": "smoke_sharer@test.xingjian.com",
        "password": DEFAULT_PASSWORD,
        "target_role": "sharer",
        "description": "Sharer角色 — 需手动/SQL提权",
    },
]

# Admin账号通常在初始迁移中已创建，不在seed中重复

# ============================================================
# SQL提权模板（如果API不支持直接角色分配）
# ============================================================

SQL_ROLE_ASSIGNMENT = """
-- 如果注册后需要手动提权（Coach/Sharer/Admin无法通过正常流程直接到达）:

-- 查找用户ID
SELECT id, email, role FROM users WHERE email LIKE 'smoke_%';

-- Coach提权
UPDATE users SET role = 'coach', role_level = 3
WHERE email = 'smoke_coach@test.xingjian.com';

-- Sharer提权
UPDATE users SET role = 'sharer', role_level = 2
WHERE email = 'smoke_sharer@test.xingjian.com';

-- 确认Admin已存在
SELECT id, email, role FROM users WHERE role = 'admin' LIMIT 1;

-- 如果需要创建Admin（谨慎使用）:
-- INSERT INTO users (username, email, password_hash, role, role_level, is_active)
-- VALUES ('smoke_admin', 'smoke_admin@test.xingjian.com', '<bcrypt_hash>', 'admin', 99, true);
"""


def seed():
    print(f"目标服务: {BASE_URL}")
    print(f"API前缀: {API}")
    print("=" * 60)

    # 检查服务可达
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=5)
    except httpx.ConnectError:
        print(f"[!!] 服务不可达: {BASE_URL}")
        print("请先启动服务")
        sys.exit(1)

    results = []

    for account in SEED_ACCOUNTS:
        email = account["email"]
        print(f"\n{'─'*40}")
        print(f"创建: {account['description']}")
        print(f"邮箱: {email}")

        # 1. 注册
        r = httpx.post(f"{API}/auth/register", json={
            "username": account["username"],
            "email": email,
            "password": account["password"],
        }, timeout=10)

        if r.status_code == 201:
            print(f"  [OK] 注册成功")
        elif r.status_code in (409, 422):
            print(f"  [--]  已存在，跳过注册")
        else:
            print(f"  [!!] 注册失败: {r.status_code} {r.text[:200]}")
            results.append((email, "FAIL", f"注册: {r.status_code}"))
            continue

        # 2. 登录获取token
        login = httpx.post(f"{API}/auth/login", data={
            "username": account["username"], "password": account["password"],
        }, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=10)

        if login.status_code != 200:
            print(f"  [!!] 登录失败: {login.status_code}")
            results.append((email, "FAIL", f"登录: {login.status_code}"))
            continue

        token = login.json().get("access_token") or login.json().get("token")
        headers = {"Authorization": f"Bearer {token}"}

        # 3. 转化（如果需要）
        if account["target_role"] == "grower":
            conv = httpx.post(f"{API}/conversion/apply", headers=headers,
                              json={"target_role": "grower"}, timeout=10)
            if conv.status_code in (200, 201):
                print(f"  [OK] 转化为Grower成功")
            elif conv.status_code == 404:
                print(f"  [??]  转化端点不存在，可能需要完成体验评估后自动转化")
            else:
                print(f"  [??]  转化: {conv.status_code}")

        elif account["target_role"] in ("coach", "sharer"):
            print(f"  [??]  需手动SQL提权为{account['target_role']}（见下方SQL模板）")

        # 4. 验证当前角色
        me = httpx.get(f"{API}/auth/me", headers=headers, timeout=10)
        if me.status_code == 200:
            role = me.json().get("role") or me.json().get("role_code") or "unknown"
            print(f"  当前角色: {role}")
            results.append((email, "OK", f"role={role}"))
        else:
            results.append((email, "WARN", f"/users/me: {me.status_code}"))

    # 摘要
    print(f"\n{'='*60}")
    print("种子数据创建摘要:")
    for email, status, detail in results:
        icon = {"OK": "[OK]", "FAIL": "[!!]", "WARN": "[??]"}[status]
        print(f"  {icon} {email} — {detail}")

    # 输出SQL提权提示
    print(f"\n{'─'*40}")
    print("如需手动提权Coach/Sharer/Admin，执行以下SQL:")
    print(SQL_ROLE_ASSIGNMENT)


if __name__ == "__main__":
    seed()
