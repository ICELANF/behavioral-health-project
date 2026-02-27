"""
core.intervention — 干预计划生成模块

从 V0 MasterAgent (6874行) 中提取的独立模块
"""
from .action_plan import create_action_plan
from .daily_briefing import generate_daily_briefing

__all__ = ["create_action_plan", "generate_daily_briefing"]
