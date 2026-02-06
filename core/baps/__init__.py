# -*- coding: utf-8 -*-
"""
行为评估系统与处方 (Behavior Assessment & Prescription System, BAPS)
行健行为教练核心评估引擎

版本: v1.0
更新: 2026-01-24
"""

from .questionnaires import (
    BigFiveQuestionnaire,
    BPT6Questionnaire,
    CAPACITYQuestionnaire,
    SPIQuestionnaire,
    TTM7Questionnaire
)
from .scoring_engine import BAPSScoringEngine
from .report_generator import BAPSReportGenerator

__version__ = "1.0.0"
__all__ = [
    "BigFiveQuestionnaire",
    "BPT6Questionnaire",
    "CAPACITYQuestionnaire",
    "SPIQuestionnaire",
    "TTM7Questionnaire",
    "BAPSScoringEngine",
    "BAPSReportGenerator"
]
