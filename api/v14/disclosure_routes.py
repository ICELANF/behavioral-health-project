"""
行为健康数字平台 - 披露控制 API
Disclosure Control API

[v14-NEW] 披露控制模块

路由前缀: /api/v2/disclosure/

端点：
- POST /decision/create - 创建披露决策
- GET /decision/{report_id} - 获取披露决策
- POST /decision/{report_id}/sign - 签名
- POST /decision/{report_id}/approve - 批准披露
- POST /decision/{report_id}/reject - 驳回披露
- POST /decision/{report_id}/chapter - 设置章节可见性
- POST /decision/{report_id}/rewrite - 添加内容重写
- GET /chapters - 获取章节列表
- GET /blacklist - 获取禁词库
- POST /blacklist/check - 检查敏感词
- POST /rewrite - AI重写文本
- GET /pending - 获取待审核列表
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from disclosure import (
    get_blacklist_manager,
    get_disclosure_controller,
    get_ai_rewriter,
    get_signature_manager,
    ViewerRole,
    DisclosureLevel,
    RiskLevel,
    SignatureRole,
    DEFAULT_CHAPTERS
)


router = APIRouter(prefix="/disclosure", tags=["disclosure"])


# ============================================
# 请求模型
# ============================================

class CreateDecisionRequest(BaseModel):
    """创建披露决策请求"""
    report_id: str
    user_id: int
    risk_level: str = "moderate"  # critical, high, moderate, low
    initial_content: Optional[str] = None


class SignRequest(BaseModel):
    """签名请求"""
    signer_id: str
    signer_name: str
    role: str  # primary, secondary
    comment: Optional[str] = None


class ChapterVisibilityRequest(BaseModel):
    """章节可见性请求"""
    chapter_id: str
    visible: bool
    expert_id: str


class RewriteRequest(BaseModel):
    """重写请求"""
    original: str
    rewritten: str
    expert_id: str


class BlacklistCheckRequest(BaseModel):
    """敏感词检查请求"""
    text: str
    min_level: str = "low"  # low, moderate, high, critical


class AIRewriteRequest(BaseModel):
    """AI重写请求"""
    text: str
    context: Optional[Dict[str, Any]] = None


# ============================================
# 披露决策API
# ============================================

@router.post("/decision/create")
async def create_disclosure_decision(request: CreateDecisionRequest):
    """创建披露决策"""
    try:
        risk_level = RiskLevel(request.risk_level)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的风险等级: {request.risk_level}")
    
    controller = get_disclosure_controller()
    decision = controller.create_decision(
        report_id=request.report_id,
        user_id=request.user_id,
        risk_level=risk_level,
        initial_content=request.initial_content
    )
    
    return {
        "success": True,
        "decision": decision.to_dict()
    }


@router.get("/decision/{report_id}")
async def get_disclosure_decision(report_id: str):
    """获取披露决策"""
    controller = get_disclosure_controller()
    decision = controller.get_decision(report_id)
    
    if not decision:
        raise HTTPException(status_code=404, detail=f"披露决策不存在: {report_id}")
    
    return {
        "success": True,
        "decision": decision.to_dict()
    }


@router.post("/decision/{report_id}/sign")
async def sign_disclosure(report_id: str, request: SignRequest):
    """签名披露决策"""
    controller = get_disclosure_controller()
    decision = controller.get_decision(report_id)
    
    if not decision:
        raise HTTPException(status_code=404, detail=f"披露决策不存在: {report_id}")
    
    if not decision.signature_request_id:
        raise HTTPException(status_code=400, detail="该决策无需签名")
    
    try:
        role = SignatureRole(request.role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的签名角色: {request.role}")
    
    signature_mgr = get_signature_manager()
    sig_request = signature_mgr.sign(
        request_id=decision.signature_request_id,
        signer_id=request.signer_id,
        signer_name=request.signer_name,
        role=role,
        comment=request.comment
    )
    
    # 如果签名完成，更新决策状态
    if sig_request.is_complete:
        decision.status = "approved"
        decision.reviewed_at = datetime.now()
    
    return {
        "success": True,
        "signature_request": sig_request.to_dict(),
        "decision_status": decision.status
    }


@router.post("/decision/{report_id}/approve")
async def approve_disclosure(
    report_id: str,
    expert_id: str,
    expert_name: str,
    role: str = "primary",
    notes: Optional[str] = None
):
    """批准披露"""
    controller = get_disclosure_controller()
    
    try:
        sig_role = SignatureRole(role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的签名角色: {role}")
    
    try:
        decision = controller.approve_disclosure(
            report_id=report_id,
            expert_id=expert_id,
            expert_name=expert_name,
            role=sig_role,
            notes=notes
        )
        
        return {
            "success": True,
            "decision": decision.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/decision/{report_id}/reject")
async def reject_disclosure(
    report_id: str,
    expert_id: str,
    expert_name: str,
    reason: str
):
    """驳回披露"""
    controller = get_disclosure_controller()
    
    try:
        decision = controller.reject_disclosure(
            report_id=report_id,
            expert_id=expert_id,
            expert_name=expert_name,
            reason=reason
        )
        
        return {
            "success": True,
            "decision": decision.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/decision/{report_id}/chapter")
async def set_chapter_visibility(report_id: str, request: ChapterVisibilityRequest):
    """设置章节可见性"""
    controller = get_disclosure_controller()
    
    try:
        decision = controller.set_chapter_visibility(
            report_id=report_id,
            chapter_id=request.chapter_id,
            visible=request.visible,
            expert_id=request.expert_id
        )
        
        return {
            "success": True,
            "chapter_id": request.chapter_id,
            "visible": request.visible,
            "decision": decision.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/decision/{report_id}/rewrite")
async def add_content_rewrite(report_id: str, request: RewriteRequest):
    """添加内容重写"""
    controller = get_disclosure_controller()
    
    try:
        decision = controller.add_content_rewrite(
            report_id=report_id,
            original=request.original,
            rewritten=request.rewritten,
            expert_id=request.expert_id
        )
        
        return {
            "success": True,
            "decision": decision.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/decision/{report_id}/visible-chapters")
async def get_visible_chapters(report_id: str, role: str = "patient"):
    """获取指定角色可见的章节"""
    try:
        viewer_role = ViewerRole(role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的角色: {role}")
    
    controller = get_disclosure_controller()
    visible = controller.get_visible_chapters(report_id, viewer_role)
    
    return {
        "report_id": report_id,
        "role": role,
        "visible_chapters": visible
    }


@router.get("/decision/{report_id}/patient-message")
async def get_patient_message(report_id: str):
    """获取患者端显示消息"""
    controller = get_disclosure_controller()
    message = controller.get_patient_view_message(report_id)
    can_view = controller.can_patient_view(report_id)
    
    return {
        "report_id": report_id,
        "can_view": can_view,
        "message": message
    }


# ============================================
# 章节配置API
# ============================================

@router.get("/chapters")
async def get_chapters():
    """获取所有章节配置"""
    chapters = []
    for chapter in DEFAULT_CHAPTERS:
        chapters.append({
            "chapter_id": chapter.chapter_id,
            "name": chapter.name,
            "description": chapter.description,
            "sensitivity": chapter.sensitivity.value,
            "requires_expert_approval": chapter.requires_expert_approval,
            "default_visibility": {
                k.value: v for k, v in chapter.default_visibility.items()
            }
        })
    
    return {
        "total": len(chapters),
        "chapters": chapters
    }


# ============================================
# 禁词库API
# ============================================

@router.get("/blacklist")
async def get_blacklist():
    """获取禁词库"""
    blacklist = get_blacklist_manager()
    return {
        "total": len(blacklist.words),
        "by_category": blacklist.to_dict(),
        "critical_words": blacklist.get_critical_words()
    }


@router.post("/blacklist/check")
async def check_blacklist(request: BlacklistCheckRequest):
    """检查文本中的敏感词"""
    from disclosure import SensitivityLevel
    
    blacklist = get_blacklist_manager()
    
    try:
        min_level = SensitivityLevel(request.min_level)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的敏感度等级: {request.min_level}")
    
    detections = blacklist.detect(request.text)
    contains = blacklist.contains_sensitive(request.text, min_level)
    suggestions = blacklist.get_replacement_suggestions(request.text)
    
    return {
        "text": request.text,
        "contains_sensitive": contains,
        "detections": [
            {
                "word": bw.word,
                "category": bw.category.value,
                "level": bw.level.value,
                "position": [start, end],
                "suggested_replacement": bw.suggested_replacement
            }
            for bw, start, end in detections
        ],
        "suggestions": suggestions,
        "highlighted_html": blacklist.highlight_html(request.text)
    }


@router.post("/blacklist/auto-replace")
async def auto_replace_blacklist(request: BlacklistCheckRequest):
    """自动替换敏感词"""
    from disclosure import SensitivityLevel
    
    blacklist = get_blacklist_manager()
    
    try:
        min_level = SensitivityLevel(request.min_level)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的敏感度等级: {request.min_level}")
    
    replaced = blacklist.auto_replace(request.text, min_level)
    
    return {
        "original": request.text,
        "replaced": replaced,
        "changed": request.text != replaced
    }


# ============================================
# AI重写API
# ============================================

@router.post("/rewrite")
async def ai_rewrite(request: AIRewriteRequest):
    """AI重写文本"""
    rewriter = get_ai_rewriter()
    result = rewriter.rewrite(request.text, request.context)
    
    return {
        "original": result.original,
        "rewritten": result.rewritten,
        "changes": result.changes,
        "confidence": result.confidence
    }


@router.post("/rewrite/assessment")
async def rewrite_assessment(
    big5_summary: str,
    ttm_stage: str,
    bpt6_type: str,
    risk_level: str = "moderate"
):
    """重写评估摘要"""
    rewriter = get_ai_rewriter()
    result = rewriter.rewrite_assessment_summary(
        big5_summary=big5_summary,
        ttm_stage=ttm_stage,
        bpt6_type=bpt6_type,
        risk_level=risk_level
    )
    
    return {
        "rewritten_summary": result
    }


@router.get("/rewrite/stage-message/{ttm_stage}")
async def get_stage_message(ttm_stage: str):
    """获取阶段鼓励消息"""
    rewriter = get_ai_rewriter()
    message = rewriter.generate_stage_message(ttm_stage)
    
    return {
        "ttm_stage": ttm_stage,
        "message": message
    }


# ============================================
# 待审核列表API
# ============================================

@router.get("/pending")
async def get_pending_reviews():
    """获取待审核列表"""
    controller = get_disclosure_controller()
    pending = controller.list_pending_reviews()
    
    return {
        "total": len(pending),
        "reviews": [d.to_dict() for d in pending]
    }


@router.get("/signature/pending")
async def get_pending_signatures(role: Optional[str] = None):
    """获取待签名请求"""
    signature_mgr = get_signature_manager()
    
    sig_role = None
    if role:
        try:
            sig_role = SignatureRole(role)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的角色: {role}")
    
    pending = signature_mgr.get_pending_requests(sig_role)
    
    return {
        "total": len(pending),
        "requests": [r.to_dict() for r in pending]
    }
