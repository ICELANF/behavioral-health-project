"""
创建模拟案例数据
Create Mock Assessment Cases

生成10个真实的模拟评估案例，涵盖不同的：
- 风险等级（R0-R4）
- 生理数据（血糖、HRV）
- Trigger类型
- Agent路由决策
- 文字日记内容

这些案例将插入数据库，并在前端/H5应用中同步显示。
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session

from core.database import SessionLocal, engine
from core.models import Base, User, Assessment, TriggerRecord, RiskLevel, TriggerSeverity, TriggerCategory, AgentType
from loguru import logger

# 创建所有表
Base.metadata.create_all(bind=engine)


# ============================================
# 模拟案例数据定义
# ============================================

MOCK_CASES = [
    # Case 1: 正常状态 - R0
    {
        "text_content": "今天感觉很好，早上跑步30分钟，整体心情愉悦。午餐控制得不错，吃了蔬菜沙拉和鸡胸肉。晚上和家人散步，睡眠质量也不错。",
        "glucose_values": [5.2, 5.8, 6.1],
        "hrv_values": [68, 72, 70],
        "risk_level": RiskLevel.R0,
        "risk_score": 12.5,
        "primary_concern": "状态良好",
        "urgency": "low",
        "reasoning": "各项指标正常，血糖控制良好，HRV值稳定在正常范围，情绪积极，建议继续保持良好习惯。",
        "primary_agent": AgentType.COACHING,
        "secondary_agents": [AgentType.NUTRITION, AgentType.EXERCISE],
        "priority": 4,
        "response_time": "1周内",
        "recommended_actions": [
            "继续保持规律运动，每周3-5次有氧运动",
            "维持均衡饮食，多吃蔬菜和优质蛋白",
            "保持良好作息，每晚23:00前入睡",
            "定期自我监测，每周记录1-2次"
        ],
        "triggers": [
            {
                "tag_id": "good_control",
                "name": "良好控制",
                "category": TriggerCategory.PHYSIOLOGICAL,
                "severity": TriggerSeverity.LOW,
                "confidence": 0.92,
                "metadata": {"glucose_avg": 5.7, "hrv_avg": 70}
            }
        ],
        "days_ago": 1
    },

    # Case 2: 轻度风险 - R1（睡眠不足）
    {
        "text_content": "这几天工作压力大，经常加班到深夜。睡眠时间只有5-6小时，早上起床感觉疲惫。饮食还算规律，但运动减少了。",
        "glucose_values": [6.8, 7.2, 8.1],
        "hrv_values": [45, 48, 42],
        "risk_level": RiskLevel.R1,
        "risk_score": 28.3,
        "primary_concern": "睡眠不足影响代谢",
        "urgency": "moderate",
        "reasoning": "检测到睡眠时间不足，HRV值偏低提示自律神经功能下降，血糖有上升趋势。建议优先改善睡眠质量。",
        "primary_agent": AgentType.SLEEP,
        "secondary_agents": [AgentType.STRESS, AgentType.GLUCOSE],
        "priority": 3,
        "response_time": "48小时内",
        "recommended_actions": [
            "保证每晚7-8小时睡眠时间",
            "建立固定的睡前放松仪式",
            "避免睡前2小时使用电子设备",
            "监测血糖变化，注意餐后血糖",
            "学习压力管理技巧"
        ],
        "triggers": [
            {
                "tag_id": "sleep_deprivation",
                "name": "睡眠不足",
                "category": TriggerCategory.BEHAVIORAL,
                "severity": TriggerSeverity.MODERATE,
                "confidence": 0.88,
                "metadata": {"sleep_duration": 5.5, "sleep_quality": 0.6}
            },
            {
                "tag_id": "low_hrv",
                "name": "HRV偏低",
                "category": TriggerCategory.PHYSIOLOGICAL,
                "severity": TriggerSeverity.MODERATE,
                "confidence": 0.85,
                "metadata": {"hrv_avg": 45, "normal_range": [60, 100]}
            }
        ],
        "days_ago": 3
    },

    # Case 3: 中度风险 - R2（血糖波动）
    {
        "text_content": "最近饮食不太规律，昨天聚餐吃了很多甜食和碳水。今天测血糖发现偏高，有点担心。最近也没怎么运动，感觉身体有点沉重。",
        "glucose_values": [9.5, 11.2, 13.8],
        "hrv_values": [52, 48, 55],
        "risk_level": RiskLevel.R2,
        "risk_score": 45.7,
        "primary_concern": "血糖波动过大",
        "urgency": "moderate",
        "reasoning": "血糖值显著升高且波动较大，餐后血糖达到13.8 mmol/L，提示饮食控制不当。HRV略低，需要立即调整饮食和增加运动。",
        "primary_agent": AgentType.GLUCOSE,
        "secondary_agents": [AgentType.NUTRITION, AgentType.EXERCISE, AgentType.METABOLIC],
        "priority": 2,
        "response_time": "24小时内",
        "recommended_actions": [
            "立即调整饮食结构，减少高GI食物",
            "监测餐后2小时血糖，每天3次",
            "每天进行30分钟中等强度运动",
            "避免含糖饮料和精制碳水",
            "必要时咨询内分泌科医生"
        ],
        "triggers": [
            {
                "tag_id": "high_glucose",
                "name": "高血糖",
                "category": TriggerCategory.PHYSIOLOGICAL,
                "severity": TriggerSeverity.HIGH,
                "confidence": 0.95,
                "metadata": {"max_glucose": 13.8, "threshold": 10.0}
            },
            {
                "tag_id": "glucose_variability",
                "name": "血糖波动",
                "category": TriggerCategory.PHYSIOLOGICAL,
                "severity": TriggerSeverity.HIGH,
                "confidence": 0.89,
                "metadata": {"std_dev": 2.15, "range": 4.3}
            },
            {
                "tag_id": "poor_diet",
                "name": "饮食不当",
                "category": TriggerCategory.BEHAVIORAL,
                "severity": TriggerSeverity.MODERATE,
                "confidence": 0.82,
                "metadata": {"high_carb_intake": True}
            }
        ],
        "days_ago": 5
    },

    # Case 4: 高度风险 - R3（持续高血糖+情绪问题）
    {
        "text_content": "感觉很糟糕，这一周血糖一直很高，不管怎么控制都降不下来。心情也很低落，对什么都提不起兴趣。晚上失眠，白天疲惫。感觉自己快坚持不下去了。",
        "glucose_values": [13.2, 14.5, 15.8, 13.9],
        "hrv_values": [38, 35, 41, 36],
        "risk_level": RiskLevel.R3,
        "risk_score": 72.4,
        "primary_concern": "持续高血糖伴随情绪低落",
        "urgency": "high",
        "reasoning": "血糖持续处于危险高位（平均14.4 mmol/L），HRV严重偏低提示严重疲劳或抑郁，患者自述情绪低落和失眠。这是代谢危机和心理健康问题的双重风险，需要立即医疗干预。",
        "primary_agent": AgentType.CRISIS,
        "secondary_agents": [AgentType.GLUCOSE, AgentType.MENTAL_HEALTH, AgentType.SLEEP],
        "priority": 1,
        "response_time": "立即",
        "recommended_actions": [
            "⚠️ 立即联系主治医生或急诊",
            "每2小时监测一次血糖",
            "停止所有剧烈运动",
            "确保充足水分摄入",
            "联系心理咨询师进行评估",
            "家人密切陪伴，避免独处",
            "准备急救药物和设备"
        ],
        "triggers": [
            {
                "tag_id": "persistent_hyperglycemia",
                "name": "持续高血糖",
                "category": TriggerCategory.PHYSIOLOGICAL,
                "severity": TriggerSeverity.CRITICAL,
                "confidence": 0.98,
                "metadata": {"avg_glucose": 14.4, "duration_days": 7}
            },
            {
                "tag_id": "depression_signs",
                "name": "抑郁倾向",
                "category": TriggerCategory.PSYCHOLOGICAL,
                "severity": TriggerSeverity.HIGH,
                "confidence": 0.87,
                "metadata": {"anhedonia": True, "hopelessness": True}
            },
            {
                "tag_id": "severe_fatigue",
                "name": "严重疲劳",
                "category": TriggerCategory.PHYSIOLOGICAL,
                "severity": TriggerSeverity.HIGH,
                "confidence": 0.91,
                "metadata": {"hrv_avg": 37.5, "sleep_quality": 0.3}
            }
        ],
        "days_ago": 7
    },

    # Case 5: 轻度风险 - R1（压力大）
    {
        "text_content": "最近项目deadline临近，压力很大。虽然尽量保持运动和健康饮食，但还是感觉紧张和焦虑。睡眠质量一般，经常做梦。",
        "glucose_values": [6.5, 7.8, 6.9],
        "hrv_values": [55, 52, 58],
        "risk_level": RiskLevel.R1,
        "risk_score": 32.1,
        "primary_concern": "压力应激反应",
        "urgency": "moderate",
        "reasoning": "检测到应激反应，虽然血糖控制尚可，但HRV显示自律神经紧张。患者自述焦虑和睡眠问题，需要压力管理干预。",
        "primary_agent": AgentType.STRESS,
        "secondary_agents": [AgentType.SLEEP, AgentType.MENTAL_HEALTH],
        "priority": 3,
        "response_time": "48小时内",
        "recommended_actions": [
            "学习放松技巧（深呼吸、冥想）",
            "保持规律运动，释放压力",
            "与朋友或家人倾诉",
            "合理安排工作和休息时间",
            "必要时进行心理咨询"
        ],
        "triggers": [
            {
                "tag_id": "stress_response",
                "name": "压力应激",
                "category": TriggerCategory.PSYCHOLOGICAL,
                "severity": TriggerSeverity.MODERATE,
                "confidence": 0.84,
                "metadata": {"stress_source": "work", "duration": "2_weeks"}
            },
            {
                "tag_id": "anxiety",
                "name": "焦虑情绪",
                "category": TriggerCategory.PSYCHOLOGICAL,
                "severity": TriggerSeverity.MODERATE,
                "confidence": 0.78,
                "metadata": {"sleep_disturbance": True}
            }
        ],
        "days_ago": 10
    },

    # Case 6: 中度风险 - R2（运动不足）
    {
        "text_content": "这个月基本没运动，每天久坐办公室8-10小时。虽然饮食还算健康，但体重增加了2公斤。感觉体能下降，爬楼梯都气喘。",
        "glucose_values": [7.8, 8.5, 9.2],
        "hrv_values": [48, 51, 46],
        "risk_level": RiskLevel.R2,
        "risk_score": 41.8,
        "primary_concern": "久坐少动导致代谢下降",
        "urgency": "moderate",
        "reasoning": "长期缺乏运动导致血糖升高、体重增加，HRV偏低提示心肺功能下降。需要立即建立运动习惯。",
        "primary_agent": AgentType.EXERCISE,
        "secondary_agents": [AgentType.METABOLIC, AgentType.NUTRITION],
        "priority": 2,
        "response_time": "24小时内",
        "recommended_actions": [
            "每天至少30分钟中等强度运动",
            "每小时站起来活动5分钟",
            "选择喜欢的运动方式（游泳、骑车、快走）",
            "逐步增加运动强度和时间",
            "监测运动前后血糖变化"
        ],
        "triggers": [
            {
                "tag_id": "sedentary_lifestyle",
                "name": "久坐不动",
                "category": TriggerCategory.BEHAVIORAL,
                "severity": TriggerSeverity.HIGH,
                "confidence": 0.93,
                "metadata": {"sitting_hours": 9, "exercise_days": 0}
            },
            {
                "tag_id": "weight_gain",
                "name": "体重增加",
                "category": TriggerCategory.PHYSIOLOGICAL,
                "severity": TriggerSeverity.MODERATE,
                "confidence": 0.86,
                "metadata": {"weight_change": 2.0, "time_period": "1_month"}
            }
        ],
        "days_ago": 12
    },

    # Case 7: 正常偏高 - R1（轻度血糖升高）
    {
        "text_content": "整体状态还不错，但注意到早餐后血糖有点高。可能是最近早餐吃了太多包子和稀饭。其他时间段血糖正常，运动和睡眠都挺好的。",
        "glucose_values": [8.2, 6.1, 5.8],
        "hrv_values": [65, 68, 62],
        "risk_level": RiskLevel.R1,
        "risk_score": 24.6,
        "primary_concern": "餐后血糖略高",
        "urgency": "low",
        "reasoning": "早餐后血糖偏高，可能与高GI食物有关。其他指标正常，通过饮食调整即可改善。",
        "primary_agent": AgentType.NUTRITION,
        "secondary_agents": [AgentType.GLUCOSE, AgentType.TCM],
        "priority": 3,
        "response_time": "3天内",
        "recommended_actions": [
            "调整早餐结构，减少精制碳水",
            "增加蛋白质和膳食纤维",
            "选择低GI食物（燕麦、全麦面包）",
            "监测不同早餐对血糖的影响",
            "保持目前的运动习惯"
        ],
        "triggers": [
            {
                "tag_id": "postprandial_hyperglycemia",
                "name": "餐后高血糖",
                "category": TriggerCategory.PHYSIOLOGICAL,
                "severity": TriggerSeverity.MODERATE,
                "confidence": 0.81,
                "metadata": {"meal": "breakfast", "peak_glucose": 8.2}
            }
        ],
        "days_ago": 14
    },

    # Case 8: 中度风险 - R2（情绪波动）
    {
        "text_content": "心情起伏很大，有时候很开心，有时候突然很沮丧。食欲也跟着变化，情绪低落时会暴食甜食。睡眠不规律，有时很早醒，有时很晚睡。",
        "glucose_values": [6.2, 10.5, 7.8, 11.2],
        "hrv_values": [42, 58, 45, 61],
        "risk_level": RiskLevel.R2,
        "risk_score": 48.9,
        "primary_concern": "情绪性进食导致代谢紊乱",
        "urgency": "moderate",
        "reasoning": "情绪波动引起的暴食行为导致血糖剧烈波动，HRV变化大提示自律神经不稳定。需要心理干预和营养指导。",
        "primary_agent": AgentType.MENTAL_HEALTH,
        "secondary_agents": [AgentType.NUTRITION, AgentType.GLUCOSE, AgentType.SLEEP],
        "priority": 2,
        "response_time": "24小时内",
        "recommended_actions": [
            "学习识别和管理情绪",
            "建立健康的应对机制（而非暴食）",
            "规律进餐，避免过度饥饿",
            "寻求心理咨询支持",
            "建立稳定的作息规律"
        ],
        "triggers": [
            {
                "tag_id": "emotional_eating",
                "name": "情绪性进食",
                "category": TriggerCategory.BEHAVIORAL,
                "severity": TriggerSeverity.HIGH,
                "confidence": 0.89,
                "metadata": {"trigger": "negative_emotions", "frequency": "weekly"}
            },
            {
                "tag_id": "mood_instability",
                "name": "情绪不稳定",
                "category": TriggerCategory.PSYCHOLOGICAL,
                "severity": TriggerSeverity.MODERATE,
                "confidence": 0.85,
                "metadata": {"pattern": "cyclical"}
            },
            {
                "tag_id": "glucose_swings",
                "name": "血糖剧烈波动",
                "category": TriggerCategory.PHYSIOLOGICAL,
                "severity": TriggerSeverity.HIGH,
                "confidence": 0.92,
                "metadata": {"range": 5.0, "frequency": "daily"}
            }
        ],
        "days_ago": 16
    },

    # Case 9: 轻度风险 - R1（熬夜）
    {
        "text_content": "最近在追剧，连续几天都熬夜到凌晨2-3点。白天困倦，喝了很多咖啡提神。饮食有点不规律，有时候忘记吃饭，晚上又吃宵夜。",
        "glucose_values": [7.5, 8.8, 7.2],
        "hrv_values": [49, 44, 52],
        "risk_level": RiskLevel.R1,
        "risk_score": 35.7,
        "primary_concern": "作息紊乱影响代谢",
        "urgency": "moderate",
        "reasoning": "熬夜导致昼夜节律紊乱，血糖升高，HRV降低。咖啡因摄入过多和饮食不规律加重了代谢负担。",
        "primary_agent": AgentType.SLEEP,
        "secondary_agents": [AgentType.NUTRITION, AgentType.METABOLIC],
        "priority": 3,
        "response_time": "48小时内",
        "recommended_actions": [
            "立即调整作息，23:00前入睡",
            "减少咖啡因摄入（下午2点后避免）",
            "规律三餐，避免宵夜",
            "创建有利于睡眠的环境",
            "逐步恢复正常作息"
        ],
        "triggers": [
            {
                "tag_id": "sleep_deprivation_chronic",
                "name": "慢性睡眠不足",
                "category": TriggerCategory.BEHAVIORAL,
                "severity": TriggerSeverity.MODERATE,
                "confidence": 0.91,
                "metadata": {"bedtime": "02:00", "duration_days": 7}
            },
            {
                "tag_id": "circadian_disruption",
                "name": "昼夜节律紊乱",
                "category": TriggerCategory.PHYSIOLOGICAL,
                "severity": TriggerSeverity.MODERATE,
                "confidence": 0.87,
                "metadata": {"irregular_schedule": True}
            }
        ],
        "days_ago": 18
    },

    # Case 10: 优秀状态 - R0（坚持健康生活方式）
    {
        "text_content": "坚持健康生活已经3个月了！每天早起运动，饮食均衡，晚上按时睡觉。感觉精力充沛，心情也很好。体重减了5公斤，血糖控制得很稳定。非常有成就感！",
        "glucose_values": [5.1, 5.6, 5.9, 5.4],
        "hrv_values": [75, 78, 73, 76],
        "risk_level": RiskLevel.R0,
        "risk_score": 8.2,
        "primary_concern": "优秀控制",
        "urgency": "low",
        "reasoning": "所有指标优秀，血糖稳定在理想范围，HRV高提示良好的心血管健康和自律神经功能。患者积极性高，生活方式改变效果显著。",
        "primary_agent": AgentType.COACHING,
        "secondary_agents": [AgentType.MOTIVATION],
        "priority": 4,
        "response_time": "1周内",
        "recommended_actions": [
            "继续保持优秀的生活方式",
            "定期自我监测和记录",
            "可以设定新的健康目标",
            "分享经验，激励他人",
            "每季度全面体检一次"
        ],
        "triggers": [
            {
                "tag_id": "excellent_control",
                "name": "优秀控制",
                "category": TriggerCategory.PHYSIOLOGICAL,
                "severity": TriggerSeverity.LOW,
                "confidence": 0.96,
                "metadata": {"glucose_stability": "excellent", "hrv_avg": 75.5}
            },
            {
                "tag_id": "high_motivation",
                "name": "高积极性",
                "category": TriggerCategory.PSYCHOLOGICAL,
                "severity": TriggerSeverity.LOW,
                "confidence": 0.94,
                "metadata": {"adherence_rate": 0.95, "weight_loss": 5.0}
            }
        ],
        "days_ago": 20
    }
]


# ============================================
# 数据库操作函数
# ============================================

def get_or_create_patient(db: Session) -> User:
    """获取或创建患者用户"""
    user = db.query(User).filter(User.username == "patient_alice").first()

    if not user:
        from core.auth import hash_password
        user = User(
            username="patient_alice",
            email="alice@example.com",
            password_hash=hash_password("password123"),
            role="patient",
            full_name="Alice Wang",
            is_active=True,
            is_verified=True,
            profile={
                "age": 45,
                "chronic_conditions": ["diabetes", "hypertension"],
                "medications": ["metformin"],
                "goals": ["glucose_control", "weight_loss"]
            }
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Created patient user: {user.username}")

    return user


def create_assessment_case(db: Session, user: User, case_data: dict) -> Assessment:
    """创建单个评估案例"""

    # 计算评估时间（往前推N天）
    days_ago = case_data.get("days_ago", 0)
    assessment_time = datetime.utcnow() - timedelta(days=days_ago)

    # 生成assessment_id
    assessment_id = f"ASS-{int(assessment_time.timestamp())}-{random.randint(1000, 9999)}"

    # 创建Assessment记录
    assessment = Assessment(
        assessment_id=assessment_id,
        user_id=user.id,
        text_content=case_data["text_content"],
        glucose_values=case_data["glucose_values"],
        hrv_values=case_data["hrv_values"],
        user_profile_snapshot=user.profile,

        # 风险评估
        risk_level=case_data["risk_level"],
        risk_score=case_data["risk_score"],
        primary_concern=case_data["primary_concern"],
        urgency=case_data["urgency"],
        reasoning=case_data["reasoning"],
        severity_distribution={
            "critical": sum(1 for t in case_data["triggers"] if t["severity"] == TriggerSeverity.CRITICAL),
            "high": sum(1 for t in case_data["triggers"] if t["severity"] == TriggerSeverity.HIGH),
            "moderate": sum(1 for t in case_data["triggers"] if t["severity"] == TriggerSeverity.MODERATE),
            "low": sum(1 for t in case_data["triggers"] if t["severity"] == TriggerSeverity.LOW),
        },

        # 路由决策
        primary_agent=case_data["primary_agent"],
        secondary_agents=[agent.value for agent in case_data["secondary_agents"]],
        priority=case_data["priority"],
        response_time=case_data["response_time"],
        recommended_actions=case_data["recommended_actions"],

        # 状态
        status="completed",
        created_at=assessment_time,
        completed_at=assessment_time
    )

    db.add(assessment)
    db.flush()  # 获取assessment.id

    # 创建Trigger记录
    for trigger_data in case_data["triggers"]:
        trigger_record = TriggerRecord(
            assessment_id=assessment.id,
            tag_id=trigger_data["tag_id"],
            name=trigger_data["name"],
            category=trigger_data["category"],
            severity=trigger_data["severity"],
            confidence=trigger_data["confidence"],
            trigger_metadata=trigger_data.get("metadata", {}),
            created_at=assessment_time
        )
        db.add(trigger_record)

    db.commit()
    db.refresh(assessment)

    return assessment


def create_all_mock_cases():
    """创建所有模拟案例"""
    db = SessionLocal()

    try:
        logger.info("=" * 60)
        logger.info("开始创建模拟案例数据")
        logger.info("=" * 60)

        # 获取或创建患者
        user = get_or_create_patient(db)
        logger.info(f"✓ 患者用户: {user.username} (ID: {user.id})")

        # 清除该用户的旧评估记录（自动删除）
        old_assessments = db.query(Assessment).filter(Assessment.user_id == user.id).all()
        if old_assessments:
            logger.info(f"⚠️  发现 {len(old_assessments)} 条旧评估记录，自动删除...")
            # 由于设置了cascade，删除Assessment会自动删除关联的TriggerRecord
            for assessment in old_assessments:
                db.delete(assessment)
            db.commit()
            logger.info("✓ 已删除旧评估记录")

        # 创建所有案例
        created_assessments = []
        for i, case_data in enumerate(MOCK_CASES, 1):
            assessment = create_assessment_case(db, user, case_data)
            created_assessments.append(assessment)

            logger.info(f"\n[{i}/10] 创建案例:")
            logger.info(f"  评估ID: {assessment.assessment_id}")
            logger.info(f"  风险等级: {assessment.risk_level.value}")
            logger.info(f"  风险分数: {assessment.risk_score}")
            logger.info(f"  主要关注: {assessment.primary_concern}")
            logger.info(f"  Trigger数量: {len(assessment.triggers)}")
            logger.info(f"  时间: {assessment.created_at.strftime('%Y-%m-%d %H:%M')}")

        logger.info("\n" + "=" * 60)
        logger.info(f"✓ 成功创建 {len(created_assessments)} 个模拟案例")
        logger.info("=" * 60)

        # 统计信息
        stats = {
            "R0": sum(1 for a in created_assessments if a.risk_level == RiskLevel.R0),
            "R1": sum(1 for a in created_assessments if a.risk_level == RiskLevel.R1),
            "R2": sum(1 for a in created_assessments if a.risk_level == RiskLevel.R2),
            "R3": sum(1 for a in created_assessments if a.risk_level == RiskLevel.R3),
            "R4": sum(1 for a in created_assessments if a.risk_level == RiskLevel.R4),
        }

        logger.info("\n风险等级分布:")
        for level, count in stats.items():
            logger.info(f"  {level}: {count} 个案例")

        logger.info("\n✓ 数据已同步到数据库")
        logger.info("✓ 前端/H5应用可以立即查看这些案例")

        return created_assessments

    except Exception as e:
        logger.error(f"创建案例失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


# ============================================
# 主函数
# ============================================

if __name__ == "__main__":
    logger.info("模拟案例生成脚本")
    logger.info("=" * 60)

    try:
        assessments = create_all_mock_cases()

        logger.info("\n" + "=" * 60)
        logger.info("✓✓✓ 任务完成 ✓✓✓")
        logger.info("=" * 60)
        logger.info("\n现在可以：")
        logger.info("1. 访问 H5 应用: http://192.168.1.103:5177")
        logger.info("2. 使用账号登录: patient_alice / password123")
        logger.info("3. 查看首页、历史记录、数据分析")
        logger.info("4. 所有10个案例已同步显示")

    except Exception as e:
        logger.error(f"执行失败: {str(e)}")
        sys.exit(1)
