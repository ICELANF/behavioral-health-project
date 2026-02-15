# -*- coding: utf-8 -*-
"""
tcm_integration.py — 中西医融合干预协议引擎

将中医体质辨识与现代行为科学深度融合，生成结构化的融合干预方案:
  - 融合干预 = 中医体质调养 + TTM 行为改变策略
  - integrat_TCM: 整合中医体质到行为干预流程
  - 体质_行为 映射: 9种体质 × TTM阶段 → 个性化方案
  - constitution_behavior 矩阵: 体质特征与行为模式关联
  - 中西结合 协议: 标准化的融合干预步骤

九种中医体质:
  平和质(A) | 气虚质(B) | 阳虚质(C) | 阴虚质(D) | 痰湿质(E)
  湿热质(F) | 血瘀质(G) | 气郁质(H) | 特禀质(I)
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# 体质-行为映射矩阵 (constitution_behavior matrix)
# ══════════════════════════════════════════════════════════════

constitution_behavior_matrix: Dict[str, Dict[str, Any]] = {
    "A_balanced": {
        "name": "平和质",
        "behavior_tendency": "适应力强，行为改变阻力低",
        "exercise_preference": ["中等强度有氧", "太极拳", "八段锦"],
        "nutrition_focus": ["均衡膳食", "五谷杂粮"],
        "sleep_advice": "保持规律作息",
        "emotion_style": "情绪稳定，正念冥想维持",
        "ttm_acceleration": 1.0,
    },
    "B_qi_deficiency": {
        "name": "气虚质",
        "behavior_tendency": "易疲劳，行为启动困难",
        "exercise_preference": ["低强度散步", "站桩", "八段锦"],
        "nutrition_focus": ["补气食材(黄芪/党参)", "山药", "红枣"],
        "sleep_advice": "午休30分钟，晚间早睡",
        "emotion_style": "容易气馁，需频繁正向激励",
        "ttm_acceleration": 0.7,
    },
    "C_yang_deficiency": {
        "name": "阳虚质",
        "behavior_tendency": "畏寒怕冷，冬季行为退化风险高",
        "exercise_preference": ["温和运动", "室内瑜伽", "艾灸操"],
        "nutrition_focus": ["温补食材(生姜/肉桂)", "羊肉", "核桃"],
        "sleep_advice": "睡前泡脚，温水足浴",
        "emotion_style": "内向退缩，需温和鼓励",
        "ttm_acceleration": 0.6,
    },
    "D_yin_deficiency": {
        "name": "阴虚质",
        "behavior_tendency": "急躁易怒，行为坚持期容易中断",
        "exercise_preference": ["游泳", "太极", "慢跑"],
        "nutrition_focus": ["滋阴食材(百合/银耳)", "梨", "莲子"],
        "sleep_advice": "睡前安神，避免过度兴奋",
        "emotion_style": "情绪波动大，需情绪管理干预",
        "ttm_acceleration": 0.8,
    },
    "E_phlegm_dampness": {
        "name": "痰湿质",
        "behavior_tendency": "体型偏胖，运动意愿低，代谢综合征高风险",
        "exercise_preference": ["有氧运动", "快走", "游泳"],
        "nutrition_focus": ["祛湿食材(薏仁/冬瓜)", "低糖低脂", "控制碳水"],
        "sleep_advice": "避免湿重环境，控制睡前进食",
        "emotion_style": "迟钝淡漠，需激发内在动机",
        "ttm_acceleration": 0.65,
    },
    "F_damp_heat": {
        "name": "湿热质",
        "behavior_tendency": "易怒冲动，行为模式波动大",
        "exercise_preference": ["中强度运动", "游泳", "球类"],
        "nutrition_focus": ["清热食材(绿豆/苦瓜)", "少油少辣", "控酒"],
        "sleep_advice": "保持通风，轻薄被褥",
        "emotion_style": "暴躁型，需冷静期后沟通",
        "ttm_acceleration": 0.75,
    },
    "G_blood_stasis": {
        "name": "血瘀质",
        "behavior_tendency": "肤色晦暗，循环差，运动后恢复慢",
        "exercise_preference": ["活血运动", "散步", "太极", "推拿操"],
        "nutrition_focus": ["活血食材(山楂/玫瑰花)", "醋", "黑木耳"],
        "sleep_advice": "规律运动促循环，睡前轻柔拉伸",
        "emotion_style": "容易抑郁消沉，需社交支持",
        "ttm_acceleration": 0.7,
    },
    "H_qi_stagnation": {
        "name": "气郁质",
        "behavior_tendency": "情绪敏感，社交退缩，行为改变受情绪影响大",
        "exercise_preference": ["户外运动", "团体运动", "瑜伽"],
        "nutrition_focus": ["疏肝食材(玫瑰/佛手)", "柑橘", "薄荷"],
        "sleep_advice": "睡前放松训练，避免思虑过度",
        "emotion_style": "高敏感型，需共情式教练沟通",
        "ttm_acceleration": 0.6,
    },
    "I_special": {
        "name": "特禀质",
        "behavior_tendency": "过敏体质，行为方案需避开过敏原",
        "exercise_preference": ["低过敏环境运动", "室内", "清晨户外"],
        "nutrition_focus": ["避免过敏食材", "清淡为主", "益生菌"],
        "sleep_advice": "清洁卧室环境，防尘螨",
        "emotion_style": "敏感脆弱，需安全感建设",
        "ttm_acceleration": 0.7,
    },
}


@dataclass
class IntegratedTCMProtocol:
    """中西结合融合干预协议"""
    protocol_id: str
    user_id: str
    constitution_type: str    # 中医体质类型
    ttm_stage: str            # TTM 行为改变阶段
    # 融合干预方案
    tcm_regimen: Dict[str, Any] = field(default_factory=dict)
    behavior_plan: Dict[str, Any] = field(default_factory=dict)
    integrated_actions: List[Dict[str, str]] = field(default_factory=list)
    constitution_behavior_score: float = 0  # 体质-行为适配度


def generate_integrated_tcm_protocol(
    user_id: str,
    constitution_type: str,
    ttm_stage: str,
    health_goals: List[str] = None,
) -> IntegratedTCMProtocol:
    """生成中西结合融合干预协议

    融合干预 = 体质调养方案 + 行为改变策略
    integrat_TCM into behavioral intervention pipeline
    """
    import uuid
    matrix = constitution_behavior_matrix.get(constitution_type, constitution_behavior_matrix["A_balanced"])

    # 体质_行为 适配度计算
    acceleration = matrix.get("ttm_acceleration", 0.7)
    constitution_behavior_score = acceleration * 100

    protocol = IntegratedTCMProtocol(
        protocol_id=f"TCM-{uuid.uuid4().hex[:8]}",
        user_id=user_id,
        constitution_type=constitution_type,
        ttm_stage=ttm_stage,
        tcm_regimen={
            "constitution": matrix["name"],
            "nutrition": matrix["nutrition_focus"],
            "exercise": matrix["exercise_preference"],
            "sleep": matrix["sleep_advice"],
            "emotion": matrix["emotion_style"],
        },
        behavior_plan={
            "stage": ttm_stage,
            "acceleration_factor": acceleration,
            "coach_style": matrix["emotion_style"],
        },
        integrated_actions=[
            {"type": "nutrition", "tcm": matrix["nutrition_focus"][0],
             "behavior": f"每日记录饮食 ({ttm_stage} 难度)"},
            {"type": "exercise", "tcm": matrix["exercise_preference"][0],
             "behavior": f"每周运动计划 ({ttm_stage} 强度)"},
            {"type": "sleep", "tcm": matrix["sleep_advice"],
             "behavior": "睡眠日志记录"},
        ],
        constitution_behavior_score=constitution_behavior_score,
    )

    logger.info(
        "融合干预协议生成: user=%s, constitution=%s, stage=%s, score=%.1f",
        user_id, matrix["name"], ttm_stage, constitution_behavior_score,
    )
    return protocol


def get_constitution_behavior_mapping(constitution_type: str) -> Dict[str, Any]:
    """获取体质-行为映射 (constitution_behavior mapping)"""
    return constitution_behavior_matrix.get(constitution_type, {})
