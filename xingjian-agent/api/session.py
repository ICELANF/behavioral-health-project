# -*- coding: utf-8 -*-
"""
会话管理模块

管理用户会话、对话历史和会话过期清理
"""

import time
import uuid
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class Message:
    """对话消息"""
    role: str                    # "user" 或 "assistant"
    content: str                 # 消息内容
    timestamp: datetime = field(default_factory=datetime.now)
    expert_id: Optional[str] = None  # 响应的专家ID（仅assistant消息）
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    """用户会话"""
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str, expert_id: str = None, **kwargs):
        """添加消息到会话"""
        message = Message(
            role=role,
            content=content,
            expert_id=expert_id,
            metadata=kwargs
        )
        self.messages.append(message)
        self.last_active = datetime.now()

    def get_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """获取最近的对话历史"""
        recent = self.messages[-limit:] if limit else self.messages
        return [
            {"role": msg.role, "content": msg.content}
            for msg in recent
        ]

    def is_expired(self, ttl_seconds: int = 3600) -> bool:
        """检查会话是否过期"""
        elapsed = (datetime.now() - self.last_active).total_seconds()
        return elapsed > ttl_seconds


class SessionManager:
    """会话管理器

    线程安全的会话存储和管理
    """

    def __init__(self, ttl_seconds: int = 3600, cleanup_interval: int = 300):
        """初始化会话管理器

        Args:
            ttl_seconds: 会话过期时间（秒），默认1小时
            cleanup_interval: 清理间隔（秒），默认5分钟
        """
        self._sessions: Dict[str, Session] = {}
        self._lock = threading.RLock()
        self._ttl = ttl_seconds
        self._cleanup_interval = cleanup_interval
        self._cleanup_thread: Optional[threading.Thread] = None
        self._running = False

    def start_cleanup_task(self):
        """启动后台清理任务"""
        if self._cleanup_thread is not None:
            return

        self._running = True
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True
        )
        self._cleanup_thread.start()

    def stop_cleanup_task(self):
        """停止后台清理任务"""
        self._running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
            self._cleanup_thread = None

    def _cleanup_loop(self):
        """清理循环"""
        while self._running:
            time.sleep(self._cleanup_interval)
            self._cleanup_expired()

    def _cleanup_expired(self):
        """清理过期会话"""
        with self._lock:
            expired_ids = [
                sid for sid, session in self._sessions.items()
                if session.is_expired(self._ttl)
            ]
            for sid in expired_ids:
                del self._sessions[sid]

            if expired_ids:
                print(f"[SessionManager] 已清理 {len(expired_ids)} 个过期会话")

    def create_session(self, session_id: str = None) -> Session:
        """创建新会话

        Args:
            session_id: 可选的会话ID，为空则自动生成

        Returns:
            新创建的会话
        """
        if not session_id:
            session_id = f"sess_{uuid.uuid4().hex[:12]}"

        with self._lock:
            if session_id in self._sessions:
                return self._sessions[session_id]

            session = Session(session_id=session_id)
            self._sessions[session_id] = session
            return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话

        Args:
            session_id: 会话ID

        Returns:
            会话对象，不存在则返回None
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session and not session.is_expired(self._ttl):
                return session
            return None

    def get_or_create_session(self, session_id: str = None) -> Session:
        """获取或创建会话

        Args:
            session_id: 会话ID，为空则创建新会话

        Returns:
            会话对象
        """
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session

        return self.create_session(session_id)

    def delete_session(self, session_id: str) -> bool:
        """删除会话

        Args:
            session_id: 会话ID

        Returns:
            是否成功删除
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        expert_id: str = None,
        **kwargs
    ) -> bool:
        """向会话添加消息

        Args:
            session_id: 会话ID
            role: 消息角色
            content: 消息内容
            expert_id: 专家ID
            **kwargs: 其他元数据

        Returns:
            是否成功添加
        """
        session = self.get_session(session_id)
        if not session:
            return False

        session.add_message(role, content, expert_id, **kwargs)
        return True

    def get_session_count(self) -> int:
        """获取活跃会话数量"""
        with self._lock:
            return len(self._sessions)

    def clear_all(self):
        """清空所有会话"""
        with self._lock:
            self._sessions.clear()


# 全局会话管理器实例
session_manager = SessionManager(ttl_seconds=3600, cleanup_interval=300)
