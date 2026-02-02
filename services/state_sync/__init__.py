"""
状态同步模块
State Sync Module

实现"一套输入，两套表述"的数据分发
"""
from services.state_sync.manager import (
    StateSyncManager,
    get_state_sync_manager,
    ViewRole,
    EventType,
    UiStyle,
    ClientView,
    CoachView,
    ExpertView,
    StateSyncRecord,
)

__all__ = [
    "StateSyncManager",
    "get_state_sync_manager",
    "ViewRole",
    "EventType",
    "UiStyle",
    "ClientView",
    "CoachView",
    "ExpertView",
    "StateSyncRecord",
]
