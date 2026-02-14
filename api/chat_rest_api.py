"""
聊天REST API端点
Chat REST API Endpoints

提供聊天会话和消息的REST接口:
- 获取用户会话列表
- 创建/删除会话
- 获取会话消息
- 发送消息(调用AI助手)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from loguru import logger

from core.database import get_db
from core.models import ChatSession, ChatMessage, User
from api.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/chat", tags=["聊天"])


# ============================================
# Pydantic 模型
# ============================================

class CreateSessionRequest(BaseModel):
    title: Optional[str] = None
    model: str = "qwen2.5:0.5b"


class SendMessageRequest(BaseModel):
    content: str
    model: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    title: Optional[str]
    model: str
    message_count: int
    is_active: bool
    created_at: str
    updated_at: str
    last_message: Optional[str] = None


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    model: Optional[str]
    created_at: str


# ============================================
# API端点
# ============================================

@router.get("/sessions")
def list_sessions(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的聊天会话列表"""
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id,
        ChatSession.is_active == True
    ).order_by(ChatSession.updated_at.desc()).limit(limit).all()

    result = []
    for s in sessions:
        # 获取最后一条消息
        last_msg = db.query(ChatMessage).filter(
            ChatMessage.session_id == s.id
        ).order_by(ChatMessage.created_at.desc()).first()

        result.append({
            "session_id": s.session_id,
            "title": s.title or "新对话",
            "model": s.model,
            "message_count": s.message_count,
            "is_active": s.is_active,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat(),
            "last_message": last_msg.content[:100] if last_msg else None,
        })

    return {"sessions": result, "total": len(result)}


@router.post("/sessions")
def create_session(
    request: CreateSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新的聊天会话"""
    import uuid

    session_id = f"chat_{current_user.id}_{int(datetime.now().timestamp())}"

    session = ChatSession(
        session_id=session_id,
        user_id=current_user.id,
        title=request.title,
        model=request.model,
        is_active=True,
        message_count=0,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    logger.info(f"✓ 创建聊天会话: {session_id}, 用户: {current_user.username}")

    return {
        "session_id": session.session_id,
        "title": session.title,
        "model": session.model,
        "created_at": session.created_at.isoformat(),
    }


@router.get("/sessions/{session_id}/messages")
def get_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=200),
    before_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取会话消息历史"""
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    query = db.query(ChatMessage).filter(ChatMessage.session_id == session.id)

    if before_id:
        query = query.filter(ChatMessage.id < before_id)

    messages = query.order_by(ChatMessage.created_at.desc()).limit(limit).all()
    messages = list(reversed(messages))

    return {
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "model": msg.model,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in messages
        ],
        "total": len(messages),
    }


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    发送消息并获取AI回复

    1. 保存用户消息
    2. 调用AI助手
    3. 保存AI回复
    4. 返回完整对话
    """
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 保存用户消息
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=request.content,
    )
    db.add(user_msg)
    session.message_count += 1
    session.updated_at = datetime.utcnow()

    # 如果是第一条消息，自动生成标题
    if session.message_count == 1 and not session.title:
        session.title = request.content[:30] + ("..." if len(request.content) > 30 else "")

    db.commit()
    db.refresh(user_msg)

    # ── SafetyPipeline L1: 输入过滤 ──
    _safety_pipeline = None
    _input_category = "normal"
    try:
        from core.safety.pipeline import get_safety_pipeline
        _safety_pipeline = get_safety_pipeline()
        _input_result = _safety_pipeline.process_input(request.content)
        _input_category = _input_result.category
        if not _input_result.safe:
            try:
                from core.models import SafetyLog
                db.add(SafetyLog(
                    user_id=current_user.id,
                    event_type="input_blocked",
                    severity=_input_result.severity,
                    input_text=request.content[:500],
                    filter_details={"category": _input_result.category, "terms": _input_result.blocked_terms},
                ))
                db.commit()
            except Exception:
                logger.warning("SafetyLog write failed")
            _safe_reply = _safety_pipeline.get_crisis_response() if _input_result.category == "crisis" else "抱歉，您的消息包含不适当的内容，无法处理。如需帮助请联系专业人员。"
            safe_msg = ChatMessage(session_id=session.id, role="assistant", content=_safe_reply, model="safety")
            db.add(safe_msg)
            session.message_count += 1
            session.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(safe_msg)
            return {
                "user_message": {"id": user_msg.id, "role": "user", "content": user_msg.content, "created_at": user_msg.created_at.isoformat()},
                "assistant_message": {"id": safe_msg.id, "role": "assistant", "content": safe_msg.content, "model": "safety", "created_at": safe_msg.created_at.isoformat()},
                "safety_filtered": True,
            }
    except Exception as e:
        logger.warning(f"SafetyPipeline input filter degraded: {e}")

    # 获取历史消息用于上下文
    history_msgs = db.query(ChatMessage).filter(
        ChatMessage.session_id == session.id
    ).order_by(ChatMessage.created_at.desc()).limit(10).all()
    history = [{"role": m.role, "content": m.content} for m in reversed(history_msgs)]

    # 调用AI助手 + RAG 知识库增强
    model = request.model or session.model
    ai_reply = "抱歉，AI助手暂时不可用，请稍后再试。"
    rag_data = None

    try:
        import httpx
        import os

        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", model)

        base_system_prompt = """你是"行健行为教练"，一位专业、温和的健康行为改变指导师。
你的职责：
1. 评估用户健康状态和心理准备度
2. 提供个性化的行为建议
3. 推荐适合的健康任务
4. 支持用户的行为改变过程
请用温和、专业、鼓励的语气回复。"""

        # RAG 增强
        final_system_prompt = base_system_prompt
        try:
            from core.knowledge import rag_enhance, record_citations

            enhanced = rag_enhance(
                db=db,
                query=request.content,
                base_system_prompt=base_system_prompt,
            )
            final_system_prompt = enhanced.system_prompt
        except Exception as e:
            logger.warning(f"RAG 增强失败, 使用原始 prompt: {e}")
            enhanced = None

        messages_for_llm = [{"role": "system", "content": final_system_prompt}] + history

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{ollama_url}/api/chat",
                json={"model": ollama_model, "messages": messages_for_llm, "stream": False},
            )
            if resp.status_code == 200:
                data = resp.json()
                ai_reply = data.get("message", {}).get("content", ai_reply)

        # 包装 RAG 引用数据
        if enhanced:
            rag_data = enhanced.wrap_response(ai_reply)
            try:
                record_citations(
                    db=db,
                    enhanced=enhanced,
                    llm_response=ai_reply,
                    session_id=session_id,
                    message_id=str(user_msg.id),
                    user_id=str(current_user.id),
                )
            except Exception as e:
                logger.warning(f"引用记录失败: {e}")

    except Exception as e:
        logger.warning(f"AI调用失败: {e}")
        ai_reply = (
            "您好！感谢您的分享。作为您的行为健康教练，我建议您：\n\n"
            "1. 保持规律的生活作息\n"
            "2. 每天进行适量运动\n"
            "3. 注意饮食均衡\n"
            "4. 定期监测健康指标\n\n"
            "如果有具体的健康问题，请随时告诉我，我会为您提供更针对性的建议。"
        )

    # ── SafetyPipeline L4: 输出过滤 ──
    _final_text = rag_data["text"] if rag_data else ai_reply
    try:
        if _safety_pipeline:
            _output_result = _safety_pipeline.filter_output(_final_text, _input_category)
            if _output_result.grade == "blocked":
                _final_text = "抱歉，生成的内容未通过安全审核。如需专业建议请咨询医生。"
                try:
                    from core.models import SafetyLog
                    db.add(SafetyLog(
                        user_id=current_user.id,
                        event_type="output_blocked",
                        severity="high",
                        input_text=request.content[:500],
                        output_text=ai_reply[:500],
                        filter_details={"grade": "blocked", "annotations": _output_result.annotations},
                    ))
                    db.commit()
                except Exception:
                    logger.warning("SafetyLog write failed (output_blocked)")
            elif _output_result.grade == "review_needed":
                _final_text = _output_result.text
                try:
                    from core.models import SafetyLog
                    db.add(SafetyLog(
                        user_id=current_user.id,
                        event_type="output_review",
                        severity="medium",
                        input_text=request.content[:500],
                        output_text=ai_reply[:500],
                        filter_details={"grade": "review_needed", "annotations": _output_result.annotations, "disclaimer": _output_result.disclaimer_added},
                    ))
                    db.commit()
                except Exception:
                    logger.warning("SafetyLog write failed (output_review)")
            else:
                _final_text = _output_result.text
            if rag_data:
                rag_data["text"] = _final_text
            else:
                ai_reply = _final_text
    except Exception as e:
        logger.warning(f"SafetyPipeline output filter degraded: {e}")

    # 保存AI回复 (metadata 包含 RAG 引用)
    import json as _json
    ai_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=rag_data["text"] if rag_data else ai_reply,
        model=model,
        msg_metadata=_json.loads(_json.dumps({
            "rag": {
                "hasKnowledge": rag_data["hasKnowledge"],
                "citationsUsed": rag_data["citationsUsed"],
                "citations": rag_data["citations"],
                "hasModelSupplement": rag_data["hasModelSupplement"],
                "modelSupplementSections": rag_data["modelSupplementSections"],
                "sourceStats": rag_data["sourceStats"],
            }
        })) if rag_data and rag_data.get("hasKnowledge") else None,
    )
    db.add(ai_msg)
    session.message_count += 1
    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ai_msg)

    logger.info(f"✓ 聊天回复: session={session_id}, user={current_user.username}, rag={bool(rag_data and rag_data.get('hasKnowledge'))}")

    # ── 审计日志 ──
    try:
        from core.models import UserActivityLog
        db.add(UserActivityLog(
            user_id=current_user.id,
            activity_type="chat.send_message",
            detail={
                "session_id": session_id,
                "msg_len": len(request.content),
                "model": model,
                "rag": bool(rag_data and rag_data.get("hasKnowledge")),
            },
            created_at=datetime.utcnow(),
        ))
        db.flush()
    except Exception:
        logger.warning("审计日志写入失败")

    result = {
        "user_message": {
            "id": user_msg.id,
            "role": "user",
            "content": user_msg.content,
            "created_at": user_msg.created_at.isoformat(),
        },
        "assistant_message": {
            "id": ai_msg.id,
            "role": "assistant",
            "content": ai_msg.content,
            "model": ai_msg.model,
            "created_at": ai_msg.created_at.isoformat(),
        },
    }
    if rag_data:
        result["rag"] = rag_data
    return result


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除会话（软删除）"""
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    session.is_active = False
    db.commit()

    logger.info(f"✓ 删除聊天会话: {session_id}")
    return {"message": "会话已删除"}
