# -*- coding: utf-8 -*-
"""
多专家协作协议

管理专家 Agent 之间的咨询和响应综合
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

from llama_index.llms.ollama import Ollama

from .registry import AgentRegistry


class ConsultationType(Enum):
    """咨询类型枚举"""
    SUPPLEMENT = "supplement"      # 补充建议
    VALIDATE = "validate"          # 验证确认
    CROSS_CHECK = "cross_check"    # 交叉检查


@dataclass
class ConsultationRequest:
    """咨询请求"""

    requester_id: str              # 请求咨询的专家 ID
    consultant_id: str             # 被咨询的专家 ID
    user_query: str                # 用户原始问题
    initial_analysis: str          # 请求方的初步分析
    consultation_type: ConsultationType = ConsultationType.SUPPLEMENT
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsultationResponse:
    """咨询响应"""

    consultant_id: str             # 咨询专家 ID
    consultant_name: str           # 咨询专家名称
    advice: str                    # 咨询建议
    confidence: float = 0.8        # 置信度
    warnings: List[str] = field(default_factory=list)  # 安全警告
    references: List[str] = field(default_factory=list)  # 参考来源


class CollaborationProtocol:
    """多专家协作协议

    管理专家之间的咨询流程和响应综合
    """

    def __init__(self, registry: AgentRegistry, config: Dict[str, Any]):
        """初始化协作协议

        Args:
            registry: Agent 注册表
            config: 全局配置
        """
        self.registry = registry
        self.config = config

        # 获取协作配置
        collab_config = config.get("collaboration", {})
        self.consultation_template = collab_config.get(
            "consultation_prompt_template",
            self._default_consultation_template()
        )
        self.synthesis_template = collab_config.get(
            "synthesis_prompt_template",
            self._default_synthesis_template()
        )

        # 初始化 LLM（用于响应综合）
        model_config = config.get("model", {})
        self.llm = Ollama(
            model=model_config.get("llm", "qwen2.5:14b"),
            base_url=model_config.get("ollama_base_url", "http://localhost:11434"),
            temperature=model_config.get("temperature", 0.3),
            request_timeout=model_config.get("request_timeout", 600.0)
        )

    def _default_consultation_template(self) -> str:
        """默认咨询提示模板"""
        return """你是{consultant_name}，正在被{requester_name}咨询。
用户原始问题：{user_query}
{requester_name}的初步分析：{initial_analysis}

请从你的专业角度提供补充建议，聚焦于：
1. 你专业领域相关的建议
2. 需要注意的跨学科协作点
3. 潜在的风险或注意事项

【重要】请用中文简洁回复，控制在200字以内。"""

    def _default_synthesis_template(self) -> str:
        """默认综合提示模板"""
        return """你是教练组的协调员，请综合以下专家意见为用户提供完整建议：

用户问题：{user_query}

专家意见：
{expert_responses}

请综合以上意见，提供：
1. 核心建议（最重要的2-3点）
2. 分步行动计划
3. 注意事项

【要求】使用中文，语气温和专业，避免评判性语言。"""

    def request_consultation(
        self,
        request: ConsultationRequest
    ) -> ConsultationResponse:
        """向另一位专家请求咨询

        Args:
            request: 咨询请求对象

        Returns:
            咨询响应对象
        """
        # 获取被咨询的专家
        consultant = self.registry.get(request.consultant_id)
        consultant_config = self.registry.get_config(request.consultant_id)
        requester_config = self.registry.get_config(request.requester_id)

        if not consultant or not consultant_config or not requester_config:
            return ConsultationResponse(
                consultant_id=request.consultant_id,
                consultant_name="未知专家",
                advice="无法获取该专家的意见",
                confidence=0.0
            )

        # 格式化咨询提示
        consultation_query = self.consultation_template.format(
            consultant_name=consultant_config.name,
            requester_name=requester_config.name,
            user_query=request.user_query,
            initial_analysis=request.initial_analysis
        )

        # 获取咨询响应
        try:
            response = consultant.chat(consultation_query)
            advice = response.response
            confidence = 0.8
        except Exception as e:
            advice = f"咨询时发生错误: {str(e)}"
            confidence = 0.0

        return ConsultationResponse(
            consultant_id=request.consultant_id,
            consultant_name=consultant_config.name,
            advice=advice,
            confidence=confidence,
            warnings=[],
            references=[]
        )

    def synthesize_responses(
        self,
        user_query: str,
        primary_response: str,
        primary_expert_name: str,
        consultation_responses: List[ConsultationResponse]
    ) -> str:
        """综合多位专家的响应

        Args:
            user_query: 用户原始问题
            primary_response: 主要专家的回复
            primary_expert_name: 主要专家名称
            consultation_responses: 咨询响应列表

        Returns:
            综合后的响应文本
        """
        # 如果没有咨询响应，直接返回主要响应
        if not consultation_responses:
            return primary_response

        # 格式化专家意见
        expert_responses_text = f"【{primary_expert_name}（主要专家）】\n{primary_response}\n\n"

        for resp in consultation_responses:
            expert_responses_text += f"【{resp.consultant_name}（咨询专家）】\n{resp.advice}\n\n"

        # 使用 LLM 进行综合
        synthesis_prompt = self.synthesis_template.format(
            user_query=user_query,
            expert_responses=expert_responses_text
        )

        # 添加语言强制指令
        final_prompt = (
            "【重要指令】你必须完全使用中文回复，严禁使用任何英文单词。\n\n"
            + synthesis_prompt
        )

        try:
            result = self.llm.complete(final_prompt)
            return result.text
        except Exception as e:
            # 如果综合失败，返回主要响应并附加咨询意见
            fallback = f"{primary_response}\n\n---\n\n"
            fallback += "【其他专家补充意见】\n"
            for resp in consultation_responses:
                fallback += f"\n{resp.consultant_name}：{resp.advice}\n"
            return fallback

    def check_safety_warnings(
        self,
        responses: List[ConsultationResponse]
    ) -> List[str]:
        """检查所有响应中的安全警告

        Args:
            responses: 咨询响应列表

        Returns:
            汇总的安全警告列表
        """
        warnings = []
        for resp in responses:
            warnings.extend(resp.warnings)
        return list(set(warnings))  # 去重
