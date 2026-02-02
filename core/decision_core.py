import os
from typing import Dict
from loguru import logger
from core.decision_models import DecisionContext, DecisionOutput
from core.trigger_engine import get_trigger_engine
from core.dify_client import DifyClient


class DecisionCore:
    def __init__(self):
        self.trigger_engine = get_trigger_engine()
        self.dify_client = DifyClient(
            api_key=os.getenv("DIFY_API_KEY", "app-4tb6a3XAHj4NTKIa18oGYPYz"),
            base_url=os.getenv("DIFY_BASE_URL", "http://localhost:8080/v1"),
        )
        logger.info("DecisionCore (大脑) 已就绪")

    async def decide_intervention(self, context: DecisionContext) -> Dict:
        """决策逻辑：TriggerEngine 识别标签 → 命中 high_glucose 时调用 Dify 获取干预建议"""
        logger.info(f"正在为用户 {context.user_name} 进行决策分析...")

        # 1. 用 TriggerEngine 识别血糖 Triggers
        glucose_values = []
        if context.current_glucose:
            glucose_values = [context.current_glucose.value]
        triggers = self.trigger_engine.recognize_glucose_triggers(glucose_values)
        trigger_ids = [t.tag_id for t in triggers]

        # 2. 默认策略
        strategy = "默认平衡策略"
        content = f"你好 {context.user_name}，目前一切正常，请保持。"

        # 3. 命中 high_glucose → 调用 Dify 获取干预建议
        if "high_glucose" in trigger_ids:
            strategy = "高血糖即时干预"
            dify_response = await self.dify_client.generate_intervention(
                user_input=f"用户血糖值 {context.current_glucose.value} mmol/L，识别到高血糖触发标签，请给出干预建议。",
                user_id=str(context.user_id),
                context_data={
                    "glucose_value": context.current_glucose.value,
                    "trigger_tags": trigger_ids,
                    "user_name": context.user_name,
                },
            )
            content = dify_response.get("answer", "系统繁忙，请稍后再试。")
            logger.info(f"Dify 返回干预建议: {content[:80]}...")

        # 4. 封装为标准输出
        output = DecisionOutput(
            strategy_name=strategy,
            content=content,
            priority=5 if "高血糖" in strategy else 3,
            triggers_addressed=trigger_ids if trigger_ids else context.recent_triggers,
        )

        return output.dict()