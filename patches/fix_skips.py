#!/usr/bin/env python3
"""
routes.json 补全 — 修复9个skip的路径差异

用法:
    python patches/fix_skips.py discover   # 自动搜索正确路径
    python patches/fix_skips.py manual     # 输出手动查找指导
"""
import json
import sys
import httpx
from pathlib import Path

# Config
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"
API_URL = f"{BASE_URL}{API_PREFIX}"
ROUTES_FILE = Path(__file__).parent.parent / "routes.json"
ADMIN_USER = "admin"
ADMIN_PWD = "Admin@2026"
TEST_PWD = "Test@Smoke2026!"


# 9个skip对应的功能点 + 扩展候选路径
SKIP_ROUTES = {
    # Day 1 skips
    "chat.send_message": {
        "method": "POST",
        "candidates": [
            "/chat/sessions/{id}/messages",
            "/conversations/{id}/messages",
            "/agent/sessions/{id}/messages",
            "/chat/{id}/messages",
            "/chat/messages",
            "/agent/chat/{id}/send",
            "/sessions/{id}/messages",
        ],
    },

    # Day 2 skips
    "points.history": {
        "method": "GET",
        "candidates": [
            "/points/history",
            "/points/log",
            "/incentive/history",
            "/incentive/log",
            "/credits/history",
            "/credits/log",
            "/gamification/history",
            "/points/transactions",
            "/incentive/transactions",
        ],
    },
    "learning.stats": {
        "method": "GET",
        "candidates": [
            "/learning/grower/stats",
            "/learning/stats",
            "/learning/progress",
            "/learning/summary",
            "/education/stats",
            "/education/progress",
            "/users/me/learning",
            "/users/me/learning/stats",
            "/content/learning/stats",
        ],
    },
    "learning.time": {
        "method": "POST",
        "candidates": [
            "/learning/time",
            "/learning/track-time",
            "/learning/record",
            "/education/time",
            "/activity/learning-time",
        ],
    },
    "journey.advance": {
        "method": "POST",
        "candidates": [
            "/journey/advance",
            "/stage/advance",
            "/journey/progress",
            "/journey/next-stage",
            "/stage/transition",
            "/users/me/stage/advance",
            "/journey/transition",
            "/stages/advance",
        ],
    },

    # Day 3 skips
    "rx.compute": {
        "method": "POST",
        "candidates": [
            "/rx/compute",
            "/prescriptions/compute",
            "/behavior-rx/compute",
            "/rx/generate",
            "/behavioral-rx/compute",
            "/treatment/compute",
            "/rx/recommend",
            "/agent/rx",
        ],
    },
    "rx.current": {
        "method": "GET",
        "candidates": [
            "/rx/current",
            "/prescriptions/current",
            "/behavior-rx/current",
            "/rx/latest",
            "/rx/active",
            "/behavioral-rx/current",
        ],
    },
    "agent_tpl.create": {
        "method": "POST",
        "candidates": [
            "/agent-templates",
            "/agents/templates",
            "/agent/templates",
            "/templates/agent",
            "/agent-template",
        ],
    },
}


def _get_token(client: httpx.Client, username: str, password: str) -> str | None:
    """Form-encoded login, returns token or None"""
    url = f"{API_URL}/auth/login"
    try:
        r = client.post(url, data={
            "username": username,
            "password": password,
        }, headers={"Content-Type": "application/x-www-form-urlencoded"})
        if r.status_code == 200:
            data = r.json()
            return data.get("access_token") or data.get("token")
    except Exception:
        pass
    return None


def discover():
    """自动探测skip路由的正确路径"""
    print(f"{'═'*60}")
    print(f"  路由补全 — 修复9个skip")
    print(f"  目标: {BASE_URL}")
    print(f"{'═'*60}\n")

    # 加载现有routes
    routes = json.loads(ROUTES_FILE.read_text()) if ROUTES_FILE.exists() else {}
    original_count = len(routes)

    with httpx.Client(timeout=10) as client:
        # 获取多角色token
        admin_token = _get_token(client, ADMIN_USER, ADMIN_PWD)
        grower_token = _get_token(client, "smoke_grower", TEST_PWD)

        admin_h = {"Authorization": f"Bearer {admin_token}"} if admin_token else {}
        grower_h = {"Authorization": f"Bearer {grower_token}"} if grower_token else {}

        found = 0
        not_found = 0

        for name, spec in SKIP_ROUTES.items():
            method = spec["method"]
            # 选择合适的headers
            if any(x in name for x in ["admin", "agent_tpl"]):
                headers = admin_h
            else:
                headers = grower_h

            print(f"[>>] {name} ({method})")

            matched = False
            for path in spec["candidates"]:
                # 构建URL
                probe_path = path.replace("{id}", "00000000-0000-0000-0000-000000000000")
                url = f"{API_URL}{probe_path}"

                try:
                    if method == "GET":
                        r = client.get(url, headers=headers)
                    else:
                        r = client.post(url, headers=headers, json={})
                except Exception:
                    continue

                # 404 = 端点不存在; 其他 = 端点存在
                if r.status_code != 404:
                    print(f"   [OK] {path} → {r.status_code}")
                    routes[name] = {"method": method, "path": path, "probe_status": r.status_code}
                    matched = True
                    found += 1
                    break
                else:
                    print(f"   ✗ {path} → 404")

            if not matched:
                print(f"   [!!] 所有候选路径均404")
                not_found += 1

        # 额外: 尝试从OpenAPI schema发现
        if not_found > 0:
            print(f"\n[>>] 尝试OpenAPI schema兜底...")
            for doc_path in ["/openapi.json", "/api/v1/openapi.json", "/docs/openapi.json"]:
                try:
                    r = client.get(f"{BASE_URL}{doc_path}")
                    if r.status_code == 200 and "paths" in r.text:
                        schema = r.json()
                        api_paths = schema.get("paths", {})
                        print(f"   OpenAPI有 {len(api_paths)} 个路径")

                        for name, spec in SKIP_ROUTES.items():
                            if name in routes:
                                continue
                            method = spec["method"]
                            # 模糊匹配
                            keywords = name.replace(".", " ").replace("_", " ").split()
                            for api_path, methods in api_paths.items():
                                if method.lower() in methods:
                                    path_lower = api_path.lower()
                                    if any(kw in path_lower for kw in keywords):
                                        clean_path = api_path.replace(API_PREFIX, "")
                                        print(f"   [OK] {name} → {clean_path} (OpenAPI)")
                                        routes[name] = {
                                            "method": method,
                                            "path": clean_path,
                                            "source": "openapi",
                                        }
                                        found += 1
                                        break
                        break
                except Exception:
                    continue

    # 保存
    ROUTES_FILE.write_text(json.dumps(routes, indent=2, ensure_ascii=False))
    new_count = len(routes)

    print(f"\n{'═'*60}")
    print(f"  结果: +{found} 路由发现, {not_found} 仍未找到")
    print(f"  routes.json: {original_count} → {new_count} 条")
    print(f"{'═'*60}")

    if not_found > 0:
        print(f"\n未找到的路由需要手动添加。运行:")
        print(f"  python patches/fix_skips.py manual")
        print(f"\n或直接从OpenAPI/代码中查找正确路径后编辑 routes.json")

    print(f"\n补全后重跑测试:")
    print(f"  python run.py all")


def manual():
    """输出手动查找指导"""
    print(f"{'═'*60}")
    print(f"  手动路由查找指导")
    print(f"{'═'*60}\n")
    print(f"在你的代码中搜索以下关键词:\n")

    searches = {
        "points.history":    "grep -rn 'points.*history\\|incentive.*log\\|credit.*history' app/api/",
        "learning.stats":    "grep -rn 'learning.*stat\\|education.*progress' app/api/",
        "learning.time":     "grep -rn 'learning.*time\\|track.time' app/api/",
        "journey.advance":   "grep -rn 'journey.*advance\\|stage.*transition\\|stage.*advance' app/api/",
        "rx.compute":        "grep -rn 'rx.*compute\\|prescription.*compute\\|behavioral.*rx' app/api/",
        "rx.current":        "grep -rn 'rx.*current\\|prescription.*current\\|rx.*active' app/api/",
        "agent_tpl.create":  "grep -rn 'agent.*template\\|template.*create' app/api/",
        "chat.send_message": "grep -rn 'send_message\\|chat.*message\\|create_message' app/api/",
    }

    for name, cmd in searches.items():
        print(f"  {name}:")
        print(f"    {cmd}")
        print()

    print(f"找到后编辑 routes.json，格式:")
    print(f'  "route_name": {{"method": "GET|POST", "path": "/actual/path"}}')
    print(f"\n然后重跑: python run.py all")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "discover"
    if cmd == "discover":
        discover()
    elif cmd == "manual":
        manual()
    else:
        print(f"用法: python patches/fix_skips.py [discover|manual]")
