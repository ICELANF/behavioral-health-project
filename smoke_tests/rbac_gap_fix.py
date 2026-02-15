"""
RBAC 93%→100% 缺口修复清单
来源: V2.4合并版 + Sheet①⑩⑮ 交叉
工期: 2天
依赖: 无（独立于Agent双层分离）

当前状态: 603/646端点有RBAC = 93%
缺口: ~43端点缺权限校验
"""

# ============================================================
# 缺口分类（基于Sheet⑩⑮分析）
# ============================================================

RBAC_GAPS = {
    "P0_supervisor_dual_identity": {
        "描述": "督导专家双身份支持（治理轨+成长轨并存）",
        "来源": "Sheet⑩ 督导专家双来源管理",
        "影响端点": "~6个督导相关端点",
        "修复方案": "RBAC角色模型支持双角色叠加，supervisor可同时持有governance_role和growth_role",
        "工时": "0.5天",
    },
    "P0_master_fine_grained": {
        "描述": "大师(Master)角色细粒度权限",
        "来源": "Sheet①⑤ 大师角色权限行",
        "影响端点": "~8个大师专属端点（督导提名、社区治理等）",
        "修复方案": "在RBAC permission表中为Master补全细粒度权限条目",
        "工时": "0.5天",
    },
    "P1_tool_engine_gaps": {
        "描述": "工具引擎端点RBAC缺口",
        "来源": "Sheet⑮ 实现状态列",
        "影响端点": [
            "400分制教练考核 (exam.coach_cert) — ❌未实现",
            "反思日志安全管线 — ⬜",
            "食物识别安全管线 — ⬜",
        ],
        "修复方案": "exam.coach_cert的RBAC可先加（角色=sharer+），安全管线⬜标V4.1",
        "工时": "0.5天",
    },
    "P1_remaining_misc": {
        "描述": "分散在各路由中的未覆盖端点",
        "来源": "功能盘点646端点",
        "影响端点": "~20+端点（多为辅助性GET端点）",
        "修复方案": "批量扫描路由注册表，给缺少@requires_role装饰器的端点补上",
        "工时": "0.5天",
    },
}

# ============================================================
# 批量扫描脚本 — 找出缺RBAC的端点
# ============================================================

SCAN_SCRIPT = '''#!/usr/bin/env python3
"""
扫描所有FastAPI路由，找出缺少RBAC装饰器的端点
用法: python rbac_scan.py > rbac_gaps.txt
"""
import importlib
import sys
import os

# 按实际项目调整
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def scan_routes():
    """扫描FastAPI app的所有路由"""
    try:
        from app.main import app  # 按实际入口调整
    except ImportError:
        print("ERROR: 无法导入app，请调整导入路径")
        return

    rbac_decorators = {"requires_role", "requires_permission", "role_required",
                       "permission_required", "check_permission", "rbac"}

    results = {"covered": [], "uncovered": []}

    for route in app.routes:
        if not hasattr(route, "endpoint"):
            continue

        path = getattr(route, "path", "?")
        methods = getattr(route, "methods", set())
        endpoint = route.endpoint
        func_source = ""

        # 检查函数及其依赖注入中是否有RBAC
        has_rbac = False

        # 检查装饰器
        if hasattr(endpoint, "__wrapped__"):
            has_rbac = True
        # 检查依赖
        deps = getattr(route, "dependencies", []) or []
        dep_names = [str(d) for d in deps]
        if any(rbac_kw in str(dep_names).lower() for rbac_kw in rbac_decorators):
            has_rbac = True
        # 检查函数签名中的Depends
        import inspect
        sig = inspect.signature(endpoint)
        for param in sig.parameters.values():
            default = param.default
            if "role" in str(default).lower() or "permission" in str(default).lower():
                has_rbac = True
                break

        entry = f"{','.join(methods):8s} {path}"
        if has_rbac:
            results["covered"].append(entry)
        else:
            # 排除公开端点
            public_prefixes = ["/health", "/docs", "/openapi", "/auth/login",
                               "/auth/register", "/content/public"]
            if any(path.startswith(p) for p in public_prefixes):
                results["covered"].append(f"{entry}  (public)")
            else:
                results["uncovered"].append(entry)

    print(f"RBAC覆盖: {len(results['covered'])}/{len(results['covered'])+len(results['uncovered'])}")
    print(f"\\n=== 缺少RBAC的端点 ({len(results['uncovered'])}个) ===")
    for r in sorted(results["uncovered"]):
        print(f"  ⬜ {r}")

    return results

if __name__ == "__main__":
    scan_routes()
'''

# ============================================================
# 批量修复模板
# ============================================================

FIX_TEMPLATE = '''
# 批量修复模式 — 给缺RBAC的端点加装饰器

# 1. 找到项目中的RBAC依赖注入（通常在 app/core/auth.py 或 app/dependencies.py）
# 常见模式:
from app.core.auth import requires_role, get_current_user

# 2. 对每个缺RBAC的端点，加上角色要求:

# 模式A: 装饰器
@router.get("/some-endpoint")
@requires_role(["admin", "coach"])  # ← 加这行
async def some_endpoint(...):
    ...

# 模式B: 依赖注入
@router.get("/some-endpoint")
async def some_endpoint(
    current_user = Depends(requires_role(["admin", "coach"])),  # ← 加这个参数
):
    ...

# 3. 角色对照表（Sheet①⑤）:
# admin    → 全部管理端点
# coach    → 客户管理 + Agent模板 + 知识贡献审核
# promoter → 内容审核 + 督导
# sharer   → 投稿 + 同伴邀请
# grower   → 评估 + 对话 + 微行动 + 挑战
# observer → 公开内容 + 体验版（HF-20 1次 + AI 3轮）
'''

if __name__ == "__main__":
    print("=" * 60)
    print("RBAC 93%→100% 修复计划")
    print("=" * 60)
    total_hours = sum(float(g["工时"].replace("天", "")) * 8 for g in RBAC_GAPS.values())
    print(f"总工时: {total_hours/8:.1f}天")
    print()
    for key, gap in RBAC_GAPS.items():
        print(f"[{key}] {gap['描述']}")
        print(f"  来源: {gap['来源']}")
        print(f"  工时: {gap['工时']}")
        print(f"  方案: {gap['修复方案']}")
        print()
