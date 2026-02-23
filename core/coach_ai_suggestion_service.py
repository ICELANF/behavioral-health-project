# -*- coding: utf-8 -*-
"""
教练AI建议生成服务（消息/提醒/测评/微行动）
Coach AI Suggestion Service

为教练消息、提醒、测评推荐、微行动推荐生成AI建议，复用 copilot_prescription_service 的模式:
采集学员数据 → 规则引擎生成基线建议 → LLM增强(可选) → 返回建议列表

遵循「AI→审核→推送」原则：AI生成建议 → 教练选择/修改 → 进入审批队列
"""
import json
import re
import time as _time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import desc
from sqlalchemy.orm import Session

from core.models import (
    User,
    BehavioralProfile,
    Assessment,
    CoachMessage,
)


# ── 阶段中文名 ──────────────────────────────────────────────
STAGE_NAMES = {
    "S0": "无知无觉", "S1": "强烈抗拒", "S2": "被动承诺",
    "S3": "勉强接受", "S4": "主动尝试", "S5": "规律践行", "S6": "内化为常",
}

# ── 按阶段的鼓励模板 ──────────────────────────────────────────
STAGE_ENCOURAGEMENT_TEMPLATES = {
    "S0": {"content": "我注意到你最近开始关注健康了，这是很棒的第一步。有什么想了解的随时问我。", "reason": "学员处于认知觉醒初期，需温和引导"},
    "S1": {"content": "改变确实不容易，你能愿意和我聊聊已经很了不起了。我们可以从最小的事情开始。", "reason": "学员处于抗拒期，以共情为主"},
    "S2": {"content": "你上次说愿意试试，这很好。我们一起选一件最简单的小事开始做，怎么样？", "reason": "学员已有承诺意向，需推动行动"},
    "S3": {"content": "看到你最近在努力坚持，虽然偶尔会波动，但整体方向是对的，继续加油！", "reason": "学员已开始行动但不稳定，需正向强化"},
    "S4": {"content": "你最近的表现真的很棒！保持这个节奏，好习惯正在慢慢形成。", "reason": "学员主动尝试中，巩固积极行为"},
    "S5": {"content": "你已经形成了很好的习惯，真为你高兴！记住，偶尔的放松不等于放弃。", "reason": "学员已规律践行，预防倦怠"},
    "S6": {"content": "你现在已经是健康生活的榜样了！也许你可以把经验分享给其他人。", "reason": "学员已内化行为，鼓励导师角色"},
}

# ── 按风险等级的关切模板 ──────────────────────────────────────
RISK_CONCERN_TEMPLATES = {
    "crisis": {"content": "我注意到你最近的一些指标变化比较大，我很关心你的状态。今天方便聊聊吗？有什么困难我们一起面对。", "reason": "学员处于危机状态，需紧急关注"},
    "high": {"content": "你最近的健康数据有些需要关注的地方，别担心，我们来一起看看怎么调整。", "reason": "学员风险较高，需及时干预"},
}

# ── 按活跃度的再激活模板 ──────────────────────────────────────
ACTIVITY_REENGAGEMENT_TEMPLATES = {
    "inactive": {"content": "好几天没看到你了，一切还好吗？不管多忙，哪怕做一件小事也是进步。", "reason": "学员近期不活跃，需温和唤回"},
    "dormant": {"content": "很久没有联系了，我一直在关注你。什么时候方便我们聊聊？不管之前怎样，随时可以重新开始。", "reason": "学员长期沉默，需重新建立连接"},
}

# ── 消息类型对应的基础模板 ────────────────────────────────────
MESSAGE_TYPE_TEMPLATES = {
    "text": [
        {"content": "你好，最近身体感觉怎么样？有什么想跟我分享的吗？", "reason": "日常问候，保持连接"},
        {"content": "看了你最近的数据记录，整体趋势不错，有几个地方我们可以一起关注一下。", "reason": "基于数据的常规沟通"},
    ],
    "encouragement": [
        {"content": "你最近的坚持我都看在眼里，真的很棒！", "reason": "正向反馈强化"},
        {"content": "每一个小进步都值得庆祝，你做到了！", "reason": "肯定学员努力"},
    ],
    "reminder": [
        {"content": "温馨提醒：今天别忘了完成你的微行动哦～", "reason": "行为提醒"},
        {"content": "记得按时吃饭、适当运动，照顾好自己。", "reason": "生活习惯提醒"},
    ],
    "advice": [
        {"content": "根据你最近的情况，建议这周可以试试每天饭后散步10分钟。", "reason": "个性化建议"},
        {"content": "最近天气变化大，注意保暖的同时也别忘了适当运动。", "reason": "季节性建议"},
    ],
}

# ── 提醒类型模板 ──────────────────────────────────────────────
REMINDER_TYPE_TEMPLATES = {
    "behavior": [
        {"title": "今日微行动提醒", "content": "别忘了完成今天的行为练习，哪怕只做5分钟也是进步！", "cron_time": "09:00", "reason": "行为习惯养成需要每日提醒"},
        {"title": "饭后散步提醒", "content": "吃完午饭休息10分钟后，起来散散步吧～", "cron_time": "12:30", "reason": "餐后运动有助于血糖控制"},
        {"title": "睡前放松提醒", "content": "放下手机，做几次深呼吸，准备好好休息吧。", "cron_time": "22:00", "reason": "睡前放松有助提升睡眠质量"},
    ],
    "medication": [
        {"title": "用药提醒", "content": "记得按时服药，这是管理健康的重要一步。", "cron_time": "08:00", "reason": "用药依从性对健康管理至关重要"},
        {"title": "餐前用药提醒", "content": "即将到饭点了，请提前准备好需要餐前服用的药物。", "cron_time": "11:30", "reason": "餐前药物需要提前提醒"},
    ],
    "visit": [
        {"title": "随访预约提醒", "content": "您有一次健康随访即将到来，请做好准备。", "cron_time": "09:00", "reason": "定期随访有助于持续健康管理"},
    ],
    "assessment": [
        {"title": "健康数据记录提醒", "content": "今天记得记录你的健康数据（血糖/血压/体重），数据是改善的基础。", "cron_time": "08:30", "reason": "规律的自我监测是行为改变的关键"},
        {"title": "周评估提醒", "content": "新的一周开始了，花几分钟回顾上周的进步和这周的目标吧。", "cron_time": "09:00", "reason": "周期性自我评估促进反思和调整"},
    ],
}

# ── 测评量表推荐模板 ─────────────────────────────────────────
ASSESSMENT_SCALE_TEMPLATES = {
    "initial": [
        {"scale": "hf20", "title": "HF-20 行为健康快速筛查", "reason": "学员尚无评估记录，建议先做初筛了解整体状态"},
        {"scale": "ttm7", "title": "TTM-7 变化阶段评估", "reason": "判断学员当前行为改变阶段，制定针对性干预"},
        {"scale": "capacity", "title": "行为能力评估", "reason": "了解学员薄弱能力维度，优先改善短板"},
    ],
    "high_risk": [
        {"scale": "hf50", "title": "HF-50 行为健康全面评估", "reason": "学员风险较高，需全面深度评估"},
        {"scale": "bpt6", "title": "BPT-6 行为人格类型评估", "reason": "了解行为人格特征，优化干预策略"},
        {"scale": "spi", "title": "SPI 自我践行指数评估", "reason": "评估自我管理能力，识别干预切入点"},
    ],
    "reassessment": [
        {"scale": "ttm7", "title": "TTM-7 阶段复评", "reason": "距上次评估已有一段时间，建议复评阶段变化"},
        {"scale": "capacity", "title": "能力维度复评", "reason": "对比前次评估，追踪能力提升"},
        {"scale": "hf20", "title": "HF-20 周期性筛查", "reason": "定期筛查维持健康管理质量"},
    ],
}

# ── 微行动推荐模板（按阶段分级） ─────────────────────────────
MICRO_ACTION_STAGE_TEMPLATES = {
    "S0": [
        {"title": "每天记录一次体重", "description": "早起后空腹称重并记录，培养自我监测意识", "domain": "nutrition", "frequency": "每天", "duration_days": 7, "reason": "认知觉醒期，从最简单的记录开始"},
        {"title": "阅读一篇健康小知识", "description": "每天花3分钟阅读平台推荐的健康知识", "domain": "cognitive", "frequency": "每天", "duration_days": 7, "reason": "激发健康意识，降低改变门槛"},
        {"title": "深呼吸练习1分钟", "description": "找一个安静的地方，做10次深呼吸", "domain": "emotion", "frequency": "每天", "duration_days": 7, "reason": "极低门槛的放松练习，建立行为习惯"},
    ],
    "S1": [
        {"title": "饭后站立5分钟", "description": "午饭或晚饭后站立5分钟，不要马上坐下", "domain": "exercise", "frequency": "每天", "duration_days": 7, "reason": "抗拒期，最小行动先破冰"},
        {"title": "喝一杯温水", "description": "早起后喝一杯250ml温水", "domain": "nutrition", "frequency": "每天", "duration_days": 7, "reason": "简单易行，无压力的健康习惯"},
        {"title": "记录今天的心情", "description": "用一个词描述今天的心情状态", "domain": "emotion", "frequency": "每天", "duration_days": 7, "reason": "培养情绪觉察能力"},
    ],
    "S2": [
        {"title": "饭后散步10分钟", "description": "午饭或晚饭后慢走10分钟", "domain": "exercise", "frequency": "每天", "duration_days": 14, "reason": "已有承诺，推动实际行动"},
        {"title": "记录三餐内容", "description": "简单记录每餐吃了什么", "domain": "nutrition", "frequency": "每天", "duration_days": 14, "reason": "增强饮食自我意识"},
        {"title": "睡前放下手机", "description": "睡前30分钟将手机放到卧室外", "domain": "sleep", "frequency": "每天", "duration_days": 14, "reason": "改善睡眠质量的第一步"},
    ],
    "S3": [
        {"title": "快走20分钟", "description": "每天进行20分钟的快走运动", "domain": "exercise", "frequency": "每天", "duration_days": 14, "reason": "已开始行动，逐步增加运动量"},
        {"title": "一餐健康饮食", "description": "每天至少有一餐按照健康食谱执行", "domain": "nutrition", "frequency": "每天", "duration_days": 14, "reason": "固化健康饮食习惯"},
        {"title": "练习正念冥想5分钟", "description": "找一段正念引导音频，跟着练习5分钟", "domain": "emotion", "frequency": "每天", "duration_days": 14, "reason": "增强情绪管理能力"},
    ],
    "S4": [
        {"title": "30分钟有氧运动", "description": "慢跑、骑行或游泳30分钟", "domain": "exercise", "frequency": "每天", "duration_days": 21, "reason": "主动尝试期，建立规律运动习惯"},
        {"title": "控制碳水摄入", "description": "午餐主食减半，用蔬菜和蛋白质补充", "domain": "nutrition", "frequency": "每天", "duration_days": 21, "reason": "精细化饮食管理"},
        {"title": "睡眠日记", "description": "记录入睡时间、醒来时间和睡眠质量评分", "domain": "sleep", "frequency": "每天", "duration_days": 21, "reason": "量化追踪睡眠改善"},
    ],
    "S5": [
        {"title": "综合健康打卡", "description": "运动+饮食+睡眠三维度每日打卡", "domain": "exercise", "frequency": "每天", "duration_days": 30, "reason": "规律践行期，维持多维度健康习惯"},
        {"title": "分享健康心得", "description": "在平台上分享一条自己的健康管理经验", "domain": "social", "frequency": "每周", "duration_days": 30, "reason": "通过分享巩固内化"},
        {"title": "带动身边人一起运动", "description": "邀请家人或朋友一起散步或运动", "domain": "social", "frequency": "每周", "duration_days": 30, "reason": "社交支持增强行为持续性"},
    ],
    "S6": [
        {"title": "制定本周健康计划", "description": "每周一规划本周的运动、饮食和休息安排", "domain": "cognitive", "frequency": "每周", "duration_days": 30, "reason": "内化为常，自主规划"},
        {"title": "健康知识分享", "description": "为平台其他学员撰写一篇经验分享", "domain": "social", "frequency": "每周", "duration_days": 30, "reason": "榜样角色，帮助他人"},
        {"title": "指导新学员", "description": "为新加入的学员提供一次经验交流", "domain": "social", "frequency": "每周", "duration_days": 30, "reason": "导师角色转化，社会价值实现"},
    ],
}


# ── LLM 冷却缓存 ─────────────────────────────────────────────
_llm_last_fail_time: float = 0.0
_LLM_COOLDOWN = 300.0  # 5 分钟


class CoachAISuggestionService:
    """为教练消息/提醒生成AI建议的无状态服务"""

    # ── 消息建议 ──────────────────────────────────────────────

    def generate_message_suggestions(
        self,
        db: Session,
        student_id: int,
        coach_id: int,
        message_type: str = "text",
        context: str = "",
    ) -> Dict[str, Any]:
        """
        生成消息建议

        Returns:
            {
              "suggestions": [{"content": "...", "reason": "..."}],
              "student_summary": "学员张三, 准备期, 中风险, 活跃",
              "meta": {"source": "llm"|"rules", "model": "..."}
            }
        """
        student_data = self._gather_student_data(db, student_id)
        if student_data is None:
            return {
                "suggestions": self._default_message_suggestions(message_type),
                "student_summary": "学员不存在",
                "meta": {"source": "error"},
            }

        # 规则引擎基线 (保底)
        rule_suggestions = self._build_rule_message_suggestions(
            student_data, message_type
        )

        # LLM 增强
        llm_suggestions = self._call_llm_message_suggestions(
            student_data, message_type, context
        )

        suggestions = llm_suggestions if llm_suggestions else rule_suggestions
        source = "llm" if llm_suggestions else "rules"

        return {
            "suggestions": suggestions[:3],
            "student_summary": self._build_student_summary(student_data),
            "meta": {"source": source},
        }

    # ── 提醒建议 ──────────────────────────────────────────────

    def generate_reminder_suggestions(
        self,
        db: Session,
        student_id: int,
        coach_id: int,
        reminder_type: str = "behavior",
    ) -> Dict[str, Any]:
        """
        生成提醒建议 (标题+内容+推荐时间)

        Returns:
            {
              "suggestions": [{"title": "...", "content": "...", "cron_time": "08:00", "reason": "..."}],
              "student_summary": "...",
              "meta": {"source": "llm"|"rules"}
            }
        """
        student_data = self._gather_student_data(db, student_id)
        if student_data is None:
            templates = REMINDER_TYPE_TEMPLATES.get(reminder_type, REMINDER_TYPE_TEMPLATES["behavior"])
            return {
                "suggestions": templates[:3],
                "student_summary": "学员不存在",
                "meta": {"source": "error"},
            }

        # 规则引擎基线
        rule_suggestions = self._build_rule_reminder_suggestions(
            student_data, reminder_type
        )

        # LLM 增强
        llm_suggestions = self._call_llm_reminder_suggestions(
            student_data, reminder_type
        )

        suggestions = llm_suggestions if llm_suggestions else rule_suggestions

        return {
            "suggestions": suggestions[:3],
            "student_summary": self._build_student_summary(student_data),
            "meta": {"source": "llm" if llm_suggestions else "rules"},
        }

    # ── 测评建议 ──────────────────────────────────────────────

    def generate_assessment_suggestions(
        self,
        db: Session,
        student_id: int,
        coach_id: int,
    ) -> Dict[str, Any]:
        """
        AI建议: 推荐评估量表 + 理由

        Returns:
            {
              "suggestions": [{"scale": "hf20", "title": "...", "reason": "..."}],
              "student_summary": "...",
              "meta": {"source": "llm"|"rules"}
            }
        """
        student_data = self._gather_student_data(db, student_id)
        if student_data is None:
            return {
                "suggestions": ASSESSMENT_SCALE_TEMPLATES["initial"],
                "student_summary": "学员不存在",
                "meta": {"source": "error"},
            }

        rule_suggestions = self._build_rule_assessment_suggestions(db, student_data)

        llm_suggestions = self._call_llm_assessment_suggestions(student_data)
        suggestions = llm_suggestions if llm_suggestions else rule_suggestions

        return {
            "suggestions": suggestions[:3],
            "student_summary": self._build_student_summary(student_data),
            "meta": {"source": "llm" if llm_suggestions else "rules"},
        }

    # ── 微行动建议 ────────────────────────────────────────────

    def generate_micro_action_suggestions(
        self,
        db: Session,
        student_id: int,
        coach_id: int,
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        AI建议: 推荐微行动任务（可按干预领域过滤）

        Args:
            domain: 干预领域 (nutrition/exercise/sleep/emotion/stress/cognitive/social)
                    为空时返回综合建议

        Returns:
            {
              "suggestions": [{"title": "...", "description": "...", "domain": "...",
                               "frequency": "每天", "duration_days": 7, "reason": "..."}],
              "student_summary": "...",
              "meta": {"source": "llm"|"rules"}
            }
        """
        student_data = self._gather_student_data(db, student_id)
        if student_data is None:
            return {
                "suggestions": MICRO_ACTION_STAGE_TEMPLATES["S1"],
                "student_summary": "学员不存在",
                "meta": {"source": "error"},
            }

        rule_suggestions = self._build_rule_micro_action_suggestions(db, student_data, domain=domain)

        llm_suggestions = self._call_llm_micro_action_suggestions(student_data, domain=domain)
        suggestions = llm_suggestions if llm_suggestions else rule_suggestions

        return {
            "suggestions": suggestions[:3],
            "student_summary": self._build_student_summary(student_data),
            "meta": {"source": "llm" if llm_suggestions else "rules"},
        }

    # ── 数据采集 ──────────────────────────────────────────────

    def _gather_student_data(self, db: Session, student_id: int) -> Optional[Dict]:
        """采集学员基本画像数据"""
        user = db.query(User).filter(User.id == student_id).first()
        if not user:
            return None

        # BehavioralProfile
        profile = (
            db.query(BehavioralProfile)
            .filter(BehavioralProfile.user_id == student_id)
            .first()
        )

        stage = "S1"
        bpt6_type = "mixed"
        capacity_weak = []
        if profile:
            stage = getattr(profile, "current_stage", "S1") or "S1"
            if hasattr(stage, "value"):
                stage = stage.value
            bpt6_type = getattr(profile, "bpt6_type", "mixed") or "mixed"
            capacity_weak = getattr(profile, "capacity_weak", []) or []

        # 最新评估
        assessment = (
            db.query(Assessment)
            .filter(Assessment.user_id == student_id)
            .order_by(desc(Assessment.created_at))
            .first()
        )
        risk_level = "normal"
        if assessment:
            risk_level = getattr(assessment, "risk_level", "normal") or "normal"

        # 活跃度 (简化: 查最近7天消息数)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_msg_count = (
            db.query(CoachMessage)
            .filter(
                CoachMessage.student_id == student_id,
                CoachMessage.created_at >= seven_days_ago,
            )
            .count()
        )

        # 学员分类 (graceful)
        activity = "moderate"
        try:
            from core.student_classification_service import classify_students_batch
            classifications = classify_students_batch(db, [student_id])
            if student_id in classifications:
                activity = classifications[student_id].activity
        except Exception:
            pass

        # 最近3条消息 (避免重复建议)
        recent_messages = (
            db.query(CoachMessage)
            .filter(CoachMessage.student_id == student_id)
            .order_by(desc(CoachMessage.created_at))
            .limit(3)
            .all()
        )
        recent_contents = [m.content[:50] for m in recent_messages] if recent_messages else []

        return {
            "user": user,
            "student_name": user.full_name or user.username,
            "stage": stage,
            "stage_name": STAGE_NAMES.get(stage, stage),
            "bpt6_type": bpt6_type,
            "capacity_weak": capacity_weak,
            "risk_level": risk_level,
            "activity": activity,
            "recent_messages": recent_contents,
        }

    def _build_student_summary(self, data: Dict) -> str:
        """构建学员一行摘要"""
        return (
            f"学员{data['student_name']}, "
            f"{data['stage_name']}({data['stage']}), "
            f"风险:{data['risk_level']}, "
            f"活跃度:{data['activity']}"
        )

    # ── 规则引擎: 消息 ───────────────────────────────────────

    def _build_rule_message_suggestions(
        self, data: Dict, message_type: str
    ) -> List[Dict]:
        suggestions = []
        stage = data["stage"]
        risk = data["risk_level"]
        activity = data["activity"]

        # 1. 按消息类型基础建议
        if message_type == "encouragement" and stage in STAGE_ENCOURAGEMENT_TEMPLATES:
            suggestions.append(STAGE_ENCOURAGEMENT_TEMPLATES[stage])
        else:
            type_templates = MESSAGE_TYPE_TEMPLATES.get(message_type, MESSAGE_TYPE_TEMPLATES["text"])
            if type_templates:
                suggestions.append(type_templates[0])

        # 2. 风险关切
        if risk in ("crisis", "high") and risk in RISK_CONCERN_TEMPLATES:
            suggestions.append(RISK_CONCERN_TEMPLATES[risk])

        # 3. 活跃度再激活
        if activity in ("inactive", "dormant") and activity in ACTIVITY_REENGAGEMENT_TEMPLATES:
            suggestions.append(ACTIVITY_REENGAGEMENT_TEMPLATES[activity])

        # 4. 阶段匹配鼓励 (补充)
        if len(suggestions) < 3 and stage in STAGE_ENCOURAGEMENT_TEMPLATES:
            enc = STAGE_ENCOURAGEMENT_TEMPLATES[stage]
            if enc not in suggestions:
                suggestions.append(enc)

        # 5. 补齐到3条
        fallback_pool = MESSAGE_TYPE_TEMPLATES.get(message_type, MESSAGE_TYPE_TEMPLATES["text"])
        for tpl in fallback_pool:
            if len(suggestions) >= 3:
                break
            if tpl not in suggestions:
                suggestions.append(tpl)

        # 最后兜底
        while len(suggestions) < 3:
            suggestions.append({
                "content": "有什么需要帮助的随时告诉我，我们一起加油！",
                "reason": "通用关怀",
            })

        return suggestions[:3]

    def _default_message_suggestions(self, message_type: str) -> List[Dict]:
        """默认建议 (无学员数据时)"""
        templates = MESSAGE_TYPE_TEMPLATES.get(message_type, MESSAGE_TYPE_TEMPLATES["text"])
        result = list(templates)
        while len(result) < 3:
            result.append({"content": "加油，我们一起努力！", "reason": "通用鼓励"})
        return result[:3]

    # ── 规则引擎: 提醒 ───────────────────────────────────────

    def _build_rule_reminder_suggestions(
        self, data: Dict, reminder_type: str
    ) -> List[Dict]:
        templates = REMINDER_TYPE_TEMPLATES.get(
            reminder_type, REMINDER_TYPE_TEMPLATES["behavior"]
        )
        suggestions = list(templates)

        # 补齐到3条
        while len(suggestions) < 3:
            suggestions.append({
                "title": "健康习惯提醒",
                "content": "每天进步一点点，坚持就是胜利！",
                "cron_time": "09:00",
                "reason": "通用行为习惯提醒",
            })

        return suggestions[:3]

    # ── 规则引擎: 测评 ───────────────────────────────────────

    def _build_rule_assessment_suggestions(
        self, db: Session, data: Dict
    ) -> List[Dict]:
        stage = data["stage"]
        risk = data["risk_level"]

        # 查最近评估
        last_assessment = (
            db.query(Assessment)
            .filter(Assessment.user_id == data["user"].id)
            .order_by(desc(Assessment.created_at))
            .first()
        )

        # 查最近评估指派
        from core.models import AssessmentAssignment
        last_assignment = (
            db.query(AssessmentAssignment)
            .filter(AssessmentAssignment.student_id == data["user"].id)
            .order_by(AssessmentAssignment.created_at.desc())
            .first()
        )

        has_any_assessment = last_assessment is not None or last_assignment is not None

        if not has_any_assessment:
            return list(ASSESSMENT_SCALE_TEMPLATES["initial"])
        elif risk in ("crisis", "high"):
            return list(ASSESSMENT_SCALE_TEMPLATES["high_risk"])
        else:
            return list(ASSESSMENT_SCALE_TEMPLATES["reassessment"])

    # ── 规则引擎: 微行动 ─────────────────────────────────────

    def _build_rule_micro_action_suggestions(
        self, db: Session, data: Dict, domain: Optional[str] = None
    ) -> List[Dict]:
        stage = data["stage"]

        # 查已有任务完成率
        from core.models import MicroActionTask
        recent_tasks = (
            db.query(MicroActionTask)
            .filter(
                MicroActionTask.user_id == data["user"].id,
                MicroActionTask.scheduled_date >= (datetime.utcnow() - timedelta(days=14)).strftime("%Y-%m-%d"),
            )
            .all()
        )
        total = len(recent_tasks)
        completed = sum(1 for t in recent_tasks if t.status == "completed")
        completion_rate = completed / total if total > 0 else 0

        # 根据阶段选择模板
        effective_stage = stage
        if completion_rate < 0.3 and stage not in ("S0", "S1"):
            effective_stage = f"S{max(int(stage[1]) - 1, 0)}"

        templates = MICRO_ACTION_STAGE_TEMPLATES.get(effective_stage, MICRO_ACTION_STAGE_TEMPLATES["S1"])

        if effective_stage != stage:
            templates = [
                {**s, "reason": s["reason"] + "（完成率较低，适当降低难度）"}
                for s in templates
            ]

        # 按干预领域过滤
        if domain:
            domain_filtered = [s for s in templates if s.get("domain") == domain]
            if domain_filtered:
                suggestions = domain_filtered
            else:
                # 该阶段没有此领域的模板，从所有阶段中找
                all_domain = []
                for stg_key, stg_templates in MICRO_ACTION_STAGE_TEMPLATES.items():
                    all_domain.extend([s for s in stg_templates if s.get("domain") == domain])
                suggestions = all_domain if all_domain else list(templates)
        else:
            suggestions = list(templates)

        return suggestions[:3]

    # ── LLM 增强: 测评 ───────────────────────────────────────

    def _call_llm_assessment_suggestions(
        self, data: Dict
    ) -> Optional[List[Dict]]:
        global _llm_last_fail_time

        now = _time.time()
        if _llm_last_fail_time > 0 and (now - _llm_last_fail_time) < _LLM_COOLDOWN:
            return None

        try:
            from core.llm_client import get_llm_client
            client = get_llm_client()
            cloud_has_key = (
                hasattr(client, "_cloud")
                and client._cloud is not None
                and getattr(client._cloud, "api_key", None)
            )
            local_ok = hasattr(client, "_local_available") and client._local_available()
            if not cloud_has_key and not local_ok:
                return None
        except Exception:
            return None

        system_prompt = (
            "你是行为健康教练的AI助手。根据学员画像推荐3个最合适的评估量表。\n"
            "返回纯JSON数组，不要markdown代码块。每条格式:\n"
            '[{"scale": "量表代号(hf20/hf50/ttm7/big5/bpt6/capacity/spi)", '
            '"title": "量表中文名", "reason": "推荐理由(30-50字)"}]\n'
            "可用量表: hf20(快速筛查20题), hf50(全面评估50题), ttm7(变化阶段), "
            "big5(大五人格), bpt6(行为人格类型), capacity(行为能力), spi(自我践行指数)"
        )

        user_prompt = (
            f"学员: {data['student_name']}, 阶段: {data['stage']}({data['stage_name']})\n"
            f"风险: {data['risk_level']}, 活跃度: {data['activity']}\n"
            f"薄弱能力: {', '.join(data['capacity_weak']) if data['capacity_weak'] else '无'}\n"
            f"\n请推荐3个最合适的评估量表。"
        )

        try:
            resp = client.chat(system=system_prompt, user=user_prompt, temperature=0.5, timeout=15.0)
            if not resp.success:
                _llm_last_fail_time = _time.time()
                return None

            content = resp.content.strip()
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)

            parsed = json.loads(content)
            if isinstance(parsed, list) and len(parsed) >= 2:
                return [
                    {"scale": s.get("scale", ""), "title": s.get("title", ""), "reason": s.get("reason", "")}
                    for s in parsed[:3]
                    if s.get("scale")
                ]
            return None
        except Exception as e:
            logger.warning(f"[coach-ai-suggest] LLM 测评建议失败: {e}")
            _llm_last_fail_time = _time.time()
            return None

    # ── LLM 增强: 微行动 ─────────────────────────────────────

    def _call_llm_micro_action_suggestions(
        self, data: Dict, domain: Optional[str] = None
    ) -> Optional[List[Dict]]:
        global _llm_last_fail_time

        now = _time.time()
        if _llm_last_fail_time > 0 and (now - _llm_last_fail_time) < _LLM_COOLDOWN:
            return None

        try:
            from core.llm_client import get_llm_client
            client = get_llm_client()
            cloud_has_key = (
                hasattr(client, "_cloud")
                and client._cloud is not None
                and getattr(client._cloud, "api_key", None)
            )
            local_ok = hasattr(client, "_local_available") and client._local_available()
            if not cloud_has_key and not local_ok:
                return None
        except Exception:
            return None

        system_prompt = (
            "你是行为健康教练的AI助手。根据学员画像推荐3个合适的微行动任务。\n"
            "返回纯JSON数组，不要markdown代码块。每条格式:\n"
            '[{"title": "任务标题(10-20字)", "description": "任务描述(30-80字)", '
            '"domain": "领域(nutrition/exercise/sleep/emotion/stress/cognitive/social)", '
            '"frequency": "每天|每周", "duration_days": 7|14|21|30, '
            '"reason": "推荐理由(20-40字)"}]\n'
            "要求: 匹配学员阶段、循序渐进、具体可操作。"
        )

        domain_labels = {
            "nutrition": "营养管理", "exercise": "运动管理", "sleep": "睡眠管理",
            "emotion": "情绪管理", "stress": "压力管理", "cognitive": "认知管理", "social": "社交管理",
        }
        domain_hint = f"\n干预领域: {domain_labels.get(domain, domain)}（所有建议必须属于此领域）" if domain else ""

        user_prompt = (
            f"学员: {data['student_name']}, 阶段: {data['stage']}({data['stage_name']})\n"
            f"风险: {data['risk_level']}, 活跃度: {data['activity']}\n"
            f"薄弱能力: {', '.join(data['capacity_weak']) if data['capacity_weak'] else '无'}"
            f"{domain_hint}\n"
            f"\n请推荐3个合适的微行动任务。"
        )

        try:
            resp = client.chat(system=system_prompt, user=user_prompt, temperature=0.7, timeout=15.0)
            if not resp.success:
                _llm_last_fail_time = _time.time()
                return None

            content = resp.content.strip()
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)

            parsed = json.loads(content)
            if isinstance(parsed, list) and len(parsed) >= 2:
                return [
                    {
                        "title": s.get("title", ""),
                        "description": s.get("description", ""),
                        "domain": s.get("domain", "exercise"),
                        "frequency": s.get("frequency", "每天"),
                        "duration_days": s.get("duration_days", 7),
                        "reason": s.get("reason", ""),
                    }
                    for s in parsed[:3]
                    if s.get("title")
                ]
            return None
        except Exception as e:
            logger.warning(f"[coach-ai-suggest] LLM 微行动建议失败: {e}")
            _llm_last_fail_time = _time.time()
            return None

    # ── LLM 增强: 消息 ───────────────────────────────────────

    def _call_llm_message_suggestions(
        self, data: Dict, message_type: str, context: str
    ) -> Optional[List[Dict]]:
        """调用 LLM 生成个性化消息建议"""
        global _llm_last_fail_time

        now = _time.time()
        if _llm_last_fail_time > 0 and (now - _llm_last_fail_time) < _LLM_COOLDOWN:
            return None

        try:
            from core.llm_client import get_llm_client
            client = get_llm_client()

            # 快速检查可用性
            cloud_has_key = (
                hasattr(client, "_cloud")
                and client._cloud is not None
                and getattr(client._cloud, "api_key", None)
            )
            local_ok = hasattr(client, "_local_available") and client._local_available()
            if not cloud_has_key and not local_ok:
                return None
        except Exception:
            return None

        type_labels = {
            "text": "日常沟通", "encouragement": "鼓励激励",
            "reminder": "温馨提醒", "advice": "专业建议",
        }

        system_prompt = (
            "你是行为健康教练的AI助手。根据学员画像为教练生成3条个性化消息建议。\n"
            "返回纯JSON数组，不要markdown代码块。每条格式:\n"
            '[{"content": "消息内容(50-150字)", "reason": "建议理由(20-40字)"}]\n'
            "要求: 温暖专业、具体可操作、匹配学员当前阶段和需求。不要使用模板化语言。"
        )

        user_prompt = (
            f"学员: {data['student_name']}\n"
            f"阶段: {data['stage']}({data['stage_name']})\n"
            f"风险: {data['risk_level']}\n"
            f"活跃度: {data['activity']}\n"
            f"薄弱能力: {', '.join(data['capacity_weak']) if data['capacity_weak'] else '无'}\n"
            f"消息类型: {type_labels.get(message_type, message_type)}\n"
            f"教练补充: {context or '无'}\n"
            f"最近消息: {'; '.join(data['recent_messages']) if data['recent_messages'] else '无'}\n"
            f"\n请生成3条{type_labels.get(message_type, message_type)}消息建议。"
        )

        try:
            resp = client.chat(
                system=system_prompt,
                user=user_prompt,
                temperature=0.7,
                timeout=15.0,
            )
            if not resp.success:
                _llm_last_fail_time = _time.time()
                return None

            content = resp.content.strip()
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)

            parsed = json.loads(content)
            if isinstance(parsed, list) and len(parsed) >= 2:
                return [
                    {"content": s.get("content", ""), "reason": s.get("reason", "")}
                    for s in parsed[:3]
                    if s.get("content")
                ]

            logger.warning("[coach-ai-suggest] LLM 返回格式不符")
            return None

        except Exception as e:
            logger.warning(f"[coach-ai-suggest] LLM 消息建议失败: {e}")
            _llm_last_fail_time = _time.time()
            return None

    # ── LLM 增强: 提醒 ───────────────────────────────────────

    def _call_llm_reminder_suggestions(
        self, data: Dict, reminder_type: str
    ) -> Optional[List[Dict]]:
        """调用 LLM 生成个性化提醒建议"""
        global _llm_last_fail_time

        now = _time.time()
        if _llm_last_fail_time > 0 and (now - _llm_last_fail_time) < _LLM_COOLDOWN:
            return None

        try:
            from core.llm_client import get_llm_client
            client = get_llm_client()
            cloud_has_key = (
                hasattr(client, "_cloud")
                and client._cloud is not None
                and getattr(client._cloud, "api_key", None)
            )
            local_ok = hasattr(client, "_local_available") and client._local_available()
            if not cloud_has_key and not local_ok:
                return None
        except Exception:
            return None

        type_labels = {
            "behavior": "行为习惯", "medication": "用药",
            "visit": "随访", "assessment": "评估记录",
        }

        system_prompt = (
            "你是行为健康教练的AI助手。根据学员画像为教练生成3条个性化提醒建议。\n"
            "返回纯JSON数组，不要markdown代码块。每条格式:\n"
            '[{"title": "提醒标题(10-20字)", "content": "提醒内容(30-80字)", "cron_time": "HH:MM", "reason": "理由(20字)"}]\n'
            "cron_time 是建议的每日提醒时间。"
        )

        user_prompt = (
            f"学员: {data['student_name']}, 阶段: {data['stage']}({data['stage_name']})\n"
            f"风险: {data['risk_level']}, 活跃度: {data['activity']}\n"
            f"提醒类型: {type_labels.get(reminder_type, reminder_type)}\n"
            f"\n请生成3条{type_labels.get(reminder_type, reminder_type)}提醒建议。"
        )

        try:
            resp = client.chat(
                system=system_prompt,
                user=user_prompt,
                temperature=0.7,
                timeout=15.0,
            )
            if not resp.success:
                _llm_last_fail_time = _time.time()
                return None

            content = resp.content.strip()
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)

            parsed = json.loads(content)
            if isinstance(parsed, list) and len(parsed) >= 2:
                return [
                    {
                        "title": s.get("title", ""),
                        "content": s.get("content", ""),
                        "cron_time": s.get("cron_time", "09:00"),
                        "reason": s.get("reason", ""),
                    }
                    for s in parsed[:3]
                    if s.get("title")
                ]

            return None

        except Exception as e:
            logger.warning(f"[coach-ai-suggest] LLM 提醒建议失败: {e}")
            _llm_last_fail_time = _time.time()
            return None
