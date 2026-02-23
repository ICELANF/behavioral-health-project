# -*- coding: utf-8 -*-
"""
AI推送建议引擎
Push Recommendation Service

基于穿戴设备数据 + 行为轨迹数据 + 评估数据，
为教练生成评估推送建议。
"""
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from loguru import logger

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import (
    User, BehavioralProfile,
    GlucoseReading, HeartRateReading, SleepRecord, ActivityRecord,
    AssessmentAssignment,
)
from core.behavior_facts_service import BehaviorFactsService


@dataclass
class PushRecommendation:
    """推送建议"""
    student_id: int
    student_name: str
    push_type: str        # "questions" / "scale"
    items: List[str]      # 题目ID列表 或 量表key列表
    item_labels: List[str]
    reasoning: str        # 推荐理由
    priority: str         # high / medium / low
    data_signals: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "student_id": self.student_id,
            "student_name": self.student_name,
            "push_type": self.push_type,
            "items": self.items,
            "item_labels": self.item_labels,
            "reasoning": self.reasoning,
            "priority": self.priority,
            "data_signals": self.data_signals,
        }


class PushRecommendationService:
    """AI推送建议引擎"""

    def __init__(self):
        self.facts_service = BehaviorFactsService()

    def generate_recommendations(self, db: Session, coach_id: int) -> List[PushRecommendation]:
        """为教练生成所有学员的推送建议"""
        recommendations = []

        # 查找教练的所有学员 (权威源: coach_student_bindings)
        from sqlalchemy import text as sa_text
        binding_rows = db.execute(sa_text(
            "SELECT student_id FROM coach_schema.coach_student_bindings "
            "WHERE coach_id = :cid AND is_active = true"
        ), {"cid": coach_id}).fetchall()
        bound_student_ids = {r[0] for r in binding_rows}

        coach_students = []
        if bound_student_ids:
            coach_students = db.query(User).filter(
                User.id.in_(bound_student_ids),
                User.is_active == True,
            ).all()

        if not coach_students:
            # Fallback: check recent assignments
            recent_student_ids = (
                db.query(AssessmentAssignment.student_id)
                .filter(AssessmentAssignment.coach_id == coach_id)
                .distinct()
                .all()
            )
            for (sid,) in recent_student_ids:
                student = db.query(User).filter(User.id == sid).first()
                if student and student not in coach_students:
                    coach_students.append(student)

        for student in coach_students:
            try:
                rec = self._analyze_student(db, student)
                if rec:
                    recommendations.append(rec)
            except Exception as e:
                logger.error(f"分析学员 {student.id} 失败: {e}")

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 9))

        return recommendations

    def generate_for_student(self, db: Session, student_id: int) -> Optional[PushRecommendation]:
        """为特定学员生成推送建议"""
        student = db.query(User).filter(User.id == student_id).first()
        if not student:
            return None
        return self._analyze_student(db, student)

    def _analyze_student(self, db: Session, student: User) -> Optional[PushRecommendation]:
        """分析单个学员，生成推送建议"""
        user_id = student.id
        student_name = student.full_name or student.username
        now = datetime.utcnow()
        seven_days_ago = now - timedelta(days=7)

        # === 数据收集 ===

        # 1. 设备数据 (最近7天)
        device_signals = self._collect_device_signals(db, user_id, seven_days_ago)

        # 2. 行为轨迹
        behavior_facts = self.facts_service.get_facts(db, user_id)

        # 3. 评估画像
        profile = db.query(BehavioralProfile).filter(
            BehavioralProfile.user_id == user_id
        ).first()

        # 4. 最近评估时间
        last_assignment = (
            db.query(AssessmentAssignment)
            .filter(AssessmentAssignment.student_id == user_id)
            .order_by(AssessmentAssignment.created_at.desc())
            .first()
        )
        days_since_assessment = None
        if last_assignment:
            days_since_assessment = (now - last_assignment.created_at).days

        # Check for pending assignment
        has_pending = (
            db.query(AssessmentAssignment)
            .filter(
                AssessmentAssignment.student_id == user_id,
                AssessmentAssignment.status == "pending",
            )
            .first()
        )
        if has_pending:
            return None  # Already has a pending assessment

        # === 决策规则 ===
        data_signals = {
            "device": device_signals,
            "behavior": behavior_facts.to_dict(),
            "days_since_assessment": days_since_assessment,
            "has_profile": profile is not None,
        }

        # Rule 1: 设备异常（血糖/心率超标频繁）
        if device_signals.get("glucose_abnormal_count", 0) >= 3:
            return PushRecommendation(
                student_id=user_id,
                student_name=student_name,
                push_type="questions",
                items=["SPI1", "SPI6", "CAP1", "CAP5", "TTM10"],
                item_labels=["动机评估", "改变理由", "觉察力", "自主感", "接受度"],
                reasoning=f"近7天血糖异常{device_signals['glucose_abnormal_count']}次，需评估营养/运动觉察和改变动机",
                priority="high",
                data_signals=data_signals,
            )

        if device_signals.get("hr_abnormal_count", 0) >= 2:
            return PushRecommendation(
                student_id=user_id,
                student_name=student_name,
                push_type="questions",
                items=["BPT7", "BPT8", "SPI11", "CAP13", "TTM13"],
                item_labels=["情绪影响", "情绪坚持", "能力评估", "资源评估", "尝试行动"],
                reasoning=f"近7天心率异常{device_signals['hr_abnormal_count']}次，需评估情绪状态和行动能力",
                priority="high",
                data_signals=data_signals,
            )

        # Rule 2: 行为回退（连续性中断、完成率下降）
        if behavior_facts.action_interrupt_72h and behavior_facts.completion_rate_30d < 0.5:
            return PushRecommendation(
                student_id=user_id,
                student_name=student_name,
                push_type="questions",
                items=["SPI1", "SPI2", "BPT16", "BPT17", "TTM07"],
                item_labels=["改变重要性", "改变意愿", "矛盾挣扎", "犹豫不决", "被动应对"],
                reasoning=f"72小时行为中断 + 30天完成率仅{behavior_facts.completion_rate_30d*100:.0f}%，需评估动机和矛盾心态",
                priority="high",
                data_signals=data_signals,
            )

        # Rule 3: 阶段停滞（>14天同阶段+低完成率）
        if profile and profile.stage_updated_at:
            days_in_stage = (now - profile.stage_updated_at).days
            if days_in_stage > 14 and behavior_facts.completion_rate_30d < 0.6:
                stage = profile.current_stage.value if profile.current_stage else "S0"
                return PushRecommendation(
                    student_id=user_id,
                    student_name=student_name,
                    push_type="questions",
                    items=["TTM01", "TTM04", "TTM07", "TTM10", "CAP1", "CAP17", "CAP29"],
                    item_labels=["S0觉察", "S1抗拒", "S2应对", "S3接受", "觉察力", "承诺", "期待"],
                    reasoning=f"在{stage}阶段停留{days_in_stage}天，完成率{behavior_facts.completion_rate_30d*100:.0f}%，需重新评估阶段和改变潜力",
                    priority="high",
                    data_signals=data_signals,
                )

        # Rule 4: 无近期评估（>30天）
        if days_since_assessment is None or days_since_assessment > 30:
            return PushRecommendation(
                student_id=user_id,
                student_name=student_name,
                push_type="questions",
                items=["hf20"],  # preset
                item_labels=["20题高频精选"],
                reasoning=f"{'从未评估' if days_since_assessment is None else f'上次评估已过{days_since_assessment}天'}，建议使用HF-20快速筛查",
                priority="medium",
                data_signals=data_signals,
            )

        # Rule 5: 画像不完整（缺BPT6/CAPACITY）
        if profile:
            missing = []
            if not profile.bpt6_type:
                missing.append("bpt6")
            if not profile.capacity_total:
                missing.append("capacity")
            if missing:
                items = []
                labels = []
                if "bpt6" in missing:
                    items.extend(["BPT1", "BPT7", "BPT16"])
                    labels.extend(["行动型", "情绪型", "矛盾型"])
                if "capacity" in missing:
                    items.extend(["CAP1", "CAP5", "CAP17"])
                    labels.extend(["觉察力", "自主感", "承诺"])
                return PushRecommendation(
                    student_id=user_id,
                    student_name=student_name,
                    push_type="questions",
                    items=items,
                    item_labels=labels,
                    reasoning=f"行为画像不完整，缺少{'、'.join(missing)}评估数据",
                    priority="medium",
                    data_signals=data_signals,
                )

        # Rule 6: 一切正常 → 最弱维度的轻量检查
        if profile and profile.capacity_weak:
            weak_dims = profile.capacity_weak[:2] if isinstance(profile.capacity_weak, list) else []
            items = ["SPI1", "CAP29"]
            labels = ["动机检查", "期待检查"]
            return PushRecommendation(
                student_id=user_id,
                student_name=student_name,
                push_type="questions",
                items=items,
                item_labels=labels,
                reasoning=f"状态正常，例行检查最弱维度: {', '.join(weak_dims) if weak_dims else '通用'}",
                priority="low",
                data_signals=data_signals,
            )

        return None

    def _collect_device_signals(self, db: Session, user_id: int, since: datetime) -> Dict[str, Any]:
        """收集最近7天设备数据信号"""
        signals = {}

        # Glucose
        glucose_readings = (
            db.query(GlucoseReading)
            .filter(
                GlucoseReading.user_id == user_id,
                GlucoseReading.recorded_at >= since,
            )
            .all()
        )
        if glucose_readings:
            values = [r.value for r in glucose_readings]
            signals["glucose_count"] = len(values)
            signals["glucose_avg"] = round(sum(values) / len(values), 2)
            signals["glucose_abnormal_count"] = sum(1 for v in values if v > 10.0 or v < 3.9)
            tir = sum(1 for v in values if 3.9 <= v <= 10.0) / len(values)
            signals["glucose_tir"] = round(tir * 100, 1)

        # Heart Rate
        hr_readings = (
            db.query(HeartRateReading)
            .filter(
                HeartRateReading.user_id == user_id,
                HeartRateReading.recorded_at >= since,
            )
            .all()
        )
        if hr_readings:
            rest_hrs = [r.hr for r in hr_readings if r.activity_type in (None, "rest", "sleep")]
            if rest_hrs:
                signals["resting_hr_avg"] = round(sum(rest_hrs) / len(rest_hrs))
            signals["hr_abnormal_count"] = sum(
                1 for r in hr_readings
                if (r.activity_type in (None, "rest", "sleep") and (r.hr > 120 or r.hr < 50))
            )

        # Sleep
        seven_days_ago_str = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        sleep_records = (
            db.query(SleepRecord)
            .filter(
                SleepRecord.user_id == user_id,
                SleepRecord.sleep_date >= seven_days_ago_str,
            )
            .all()
        )
        if sleep_records:
            scores = [r.sleep_score for r in sleep_records if r.sleep_score]
            if scores:
                signals["sleep_avg_score"] = round(sum(scores) / len(scores), 1)

        # Activity
        activity_records = (
            db.query(ActivityRecord)
            .filter(
                ActivityRecord.user_id == user_id,
                ActivityRecord.activity_date >= seven_days_ago_str,
            )
            .all()
        )
        if activity_records:
            steps = [r.steps for r in activity_records]
            signals["steps_avg"] = round(sum(steps) / len(steps))
            sedentary = [r.sedentary_min for r in activity_records if r.sedentary_min]
            if sedentary:
                signals["sedentary_avg_min"] = round(sum(sedentary) / len(sedentary))

        return signals
