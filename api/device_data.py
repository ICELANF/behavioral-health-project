# -*- coding: utf-8 -*-
"""
设备数据接入 API
Device Data Integration API

Phase 1 实现：
- 设备管理（绑定/解绑/列表）
- 血糖数据（手动录入/查询/统计）
- 体重数据（录入/查询）
- 今日健康概览
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Header
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from loguru import logger
import enum

from api.dependencies import get_current_user
from core.database import get_db_session, db_transaction
from core.models import (
    UserDevice, DeviceType, DeviceStatus,
    GlucoseReading, HeartRateReading, HRVReading,
    SleepRecord, ActivityRecord, WorkoutRecord, VitalSign
)

router = APIRouter(prefix="/device", tags=["设备数据"])


# ============================================
# Pydantic 模型
# ============================================

class DeviceTypeEnum(str, enum.Enum):
    CGM = "cgm"
    GLUCOMETER = "glucometer"
    SMARTWATCH = "smartwatch"
    SMARTBAND = "smartband"
    SCALE = "scale"
    BP_MONITOR = "bp_monitor"


class DeviceInfo(BaseModel):
    """设备信息"""
    device_id: str
    device_type: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    status: str
    battery_level: Optional[int] = None
    last_sync_at: Optional[str] = None


class DeviceBindRequest(BaseModel):
    """设备绑定请求"""
    device_type: DeviceTypeEnum
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None


class GlucoseReadingInput(BaseModel):
    """血糖录入"""
    value: float = Field(..., ge=1.0, le=35.0, description="血糖值 mmol/L")
    unit: str = Field(default="mmol/L")
    meal_tag: Optional[str] = Field(None, description="餐标: fasting/before_meal/after_meal/bedtime")
    timestamp: Optional[datetime] = None
    notes: Optional[str] = None

    @validator('meal_tag')
    def validate_meal_tag(cls, v):
        if v and v not in ['fasting', 'before_meal', 'after_meal', 'bedtime']:
            raise ValueError('Invalid meal_tag')
        return v


class GlucoseReadingResponse(BaseModel):
    """血糖读数响应"""
    id: int
    value: float
    value_mgdl: float
    unit: str
    trend: Optional[str] = None
    trend_arrow: Optional[str] = None
    source: str
    meal_tag: Optional[str] = None
    recorded_at: str
    notes: Optional[str] = None


class GlucoseStatistics(BaseModel):
    """血糖统计"""
    avg_glucose: Optional[float] = None
    min_glucose: Optional[float] = None
    max_glucose: Optional[float] = None
    std_glucose: Optional[float] = None
    cv: Optional[float] = None
    time_in_range: Optional[float] = None
    time_below_range: Optional[float] = None
    time_above_range: Optional[float] = None
    readings_count: int = 0


class WeightInput(BaseModel):
    """体重录入"""
    weight_kg: float = Field(..., ge=20.0, le=300.0)
    body_fat_percent: Optional[float] = Field(None, ge=3.0, le=60.0)
    muscle_mass_kg: Optional[float] = None
    timestamp: Optional[datetime] = None


class WeightResponse(BaseModel):
    """体重响应"""
    id: int
    weight_kg: float
    bmi: Optional[float] = None
    body_fat_percent: Optional[float] = None
    muscle_mass_kg: Optional[float] = None
    recorded_at: str


class BloodPressureInput(BaseModel):
    """血压录入"""
    systolic: int = Field(..., ge=60, le=250, description="收缩压")
    diastolic: int = Field(..., ge=40, le=150, description="舒张压")
    pulse: Optional[int] = Field(None, ge=30, le=200)
    timestamp: Optional[datetime] = None


class DashboardResponse(BaseModel):
    """今日仪表盘"""
    date: str
    glucose: Optional[Dict[str, Any]] = None
    activity: Optional[Dict[str, Any]] = None
    sleep: Optional[Dict[str, Any]] = None
    weight: Optional[Dict[str, Any]] = None
    alerts: List[Dict[str, Any]] = []


# ============================================
# 辅助函数
# ============================================

def mmol_to_mgdl(mmol: float) -> float:
    """mmol/L 转 mg/dL"""
    return round(mmol * 18.0182, 1)


def get_trend_arrow(trend: Optional[str]) -> Optional[str]:
    """获取趋势箭头"""
    arrows = {
        'rising_fast': '↑↑',
        'rising': '↑',
        'stable': '→',
        'falling': '↓',
        'falling_fast': '↓↓'
    }
    return arrows.get(trend)


def calculate_glucose_stats(readings: List[GlucoseReading]) -> GlucoseStatistics:
    """计算血糖统计"""
    if not readings:
        return GlucoseStatistics()

    values = [r.value for r in readings]
    avg = sum(values) / len(values)

    # 标准差
    if len(values) > 1:
        variance = sum((x - avg) ** 2 for x in values) / len(values)
        std = variance ** 0.5
        cv = (std / avg) * 100 if avg > 0 else 0
    else:
        std = 0
        cv = 0

    # 范围时间 (TIR: 3.9-10.0)
    in_range = sum(1 for v in values if 3.9 <= v <= 10.0)
    below = sum(1 for v in values if v < 3.9)
    above = sum(1 for v in values if v > 10.0)
    total = len(values)

    return GlucoseStatistics(
        avg_glucose=round(avg, 2),
        min_glucose=round(min(values), 2),
        max_glucose=round(max(values), 2),
        std_glucose=round(std, 2),
        cv=round(cv, 1),
        time_in_range=round(in_range / total * 100, 1) if total > 0 else None,
        time_below_range=round(below / total * 100, 1) if total > 0 else None,
        time_above_range=round(above / total * 100, 1) if total > 0 else None,
        readings_count=total
    )


# DEPRECATED: 建议端点直接使用 Depends(get_current_user)
async def get_current_user_id(
    current_user=Depends(get_current_user),
) -> int:
    """获取当前用户ID (JWT认证)"""
    return current_user.id


# ============================================
# 设备管理 API
# ============================================

@router.get("/devices", response_model=Dict[str, Any])
async def list_devices(user_id: int = Depends(get_current_user_id)):
    """
    获取用户已绑定的设备列表
    """
    try:
        with db_transaction() as db:
            devices = db.query(UserDevice).filter(
                UserDevice.user_id == user_id
            ).order_by(UserDevice.created_at.desc()).all()

            return {
                "devices": [
                    {
                        "device_id": d.device_id,
                        "device_type": d.device_type.value if d.device_type else None,
                        "manufacturer": d.manufacturer,
                        "model": d.model,
                        "status": d.status.value if d.status else "unknown",
                        "battery_level": d.battery_level,
                        "last_sync_at": d.last_sync_at.isoformat() if d.last_sync_at else None
                    }
                    for d in devices
                ],
                "total": len(devices)
            }
    except Exception as e:
        logger.error(f"List devices error: {e}")
        return {"devices": [], "total": 0}


@router.post("/devices/bind")
async def bind_device(
    request: DeviceBindRequest,
    user_id: int = Depends(get_current_user_id)
):
    """
    绑定新设备
    """
    import uuid

    try:
        with db_transaction() as db:
            # 生成设备ID
            device_id = f"{request.device_type.value}_{user_id}_{uuid.uuid4().hex[:8]}"

            # 检查是否已绑定同类型设备
            existing = db.query(UserDevice).filter(
                UserDevice.user_id == user_id,
                UserDevice.device_type == DeviceType(request.device_type.value)
            ).first()

            if existing:
                # 更新现有设备
                existing.manufacturer = request.manufacturer
                existing.model = request.model
                existing.serial_number = request.serial_number
                existing.status = DeviceStatus.CONNECTED
                existing.updated_at = datetime.utcnow()
                device_id = existing.device_id
                logger.info(f"[Device] Updated device: {device_id}")
            else:
                # 创建新设备
                device = UserDevice(
                    user_id=user_id,
                    device_id=device_id,
                    device_type=DeviceType(request.device_type.value),
                    manufacturer=request.manufacturer,
                    model=request.model,
                    serial_number=request.serial_number,
                    status=DeviceStatus.CONNECTED
                )
                db.add(device)
                logger.info(f"[Device] Bound new device: {device_id}")

            return {
                "success": True,
                "device_id": device_id,
                "message": "设备绑定成功"
            }

    except Exception as e:
        logger.error(f"Bind device error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/devices/{device_id}")
async def unbind_device(
    device_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    解绑设备
    """
    try:
        with db_transaction() as db:
            device = db.query(UserDevice).filter(
                UserDevice.device_id == device_id,
                UserDevice.user_id == user_id
            ).first()

            if not device:
                raise HTTPException(status_code=404, detail="设备不存在")

            db.delete(device)
            logger.info(f"[Device] Unbound device: {device_id}")

            return {"success": True, "message": "设备已解绑"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unbind device error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 血糖数据 API
# ============================================

@router.post("/glucose/manual")
async def record_glucose_manual(
    reading: GlucoseReadingInput,
    user_id: int = Depends(get_current_user_id)
):
    """
    手动记录血糖
    """
    try:
        with db_transaction() as db:
            recorded_at = reading.timestamp or datetime.utcnow()

            glucose = GlucoseReading(
                user_id=user_id,
                value=reading.value,
                unit=reading.unit,
                source="manual",
                meal_tag=reading.meal_tag,
                notes=reading.notes,
                recorded_at=recorded_at
            )
            db.add(glucose)
            db.flush()

            logger.info(f"[Glucose] Manual record: user={user_id}, value={reading.value}")

            # 设备预警检查
            try:
                from core.device_alert_service import DeviceAlertService
                alert_svc = DeviceAlertService()
                alert_svc.check_glucose(db, user_id, reading.value)
            except Exception as e:
                logger.warning(f"DeviceAlertService glucose检查失败: {e}")

            return {
                "success": True,
                "reading_id": glucose.id,
                "value": reading.value,
                "value_mgdl": mmol_to_mgdl(reading.value),
                "recorded_at": recorded_at.isoformat()
            }

    except Exception as e:
        logger.error(f"Record glucose error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/glucose")
async def get_glucose_readings(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    limit: int = Query(100, ge=1, le=1000),
    user_id: int = Depends(get_current_user_id)
):
    """
    获取血糖数据
    """
    try:
        with db_transaction() as db:
            query = db.query(GlucoseReading).filter(
                GlucoseReading.user_id == user_id
            )

            # 日期过滤
            if start_date:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(GlucoseReading.recorded_at >= start)
            if end_date:
                end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(GlucoseReading.recorded_at < end)

            readings = query.order_by(
                GlucoseReading.recorded_at.desc()
            ).limit(limit).all()

            # 计算统计
            stats = calculate_glucose_stats(readings)

            return {
                "readings": [
                    {
                        "id": r.id,
                        "value": r.value,
                        "value_mgdl": mmol_to_mgdl(r.value),
                        "unit": r.unit,
                        "trend": r.trend,
                        "trend_arrow": get_trend_arrow(r.trend),
                        "source": r.source,
                        "meal_tag": r.meal_tag,
                        "recorded_at": r.recorded_at.isoformat(),
                        "notes": r.notes
                    }
                    for r in readings
                ],
                "statistics": stats.dict(),
                "period": {
                    "start": start_date,
                    "end": end_date,
                    "count": len(readings)
                }
            }

    except Exception as e:
        logger.error(f"Get glucose error: {e}")
        return {"readings": [], "statistics": {}, "period": {}}


@router.get("/glucose/current")
async def get_current_glucose(user_id: int = Depends(get_current_user_id)):
    """
    获取最新血糖读数
    """
    try:
        with db_transaction() as db:
            reading = db.query(GlucoseReading).filter(
                GlucoseReading.user_id == user_id
            ).order_by(GlucoseReading.recorded_at.desc()).first()

            if not reading:
                return {"message": "暂无血糖数据", "value": None}

            minutes_ago = int((datetime.utcnow() - reading.recorded_at).total_seconds() / 60)
            in_range = 3.9 <= reading.value <= 10.0

            return {
                "value": reading.value,
                "value_mgdl": mmol_to_mgdl(reading.value),
                "trend": reading.trend,
                "trend_arrow": get_trend_arrow(reading.trend),
                "timestamp": reading.recorded_at.isoformat(),
                "source": reading.source,
                "minutes_ago": minutes_ago,
                "in_range": in_range,
                "status": "good" if in_range else ("low" if reading.value < 3.9 else "high")
            }

    except Exception as e:
        logger.error(f"Get current glucose error: {e}")
        return {"value": None, "message": str(e)}


@router.get("/glucose/chart/daily")
async def get_glucose_daily_chart(
    date: str = Query(..., description="日期 YYYY-MM-DD"),
    user_id: int = Depends(get_current_user_id)
):
    """
    获取每日血糖图表数据
    """
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d")
        next_date = target_date + timedelta(days=1)

        with db_transaction() as db:
            readings = db.query(GlucoseReading).filter(
                GlucoseReading.user_id == user_id,
                GlucoseReading.recorded_at >= target_date,
                GlucoseReading.recorded_at < next_date
            ).order_by(GlucoseReading.recorded_at).all()

            if not readings:
                return {
                    "date": date,
                    "chart_data": {"timestamps": [], "values": []},
                    "daily_stats": None,
                    "message": "当天无血糖数据"
                }

            timestamps = [r.recorded_at.strftime("%H:%M") for r in readings]
            values = [r.value for r in readings]

            stats = calculate_glucose_stats(readings)

            return {
                "date": date,
                "chart_data": {
                    "timestamps": timestamps,
                    "values": values,
                    "target_low": 3.9,
                    "target_high": 10.0
                },
                "daily_stats": {
                    "avg": stats.avg_glucose,
                    "min": stats.min_glucose,
                    "max": stats.max_glucose,
                    "tir": stats.time_in_range,
                    "count": stats.readings_count
                }
            }

    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Get glucose chart error: {e}")
        return {"date": date, "chart_data": {}, "error": str(e)}


# ============================================
# 体重/体征数据 API
# ============================================

@router.post("/weight")
async def record_weight(
    data: WeightInput,
    user_id: int = Depends(get_current_user_id)
):
    """
    记录体重
    """
    try:
        with db_transaction() as db:
            recorded_at = data.timestamp or datetime.utcnow()

            # BMI 需要用户身高 (后续从 behavioral_profiles 获取)
            bmi = None

            vital = VitalSign(
                user_id=user_id,
                data_type="weight",
                weight_kg=data.weight_kg,
                bmi=bmi,
                body_fat_percent=data.body_fat_percent,
                muscle_mass_kg=data.muscle_mass_kg,
                recorded_at=recorded_at
            )
            db.add(vital)
            db.flush()

            logger.info(f"[Weight] Record: user={user_id}, weight={data.weight_kg}kg")

            return {
                "success": True,
                "record_id": vital.id,
                "weight_kg": data.weight_kg,
                "recorded_at": recorded_at.isoformat()
            }

    except Exception as e:
        logger.error(f"Record weight error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weight")
async def get_weight_records(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(30, ge=1, le=365),
    user_id: int = Depends(get_current_user_id)
):
    """
    获取体重记录
    """
    try:
        with db_transaction() as db:
            query = db.query(VitalSign).filter(
                VitalSign.user_id == user_id,
                VitalSign.data_type == "weight"
            )

            if start_date:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(VitalSign.recorded_at >= start)
            if end_date:
                end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(VitalSign.recorded_at < end)

            records = query.order_by(VitalSign.recorded_at.desc()).limit(limit).all()

            # 计算趋势
            trend = None
            if len(records) >= 2:
                diff = records[0].weight_kg - records[-1].weight_kg
                if diff < -0.5:
                    trend = "decreasing"
                elif diff > 0.5:
                    trend = "increasing"
                else:
                    trend = "stable"

            return {
                "records": [
                    {
                        "id": r.id,
                        "weight_kg": r.weight_kg,
                        "bmi": r.bmi,
                        "body_fat_percent": r.body_fat_percent,
                        "muscle_mass_kg": r.muscle_mass_kg,
                        "recorded_at": r.recorded_at.isoformat()
                    }
                    for r in records
                ],
                "trend": {
                    "direction": trend,
                    "period_days": (records[0].recorded_at - records[-1].recorded_at).days if len(records) >= 2 else 0,
                    "weight_change_kg": round(records[0].weight_kg - records[-1].weight_kg, 1) if len(records) >= 2 else 0
                } if records else None,
                "total": len(records)
            }

    except Exception as e:
        logger.error(f"Get weight error: {e}")
        return {"records": [], "trend": None, "total": 0}


@router.post("/blood-pressure")
async def record_blood_pressure(
    data: BloodPressureInput,
    user_id: int = Depends(get_current_user_id)
):
    """
    记录血压
    """
    try:
        with db_transaction() as db:
            recorded_at = data.timestamp or datetime.utcnow()

            vital = VitalSign(
                user_id=user_id,
                data_type="blood_pressure",
                systolic=data.systolic,
                diastolic=data.diastolic,
                pulse=data.pulse,
                recorded_at=recorded_at
            )
            db.add(vital)
            db.flush()

            logger.info(f"[BP] Record: user={user_id}, {data.systolic}/{data.diastolic}")

            # 判断血压分类
            if data.systolic < 120 and data.diastolic < 80:
                classification = "正常"
            elif data.systolic < 130 and data.diastolic < 85:
                classification = "正常偏高"
            elif data.systolic < 140 or data.diastolic < 90:
                classification = "1级高血压"
            else:
                classification = "2级高血压"

            return {
                "success": True,
                "record_id": vital.id,
                "systolic": data.systolic,
                "diastolic": data.diastolic,
                "classification": classification,
                "recorded_at": recorded_at.isoformat()
            }

    except Exception as e:
        logger.error(f"Record BP error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/blood-pressure")
async def get_blood_pressure_records(
    limit: int = Query(30, ge=1, le=100),
    user_id: int = Depends(get_current_user_id)
):
    """
    获取血压记录
    """
    try:
        with db_transaction() as db:
            records = db.query(VitalSign).filter(
                VitalSign.user_id == user_id,
                VitalSign.data_type == "blood_pressure"
            ).order_by(VitalSign.recorded_at.desc()).limit(limit).all()

            # 计算平均值
            avg_systolic = None
            avg_diastolic = None
            if records:
                avg_systolic = round(sum(r.systolic for r in records if r.systolic) / len(records))
                avg_diastolic = round(sum(r.diastolic for r in records if r.diastolic) / len(records))

            return {
                "records": [
                    {
                        "id": r.id,
                        "systolic": r.systolic,
                        "diastolic": r.diastolic,
                        "pulse": r.pulse,
                        "recorded_at": r.recorded_at.isoformat()
                    }
                    for r in records
                ],
                "statistics": {
                    "avg_systolic": avg_systolic,
                    "avg_diastolic": avg_diastolic,
                    "count": len(records)
                },
                "total": len(records)
            }

    except Exception as e:
        logger.error(f"Get BP error: {e}")
        return {"records": [], "statistics": {}, "total": 0}


# ============================================
# 仪表盘 API
# ============================================

@router.get("/dashboard/today", response_model=DashboardResponse)
async def get_today_dashboard(user_id: int = Depends(get_current_user_id)):
    """
    获取今日健康概览
    """
    try:
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today + timedelta(days=1), datetime.min.time())

        with db_transaction() as db:
            # 血糖数据
            glucose_readings = db.query(GlucoseReading).filter(
                GlucoseReading.user_id == user_id,
                GlucoseReading.recorded_at >= today_start,
                GlucoseReading.recorded_at < today_end
            ).order_by(GlucoseReading.recorded_at.desc()).all()

            glucose_data = None
            if glucose_readings:
                latest = glucose_readings[0]
                stats = calculate_glucose_stats(glucose_readings)
                in_range = 3.9 <= latest.value <= 10.0
                glucose_data = {
                    "current": latest.value,
                    "current_mgdl": mmol_to_mgdl(latest.value),
                    "trend": latest.trend,
                    "trend_arrow": get_trend_arrow(latest.trend),
                    "avg_today": stats.avg_glucose,
                    "tir_today": stats.time_in_range,
                    "readings_count": stats.readings_count,
                    "status": "good" if in_range else ("low" if latest.value < 3.9 else "high"),
                    "last_reading_at": latest.recorded_at.isoformat()
                }

            # 活动数据
            activity = db.query(ActivityRecord).filter(
                ActivityRecord.user_id == user_id,
                ActivityRecord.activity_date == today.isoformat()
            ).first()

            activity_data = None
            if activity:
                steps_goal = 10000
                activity_data = {
                    "steps": activity.steps,
                    "steps_goal": steps_goal,
                    "progress_percent": round(activity.steps / steps_goal * 100, 1),
                    "distance_km": round(activity.distance_m / 1000, 2) if activity.distance_m else 0,
                    "calories_active": activity.calories_active,
                    "active_minutes": activity.light_active_min + activity.moderate_active_min + activity.vigorous_active_min
                }

            # 睡眠数据 (昨晚)
            yesterday = (today - timedelta(days=1)).isoformat()
            sleep = db.query(SleepRecord).filter(
                SleepRecord.user_id == user_id,
                SleepRecord.sleep_date == yesterday
            ).first()

            sleep_data = None
            if sleep:
                sleep_data = {
                    "duration_hours": round(sleep.total_duration_min / 60, 1) if sleep.total_duration_min else None,
                    "score": sleep.sleep_score,
                    "deep_percent": round(sleep.deep_min / sleep.total_duration_min * 100, 1) if sleep.total_duration_min else None,
                    "status": "good" if sleep.sleep_score and sleep.sleep_score >= 70 else "needs_attention"
                }

            # 最新体重
            latest_weight = db.query(VitalSign).filter(
                VitalSign.user_id == user_id,
                VitalSign.data_type == "weight"
            ).order_by(VitalSign.recorded_at.desc()).first()

            weight_data = None
            if latest_weight:
                weight_data = {
                    "weight_kg": latest_weight.weight_kg,
                    "bmi": latest_weight.bmi,
                    "recorded_at": latest_weight.recorded_at.isoformat()
                }

            # 告警
            alerts = []
            if glucose_data:
                if glucose_data["current"] > 13.9:
                    alerts.append({
                        "type": "glucose_very_high",
                        "message": f"血糖偏高 ({glucose_data['current']} mmol/L)，请注意",
                        "severity": "danger"
                    })
                elif glucose_data["current"] > 10.0:
                    alerts.append({
                        "type": "glucose_high",
                        "message": f"血糖偏高 ({glucose_data['current']} mmol/L)",
                        "severity": "warning"
                    })
                elif glucose_data["current"] < 3.9:
                    alerts.append({
                        "type": "glucose_low",
                        "message": f"血糖偏低 ({glucose_data['current']} mmol/L)，请及时进食",
                        "severity": "danger"
                    })

            return DashboardResponse(
                date=today.isoformat(),
                glucose=glucose_data,
                activity=activity_data,
                sleep=sleep_data,
                weight=weight_data,
                alerts=alerts
            )

    except Exception as e:
        logger.error(f"Get dashboard error: {e}")
        return DashboardResponse(
            date=datetime.utcnow().date().isoformat(),
            alerts=[{"type": "error", "message": str(e), "severity": "info"}]
        )


# ============================================
# 数据同步 API (基础版)
# ============================================

@router.post("/sync")
async def sync_device_data(
    device_id: str,
    data: Dict[str, Any],
    user_id: int = Depends(get_current_user_id)
):
    """
    同步设备数据 (通用接口)
    """
    try:
        records_processed = 0

        with db_transaction() as db:
            # 验证设备
            device = db.query(UserDevice).filter(
                UserDevice.device_id == device_id,
                UserDevice.user_id == user_id
            ).first()

            if not device:
                raise HTTPException(status_code=404, detail="设备未绑定")

            # 处理血糖数据
            if "glucose" in data and data["glucose"].get("readings"):
                for reading in data["glucose"]["readings"]:
                    glucose = GlucoseReading(
                        user_id=user_id,
                        device_id=device_id,
                        value=reading["value"],
                        trend=reading.get("trend"),
                        source="cgm" if device.device_type == DeviceType.CGM else "device",
                        meal_tag=reading.get("meal_tag"),
                        recorded_at=datetime.fromisoformat(reading["timestamp"].replace("Z", "+00:00"))
                    )
                    db.add(glucose)
                    records_processed += 1

            # 更新设备同步时间
            device.last_sync_at = datetime.utcnow()

        logger.info(f"[Sync] Device {device_id}: {records_processed} records")

        return {
            "success": True,
            "device_id": device_id,
            "records_processed": records_processed,
            "synced_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Phase 2: 增强同步功能
# ============================================

class SyncRequest(BaseModel):
    """同步请求"""
    device_id: str
    sync_type: str = "incremental"  # full/incremental
    data_types: List[str] = ["glucose"]
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    data: Dict[str, Any]


class SyncHistoryItem(BaseModel):
    """同步历史"""
    sync_id: str
    device_id: str
    sync_type: str
    data_types: List[str]
    status: str
    records_count: int
    synced_at: str
    error_message: Optional[str] = None


@router.post("/sync/batch")
async def sync_device_data_batch(
    request: SyncRequest,
    user_id: int = Depends(get_current_user_id)
):
    """
    批量同步设备数据 (增强版)

    支持多种数据类型:
    - glucose: 血糖数据
    - heart_rate: 心率数据
    - hrv: HRV数据
    - sleep: 睡眠数据
    - activity: 活动数据
    - workout: 运动记录
    """
    import uuid
    sync_id = f"sync_{uuid.uuid4().hex[:12]}"
    records_processed = 0
    records_new = 0
    errors = []

    try:
        with db_transaction() as db:
            # 验证设备
            device = db.query(UserDevice).filter(
                UserDevice.device_id == request.device_id,
                UserDevice.user_id == user_id
            ).first()

            if not device:
                raise HTTPException(status_code=404, detail="设备未绑定")

            data = request.data

            # 处理血糖数据
            if "glucose" in data and data["glucose"].get("readings"):
                for reading in data["glucose"]["readings"]:
                    try:
                        recorded_at = datetime.fromisoformat(
                            reading["timestamp"].replace("Z", "+00:00")
                        )
                        # 检查是否已存在
                        existing = db.query(GlucoseReading).filter(
                            GlucoseReading.user_id == user_id,
                            GlucoseReading.device_id == request.device_id,
                            GlucoseReading.recorded_at == recorded_at
                        ).first()

                        if not existing:
                            glucose = GlucoseReading(
                                user_id=user_id,
                                device_id=request.device_id,
                                value=reading["value"],
                                trend=reading.get("trend"),
                                trend_rate=reading.get("trend_rate"),
                                source="cgm" if device.device_type == DeviceType.CGM else "device",
                                meal_tag=reading.get("meal_tag"),
                                recorded_at=recorded_at
                            )
                            db.add(glucose)
                            records_new += 1
                        records_processed += 1
                    except Exception as e:
                        errors.append(f"glucose: {str(e)}")

            # 处理心率数据
            if "heart_rate" in data and data["heart_rate"].get("readings"):
                for reading in data["heart_rate"]["readings"]:
                    try:
                        recorded_at = datetime.fromisoformat(
                            reading["timestamp"].replace("Z", "+00:00")
                        )
                        hr = HeartRateReading(
                            user_id=user_id,
                            device_id=request.device_id,
                            hr=reading["hr"],
                            activity_type=reading.get("activity_type"),
                            recorded_at=recorded_at
                        )
                        db.add(hr)
                        records_processed += 1
                        records_new += 1
                    except Exception as e:
                        errors.append(f"heart_rate: {str(e)}")

            # 处理 HRV 数据
            if "hrv" in data and data["hrv"].get("readings"):
                for reading in data["hrv"]["readings"]:
                    try:
                        recorded_at = datetime.fromisoformat(
                            reading["timestamp"].replace("Z", "+00:00")
                        )
                        hrv = HRVReading(
                            user_id=user_id,
                            device_id=request.device_id,
                            sdnn=reading.get("sdnn"),
                            rmssd=reading.get("rmssd"),
                            lf=reading.get("lf"),
                            hf=reading.get("hf"),
                            lf_hf_ratio=reading.get("lf_hf_ratio"),
                            stress_score=reading.get("stress_score"),
                            recovery_score=reading.get("recovery_score"),
                            recorded_at=recorded_at
                        )
                        db.add(hrv)
                        records_processed += 1
                        records_new += 1
                    except Exception as e:
                        errors.append(f"hrv: {str(e)}")

            # 处理睡眠数据
            if "sleep" in data and data["sleep"].get("records"):
                for record in data["sleep"]["records"]:
                    try:
                        sleep_date = record.get("date") or record.get("sleep_date")
                        # 检查是否已存在
                        existing = db.query(SleepRecord).filter(
                            SleepRecord.user_id == user_id,
                            SleepRecord.sleep_date == sleep_date
                        ).first()

                        if existing:
                            # 更新现有记录
                            existing.total_duration_min = record.get("total_duration_min")
                            existing.sleep_score = record.get("sleep_score")
                            existing.deep_min = record.get("deep_min", 0)
                            existing.light_min = record.get("light_min", 0)
                            existing.rem_min = record.get("rem_min", 0)
                            existing.awake_min = record.get("awake_min", 0)
                            existing.awakenings = record.get("awakenings", 0)
                            existing.efficiency = record.get("efficiency")
                        else:
                            sleep = SleepRecord(
                                user_id=user_id,
                                device_id=request.device_id,
                                sleep_date=sleep_date,
                                sleep_start=datetime.fromisoformat(record["sleep_start"].replace("Z", "+00:00")) if record.get("sleep_start") else None,
                                sleep_end=datetime.fromisoformat(record["sleep_end"].replace("Z", "+00:00")) if record.get("sleep_end") else None,
                                total_duration_min=record.get("total_duration_min"),
                                awake_min=record.get("awake_min", 0),
                                light_min=record.get("light_min", 0),
                                deep_min=record.get("deep_min", 0),
                                rem_min=record.get("rem_min", 0),
                                sleep_score=record.get("sleep_score"),
                                efficiency=record.get("efficiency"),
                                awakenings=record.get("awakenings", 0),
                                avg_spo2=record.get("avg_spo2"),
                                min_spo2=record.get("min_spo2"),
                                stages_data=record.get("stages")
                            )
                            db.add(sleep)
                            records_new += 1
                        records_processed += 1
                    except Exception as e:
                        errors.append(f"sleep: {str(e)}")

            # 处理活动数据
            if "activity" in data and data["activity"].get("records"):
                for record in data["activity"]["records"]:
                    try:
                        activity_date = record.get("date") or record.get("activity_date")
                        existing = db.query(ActivityRecord).filter(
                            ActivityRecord.user_id == user_id,
                            ActivityRecord.activity_date == activity_date
                        ).first()

                        if existing:
                            # 更新
                            existing.steps = record.get("steps", existing.steps)
                            existing.distance_m = record.get("distance_m", existing.distance_m)
                            existing.calories_total = record.get("calories_total", existing.calories_total)
                            existing.calories_active = record.get("calories_active", existing.calories_active)
                        else:
                            activity = ActivityRecord(
                                user_id=user_id,
                                activity_date=activity_date,
                                steps=record.get("steps", 0),
                                distance_m=record.get("distance_m", 0),
                                floors_climbed=record.get("floors_climbed", 0),
                                calories_total=record.get("calories_total", 0),
                                calories_active=record.get("calories_active", 0),
                                sedentary_min=record.get("sedentary_min", 0),
                                light_active_min=record.get("light_active_min", 0),
                                moderate_active_min=record.get("moderate_active_min", 0),
                                vigorous_active_min=record.get("vigorous_active_min", 0),
                                hourly_data=record.get("hourly_data")
                            )
                            db.add(activity)
                            records_new += 1
                        records_processed += 1
                    except Exception as e:
                        errors.append(f"activity: {str(e)}")

            # 处理运动记录
            if "workout" in data and data["workout"].get("records"):
                for record in data["workout"]["records"]:
                    try:
                        workout = WorkoutRecord(
                            user_id=user_id,
                            device_id=request.device_id,
                            workout_type=record["workout_type"],
                            start_time=datetime.fromisoformat(record["start_time"].replace("Z", "+00:00")),
                            end_time=datetime.fromisoformat(record["end_time"].replace("Z", "+00:00")) if record.get("end_time") else None,
                            duration_min=record.get("duration_min"),
                            distance_m=record.get("distance_m"),
                            calories=record.get("calories"),
                            avg_hr=record.get("avg_hr"),
                            max_hr=record.get("max_hr"),
                            avg_pace=record.get("avg_pace"),
                            notes=record.get("notes")
                        )
                        db.add(workout)
                        records_processed += 1
                        records_new += 1
                    except Exception as e:
                        errors.append(f"workout: {str(e)}")

            # 更新设备同步时间和游标
            device.last_sync_at = datetime.utcnow()
            if request.end_time:
                device.sync_cursor = request.end_time

        logger.info(f"[Sync] {sync_id}: processed={records_processed}, new={records_new}, errors={len(errors)}")

        # 设备→行为事实桥接
        try:
            from core.device_behavior_bridge import DeviceBehaviorBridge
            bridge = DeviceBehaviorBridge()
            with db_transaction() as bridge_db:
                # 活动数据: 步数达标自动完成exercise任务
                if "activity" in data and data["activity"].get("records"):
                    for rec in data["activity"]["records"]:
                        steps = rec.get("steps", 0)
                        if steps > 0:
                            bridge.process_activity(bridge_db, user_id, steps)
                # 睡眠数据: 评分达标自动完成sleep任务
                if "sleep" in data and data["sleep"].get("records"):
                    for rec in data["sleep"]["records"]:
                        score = rec.get("sleep_score")
                        if score and score > 0:
                            bridge.process_sleep(bridge_db, user_id, score)
        except Exception as e:
            logger.warning(f"DeviceBehaviorBridge batch处理失败: {e}")

        # 设备预警检查（批量同步后）
        try:
            from core.device_alert_service import DeviceAlertService
            alert_svc = DeviceAlertService()
            with db_transaction() as alert_db:
                # 血糖预警
                if "glucose" in data and data["glucose"].get("readings"):
                    for reading in data["glucose"]["readings"]:
                        alert_svc.check_glucose(alert_db, user_id, reading["value"])
                # 心率预警
                if "heart_rate" in data and data["heart_rate"].get("readings"):
                    for reading in data["heart_rate"]["readings"]:
                        alert_svc.check_heart_rate(
                            alert_db, user_id,
                            reading["hr"],
                            reading.get("activity_type"),
                        )
                # 睡眠预警
                if "sleep" in data and data["sleep"].get("records"):
                    for rec in data["sleep"]["records"]:
                        alert_svc.check_sleep(alert_db, user_id, rec)
                # 活动预警
                if "activity" in data and data["activity"].get("records"):
                    for rec in data["activity"]["records"]:
                        alert_svc.check_activity(alert_db, user_id, rec)
        except Exception as e:
            logger.warning(f"DeviceAlertService batch检查失败: {e}")

        return {
            "success": True,
            "sync_id": sync_id,
            "device_id": request.device_id,
            "records_processed": records_processed,
            "records_new": records_new,
            "records_updated": records_processed - records_new,
            "errors": errors if errors else None,
            "synced_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync/status/{device_id}")
async def get_sync_status(
    device_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    获取设备同步状态
    """
    try:
        with db_transaction() as db:
            device = db.query(UserDevice).filter(
                UserDevice.device_id == device_id,
                UserDevice.user_id == user_id
            ).first()

            if not device:
                raise HTTPException(status_code=404, detail="设备未绑定")

            # 统计各类数据量
            glucose_count = db.query(GlucoseReading).filter(
                GlucoseReading.device_id == device_id
            ).count()

            hr_count = db.query(HeartRateReading).filter(
                HeartRateReading.device_id == device_id
            ).count()

            return {
                "device_id": device_id,
                "status": device.status.value if device.status else "unknown",
                "last_sync_at": device.last_sync_at.isoformat() if device.last_sync_at else None,
                "sync_cursor": device.sync_cursor,
                "data_counts": {
                    "glucose": glucose_count,
                    "heart_rate": hr_count
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get sync status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 睡眠和活动数据查询 API
# ============================================

@router.get("/sleep")
async def get_sleep_records(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(7, ge=1, le=30),
    user_id: int = Depends(get_current_user_id)
):
    """
    获取睡眠记录
    """
    try:
        with db_transaction() as db:
            query = db.query(SleepRecord).filter(
                SleepRecord.user_id == user_id
            )

            if start_date:
                query = query.filter(SleepRecord.sleep_date >= start_date)
            if end_date:
                query = query.filter(SleepRecord.sleep_date <= end_date)

            records = query.order_by(SleepRecord.sleep_date.desc()).limit(limit).all()

            # 计算周平均
            if records:
                avg_duration = sum(r.total_duration_min or 0 for r in records) / len(records)
                avg_score = sum(r.sleep_score or 0 for r in records if r.sleep_score) / max(1, len([r for r in records if r.sleep_score]))
            else:
                avg_duration = 0
                avg_score = 0

            return {
                "records": [
                    {
                        "date": r.sleep_date,
                        "sleep_start": r.sleep_start.isoformat() if r.sleep_start else None,
                        "sleep_end": r.sleep_end.isoformat() if r.sleep_end else None,
                        "total_duration_min": r.total_duration_min,
                        "stages": {
                            "awake_min": r.awake_min,
                            "light_min": r.light_min,
                            "deep_min": r.deep_min,
                            "rem_min": r.rem_min
                        },
                        "sleep_score": r.sleep_score,
                        "efficiency": r.efficiency,
                        "awakenings": r.awakenings
                    }
                    for r in records
                ],
                "weekly_avg": {
                    "duration_min": round(avg_duration),
                    "sleep_score": round(avg_score, 1)
                },
                "total": len(records)
            }

    except Exception as e:
        logger.error(f"Get sleep error: {e}")
        return {"records": [], "weekly_avg": {}, "total": 0}


@router.get("/sleep/last-night")
async def get_last_night_sleep(user_id: int = Depends(get_current_user_id)):
    """
    获取昨晚睡眠数据
    """
    try:
        yesterday = (datetime.utcnow().date() - timedelta(days=1)).isoformat()

        with db_transaction() as db:
            sleep = db.query(SleepRecord).filter(
                SleepRecord.user_id == user_id,
                SleepRecord.sleep_date == yesterday
            ).first()

            if not sleep:
                return {"date": yesterday, "message": "暂无昨晚睡眠数据"}

            # 生成洞察
            insights = []
            if sleep.deep_min and sleep.total_duration_min:
                deep_pct = sleep.deep_min / sleep.total_duration_min * 100
                if deep_pct >= 15:
                    insights.append(f"深睡时长充足，占比{deep_pct:.0f}%")
                else:
                    insights.append(f"深睡时长偏少，仅占{deep_pct:.0f}%")

            if sleep.onset_latency_min:
                if sleep.onset_latency_min <= 15:
                    insights.append("入睡较快")
                else:
                    insights.append(f"入睡较慢，用时{sleep.onset_latency_min}分钟")

            if sleep.awakenings:
                if sleep.awakenings <= 1:
                    insights.append("睡眠连续性好")
                else:
                    insights.append(f"夜醒{sleep.awakenings}次")

            hours = (sleep.total_duration_min or 0) / 60
            return {
                "date": yesterday,
                "sleep_start": sleep.sleep_start.strftime("%H:%M") if sleep.sleep_start else None,
                "sleep_end": sleep.sleep_end.strftime("%H:%M") if sleep.sleep_end else None,
                "duration": f"{int(hours)}小时{int((hours % 1) * 60)}分",
                "score": sleep.sleep_score,
                "stages": {
                    "awake_min": sleep.awake_min,
                    "light_min": sleep.light_min,
                    "deep_min": sleep.deep_min,
                    "rem_min": sleep.rem_min
                },
                "insights": insights
            }

    except Exception as e:
        logger.error(f"Get last night sleep error: {e}")
        return {"message": str(e)}


@router.get("/activity")
async def get_activity_records(
    date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_id: int = Depends(get_current_user_id)
):
    """
    获取活动数据
    """
    try:
        with db_transaction() as db:
            # 单日查询
            if date:
                activity = db.query(ActivityRecord).filter(
                    ActivityRecord.user_id == user_id,
                    ActivityRecord.activity_date == date
                ).first()

                if not activity:
                    return {"date": date, "message": "暂无当天活动数据"}

                steps_goal = 10000
                return {
                    "date": date,
                    "steps": activity.steps,
                    "steps_goal": steps_goal,
                    "progress_percent": round(activity.steps / steps_goal * 100, 1),
                    "distance_km": round(activity.distance_m / 1000, 2) if activity.distance_m else 0,
                    "calories_total": activity.calories_total,
                    "calories_active": activity.calories_active,
                    "floors_climbed": activity.floors_climbed,
                    "active_minutes": activity.light_active_min + activity.moderate_active_min + activity.vigorous_active_min,
                    "hourly_steps": activity.hourly_data
                }

            # 范围查询
            query = db.query(ActivityRecord).filter(
                ActivityRecord.user_id == user_id
            )
            if start_date:
                query = query.filter(ActivityRecord.activity_date >= start_date)
            if end_date:
                query = query.filter(ActivityRecord.activity_date <= end_date)

            records = query.order_by(ActivityRecord.activity_date.desc()).limit(7).all()

            return {
                "records": [
                    {
                        "date": r.activity_date,
                        "steps": r.steps,
                        "distance_km": round(r.distance_m / 1000, 2) if r.distance_m else 0,
                        "calories_active": r.calories_active,
                        "active_minutes": r.light_active_min + r.moderate_active_min + r.vigorous_active_min
                    }
                    for r in records
                ],
                "total": len(records)
            }

    except Exception as e:
        logger.error(f"Get activity error: {e}")
        return {"records": [], "total": 0}


@router.get("/heart-rate")
async def get_heart_rate_data(
    date: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    user_id: int = Depends(get_current_user_id)
):
    """
    获取心率数据
    """
    try:
        with db_transaction() as db:
            query = db.query(HeartRateReading).filter(
                HeartRateReading.user_id == user_id
            )

            if date:
                target_date = datetime.strptime(date, "%Y-%m-%d")
                next_date = target_date + timedelta(days=1)
                query = query.filter(
                    HeartRateReading.recorded_at >= target_date,
                    HeartRateReading.recorded_at < next_date
                )

            readings = query.order_by(HeartRateReading.recorded_at.desc()).limit(limit).all()

            if not readings:
                return {"date": date, "readings": [], "statistics": {}}

            hrs = [r.hr for r in readings]
            resting_hrs = [r.hr for r in readings if r.activity_type == "rest"]

            return {
                "date": date,
                "readings": [
                    {
                        "hr": r.hr,
                        "activity_type": r.activity_type,
                        "timestamp": r.recorded_at.isoformat()
                    }
                    for r in readings[:50]  # 返回最近50条
                ],
                "statistics": {
                    "resting_hr": round(sum(resting_hrs) / len(resting_hrs)) if resting_hrs else None,
                    "avg_hr": round(sum(hrs) / len(hrs)),
                    "max_hr": max(hrs),
                    "min_hr": min(hrs),
                    "count": len(readings)
                }
            }

    except Exception as e:
        logger.error(f"Get heart rate error: {e}")
        return {"readings": [], "statistics": {}}


@router.get("/hrv")
async def get_hrv_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(30, ge=1, le=100),
    user_id: int = Depends(get_current_user_id)
):
    """
    获取 HRV 数据
    """
    try:
        with db_transaction() as db:
            query = db.query(HRVReading).filter(
                HRVReading.user_id == user_id
            )

            if start_date:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(HRVReading.recorded_at >= start)
            if end_date:
                end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(HRVReading.recorded_at < end)

            readings = query.order_by(HRVReading.recorded_at.desc()).limit(limit).all()

            if not readings:
                return {"readings": [], "statistics": {}}

            sdnns = [r.sdnn for r in readings if r.sdnn]
            stress_scores = [r.stress_score for r in readings if r.stress_score]

            return {
                "readings": [
                    {
                        "sdnn": r.sdnn,
                        "rmssd": r.rmssd,
                        "lf_hf_ratio": r.lf_hf_ratio,
                        "stress_score": r.stress_score,
                        "recovery_score": r.recovery_score,
                        "timestamp": r.recorded_at.isoformat()
                    }
                    for r in readings
                ],
                "statistics": {
                    "avg_hrv": round(sum(sdnns) / len(sdnns), 1) if sdnns else None,
                    "avg_stress": round(sum(stress_scores) / len(stress_scores), 1) if stress_scores else None,
                    "trend": "stable",
                    "count": len(readings)
                }
            }

    except Exception as e:
        logger.error(f"Get HRV error: {e}")
        return {"readings": [], "statistics": {}}


# 注册日志
logger.info("[DeviceData] API 模块已加载 (Phase 2)")
