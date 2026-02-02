from fastapi import APIRouter, HTTPException
from core.decision_core import DecisionCore
from agents.snapshot_factory import SnapshotFactory
from agents.base_agent import BaseAgent

router = APIRouter()
decision_core = DecisionCore()
snapshot_factory = SnapshotFactory()
agent_gateway = BaseAgent(agent_id="gateway_001")

@router.post("/device/cgm/sync")
async def handle_cgm_sync(payload: dict):
    try:
        # 1. 穿透至决策中枢
        decision = decision_core.evaluate_trigger(payload)
        
        # 2. 生成隔离指令快照
        snapshot = snapshot_factory.build(decision)
        
        # 3. 渲染系统提示词
        system_prompt = agent_gateway.build_system_prompt(snapshot)
        
        return {
            "status": "processed",
            "decision_id": decision.decision_id,
            "agent": decision.primary_agent,
            "risk": decision.risk_level,
            "prompt_package": {
                "system_message": system_prompt,
                "user_query": f"我现在的数据是 {payload.get('value')}，该怎么办？"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))