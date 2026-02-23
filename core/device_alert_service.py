# -*- coding: utf-8 -*-
"""
设备预警服务
Device Alert Service

检查设备数据是否超过预警阈值，创建预警记录，
同时向教练和服务对象发送通知。
"""
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from loguru import logger


class DeviceAlertService:
    """设备预警检查 + 双向通知"""

    def __init__(self):
        self._thresholds = None

    def _load_thresholds(self):
        """懒加载预警阈值配置"""
        if self._thresholds is not None:
            return
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "configs", "alert_thresholds.json"
        )
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._thresholds = json.load(f)
        except Exception as e:
            logger.error(f"加载预警阈值配置失败: {e}")
            self._thresholds = {}

    def check_glucose(self, db: Session, user_id: int, value: float) -> Optional[Any]:
        """检查血糖值是否触发预警"""
        self._load_thresholds()
        glucose_cfg = self._thresholds.get("glucose", {})

        # Check danger high first, then warning high, then lows
        danger_high = glucose_cfg.get("danger_high", {})
        if value >= danger_high.get("value", 999):
            return self._create_alert(
                db, user_id,
                alert_type="glucose_danger_high",
                severity="danger",
                message=danger_high.get("message", "血糖危险偏高"),
                data_value=value,
                threshold_value=danger_high["value"],
                data_type="glucose",
            )

        warning_high = glucose_cfg.get("warning_high", {})
        if value >= warning_high.get("value", 999):
            return self._create_alert(
                db, user_id,
                alert_type="glucose_warning_high",
                severity="warning",
                message=warning_high.get("message", "血糖偏高"),
                data_value=value,
                threshold_value=warning_high["value"],
                data_type="glucose",
            )

        warning_low = glucose_cfg.get("warning_low", {})
        if value <= warning_low.get("value", 0):
            return self._create_alert(
                db, user_id,
                alert_type="glucose_danger_low",
                severity="danger",
                message=warning_low.get("message", "血糖极低"),
                data_value=value,
                threshold_value=warning_low["value"],
                data_type="glucose",
            )

        danger_low = glucose_cfg.get("danger_low", {})
        if value <= danger_low.get("value", 0):
            return self._create_alert(
                db, user_id,
                alert_type="glucose_danger_low",
                severity="danger",
                message=danger_low.get("message", "血糖危险偏低"),
                data_value=value,
                threshold_value=danger_low["value"],
                data_type="glucose",
            )

        return None

    def check_heart_rate(self, db: Session, user_id: int, hr: int, activity_type: Optional[str] = None) -> Optional[Any]:
        """检查心率是否触发预警"""
        self._load_thresholds()
        hr_cfg = self._thresholds.get("heart_rate", {})

        # High HR checks (rest_only means only trigger during rest)
        danger_high = hr_cfg.get("danger_high", {})
        is_rest = activity_type in (None, "rest", "sleep")
        if danger_high.get("rest_only", True) and not is_rest:
            pass  # skip non-rest
        elif hr >= danger_high.get("value", 999):
            return self._create_alert(
                db, user_id,
                alert_type="hr_danger_high",
                severity="danger",
                message=danger_high.get("message", "心率危险偏高"),
                data_value=float(hr),
                threshold_value=float(danger_high["value"]),
                data_type="heart_rate",
            )

        warning_high = hr_cfg.get("warning_high", {})
        if warning_high.get("rest_only", True) and not is_rest:
            pass
        elif hr >= warning_high.get("value", 999):
            return self._create_alert(
                db, user_id,
                alert_type="hr_warning_high",
                severity="warning",
                message=warning_high.get("message", "心率偏高"),
                data_value=float(hr),
                threshold_value=float(warning_high["value"]),
                data_type="heart_rate",
            )

        # Low HR checks (regardless of activity)
        danger_low = hr_cfg.get("danger_low", {})
        if hr <= danger_low.get("value", 0):
            return self._create_alert(
                db, user_id,
                alert_type="hr_danger_low",
                severity="danger",
                message=danger_low.get("message", "心率危险偏低"),
                data_value=float(hr),
                threshold_value=float(danger_low["value"]),
                data_type="heart_rate",
            )

        warning_low = hr_cfg.get("warning_low", {})
        if hr <= warning_low.get("value", 0):
            return self._create_alert(
                db, user_id,
                alert_type="hr_warning_low",
                severity="warning",
                message=warning_low.get("message", "心率偏低"),
                data_value=float(hr),
                threshold_value=float(warning_low["value"]),
                data_type="heart_rate",
            )

        return None

    def check_activity(self, db: Session, user_id: int, activity_record: Dict[str, Any]) -> Optional[Any]:
        """检查活动数据是否触发预警"""
        self._load_thresholds()
        exercise_cfg = self._thresholds.get("exercise", {})

        # Check excessive exercise
        moderate_min = activity_record.get("moderate_active_min", 0)
        vigorous_min = activity_record.get("vigorous_active_min", 0)
        total_active = moderate_min + vigorous_min

        excessive = exercise_cfg.get("warning_excessive", {})
        if total_active >= excessive.get("value", 999):
            return self._create_alert(
                db, user_id,
                alert_type="exercise_excessive",
                severity="warning",
                message=excessive.get("message", "运动量过大"),
                data_value=float(total_active),
                threshold_value=float(excessive["value"]),
                data_type="exercise",
            )

        # Check sedentary
        sedentary_min = activity_record.get("sedentary_min", 0)
        sedentary_cfg = exercise_cfg.get("warning_sedentary", {})
        if sedentary_min >= sedentary_cfg.get("value", 999):
            return self._create_alert(
                db, user_id,
                alert_type="exercise_sedentary",
                severity="warning",
                message=sedentary_cfg.get("message", "久坐时间过长"),
                data_value=float(sedentary_min),
                threshold_value=float(sedentary_cfg["value"]),
                data_type="exercise",
            )

        return None

    def check_sleep(self, db: Session, user_id: int, sleep_record: Dict[str, Any]) -> Optional[Any]:
        """检查睡眠数据是否触发预警"""
        self._load_thresholds()
        sleep_cfg = self._thresholds.get("sleep", {})

        # Check low sleep score
        score = sleep_record.get("sleep_score")
        if score is not None:
            low_score = sleep_cfg.get("warning_low_score", {})
            if score <= low_score.get("value", 0):
                return self._create_alert(
                    db, user_id,
                    alert_type="sleep_low_score",
                    severity="warning",
                    message=low_score.get("message", "睡眠质量差"),
                    data_value=float(score),
                    threshold_value=float(low_score["value"]),
                    data_type="sleep",
                )

        # Check short sleep
        duration = sleep_record.get("total_duration_min")
        if duration is not None:
            short = sleep_cfg.get("warning_short", {})
            if duration <= short.get("value", 0):
                return self._create_alert(
                    db, user_id,
                    alert_type="sleep_short",
                    severity="warning",
                    message=short.get("message", "睡眠不足"),
                    data_value=float(duration),
                    threshold_value=float(short["value"]),
                    data_type="sleep",
                )

        return None

    def _create_alert(
        self, db: Session, user_id: int,
        alert_type: str, severity: str, message: str,
        data_value: float, threshold_value: float, data_type: str,
    ) -> Optional[Any]:
        """
        创建预警记录 (含去重 + 双向通知)

        1. 去重: 同一用户+类型在1小时内不重复创建
        2. 查找用户的教练
        3. 创建 DeviceAlert 记录
        4. 创建 CoachMessage(type="alert") 通知教练
        5. 创建 Reminder(source="system") 通知用户
        """
        from core.models import DeviceAlert, User, CoachMessage, Reminder

        now = datetime.utcnow()
        dedup_key = f"{user_id}:{alert_type}:{now.strftime('%Y-%m-%d-%H')}"

        # 去重检查
        existing = db.query(DeviceAlert).filter(
            DeviceAlert.dedup_key == dedup_key
        ).first()
        if existing:
            logger.debug(f"预警去重: {dedup_key}")
            return None

        # 查找教练 (权威源: coach_student_bindings)
        user = db.query(User).filter(User.id == user_id).first()
        coach_id = None
        try:
            from sqlalchemy import text as sa_text
            row = db.execute(sa_text(
                "SELECT coach_id FROM coach_schema.coach_student_bindings "
                "WHERE student_id = :sid AND is_active = true LIMIT 1"
            ), {"sid": user_id}).first()
            coach_id = row[0] if row else None
        except Exception:
            pass

        # 创建 DeviceAlert
        alert = DeviceAlert(
            user_id=user_id,
            coach_id=coach_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            data_value=data_value,
            threshold_value=threshold_value,
            data_type=data_type,
            dedup_key=dedup_key,
        )
        db.add(alert)
        db.flush()

        # 通知教练 (CoachMessage) — 直接通知
        if coach_id:
            coach_msg = CoachMessage(
                coach_id=coach_id,
                student_id=user_id,
                content=f"[健康预警] {user.full_name or user.username}: {message}（实际值: {data_value}）",
                message_type="alert",
            )
            db.add(coach_msg)

        # 通知用户 (Reminder)
        reminder = Reminder(
            user_id=user_id,
            type="alert",
            title=f"健康预警: {message}",
            content=f"您的{data_type}数据异常: {message}（当前值: {data_value}）",
            source="system",
            is_active=True,
        )
        db.add(reminder)

        # 创建推送审批队列条目（教练确认后再投递后续干预建议）
        if coach_id:
            try:
                from core import coach_push_queue_service as queue_svc
                queue_svc.create_queue_item(
                    db,
                    coach_id=coach_id,
                    student_id=user_id,
                    source_type="device_alert",
                    source_id=str(alert.id),
                    title=f"设备预警: {message}",
                    content=f"{data_type}数据异常: {message}（当前值: {data_value}, 阈值: {threshold_value}）",
                    content_extra={"alert_type": alert_type, "data_type": data_type, "data_value": data_value, "threshold_value": threshold_value},
                    priority="high" if severity == "danger" else "normal",
                )
            except Exception as e:
                logger.warning(f"[DeviceAlert] 创建推送队列失败: {e}")

        logger.info(f"[DeviceAlert] 已创建预警: user={user_id} type={alert_type} severity={severity} value={data_value}")
        return alert
