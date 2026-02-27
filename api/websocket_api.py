# -*- coding: utf-8 -*-
"""
WebSocket API - 实时推送服务

支持：
- 内容详情页实时更新（评论、点赞、动态）
- 用户学习进度同步
- 系统通知推送
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Set, Optional, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from loguru import logger

from core.auth import verify_token_with_blacklist

router = APIRouter(tags=["WebSocket"])


# ============================================================================
# 连接管理器
# ============================================================================

class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # content_id -> Set[WebSocket]
        self.content_connections: Dict[str, Set[WebSocket]] = {}
        # user_id -> WebSocket
        self.user_connections: Dict[str, WebSocket] = {}
        # 全局广播连接
        self.broadcast_connections: Set[WebSocket] = set()

    async def connect_content(self, websocket: WebSocket, content_id: str):
        """连接到内容频道"""
        await websocket.accept()
        if content_id not in self.content_connections:
            self.content_connections[content_id] = set()
        self.content_connections[content_id].add(websocket)
        logger.info(f"[WS] Client connected to content: {content_id}")

    async def connect_user(self, websocket: WebSocket, user_id: str):
        """连接用户频道"""
        await websocket.accept()
        self.user_connections[user_id] = websocket
        logger.info(f"[WS] User connected: {user_id}")

    async def connect_broadcast(self, websocket: WebSocket):
        """连接全局广播"""
        await websocket.accept()
        self.broadcast_connections.add(websocket)
        logger.info(f"[WS] Client connected to broadcast")

    def disconnect_content(self, websocket: WebSocket, content_id: str):
        """断开内容频道"""
        if content_id in self.content_connections:
            self.content_connections[content_id].discard(websocket)
            if not self.content_connections[content_id]:
                del self.content_connections[content_id]
        logger.info(f"[WS] Client disconnected from content: {content_id}")

    def disconnect_user(self, websocket: WebSocket, user_id: str):
        """断开用户频道"""
        if user_id in self.user_connections:
            del self.user_connections[user_id]
        logger.info(f"[WS] User disconnected: {user_id}")

    def disconnect_broadcast(self, websocket: WebSocket):
        """断开全局广播"""
        self.broadcast_connections.discard(websocket)
        logger.info(f"[WS] Client disconnected from broadcast")

    async def send_to_content(self, content_id: str, message: dict):
        """发送消息到内容频道的所有连接"""
        if content_id in self.content_connections:
            dead_connections = set()
            for connection in self.content_connections[content_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.add(connection)
            # 清理断开的连接
            self.content_connections[content_id] -= dead_connections

    async def send_to_user(self, user_id: str, message: dict):
        """发送消息到特定用户"""
        if user_id in self.user_connections:
            try:
                await self.user_connections[user_id].send_json(message)
            except Exception:
                del self.user_connections[user_id]

    async def broadcast(self, message: dict):
        """广播消息到所有连接"""
        dead_connections = set()
        for connection in self.broadcast_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.add(connection)
        self.broadcast_connections -= dead_connections


# 全局连接管理器实例
manager = ConnectionManager()


# ============================================================================
# 模拟数据生成器（后期替换为真实数据库查询）
# ============================================================================

async def get_content_updates(content_id: str) -> Optional[dict]:
    """获取内容更新（模拟）"""
    import random

    # 模拟：30%概率有新更新
    if random.random() > 0.3:
        return None

    update_types = ["new_comment", "like_update", "view_update"]
    update_type = random.choice(update_types)

    if update_type == "new_comment":
        return {
            "type": "new_comment",
            "data": {
                "id": f"c_{datetime.now().timestamp()}",
                "user": {"name": random.choice(["小明", "静心", "成长中", "阳光"]), "avatar": None},
                "content": random.choice([
                    "这个练习真的很有帮助！",
                    "坚持了一周，感觉好多了",
                    "推荐给朋友们",
                    "每天都在做，效果不错"
                ]),
                "rating": random.randint(4, 5),
                "created_at": datetime.now().isoformat()
            }
        }
    elif update_type == "like_update":
        return {
            "type": "stats_update",
            "data": {
                "like_count": random.randint(320, 350),
                "collect_count": random.randint(890, 910)
            }
        }
    else:
        return {
            "type": "stats_update",
            "data": {
                "view_count": random.randint(12800, 13000)
            }
        }


async def get_feed_updates(domain: str = None) -> Optional[dict]:
    """获取动态更新（模拟）"""
    import random

    # 模拟：20%概率有新动态
    if random.random() > 0.2:
        return None

    feed_templates = [
        {
            "type": "notification",
            "icon": "🔔",
            "title": "新活动上线：7天正念挑战",
            "summary": "参与挑战，赢取专属徽章",
            "link": "/activity/7day-challenge"
        },
        {
            "type": "news",
            "icon": "📰",
            "title": "研究：正念冥想可改善睡眠质量",
            "summary": "最新研究表明每天10分钟正念练习...",
            "link": "/content/article/mindfulness-sleep"
        },
        {
            "type": "community",
            "icon": "🏆",
            "title": "用户达成100天打卡成就",
            "summary": "恭喜用户「静心」完成百日正念之旅",
            "link": "/cases/100days-achievement"
        },
        {
            "type": "tip",
            "icon": "💡",
            "title": "小贴士：呼吸练习的注意事项",
            "summary": "保持自然呼吸，不要刻意控制",
            "link": None
        }
    ]

    feed = random.choice(feed_templates)
    feed["id"] = f"f_{datetime.now().timestamp()}"
    feed["time"] = "刚刚"
    feed["is_new"] = True

    return {
        "type": "new_feed",
        "data": feed
    }


# ============================================================================
# WebSocket 端点
# ============================================================================

@router.websocket("/ws/content/{content_id}")
async def content_websocket(
    websocket: WebSocket,
    content_id: str,
    user_id: str = Query(default="anonymous")
):
    """
    内容详情页 WebSocket 连接

    推送：
    - 新评论
    - 点赞/收藏数更新
    - 浏览量更新
    """
    await manager.connect_content(websocket, content_id)

    try:
        # 发送连接确认
        await websocket.send_json({
            "type": "connected",
            "content_id": content_id,
            "message": "实时更新已连接"
        })

        while True:
            # 检查内容更新
            updates = await get_content_updates(content_id)
            if updates:
                await websocket.send_json(updates)

            # 同时监听客户端消息（如用户操作）
            try:
                # 非阻塞接收，超时5秒
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=5.0
                )

                # 处理客户端消息
                if data.get("action") == "like":
                    # 广播点赞到所有连接
                    await manager.send_to_content(content_id, {
                        "type": "stats_update",
                        "data": {"like_count_delta": 1}
                    })
                elif data.get("action") == "comment":
                    # 广播新评论
                    await manager.send_to_content(content_id, {
                        "type": "new_comment",
                        "data": data.get("comment")
                    })

            except asyncio.TimeoutError:
                # 超时继续循环
                pass

    except WebSocketDisconnect:
        manager.disconnect_content(websocket, content_id)
    except Exception as e:
        logger.error(f"[WS] Content connection error: {e}")
        manager.disconnect_content(websocket, content_id)


@router.websocket("/ws/feed")
async def feed_websocket(
    websocket: WebSocket,
    domain: str = Query(default=None),
    user_id: str = Query(default="anonymous")
):
    """
    实时动态 WebSocket 连接

    推送：
    - 新通知
    - 新闻资讯
    - 社区热点
    - 活动提醒
    """
    await manager.connect_broadcast(websocket)

    try:
        # 发送连接确认
        await websocket.send_json({
            "type": "connected",
            "domain": domain,
            "message": "动态推送已连接"
        })

        while True:
            # 检查动态更新
            updates = await get_feed_updates(domain)
            if updates:
                await websocket.send_json(updates)

            # 等待10秒
            await asyncio.sleep(10)

    except WebSocketDisconnect:
        manager.disconnect_broadcast(websocket)
    except Exception as e:
        logger.error(f"[WS] Feed connection error: {e}")
        manager.disconnect_broadcast(websocket)


@router.websocket("/ws/user/{user_id}")
async def user_websocket(
    websocket: WebSocket,
    user_id: str,
    token: str = Query(default=""),
):
    """
    用户个人频道 WebSocket 连接（JWT认证）

    连接时需传 ?token=<JWT>，验证通过后才 accept。
    认证失败返回 close(4001, "unauthorized")。

    推送类型：
    - coach_push: 教练审批通过的推送
    - assessment: 评估相关通知
    - device_alert: 设备预警
    - system: 系统通知
    - 学习进度更新 / 成就解锁 / 奖励领取
    """
    # ── JWT 认证 ──
    if not token:
        await websocket.close(code=4001, reason="unauthorized: missing token")
        return

    try:
        payload = verify_token_with_blacklist(token, "access")
        if payload is None:
            await websocket.close(code=4001, reason="unauthorized: invalid token")
            return

        token_user_id = str(payload.get("user_id") or payload.get("sub") or "")
        if token_user_id != user_id:
            await websocket.close(code=4001, reason="unauthorized: user_id mismatch")
            return
    except Exception:
        await websocket.close(code=4001, reason="unauthorized: token verification failed")
        return

    # ── 认证通过，建立连接 ──
    await manager.connect_user(websocket, user_id)

    try:
        await websocket.send_json({
            "type": "connected",
            "user_id": user_id,
            "message": "个人频道已连接"
        })

        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0
                )

                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif data.get("action") == "progress_update":
                    await websocket.send_json({
                        "type": "progress_confirmed",
                        "data": data.get("progress")
                    })

            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})

    except WebSocketDisconnect:
        manager.disconnect_user(websocket, user_id)
    except Exception as e:
        logger.error(f"[WS] User connection error: {e}")
        manager.disconnect_user(websocket, user_id)


# ============================================================================
# 辅助函数：供其他模块调用推送消息
# ============================================================================

async def push_content_update(content_id: str, update_type: str, data: dict):
    """推送内容更新（供其他API调用）"""
    await manager.send_to_content(content_id, {
        "type": update_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    })


async def push_user_notification(user_id: str, notification: dict):
    """推送用户通知（供其他API调用）"""
    await manager.send_to_user(user_id, {
        "type": "notification",
        "data": notification,
        "timestamp": datetime.now().isoformat()
    })


async def push_broadcast(message: dict):
    """全局广播（供其他API调用）"""
    await manager.broadcast({
        **message,
        "timestamp": datetime.now().isoformat()
    })


# 导出
__all__ = [
    "router",
    "manager",
    "push_content_update",
    "push_user_notification",
    "push_broadcast"
]
