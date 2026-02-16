"""
中医骨科康复 — 安全红线规则引擎

4级安全体系:
  L1 紧急就医: 红旗症状 → 中断对话 → crisis_responder
  L2 建议就医: 高风险信号 → 提示就医 + 通知教练
  L3 边界约束: 超范围请求 → 免责声明 + 科普引导
  L4 特殊人群: 禁忌人群 → 嵌入禁忌列表 + 强制医师确认
"""
from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional

logger = logging.getLogger(__name__)


class SafetyLevel(IntEnum):
    """安全级别, 数值越小越严重"""
    L1_EMERGENCY = 1
    L2_REFER = 2
    L3_BOUNDARY = 3
    L4_SPECIAL_POP = 4
    SAFE = 99


@dataclass
class SafetyCheckResult:
    """安全检查结果"""
    level: SafetyLevel
    triggered_rules: list[str] = field(default_factory=list)
    response_template: str = ""
    should_halt: bool = False
    notify_coach: bool = False
    refer_department: str = ""
    contraindications: list[str] = field(default_factory=list)


# ──────────────────────────────────────────────
# L1 红旗症状关键词 (立即就医/拨打120)
# ──────────────────────────────────────────────
RED_FLAG_PATTERNS: list[tuple[str, str]] = [
    # (正则模式, 规则描述)
    (r"剧烈头痛.{0,10}(意识|昏迷|呕吐|视力)", "剧烈头痛伴意识/神经症状"),
    (r"(意识模糊|意识丧失|昏迷|抽搐)", "意识障碍"),
    (r"胸痛.{0,10}(呼吸困难|气短|大汗|放射)", "胸痛伴心血管症状"),
    (r"((肢体|腿|手臂|上肢|下肢)?突发无力|突然麻木|半身不遂|口角歪斜)", "疑似卒中"),
    (r"(外伤|摔倒|摔伤).{0,15}(骨折|畸形|变形|开放性|出血不止)", "严重外伤/疑似骨折"),
    (r"(马尾综合征|鞍区麻木|大小便失禁|括约肌)", "马尾综合征"),
    (r"脊髓.{0,10}(损伤|压迫|截瘫|四肢瘫)", "脊髓损伤"),
    (r"(高处坠落|车祸|重物砸伤).{0,15}(脊柱|颈椎|腰椎)", "高能量外伤"),
    (r"(呼吸困难|窒息|无法呼吸)", "呼吸困难"),
    (r"(大量出血|止不住血|动脉出血)", "大出血"),
    (r"关节.{0,10}(脱位|弹响后无法活动|锁死)", "关节脱位/交锁"),
    (r"(开放性伤口|骨头外露|伤口可见骨)", "开放性骨折"),
]

# ──────────────────────────────────────────────
# L2 高风险信号 (强烈建议就医)
# ──────────────────────────────────────────────
HIGH_RISK_PATTERNS: list[tuple[str, str, str]] = [
    # (正则模式, 规则描述, 建议科室)
    (r"(VAS|NRS|疼痛评分).{0,10}([89]|10)分?.{0,10}(持续|超过)", "剧烈疼痛持续", "疼痛科/骨科"),
    (r"夜间痛.{0,10}(影响睡眠|无法入睡).{0,10}(超过|两|2).{0,5}周", "夜间痛>2周", "骨科/肿瘤科"),
    (r"(不明原因|无外伤).{0,10}体重(下降|减轻)", "不明原因体重下降", "骨科/肿瘤科"),
    (r"发(热|烧).{0,10}(关节|脊柱|骨).{0,10}(疼痛|肿)", "发热伴骨关节痛", "骨科/感染科"),
    (r"疼痛.{0,10}(进行性|逐渐|越来越).{0,5}加重", "进行性疼痛加重", "骨科"),
    (r"(下肢|腿|脚).{0,10}(放射痛|串痛|麻木).{0,10}(加重|无力)", "神经根症状加重", "脊柱科/神经外科"),
    (r"(外伤|摔倒).{0,10}(48|72|两天|三天).{0,10}(肿胀加重|不能活动)", "外伤后持续加重", "急诊/骨科"),
    (r"(长期|超过3个月|慢性).{0,10}(服用|吃).{0,10}(止痛药|布洛芬|芬必得)", "长期NSAID使用", "疼痛科"),
    (r"(关节红肿热痛|痛风发作|急性痛风)", "急性关节炎", "风湿免疫科/骨科"),
    (r"(骨质疏松|T值).{0,10}(-2\.5|严重)", "严重骨质疏松", "骨科/内分泌科"),
]

# ──────────────────────────────────────────────
# L3 边界约束关键词 (超出平台范围)
# ──────────────────────────────────────────────
BOUNDARY_PATTERNS: list[tuple[str, str]] = [
    (r"(开.{0,3}处方|开.{0,3}药方|开.{0,3}中药|处方.{0,3}药)", "要求开具处方"),
    (r"(诊断.{0,3}是什么|确诊|明确诊断|是不是得了)", "要求明确诊断"),
    (r"(手术.{0,5}(选择|方案|好不好)|要不要做手术|微创还是开放)", "咨询手术方案"),
    (r"(封闭.{0,3}注射|针刀|银质针|射频消融)", "侵入性操作"),
    (r"(阿片|吗啡|曲马多|芬太尼|杜冷丁)", "阿片类药物"),
    (r"(要不要拍片|需要CT|需要MRI|核磁共振)", "影像检查建议"),
]

# ──────────────────────────────────────────────
# L4 特殊人群标签 → 禁忌列表
# ──────────────────────────────────────────────
SPECIAL_POPULATION_TAGS = {
    "pregnant": {
        "keywords": [r"(怀孕|孕妇|妊娠|备孕|哺乳)"],
        "contraindicated_acupoints": [
            "合谷", "三阴交", "昆仑", "至阴", "肩井",
            "缺盆", "气冲", "石门", "天枢(深刺)"
        ],
        "contraindicated_methods": [
            "腰骶部推拿", "腹部手法", "强刺激手法",
            "活血化瘀类外用药", "含麝香制剂"
        ],
        "refer_note": "孕妇骨科问题请优先就诊产科+骨科联合门诊"
    },
    "child": {
        "keywords": [r"(儿童|小孩|孩子|未成年|(\d{1,2})岁.{0,5}(小朋友|孩子))"],
        "contraindicated_methods": [
            "正骨手法(骨骺未闭合)", "强力牵引",
            "成人剂量外用药", "重手法推拿"
        ],
        "refer_note": "儿童骨科问题请就诊小儿骨科专科"
    },
    "osteoporosis_severe": {
        "keywords": [r"(严重骨质疏松|T值.{0,5}-2\.5|骨密度.{0,5}(很低|极低))"],
        "contraindicated_methods": [
            "脊柱正骨手法", "暴力推拿", "拍打法",
            "重力牵引", "高冲击运动"
        ],
        "refer_note": "严重骨质疏松需内分泌科评估后再行康复"
    },
    "tumor": {
        "keywords": [r"(肿瘤|癌症|恶性|骨转移|病理性骨折)"],
        "contraindicated_methods": [
            "局部推拿按摩", "热敷(肿瘤部位)", "正骨手法",
            "一切物理刺激(肿瘤区域)"
        ],
        "refer_note": "肿瘤相关骨痛请就诊肿瘤科/疼痛科"
    },
    "coagulation_disorder": {
        "keywords": [r"(血友病|凝血障碍|抗凝药|华法林|利伐沙班|长期服用阿司匹林)"],
        "contraindicated_methods": [
            "刮痧", "拔罐(强力)", "针刺(深刺)",
            "暴力推拿", "可能引起出血的手法"
        ],
        "refer_note": "凝血功能异常者需血液科评估后指导康复"
    },
}


# ──────────────────────────────────────────────
# 安全响应模板
# ──────────────────────────────────────────────
RESPONSE_TEMPLATES = {
    SafetyLevel.L1_EMERGENCY: (
        "⚠️ 紧急提醒：根据您描述的症状（{symptoms}），"
        "这可能是需要紧急处理的情况。\n\n"
        "🚨 请立即拨打 120 或前往最近的急诊科就诊。\n"
        "在等待期间请保持静卧，不要随意移动受伤部位。\n\n"
        "您的健康教练已收到通知，会尽快跟进。"
    ),
    SafetyLevel.L2_REFER: (
        "🏥 就医建议：根据您描述的情况（{symptoms}），"
        "建议您尽快前往 {department} 就诊。\n\n"
        "📋 就诊参考摘要：\n{summary}\n\n"
        "以上信息仅供参考，不构成医疗诊断。"
        "您的健康教练已收到通知。"
    ),
    SafetyLevel.L3_BOUNDARY: (
        "📌 温馨提示：{reason}\n\n"
        "行健平台定位为健康管理服务，{scope_note}\n\n"
        "关于您的问题，以下科普信息供参考：\n{info}\n\n"
        "⚕️ 免责声明：以上内容仅为健康科普，不构成医疗建议或诊断。"
        "具体诊疗方案请以医疗机构专业医师意见为准。"
    ),
    SafetyLevel.L4_SPECIAL_POP: (
        "⚠️ 特殊人群提醒：检测到您可能属于 {population} 人群。\n\n"
        "以下操作/穴位对您可能存在禁忌：\n{contraindications}\n\n"
        "建议：{refer_note}\n\n"
        "本方案已标注特殊人群禁忌，请在专业医师指导下实施。"
    ),
}


class OrthoSafetyGate:
    """骨科康复安全门 — 所有骨科Agent输出前必须经过此检查"""

    def __init__(self):
        self._compiled_red_flags = [
            (re.compile(p, re.IGNORECASE), desc)
            for p, desc in RED_FLAG_PATTERNS
        ]
        self._compiled_high_risk = [
            (re.compile(p, re.IGNORECASE), desc, dept)
            for p, desc, dept in HIGH_RISK_PATTERNS
        ]
        self._compiled_boundary = [
            (re.compile(p, re.IGNORECASE), desc)
            for p, desc in BOUNDARY_PATTERNS
        ]
        self._compiled_special_pop = {}
        for tag, config in SPECIAL_POPULATION_TAGS.items():
            patterns = [
                re.compile(kw, re.IGNORECASE) for kw in config["keywords"]
            ]
            self._compiled_special_pop[tag] = (patterns, config)

    def check(
        self,
        user_message: str,
        user_tags: Optional[list[str]] = None,
        pain_score: Optional[int] = None,
    ) -> SafetyCheckResult:
        """
        对用户消息执行安全检查, 返回最高级别的触发结果

        Args:
            user_message: 用户输入文本
            user_tags: 用户画像标签 (如 ["pregnant", "osteoporosis_severe"])
            pain_score: 当前疼痛评分 (0-10), 如果有的话

        Returns:
            SafetyCheckResult
        """
        user_tags = user_tags or []
        results: list[SafetyCheckResult] = []

        # === L1: 红旗症状检查 ===
        l1_triggers = []
        for pattern, desc in self._compiled_red_flags:
            if pattern.search(user_message):
                l1_triggers.append(desc)
        if l1_triggers:
            results.append(SafetyCheckResult(
                level=SafetyLevel.L1_EMERGENCY,
                triggered_rules=l1_triggers,
                should_halt=True,
                notify_coach=True,
                response_template=RESPONSE_TEMPLATES[SafetyLevel.L1_EMERGENCY].format(
                    symptoms="、".join(l1_triggers)
                ),
            ))

        # === L2: 高风险信号检查 ===
        l2_triggers = []
        departments = set()
        for pattern, desc, dept in self._compiled_high_risk:
            if pattern.search(user_message):
                l2_triggers.append(desc)
                departments.add(dept)
        # 疼痛评分触发
        if pain_score is not None and pain_score >= 8:
            l2_triggers.append(f"疼痛评分{pain_score}/10")
            departments.add("疼痛科/骨科")
        if l2_triggers:
            results.append(SafetyCheckResult(
                level=SafetyLevel.L2_REFER,
                triggered_rules=l2_triggers,
                notify_coach=True,
                refer_department="、".join(departments),
                response_template=RESPONSE_TEMPLATES[SafetyLevel.L2_REFER].format(
                    symptoms="、".join(l2_triggers),
                    department="、".join(departments),
                    summary="（由Agent生成症状摘要）",
                ),
            ))

        # === L3: 边界约束检查 ===
        l3_triggers = []
        for pattern, desc in self._compiled_boundary:
            if pattern.search(user_message):
                l3_triggers.append(desc)
        if l3_triggers:
            results.append(SafetyCheckResult(
                level=SafetyLevel.L3_BOUNDARY,
                triggered_rules=l3_triggers,
                response_template=RESPONSE_TEMPLATES[SafetyLevel.L3_BOUNDARY].format(
                    reason="、".join(l3_triggers),
                    scope_note="不提供处方、诊断、手术建议等医疗行为。",
                    info="（由Agent生成相关科普内容）",
                ),
            ))

        # === L4: 特殊人群检查 ===
        # 从用户标签检查
        for tag in user_tags:
            if tag in SPECIAL_POPULATION_TAGS:
                config = SPECIAL_POPULATION_TAGS[tag]
                contras = (
                    config.get("contraindicated_acupoints", [])
                    + config.get("contraindicated_methods", [])
                )
                results.append(SafetyCheckResult(
                    level=SafetyLevel.L4_SPECIAL_POP,
                    triggered_rules=[f"用户标签:{tag}"],
                    contraindications=contras,
                    response_template=RESPONSE_TEMPLATES[SafetyLevel.L4_SPECIAL_POP].format(
                        population=tag,
                        contraindications="\n".join(f"  ❌ {c}" for c in contras),
                        refer_note=config.get("refer_note", "请咨询专业医师"),
                    ),
                ))

        # 从消息文本检查
        for tag, (patterns, config) in self._compiled_special_pop.items():
            if tag in user_tags:
                continue  # 已通过标签触发, 避免重复
            for p in patterns:
                if p.search(user_message):
                    contras = (
                        config.get("contraindicated_acupoints", [])
                        + config.get("contraindicated_methods", [])
                    )
                    results.append(SafetyCheckResult(
                        level=SafetyLevel.L4_SPECIAL_POP,
                        triggered_rules=[f"文本检测:{tag}"],
                        contraindications=contras,
                        response_template=RESPONSE_TEMPLATES[SafetyLevel.L4_SPECIAL_POP].format(
                            population=tag,
                            contraindications="\n".join(f"  ❌ {c}" for c in contras),
                            refer_note=config.get("refer_note", "请咨询专业医师"),
                        ),
                    ))
                    break

        # 返回最高优先级的结果, 如果没有触发则返回SAFE
        if not results:
            return SafetyCheckResult(level=SafetyLevel.SAFE)

        results.sort(key=lambda r: r.level)
        highest = results[0]
        # 合并所有触发的规则到最高级别结果
        all_rules = []
        for r in results:
            all_rules.extend(r.triggered_rules)
        highest.triggered_rules = all_rules
        return highest


# 全局单例
_safety_gate: Optional[OrthoSafetyGate] = None


def get_ortho_safety_gate() -> OrthoSafetyGate:
    """获取骨科安全门单例"""
    global _safety_gate
    if _safety_gate is None:
        _safety_gate = OrthoSafetyGate()
    return _safety_gate
