#!/usr/bin/env python3
"""
BHP v3 — 180天全流程模拟数据生成器
====================================

模拟规模:
  - 180 天运营 (2025-08-15 → 2026-02-10)
  - 1,200 注册用户 (前60天密集注册)
  - 日均 300 活跃人次
  - 覆盖: 注册→诊断→评估→对话→打卡→追踪→积分→阶段转变→专家审核

生成表 (20张):
  users, change_causes, user_change_cause_scores, intervention_strategies,
  health_competency_assessments, comb_assessments, self_efficacy_assessments,
  obstacle_assessments, support_assessments, intervention_outcomes,
  stage_transition_logs, point_events, user_point_balances, incentive_rewards,
  user_rewards, assessment_sessions, batch_answers, llm_call_logs,
  rag_query_logs, knowledge_chunks

用法:
  # SQLite (本地测试)
  python scripts/generate_sim_data.py

  # PostgreSQL (生产)
  DATABASE_URL=postgresql://bhp:xxx@localhost:5432/bhp python scripts/generate_sim_data.py

  # 自定义参数
  python scripts/generate_sim_data.py --users 500 --days 90 --dau 150
"""

import os
import sys
import json
import random
import hashlib
import math
import uuid
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

# ── 路径 ──
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:difyai123456@localhost:5432/health_platform")

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker


# ══════════════════════════════════════════════
# 配置
# ══════════════════════════════════════════════

@dataclass
class SimConfig:
    start_date: datetime = datetime(2025, 8, 15, tzinfo=timezone.utc)
    total_days: int = 180
    total_users: int = 1200
    target_dau: int = 300
    seed: int = 42

    # 用户画像分布 (5类)
    ARCHETYPES = {
        "motivated":   0.20,  # 高动机: 坚持打卡, 快速进阶
        "steady":      0.30,  # 稳定型: 按节奏推进, 偶尔缺勤
        "struggling":  0.25,  # 挣扎型: 时做时停, 阶段反复
        "explorer":    0.15,  # 探索型: 评估/对话多, 执行少
        "dropout":     0.10,  # 流失型: 注册后逐渐不活跃
    }

    # 慢性病种分布
    CONDITIONS = [
        ("metabolic_syndrome", 0.30),  # 代谢综合征
        ("type2_diabetes",     0.25),  # 2型糖尿病
        ("hypertension",       0.20),  # 高血压
        ("dyslipidemia",       0.15),  # 血脂异常
        ("obesity",            0.10),  # 肥胖
    ]

    # 年龄分布 (40-75 为主)
    AGE_DIST = [(35, 45, 0.15), (45, 55, 0.30), (55, 65, 0.35), (65, 78, 0.20)]

    # 中国城市分布
    CITIES = [
        "北京", "上海", "广州", "深圳", "杭州", "南京", "成都", "武汉",
        "重庆", "西安", "长沙", "郑州", "济南", "沈阳", "青岛", "大连",
        "苏州", "厦门", "昆明", "合肥", "福州", "南昌", "贵阳", "兰州",
    ]

    # 姓氏 + 名字素材
    SURNAMES = "王李张刘陈杨赵黄周吴徐孙胡朱高林何郭马罗梁宋郑谢韩唐冯于董萧程曹袁邓许"
    GIVEN_NAMES = [
        "伟", "芳", "秀英", "敏", "静", "丽", "强", "磊", "洋", "艳",
        "勇", "军", "杰", "娟", "涛", "明", "超", "秀兰", "霞", "平",
        "刚", "桂英", "华", "玉兰", "萍", "红", "玉", "凤", "辉", "建华",
        "建国", "建军", "文", "志强", "永", "春", "雪", "慧", "婷", "浩",
    ]


CFG = SimConfig()


# ══════════════════════════════════════════════
# 随机工具
# ══════════════════════════════════════════════

class RNG:
    """可复现的随机数生成器"""
    def __init__(self, seed):
        self.r = random.Random(seed)

    def choice(self, seq):
        return self.r.choice(seq)

    def choices(self, seq, weights=None, k=1):
        return self.r.choices(seq, weights=weights, k=k)

    def randint(self, a, b):
        return self.r.randint(a, b)

    def uniform(self, a, b):
        return self.r.uniform(a, b)

    def gauss(self, mu, sigma):
        return self.r.gauss(mu, sigma)

    def shuffle(self, x):
        self.r.shuffle(x)

    def random(self):
        return self.r.random()

    def weighted_choice(self, items_weights):
        items = [i for i, _ in items_weights]
        weights = [w for _, w in items_weights]
        return self.choices(items, weights=weights, k=1)[0]

    def phone(self):
        prefixes = ["130","131","132","133","134","135","136","137","138","139",
                     "150","151","152","153","155","156","157","158","159",
                     "170","171","172","173","175","176","177","178",
                     "180","181","182","183","184","185","186","187","188","189"]
        return self.choice(prefixes) + "".join([str(self.randint(0,9)) for _ in range(8)])

    def chinese_name(self):
        s = self.choice(CFG.SURNAMES)
        g = self.choice(CFG.GIVEN_NAMES)
        return s + g


rng = RNG(CFG.seed)


# ══════════════════════════════════════════════
# 用户画像
# ══════════════════════════════════════════════

STAGES = ["S0", "S1", "S2", "S3", "S4", "S5", "S6"]
GROWTH_LEVELS = ["G0", "G1", "G2", "G3", "G4"]
READINESS = ["L1", "L2", "L3", "L4", "L5"]
CULTIVATION = ["startup", "adaptation", "stability", "internalization"]

# 各画像的行为参数
ARCHETYPE_PARAMS = {
    "motivated": {
        "daily_active_prob": 0.85,   # 每天活跃概率
        "checkin_prob":      0.90,   # 打卡概率
        "chat_prob":         0.40,   # 发起对话概率
        "assessment_speed":  1.5,    # 评估完成速度倍率
        "completion_rate":   (0.75, 0.95),  # 任务完成率范围
        "stage_advance_rate": 0.015,  # 每天进阶概率
        "dropout_prob":      0.001,  # 每天流失概率
        "init_stage_dist":   [(0,0.05),(1,0.15),(2,0.40),(3,0.30),(4,0.10)],
    },
    "steady": {
        "daily_active_prob": 0.65,
        "checkin_prob":      0.70,
        "chat_prob":         0.25,
        "assessment_speed":  1.0,
        "completion_rate":   (0.50, 0.80),
        "stage_advance_rate": 0.008,
        "dropout_prob":      0.003,
        "init_stage_dist":   [(0,0.10),(1,0.25),(2,0.35),(3,0.25),(4,0.05)],
    },
    "struggling": {
        "daily_active_prob": 0.40,
        "checkin_prob":      0.45,
        "chat_prob":         0.35,
        "assessment_speed":  0.7,
        "completion_rate":   (0.20, 0.55),
        "stage_advance_rate": 0.004,
        "dropout_prob":      0.008,
        "init_stage_dist":   [(0,0.25),(1,0.35),(2,0.25),(3,0.10),(4,0.05)],
    },
    "explorer": {
        "daily_active_prob": 0.55,
        "checkin_prob":      0.30,
        "chat_prob":         0.65,
        "assessment_speed":  1.2,
        "completion_rate":   (0.30, 0.60),
        "stage_advance_rate": 0.005,
        "dropout_prob":      0.005,
        "init_stage_dist":   [(0,0.15),(1,0.30),(2,0.30),(3,0.20),(4,0.05)],
    },
    "dropout": {
        "daily_active_prob": 0.25,
        "checkin_prob":      0.20,
        "chat_prob":         0.15,
        "assessment_speed":  0.5,
        "completion_rate":   (0.10, 0.35),
        "stage_advance_rate": 0.001,
        "dropout_prob":      0.025,
        "init_stage_dist":   [(0,0.40),(1,0.30),(2,0.20),(3,0.08),(4,0.02)],
    },
}


@dataclass
class SimUser:
    """模拟用户状态机"""
    id: int
    phone: str
    nickname: str
    password_hash: str
    role: str
    archetype: str
    condition: str
    city: str
    age: int
    gender: str
    register_day: int  # 注册在第几天

    # 动态状态
    current_stage: int = 0        # S0-S6 的数字
    growth_level: int = 0         # G0-G4
    readiness: int = 1            # L1-L5
    cultivation: int = 0          # 培养阶段 index
    spi_score: float = 30.0       # 成功可能性指数
    health_competency: str = "Lv0"
    is_active: bool = True
    dropped_out: bool = False

    # 积分
    growth_points: int = 0
    contribution_points: int = 0
    influence_points: int = 0
    streak_days: int = 0
    longest_streak: int = 0
    tasks_completed_total: int = 0
    assessments_completed: int = 0
    last_checkin_day: int = -999

    # 评估进度
    completed_batches: list = field(default_factory=list)
    assessment_session_id: Optional[int] = None
    diagnostic_done: bool = False
    full_diagnostic_done: bool = False

    @property
    def params(self):
        return ARCHETYPE_PARAMS[self.archetype]

    @property
    def stage_str(self):
        return STAGES[min(self.current_stage, 6)]

    @property
    def growth_str(self):
        return GROWTH_LEVELS[min(self.growth_level, 4)]

    def daily_active_prob(self, day_offset):
        """活跃概率随时间衰减 (dropout 类型衰减快)"""
        base = self.params["daily_active_prob"]
        days_since_reg = day_offset - self.register_day
        if self.dropped_out:
            return 0.02  # 偶尔回来看看
        if self.archetype == "dropout":
            decay = math.exp(-0.02 * days_since_reg)
        elif self.archetype == "struggling":
            decay = math.exp(-0.005 * days_since_reg)
        else:
            decay = max(0.8, math.exp(-0.001 * days_since_reg))
        return base * decay


def generate_users() -> list[SimUser]:
    """生成 1200 个模拟用户, 注册分布在 180 天内"""
    users = []

    # 注册分布: 前 30 天密集 (60%), 30-90 天中等 (25%), 90-180 天稀疏 (15%)
    reg_days = []
    n = CFG.total_users
    for _ in range(int(n * 0.60)):
        reg_days.append(rng.randint(0, 29))
    for _ in range(int(n * 0.25)):
        reg_days.append(rng.randint(30, 89))
    for _ in range(n - len(reg_days)):
        reg_days.append(rng.randint(90, 179))
    reg_days.sort()

    used_phones = set()
    archetypes = list(CFG.ARCHETYPES.keys())
    archetype_weights = list(CFG.ARCHETYPES.values())

    # Start IDs at 1001 to avoid conflict with seed users (IDs 2-33)
    SIM_ID_OFFSET = 1000
    for i, reg_day in enumerate(reg_days):
        uid = i + 1 + SIM_ID_OFFSET

        # 手机号去重
        phone = rng.phone()
        while phone in used_phones:
            phone = rng.phone()
        used_phones.add(phone)

        archetype = rng.weighted_choice(list(CFG.ARCHETYPES.items()))
        condition = rng.weighted_choice(CFG.CONDITIONS)

        # 年龄
        age_bracket = rng.weighted_choice([(b, w) for b in CFG.AGE_DIST for _, _, w in [b]])
        # Fix: properly unpack
        for lo, hi, w in CFG.AGE_DIST:
            if rng.random() < w / sum(ww for _, _, ww in CFG.AGE_DIST):
                age = rng.randint(lo, hi)
                break
        else:
            age = rng.randint(45, 65)

        gender = rng.choice(["male", "female"])
        city = rng.choice(CFG.CITIES)

        # 初始阶段
        init_stages = ARCHETYPE_PARAMS[archetype]["init_stage_dist"]
        init_stage = rng.weighted_choice(init_stages)

        # 初始 SPI (与阶段相关)
        base_spi = 15 + init_stage * 12 + rng.gauss(0, 5)
        spi = max(5, min(95, base_spi))

        # 密码散列 (固定格式, 不真正用 bcrypt 加速生成)
        pw_hash = "$2b$12$" + hashlib.sha256(f"sim_{uid}_{phone}".encode()).hexdigest()[:53]

        # 角色 (使用 PostgreSQL userrole 枚举值)
        if uid <= 5:
            role = "ADMIN"
        elif uid <= 15:
            role = "MASTER"
        elif uid <= 35:
            role = "COACH"
        else:
            role = "OBSERVER"

        user = SimUser(
            id=uid, phone=phone, nickname=rng.chinese_name(),
            password_hash=pw_hash, role=role, archetype=archetype,
            condition=condition, city=city, age=age, gender=gender,
            register_day=reg_day, current_stage=init_stage,
            spi_score=round(spi, 1),
            readiness=min(init_stage + 1, 5),
        )
        users.append(user)

    return users


# ══════════════════════════════════════════════
# 种子数据
# ══════════════════════════════════════════════

CHANGE_CAUSES = [
    ("C01", "psychological", "健康信念", "health_belief", 1.2),
    ("C02", "psychological", "自我效能", "self_efficacy", 1.3),
    ("C03", "psychological", "风险感知", "risk_perception", 1.1),
    ("C04", "psychological", "结果期望", "outcome_expectation", 1.0),
    ("C05", "behavioral", "行为习惯", "habit_pattern", 1.2),
    ("C06", "behavioral", "自我监控", "self_monitoring", 1.1),
    ("C07", "behavioral", "目标设定", "goal_setting", 1.0),
    ("C08", "behavioral", "应对策略", "coping_strategy", 0.9),
    ("C09", "social", "社会支持", "social_support", 1.0),
    ("C10", "social", "同伴影响", "peer_influence", 0.8),
    ("C11", "social", "家庭环境", "family_environment", 1.1),
    ("C12", "environmental", "医疗可及性", "healthcare_access", 0.9),
    ("C13", "environmental", "健康素养", "health_literacy", 1.2),
    ("C14", "environmental", "经济因素", "economic_factor", 0.7),
    ("C15", "motivational", "内在动机", "intrinsic_motivation", 1.4),
    ("C16", "motivational", "改变意愿", "readiness_to_change", 1.3),
    ("C17", "motivational", "迫切感", "urgency_sense", 1.1),
    ("C18", "cognitive", "认知偏差", "cognitive_bias", 0.9),
    ("C19", "cognitive", "知识水平", "knowledge_level", 1.0),
    ("C20", "cognitive", "决策能力", "decision_making", 0.8),
]

INTERVENTION_STRATEGIES = [
    # (stage, readiness, cause_code, strategy_type, coach_script_snippet)
    ("S0", "L1", "C01", "awareness_raising", "您是否了解您目前的健康状况？"),
    ("S0", "L1", "C03", "risk_education",    "让我们了解一下不管理血糖可能带来的风险"),
    ("S1", "L2", "C02", "efficacy_building",  "相信自己可以做到，我们从小目标开始"),
    ("S1", "L2", "C16", "motivational_interview", "是什么让您开始考虑改变？"),
    ("S2", "L3", "C05", "habit_formation",    "每天固定时间做一件健康小事"),
    ("S2", "L3", "C07", "smart_goal",         "让我们制定一个具体可衡量的目标"),
    ("S3", "L3", "C06", "self_monitoring",    "坚持记录您的饮食和运动"),
    ("S3", "L4", "C08", "relapse_prevention", "遇到困难时可以试试这些应对方法"),
    ("S4", "L4", "C09", "social_mobilization","发动家人一起参与健康管理"),
    ("S4", "L5", "C15", "intrinsic_reward",   "感受到身体的变化了吗？这就是最好的奖励"),
    ("S5", "L5", "C05", "maintenance_plan",   "建立长期维持的日常节律"),
    ("S5", "L5", "C11", "family_engagement",  "让健康成为全家人的生活方式"),
]

REWARDS_CATALOG = [
    ("badge",   "首次打卡",       "完成第一次每日打卡",         "🎯", "growth",       10),
    ("badge",   "连续七天",       "连续打卡7天",               "🔥", "streak",       7),
    ("badge",   "连续三十天",     "连续打卡30天",              "💪", "streak",       30),
    ("badge",   "评估达人",       "完成所有评估批次",           "📋", "growth",       500),
    ("badge",   "知识探索者",     "累计发起20次知识问答",       "📚", "growth",       200),
    ("title",   "健康新手",       "达到G1成长等级",            "🌱", "growth",       100),
    ("title",   "健康践行者",     "达到G2成长等级",            "🌿", "growth",       300),
    ("title",   "健康达人",       "达到G3成长等级",            "🌳", "growth",       800),
    ("title",   "健康导师",       "达到G4成长等级",            "👑", "growth",       2000),
    ("feature", "Coach 深度对话",  "解锁与AI教练的深度分析功能", "🧠", "growth",       150),
    ("feature", "个性化报告",     "解锁每周个性化健康报告",     "📊", "growth",       250),
    ("item",    "健康手环优惠券", "合作品牌健康设备折扣",       "⌚", "contribution", 500),
]

# Coach 对话模板 (按意图分类)
CHAT_TEMPLATES = {
    "knowledge_query": [
        "代谢综合征的饮食原则是什么？",
        "二甲双胍和运动可以一起吗？",
        "血糖多少算正常范围？",
        "高血压患者能不能喝咖啡？",
        "什么是糖化血红蛋白？",
        "减重对血脂有什么帮助？",
        "如何判断自己是否有胰岛素抵抗？",
        "低GI饮食具体怎么做？",
        "运动降压的原理是什么？",
        "中医如何看待代谢综合征？",
        "痰湿体质怎么调理？",
        "糖尿病前期能逆转吗？",
        "肝功能不好能吃降脂药吗？",
        "间歇性断食适合糖尿病人吗？",
        "什么运动对降血糖最有效？",
    ],
    "emotional_support": [
        "我今天又没管住嘴，好自责",
        "坚持了一周，突然很想放弃",
        "家人不理解我为什么要忌口",
        "血糖一直降不下来好焦虑",
        "同事聚餐不好意思拒绝",
        "最近压力很大，完全不想动",
        "医生说可能要打胰岛素，很害怕",
        "减了5斤又反弹了，很沮丧",
        "老伴走了以后一个人也不想做饭了",
        "年纪大了记性不好总忘吃药",
    ],
    "prescription_adjust": [
        "上周的方案感觉太难了，能调整吗？",
        "我的运动量想加一些",
        "最近工作忙想减少打卡频率",
        "想把走路换成游泳可以吗？",
        "饮食方案里面的粗粮我吃不惯",
        "我现在状态好了很多，想挑战更高目标",
    ],
    "casual": [
        "你好",
        "今天天气不错",
        "谢谢你的建议",
        "我知道了",
        "好的",
        "晚安",
    ],
}

COACH_RESPONSES = {
    "knowledge_query": [
        "根据最新临床指南，建议您…",
        "这个问题很好。从营养学角度来看…",
        "根据您的个人情况，我建议…",
    ],
    "emotional_support": [
        "理解您的感受，改变从来不是一帆风顺的…",
        "您已经很棒了，坚持到现在本身就是进步…",
        "我们可以一起想想适合您的应对方法…",
    ],
    "prescription_adjust": [
        "好的，根据您的反馈我来调整一下…",
        "了解了，我们把目标降低一点…",
        "很高兴您状态好了，我来制定新方案…",
    ],
    "casual": [
        "您好！有什么我可以帮您的吗？",
        "不客气，随时可以找我聊天。",
        "祝您今天愉快！",
    ],
}


# ══════════════════════════════════════════════
# 生成引擎
# ══════════════════════════════════════════════

class SimDataGenerator:
    def __init__(self, config: SimConfig):
        self.cfg = config
        self.users: list[SimUser] = []
        self.records = defaultdict(list)  # table_name → [dict, ...]
        self.counters = defaultdict(int)  # auto-increment counters

    def next_id(self, table: str) -> int:
        self.counters[table] += 1
        return self.counters[table]

    def ts(self, day: int, hour: int = 8, minute: int = 0) -> datetime:
        """日期转 datetime"""
        return self.cfg.start_date + timedelta(days=day, hours=hour, minutes=minute)

    def ts_rand(self, day: int, hour_range=(7, 22)) -> datetime:
        """随机时间点"""
        h = rng.randint(hour_range[0], hour_range[1])
        m = rng.randint(0, 59)
        s = rng.randint(0, 59)
        return self.cfg.start_date + timedelta(days=day, hours=h, minutes=m, seconds=s)

    # ── 1. 种子数据 ──

    def gen_seed_data(self):
        """字典表 + 策略表 + 奖励表"""
        print("  [种子] change_causes × 20")
        for code, cat, name_zh, name_en, weight in CHANGE_CAUSES:
            self.records["change_causes"].append({
                "id": code, "category": cat, "name_zh": name_zh,
                "name_en": name_en, "weight": weight,
                "description": f"{name_zh}({name_en})对行为改变的影响评估",
                "assessment_question": f"请评估您在「{name_zh}」方面的状态(1-5分)",
            })

        print("  [种子] intervention_strategies × 12")
        cause_cat_map = {c[0]: c[1] for c in CHANGE_CAUSES}
        cause_name_map = {c[0]: c[2] for c in CHANGE_CAUSES}
        stage_name_map = {"S0":"前意向","S1":"意向","S2":"准备","S3":"行动","S4":"维持","S5":"巩固"}
        for stage, readiness, cause, stype, script in INTERVENTION_STRATEGIES:
            self.records["intervention_strategies"].append({
                "id": self.next_id("intervention_strategies"),
                "stage_code": stage, "readiness_level": readiness,
                "stage_name": stage_name_map.get(stage, stage),
                "cause_code": cause,
                "cause_category": cause_cat_map.get(cause, ""),
                "cause_name": cause_name_map.get(cause, ""),
                "strategy_type": stype, "coach_script": script,
            })

        print("  [种子] incentive_rewards × 12")
        for rtype, name, desc, icon, dim, thresh in REWARDS_CATALOG:
            self.records["incentive_rewards"].append({
                "id": self.next_id("incentive_rewards"),
                "reward_type": rtype, "name": name, "description": desc,
                "icon": icon, "unlock_dimension": dim, "unlock_threshold": thresh,
            })

        print("  [种子] knowledge_chunks × 50")
        doc_types = ["clinical_guideline", "theory_framework", "intervention_strategy",
                     "behavior_guide", "tcm_principle", "nutrition_guide"]
        topics = [
            "代谢综合征概述", "2型糖尿病管理", "高血压饮食指导", "血脂异常运动方案",
            "TTM行为改变模型", "动机访谈技术", "COM-B行为模型", "自我效能理论",
            "认知行为疗法基础", "正念减压技术", "习惯养成科学", "社会支持理论",
            "糖尿病足预防", "胰岛素抵抗机制", "GLP-1受体激动剂", "SGLT2抑制剂",
            "八段锦功法", "太极拳健身", "中医体质辨识", "痰湿体质调理",
            "低GI饮食原则", "地中海饮食", "DASH饮食", "间歇性断食",
            "有氧运动处方", "抗阻训练指导", "柔韧性训练", "平衡训练",
            "睡眠卫生指导", "压力管理技术", "社交处方", "家庭健康管理",
            "血糖监测规范", "血压测量指南", "BMI与腰围标准", "实验室检查解读",
            "S0阶段干预策略", "S1阶段干预策略", "S2阶段干预策略", "S3阶段干预策略",
            "行为模式分型A型", "行为模式分型B型", "行为模式分型C型",
            "大五人格与健康", "外向性健康效应", "尽责性健康效应",
            "180天代谢重建方案", "90天血糖达标路径", "60天血压管理", "30天饮食革命",
        ]
        for i, topic in enumerate(topics):
            self.records["knowledge_chunks"].append({
                "id": self.next_id("knowledge_chunks"),
                "chunk_id": f"kc_{i+1:04d}",
                "source": f"knowledge/{doc_types[i % len(doc_types)]}/{topic}.md",
                "doc_type": doc_types[i % len(doc_types)],
                "section": topic,
                "seq": i % 5,
                "char_count": rng.randint(300, 1500),
                "text_preview": f"[{topic}] 本章节详细介绍了{topic}的核心内容...",
                "created_at": self.ts(0).isoformat(),
                "updated_at": self.ts(0).isoformat(),
            })

    # ── 2. 用户 ──

    def gen_users(self):
        self.users = generate_users()
        print(f"  [用户] users × {len(self.users)}")

        for u in self.users:
            reg_ts = self.ts_rand(u.register_day, (8, 20))
            username = f"sim_{u.id:04d}"
            self.records["users"].append({
                "id": u.id, "phone": u.phone,
                "username": username,
                "email": f"{username}@sim.bhp.local",
                "nickname": u.nickname,
                "password_hash": u.password_hash, "role": u.role,
                "is_active": True, "health_competency_level": "Lv0",
                "current_stage": u.stage_str, "growth_level": u.growth_str,
                "created_at": reg_ts.isoformat(),
                "updated_at": reg_ts.isoformat(),
                "last_login_at": reg_ts.isoformat(),
                "avatar_url": "",
            })

    # ── 3. 每日模拟 ──

    def simulate_day(self, day: int):
        """模拟第 day 天 (0-indexed) 的所有活动"""
        active_today = []

        for user in self.users:
            if user.register_day > day:
                continue  # 还没注册
            if not user.is_active and not user.dropped_out:
                continue

            prob = user.daily_active_prob(day)
            if rng.random() < prob:
                active_today.append(user)

        # ── 新用户首日: 诊断 + 评估启动 ──
        for user in active_today:
            if user.register_day == day:
                self._do_onboarding(user, day)

        # ── 日常活动 ──
        for user in active_today:
            ts = self.ts_rand(day)

            # 打卡
            if rng.random() < user.params["checkin_prob"]:
                self._do_checkin(user, day, ts)

            # 任务完成 (日常干预)
            if rng.random() < user.params["completion_rate"][1]:
                self._do_daily_outcome(user, day, ts)

            # 对话
            if rng.random() < user.params["chat_prob"]:
                n_chats = rng.randint(1, 3)
                for _ in range(n_chats):
                    self._do_chat(user, day)

            # 评估推进
            days_since_reg = day - user.register_day
            assessment_interval = int(7 / user.params["assessment_speed"])
            if (days_since_reg > 0 and
                days_since_reg % max(assessment_interval, 3) == 0 and
                len(user.completed_batches) < 12):
                self._do_assessment_batch(user, day)

            # 阶段进阶检查
            if rng.random() < user.params["stage_advance_rate"]:
                self._do_stage_advance(user, day)

            # 流失检查
            if rng.random() < user.params["dropout_prob"]:
                user.dropped_out = True

        # 更新 last_login
        for user in active_today:
            for rec in self.records["users"]:
                if rec["id"] == user.id:
                    rec["last_login_at"] = self.ts_rand(day).isoformat()
                    rec["current_stage"] = user.stage_str
                    rec["growth_level"] = user.growth_str
                    break

        return len(active_today)

    # ── 首日引导 ──

    def _do_onboarding(self, user: SimUser, day: int):
        ts = self.ts_rand(day, (8, 12))

        # 最小启动诊断
        user.diagnostic_done = True

        # 创建评估 session
        sid = self.next_id("assessment_sessions")
        user.assessment_session_id = sid
        self.records["assessment_sessions"].append({
            "id": sid, "user_id": user.id, "status": "in_progress",
            "completed_batches": json.dumps([]),
            "pending_batches": json.dumps(["B1_TTM7_CORE", "B2_SPI_QUICK"]),
            "total_questions_answered": 0, "total_questions": 176,
            "partial_results": json.dumps({}),
            "started_at": ts.isoformat(), "last_activity": ts.isoformat(),
            "completed_at": None,
            "expires_at": (ts + timedelta(days=30)).isoformat(),
        })

        # 完成 B1 + B2 (首日必做)
        self._submit_batch(user, "B1_TTM7_CORE", 7, day, ts)
        self._submit_batch(user, "B2_SPI_QUICK", 5, day,
                          ts + timedelta(minutes=rng.randint(3, 10)))

        # 动因评分 (基于初始诊断)
        for cause_code, _, name_zh, _, weight in CHANGE_CAUSES:
            base = 2 + user.current_stage * 0.3
            score = max(1, min(5, int(base + rng.gauss(0, 1))))
            self.records["user_change_cause_scores"].append({
                "id": self.next_id("user_change_cause_scores"),
                "user_id": user.id, "assessment_id": sid,
                "cause_id": cause_code,
                "score": score,
                "created_at": ts.isoformat(),
            })

        # 健康素养评估
        base_score = 30 + user.current_stage * 8 + rng.gauss(0, 10)
        hc_score = max(10, min(100, base_score))
        hc_level = "Lv0" if hc_score < 40 else "Lv1" if hc_score < 60 else "Lv2" if hc_score < 80 else "Lv3"
        user.health_competency = hc_level
        self.records["health_competency_assessments"].append({
            "id": self.next_id("health_competency_assessments"),
            "user_id": user.id,
            "answers": json.dumps({"total_score": round(hc_score, 1)}),
            "level_scores": json.dumps({
                "knowledge": round(hc_score * rng.uniform(0.8, 1.2), 1),
                "attitude": round(hc_score * rng.uniform(0.9, 1.1), 1),
                "practice": round(hc_score * rng.uniform(0.7, 1.3), 1),
            }),
            "current_level": hc_level,
            "recommended_content_stage": CULTIVATION[min(user.cultivation, 3)],
            "created_at": ts.isoformat(),
        })

        # COMB 评估
        cap = round(rng.uniform(30, 80), 1)
        opp = round(rng.uniform(40, 85), 1)
        mot = round(rng.uniform(20 + user.current_stage * 10, 90), 1)
        bottleneck = min([("capability", cap), ("opportunity", opp), ("motivation", mot)],
                        key=lambda x: x[1])[0]
        self.records["comb_assessments"].append({
            "id": self.next_id("comb_assessments"),
            "user_id": user.id,
            "answers": json.dumps({"capability": cap, "opportunity": opp, "motivation": mot}),
            "dimension_scores": json.dumps({"capability": cap, "opportunity": opp, "motivation": mot}),
            "bottleneck": bottleneck,
            "total_score": round((cap + opp + mot) / 3, 1),
            "created_at": ts.isoformat(),
        })

        # 自我效能评估
        se_score = round(20 + user.current_stage * 12 + rng.gauss(0, 8), 1)
        se_score = max(10, min(100, se_score))
        se_level = "low" if se_score < 40 else "medium" if se_score < 70 else "high"
        self.records["self_efficacy_assessments"].append({
            "id": self.next_id("self_efficacy_assessments"),
            "user_id": user.id,
            "answers": json.dumps({"raw_score": se_score}),
            "avg_score": se_score,
            "level": se_level, "created_at": ts.isoformat(),
        })

        # 障碍评估
        obstacles = rng.choices(
            ["time", "motivation", "knowledge", "social", "cost", "physical", "emotional"],
            k=rng.randint(2, 4))
        obs_score = round(rng.uniform(20, 70), 1)
        self.records["obstacle_assessments"].append({
            "id": self.next_id("obstacle_assessments"),
            "user_id": user.id,
            "answers": json.dumps({"total_score": obs_score}),
            "category_scores": json.dumps({o: round(rng.uniform(1, 5), 1) for o in obstacles}),
            "top_obstacles": json.dumps(obstacles),
            "rx_adjustments": json.dumps({"reduce_intensity": obstacles[0] == "physical"}),
            "created_at": ts.isoformat(),
        })

        # 支持评估
        support_score = round(rng.uniform(30, 80), 1)
        weakest = rng.choice(["family", "peer", "professional", "community"])
        self.records["support_assessments"].append({
            "id": self.next_id("support_assessments"),
            "user_id": user.id,
            "answers": json.dumps({"raw_score": support_score}),
            "layer_scores": json.dumps({
                "family": round(rng.uniform(20, 90), 1),
                "peer": round(rng.uniform(10, 70), 1),
                "professional": round(rng.uniform(30, 80), 1),
                "community": round(rng.uniform(15, 60), 1),
            }),
            "total_score": support_score,
            "support_level": "low" if support_score < 40 else "medium" if support_score < 65 else "high",
            "weakest_layer": weakest,
            "created_at": ts.isoformat(),
        })

        # 首次对话 (欢迎)
        self._do_chat(user, day, intent="casual",
                     msg="你好，我刚注册", resp="欢迎加入BHP健康管理平台！我是您的AI健康教练…")

        # 首日积分
        self._add_points(user, "registration", "growth", 20, "完成注册", day)
        self._add_points(user, "first_assessment", "growth", 30, "首次评估完成", day)

    # ── 评估批次提交 ──

    def _submit_batch(self, user: SimUser, batch_id: str, q_count: int,
                     day: int, ts: datetime):
        if batch_id in user.completed_batches:
            return  # 幂等

        answers = {}
        for q in range(1, q_count + 1):
            answers[f"q{q}"] = rng.randint(1, 5)

        self.records["batch_answers"].append({
            "id": self.next_id("batch_answers"),
            "session_id": user.assessment_session_id or 1,
            "user_id": user.id,
            "batch_id": batch_id,
            "questionnaire": batch_id.split("_")[1] if "_" in batch_id else batch_id,
            "answers": json.dumps(answers),
            "scores": json.dumps({"avg": round(sum(answers.values()) / len(answers), 2)}),
            "duration_seconds": rng.randint(60, 300),
            "created_at": ts.isoformat(),
        })

        user.completed_batches.append(batch_id)
        user.assessments_completed += 1

        # 更新 session
        for rec in self.records["assessment_sessions"]:
            if rec["user_id"] == user.id:
                rec["completed_batches"] = json.dumps(user.completed_batches)
                rec["total_questions_answered"] = sum(
                    [7,5,13,12,20,5,18,25,25,16,16,14][:len(user.completed_batches)])
                rec["last_activity"] = ts.isoformat()
                if len(user.completed_batches) >= 12:
                    rec["status"] = "completed"
                    rec["completed_at"] = ts.isoformat()
                break

    # ── 评估推进 ──

    def _do_assessment_batch(self, user: SimUser, day: int):
        BATCH_ORDER = [
            "B1_TTM7_CORE", "B2_SPI_QUICK", "B3_SPI_TRIGGERS", "B4_SPI_TRIGGERS2",
            "B5_SPI_PSY", "B6_SPI_URGENCY", "B7_BPT6", "B8_BIG5_PART1",
            "B9_BIG5_PART2", "B10_CAPACITY_PART1", "B11_CAPACITY_PART2", "B12_TTM7_DEEP",
        ]
        BATCH_Q_COUNTS = [7, 5, 13, 12, 20, 5, 18, 25, 25, 16, 16, 14]

        for i, bid in enumerate(BATCH_ORDER):
            if bid not in user.completed_batches:
                ts = self.ts_rand(day)
                self._submit_batch(user, bid, BATCH_Q_COUNTS[i], day, ts)
                self._add_points(user, "assessment_complete", "growth", 15,
                               f"完成评估 {bid}", day)
                break

    # ── 打卡 ──

    def _do_checkin(self, user: SimUser, day: int, ts: datetime):
        # 连续打卡
        if user.last_checkin_day == day - 1:
            user.streak_days += 1
        elif user.last_checkin_day != day:
            user.streak_days = 1
        user.last_checkin_day = day
        user.longest_streak = max(user.longest_streak, user.streak_days)

        pts = 5
        if user.streak_days >= 30:
            pts = 15
        elif user.streak_days >= 7:
            pts = 10

        self._add_points(user, "daily_checkin", "growth", pts,
                        f"每日打卡(连续{user.streak_days}天)", day)

    # ── 日常干预效果 ──

    def _do_daily_outcome(self, user: SimUser, day: int, ts: datetime):
        params = user.params
        cr_lo, cr_hi = params["completion_rate"]
        completion = round(rng.uniform(cr_lo, cr_hi), 2)

        tasks_assigned = rng.randint(3, 6)
        tasks_completed = int(tasks_assigned * completion)
        tasks_skipped = tasks_assigned - tasks_completed

        # SPI 微调
        spi_before = user.spi_score
        delta = (completion - 0.5) * rng.uniform(0.2, 1.0)
        user.spi_score = round(max(5, min(95, user.spi_score + delta)), 1)

        # PDCA
        if completion >= 0.8:
            pdca = "maintain"
        elif completion >= 0.5:
            pdca = "adjust"
        else:
            pdca = "downgrade"

        mood = rng.randint(1, 5) if rng.random() > 0.3 else None
        difficulty = rng.randint(1, 5) if rng.random() > 0.4 else None

        self.records["intervention_outcomes"].append({
            "id": self.next_id("intervention_outcomes"),
            "user_id": user.id,
            "outcome_type": "daily",
            "period_start": ts.replace(hour=0, minute=0, second=0).isoformat(),
            "period_end": ts.replace(hour=23, minute=59, second=59).isoformat(),
            "completion_rate": completion,
            "streak_days": user.streak_days,
            "tasks_assigned": tasks_assigned,
            "tasks_completed": tasks_completed,
            "tasks_skipped": tasks_skipped,
            "spi_before": spi_before,
            "spi_after": user.spi_score,
            "spi_delta": round(user.spi_score - spi_before, 2),
            "stage_before": user.stage_str,
            "stage_after": user.stage_str,
            "readiness_before": READINESS[min(user.readiness - 1, 4)],
            "readiness_after": READINESS[min(user.readiness - 1, 4)],
            "cultivation_stage": CULTIVATION[min(user.cultivation, 3)],
            "user_mood": mood,
            "user_difficulty": difficulty,
            "user_notes": "",
            "adjustment_action": pdca,
            "adjustment_detail": json.dumps({"reason": pdca}),
            "effectiveness_score": round(completion * user.spi_score / 100, 3),
            "created_at": ts.isoformat(),
        })

        user.tasks_completed_total += tasks_completed

        if tasks_completed > 0:
            self._add_points(user, "task_complete", "growth",
                           tasks_completed * 3, f"完成{tasks_completed}项任务", day)

    # ── 对话 ──

    def _do_chat(self, user: SimUser, day: int,
                intent: str = None, msg: str = None, resp: str = None):
        ts = self.ts_rand(day)

        if intent is None:
            # 按画像分配意图
            if user.archetype == "explorer":
                intent_weights = [("knowledge_query", 0.5), ("emotional_support", 0.15),
                                 ("prescription_adjust", 0.15), ("casual", 0.2)]
            elif user.archetype == "struggling":
                intent_weights = [("knowledge_query", 0.2), ("emotional_support", 0.45),
                                 ("prescription_adjust", 0.2), ("casual", 0.15)]
            else:
                intent_weights = [("knowledge_query", 0.35), ("emotional_support", 0.2),
                                 ("prescription_adjust", 0.2), ("casual", 0.25)]
            intent = rng.weighted_choice(intent_weights)

        if msg is None:
            msg = rng.choice(CHAT_TEMPLATES.get(intent, CHAT_TEMPLATES["casual"]))
        if resp is None:
            resp = rng.choice(COACH_RESPONSES.get(intent, COACH_RESPONSES["casual"]))

        # 模型路由
        if intent == "casual":
            model, provider, complexity = "deepseek-chat", "deepseek", "simple"
            in_tok, out_tok = rng.randint(10, 50), rng.randint(20, 80)
            cost = round(in_tok * 0.0001 + out_tok * 0.0002, 4)
            latency = rng.randint(200, 800)
        elif intent == "knowledge_query":
            model, provider, complexity = "qwen-plus", "dashscope", "moderate"
            in_tok, out_tok = rng.randint(100, 400), rng.randint(200, 600)
            cost = round(in_tok * 0.0008 + out_tok * 0.002, 4)
            latency = rng.randint(800, 3000)
        elif intent == "prescription_adjust":
            model, provider, complexity = "qwen-max", "dashscope", "complex"
            in_tok, out_tok = rng.randint(300, 800), rng.randint(400, 1000)
            cost = round(in_tok * 0.002 + out_tok * 0.006, 4)
            latency = rng.randint(1500, 5000)
        else:
            model, provider, complexity = "qwen-plus", "dashscope", "moderate"
            in_tok, out_tok = rng.randint(80, 300), rng.randint(150, 500)
            cost = round(in_tok * 0.0008 + out_tok * 0.002, 4)
            latency = rng.randint(600, 2500)

        fell_back = rng.random() < 0.03  # 3% 降级率
        if fell_back:
            model = "deepseek-chat"
            provider = "deepseek"

        session_id = f"sess_{user.id}_{day}_{rng.randint(1000,9999)}"

        # LLM 日志
        self.records["llm_call_logs"].append({
            "id": self.next_id("llm_call_logs"),
            "user_id": user.id, "session_id": session_id,
            "created_at": ts.isoformat(),
            "intent": intent, "complexity": complexity,
            "model_requested": model if not fell_back else "qwen-plus",
            "model_actual": model, "provider": provider,
            "fell_back": fell_back,
            "input_tokens": in_tok, "output_tokens": out_tok,
            "cost_yuan": cost, "latency_ms": latency,
            "finish_reason": "stop",
            "user_message_preview": msg[:100],
            "assistant_message_preview": resp[:100],
            "error_message": None,
        })

        # RAG 日志 (知识查询类)
        if intent == "knowledge_query":
            results_count = rng.randint(2, 5)
            top_score = round(rng.uniform(0.65, 0.95), 3)
            self.records["rag_query_logs"].append({
                "id": self.next_id("rag_query_logs"),
                "user_id": user.id, "created_at": ts.isoformat(),
                "query_text": msg, "query_type": "knowledge",
                "doc_type_filter": None, "top_k": 5,
                "results_count": results_count,
                "top_score": top_score,
                "avg_score": round(top_score * rng.uniform(0.7, 0.9), 3),
                "sources_json": json.dumps([f"kc_{rng.randint(1,50):04d}" for _ in range(results_count)]),
                "total_latency_ms": rng.randint(50, 300),
                "llm_call_log_id": self.counters["llm_call_logs"],
            })

    # ── 阶段进阶 ──

    def _do_stage_advance(self, user: SimUser, day: int):
        if user.current_stage >= 6:
            return
        if user.spi_score < 20 + user.current_stage * 10:
            return  # SPI 不够

        old_stage = user.current_stage
        user.current_stage += 1
        ts = self.ts_rand(day)

        self.records["stage_transition_logs"].append({
            "id": self.next_id("stage_transition_logs"),
            "user_id": user.id, "transition_type": "behavioral",
            "from_value": STAGES[old_stage], "to_value": STAGES[user.current_stage],
            "trigger": "spi_threshold",
            "evidence": json.dumps({
                "spi_score": user.spi_score,
                "days_in_stage": rng.randint(7, 45),
                "completion_rate_avg": round(rng.uniform(0.5, 0.9), 2),
            }),
            "created_at": ts.isoformat(),
        })

        # 成长等级联动
        new_gl = min(user.current_stage // 2 + (1 if user.growth_points > 300 else 0), 4)
        if new_gl > user.growth_level:
            old_gl = user.growth_level
            user.growth_level = new_gl
            self.records["stage_transition_logs"].append({
                "id": self.next_id("stage_transition_logs"),
                "user_id": user.id, "transition_type": "growth",
                "from_value": GROWTH_LEVELS[old_gl], "to_value": GROWTH_LEVELS[new_gl],
                "trigger": "stage_advance",
                "evidence": json.dumps({"growth_points": user.growth_points}),
                "created_at": ts.isoformat(),
            })

        # 可读性提升
        if user.readiness < 5 and rng.random() < 0.5:
            old_r = user.readiness
            user.readiness += 1
            self.records["stage_transition_logs"].append({
                "id": self.next_id("stage_transition_logs"),
                "user_id": user.id, "transition_type": "readiness",
                "from_value": READINESS[old_r - 1], "to_value": READINESS[user.readiness - 1],
                "trigger": "behavioral_advance",
                "evidence": json.dumps({}),
                "created_at": ts.isoformat(),
            })

        # 培养阶段
        days_total = day - user.register_day
        new_cult = 0 if days_total < 30 else 1 if days_total < 90 else 2 if days_total < 150 else 3
        if new_cult > user.cultivation:
            old_c = user.cultivation
            user.cultivation = new_cult
            self.records["stage_transition_logs"].append({
                "id": self.next_id("stage_transition_logs"),
                "user_id": user.id, "transition_type": "cultivation",
                "from_value": CULTIVATION[old_c], "to_value": CULTIVATION[new_cult],
                "trigger": "time_elapsed",
                "evidence": json.dumps({"days_total": days_total}),
                "created_at": ts.isoformat(),
            })

        self._add_points(user, "stage_advance", "growth", 50,
                        f"阶段进阶 {STAGES[old_stage]}→{STAGES[user.current_stage]}", day)

    # ── 积分 ──

    def _add_points(self, user: SimUser, event_type: str, dimension: str,
                   points: int, desc: str, day: int):
        self.records["point_events"].append({
            "id": self.next_id("point_events"),
            "user_id": user.id, "event_type": event_type,
            "dimension": dimension, "points": points,
            "source_type": event_type.split("_")[0],
            "source_id": f"{event_type}_{user.id}_{day}",
            "description": desc,
            "created_at": self.ts_rand(day).isoformat(),
        })
        if dimension == "growth":
            user.growth_points += points
        elif dimension == "contribution":
            user.contribution_points += points
        elif dimension == "influence":
            user.influence_points += points

    # ── 生成积分余额快照 ──

    def gen_point_balances(self):
        print("  [积分] user_point_balances")
        for user in self.users:
            total = user.growth_points + user.contribution_points + user.influence_points
            self.records["user_point_balances"].append({
                "user_id": user.id,
                "growth": user.growth_points,
                "contribution": user.contribution_points,
                "influence": user.influence_points,
                "total": total,
                "streak_days": user.streak_days,
                "longest_streak": user.longest_streak,
                "last_checkin_date": (self.ts(user.last_checkin_day).isoformat()
                                     if user.last_checkin_day >= 0 else None),
                "tasks_completed_total": user.tasks_completed_total,
                "assessments_completed": user.assessments_completed,
                "updated_at": self.ts(self.cfg.total_days - 1).isoformat(),
            })

    # ── 奖励兑换 ──

    def gen_user_rewards(self):
        print("  [奖励] user_rewards")
        for user in self.users:
            for reward in REWARDS_CATALOG:
                rtype, name, desc, icon, dim, thresh = reward
                pts = getattr(user, f"{dim}_points", 0) if dim != "streak" else user.longest_streak
                if pts >= thresh:
                    self.records["user_rewards"].append({
                        "id": self.next_id("user_rewards"),
                        "user_id": user.id,
                        "reward_id": REWARDS_CATALOG.index(reward) + 1,
                        "earned_at": self.ts(
                            min(user.register_day + rng.randint(1, 90),
                                self.cfg.total_days - 1)).isoformat(),
                    })

    # ── 周报 (每 7 天汇总) ──

    def gen_weekly_reviews(self):
        print("  [周报] weekly intervention_outcomes")
        for user in self.users:
            reg = user.register_day
            for week_start in range(reg + 7, self.cfg.total_days, 7):
                # 汇总该周数据
                week_outcomes = [
                    r for r in self.records["intervention_outcomes"]
                    if r["user_id"] == user.id and
                    self.ts(week_start - 7).isoformat() <= r["period_start"] < self.ts(week_start).isoformat()
                ]
                if not week_outcomes:
                    continue

                avg_cr = sum(o["completion_rate"] for o in week_outcomes) / len(week_outcomes)
                spi_start = week_outcomes[0]["spi_before"]
                spi_end = week_outcomes[-1]["spi_after"]

                self.records["intervention_outcomes"].append({
                    "id": self.next_id("intervention_outcomes"),
                    "user_id": user.id,
                    "outcome_type": "weekly",
                    "period_start": self.ts(week_start - 7).isoformat(),
                    "period_end": self.ts(week_start - 1, 23, 59).isoformat(),
                    "completion_rate": round(avg_cr, 3),
                    "streak_days": user.streak_days,
                    "tasks_assigned": sum(o["tasks_assigned"] for o in week_outcomes),
                    "tasks_completed": sum(o["tasks_completed"] for o in week_outcomes),
                    "tasks_skipped": sum(o["tasks_skipped"] for o in week_outcomes),
                    "spi_before": spi_start,
                    "spi_after": spi_end,
                    "spi_delta": round(spi_end - spi_start, 2),
                    "stage_before": week_outcomes[0]["stage_before"],
                    "stage_after": week_outcomes[-1]["stage_after"],
                    "readiness_before": week_outcomes[0]["readiness_before"],
                    "readiness_after": week_outcomes[-1]["readiness_after"],
                    "cultivation_stage": week_outcomes[-1]["cultivation_stage"],
                    "user_mood": None, "user_difficulty": None, "user_notes": "",
                    "adjustment_action": "review",
                    "adjustment_detail": json.dumps({"type": "weekly_summary"}),
                    "effectiveness_score": round(avg_cr * spi_end / 100, 3),
                    "created_at": self.ts(week_start).isoformat(),
                })

    # ══════════════════════════════════════════════
    # 主运行
    # ══════════════════════════════════════════════

    def run(self):
        print("=" * 60)
        print("BHP v3 — 180天全流程模拟数据生成")
        print("=" * 60)

        print("\n📦 生成种子数据...")
        self.gen_seed_data()

        print("\n👤 生成用户...")
        self.gen_users()

        print(f"\n🔄 模拟 {self.cfg.total_days} 天运营...")
        daily_stats = []
        for day in range(self.cfg.total_days):
            dau = self.simulate_day(day)
            daily_stats.append(dau)
            if (day + 1) % 30 == 0 or day == 0:
                print(f"  Day {day+1:3d}: DAU={dau:4d}  "
                      f"注册={sum(1 for u in self.users if u.register_day <= day):5d}  "
                      f"活跃={sum(1 for u in self.users if not u.dropped_out and u.register_day <= day):5d}  "
                      f"流失={sum(1 for u in self.users if u.dropped_out):4d}")

        print("\n📊 生成汇总数据...")
        self.gen_point_balances()
        self.gen_user_rewards()
        self.gen_weekly_reviews()

        # 统计
        print("\n" + "=" * 60)
        print("📈 数据统计:")
        total_records = 0
        for table, rows in sorted(self.records.items()):
            print(f"  {table:40s} {len(rows):>8,} 条")
            total_records += len(rows)
        print(f"  {'─' * 40} {'─' * 8}")
        print(f"  {'总计':40s} {total_records:>8,} 条")
        print(f"\n  平均 DAU: {sum(daily_stats) / len(daily_stats):.0f}")
        print(f"  最高 DAU: {max(daily_stats)}")
        print(f"  最低 DAU: {min(daily_stats)}")

        # 画像分布
        arch_counts = defaultdict(int)
        for u in self.users:
            arch_counts[u.archetype] += 1
        print(f"\n  用户画像分布:")
        for a, c in sorted(arch_counts.items()):
            print(f"    {a:15s} {c:5d} ({c/len(self.users)*100:.1f}%)")

        # 阶段分布 (最终)
        stage_counts = defaultdict(int)
        for u in self.users:
            stage_counts[u.stage_str] += 1
        print(f"\n  最终阶段分布:")
        for s in STAGES:
            c = stage_counts.get(s, 0)
            print(f"    {s}: {c:5d} ({c/len(self.users)*100:.1f}%)")

        return self.records, daily_stats


# ══════════════════════════════════════════════
# 数据库写入
# ══════════════════════════════════════════════

def write_to_db(records: dict, db_url: str = None):
    """批量写入数据库 (自包含建表, 不依赖 ORM metadata)"""
    if db_url is None:
        db_url = os.environ.get("DATABASE_URL", "sqlite:///bhp_sim_180d.db")

    print(f"\n💾 写入数据库: {db_url.split('@')[-1] if '@' in db_url else db_url}")

    engine = create_engine(db_url)

    # 所有建表 DDL (SQLite 兼容, PG 也基本兼容)
    DDL_STATEMENTS = [
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, phone VARCHAR(20) UNIQUE,
            username VARCHAR(50) UNIQUE NOT NULL, email VARCHAR(120) NOT NULL,
            password_hash VARCHAR(128) NOT NULL, nickname VARCHAR(64) DEFAULT '',
            avatar_url VARCHAR(256) DEFAULT '', role VARCHAR(32) DEFAULT 'OBSERVER',
            is_active BOOLEAN DEFAULT true, health_competency_level VARCHAR(4) DEFAULT 'Lv0',
            current_stage VARCHAR(4) DEFAULT 'S0', growth_level VARCHAR(4) DEFAULT 'G0',
            created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW(),
            last_login_at TIMESTAMP)""",
        """CREATE TABLE IF NOT EXISTS change_causes (
            id VARCHAR(4) PRIMARY KEY, category VARCHAR(20), name_zh VARCHAR(50),
            name_en VARCHAR(50), description TEXT, assessment_question TEXT, weight FLOAT DEFAULT 1.0)""",
        """CREATE TABLE IF NOT EXISTS user_change_cause_scores (
            id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id),
            assessment_id INTEGER, cause_code VARCHAR(32), raw_score INTEGER DEFAULT 0,
            weighted_score FLOAT DEFAULT 0)""",
        """CREATE TABLE IF NOT EXISTS intervention_strategies (
            id INTEGER PRIMARY KEY, stage_code VARCHAR(8), readiness_level VARCHAR(8),
            cause_code VARCHAR(32), cause_name VARCHAR(64), strategy_type VARCHAR(64),
            coach_script TEXT, priority INTEGER DEFAULT 0, bpt_tags TEXT, domain VARCHAR(32))""",
        """CREATE TABLE IF NOT EXISTS health_competency_assessments (
            id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id),
            total_score FLOAT, level VARCHAR(4), dimension_scores TEXT, created_at DATETIME)""",
        """CREATE TABLE IF NOT EXISTS comb_assessments (
            id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id),
            capability FLOAT, opportunity FLOAT, motivation FLOAT,
            bottleneck VARCHAR(32), created_at DATETIME)""",
        """CREATE TABLE IF NOT EXISTS self_efficacy_assessments (
            id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id),
            total_score FLOAT, level VARCHAR(16), created_at DATETIME)""",
        """CREATE TABLE IF NOT EXISTS obstacle_assessments (
            id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id),
            total_score FLOAT, top_obstacles TEXT, prescription_adjustments TEXT, created_at DATETIME)""",
        """CREATE TABLE IF NOT EXISTS support_assessments (
            id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id),
            support_level VARCHAR(16), layer_scores TEXT, weakest_layer VARCHAR(32), created_at DATETIME)""",
        """CREATE TABLE IF NOT EXISTS intervention_outcomes (
            id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id),
            outcome_type VARCHAR(20), period_start DATETIME, period_end DATETIME,
            completion_rate FLOAT, streak_days INTEGER DEFAULT 0,
            tasks_assigned INTEGER DEFAULT 0, tasks_completed INTEGER DEFAULT 0,
            tasks_skipped INTEGER DEFAULT 0, spi_before FLOAT, spi_after FLOAT,
            spi_delta FLOAT, stage_before VARCHAR(4), stage_after VARCHAR(4),
            readiness_before VARCHAR(4), readiness_after VARCHAR(4),
            cultivation_stage VARCHAR(20), user_mood INTEGER, user_difficulty INTEGER,
            user_notes TEXT DEFAULT '', adjustment_action VARCHAR(16),
            adjustment_detail TEXT, effectiveness_score FLOAT, created_at DATETIME)""",
        """CREATE TABLE IF NOT EXISTS stage_transition_logs (
            id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id),
            transition_type VARCHAR(20), from_value VARCHAR(10), to_value VARCHAR(10),
            trigger VARCHAR(50), evidence TEXT, created_at DATETIME)""",
        """CREATE TABLE IF NOT EXISTS point_events (
            id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id),
            event_type VARCHAR(30), dimension VARCHAR(15), points INTEGER,
            source_type VARCHAR(30), source_id VARCHAR(50), description VARCHAR(200),
            created_at DATETIME)""",
        """CREATE TABLE IF NOT EXISTS user_point_balances (
            user_id INTEGER PRIMARY KEY REFERENCES users(id),
            growth INTEGER DEFAULT 0, contribution INTEGER DEFAULT 0,
            influence INTEGER DEFAULT 0, total INTEGER DEFAULT 0,
            streak_days INTEGER DEFAULT 0, longest_streak INTEGER DEFAULT 0,
            last_checkin_date DATETIME, tasks_completed_total INTEGER DEFAULT 0,
            assessments_completed INTEGER DEFAULT 0, updated_at DATETIME)""",
        """CREATE TABLE IF NOT EXISTS incentive_rewards (
            id INTEGER PRIMARY KEY, reward_type VARCHAR(30), name VARCHAR(50),
            description TEXT, icon VARCHAR(10), unlock_dimension VARCHAR(15),
            unlock_threshold INTEGER)""",
        """CREATE TABLE IF NOT EXISTS user_rewards (
            id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id),
            reward_id INTEGER REFERENCES incentive_rewards(id),
            points_spent INTEGER DEFAULT 0, created_at DATETIME)""",
        """CREATE TABLE IF NOT EXISTS assessment_sessions (
            id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id),
            status VARCHAR(15) DEFAULT 'in_progress', completed_batches TEXT DEFAULT '[]',
            pending_batches TEXT DEFAULT '[]', total_questions_answered INTEGER DEFAULT 0,
            total_questions INTEGER DEFAULT 176, partial_results TEXT DEFAULT '{}',
            started_at DATETIME, last_activity DATETIME, completed_at DATETIME, expires_at DATETIME)""",
        """CREATE TABLE IF NOT EXISTS batch_answers (
            id INTEGER PRIMARY KEY, session_id INTEGER REFERENCES assessment_sessions(id),
            user_id INTEGER REFERENCES users(id), batch_id VARCHAR(30),
            questionnaire VARCHAR(10), answers TEXT, scores TEXT,
            duration_seconds INTEGER DEFAULT 0, created_at DATETIME)""",
        """CREATE TABLE IF NOT EXISTS llm_call_logs (
            id INTEGER PRIMARY KEY, user_id INTEGER, session_id VARCHAR(64),
            created_at DATETIME, intent VARCHAR(32), complexity VARCHAR(16),
            model_requested VARCHAR(64), model_actual VARCHAR(64), provider VARCHAR(32),
            fell_back BOOLEAN DEFAULT 0, input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0, cost_yuan FLOAT DEFAULT 0,
            latency_ms INTEGER DEFAULT 0, finish_reason VARCHAR(32),
            user_message_preview TEXT, assistant_message_preview TEXT, error_message TEXT)""",
        """CREATE TABLE IF NOT EXISTS rag_query_logs (
            id INTEGER PRIMARY KEY, user_id INTEGER, created_at DATETIME,
            query_text TEXT, query_type VARCHAR(32), doc_type_filter VARCHAR(32),
            top_k INTEGER DEFAULT 5, results_count INTEGER DEFAULT 0,
            top_score FLOAT DEFAULT 0, avg_score FLOAT DEFAULT 0,
            sources_json TEXT, total_latency_ms INTEGER DEFAULT 0, llm_call_log_id INTEGER)""",
        """CREATE TABLE IF NOT EXISTS knowledge_chunks (
            id INTEGER PRIMARY KEY, chunk_id VARCHAR(128) UNIQUE,
            source VARCHAR(256), doc_type VARCHAR(32), section VARCHAR(256),
            seq INTEGER DEFAULT 0, char_count INTEGER DEFAULT 0,
            text_preview TEXT, created_at DATETIME, updated_at DATETIME)""",
    ]

    # Skip DDL for PostgreSQL (tables already exist with correct schema)
    if "postgresql" not in db_url:
        with engine.begin() as conn:
            for ddl in DDL_STATEMENTS:
                conn.execute(text(ddl))

    # 写入顺序 (按外键依赖; skip knowledge_chunks — different schema in prod)
    TABLE_ORDER = [
        "users", "change_causes", "intervention_strategies",
        "incentive_rewards",
        "assessment_sessions",
        "user_change_cause_scores", "health_competency_assessments",
        "comb_assessments", "self_efficacy_assessments",
        "obstacle_assessments", "support_assessments",
        "batch_answers",
        "intervention_outcomes", "stage_transition_logs",
        "point_events", "user_point_balances",
        "user_rewards",
        "llm_call_logs", "rag_query_logs",
    ]

    # For PostgreSQL: delete sim data before re-inserting
    # Only preserve seed users (id < 1001); all other tables fully cleared
    # Explicit FK-safe delete order (children before parents)
    DELETE_ORDER = [
        "batch_answers",                     # → assessment_sessions, users
        "user_change_cause_scores",          # → users, change_causes
        "health_competency_assessments",     # → users
        "comb_assessments",                  # → users
        "self_efficacy_assessments",         # → users
        "obstacle_assessments",              # → users
        "support_assessments",               # → users
        "user_rewards",                      # → users, incentive_rewards
        "point_events",                      # → users
        "user_point_balances",               # → users
        "intervention_outcomes",             # → users
        "stage_transition_logs",             # → users
        "llm_call_logs",                     # no FK
        "rag_query_logs",                    # no FK
        "assessment_sessions",               # → users
        "incentive_rewards",                 # parent
        "intervention_strategies",           # parent
        "change_causes",                     # parent
        "users",                             # root
    ]
    SIM_ID_OFFSET = 1001
    print("  🗑️ 清理旧数据...")
    with engine.begin() as conn:
        for table_name in DELETE_ORDER:
            rows = records.get(table_name, [])
            if not rows:
                continue
            try:
                if table_name == "users":
                    conn.execute(text(f"DELETE FROM {table_name} WHERE id >= {SIM_ID_OFFSET}"))
                else:
                    conn.execute(text(f"DELETE FROM {table_name}"))
                print(f"    DELETE {table_name} ✓")
            except Exception as e:
                print(f"    ⚠️ DELETE {table_name} failed: {e}")

    with engine.begin() as conn:
        for table_name in TABLE_ORDER:
            rows = records.get(table_name, [])
            if not rows:
                continue

            # 批量插入 (每次 500 行)
            cols = list(rows[0].keys())
            placeholders = ", ".join([f":{c}" for c in cols])
            col_str = ", ".join(cols)
            sql = text(f"INSERT INTO {table_name} ({col_str}) VALUES ({placeholders})")

            batch_size = 500
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i+batch_size]
                conn.execute(sql, batch)

            print(f"  ✅ {table_name}: {len(rows):,} 条")

    # Reset users sequence to max(id)+1 so future INSERTs don't conflict
    if "postgresql" in db_url:
        with engine.begin() as conn:
            conn.execute(text("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))"))

    print("\n✅ 数据写入完成!")


# ══════════════════════════════════════════════
# CLI 入口
# ══════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="BHP v3 模拟数据生成器")
    parser.add_argument("--users", type=int, default=1200, help="总用户数")
    parser.add_argument("--days", type=int, default=180, help="模拟天数")
    parser.add_argument("--dau", type=int, default=300, help="目标 DAU")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    parser.add_argument("--no-db", action="store_true", help="只生成不写入")
    parser.add_argument("--json", action="store_true", help="导出 JSON")
    args = parser.parse_args()

    CFG.total_users = args.users
    CFG.total_days = args.days
    CFG.target_dau = args.dau
    CFG.seed = args.seed

    gen = SimDataGenerator(CFG)
    records, stats = gen.run()

    if args.json:
        out_file = "bhp_sim_data.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump({k: v for k, v in records.items()}, f,
                     ensure_ascii=False, indent=2, default=str)
        print(f"\n📄 JSON 导出: {out_file}")

    if not args.no_db:
        write_to_db(records)
