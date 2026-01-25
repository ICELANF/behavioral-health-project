# -*- coding: utf-8 -*-
"""
八爪鱼限幅引擎 (Octopus Clamping Engine)

核心职责：
1. 根据用户效能感分值动态裁剪任务难度和数量
2. 记录完整推理路径 (reasoning_path)
3. 接收穿戴设备数据 (wearable_data) 进行动态调节
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class ClampingLevel(Enum):
    """限幅等级"""
    MINIMAL = "minimal"      # 最小干预：效能 < 20，仅返回1个最简任务
    MODERATE = "moderate"    # 中等干预：效能 20-50，返回2个中等任务
    FULL = "full"            # 完全干预：效能 > 50，返回全部任务


@dataclass
class ReasoningStep:
    """推理步骤记录"""
    phase: str                   # 阶段名称
    input_data: Dict[str, Any]   # 输入数据
    output_data: Dict[str, Any]  # 输出数据
    decision: str                # 决策说明
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ClampingResult:
    """限幅结果"""
    clamped_tasks: List[Dict[str, Any]]
    reasoning_path: List[Dict[str, Any]]
    final_efficacy: int
    clamping_level: str
    wearable_impact: Optional[Dict[str, Any]] = None


class OctopusClampingEngine:
    """
    八爪鱼限幅引擎

    执行效能感限幅算法，根据用户当前状态动态调节任务输出
    """

    # 限幅阈值配置
    CLAMPING_THRESHOLDS = {
        "minimal": {"max_score": 20, "max_tasks": 1, "max_difficulty": 1},
        "moderate": {"max_score": 50, "max_tasks": 2, "max_difficulty": 2},
        "full": {"max_score": 100, "max_tasks": 5, "max_difficulty": 5}
    }

    # 心率影响配置
    HR_IMPACT = {
        "high_stress": {"threshold": 100, "penalty": -20},
        "elevated": {"threshold": 85, "penalty": -10},
        "normal": {"threshold": 60, "penalty": 0},
        "relaxed": {"threshold": 50, "bonus": 5}
    }

    def __init__(self, user_id: str, base_efficacy: int = 50):
        self.user_id = user_id
        self.base_efficacy = base_efficacy
        self.current_efficacy = base_efficacy
        self.reasoning_path: List[ReasoningStep] = []
        self.wearable_data: Optional[Dict[str, Any]] = None

    def _add_reasoning_step(self, phase: str, input_data: Dict, output_data: Dict, decision: str):
        """添加推理步骤到路径"""
        step = ReasoningStep(
            phase=phase,
            input_data=input_data,
            output_data=output_data,
            decision=decision
        )
        self.reasoning_path.append(step)

    def _apply_wearable_adjustment(self, wearable_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """应用穿戴设备数据调节"""
        if not wearable_data:
            return {"applied": False, "adjustment": 0, "reason": "无穿戴数据"}

        hr = wearable_data.get("hr", 75)
        adjustment = 0
        reason = ""

        if hr >= self.HR_IMPACT["high_stress"]["threshold"]:
            adjustment = self.HR_IMPACT["high_stress"]["penalty"]
            reason = f"心率过高({hr}bpm)，触发高压保护，效能-20"
        elif hr >= self.HR_IMPACT["elevated"]["threshold"]:
            adjustment = self.HR_IMPACT["elevated"]["penalty"]
            reason = f"心率偏高({hr}bpm)，轻度降档，效能-10"
        elif hr <= self.HR_IMPACT["relaxed"]["threshold"]:
            adjustment = self.HR_IMPACT["relaxed"]["bonus"]
            reason = f"心率平稳({hr}bpm)，状态良好，效能+5"
        else:
            reason = f"心率正常({hr}bpm)，维持当前效能"

        return {"applied": True, "adjustment": adjustment, "reason": reason, "hr": hr}

    def _determine_clamping_level(self, efficacy: int) -> ClampingLevel:
        """确定限幅等级"""
        if efficacy < self.CLAMPING_THRESHOLDS["minimal"]["max_score"]:
            return ClampingLevel.MINIMAL
        elif efficacy < self.CLAMPING_THRESHOLDS["moderate"]["max_score"]:
            return ClampingLevel.MODERATE
        else:
            return ClampingLevel.FULL

    def _get_constraints(self, level: ClampingLevel) -> Dict[str, int]:
        """获取限幅约束条件"""
        level_key = level.value
        return {
            "max_tasks": self.CLAMPING_THRESHOLDS[level_key]["max_tasks"],
            "max_difficulty": self.CLAMPING_THRESHOLDS[level_key]["max_difficulty"]
        }

    def octopus_clamping(
        self,
        raw_tasks: List[Dict[str, Any]],
        wearable_data: Optional[Dict[str, Any]] = None
    ) -> ClampingResult:
        """
        执行八爪鱼限幅算法

        Args:
            raw_tasks: 原始任务列表，每个任务需包含 difficulty 字段
            wearable_data: 穿戴设备数据，可包含 hr(心率)、steps(步数)等

        Returns:
            ClampingResult: 包含限幅后任务和完整推理路径
        """
        self.reasoning_path = []  # 重置推理路径
        self.wearable_data = wearable_data

        # Phase 1: 穿戴设备数据处理
        wearable_impact = self._apply_wearable_adjustment(wearable_data)
        self._add_reasoning_step(
            phase="WEARABLE_AUDIT",
            input_data={"wearable_data": wearable_data, "base_efficacy": self.base_efficacy},
            output_data=wearable_impact,
            decision=wearable_impact["reason"]
        )

        # Phase 2: 计算最终效能分
        adjusted_efficacy = max(0, min(100, self.base_efficacy + wearable_impact["adjustment"]))
        self.current_efficacy = adjusted_efficacy
        self._add_reasoning_step(
            phase="EFFICACY_CALC",
            input_data={"base": self.base_efficacy, "adjustment": wearable_impact["adjustment"]},
            output_data={"final_efficacy": adjusted_efficacy},
            decision=f"效能分: {self.base_efficacy} + ({wearable_impact['adjustment']}) = {adjusted_efficacy}"
        )

        # Phase 3: 确定限幅等级
        clamping_level = self._determine_clamping_level(adjusted_efficacy)
        constraints = self._get_constraints(clamping_level)
        self._add_reasoning_step(
            phase="CLAMPING_LEVEL",
            input_data={"efficacy": adjusted_efficacy},
            output_data={"level": clamping_level.value, "constraints": constraints},
            decision=f"效能{adjusted_efficacy}分 -> {clamping_level.value}等级, 最多{constraints['max_tasks']}任务, 难度≤{constraints['max_difficulty']}"
        )

        # Phase 4: 执行限幅过滤
        filtered_tasks = [
            t for t in raw_tasks
            if t.get("difficulty", 1) <= constraints["max_difficulty"]
        ]
        clamped_tasks = filtered_tasks[:constraints["max_tasks"]]

        self._add_reasoning_step(
            phase="TASK_FILTER",
            input_data={"raw_count": len(raw_tasks), "raw_tasks": raw_tasks},
            output_data={"filtered_count": len(clamped_tasks), "clamped_tasks": clamped_tasks},
            decision=f"从{len(raw_tasks)}个任务中筛选出{len(clamped_tasks)}个符合条件的任务"
        )

        # 构建推理路径（转换为可序列化格式）
        reasoning_path_serializable = [
            {
                "phase": step.phase,
                "input": step.input_data,
                "output": step.output_data,
                "decision": step.decision,
                "timestamp": step.timestamp.isoformat()
            }
            for step in self.reasoning_path
        ]

        return ClampingResult(
            clamped_tasks=clamped_tasks,
            reasoning_path=reasoning_path_serializable,
            final_efficacy=adjusted_efficacy,
            clamping_level=clamping_level.value,
            wearable_impact=wearable_impact if wearable_impact["applied"] else None
        )

    def set_base_efficacy(self, score: int):
        """设置基础效能分"""
        self.base_efficacy = max(0, min(100, score))
        self.current_efficacy = self.base_efficacy


# 单例工厂函数
_engine_cache: Dict[str, OctopusClampingEngine] = {}

def get_clamping_engine(user_id: str, efficacy_score: int = 50) -> OctopusClampingEngine:
    """获取或创建用户的限幅引擎实例"""
    if user_id not in _engine_cache:
        _engine_cache[user_id] = OctopusClampingEngine(user_id, efficacy_score)
    else:
        _engine_cache[user_id].set_base_efficacy(efficacy_score)
    return _engine_cache[user_id]


# 本地测试
if __name__ == "__main__":
    # 模拟效能分为 10 的用户
    engine = OctopusClampingEngine(user_id="test_user", base_efficacy=10)

    # 模拟原始任务列表
    raw_tasks = [
        {"id": 1, "content": "深度冥想20分钟", "difficulty": 4, "type": "mental"},
        {"id": 2, "content": "记录一次情绪日志", "difficulty": 2, "type": "mental"},
        {"id": 3, "content": "进行3次深呼吸", "difficulty": 1, "type": "mental"}
    ]

    # 执行限幅
    result = engine.octopus_clamping(raw_tasks, wearable_data={"hr": 95})

    print("=" * 50)
    print("八爪鱼限幅引擎测试结果")
    print("=" * 50)
    print(f"最终效能分: {result.final_efficacy}")
    print(f"限幅等级: {result.clamping_level}")
    print(f"输出任务数: {len(result.clamped_tasks)}")
    print(f"\n限幅后任务:")
    for task in result.clamped_tasks:
        print(f"  - [{task['difficulty']}] {task['content']}")
    print(f"\n推理路径:")
    for step in result.reasoning_path:
        print(f"  [{step['phase']}] {step['decision']}")
