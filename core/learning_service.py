"""
学习业务逻辑服务

- 记录学习事件 (时长/积分)
- 更新连续打卡
- 角色自动晋级检查（六级四同道者体系）

晋级阈值统一来源: paths_api.py GET /coach-levels/levels
"""
from datetime import datetime, date
from sqlalchemy.orm import Session
from loguru import logger

from core.models import (
    User, UserRole, UserLearningStats, LearningTimeLog,
    LearningPointsLog, ExamResult, Assessment
)


def get_or_create_stats(db: Session, user_id: int) -> UserLearningStats:
    """获取或创建用户学习统计"""
    stats = db.query(UserLearningStats).filter(
        UserLearningStats.user_id == user_id
    ).first()
    if not stats:
        stats = UserLearningStats(
            user_id=user_id,
            updated_at=datetime.utcnow(),
        )
        db.add(stats)
        db.flush()
    return stats


def record_learning_time(
    db: Session,
    user_id: int,
    minutes: int,
    content_id: int = None,
    domain: str = None,
) -> dict:
    """记录学习时长"""
    log = LearningTimeLog(
        user_id=user_id,
        content_id=content_id,
        domain=domain,
        minutes=minutes,
        earned_at=datetime.utcnow(),
    )
    db.add(log)

    stats = get_or_create_stats(db, user_id)
    stats.total_minutes += minutes
    update_streak(db, stats)
    stats.updated_at = datetime.utcnow()
    db.commit()

    return {
        "total_minutes": stats.total_minutes,
        "current_streak": stats.current_streak,
    }


def record_learning_points(
    db: Session,
    user_id: int,
    points: int,
    source_type: str,
    category: str = "growth",
    source_id: str = None,
) -> dict:
    """记录学习积分"""
    log = LearningPointsLog(
        user_id=user_id,
        source_type=source_type,
        source_id=source_id,
        points=points,
        category=category,
        earned_at=datetime.utcnow(),
    )
    db.add(log)

    stats = get_or_create_stats(db, user_id)
    stats.total_points += points
    if category == "growth":
        stats.growth_points += points
    elif category == "contribution":
        stats.contribution_points += points
    elif category == "influence":
        stats.influence_points += points
    stats.updated_at = datetime.utcnow()
    db.commit()

    return {"total_points": stats.total_points, "category": category, "added": points}


def update_streak(db: Session, stats: UserLearningStats):
    """更新连续学习天数"""
    today = date.today().isoformat()
    if stats.last_learn_date == today:
        return  # 今天已记录

    yesterday = date.today()
    from datetime import timedelta
    yesterday_str = (yesterday - timedelta(days=1)).isoformat()

    if stats.last_learn_date == yesterday_str:
        stats.current_streak += 1
    else:
        stats.current_streak = 1

    stats.last_learn_date = today
    if stats.current_streak > stats.longest_streak:
        stats.longest_streak = stats.current_streak


def record_quiz_result(
    db: Session,
    user_id: int,
    passed: bool,
) -> dict:
    """记录考试结果到学习统计"""
    stats = get_or_create_stats(db, user_id)
    stats.quiz_total += 1
    if passed:
        stats.quiz_passed += 1
    stats.updated_at = datetime.utcnow()
    db.commit()
    return {"quiz_total": stats.quiz_total, "quiz_passed": stats.quiz_passed}


# ============================================
# 角色晋级规则（六级四同道者体系）
#
# 阈值对齐: paths_api.py GET /coach-levels/levels
# 每级 advancement.points_required 即为下一级最低要求
#
# L0 观察员  → L1 成长者:  growth≥100 + 完成评估
# L1 成长者  → L2 分享者:  growth≥500 + contribution≥50
# L2 分享者  → L3 教练:    growth≥800 + contribution≥200 + influence≥50 + 考试 + 4同道者→L1
# L3 教练    → L4 促进师:  growth≥1500 + contribution≥600 + influence≥200 + 考试 + 4同道者→L2
# L4 促进师  → L5 大师:    growth≥3000 + contribution≥1500 + influence≥600 + 考试 + 4同道者→L3
# ============================================

ROLE_PROGRESSION_RULES = {
    "observer": {
        "target": "grower",
        "check": "_check_observer_to_grower",
    },
    "grower": {
        "target": "sharer",
        "check": "_check_grower_to_sharer",
    },
    "sharer": {
        "target": "coach",
        "check": "_check_sharer_to_coach",
    },
    "coach": {
        "target": "promoter",
        "check": "_check_coach_to_promoter",
    },
    "promoter": {
        "target": "master",
        "check": "_check_promoter_to_master",
    },
}


def check_role_progression(db: Session, user: User) -> dict:
    """
    检查角色晋级条件

    Returns:
        {"eligible": bool, "current_role": str, "target_role": str, "missing": [...]}
    """
    role = user.role.value if hasattr(user.role, 'value') else user.role
    rule = ROLE_PROGRESSION_RULES.get(role)
    if not rule:
        return {"eligible": False, "current_role": role, "target_role": None, "missing": ["已达最高等级或无晋级路径"]}

    checker = globals().get(rule["check"])
    if not checker:
        return {"eligible": False, "current_role": role, "target_role": rule["target"], "missing": ["检查函数未找到"]}

    return checker(db, user, rule["target"])


def _count_companions(db: Session, mentor_id: int, target_role: str) -> int:
    """
    统计该用户已引领到目标角色的同道者数量

    优先使用 companion_relations 表（V002迁移后可用），
    回退到 referred_by 字段（旧方案）。
    """
    from core.models import ROLE_LEVEL_STR

    target_level = ROLE_LEVEL_STR.get(target_role, 99)

    # 优先: 使用 companion_relations 表 (V002 迁移后可用)
    try:
        from sqlalchemy import text
        result = db.execute(text(
            "SELECT COUNT(*) FROM companion_relations "
            "WHERE mentor_id = :mid AND status = 'graduated'"
        ), {"mid": mentor_id}).scalar()
        if result is not None:
            return result
    except Exception:
        pass

    # 回退: 使用 User.referred_by 字段（旧方案）
    if not hasattr(User, 'referred_by'):
        return 0

    referred_users = db.query(User).filter(
        User.referred_by == mentor_id
    ).all()

    count = 0
    for u in referred_users:
        r = u.role.value if hasattr(u.role, 'value') else str(u.role)
        level = ROLE_LEVEL_STR.get(r, 0)
        if level >= target_level:
            count += 1
    return count


# ---- L0 → L1 ----

def _check_observer_to_grower(db: Session, user: User, target: str) -> dict:
    """
    observer → grower
    条件: growth≥100 + 完成首次评估
    """
    missing = []
    stats = get_or_create_stats(db, user.id)

    # 1. 完成评估
    has_assessment = db.query(Assessment).filter(
        Assessment.user_id == user.id,
        Assessment.status == "completed",
    ).first()
    if not has_assessment:
        missing.append("完成首次评估")

    # 2. 成长积分 ≥ 100
    if stats.growth_points < 100:
        missing.append(f"成长积分 {stats.growth_points}/100")

    return {
        "eligible": len(missing) == 0,
        "current_role": "observer",
        "target_role": target,
        "missing": missing,
    }


# ---- L1 → L2 ----

def _check_grower_to_sharer(db: Session, user: User, target: str) -> dict:
    """
    grower → sharer
    条件: growth≥500 + contribution≥50
    """
    missing = []
    stats = get_or_create_stats(db, user.id)

    if stats.growth_points < 500:
        missing.append(f"成长积分 {stats.growth_points}/500")

    if stats.contribution_points < 50:
        missing.append(f"贡献积分 {stats.contribution_points}/50")

    return {
        "eligible": len(missing) == 0,
        "current_role": "grower",
        "target_role": target,
        "missing": missing,
    }


# ---- L2 → L3 ----

def _check_sharer_to_coach(db: Session, user: User, target: str) -> dict:
    """
    sharer → coach
    条件: growth≥800 + contribution≥200 + influence≥50 + 考试通过 + 4同道者→L1(成长者)
    """
    missing = []
    stats = get_or_create_stats(db, user.id)

    # 积分检查
    if stats.growth_points < 800:
        missing.append(f"成长积分 {stats.growth_points}/800")

    if stats.contribution_points < 200:
        missing.append(f"贡献积分 {stats.contribution_points}/200")

    if stats.influence_points < 50:
        missing.append(f"影响力积分 {stats.influence_points}/50")

    # 考试检查
    exam_pass = db.query(ExamResult).filter(
        ExamResult.user_id == user.id,
        ExamResult.status == "passed",
    ).first()
    if not exam_pass:
        missing.append("通过认证考试")

    # 四同道者检查: 需引领4位观察员成为成长者
    companions = _count_companions(db, user.id, "grower")
    if companions < 4:
        missing.append(f"引领同道者成为成长者 {companions}/4")

    return {
        "eligible": len(missing) == 0,
        "current_role": "sharer",
        "target_role": target,
        "missing": missing,
    }


# ---- L3 → L4 ----

def _check_coach_to_promoter(db: Session, user: User, target: str) -> dict:
    """
    coach → promoter
    条件: growth≥1500 + contribution≥600 + influence≥200 + 考试通过 + 4同道者→L2(分享者)
    """
    missing = []
    stats = get_or_create_stats(db, user.id)

    if stats.growth_points < 1500:
        missing.append(f"成长积分 {stats.growth_points}/1500")

    if stats.contribution_points < 600:
        missing.append(f"贡献积分 {stats.contribution_points}/600")

    if stats.influence_points < 200:
        missing.append(f"影响力积分 {stats.influence_points}/200")

    exam_pass = db.query(ExamResult).filter(
        ExamResult.user_id == user.id,
        ExamResult.status == "passed",
    ).first()
    if not exam_pass:
        missing.append("通过促进师认证考试")

    companions = _count_companions(db, user.id, "sharer")
    if companions < 4:
        missing.append(f"引领同道者成为分享者 {companions}/4")

    return {
        "eligible": len(missing) == 0,
        "current_role": "coach",
        "target_role": target,
        "missing": missing,
    }


# ---- L4 → L5 ----

def _check_promoter_to_master(db: Session, user: User, target: str) -> dict:
    """
    promoter → master
    条件: growth≥3000 + contribution≥1500 + influence≥600 + 考试通过 + 4同道者→L3(教练)
    """
    missing = []
    stats = get_or_create_stats(db, user.id)

    if stats.growth_points < 3000:
        missing.append(f"成长积分 {stats.growth_points}/3000")

    if stats.contribution_points < 1500:
        missing.append(f"贡献积分 {stats.contribution_points}/1500")

    if stats.influence_points < 600:
        missing.append(f"影响力积分 {stats.influence_points}/600")

    exam_pass = db.query(ExamResult).filter(
        ExamResult.user_id == user.id,
        ExamResult.status == "passed",
    ).first()
    if not exam_pass:
        missing.append("通过大师认证考试")

    companions = _count_companions(db, user.id, "coach")
    if companions < 4:
        missing.append(f"引领同道者成为教练 {companions}/4")

    return {
        "eligible": len(missing) == 0,
        "current_role": "promoter",
        "target_role": target,
        "missing": missing,
    }


def apply_role_progression(db: Session, user: User) -> dict:
    """执行角色晋级(如果符合条件)"""
    result = check_role_progression(db, user)
    if result["eligible"] and result["target_role"]:
        old_role = user.role.value if hasattr(user.role, 'value') else user.role
        try:
            user.role = UserRole(result["target_role"])
            db.commit()
            logger.info(f"用户 {user.id} 晋级: {old_role} → {result['target_role']}")
            result["promoted"] = True
        except Exception as e:
            logger.error(f"晋级失败: {e}")
            result["promoted"] = False
    else:
        result["promoted"] = False
    return result
