# -*- coding: utf-8 -*-
"""
意图路由器

基于关键词匹配将用户查询路由到合适的专家 Agent
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

from .registry import AgentRegistry


@dataclass
class RoutingResult:
    """路由结果"""

    primary_agent: str                      # 主要处理专家 ID
    confidence: float                       # 置信度 (0-1)
    secondary_agents: List[str] = field(default_factory=list)  # 需要咨询的专家
    reasoning: str = ""                     # 路由原因说明
    scores: Dict[str, int] = field(default_factory=dict)  # 各专家得分


class IntentRouter:
    """意图路由器

    基于关键词匹配和跨领域触发器将用户查询路由到合适的专家
    """

    # 跨领域咨询触发关键词
    CONSULTATION_TRIGGERS: Dict[Tuple[str, str], List[str]] = {
        ("mental_health", "nutrition"): [
            "情绪化进食", "压力进食", "暴食", "厌食", "压力大想吃", "心情不好就想吃"
        ],
        ("mental_health", "sports_rehab"): [
            "运动焦虑", "运动成瘾", "身体形象", "不敢运动", "运动恐惧"
        ],
        ("nutrition", "tcm_wellness"): [
            "食疗", "药膳", "体质调理", "养生饮食", "食补"
        ],
        ("sports_rehab", "tcm_wellness"): [
            "穴位按摩", "运动后调理", "气功", "太极", "运动恢复"
        ],
        ("nutrition", "mental_health"): [
            "吃不下", "没胃口", "焦虑吃东西"
        ],
        ("sports_rehab", "mental_health"): [
            "运动受伤后情绪", "康复信心", "运动动力"
        ],
    }

    def __init__(self, registry: AgentRegistry, config: Dict = None):
        """初始化路由器

        Args:
            registry: Agent 注册表
            config: 配置字典（可选，用于获取默认专家）
        """
        self.registry = registry
        self.config = config or {}
        self._build_keyword_map()

    def _build_keyword_map(self):
        """从注册表构建关键词映射"""
        self.keyword_map: Dict[str, List[str]] = {}

        for agent_id in self.registry.list_agents():
            config = self.registry.get_config(agent_id)
            if config and config.keywords:
                self.keyword_map[agent_id] = config.keywords

    def route(self, query: str) -> RoutingResult:
        """将查询路由到合适的专家

        Args:
            query: 用户查询文本

        Returns:
            RoutingResult 对象
        """
        # 计算每个专家的得分
        scores = self._calculate_scores(query)

        # 确定主要专家
        primary, confidence = self._determine_primary(scores)

        # 检查是否需要跨专业咨询
        secondary = self._check_consultation_need(query, primary)

        # 生成路由原因
        reasoning = self._generate_reasoning(scores, primary, secondary)

        return RoutingResult(
            primary_agent=primary,
            confidence=confidence,
            secondary_agents=secondary,
            reasoning=reasoning,
            scores=scores
        )

    def _calculate_scores(self, query: str) -> Dict[str, int]:
        """计算各专家的匹配得分

        Args:
            query: 用户查询文本

        Returns:
            专家ID到得分的映射
        """
        scores = {}

        for agent_id, keywords in self.keyword_map.items():
            score = 0
            for keyword in keywords:
                if keyword in query:
                    # 关键词越长权重越高
                    score += len(keyword)
            scores[agent_id] = score

        return scores

    def _determine_primary(self, scores: Dict[str, int]) -> Tuple[str, float]:
        """确定主要处理专家

        Args:
            scores: 专家得分映射

        Returns:
            (专家ID, 置信度) 元组
        """
        max_score = max(scores.values()) if scores else 0

        if max_score == 0:
            # 无匹配，使用默认专家
            default = self.config.get("orchestrator", {}).get(
                "default_expert", "mental_health"
            )
            return default, 0.3

        # 找到得分最高的专家
        primary = max(scores, key=scores.get)

        # 计算置信度 (基于得分归一化)
        confidence = min(max_score / 10.0, 1.0)

        # 如果有多个专家得分相近，降低置信度
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) > 1 and sorted_scores[0] - sorted_scores[1] < 3:
            confidence *= 0.8

        return primary, round(confidence, 2)

    def _check_consultation_need(
        self,
        query: str,
        primary: str
    ) -> List[str]:
        """检查是否需要跨专业咨询

        Args:
            query: 用户查询文本
            primary: 主要专家 ID

        Returns:
            需要咨询的专家 ID 列表
        """
        secondary = []

        for (domain1, domain2), triggers in self.CONSULTATION_TRIGGERS.items():
            if primary not in (domain1, domain2):
                continue

            other = domain2 if primary == domain1 else domain1

            for trigger in triggers:
                if trigger in query:
                    if other not in secondary:
                        secondary.append(other)
                    break

        # 限制咨询数量
        max_consult = self.config.get("orchestrator", {}).get(
            "max_consultations", 2
        )
        return secondary[:max_consult]

    def _generate_reasoning(
        self,
        scores: Dict[str, int],
        primary: str,
        secondary: List[str]
    ) -> str:
        """生成路由原因说明

        Args:
            scores: 专家得分映射
            primary: 主要专家 ID
            secondary: 咨询专家列表

        Returns:
            路由原因说明文本
        """
        primary_config = self.registry.get_config(primary)
        primary_name = primary_config.name if primary_config else primary

        parts = [f"主要专家: {primary_name} (得分: {scores.get(primary, 0)})"]

        if secondary:
            secondary_names = []
            for agent_id in secondary:
                config = self.registry.get_config(agent_id)
                name = config.name if config else agent_id
                secondary_names.append(name)
            parts.append(f"咨询专家: {', '.join(secondary_names)}")

        # 添加得分详情
        score_details = ", ".join(
            f"{self.registry.get_config(k).name if self.registry.get_config(k) else k}: {v}"
            for k, v in sorted(scores.items(), key=lambda x: -x[1])
            if v > 0
        )
        if score_details:
            parts.append(f"得分详情: {score_details}")

        return " | ".join(parts)

    def refresh_keywords(self):
        """刷新关键词映射（当注册表更新后调用）"""
        self._build_keyword_map()
