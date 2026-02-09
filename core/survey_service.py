# -*- coding: utf-8 -*-
"""
问卷引擎核心服务

职责:
  - 问卷CRUD + 状态机
  - 短链生成
  - 回收 + 自动评分
  - BAPS回流
  - 统计与导出
"""
import string
import random
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func, select

from core.models import (
    Survey, SurveyQuestion, SurveyResponse, SurveyResponseAnswer,
    SurveyDistribution, SurveyStatus, SurveyType, QuestionType,
    DistributionChannel, BehavioralProfile,
)

logger = logging.getLogger(__name__)

CHARSET = string.ascii_letters + string.digits


def generate_short_code(length: int = 6) -> str:
    """生成 6 位短链码 (62^6 ≈ 568亿种组合)"""
    return ''.join(random.choices(CHARSET, k=length))


class SurveyService:

    def __init__(self, db: Session):
        self.db = db

    # ── 创建 ──
    def create_survey(self, data: dict, user_id: int) -> Survey:
        short_code = generate_short_code()
        while self.db.query(Survey).filter(Survey.short_code == short_code).first():
            short_code = generate_short_code()

        survey = Survey(
            title=data["title"],
            description=data.get("description", ""),
            survey_type=data.get("survey_type", "general"),
            status=SurveyStatus.draft,
            created_by=user_id,
            tenant_id=data.get("tenant_id"),
            settings=data.get("settings", {}),
            baps_mapping=data.get("baps_mapping"),
            short_code=short_code,
        )
        self.db.add(survey)
        self.db.flush()

        if "questions" in data:
            self._save_questions(survey.id, data["questions"])

        self.db.commit()
        self.db.refresh(survey)
        return survey

    # ── 获取详情 ──
    def get_survey(self, survey_id: int) -> Optional[Survey]:
        return self.db.query(Survey).filter(Survey.id == survey_id).first()

    # ── 列表 ──
    def list_surveys(self, user_id: int, status: Optional[str] = None, skip: int = 0, limit: int = 20) -> Tuple[List[Survey], int]:
        q = self.db.query(Survey).filter(Survey.created_by == user_id)
        if status:
            q = q.filter(Survey.status == status)
        total = q.count()
        surveys = q.order_by(Survey.created_at.desc()).offset(skip).limit(limit).all()
        return surveys, total

    # ── 更新 ──
    def update_survey(self, survey_id: int, user_id: int, data: dict) -> Survey:
        survey = self._get_owned(survey_id, user_id)
        if survey.status != SurveyStatus.draft:
            for field in ("title", "description", "survey_type"):
                data.pop(field, None)

        for field in ("title", "description", "settings", "baps_mapping", "survey_type"):
            if field in data:
                setattr(survey, field, data[field])
        survey.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(survey)
        return survey

    # ── 删除 ──
    def delete_survey(self, survey_id: int, user_id: int):
        survey = self._get_owned(survey_id, user_id)
        if survey.status not in (SurveyStatus.draft, SurveyStatus.archived):
            raise ValueError("只能删除草稿或已归档的问卷")
        self.db.delete(survey)
        self.db.commit()

    # ── 发布 ──
    def publish_survey(self, survey_id: int, user_id: int) -> Survey:
        survey = self._get_owned(survey_id, user_id)
        if survey.status != SurveyStatus.draft:
            raise ValueError(f"只能发布草稿状态的问卷, 当前: {survey.status.value}")
        q_count = self.db.query(SurveyQuestion).filter(
            SurveyQuestion.survey_id == survey_id,
            SurveyQuestion.question_type.notin_(["section_break", "description"]),
        ).count()
        if q_count == 0:
            raise ValueError("问卷至少需要 1 道题目才能发布")
        survey.status = SurveyStatus.published
        survey.published_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(survey)
        return survey

    # ── 关闭 ──
    def close_survey(self, survey_id: int, user_id: int) -> Survey:
        survey = self._get_owned(survey_id, user_id)
        if survey.status != SurveyStatus.published:
            raise ValueError("只能关闭已发布的问卷")
        survey.status = SurveyStatus.closed
        survey.closed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(survey)
        return survey

    # ── 公开获取 (短链) ──
    def get_by_short_code(self, code: str) -> dict:
        survey = self.db.query(Survey).filter(Survey.short_code == code).first()
        if not survey:
            raise ValueError("问卷不存在")
        if survey.status != SurveyStatus.published:
            raise ValueError("问卷未开放")

        settings = survey.settings or {}
        now = datetime.utcnow()
        if settings.get("start_time"):
            if now < datetime.fromisoformat(settings["start_time"]):
                raise ValueError("问卷尚未开放")
        if settings.get("end_time"):
            if now > datetime.fromisoformat(settings["end_time"]):
                raise ValueError("问卷已截止")
        if settings.get("max_responses") and survey.response_count >= settings["max_responses"]:
            raise ValueError("问卷已达最大回收数")

        questions = self.db.query(SurveyQuestion).filter(
            SurveyQuestion.survey_id == survey.id
        ).order_by(SurveyQuestion.sort_order).all()

        return {
            "survey": survey,
            "questions": questions,
            "estimated_minutes": max(1, len(questions) * 0.5),
        }

    # ── 提交回答 ──
    def submit_response(
        self, short_code: str, answers: List[dict],
        user_id: Optional[int] = None, meta: dict = None
    ) -> Tuple["SurveyResponse", bool]:
        survey_data = self.get_by_short_code(short_code)
        survey = survey_data["survey"]
        settings = survey.settings or {}

        if settings.get("one_response_per_user") and user_id:
            existing = self.db.query(SurveyResponse).filter(
                SurveyResponse.survey_id == survey.id,
                SurveyResponse.user_id == user_id,
                SurveyResponse.is_complete == True,
            ).first()
            if existing:
                raise ValueError("您已提交过此问卷")

        meta = meta or {}
        response = SurveyResponse(
            survey_id=survey.id,
            user_id=user_id,
            respondent_ip=meta.get("ip"),
            respondent_ua=meta.get("user_agent"),
            device_type=meta.get("device_type", "unknown"),
            duration_sec=meta.get("duration_sec"),
            is_complete=True,
            completed_at=datetime.utcnow(),
        )
        self.db.add(response)
        self.db.flush()

        q_map = {q.id: q for q in survey_data["questions"]}
        for ans in answers:
            qid = ans["question_id"]
            q = q_map.get(qid)
            if not q:
                continue
            score = self._calc_score(q, ans["answer_value"])
            answer = SurveyResponseAnswer(
                response_id=response.id,
                question_id=qid,
                answer_value=ans["answer_value"],
                score=score,
            )
            self.db.add(answer)

        survey.response_count = (survey.response_count or 0) + 1
        self.db.commit()

        # BAPS 回流
        baps_synced = False
        if survey.baps_mapping and survey.baps_mapping.get("enabled") and user_id:
            try:
                self._sync_to_baps(survey, answers, user_id)
                response.baps_synced = True
                response.baps_synced_at = datetime.utcnow()
                self.db.commit()
                baps_synced = True
            except Exception as e:
                logger.warning(f"BAPS回流失败: {e}")

        self.db.refresh(response)
        return response, baps_synced

    # ── 暂存 (断点续填) ──
    def save_draft_response(
        self, short_code: str, answers: List[dict],
        current_page: int = 0, user_id: Optional[int] = None,
    ) -> SurveyResponse:
        survey_data = self.get_by_short_code(short_code)
        survey = survey_data["survey"]

        # 查找已有的未完成记录
        existing = None
        if user_id:
            existing = self.db.query(SurveyResponse).filter(
                SurveyResponse.survey_id == survey.id,
                SurveyResponse.user_id == user_id,
                SurveyResponse.is_complete == False,
            ).first()

        if existing:
            response = existing
            # 删除旧答案，重写
            self.db.query(SurveyResponseAnswer).filter(
                SurveyResponseAnswer.response_id == response.id
            ).delete()
        else:
            response = SurveyResponse(
                survey_id=survey.id,
                user_id=user_id,
                is_complete=False,
            )
            self.db.add(response)
            self.db.flush()

        response.current_page = current_page

        q_map = {q.id: q for q in survey_data["questions"]}
        for ans in answers:
            qid = ans["question_id"]
            q = q_map.get(qid)
            if not q:
                continue
            answer = SurveyResponseAnswer(
                response_id=response.id,
                question_id=qid,
                answer_value=ans["answer_value"],
                score=self._calc_score(q, ans["answer_value"]),
            )
            self.db.add(answer)

        self.db.commit()
        self.db.refresh(response)
        return response

    # ── 题目管理 ──
    def save_questions(self, survey_id: int, user_id: int, questions: List[dict]) -> int:
        survey = self._get_owned(survey_id, user_id)
        if survey.status != SurveyStatus.draft:
            raise ValueError("只能在草稿状态修改题目")
        # 全量替换
        self.db.query(SurveyQuestion).filter(SurveyQuestion.survey_id == survey_id).delete()
        self._save_questions(survey_id, questions)
        self.db.commit()
        return len(questions)

    def reorder_questions(self, survey_id: int, user_id: int, question_ids: List[int]):
        self._get_owned(survey_id, user_id)
        for idx, qid in enumerate(question_ids):
            self.db.query(SurveyQuestion).filter(
                SurveyQuestion.id == qid, SurveyQuestion.survey_id == survey_id
            ).update({"sort_order": idx})
        self.db.commit()

    def delete_question(self, survey_id: int, user_id: int, question_id: int):
        survey = self._get_owned(survey_id, user_id)
        if survey.status != SurveyStatus.draft:
            raise ValueError("只能在草稿状态删除题目")
        self.db.query(SurveyQuestion).filter(
            SurveyQuestion.id == question_id, SurveyQuestion.survey_id == survey_id
        ).delete()
        self.db.commit()

    # ── 统计 ──
    def get_stats(self, survey_id: int) -> dict:
        survey = self.db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            raise ValueError("问卷不存在")

        questions = self.db.query(SurveyQuestion).filter(
            SurveyQuestion.survey_id == survey_id
        ).order_by(SurveyQuestion.sort_order).all()

        total = self.db.query(func.count(SurveyResponse.id)).filter(
            SurveyResponse.survey_id == survey_id
        ).scalar() or 0
        complete = self.db.query(func.count(SurveyResponse.id)).filter(
            SurveyResponse.survey_id == survey_id,
            SurveyResponse.is_complete == True,
        ).scalar() or 0
        avg_dur = self.db.query(func.avg(SurveyResponse.duration_sec)).filter(
            SurveyResponse.survey_id == survey_id,
            SurveyResponse.is_complete == True,
        ).scalar()

        question_stats = []
        for q in questions:
            if q.question_type.value in ("section_break", "description"):
                continue
            stats = self._question_stats(q)
            question_stats.append(stats)

        return {
            "survey_id": survey_id,
            "summary": {
                "total_responses": total,
                "complete_responses": complete,
                "completion_rate": round(complete / total, 3) if total > 0 else 0,
                "avg_duration_sec": int(avg_dur or 0),
            },
            "questions": question_stats,
        }

    # ── 回收列表 ──
    def list_responses(self, survey_id: int, skip: int = 0, limit: int = 20) -> Tuple[List[dict], int]:
        total = self.db.query(func.count(SurveyResponse.id)).filter(
            SurveyResponse.survey_id == survey_id,
            SurveyResponse.is_complete == True,
        ).scalar() or 0

        responses = self.db.query(SurveyResponse).filter(
            SurveyResponse.survey_id == survey_id,
            SurveyResponse.is_complete == True,
        ).order_by(SurveyResponse.created_at.desc()).offset(skip).limit(limit).all()

        result = []
        for resp in responses:
            answers = self.db.query(SurveyResponseAnswer).filter(
                SurveyResponseAnswer.response_id == resp.id
            ).all()
            result.append({
                "id": resp.id,
                "user_id": resp.user_id,
                "device_type": resp.device_type,
                "duration_sec": resp.duration_sec,
                "completed_at": resp.completed_at.isoformat() if resp.completed_at else None,
                "baps_synced": resp.baps_synced,
                "answers": {a.question_id: a.answer_value for a in answers},
            })
        return result, total

    # ── 导出 CSV ──
    def export_csv(self, survey_id: int) -> bytes:
        import csv
        import io

        questions = self.db.query(SurveyQuestion).filter(
            SurveyQuestion.survey_id == survey_id
        ).order_by(SurveyQuestion.sort_order).all()

        real_qs = [q for q in questions if q.question_type.value not in ("section_break", "description")]

        headers = ["回收ID", "填写者", "填写时间", "耗时(秒)"]
        headers.extend([q.title[:50] for q in real_qs])

        responses = self.db.query(SurveyResponse).filter(
            SurveyResponse.survey_id == survey_id,
            SurveyResponse.is_complete == True,
        ).order_by(SurveyResponse.created_at).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)

        for resp in responses:
            answers = self.db.query(SurveyResponseAnswer).filter(
                SurveyResponseAnswer.response_id == resp.id
            ).all()
            answer_map = {a.question_id: a for a in answers}

            row = [resp.id, resp.user_id or "匿名", str(resp.completed_at or ""), resp.duration_sec]
            for q in real_qs:
                a = answer_map.get(q.id)
                row.append(self._answer_to_text(q, a) if a else "")
            writer.writerow(row)

        return output.getvalue().encode("utf-8-sig")

    # ═══════════ 私有方法 ═══════════

    def _get_owned(self, survey_id: int, user_id: int) -> Survey:
        survey = self.db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            raise ValueError("问卷不存在")
        if survey.created_by != user_id:
            raise ValueError("无权操作此问卷")
        return survey

    def _save_questions(self, survey_id: int, questions: List[dict]):
        for idx, q_data in enumerate(questions):
            q = SurveyQuestion(
                survey_id=survey_id,
                question_type=q_data["question_type"],
                sort_order=idx,
                title=q_data["title"],
                description=q_data.get("description", ""),
                is_required=q_data.get("is_required", False),
                config=q_data.get("config", {}),
                skip_logic=q_data.get("skip_logic"),
            )
            self.db.add(q)

    @staticmethod
    def _calc_score(question: SurveyQuestion, answer_value: dict) -> Optional[float]:
        config = question.config or {}
        qtype = question.question_type.value

        if qtype == "single_choice":
            options = {o["id"]: o.get("score") for o in config.get("options", [])}
            return options.get(answer_value.get("selected"))

        if qtype in ("rating", "nps", "slider"):
            return answer_value.get("value")

        if qtype == "matrix_single":
            columns = {c["id"]: c.get("score", 0) for c in config.get("columns", [])}
            scores = [columns.get(v, 0) for v in answer_value.values()]
            return sum(scores) / len(scores) if scores else None

        return None

    def _sync_to_baps(self, survey: Survey, answers: List[dict], user_id: int):
        mapping = survey.baps_mapping
        if not mapping or not mapping.get("mappings"):
            return

        profile = self.db.query(BehavioralProfile).filter(
            BehavioralProfile.user_id == user_id
        ).first()
        if not profile:
            return

        answer_map = {a["question_id"]: a["answer_value"] for a in answers}
        for m in mapping["mappings"]:
            qid = m["question_id"]
            if qid not in answer_map:
                continue
            raw_value = answer_map[qid]
            target = m["target_field"]
            transform = m.get("transform", "direct")
            value = self._transform_value(raw_value, transform, m)
            if value is not None and hasattr(profile, target):
                setattr(profile, target, value)

        self.db.flush()

    @staticmethod
    def _transform_value(raw_value: dict, transform: str, mapping: dict):
        if transform == "direct":
            return raw_value.get("value") or raw_value.get("selected")
        if transform == "scale_1_5_to_1_10":
            v = raw_value.get("value")
            return v * 2 if v else None
        if transform == "option_to_number":
            return raw_value.get("score")
        if transform == "matrix_row":
            row_id = mapping.get("row_id")
            return raw_value.get(row_id)
        return None

    def _question_stats(self, question: SurveyQuestion) -> dict:
        answers = self.db.query(SurveyResponseAnswer).filter(
            SurveyResponseAnswer.question_id == question.id
        ).all()

        qtype = question.question_type.value
        config = question.config or {}
        stats: Dict[str, Any] = {}

        if qtype in ("single_choice", "multiple_choice"):
            option_counts: Dict[str, int] = {}
            for opt in config.get("options", []):
                option_counts[opt["id"]] = 0
            for a in answers:
                val = a.answer_value or {}
                if qtype == "single_choice":
                    sel = val.get("selected")
                    if sel in option_counts:
                        option_counts[sel] += 1
                else:
                    for sel in val.get("selected", []):
                        if sel in option_counts:
                            option_counts[sel] += 1
            total_ans = len(answers)
            stats["options"] = [
                {
                    "id": opt["id"], "text": opt.get("text", ""),
                    "count": option_counts.get(opt["id"], 0),
                    "percent": round(option_counts.get(opt["id"], 0) / total_ans, 3) if total_ans else 0,
                }
                for opt in config.get("options", [])
            ]

        elif qtype in ("rating", "slider"):
            values = [a.answer_value.get("value") for a in answers if a.answer_value and a.answer_value.get("value") is not None]
            stats["avg"] = round(sum(values) / len(values), 2) if values else 0
            stats["min"] = min(values) if values else 0
            stats["max"] = max(values) if values else 0
            stats["count"] = len(values)

        elif qtype == "nps":
            values = [a.answer_value.get("value") for a in answers if a.answer_value and a.answer_value.get("value") is not None]
            promoters = len([v for v in values if v >= 9])
            passives = len([v for v in values if 7 <= v <= 8])
            detractors = len([v for v in values if v <= 6])
            total_nps = len(values)
            nps_score = round((promoters - detractors) / total_nps * 100) if total_nps else 0
            stats = {"nps_score": nps_score, "promoters": promoters, "passives": passives, "detractors": detractors}

        elif qtype == "matrix_single":
            rows = config.get("rows", [])
            columns = config.get("columns", [])
            row_stats = []
            for row in rows:
                col_counts = {c["id"]: 0 for c in columns}
                for a in answers:
                    sel = (a.answer_value or {}).get(row["id"])
                    if sel in col_counts:
                        col_counts[sel] += 1
                col_scores = [c.get("score", 0) for c in columns]
                total_row = sum(col_counts.values())
                avg_score = 0
                if total_row > 0 and col_scores:
                    weighted = sum(col_counts.get(c["id"], 0) * c.get("score", 0) for c in columns)
                    avg_score = round(weighted / total_row, 2)
                row_stats.append({
                    "id": row["id"], "text": row.get("text", ""),
                    "avg_score": avg_score,
                    "distribution": [col_counts.get(c["id"], 0) for c in columns],
                })
            stats["rows"] = row_stats

        else:
            stats["count"] = len(answers)

        return {
            "question_id": question.id,
            "title": question.title,
            "question_type": qtype,
            "response_count": len(answers),
            "stats": stats,
        }

    @staticmethod
    def _answer_to_text(question: SurveyQuestion, answer: SurveyResponseAnswer) -> str:
        val = answer.answer_value
        qtype = question.question_type.value
        config = question.config or {}

        if qtype == "single_choice":
            options = {o["id"]: o["text"] for o in config.get("options", [])}
            return options.get(val.get("selected"), str(val.get("selected", "")))

        if qtype == "multiple_choice":
            options = {o["id"]: o["text"] for o in config.get("options", [])}
            return ", ".join(options.get(s, s) for s in val.get("selected", []))

        if qtype in ("text_short", "text_long"):
            return val.get("text", "")

        if qtype in ("rating", "nps", "slider"):
            return str(val.get("value", ""))

        if qtype == "matrix_single":
            cols = {c["id"]: c["text"] for c in config.get("columns", [])}
            return "; ".join(f"{k}={cols.get(v, v)}" for k, v in val.items())

        if qtype == "date":
            return val.get("value", "")

        return str(val)
