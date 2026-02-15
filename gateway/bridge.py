# -*- coding: utf-8 -*-
"""
V4.1 路由桥接 — 旧路径兼容

在迁移过渡期，旧路径自动转发到新双层路由。
迁移完成后删除此文件。

用法: 在 main.py 中 app.include_router(bridge_router)
"""
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

bridge_router = APIRouter(tags=["v41_bridge"])


# -- 用户层: /chat/* -> /v1/assistant/chat/* --

@bridge_router.api_route("/chat", methods=["POST"], deprecated=True)
@bridge_router.api_route("/chat/stream", methods=["POST"], deprecated=True)
async def bridge_chat_to_assistant(request: Request):
    """旧对话入口 -> 新用户层"""
    new_path = request.url.path.replace("/chat", "/v1/assistant/chat", 1)
    return RedirectResponse(url=new_path, status_code=307)


@bridge_router.api_route("/sessions", methods=["GET", "POST"], deprecated=True)
@bridge_router.api_route("/sessions/{session_id}", methods=["DELETE"], deprecated=True)
@bridge_router.api_route("/sessions/{session_id}/messages", methods=["GET", "POST"], deprecated=True)
async def bridge_sessions_to_assistant(request: Request):
    """旧会话管理 -> 新用户层"""
    new_path = "/v1/assistant" + request.url.path
    return RedirectResponse(url=new_path, status_code=307)


# -- 教练层: /api/v1/agent/* -> /v1/professional/agent/* --

@bridge_router.api_route("/api/v1/agent/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], deprecated=True)
async def bridge_agent_to_professional(request: Request, path: str):
    """旧Agent API -> 新教练层"""
    new_path = f"/v1/professional/agent/{path}"
    return RedirectResponse(url=new_path, status_code=307)


@bridge_router.api_route("/api/v1/coach/{path:path}", methods=["GET", "POST"], deprecated=True)
async def bridge_coach_to_professional(request: Request, path: str):
    """旧教练API -> 新教练层"""
    new_path = f"/v1/professional/coach/{path}"
    return RedirectResponse(url=new_path, status_code=307)
