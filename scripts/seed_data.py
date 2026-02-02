"""
种子数据脚本
Seed Data Script

加载初始数据到数据库：
- 管理员用户
- 测试用户
- 示例评估数据
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database import db_transaction, get_table_counts
from core.models import (
    User, UserRole, Assessment, TriggerRecord,
    RiskLevel, TriggerSeverity, TriggerCategory, AgentType
)
from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """哈希密码"""
    return pwd_context.hash(password)


def create_admin_user():
    """创建管理员用户"""
    try:
        with db_transaction() as db:
            # 检查是否已存在
            existing = db.query(User).filter(User.username == "admin").first()
            if existing:
                logger.info("管理员用户已存在，跳过创建")
                return existing

            admin = User(
                username="admin",
                email="admin@behavioral-health.com",
                password_hash=hash_password("admin123456"),  # 默认密码
                role=UserRole.ADMIN,
                full_name="系统管理员",
                is_active=True,
                is_verified=True,
                profile={
                    "role_description": "系统管理员",
                    "permissions": ["all"]
                }
            )
            db.add(admin)

            logger.success("✓ 管理员用户创建成功")
            logger.info("  用户名: admin")
            logger.info("  密码: admin123456")
            return admin

    except Exception as e:
        logger.error(f"创建管理员失败: {e}")
        return None


def create_test_users():
    """创建测试用户"""
    test_users_data = [
        {
            "username": "patient_alice",
            "email": "alice@example.com",
            "password": "password123",
            "role": UserRole.PATIENT,
            "full_name": "Alice Wang",
            "profile": {
                "age": 45,
                "gender": "female",
                "chronic_conditions": ["diabetes_type2"],
                "goals": ["glucose_control", "weight_loss"]
            }
        },
        {
            "username": "patient_bob",
            "email": "bob@example.com",
            "password": "password123",
            "role": UserRole.PATIENT,
            "full_name": "Bob Chen",
            "profile": {
                "age": 38,
                "gender": "male",
                "chronic_conditions": ["hypertension"],
                "goals": ["stress_management"]
            }
        },
        {
            "username": "coach_carol",
            "email": "carol@behavioral-health.com",
            "password": "coach123",
            "role": UserRole.COACH,
            "full_name": "Carol Li",
            "profile": {
                "specializations": ["diabetes", "nutrition"],
                "certification": "CDE"
            }
        }
    ]

    created_users = []

    try:
        with db_transaction() as db:
            for user_data in test_users_data:
                # 检查是否已存在
                existing = db.query(User).filter(
                    User.username == user_data["username"]
                ).first()

                if existing:
                    logger.info(f"用户 {user_data['username']} 已存在，跳过")
                    created_users.append(existing)
                    continue

                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    password_hash=hash_password(user_data["password"]),
                    role=user_data["role"],
                    full_name=user_data["full_name"],
                    is_active=True,
                    is_verified=True,
                    profile=user_data["profile"],
                    adherence_rate=75.0 if user_data["role"] == UserRole.PATIENT else 0.0
                )
                db.add(user)
                created_users.append(user)

                logger.success(f"✓ 用户 {user_data['username']} 创建成功")

        return created_users

    except Exception as e:
        logger.error(f"创建测试用户失败: {e}")
        return []


def create_sample_assessments():
    """创建示例评估数据"""
    try:
        with db_transaction() as db:
            # 获取测试患者
            alice = db.query(User).filter(User.username == "patient_alice").first()
            bob = db.query(User).filter(User.username == "patient_bob").first()

            if not alice or not bob:
                logger.warning("测试用户不存在，跳过创建示例评估")
                return []

            # Alice的评估 - 高血糖风险
            assessment1 = Assessment(
                assessment_id="ASS-SEED-001",
                user_id=alice.id,
                text_content="最近血糖有点高，感觉有些疲劳",
                glucose_values=[6.5, 11.2, 13.5, 12.8, 10.5],
                hrv_values=[68, 72, 65],
                risk_level=RiskLevel.R2,
                risk_score=45.0,
                primary_concern="高血糖",
                urgency="moderate",
                severity_distribution={"high": 1, "moderate": 1},
                reasoning="检测到1个高风险信号，1个中等风险信号，综合风险分数45.0/100",
                primary_agent=AgentType.GLUCOSE,
                secondary_agents=["MetabolicAgent", "NutritionAgent"],
                priority=2,
                response_time="24小时内",
                routing_reasoning="基于高血糖主要问题，路由到GlucoseAgent进行专业评估",
                recommended_actions=["查看血糖趋势图", "评估饮食记录"],
                status="completed",
                created_at=datetime.utcnow() - timedelta(days=2),
                completed_at=datetime.utcnow() - timedelta(days=2, hours=1)
            )
            db.add(assessment1)
            db.flush()  # Flush to get assessment1.id

            # Alice的Triggers
            trigger1 = TriggerRecord(
                assessment_id=assessment1.id,
                tag_id="high_glucose",
                name="高血糖",
                category=TriggerCategory.PHYSIOLOGICAL,
                severity=TriggerSeverity.HIGH,
                confidence=1.0,
                trigger_metadata={"max_glucose": 13.5, "threshold": 10.0}
            )
            db.add(trigger1)

            trigger2 = TriggerRecord(
                assessment_id=assessment1.id,
                tag_id="glucose_spike",
                name="血糖波动",
                category=TriggerCategory.PHYSIOLOGICAL,
                severity=TriggerSeverity.MODERATE,
                confidence=1.0,
                trigger_metadata={"variation": 7.0, "threshold": 3.0}
            )
            db.add(trigger2)

            # Bob的评估 - 压力过载
            assessment2 = Assessment(
                assessment_id="ASS-SEED-002",
                user_id=bob.id,
                text_content="工作压力很大，天天加班，睡眠不好",
                hrv_values=[55, 58, 52, 60, 57],
                risk_level=RiskLevel.R3,
                risk_score=75.0,
                primary_concern="压力过载",
                urgency="high",
                severity_distribution={"high": 1, "moderate": 3},
                reasoning="检测到1个高风险信号，3个中等风险信号，综合风险分数75.0/100",
                primary_agent=AgentType.STRESS,
                secondary_agents=["MentalHealthAgent", "SleepAgent", "CoachingAgent"],
                priority=1,
                response_time="1小时内",
                routing_reasoning="基于压力过载主要问题，路由到StressAgent进行专业评估",
                recommended_actions=["压力源评估", "压力管理技巧", "睡眠优化建议"],
                status="completed",
                created_at=datetime.utcnow() - timedelta(days=1),
                completed_at=datetime.utcnow() - timedelta(days=1, hours=2)
            )
            db.add(assessment2)
            db.flush()  # Flush to get assessment2.id

            # Bob的Triggers
            trigger3 = TriggerRecord(
                assessment_id=assessment2.id,
                tag_id="stress_overload",
                name="压力过载",
                category=TriggerCategory.PSYCHOLOGICAL,
                severity=TriggerSeverity.HIGH,
                confidence=0.8,
                trigger_metadata={"detection_method": "keyword", "source": "text"}
            )
            db.add(trigger3)

            trigger4 = TriggerRecord(
                assessment_id=assessment2.id,
                tag_id="work_stress",
                name="工作压力",
                category=TriggerCategory.ENVIRONMENTAL,
                severity=TriggerSeverity.MODERATE,
                confidence=0.8,
                trigger_metadata={"detection_method": "keyword", "source": "text"}
            )
            db.add(trigger4)

            trigger5 = TriggerRecord(
                assessment_id=assessment2.id,
                tag_id="poor_sleep",
                name="睡眠质量差",
                category=TriggerCategory.PHYSIOLOGICAL,
                severity=TriggerSeverity.MODERATE,
                confidence=0.8,
                trigger_metadata={"detection_method": "keyword", "source": "text"}
            )
            db.add(trigger5)

            trigger6 = TriggerRecord(
                assessment_id=assessment2.id,
                tag_id="low_hrv",
                name="低心率变异性",
                category=TriggerCategory.PHYSIOLOGICAL,
                severity=TriggerSeverity.MODERATE,
                confidence=1.0,
                trigger_metadata={"hrv_sdnn": 25, "threshold": 30}
            )
            db.add(trigger6)

            logger.success("✓ 示例评估数据创建成功")
            return [assessment1, assessment2]

    except Exception as e:
        logger.error(f"创建示例评估失败: {e}")
        return []


def seed_all():
    """执行完整的数据种子"""
    logger.info("=" * 60)
    logger.info("开始加载种子数据")
    logger.info("=" * 60)

    # 1. 创建管理员
    logger.info("\n[1/3] 创建管理员用户...")
    admin = create_admin_user()

    # 2. 创建测试用户
    logger.info("\n[2/3] 创建测试用户...")
    test_users = create_test_users()

    # 3. 创建示例评估
    logger.info("\n[3/3] 创建示例评估数据...")
    assessments = create_sample_assessments()

    # 统计
    logger.info("\n" + "=" * 60)
    logger.info("种子数据加载完成")
    logger.info("=" * 60)

    counts = get_table_counts()
    logger.info("\n数据库记录统计:")
    for table, count in counts.items():
        logger.info(f"  {table}: {count}条")

    logger.info("\n默认账号信息:")
    logger.info("  管理员:")
    logger.info("    用户名: admin")
    logger.info("    密码: admin123456")
    logger.info("\n  测试患者:")
    logger.info("    用户名: patient_alice / patient_bob")
    logger.info("    密码: password123")
    logger.info("\n  测试教练:")
    logger.info("    用户名: coach_carol")
    logger.info("    密码: coach123")

    logger.success("\n✅ 种子数据加载成功！")


if __name__ == "__main__":
    seed_all()
