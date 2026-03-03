# -*- coding: utf-8 -*-
"""
健康数据风险评估引擎

职责：
  1. 根据测量值判断风险等级 (critical / high / medium / low)
  2. 生成 AI 摘要和建议文本
  3. 自动写入 health_review_queue（24h 内同一用户+数据类型去重）

调用方：
  - device_rest_api.py → create_glucose_reading() 之后
  - device_rest_api.py → create_vital_sign() 之后
  - health_review_api.py → sync_werun_data() 之后（活动量过低时）
"""

from typing import Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text as sa_text
from loguru import logger


# ─────────────────────────────────────────────────────────────
# 风险等级 → 审核角色映射
# ─────────────────────────────────────────────────────────────
RISK_TO_REVIEWER = {
    "critical": "master",
    "high":     "supervisor",
    "medium":   "coach",
    "low":      "coach",
}


# ─────────────────────────────────────────────────────────────
# 血糖风险评估
# ─────────────────────────────────────────────────────────────
def assess_glucose_risk(
    value: float,
    meal_tag: Optional[str] = None,
) -> Tuple[str, str, str]:
    """
    返回 (risk_level, ai_summary, ai_recommendation)
    meal_tag: before_meal | after_meal | fasting | bedtime | None
    """
    is_fasting = meal_tag in ("before_meal", "fasting")
    is_postmeal = meal_tag == "after_meal"

    # ── 低血糖（任何时候均危险）──────────────────────────────
    if value < 3.0:
        return (
            "critical",
            f"【危急】血糖严重偏低：{value} mmol/L（低血糖危象阈值3.0）",
            "立即补充含糖食物或饮料，15分钟后复测；如意识模糊请立即就医。暂停一切运动处方。",
        )
    if value < 3.9:
        return (
            "high",
            f"血糖偏低：{value} mmol/L，存在低血糖风险（正常低限 3.9 mmol/L）",
            "建议立即少量补糖，检查近期饮食和运动情况，复测血糖，必要时调整处方剂量。",
        )

    # ── 空腹/餐前血糖 ──────────────────────────────────────
    if is_fasting:
        if value > 13.9:
            return (
                "critical",
                f"【危急】空腹血糖极高：{value} mmol/L（正常 < 6.1，危急 > 13.9）",
                "建议立即联系学员确认状态，告知就医；暂停高强度运动干预，监测是否存在酮症风险。",
            )
        if value > 7.0:
            return (
                "high",
                f"空腹血糖升高：{value} mmol/L（糖尿病诊断参考 ≥ 7.0 mmol/L）",
                "建议减少精制碳水，增加蔬菜摄入；复查空腹血糖，考虑HbA1c检测；审核当前运动处方。",
            )
        if value > 6.1:
            return (
                "medium",
                f"空腹血糖偏高：{value} mmol/L（糖尿病前期参考 6.1-7.0 mmol/L）",
                "建议晚餐减少精制碳水，加入餐后30分钟步行；下周跟进空腹血糖变化趋势。",
            )

    # ── 餐后血糖 ───────────────────────────────────────────
    elif is_postmeal:
        if value > 16.7:
            return (
                "critical",
                f"【危急】餐后血糖极高：{value} mmol/L（正常 < 7.8，危急 > 16.7）",
                "建议立即联系学员，评估是否需要医疗干预；详细回顾本餐食物种类和份量。",
            )
        if value > 11.1:
            return (
                "high",
                f"餐后2h血糖升高：{value} mmol/L（糖尿病诊断参考 ≥ 11.1 mmol/L）",
                "建议本餐主食减量（每餐 < 50g精制碳水），增加蔬菜蛋白比例；餐后步行15分钟。",
            )
        if value > 7.8:
            return (
                "medium",
                f"餐后血糖偏高：{value} mmol/L（正常 < 7.8 mmol/L，糖尿病前期参考）",
                "建议适当调整餐食顺序（先蔬菜再蛋白质再主食），餐后10分钟轻量活动。",
            )

    # ── 通用高血糖（无餐次标记）──────────────────────────
    else:
        if value > 16.7:
            return (
                "critical",
                f"【危急】血糖极高：{value} mmol/L",
                "建议立即联系学员确认状态，评估是否需要医疗干预。",
            )
        if value > 10.0:
            return (
                "high",
                f"血糖偏高：{value} mmol/L（参考范围 3.9-10.0 mmol/L）",
                "建议回顾近期饮食，减少高GI食物；增加有氧运动频次；下次测量时标注餐次。",
            )
        if value > 7.8:
            return (
                "medium",
                f"血糖略高：{value} mmol/L，建议持续关注",
                "建议餐后适量步行，减少精制碳水摄入，下次测量请标注是否为餐前或餐后。",
            )

    # ── 正常范围 → 不进队列 ────────────────────────────────
    return ("normal", "", "")


# ─────────────────────────────────────────────────────────────
# 体征风险评估
# ─────────────────────────────────────────────────────────────
def assess_vitals_risk(
    data_type: str,
    weight_kg: Optional[float] = None,
    bmi: Optional[float] = None,
    body_fat_percent: Optional[float] = None,
    systolic: Optional[float] = None,
    diastolic: Optional[float] = None,
    pulse: Optional[float] = None,
    spo2: Optional[float] = None,
    temperature: Optional[float] = None,
) -> Tuple[str, str, str]:
    """
    返回 (risk_level, ai_summary, ai_recommendation)
    data_type: weight | blood_pressure | spo2 | temperature | body_composition
    """

    # ── 血氧 ─────────────────────────────────────────────
    if data_type == "spo2" and spo2 is not None:
        if spo2 < 90:
            return (
                "critical",
                f"【危急】血氧饱和度极低：SpO₂ {spo2}%（正常 ≥ 95%，危急 < 90%）",
                "建议立即联系学员，确认是否有呼吸困难症状，指导就医或拨打急救电话。",
            )
        if spo2 < 94:
            return (
                "high",
                f"血氧饱和度偏低：SpO₂ {spo2}%（正常 ≥ 95%）",
                "建议排查近期是否有感冒、哮喘、高原活动；暂停高强度运动，监测24h内变化。",
            )
        return ("normal", "", "")

    # ── 血压 ─────────────────────────────────────────────
    if data_type == "blood_pressure" and systolic is not None:
        diastolic = diastolic or 0
        if systolic > 180 or diastolic > 120:
            return (
                "critical",
                f"【危急】血压极高：{systolic}/{diastolic} mmHg（高血压危象阈值 180/120）",
                "建议学员立即静卧休息，停止一切运动；如伴有头痛/视物模糊/胸痛，立即就医。",
            )
        if systolic > 160 or diastolic > 100:
            return (
                "high",
                f"血压显著升高：{systolic}/{diastolic} mmHg（2级高血压参考）",
                "建议减少钠盐摄入（< 5g/天），暂停大重量抗阻训练；回顾近期饮食和压力状态。",
            )
        if systolic > 140 or diastolic > 90:
            return (
                "medium",
                f"血压偏高：{systolic}/{diastolic} mmHg（1级高血压参考）",
                "建议增加有氧运动（每周 ≥ 150分钟），限制咖啡因，监测下周血压变化趋势。",
            )
        if systolic < 90 or diastolic < 60:
            return (
                "medium",
                f"血压偏低：{systolic}/{diastolic} mmHg（低血压参考 < 90/60）",
                "建议增加水分和盐分摄入，避免久站后快速起立，监测是否伴有头晕症状。",
            )
        return ("normal", "", "")

    # ── 体温 ─────────────────────────────────────────────
    if data_type == "temperature" and temperature is not None:
        if temperature > 39.5:
            return (
                "critical",
                f"【危急】体温过高：{temperature}°C（高热参考 > 39.5°C）",
                "建议立即暂停所有运动处方，指导学员就医，排查感染原因。",
            )
        if temperature > 38.5:
            return (
                "high",
                f"体温升高：{temperature}°C（发热参考 ≥ 38.5°C）",
                "建议暂停高强度运动，充分休息和补水，监测体温变化，必要时就医。",
            )
        if temperature < 35.5:
            return (
                "high",
                f"体温偏低：{temperature}°C（低体温参考 < 35.5°C）",
                "建议排查是否有甲状腺功能减退或营养不足；增加保暖措施，监测体温趋势。",
            )
        return ("normal", "", "")

    # ── 体重/体成分 ──────────────────────────────────────
    if data_type in ("weight", "body_composition"):
        bmi_val = bmi
        if bmi_val is None and weight_kg:
            # 无身高无法计算 BMI，跳过
            pass
        if bmi_val is not None:
            if bmi_val > 40 or bmi_val < 15:
                return (
                    "high",
                    f"BMI 极端值：{bmi_val:.1f}（正常 18.5-24）",
                    "建议详细评估营养状态和体成分；制定个性化目标，必要时转介营养师。",
                )
            if bmi_val > 35:
                return (
                    "medium",
                    f"BMI 重度超重：{bmi_val:.1f}（正常 18.5-24，轻度 24-28，重度 > 35）",
                    "建议每周记录体重，设置小目标（每月减0.5-1kg）；调整饮食结构为低GI食物为主。",
                )
            if bmi_val > 28:
                return (
                    "medium",
                    f"BMI 超重：{bmi_val:.1f}（正常 18.5-24，超重 24-28，肥胖 28+）",
                    "建议增加有氧运动频次，记录每日饮食，优先调整高热量零食和含糖饮料。",
                )
            if bmi_val < 18.5:
                return (
                    "medium",
                    f"BMI 偏低：{bmi_val:.1f}（正常 18.5-24，偏瘦 < 18.5）",
                    "建议增加优质蛋白和健康脂肪摄入，减少过度有氧训练，评估是否存在厌食倾向。",
                )

        # 体脂率异常
        if body_fat_percent is not None:
            if body_fat_percent > 40:
                return (
                    "medium",
                    f"体脂率偏高：{body_fat_percent:.1f}%",
                    "建议增加抗阻训练保持肌肉量，同时控制热量摄入，以维持基础代谢率。",
                )

    # ── 心率 ─────────────────────────────────────────────
    if pulse is not None:
        if pulse > 150 or pulse < 35:
            return (
                "critical",
                f"【危急】静息心率异常：{pulse} bpm（正常 60-100 bpm）",
                "建议立即联系学员确认状态；心率过高或过低均可能为心律失常信号，建议就医检查。",
            )
        if pulse > 120:
            return (
                "high",
                f"静息心率偏高：{pulse} bpm（正常 60-100 bpm）",
                "建议回顾近期压力、咖啡因摄入和睡眠质量；暂停高强度运动，监测HRV趋势。",
            )
        if pulse < 45:
            return (
                "medium",
                f"静息心率偏低：{pulse} bpm（运动员型心率，需结合症状评估）",
                "如无症状可能为良性，建议确认是否有头晕或晕厥史；继续观察。",
            )

    return ("normal", "", "")


# ─────────────────────────────────────────────────────────────
# 活动量风险评估
# ─────────────────────────────────────────────────────────────
def assess_activity_risk(
    steps: int,
    consecutive_low_days: int = 1,
) -> Tuple[str, str, str]:
    """
    steps: 当天步数
    consecutive_low_days: 连续低活动天数（可选，增加精准度）
    返回 (risk_level, ai_summary, ai_recommendation)
    """
    if steps < 1500 and consecutive_low_days >= 3:
        return (
            "medium",
            f"运动量持续严重不足：本日步数 {steps} 步，已连续 {consecutive_low_days} 天低于 1500 步",
            "建议制定最小运动目标（每天10分钟步行），排查是否有身体不适或行动障碍，发送激励提醒。",
        )
    if steps < 3000 and consecutive_low_days >= 5:
        return (
            "medium",
            f"运动量长期不足：本日步数 {steps} 步，已连续 {consecutive_low_days} 天低于 3000 步",
            "建议与学员沟通运动障碍，调整运动处方为更容易执行的方式（如室内运动）。",
        )
    return ("normal", "", "")


# ─────────────────────────────────────────────────────────────
# 写入审核队列（带24h去重）
# ─────────────────────────────────────────────────────────────
def auto_enqueue_review(
    db: Session,
    user_id: int,
    data_type: str,
    risk_level: str,
    reviewer_role: str,
    ai_summary: str,
    ai_recommendation: str,
) -> bool:
    """
    将风险评估结果写入 health_review_queue。
    去重策略：同一 user_id + data_type 在过去 24h 内已有 pending 记录则跳过。
    返回是否实际写入。
    """
    if risk_level in ("normal", "low"):
        return False

    try:
        # 检查表是否存在
        exists = db.execute(sa_text(
            "SELECT to_regclass('public.health_review_queue')"
        )).scalar()
        if not exists:
            logger.warning("[RiskEngine] health_review_queue 表不存在，跳过入队")
            return False

        # 24h 去重：同一用户+数据类型已有 pending 记录则跳过
        recent = db.execute(sa_text("""
            SELECT id FROM health_review_queue
            WHERE user_id = :uid
              AND data_type = :dtype
              AND status = 'pending'
              AND created_at > NOW() - INTERVAL '24 hours'
            LIMIT 1
        """), {"uid": user_id, "dtype": data_type}).fetchone()

        if recent:
            logger.debug(
                f"[RiskEngine] 跳过入队 — user={user_id} dtype={data_type} "
                f"已有 pending 记录 id={recent[0]}"
            )
            return False

        db.execute(sa_text("""
            INSERT INTO health_review_queue
                (user_id, data_type, risk_level, reviewer_role,
                 ai_summary, ai_recommendation, status, created_at)
            VALUES
                (:uid, :dtype, :risk, :role, :summary, :rec, 'pending', NOW())
        """), {
            "uid":     user_id,
            "dtype":   data_type,
            "risk":    risk_level,
            "role":    reviewer_role,
            "summary": ai_summary,
            "rec":     ai_recommendation,
        })
        db.commit()

        logger.info(
            f"[RiskEngine] 入队成功 — user={user_id} dtype={data_type} "
            f"risk={risk_level} reviewer={reviewer_role}"
        )
        return True

    except Exception as e:
        logger.error(f"[RiskEngine] 入队失败: {e}")
        try:
            db.rollback()
        except Exception:
            pass
        return False


# ─────────────────────────────────────────────────────────────
# 一键触发（给调用方用的统一入口）
# ─────────────────────────────────────────────────────────────
def trigger_glucose_review(db: Session, user_id: int, value: float, meal_tag: Optional[str]) -> bool:
    """血糖数据保存后调用"""
    risk, summary, rec = assess_glucose_risk(value, meal_tag)
    if risk == "normal":
        return False
    reviewer = RISK_TO_REVIEWER.get(risk, "coach")
    return auto_enqueue_review(db, user_id, "glucose", risk, reviewer, summary, rec)


def trigger_vitals_review(db: Session, user_id: int, data_type: str, **kwargs) -> bool:
    """体征数据保存后调用"""
    risk, summary, rec = assess_vitals_risk(data_type, **kwargs)
    if risk == "normal":
        return False
    reviewer = RISK_TO_REVIEWER.get(risk, "coach")
    return auto_enqueue_review(db, user_id, data_type, risk, reviewer, summary, rec)


def trigger_activity_review(db: Session, user_id: int, steps: int, consecutive_low_days: int = 1) -> bool:
    """活动量数据保存后调用"""
    risk, summary, rec = assess_activity_risk(steps, consecutive_low_days)
    if risk == "normal":
        return False
    reviewer = RISK_TO_REVIEWER.get(risk, "coach")
    return auto_enqueue_review(db, user_id, "activity", risk, reviewer, summary, rec)
