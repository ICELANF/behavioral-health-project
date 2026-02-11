# -*- coding: utf-8 -*-
"""
L3 — 生成约束

- 为 LLM system prompt 注入安全指令
- 领域边界检查
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# 安全 system prompt 注入片段
SAFETY_SYSTEM_INJECTION = """
【安全约束 — 必须严格遵守】
1. 你不是医生, 不得直接诊断疾病或开具处方
2. 涉及药物、剂量、手术等医疗决策时, 必须引导用户咨询专业医生
3. 对于心理危机(自杀/自伤), 提供紧急热线信息并建议立即寻求专业帮助
4. 不得给出绝对化的健康承诺 (如"保证治愈", "100%有效")
5. 所有建议应以循证医学为基础, 标注信息来源可靠等级
6. 回复末尾应包含: "以上建议仅供参考, 具体请咨询您的主治医生"
"""

# 危机回复模板
CRISIS_RESPONSE_TEMPLATE = (
    "我注意到你可能正在经历非常困难的时刻。请记住, 你并不孤单。\n\n"
    "如果你需要帮助, 请拨打以下热线:\n"
    "- 全国心理援助热线: 400-161-9995\n"
    "- 北京心理危机研究与干预中心: 010-82951332\n"
    "- 生命热线: 400-821-1215\n\n"
    "请现在就联系专业人士, 他们能够提供你需要的支持。"
)


@dataclass
class GuardedPrompt:
    system_prompt: str
    constraints: list[str] = field(default_factory=list)
    is_crisis: bool = False
    domain_boundary: str = ""


class GenerationGuard:
    """L3 生成约束"""

    def guard(self,
              system_prompt: str,
              input_category: str = "normal",
              agent_domain: str = "",
              user_message: str = "") -> GuardedPrompt:
        """
        为 LLM 生成添加安全约束.

        Args:
            system_prompt: 原始 system prompt
            input_category: L1 输入过滤结果的 category
            agent_domain: 当前 Agent 的领域
            user_message: 用户原始消息 (用于领域边界检测)

        Returns:
            GuardedPrompt: 注入安全约束后的 prompt
        """
        constraints = []

        # 危机情况 — 直接返回危机模板
        if input_category == "crisis":
            return GuardedPrompt(
                system_prompt=system_prompt,
                constraints=["crisis_override"],
                is_crisis=True,
                domain_boundary=agent_domain,
            )

        # 医疗建议 — 加强医疗安全约束
        if input_category == "medical_advice":
            constraints.append("medical_safety")
            system_prompt = system_prompt + "\n" + SAFETY_SYSTEM_INJECTION
            system_prompt += "\n【额外医疗约束】不得推荐具体药品名称和剂量, 仅提供一般性生活方式建议。"

        else:
            # 常规 — 注入基础安全约束
            system_prompt = system_prompt + "\n" + SAFETY_SYSTEM_INJECTION
            constraints.append("base_safety")

        # 领域边界检测
        domain_boundary = ""
        if agent_domain:
            domain_boundary = agent_domain
            system_prompt += f"\n【领域边界】你当前的专业领域是「{agent_domain}」, 超出此领域的问题应建议用户咨询对应专业人士。"
            constraints.append("domain_boundary")

        return GuardedPrompt(
            system_prompt=system_prompt,
            constraints=constraints,
            is_crisis=False,
            domain_boundary=domain_boundary,
        )
