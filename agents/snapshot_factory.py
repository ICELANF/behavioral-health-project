import uuid
from datetime import datetime
from core.decision_models import DecisionOutput, AgentRoute
from agents.base_agent import AgentInstructionSnapshot, UserContextSnapshot

class SnapshotFactory:
    ACTION_LIB = {
        "validate_emotion": "使用共情技术确认用户当下的焦虑或阻抗情绪",
        "affirm_autonomy": "强调用户拥有对健康决策的绝对自主权",
        "provide_tip": "给出当前场景下的一个微习惯建议",
        "safety_alert": "明确提示生理数值异常，建议立即停止当前活动"
    }

    def build(self, decision: DecisionOutput) -> AgentInstructionSnapshot:
        guidelines = [self.ACTION_LIB.get(act, act) for act in decision.required_actions]
        role_map = {
            AgentRoute.MOTIVATION: "资深健康动机教练（动机访谈 MI）",
            AgentRoute.COMPANION: "健康陪伴伙伴（专注行为执行）",
            AgentRoute.MEDICAL: "医疗干预专家（风险控制预警）"
        }

        return AgentInstructionSnapshot(
            snapshot_id=str(uuid.uuid4()),
            decision_id=decision.decision_id,
            issued_at=datetime.utcnow(),
            agent_role=role_map.get(decision.primary_agent, "健康助手"),
            user_context=UserContextSnapshot(**decision.context_snapshot),
            trigger_type=decision.trigger_type,
            action_guidelines=guidelines,
            allowed_output_types=decision.required_actions,
            output_constraints=["不超过100字", "禁止医疗诊断", "语气亲和非评判"]
        )