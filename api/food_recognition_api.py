# -*- coding: utf-8 -*-
"""
食物拍照识别 + 营养指导 API
使用 Ollama qwen2.5-vl:7b 视觉模型
"""

import os
import re
import json
import uuid
import base64
import time
import asyncio
from datetime import datetime, date, timedelta
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from loguru import logger

from core.database import get_db, get_db_session
from core.models import FoodAnalysis, DailyTask, TaskCheckin
from api.dependencies import get_current_user
from api.config import OLLAMA_API_URL

router = APIRouter(prefix="/api/v1/food", tags=["食物识别"])

# 上传目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOOD_IMAGE_DIR = os.path.join(BASE_DIR, "static", "uploads", "food_images")
os.makedirs(FOOD_IMAGE_DIR, exist_ok=True)

# 文件限制
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

# 视觉模型
VL_MODEL = os.getenv("OLLAMA_VL_MODEL", "qwen2.5vl:7b")

FOOD_ANALYSIS_PROMPT = """你是一位专业营养师。请分析图片中的食物，以JSON格式返回：
{
  "food_name": "食物名称，多个用逗号分隔",
  "calories": 估算总热量(kcal数字),
  "protein": 蛋白质(g数字),
  "fat": 脂肪(g数字),
  "carbs": 碳水化合物(g数字),
  "fiber": 膳食纤维(g数字),
  "foods": [
    {"name": "单个食物", "portion": "估算份量", "calories": 热量数字}
  ],
  "advice": "针对该餐的营养建议，100字以内"
}
只返回JSON，不要其他文字。"""


def _parse_llm_response(text: str) -> dict:
    """解析 LLM 响应，尝试提取 JSON"""
    # 尝试直接解析
    text = text.strip()
    # 去除 markdown 代码块包裹
    if text.startswith("```"):
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试提取 JSON 块
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # 正则 fallback
    result = {}
    for field in ["food_name", "advice"]:
        m = re.search(rf'"{field}"\s*:\s*"([^"]*)"', text)
        if m:
            result[field] = m.group(1)
    for field in ["calories", "protein", "fat", "carbs", "fiber"]:
        m = re.search(rf'"{field}"\s*:\s*([\d.]+)', text)
        if m:
            result[field] = float(m.group(1))

    return result if result else {"food_name": "未能识别", "advice": "请尝试拍摄更清晰的食物照片"}


def _try_auto_checkin_nutrition_task(
    user_id: int, food_result: dict, photo_url: str, db: Session
) -> Optional[dict]:
    """
    自动打卡营养任务: 查找今日未完成的营养拍照任务，自动完成并更新积分/连续天数。
    返回 task_info dict 或 None (无待完成任务时)。
    """
    try:
        today = date.today()
        now = datetime.now()

        # 1) 查找今日未完成的营养任务 (只取第一个)
        task = (
            db.query(DailyTask)
            .filter(
                DailyTask.user_id == user_id,
                DailyTask.tag == "营养",
                DailyTask.done == False,
                DailyTask.task_date == today,
            )
            .order_by(DailyTask.id)
            .first()
        )
        if not task:
            return None

        # 2) 写入打卡记录
        food_name = food_result.get("food_name", "")
        calories = food_result.get("calories")
        checkin = TaskCheckin(
            task_id=task.id,
            user_id=user_id,
            photo_url=photo_url,
            value=float(calories) if calories is not None else None,
            note=f"AI识别: {food_name}" + (f" {calories}kcal" if calories else ""),
            points_earned=10,
        )
        db.add(checkin)

        # 3) 标记任务完成
        task.done = True
        task.done_time = now

        # 4) 累加成长积分
        db.execute(
            text("UPDATE users SET growth_points = COALESCE(growth_points, 0) + 10 WHERE id = :uid"),
            {"uid": user_id},
        )

        # 5) 更新连续天数 (user_streaks 表)
        streak_row = db.execute(
            text("SELECT current_streak, longest_streak, last_checkin_date FROM user_streaks WHERE user_id = :uid"),
            {"uid": user_id},
        ).mappings().first()

        streak_days = 1
        if not streak_row:
            db.execute(
                text("""INSERT INTO user_streaks (user_id, current_streak, longest_streak, last_checkin_date, updated_at)
                        VALUES (:uid, 1, 1, :today, NOW())"""),
                {"uid": user_id, "today": today},
            )
        else:
            last_date = streak_row["last_checkin_date"]
            current = streak_row["current_streak"] or 0
            longest = streak_row["longest_streak"] or 0
            if last_date == today:
                streak_days = current
            else:
                streak_days = current + 1 if last_date == today - timedelta(days=1) else 1
                new_longest = max(longest, streak_days)
                db.execute(
                    text("""UPDATE user_streaks
                            SET current_streak = :streak, longest_streak = :longest,
                                last_checkin_date = :today, updated_at = NOW()
                            WHERE user_id = :uid"""),
                    {"streak": streak_days, "longest": new_longest, "today": today, "uid": user_id},
                )

        db.commit()

        return {
            "task_id": task.id,
            "task_title": task.title,
            "points_earned": 10,
            "streak": streak_days,
        }
    except Exception as e:
        logger.warning(f"[Food] 自动打卡营养任务失败: {e}")
        try:
            db.rollback()
        except Exception:
            pass
        return None


@router.post("/recognize")
async def recognize_food(
    file: UploadFile = File(...),
    meal_type: Optional[str] = Form(None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    食物拍照识别

    上传食物图片，AI 分析营养成分并给出饮食建议。
    - 支持 jpg/png/webp/bmp，最大 5MB
    - meal_type 可选: breakfast / lunch / dinner / snack
    """
    # 1. 验证文件
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")

    ext = os.path.splitext(file.filename or "photo.jpg")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的图片格式: {ext}")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过 5MB")

    # 2. 保存图片
    ts = int(time.time())
    short_uuid = uuid.uuid4().hex[:8]
    filename = f"{current_user.id}_{ts}_{short_uuid}{ext}"
    filepath = os.path.join(FOOD_IMAGE_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    image_url = f"/api/static/uploads/food_images/{filename}"

    # 3. Base64 编码
    b64_data = base64.b64encode(contents).decode("utf-8")

    # 4. 调用 Ollama 视觉模型
    payload = {
        "model": VL_MODEL,
        "messages": [
            {
                "role": "user",
                "content": FOOD_ANALYSIS_PROMPT,
                "images": [b64_data],
            }
        ],
        "stream": False,
        "options": {"temperature": 0.3},
    }

    raw_text = ""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{OLLAMA_API_URL}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            raw_text = data.get("message", {}).get("content", "")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI 模型响应超时，请稍后重试")
    except Exception as e:
        logger.error(f"[Food] Ollama 调用失败: {e}")
        raise HTTPException(status_code=502, detail="AI 模型服务不可用")

    # 5. 解析响应
    parsed = _parse_llm_response(raw_text)

    # 6. 写入数据库
    record = FoodAnalysis(
        user_id=current_user.id,
        image_url=image_url,
        food_name=parsed.get("food_name"),
        calories=parsed.get("calories"),
        protein=parsed.get("protein"),
        fat=parsed.get("fat"),
        carbs=parsed.get("carbs"),
        fiber=parsed.get("fiber"),
        advice=parsed.get("advice"),
        raw_response=raw_text,
        meal_type=meal_type,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # 6.5 积分记录
    try:
        from core.models import PointTransaction
        db.add(PointTransaction(
            user_id=current_user.id,
            action="food_recognize",
            point_type="growth",
            amount=2,
        ))
        db.commit()
    except Exception as e:
        logger.warning(f"积分记录失败: {e}")

    # 6.6 自动打卡营养任务
    task_result = _try_auto_checkin_nutrition_task(
        user_id=current_user.id,
        food_result=parsed,
        photo_url=image_url,
        db=db,
    )

    # 6.7 异步刷新信任分 (不阻塞响应)
    if task_result:
        try:
            from core.trust_score_service import extract_trust_signals_from_checkins, TrustScoreService
            uid = current_user.id

            def _update_trust():
                with get_db_session() as sync_db:
                    signals = extract_trust_signals_from_checkins(sync_db, uid, days=7)
                    svc = TrustScoreService(sync_db)
                    svc.update_user_trust(uid, signals, source="food_recognize")
                    sync_db.commit()

            await asyncio.to_thread(_update_trust)
        except Exception:
            pass  # 信任分更新失败不影响主流程

    # 7. 返回结果
    return {
        "id": record.id,
        "image_url": image_url,
        "food_name": parsed.get("food_name"),
        "calories": parsed.get("calories"),
        "protein": parsed.get("protein"),
        "fat": parsed.get("fat"),
        "carbs": parsed.get("carbs"),
        "fiber": parsed.get("fiber"),
        "foods": parsed.get("foods", []),
        "advice": parsed.get("advice"),
        "meal_type": meal_type,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "task_completed": task_result is not None,
        "task_info": task_result,
    }


@router.get("/history")
async def food_history(
    limit: int = 20,
    offset: int = 0,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的食物分析历史"""
    query = (
        db.query(FoodAnalysis)
        .filter(FoodAnalysis.user_id == current_user.id)
        .order_by(FoodAnalysis.created_at.desc())
    )
    total = query.count()
    records = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "items": [
            {
                "id": r.id,
                "image_url": r.image_url,
                "food_name": r.food_name,
                "calories": r.calories,
                "protein": r.protein,
                "fat": r.fat,
                "carbs": r.carbs,
                "fiber": r.fiber,
                "advice": r.advice,
                "meal_type": r.meal_type,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ],
    }
