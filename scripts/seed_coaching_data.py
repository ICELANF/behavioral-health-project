# -*- coding: utf-8 -*-
"""
生成教练指导模拟数据
Seed Coaching Demo Data

创建:
  1. 教练-学员绑定 (coach_student_bindings)
  2. 行为画像 (behavioral_profiles) - TTM阶段分布
  3. 评估记录 (assessments) - 风险等级分布

用法:
    docker exec bhp-api python scripts/seed_coaching_data.py
"""

import sys, os, json, random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text as sa_text
from sqlalchemy.orm import Session
from core.database import SessionLocal
from core.models import (
    User, UserRole, BehavioralProfile, BehavioralStage, StageStability,
    Assessment, RiskLevel, AgentType,
)
from loguru import logger

# TTM 阶段分布 (模拟真实分布)
STAGE_POOL = [
    BehavioralStage.S0,  # 前思考
    BehavioralStage.S1,  # 思考
    BehavioralStage.S2,  # 准备
    BehavioralStage.S3,  # 准备
    BehavioralStage.S4,  # 行动
    BehavioralStage.S4,  # 行动
    BehavioralStage.S5,  # 维持
]

RISK_POOL = [
    RiskLevel.R0, RiskLevel.R0, RiskLevel.R1, RiskLevel.R1,
    RiskLevel.R2, RiskLevel.R2, RiskLevel.R3,
]

AGENT_POOL = [
    AgentType.METABOLIC, AgentType.SLEEP, AgentType.STRESS,
    AgentType.MOTIVATION, AgentType.GLUCOSE,
]


def seed_coaching_data():
    db: Session = SessionLocal()

    try:
        # ── 1. 找到教练角色用户和学员角色用户 ──
        coach_roles = [UserRole.COACH, UserRole.PROMOTER, UserRole.SUPERVISOR, UserRole.MASTER]
        student_roles = [UserRole.OBSERVER, UserRole.GROWER, UserRole.SHARER]

        coaches = db.query(User).filter(
            User.role.in_(coach_roles), User.is_active == True
        ).all()
        students = db.query(User).filter(
            User.role.in_(student_roles), User.is_active == True
        ).all()

        logger.info(f"找到 {len(coaches)} 个教练角色, {len(students)} 个学员角色")

        if not coaches or not students:
            logger.warning("没有足够的教练或学员用户，请先运行 seed_demo_members.py")
            return

        # ── 2. 创建教练-学员绑定 ──
        bindings_created = 0
        for student in students:
            # 每个学员随机分配给一个教练
            coach = random.choice(coaches)

            # 检查是否已存在
            existing = db.execute(sa_text(
                "SELECT id FROM coach_schema.coach_student_bindings "
                "WHERE coach_id = :cid AND student_id = :sid AND is_active = true"
            ), {"cid": coach.id, "sid": student.id}).first()

            if existing:
                logger.info(f"  绑定已存在: {coach.username} → {student.username}")
                continue

            permissions = json.dumps({
                "view_profile": True, "view_assessment_summary": True,
                "send_message": True, "create_rx": True, "view_chat_summary": False,
            })
            db.execute(sa_text(
                "INSERT INTO coach_schema.coach_student_bindings "
                "(id, coach_id, student_id, binding_type, permissions, is_active, bound_at, created_at, updated_at) "
                "VALUES (gen_random_uuid(), :cid, :sid, 'assigned', :perms, true, NOW(), NOW(), NOW())"
            ), {"cid": coach.id, "sid": student.id, "perms": permissions})
            bindings_created += 1
            logger.info(f"  绑定: {coach.username}({coach.role.value}) → {student.username}({student.role.value})")

        db.commit()
        logger.info(f"绑定创建完成: {bindings_created} 个")

        # ── 3. 创建行为画像 ──
        profiles_created = 0
        for student in students:
            existing = db.query(BehavioralProfile).filter(
                BehavioralProfile.user_id == student.id
            ).first()
            if existing:
                logger.info(f"  画像已存在: {student.username}")
                continue

            stage = random.choice(STAGE_POOL)
            profile = BehavioralProfile(
                user_id=student.id,
                current_stage=stage,
                stage_confidence=round(random.uniform(0.5, 0.95), 2),
                stage_stability=random.choice([StageStability.STABLE, StageStability.UNSTABLE, StageStability.SEMI_STABLE]),
                stage_updated_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                bpt6_type=random.choice(["action", "knowledge", "emotion", "relation"]),
                capacity_total=random.randint(40, 90),
                spi_score=round(random.uniform(30, 85), 1),
                spi_level=random.choice(["high", "medium", "low"]),
            )
            db.add(profile)
            profiles_created += 1
            logger.info(f"  画像: {student.username} → {stage.value}")

        db.commit()
        logger.info(f"画像创建完成: {profiles_created} 个")

        # ── 4. 创建评估记录 ──
        assessments_created = 0
        for student in students:
            # 检查是否已有评估
            existing_count = db.query(Assessment).filter(
                Assessment.user_id == student.id
            ).count()
            if existing_count >= 2:
                logger.info(f"  评估已存在: {student.username} ({existing_count}条)")
                continue

            # 为每个学员创建2-3条评估记录
            for i in range(random.randint(2, 3)):
                risk = random.choice(RISK_POOL)
                risk_score_map = {
                    RiskLevel.R0: random.uniform(5, 20),
                    RiskLevel.R1: random.uniform(20, 40),
                    RiskLevel.R2: random.uniform(40, 60),
                    RiskLevel.R3: random.uniform(60, 80),
                    RiskLevel.R4: random.uniform(80, 95),
                }
                days_ago = random.randint(1, 60)
                assessment = Assessment(
                    assessment_id=f"ASS-DEMO-{student.id}-{i}-{random.randint(1000,9999)}",
                    user_id=student.id,
                    risk_level=risk,
                    risk_score=round(risk_score_map[risk], 1),
                    primary_concern=random.choice([
                        "血糖控制不佳", "睡眠质量下降", "情绪波动较大",
                        "运动量不足", "饮食不规律", "压力管理困难",
                    ]),
                    urgency=random.choice(["low", "moderate", "high"]),
                    primary_agent=random.choice(AGENT_POOL),
                    priority=random.randint(1, 4),
                    created_at=datetime.utcnow() - timedelta(days=days_ago),
                )
                db.add(assessment)
                assessments_created += 1

        db.commit()
        logger.info(f"评估创建完成: {assessments_created} 条")

        logger.info(f"\n=== 完成 ===\n  绑定: {bindings_created}\n  画像: {profiles_created}\n  评估: {assessments_created}")

    except Exception as e:
        db.rollback()
        logger.error(f"失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("=== 生成教练指导模拟数据 ===")
    seed_coaching_data()
