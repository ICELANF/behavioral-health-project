"""
rx_response_mapper.py — RxPrescriptionDTO → Copilot JSON 映射

将 BehaviorRx 引擎的结构化 RxPrescriptionDTO 映射为现有
CopilotPrescriptionService 返回的 6-key JSON 格式, 保持
admin-portal CoachHome.vue 5标签页完全向后兼容。
"""
import logging
from datetime import datetime
from typing import Any, Dict

from behavior_rx.core.rx_schemas import RxPrescriptionDTO

logger = logging.getLogger(__name__)

# 枚举 → 中文显示
_STRATEGY_ZH = {
    "consciousness_raising": "意识唤醒",
    "dramatic_relief": "戏剧性解脱",
    "self_reevaluation": "自我再评价",
    "decisional_balance": "决策平衡",
    "cognitive_restructuring": "认知重构",
    "self_liberation": "自我解放",
    "stimulus_control": "刺激控制",
    "contingency_management": "强化管理",
    "habit_stacking": "习惯叠加",
    "systematic_desensitization": "系统脱敏",
    "relapse_prevention": "复发预防",
    "self_monitoring": "自我监控",
}

_INTENSITY_ZH = {
    "minimal": "极低", "low": "低", "moderate": "中等",
    "high": "高", "intensive": "强化",
}

_TTM_PHASE_MAP = {
    0: "认知唤醒", 1: "认知唤醒", 2: "动机激发",
    3: "行为塑造", 4: "习惯强化", 5: "习惯强化", 6: "习惯强化",
}


def rx_dto_to_copilot_json(
    dto: RxPrescriptionDTO,
    student_id: int,
    coach_id: int,
) -> Dict[str, Any]:
    """
    将 RxPrescriptionDTO 映射为 CopilotPrescriptionService 的 6-key 格式。

    返回结构与 copilot_prescription_service.generate_prescription() 完全一致:
    {diagnosis, prescription, ai_suggestions, health_summary, intervention_plan, meta}
    """
    strategy_str = dto.strategy_type.value if hasattr(dto.strategy_type, "value") else str(dto.strategy_type)
    intensity_str = dto.intensity.value if hasattr(dto.intensity, "value") else str(dto.intensity)
    comm_str = dto.communication_style.value if hasattr(dto.communication_style, "value") else str(dto.communication_style)

    # --- diagnosis ---
    capacity_pct = int(dto.domain_context.get("capacity_pct", dto.confidence * 100))
    diagnosis = {
        "spiScore": capacity_pct,
        "successRate": int(dto.confidence * 100),
        "sixReasons": _build_six_reasons(dto),
        "problem": dto.reasoning.split("。")[0] if dto.reasoning else "需要关注行为改变",
        "difficulty": _intensity_to_difficulty(intensity_str),
        "purpose": f"通过{_STRATEGY_ZH.get(strategy_str, strategy_str)}策略促进行为改变",
        "evidence": [{"tier": "T3", "label": "专家共识"}],
        "interventionAlert": "",
    }

    # --- prescription ---
    phase_name = _TTM_PHASE_MAP.get(dto.ttm_stage, "行为塑造")
    prescription = {
        "phase": {
            "current": phase_name,
            "week": 1,
            "total": 12,
        },
        "phaseTags": [
            {"label": "认知唤醒", "done": dto.ttm_stage >= 2, "active": dto.ttm_stage < 2},
            {"label": "动机激发", "done": dto.ttm_stage >= 3, "active": dto.ttm_stage == 2},
            {"label": "行为塑造", "done": dto.ttm_stage >= 4, "active": dto.ttm_stage == 3},
            {"label": "习惯强化", "done": dto.ttm_stage >= 6, "active": dto.ttm_stage >= 4},
        ],
        "targetBehaviors": [
            {
                "name": dto.goal_behavior,
                "progress": 0,
                "target": ma.action if dto.micro_actions else dto.goal_behavior,
                "currentDays": 0,
            }
            for ma in (dto.micro_actions[:3] if dto.micro_actions else [{"action": dto.goal_behavior}])
        ] or [{"name": dto.goal_behavior, "progress": 0, "target": dto.goal_behavior, "currentDays": 0}],
        "strategies": _build_strategy_tags(dto),
    }

    # --- ai_suggestions ---
    ai_suggestions = []
    for i, ma in enumerate(dto.micro_actions[:5]):
        ai_suggestions.append({
            "id": f"sug_{i+1}",
            "title": ma.action,
            "content": f"触发: {ma.trigger} | 频率: {ma.frequency} | 时长: {ma.duration_min}分钟",
            "type": "behavior",
            "priority": "high" if ma.difficulty < 0.4 else "medium",
        })
    if not ai_suggestions:
        ai_suggestions.append({
            "id": "sug_1",
            "title": dto.goal_behavior,
            "content": dto.reasoning or "基于评估结果的个性化建议",
            "type": "behavior",
            "priority": "high",
        })

    # --- health_summary ---
    health_summary = {
        "fastingGlucose": 0,
        "postprandialGlucose": 0,
        "sleepHours": 0,
        "exerciseMinutes": 0,
        "weight": 0,
        "heartRate": 0,
        "highlights": [],
    }

    # --- intervention_plan ---
    intervention_plan = {
        "name": f"{phase_name} · {_INTENSITY_ZH.get(intensity_str, intensity_str)}强度",
        "description": dto.reasoning or "基于三维评估的个性化干预方案",
        "domains": list(dto.domain_context.get("domains", [])) or ["general"],
        "tone": _comm_to_tone(comm_str),
        "scripts": {
            "opening": f"您好！根据您的评估结果，我们为您制定了{_INTENSITY_ZH.get(intensity_str, '适度')}强度的行为改变方案。",
            "motivation": f"当前策略重点: {_STRATEGY_ZH.get(strategy_str, strategy_str)}",
            "closing": "我们会持续跟进您的进展，有任何问题随时联系教练。",
        },
    }

    # --- meta ---
    meta = {
        "source": "behavior_rx",
        "llm_used": False,
        "has_real_data": {
            "profile": True,
            "assessment": True,
            "glucose": False,
            "sleep": False,
            "activity": False,
            "vitals": False,
            "micro_actions": bool(dto.micro_actions),
        },
        "student_id": student_id,
        "coach_id": coach_id,
        "generated_at": datetime.utcnow().isoformat(),
        "agent_type": dto.agent_type.value if hasattr(dto.agent_type, "value") else str(dto.agent_type),
        "confidence": dto.confidence,
        "rx_id": str(dto.rx_id) if dto.rx_id else None,
        "evidence_tier": getattr(dto, "evidence_tier", "T3"),
    }

    return {
        "diagnosis": diagnosis,
        "prescription": prescription,
        "ai_suggestions": ai_suggestions,
        "health_summary": health_summary,
        "intervention_plan": intervention_plan,
        "meta": meta,
    }


# ── helpers ──

def _build_six_reasons(dto: RxPrescriptionDTO) -> list:
    """构造 CAPACITY 六因子雷达图数据 (从 domain_context 或默认)."""
    dc = dto.domain_context or {}
    cap = dc.get("capacity_factors", {})
    factors = [
        ("信心", "C"), ("能力", "A"), ("感知", "P"),
        ("资源", "A2"), ("兴趣", "I"), ("时间", "T"),
    ]
    result = []
    for name, key in factors:
        score = cap.get(key, int(dto.confidence * 60 + 20))
        result.append({
            "name": name, "score": int(score), "max": 100,
            "isWeak": int(score) < 50,
        })
    return result


def _build_strategy_tags(dto: RxPrescriptionDTO) -> list:
    s = dto.strategy_type.value if hasattr(dto.strategy_type, "value") else str(dto.strategy_type)
    tags = [{"label": _STRATEGY_ZH.get(s, s), "type": "success"}]
    for ss in (dto.secondary_strategies or [])[:3]:
        sv = ss.value if hasattr(ss, "value") else str(ss)
        tags.append({"label": _STRATEGY_ZH.get(sv, sv), "type": "processing"})
    return tags


def _intensity_to_difficulty(intensity: str) -> int:
    return {"minimal": 1, "low": 2, "moderate": 3, "high": 4, "intensive": 5}.get(intensity, 3)


def _comm_to_tone(comm: str) -> str:
    return {
        "empathetic": "gentle_accepting",
        "data_driven": "structured_analytical",
        "challenge": "encouraging_practical",
        "social_proof": "encouraging_practical",
        "exploratory": "gentle_accepting",
        "neutral": "gentle_accepting",
    }.get(comm, "gentle_accepting")
