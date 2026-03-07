# -*- coding: utf-8 -*-
"""
同道者关系 API

同道者关系管理、统计查询、管理端查看
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from loguru import logger

from core.database import get_db
from api.dependencies import get_current_user, require_admin, require_coach_or_admin
from core.models import User, CompanionRelation, CompanionStatus

router = APIRouter(prefix="/api/v1/companions", tags=["同道者关系"])

# 角色→等级映射
_ROLE_LEVELS = {
    "observer": 1, "grower": 2, "sharer": 3, "coach": 4,
    "promoter": 5, "supervisor": 5, "master": 6, "admin": 99,
}


def _require_grower_or_above(user: User):
    """写操作需要 Grower(L2) 及以上角色"""
    role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
    level = _ROLE_LEVELS.get(role_str.lower(), 0)
    if level < 2:
        raise HTTPException(403, "需要成长者及以上角色才能执行此操作")


@router.get("/my-mentees")
def get_my_mentees(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我带教的同道者列表"""
    q = db.query(CompanionRelation).filter(
        CompanionRelation.mentor_id == current_user.id
    )
    if status:
        q = q.filter(CompanionRelation.status == status)
    q = q.order_by(CompanionRelation.started_at.desc())

    relations = q.all()
    result = []
    for cr in relations:
        mentee = db.query(User).filter(User.id == cr.mentee_id).first()
        result.append({
            "id": str(cr.id),
            "mentee_id": cr.mentee_id,
            "mentee_name": mentee.username if mentee else None,
            "mentee_current_role": mentee.role.value if mentee and hasattr(mentee.role, 'value') else (str(mentee.role) if mentee else None),
            "mentor_role": cr.mentor_role,
            "mentee_role": cr.mentee_role,
            "status": cr.status,
            "quality_score": float(cr.quality_score) if cr.quality_score else None,
            "started_at": str(cr.started_at) if cr.started_at else None,
            "graduated_at": str(cr.graduated_at) if cr.graduated_at else None,
            "notes": cr.notes,
        })
    return result


@router.get("/my-mentors")
def get_my_mentors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我的导师列表"""
    relations = db.query(CompanionRelation).filter(
        CompanionRelation.mentee_id == current_user.id
    ).order_by(CompanionRelation.started_at.desc()).all()

    result = []
    for cr in relations:
        mentor = db.query(User).filter(User.id == cr.mentor_id).first()
        result.append({
            "id": str(cr.id),
            "mentor_id": cr.mentor_id,
            "mentor_name": mentor.username if mentor else None,
            "mentor_current_role": mentor.role.value if mentor and hasattr(mentor.role, 'value') else (str(mentor.role) if mentor else None),
            "mentor_role": cr.mentor_role,
            "mentee_role": cr.mentee_role,
            "status": cr.status,
            "quality_score": float(cr.quality_score) if cr.quality_score else None,
            "started_at": str(cr.started_at) if cr.started_at else None,
            "graduated_at": str(cr.graduated_at) if cr.graduated_at else None,
        })
    return result


@router.get("/stats")
def get_companion_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我的同道者统计"""
    _empty = {
        "mentor_id": current_user.id,
        "graduated_count": 0,
        "active_count": 0,
        "dropped_count": 0,
        "avg_quality": None,
    }
    try:
        row = db.execute(
            text("SELECT * FROM v_companion_stats WHERE mentor_id = :mid"),
            {"mid": current_user.id}
        ).mappings().first()
    except Exception as e:
        logger.warning(f"DB object missing ({e.__class__.__name__}), returning empty fallback")
        db.rollback()
        return _empty

    return dict(row) if row else _empty


@router.post("/invite")
def invite_mentee(
    mentee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """邀请同道者(建立带教关系) — 需要Grower+"""
    _require_grower_or_above(current_user)
    if mentee_id == current_user.id:
        raise HTTPException(400, "不能带教自己")

    mentee = db.query(User).filter(User.id == mentee_id).first()
    if not mentee:
        raise HTTPException(404, "用户不存在")

    # 检查是否已存在关系 (ORM)
    existing = db.query(CompanionRelation).filter(
        CompanionRelation.mentor_id == current_user.id,
        CompanionRelation.mentee_id == mentee_id,
    ).first()

    if existing:
        raise HTTPException(409, "带教关系已存在")

    mentor_role = (current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)).upper()
    mentee_role_str = (mentee.role.value if hasattr(mentee.role, 'value') else str(mentee.role)).upper()

    cr = CompanionRelation(
        mentor_id=current_user.id,
        mentee_id=mentee_id,
        mentor_role=mentor_role,
        mentee_role=mentee_role_str,
        status=CompanionStatus.PENDING.value,  # 等待对方接受
    )
    db.add(cr)
    db.commit()
    db.refresh(cr)

    return {"message": "邀请已发送，等待对方接受", "id": str(cr.id), "mentee_id": mentee_id}


@router.get("/pending-invitations")
def list_pending_invitations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出我收到的待处理邀请（我是 mentee 且 status=pending）"""
    relations = db.query(CompanionRelation).filter(
        CompanionRelation.mentee_id == current_user.id,
        CompanionRelation.status == CompanionStatus.PENDING.value,
    ).order_by(CompanionRelation.started_at.desc()).all()

    result = []
    for cr in relations:
        mentor = db.query(User).filter(User.id == cr.mentor_id).first()
        result.append({
            "id": str(cr.id),
            "mentor_id": cr.mentor_id,
            "from_name": mentor.full_name or mentor.username if mentor else "用户",
            "mentor_role": cr.mentor_role,
            "created_at": str(cr.started_at) if cr.started_at else None,
        })
    return {"items": result, "total": len(result)}


@router.post("/invitations/{invitation_id}/accept")
def accept_invitation(
    invitation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """接受同道邀请 — 当前用户必须是 mentee"""
    cr = db.query(CompanionRelation).filter(
        CompanionRelation.id == invitation_id,
        CompanionRelation.mentee_id == current_user.id,
        CompanionRelation.status == CompanionStatus.PENDING.value,
    ).first()
    if not cr:
        raise HTTPException(404, "邀请不存在或已处理")

    cr.status = CompanionStatus.ACTIVE.value
    cr.state_changed_at = datetime.utcnow()
    db.commit()

    try:
        from core.models import PointTransaction
        db.add(PointTransaction(
            user_id=cr.mentor_id,
            action="companion_accepted",
            point_type="contribution",
            amount=3,
        ))
        db.commit()
    except Exception as e:
        logger.warning(f"积分记录失败: {e}")

    return {"message": "已接受邀请，带教关系已建立", "id": str(cr.id)}


@router.post("/invitations/{invitation_id}/reject")
def reject_invitation(
    invitation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """拒绝同道邀请 — 当前用户必须是 mentee"""
    cr = db.query(CompanionRelation).filter(
        CompanionRelation.id == invitation_id,
        CompanionRelation.mentee_id == current_user.id,
        CompanionRelation.status == CompanionStatus.PENDING.value,
    ).first()
    if not cr:
        raise HTTPException(404, "邀请不存在或已处理")

    cr.status = CompanionStatus.DROPPED.value
    cr.state_changed_at = datetime.utcnow()
    cr.dissolve_reason = "rejected_by_mentee"
    db.commit()

    return {"message": "已拒绝邀请", "id": str(cr.id)}


# ─── Admin / Coach endpoints ───


@router.get("/all")
def admin_list_all_relations(
    status: Optional[str] = None,
    mentor_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """管理员/教练查看所有同道者关系"""
    q = db.query(CompanionRelation)
    if status:
        q = q.filter(CompanionRelation.status == status)
    if mentor_id:
        q = q.filter(CompanionRelation.mentor_id == mentor_id)

    total = q.count()
    relations = q.order_by(CompanionRelation.started_at.desc()).offset(skip).limit(limit).all()

    items = []
    for cr in relations:
        mentor = db.query(User).filter(User.id == cr.mentor_id).first()
        mentee = db.query(User).filter(User.id == cr.mentee_id).first()
        items.append({
            "id": str(cr.id),
            "mentor_id": cr.mentor_id,
            "mentor_name": mentor.username if mentor else None,
            "mentee_id": cr.mentee_id,
            "mentee_name": mentee.username if mentee else None,
            "mentor_role": cr.mentor_role,
            "mentee_role": cr.mentee_role,
            "status": cr.status,
            "quality_score": float(cr.quality_score) if cr.quality_score else None,
            "started_at": str(cr.started_at) if cr.started_at else None,
            "graduated_at": str(cr.graduated_at) if cr.graduated_at else None,
        })

    return {"total": total, "items": items}


@router.put("/{relation_id}/graduate")
def graduate_mentee(
    relation_id: str,
    quality_score: Optional[float] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """标记同道者毕业"""
    cr = db.query(CompanionRelation).filter(
        CompanionRelation.id == relation_id,
        CompanionRelation.mentor_id == current_user.id,
    ).first()

    if not cr:
        raise HTTPException(404, "带教关系不存在")

    if cr.status == CompanionStatus.GRADUATED.value:
        raise HTTPException(400, "该同道者已毕业")

    cr.status = CompanionStatus.GRADUATED.value
    cr.graduated_at = datetime.utcnow()
    if quality_score is not None:
        cr.quality_score = quality_score
    if notes:
        cr.notes = notes

    db.commit()
    return {"message": "同道者已标记毕业", "id": str(cr.id)}


# ══════════════════════════════════════════════════════════
# CR-28: 同道者匹配 + 追踪端点 (审计修复)
# ══════════════════════════════════════════════════════════

from core.peer_tracking_service import PeerTrackingService, CompanionMatchStrategy


@router.get("/match", summary="同道者智能匹配")
def find_companion_matches(
    strategy: str = "stage_proximity",
    top_k: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """基于多维度匹配算法推荐同道者候选人"""
    try:
        match_strategy = CompanionMatchStrategy(strategy)
    except ValueError:
        match_strategy = CompanionMatchStrategy.STAGE_PROXIMITY
    service = PeerTrackingService(db)
    matches = service.find_matches(current_user.id, match_strategy, min(top_k, 10))
    return {"matches": matches, "strategy": strategy}


@router.post("/{companion_id}/interact", summary="记录同道互动")
def record_companion_interaction(
    companion_id: int,
    interaction_type: str = "message",
    quality_score: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """记录一次同道者互动（消息/视频/线下等） — 需要Grower+"""
    _require_grower_or_above(current_user)
    service = PeerTrackingService(db)
    ok = service.record_interaction(
        current_user.id, companion_id, interaction_type, quality_score,
    )
    if not ok:
        raise HTTPException(404, "同道关系不存在或已解除")
    return {"status": "recorded"}


@router.get("/dashboard", summary="同道仪表盘")
def companion_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的同道者全景仪表盘"""
    service = PeerTrackingService(db)
    return service.get_companion_dashboard(current_user.id)


# ══════════════════════════════════════════════════════════
# 成长者「我的教练」支持入口
# ══════════════════════════════════════════════════════════

from core.models import AssessmentAssignment, Notification


@router.get("/my-coach", summary="获取我的教练信息")
def get_my_coach(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """成长者获取自己分配的教练信息（从 assessment_assignments 取最近一条）"""
    row = (
        db.query(AssessmentAssignment)
        .filter(AssessmentAssignment.student_id == current_user.id)
        .order_by(AssessmentAssignment.created_at.desc())
        .first()
    )
    if not row or not row.coach_id:
        return {"coach": None}
    coach = db.query(User).filter(User.id == row.coach_id).first()
    if not coach:
        return {"coach": None}
    return {
        "coach": {
            "id":        coach.id,
            "name":      coach.full_name or coach.username,
            "role":      "coach",
            "avatar":    None,
        }
    }


class CoachMessageRequest(BaseModel):
    content: str
    image_desc: Optional[str] = None   # 图片描述（前端 OCR/识图后附上）
    voice_text: Optional[str] = None   # 语音转文字结果


@router.post("/message-to-coach", summary="向我的教练发送消息")
def send_message_to_coach(
    body: CoachMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """成长者向自己的教练发送一条通知消息"""
    content = (body.content or "").strip()
    if not content:
        raise HTTPException(400, "消息内容不能为空")

    # 找教练
    row = (
        db.query(AssessmentAssignment)
        .filter(AssessmentAssignment.student_id == current_user.id)
        .order_by(AssessmentAssignment.created_at.desc())
        .first()
    )
    if not row or not row.coach_id:
        raise HTTPException(404, "暂无分配的教练，无法发送消息")

    sender_name = current_user.full_name or current_user.username or "成长者"

    # 附上图片描述/语音文字
    extras = []
    if body.image_desc:
        extras.append(f"[图片：{body.image_desc}]")
    if body.voice_text:
        extras.append(f"[语音：{body.voice_text}]")
    full_content = content + ("\n" + "\n".join(extras) if extras else "")

    notif = Notification(
        user_id=row.coach_id,
        title=f"学员 {sender_name} 发来消息",
        body=full_content,
        type="coach_message",
        is_read=False,
    )
    db.add(notif)
    db.commit()
    return {"status": "sent", "to_coach_id": row.coach_id}


@router.post("/ai-draft-message", summary="AI 帮我起草给教练的消息")
def ai_draft_message(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    分析学员近期健康 + 行为数据，生成给教练的消息草稿。
    优先调用 Ollama，失败时降级到模板。
    """
    uid = current_user.id
    name = current_user.full_name or current_user.username or "我"

    # ── 收集近期数据上下文 ─────────────────────────────
    ctx: dict = {}

    # 最近体重
    w = db.execute(text("""
        SELECT weight_kg, DATE(recorded_at) AS d
        FROM vital_signs WHERE user_id=:uid AND weight_kg IS NOT NULL
        ORDER BY recorded_at DESC LIMIT 1
    """), {"uid": uid}).mappings().first()
    if w:
        ctx["weight"] = f"{w['weight_kg']:.1f}kg（{w['d']}）"

    # 最近血糖
    g = db.execute(text("""
        SELECT value, DATE(recorded_at) AS d, meal_context
        FROM glucose_readings WHERE user_id=:uid
        ORDER BY recorded_at DESC LIMIT 1
    """), {"uid": uid}).mappings().first()
    if g:
        ctx["glucose"] = f"{g['value']:.1f} mmol/L（{g['d']}，{g['meal_context'] or '未标注'}）"

    # 近7天步数均值
    steps = db.execute(text("""
        SELECT ROUND(AVG(steps)) AS avg_steps
        FROM activity_records
        WHERE user_id=:uid AND activity_date >= CURRENT_DATE - INTERVAL '7 days'
          AND steps > 0
    """), {"uid": uid}).scalar()
    if steps:
        ctx["steps"] = f"近7天均 {int(steps)} 步/天"

    # 最近评估 TTM 阶段
    assess = db.execute(text("""
        SELECT pipeline_result->>'stage_decision' AS sd,
               pipeline_result->>'profile_summary' AS ps
        FROM assessment_assignments
        WHERE student_id=:uid AND status='completed' AND pipeline_result IS NOT NULL
        ORDER BY completed_at DESC LIMIT 1
    """), {"uid": uid}).mappings().first()
    if assess and assess["ps"]:
        import json as _json
        try:
            ps = _json.loads(assess["ps"])
            stage = ps.get("current_stage") or ps.get("ttm_stage") or ""
            if stage:
                ctx["ttm_stage"] = stage
        except Exception:
            pass

    # ── 构建 Prompt ───────────────────────────────────
    data_lines = []
    if "weight" in ctx:      data_lines.append(f"体重：{ctx['weight']}")
    if "glucose" in ctx:     data_lines.append(f"血糖：{ctx['glucose']}")
    if "steps" in ctx:       data_lines.append(f"运动：{ctx['steps']}")
    if "ttm_stage" in ctx:   data_lines.append(f"行为阶段：{ctx['ttm_stage']}")

    if not data_lines:
        data_lines = ["暂无近期健康记录"]

    data_str = "\n".join(data_lines)
    prompt = (
        f"你是健康成长学员 {name} 的助手。请根据以下近期健康数据，"
        f"帮 {name} 起草一段简短的消息发给自己的教练（不超过150字），"
        f"汇报近况、提出一两个问题或请求建议。语气自然、真诚。\n\n"
        f"近期数据：\n{data_str}\n\n"
        f"只输出消息正文，不要任何解释前缀。"
    )

    draft = ""

    # 尝试调用 Ollama
    try:
        import httpx
        resp = httpx.post(
            "http://ollama:11434/api/generate",
            json={"model": "qwen3-coder:latest", "prompt": prompt, "stream": False},
            timeout=15,
        )
        if resp.status_code == 200:
            draft = resp.json().get("response", "").strip()
    except Exception as e:
        logger.warning(f"[ai-draft] Ollama unavailable: {e}")

    # 降级：模板草稿
    if not draft:
        parts = [f"教练你好！我是 {name}。"]
        if "weight" in ctx:
            parts.append(f"最近体重 {ctx['weight']}。")
        if "glucose" in ctx:
            parts.append(f"血糖 {ctx['glucose']}，想了解是否需要调整饮食？")
        if "steps" in ctx:
            parts.append(f"运动方面{ctx['steps']}，请问强度是否合适？")
        if not ctx:
            parts.append("最近想和您汇报一下近期的健康情况，方便时希望能聊聊。")
        draft = "".join(parts)

    return {
        "draft": draft,
        "context": ctx,
        "source": "ollama" if "ollama" in draft.lower() or len(draft) > 50 else "template",
    }


@router.get("")
def list_companions(
    status: Optional[str] = Query(None, description="active|pending|graduated"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    GET /companions — 聚合当前用户的全部同道关系（带教的 + 被带教的）。
    前端 companions/index.vue 使用。
    """
    q_mentor = db.query(CompanionRelation).filter(
        CompanionRelation.mentor_id == current_user.id
    )
    q_mentee = db.query(CompanionRelation).filter(
        CompanionRelation.mentee_id == current_user.id
    )
    if status:
        q_mentor = q_mentor.filter(CompanionRelation.status == status)
        q_mentee = q_mentee.filter(CompanionRelation.status == status)

    items = []
    for cr in q_mentor.order_by(CompanionRelation.started_at.desc()).all():
        peer = db.query(User).filter(User.id == cr.mentee_id).first()
        items.append({
            "id": str(cr.id),
            "peer_id": cr.mentee_id,
            "peer_name": (peer.full_name or peer.username) if peer else "用户",
            "peer_role": cr.mentee_role,
            "relation": "mentor",
            "status": cr.status,
            "quality_score": float(cr.quality_score) if cr.quality_score else None,
            "started_at": str(cr.started_at) if cr.started_at else None,
            "graduated_at": str(cr.graduated_at) if cr.graduated_at else None,
        })
    for cr in q_mentee.order_by(CompanionRelation.started_at.desc()).all():
        peer = db.query(User).filter(User.id == cr.mentor_id).first()
        items.append({
            "id": str(cr.id),
            "peer_id": cr.mentor_id,
            "peer_name": (peer.full_name or peer.username) if peer else "用户",
            "peer_role": cr.mentor_role,
            "relation": "mentee",
            "status": cr.status,
            "quality_score": float(cr.quality_score) if cr.quality_score else None,
            "started_at": str(cr.started_at) if cr.started_at else None,
            "graduated_at": str(cr.graduated_at) if cr.graduated_at else None,
        })

    return {"items": items, "total": len(items)}
