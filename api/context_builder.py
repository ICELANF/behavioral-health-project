# -*- coding: utf-8 -*-
"""
用户上下文聚合 - 为 Dify 工作流构建 inputs

聚合用户阶段、风险、设备数据等信息注入 Dify inputs 字典
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
from loguru import logger


def build_dify_inputs(user_id: int, state: Optional[Dict] = None) -> Dict[str, str]:
    """
    聚合用户上下文数据，构建 Dify inputs 字典

    Args:
        user_id: 用户ID
        state: 用户状态（来自 get_user_state()），若不传则尝试获取

    Returns:
        inputs 字典，所有值为字符串类型（Dify 要求）
    """
    # 如果未传入 state，尝试获取
    if state is None:
        try:
            from api.miniprogram import get_user_state
            state = get_user_state(user_id)
        except Exception as e:
            logger.warning(f"[ContextBuilder] 无法获取用户状态: {e}")
            state = {}

    inputs = {}

    # behavior_stage — 当前干预阶段
    inputs["behavior_stage"] = state.get("stage", "ONBOARDING")

    # risk_level — 当前风险等级
    inputs["risk_level"] = state.get("risk_level", "LOW")

    # day_index — 干预第几天
    inputs["day_index"] = str(state.get("day_index", 1))

    # device_summary — 最近设备数据文本摘要
    inputs["device_summary"] = _build_device_summary(user_id)

    return inputs


def _build_device_summary(user_id: int) -> str:
    """
    构建最近设备数据的文本摘要

    尝试从数据库查询最近的血糖、睡眠、HRV 数据
    若查询失败则返回"暂无设备数据"
    """
    parts = []

    try:
        from api.session import db_transaction
        from api.device_data import GlucoseReading, SleepRecord, HRVReading
    except ImportError:
        return "暂无设备数据"

    try:
        with db_transaction() as db:
            # 最近血糖
            recent_glucose = (
                db.query(GlucoseReading)
                .filter(GlucoseReading.user_id == user_id)
                .order_by(GlucoseReading.recorded_at.desc())
                .limit(3)
                .all()
            )
            if recent_glucose:
                values = [f"{r.value:.1f}" for r in recent_glucose]
                parts.append(f"近期血糖: {', '.join(values)} mmol/L")

            # 最近睡眠
            recent_sleep = (
                db.query(SleepRecord)
                .filter(SleepRecord.user_id == user_id)
                .order_by(SleepRecord.sleep_date.desc())
                .first()
            )
            if recent_sleep:
                duration_h = (recent_sleep.total_minutes or 0) / 60
                parts.append(f"昨晚睡眠: {duration_h:.1f}小时")

            # 最近HRV
            recent_hrv = (
                db.query(HRVReading)
                .filter(HRVReading.user_id == user_id)
                .order_by(HRVReading.recorded_at.desc())
                .first()
            )
            if recent_hrv and recent_hrv.sdnn:
                parts.append(f"HRV(SDNN): {recent_hrv.sdnn:.0f}ms")

    except Exception as e:
        logger.debug(f"[ContextBuilder] 设备数据查询失败（可忽略）: {e}")

    return "; ".join(parts) if parts else "暂无设备数据"
