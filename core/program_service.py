"""
BHP 智能监测方案引擎 — 核心服务
直接复制到 app/services/program_service.py

职责:
1. 方案模板管理 (CRUD)
2. 用户报名/退出/暂停
3. 每日推送内容生成 (含微调查)
4. 交互处理 (survey回答+照片+设备数据)
5. 行为轨迹分析 + 特征计算
6. 算法推荐 (根据behavior_profile匹配内容)
7. 与V003激励系统联动

依赖:
- SQLAlchemy sync session (同V003部署后的模式)
- 现有 point_service / notification_service (可选)
"""

import json
import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path
from collections import Counter

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ── 配置加载 ──────────────────────────────────────────
CONFIG_DIR = Path(__file__).parent.parent / "configs"

def _load_template_json(slug: str) -> Optional[dict]:
    """从config目录加载预置方案模板"""
    path = CONFIG_DIR / f"{slug}-template.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


class ProgramService:
    """智能监测方案引擎"""

    def __init__(
        self,
        db: Session,
        point_service=None,
        notification_service=None,
        milestone_service=None,
    ):
        self.db = db
        self.point_service = point_service
        self.notification_service = notification_service
        self.milestone_service = milestone_service

    # ═══════════════════════════════════════════════════
    # 1. 方案模板管理
    # ═══════════════════════════════════════════════════

    def list_templates(
        self,
        category: Optional[str] = None,
        is_active: bool = True,
        tenant_id: Optional[int] = None,
    ) -> List[dict]:
        """列出方案模板"""
        conditions = ["pt.is_active = :active"]
        params: Dict[str, Any] = {"active": is_active}

        if category:
            conditions.append("pt.category = :cat")
            params["cat"] = category
        if tenant_id is not None:
            conditions.append("(pt.tenant_id = :tid OR pt.tenant_id IS NULL)")
            params["tid"] = tenant_id
        else:
            conditions.append("pt.is_public = true")

        where = " AND ".join(conditions)
        result = self.db.execute(text(f"""
            SELECT id, slug, title, description, category, total_days,
                   pushes_per_day, tags, cover_image, tenant_id, created_at
            FROM program_templates pt
            WHERE {where}
            ORDER BY created_at DESC
        """), params)

        return [
            {
                "id": str(r.id), "slug": r.slug, "title": r.title,
                "description": r.description, "category": r.category,
                "total_days": r.total_days, "pushes_per_day": r.pushes_per_day,
                "tags": r.tags, "cover_image": r.cover_image,
                "tenant_id": r.tenant_id,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in result.fetchall()
        ]

    def get_template(self, template_id: str) -> Optional[dict]:
        """获取模板详情(含完整schedule_json)"""
        result = self.db.execute(text("""
            SELECT * FROM program_templates WHERE id = :tid
        """), {"tid": template_id})
        r = result.fetchone()
        if not r:
            return None
        return {
            "id": str(r.id), "slug": r.slug, "title": r.title,
            "description": r.description, "category": r.category,
            "total_days": r.total_days, "pushes_per_day": r.pushes_per_day,
            "schedule_json": r.schedule_json,
            "recommendation_rules": r.recommendation_rules,
            "tags": r.tags, "cover_image": r.cover_image,
            "is_active": r.is_active, "is_public": r.is_public,
            "tenant_id": r.tenant_id, "created_by": r.created_by,
        }

    def get_template_by_slug(self, slug: str) -> Optional[dict]:
        """按slug获取模板"""
        result = self.db.execute(text("""
            SELECT id FROM program_templates WHERE slug = :slug
        """), {"slug": slug})
        r = result.fetchone()
        if not r:
            return None
        return self.get_template(str(r.id))

    def create_template(self, data: dict, created_by: int) -> dict:
        """创建方案模板"""
        result = self.db.execute(text("""
            INSERT INTO program_templates
              (slug, title, description, category, total_days, pushes_per_day,
               schedule_json, recommendation_rules, tags, cover_image,
               is_active, is_public, created_by, tenant_id)
            VALUES
              (:slug, :title, :desc, :cat, :days, :ppd,
               :schedule, :rules, :tags, :cover,
               :active, :public, :by, :tid)
            RETURNING id
        """), {
            "slug": data["slug"], "title": data["title"],
            "desc": data.get("description", ""),
            "cat": data.get("category", "custom"),
            "days": data["total_days"],
            "ppd": data.get("pushes_per_day", 3),
            "schedule": json.dumps(data["schedule_json"], ensure_ascii=False),
            "rules": json.dumps(data.get("recommendation_rules", {"rules": []})),
            "tags": json.dumps(data.get("tags", [])),
            "cover": data.get("cover_image"),
            "active": data.get("is_active", True),
            "public": data.get("is_public", True),
            "by": created_by,
            "tid": data.get("tenant_id"),
        })
        self.db.commit()
        row = result.fetchone()
        return {"id": str(row.id), "slug": data["slug"]}

    def update_template(self, template_id: str, data: dict) -> bool:
        """更新方案模板"""
        sets = []
        params: Dict[str, Any] = {"tid": template_id}

        for field in ("title", "description", "is_active", "is_public", "cover_image"):
            if field in data:
                sets.append(f"{field} = :{field}")
                params[field] = data[field]

        if "schedule_json" in data:
            sets.append("schedule_json = :sched")
            params["sched"] = json.dumps(data["schedule_json"], ensure_ascii=False)
        if "recommendation_rules" in data:
            sets.append("recommendation_rules = :rules")
            params["rules"] = json.dumps(data["recommendation_rules"])
        if "tags" in data:
            sets.append("tags = :tags")
            params["tags"] = json.dumps(data["tags"])

        if not sets:
            return False

        self.db.execute(text(f"""
            UPDATE program_templates SET {', '.join(sets)} WHERE id = :tid
        """), params)
        self.db.commit()
        return True

    def seed_template_from_json(self, slug: str) -> Optional[dict]:
        """从config目录的JSON文件导入预置模板"""
        data = _load_template_json(slug)
        if not data:
            return None

        # 检查是否已存在
        existing = self.get_template_by_slug(slug)
        if existing:
            logger.info(f"Template {slug} already exists, skipping seed")
            return existing

        return self.create_template({
            "slug": data["slug"],
            "title": data["title"],
            "description": data.get("description", ""),
            "category": data.get("category", "custom"),
            "total_days": data["total_days"],
            "pushes_per_day": data.get("pushes_per_day", 3),
            "schedule_json": data["schedule"],
            "recommendation_rules": data.get("recommendation_rules", {"rules": []}),
            "tags": data.get("tags", []),
        }, created_by=2)  # admin user (id=2 in BHP)

    # ═══════════════════════════════════════════════════
    # 2. 用户报名/退出/暂停
    # ═══════════════════════════════════════════════════

    def enroll(
        self,
        user_id: int,
        template_id: str,
        coach_id: Optional[int] = None,
        push_preferences: Optional[dict] = None,
        custom_schedule: Optional[dict] = None,
    ) -> dict:
        """用户报名方案"""
        # 检查是否已有active enrollment
        existing = self.db.execute(text("""
            SELECT id FROM program_enrollments
            WHERE user_id = :uid AND template_id = :tid AND status = 'active'
        """), {"uid": user_id, "tid": template_id})
        if existing.fetchone():
            return {"success": False, "reason": "already_enrolled"}

        prefs = push_preferences or {
            "morning": "09:00", "noon": "11:30", "evening": "17:30"
        }

        result = self.db.execute(text("""
            INSERT INTO program_enrollments
              (user_id, template_id, start_date, current_day, status,
               push_preferences, custom_schedule, coach_id)
            VALUES
              (:uid, :tid, CURRENT_DATE, 0, 'active',
               :prefs, :custom, :coach)
            RETURNING id, start_date
        """), {
            "uid": user_id, "tid": template_id,
            "prefs": json.dumps(prefs),
            "custom": json.dumps(custom_schedule) if custom_schedule else None,
            "coach": coach_id,
        })
        self.db.commit()
        row = result.fetchone()

        # 立即生成第0天的推送交互记录
        self._generate_day_interactions(str(row.id), template_id, 0)

        # 发放报名积分(如有积分服务)
        if self.point_service:
            try:
                self.point_service.emit_event(
                    user_id=user_id,
                    action="program_enroll",
                    point_type="growth",
                    amount=10,
                )
            except Exception as e:
                logger.warning(f"Point emit failed on enroll: {e}")

        return {
            "success": True,
            "enrollment_id": str(row.id),
            "start_date": row.start_date.isoformat(),
        }

    def pause_enrollment(self, enrollment_id: str, user_id: int) -> dict:
        """暂停方案"""
        result = self.db.execute(text("""
            UPDATE program_enrollments
            SET status = 'paused', paused_at = NOW()
            WHERE id = :eid AND user_id = :uid AND status = 'active'
            RETURNING id
        """), {"eid": enrollment_id, "uid": user_id})
        self.db.commit()
        if result.fetchone():
            return {"success": True}
        return {"success": False, "reason": "not_found_or_not_active"}

    def resume_enrollment(self, enrollment_id: str, user_id: int) -> dict:
        """恢复方案"""
        result = self.db.execute(text("""
            UPDATE program_enrollments
            SET status = 'active', paused_at = NULL
            WHERE id = :eid AND user_id = :uid AND status = 'paused'
            RETURNING id
        """), {"eid": enrollment_id, "uid": user_id})
        self.db.commit()
        if result.fetchone():
            return {"success": True}
        return {"success": False, "reason": "not_found_or_not_paused"}

    def drop_enrollment(self, enrollment_id: str, user_id: int, reason: str = "") -> dict:
        """退出方案"""
        result = self.db.execute(text("""
            UPDATE program_enrollments
            SET status = 'dropped', dropped_at = NOW(), drop_reason = :reason
            WHERE id = :eid AND user_id = :uid AND status IN ('active', 'paused')
            RETURNING id
        """), {"eid": enrollment_id, "uid": user_id, "reason": reason})
        self.db.commit()
        if result.fetchone():
            return {"success": True}
        return {"success": False, "reason": "not_found_or_already_ended"}

    # ═══════════════════════════════════════════════════
    # 3. 每日推送内容生成
    # ═══════════════════════════════════════════════════

    def get_today_content(self, enrollment_id: str, user_id: int) -> dict:
        """获取今日推送内容 + 待答调查"""
        # 获取enrollment + template
        row = self.db.execute(text("""
            SELECT pe.*, pt.schedule_json, pt.title AS template_title,
                   pt.total_days, pt.recommendation_rules
            FROM program_enrollments pe
            JOIN program_templates pt ON pe.template_id = pt.id
            WHERE pe.id = :eid AND pe.user_id = :uid
        """), {"eid": enrollment_id, "uid": user_id}).fetchone()

        if not row:
            return {"error": "enrollment_not_found"}
        if row.status != "active":
            return {"error": "enrollment_not_active", "status": row.status}

        schedule = row.schedule_json
        current_day = row.current_day

        # 从schedule_json中提取当天内容
        day_content = self._get_day_from_schedule(schedule, current_day)
        if not day_content:
            return {"error": "no_content_for_day", "day": current_day}

        # 获取已有的交互记录
        interactions = self.db.execute(text("""
            SELECT slot, survey_answers, answered_at, photo_urls, recommended_content
            FROM program_interactions
            WHERE enrollment_id = :eid AND day_number = :day
        """), {"eid": enrollment_id, "day": current_day}).fetchall()

        interaction_map = {
            r.slot: {
                "answered": r.survey_answers is not None,
                "answered_at": r.answered_at.isoformat() if r.answered_at else None,
                "photo_urls": r.photo_urls,
                "recommended_content": r.recommended_content,
            }
            for r in interactions
        }

        # 组装响应
        pushes = []
        for push in day_content.get("pushes", []):
            slot = push["slot"]
            status = interaction_map.get(slot, {})
            pushes.append({
                "slot": slot,
                "time": push.get("time"),
                "is_core": push.get("is_core", True),
                "content": push.get("content", {}),
                "survey": push.get("survey"),
                "answered": status.get("answered", False),
                "answered_at": status.get("answered_at"),
                "photo_urls": status.get("photo_urls", []),
                "recommended_content": status.get("recommended_content", []),
            })

        return {
            "enrollment_id": enrollment_id,
            "template_title": row.template_title,
            "current_day": current_day,
            "total_days": row.total_days,
            "progress_pct": round(current_day / max(row.total_days, 1) * 100, 1),
            "is_milestone": day_content.get("is_milestone", False),
            "pushes": pushes,
        }

    def _get_day_from_schedule(self, schedule: dict, day_number: int) -> Optional[dict]:
        """从schedule_json中提取指定天的内容"""
        days = schedule.get("days", [])
        for d in days:
            if d.get("day") == day_number:
                return d
        return None

    def _generate_day_interactions(
        self, enrollment_id: str, template_id: str, day_number: int
    ):
        """为指定天生成交互记录(预占位)"""
        template = self.get_template(template_id)
        if not template:
            return

        schedule = template["schedule_json"]
        day_content = self._get_day_from_schedule(schedule, day_number)
        if not day_content:
            return

        for push in day_content.get("pushes", []):
            slot = push["slot"]
            self.db.execute(text("""
                INSERT INTO program_interactions
                  (enrollment_id, day_number, slot, push_content, survey_questions)
                VALUES
                  (:eid, :day, :slot, :content, :survey)
                ON CONFLICT (enrollment_id, day_number, slot) DO NOTHING
            """), {
                "eid": enrollment_id,
                "day": day_number,
                "slot": slot,
                "content": json.dumps({
                    "is_core": push.get("is_core", True),
                    "time": push.get("time"),
                    **push.get("content", {}),
                }, ensure_ascii=False),
                "survey": json.dumps(
                    push.get("survey", {}).get("questions", []),
                    ensure_ascii=False
                ),
            })
        self.db.commit()

    # ═══════════════════════════════════════════════════
    # 4. 交互处理
    # ═══════════════════════════════════════════════════

    def submit_interaction(
        self,
        enrollment_id: str,
        user_id: int,
        day_number: int,
        slot: str,
        survey_answers: Optional[dict] = None,
        photo_urls: Optional[list] = None,
        device_data: Optional[dict] = None,
    ) -> dict:
        """提交微调查回答 + 照片 → 触发推荐"""
        # 验证enrollment
        enrollment = self.db.execute(text("""
            SELECT pe.*, pt.recommendation_rules
            FROM program_enrollments pe
            JOIN program_templates pt ON pe.template_id = pt.id
            WHERE pe.id = :eid AND pe.user_id = :uid AND pe.status = 'active'
        """), {"eid": enrollment_id, "uid": user_id}).fetchone()

        if not enrollment:
            return {"error": "enrollment_not_found_or_inactive"}

        # 更新交互记录
        update_parts = ["answered_at = NOW()"]
        params: Dict[str, Any] = {
            "eid": enrollment_id, "day": day_number, "slot": slot,
        }

        if survey_answers is not None:
            update_parts.append("survey_answers = :answers")
            params["answers"] = json.dumps(survey_answers, ensure_ascii=False)

        if photo_urls:
            update_parts.append("photo_urls = :photos")
            params["photos"] = json.dumps(photo_urls)

        if device_data:
            update_parts.append("device_data_snapshot = :device")
            params["device"] = json.dumps(device_data)

        self.db.execute(text(f"""
            UPDATE program_interactions
            SET {', '.join(update_parts)}
            WHERE enrollment_id = :eid AND day_number = :day AND slot = :slot
        """), params)

        # 更新行为轨迹
        behavior_update = self._update_behavior_profile(
            enrollment_id, user_id, survey_answers, device_data
        )

        # 触发算法推荐
        recommendations = self._generate_recommendations(
            enrollment, behavior_update
        )

        # 保存推荐结果到交互记录
        if recommendations:
            self.db.execute(text("""
                UPDATE program_interactions
                SET recommended_content = :recs
                WHERE enrollment_id = :eid AND day_number = :day AND slot = :slot
            """), {
                "eid": enrollment_id, "day": day_number, "slot": slot,
                "recs": json.dumps(recommendations, ensure_ascii=False),
            })

        # 发放交互积分
        if self.point_service:
            try:
                self.point_service.emit_event(
                    user_id=user_id,
                    action="program_interaction",
                    point_type="growth",
                    amount=3,
                )
            except Exception as e:
                logger.warning(f"Point emit failed: {e}")

        self.db.commit()

        return {
            "success": True,
            "behavior_update": behavior_update,
            "recommendations": recommendations,
        }

    # ═══════════════════════════════════════════════════
    # 5. 行为轨迹分析
    # ═══════════════════════════════════════════════════

    def _update_behavior_profile(
        self,
        enrollment_id: str,
        user_id: int,
        survey_answers: Optional[dict],
        device_data: Optional[dict],
    ) -> dict:
        """更新行为轨迹特征"""
        # 获取当前profile
        row = self.db.execute(text("""
            SELECT behavior_profile FROM program_enrollments WHERE id = :eid
        """), {"eid": enrollment_id}).fetchone()

        profile = row.behavior_profile if row and row.behavior_profile else {}

        # ── 特征1: 执行稳定性 ──
        rate_result = self.db.execute(text("""
            SELECT * FROM calc_interaction_rate(:eid, 7)
        """), {"eid": enrollment_id}).fetchone()

        if rate_result:
            profile["exec_rate_7d"] = float(rate_result.completion_rate or 0) / 100
            profile["core_exec_rate_7d"] = float(rate_result.core_completion_rate or 0) / 100

        # ── 特征2: 行为链缺口 (从survey_answers中提取) ──
        if survey_answers:
            # 提取"最难坚持"/"困难"关键词
            pain_points = profile.get("pain_points", [])
            for key, value in survey_answers.items():
                if isinstance(value, str) and len(value) > 2:
                    # 简单关键词提取(生产中应用NLP)
                    for keyword in ["主食", "运动", "蔬菜", "时间", "应酬", "情绪", "压力"]:
                        if keyword in value:
                            pain_points.append(keyword)
            # 取最近30个，统计频率
            pain_points = pain_points[-30:]
            profile["pain_points"] = pain_points
            if pain_points:
                counter = Counter(pain_points)
                profile["top_pain_point"] = counter.most_common(1)[0][0]

            # 提取数值评分(scale类型答案)
            scores = []
            for key, value in survey_answers.items():
                if isinstance(value, (int, float)):
                    scores.append(value)
            if scores:
                profile["avg_score_latest"] = round(sum(scores) / len(scores), 2)

        # ── 特征3: 设备数据趋势 ──
        if device_data:
            glucose_readings = device_data.get("glucose_readings", [])
            if glucose_readings:
                values = [r.get("value", 0) for r in glucose_readings if r.get("value")]
                if values:
                    avg = sum(values) / len(values)
                    # 变异系数 CV
                    variance = sum((v - avg) ** 2 for v in values) / len(values)
                    cv = (variance ** 0.5) / avg if avg > 0 else 0
                    prev_cv = profile.get("glucose_cv", cv)
                    profile["glucose_cv"] = round(cv, 4)
                    profile["glucose_cv_trend"] = round(cv - prev_cv, 4)
                    profile["glucose_avg"] = round(avg, 2)

        # ── 特征4: 交互活跃度 ──
        activity = self.db.execute(text("""
            SELECT
              COUNT(*) FILTER (WHERE answered_at IS NOT NULL) as answered,
              COUNT(*) FILTER (WHERE photo_urls != '[]'::jsonb) as photos,
              COUNT(*) as total
            FROM program_interactions
            WHERE enrollment_id = :eid
        """), {"eid": enrollment_id}).fetchone()

        if activity:
            profile["total_interactions"] = activity.total
            profile["total_answered"] = activity.answered
            profile["total_photos"] = activity.photos

        profile["last_updated"] = datetime.utcnow().isoformat()

        # 保存更新后的profile
        self.db.execute(text("""
            UPDATE program_enrollments
            SET behavior_profile = :profile
            WHERE id = :eid
        """), {
            "eid": enrollment_id,
            "profile": json.dumps(profile, ensure_ascii=False),
        })

        return profile

    # ═══════════════════════════════════════════════════
    # 6. 算法推荐
    # ═══════════════════════════════════════════════════

    def _generate_recommendations(
        self, enrollment, behavior_profile: dict
    ) -> List[dict]:
        """根据行为轨迹生成推荐内容"""
        rules = enrollment.recommendation_rules or {"rules": []}
        recommendations = []

        for rule in rules.get("rules", []):
            condition = rule.get("condition", {})
            metric = condition.get("metric", "")
            op = condition.get("op", "")
            threshold = condition.get("value")

            # 从behavior_profile取值
            actual = behavior_profile.get(metric)
            if actual is None:
                continue

            # 评估条件
            matched = False
            if op == "<" and isinstance(actual, (int, float)):
                matched = actual < threshold
            elif op == ">" and isinstance(actual, (int, float)):
                matched = actual > threshold
            elif op == "==" and isinstance(actual, str):
                matched = actual == threshold
            elif op == "contains" and isinstance(actual, (str, list)):
                if isinstance(actual, list):
                    matched = threshold in actual
                else:
                    matched = threshold in actual

            if matched:
                action = rule.get("action", "recommend")
                if action == "recommend":
                    recommendations.append({
                        "type": "content",
                        "tags": rule.get("content_tags", []),
                        "priority": rule.get("priority", "medium"),
                        "reason": rule.get("message", ""),
                    })
                elif action == "alert_coach":
                    recommendations.append({
                        "type": "coach_alert",
                        "message": rule.get("message", ""),
                        "metric": metric,
                        "value": actual,
                    })
                    # 实际发送教练通知
                    if self.notification_service and enrollment.coach_id:
                        try:
                            self.notification_service.send(
                                user_id=enrollment.coach_id,
                                channel="in_app",
                                title="方案学员异常提醒",
                                message=rule.get("message", ""),
                            )
                        except Exception as e:
                            logger.warning(f"Coach alert failed: {e}")

                elif action == "positive_feedback":
                    recommendations.append({
                        "type": "positive_feedback",
                        "message": rule.get("message", ""),
                    })
                elif action == "prefer_format":
                    recommendations.append({
                        "type": "format_preference",
                        "format": rule.get("format", "article"),
                    })

        return recommendations

    # ═══════════════════════════════════════════════════
    # 7. 用户查询接口
    # ═══════════════════════════════════════════════════

    def get_my_programs(self, user_id: int) -> List[dict]:
        """我的方案列表"""
        result = self.db.execute(text("""
            SELECT * FROM v_program_enrollment_summary
            WHERE user_id = :uid
            ORDER BY
              CASE status
                WHEN 'active' THEN 0
                WHEN 'paused' THEN 1
                WHEN 'completed' THEN 2
                ELSE 3
              END,
              last_interaction_at DESC NULLS LAST
        """), {"uid": user_id})

        return [
            {
                "enrollment_id": str(r.enrollment_id),
                "template_slug": r.template_slug,
                "template_title": r.template_title,
                "category": r.category,
                "total_days": r.total_days,
                "current_day": r.current_day,
                "progress_pct": float(r.progress_pct) if r.progress_pct else 0,
                "status": r.status,
                "start_date": r.start_date.isoformat() if hasattr(r, 'start_date') and r.start_date else None,
                "total_pushes": r.total_pushes,
                "answered_count": r.answered_count,
                "photo_count": r.photo_count,
                "last_interaction_at": r.last_interaction_at.isoformat() if r.last_interaction_at else None,
            }
            for r in result.fetchall()
        ]

    def get_timeline(self, enrollment_id: str, user_id: int) -> dict:
        """用户行为轨迹时间线"""
        # 验证ownership
        enrollment = self.db.execute(text("""
            SELECT pe.*, pt.title
            FROM program_enrollments pe
            JOIN program_templates pt ON pe.template_id = pt.id
            WHERE pe.id = :eid AND pe.user_id = :uid
        """), {"eid": enrollment_id, "uid": user_id}).fetchone()

        if not enrollment:
            return {"error": "not_found"}

        interactions = self.db.execute(text("""
            SELECT day_number, slot, push_sent_at, answered_at,
                   survey_answers, photo_urls, device_data_snapshot,
                   recommended_content, push_content
            FROM program_interactions
            WHERE enrollment_id = :eid
            ORDER BY day_number, slot
        """), {"eid": enrollment_id}).fetchall()

        # 按天分组
        days = {}
        for r in interactions:
            day = r.day_number
            if day not in days:
                days[day] = {"day": day, "pushes": []}
            days[day]["pushes"].append({
                "slot": r.slot,
                "is_core": r.push_content.get("is_core", True) if r.push_content else True,
                "sent_at": r.push_sent_at.isoformat() if r.push_sent_at else None,
                "answered_at": r.answered_at.isoformat() if r.answered_at else None,
                "has_answer": r.survey_answers is not None,
                "has_photo": r.photo_urls and r.photo_urls != [],
                "has_device_data": r.device_data_snapshot is not None,
                "recommendations_count": len(r.recommended_content) if r.recommended_content else 0,
            })

        return {
            "enrollment_id": enrollment_id,
            "title": enrollment.title,
            "current_day": enrollment.current_day,
            "behavior_profile": enrollment.behavior_profile,
            "timeline": sorted(days.values(), key=lambda x: x["day"]),
        }

    def get_progress_radar(self, enrollment_id: str, user_id: int) -> dict:
        """行为特征雷达图数据"""
        enrollment = self.db.execute(text("""
            SELECT behavior_profile
            FROM program_enrollments
            WHERE id = :eid AND user_id = :uid
        """), {"eid": enrollment_id, "uid": user_id}).fetchone()

        if not enrollment:
            return {"error": "not_found"}

        profile = enrollment.behavior_profile or {}

        # 构建雷达图维度(0-100标准化)
        radar = {
            "dimensions": [
                {
                    "label": "执行稳定性",
                    "key": "exec_stability",
                    "value": min(100, (profile.get("exec_rate_7d", 0)) * 100),
                    "description": "近7天核心行为完成率",
                },
                {
                    "label": "知识吸收",
                    "key": "knowledge_absorption",
                    "value": min(100, (profile.get("total_answered", 0) / max(profile.get("total_interactions", 1), 1)) * 100),
                    "description": "调查回答率",
                },
                {
                    "label": "行为记录",
                    "key": "behavior_logging",
                    "value": min(100, profile.get("total_photos", 0) * 10),
                    "description": "打卡照片数量",
                },
                {
                    "label": "血糖控制",
                    "key": "glucose_control",
                    "value": max(0, 100 - profile.get("glucose_cv", 0.3) * 200),
                    "description": "血糖变异系数(越小越好)",
                },
                {
                    "label": "情绪状态",
                    "key": "mood",
                    "value": min(100, profile.get("avg_score_latest", 3) * 20),
                    "description": "最近评分均值",
                },
            ],
            "raw_profile": profile,
        }

        return radar

    # ═══════════════════════════════════════════════════
    # 8. Admin分析接口
    # ═══════════════════════════════════════════════════

    def admin_get_analytics(
        self,
        template_id: Optional[str] = None,
        category: Optional[str] = None,
    ) -> dict:
        """方案效果分析(管理员)"""
        conditions = ["1=1"]
        params: Dict[str, Any] = {}

        if template_id:
            conditions.append("pe.template_id = :tid")
            params["tid"] = template_id
        if category:
            conditions.append("pt.category = :cat")
            params["cat"] = category

        where = " AND ".join(conditions)

        result = self.db.execute(text(f"""
            SELECT
              pt.slug, pt.title, pt.category,
              COUNT(pe.id) AS total_enrollments,
              COUNT(*) FILTER (WHERE pe.status = 'active') AS active_count,
              COUNT(*) FILTER (WHERE pe.status = 'completed') AS completed_count,
              COUNT(*) FILTER (WHERE pe.status = 'dropped') AS dropped_count,
              ROUND(AVG(pe.current_day), 1) AS avg_current_day,
              ROUND(
                COUNT(*) FILTER (WHERE pe.status = 'completed')::numeric /
                NULLIF(COUNT(pe.id), 0) * 100, 1
              ) AS completion_rate
            FROM program_enrollments pe
            JOIN program_templates pt ON pe.template_id = pt.id
            WHERE {where}
            GROUP BY pt.slug, pt.title, pt.category
        """), params)

        templates = []
        for r in result.fetchall():
            templates.append({
                "slug": r.slug, "title": r.title, "category": r.category,
                "total_enrollments": r.total_enrollments,
                "active": r.active_count, "completed": r.completed_count,
                "dropped": r.dropped_count,
                "avg_current_day": float(r.avg_current_day) if r.avg_current_day else 0,
                "completion_rate": float(r.completion_rate) if r.completion_rate else 0,
            })

        return {"templates": templates}

    def admin_get_enrollments(
        self,
        template_id: Optional[str] = None,
        status: Optional[str] = None,
        coach_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """全部参与者列表(管理员)"""
        conditions = ["1=1"]
        params: Dict[str, Any] = {
            "limit": page_size,
            "offset": (page - 1) * page_size,
        }

        if template_id:
            conditions.append("template_id = :tid")
            params["tid"] = template_id
        if status:
            conditions.append("status = :st")
            params["st"] = status
        if coach_id:
            conditions.append("coach_id = :cid")
            params["cid"] = coach_id

        where = " AND ".join(conditions)

        # Count
        count_row = self.db.execute(text(f"""
            SELECT COUNT(*) as cnt FROM v_program_enrollment_summary WHERE {where}
        """), params).fetchone()

        # Data
        result = self.db.execute(text(f"""
            SELECT * FROM v_program_enrollment_summary
            WHERE {where}
            ORDER BY last_interaction_at DESC NULLS LAST
            LIMIT :limit OFFSET :offset
        """), params)

        items = []
        for r in result.fetchall():
            items.append({
                "enrollment_id": str(r.enrollment_id),
                "user_id": r.user_id,
                "template_title": r.template_title,
                "category": r.category,
                "current_day": r.current_day,
                "total_days": r.total_days,
                "progress_pct": float(r.progress_pct) if r.progress_pct else 0,
                "status": r.status,
                "answered_count": r.answered_count,
                "photo_count": r.photo_count,
                "behavior_profile": r.behavior_profile,
            })

        return {
            "total": count_row.cnt,
            "page": page,
            "page_size": page_size,
            "items": items,
        }

    # ═══════════════════════════════════════════════════
    # 9. 定时任务接口 (供APScheduler调用)
    # ═══════════════════════════════════════════════════

    def scheduled_advance_day(self):
        """
        每日凌晨调用: 推进所有active enrollment的天数
        由APScheduler触发
        """
        enrollments = self.db.execute(text("""
            SELECT pe.id, pe.user_id, pe.template_id, pe.current_day,
                   pt.total_days
            FROM program_enrollments pe
            JOIN program_templates pt ON pe.template_id = pt.id
            WHERE pe.status = 'active'
              AND pe.start_date < CURRENT_DATE  -- 不推进报名当天的
        """)).fetchall()

        advanced = 0
        completed = 0
        for e in enrollments:
            result = self.db.execute(text("""
                SELECT * FROM advance_program_day(:eid)
            """), {"eid": str(e.id)}).fetchone()

            if result:
                advanced += 1
                if result.is_completed:
                    completed += 1
                    # 触发完成事件 → V003激励
                    if self.milestone_service:
                        try:
                            self.milestone_service.process_daily_checkin(e.user_id)
                        except Exception as ex:
                            logger.warning(f"Milestone trigger failed: {ex}")
                else:
                    # 为新一天生成交互记录
                    self._generate_day_interactions(
                        str(e.id), str(e.template_id), result.new_day
                    )

        self.db.commit()
        logger.info(
            f"Program day advance: {advanced} enrollments, {completed} completed"
        )
        return {"advanced": advanced, "completed": completed}

    def scheduled_send_pushes(self, slot: str):
        """
        定时推送: morning/noon/evening 各调用一次
        由APScheduler触发
        """
        # 获取当前时段待推送的交互
        interactions = self.db.execute(text("""
            SELECT pi.id, pi.enrollment_id, pe.user_id,
                   pi.push_content, pi.survey_questions
            FROM program_interactions pi
            JOIN program_enrollments pe ON pi.enrollment_id = pe.id
            WHERE pe.status = 'active'
              AND pi.day_number = pe.current_day
              AND pi.slot = :slot
              AND pi.push_sent_at IS NULL
        """), {"slot": slot}).fetchall()

        sent = 0
        for pi in interactions:
            # 标记已推送
            self.db.execute(text("""
                UPDATE program_interactions
                SET push_sent_at = NOW()
                WHERE id = :pid
            """), {"pid": str(pi.id)})

            # 发送推送
            if self.notification_service:
                try:
                    content = pi.push_content or {}
                    title = content.get("knowledge", "")[:50]
                    self.notification_service.send(
                        user_id=pi.user_id,
                        channel="push",
                        title=f"📋 {title}",
                        message="点击查看今日方案内容",
                        action={"type": "open_program", "enrollment_id": str(pi.enrollment_id)},
                    )
                except Exception as e:
                    logger.warning(f"Push send failed: {e}")

            sent += 1

        self.db.commit()
        logger.info(f"Program push [{slot}]: {sent} sent")
        return {"slot": slot, "sent": sent}
