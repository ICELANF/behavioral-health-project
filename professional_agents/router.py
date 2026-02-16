"""
Professional Agent API路由

前缀: /v1/agent
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# 按实际路径调整
# from app.core.auth import get_current_user, requires_role
# from app.core.database import get_db

router = APIRouter(prefix="/v1/agent", tags=["professional_agents"])


@router.get("/agents")
async def list_agents():
    """列出可用Agent"""
    from .registry import list_agents
    return {"agents": list_agents()}


@router.post("/chat")
async def chat(
    agent_name: str,
    message: str,
    # current_user = Depends(get_current_user),
    # db: AsyncSession = Depends(get_db),
):
    """与Agent对话"""
    from .registry import get_agent
    try:
        agent = get_agent(agent_name)
    except (ValueError, ImportError) as e:
        raise HTTPException(404, str(e))

    # 直接调用 agent.run; 用户上下文由 MasterAgent 层注入
    result = await agent.run(message)
    return result


@router.get("/agents/{agent_name}")
async def get_agent_info(agent_name: str):
    """获取Agent详情"""
    from .registry import REGISTRY
    if agent_name not in REGISTRY:
        raise HTTPException(404, f"Agent不存在: {agent_name}")
    return {"name": agent_name, **REGISTRY[agent_name]}
