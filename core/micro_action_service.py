# -*- coding: utf-8 -*-
"""
MicroActionTaskService - 微行动任务服务

╔══════════════════════════════════════════════════════════════════════╗
║          平台行为处方生成铁律（四原则）— 写入时间 2026-02-27         ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  【原则一：三来源任务体系，有优先级】                                ║
║  L1 教练指定 (source=coach_assigned)                                 ║
║     流程：AI生成建议 → 教练审核/修订 → 经 coach_push_queue 推送     ║
║     铁律：禁止绕过审核直接触达用户；教练对任务内容负最终责任        ║
║  L2 AI推荐 (source=ai_recommended)                                   ║
║     流程：系统基于四维隐性数据自动生成 → 展示给用户选择             ║
║     优先级：无教练指定任务时，作为第一展示来源                       ║
║  L3 用户自选 (source=user_selected)                                  ║
║     流程：用户从 AI 预生成候选池中主动选取                           ║
║     铁律：候选池本身也由 AI 基于关注领域预生成，不允许凭空填写      ║
║                                                                      ║
║  【原则二：关注问题直接导出任务】                                    ║
║  成长者设置"关注领域"(BehavioralProfile.primary_domains)后，        ║
║  系统优先从该领域生成 AI 候选任务池，作为无教练指定时的首选路径。  ║
║  关注领域由用户主动设置，也可从任务完成行为自动反哺更新。           ║
║                                                                      ║
║  【原则三：四维隐性数据驱动】                                        ║
║  所有 AI 推荐的底层数据来源：                                        ║
║  1. 用户关注内容    → BehavioralProfile.primary_domains              ║
║  2. 行为轨迹       → BehaviorFacts (streak/rate/domain_activity)     ║
║  3. 穿戴设备数据   → GlucoseReading/SleepRecord/ActivityRecord       ║
║  4. 认知调查结果   → Assessment/BehavioralProfile(stage/SPI/level)   ║
║                                                                      ║
║  【原则四：AI必须先于人工（不可绕过）】                              ║
║  用户自选 = 从 AI 预生成候选池选取，禁止直接填写任意内容            ║
║  教练指定 = AI 先给教练生成建议(copilot_prescription_service)        ║
║             → 教练审核修订 → coach_push_queue_service 推送           ║
║             → 禁止绕过审核直接触达用户                               ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  【数据闭环 Feedback Loop】                                          ║
║  任务完成/跳过 → MicroActionLog                                      ║
║               → BehaviorFacts 更新                                   ║
║               → BehavioralProfile.primary_domains 自动反哺           ║
║                 (连续完成某领域3次 → 加入关注；连续跳过 → 降优先级) ║
║               → 下次 AI 推荐质量提升（形成闭环）                    ║
║                                                                      ║
║  【积分差异化（按来源 × 难度）】                                     ║
║  coach_assigned + challenging = 7 pts  (最高，体现教练价值)         ║
║  coach_assigned + moderate    = 6 pts                                ║
║  coach_assigned + easy        = 5 pts                                ║
║  ai_recommended + challenging = 6 pts                                ║
║  ai_recommended + moderate    = 5 pts                                ║
║  ai_recommended + easy        = 4 pts                                ║
║  user_selected  + challenging = 5 pts                                ║
║  user_selected  + moderate    = 4 pts                                ║
║  user_selected  + easy        = 3 pts                                ║
║  intervention_plan / *        = 3 pts                                ║
║  system / *                   = 2 pts                                ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

职责:
- 从 InterventionPlan 生成每日微行动任务（自动，06:15 调度器）
- 提供三来源候选任务池（get_task_pool_by_focus，供用户主动选择）
- 用户自选确认（user_self_add_task，source=user_selected）
- 管理任务完成/跳过/过期，附带差异化积分权重
- 任务行为反哺 BehavioralProfile（数据闭环）
- 支持设备数据自动完成（DeviceBehaviorBridge 调用）
- 教练手动创建任务（经 coach_push_queue 审批）
"""
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from loguru import logger

from core.models import (
    MicroActionTask, MicroActionLog,
    BehavioralProfile, User,
)
from core.intervention_matcher import InterventionMatcher


# 全局 InterventionMatcher 实例
_matcher = None


def _get_matcher() -> InterventionMatcher:
    global _matcher
    if _matcher is None:
        _matcher = InterventionMatcher()
    return _matcher


# 领域中文名映射
DOMAIN_NAMES = {
    "nutrition": "营养管理",
    "exercise": "运动习惯",
    "sleep": "睡眠调节",
    "emotion": "情绪调节",
    "stress": "压力管理",
    "cognitive": "认知提升",
    "social": "社交连接",
    "tcm": "中医健康",
}

# 有效领域集合
VALID_DOMAINS = set(DOMAIN_NAMES.keys())

# 默认候选任务库（InterventionMatcher 不可用时降级）
_DEFAULT_CANDIDATES: Dict[str, List[Dict]] = {
    "nutrition": [
        {"title": "记录今日三餐", "description": "拍照或文字记录，培养饮食意识", "difficulty": "easy"},
        {"title": "减少精制糖摄入", "description": "今日饮料选无糖款，或减少一份甜食", "difficulty": "moderate"},
        {"title": "增加蔬菜摄入量", "description": "每餐保证至少一种蔬菜", "difficulty": "easy"},
    ],
    "exercise": [
        {"title": "饭后散步15分钟", "description": "饭后30分钟内开始，温和启动代谢", "difficulty": "easy"},
        {"title": "拉伸放松5分钟", "description": "颈肩腰背全身拉伸，缓解久坐僵硬", "difficulty": "easy"},
        {"title": "有氧运动20分钟", "description": "快走/慢跑/骑车，心率达到中等强度", "difficulty": "moderate"},
    ],
    "sleep": [
        {"title": "22:30前放下手机", "description": "睡前1小时远离蓝光，帮助褪黑素分泌", "difficulty": "moderate"},
        {"title": "记录今晚入睡时间", "description": "记录实际入睡时刻和睡眠质量感受", "difficulty": "easy"},
        {"title": "睡前5分钟腹式呼吸", "description": "放松神经系统，提高睡眠深度", "difficulty": "easy"},
    ],
    "emotion": [
        {"title": "3分钟腹式呼吸", "description": "4秒吸气-7秒屏息-8秒呼气，激活副交感神经", "difficulty": "easy"},
        {"title": "写下今日一件感恩的事", "description": "感恩日记，哪怕一句话，建立积极归因习惯", "difficulty": "easy"},
        {"title": "情绪觉察记录", "description": "标注当下情绪名称和触发事件，提升情绪粒度", "difficulty": "moderate"},
    ],
    "stress": [
        {"title": "5分钟正念冥想", "description": "专注呼吸，觉察但不评判当下感受", "difficulty": "easy"},
        {"title": "写下今日三项优先任务", "description": "清单减轻认知负荷，降低压力焦虑", "difficulty": "easy"},
        {"title": "与信任的人倾诉5分钟", "description": "社会支持是最有效的压力缓冲", "difficulty": "moderate"},
    ],
    "cognitive": [
        {"title": "阅读行为健康内容10分钟", "description": "在学习中心选择感兴趣内容，积累知识积分", "difficulty": "easy"},
        {"title": "完成一项认知测评", "description": "了解自己当前的认知状态和成长阶段", "difficulty": "easy"},
        {"title": "写下今日一个新认知", "description": "记录学到的新观点或对旧问题的新理解", "difficulty": "easy"},
    ],
    "social": [
        {"title": "与家人分享今日健康行动", "description": "传递健康行为影响力，强化社会认同", "difficulty": "easy"},
        {"title": "给同道者发一条鼓励消息", "description": "利他行为同时强化自身动机", "difficulty": "easy"},
        {"title": "参与一次健康话题讨论", "description": "在平台社区或线下分享观点", "difficulty": "moderate"},
    ],
    "tcm": [
        {"title": "穴位按摩5分钟", "description": "按揉合谷、内关等穴位，调和气血", "difficulty": "easy"},
        {"title": "记录今日体质感受", "description": "记录精力、消化、睡眠等中医体质指标", "difficulty": "easy"},
    ],
}


class MicroActionTaskService:
    """微行动任务服务"""

    # ──────────────────────────────────────────────────────────────
    # 每日自动生成（调度器 06:15 调用）
    # ──────────────────────────────────────────────────────────────

    def generate_daily_tasks(
        self,
        db: Session,
        user_id: int,
        max_tasks: int = 3,
    ) -> List[MicroActionTask]:
        """
        为用户生成今日微行动任务（调度器自动调用，原则三：四维数据驱动）

        流程:
        1. 检查今日是否已有系统生成任务（避免重复）
        2. 统计用户自选任务，跳过已覆盖领域
        3. 获取用户 BehavioralProfile（含关注领域 primary_domains）
        4. 通过 InterventionMatcher 匹配干预计划（结合阶段+类型+积分）
        5. 从 advice 列表提取微行动，写入 DB
        6. 若用户有教练，汇总通知
        """
        today_str = date.today().isoformat()

        # 检查今日是否已有系统生成任务
        existing = (
            db.query(MicroActionTask)
            .filter(
                MicroActionTask.user_id == user_id,
                MicroActionTask.scheduled_date == today_str,
                MicroActionTask.source.notin_(["user_selected"]),
            )
            .all()
        )
        if existing:
            return existing

        # 统计用户今日已自选的领域（跳过，避免重复）
        self_selected = (
            db.query(MicroActionTask)
            .filter(
                MicroActionTask.user_id == user_id,
                MicroActionTask.scheduled_date == today_str,
                MicroActionTask.source == "user_selected",
            )
            .all()
        )
        covered_by_self = {t.domain for t in self_selected}
        remaining_slots = max_tasks - len(self_selected)

        if remaining_slots <= 0:
            # 自选任务已满，不再自动生成
            return self_selected

        # 获取用户画像
        profile = (
            db.query(BehavioralProfile)
            .filter(BehavioralProfile.user_id == user_id)
            .first()
        )

        if not profile:
            return self._generate_default_tasks(db, user_id, today_str, covered_by_self, remaining_slots)

        # 获取干预计划（原则三：四维数据驱动）
        matcher = _get_matcher()
        # 优先使用关注领域（原则二）
        focus_domains = list(profile.primary_domains or [])
        fallback_domains = ["nutrition", "exercise", "sleep"]
        target_domains = focus_domains + [d for d in fallback_domains if d not in focus_domains]
        target_domains = [d for d in target_domains if d not in covered_by_self][:remaining_slots + 2]

        current_stage = profile.current_stage.value if profile.current_stage else "S0"

        plan = matcher.match(
            user_id=user_id,
            current_stage=current_stage,
            psychological_level=profile.psychological_level.value if profile.psychological_level else "L3",
            bpt6_type=profile.bpt6_type or "mixed",
            spi_score=profile.spi_score or 0,
            target_domains=target_domains,
        )

        # 从干预计划提取微行动
        tasks = []
        for di in plan.domain_interventions:
            if di.domain in covered_by_self:
                continue
            if len(tasks) >= remaining_slots:
                break

            advice = di.advice[0] if di.advice else None
            title = advice["title"] if advice else di.core_goal or f"{di.domain_name}练习"
            description = advice["description"] if advice else ""
            difficulty = self._map_difficulty(advice.get("difficulty", 1)) if advice else "easy"

            task = MicroActionTask(
                user_id=user_id,
                domain=di.domain,
                title=title,
                description=description,
                difficulty=difficulty,
                source="intervention_plan",
                source_id=di.rx_id,
                status="pending",
                scheduled_date=today_str,
            )
            db.add(task)
            tasks.append(task)

        if tasks:
            db.commit()
            for t in tasks:
                db.refresh(t)
            logger.info(f"生成每日任务: user={user_id}, count={len(tasks)}")
            self._create_queue_summary(db, user_id, tasks)

        return tasks + self_selected

    # ──────────────────────────────────────────────────────────────
    # 三来源候选任务池（供用户在"添加任务"时选择，原则一）
    # ──────────────────────────────────────────────────────────────

    def get_task_pool_by_focus(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        生成三来源候选任务池（不写DB，供前端"添加任务"面板展示）

        返回结构:
        {
          "focus_domains": [...],          # 当前关注领域
          "covered_today": [...],          # 今日已有任务的领域（用于前端去重提示）
          "coach_pending": [...],          # L1：教练指定待执行（只读展示）
          "ai_recommended": [...],         # L2：AI基于关注领域+隐性数据推荐
          "user_selectable": {             # L3：按领域分组的自选候选池
              "nutrition": {
                  "domain_name": "营养管理",
                  "is_focus": true,
                  "candidates": [...]
              }, ...
          }
        }
        """
        today_str = date.today().isoformat()

        # 今日已有任务的领域
        today_tasks = (
            db.query(MicroActionTask)
            .filter(
                MicroActionTask.user_id == user_id,
                MicroActionTask.scheduled_date == today_str,
            )
            .all()
        )
        covered_today = {t.domain for t in today_tasks}

        # 获取用户画像（原则三：四维数据来源 #1+#4）
        profile = (
            db.query(BehavioralProfile)
            .filter(BehavioralProfile.user_id == user_id)
            .first()
        )
        focus_domains = list(profile.primary_domains or ["nutrition", "exercise", "sleep"]) if profile else ["nutrition", "exercise", "sleep"]
        current_stage = profile.current_stage.value if profile and profile.current_stage else "S0"
        psych_level = profile.psychological_level.value if profile and profile.psychological_level else "L3"
        bpt6_type = profile.bpt6_type or "mixed" if profile else "mixed"
        spi_score = profile.spi_score or 0 if profile else 0

        # ---- L1：教练指定任务（只读展示）----
        coach_pending = []
        try:
            coach_tasks = (
                db.query(MicroActionTask)
                .filter(
                    MicroActionTask.user_id == user_id,
                    MicroActionTask.source.in_(["coach", "coach_assigned"]),
                    MicroActionTask.status == "pending",
                )
                .order_by(MicroActionTask.created_at.desc())
                .limit(5)
                .all()
            )
            coach_pending = [self._task_to_dict(t) for t in coach_tasks]
        except Exception as e:
            logger.warning(f"加载教练指定任务失败: {e}")

        # ---- L2+L3：通过 InterventionMatcher 生成 AI 候选池 ----
        ai_recommended: List[Dict] = []
        user_selectable: Dict[str, Any] = {}

        try:
            matcher = _get_matcher()
            # 扩展领域：关注领域优先，补充常用领域至最多6个
            all_domains = list(focus_domains)
            for d in ["nutrition", "exercise", "sleep", "emotion", "stress", "cognitive"]:
                if d not in all_domains:
                    all_domains.append(d)
            all_domains = all_domains[:6]

            plan = matcher.match(
                user_id=user_id,
                current_stage=current_stage,
                psychological_level=psych_level,
                bpt6_type=bpt6_type,
                spi_score=spi_score,
                target_domains=all_domains,
            )

            for di in plan.domain_interventions:
                domain_candidates = []
                for i, advice in enumerate(di.advice[:3]):
                    candidate = {
                        "domain": di.domain,
                        "domain_name": DOMAIN_NAMES.get(di.domain, di.domain_name),
                        "title": advice.get("title", di.core_goal or f"{di.domain_name}练习"),
                        "description": advice.get("description", ""),
                        "difficulty": self._map_difficulty(advice.get("difficulty", 1)),
                        "rx_id": di.rx_id,
                        "already_today": di.domain in covered_today,
                    }
                    # L2：关注领域的第一条建议进入 ai_recommended
                    if i == 0 and di.domain in focus_domains:
                        ai_recommended.append({**candidate, "source_hint": "ai_recommended"})
                    # L3：所有候选按领域分组
                    domain_candidates.append({**candidate, "source_hint": "user_selectable"})

                if domain_candidates:
                    user_selectable[di.domain] = {
                        "domain_name": DOMAIN_NAMES.get(di.domain, di.domain),
                        "is_focus": di.domain in focus_domains,
                        "candidates": domain_candidates,
                    }

        except Exception as e:
            logger.warning(f"InterventionMatcher 生成候选池失败 user={user_id}: {e}")
            # 降级：使用默认候选库
            ai_recommended = self._get_default_candidates(focus_domains, covered_today)
            for domain in focus_domains + ["nutrition", "exercise", "sleep"]:
                if domain in _DEFAULT_CANDIDATES:
                    user_selectable[domain] = {
                        "domain_name": DOMAIN_NAMES.get(domain, domain),
                        "is_focus": domain in focus_domains,
                        "candidates": [
                            {**c, "domain": domain, "domain_name": DOMAIN_NAMES.get(domain, domain),
                             "rx_id": None, "already_today": domain in covered_today,
                             "source_hint": "user_selectable"}
                            for c in _DEFAULT_CANDIDATES[domain]
                        ],
                    }

        return {
            "focus_domains": focus_domains,
            "covered_today": list(covered_today),
            "coach_pending": coach_pending,
            "ai_recommended": ai_recommended,
            "user_selectable": user_selectable,
        }

    # ──────────────────────────────────────────────────────────────
    # 用户自选添加任务（原则一 L3）
    # ──────────────────────────────────────────────────────────────

    def user_self_add_task(
        self,
        db: Session,
        user_id: int,
        domain: str,
        title: str,
        description: str = "",
        difficulty: str = "easy",
        rx_id: Optional[str] = None,
    ) -> MicroActionTask:
        """
        用户自选添加任务（原则一L3 + 原则四：候选池由AI预生成）

        - source = 'user_selected'
        - 同域今日上限：每领域最多1个自选任务
        - 今日总上限：5个任务
        - 自动通知教练（知情，非审核）
        - 自动更新 BehavioralProfile.primary_domains（数据闭环）
        """
        today_str = date.today().isoformat()

        # 检查今日总任务上限（5个）
        today_count = (
            db.query(func.count(MicroActionTask.id))
            .filter(
                MicroActionTask.user_id == user_id,
                MicroActionTask.scheduled_date == today_str,
                MicroActionTask.status.notin_(["expired"]),
            )
            .scalar() or 0
        )
        if today_count >= 5:
            raise ValueError("今日任务已达上限（5个），请先完成现有任务")

        # 检查同领域今日是否已有自选任务
        same_domain_self = (
            db.query(func.count(MicroActionTask.id))
            .filter(
                MicroActionTask.user_id == user_id,
                MicroActionTask.domain == domain,
                MicroActionTask.scheduled_date == today_str,
                MicroActionTask.source == "user_selected",
            )
            .scalar() or 0
        )
        if same_domain_self >= 1:
            raise ValueError(f"今日「{DOMAIN_NAMES.get(domain, domain)}」领域已有自选任务")

        # 创建自选任务
        task = MicroActionTask(
            user_id=user_id,
            domain=domain,
            title=title,
            description=description,
            difficulty=difficulty,
            source="user_selected",
            source_id=rx_id,
            status="pending",
            scheduled_date=today_str,
        )
        db.add(task)
        db.flush()  # 获取 task.id，但不提交

        # 通知教练（知情，非审核）
        self._notify_coach_self_selected(db, user_id, task)

        # 数据闭环：自选即更新关注领域
        self._update_profile_from_behavior(db, user_id, domain, "self_selected")

        db.commit()
        db.refresh(task)

        logger.info(f"用户自选任务: user={user_id}, domain={domain}, title={title}")
        return task

    # ──────────────────────────────────────────────────────────────
    # 积分差异化（原则一：来源 × 难度权重）
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def get_completion_points(task: MicroActionTask) -> int:
        """
        差异化积分：来源权重 + 难度加成（原则一铁律）

        来源基础分:
          coach_assigned / coach → 5  (教练指定，体现教练价值)
          ai_recommended         → 4  (AI推荐)
          user_selected          → 3  (用户自选)
          intervention_plan      → 3  (系统计划)
          system                 → 2  (默认)

        难度加成:
          challenging → +2
          moderate    → +1
          easy        → +0
        """
        base = {
            "coach_assigned": 5,
            "coach": 5,
            "ai_recommended": 4,
            "user_selected": 3,
            "intervention_plan": 3,
            "system": 2,
        }.get(task.source or "system", 3)

        bonus = {
            "challenging": 2,
            "moderate": 1,
            "easy": 0,
        }.get(task.difficulty or "easy", 0)

        return base + bonus

    # ──────────────────────────────────────────────────────────────
    # 数据闭环：行为反哺画像（原则三 Feedback Loop）
    # ──────────────────────────────────────────────────────────────

    def _update_profile_from_behavior(
        self,
        db: Session,
        user_id: int,
        domain: str,
        action: str,
    ) -> None:
        """
        行为反哺 BehavioralProfile.primary_domains（数据闭环）

        规则:
        - self_selected  → 立即加入关注领域
        - completed × 3  → 7天内连续完成3次，加入关注领域
        - skipped × 3    → 7天内连续跳过3次，降至关注列表末尾（障碍信号）
        最多保留 8 个关注领域
        """
        try:
            profile = (
                db.query(BehavioralProfile)
                .filter(BehavioralProfile.user_id == user_id)
                .first()
            )
            if not profile:
                return

            current_domains = list(profile.primary_domains or [])

            if action == "self_selected":
                if domain not in current_domains:
                    current_domains.append(domain)
                    profile.primary_domains = current_domains[:8]
                    db.flush()
                    logger.info(f"画像反哺(自选): user={user_id} 新增关注领域 {domain}")
                return

            # 统计近7天该领域行为
            seven_days_ago = (date.today() - timedelta(days=7)).isoformat()
            recent_completed = (
                db.query(func.count(MicroActionTask.id))
                .filter(
                    MicroActionTask.user_id == user_id,
                    MicroActionTask.domain == domain,
                    MicroActionTask.status == "completed",
                    MicroActionTask.scheduled_date >= seven_days_ago,
                )
                .scalar() or 0
            )
            recent_skipped = (
                db.query(func.count(MicroActionTask.id))
                .filter(
                    MicroActionTask.user_id == user_id,
                    MicroActionTask.domain == domain,
                    MicroActionTask.status == "skipped",
                    MicroActionTask.scheduled_date >= seven_days_ago,
                )
                .scalar() or 0
            )

            changed = False
            if action == "completed" and recent_completed >= 3 and domain not in current_domains:
                # 连续完成 → 加入关注领域
                current_domains.append(domain)
                changed = True
                logger.info(f"画像反哺(完成): user={user_id} 新增关注领域 {domain}（7天内{recent_completed}次）")
            elif action == "skipped" and recent_skipped >= 3 and domain in current_domains:
                # 连续跳过 → 降优先级（移至末尾，标记障碍信号，但不删除）
                current_domains = [d for d in current_domains if d != domain] + [domain]
                changed = True
                logger.info(f"画像反哺(跳过): user={user_id} 领域 {domain} 优先级降低（障碍信号）")

            if changed:
                profile.primary_domains = current_domains[:8]
                db.flush()

        except Exception as e:
            logger.warning(f"画像反哺失败: user={user_id}, domain={domain}, err={e}")

    # ──────────────────────────────────────────────────────────────
    # 任务完成 / 跳过 / 设备自动完成
    # ──────────────────────────────────────────────────────────────

    def complete_task(
        self,
        db: Session,
        task_id: int,
        user_id: int,
        note: Optional[str] = None,
        mood_score: Optional[int] = None,
    ) -> MicroActionTask:
        """
        完成任务（附带数据闭环反哺）

        1. 更新 task status → completed
        2. 写入 MicroActionLog
        3. 反哺 BehavioralProfile（completed × 3 → 加入关注领域）
        """
        task = (
            db.query(MicroActionTask)
            .filter(
                MicroActionTask.id == task_id,
                MicroActionTask.user_id == user_id,
            )
            .first()
        )
        if not task:
            raise ValueError("任务不存在或无权操作")
        if task.status == "completed":
            raise ValueError("任务已完成")

        task.status = "completed"
        task.completed_at = datetime.utcnow()

        log = MicroActionLog(
            task_id=task_id,
            user_id=user_id,
            action="completed",
            note=note,
            mood_score=mood_score,
        )
        db.add(log)
        db.commit()
        db.refresh(task)

        # 数据闭环：完成行为反哺画像
        try:
            self._update_profile_from_behavior(db, user_id, task.domain, "completed")
            db.commit()
        except Exception as e:
            logger.warning(f"完成反哺失败: {e}")

        logger.info(f"任务完成: task={task_id}, user={user_id}, source={task.source}, domain={task.domain}")
        return task

    def skip_task(
        self,
        db: Session,
        task_id: int,
        user_id: int,
        note: Optional[str] = None,
    ) -> MicroActionTask:
        """
        跳过任务（附带数据闭环反哺）

        连续跳过3次同领域 → 降低该领域在关注列表中的优先级（障碍信号）
        """
        task = (
            db.query(MicroActionTask)
            .filter(
                MicroActionTask.id == task_id,
                MicroActionTask.user_id == user_id,
            )
            .first()
        )
        if not task:
            raise ValueError("任务不存在或无权操作")

        task.status = "skipped"

        log = MicroActionLog(
            task_id=task_id,
            user_id=user_id,
            action="skipped",
            note=note,
        )
        db.add(log)
        db.commit()
        db.refresh(task)

        # 数据闭环：跳过行为反哺画像
        try:
            self._update_profile_from_behavior(db, user_id, task.domain, "skipped")
            db.commit()
        except Exception as e:
            logger.warning(f"跳过反哺失败: {e}")

        return task

    def auto_complete(
        self,
        db: Session,
        user_id: int,
        domain: str,
        note: str = "设备数据自动完成",
    ) -> Optional[MicroActionTask]:
        """
        设备数据自动完成指定领域的今日任务

        由 DeviceBehaviorBridge 调用（原则三：穿戴设备数据驱动）
        """
        today_str = date.today().isoformat()
        task = (
            db.query(MicroActionTask)
            .filter(
                MicroActionTask.user_id == user_id,
                MicroActionTask.domain == domain,
                MicroActionTask.scheduled_date == today_str,
                MicroActionTask.status == "pending",
            )
            .first()
        )
        if not task:
            return None

        return self.complete_task(db, task.id, user_id, note=note)

    # ──────────────────────────────────────────────────────────────
    # 今日任务列表 / 历史 / 教练创建
    # ──────────────────────────────────────────────────────────────

    def get_today_tasks(
        self,
        db: Session,
        user_id: int,
    ) -> List[MicroActionTask]:
        """获取今日任务列表（自动生成）"""
        today_str = date.today().isoformat()

        tasks = (
            db.query(MicroActionTask)
            .filter(
                MicroActionTask.user_id == user_id,
                MicroActionTask.scheduled_date == today_str,
            )
            .all()
        )

        if not tasks:
            tasks = self.generate_daily_tasks(db, user_id)

        return tasks

    def get_history(
        self,
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取历史记录（分页）"""
        query = (
            db.query(MicroActionTask)
            .filter(MicroActionTask.user_id == user_id)
        )

        if date_from:
            query = query.filter(MicroActionTask.scheduled_date >= date_from)
        if date_to:
            query = query.filter(MicroActionTask.scheduled_date <= date_to)

        total = query.count()
        tasks = (
            query
            .order_by(MicroActionTask.scheduled_date.desc(), MicroActionTask.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [self._task_to_dict(t) for t in tasks],
        }

    def create_coach_task(
        self,
        db: Session,
        user_id: int,
        coach_id: int,
        domain: str,
        title: str,
        description: Optional[str] = None,
        difficulty: str = "easy",
        scheduled_date: Optional[str] = None,
    ) -> MicroActionTask:
        """教练为学员创建微行动任务（经 coach_push_queue 审批后调用）"""
        task = MicroActionTask(
            user_id=user_id,
            domain=domain,
            title=title,
            description=description,
            difficulty=difficulty,
            source="coach_assigned",
            source_id=str(coach_id),
            status="pending",
            scheduled_date=scheduled_date or date.today().isoformat(),
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def expire_overdue_tasks(self, db: Session) -> int:
        """将过期的未完成任务标记为 expired"""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        count = (
            db.query(MicroActionTask)
            .filter(
                MicroActionTask.scheduled_date < yesterday,
                MicroActionTask.status == "pending",
            )
            .update({"status": "expired"})
        )
        db.commit()
        if count:
            logger.info(f"过期任务标记: count={count}")
        return count

    # ──────────────────────────────────────────────────────────────
    # 内部工具方法
    # ──────────────────────────────────────────────────────────────

    def _create_queue_summary(self, db: Session, user_id: int, tasks: List[MicroActionTask]):
        """若用户有教练，为今日微行动创建汇总 CoachPushQueue 条目（知情通知）"""
        try:
            from sqlalchemy import text as sa_text
            row = db.execute(sa_text(
                "SELECT coach_id FROM coach_schema.coach_student_bindings "
                "WHERE student_id = :sid AND is_active = true LIMIT 1"
            ), {"sid": user_id}).first()
            coach_id = row[0] if row else None
            if not coach_id:
                return

            from core import coach_push_queue_service as queue_svc
            task_titles = [t.title for t in tasks]
            queue_svc.create_queue_item(
                db,
                coach_id=coach_id,
                student_id=user_id,
                source_type="micro_action",
                source_id=None,
                title=f"今日微行动: {len(tasks)}项",
                content="、".join(task_titles),
                content_extra={
                    "task_ids": [t.id for t in tasks],
                    "domains": list(set(t.domain for t in tasks)),
                },
                priority="low",
            )
            db.commit()
        except Exception as e:
            logger.warning(f"创建微行动推送队列失败: user={user_id} err={e}")

    def _notify_coach_self_selected(self, db: Session, user_id: int, task: MicroActionTask) -> None:
        """通知教练：学员自选了任务（知情通知，不需要审核）"""
        try:
            from sqlalchemy import text as sa_text
            row = db.execute(sa_text(
                "SELECT coach_id FROM coach_schema.coach_student_bindings "
                "WHERE student_id = :sid AND is_active = true LIMIT 1"
            ), {"sid": user_id}).first()
            if not row:
                return
            coach_id = row[0]

            from core import coach_push_queue_service as queue_svc
            queue_svc.create_queue_item(
                db,
                coach_id=coach_id,
                student_id=user_id,
                source_type="micro_action_self_selected",
                source_id=None,
                title=f"学员自选任务: {task.title}",
                content=f"领域: {DOMAIN_NAMES.get(task.domain, task.domain)} | 难度: {task.difficulty}",
                content_extra={
                    "task_id": task.id,
                    "domain": task.domain,
                    "title": task.title,
                    "source": "user_selected",
                    "is_notification_only": True,
                },
                priority="low",
            )
        except Exception as e:
            logger.warning(f"通知教练(自选任务)失败: user={user_id}, err={e}")

    def _generate_default_tasks(
        self,
        db: Session,
        user_id: int,
        today_str: str,
        skip_domains: set = None,
        max_count: int = 3,
    ) -> List[MicroActionTask]:
        """无画像时生成默认简单任务"""
        skip_domains = skip_domains or set()
        defaults = [
            {"domain": "exercise", "title": "饭后散步10分钟", "difficulty": "easy"},
            {"domain": "nutrition", "title": "今天多喝一杯水", "difficulty": "easy"},
            {"domain": "sleep", "title": "记录今晚的入睡时间", "difficulty": "easy"},
        ]
        tasks = []
        for d in defaults:
            if d["domain"] in skip_domains or len(tasks) >= max_count:
                continue
            task = MicroActionTask(
                user_id=user_id,
                domain=d["domain"],
                title=d["title"],
                difficulty=d["difficulty"],
                source="system",
                status="pending",
                scheduled_date=today_str,
            )
            db.add(task)
            tasks.append(task)

        if tasks:
            db.commit()
            for t in tasks:
                db.refresh(t)
        return tasks

    def _get_default_candidates(self, focus_domains: List[str], covered_today: set = None) -> List[Dict]:
        """InterventionMatcher 不可用时的降级候选池（原则三 fallback）"""
        covered_today = covered_today or set()
        candidates = []
        for domain in focus_domains:
            for item in _DEFAULT_CANDIDATES.get(domain, []):
                candidates.append({
                    "domain": domain,
                    "domain_name": DOMAIN_NAMES.get(domain, domain),
                    "title": item["title"],
                    "description": item["description"],
                    "difficulty": item["difficulty"],
                    "source_hint": "ai_recommended",
                    "rx_id": None,
                    "already_today": domain in covered_today,
                })
        return candidates[:6]

    @staticmethod
    def _map_difficulty(difficulty_score) -> str:
        """将数字难度分映射为文字难度"""
        try:
            score = int(difficulty_score)
        except (TypeError, ValueError):
            return "easy"
        if score >= 4:
            return "challenging"
        elif score >= 2:
            return "moderate"
        return "easy"

    @staticmethod
    def _task_to_dict(task: MicroActionTask) -> Dict:
        return {
            "id": task.id,
            "user_id": task.user_id,
            "domain": task.domain,
            "domain_name": DOMAIN_NAMES.get(task.domain, task.domain),
            "title": task.title,
            "description": task.description,
            "difficulty": task.difficulty,
            "source": task.source,
            "source_id": task.source_id,
            "status": task.status,
            "scheduled_date": task.scheduled_date,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "created_at": task.created_at.isoformat() if task.created_at else None,
        }
