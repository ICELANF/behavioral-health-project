# -*- coding: utf-8 -*-
"""
业务逻辑服务层

封装任务分解、效能评估等核心业务逻辑
"""

import json
import re
from typing import List, Dict, Any, Optional

from llama_index.llms.ollama import Ollama

from .schemas import (
    AtomicTask,
    EfficacyScore,
    TaskCategory,
    TaskPriority,
    DifficultyLevel,
)


class TaskDecomposer:
    """任务分解器

    使用 LLM 将专家建议拆解为可执行的原子任务
    """

    DECOMPOSE_PROMPT = '''你是一个任务分解专家。请将以下健康建议拆解为具体可执行的原子任务。

【原始建议】
{advice_text}

【输出要求】
请输出JSON格式的任务列表，每个任务包含以下字段：
- title: 任务标题（简洁的动词短语，如"进行腹式呼吸练习"）
- description: 详细描述（具体步骤说明）
- category: 类别（mental_health/nutrition/exercise/tcm_wellness/lifestyle/medical）
- priority: 优先级（high/medium/low）
- difficulty: 难度（easy/moderate/hard）
- duration_minutes: 预计耗时（分钟数）
- frequency: 执行频率（如"每日一次"、"每周三次"）
- prerequisites: 前置条件列表
- notes: 注意事项

【效能评分要求】
{efficacy_instruction}

【约束条件】
1. 最多输出 {max_tasks} 个任务
2. 每个任务必须是具体可执行的行动
3. 优先输出高优先级、易执行的任务
4. 所有内容使用中文
5. 只输出JSON，不要其他内容

【输出格式示例】
```json
{{
    "tasks": [
        {{
            "title": "睡前腹式呼吸",
            "description": "躺在床上进行腹式呼吸：吸气4秒，屏息2秒，呼气6秒，重复10次",
            "category": "mental_health",
            "priority": "high",
            "difficulty": "easy",
            "duration_minutes": 10,
            "frequency": "每晚睡前",
            "prerequisites": ["安静的卧室"],
            "notes": "如感到头晕请停止",
            "efficacy": {{
                "effectiveness": 0.8,
                "feasibility": 0.95,
                "immediacy": 0.7,
                "sustainability": 0.85
            }}
        }}
    ]
}}
```

请开始分解：'''

    EFFICACY_INSTRUCTION_WITH = '''每个任务需要包含efficacy字段，评估：
- effectiveness: 有效性(0-1)，基于科学依据
- feasibility: 可行性(0-1)，考虑执行难度
- immediacy: 即时性(0-1)，见效速度
- sustainability: 可持续性(0-1)，长期坚持可能'''

    EFFICACY_INSTRUCTION_WITHOUT = '''不需要输出efficacy字段'''

    def __init__(self, config: Dict[str, Any]):
        """初始化分解器

        Args:
            config: 配置字典
        """
        model_config = config.get("model", {})

        self.llm = Ollama(
            model=model_config.get("llm", "qwen2.5:14b"),
            base_url=model_config.get("ollama_base_url", "http://localhost:11434"),
            temperature=0.2,  # 低温度保证输出稳定
            request_timeout=model_config.get("request_timeout", 600.0)
        )

    def decompose(
        self,
        advice_text: str,
        max_tasks: int = 10,
        include_efficacy: bool = True,
        user_context: Optional[Dict[str, Any]] = None
    ) -> List[AtomicTask]:
        """将建议文本分解为原子任务

        Args:
            advice_text: 需要分解的建议文本
            max_tasks: 最大任务数量
            include_efficacy: 是否包含效能评分
            user_context: 用户上下文（用于个性化）

        Returns:
            原子任务列表
        """
        # 构建提示
        efficacy_instruction = (
            self.EFFICACY_INSTRUCTION_WITH if include_efficacy
            else self.EFFICACY_INSTRUCTION_WITHOUT
        )

        prompt = self.DECOMPOSE_PROMPT.format(
            advice_text=advice_text,
            max_tasks=max_tasks,
            efficacy_instruction=efficacy_instruction
        )

        # 如果有用户上下文，添加到提示中
        if user_context:
            context_str = "\n".join(f"- {k}: {v}" for k, v in user_context.items())
            prompt += f"\n\n【用户信息】\n{context_str}"

        # 调用 LLM
        try:
            response = self.llm.complete(prompt)
            response_text = response.text
        except Exception as e:
            print(f"[TaskDecomposer] LLM调用失败: {e}")
            return []

        # 解析 JSON 响应
        tasks = self._parse_response(response_text, include_efficacy)

        return tasks[:max_tasks]

    def _parse_response(
        self,
        response_text: str,
        include_efficacy: bool
    ) -> List[AtomicTask]:
        """解析 LLM 响应

        Args:
            response_text: LLM 响应文本
            include_efficacy: 是否解析效能评分

        Returns:
            原子任务列表
        """
        # 提取 JSON 部分
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if not json_match:
            print(f"[TaskDecomposer] 无法提取JSON: {response_text[:200]}")
            return []

        try:
            data = json.loads(json_match.group())
        except json.JSONDecodeError as e:
            print(f"[TaskDecomposer] JSON解析失败: {e}")
            return []

        # 提取任务列表
        tasks_data = data.get("tasks", [])
        if not isinstance(tasks_data, list):
            tasks_data = [data] if "title" in data else []

        # 转换为 AtomicTask 对象
        tasks = []
        for task_data in tasks_data:
            try:
                task = self._convert_to_atomic_task(task_data, include_efficacy)
                if task:
                    tasks.append(task)
            except Exception as e:
                print(f"[TaskDecomposer] 任务转换失败: {e}")
                continue

        return tasks

    def _convert_to_atomic_task(
        self,
        data: Dict[str, Any],
        include_efficacy: bool
    ) -> Optional[AtomicTask]:
        """将字典转换为 AtomicTask

        Args:
            data: 任务数据字典
            include_efficacy: 是否包含效能评分

        Returns:
            AtomicTask 对象
        """
        # 必填字段检查
        title = data.get("title", "").strip()
        description = data.get("description", "").strip()

        if not title or not description:
            return None

        # 类别映射
        category_map = {
            "mental_health": TaskCategory.MENTAL_HEALTH,
            "nutrition": TaskCategory.NUTRITION,
            "exercise": TaskCategory.EXERCISE,
            "tcm_wellness": TaskCategory.TCM_WELLNESS,
            "lifestyle": TaskCategory.LIFESTYLE,
            "medical": TaskCategory.MEDICAL,
        }

        # 优先级映射
        priority_map = {
            "high": TaskPriority.HIGH,
            "medium": TaskPriority.MEDIUM,
            "low": TaskPriority.LOW,
        }

        # 难度映射
        difficulty_map = {
            "easy": DifficultyLevel.EASY,
            "moderate": DifficultyLevel.MODERATE,
            "hard": DifficultyLevel.HARD,
        }

        # 解析效能评分
        efficacy = None
        if include_efficacy and "efficacy" in data:
            eff_data = data["efficacy"]
            if isinstance(eff_data, dict):
                try:
                    efficacy = EfficacyScore(
                        effectiveness=float(eff_data.get("effectiveness", 0.5)),
                        feasibility=float(eff_data.get("feasibility", 0.5)),
                        immediacy=float(eff_data.get("immediacy", 0.5)),
                        sustainability=float(eff_data.get("sustainability", 0.5))
                    )
                except Exception:
                    pass

        # 构建任务对象
        return AtomicTask(
            title=title[:50],
            description=description[:200],
            category=category_map.get(
                data.get("category", "lifestyle"),
                TaskCategory.LIFESTYLE
            ),
            priority=priority_map.get(
                data.get("priority", "medium"),
                TaskPriority.MEDIUM
            ),
            difficulty=difficulty_map.get(
                data.get("difficulty", "easy"),
                DifficultyLevel.EASY
            ),
            duration_minutes=min(max(int(data.get("duration_minutes", 15)), 1), 480),
            frequency=data.get("frequency", "每日一次")[:30],
            prerequisites=data.get("prerequisites", [])[:5],
            efficacy=efficacy,
            expert_source=data.get("expert_source", ""),
            notes=data.get("notes", "")[:200]
        )


def calculate_average_efficacy(tasks: List[AtomicTask]) -> Optional[float]:
    """计算任务列表的平均效能评分

    Args:
        tasks: 任务列表

    Returns:
        平均效能评分，无评分时返回None
    """
    scores = [
        task.efficacy.overall
        for task in tasks
        if task.efficacy is not None
    ]

    if not scores:
        return None

    return round(sum(scores) / len(scores), 2)


def count_categories(tasks: List[AtomicTask]) -> Dict[str, int]:
    """统计各类别任务数量

    Args:
        tasks: 任务列表

    Returns:
        类别到数量的映射
    """
    counts: Dict[str, int] = {}

    for task in tasks:
        category = task.category.value
        counts[category] = counts.get(category, 0) + 1

    return counts
