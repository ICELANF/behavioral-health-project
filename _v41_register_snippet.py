
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
