#!/usr/bin/env python3
"""
V4.1 迁移映射 — 基于 analyze 实际输出

68条API路由 → 用户层 / 教练层 / 网关 / 废弃

用法:
    python migrate_map.py show              # 显示映射表
    python migrate_map.py bridge            # 生成路由桥接代码
    python migrate_map.py register          # 生成main.py注册代码
    python migrate_map.py execute [app_dir] # 执行迁移（移动import，不改逻辑）
"""
import sys
import re
import shutil
from pathlib import Path
from datetime import datetime

# ═══════════════════════════════════════════════════════════
# 路由映射表 — 每条路由的归属决策
# ═══════════════════════════════════════════════════════════

ROUTE_MAP = {
    # ────────── 用户层 (assistant_agents) ──────────
    # 用户直接交互的对话、试用、会话管理
    "assistant": [
        # chat_rest_api.py — 用户对话核心
        {"method": "GET",    "path": "/sessions",                       "source": "api/chat_rest_api.py",    "func": "list_sessions"},
        {"method": "POST",   "path": "/sessions",                       "source": "api/chat_rest_api.py",    "func": "create_session"},
        {"method": "DELETE", "path": "/sessions/{session_id}",          "source": "api/chat_rest_api.py",    "func": "delete_session"},
        {"method": "GET",    "path": "/sessions/{session_id}/messages", "source": "api/chat_rest_api.py",    "func": "get_messages"},
        {"method": "POST",   "path": "/sessions/{session_id}/messages", "source": "api/chat_rest_api.py",    "func": "send_message"},

        # miniprogram.py — 小程序端对话
        {"method": "POST",   "path": "/chat",                           "source": "api/miniprogram.py",      "func": "chat"},
        {"method": "POST",   "path": "/chat/stream",                    "source": "api/miniprogram.py",      "func": "chat_stream"},
        {"method": "GET",    "path": "/chat/sessions",                  "source": "api/miniprogram.py",      "func": "list_chat_sessions"},
        {"method": "GET",    "path": "/chat/history/{session_id}",      "source": "api/miniprogram.py",      "func": "get_chat_history"},
        {"method": "DELETE", "path": "/chat/history",                   "source": "api/miniprogram.py",      "func": "clear_history"},
        {"method": "DELETE", "path": "/chat/session/{session_id}",      "source": "api/miniprogram.py",      "func": "delete_chat_session"},

        # trial_api.py — 试用限额
        {"method": "POST",   "path": "/chat/consume",                   "source": "api/trial_api.py",        "func": "consume_trial"},
        {"method": "GET",    "path": "/chat/status",                    "source": "api/trial_api.py",        "func": "get_trial_status"},

        # routes.py — 通用对话入口
        {"method": "POST",   "path": "/chat",                           "source": "api/routes.py",           "func": "chat_endpoint"},
        {"method": "POST",   "path": "/session/reset-all",              "source": "api/routes.py",           "func": "reset_sessions"},
        {"method": "DELETE", "path": "/session/{session_id}",           "source": "api/routes.py",           "func": "delete_session"},

        # routers/chat.py — 消息发送
        {"method": "POST",   "path": "/message",                        "source": "api/routers/chat.py",     "func": "send_message"},

        # routers/assessment.py — 评估会话(用户侧)
        {"method": "GET",    "path": "/session",                        "source": "api/routers/assessment.py", "func": "get_assessment_session"},
    ],

    # ────────── 教练层 (professional_agents) ──────────
    # 教练/督导操作、Agent管理、专业处方、反馈追踪
    "professional": [
        # agent_api.py — Agent核心操作 (教练使用)
        {"method": "POST",   "path": "/api/v1/agent/run",                       "source": "api/agent_api.py",          "func": "run_agent"},
        {"method": "GET",    "path": "/api/v1/agent/list",                      "source": "api/agent_api.py",          "func": "list_agents"},
        {"method": "GET",    "path": "/api/v1/agent/status",                    "source": "api/agent_api.py",          "func": "agent_status"},
        {"method": "GET",    "path": "/api/v1/agent/history",                   "source": "api/agent_api.py",          "func": "agent_history"},
        {"method": "GET",    "path": "/api/v1/agent/stats/{agent_id}",          "source": "api/agent_api.py",          "func": "agent_stats"},
        {"method": "POST",   "path": "/api/v1/agent/feedback",                  "source": "api/agent_api.py",          "func": "submit_feedback"},
        {"method": "GET",    "path": "/api/v1/agent/pending-reviews",           "source": "api/agent_api.py",          "func": "pending_reviews"},
        {"method": "POST",   "path": "/api/v1/agent/pending-reviews/inject",    "source": "api/agent_api.py",          "func": "inject_review"},
        {"method": "POST",   "path": "/api/v1/agent/events/inject",             "source": "api/agent_api.py",          "func": "inject_event"},

        # v14/routes.py — Agent处理/安全检查
        {"method": "POST",   "path": "/agent/process",                          "source": "api/v14/routes.py",         "func": "agent_process"},
        {"method": "POST",   "path": "/agent/safety-check",                     "source": "api/v14/routes.py",         "func": "agent_safety_check"},

        # miniprogram.py — Agent respond (教练侧)
        {"method": "POST",   "path": "/agent/respond",                          "source": "api/miniprogram.py",        "func": "agent_respond"},

        # coach_message_api.py — 教练消息
        {"method": "POST",   "path": "/api/v1/coach/messages",                  "source": "api/coach_message_api.py",  "func": "send_coach_message"},
        {"method": "GET",    "path": "/api/v1/coach/messages/{student_id}",     "source": "api/coach_message_api.py",  "func": "get_student_messages"},
        {"method": "GET",    "path": "/api/v1/coach/students-with-messages",    "source": "api/coach_message_api.py",  "func": "students_with_messages"},

        # expert_agent_api.py — 督导专家Agent管理
        {"method": "POST",   "path": "/api/v1/tenants/{tid}/my-agents",              "source": "api/expert_agent_api.py",  "func": "create_expert_agent"},
        {"method": "GET",    "path": "/api/v1/tenants/{tid}/my-agents",              "source": "api/expert_agent_api.py",  "func": "list_expert_agents"},
        {"method": "POST",   "path": "/api/v1/tenants/{tid}/my-agents/test-routing", "source": "api/expert_agent_api.py",  "func": "test_routing"},
        {"method": "PUT",    "path": "/api/v1/tenants/{tid}/my-agents/{aid}",        "source": "api/expert_agent_api.py",  "func": "update_expert_agent"},
        {"method": "DELETE", "path": "/api/v1/tenants/{tid}/my-agents/{aid}",        "source": "api/expert_agent_api.py",  "func": "delete_expert_agent"},
        {"method": "POST",   "path": "/api/v1/tenants/{tid}/my-agents/{aid}/toggle", "source": "api/expert_agent_api.py",  "func": "toggle_expert_agent"},

        # agent_template_api.py — Agent模板管理
        {"method": "GET",    "path": "/{agent_id}",                              "source": "api/agent_template_api.py", "func": "get_template"},
        {"method": "PUT",    "path": "/{agent_id}",                              "source": "api/agent_template_api.py", "func": "update_template"},
        {"method": "DELETE", "path": "/{agent_id}",                              "source": "api/agent_template_api.py", "func": "delete_template"},
        {"method": "POST",   "path": "/{agent_id}/clone",                        "source": "api/agent_template_api.py", "func": "clone_template"},
        {"method": "POST",   "path": "/{agent_id}/toggle",                       "source": "api/agent_template_api.py", "func": "toggle_template"},

        # agent_feedback_api.py — Agent反馈/指标
        {"method": "GET",    "path": "/growth/{agent_id}",                       "source": "api/agent_feedback_api.py", "func": "get_growth"},
        {"method": "GET",    "path": "/metrics/{agent_id}",                      "source": "api/agent_feedback_api.py", "func": "get_metrics"},
        {"method": "GET",    "path": "/prompt-versions/{agent_id}",              "source": "api/agent_feedback_api.py", "func": "get_prompt_versions"},

        # v14/disclosure_routes.py — 处方交付
        {"method": "GET",    "path": "/decision/{report_id}/patient-message",    "source": "api/v14/disclosure_routes.py", "func": "patient_message"},
        {"method": "GET",    "path": "/rewrite/stage-message/{ttm_stage}",       "source": "api/v14/disclosure_routes.py", "func": "rewrite_message"},

        # policy_api.py — Agent追踪
        {"method": "GET",    "path": "/traces/agent/{agent_id}/stats",           "source": "api/policy_api.py",         "func": "agent_trace_stats"},

        # ecosystem_v4_api.py — 阶段Agent分配
        {"method": "GET",    "path": "/course/agent-assignments/{stage}",        "source": "api/ecosystem_v4_api.py",   "func": "agent_assignments"},

        # rx_routes.py — Rx状态
        {"method": "GET",    "path": "/agents/status",                           "source": "behavior_rx/api/rx_routes.py", "func": "rx_agent_status"},
    ],

    # ────────── 网关层 (gateway) ──────────
    # 治理、跨层查询、用户收件箱
    "gateway": [
        # governance_api.py — Agent层治理
        {"method": "GET",    "path": "/agent-layer",                  "source": "api/governance_api.py",     "func": "get_agent_layer"},
        {"method": "GET",    "path": "/agent-layer/check/{agent_id}", "source": "api/governance_api.py",     "func": "check_agent_layer"},

        # advanced_rights_api.py — 能力查询
        {"method": "GET",    "path": "/agent-capabilities",           "source": "api/advanced_rights_api.py","func": "get_capabilities"},

        # coach_message_api.py — 用户侧消息（跨层）
        {"method": "GET",    "path": "/api/v1/messages/inbox",            "source": "api/coach_message_api.py", "func": "get_inbox"},
        {"method": "GET",    "path": "/api/v1/messages/unread-count",     "source": "api/coach_message_api.py", "func": "unread_count"},
        {"method": "POST",   "path": "/api/v1/messages/{mid}/read",      "source": "api/coach_message_api.py", "func": "mark_read"},
    ],

    # ────────── 废弃/Legacy ──────────
    "deprecated": [
        # v3 legacy
        {"method": "POST", "path": "/message",  "source": "v3/routers/chat.py",     "note": "v3 legacy, 已被chat_rest_api替代"},
        {"method": "GET",  "path": "/session",   "source": "v3/routers/assessment.py", "note": "v3 legacy"},
        # xingjian-agent 独立项目
        {"method": "POST",   "path": "/chat",               "source": "xingjian-agent/api/routes.py", "note": "独立Agent项目，非主服务"},
        {"method": "POST",   "path": "/session/reset-all",  "source": "xingjian-agent/api/routes.py", "note": "独立Agent项目"},
        {"method": "DELETE", "path": "/session/{session_id}","source": "xingjian-agent/api/routes.py", "note": "独立Agent项目"},
        # behavior_rx_v32_complete legacy
        {"method": "GET",  "path": "/agents/status", "source": "behavior_rx_v32_complete/behavior_rx/api/rx_routes.py", "note": "v32 legacy"},
    ],
}

# 源文件→层映射（用于move_imports）
SOURCE_FILE_LAYER = {
    "api/chat_rest_api.py":        "assistant",
    "api/miniprogram.py":          "mixed",     # 含用户层+教练层路由
    "api/trial_api.py":            "assistant",
    "api/routes.py":               "assistant",
    "api/routers/chat.py":         "assistant",
    "api/routers/assessment.py":   "assistant",

    "api/agent_api.py":            "professional",
    "api/v14/routes.py":           "professional",
    "api/coach_message_api.py":    "mixed",     # 教练发送+用户收件箱
    "api/expert_agent_api.py":     "professional",
    "api/agent_template_api.py":   "professional",
    "api/agent_feedback_api.py":   "professional",
    "api/v14/disclosure_routes.py":"professional",
    "api/policy_api.py":           "professional",
    "api/ecosystem_v4_api.py":     "professional",
    "behavior_rx/api/rx_routes.py":"professional",

    "api/governance_api.py":       "gateway",
    "api/advanced_rights_api.py":  "gateway",

    "core/agents/router.py":       "shared",    # 路由器核心，两层共用
}


# ═══════════════════════════════════════════════════════════
# 显示映射表
# ═══════════════════════════════════════════════════════════

def show():
    print(f"\n{'═'*70}")
    print(f"  V4.1 路由迁移映射 — 68条路由分层")
    print(f"{'═'*70}\n")

    totals = {}
    for layer, routes in ROUTE_MAP.items():
        totals[layer] = len(routes)
        icon = {"assistant": "🟢", "professional": "🔵", "gateway": "🟡", "deprecated": "⚫"}[layer]
        label = {
            "assistant": "用户层 (assistant_agents/)",
            "professional": "教练层 (professional_agents/)",
            "gateway": "网关层 (gateway/)",
            "deprecated": "废弃/Legacy",
        }[layer]
        print(f"  {icon} {label} — {len(routes)}条路由")
        print(f"  {'─'*66}")
        for r in routes:
            src = r["source"].split("/")[-1]
            note = r.get("note", "")
            extra = f"  ({note})" if note else ""
            print(f"    {r['method']:6s} {r['path']:50s} ← {src}{extra}")
        print()

    print(f"  合计: {sum(totals.values())}条")
    for layer, count in totals.items():
        print(f"    {layer}: {count}")

    # 源文件影响
    print(f"\n  源文件影响:")
    for src, layer in sorted(SOURCE_FILE_LAYER.items()):
        tag = {"assistant": "→ 用户层", "professional": "→ 教练层",
               "gateway": "→ 网关", "mixed": "→ 需拆分", "shared": "→ 共享"}[layer]
        print(f"    {src:45s} {tag}")


# ═══════════════════════════════════════════════════════════
# 生成路由桥接代码 — 旧路径→新路径兼容
# ═══════════════════════════════════════════════════════════

def bridge():
    print(f"\n生成路由桥接代码...\n")

    code = '''"""
V4.1 路由桥接 — 旧路径兼容

在迁移过渡期，旧路径自动转发到新双层路由。
迁移完成后删除此文件。

用法: 在 main.py 中 app.include_router(bridge_router)
"""
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

bridge_router = APIRouter(tags=["v41_bridge"])


# ── 用户层: /chat/* → /v1/assistant/chat/* ──

@bridge_router.api_route("/chat", methods=["POST"], deprecated=True)
@bridge_router.api_route("/chat/stream", methods=["POST"], deprecated=True)
async def bridge_chat_to_assistant(request: Request):
    """旧对话入口 → 新用户层"""
    new_path = request.url.path.replace("/chat", "/v1/assistant/chat", 1)
    return RedirectResponse(url=new_path, status_code=307)


@bridge_router.api_route("/sessions", methods=["GET", "POST"], deprecated=True)
@bridge_router.api_route("/sessions/{session_id}", methods=["DELETE"], deprecated=True)
@bridge_router.api_route("/sessions/{session_id}/messages", methods=["GET", "POST"], deprecated=True)
async def bridge_sessions_to_assistant(request: Request):
    """旧会话管理 → 新用户层"""
    new_path = "/v1/assistant" + request.url.path
    return RedirectResponse(url=new_path, status_code=307)


# ── 教练层: /api/v1/agent/* → /v1/professional/agent/* ──

@bridge_router.api_route("/api/v1/agent/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], deprecated=True)
async def bridge_agent_to_professional(request: Request, path: str):
    """旧Agent API → 新教练层"""
    new_path = f"/v1/professional/agent/{path}"
    return RedirectResponse(url=new_path, status_code=307)


@bridge_router.api_route("/api/v1/coach/{path:path}", methods=["GET", "POST"], deprecated=True)
async def bridge_coach_to_professional(request: Request, path: str):
    """旧教练API → 新教练层"""
    new_path = f"/v1/professional/coach/{path}"
    return RedirectResponse(url=new_path, status_code=307)
'''
    out = Path("gateway/bridge.py")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(code)
    print(f"  ✅ {out} (路由桥接)")
    return code


# ═══════════════════════════════════════════════════════════
# 生成 main.py 注册代码
# ═══════════════════════════════════════════════════════════

def register():
    print(f"\n生成 main.py 路由注册代码...\n")

    code = '''
# ═══════════════════════════════════════════════════════════
# V4.1 双层Agent路由注册 — 添加到 main.py 或 app_factory
# ═══════════════════════════════════════════════════════════

# ── Step 1: 导入双层路由 ──
from assistant_agents.router import router as assistant_router
from professional_agents.router import router as professional_router
from gateway.router import router as gateway_router
from gateway.bridge import bridge_router  # 兼容层（过渡期）

# ── Step 2: 注册到 FastAPI app ──
# 用户层 — 前缀 /v1/assistant
app.include_router(
    assistant_router,
    prefix="/v1/assistant",
    tags=["assistant_agents"],
)

# 教练层 — 前缀 /v1/professional
app.include_router(
    professional_router,
    prefix="/v1/professional",
    tags=["professional_agents"],
)

# 跨层网关 — 前缀 /v1/gateway
app.include_router(
    gateway_router,
    prefix="/v1/gateway",
    tags=["cross_layer_gateway"],
)

# 兼容桥接 — 旧路径→新路径（过渡期，迁移完成后删除）
app.include_router(bridge_router)

# ── Step 3: 保留现有路由（避免breaking change）──
# 现有的 api/agent_api.py, api/chat_rest_api.py 等路由
# 暂时保留，bridge_router 会将旧路径转发到新路径。
# Week 4 灰度验证后，逐步删除旧路由文件。

# ═══════════════════════════════════════════════════════════
# 验证脚本 — 确认双层路由已注册
# ═══════════════════════════════════════════════════════════
#
# 启动服务后运行:
#   curl http://localhost:8000/v1/assistant/agents    # 用户层Agent列表
#   curl http://localhost:8000/v1/professional/agents # 教练层Agent列表
#   curl http://localhost:8000/v1/gateway/...         # 跨层网关
#
# 兼容验证:
#   curl http://localhost:8000/api/v1/agent/list      # 旧路径→自动转发
#   curl http://localhost:8000/sessions                # 旧路径→自动转发
'''
    out = Path("_v41_register_snippet.py")
    out.write_text(code)
    print(f"  ✅ {out}")
    print(f"\n  将上述代码复制到你的 main.py 中。")
    print(f"  现有路由不要删除，bridge会处理兼容。")
    return code


# ═══════════════════════════════════════════════════════════
# 执行迁移 — 在源文件中添加层标记和导入重定向
# ═══════════════════════════════════════════════════════════

def execute(app_dir: str):
    """把现有API文件中的路由函数复制到双层结构"""
    app_path = Path(app_dir)

    print(f"\n{'═'*60}")
    print(f"  V4.1 迁移执行")
    print(f"{'═'*60}\n")

    # 拆分 miniprogram.py（mixed文件示例）
    print("[1] 拆分 mixed 文件")
    for src_file, layer in SOURCE_FILE_LAYER.items():
        if layer != "mixed":
            continue
        fpath = app_path / src_file
        if not fpath.exists():
            print(f"  ⏭  {src_file} 不存在")
            continue

        content = fpath.read_text(errors="ignore")
        print(f"  📄 {src_file}: ", end="")

        # 统计路由
        assistant_count = 0
        professional_count = 0
        for routes in [ROUTE_MAP["assistant"], ROUTE_MAP["professional"], ROUTE_MAP["gateway"]]:
            for r in routes:
                if r["source"] == src_file:
                    if r in ROUTE_MAP["assistant"]:
                        assistant_count += 1
                    elif r in ROUTE_MAP["professional"]:
                        professional_count += 1

        print(f"{assistant_count}条用户层 + {professional_count}条教练层")

        # 在文件头部添加层归属注释
        if "# V4.1 LAYER:" not in content:
            header = f"""
# ═══ V4.1 双层分离标记 ═══
# 此文件包含混合路由，计划拆分到:
#   用户层路由 → assistant_agents/router.py
#   教练层路由 → professional_agents/router.py
# 拆分完成后此文件废弃
# V4.1 LAYER: mixed
"""
            # 不写入，仅提示
            print(f"    建议在文件头添加分层标记")

    # 为每个纯层文件添加标记
    print(f"\n[2] 标记纯层文件")
    for src_file, layer in SOURCE_FILE_LAYER.items():
        if layer in ("mixed", "shared"):
            continue
        fpath = app_path / src_file
        if not fpath.exists():
            continue
        label = {"assistant": "用户层", "professional": "教练层", "gateway": "网关层"}[layer]
        print(f"  {label} ← {src_file}")

    # 生成桥接
    print(f"\n[3] 生成桥接代码")
    bridge()

    # 生成注册代码
    print(f"\n[4] 生成注册代码")
    register()

    # 下一步
    print(f"""
{'═'*60}
  Week 1 剩余工作
{'═'*60}

  1. 把 _v41_register_snippet.py 的内容合并到 main.py
  2. 在 assistant_agents/router.py 中实现用户层路由:
     - 从 api/chat_rest_api.py 移入 5 个会话端点
     - 从 api/miniprogram.py 移入 7 个对话端点
     - 从 api/trial_api.py 移入 2 个试用端点

  3. 在 professional_agents/router.py 中实现教练层路由:
     - 从 api/agent_api.py 移入 9 个Agent操作端点
     - 从 api/coach_message_api.py 移入 3 个教练消息端点
     - 从 api/expert_agent_api.py 移入 6 个督导Agent端点

  4. 启动服务验证:
     curl http://localhost:8000/v1/assistant/agents
     curl http://localhost:8000/v1/professional/agents

  5. 运行冒烟测试:
     python xingjian_smoke/run.py all

  6. 提交:
     git add -A
     git commit -m "V4.1 Week1: 路由迁移映射 + 桥接 + 双层注册"
""")


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"
    if cmd == "show":
        show()
    elif cmd == "bridge":
        bridge()
    elif cmd == "register":
        register()
    elif cmd == "execute":
        target = sys.argv[2] if len(sys.argv) > 2 else "."
        execute(target)
    else:
        print(__doc__)
