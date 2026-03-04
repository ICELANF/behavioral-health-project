# -*- coding: utf-8 -*-
"""
食物拍照识别 + 营养指导 API
使用 VLMService (ollama_first: Ollama qwen2.5vl → Cloud VLM fallback)
"""

import os
import re
import json
import uuid
import base64
import time
import asyncio
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from loguru import logger

from core.database import get_db, get_db_session
from core.models import FoodAnalysis, DailyTask, TaskCheckin
from api.dependencies import get_current_user
router = APIRouter(prefix="/api/v1/food", tags=["食物识别"])

# 上传目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOOD_IMAGE_DIR = os.path.join(BASE_DIR, "static", "uploads", "food_images")
os.makedirs(FOOD_IMAGE_DIR, exist_ok=True)

# 文件限制
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

FOOD_ANALYSIS_PROMPT = """你是一位专业营养师。请分析图片中的食物，以JSON格式返回：
{{
  "food_name": "食物名称，多个用逗号分隔",
  "calories": 估算总热量(kcal数字),
  "protein": 蛋白质(g数字),
  "fat": 脂肪(g数字),
  "carbs": 碳水化合物(g数字),
  "fiber": 膳食纤维(g数字),
  "foods": [
    {{"name": "单个食物", "portion": "估算份量", "calories": 热量数字}}
  ],
  "advice": "针对该餐的营养建议，100字以内"
}}
只返回JSON，不要其他文字。{cooking_hint}"""

PACKAGED_FOOD_PROMPT = """你是一位专业营养师。请从图片中的食品营养成分表标签读取数值，以JSON格式返回：
{{
  "food_name": "产品名称（若可见）",
  "calories": 每份或每100g热量(kcal数字),
  "protein": 蛋白质(g数字),
  "fat": 脂肪(g数字),
  "carbs": 碳水化合物(g数字),
  "fiber": 膳食纤维(g数字，若有),
  "serving_size": "每份重量（如有）",
  "source": "label",
  "advice": "根据标签成分的营养建议，50字以内"
}}
数据来自标签，请精确读取，不要估算。只返回JSON，不要其他文字。"""


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

    # 4. 调用 VLM 视觉模型 (ollama_first: Ollama → Cloud fallback)
    raw_text = ""
    vlm_available = True
    try:
        from core.vlm_service import VLMService
        vlm = VLMService()
        result = await vlm.analyze_image(b64_data, FOOD_ANALYSIS_PROMPT, temperature=0.3)
        raw_text = result.get("text", "")
        logger.info(f"[Food] VLM provider: {result.get('provider')}")
    except Exception as e:
        logger.warning(f"[Food] VLM 不可用，保存图片记录（无AI分析）: {e}")
        vlm_available = False
        raw_text = ""

    # 5. 解析响应 (VLM不可用时使用空数据)
    parsed = _parse_llm_response(raw_text) if vlm_available and raw_text else {}

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
        "review_status": "auto",
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


@router.get("/vlm-status")
async def vlm_status(current_user=Depends(get_current_user)):
    """检查 VLM 视觉模型服务可用性"""
    from core.vlm_service import VLMService
    svc = VLMService()
    return {
        "code": 0,
        "message": "success",
        "data": svc.is_available(),
    }


# ─────────────────────────────────────────────────────────────
# 小程序前端专用端点（food/scan.vue + food/diary.vue）
# ─────────────────────────────────────────────────────────────

class NutritionInfo(BaseModel):
    calories: Optional[float] = None
    carbs:    Optional[float] = None
    protein:  Optional[float] = None
    fat:      Optional[float] = None
    fiber:    Optional[float] = None


class FoodRecordRequest(BaseModel):
    food_name:       str
    meal_type:       Optional[str] = None
    image_url:       Optional[str] = None
    nutrition:       Optional[NutritionInfo] = None
    recorded_at:     Optional[str] = None
    cooking_method:  Optional[str] = None
    is_packaged:     bool = False


@router.post("/analyze")
async def analyze_food_image(
    image: UploadFile = File(...),
    meal_type: Optional[str] = Form(None),
    cooking_method: Optional[str] = Form(None),
    is_packaged: bool = Form(False),
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    食物图片 AI 分析（小程序 food/scan.vue 调用）
    - is_packaged=true 时使用营养标签专用 Prompt，精确读取数值
    - cooking_method 传入时告知 AI 烹饪方式以提升热量估算精度
    返回：{food_name, nutrition:{calories,carbs,protein,fat,fiber}, advice, source}
    """
    ext = os.path.splitext(image.filename or "photo.jpg")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".jpg"
    contents = await image.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="图片不能超过 5MB")

    ts = int(time.time())
    filename = f"{current_user.id}_{ts}_{uuid.uuid4().hex[:8]}{ext}"
    with open(os.path.join(FOOD_IMAGE_DIR, filename), "wb") as f:
        f.write(contents)
    image_url = f"/api/static/uploads/food_images/{filename}"

    # 选择 Prompt
    if is_packaged:
        prompt = PACKAGED_FOOD_PROMPT
    else:
        cooking_hint = (
            f"\n烹饪方式：{cooking_method}，请据此调整热量估算（如炸/煎会增加油脂吸收）。"
            if cooking_method else ""
        )
        prompt = FOOD_ANALYSIS_PROMPT.format(cooking_hint=cooking_hint)

    parsed: dict = {}
    try:
        b64_data = base64.b64encode(contents).decode("utf-8")
        from core.vlm_service import VLMService
        vlm = VLMService()
        result = await vlm.analyze_image(b64_data, prompt, temperature=0.3)
        raw_text = result.get("text", "")
        parsed = _parse_llm_response(raw_text) if raw_text else {}
        logger.info(f"[Food/analyze] VLM provider: {result.get('provider')}, packaged={is_packaged}, cooking={cooking_method}")
    except Exception as e:
        logger.warning(f"[Food/analyze] VLM 不可用: {e}")

    try:
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
            raw_response=json.dumps(parsed, ensure_ascii=False),
            meal_type=meal_type,
            cooking_method=cooking_method,
            is_packaged=is_packaged,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
    except Exception as e:
        logger.warning(f"[Food/analyze] DB write failed: {e}")
        db.rollback()

    return {
        "food_name":     parsed.get("food_name") or "未能识别",
        "cooking_method": cooking_method,
        "is_packaged":   is_packaged,
        "source":        "label" if is_packaged else "ai_estimate",
        "nutrition": {
            "calories": parsed.get("calories"),
            "carbs":    parsed.get("carbs"),
            "protein":  parsed.get("protein"),
            "fat":      parsed.get("fat"),
            "fiber":    parsed.get("fiber"),
        },
        "advice":    parsed.get("advice") or "",
        "image_url": image_url,
        "foods":     parsed.get("foods", []),
    }


@router.post("/record")
async def save_food_record(
    body: FoodRecordRequest,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    手动保存饮食记录（小程序 food/scan.vue saveManual 调用）
    写入 food_analyses 表（image_url 可为空）
    """
    nut = body.nutrition or NutritionInfo()
    try:
        record = FoodAnalysis(
            user_id=current_user.id,
            image_url=body.image_url or "",
            food_name=body.food_name,
            calories=nut.calories,
            protein=nut.protein,
            fat=nut.fat,
            carbs=nut.carbs,
            fiber=nut.fiber,
            meal_type=body.meal_type,
            cooking_method=body.cooking_method,
            is_packaged=body.is_packaged,
            advice=None,
            raw_response=None,
        )
        # 覆盖 created_at（前端传了 recorded_at 时用前端时间）
        if body.recorded_at:
            try:
                record.created_at = datetime.fromisoformat(
                    body.recorded_at.replace("Z", "+00:00")
                ).replace(tzinfo=None)
            except Exception:
                pass

        db.add(record)
        db.commit()
        db.refresh(record)
        return {"success": True, "id": record.id}
    except Exception as e:
        db.rollback()
        logger.error(f"[Food/record] save failed: {e}")
        raise HTTPException(status_code=500, detail="保存失败")


@router.get("/diary")
async def food_diary(
    date_str: Optional[str] = Query(None, alias="date",
                                    description="YYYY-MM-DD，默认今日"),
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取指定日期的饮食日记（小程序 food/diary.vue + scan.vue 摘要调用）
    返回：{items: [...], date, total_calories, total_carbs, total_protein, total_fat}
    """
    target_date = date_str or date.today().isoformat()

    try:
        rows = db.execute(text("""
            SELECT id, food_name, meal_type, calories, protein, fat, carbs, fiber,
                   advice, image_url, created_at
            FROM food_analyses
            WHERE user_id = :uid
              AND DATE(created_at) = :d
            ORDER BY created_at ASC
        """), {"uid": current_user.id, "d": target_date}).mappings().all()

        items = []
        total = {"calories": 0.0, "carbs": 0.0, "protein": 0.0, "fat": 0.0}
        for r in rows:
            ts = r["created_at"].isoformat() if r["created_at"] else None
            item = {
                "id":          r["id"],
                "food_name":   r["food_name"] or "",
                "meal_type":   r["meal_type"] or "",
                "image_url":   r["image_url"] or "",
                "advice":      r["advice"] or "",
                "created_at":  ts,
                "recorded_at": ts,   # diary.vue 兼容字段
                "nutrition": {
                    "calories": r["calories"],
                    "carbs":    r["carbs"],
                    "protein":  r["protein"],
                    "fat":      r["fat"],
                    "fiber":    r["fiber"],
                },
            }
            items.append(item)
            total["calories"] += r["calories"] or 0
            total["carbs"]    += r["carbs"]    or 0
            total["protein"]  += r["protein"]  or 0
            total["fat"]      += r["fat"]      or 0

        return {
            "items": items,
            "date":  target_date,
            "total_calories": round(total["calories"]),
            "total_carbs":    round(total["carbs"], 1),
            "total_protein":  round(total["protein"], 1),
            "total_fat":      round(total["fat"], 1),
        }
    except Exception as e:
        logger.warning(f"[Food/diary] query failed: {e}")
        return {"items": [], "date": target_date,
                "total_calories": 0, "total_carbs": 0, "total_protein": 0, "total_fat": 0}


# ─────────────────────────────────────────────────────────────
# 热量平衡审计  GET /api/v1/food/balance
# 算法优先级：
#   TDEE = 经验法(体重变化+饮食记录) > Katch-McArdle(有体脂率) > Mifflin-St Jeor > 参考值
#   EAT  = 设备直接值 > 步数公式 > 手动运动MET > 0
# ─────────────────────────────────────────────────────────────

def _calc_age(birth: Any) -> int:
    if not birth:
        return 35
    if isinstance(birth, str):
        birth = datetime.fromisoformat(birth.replace("Z", "+00:00"))
    today = date.today()
    return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))


def _balance_label(balance: float) -> str:
    if balance > 500:   return "显著盈余，建议增加运动"
    if balance > 200:   return "轻微盈余"
    if balance > -200:  return "基本平衡"
    if balance > -500:  return "轻微亏缺"
    return "显著亏缺，注意营养补充"


MET_MAP = {
    "walking": 3.5, "running": 8.3, "cycling": 6.8,
    "swimming": 5.8, "strength": 3.5, "yoga": 2.5,
    "dance": 4.8, "stairs": 8.0, "other": 4.0,
}


@router.get("/balance")
async def food_energy_balance(
    date_str: Optional[str] = Query(None, alias="date", description="YYYY-MM-DD，默认今日"),
    window_days: int = Query(30, ge=7, le=90, description="经验TDEE计算窗口（天）"),
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    当日热量平衡审计。

    返回字段：
    - intake: 今日饮食摄入汇总
    - expenditure: {bmr, neat, eat, tef, total, eat_source}
    - balance: 摄入 - 支出（正=盈余，负=亏缺）
    - tdee_empirical: 经验TDEE（若有足够历史数据）
    - confidence: low/medium/high
    """
    target_date = date_str or date.today().isoformat()

    # ── 1. 今日摄入 ──────────────────────────────────────
    intake_row = db.execute(text("""
        SELECT COALESCE(SUM(calories), 0) AS cal,
               COALESCE(SUM(carbs),    0) AS carbs,
               COALESCE(SUM(protein),  0) AS protein,
               COALESCE(SUM(fat),      0) AS fat
        FROM food_analyses
        WHERE user_id = :uid AND DATE(created_at) = :d
    """), {"uid": current_user.id, "d": target_date}).mappings().first()
    intake_cal = round(float(intake_row["cal"] or 0))

    # ── 2. 用户体征 ───────────────────────────────────────
    vital = db.execute(text("""
        SELECT weight_kg, body_fat_percent, muscle_mass_kg
        FROM vital_signs
        WHERE user_id = :uid AND weight_kg IS NOT NULL
        ORDER BY recorded_at DESC LIMIT 1
    """), {"uid": current_user.id}).mappings().first()

    profile   = getattr(current_user, "profile", None) or {}
    weight    = float((vital and vital["weight_kg"]) or profile.get("weight") or 65)
    body_fat  = float(vital["body_fat_percent"]) if vital and vital["body_fat_percent"] else None
    height    = float(profile.get("height") or 170)
    gender    = (getattr(current_user, "gender", None) or profile.get("gender", "male") or "male").lower()
    age       = _calc_age(getattr(current_user, "date_of_birth", None))

    # ── 3. BMR ───────────────────────────────────────────
    if body_fat is not None:
        lbm = weight * (1 - body_fat / 100)
        bmr = round(370 + 21.6 * lbm)
        bmr_method = "katch_mcardle"
    elif weight and height and age:
        if gender in ("male", "m", "男"):
            bmr = round(10 * weight + 6.25 * height - 5 * age + 5)
        else:
            bmr = round(10 * weight + 6.25 * height - 5 * age - 161)
        bmr_method = "mifflin_st_jeor"
    else:
        bmr = 1600 if gender in ("male", "m", "男") else 1300
        bmr_method = "reference_value"

    # ── 4. 经验 TDEE（体重趋势 + 饮食记录） ─────────────
    window_start = (date.fromisoformat(target_date) - timedelta(days=window_days)).isoformat()

    weight_pts = db.execute(text("""
        SELECT DATE(recorded_at) AS d, AVG(weight_kg) AS w
        FROM vital_signs
        WHERE user_id = :uid AND weight_kg IS NOT NULL
          AND DATE(recorded_at) BETWEEN :s AND :e
        GROUP BY DATE(recorded_at) ORDER BY d
    """), {"uid": current_user.id, "s": window_start, "e": target_date}).mappings().all()

    intake_hist = db.execute(text("""
        SELECT DATE(created_at) AS d, SUM(calories) AS cal
        FROM food_analyses
        WHERE user_id = :uid AND calories IS NOT NULL
          AND DATE(created_at) BETWEEN :s AND :e
        GROUP BY DATE(created_at) ORDER BY d
    """), {"uid": current_user.id, "s": window_start, "e": target_date}).mappings().all()

    empirical_tdee: Optional[float] = None
    empirical_note = ""
    if len(weight_pts) >= 3 and len(intake_hist) >= 7:
        w0 = float(weight_pts[0]["w"])
        w1 = float(weight_pts[-1]["w"])
        span = (date.fromisoformat(str(weight_pts[-1]["d"])) -
                date.fromisoformat(str(weight_pts[0]["d"]))).days
        avg_intake = sum(float(r["cal"]) for r in intake_hist) / len(intake_hist)
        if span > 0:
            # 1kg 混合体组织 ≈ 7700 kcal
            daily_energy_from_weight = (w1 - w0) * 7700 / span
            empirical_tdee = avg_intake - daily_energy_from_weight
            empirical_note = (
                f"经验法：{len(intake_hist)}天饮食记录 + "
                f"{len(weight_pts)}次体重测量，窗口{span}天"
            )
            logger.info(f"[Food/balance] empirical TDEE={empirical_tdee:.0f}, "
                        f"avg_intake={avg_intake:.0f}, weight_delta={w1-w0:.2f}kg/{span}d")

    # ── 5. 今日活动消耗（EAT） ────────────────────────────
    act = db.execute(text("""
        SELECT steps, calories_total, calories_active
        FROM activity_records
        WHERE user_id = :uid AND activity_date = :d
        ORDER BY updated_at DESC LIMIT 1
    """), {"uid": current_user.id, "d": target_date}).mappings().first()

    eat = 0
    eat_source = "none"
    if act:
        if act["calories_active"] and act["calories_active"] > 0:
            eat = int(act["calories_active"])
            eat_source = "device"
        elif act["steps"] and act["steps"] > 0:
            eat = round(act["steps"] * weight * 0.00065)
            eat_source = "steps_formula"


    # ── 6. NEAT + TEF ────────────────────────────────────
    neat = round(bmr * 0.25)
    tef  = round(intake_cal * 0.10)

    # ── 7. 今日总支出 ─────────────────────────────────────
    tdee_today = bmr + neat + eat + tef

    # ── 8. 参考 TDEE（经验 > 公式）──────────────────────
    ref_tdee = round(empirical_tdee) if (empirical_tdee and 800 < empirical_tdee < 5000) \
               else round(bmr * 1.45)
    ref_tdee_method = empirical_note if empirical_tdee else f"BMR({bmr_method})×1.45"

    # ── 9. 平衡 ──────────────────────────────────────────
    balance = intake_cal - tdee_today

    # ── 10. 置信度 ────────────────────────────────────────
    score = 0
    if empirical_tdee:                   score += 40
    if body_fat is not None:             score += 20
    elif weight and height and age < 80: score += 10
    if eat_source in ("device", "steps_formula"):  score += 20
    elif eat_source == "manual_exercise_met":       score += 10
    if len(intake_hist) >= 14:  score += 20
    elif len(intake_hist) >= 7: score += 10
    confidence = "high" if score >= 70 else "medium" if score >= 35 else "low"

    return {
        "date": target_date,
        "intake": {
            "calories": intake_cal,
            "carbs":    round(float(intake_row["carbs"] or 0), 1),
            "protein":  round(float(intake_row["protein"] or 0), 1),
            "fat":      round(float(intake_row["fat"] or 0), 1),
        },
        "expenditure": {
            "bmr":        bmr,
            "bmr_method": bmr_method,
            "neat":       neat,
            "eat":        eat,
            "eat_source": eat_source,
            "tef":        tef,
            "total":      tdee_today,
        },
        "tdee_reference":        ref_tdee,
        "tdee_reference_method": ref_tdee_method,
        "balance":       balance,
        "balance_label": _balance_label(balance),
        "confidence":    confidence,
        "confidence_score": score,
        "empirical": {
            "available":      empirical_tdee is not None,
            "tdee":           round(empirical_tdee) if empirical_tdee else None,
            "note":           empirical_note,
            "food_days":      len(intake_hist),
            "weight_records": len(weight_pts),
            "window_days":    window_days,
        },
    }
