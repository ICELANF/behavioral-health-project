"""
种子数据脚本 - 为演示用户注入真实感健康数据
Seed Script - Inject realistic health data for demo users

运行方式: cd D:\behavioral-health-project && python scripts/seed_health_data.py
"""
import sys
import os
import random
from datetime import datetime, timedelta

# 将项目根目录加入 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_engine, SessionLocal
from core.models import (
    GlucoseReading, HeartRateReading, HRVReading,
    SleepRecord, ActivityRecord, VitalSign
)

random.seed(42)


def seed_glucose(db, user_id: int, days: int = 14):
    """生成血糖数据 - 每天 3-5 条"""
    count = 0
    now = datetime.utcnow()
    for day_offset in range(days):
        day = now - timedelta(days=day_offset)
        # 空腹血糖 (早 7 点)
        fasting = round(random.uniform(4.5, 6.5), 1)
        db.add(GlucoseReading(
            user_id=user_id, value=fasting, unit="mmol/L",
            source="manual", meal_tag="fasting",
            recorded_at=day.replace(hour=7, minute=random.randint(0, 30))
        ))
        count += 1

        # 午餐后 (13 点)
        after_lunch = round(random.uniform(6.0, 9.5), 1)
        db.add(GlucoseReading(
            user_id=user_id, value=after_lunch, unit="mmol/L",
            source="manual", meal_tag="after_meal",
            recorded_at=day.replace(hour=13, minute=random.randint(0, 30))
        ))
        count += 1

        # 晚餐前 (17 点)
        before_dinner = round(random.uniform(4.8, 7.0), 1)
        db.add(GlucoseReading(
            user_id=user_id, value=before_dinner, unit="mmol/L",
            source="manual", meal_tag="before_meal",
            recorded_at=day.replace(hour=17, minute=random.randint(0, 30))
        ))
        count += 1

        # 晚餐后 (随机)
        if random.random() > 0.3:
            after_dinner = round(random.uniform(5.5, 10.0), 1)
            db.add(GlucoseReading(
                user_id=user_id, value=after_dinner, unit="mmol/L",
                source="manual", meal_tag="after_meal",
                recorded_at=day.replace(hour=20, minute=random.randint(0, 59))
            ))
            count += 1

    print(f"  [Glucose] {count} records")


def seed_heart_rate(db, user_id: int, days: int = 14):
    """生成心率数据 - 每天 24 条 (每小时一条)"""
    count = 0
    now = datetime.utcnow()
    for day_offset in range(days):
        day = now - timedelta(days=day_offset)
        for hour in range(24):
            if hour < 6:
                hr = random.randint(55, 68)
                activity = "rest"
            elif hour < 8:
                hr = random.randint(65, 85)
                activity = "light"
            elif hour < 12:
                hr = random.randint(70, 95)
                activity = "moderate" if random.random() > 0.6 else "light"
            elif hour < 14:
                hr = random.randint(68, 80)
                activity = "rest"
            elif hour < 18:
                hr = random.randint(72, 100)
                activity = "moderate" if random.random() > 0.5 else "light"
            elif hour < 22:
                hr = random.randint(65, 85)
                activity = "light"
            else:
                hr = random.randint(58, 72)
                activity = "rest"

            db.add(HeartRateReading(
                user_id=user_id, hr=hr,
                activity_type=activity,
                recorded_at=day.replace(hour=hour, minute=random.randint(0, 59))
            ))
            count += 1

    print(f"  [HeartRate] {count} records")


def seed_hrv(db, user_id: int, days: int = 14):
    """生成 HRV 数据 - 每天 4 条"""
    count = 0
    now = datetime.utcnow()
    for day_offset in range(days):
        day = now - timedelta(days=day_offset)
        for hour in [7, 12, 18, 23]:
            sdnn = round(random.uniform(30, 80), 1)
            rmssd = round(random.uniform(20, 60), 1)
            lf = round(random.uniform(200, 800), 1)
            hf = round(random.uniform(150, 600), 1)
            stress = random.randint(20, 75)
            recovery = random.randint(40, 95)

            db.add(HRVReading(
                user_id=user_id,
                sdnn=sdnn, rmssd=rmssd,
                lf=lf, hf=hf,
                lf_hf_ratio=round(lf / hf, 2) if hf > 0 else None,
                stress_score=stress,
                recovery_score=recovery,
                recorded_at=day.replace(hour=hour, minute=random.randint(0, 30))
            ))
            count += 1

    print(f"  [HRV] {count} records")


def seed_sleep(db, user_id: int, days: int = 14):
    """生成睡眠数据 - 每天 1 条"""
    count = 0
    now = datetime.utcnow()
    for day_offset in range(1, days + 1):
        day = now - timedelta(days=day_offset)
        sleep_date = day.strftime("%Y-%m-%d")

        # 入睡时间 22:30 - 0:30
        sleep_hour = random.choice([22, 23, 0])
        sleep_min = random.randint(0, 59)
        sleep_start = day.replace(hour=sleep_hour, minute=sleep_min)

        # 总睡眠时长 5.5h - 8.5h
        total_min = random.randint(330, 510)
        sleep_end = sleep_start + timedelta(minutes=total_min + random.randint(10, 40))

        deep_min = random.randint(60, 120)
        light_min = random.randint(120, 200)
        rem_min = random.randint(40, 100)
        awake_min = total_min - deep_min - light_min - rem_min
        if awake_min < 0:
            awake_min = random.randint(5, 20)
            total_min = deep_min + light_min + rem_min + awake_min

        score = min(100, max(30, int(
            50 + (deep_min / total_min * 100) + (total_min / 60 * 5) - (awake_min * 0.5)
        )))

        db.add(SleepRecord(
            user_id=user_id,
            sleep_date=sleep_date,
            sleep_start=sleep_start,
            sleep_end=sleep_end,
            total_duration_min=total_min,
            awake_min=awake_min,
            light_min=light_min,
            deep_min=deep_min,
            rem_min=rem_min,
            sleep_score=score,
            efficiency=round(random.uniform(80, 96), 1),
            awakenings=random.randint(0, 4),
        ))
        count += 1

    print(f"  [Sleep] {count} records")


def seed_activity(db, user_id: int, days: int = 14):
    """生成活动数据 - 每天 1 条"""
    count = 0
    now = datetime.utcnow()
    for day_offset in range(days):
        day = now - timedelta(days=day_offset)
        activity_date = day.strftime("%Y-%m-%d")

        steps = random.randint(3000, 15000)
        distance_m = int(steps * 0.7)
        sedentary = random.randint(300, 600)
        light = random.randint(60, 180)
        moderate = random.randint(10, 60)
        vigorous = random.randint(0, 30)
        calories_total = random.randint(1500, 2500)
        calories_active = random.randint(150, 600)

        db.add(ActivityRecord(
            user_id=user_id,
            activity_date=activity_date,
            steps=steps,
            distance_m=distance_m,
            floors_climbed=random.randint(0, 15),
            calories_total=calories_total,
            calories_active=calories_active,
            sedentary_min=sedentary,
            light_active_min=light,
            moderate_active_min=moderate,
            vigorous_active_min=vigorous,
        ))
        count += 1

    print(f"  [Activity] {count} records")


def seed_blood_pressure(db, user_id: int, days: int = 14):
    """生成血压数据 - 每天 1-2 条"""
    count = 0
    now = datetime.utcnow()
    for day_offset in range(days):
        day = now - timedelta(days=day_offset)

        # 晨起血压
        systolic = random.randint(110, 135)
        diastolic = random.randint(65, 85)
        db.add(VitalSign(
            user_id=user_id,
            data_type="blood_pressure",
            systolic=systolic,
            diastolic=diastolic,
            pulse=random.randint(60, 80),
            recorded_at=day.replace(hour=7, minute=random.randint(0, 30))
        ))
        count += 1

        # 晚间血压 (随机)
        if random.random() > 0.4:
            systolic = random.randint(115, 140)
            diastolic = random.randint(70, 88)
            db.add(VitalSign(
                user_id=user_id,
                data_type="blood_pressure",
                systolic=systolic,
                diastolic=diastolic,
                pulse=random.randint(62, 85),
                recorded_at=day.replace(hour=21, minute=random.randint(0, 59))
            ))
            count += 1

    print(f"  [BloodPressure] {count} records")


def seed_weight(db, user_id: int, days: int = 14):
    """生成体重数据 - 每天 1 条"""
    count = 0
    now = datetime.utcnow()
    base_weight = round(random.uniform(65, 78), 1)

    for day_offset in range(days):
        day = now - timedelta(days=day_offset)
        # 每天微小波动
        weight = round(base_weight + random.uniform(-0.5, 0.5), 1)
        bmi = round(weight / (1.72 ** 2), 1)  # 假设身高 172cm

        db.add(VitalSign(
            user_id=user_id,
            data_type="weight",
            weight_kg=weight,
            bmi=bmi,
            body_fat_percent=round(random.uniform(18, 28), 1),
            muscle_mass_kg=round(weight * random.uniform(0.38, 0.45), 1),
            recorded_at=day.replace(hour=7, minute=random.randint(0, 15))
        ))
        count += 1

    print(f"  [Weight] {count} records")


def main():
    print("=" * 50)
    print("健康数据种子脚本 - Seeding Health Data")
    print("=" * 50)

    db = SessionLocal()
    try:
        # 为 user_id=1 (admin) 和 user_id=4 (patient_alice) 生成数据
        for user_id, name in [(1, "admin"), (4, "patient_alice")]:
            print(f"\n>>> User {user_id} ({name}):")
            seed_glucose(db, user_id)
            seed_heart_rate(db, user_id)
            seed_hrv(db, user_id)
            seed_sleep(db, user_id)
            seed_activity(db, user_id)
            seed_blood_pressure(db, user_id)
            seed_weight(db, user_id)

        db.commit()
        print("\n" + "=" * 50)
        print("Done! All health data seeded successfully.")
        print("=" * 50)

    except Exception as e:
        db.rollback()
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
