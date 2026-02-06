# -*- coding: utf-8 -*-
"""
聊天历史持久化服务

管理 AI 对话的会话和消息存储
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger

from core.database import get_db_session, db_transaction
from core.models import ChatSession, ChatMessage


class ChatHistoryService:
    """聊天历史服务"""

    @staticmethod
    def create_session(user_id: int, session_id: str = None, model: str = "qwen2.5:0.5b") -> ChatSession:
        """
        创建新的聊天会话

        Args:
            user_id: 用户ID
            session_id: 可选的会话ID，为空则自动生成
            model: 使用的模型

        Returns:
            ChatSession 对象
        """
        import uuid

        if not session_id:
            session_id = f"chat_{user_id}_{int(datetime.now().timestamp())}"

        with db_transaction() as db:
            # 检查是否已存在
            existing = db.query(ChatSession).filter(
                ChatSession.session_id == session_id
            ).first()

            if existing:
                return existing

            session = ChatSession(
                session_id=session_id,
                user_id=user_id,
                model=model,
                is_active=True,
                message_count=0
            )
            db.add(session)
            db.flush()

            logger.info(f"[ChatHistory] 创建会话: {session_id} for user {user_id}")
            return session

    @staticmethod
    def get_session(session_id: str) -> Optional[ChatSession]:
        """获取会话"""
        with get_db_session() as db:
            session = db.query(ChatSession).filter(
                ChatSession.session_id == session_id,
                ChatSession.is_active == True
            ).first()
            return session

    @staticmethod
    def get_or_create_session(user_id: int, session_id: str = None, model: str = "qwen2.5:0.5b") -> ChatSession:
        """获取或创建会话"""
        if session_id:
            with get_db_session() as db:
                session = db.query(ChatSession).filter(
                    ChatSession.session_id == session_id
                ).first()
                if session:
                    return session

        return ChatHistoryService.create_session(user_id, session_id, model)

    @staticmethod
    def add_message(
        session_id: str,
        role: str,
        content: str,
        model: str = None,
        metadata: Dict[str, Any] = None
    ) -> Optional[ChatMessage]:
        """
        添加消息到会话

        Args:
            session_id: 会话ID
            role: 消息角色 (user/assistant)
            content: 消息内容
            model: 模型名称（仅assistant消息）
            metadata: 元数据

        Returns:
            ChatMessage 对象
        """
        with db_transaction() as db:
            # 获取会话
            session = db.query(ChatSession).filter(
                ChatSession.session_id == session_id
            ).first()

            if not session:
                logger.warning(f"[ChatHistory] 会话不存在: {session_id}")
                return None

            # 创建消息
            message = ChatMessage(
                session_id=session.id,
                role=role,
                content=content,
                model=model,
                msg_metadata=metadata or {}
            )
            db.add(message)

            # 更新会话消息计数
            session.message_count += 1
            session.updated_at = datetime.utcnow()

            db.flush()
            logger.debug(f"[ChatHistory] 添加消息: {role} -> {content[:50]}...")
            return message

    @staticmethod
    def get_messages(session_id: str, limit: int = 50) -> List[Dict[str, str]]:
        """
        获取会话消息历史

        Args:
            session_id: 会话ID
            limit: 返回消息数量限制

        Returns:
            消息列表 [{"role": "user", "content": "..."}, ...]
        """
        with get_db_session() as db:
            session = db.query(ChatSession).filter(
                ChatSession.session_id == session_id
            ).first()

            if not session:
                return []

            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session.id
            ).order_by(ChatMessage.created_at.desc()).limit(limit).all()

            # 反转顺序（从旧到新）
            messages = list(reversed(messages))

            return [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

    @staticmethod
    def get_user_sessions(user_id: int, limit: int = 20) -> List[ChatSession]:
        """获取用户的所有会话"""
        with get_db_session() as db:
            sessions = db.query(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatSession.is_active == True
            ).order_by(ChatSession.updated_at.desc()).limit(limit).all()
            return sessions

    @staticmethod
    def delete_session(session_id: str) -> bool:
        """删除会话（软删除）"""
        with db_transaction() as db:
            session = db.query(ChatSession).filter(
                ChatSession.session_id == session_id
            ).first()

            if session:
                session.is_active = False
                logger.info(f"[ChatHistory] 删除会话: {session_id}")
                return True
            return False

    @staticmethod
    def clear_user_history(user_id: int) -> int:
        """清空用户所有聊天历史"""
        with db_transaction() as db:
            count = db.query(ChatSession).filter(
                ChatSession.user_id == user_id
            ).update({"is_active": False})

            logger.info(f"[ChatHistory] 清空用户 {user_id} 的 {count} 个会话")
            return count


# 全局实例
chat_history = ChatHistoryService()
