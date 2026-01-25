# -*- coding: utf-8 -*-
from core.limiter import EfficacyLimiter
from protocols.wearable import calculate_efficacy_adjustment
from agents.orchestrator import AgentOrchestrator

# 模拟一个简单的内存数据库（实际生产环境建议用 Redis）
USER_SESSION_CACHE = {}

class OctopusWorkflow:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.base_efficacy = 35 
        self.orchestrator = AgentOrchestrator("config.yaml")

    def _get_heart_rate_trend(self, current_hr: int) -> float:
        """
        计算心率趋势逻辑：
        返回 > 0: 心率正在下降 (状态好转)
        返回 < 0: 心率正在上升 (压力增加)
        """
        if self.user_id not in USER_SESSION_CACHE:
            USER_SESSION_CACHE[self.user_id] = {"last_hr": current_hr}
            return 0.0
        
        last_hr = USER_SESSION_CACHE[self.user_id]["last_hr"]
        # 更新缓存供下一次对比
        USER_SESSION_CACHE[self.user_id]["last_hr"] = current_hr
        
        # 返回变化差值
        return last_hr - current_hr

    async def process_request(self, user_input: str, wearable_data: dict = None):
        # 1. Audit: 穿戴设备调节 + 趋势分析 (目标 2 进阶)
        current_hr = wearable_data.get("hr", 75) if wearable_data else 75
        hr_improvement = self._get_heart_rate_trend(current_hr)
        
        # 基础调节
        adjustment = calculate_efficacy_adjustment(wearable_data)
        
        # --- 多轮记忆奖励逻辑 ---
        # 如果心率下降超过 10 且当前处于正常水平，给予“效能奖励”
        trend_bonus = 0
        if hr_improvement >= 20: # 比如从 115 降到 80，差值 35
            trend_bonus = 15
            trend_msg = f"检测到心率显著下降 ({hr_improvement}bpm)，状态正在恢复，已动态调高建议难度。"
        else:
            trend_msg = "心率平稳。"

        current_score = max(5, self.base_efficacy + adjustment + trend_bonus)
        
        print(f"[Memory] {trend_msg} 当前效能分: {current_score}")

        # 2. Decompose: 专家检索
        expert_response = await self.orchestrator.dispatch(user_input)
        raw_tasks = expert_response.get("proposed_tasks", [])

        # 3. Constraint: 根据带“奖金”的评分进行限幅
        final_tasks = EfficacyLimiter.clamp(raw_tasks, current_score)
        
        return {
            "user_id": self.user_id,
            "status": "Success",
            "meta": {
                "current_hr": current_hr,
                "hr_improvement": hr_improvement,
                "calculated_efficacy": current_score,
                "trend_note": trend_msg
            },
            "data": { "tasks": final_tasks }
        }
