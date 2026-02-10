"""
行为画像系统
来源: §5 行为画像系统

核心:
  - BehavioralProfile: 统一行为画像 (系统唯一真相源)
  - BehavioralProfileService: 画像服务 (BAPS→统一画像)

画像维度 (§5.1):
  人口统计 | 医疗档案 | 设备档案 | 行为档案 | 内在需求 | 风险档案 | 干预状态 | 历史引用

交互模式 (§5.4):
  empathy(共情) — S0-S1 | challenge(挑战) — S2-S3 | execution(执行) — S4-S6

CAPACITY弱项→领域映射 (§5.3):
  C_信心→emotion,cognitive | A1_觉察→cognitive | A2_资源→social
  P_计划→nutrition,exercise | A3_能力→exercise,nutrition | C2_应对→stress,emotion
  I_网络→social | T_时间→exercise,sleep | Y_收益→cognitive
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime


# ── 交互模式 (§5.4) ──

INTERACTION_MODES = {
    "empathy":   {"stages": ["S0", "S1"], "description": "共情: 倾听理解, 不施压"},
    "challenge": {"stages": ["S2", "S3"], "description": "挑战: 适度激励, 引导行动",
                  "condition": "行动型(action type)"},
    "execution": {"stages": ["S4", "S5", "S6"], "description": "执行: 系统规划, 执行监督"},
}

# ── CAPACITY弱项→领域映射 (§5.3) ──

CAPACITY_TO_DOMAIN = {
    "C_confidence":  ["emotion", "cognitive"],
    "A1_awareness":  ["cognitive"],
    "A2_resource":   ["social"],
    "P_planning":    ["nutrition", "exercise"],
    "A3_ability":    ["exercise", "nutrition"],
    "C2_coping":     ["stress", "emotion"],
    "I_network":     ["social"],
    "T_time":        ["exercise", "sleep"],
    "Y_yield":       ["cognitive"],
}


# ── 统一行为画像 (§5.1) ──

@dataclass
class BehavioralProfile:
    """系统唯一真相源 — 存储用户的行为改变全貌"""

    user_id: int

    # 人口统计
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None

    # 医疗档案
    diagnoses: list[str] = field(default_factory=list)
    medications: list[str] = field(default_factory=list)
    lab_summary: dict = field(default_factory=dict)

    # 设备档案
    cgm_summary: dict = field(default_factory=dict)
    hrv_summary: dict = field(default_factory=dict)
    activity_summary: dict = field(default_factory=dict)

    # 行为档案 (BAPS评估输出)
    current_stage: str = "S0"           # TTM7 阶段 S0-S6
    readiness_level: str = "L1"         # 心理准备度 L1-L5
    growth_level: str = "G0"            # 成长等级 G0-G5
    health_competency: str = "Lv0"      # 健康能力 Lv0-Lv5
    motivation_level: float = 0.0
    self_efficacy: float = 0.0
    resistance_level: float = 0.0
    bpt6_type: str = "mixed"            # BPT-6行为分型
    spi_score: float = 0.0             # SPI评分

    # 内在需求 (AI提取)
    core_needs: list[str] = field(default_factory=list)
    emotional_tendencies: list[str] = field(default_factory=list)

    # 风险档案
    metabolic_risk: str = "low"
    cardiovascular_risk: str = "low"
    mental_stress: str = "low"

    # 干预状态
    active_plan_id: Optional[str] = None
    adherence_score: float = 0.0

    # 历史引用
    recent_assessments: list[dict] = field(default_factory=list)
    recent_tasks: list[dict] = field(default_factory=list)

    # 元数据
    stability: str = "stable"           # stable | unstable | critical
    dropout_risk: bool = False
    relapse_risk: bool = False
    interaction_mode: str = "empathy"   # empathy | challenge | execution
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def bmi(self) -> Optional[float]:
        if self.height and self.weight and self.height > 0:
            h_m = self.height / 100.0
            return round(self.weight / (h_m * h_m), 1)
        return None

    def to_dict(self) -> dict:
        """转为可序列化的dict"""
        d = {}
        for k, v in self.__dict__.items():
            if isinstance(v, datetime):
                d[k] = v.isoformat()
            else:
                d[k] = v
        return d


# ── 画像服务 (§5.2) ──

class BehavioralProfileService:
    """
    画像服务 — 从BAPS五套问卷结果生成/更新BehavioralProfile

    职责链 (§5.2):
      1. BAPS五套问卷 → 统一BehavioralProfile
      2. 阶段判定 (TTM7)
      3. 心理层级判定 (SPI)
      4. 交互模式判定 (Stage × BPT6 type)
      5. 领域需求识别 (CAPACITY弱项 + Trigger)
      6. 部分更新 (设备数据触发时)
    """

    def build_profile(self, user_id: int, baps_results: dict) -> BehavioralProfile:
        """
        从BAPS评估结果构建完整画像

        Args:
            baps_results: {
                "ttm7": {"current_stage": "S2", ...},
                "spi": {"spi_score": 65, "level": "L3", ...},
                "bpt6": {"dominant": "action", "scores": {...}},
                "big5": {"openness": 4.2, ...},
                "capacity": {"C_confidence": 3.5, ...},
            }
        """
        profile = BehavioralProfile(user_id=user_id)

        # 1. 阶段判定
        ttm7 = baps_results.get("ttm7", {})
        profile.current_stage = ttm7.get("current_stage", "S0")

        # 2. 心理层级判定
        spi = baps_results.get("spi", {})
        profile.spi_score = spi.get("spi_score", 0)
        profile.readiness_level = spi.get("level", "L1")

        # 3. 行为分型
        bpt6 = baps_results.get("bpt6", {})
        profile.bpt6_type = bpt6.get("dominant", "mixed")

        # 4. 交互模式
        profile.interaction_mode = self._determine_interaction_mode(
            profile.current_stage, profile.bpt6_type
        )

        # 5. CAPACITY分析
        capacity = baps_results.get("capacity", {})
        profile.self_efficacy = capacity.get("C_confidence", 0)
        weak_dims = self._find_weak_dimensions(capacity)
        profile.core_needs = self._map_needs_from_capacity(weak_dims)

        # 6. 动机/阻抗
        profile.motivation_level = spi.get("motivation", 0)
        profile.resistance_level = spi.get("resistance", 0)

        profile.updated_at = datetime.utcnow()
        return profile

    def update_from_device(self, profile: BehavioralProfile,
                            device_data: dict) -> BehavioralProfile:
        """设备数据触发的部分更新"""
        if "cgm_value" in device_data:
            profile.cgm_summary["latest"] = device_data["cgm_value"]
        if "hrv_sdnn" in device_data:
            profile.hrv_summary["latest_sdnn"] = device_data["hrv_sdnn"]
        if "steps" in device_data:
            profile.activity_summary["latest_steps"] = device_data["steps"]
        if "sleep_hours" in device_data:
            profile.activity_summary["latest_sleep"] = device_data["sleep_hours"]
        profile.updated_at = datetime.utcnow()
        return profile

    def update_from_tasks(self, profile: BehavioralProfile,
                           adherence: float, streak: int) -> BehavioralProfile:
        """任务依从性数据更新"""
        profile.adherence_score = adherence
        if adherence < 0.3 and streak == 0:
            profile.dropout_risk = True
        elif adherence >= 0.7:
            profile.dropout_risk = False
        profile.updated_at = datetime.utcnow()
        return profile

    # ── 内部方法 ──

    def _determine_interaction_mode(self, stage: str, bpt6_type: str) -> str:
        """§5.4 交互模式判定"""
        if stage in ("S0", "S1"):
            return "empathy"
        elif stage in ("S2", "S3"):
            if bpt6_type == "action":
                return "challenge"
            return "empathy"  # 非行动型在S2-S3仍用共情
        else:  # S4-S6
            return "execution"

    def _find_weak_dimensions(self, capacity: dict,
                               threshold: float = 3.0) -> list[str]:
        """找出CAPACITY中低于阈值的维度"""
        return [dim for dim, score in capacity.items()
                if isinstance(score, (int, float)) and score < threshold]

    def _map_needs_from_capacity(self, weak_dims: list[str]) -> list[str]:
        """§5.3 CAPACITY弱项→领域映射"""
        needs = set()
        for dim in weak_dims:
            domains = CAPACITY_TO_DOMAIN.get(dim, [])
            needs.update(domains)
        return sorted(needs)

    def get_communication_style(self, profile: BehavioralProfile) -> dict:
        """
        根据画像生成沟通风格建议

        来源: core/behavioral_profile_service.py (之前对话中生成的)
        """
        style = {
            "tone": "温暖支持",
            "approach": "渐进式",
            "emphasis": [],
            "avoid": [],
        }

        stage = profile.current_stage
        if stage in ("S0", "S1"):
            style["tone"] = "非评判、好奇"
            style["approach"] = "探索式"
            style["emphasis"] = ["倾听", "反映", "不施压"]
            style["avoid"] = ["直接建议", "说教", "数据轰炸"]
        elif stage == "S2":
            style["tone"] = "理解、同理"
            style["approach"] = "动机访谈"
            style["emphasis"] = ["探索矛盾", "激发思考"]
            style["avoid"] = ["急于给方案", "过度乐观"]
        elif stage == "S3":
            style["tone"] = "鼓励、务实"
            style["approach"] = "计划导向"
            style["emphasis"] = ["具体目标", "可行方案"]
            style["avoid"] = ["过高期望", "复杂计划"]
        elif stage in ("S4", "S5"):
            style["tone"] = "支持、赞赏"
            style["approach"] = "陪伴式"
            style["emphasis"] = ["庆祝进步", "问题解决", "持续反馈"]
            style["avoid"] = ["忽视困难", "过早撤离"]
        else:  # S6
            style["tone"] = "欣赏、预警"
            style["approach"] = "维护式"
            style["emphasis"] = ["身份强化", "复发预防"]
            style["avoid"] = ["过度放松", "忽视风险"]

        # BPT-6 补充
        bpt = profile.bpt6_type
        if bpt == "emotion":
            style["emphasis"].append("情绪认可")
            style["avoid"].append("纯理性说教")
        elif bpt == "knowledge":
            style["emphasis"].append("提供原理")
            style["avoid"].append("缺乏解释的指令")
        elif bpt == "relation":
            style["emphasis"].append("社群连接")
            style["avoid"].append("孤立式任务")

        return style


# 单例
behavioral_profile_service = BehavioralProfileService()
