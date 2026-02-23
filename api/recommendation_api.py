# Recommendation API — 个性化推荐系统
from fastapi import APIRouter, Depends, Query
from api.dependencies import get_current_user
from core.models import User

router = APIRouter(prefix="/api/v1/recommendations", tags=["推荐系统"])


@router.get("/focus-areas")
def get_focus_areas(
    current_user: User = Depends(get_current_user),
):
    """获取用户关注的问题领域"""
    return ["blood_sugar", "weight", "exercise"]


@router.put("/focus-areas")
def update_focus_areas(
    body: dict = None,
    current_user: User = Depends(get_current_user),
):
    """更新用户关注领域"""
    return True


@router.get("")
def get_recommendations(
    stage: str = Query(default="S1_PRE_CONTEMPLATION"),
    focus_areas: str = Query(default=""),
    current_user: User = Depends(get_current_user),
):
    """获取个性化推荐"""
    areas = [a for a in focus_areas.split(",") if a] if focus_areas else []
    return {
        "userStage": stage,
        "focusAreas": areas,
        "videos": [],
        "products": [],
        "courses": [],
        "coachActions": [],
        "dailyTip": {
            "icon": "bulb",
            "title": "今日小贴士",
            "content": "保持规律作息有助于血糖稳定。",
        },
    }


@router.post("/track")
def track_recommendation(
    body: dict = None,
    current_user: User = Depends(get_current_user),
):
    """记录推荐点击行为"""
    return {"message": "已记录"}
