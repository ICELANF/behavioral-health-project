from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel

class UserContextSnapshot(BaseModel):
    user_name: str
    current_stage: Literal["precontemplation", "contemplation", "preparation", "action", "maintenance"]
    key_barrier: str

class AgentInstructionSnapshot(BaseModel):
    snapshot_id: str
    decision_id: str
    issued_at: datetime
    agent_role: str
    user_context: UserContextSnapshot
    trigger_type: Optional[str]
    action_guidelines: List[str]
    allowed_output_types: List[str]
    output_constraints: List[str]

class BaseAgent:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    def build_system_prompt(self, snapshot: AgentInstructionSnapshot) -> str:
        return f"""
# Role
{snapshot.agent_role}

# User State
- Name: {snapshot.user_context.user_name}
- Stage: {snapshot.user_context.current_stage}
- Focus Barrier: {snapshot.user_context.key_barrier}

# Trigger
{snapshot.trigger_type or "Routine check-in"}

# Allowed Actions
{chr(10).join([f"- {a}" for a in snapshot.allowed_output_types])}

# Action Guidelines
{chr(10).join([f"- {g}" for g in snapshot.action_guidelines])}

# Output Constraints
{chr(10).join([f"- {c}" for c in snapshot.output_constraints])}
""".strip()