# -*- coding: utf-8 -*-
"""
高频题目服务
High-Frequency Question Service

从配置文件加载高频题目预设，提供题目查询和部分答案评分
"""
import os
import json
from typing import Dict, List, Optional, Any
from loguru import logger


class HighFreqQuestionService:
    """高频题目查询 + 部分评分服务"""

    def __init__(self):
        self._presets = None
        self._question_map = None  # id -> {questionnaire, dimension, text, scale_type, scale_range, scale_labels}

    def _load_config(self):
        """懒加载配置"""
        if self._presets is not None:
            return

        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "configs", "assessment", "high_freq_questions.json"
        )
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._presets = data.get("presets", {})

    def _build_question_map(self):
        """构建题目 ID → 完整信息映射"""
        if self._question_map is not None:
            return

        from core.baps.questionnaires import (
            TTM7Questionnaire, BigFiveQuestionnaire,
            BPT6Questionnaire, CAPACITYQuestionnaire, SPIQuestionnaire
        )

        self._question_map = {}
        questionnaires = {
            "ttm7": TTM7Questionnaire(),
            "big_five": BigFiveQuestionnaire(),
            "bpt6": BPT6Questionnaire(),
            "capacity": CAPACITYQuestionnaire(),
            "spi": SPIQuestionnaire(),
        }

        for q_key, q_inst in questionnaires.items():
            scale_labels = {str(k): v for k, v in q_inst.scale.labels.items()} if q_inst.scale else {}
            for item in q_inst.items:
                self._question_map[item.id] = {
                    "id": item.id,
                    "questionnaire": q_key,
                    "dimension": item.dimension,
                    "text": item.text,
                    "reverse": item.reverse,
                    "scale_type": q_inst.scale.type if q_inst.scale else "likert",
                    "scale_range": list(q_inst.scale.range) if q_inst.scale else [1, 5],
                    "scale_labels": scale_labels,
                }

    def get_presets(self) -> List[Dict[str, Any]]:
        """列出可用预设"""
        self._load_config()
        result = []
        for key, preset in self._presets.items():
            result.append({
                "key": key,
                "name": preset["name"],
                "description": preset.get("description", ""),
                "estimated_minutes": preset.get("estimated_minutes", 0),
                "item_count": len(preset.get("items", [])),
            })
        return result

    def get_preset_items(self, preset: str = "hf20") -> List[Dict[str, Any]]:
        """
        获取某预设的完整题目列表（含题目文本+选项）

        Returns:
            [{id, questionnaire, dimension, text, reverse, scale_type, scale_range, scale_labels}, ...]
        """
        self._load_config()
        self._build_question_map()

        preset_data = self._presets.get(preset)
        if not preset_data:
            return []

        items = []
        for item_ref in preset_data.get("items", []):
            q_id = item_ref["id"]
            full_info = self._question_map.get(q_id)
            if full_info:
                items.append(full_info)
            else:
                logger.warning(f"高频题目 {q_id} 未在题库中找到")
        return items

    def get_all_questions(self) -> List[Dict[str, Any]]:
        """获取所有171题（供自选模式使用）"""
        self._build_question_map()
        return list(self._question_map.values())

    def get_questions_by_ids(self, ids: List[str]) -> List[Dict[str, Any]]:
        """根据题目ID列表获取完整题目信息"""
        self._build_question_map()
        result = []
        for qid in ids:
            info = self._question_map.get(qid)
            if info:
                result.append(info)
        return result

    def score_partial_answers(self, answers: Dict[str, int], question_ids: List[str]) -> Dict[str, Any]:
        """
        对部分答案进行评分

        Args:
            answers: {题目ID: 分值}
            question_ids: 本次测评包含的题目ID列表

        Returns:
            {
                "dimension_signals": {维度: {count, sum, avg}},
                "questionnaire_signals": {问卷: {answered, total, dimensions}},
                "stage_estimate": "S0"-"S6" or null,
                "bpt6_tendency": "action"/"emotion"/... or null,
                "spi_partial": float or null,
            }
        """
        self._build_question_map()

        # 按问卷+维度聚合
        q_dim_scores = {}  # {(questionnaire, dimension): [scores]}
        for qid, score in answers.items():
            info = self._question_map.get(qid)
            if not info:
                continue
            key = (info["questionnaire"], info["dimension"])
            if key not in q_dim_scores:
                q_dim_scores[key] = []
            # 处理反转题
            if info.get("reverse"):
                if info["scale_type"] == "bipolar":
                    score = -score
                else:
                    lo, hi = info["scale_range"]
                    score = lo + hi - score
            q_dim_scores[key].append(score)

        # 构建维度信号
        dimension_signals = {}
        questionnaire_signals = {}

        for (q_name, dim), scores in q_dim_scores.items():
            dim_key = f"{q_name}:{dim}"
            dimension_signals[dim_key] = {
                "count": len(scores),
                "sum": sum(scores),
                "avg": round(sum(scores) / len(scores), 2) if scores else 0,
            }
            if q_name not in questionnaire_signals:
                questionnaire_signals[q_name] = {"answered": 0, "dimensions": {}}
            questionnaire_signals[q_name]["answered"] += len(scores)
            questionnaire_signals[q_name]["dimensions"][dim] = {
                "avg": round(sum(scores) / len(scores), 2) if scores else 0,
            }

        # TTM7 阶段估计: 找到平均分最高的阶段
        stage_estimate = None
        ttm_stages = {}
        for (q, dim), scores in q_dim_scores.items():
            if q == "ttm7":
                ttm_stages[dim] = sum(scores) / len(scores) if scores else 0
        if ttm_stages:
            # 高分阶段 = 最符合的阶段
            stage_estimate = max(ttm_stages, key=ttm_stages.get)

        # BPT6 倾向: 找到平均分最高的行为类型
        bpt6_tendency = None
        bpt_types = {}
        for (q, dim), scores in q_dim_scores.items():
            if q == "bpt6":
                bpt_types[dim] = sum(scores) / len(scores) if scores else 0
        if bpt_types:
            bpt6_tendency = max(bpt_types, key=bpt_types.get)

        # SPI 部分得分
        spi_partial = None
        spi_dims = {}
        weights = {"M": 0.30, "A": 0.25, "S": 0.20, "E": 0.15, "H": 0.10}
        for (q, dim), scores in q_dim_scores.items():
            if q == "spi":
                spi_dims[dim] = sum(scores) / len(scores) if scores else 0
        if spi_dims:
            weighted_sum = sum(
                spi_dims.get(d, 0) * w for d, w in weights.items()
            )
            # Normalize: each dim avg is 1-5, weighted max = 5, scale to 0-100
            spi_partial = round(weighted_sum / 5 * 100, 1)

        return {
            "dimension_signals": dimension_signals,
            "questionnaire_signals": questionnaire_signals,
            "stage_estimate": stage_estimate,
            "bpt6_tendency": bpt6_tendency,
            "spi_partial": spi_partial,
        }
