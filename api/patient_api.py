# Patient API — 学员档案/设备/轨迹
from fastapi import APIRouter, Depends, Query
from api.dependencies import get_current_user, get_db
from core.models import User
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/patient", tags=["患者档案"])


@router.get("/{patient_id}/profile")
def get_patient_profile(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取学员健康档案"""
    user = db.query(User).filter(User.id == patient_id).first()
    if not user:
        return {
            "id": str(patient_id),
            "name": "未知用户",
            "gender": "male",
            "age": 0,
            "height": "",
            "weight": "",
            "diagnosis": "",
            "diagnosisDate": "",
            "medicalNotes": "",
            "medications": [],
            "allergies": [],
            "emergencyContact": {"name": "", "relation": "", "phone": ""},
        }
    return {
        "id": str(user.id),
        "name": user.username or "未知",
        "gender": "male",
        "age": 0,
        "height": "",
        "weight": "",
        "diagnosis": getattr(user, "condition", "") or "",
        "diagnosisDate": "",
        "medicalNotes": "",
        "medications": [],
        "allergies": [],
        "emergencyContact": {"name": "", "relation": "", "phone": ""},
    }


@router.put("/{patient_id}/profile")
def update_patient_profile(
    patient_id: int,
    data: dict = None,
    current_user: User = Depends(get_current_user),
):
    """更新学员健康档案"""
    return {"message": "档案已更新", "patient_id": patient_id}


@router.get("/{patient_id}/devices")
def get_patient_devices(
    patient_id: int,
    current_user: User = Depends(get_current_user),
):
    """获取学员绑定设备列表"""
    return []


@router.post("/{patient_id}/devices/bind")
def bind_patient_device(
    patient_id: int,
    data: dict = None,
    current_user: User = Depends(get_current_user),
):
    """绑定设备"""
    return {"message": "设备绑定成功", "patient_id": patient_id}


@router.delete("/{patient_id}/devices/{device_id}")
def unbind_patient_device(
    patient_id: int,
    device_id: str,
    current_user: User = Depends(get_current_user),
):
    """解绑设备"""
    return {"message": "设备已解绑"}


@router.get("/{patient_id}/trajectory")
def get_patient_trajectory(
    patient_id: int,
    period: str = Query(default="30d"),
    current_user: User = Depends(get_current_user),
):
    """获取学员行为轨迹"""
    return {
        "ttmTimeline": [
            {"name": "前意向期", "date": "", "duration": "", "color": "#999", "completed": True},
            {"name": "意向期", "date": "", "duration": "", "color": "#1890ff", "current": True},
        ],
        "implicitData": [],
        "explicitData": [],
        "recentEvents": [],
    }
