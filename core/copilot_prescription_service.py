# -*- coding: utf-8 -*-
"""
CopilotPrescriptionService - AI 行为处方生成服务

教练打开学员详情时自动调用：
1. 采集学员数据 (评估/健康指标/行为画像/微行动)
2. 调用 LLM 生成结构化诊断+处方
3. LLM 不可用时走规则引擎降级
4. 无真实数据时生成阶段匹配模拟数据
"""
import json
import random
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import desc
from sqlalchemy.orm import Session

from core.models import (
    User,
    BehavioralProfile,
    Assessment,
    GlucoseReading,
    SleepRecord,
    ActivityRecord,
    VitalSign,
    MicroActionTask,
)

# 阶段中文名映射
STAGE_NAMES = {
    "S0": "无知无觉", "S1": "强烈抗拒", "S2": "被动承诺",
    "S3": "勉强接受", "S4": "主动尝试", "S5": "规律践行", "S6": "内化为常",
}

# CAPACITY 六因素
CAPACITY_FACTORS = [
    {"key": "C", "name": "信心", "full": "Confidence"},
    {"key": "A", "name": "能力", "full": "Ability"},
    {"key": "P", "name": "感知", "full": "Perception"},
    {"key": "A2", "name": "资源", "full": "Access"},
    {"key": "I", "name": "兴趣", "full": "Interest"},
    {"key": "T", "name": "时间", "full": "Time"},
]

# 阶段 → 干预阶段映射
STAGE_TO_PHASE = {
    "S0": "认知唤醒", "S1": "认知唤醒", "S2": "动机激发",
    "S3": "行为塑造", "S4": "习惯强化", "S5": "自主维持", "S6": "自主维持",
}

# 阶段 → 模拟 SPI 范围
STAGE_SPI_RANGE = {
    "S0": (5, 15), "S1": (10, 25), "S2": (20, 40),
    "S3": (35, 55), "S4": (50, 70), "S5": (65, 85), "S6": (80, 95),
}


# 模块级 LLM 失败缓存: 失败后 300 秒内不再尝试
_llm_last_fail_time: float = 0.0
_LLM_COOLDOWN = 300.0  # 5 分钟


class CopilotPrescriptionService:
    """AI 行为处方生成核心服务"""

    def generate_prescription(
        self, db: Session, student_id: int, coach_id: int
    ) -> Dict[str, Any]:
        """
        主入口: 采集数据 → LLM 分析 → 降级回退 → 返回结构化 JSON

        Returns:
            {diagnosis, prescription, ai_suggestions, health_summary,
             intervention_plan, meta}
        """
        # 1. 采集学员数据
        student_data = self._gather_student_data(db, student_id)
        if student_data is None:
            return {"error": "学员不存在", "meta": {"source": "error"}}

        # 2. 始终生成规则引擎基线 (保证数据完整)
        fallback = self._build_fallback_response(student_data)

        # 3. 尝试 LLM 增强
        llm_result = self._call_llm_analysis(student_data)

        # 4. 合并: LLM 成功则用 LLM 数据覆盖基线, 否则纯用基线
        if llm_result is not None:
            result = self._merge_llm_with_fallback(llm_result, fallback)
        else:
            logger.info(f"[copilot-rx] LLM 不可用, 纯规则引擎 student={student_id}")
            result = fallback

        # 5. 附加 meta
        result["meta"] = {
            "source": result.get("meta", {}).get("source", "fallback"),
            "llm_used": result.get("meta", {}).get("llm_used", False),
            "has_real_data": student_data["has_real_data"],
            "student_id": student_id,
            "coach_id": coach_id,
            "generated_at": datetime.utcnow().isoformat(),
        }
        return result

    # ── 数据采集 ──────────────────────────────────────────────────────

    def _gather_student_data(self, db: Session, student_id: int) -> Optional[Dict]:
        """查询学员全维度数据，无真实数据时生成模拟"""
        user = db.query(User).filter(User.id == student_id).first()
        if not user:
            return None

        has_real_data: Dict[str, bool] = {}
        now = datetime.utcnow()
        seven_days_ago = now - timedelta(days=7)

        # -- BehavioralProfile --
        profile = (
            db.query(BehavioralProfile)
            .filter(BehavioralProfile.user_id == student_id)
            .first()
        )
        has_real_data["profile"] = profile is not None
        if not profile:
            profile = self._simulate_profile(user)

        stage = profile.current_stage if hasattr(profile, "current_stage") else "S1"
        if hasattr(stage, "value"):
            stage = stage.value

        # -- Assessment (最新一次) --
        assessment = (
            db.query(Assessment)
            .filter(Assessment.user_id == student_id)
            .order_by(desc(Assessment.created_at))
            .first()
        )
        has_real_data["assessment"] = assessment is not None

        # -- GlucoseReading (7 天) --
        glucose_readings = (
            db.query(GlucoseReading)
            .filter(
                GlucoseReading.user_id == student_id,
                GlucoseReading.recorded_at >= seven_days_ago,
            )
            .order_by(desc(GlucoseReading.recorded_at))
            .all()
        )
        has_real_data["glucose"] = len(glucose_readings) > 0

        # -- SleepRecord (7 天) --
        sleep_cutoff = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        sleep_records = (
            db.query(SleepRecord)
            .filter(
                SleepRecord.user_id == student_id,
                SleepRecord.sleep_date >= sleep_cutoff,
            )
            .order_by(desc(SleepRecord.sleep_date))
            .all()
        )
        has_real_data["sleep"] = len(sleep_records) > 0

        # -- ActivityRecord (7 天) --
        activity_cutoff = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        activity_records = (
            db.query(ActivityRecord)
            .filter(
                ActivityRecord.user_id == student_id,
                ActivityRecord.activity_date >= activity_cutoff,
            )
            .order_by(desc(ActivityRecord.activity_date))
            .all()
        )
        has_real_data["activity"] = len(activity_records) > 0

        # -- VitalSign (最近 5 条) --
        vital_signs = (
            db.query(VitalSign)
            .filter(VitalSign.user_id == student_id)
            .order_by(desc(VitalSign.recorded_at))
            .limit(5)
            .all()
        )
        has_real_data["vitals"] = len(vital_signs) > 0

        # -- MicroActionTask (7 天) --
        micro_cutoff = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        micro_tasks = (
            db.query(MicroActionTask)
            .filter(
                MicroActionTask.user_id == student_id,
                MicroActionTask.scheduled_date >= micro_cutoff,
            )
            .all()
        )
        has_real_data["micro_actions"] = len(micro_tasks) > 0

        # 构建健康摘要 (真实或模拟)
        health = self._build_health_summary(
            glucose_readings, sleep_records, activity_records, vital_signs,
            has_real_data, stage,
        )

        # 微行动统计
        total_micro = len(micro_tasks)
        completed_micro = sum(1 for t in micro_tasks if t.status == "completed")

        return {
            "user": user,
            "profile": profile,
            "stage": stage,
            "assessment": assessment,
            "health": health,
            "micro_actions": {"total": total_micro, "completed": completed_micro},
            "has_real_data": has_real_data,
        }

    def _build_health_summary(
        self, glucose, sleep, activity, vitals, has_real, stage
    ) -> Dict:
        """构建健康摘要 — 有真实数据用真实, 否则模拟"""
        summary: Dict[str, Any] = {}
        highlights: List[str] = []

        # 血糖
        if has_real["glucose"] and glucose:
            fasting = [g.value for g in glucose if g.meal_tag == "fasting"]
            postprandial = [g.value for g in glucose if g.meal_tag == "after_meal"]
            summary["fastingGlucose"] = round(sum(fasting) / len(fasting), 1) if fasting else 0
            summary["postprandialGlucose"] = round(sum(postprandial) / len(postprandial), 1) if postprandial else 0
            if summary["fastingGlucose"] > 7.0:
                highlights.append("空腹血糖偏高")
            if summary["postprandialGlucose"] > 11.1:
                highlights.append("餐后血糖偏高")
        else:
            sim = self._simulate_health_data(stage)
            summary["fastingGlucose"] = sim["fasting_glucose"]
            summary["postprandialGlucose"] = sim["postprandial_glucose"]

        # 睡眠
        if has_real["sleep"] and sleep:
            avg_dur = sum(s.total_duration_min or 0 for s in sleep) / len(sleep)
            summary["sleepHours"] = round(avg_dur / 60, 1)
            if summary["sleepHours"] < 6:
                highlights.append("睡眠不足6小时")
        else:
            sim = self._simulate_health_data(stage)
            summary["sleepHours"] = sim["sleep_hours"]

        # 运动
        if has_real["activity"] and activity:
            total_min = sum(
                (a.moderate_active_min or 0) + (a.vigorous_active_min or 0)
                for a in activity
            )
            summary["exerciseMinutes"] = total_min
            if total_min < 150:
                highlights.append("周运动量未达标(<150分钟)")
        else:
            sim = self._simulate_health_data(stage)
            summary["exerciseMinutes"] = sim["exercise_minutes"]

        # 体重/心率
        if has_real["vitals"] and vitals:
            weight_records = [v for v in vitals if v.data_type == "weight" and v.weight_kg]
            hr_records = [v for v in vitals if v.pulse]
            summary["weight"] = weight_records[0].weight_kg if weight_records else 0
            summary["heartRate"] = hr_records[0].pulse if hr_records else 0
        else:
            sim = self._simulate_health_data(stage)
            summary["weight"] = sim["weight"]
            summary["heartRate"] = sim["heart_rate"]

        summary["highlights"] = highlights
        return summary

    # ── LLM + 规则引擎合并 ─────────────────────────────────────────────

    def _merge_llm_with_fallback(self, llm: Dict, fallback: Dict) -> Dict:
        """LLM 返回可能不完整, 用 fallback 基线补齐所有字段"""
        result = {}

        # diagnosis: 保证 sixReasons 有 6 项, evidence 有 4 项
        llm_dx = llm.get("diagnosis", {})
        fb_dx = fallback["diagnosis"]
        result["diagnosis"] = {
            "spiScore": llm_dx.get("spiScore") if isinstance(llm_dx.get("spiScore"), (int, float)) else fb_dx["spiScore"],
            "successRate": llm_dx.get("successRate") if isinstance(llm_dx.get("successRate"), (int, float)) else fb_dx["successRate"],
            "sixReasons": llm_dx.get("sixReasons") if isinstance(llm_dx.get("sixReasons"), list) and len(llm_dx.get("sixReasons", [])) >= 6 else fb_dx["sixReasons"],
            "problem": llm_dx.get("problem") or fb_dx["problem"],
            "difficulty": llm_dx.get("difficulty") if isinstance(llm_dx.get("difficulty"), int) and 1 <= llm_dx.get("difficulty", 0) <= 5 else fb_dx["difficulty"],
            "purpose": llm_dx.get("purpose") or fb_dx["purpose"],
            "evidence": llm_dx.get("evidence") if isinstance(llm_dx.get("evidence"), list) and len(llm_dx.get("evidence", [])) >= 3 else fb_dx["evidence"],
            "interventionAlert": llm_dx.get("interventionAlert") or fb_dx["interventionAlert"],
        }

        # prescription: 保证 phaseTags 有 4 项
        llm_rx = llm.get("prescription", {})
        fb_rx = fallback["prescription"]
        llm_phase = llm_rx.get("phase") if isinstance(llm_rx.get("phase"), dict) and llm_rx.get("phase", {}).get("current") else fb_rx["phase"]
        # Ensure week/total are int
        if isinstance(llm_phase.get("week"), str):
            try: llm_phase["week"] = int(llm_phase["week"])
            except (ValueError, TypeError): llm_phase["week"] = 1
        if isinstance(llm_phase.get("total"), str):
            try: llm_phase["total"] = int(llm_phase["total"])
            except (ValueError, TypeError): llm_phase["total"] = 12
        result["prescription"] = {
            "phase": llm_phase,
            "phaseTags": llm_rx.get("phaseTags") if isinstance(llm_rx.get("phaseTags"), list) and len(llm_rx.get("phaseTags", [])) >= 4 else fb_rx["phaseTags"],
            "targetBehaviors": llm_rx.get("targetBehaviors") if isinstance(llm_rx.get("targetBehaviors"), list) and len(llm_rx.get("targetBehaviors", [])) >= 2 else fb_rx["targetBehaviors"],
            "strategies": llm_rx.get("strategies") if isinstance(llm_rx.get("strategies"), list) and len(llm_rx.get("strategies", [])) >= 2 else fb_rx["strategies"],
        }

        # ai_suggestions: 至少 3 条
        llm_sug = llm.get("ai_suggestions", [])
        result["ai_suggestions"] = llm_sug if isinstance(llm_sug, list) and len(llm_sug) >= 3 else fallback["ai_suggestions"]

        # health_summary / intervention_plan: 优先 LLM, 回退 fallback
        result["health_summary"] = llm.get("health_summary") or fallback["health_summary"]
        result["intervention_plan"] = llm.get("intervention_plan") if isinstance(llm.get("intervention_plan"), dict) and llm.get("intervention_plan", {}).get("name") else fallback["intervention_plan"]

        # meta: 保留 LLM meta
        result["meta"] = llm.get("meta", {"source": "llm_merged", "llm_used": True})
        result["meta"]["source"] = "llm_merged"

        logger.info("[copilot-rx] LLM + fallback 合并完成")
        return result

    # ── LLM 分析 ──────────────────────────────────────────────────────

    def _call_llm_analysis(self, data: Dict) -> Optional[Dict]:
        """调用 UnifiedLLMClient 生成结构化诊断+处方 (快速失败 + 冷却缓存)"""
        import concurrent.futures
        import time as _time

        global _llm_last_fail_time
        # 冷却期内直接跳过
        now = _time.time()
        if _llm_last_fail_time > 0 and (now - _llm_last_fail_time) < _LLM_COOLDOWN:
            logger.info(f"[copilot-rx] LLM 冷却中 ({now - _llm_last_fail_time:.0f}s/{_LLM_COOLDOWN:.0f}s), 跳过")
            return None
        logger.info(f"[copilot-rx] 尝试 LLM 调用 (last_fail={_llm_last_fail_time})")

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(self._do_llm_call, data)
                result = future.result(timeout=25)
                if result is None:
                    _llm_last_fail_time = _time.time()
                return result
        except concurrent.futures.TimeoutError:
            logger.warning("[copilot-rx] LLM 总耗时超过 25s, 放弃 (进入冷却)")
            _llm_last_fail_time = _time.time()
            return None
        except Exception as e:
            logger.warning(f"[copilot-rx] LLM 调用异常: {e}")
            _llm_last_fail_time = _time.time()
            return None

    def _do_llm_call(self, data: Dict) -> Optional[Dict]:
        """实际 LLM 调用 (在子线程中运行)"""
        try:
            from core.llm_client import get_llm_client
            client = get_llm_client()
            # 快速检查: 如果云端无 API key 且本地也无, 直接跳过 (避免 10s 超时)
            cloud_has_key = hasattr(client, '_cloud') and client._cloud is not None and getattr(client._cloud, 'api_key', None)
            local_ok = hasattr(client, '_local_available') and client._local_available()
            if not cloud_has_key and not local_ok:
                logger.info("[copilot-rx] 无可用 LLM 后端, 跳过")
                return None
        except Exception:
            return None

        profile = data["profile"]
        stage = data["stage"]
        health = data["health"]
        micro = data["micro_actions"]

        # 提取 profile 字段 (兼容 ORM 对象和 dict)
        def _get(obj, attr, default=None):
            if isinstance(obj, dict):
                return obj.get(attr, default)
            return getattr(obj, attr, default)

        spi_score = _get(profile, "spi_score", 0) or 0
        bpt6_type = _get(profile, "bpt6_type", "mixed") or "mixed"
        capacity_weak = _get(profile, "capacity_weak", []) or []
        primary_domains = _get(profile, "primary_domains", []) or []
        stage_name = STAGE_NAMES.get(stage, stage)

        system_prompt = (
            "你是一位资深行为健康教练助手，精通 TTM 七阶段模型、BPT-6 行为类型学、"
            "CAPACITY 六因素评估和 SPI 成功预测指数。\n\n"
            "请根据学员数据生成结构化 JSON 诊断与处方。要求：\n"
            "1. 返回纯 JSON，不要包含 markdown 代码块标记\n"
            "2. 所有文本使用中文\n"
            "3. 严格遵循以下 JSON 结构：\n"
            '{\n'
            '  "diagnosis": {\n'
            '    "spiScore": <0-100整数>,\n'
            '    "successRate": <0-100整数>,\n'
            '    "sixReasons": [{"name":"<因素名>","score":<0-100>,"max":100,"isWeak":<bool>}],\n'
            '    "problem": "<核心问题一句话>",\n'
            '    "difficulty": <1-5整数>,\n'
            '    "purpose": "<干预目的>",\n'
            '    "evidence": [{"label":"<指标>","value":"<值>","status":"<normal/warning/danger>"}],\n'
            '    "interventionAlert": "<干预警示>"\n'
            '  },\n'
            '  "prescription": {\n'
            '    "phase": {"current":"<当前阶段>","week":<第几周int>,"total":<共几周int>},\n'
            '    "phaseTags": [{"label":"<阶段名>","done":<bool>,"active":<bool>}],\n'
            '    "targetBehaviors": [{"name":"<行为>","progress":<0-100>,"target":"<目标描述>","currentDays":<天数>}],\n'
            '    "strategies": [{"label":"<策略>","type":"<info/success/warning/processing>"}]\n'
            '  },\n'
            '  "ai_suggestions": [{"id":"<id>","title":"<标题>","content":"<详细建议>","type":"<behavior/assessment/risk/coaching>","priority":"<high/medium/low>"}],\n'
            '  "intervention_plan": {\n'
            '    "name": "<方案名称>",\n'
            '    "description": "<方案描述>",\n'
            '    "domains": ["<领域>"],\n'
            '    "tone": "<语气>",\n'
            '    "scripts": {"opening":"<开场白>","motivation":"<动机激发>","closing":"<结束语>"}\n'
            '  }\n'
            '}'
        )

        user_message = (
            f"## 学员信息\n"
            f"- 当前阶段: {stage} ({stage_name})\n"
            f"- SPI 分数: {spi_score}\n"
            f"- BPT-6 类型: {bpt6_type}\n"
            f"- CAPACITY 弱项: {', '.join(capacity_weak) if capacity_weak else '无'}\n"
            f"- 关注领域: {', '.join(primary_domains) if primary_domains else '综合'}\n\n"
            f"## 健康数据\n"
            f"- 空腹血糖: {health.get('fastingGlucose', 0)} mmol/L\n"
            f"- 餐后血糖: {health.get('postprandialGlucose', 0)} mmol/L\n"
            f"- 体重: {health.get('weight', 0)} kg\n"
            f"- 周运动: {health.get('exerciseMinutes', 0)} 分钟\n"
            f"- 睡眠: {health.get('sleepHours', 0)} 小时/天\n"
            f"- 心率: {health.get('heartRate', 0)} bpm\n"
            f"- 健康提示: {', '.join(health.get('highlights', [])) or '无'}\n\n"
            f"## 微行动完成\n"
            f"- 7天总任务: {micro['total']}, 已完成: {micro['completed']}\n\n"
            f"请生成诊断评估和行为处方。"
        )

        try:
            resp = client.chat(
                system=system_prompt,
                user=user_message,
                temperature=0.3,
                timeout=20.0,
            )
            if not resp.success:
                logger.warning(f"[copilot-rx] LLM 返回失败: {resp.error}")
                return None

            # 解析 JSON (自动去除 markdown 代码块)
            content = resp.content.strip()
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)

            parsed = json.loads(content)

            # 补充 health_summary (LLM 不返回此字段，用采集数据)
            parsed["health_summary"] = data["health"]
            parsed.setdefault("meta", {})
            parsed["meta"]["source"] = "llm"
            parsed["meta"]["llm_used"] = True
            parsed["meta"]["model"] = resp.model
            parsed["meta"]["provider"] = resp.provider

            logger.info(
                f"[copilot-rx] LLM 生成成功: model={resp.model}, "
                f"latency={resp.latency_ms}ms"
            )
            return parsed

        except json.JSONDecodeError as e:
            logger.warning(f"[copilot-rx] LLM 返回非法 JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"[copilot-rx] LLM 调用异常: {e}")
            return None

    # ── 规则引擎降级 ──────────────────────────────────────────────────

    def _build_fallback_response(self, data: Dict) -> Dict:
        """LLM 不可用时走规则引擎生成结构化响应"""
        profile = data["profile"]
        stage = data["stage"]
        health = data["health"]
        micro = data["micro_actions"]

        def _get(obj, attr, default=None):
            if isinstance(obj, dict):
                return obj.get(attr, default)
            return getattr(obj, attr, default)

        spi_score = _get(profile, "spi_score", 0) or 0
        bpt6_type = _get(profile, "bpt6_type", "mixed") or "mixed"
        capacity_weak = _get(profile, "capacity_weak", []) or []
        primary_domains = _get(profile, "primary_domains", ["nutrition", "exercise"]) or ["nutrition", "exercise"]

        stage_name = STAGE_NAMES.get(stage, stage)
        phase_name = STAGE_TO_PHASE.get(stage, "认知唤醒")

        # ── diagnosis ──
        six_reasons = self._build_six_reasons(capacity_weak)
        success_rate = max(10, min(90, int(spi_score * 0.8 + 10)))
        difficulty = self._stage_to_difficulty(stage)

        evidence = [
            {"label": "空腹血糖", "value": f"{health.get('fastingGlucose', 0)} mmol/L",
             "status": "warning" if health.get("fastingGlucose", 0) > 7.0 else "normal"},
            {"label": "餐后血糖", "value": f"{health.get('postprandialGlucose', 0)} mmol/L",
             "status": "warning" if health.get("postprandialGlucose", 0) > 11.1 else "normal"},
            {"label": "周运动量", "value": f"{health.get('exerciseMinutes', 0)} 分钟",
             "status": "warning" if health.get("exerciseMinutes", 0) < 150 else "normal"},
            {"label": "睡眠时长", "value": f"{health.get('sleepHours', 0)} 小时/天",
             "status": "warning" if health.get("sleepHours", 0) < 7 else "normal"},
        ]

        diagnosis = {
            "spiScore": int(spi_score),
            "successRate": success_rate,
            "sixReasons": six_reasons,
            "problem": self._generate_problem(stage, bpt6_type, health),
            "difficulty": difficulty,
            "purpose": self._generate_purpose(stage, primary_domains),
            "evidence": evidence,
            "interventionAlert": self._generate_alert(stage, health),
        }

        # ── prescription ──
        phase_tags = self._build_phase_tags(stage)
        target_behaviors = self._build_target_behaviors(stage, primary_domains, micro)
        strategies = self._build_strategies(stage, bpt6_type, capacity_weak)

        prescription = {
            "phase": {
                "current": phase_name,
                "week": random.randint(1, 4),
                "total": 12,
            },
            "phaseTags": phase_tags,
            "targetBehaviors": target_behaviors,
            "strategies": strategies,
        }

        # ── ai_suggestions ──
        ai_suggestions = self._build_suggestions(stage, bpt6_type, health, capacity_weak)

        # ── intervention_plan (从 InterventionMatcher) ──
        intervention_plan = self._build_intervention_plan(
            data["user"], stage, primary_domains, spi_score
        )

        return {
            "diagnosis": diagnosis,
            "prescription": prescription,
            "ai_suggestions": ai_suggestions,
            "health_summary": health,
            "intervention_plan": intervention_plan,
            "meta": {"source": "fallback", "llm_used": False},
        }

    # ── 辅助构建方法 ──────────────────────────────────────────────────

    def _build_six_reasons(self, capacity_weak: List[str]) -> List[Dict]:
        """CAPACITY 弱项 → 六因素分数映射"""
        weak_keys = set()
        for w in capacity_weak:
            # 格式: "A2_资源" or "T_时间" → 取下划线前部分
            key = w.split("_")[0] if "_" in w else w
            weak_keys.add(key)

        reasons = []
        for factor in CAPACITY_FACTORS:
            is_weak = factor["key"] in weak_keys
            score = random.randint(15, 40) if is_weak else random.randint(55, 90)
            reasons.append({
                "name": factor["name"],
                "score": score,
                "max": 100,
                "isWeak": is_weak,
            })
        return reasons

    def _stage_to_difficulty(self, stage: str) -> int:
        """阶段 → 干预难度 1-5"""
        mapping = {"S0": 5, "S1": 5, "S2": 4, "S3": 3, "S4": 2, "S5": 2, "S6": 1}
        return mapping.get(stage, 3)

    def _generate_problem(self, stage: str, bpt6: str, health: Dict) -> str:
        """生成核心问题描述"""
        stage_problems = {
            "S0": "学员尚无健康管理意识，完全处于无知无觉状态",
            "S1": "学员存在强烈抗拒心理，对行为改变持防御态度",
            "S2": "学员口头承诺但缺乏内在动力，行为改变被动",
            "S3": "学员勉强接受改变但执行不稳定，容易反复",
            "S4": "学员主动尝试中，需要巩固新建立的行为模式",
            "S5": "学员已形成规律，需防止倦怠和环境干扰",
            "S6": "学员已内化健康行为，维护和深化阶段",
        }
        base = stage_problems.get(stage, "行为改变过程中存在多维度挑战")
        highlights = health.get("highlights", [])
        if highlights:
            base += f"，同时{highlights[0]}"
        return base

    def _generate_purpose(self, stage: str, domains: List[str]) -> str:
        """生成干预目的"""
        domain_names = {
            "nutrition": "营养管理", "exercise": "运动习惯", "sleep": "睡眠质量",
            "emotion": "情绪调节", "stress": "压力管理", "cognitive": "认知提升",
            "social": "社交支持", "tcm": "中医调理",
        }
        domain_str = "、".join(domain_names.get(d, d) for d in domains[:3])
        phase = STAGE_TO_PHASE.get(stage, "认知唤醒")
        return f"通过{phase}策略，帮助学员在{domain_str}等领域建立可持续的行为改变"

    def _generate_alert(self, stage: str, health: Dict) -> str:
        """生成干预警示"""
        alerts = []
        if health.get("fastingGlucose", 0) > 7.0:
            alerts.append("空腹血糖持续偏高，需关注用药依从性")
        if health.get("sleepHours", 0) < 6:
            alerts.append("睡眠严重不足，可能影响血糖控制和情绪稳定")
        if health.get("exerciseMinutes", 0) < 60:
            alerts.append("运动量极低，建议从 5 分钟散步开始")
        if stage in ("S0", "S1"):
            alerts.append("学员处于抵触期，避免直接说教，以共情为主")
        return "；".join(alerts) if alerts else "当前无特殊警示，保持常规跟进频率"

    def _build_phase_tags(self, stage: str) -> List[Dict]:
        """构建干预阶段标签"""
        phases = ["认知唤醒", "动机激发", "行为塑造", "习惯强化"]
        stage_phase_idx = {"S0": 0, "S1": 0, "S2": 1, "S3": 2, "S4": 3, "S5": 3, "S6": 3}
        current_idx = stage_phase_idx.get(stage, 0)
        return [
            {"label": p, "done": i < current_idx, "active": i == current_idx}
            for i, p in enumerate(phases)
        ]

    def _build_target_behaviors(
        self, stage: str, domains: List[str], micro: Dict
    ) -> List[Dict]:
        """生成目标行为列表"""
        behavior_templates = {
            "nutrition": {"name": "规律三餐+控制精制碳水", "target": "每日三餐定时，精制碳水占比<30%"},
            "exercise": {"name": "每日步行30分钟", "target": "每周累计中等强度运动≥150分钟"},
            "sleep": {"name": "22:30前入睡", "target": "每晚睡眠≥7小时，入睡潜伏期<20分钟"},
            "emotion": {"name": "情绪日记+呼吸练习", "target": "每日记录情绪，每周3次呼吸练习"},
            "stress": {"name": "工间微休息", "target": "每2小时休息5分钟，每周压力评分下降"},
            "cognitive": {"name": "健康知识学习", "target": "每周完成2篇健康课程学习"},
            "social": {"name": "同伴支持互动", "target": "每周与同道者交流≥2次"},
            "tcm": {"name": "体质调理方案", "target": "按中医体质方案执行日常调理"},
        }

        completion = micro["completed"] / max(micro["total"], 1) * 100
        behaviors = []
        for domain in domains[:4]:
            tmpl = behavior_templates.get(domain, {"name": f"{domain}行为改善", "target": "持续改善"})
            stage_progress_base = {"S0": 0, "S1": 5, "S2": 15, "S3": 30, "S4": 50, "S5": 70, "S6": 90}
            base_progress = stage_progress_base.get(stage, 20)
            progress = min(100, int(base_progress + completion * 0.3))
            behaviors.append({
                "name": tmpl["name"],
                "progress": progress,
                "target": tmpl["target"],
                "currentDays": random.randint(1, 21),
            })
        return behaviors

    def _build_strategies(
        self, stage: str, bpt6: str, capacity_weak: List[str]
    ) -> List[Dict]:
        """生成干预策略标签"""
        base_strategies = {
            "S0": [("健康教育", "info"), ("环境暗示", "processing")],
            "S1": [("动机式访谈", "warning"), ("共情倾听", "info")],
            "S2": [("目标设置", "success"), ("承诺强化", "processing")],
            "S3": [("行为塑造", "success"), ("自我监控", "info"), ("社会支持", "processing")],
            "S4": [("习惯堆叠", "success"), ("正向反馈", "info"), ("应对计划", "warning")],
            "S5": [("复发预防", "warning"), ("身份认同", "success"), ("灵活调整", "processing")],
            "S6": [("维持巩固", "success"), ("导师角色", "info")],
        }
        strategies = [
            {"label": s[0], "type": s[1]}
            for s in base_strategies.get(stage, [("综合干预", "info")])
        ]

        # 根据 BPT-6 类型追加
        bpt6_extra = {
            "action": ("行为激活", "success"),
            "knowledge": ("认知重构", "info"),
            "emotion": ("情绪调节", "warning"),
            "relation": ("社交赋能", "processing"),
            "environment": ("环境优化", "processing"),
        }
        extra = bpt6_extra.get(bpt6)
        if extra and len(strategies) < 5:
            strategies.append({"label": extra[0], "type": extra[1]})

        return strategies[:5]

    def _build_suggestions(
        self, stage: str, bpt6: str, health: Dict, capacity_weak: List[str]
    ) -> List[Dict]:
        """生成 AI 诊断建议 3-5 条"""
        suggestions = []
        idx = 1

        # 基于阶段的建议
        stage_suggestions = {
            "S0": {"title": "认知唤醒建议", "content": "学员处于无意识期，建议通过健康风险评估报告引起重视，避免直接行为要求", "type": "coaching", "priority": "high"},
            "S1": {"title": "抗拒应对策略", "content": "使用动机式访谈技术，探索学员矛盾心理，避免说教和对抗", "type": "coaching", "priority": "high"},
            "S2": {"title": "动机内化引导", "content": "帮助学员将外部动机转化为内在动机，通过自主选择增强控制感", "type": "behavior", "priority": "medium"},
            "S3": {"title": "行为塑造支持", "content": "设置微小可执行目标，建立成功体验循环，逐步提高难度", "type": "behavior", "priority": "medium"},
            "S4": {"title": "习惯巩固方案", "content": "引入习惯堆叠技术，将新行为与已有习惯绑定，建立触发-行为-奖励闭环", "type": "behavior", "priority": "medium"},
            "S5": {"title": "复发预防提醒", "content": "识别高风险情境，提前制定应对策略，保持定期回顾", "type": "risk", "priority": "low"},
            "S6": {"title": "自主维持支持", "content": "逐步减少干预频率，鼓励学员发展导师角色，分享经验", "type": "coaching", "priority": "low"},
        }
        s = stage_suggestions.get(stage, stage_suggestions["S3"])
        suggestions.append({"id": f"sug_{idx}", **s})
        idx += 1

        # 基于健康指标的建议
        if health.get("fastingGlucose", 0) > 7.0:
            suggestions.append({
                "id": f"sug_{idx}", "title": "血糖管理优化",
                "content": "空腹血糖偏高，建议评估用药依从性，同时关注晚餐碳水摄入和餐后运动",
                "type": "assessment", "priority": "high",
            })
            idx += 1

        if health.get("sleepHours", 0) < 7:
            suggestions.append({
                "id": f"sug_{idx}", "title": "睡眠质量改善",
                "content": "睡眠不足会影响胰岛素敏感性和情绪调控，建议优先建立睡前仪式",
                "type": "behavior", "priority": "medium",
            })
            idx += 1

        if health.get("exerciseMinutes", 0) < 100:
            suggestions.append({
                "id": f"sug_{idx}", "title": "运动处方调整",
                "content": "运动量偏低，建议从每日5分钟餐后散步起步，逐周增加",
                "type": "behavior", "priority": "medium",
            })
            idx += 1

        # 确保至少 3 条
        if len(suggestions) < 3:
            suggestions.append({
                "id": f"sug_{idx}", "title": "综合评估建议",
                "content": "建议安排一次全面 BAPS 评估，更新行为画像数据以优化干预方案",
                "type": "assessment", "priority": "low",
            })

        return suggestions[:5]

    def _build_intervention_plan(
        self, user, stage: str, domains: List[str], spi_score: float
    ) -> Dict:
        """尝试用 InterventionMatcher 生成干预方案，失败则静态构建"""
        try:
            from core.intervention_matcher import InterventionMatcher
            matcher = InterventionMatcher()
            plan = matcher.match(
                user_id=user.id if hasattr(user, "id") else 0,
                current_stage=stage,
                psychological_level="L2",
                bpt6_type="mixed",
                spi_score=spi_score,
                target_domains=domains[:3],
            )
            if plan.domain_interventions:
                di = plan.domain_interventions[0]
                return {
                    "name": di.rx_name or f"{di.domain_name}干预方案",
                    "description": di.core_goal or f"基于{STAGE_NAMES.get(stage, stage)}阶段的{di.domain_name}专项干预",
                    "domains": [d.domain for d in plan.domain_interventions],
                    "tone": di.tone,
                    "scripts": di.scripts,
                }
        except Exception as e:
            logger.debug(f"[copilot-rx] InterventionMatcher 不可用: {e}")

        # 静态降级
        phase = STAGE_TO_PHASE.get(stage, "认知唤醒")
        return {
            "name": f"{phase}综合干预方案",
            "description": f"针对{STAGE_NAMES.get(stage, stage)}阶段学员的综合行为健康干预方案",
            "domains": domains[:3],
            "tone": "gentle_accepting" if stage in ("S0", "S1") else "encouraging_practical",
            "scripts": {
                "opening": f"你好，看到你最近的数据变化，想和你聊聊目前的感受和想法。",
                "motivation": f"每一步小进步都是有意义的。我们一起来看看哪些方面可以做些小调整。",
                "closing": f"今天聊的内容不需要一下子全做到，选一个你觉得最容易开始的，我们下次再看效果。",
            },
        }

    # ── 模拟数据生成 ──────────────────────────────────────────────────

    def _simulate_profile(self, user) -> Dict:
        """为无 BehavioralProfile 的学员生成模拟画像"""
        stage = getattr(user, "current_stage", "S1") or "S1"
        spi_range = STAGE_SPI_RANGE.get(stage, (10, 25))
        return {
            "current_stage": stage,
            "spi_score": random.randint(*spi_range),
            "bpt6_type": random.choice(["action", "knowledge", "emotion", "relation", "mixed"]),
            "capacity_weak": random.sample(["C_信心", "A_能力", "P_感知", "A2_资源", "I_兴趣", "T_时间"], 2),
            "primary_domains": random.sample(["nutrition", "exercise", "sleep", "emotion", "stress"], 3),
            "risk_flags": [],
        }

    def _simulate_health_data(self, stage: str) -> Dict:
        """生成阶段匹配的模拟健康数据"""
        # 早期阶段指标较差，后期较好
        stage_idx = int(stage[1]) if len(stage) == 2 and stage[1].isdigit() else 1
        improvement = stage_idx / 6  # 0.0 ~ 1.0

        return {
            "fasting_glucose": round(8.5 - improvement * 3.0 + random.uniform(-0.5, 0.5), 1),
            "postprandial_glucose": round(13.0 - improvement * 4.0 + random.uniform(-1.0, 1.0), 1),
            "weight": round(78 - improvement * 8 + random.uniform(-2, 2), 1),
            "exercise_minutes": int(30 + improvement * 200 + random.randint(-20, 20)),
            "sleep_hours": round(5.5 + improvement * 2.5 + random.uniform(-0.5, 0.5), 1),
            "heart_rate": int(85 - improvement * 15 + random.randint(-5, 5)),
        }
