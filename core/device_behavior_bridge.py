# -*- coding: utf-8 -*-
"""
DeviceBehaviorBridge - 设备数据→行为事实桥接

职责:
- 将设备数据（步数/睡眠/血糖）自动转化为行为事实
- 自动完成对应领域的今日微行动任务
- 由 device_rest_api.py 在数据写入后调用
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from loguru import logger

from core.micro_action_service import MicroActionTaskService

# 默认目标阈值
DEFAULT_STEP_GOAL = 6000
DEFAULT_SLEEP_SCORE_GOAL = 70
DEFAULT_GLUCOSE_TARGET = 10.0  # 餐后2h血糖 mmol/L


class DeviceBehaviorBridge:
    """设备数据→行为事实转化"""

    def __init__(self):
        self.task_service = MicroActionTaskService()

    def process_activity(
        self,
        db: Session,
        user_id: int,
        steps: int,
        step_goal: int = DEFAULT_STEP_GOAL,
    ) -> Optional[Dict]:
        """
        处理活动数据

        步数 >= 目标 → 自动完成 exercise 领域今日任务
        """
        if steps < step_goal:
            return None

        task = self.task_service.auto_complete(
            db, user_id, "exercise",
            note=f"步数达标: {steps}/{step_goal}步",
        )
        if task:
            logger.info(f"[Bridge] exercise任务自动完成: user={user_id}, steps={steps}")
            return {"domain": "exercise", "task_id": task.id, "steps": steps}
        return None

    def process_sleep(
        self,
        db: Session,
        user_id: int,
        sleep_score: int,
        score_goal: int = DEFAULT_SLEEP_SCORE_GOAL,
    ) -> Optional[Dict]:
        """
        处理睡眠数据

        睡眠评分 >= 目标 → 自动完成 sleep 领域今日任务
        """
        if sleep_score < score_goal:
            return None

        task = self.task_service.auto_complete(
            db, user_id, "sleep",
            note=f"睡眠评分达标: {sleep_score}/{score_goal}",
        )
        if task:
            logger.info(f"[Bridge] sleep任务自动完成: user={user_id}, score={sleep_score}")
            return {"domain": "sleep", "task_id": task.id, "sleep_score": sleep_score}
        return None

    def process_glucose(
        self,
        db: Session,
        user_id: int,
        postprandial_value: float,
        target: float = DEFAULT_GLUCOSE_TARGET,
    ) -> Optional[Dict]:
        """
        处理血糖数据

        餐后血糖达标 → 自动完成 nutrition 相关任务
        """
        if postprandial_value > target or postprandial_value <= 0:
            return None

        task = self.task_service.auto_complete(
            db, user_id, "nutrition",
            note=f"餐后血糖达标: {postprandial_value}/{target} mmol/L",
        )
        if task:
            logger.info(f"[Bridge] nutrition任务自动完成: user={user_id}, glucose={postprandial_value}")
            return {"domain": "nutrition", "task_id": task.id, "glucose": postprandial_value}
        return None
