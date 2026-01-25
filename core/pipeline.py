# -*- coding: utf-8 -*-
"""
pipeline.py - 八爪鱼五层架构处理流程引擎

五层架构:
1. 输入层 (Input): 从 Excel/PDF 抓取生理/心理数据
2. 解析层 (Parsing): 状态建模 - 改变阶段判定 + 动机强度计算
3. 策略层 (Strategy): 匹配 behavior_logic.json 专家规则
4. 输出层 (Output): 生成处方包 (指导意见 + 知识点 + 视频 + 产品ID)
5. 反馈层 (Feedback): 记录执行后数据波动，效能闭环
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field, asdict

# 导入输入层模块
from core.data_extractor import extract_health_data, ExtractionResult


@dataclass
class UserHistory:
    """用户历史数据（用于阶段判定）"""
    assessment_count: int = 0
    consecutive_improvement_weeks: int = 0
    stable_weeks: int = 0
    task_completion_rate: float = 0.0
    previous_metrics: Dict[str, float] = field(default_factory=dict)
    last_assessment_date: Optional[str] = None


@dataclass
class ParsedState:
    """解析层输出 - 用户状态模型"""
    # 生理指标
    physiological: Dict[str, Any] = field(default_factory=dict)
    # 心理指标
    psychological: Dict[str, Any] = field(default_factory=dict)
    # 改变阶段
    detected_stage: str = "intention"
    stage_name: str = "意向期"
    readiness_level: int = 2
    spi_coefficient: float = 0.5
    # 动机强度
    motivation_score: float = 50.0
    motivation_level: str = "moderate"
    energy_mood_match: float = 0.5
    motivation_interpretation: str = ""
    # 行为模式
    behavior_pattern: str = "balanced"
    pattern_confidence: float = 0.5


@dataclass
class StrategyMatch:
    """策略层输出 - 匹配的干预策略"""
    intervention_strategy: str = ""
    strategy_name: str = ""
    primary_expert: str = "mental_health"
    consulted_experts: List[str] = field(default_factory=list)
    matched_rules: List[str] = field(default_factory=list)
    content_types: List[str] = field(default_factory=list)
    tone: str = "supportive"
    max_tasks: int = 2
    max_difficulty: int = 3
    techniques: List[str] = field(default_factory=list)
    # rx_library 集成
    matched_prescriptions: List[Dict[str, Any]] = field(default_factory=list)
    active_prescription: Optional[Dict[str, Any]] = None
    stage_script: Dict[str, str] = field(default_factory=dict)


class OctopusPipeline:
    """八爪鱼五层处理流程引擎"""

    def __init__(self,
                 config_path: str = "core/schemas/behavior_logic.json",
                 rx_library_path: str = "models/rx_library.json"):
        """
        初始化处理流程引擎

        Args:
            config_path: behavior_logic.json 路径
            rx_library_path: rx_library.json 处方库路径
        """
        self.config_path = Path(config_path)
        self.rx_library_path = Path(rx_library_path)
        self.behavior_logic = self._load_behavior_logic()
        self.rx_library = self._load_rx_library()

        # 用户历史缓存 (实际生产环境应使用数据库)
        self._user_history_cache: Dict[str, UserHistory] = {}

    def _load_behavior_logic(self) -> Dict[str, Any]:
        """加载专家规则库"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _load_rx_library(self) -> Dict[str, Any]:
        """加载行为处方库"""
        if self.rx_library_path.exists():
            with open(self.rx_library_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        print(f"[警告] 处方库未找到: {self.rx_library_path}")
        return {"prescriptions": []}

    # ========== 第一层：输入层 ==========

    def layer_input(self, data_dir: str, user_id: str = None) -> ExtractionResult:
        """
        输入层：从 Excel/PDF 抓取生理与心理数据

        Args:
            data_dir: 数据目录路径
            user_id: 用户ID

        Returns:
            ExtractionResult 提取结果
        """
        print("\n" + "="*60)
        print("【第一层：输入层】数据抓取")
        print("="*60)

        result = extract_health_data(data_dir, user_id)
        return result

    # ========== 第二层：解析层 ==========

    def layer_parsing(self,
                      extraction_result: ExtractionResult,
                      user_id: str,
                      user_history: UserHistory = None) -> ParsedState:
        """
        解析层：状态建模
        - 改变阶段判定（基于历史数据频率）
        - 动机强度计算（基于精力与心情匹配度）
        - 行为模式识别

        Args:
            extraction_result: 输入层提取的数据
            user_id: 用户ID
            user_history: 用户历史数据

        Returns:
            ParsedState 解析后的状态
        """
        print("\n" + "="*60)
        print("【第二层：解析层】状态建模")
        print("="*60)

        state = ParsedState()

        # 填充生理/心理数据
        state.physiological = extraction_result.physio_data
        state.psychological = extraction_result.psych_data

        # 获取用户历史
        if user_history is None:
            user_history = self._get_user_history(user_id)

        # 1. 改变阶段判定（基于历史数据频率）
        stage_result = self._detect_change_stage(user_history, extraction_result)
        state.detected_stage = stage_result["stage"]
        state.stage_name = stage_result["stage_name"]
        state.readiness_level = stage_result["readiness_level"]
        state.spi_coefficient = stage_result["spi_coefficient"]

        print(f"  改变阶段: {state.stage_name} (Level {state.readiness_level})")
        print(f"  SPI系数: {state.spi_coefficient}")

        # 2. 动机强度计算（基于精力与心情匹配度）
        motivation_result = self._calculate_motivation(extraction_result.psych_data)
        state.motivation_score = motivation_result["score"]
        state.motivation_level = motivation_result["level"]
        state.energy_mood_match = motivation_result["match_score"]
        state.motivation_interpretation = motivation_result["interpretation"]

        print(f"  动机强度: {state.motivation_score:.1f} ({state.motivation_level})")
        print(f"  精力-心情匹配度: {state.energy_mood_match:.2f}")
        print(f"  状态解读: {state.motivation_interpretation}")

        # 3. 行为模式识别
        pattern_result = self._identify_behavior_pattern(
            extraction_result.physio_data,
            extraction_result.psych_data
        )
        state.behavior_pattern = pattern_result["pattern"]
        state.pattern_confidence = pattern_result["confidence"]

        print(f"  行为模式: {pattern_result['pattern_name']} (置信度: {state.pattern_confidence:.2f})")

        # 更新用户历史
        self._update_user_history(user_id, extraction_result)

        return state

    def _get_user_history(self, user_id: str) -> UserHistory:
        """获取用户历史数据"""
        if user_id not in self._user_history_cache:
            self._user_history_cache[user_id] = UserHistory()
        return self._user_history_cache[user_id]

    def _update_user_history(self, user_id: str, result: ExtractionResult):
        """更新用户历史数据"""
        history = self._get_user_history(user_id)
        history.assessment_count += 1
        history.last_assessment_date = datetime.now().isoformat()

        # 检查是否有改善
        current_metrics = {**result.physio_data, **result.psych_data}
        if history.previous_metrics:
            improved = self._check_improvement(history.previous_metrics, current_metrics)
            if improved:
                history.consecutive_improvement_weeks += 1
            else:
                history.consecutive_improvement_weeks = 0

        history.previous_metrics = current_metrics
        self._user_history_cache[user_id] = history

    def _check_improvement(self, prev: Dict, curr: Dict) -> bool:
        """检查指标是否有改善"""
        improvement_count = 0
        check_count = 0

        # 正向指标（越高越好）
        positive_metrics = ['SDNN', 'RMSSD', 'energy', 'mood', 'sleep_quality']
        # 负向指标（越低越好）
        negative_metrics = ['anxiety_score', 'stress_index', 'fatigue_index']

        for metric in positive_metrics:
            if metric in prev and metric in curr:
                check_count += 1
                if curr[metric] > prev[metric] * 1.1:  # 改善10%以上
                    improvement_count += 1

        for metric in negative_metrics:
            if metric in prev and metric in curr:
                check_count += 1
                if curr[metric] < prev[metric] * 0.9:  # 降低10%以上
                    improvement_count += 1

        return check_count > 0 and improvement_count / check_count > 0.5

    def _detect_change_stage(self,
                             history: UserHistory,
                             result: ExtractionResult) -> Dict[str, Any]:
        """
        改变阶段判定（基于历史数据频率）
        - 初次测评 = 意向期
        - 连续好转 = 行动期
        """
        stage_detection = self.behavior_logic.get("stage_detection", {})
        readiness_levels = self.behavior_logic.get("psychological_readiness_levels", {})

        # 判定逻辑
        if history.assessment_count == 0 or history.assessment_count == 1:
            # 初次测评 = 意向期
            stage = "intention"
            stage_name = "意向期"
            mapped_level = "level_2_resistance_reflection"
        elif history.consecutive_improvement_weeks >= 2:
            # 连续好转 = 行动期
            stage = "action"
            stage_name = "行动期"
            mapped_level = "level_4_adaptive_alignment"
        elif history.stable_weeks >= 8 and history.task_completion_rate >= 0.8:
            # 稳定维持
            stage = "maintenance"
            stage_name = "维持期"
            mapped_level = "level_5_full_internalization"
        elif history.assessment_count > 1 and history.consecutive_improvement_weeks == 0:
            # 多次测评无改善 = 思考期
            stage = "contemplation"
            stage_name = "思考期"
            mapped_level = "level_2_resistance_reflection"
        else:
            # 默认准备期
            stage = "preparation"
            stage_name = "准备期"
            mapped_level = "level_3_selective_acceptance"

        # 获取对应的心理准备度层次信息
        level_info = readiness_levels.get(mapped_level, {})
        readiness_level = level_info.get("level", 3)
        spi_coefficient = level_info.get("spi_coefficient", 0.7)

        return {
            "stage": stage,
            "stage_name": stage_name,
            "mapped_level": mapped_level,
            "readiness_level": readiness_level,
            "spi_coefficient": spi_coefficient
        }

    def _calculate_motivation(self, psych_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        动机强度计算（核心：精力与心情匹配度）

        计算公式:
        step_1: match_score = 1 - abs(energy - mood) / 100
        step_2: base_motivation = (energy + mood) / 2
        step_3: motivation = base_motivation * (0.5 + 0.5 * match_score)
        """
        motivation_config = self.behavior_logic.get("motivation_calculation", {})

        # 获取精力和心情值
        energy = psych_data.get("energy", 50)
        mood = psych_data.get("mood", 50)

        # 如果没有直接的 energy/mood，尝试从其他字段推断
        if energy == 50 and "energy_level" in psych_data:
            energy = psych_data["energy_level"]
        if mood == 50 and "mood_score" in psych_data:
            mood = psych_data["mood_score"]

        # 计算匹配度
        match_score = 1 - abs(energy - mood) / 100

        # 计算基础动机
        base_motivation = (energy + mood) / 2

        # 计算最终动机（匹配度高时动机更强）
        motivation = base_motivation * (0.5 + 0.5 * match_score)

        # 确定动机等级
        if motivation >= 70:
            level = "high"
        elif motivation >= 40:
            level = "moderate"
        else:
            level = "low"

        # 四象限解读
        interpretation_config = motivation_config.get("interpretation", {})
        if energy >= 70 and mood >= 70:
            interpretation = "最佳状态，适合挑战性任务"
        elif energy >= 70 and mood < 50:
            interpretation = "精力充沛但情绪低落，建议先进行情绪调节"
        elif energy < 50 and mood >= 70:
            interpretation = "心情好但精力不足，安排轻松愉快的小任务"
        elif energy < 50 and mood < 50:
            interpretation = "双低状态，优先休息恢复，暂缓行为任务"
        else:
            interpretation = "状态中等，可安排适度任务"

        return {
            "score": round(motivation, 1),
            "level": level,
            "match_score": round(match_score, 2),
            "energy": energy,
            "mood": mood,
            "interpretation": interpretation
        }

    def _identify_behavior_pattern(self,
                                   physio_data: Dict[str, Any],
                                   psych_data: Dict[str, Any]) -> Dict[str, Any]:
        """行为模式识别"""
        patterns = self.behavior_logic.get("behavior_patterns", {})

        best_match = "balanced"
        best_score = 0
        best_name = "平衡型"

        for pattern_id, pattern_info in patterns.items():
            indicators = pattern_info.get("indicators", {})
            score = 0
            total_weight = 0

            for indicator, criteria in indicators.items():
                value = physio_data.get(indicator) or psych_data.get(indicator)
                if value is not None:
                    weight = criteria.get("weight", 0.25)
                    range_min, range_max = criteria.get("range", [0, 100])

                    if range_min <= value <= range_max:
                        score += weight
                    total_weight += weight

            if total_weight > 0:
                normalized_score = score / total_weight
                if normalized_score > best_score:
                    best_score = normalized_score
                    best_match = pattern_id
                    best_name = pattern_info.get("name", pattern_id)

        return {
            "pattern": best_match,
            "pattern_name": best_name,
            "confidence": round(best_score, 2)
        }

    # ========== 第三层：策略层 ==========

    def layer_strategy(self, parsed_state: ParsedState) -> StrategyMatch:
        """
        策略层：匹配 behavior_logic.json 专家规则 + rx_library 处方库

        Args:
            parsed_state: 解析层输出的状态

        Returns:
            StrategyMatch 匹配的干预策略
        """
        print("\n" + "="*60)
        print("【第三层：策略层】规则匹配")
        print("="*60)

        match = StrategyMatch()

        # 1. 根据心理准备度层次选择干预策略
        readiness_levels = self.behavior_logic.get("psychological_readiness_levels", {})
        strategies = self.behavior_logic.get("intervention_strategies", {})

        # 找到对应层次
        for level_key, level_info in readiness_levels.items():
            if level_info.get("level") == parsed_state.readiness_level:
                strategy_key = level_info.get("strategy", "threshold_lowering")
                strategy_info = strategies.get(strategy_key, {})

                match.intervention_strategy = strategy_key
                match.strategy_name = strategy_info.get("name", "")
                match.content_types = strategy_info.get("content_types", [])
                match.tone = strategy_info.get("tone", "supportive")
                match.max_tasks = level_info.get("max_tasks", 2)
                match.max_difficulty = level_info.get("max_difficulty", 3)
                match.techniques = strategy_info.get("techniques", [])
                break

        print(f"  干预策略: {match.strategy_name}")
        print(f"  最大任务数: {match.max_tasks}")
        print(f"  最大难度: {match.max_difficulty}")
        print(f"  干预技术: {', '.join(match.techniques[:3])}")

        # 2. 根据行为模式选择专家
        patterns = self.behavior_logic.get("behavior_patterns", {})
        pattern_info = patterns.get(parsed_state.behavior_pattern, {})
        recommended_experts = pattern_info.get("recommended_experts", ["mental_health"])

        match.primary_expert = recommended_experts[0] if recommended_experts else "mental_health"
        match.consulted_experts = recommended_experts[1:] if len(recommended_experts) > 1 else []

        print(f"  主要专家: {match.primary_expert}")
        print(f"  协作专家: {', '.join(match.consulted_experts) or '无'}")

        # 3. 匹配规则
        matching_rules = self.behavior_logic.get("matching_rules", [])
        for rule in matching_rules:
            if self._check_rule_match(rule, parsed_state):
                match.matched_rules.append(rule.get("id", ""))

        if match.matched_rules:
            print(f"  匹配规则: {', '.join(match.matched_rules)}")

        # 4. 匹配 rx_library 处方库
        matched_rx = self._match_prescriptions(parsed_state)
        match.matched_prescriptions = matched_rx

        if matched_rx:
            # 选择最匹配的处方作为激活处方
            match.active_prescription = matched_rx[0]
            rx_id = match.active_prescription.get("rx_id", "")
            rx_name = match.active_prescription.get("name", "")

            # 获取对应阶段的话术
            stage_key = self._get_stage_key(parsed_state.detected_stage)
            stage_strategy = match.active_prescription.get("stage_strategy", {}).get(stage_key, {})
            match.stage_script = stage_strategy
            match.tone = stage_strategy.get("tone", match.tone)

            print(f"\n  [处方库匹配]")
            print(f"  激活处方: {rx_id} - {rx_name}")
            print(f"  匹配处方数: {len(matched_rx)}")
            print(f"  阶段话术: {stage_key} ({stage_strategy.get('stage_name', '')})")
        else:
            print(f"\n  [处方库匹配] 无匹配处方，使用默认模板")

        return match

    def _match_prescriptions(self, state: ParsedState) -> List[Dict[str, Any]]:
        """
        从 rx_library 匹配适用的处方

        匹配规则:
        1. 行为模式匹配 (applicable_patterns)
        2. 专家来源匹配 (expert_source)
        3. 心理准备度层次匹配 (stage_strategy.readiness_level)
        """
        prescriptions = self.rx_library.get("prescriptions", [])
        matched = []

        for rx in prescriptions:
            score = 0

            # 1. 行为模式匹配
            applicable_patterns = rx.get("applicable_patterns", [])
            if state.behavior_pattern in applicable_patterns:
                score += 3

            # 2. 专家来源匹配
            patterns = self.behavior_logic.get("behavior_patterns", {})
            pattern_info = patterns.get(state.behavior_pattern, {})
            recommended_experts = pattern_info.get("recommended_experts", [])
            if rx.get("expert_source") in recommended_experts:
                score += 2

            # 3. 心理准备度层次匹配
            stage_key = self._get_stage_key(state.detected_stage)
            stage_strategy = rx.get("stage_strategy", {}).get(stage_key, {})
            readiness_levels = stage_strategy.get("readiness_level", [])
            if state.readiness_level in readiness_levels:
                score += 2

            if score > 0:
                matched.append({
                    **rx,
                    "_match_score": score
                })

        # 按匹配分数排序
        matched.sort(key=lambda x: x.get("_match_score", 0), reverse=True)
        return matched

    def _get_stage_key(self, detected_stage: str) -> str:
        """将检测到的阶段映射到处方库的阶段键"""
        stage_mapping = {
            "intention": "intention",
            "contemplation": "intention",
            "preparation": "preparation",
            "action": "action",
            "maintenance": "action"
        }
        return stage_mapping.get(detected_stage, "preparation")

    def _check_rule_match(self, rule: Dict, state: ParsedState) -> bool:
        """检查规则是否匹配"""
        conditions = rule.get("conditions", {})

        for indicator, criteria in conditions.items():
            value = state.physiological.get(indicator) or state.psychological.get(indicator)
            if value is None:
                continue

            if isinstance(criteria, dict):
                min_val = criteria.get("min", float("-inf"))
                max_val = criteria.get("max", float("inf"))
                if not (min_val <= value <= max_val):
                    return False
            elif isinstance(criteria, list):
                if value not in criteria:
                    return False

        return True

    # ========== 第四层：输出层 ==========

    def layer_output(self,
                     user_id: str,
                     parsed_state: ParsedState,
                     strategy_match: StrategyMatch) -> Dict[str, Any]:
        """
        输出层：生成处方包 JSON
        包含: 指导意见、知识点、教学视频路径、商城产品ID

        Args:
            user_id: 用户ID
            parsed_state: 解析层状态
            strategy_match: 策略层匹配结果

        Returns:
            处方包 JSON
        """
        print("\n" + "="*60)
        print("【第四层：输出层】生成处方包")
        print("="*60)

        now = datetime.now()
        prescription_id = f"RX-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        prescription = {
            "prescription_id": prescription_id,
            "user_id": user_id,
            "created_at": now.isoformat(),
            "valid_until": (now + timedelta(days=7)).isoformat(),
            "version": "1.0",

            # 评估摘要
            "assessment_summary": {
                "physiological": parsed_state.physiological,
                "psychological": parsed_state.psychological,
                "behavior_pattern": {
                    "primary_pattern": parsed_state.behavior_pattern,
                    "confidence": parsed_state.pattern_confidence
                },
                "change_stage": {
                    "current_stage": parsed_state.detected_stage,
                    "stage_name": parsed_state.stage_name,
                    "readiness_level": parsed_state.readiness_level,
                    "spi_coefficient": parsed_state.spi_coefficient
                },
                "motivation": {
                    "score": parsed_state.motivation_score,
                    "level": parsed_state.motivation_level,
                    "energy_mood_match": parsed_state.energy_mood_match,
                    "interpretation": parsed_state.motivation_interpretation
                }
            },

            # 处方内容
            "prescription_content": {
                "guidance": self._generate_guidance(parsed_state, strategy_match),
                "tasks": self._generate_tasks(parsed_state, strategy_match),
                "knowledge": self._generate_knowledge_refs(strategy_match),
                "videos": self._generate_video_refs(strategy_match),
                "products": self._generate_product_refs(strategy_match)
            },

            # 限幅信息
            "clamping_info": {
                "max_tasks_allowed": strategy_match.max_tasks,
                "max_difficulty_allowed": strategy_match.max_difficulty,
                "clamping_level": self._get_clamping_level(parsed_state.readiness_level)
            },

            # 反馈追踪（初始化）
            "feedback_tracking": {
                "tracking_id": f"TRK-{uuid.uuid4().hex[:8].upper()}",
                "baseline_metrics": {
                    **parsed_state.physiological,
                    **parsed_state.psychological
                },
                "checkpoints": [],
                "outcome": {
                    "status": "in_progress"
                }
            },

            # 元数据
            "metadata": {
                "generated_by": "xingjian_coach",
                "model_version": "1.0",
                "rules_version": self.behavior_logic.get("version", "1.0.0"),
                "primary_expert": strategy_match.primary_expert,
                "consulted_experts": strategy_match.consulted_experts,
                "matched_rules": strategy_match.matched_rules,
                "intervention_strategy": strategy_match.intervention_strategy
            }
        }

        print(f"  处方ID: {prescription_id}")
        print(f"  有效期至: {prescription['valid_until'][:10]}")
        print(f"  任务数量: {len(prescription['prescription_content']['tasks'])}")
        print(f"  知识点: {len(prescription['prescription_content']['knowledge'])}")
        print(f"  视频: {len(prescription['prescription_content']['videos'])}")
        print(f"  产品: {len(prescription['prescription_content']['products'])}")

        return prescription

    def _generate_guidance(self, state: ParsedState, match: StrategyMatch) -> Dict:
        """生成指导意见 - 集成 rx_library 分阶段话术"""
        # 获取干预策略的 do/dont
        strategies = self.behavior_logic.get("intervention_strategies", {})
        strategy_info = strategies.get(match.intervention_strategy, {})

        # 如果有匹配的处方，使用处方库的分阶段话术
        if match.active_prescription and match.stage_script:
            script = match.stage_script
            rx_name = match.active_prescription.get("name", "")

            # 核心建议摘要 - 使用处方话术
            summary = script.get("script_opening", "")[:100]

            detailed_advice = [
                {
                    "expert": match.active_prescription.get("expert_source", match.primary_expert),
                    "advice": script.get("script_motivation", ""),
                    "priority": 1
                },
                {
                    "expert": match.primary_expert,
                    "advice": f"核心目标: {script.get('core_goal', '')}",
                    "priority": 2
                }
            ]

            return {
                "summary": summary,
                "rx_source": match.active_prescription.get("rx_id", ""),
                "rx_name": rx_name,
                "stage_name": script.get("stage_name", state.stage_name),
                "script": {
                    "opening": script.get("script_opening", ""),
                    "motivation": script.get("script_motivation", ""),
                    "closing": script.get("script_closing", "")
                },
                "detailed_advice": detailed_advice,
                "warnings": script.get("dont", []),
                "tone": script.get("tone", match.tone),
                "do": script.get("do", []),
                "dont": script.get("dont", [])
            }

        # 默认：使用 behavior_logic 的策略
        summary = f"当前处于{state.stage_name}，建议采用{match.strategy_name}策略。"
        summary += f"动机水平{state.motivation_level}，{state.motivation_interpretation}"

        return {
            "summary": summary[:100],
            "detailed_advice": [
                {
                    "expert": match.primary_expert,
                    "advice": f"采用{match.strategy_name}策略，核心技术：{', '.join(match.techniques[:2])}",
                    "priority": 1
                }
            ],
            "warnings": strategy_info.get("dont", []),
            "tone": match.tone,
            "do": strategy_info.get("do", []),
            "dont": strategy_info.get("dont", [])
        }

    def _generate_tasks(self, state: ParsedState, match: StrategyMatch) -> List[Dict]:
        """生成任务列表（已限幅）- 优先使用 rx_library 的建设性意见"""
        tasks = []

        # 优先从 rx_library 获取建设性意见
        if match.active_prescription:
            content = match.active_prescription.get("content", {})
            advice_list = content.get("constructive_advice", [])

            for advice in advice_list:
                if len(tasks) >= match.max_tasks:
                    break

                difficulty = advice.get("difficulty", 2)
                if difficulty <= match.max_difficulty:
                    # 计算大致时长（基于难度）
                    base_duration = 5 + (difficulty - 1) * 10

                    tasks.append({
                        "task_id": f"T-{uuid.uuid4().hex[:6].upper()}",
                        "advice_id": advice.get("advice_id", ""),
                        "content": advice.get("title", ""),
                        "description": advice.get("description", ""),
                        "difficulty": difficulty,
                        "type": self._infer_task_type(match.active_prescription.get("category", "")),
                        "duration_minutes": base_duration,
                        "frequency": "每日1次",
                        "priority": advice.get("priority", 99),
                        "duration_to_form_habit": advice.get("duration_to_form_habit", "2-4周"),
                        "expert_source": match.active_prescription.get("expert_source", match.primary_expert),
                        "rx_source": match.active_prescription.get("rx_id", ""),
                        "linked_knowledge": [],
                        "linked_video": "",
                        "linked_product": ""
                    })

            # 按优先级排序
            tasks.sort(key=lambda x: x.get("priority", 99))

            if tasks:
                return tasks

        # 回退：使用默认任务模板
        task_templates = {
            "safety_building": [
                {"content": "完成3分钟正念呼吸练习", "difficulty": 1, "type": "mental", "duration": 3},
                {"content": "记录今日情绪日志（不评判）", "difficulty": 1, "type": "mental", "duration": 5},
            ],
            "ambivalence_processing": [
                {"content": "完成改变利弊分析表", "difficulty": 2, "type": "mental", "duration": 15},
                {"content": "写下保持现状的3个风险", "difficulty": 1, "type": "mental", "duration": 10},
            ],
            "threshold_lowering": [
                {"content": "完成5分钟轻度拉伸", "difficulty": 1, "type": "physical", "duration": 5},
                {"content": "喝一杯温水", "difficulty": 1, "type": "nutrition", "duration": 1},
                {"content": "户外步行1000步", "difficulty": 2, "type": "physical", "duration": 10},
            ],
            "habit_strengthening": [
                {"content": "按计划完成30分钟运动", "difficulty": 3, "type": "physical", "duration": 30},
                {"content": "记录饮食打卡", "difficulty": 2, "type": "nutrition", "duration": 5},
                {"content": "完成睡前放松练习", "difficulty": 2, "type": "mental", "duration": 10},
            ],
            "identity_consolidation": [
                {"content": "分享本周健康成果到群组", "difficulty": 2, "type": "social", "duration": 10},
                {"content": "反思健康习惯对生活的意义", "difficulty": 3, "type": "mental", "duration": 15},
                {"content": "帮助他人解答健康问题", "difficulty": 4, "type": "social", "duration": 20},
            ]
        }

        template_tasks = task_templates.get(match.intervention_strategy, task_templates["threshold_lowering"])

        for i, t in enumerate(template_tasks):
            if len(tasks) >= match.max_tasks:
                break
            if t["difficulty"] <= match.max_difficulty:
                tasks.append({
                    "task_id": f"T-{uuid.uuid4().hex[:6].upper()}",
                    "content": t["content"],
                    "difficulty": t["difficulty"],
                    "type": t["type"],
                    "duration_minutes": t["duration"],
                    "frequency": "每日1次",
                    "expert_source": match.primary_expert,
                    "linked_knowledge": [],
                    "linked_video": "",
                    "linked_product": ""
                })

        return tasks

    def _infer_task_type(self, category: str) -> str:
        """根据处方分类推断任务类型"""
        type_mapping = {
            "sleep_regulation": "mental",
            "stress_management": "mental",
            "exercise_habit": "physical",
            "nutrition_management": "nutrition",
            "emotional_regulation": "mental",
            "tcm_wellness": "tcm",
            "social_connection": "social",
            "cognitive_improvement": "mental"
        }
        return type_mapping.get(category, "general")

    def _generate_knowledge_refs(self, match: StrategyMatch) -> List[Dict]:
        """生成知识点引用 - 优先使用 rx_library"""
        # 优先从 rx_library 获取知识点
        if match.active_prescription:
            content = match.active_prescription.get("content", {})
            knowledge_points = content.get("knowledge_points", [])

            if knowledge_points:
                refs = []
                for kp in knowledge_points[:3]:
                    refs.append({
                        "knowledge_id": kp.get("knowledge_id", ""),
                        "title": kp.get("title", ""),
                        "summary": kp.get("summary", ""),
                        "category": kp.get("category", ""),
                        "content_url": kp.get("content_url", ""),
                        "reading_time_minutes": kp.get("reading_time_minutes", 5),
                        "difficulty_level": kp.get("difficulty_level", "beginner"),
                        "rx_source": match.active_prescription.get("rx_id", "")
                    })
                return refs

        # 回退：使用默认映射
        knowledge_map = {
            "mental_health": [
                {"knowledge_id": "K001", "title": "压力管理基础", "category": "mental_health"},
                {"knowledge_id": "K002", "title": "睡眠卫生指南", "category": "sleep"},
            ],
            "nutrition": [
                {"knowledge_id": "K010", "title": "均衡膳食原则", "category": "nutrition"},
            ],
            "sports_rehab": [
                {"knowledge_id": "K020", "title": "久坐族运动指南", "category": "exercise"},
            ],
            "tcm_wellness": [
                {"knowledge_id": "K030", "title": "四季养生基础", "category": "tcm"},
            ]
        }

        refs = knowledge_map.get(match.primary_expert, [])
        for expert in match.consulted_experts:
            refs.extend(knowledge_map.get(expert, [])[:1])

        return refs[:3]

    def _generate_video_refs(self, match: StrategyMatch) -> List[Dict]:
        """生成视频引用 - 优先使用 rx_library"""
        # 优先从 rx_library 获取视频
        if match.active_prescription:
            content = match.active_prescription.get("content", {})
            videos = content.get("teaching_videos", [])

            if videos:
                refs = []
                for vid in videos[:3]:
                    refs.append({
                        "video_id": vid.get("video_id", ""),
                        "title": vid.get("title", ""),
                        "description": vid.get("description", ""),
                        "duration_seconds": vid.get("duration_seconds", 0),
                        "video_path": vid.get("video_path", ""),
                        "thumbnail_path": vid.get("thumbnail_path", ""),
                        "instructor": vid.get("instructor", ""),
                        "rx_source": match.active_prescription.get("rx_id", "")
                    })
                return refs

        # 回退：使用默认映射
        video_map = {
            "mental_health": [
                {"video_id": "V001", "title": "5分钟正念呼吸", "duration_seconds": 300},
            ],
            "sports_rehab": [
                {"video_id": "V010", "title": "办公室拉伸操", "duration_seconds": 420},
            ]
        }

        return video_map.get(match.primary_expert, [])[:2]

    def _generate_product_refs(self, match: StrategyMatch) -> List[Dict]:
        """生成产品引用 - 优先使用 rx_library product_mapping"""
        # 优先从 rx_library 获取产品推荐
        if match.active_prescription:
            products = match.active_prescription.get("product_mapping", [])

            if products:
                refs = []
                for prod in products[:3]:
                    refs.append({
                        "product_id": prod.get("product_id", ""),
                        "name": prod.get("name", ""),
                        "category": prod.get("category", ""),
                        "relevance": prod.get("relevance", ""),
                        "recommendation_trigger": prod.get("recommendation_trigger", ""),
                        "rx_source": match.active_prescription.get("rx_id", "")
                    })
                return refs

        # 回退：使用默认映射
        product_map = {
            "nutrition": [
                {"product_id": "P001", "name": "代餐奶昔", "category": "nutrition"},
            ],
            "tcm_wellness": [
                {"product_id": "P010", "name": "养生茶", "category": "tcm"},
            ]
        }

        return product_map.get(match.primary_expert, [])[:2]

    def _get_clamping_level(self, readiness_level: int) -> str:
        """获取限幅等级"""
        if readiness_level <= 2:
            return "strict"
        elif readiness_level == 3:
            return "moderate"
        elif readiness_level == 4:
            return "relaxed"
        else:
            return "none"

    # ========== 第五层：反馈层 ==========

    def layer_feedback(self,
                       prescription: Dict[str, Any],
                       new_metrics: Dict[str, Any] = None,
                       task_completion: Dict[str, Any] = None,
                       user_feedback: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        反馈层：记录执行后数据波动，效能闭环

        Args:
            prescription: 原处方包
            new_metrics: 新的指标数据
            task_completion: 任务完成情况
            user_feedback: 用户反馈

        Returns:
            更新后的处方包
        """
        print("\n" + "="*60)
        print("【第五层：反馈层】效能闭环")
        print("="*60)

        tracking = prescription.get("feedback_tracking", {})
        baseline = tracking.get("baseline_metrics", {})
        checkpoints = tracking.get("checkpoints", [])

        # 创建新的检查点
        checkpoint = {
            "checkpoint_date": datetime.now().strftime("%Y-%m-%d"),
            "days_since_prescription": len(checkpoints) + 1
        }

        # 记录指标快照
        if new_metrics:
            checkpoint["metrics_snapshot"] = new_metrics

            # 计算变化
            changes = {}
            for key, new_val in new_metrics.items():
                if key in baseline and isinstance(new_val, (int, float)):
                    old_val = baseline[key]
                    if old_val != 0:
                        change_pct = (new_val - old_val) / old_val * 100
                        changes[key] = round(change_pct, 1)

            if changes:
                checkpoint["metric_changes"] = changes
                print(f"  指标变化: {changes}")

        # 记录任务完成情况
        if task_completion:
            checkpoint["task_completion"] = task_completion
            print(f"  任务完成: {task_completion.get('completed', 0)}/{task_completion.get('total', 0)}")

        # 记录用户反馈
        if user_feedback:
            checkpoint["user_feedback"] = user_feedback
            print(f"  用户满意度: {user_feedback.get('satisfaction', '-')}/5")

        checkpoints.append(checkpoint)
        tracking["checkpoints"] = checkpoints
        prescription["feedback_tracking"] = tracking

        return prescription

    # ========== 完整流程执行 ==========

    def process(self,
                data_dir: str,
                user_id: str,
                save_output: bool = True) -> Dict[str, Any]:
        """
        执行完整的五层处理流程

        Args:
            data_dir: 数据目录
            user_id: 用户ID
            save_output: 是否保存输出

        Returns:
            完整处方包
        """
        print("\n" + "="*70)
        print("八爪鱼五层架构处理流程启动")
        print("="*70)
        print(f"用户ID: {user_id}")
        print(f"数据目录: {data_dir}")

        # 第一层：输入
        extraction_result = self.layer_input(data_dir, user_id)

        # 第二层：解析
        parsed_state = self.layer_parsing(extraction_result, user_id)

        # 第三层：策略
        strategy_match = self.layer_strategy(parsed_state)

        # 第四层：输出
        prescription = self.layer_output(user_id, parsed_state, strategy_match)

        # 保存处方
        if save_output:
            output_dir = Path("output/prescriptions")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{prescription['prescription_id']}.json"

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(prescription, f, ensure_ascii=False, indent=2)

            print(f"\n处方已保存: {output_path}")

        print("\n" + "="*70)
        print("处理流程完成")
        print("="*70)

        return prescription


# ============ 主函数入口 ============
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="八爪鱼五层架构处理流程")
    parser.add_argument("--data-dir", default=r"data\raw", help="数据目录")
    parser.add_argument("--user-id", default="test_user", help="用户ID")
    parser.add_argument("--no-save", action="store_true", help="不保存输出")

    args = parser.parse_args()

    pipeline = OctopusPipeline()
    prescription = pipeline.process(
        args.data_dir,
        args.user_id,
        save_output=not args.no_save
    )

    print("\n处方包预览:")
    print(json.dumps(prescription, ensure_ascii=False, indent=2)[:2000] + "...")
