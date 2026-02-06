# CoachCopilot 后端路由 (生产 8002)
# POST /api/v1/copilot/analyze — 与沙盒相同的分析逻辑
import os
import json
from fastapi import APIRouter, Body
from loguru import logger

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
