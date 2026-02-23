# CoachCopilot 后端路由 (生产 8002)
# POST /api/v1/copilot/analyze — 与沙盒相同的分析逻辑
# POST /api/v1/copilot/generate-prescription — AI行为处方生成
import os
import json
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session
from loguru import logger

from core.database import get_db
from api.dependencies import require_coach_or_admin

router = APIRouter(tags=["copilot"])

# 加载 actions_master.json
_resource_dir = os.path.join(os.path.dirname(__file__), "..", "..", "services", "logic_engine", "resource")
_actions_path = os.path.normpath(os.path.join(_resource_dir, "actions_master.json"))

try:
    with open(_actions_path, "r", encoding="utf-8") as f:
        ACTIONS_MASTER = json.load(f)
    logger.info(f"[copilot] actions_master 加载成功: {_actions_path}")
except FileNotFoundError:
    ACTIONS_MASTER = {}
    logger.warning(f"[copilot] actions_master 未找到: {_actions_path}")

# 关键词母库 (与沙盒一致)
RULES_LIBRARY = {
    "T_EMO_EAT":       ["薯片", "后悔", "没忍住", "宵夜"],
    "T_RESISTANCE":     ["别跟我提", "活得累", "怎么了"],
    "T_ACTION_WILL":    ["打算", "开始", "行吗"],
    "T_HOPELESS":       ["没希望", "这辈子", "放弃"],
    "T_STRESS":         ["老板", "骂", "压力", "加班"],
}

TAG_META = {
    "T_EMO_EAT":    {"label": "情绪化进食",   "risk": "L2", "priority": "Medium",
                     "patient_msg": "能感受到你的自责，偶尔破戒不代表失败，我们来看看怎么调整。",
                     "coach_alert": "情绪化进食信号，建议关注饮食日记和情绪触发因素。"},
    "T_RESISTANCE": {"label": "抵触/防御心态", "risk": "L3", "priority": "High",
                     "patient_msg": "理解你的感受，改变确实不容易。我们按你的节奏来，不勉强。",
                     "coach_alert": "防御型抵触，避免直接说教，采用动机式访谈。"},
    "T_ACTION_WILL":{"label": "行动意愿萌芽", "risk": "L1", "priority": "Low",
                     "patient_msg": "这个想法很棒！我们来制定一个具体可执行的小目标吧。",
                     "coach_alert": "行动意愿出现，适合推送具体行为处方。"},
    "T_HOPELESS":   {"label": "绝望感/习得性无助","risk": "L3", "priority": "High",
                     "patient_msg": "听起来你现在很沮丧。每一步小进步都有意义，我们一起面对。",
                     "coach_alert": "高风险: 绝望情绪，需优先人工跟进评估心理状态。"},
    "T_STRESS":     {"label": "职场压力触发", "risk": "L2", "priority": "Medium",
                     "patient_msg": "工作压力确实会影响健康管理，我们看看怎么在高压下保持节奏。",
                     "coach_alert": "职场压力触发，关注是否引发代偿性行为（暴食/失眠）。"},
}


def match_triggers(text: str) -> list:
    """关键词匹配母库规则"""
    hits = []
    for tag, keywords in RULES_LIBRARY.items():
        if any(k in text for k in keywords):
            hits.append(tag)
    return hits


@router.post("/test/simulate-chat")
@router.post("/copilot/analyze")
async def copilot_analyze(
    uid: str = Body(...),
    message: str = Body(...),
    context: dict = Body(default={})
):
    """
    CoachCopilot 分析端点 (生产环境)
    Layer 1: 关键词匹配
    Layer 2: BehaviorEngine 条件引擎 (可选)
    返回与沙盒 simulate-chat 相同的响应格式
    """
    # Layer 1: 关键词匹配
    kw_tags = match_triggers(message)

    # Layer 2: 尝试调用 BehaviorEngine
    engine_tags = []
    try:
        from services.logic_engine.behavior_engine import BehaviorEngine
        engine = BehaviorEngine(
            config_path=os.path.join(
                os.path.dirname(__file__), "..", "..", "configs", "behavior", "behavior_rules.json"
            )
        )
        snippet = {"text": message, "source": "copilot"}
        user_context = {
            "stage": context.get("stage", "S1_PRE_CONTEMPLATION"),
            "baps": context.get("baps", {}),
            "user_id": uid,
        }
        engine_result = engine.evaluate_state(
            user_id=uid,
            user_context=user_context,
            new_snippet=snippet,
        )
        if engine_result:
            trigger, action = engine_result
            engine_tags = [trigger.id]
    except Exception as e:
        logger.debug(f"[copilot] BehaviorEngine 不可用，仅使用关键词匹配: {e}")

    # 合并去重
    all_tags = list(dict.fromkeys(kw_tags + engine_tags))

    # 构建分角色输出
    patient_messages = []
    coach_alerts = []
    analysis_details = []

    for tag in all_tags:
        meta = TAG_META.get(tag, {})
        patient_messages.append(meta.get("patient_msg", ""))
        coach_alerts.append({
            "tag": tag,
            "label": meta.get("label", tag),
            "risk": meta.get("risk", "L1"),
            "priority": meta.get("priority", "Low"),
            "alert": meta.get("coach_alert", ""),
        })
        analysis_details.append({
            "tag": tag,
            "label": meta.get("label", tag),
            "source": "keyword" if tag in kw_tags else "engine",
        })

    # 从动作母库构建教练处方
    prescriptions = []
    for tag in all_tags:
        action = ACTIONS_MASTER.get(tag, {})
        if action:
            prescriptions.append({
                "risk_level": action.get("risk", "L1"),
                "instruction": action.get("coach_directive", "常规观察"),
                "suggested_tool": action.get("tool_id", "GENERAL_CHAT"),
                "tool_props": action.get("tool_props", {}),
            })

    if not all_tags:
        patient_messages = ["一切正常，继续加油！"]
        coach_alerts = [{"alert": None}]
        prescriptions = []

    return {
        "status": "analyzed",
        "source": "copilot_live",
        "analysis": analysis_details or [{"matched": False}],
        "triggered_tags": all_tags,
        "outputs": {
            "to_patient": {"content": " ".join(patient_messages)},
            "to_coach": prescriptions,
        }
    }


@router.post("/copilot/suggested-actions")
async def copilot_suggested_actions(
    stage: str = Body(default=""),
    risk_level: str = Body(default=""),
    recent_tags: list = Body(default=[]),
):
    """
    根据当前阶段 / 风险 / 近期标签推荐教练可用动作
    """
    suggestions = []
    # 基于 risk_level 推荐
    if risk_level in ("L3", "L4", "R3", "R4"):
        suggestions.append({
            "id": "urgent_followup",
            "label": "紧急跟进",
            "description": "高风险学员需要立即人工跟进",
            "tool": "COACH_CALL",
            "priority": 1,
            "context_match": ["high_risk"],
        })
    # 基于近期标签推荐
    for tag in recent_tags:
        meta = TAG_META.get(tag, {})
        if meta:
            suggestions.append({
                "id": f"action_{tag.lower()}",
                "label": meta.get("label", tag),
                "description": meta.get("coach_alert", ""),
                "tool": "GENERAL_CHAT",
                "priority": 2,
                "context_match": [tag],
            })
    # 通用建议
    if not suggestions:
        suggestions.append({
            "id": "routine_check",
            "label": "日常关怀",
            "description": "发送日常关怀消息，保持连接",
            "tool": "GENERAL_CHAT",
            "priority": 3,
            "context_match": ["routine"],
        })
    return {"actions": suggestions}


@router.get("/copilot/prescriptions/{coach_id}")
async def copilot_prescriptions(
    coach_id: str,
    page: int = 1,
    pageSize: int = 10,
    startDate: str = "",
    endDate: str = "",
    riskLevel: str = "",
):
    """获取教练历史处方列表"""
    return {
        "items": [],
        "total": 0,
        "page": page,
        "pageSize": pageSize,
    }


@router.post("/copilot/prescriptions/{prescription_id}/action")
async def copilot_prescription_action(
    prescription_id: str,
    action: dict = Body(default={}),
):
    """提交处方动作"""
    return {"message": "操作已记录", "prescription_id": prescription_id}


@router.post("/copilot/chat-sync")
async def copilot_chat_sync(
    message: str = Body(...),
    user_id: str = Body(default="anonymous"),
):
    """
    同步聊天端点 — 教练跟进建议生成
    使用 UnifiedLLMClient 生成回复
    """
    try:
        from core.llm_client import get_llm_client
        client = get_llm_client()
        result = client.chat(
            system="你是一位专业的行为健康教练助手，帮助教练生成跟进消息。请直接输出消息内容，语气温暖专业，100字以内。",
            user=message,
            temperature=0.7,
            timeout=30.0,
        )
        if result.success:
            return {"reply": result.content}
        else:
            logger.warning(f"[copilot] chat-sync LLM调用失败: {result.error}")
            return {"reply": "AI暂时不可用，请手动输入跟进消息。"}
    except Exception as e:
        logger.error(f"[copilot] chat-sync 异常: {e}")
        return {"reply": "AI暂时不可用，请手动输入跟进消息。"}


@router.post("/copilot/generate-prescription")
def generate_prescription(
    student_id: int = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    """
    AI 行为处方生成 — 一次调用填充教练工作台学员详情全部 5 个标签页

    请求: {"student_id": 3}
    返回: {diagnosis, prescription, ai_suggestions, health_summary, intervention_plan, meta}
    """
    from core.copilot_prescription_service import CopilotPrescriptionService

    service = CopilotPrescriptionService()
    return service.generate_prescription(db, student_id, current_user.id)
