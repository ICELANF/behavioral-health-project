#!/usr/bin/env python3
"""
加固层执行器 — 冒烟通过后的4天加固工作

用法:
    python harden.py status          # 查看加固进度
    python harden.py audit           # Step 1: 审计补全 (0.5天)
    python harden.py rbac            # Step 2: RBAC封口 (2天)
    python harden.py routes          # Step 3: 路由补全+重跑 (0.5天)
    python harden.py rfc             # Step 4: Agent双层RFC (1天)
    python harden.py verify          # 加固后全量回归
"""
import json
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

PROGRESS_FILE = ROOT / "harden_progress.json"


def _load_progress() -> dict:
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text())
    return {
        "smoke_passed": "2026-02-15",
        "audit": {"status": "pending", "started": None, "completed": None},
        "rbac": {"status": "pending", "started": None, "completed": None},
        "routes": {"status": "pending", "started": None, "completed": None},
        "rfc": {"status": "pending", "started": None, "completed": None},
        "regression": {"status": "pending", "result": None},
    }


def _save_progress(p: dict):
    PROGRESS_FILE.write_text(json.dumps(p, indent=2, ensure_ascii=False))


def _run(cmd: str):
    print(f"$ {cmd}")
    return subprocess.run(cmd, shell=True)


def _header(text: str):
    print(f"\n{'━'*60}")
    print(f"  {text}")
    print(f"{'━'*60}\n")


# ═══════════════════════════════════════════
# Status
# ═══════════════════════════════════════════

def cmd_status():
    p = _load_progress()
    _header("加固层进度")
    steps = [
        ("冒烟测试", "smoke_passed", p.get("smoke_passed", "?")),
        ("审计补全", "audit", p["audit"]["status"]),
        ("RBAC封口", "rbac", p["rbac"]["status"]),
        ("路由补全", "routes", p["routes"]["status"]),
        ("Agent RFC", "rfc", p["rfc"]["status"]),
        ("回归验证", "regression", p["regression"]["status"]),
    ]
    icons = {"completed": "[OK]", "in_progress": "[..]", "pending": "[  ]"}
    for name, key, status in steps:
        icon = icons.get(status, "[OK]" if isinstance(status, str) and "202" in status else "[  ]")
        print(f"  {icon} {name}: {status}")

    print(f"\n下一步: ", end="")
    for name, key, status in steps:
        if status == "pending":
            print(f"python harden.py {key.split('_')[0] if '_' in key else key}")
            break
    else:
        print("全部完成!")


# ═══════════════════════════════════════════
# Step 1: 审计补全
# ═══════════════════════════════════════════

def cmd_audit():
    _header("Step 1: 审计补全 (Sheet⑮ 3端点)")
    p = _load_progress()
    p["audit"]["status"] = "in_progress"
    p["audit"]["started"] = datetime.now().isoformat()
    _save_progress(p)

    print("""
┌─────────────────────────────────────────────────────────┐
│  目标: 给 survey.create / exam.create / exam.submit     │
│        3个端点补全审计日志写入                            │
│  工时: 0.5天                                             │
│  工具: patches/audit_patch.py                            │
└─────────────────────────────────────────────────────────┘

执行步骤:

  1. 扫描你的app目录，找出缺审计的端点:
     python patches/audit_patch.py scan /path/to/xingjian/app

  2. 对3个目标端点注入审计代码:
     python patches/audit_patch.py inject /path/to/app/api/v1/survey.py survey.create
     python patches/audit_patch.py inject /path/to/app/api/v1/exam.py exam.create
     python patches/audit_patch.py inject /path/to/app/api/v1/exam.py exam.submit

     (如果文件路径不同，scan的输出会告诉你正确位置)

  3. 重启服务后验证:
     python patches/audit_patch.py verify http://localhost:8000

  4. 完成后标记:
     python harden.py audit-done
""")


def cmd_audit_done():
    p = _load_progress()
    p["audit"]["status"] = "completed"
    p["audit"]["completed"] = datetime.now().isoformat()
    _save_progress(p)
    print("[OK] Audit completed")
    print("下一步: python harden.py rbac")


# ═══════════════════════════════════════════
# Step 2: RBAC封口
# ═══════════════════════════════════════════

def cmd_rbac():
    _header("Step 2: RBAC 93%→100% (Sheet①⑤⑩)")
    p = _load_progress()
    p["rbac"]["status"] = "in_progress"
    p["rbac"]["started"] = datetime.now().isoformat()
    _save_progress(p)

    print("""
┌─────────────────────────────────────────────────────────┐
│  目标: 补全~43个缺RBAC装饰器的端点                      │
│  工时: 2天                                               │
│  工具: patches/rbac_patch.py                             │
└─────────────────────────────────────────────────────────┘

执行步骤:

  Day 1 — 扫描 + Supervisor/Master修复:

    1. 扫描缺口:
       python patches/rbac_patch.py scan /path/to/xingjian/app

    2. 预览修复 (不写文件):
       python patches/rbac_patch.py fix /path/to/xingjian/app --dry-run

    3. 手动修复 P0 (Supervisor双身份 + Master细粒度):
       - 找到RBAC角色模型，给Supervisor添加双角色支持
       - 给Master补全细粒度权限条目
       - 参考 Sheet① 角色架构 + Sheet⑤ 权限矩阵

  Day 2 — 批量修复 + 验证:

    4. 执行自动修复 (备份原文件):
       python patches/rbac_patch.py fix /path/to/xingjian/app --apply

    5. 重启服务，重跑RBAC测试:
       python run.py day3

    6. 确认覆盖率:
       python patches/rbac_patch.py scan /path/to/xingjian/app
       # 目标: 100% 或 ≥98% (少量webhook/health可豁免)

  完成后标记:
    python harden.py rbac-done
""")


def cmd_rbac_done():
    p = _load_progress()
    p["rbac"]["status"] = "completed"
    p["rbac"]["completed"] = datetime.now().isoformat()
    _save_progress(p)
    print("[OK] RBAC completed")
    print("下一步: python harden.py routes")


# ═══════════════════════════════════════════
# Step 3: 路由补全
# ═══════════════════════════════════════════

def cmd_routes():
    _header("Step 3: 路由补全 + 9个Skip重跑")
    p = _load_progress()
    p["routes"]["status"] = "in_progress"
    p["routes"]["started"] = datetime.now().isoformat()
    _save_progress(p)

    print("自动搜索正确路径...\n")
    result = _run(f"{sys.executable} patches/fix_skips.py discover")

    print(f"""
搜索完毕。如仍有未找到的路由，手动查找:
  python patches/fix_skips.py manual

路由补全后全量重跑:
  python run.py all

完成后标记:
  python harden.py routes-done
""")


def cmd_routes_done():
    p = _load_progress()
    p["routes"]["status"] = "completed"
    p["routes"]["completed"] = datetime.now().isoformat()
    _save_progress(p)
    print("[OK] Routes completed")
    print("下一步: python harden.py rfc")


# ═══════════════════════════════════════════
# Step 4: Agent双层RFC
# ═══════════════════════════════════════════

def cmd_rfc():
    _header("Step 4: Agent双层物理分离 RFC")
    p = _load_progress()
    p["rfc"]["status"] = "in_progress"
    p["rfc"]["started"] = datetime.now().isoformat()
    _save_progress(p)

    # 生成RFC模板
    rfc_path = ROOT / "outputs" / "agent_dual_layer_rfc.md"
    rfc_path.parent.mkdir(exist_ok=True)
    rfc_path.write_text(RFC_TEMPLATE)
    print(f"RFC模板已生成: {rfc_path}")
    print(f"\n请填写并提交架构评审后标记: python harden.py rfc-done")


def cmd_rfc_done():
    p = _load_progress()
    p["rfc"]["status"] = "completed"
    p["rfc"]["completed"] = datetime.now().isoformat()
    _save_progress(p)
    print("[OK] Agent RFC completed")
    print("加固层全部完成! 下一步: Agent双层编码 (V4.1主线, 4周)")


# ═══════════════════════════════════════════
# 全量回归
# ═══════════════════════════════════════════

def cmd_verify():
    _header("加固后全量回归")
    result = _run(f"{sys.executable} run.py all")
    p = _load_progress()
    p["regression"]["status"] = "completed"
    p["regression"]["result"] = "PASS" if result.returncode == 0 else f"exit={result.returncode}"
    _save_progress(p)


# ═══════════════════════════════════════════
# RFC Template
# ═══════════════════════════════════════════

RFC_TEMPLATE = """# RFC: Agent双层物理分离

**版本:** 0.1 Draft
**日期:** {date}
**作者:** 行健平台团队
**来源:** 契约注册表 Sheet⑫ · V4.1 P0
**预计工期:** 4周

---

## 1. 动机

当前Agent架构使用RBAC逻辑隔离，用户层和教练层Agent共享同一数据库schema和服务进程。
在行为健康场景下，用户层数据（健康记录、心理评估）和教练层数据（督导记录、专业诊断）
需要物理隔离以满足合规要求。

**冒烟测试验证了当前RBAC隔离在MVP阶段有效（Day 3 C1-C5全绿），但不能替代物理隔离。**

## 2. 目标

- 用户层12个健康助手Agent → assistant_agents/ 独立部署单元
- 教练层12+4个专业Agent → professional_agents/ 独立部署单元
- 两层之间通过API网关通信，无直接数据库访问
- 向后兼容: 现有API路由不变，客户端无感

## 3. 架构设计

### 3.1 现状 (V4.0)

```
┌─────────────────────────────────┐
│        MasterAgent 9步编排       │
│  ┌───────────┬────────────────┐ │
│  │ User Agent│ Coach Agent    │ │
│  │ (12个)    │ (16个)         │ │
│  └───────┬───┴───────┬────────┘ │
│          │  共享DB    │          │
│          └───────────┘           │
└─────────────────────────────────┘
```

### 3.2 目标 (V4.1)

```
┌──────────────────┐    API GW    ┌──────────────────┐
│  assistant_agents │◄───────────►│ professional_agents│
│  (用户层)         │             │ (教练层)           │
│  ┌─────────────┐ │             │ ┌──────────────┐  │
│  │ 12个健康助手 │ │             │ │ 12+4专业Agent│  │
│  └─────────────┘ │             │ └──────────────┘  │
│  ┌─────────────┐ │             │ ┌──────────────┐  │
│  │ user_db     │ │             │ │ coach_db     │  │
│  └─────────────┘ │             │ └──────────────┘  │
└──────────────────┘              └──────────────────┘
```

### 3.3 数据隔离边界

| 数据类别 | 用户层可见 | 教练层可见 | 隔离方式 |
|---------|-----------|-----------|---------|
| 用户健康记录 | ✅ 本人 | ✅ 授权教练 | API网关授权 |
| 心理评估原始数据 | ✅ 本人 | ❌ 仅聚合统计 | 物理隔离 |
| 教练督导记录 | ❌ | ✅ 本人+上级督导 | 物理隔离 |
| Agent对话日志 | ✅ 本人 | ✅ 授权教练(脱敏) | API网关+脱敏 |
| 行为处方 | ✅ 本人 | ✅ 制定教练 | API网关授权 |

### 3.4 迁移策略

- Phase A (Week 1-2): 代码分离 — 复制Agent代码到两个独立模块
- Phase B (Week 2-3): 数据分离 — 双schema + 迁移脚本
- Phase C (Week 3-4): 网关接入 — API路由切换 + 灰度发布

## 4. 影响范围

- **端点变更:** ~30个端点路由调整 (Sheet⑫)
- **数据库:** 新增 coach_db schema，迁移教练相关表
- **依赖链:** 督导三重角色 (3周) + Agent注册 (2.5周) 依赖本RFC
- **测试:** 需新增跨层集成测试 ~40个用例

## 5. 风险

| 风险 | 等级 | 缓解 |
|------|-----|------|
| 迁移期间数据不一致 | HIGH | 双写期 + 一致性校验脚本 |
| 跨层API延迟增加 | MEDIUM | 缓存 + 批量API |
| 现有RBAC逻辑冲突 | LOW | 冒烟测试已验证RBAC稳定 |

## 6. 里程碑

| 周 | 交付物 | 验收标准 |
|----|-------|---------|
| W1 | 代码分离完成 | 两个模块独立编译通过 |
| W2 | 数据schema分离 | 双schema迁移脚本可逆 |
| W3 | API网关路由切换 | 冒烟测试在新架构下全绿 |
| W4 | 灰度发布 + 回滚验证 | 生产环境切换无故障 |

## 7. 审批

- [ ] 架构评审
- [ ] 数据安全评审
- [ ] 合规评审
""".replace("{date}", datetime.now().strftime("%Y-%m-%d"))


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════

COMMANDS = {
    "status": cmd_status,
    "audit": cmd_audit,
    "audit-done": cmd_audit_done,
    "rbac": cmd_rbac,
    "rbac-done": cmd_rbac_done,
    "routes": cmd_routes,
    "routes-done": cmd_routes_done,
    "rfc": cmd_rfc,
    "rfc-done": cmd_rfc_done,
    "verify": cmd_verify,
}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd in COMMANDS:
        COMMANDS[cmd]()
    else:
        print(__doc__)
        print("可用命令:")
        for name in COMMANDS:
            print(f"  python harden.py {name}")
