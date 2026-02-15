"""
V4.0 BPT-6 Four-Dimension Rx Engine — 四维行为处方引擎 (MEU-33)

BPT-6 = Behavior Prescription Template with 6 stages
  Dim 1: TTM Stage (S0-S5)
  Dim 2: Domain (nutrition/exercise/sleep/emotion/stress/cognitive)
  Dim 3: Agency Mode (passive/transitional/active)
  Dim 4: Intensity (gentle/moderate/intensive)

36 variant templates = 6 stages × 6 domains
Each variant adapts delivery based on agency_mode + intensity
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, Dict, List

from sqlalchemy.orm import Session
from sqlalchemy import func

from core.models import User, JourneyState

logger = logging.getLogger(__name__)

# ── 36 Variant Templates (6 stages × 6 domains) ──

DOMAINS = ["nutrition", "exercise", "sleep", "emotion", "stress", "cognitive"]
STAGES = ["s0", "s1", "s2", "s3", "s4", "s5"]

# Stage-Domain prescription matrix
RX_MATRIX = {
    # S0 Authorization — Minimal, observation-only
    ("s0", "nutrition"): {
        "title": "饮食观察日记",
        "actions": ["记录今天吃了什么(不做任何改变)", "注意吃东西时的心情"],
        "duration_days": 7, "intensity": "gentle",
    },
    ("s0", "exercise"): {
        "title": "活动量感知",
        "actions": ["记录今天走了多少步", "注意身体什么时候想动/不想动"],
        "duration_days": 7, "intensity": "gentle",
    },
    ("s0", "sleep"): {
        "title": "睡眠觉察",
        "actions": ["记录入睡和起床时间", "注意睡前在做什么"],
        "duration_days": 7, "intensity": "gentle",
    },
    ("s0", "emotion"): {
        "title": "情绪地图",
        "actions": ["每天记录3次心情(1-10分)", "注意什么事件引起情绪变化"],
        "duration_days": 7, "intensity": "gentle",
    },
    ("s0", "stress"): {
        "title": "压力信号识别",
        "actions": ["注意身体哪里会紧张", "记录压力最大的时刻"],
        "duration_days": 7, "intensity": "gentle",
    },
    ("s0", "cognitive"): {
        "title": "想法记录",
        "actions": ["记录今天最频繁的一个想法", "不评价, 只是看见"],
        "duration_days": 7, "intensity": "gentle",
    },

    # S1 Awareness — Guided observation with gentle prompts
    ("s1", "nutrition"): {
        "title": "饮食模式发现",
        "actions": ["标记哪些食物让你精力充沛", "找到一个你愿意尝试的小改变"],
        "duration_days": 14, "intensity": "gentle",
    },
    ("s1", "exercise"): {
        "title": "运动偏好探索",
        "actions": ["尝试3种不同的运动方式(各5分钟)", "找到让你觉得'还不错'的那一种"],
        "duration_days": 14, "intensity": "gentle",
    },
    ("s1", "sleep"): {
        "title": "睡眠环境优化",
        "actions": ["评估卧室的光线/温度/噪音", "尝试一个简单的改变(如调暗灯光)"],
        "duration_days": 14, "intensity": "gentle",
    },
    ("s1", "emotion"): {
        "title": "情绪命名练习",
        "actions": ["学习5个新的情绪词汇", "用精确的词描述今天的情绪"],
        "duration_days": 14, "intensity": "gentle",
    },
    ("s1", "stress"): {
        "title": "呼吸觉察",
        "actions": ["每天做1次3分钟呼吸练习", "注意呼吸前后身体感觉的变化"],
        "duration_days": 14, "intensity": "gentle",
    },
    ("s1", "cognitive"): {
        "title": "自动思维捕捉",
        "actions": ["识别一个反复出现的自动想法", "问自己'这个想法是事实还是解读?'"],
        "duration_days": 14, "intensity": "gentle",
    },

    # S2 Trial — Active behavior experiments
    ("s2", "nutrition"): {
        "title": "饮食微实验",
        "actions": ["本周每天增加1份蔬菜", "记录身体对这个改变的反应"],
        "duration_days": 14, "intensity": "moderate",
    },
    ("s2", "exercise"): {
        "title": "运动微习惯",
        "actions": ["每天运动10分钟(任何形式)", "固定一个时间段(如早起后)"],
        "duration_days": 14, "intensity": "moderate",
    },
    ("s2", "sleep"): {
        "title": "睡前仪式建立",
        "actions": ["设计一个30分钟睡前仪式", "手机在卧室外充电"],
        "duration_days": 14, "intensity": "moderate",
    },
    ("s2", "emotion"): {
        "title": "情绪回应策略",
        "actions": ["学习STOP技术(Stop-Take breath-Observe-Proceed)", "在情绪波动时使用1次"],
        "duration_days": 14, "intensity": "moderate",
    },
    ("s2", "stress"): {
        "title": "压力管理工具箱",
        "actions": ["建立3种应对压力的方法", "本周至少使用每种1次"],
        "duration_days": 14, "intensity": "moderate",
    },
    ("s2", "cognitive"): {
        "title": "思维重构练习",
        "actions": ["对一个负面想法写出3种替代解读", "评估哪种解读最接近事实"],
        "duration_days": 14, "intensity": "moderate",
    },

    # S3 Pathway — Behavior chain consolidation
    ("s3", "nutrition"): {
        "title": "饮食行为链",
        "actions": ["建立3条稳定的健康饮食习惯链", "记录触发→行为→奖励"],
        "duration_days": 21, "intensity": "moderate",
    },
    ("s3", "exercise"): {
        "title": "运动行为链",
        "actions": ["将运动链接到现有日常习惯", "每周运动≥150分钟"],
        "duration_days": 21, "intensity": "moderate",
    },
    ("s3", "sleep"): {
        "title": "睡眠稳定化",
        "actions": ["固定睡眠-起床时间(±30min)", "建立完整的睡眠卫生清单"],
        "duration_days": 21, "intensity": "moderate",
    },
    ("s3", "emotion"): {
        "title": "情绪调节常态化",
        "actions": ["每天练习正念5分钟", "情绪日记写3次/周"],
        "duration_days": 21, "intensity": "moderate",
    },
    ("s3", "stress"): {
        "title": "压力-恢复平衡",
        "actions": ["识别压力源并制定预案", "每天安排15分钟纯恢复时间"],
        "duration_days": 21, "intensity": "moderate",
    },
    ("s3", "cognitive"): {
        "title": "认知灵活性训练",
        "actions": ["练习'多角度看问题'(每周3次)", "记录认知模式变化"],
        "duration_days": 21, "intensity": "moderate",
    },

    # S4 Internalization — Deep integration
    ("s4", "nutrition"): {
        "title": "直觉饮食探索",
        "actions": ["练习饥饱信号感知", "减少食物规则, 增加内在引导"],
        "duration_days": 30, "intensity": "intensive",
    },
    ("s4", "exercise"): {
        "title": "运动身份融合",
        "actions": ["将运动视为'我是一个爱运动的人'", "探索运动的更深意义"],
        "duration_days": 30, "intensity": "intensive",
    },
    ("s4", "sleep"): {
        "title": "睡眠自信建立",
        "actions": ["信任自己的睡眠能力", "减少对睡眠的过度监控"],
        "duration_days": 30, "intensity": "intensive",
    },
    ("s4", "emotion"): {
        "title": "情绪智慧深化",
        "actions": ["探索情绪与价值观的连接", "练习接纳所有情绪(包括'负面'的)"],
        "duration_days": 30, "intensity": "intensive",
    },
    ("s4", "stress"): {
        "title": "压力转化艺术",
        "actions": ["将适度压力重框为成长信号", "建立抗逆力叙事"],
        "duration_days": 30, "intensity": "intensive",
    },
    ("s4", "cognitive"): {
        "title": "核心信念工作",
        "actions": ["识别并检视1-2个核心信念", "建立更灵活的替代信念"],
        "duration_days": 30, "intensity": "intensive",
    },

    # S5 Graduation — Maintenance & giving back
    ("s5", "nutrition"): {
        "title": "饮食智慧传承",
        "actions": ["总结个人饮食智慧3条", "分享给1位同伴"],
        "duration_days": 30, "intensity": "gentle",
    },
    ("s5", "exercise"): {
        "title": "运动生活方式",
        "actions": ["运动已成为生活的一部分", "带领1位朋友一起运动"],
        "duration_days": 30, "intensity": "gentle",
    },
    ("s5", "sleep"): {
        "title": "睡眠自主管理",
        "actions": ["信任自己的睡眠系统", "偶尔的失眠不再焦虑"],
        "duration_days": 30, "intensity": "gentle",
    },
    ("s5", "emotion"): {
        "title": "情绪智慧分享",
        "actions": ["分享情绪管理经验", "成为他人的情绪支持者"],
        "duration_days": 30, "intensity": "gentle",
    },
    ("s5", "stress"): {
        "title": "抗逆力导师",
        "actions": ["分享压力管理故事", "帮助他人建立应对策略"],
        "duration_days": 30, "intensity": "gentle",
    },
    ("s5", "cognitive"): {
        "title": "思维自由",
        "actions": ["灵活的思维已成为习惯", "帮助他人看到不同视角"],
        "duration_days": 30, "intensity": "gentle",
    },
}

# Agency mode adaptation
AGENCY_ADAPTATION = {
    "passive": {
        "delivery": "push",
        "reminder_frequency": "daily",
        "check_in": True,
        "choice_presented": False,
        "tone": "我来帮你完成这个步骤",
    },
    "transitional": {
        "delivery": "suggest",
        "reminder_frequency": "every_other_day",
        "check_in": False,
        "choice_presented": True,
        "tone": "你想今天尝试哪个?",
    },
    "active": {
        "delivery": "available",
        "reminder_frequency": "none",
        "check_in": False,
        "choice_presented": True,
        "tone": "如果你需要, 这些资源在这里",
    },
}


class BPT6RxEngine:
    """BPT-6 四维行为处方引擎"""

    def __init__(self, db: Session):
        self.db = db

    def generate_rx(
        self,
        user_id: int,
        domain: str = None,
        override_stage: str = None,
    ) -> dict:
        """生成个性化行为处方"""
        journey = self.db.query(JourneyState).filter(
            JourneyState.user_id == user_id
        ).first()

        stage_full = override_stage or (journey.journey_stage if journey else "s0_authorization")
        stage = stage_full.split("_")[0]  # s0, s1, etc.
        agency_mode = journey.agency_mode if journey else "passive"

        if domain:
            domains_to_prescribe = [domain] if domain in DOMAINS else DOMAINS
        else:
            domains_to_prescribe = DOMAINS

        prescriptions = []
        for d in domains_to_prescribe:
            key = (stage, d)
            template = RX_MATRIX.get(key)
            if template:
                adaptation = AGENCY_ADAPTATION.get(agency_mode, AGENCY_ADAPTATION["passive"])
                prescriptions.append({
                    "domain": d,
                    "stage": stage,
                    "title": template["title"],
                    "actions": template["actions"],
                    "duration_days": template["duration_days"],
                    "intensity": template["intensity"],
                    "agency_adaptation": adaptation,
                })

        return {
            "user_id": user_id,
            "stage": stage_full,
            "agency_mode": agency_mode,
            "prescriptions": prescriptions,
            "total_variants": len(prescriptions),
        }

    def get_rx_catalog(self) -> dict:
        """获取完整处方目录"""
        catalog = {}
        for (stage, domain), template in RX_MATRIX.items():
            if stage not in catalog:
                catalog[stage] = {}
            catalog[stage][domain] = {
                "title": template["title"],
                "actions": template["actions"],
                "intensity": template["intensity"],
                "duration_days": template["duration_days"],
            }
        return {
            "stages": STAGES,
            "domains": DOMAINS,
            "total_variants": len(RX_MATRIX),
            "catalog": catalog,
        }

    def get_adaptation_rules(self) -> dict:
        """获取agency适配规则"""
        return AGENCY_ADAPTATION
