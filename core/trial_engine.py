"""
体验版评估 + AI试用引擎
契约来源: Sheet③ 访客与入口契约 + Sheet⑤ 服务权益契约 + Sheet⑩ P1

两大体验功能:
  1. 体验版HF-20快筛 (限1次) — 注册观察员可用
  2. AI体验对话 (限3轮)   — 注册观察员可用

转化路径:
  评估结果 → "成为成长者获取完整服务" 引导
  AI对话达限 → "注册/升级解锁完整对话" 引导

内容等级门控 (v3.7.1):
  L0-L5 分级可见性, 不可访问内容显示解锁提示

访问层级 (Sheet③ §A):
  - 免注册游客: T1公开科普+浏览, 无AI/评估
  - 注册观察员: 上述+体验评估(1次)+AI对话(3轮)+案例收藏
  - 成长者+: 完整功能

集成:
  - Week1 Task1 观察员分层 (Observer tiers)
  - Week2 防刷策略 (AS-01 日限)
  - RBAC 权限系统
"""

from __future__ import annotations
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field


# ══════════════════════════════════════════
# 0. 访问层级与数据结构
# ══════════════════════════════════════════

class AccessTier(str, Enum):
    ANONYMOUS = "anonymous"           # 免注册游客
    REGISTERED_OBSERVER = "registered_observer"  # 注册观察员
    GROWER = "grower"                 # 成长者 (L1)
    SHARER = "sharer"                 # 分享者 (L2)
    COACH = "coach"                   # 教练 (L3)
    PROMOTER = "promoter"             # 促进师 (L4)
    MASTER = "master"                 # 大师 (L5)
    ADMIN = "admin"                   # 管理员


TIER_LEVEL_MAP = {
    AccessTier.ANONYMOUS: 0,
    AccessTier.REGISTERED_OBSERVER: 0,
    AccessTier.GROWER: 1,
    AccessTier.SHARER: 2,
    AccessTier.COACH: 3,
    AccessTier.PROMOTER: 4,
    AccessTier.MASTER: 5,
    AccessTier.ADMIN: 6,
}


class TrialStatus(str, Enum):
    AVAILABLE = "available"
    USED = "used"
    LIMIT_REACHED = "limit_reached"
    NOT_ELIGIBLE = "not_eligible"


@dataclass
class TrialUsageRecord:
    user_id: int
    feature: str                  # "hf20_assessment" | "ai_dialog"
    used_count: int = 0
    max_allowed: int = 0
    first_used_at: str = ""
    last_used_at: str = ""
    conversion_shown: bool = False


@dataclass
class ConversionHook:
    """转化钩子配置"""
    trigger: str
    message_zh: str
    cta_text: str
    cta_action: str
    priority: int = 0


# ══════════════════════════════════════════
# 1. 体验版评估引擎 (HF-20 快筛)
# ══════════════════════════════════════════

class TrialAssessmentEngine:
    """
    体验版HF-20快筛引擎。

    规则 (Sheet③+⑤):
      - 仅注册观察员可用
      - 限1次
      - 完成后展示简化结果 + 转化引导
      - 完整评估需成为成长者

    HF-20: 20题健康行为快速筛查
      - 5维度: 饮食(4题)+运动(4题)+睡眠(4题)+压力(4题)+习惯(4题)
      - 评分: 0-100分 (每题0-5分)
      - 结果分级: 优(≥80) / 良(60-79) / 需关注(40-59) / 建议评估(<40)
    """

    MAX_TRIAL_ASSESSMENTS = 1
    TOTAL_QUESTIONS = 20
    MAX_SCORE = 100

    HF20_DIMENSIONS = [
        {"id": "diet", "name": "饮食行为", "question_count": 4, "max_score": 20},
        {"id": "exercise", "name": "运动习惯", "question_count": 4, "max_score": 20},
        {"id": "sleep", "name": "睡眠质量", "question_count": 4, "max_score": 20},
        {"id": "stress", "name": "压力管理", "question_count": 4, "max_score": 20},
        {"id": "habit", "name": "健康习惯", "question_count": 4, "max_score": 20},
    ]

    RESULT_TIERS = [
        (80, "excellent", "优秀", "您的健康行为习惯非常好!继续保持,并探索更深层的成长路径。"),
        (60, "good", "良好", "您有不错的健康基础!了解自己的行为模式,可以帮助您更进一步。"),
        (40, "attention", "需关注", "部分领域需要关注。系统化的行为改变方案可以帮助您建立更健康的习惯。"),
        (0, "suggest_full", "建议完整评估", "建议进行完整评估,获取个性化的行为改变方案。"),
    ]

    CONVERSION_HOOKS = [
        ConversionHook(
            trigger="assessment_complete",
            message_zh="您的快筛结果已生成!成为成长者可获取完整评估报告和个性化行为改变方案。",
            cta_text="成为成长者,获取完整服务",
            cta_action="upgrade_to_grower",
            priority=10,
        ),
        ConversionHook(
            trigger="assessment_suggest_full",
            message_zh="快筛发现需要关注的领域。完整评估(COM-B/TTM)可深入分析您的行为模式。",
            cta_text="立即开始完整评估",
            cta_action="upgrade_to_grower",
            priority=20,
        ),
    ]

    def __init__(self):
        self._usage: Dict[int, TrialUsageRecord] = {}

    def check_eligibility(self, user_id: int, access_tier: AccessTier) -> Dict[str, Any]:
        """检查用户是否有资格使用体验版评估"""
        if access_tier == AccessTier.ANONYMOUS:
            return {
                "status": TrialStatus.NOT_ELIGIBLE.value,
                "reason": "需要注册才能使用体验版评估",
                "action": "register",
                "cta": "注册解锁体验版评估",
            }

        # 成长者+已有完整评估权限
        if TIER_LEVEL_MAP.get(access_tier, 0) >= 1:
            return {
                "status": "full_access",
                "reason": "您已拥有完整评估权限",
                "action": "full_assessment",
            }

        # 注册观察员: 检查使用次数
        record = self._usage.get(user_id)
        if record and record.used_count >= self.MAX_TRIAL_ASSESSMENTS:
            return {
                "status": TrialStatus.USED.value,
                "reason": "体验版评估已使用 (限1次)",
                "action": "upgrade",
                "cta": "成为成长者获取完整评估",
                "first_used_at": record.first_used_at,
            }

        return {
            "status": TrialStatus.AVAILABLE.value,
            "reason": "可以开始体验版评估 (HF-20快筛)",
            "action": "start_trial",
            "questions_count": self.TOTAL_QUESTIONS,
            "estimated_minutes": 5,
        }

    async def start_assessment(self, user_id: int, access_tier: AccessTier) -> Dict[str, Any]:
        """开始体验版评估"""
        eligibility = self.check_eligibility(user_id, access_tier)
        if eligibility["status"] not in (TrialStatus.AVAILABLE.value,):
            return {"error": True, **eligibility}

        # 生成题目 (简化: 返回题目结构)
        questions = self._generate_hf20_questions()
        return {
            "assessment_id": f"trial-hf20-{user_id}-{int(datetime.now(timezone.utc).timestamp())}",
            "type": "hf20_trial",
            "dimensions": self.HF20_DIMENSIONS,
            "questions": questions,
            "total_questions": self.TOTAL_QUESTIONS,
            "instructions": "请根据您最近30天的实际情况作答,每题1-5分。",
        }

    async def submit_assessment(
        self, user_id: int, assessment_id: str, answers: Dict[str, int]
    ) -> Dict[str, Any]:
        """提交评估并生成结果"""
        # 计算分数
        total_score = sum(answers.values())
        dimension_scores = {}
        for dim in self.HF20_DIMENSIONS:
            dim_questions = [
                k for k in answers if k.startswith(dim["id"])
            ]
            dim_score = sum(answers[q] for q in dim_questions)
            dimension_scores[dim["id"]] = {
                "name": dim["name"],
                "score": dim_score,
                "max_score": dim["max_score"],
                "percent": round(dim_score / dim["max_score"] * 100, 1),
            }

        # 分级
        tier_id, tier_name, tier_label, tier_message = "suggest_full", "建议评估", "建议完整评估", ""
        for threshold, tid, tname, tmsg in self.RESULT_TIERS:
            if total_score >= threshold:
                tier_id, tier_name, tier_label, tier_message = tid, tname, tname, tmsg
                break

        # 记录使用
        now = datetime.now(timezone.utc).isoformat()
        record = self._usage.get(user_id)
        if record:
            record.used_count += 1
            record.last_used_at = now
        else:
            self._usage[user_id] = TrialUsageRecord(
                user_id=user_id, feature="hf20_assessment",
                used_count=1, max_allowed=self.MAX_TRIAL_ASSESSMENTS,
                first_used_at=now, last_used_at=now,
            )

        # 转化钩子
        hook = self.CONVERSION_HOOKS[1] if tier_id == "suggest_full" else self.CONVERSION_HOOKS[0]

        return {
            "assessment_id": assessment_id,
            "total_score": total_score,
            "max_score": self.MAX_SCORE,
            "percent": round(total_score / self.MAX_SCORE * 100, 1),
            "tier": {"id": tier_id, "name": tier_name, "message": tier_message},
            "dimensions": dimension_scores,
            # 体验版: 简化结果 (完整报告需升级)
            "trial_limited": True,
            "locked_features": [
                "完整COM-B行为分析",
                "TTM阶段评估",
                "个性化行为改变方案",
                "教练匹配推荐",
                "AI深度对话",
            ],
            # 转化引导
            "conversion_hook": {
                "message": hook.message_zh,
                "cta_text": hook.cta_text,
                "cta_action": hook.cta_action,
            },
            "remaining_trials": 0,
        }

    def _generate_hf20_questions(self) -> List[Dict]:
        """生成HF-20题目结构"""
        questions = []
        q_templates = {
            "diet": [
                "您每天是否规律进食三餐?",
                "您每天摄入蔬果是否达到推荐量?",
                "您是否注意控制加工食品的摄入?",
                "您是否有意识地控制饮食中的糖分摄入?",
            ],
            "exercise": [
                "您每周是否进行中等强度运动至少150分钟?",
                "您是否有规律的运动计划?",
                "您日常是否有步行或其他身体活动习惯?",
                "您是否避免长时间久坐不动?",
            ],
            "sleep": [
                "您通常是否能在30分钟内入睡?",
                "您每晚睡眠时长是否达到7-8小时?",
                "您的作息时间是否规律?",
                "您起床后是否感觉精神饱满?",
            ],
            "stress": [
                "您是否有有效的压力应对方式?",
                "您是否能在压力下保持良好情绪?",
                "您是否有定期放松或冥想的习惯?",
                "您是否感觉能够控制日常压力水平?",
            ],
            "habit": [
                "您是否有定期健康体检的习惯?",
                "您是否能够坚持已建立的健康习惯?",
                "您是否主动获取健康知识?",
                "您的社交关系是否积极健康?",
            ],
        }
        idx = 0
        for dim_id, dim_qs in q_templates.items():
            for i, q_text in enumerate(dim_qs):
                idx += 1
                questions.append({
                    "id": f"{dim_id}_{i+1}",
                    "dimension": dim_id,
                    "index": idx,
                    "text": q_text,
                    "scale": {"min": 1, "max": 5},
                    "labels": {1: "完全不是", 2: "较少", 3: "有时", 4: "经常", 5: "总是"},
                })
        return questions


# ══════════════════════════════════════════
# 2. AI 体验对话引擎 (限3轮)
# ══════════════════════════════════════════

class TrialAIDialogEngine:
    """
    AI体验对话引擎。

    规则 (Sheet③+⑤):
      - 注册观察员: 限3轮对话
      - 免注册游客: 不可用
      - 成长者+: 12个专业Agent完整对话

    3轮对话策略:
      第1轮: 健康关注点探索 (开放式)
      第2轮: 初步行为分析 (引导式)
      第3轮: 价值展示 + 转化引导 (限制到达)
    """

    MAX_TRIAL_ROUNDS = 3

    CONVERSION_HOOKS = [
        ConversionHook(
            trigger="dialog_limit_reached",
            message_zh="您已体验了AI健康对话的核心能力!成为成长者可解锁12个专业Agent的完整对话服务。",
            cta_text="升级为成长者,解锁完整AI服务",
            cta_action="upgrade_to_grower",
            priority=15,
        ),
        ConversionHook(
            trigger="dialog_round_2",
            message_zh="AI正在为您分析行为模式...完整分析报告需成为成长者后获取。",
            cta_text="了解更多",
            cta_action="show_grower_benefits",
            priority=5,
        ),
    ]

    def __init__(self):
        self._sessions: Dict[int, Dict] = {}

    def check_eligibility(self, user_id: int, access_tier: AccessTier) -> Dict[str, Any]:
        """检查AI对话体验资格"""
        if access_tier == AccessTier.ANONYMOUS:
            return {
                "status": TrialStatus.NOT_ELIGIBLE.value,
                "reason": "注册后即可体验AI健康对话",
                "action": "register",
            }

        if TIER_LEVEL_MAP.get(access_tier, 0) >= 1:
            return {
                "status": "full_access",
                "reason": "您已拥有完整AI对话权限",
                "available_agents": 12,
            }

        session = self._sessions.get(user_id)
        if session and session["rounds_used"] >= self.MAX_TRIAL_ROUNDS:
            return {
                "status": TrialStatus.LIMIT_REACHED.value,
                "reason": f"体验对话已达上限 ({self.MAX_TRIAL_ROUNDS}轮)",
                "action": "upgrade",
                "conversion_hook": {
                    "message": self.CONVERSION_HOOKS[0].message_zh,
                    "cta_text": self.CONVERSION_HOOKS[0].cta_text,
                },
            }

        remaining = self.MAX_TRIAL_ROUNDS - (session["rounds_used"] if session else 0)
        return {
            "status": TrialStatus.AVAILABLE.value,
            "rounds_remaining": remaining,
            "max_rounds": self.MAX_TRIAL_ROUNDS,
        }

    async def send_message(
        self, user_id: int, access_tier: AccessTier, message: str
    ) -> Dict[str, Any]:
        """发送体验对话消息"""
        eligibility = self.check_eligibility(user_id, access_tier)
        if eligibility["status"] not in (TrialStatus.AVAILABLE.value,):
            return {"error": True, **eligibility}

        # 获取/创建会话
        if user_id not in self._sessions:
            self._sessions[user_id] = {
                "rounds_used": 0,
                "messages": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

        session = self._sessions[user_id]
        current_round = session["rounds_used"] + 1

        # 记录用户消息
        session["messages"].append({"role": "user", "content": message, "round": current_round})

        # 生成AI回复 (按轮次策略)
        ai_response = self._generate_trial_response(current_round, message, session)

        session["messages"].append({"role": "assistant", "content": ai_response["text"], "round": current_round})
        session["rounds_used"] = current_round

        remaining = self.MAX_TRIAL_ROUNDS - current_round
        result = {
            "round": current_round,
            "max_rounds": self.MAX_TRIAL_ROUNDS,
            "remaining": remaining,
            "response": ai_response["text"],
            "response_type": ai_response["type"],
        }

        # 转化钩子
        if current_round == 2:
            result["conversion_hint"] = {
                "message": self.CONVERSION_HOOKS[1].message_zh,
                "cta_text": self.CONVERSION_HOOKS[1].cta_text,
                "subtle": True,
            }
        elif current_round >= self.MAX_TRIAL_ROUNDS:
            result["trial_ended"] = True
            result["conversion_hook"] = {
                "message": self.CONVERSION_HOOKS[0].message_zh,
                "cta_text": self.CONVERSION_HOOKS[0].cta_text,
                "cta_action": self.CONVERSION_HOOKS[0].cta_action,
            }
            result["locked_features"] = [
                "12个专业健康Agent",
                "行为处方AI",
                "危机干预Agent",
                "食物识别AI",
                "持续对话记录",
            ]

        return result

    def _generate_trial_response(self, round_num: int, message: str, session: Dict) -> Dict:
        """按轮次策略生成回复"""
        if round_num == 1:
            return {
                "type": "exploration",
                "text": (
                    "您好!很高兴为您提供健康行为咨询体验。"
                    f"关于您提到的「{message[:20]}...」，这是一个很好的关注方向。"
                    "能否告诉我,您在这方面目前的日常习惯是怎样的?我来帮您初步分析一下行为模式。"
                ),
            }
        elif round_num == 2:
            return {
                "type": "analysis",
                "text": (
                    "根据您的描述,我注意到几个关键的行为模式。"
                    "您的情况涉及行为改变的多个维度,包括认知、动机和环境因素。"
                    "完整的COM-B行为分析可以帮助您系统性地了解行为改变的切入点。"
                    "这是最后一轮体验对话,您还有什么想了解的吗?"
                ),
            }
        else:
            return {
                "type": "value_demo",
                "text": (
                    "感谢您的体验!基于我们的对话,我已经初步识别了您的行为模式。"
                    "完整的AI健康服务包括:个性化行为分析、专业Agent持续陪伴、"
                    "行为处方定制、以及教练协作支持。成为成长者即可解锁全部服务。"
                ),
            }


# ══════════════════════════════════════════
# 3. 内容等级门控 (v3.7.1)
# ══════════════════════════════════════════

class ContentGatingEngine:
    """
    内容等级门控 (Sheet⑤ 内容等级门控表)。

    L0-L5 内容分级:
      不可访问时: 标题+封面+统计可见, body+video_url隐藏
      返回: access_status{accessible, reason, unlock_level}
    """

    CONTENT_LEVELS = {
        0: {"name": "L0公开内容", "description": "健康常识·平台介绍"},
        1: {"name": "L1基础内容", "description": "基础健康知识·入门课程"},
        2: {"name": "L2进阶内容", "description": "进阶课程·案例分享"},
        3: {"name": "L3专业内容", "description": "专业教练培训课程"},
        4: {"name": "L4高阶内容", "description": "高阶管理·督导培训"},
        5: {"name": "L5大师内容", "description": "所有内容·无限制"},
    }

    UNLOCK_MESSAGES = {
        1: "完成L1成长者认证即可解锁更多内容",
        2: "升级为L2分享者解锁进阶内容",
        3: "成为L3教练解锁专业内容",
        4: "晋升促进师解锁高阶内容",
        5: "成为大师解锁全部内容",
    }

    def check_content_access(
        self, user_level: int, content_level: int, content_item: Dict
    ) -> Dict[str, Any]:
        """检查内容访问权限"""
        accessible = user_level >= content_level

        if accessible:
            return {
                "accessible": True,
                "content": content_item,  # 完整内容
            }

        # 不可访问: 隐藏body+video_url
        gated_content = {
            k: v for k, v in content_item.items()
            if k not in ("body", "video_url", "full_text", "attachments")
        }

        return {
            "accessible": False,
            "content": gated_content,
            "access_status": {
                "reason": f"需要{self.CONTENT_LEVELS.get(content_level, {}).get('name', '')}权限",
                "unlock_level": content_level,
                "unlock_message": self.UNLOCK_MESSAGES.get(content_level, "升级解锁"),
                "current_level": user_level,
            },
        }

    def filter_content_list(
        self, user_level: int, content_items: List[Dict]
    ) -> List[Dict]:
        """批量过滤内容列表"""
        results = []
        for item in content_items:
            content_level = item.get("level", 0)
            result = self.check_content_access(user_level, content_level, item)
            results.append(result)
        return results


# ══════════════════════════════════════════
# 4. 功能权限矩阵 (Sheet⑤ 全量)
# ══════════════════════════════════════════

FEATURE_ACCESS_MATRIX: Dict[str, Dict[str, Any]] = {
    # 浏览
    "t1_public_content": {"anonymous": True, "registered": True, "grower": True},
    "expert_hub_browse": {"anonymous": True, "registered": True, "grower": True},
    "knowledge_search": {"anonymous": False, "registered": True, "grower": True},
    "deep_case_detail": {"anonymous": False, "registered": True, "grower": True},
    # 学习
    "t2_health_content": {"anonymous": False, "registered": False, "grower": True},
    "t3_growth_content": {"anonymous": False, "registered": False, "grower": False, "sharer": True},
    "t4_professional_content": {"anonymous": False, "registered": False, "grower": False, "sharer": False, "promoter": True},
    "course_learning": {"anonymous": False, "registered": False, "grower": True},
    # 评估
    "trial_hf20": {"anonymous": False, "registered": True, "grower": True},
    "full_assessment": {"anonymous": False, "registered": False, "grower": True},
    "assessment_assign": {"anonymous": False, "registered": False, "grower": False, "coach": True},
    # AI
    "ai_trial_dialog": {"anonymous": False, "registered": True, "grower": True},
    "ai_full_agents": {"anonymous": False, "registered": False, "grower": True},
    "ai_crisis_agent": {"anonymous": False, "registered": False, "grower": True},
    "ai_food_recognition": {"anonymous": False, "registered": False, "grower": True},
    "ai_expert_agents": {"anonymous": False, "registered": False, "grower": False, "coach": True},
    "ai_custom_agent": {"anonymous": False, "registered": False, "grower": False, "promoter": True},
    "ai_agent_market": {"anonymous": False, "registered": False, "grower": False, "promoter": True},
    "ai_multi_agent": {"anonymous": False, "registered": False, "grower": False, "master": True},
    # 健康数据
    "health_data_entry": {"anonymous": False, "registered": False, "grower": True},
    "health_dashboard": {"anonymous": False, "registered": False, "grower": True},
    # 行为养成
    "micro_action": {"anonymous": False, "registered": False, "grower": True},
    "challenge_join": {"anonymous": False, "registered": False, "grower": True},
    "behavior_rx_create": {"anonymous": False, "registered": False, "grower": False, "coach": True},
    # 社交
    "peer_invite": {"anonymous": False, "registered": False, "grower": True},
    "promotion_apply": {"anonymous": False, "registered": False, "grower": True},
    # 教练
    "coach_workbench": {"anonymous": False, "registered": False, "grower": False, "coach": True},
    # 专家
    "expert_studio": {"anonymous": False, "registered": False, "grower": False, "promoter": True},
    "supervision_center": {"anonymous": False, "registered": False, "grower": False, "promoter": True},
}


def check_feature_access(feature: str, access_tier: AccessTier) -> bool:
    """检查功能访问权限"""
    matrix = FEATURE_ACCESS_MATRIX.get(feature)
    if not matrix:
        return False

    tier_key_map = {
        AccessTier.ANONYMOUS: "anonymous",
        AccessTier.REGISTERED_OBSERVER: "registered",
        AccessTier.GROWER: "grower",
        AccessTier.SHARER: "sharer",
        AccessTier.COACH: "coach",
        AccessTier.PROMOTER: "promoter",
        AccessTier.MASTER: "master",
        AccessTier.ADMIN: "grower",
    }

    tier_key = tier_key_map.get(access_tier, "anonymous")

    # 检查当前层级及以上
    tier_order = ["anonymous", "registered", "grower", "sharer", "coach", "promoter", "master"]
    try:
        user_idx = tier_order.index(tier_key)
    except ValueError:
        return False

    for level in tier_order[:user_idx + 1]:
        if matrix.get(level, False):
            return True
    # 也检查精确匹配
    return matrix.get(tier_key, False)


# ══════════════════════════════════════════
# 5. API 端点
# ══════════════════════════════════════════

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/v1/trial", tags=["trial"])


class TrialAssessmentSubmit(BaseModel):
    assessment_id: str
    answers: Dict[str, int]


class TrialDialogMessage(BaseModel):
    message: str


@router.get("/assessment/eligibility")
async def check_assessment_eligibility(user_id: int, access_tier: str = "registered_observer"):
    engine = TrialAssessmentEngine()
    tier = AccessTier(access_tier)
    return engine.check_eligibility(user_id, tier)


@router.post("/assessment/start")
async def start_trial_assessment(user_id: int, access_tier: str = "registered_observer"):
    engine = TrialAssessmentEngine()
    return await engine.start_assessment(user_id, AccessTier(access_tier))


@router.post("/assessment/submit")
async def submit_trial_assessment(user_id: int, req: TrialAssessmentSubmit):
    engine = TrialAssessmentEngine()
    return await engine.submit_assessment(user_id, req.assessment_id, req.answers)


@router.get("/ai-dialog/eligibility")
async def check_ai_dialog_eligibility(user_id: int, access_tier: str = "registered_observer"):
    engine = TrialAIDialogEngine()
    return engine.check_eligibility(user_id, AccessTier(access_tier))


@router.post("/ai-dialog/message")
async def send_trial_ai_message(user_id: int, req: TrialDialogMessage, access_tier: str = "registered_observer"):
    engine = TrialAIDialogEngine()
    return await engine.send_message(user_id, AccessTier(access_tier), req.message)


@router.get("/content/access")
async def check_content_access(user_level: int, content_level: int):
    engine = ContentGatingEngine()
    sample_content = {"id": "demo", "title": "示例内容", "body": "完整内容", "level": content_level}
    return engine.check_content_access(user_level, content_level, sample_content)


@router.get("/feature/access")
async def check_feature(feature: str, access_tier: str):
    allowed = check_feature_access(feature, AccessTier(access_tier))
    return {"feature": feature, "access_tier": access_tier, "allowed": allowed}
