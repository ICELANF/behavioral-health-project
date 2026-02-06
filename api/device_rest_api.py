# -*- coding: utf-8 -*-
"""
Device Management & Health Data REST API

Provides standard RESTful endpoints:
- Device management (list / bind / sync / unbind)
- Glucose data (query / manual entry)
- Sleep data query
- Activity data query
- Vital signs (query / entry)
- Health dashboard summary
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Path, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from loguru import logger
import uuid

from core.database import get_db
from core.models import (
    User,
    UserDevice, DeviceType, DeviceStatus,
    GlucoseReading, HeartRateReading, HRVReading,
    SleepRecord, ActivityRecord, WorkoutRecord,
    VitalSign, HealthData,
)
from api.dependencies import get_current_user


# ============================================
# Router
# ============================================

router = APIRouter(prefix="/api/v1", tags=["Device & Health Data"])


# ============================================
# Pydantic Schemas - Devices
# ============================================

class DeviceBindRequest(BaseModel):
    """Bind device request body."""
    device_type: DeviceType = Field(..., description="Device type")
    manufacturer: Optional[str] = Field(None, max_length=50, description="Manufacturer (abbott/dexcom/huawei/xiaomi/apple)")
    model: Optional[str] = Field(None, max_length=100, description="Model name")
    serial_number: Optional[str] = Field(None, max_length=100, description="Serial number")
    firmware_version: Optional[str] = Field(None, max_length=50, description="Firmware version")

    class Config:
        use_enum_values = True


class DeviceOut(BaseModel):
    """Device information response."""
    id: int
    device_id: str
    device_type: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    serial_number: Optional[str] = None
    status: str
    battery_level: Optional[int] = None
    last_sync_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DeviceSyncResponse(BaseModel):
    """Sync trigger response."""
    device_id: str
    status: str
    message: str
    last_sync_at: Optional[datetime] = None


# ============================================
# Pydantic Schemas - Glucose
# ============================================

class GlucoseCreateRequest(BaseModel):
    """Manual glucose entry."""
    value: float = Field(..., ge=1.0, le=35.0, description="Glucose value (mmol/L)")
    unit: str = Field(default="mmol/L", description="Unit")
    meal_tag: Optional[str] = Field(
        None,
        description="Meal tag: fasting / before_meal / after_meal / bedtime",
    )
    notes: Optional[str] = Field(None, max_length=500, description="Notes")
    recorded_at: Optional[datetime] = Field(None, description="Recorded time; defaults to now")

    @validator("meal_tag")
    def validate_meal_tag(cls, v):
        allowed = {"fasting", "before_meal", "after_meal", "bedtime"}
        if v is not None and v not in allowed:
            raise ValueError(f"meal_tag must be one of {allowed}")
        return v


class GlucoseOut(BaseModel):
    """Glucose reading response."""
    id: int
    value: float
    unit: str
    trend: Optional[str] = None
    trend_rate: Optional[float] = None
    source: str
    meal_tag: Optional[str] = None
    notes: Optional[str] = None
    recorded_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# Pydantic Schemas - Sleep
# ============================================

class SleepOut(BaseModel):
    """Sleep record response."""
    id: int
    sleep_date: str
    sleep_start: Optional[datetime] = None
    sleep_end: Optional[datetime] = None
    total_duration_min: Optional[int] = None
    awake_min: int = 0
    light_min: int = 0
    deep_min: int = 0
    rem_min: int = 0
    sleep_score: Optional[int] = None
    efficiency: Optional[float] = None
    awakenings: int = 0
    onset_latency_min: Optional[int] = None
    avg_spo2: Optional[float] = None
    min_spo2: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# Pydantic Schemas - Activity
# ============================================

class ActivityOut(BaseModel):
    """Activity record response."""
    id: int
    activity_date: str
    steps: int = 0
    distance_m: int = 0
    floors_climbed: int = 0
    calories_total: int = 0
    calories_active: int = 0
    sedentary_min: int = 0
    light_active_min: int = 0
    moderate_active_min: int = 0
    vigorous_active_min: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# Pydantic Schemas - Vitals
# ============================================

class VitalSignCreateRequest(BaseModel):
    """Record vital sign data."""
    data_type: str = Field(
        ...,
        description="Data type: weight / blood_pressure / temperature / spo2",
    )
    # Weight / body composition
    weight_kg: Optional[float] = Field(None, ge=20.0, le=300.0)
    bmi: Optional[float] = Field(None, ge=10.0, le=80.0)
    body_fat_percent: Optional[float] = Field(None, ge=1.0, le=60.0)
    muscle_mass_kg: Optional[float] = None
    water_percent: Optional[float] = None
    visceral_fat: Optional[int] = None

    # Blood pressure
    systolic: Optional[int] = Field(None, ge=60, le=260)
    diastolic: Optional[int] = Field(None, ge=30, le=160)
    pulse: Optional[int] = Field(None, ge=30, le=220)

    # Temperature
    temperature: Optional[float] = Field(None, ge=34.0, le=43.0)

    # SpO2
    spo2: Optional[float] = Field(None, ge=50.0, le=100.0)

    recorded_at: Optional[datetime] = Field(None, description="Recorded time; defaults to now")

    @validator("data_type")
    def validate_data_type(cls, v):
        allowed = {"weight", "blood_pressure", "temperature", "spo2"}
        if v not in allowed:
            raise ValueError(f"data_type must be one of {allowed}")
        return v


class VitalSignOut(BaseModel):
    """Vital sign response."""
    id: int
    data_type: str
    weight_kg: Optional[float] = None
    bmi: Optional[float] = None
    body_fat_percent: Optional[float] = None
    muscle_mass_kg: Optional[float] = None
    water_percent: Optional[float] = None
    visceral_fat: Optional[int] = None
    systolic: Optional[int] = None
    diastolic: Optional[int] = None
    pulse: Optional[int] = None
    temperature: Optional[float] = None
    spo2: Optional[float] = None
    recorded_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# Pydantic Schemas - Dashboard Summary
# ============================================

class DashboardSummary(BaseModel):
    """Health dashboard summary aggregating latest key metrics."""
    latest_glucose: Optional[Dict[str, Any]] = None
    sleep_score: Optional[int] = None
    steps_today: Optional[int] = None
    latest_weight_kg: Optional[float] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================
#  Device Management Endpoints
# ============================================

@router.get(
    "/devices",
    response_model=List[DeviceOut],
    summary="List user devices",
)
def list_devices(
    device_type: Optional[DeviceType] = Query(None, description="Filter by device type"),
    status_filter: Optional[DeviceStatus] = Query(None, alias="status", description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return all devices bound to the current user.
    Optionally filter by device_type or status.
    """
    logger.info("list_devices | user_id={}", current_user.id)

    query = db.query(UserDevice).filter(UserDevice.user_id == current_user.id)

    if device_type is not None:
        query = query.filter(UserDevice.device_type == device_type)
    if status_filter is not None:
        query = query.filter(UserDevice.status == status_filter)

    devices = query.order_by(UserDevice.created_at.desc()).all()
    logger.debug("list_devices | user_id={} | count={}", current_user.id, len(devices))
    return devices


@router.post(
    "/devices/bind",
    response_model=DeviceOut,
    status_code=status.HTTP_201_CREATED,
    summary="Bind a new device",
)
def bind_device(
    req: DeviceBindRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Bind a new device to the current user.

    - If a serial_number is provided, checks it is not already bound.
    - Generates a unique device_id automatically.
    - Initial status is PAIRING.
    """
    logger.info(
        "bind_device | user_id={} | type={} | manufacturer={}",
        current_user.id, req.device_type, req.manufacturer,
    )

    # Check duplicate serial number
    if req.serial_number:
        existing = (
            db.query(UserDevice)
            .filter(UserDevice.serial_number == req.serial_number)
            .first()
        )
        if existing:
            logger.warning(
                "bind_device | serial_number {} already bound to user_id={}",
                req.serial_number, existing.user_id,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Device serial number {req.serial_number} is already bound",
            )

    device_id = f"DEV-{uuid.uuid4().hex[:12].upper()}"

    device = UserDevice(
        user_id=current_user.id,
        device_id=device_id,
        device_type=req.device_type,
        manufacturer=req.manufacturer,
        model=req.model,
        serial_number=req.serial_number,
        firmware_version=req.firmware_version,
        status=DeviceStatus.PAIRING,
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    logger.info("bind_device | success | device_id={}", device.device_id)
    return device


@router.put(
    "/devices/{device_id}/sync",
    response_model=DeviceSyncResponse,
    summary="Trigger device sync",
)
def trigger_device_sync(
    device_id: str = Path(..., description="Device ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger a data sync for the specified device.

    - Only CONNECTED or PAIRING devices may be synced.
    - Updates last_sync_at and sets status to CONNECTED.
    """
    logger.info("trigger_sync | user_id={} | device_id={}", current_user.id, device_id)

    device = (
        db.query(UserDevice)
        .filter(
            UserDevice.device_id == device_id,
            UserDevice.user_id == current_user.id,
        )
        .first()
    )

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found or does not belong to current user",
        )

    if device.status in (DeviceStatus.EXPIRED, DeviceStatus.DISCONNECTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device status is {device.status.value}; cannot sync. Please reconnect the device.",
        )

    now = datetime.utcnow()
    device.status = DeviceStatus.CONNECTED
    device.last_sync_at = now
    db.commit()

    logger.info("trigger_sync | success | device_id={} | synced_at={}", device_id, now)

    return DeviceSyncResponse(
        device_id=device.device_id,
        status="syncing",
        message="Sync triggered successfully",
        last_sync_at=now,
    )


@router.delete(
    "/devices/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unbind device",
)
def unbind_device(
    device_id: str = Path(..., description="Device ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Unbind (delete) the specified device.
    Only devices belonging to the current user may be deleted.
    """
    logger.info("unbind_device | user_id={} | device_id={}", current_user.id, device_id)

    device = (
        db.query(UserDevice)
        .filter(
            UserDevice.device_id == device_id,
            UserDevice.user_id == current_user.id,
        )
        .first()
    )

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found or does not belong to current user",
        )

    db.delete(device)
    db.commit()

    logger.info("unbind_device | deleted | device_id={}", device_id)
    return None


# ============================================
#  Glucose Endpoints
# ============================================

@router.get(
    "/health-data/glucose",
    response_model=List[GlucoseOut],
    summary="Get glucose readings",
)
def get_glucose_readings(
    days: int = Query(7, ge=1, le=90, description="Number of days to look back"),
    source: Optional[str] = Query(None, description="Source filter: cgm / finger / manual"),
    meal_tag: Optional[str] = Query(None, description="Meal tag filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve glucose readings for the current user within the specified
    number of days, ordered by recorded_at descending.
    """
    logger.info("get_glucose | user_id={} | days={}", current_user.id, days)

    since = datetime.utcnow() - timedelta(days=days)

    query = (
        db.query(GlucoseReading)
        .filter(
            GlucoseReading.user_id == current_user.id,
            GlucoseReading.recorded_at >= since,
        )
    )

    if source:
        query = query.filter(GlucoseReading.source == source)
    if meal_tag:
        query = query.filter(GlucoseReading.meal_tag == meal_tag)

    readings = query.order_by(GlucoseReading.recorded_at.desc()).all()
    logger.debug("get_glucose | user_id={} | count={}", current_user.id, len(readings))
    return readings


@router.post(
    "/health-data/glucose",
    response_model=GlucoseOut,
    status_code=status.HTTP_201_CREATED,
    summary="Record a glucose reading (manual)",
)
def create_glucose_reading(
    req: GlucoseCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Manually record a single glucose reading.

    - source is always set to "manual".
    - If recorded_at is omitted, the current UTC time is used.
    """
    logger.info(
        "create_glucose | user_id={} | value={} | meal_tag={}",
        current_user.id, req.value, req.meal_tag,
    )

    recorded_at = req.recorded_at or datetime.utcnow()

    reading = GlucoseReading(
        user_id=current_user.id,
        value=req.value,
        unit=req.unit,
        source="manual",
        meal_tag=req.meal_tag,
        notes=req.notes,
        recorded_at=recorded_at,
    )

    db.add(reading)
    db.commit()
    db.refresh(reading)

    # 设备→行为事实桥接: 餐后血糖达标自动完成nutrition任务
    if req.meal_tag == "after_meal" and req.value > 0:
        try:
            from core.device_behavior_bridge import DeviceBehaviorBridge
            bridge = DeviceBehaviorBridge()
            bridge.process_glucose(db, current_user.id, req.value)
        except Exception as e:
            logger.warning(f"DeviceBehaviorBridge glucose处理失败: {e}")

    logger.info("create_glucose | success | id={}", reading.id)
    return reading


# ============================================
#  Sleep Endpoints
# ============================================

@router.get(
    "/health-data/sleep",
    response_model=List[SleepOut],
    summary="Get sleep records",
)
def get_sleep_records(
    days: int = Query(7, ge=1, le=90, description="Number of days to look back"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve sleep records for the current user within the specified
    number of days, ordered by sleep_date descending.
    """
    logger.info("get_sleep | user_id={} | days={}", current_user.id, days)

    since_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

    records = (
        db.query(SleepRecord)
        .filter(
            SleepRecord.user_id == current_user.id,
            SleepRecord.sleep_date >= since_date,
        )
        .order_by(SleepRecord.sleep_date.desc())
        .all()
    )

    logger.debug("get_sleep | user_id={} | count={}", current_user.id, len(records))
    return records


# ============================================
#  Activity Endpoints
# ============================================

@router.get(
    "/health-data/activity",
    response_model=List[ActivityOut],
    summary="Get activity records",
)
def get_activity_records(
    days: int = Query(7, ge=1, le=90, description="Number of days to look back"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve daily activity records for the current user within the
    specified number of days, ordered by activity_date descending.
    """
    logger.info("get_activity | user_id={} | days={}", current_user.id, days)

    since_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

    records = (
        db.query(ActivityRecord)
        .filter(
            ActivityRecord.user_id == current_user.id,
            ActivityRecord.activity_date >= since_date,
        )
        .order_by(ActivityRecord.activity_date.desc())
        .all()
    )

    logger.debug("get_activity | user_id={} | count={}", current_user.id, len(records))
    return records


# ============================================
#  Vital Signs Endpoints
# ============================================

@router.get(
    "/health-data/vitals",
    response_model=List[VitalSignOut],
    summary="Get latest vital signs",
)
def get_vital_signs(
    data_type: Optional[str] = Query(
        None, description="Data type filter: weight / blood_pressure / temperature / spo2",
    ),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve vital sign records (weight, blood pressure, temperature, SpO2)
    for the current user, ordered by recorded_at descending.

    - Omit data_type to return all types.
    - Defaults to the last 30 days, up to 50 records.
    """
    logger.info(
        "get_vitals | user_id={} | data_type={} | days={}",
        current_user.id, data_type, days,
    )

    since = datetime.utcnow() - timedelta(days=days)

    query = (
        db.query(VitalSign)
        .filter(
            VitalSign.user_id == current_user.id,
            VitalSign.recorded_at >= since,
        )
    )

    if data_type:
        query = query.filter(VitalSign.data_type == data_type)

    records = (
        query.order_by(VitalSign.recorded_at.desc())
        .limit(limit)
        .all()
    )

    logger.debug("get_vitals | user_id={} | count={}", current_user.id, len(records))
    return records


@router.post(
    "/health-data/vitals",
    response_model=VitalSignOut,
    status_code=status.HTTP_201_CREATED,
    summary="Record vital signs",
)
def create_vital_sign(
    req: VitalSignCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Manually record a single vital sign measurement.

    Populate the relevant fields based on data_type:
    - weight: weight_kg, bmi, body_fat_percent, etc.
    - blood_pressure: systolic, diastolic, pulse
    - temperature: temperature
    - spo2: spo2
    """
    logger.info(
        "create_vital | user_id={} | data_type={}",
        current_user.id, req.data_type,
    )

    recorded_at = req.recorded_at or datetime.utcnow()

    vital = VitalSign(
        user_id=current_user.id,
        data_type=req.data_type,
        weight_kg=req.weight_kg,
        bmi=req.bmi,
        body_fat_percent=req.body_fat_percent,
        muscle_mass_kg=req.muscle_mass_kg,
        water_percent=req.water_percent,
        visceral_fat=req.visceral_fat,
        systolic=req.systolic,
        diastolic=req.diastolic,
        pulse=req.pulse,
        temperature=req.temperature,
        spo2=req.spo2,
        recorded_at=recorded_at,
    )

    db.add(vital)
    db.commit()
    db.refresh(vital)

    logger.info("create_vital | success | id={}", vital.id)
    return vital


# ============================================
#  Dashboard Summary Endpoint
# ============================================

@router.get(
    "/health-data/summary",
    response_model=DashboardSummary,
    summary="Dashboard summary",
)
def get_health_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Aggregate the user's key health metrics into a single dashboard payload:

    - **latest_glucose** - most recent glucose reading (value, unit, trend, time)
    - **sleep_score** - most recent night's sleep score
    - **steps_today** - today's step count
    - **latest_weight_kg** - most recent weight measurement
    """
    logger.info("get_health_summary | user_id={}", current_user.id)

    now = datetime.utcnow()
    today_str = now.strftime("%Y-%m-%d")

    # ---- Latest glucose ----
    latest_glucose_row = (
        db.query(GlucoseReading)
        .filter(GlucoseReading.user_id == current_user.id)
        .order_by(GlucoseReading.recorded_at.desc())
        .first()
    )

    latest_glucose = None
    if latest_glucose_row:
        latest_glucose = {
            "value": latest_glucose_row.value,
            "unit": latest_glucose_row.unit,
            "trend": latest_glucose_row.trend,
            "meal_tag": latest_glucose_row.meal_tag,
            "recorded_at": latest_glucose_row.recorded_at.isoformat(),
        }

    # ---- Sleep score (most recent night) ----
    latest_sleep = (
        db.query(SleepRecord)
        .filter(SleepRecord.user_id == current_user.id)
        .order_by(SleepRecord.sleep_date.desc())
        .first()
    )
    sleep_score = latest_sleep.sleep_score if latest_sleep else None

    # ---- Steps today ----
    today_activity = (
        db.query(ActivityRecord)
        .filter(
            ActivityRecord.user_id == current_user.id,
            ActivityRecord.activity_date == today_str,
        )
        .first()
    )
    steps_today = today_activity.steps if today_activity else None

    # ---- Latest weight ----
    latest_weight = (
        db.query(VitalSign)
        .filter(
            VitalSign.user_id == current_user.id,
            VitalSign.data_type == "weight",
            VitalSign.weight_kg.isnot(None),
        )
        .order_by(VitalSign.recorded_at.desc())
        .first()
    )
    weight_kg = latest_weight.weight_kg if latest_weight else None

    summary = DashboardSummary(
        latest_glucose=latest_glucose,
        sleep_score=sleep_score,
        steps_today=steps_today,
        latest_weight_kg=weight_kg,
        updated_at=now,
    )

    logger.debug(
        "get_health_summary | user_id={} | glucose={} | sleep={} | steps={} | weight={}",
        current_user.id,
        latest_glucose_row.value if latest_glucose_row else None,
        sleep_score,
        steps_today,
        weight_kg,
    )

    return summary
